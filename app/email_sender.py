"""
email_sender.py - SMTP email sender (mock mode for dev)
In production you'd configure real SMTP credentials.
For now it just logs the email details and saves a .eml-like file to output/.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

# load .env if it exists
load_dotenv()


def get_smtp_config():
    """Pull SMTP settings from environment variables."""
    return {
        'host': os.getenv('SMTP_HOST', 'smtp.example.com'),
        'port': int(os.getenv('SMTP_PORT', '587')),
        'user': os.getenv('SMTP_USER', 'reports@example.com'),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'default_recipient': os.getenv('DEFAULT_RECIPIENT', 'manager@example.com'),
    }


def build_email(recipient, subject, body_html, attachment_path=None):
    """Build a MIME email message with optional attachment."""
    cfg = get_smtp_config()

    msg = MIMEMultipart()
    msg['From'] = cfg['user']
    msg['To'] = recipient
    msg['Subject'] = subject
    msg['X-Generator'] = 'SheetSync v1.0'

    # html body
    msg.attach(MIMEText(body_html, 'html'))

    # attach report file if provided
    if attachment_path and os.path.exists(attachment_path):
        filename = os.path.basename(attachment_path)
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)
        print(f"  Attached: {filename}")

    return msg


def send_email(recipient, subject, body_html, attachment_path=None, mock=True):
    """
    Send an email. If mock=True (default), just log it and save to disk.
    Set mock=False and configure SMTP env vars for real sending.
    """
    cfg = get_smtp_config()

    if not recipient:
        recipient = cfg['default_recipient']

    print(f"\n[Email] Preparing email...")
    print(f"  To: {recipient}")
    print(f"  Subject: {subject}")
    print(f"  From: {cfg['user']}")

    msg = build_email(recipient, subject, body_html, attachment_path)

    if mock:
        # mock mode — save the email to a file instead of sending
        print(f"  Mode: MOCK (not actually sending)")
        output_dir = os.getenv('OUTPUT_DIR', './output')
        os.makedirs(output_dir, exist_ok=True)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        email_file = os.path.join(output_dir, f"email_{ts}.eml")

        with open(email_file, 'w') as f:
            f.write(msg.as_string())

        print(f"  Saved mock email: {email_file}")
        print(f"  [OK] Email would have been sent to {recipient}")
        return email_file
    else:
        # real SMTP sending
        print(f"  Mode: LIVE (connecting to {cfg['host']}:{cfg['port']})")
        try:
            with smtplib.SMTP(cfg['host'], cfg['port'], timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if cfg['password']:
                    server.login(cfg['user'], cfg['password'])
                server.send_message(msg)
            print(f"  [OK] Email sent successfully to {recipient}")
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to send email: {e}")
            return False


def send_report(report_path, recipient=None, report_type='monthly'):
    """
    Convenience function: send a generated report as an email attachment.
    Builds a nice subject line and simple HTML body.
    """
    ts = datetime.now().strftime('%B %d, %Y')
    subject = f"SheetSync {report_type.capitalize()} Report - {ts}"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Your {report_type.capitalize()} Report is Ready</h2>
        <p>Hi,</p>
        <p>Please find your <strong>{report_type} report</strong> attached to this email.</p>
        <p>Generated on {ts} by SheetSync.</p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="font-size: 12px; color: #999;">
            This is an automated email from SheetSync reporting tool.
        </p>
    </body>
    </html>
    """

    return send_email(recipient, subject, body, attachment_path=report_path, mock=True)
