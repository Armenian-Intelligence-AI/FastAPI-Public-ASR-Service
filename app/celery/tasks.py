from .celery import celery_app
from app.utils.smtp_client import SMTPClient
from app.core.config import settings

@celery_app.task
def send_email_confirmation_otp_email(email, otp):
    smtp_client = SMTPClient(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        mail_from='noreply@fastbank.am'
    )
    html_body = f"""
    <html>
      <body>
        <h2>Welcome to FastBank - Speech To Text</h2>
        <p>Your OTP is: <strong>{otp}</strong></p>
        <p>This OTP will expire in 5 minutes.</p>
      </body>
    </html>
    """
    smtp_client.send_email(
        subject="Your FastBank - Speech To Text OTP",
        body=f"Your OTP is {otp}",
        recipients=[email],
        html_body=html_body
    )

@celery_app.task
def send_password_reset_otp_email(email, otp):
    smtp_client = SMTPClient(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        mail_from='noreply@fastbank.am'
    )
    html_body = f"""
    <html>
      <body>
        <h2>Your FastBank - Speech To Text Password Reset OTP</h2>
        <p>Your OTP is: <strong>{otp}</strong></p>
        <p>This OTP will expire in 5 minutes.</p>
        <p>Thank you for registering!</p>
      </body>
    </html>
    """
    smtp_client.send_email(
        subject="Your FastBank - Speech To Text OTP",
        body=f"Your OTP is {otp}",
        recipients=[email],
        html_body=html_body
    )

@celery_app.task
def send_password_reset_otp_email(email, otp):
    smtp_client = SMTPClient(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        mail_from='noreply@fastbank.am'
    )
    html_body = f"""
    <html>
      <body>
        <h2>Your FastBank - Speech To Text Password Reset OTP</h2>
        <p>Your OTP is: <strong>{otp}</strong></p>
        <p>This OTP will expire in 5 minutes.</p>
        <p>Thank you for registering!</p>
      </body>
    </html>
    """
    smtp_client.send_email(
        subject="Your FastBank - Speech To Text OTP",
        body=f"Your OTP is {otp}",
        recipients=[email],
        html_body=html_body
    )
