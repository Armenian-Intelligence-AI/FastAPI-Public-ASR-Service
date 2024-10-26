import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

class SMTPClient:
    def __init__(self, smtp_server, smtp_port, username, password, mail_from):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.mail_from = mail_from

    def send_email(self, subject, body, recipients, html_body=None, attachments=None):
        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = self.mail_from
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        # Attach plain text body
        msg.attach(MIMEText(body, 'plain'))

        # Attach HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Attach files
        if attachments:
            for file_path in attachments:
                part = MIMEBase('application', 'octet-stream')
                with open(file_path, 'rb') as attachment:
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                msg.attach(part)

        # Send the email via SMTP
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.mail_from, recipients, msg.as_string())
