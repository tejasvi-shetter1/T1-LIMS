from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.certificates import Certificate
from app.services.certificate_service import CertificateService
from app.schemas.certificates import (
    CertificateGenerate, CertificateResponse, 
    CertificateDetailResponse, CertificateDownloadResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate")
async def generate_certificate(
    cert_request: CertificateGenerate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate certificate for job"""
    try:
        # TODO: Get current user from JWT token
        current_user = "system"  
        
        certificate = CertificateService.generate_certificate(
            db=db,
            job_id=cert_request.job_id,
            template_type=cert_request.template_type,
            generated_by=current_user
        )
        
        # TODO: Add notification task
        # background_tasks.add_task(NotificationService.send_certificate_ready_notification, certificate.id)
        
        return {
            "success": True,
            "message": "Certificate generated successfully",
            "certificate_id": certificate.id,
            "certificate_number": certificate.certificate_number,
            "download_url": f"/api/v1/certificates/{certificate.id}/download",
            "status": certificate.generation_status
        }
        
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/job/{job_id}", response_model=List[CertificateResponse])
async def get_job_certificates(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get all certificates for a job"""
    certificates = CertificateService.get_job_certificates(db=db, job_id=job_id)
    return certificates

@router.get("/{certificate_id}", response_model=CertificateDetailResponse)
async def get_certificate_details(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """Get certificate details"""
    certificate = CertificateService.get_certificate_by_id(db=db, certificate_id=certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return certificate

@router.get("/{certificate_id}/download")
async def download_certificate(
    certificate_id: int,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Download certificate PDF"""
    certificate = CertificateService.get_certificate_by_id(db=db, certificate_id=certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if not certificate.pdf_content:
        raise HTTPException(status_code=404, detail="PDF content not available")
    
    # Check if password is required
    if certificate.password_protected and not password:
        raise HTTPException(
            status_code=401, 
            detail="Password required for protected certificate"
        )
    
    # Validate password if provided
    if certificate.password_protected and password:
        # TODO: Implement proper password validation
        expected_password = certificate.certificate_number[-6:]  # Last 6 chars
        if password != expected_password:
            raise HTTPException(status_code=401, detail="Invalid password")
    
    # Update download count
    CertificateService.increment_download_count(db=db, certificate_id=certificate_id)
    
    # Generate filename
    filename = f"{certificate.certificate_number.replace('/', '_').replace(' ', '_')}.pdf"
    
    # Return PDF response
    return Response(
        content=certificate.pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(certificate.pdf_content))
        }
    )

@router.get("/", response_model=List[CertificateResponse])
async def list_certificates(
    status: Optional[str] = None,
    generation_status: Optional[str] = None,
    job_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List certificates with filters"""
    query = db.query(Certificate)
    
    if status:
        query = query.filter(Certificate.status == status)
    if generation_status:
        query = query.filter(Certificate.generation_status == generation_status)
    if job_id:
        query = query.filter(Certificate.job_id == job_id)
    
    certificates = query.offset(skip).limit(limit).all()
    return certificates

@router.put("/{certificate_id}/approve")
async def approve_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """Approve certificate for delivery"""
    certificate = CertificateService.get_certificate_by_id(db=db, certificate_id=certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if certificate.generation_status != "completed":
        raise HTTPException(status_code=400, detail="Certificate not ready for approval")
    
    # TODO: Get current user from JWT
    current_user = "quality_manager"
    
    certificate.status = "approved"
    certificate.approved_by = current_user
    db.commit()
    
    return {
        "success": True,
        "message": "Certificate approved successfully",
        "certificate_id": certificate.id,
        "status": certificate.status
    }

@router.get("/{certificate_id}/info", response_model=CertificateDownloadResponse)
async def get_certificate_download_info(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """Get certificate download information"""
    certificate = CertificateService.get_certificate_by_id(db=db, certificate_id=certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    filename = f"{certificate.certificate_number.replace('/', '_').replace(' ', '_')}.pdf"
    
    return CertificateDownloadResponse(
        certificate_id=certificate.id,
        filename=filename,
        download_url=f"/api/v1/certificates/{certificate.id}/download",
        requires_password=certificate.password_protected
    )
