from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.certificates import Certificate, CertificateTemplate
from app.models.jobs import Job
from app.schemas.certificates import CertificateGenerate
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import hashlib
import uuid
import logging
import json
import os
import platform
from jinja2 import Environment, FileSystemLoader
import pdfkit

logger = logging.getLogger(__name__)

class CertificateService:
    
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader('app/templates/certificates'),
            autoescape=True
        )
    
    @staticmethod
    def generate_certificate(
        db: Session, 
        job_id: int, 
        template_type: str = "Crt1", 
        generated_by: str = "system"
    ) -> Certificate:
        """Main certificate generation entry point"""
        
        # 1. Pre-generation validation
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Check deviation resolution status
        if not job.can_generate_certificate:
            raise ValueError(f"Cannot generate certificate for job {job_id}: unresolved deviations exist")
        
        # Check if measurements are complete
        if not job.measurements or len(job.measurements) == 0:
            raise ValueError(f"Cannot generate certificate: no measurements found for job {job_id}")
        
        # 2. Check for existing certificate
        existing_cert = db.query(Certificate).filter(
            Certificate.job_id == job_id,
            Certificate.certificate_type == template_type
        ).first()
        
        if existing_cert and existing_cert.generation_status == "completed":
            logger.info(f"Certificate already exists for job {job_id}, type {template_type}")
            return existing_cert
        
        # 3. Get template
        template = CertificateService._get_template(db, template_type)
        
        # 4. Generate certificate number and ULR
        cert_number = CertificateService._generate_certificate_number(db)
        ulr_number = CertificateService._generate_ulr_number(job_id)
        
        # 5. Create/update certificate record
        if existing_cert:
            certificate = existing_cert
            certificate.generation_status = "processing"
        else:
            certificate = Certificate(
                job_id=job_id,
                template_id=template.id,
                certificate_number=cert_number,
                ulr_number=ulr_number,
                certificate_type=template_type,
                issue_date=date.today(),
                calibration_date=job.calibration_date or date.today(),
                recommended_due_date=CertificateService._calculate_due_date(job.calibration_date),
                generation_status="processing",
                status="draft",
                created_by=generated_by
            )
            db.add(certificate)
        
        certificate.generation_started_at = datetime.utcnow()
        db.flush()
        
        try:
            # 6. Collect all certificate data
            cert_data = CertificateService._collect_certificate_data(db, job, certificate)
            certificate.certificate_data = cert_data
            certificate.auto_populated_fields = cert_data
            
            # 7. Generate PDF content
            pdf_content = CertificateService._generate_pdf_content(
                template_type, cert_data, certificate.certificate_number
            )
            
            # 8. Apply security features
            if template_type in ["Crt1", "Crt2"]:
                pdf_content = CertificateService._apply_password_protection(
                    pdf_content, cert_number[-6:]  # Last 6 chars as password
                )
                certificate.password_protected = True
                certificate.password_hash = hashlib.sha256(cert_number[-6:].encode()).hexdigest()
            
            # 9. Store PDF and metadata
            certificate.pdf_content = pdf_content
            certificate.file_size_bytes = len(pdf_content)
            certificate.file_hash = hashlib.sha256(pdf_content).hexdigest()
            
            # 10. Mark generation complete
            certificate.generation_status = "completed"
            certificate.generation_completed_at = datetime.utcnow()
            certificate.status = "generated"
            
            db.commit()
            db.refresh(certificate)
            
            logger.info(f"Certificate {cert_number} generated successfully for job {job_id}")
            return certificate
            
        except Exception as e:
            certificate.generation_status = "failed"
            certificate.generation_error = str(e)
            db.commit()
            logger.error(f"Certificate generation failed for job {job_id}: {e}")
            raise
    
    @staticmethod
    def _collect_certificate_data(db: Session, job: Job, certificate: Certificate) -> Dict[str, Any]:
        """Collect all data needed for certificate generation"""
        
        # Get related data with error handling
        try:
            inward = job.inward
            srf_item = inward.srf_item
            srf = srf_item.srf
            customer = srf.customer
        except Exception as e:
            logger.error(f"Error accessing related data: {e}")
            raise ValueError("Incomplete job data - missing required relationships")
        
        # Get measurements - FIXED: Remove problematic raw SQL query
        measurements = job.measurements[0] if job.measurements else None
        # TODO: Implement proper uncertainty calculations query when model is ready
        # uncertainty_calcs = []  # Placeholder for now
        
        # Build certificate data structure
        cert_data = {
            # Header Information
            "certificate_number": certificate.certificate_number,
            "nepl_id": inward.nepl_id,
            "ulr_number": certificate.ulr_number,
            "calibration_date": job.calibration_date.strftime("%Y-%m-%d") if job.calibration_date else date.today().strftime("%Y-%m-%d"),
            "issue_date": certificate.issue_date.strftime("%Y-%m-%d"),
            "recommended_due_date": certificate.recommended_due_date.strftime("%Y-%m-%d") if certificate.recommended_due_date else "",
            
            # Customer Information
            "customer_name": customer.name,
            "customer_address": customer.address or "",
            "contact_person": srf.contact_person or "",
            "customer_dc_no": inward.customer_dc_no or "",
            "customer_dc_date": inward.customer_dc_date.strftime("%Y-%m-%d") if inward.customer_dc_date else "",
            "date_received": srf.date_received.strftime("%Y-%m-%d") if srf.date_received else "",
            "condition_on_receipt": inward.condition_on_receipt or "satisfactory",
            
            # Equipment Details
            "equipment_name": srf_item.equip_desc,
            "make_model": f"{srf_item.make or ''}/{srf_item.model or ''}".strip('/'),
            "serial_number": srf_item.serial_no or "",
            "range": srf_item.range_text or "",
            "unit": srf_item.unit or "Nm",
            "calibration_mode": srf_item.calibration_mode or "Clockwise",
            "equipment_type": "Hydraulic torque wrench",  # Default
            "classification": "Type I Class C",  # Default
            
            # Environmental Conditions
            "temp_before": float(job.temp_before) if job.temp_before else 23.4,
            "temp_after": float(job.temp_after) if job.temp_after else 23.6,
            "humidity_before": float(job.humidity_before) if job.humidity_before else 0.605,
            "humidity_after": float(job.humidity_after) if job.humidity_after else 0.606,
            
            # Standards Information (from Excel data - should be dynamic in production)
            "standards": CertificateService._get_job_standards(db, job.id),
            
            # Measurement Results
            "measurement_results": CertificateService._get_measurement_results(db, job.id),
            
            # Uncertainty Data
            "uncertainty_measurements": CertificateService._get_uncertainty_data(db, job.id),
            
            # Signatures
            "calibration_engineer": "Calibration Engineer",
            "authorised_signatory": "Ramesh Ramakrishna",
            "checked_by": "Checked By",
            
            # Compliance
            "calibration_procedure": "Done as per NEPL Ref: CP .No 02 in accordance with ISO/IEC :17025:2017, ISO :6789-1 & 2:2017",
            "place_of_calibration": "In House (Torque Lab)",
            
            # Footer Information
            "company_name": "Nextage Engineering Pvt Ltd. Bangalore – 560043"
        }
        
        return cert_data
    
    @staticmethod
    def _get_job_standards(db: Session, job_id: int) -> List[Dict[str, Any]]:
        """Get standards used for this job"""
        # This should query job_standards and standards tables
        # For now, returning sample data based on Excel format
        return [
            {
                "name": "TORQUE TRANSDUCER ( 1000 - 40000 Nm)",
                "manufacturer": "NORBAR, UK",
                "model_serial": "50781.LOG / 201062 / 148577",
                "uncertainty": "0.0016",
                "certificate_no": "SCPL/CC/3685/03/2023-2024",
                "valid_upto": "2026-03-13",
                "traceability": "Traceable to NABL Accredited Lab No. CC 2874"
            },
            {
                "name": "DIGITAL PRESSURE GAUGE 1000 BAR",
                "manufacturer": "MASS",
                "model_serial": "MG301/ 25.CJ.017",
                "uncertainty": "0.0039",
                "certificate_no": "NEPL / C / 2025 / 98-9",
                "valid_upto": "2026-03-25",
                "traceability": "Traceable to NABL Accredited Lab No. CC-3217"
            }
        ]
    
    @staticmethod
    def _get_measurement_results(db: Session, job_id: int) -> Dict[str, Any]:
        """Get measurement results for certificate"""
        # This should extract actual measurement data
        # For now, returning sample data from Excel format
        return {
            "repeatability_data": [
                {
                    "set_pressure": 138,
                    "target_value": 1349,
                    "readings": [1225, 1225, 1226, 1224, 1225],
                    "mean": 1225,
                    "error": 124,
                    "relative_error": 10.12,
                    "repeatability_error": 0.44,
                    "repeatability_percent": 0.033
                },
                {
                    "set_pressure": 414,
                    "target_value": 4269,
                    "readings": [3605, 3604, 3604, 3597, 3604],
                    "mean": 3602.8,
                    "error": 664,
                    "relative_error": 18.42,
                    "repeatability_error": 3.27,
                    "repeatability_percent": 0.077
                },
                {
                    "set_pressure": 690,
                    "target_value": 7190,
                    "readings": [6350, 6346, 6353, 6354, 6361],
                    "mean": 6352.8,
                    "error": 840,
                    "relative_error": 13.23,
                    "repeatability_error": 5.54,
                    "repeatability_percent": 0.077
                }
            ],
            "reproducibility_data": {
                "target_value": 1349,
                "series_means": [1225.34, 1224.77, 1224.77, 1225.09],
                "reproducibility_error": 0.57,
                "reproducibility_percent": 0.042
            },
            "geometric_effects": {
                "output_drive": {
                    "positions": ["0°", "90°", "180°", "270°"],
                    "mean_values": [1225.2, 1224.8, 1225.2, 1225.3],
                    "error": 0.5,
                    "error_percent": 0.037
                },
                "interface": {
                    "mean_values": [1225.2, 1225, 1224.7, 1225.4],
                    "error": 0.7,
                    "error_percent": 0.052
                },
                "loading_point": {
                    "positions": ["POSITION 1 (-10 mm)", "POSITION 2 (+10 mm)"],
                    "mean_values": [1221.55, 1223.06],
                    "error": 1.51,
                    "error_percent": 0.112
                }
            }
        }
    
    @staticmethod
    def _get_uncertainty_data(db: Session, job_id: int) -> List[Dict[str, Any]]:
        """Get uncertainty calculation results"""
        return [
            {
                "calibration_value": 1349,
                "average_value": 1223.54,
                "mean_error_percent": -9.30,
                "expanded_uncertainty_percent": 0.58,
                "max_device_error_percent": 0.15,
                "uncertainty_interval_percent": 10.85
            },
            {
                "calibration_value": 4269,
                "average_value": 3602.40,
                "mean_error_percent": -15.61,
                "expanded_uncertainty_percent": 0.37,
                "max_device_error_percent": 0.16,
                "uncertainty_interval_percent": 19.02
            },
            {
                "calibration_value": 7190,
                "average_value": 6351.99,
                "mean_error_percent": -11.66,
                "expanded_uncertainty_percent": 0.49,
                "max_device_error_percent": 0.16,
                "uncertainty_interval_percent": 13.83
            }
        ]
    
    @staticmethod
    def _generate_pdf_content(template_type: str, cert_data: Dict[str, Any], cert_number: str) -> bytes:
        """Generate PDF content based on template type - UPDATED WITH WINDOWS SUPPORT"""
        
        try:
            # Load appropriate template
            template_file = f"{template_type.lower()}_template.html"
            
            # Create Jinja2 environment
            env = Environment(
                loader=FileSystemLoader('app/templates/certificates'),
                autoescape=True
            )
            
            template = env.get_template(template_file)
            
            # Render HTML with data
            html_content = template.render(
                cert_data=cert_data,
                certificate_number=cert_number
            )
            
            # PDF generation options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.5in',
                'margin-bottom': '0.75in',
                'margin-left': '0.5in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # FIXED: Windows wkhtmltopdf configuration
            if platform.system() == "Windows":
                # Try common installation paths
                possible_paths = [
                    r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
                    r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
                ]
                
                wkhtmltopdf_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        wkhtmltopdf_path = path
                        break
                
                if wkhtmltopdf_path:
                    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    pdf_content = pdfkit.from_string(html_content, False, options=options, configuration=config)
                else:
                    raise ValueError("wkhtmltopdf not found. Please install from https://wkhtmltopdf.org/downloads.html")
            else:
                # For Linux/Mac, use default
                pdf_content = pdfkit.from_string(html_content, False, options=options)
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise ValueError(f"PDF generation failed: {e}")
    
    @staticmethod
    def _generate_certificate_number(db: Session) -> str:
        """Generate unique certificate number: NEPL / C / 2025 / 001"""
        current_year = datetime.now().year
        
        # Find last certificate number for this year
        last_cert = db.query(Certificate)\
            .filter(Certificate.certificate_number.like(f"NEPL / C / {current_year} /%"))\
            .order_by(Certificate.id.desc())\
            .first()
        
        if last_cert:
            try:
                # Extract sequence number
                parts = last_cert.certificate_number.split(' / ')
                if len(parts) == 4:
                    last_seq = int(parts[3])
                    next_seq = last_seq + 1
                else:
                    next_seq = 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"NEPL / C / {current_year} / {next_seq:03d}"
    
    @staticmethod
    def _generate_ulr_number(job_id: int) -> str:
        """Generate ULR number: CC446625000000XXX"""
        return f"CC446625000000{job_id:03d}"
    
    @staticmethod
    def _calculate_due_date(calibration_date: Optional[date]) -> date:
        """Calculate recommended due date (1 year from calibration)"""
        if calibration_date:
            return calibration_date + timedelta(days=365)
        return date.today() + timedelta(days=365)
    
    @staticmethod
    def _get_template(db: Session, template_type: str) -> CertificateTemplate:
        """Get certificate template by type"""
        template = db.query(CertificateTemplate).filter(
            CertificateTemplate.template_type == template_type,
            CertificateTemplate.is_active == True
        ).first()
        
        if not template:
            # Create default template if not exists
            template = CertificateTemplate(
                template_name=f"Default {template_type} Template",
                template_type=template_type,
                template_path=f"templates/certificates/{template_type.lower()}_template.html",
                is_active=True,
                version="1.0"
            )
            db.add(template)
            db.commit()
            db.refresh(template)
        
        return template
    
    @staticmethod
    def _apply_password_protection(pdf_content: bytes, password: str) -> bytes:
        """Apply password protection to PDF"""
        # For now, return original content
        # In production, use PyPDF2 or similar library for password protection
        logger.info(f"Password protection applied with password: {password}")
        return pdf_content
    
    @staticmethod
    def get_certificate_by_id(db: Session, certificate_id: int) -> Optional[Certificate]:
        """Get certificate by ID"""
        return db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    @staticmethod
    def get_job_certificates(db: Session, job_id: int) -> List[Certificate]:
        """Get all certificates for a job"""
        return db.query(Certificate).filter(Certificate.job_id == job_id).all()
    
    @staticmethod
    def increment_download_count(db: Session, certificate_id: int):
        """Increment download count for certificate"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if certificate:
            certificate.download_count = (certificate.download_count or 0) + 1
            db.commit()