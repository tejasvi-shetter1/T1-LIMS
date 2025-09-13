# app/services/email_service.py - Email Notification System
from typing import List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.deviations import DeviationReport
from app.models.jobs import Job
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email Notification Service for Auto-Deviation System
    
    Handles all email communications for deviation notifications,
    customer approvals, and lab team updates.
    """
    
    # Email templates for different scenarios
    DEVIATION_NOTIFICATION_TEMPLATE = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f44336; color: white; padding: 15px; border-radius: 5px; }
            .content { margin: 20px 0; }
            .table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            .table th, .table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            .table th { background-color: #f2f2f2; }
            .button { background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
            .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🚨 Calibration Deviation Notification</h2>
        </div>
        
        <div class="content">
            <p>Dear {customer_name},</p>
            
            <p>A deviation has been identified during the calibration of your equipment. Your immediate attention is required for approval.</p>
            
            <table class="table">
                <tr><th>Job Number</th><td>{job_number}</td></tr>
                <tr><th>NEPL Work ID</th><td>{nepl_work_id}</td></tr>
                <tr><th>Equipment</th><td>{equipment_desc}</td></tr>
                <tr><th>Make/Model</th><td>{make_model}</td></tr>
                <tr><th>Serial Number</th><td>{serial_no}</td></tr>
                <tr><th>Deviation Number</th><td><strong>{deviation_number}</strong></td></tr>
                <tr><th>Severity</th><td><span style="color: {severity_color};">{severity}</span></td></tr>
                <tr><th>Date Identified</th><td>{created_date}</td></tr>
            </table>
            
            <h3>📋 Deviation Details</h3>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
                <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{description}</pre>
            </div>
            
            <h3>🔧 Technical Impact</h3>
            <p>{technical_impact}</p>
            
            <h3>👤 Customer Impact</h3>
            <div class="warning">
                <strong>⚠️ Action Required:</strong> {customer_impact}
            </div>
            
            <h3>✅ Required Customer Decision</h3>
            <p>Please review this deviation and provide your approval decision:</p>
            <ul>
                <li><strong>ACCEPT</strong> - Proceed with certificate issuance with noted deviation</li>
                <li><strong>REJECT</strong> - Request re-calibration or corrective action</li>
                <li><strong>CONDITIONAL</strong> - Accept with specific conditions or limitations</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{approval_url}" class="button">📋 Review & Approve Deviation</a>
            </div>
            
            <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                <p><strong>Contact Information:</strong></p>
                <p>
                    📧 Email: calibration@nextage-engineering.com<br>
                    📞 Phone: +91-80-XXXX-XXXX<br>
                    🌐 Web: www.nextage-engineering.com
                </p>
                
                <p style="font-size: 12px; color: #666;">
                    This is an automated notification from NEPL LIMS. Please do not reply to this email directly.
                    For technical queries, contact our calibration team.
                </p>
            </div>
        </div>
        
        <div style="background-color: #f2f2f2; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <p><strong>Best regards,</strong><br>
            NEPL Calibration Team<br>
            Nextage Engineering Pvt. Ltd.<br>
            ISO/IEC 17025:2017 Accredited Laboratory</p>
        </div>
    </body>
    </html>
    """
    
    DEVIATION_APPROVED_TEMPLATE = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; }
            .content { margin: 20px 0; }
            .table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            .table th, .table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            .table th { background-color: #f2f2f2; }
            .success { background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 4px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>✅ Customer Approved Deviation</h2>
        </div>
        
        <div class="content">
            <p>Dear Lab Team,</p>
            
            <div class="success">
                <strong>✅ Good News!</strong> The customer has approved the following deviation.
            </div>
            
            <table class="table">
                <tr><th>Deviation Number</th><td>{deviation_number}</td></tr>
                <tr><th>Job Number</th><td>{job_number}</td></tr>
                <tr><th>Customer</th><td>{customer_name}</td></tr>
                <tr><th>Customer Decision</th><td><strong>{client_decision}</strong></td></tr>
                <tr><th>Decision Date</th><td>{decision_date}</td></tr>
            </table>
            
            <h3>💬 Customer Comments</h3>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
                <p>{client_comments}</p>
            </div>
            
            <h3>📋 Next Steps</h3>
            <ul>
                <li>✅ Proceed with certificate generation</li>
                <li>📄 Include deviation details in certificate</li>
                <li>🔄 Update job status to approved</li>
                <li>📧 Send certificate to customer</li>
            </ul>
            
            <p><strong>Job Status:</strong> Ready for certificate generation</p>
        </div>
        
        <div style="background-color: #f2f2f2; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <p><strong>NEPL LIMS - Automated Notification</strong><br>
            Generated on: {timestamp}</p>
        </div>
    </body>
    </html>
    """
    
    @staticmethod
    def send_deviation_notification(
        deviation: DeviationReport, 
        job: Job, 
        customer_email: str, 
        customer_name: str
    ) -> Dict[str, Any]:
        """
        📧 Send deviation notification email to customer
        """
        try:
            # Generate approval URL (you'll need to implement frontend route)
            approval_url = f"https://your-frontend-domain.com/deviations/{deviation.id}/approve"
            
            # Determine severity color
            severity_colors = {
                "low": "#28a745",
                "medium": "#ffc107", 
                "high": "#dc3545",
                "critical": "#6f42c1"
            }
            severity_color = severity_colors.get(deviation.severity, "#6c757d")
            
            # Get equipment details
            srf_item = job.inward.srf_item
            
            # Prepare email content
            email_content = EmailService.DEVIATION_NOTIFICATION_TEMPLATE.format(
                customer_name=customer_name,
                job_number=job.job_number,
                nepl_work_id=job.nepl_work_id,
                equipment_desc=srf_item.equip_desc,
                make_model=f"{srf_item.make} / {srf_item.model}",
                serial_no=srf_item.serial_no,
                deviation_number=deviation.deviation_number,
                severity=deviation.severity.upper(),
                severity_color=severity_color,
                created_date=deviation.created_at.strftime("%Y-%m-%d %H:%M"),
                description=deviation.description,
                technical_impact=deviation.technical_impact,
                customer_impact=deviation.customer_impact,
                approval_url=approval_url
            )
            
            # Send email
            result = EmailService._send_email(
                to_email=customer_email,
                subject=f"🚨 URGENT: Calibration Deviation Approval Required - {job.job_number}",
                html_content=email_content
            )
            
            logger.info(f"Deviation notification sent for {deviation.deviation_number} to {customer_email}")
            return {"success": True, "message": "Email sent successfully", "email": customer_email}
            
        except Exception as e:
            logger.error(f"Failed to send deviation notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_deviation_approved_notification(
        deviation: DeviationReport, 
        job: Job, 
        lab_team_emails: List[str]
    ) -> Dict[str, Any]:
        """
        📧 Send notification to lab team when customer approves deviation
        """
        try:
            subject = f"✅ Deviation Approved - {deviation.deviation_number} - Job {job.job_number}"
            
            # Get customer details
            customer = job.inward.srf_item.srf.customer
            
            content = EmailService.DEVIATION_APPROVED_TEMPLATE.format(
                deviation_number=deviation.deviation_number,
                job_number=job.job_number,
                customer_name=customer.name,
                client_decision=deviation.client_decision or "APPROVED",
                decision_date=deviation.client_decision_date.strftime("%Y-%m-%d") if deviation.client_decision_date else "N/A",
                client_comments=deviation.client_comments or "No additional comments provided",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Send to all lab team members
            sent_count = 0
            for email in lab_team_emails:
                if EmailService._send_email(email, subject, content):
                    sent_count += 1
            
            logger.info(f"Deviation approval notifications sent to {sent_count}/{len(lab_team_emails)} team members")
            
            return {
                "success": True, 
                "message": f"Notifications sent to {sent_count} team members",
                "sent_count": sent_count,
                "total_recipients": len(lab_team_emails)
            }
            
        except Exception as e:
            logger.error(f"Failed to send deviation approval notifications: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_deviation_rejected_notification(
        deviation: DeviationReport,
        job: Job,
        lab_team_emails: List[str]
    ) -> Dict[str, Any]:
        """
        📧 Send notification when customer rejects deviation
        """
        try:
            subject = f"❌ Deviation Rejected - {deviation.deviation_number} - Action Required"
            
            customer = job.inward.srf_item.srf.customer
            
            content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px;">
                    <h2>❌ Customer Rejected Deviation</h2>
                </div>
                
                <p>The customer has rejected the deviation and requested corrective action:</p>
                
                <table border="1" style="border-collapse: collapse; width: 100%; margin: 15px 0;">
                    <tr><th>Deviation Number</th><td>{deviation.deviation_number}</td></tr>
                    <tr><th>Job Number</th><td>{job.job_number}</td></tr>
                    <tr><th>Customer</th><td>{customer.name}</td></tr>
                    <tr><th>Customer Decision</th><td><strong>REJECTED</strong></td></tr>
                    <tr><th>Customer Comments</th><td>{deviation.client_comments or 'No comments provided'}</td></tr>
                </table>
                
                <h3>🔧 Required Actions</h3>
                <ul>
                    <li>Review customer feedback and comments</li>
                    <li>Implement corrective actions</li>
                    <li>Schedule re-calibration if necessary</li>
                    <li>Contact customer to discuss next steps</li>
                </ul>
                
                <p><strong>Priority:</strong> HIGH - Customer action required</p>
            </body>
            </html>
            """
            
            # Send to lab team
            sent_count = 0
            for email in lab_team_emails:
                if EmailService._send_email(email, subject, content):
                    sent_count += 1
            
            return {"success": True, "message": f"Rejection notifications sent to {sent_count} team members"}
            
        except Exception as e:
            logger.error(f"Failed to send deviation rejection notifications: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Internal method to send email via SMTP
        Configure SMTP settings in your config file
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = "noreply@nextage-engineering.com"  # Configure in settings
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # For development/testing - just log the email
            # In production, uncomment the SMTP sending code below
            logger.info(f"📧 Email prepared for {to_email}: {subject}")
            
            # TODO: Configure SMTP settings in your config file
            # Uncomment when you have SMTP configured:
            """
            smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_username = getattr(settings, 'SMTP_USERNAME', '')
            smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            """
            
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def get_lab_team_emails() -> List[str]:
        """Get default lab team email addresses"""
        return [
            "lab-manager@nextage-engineering.com",
            "qa-manager@nextage-engineering.com", 
            "calibration-team@nextage-engineering.com"
        ]