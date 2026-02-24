"""
Email utility for sending automated reports via SMTP.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from typing import List, Optional
from src.utils.logger import logger


def send_email_with_attachment(
    smtp_server: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    recipient_emails: List[str],
    subject: str,
    body: str,
    attachment_path: Optional[str] = None
) -> bool:
    """
    Send an email with optional attachment via SMTP.
    """
    if not recipient_emails:
        logger.warning("No recipient emails specified, skipping email send")
        return False
    
    logger.info(f"Preparing to send email to {len(recipient_emails)} recipient(s)...")
    
    try:
        # Create message
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = ", ".join(recipient_emails)
        message['Subject'] = Header(subject, 'utf-8')
        
        # Add body
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            filename = os.path.basename(attachment_path)
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                message.attach(part)
            logger.info(f"Attached file: {filename}")
        elif attachment_path:
            logger.warning(f"Attachment not found: {attachment_path}")
        
        # Connect and send
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_emails, message.as_string())
        server.quit()
        
        logger.info(f"✓ Email sent successfully to {len(recipient_emails)} recipient(s)")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to send email: {e}")
        return False
