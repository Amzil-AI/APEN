"""
Email send – acknowledgments and planning (beyond Limova).
Uses SMTP from env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Union


def _smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from": os.environ.get("EMAIL_FROM", ""),
    }


def can_send() -> bool:
    """True if SMTP is configured."""
    c = _smtp_config()
    return bool(c["host"] and c["user"] and c["password"])


def send_email(
    to: Union[str, List[str]],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachment_path: Optional[Path] = None,
    attachment_filename: Optional[str] = None,
) -> bool:
    """Send email. Returns True on success."""
    c = _smtp_config()
    if not c["host"] or not c["user"] or not c["password"]:
        return False
    to_list = [to] if isinstance(to, str) else to
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = c["from"] or c["user"]
    msg["To"] = ", ".join(to_list)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    if attachment_path and attachment_path.exists():
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_path.read_bytes())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_filename or attachment_path.name,
        )
        msg.attach(part)
    try:
        with smtplib.SMTP(c["host"], c["port"]) as s:
            s.starttls()
            s.login(c["user"], c["password"])
            s.sendmail(msg["From"], to_list, msg.as_string())
        return True
    except Exception:
        return False


def make_acknowledgment_body(incoming_subject: str, incoming_from: str) -> str:
    """Personalized acknowledgment text (French)."""
    return (
        f"Bonjour,\n\n"
        f"Nous avons bien reçu votre message concernant : {incoming_subject or 'votre demande'}.\n\n"
        f"Un conseiller APEN vous répondra dans les plus brefs délais.\n\n"
        f"Cordialement,\nL'équipe APEN"
    )
