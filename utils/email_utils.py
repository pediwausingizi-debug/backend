import os
import base64
import resend
from typing import Dict, Optional


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "FarmXpat <noreply@farmxpat.com>")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_email(
    to: str,
    subject: str,
    html_body: Optional[str] = None,
    body: Optional[str] = None,
    attachments: Optional[Dict[str, bytes]] = None,
):
    """
    Send email using Resend.

    Supports both:
    - html_body="..."
    - body="..."

    This prevents crashes from older calls in reports.py.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    if not to:
        raise ValueError("Recipient email is required")

    final_html = html_body or body or ""

    if not final_html:
        final_html = "FarmXpat notification"

    payload = {
        "from": EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": final_html.replace("\n", "<br />"),
    }

    if attachments:
        payload["attachments"] = [
            {
                "filename": filename,
                "content": base64.b64encode(file_bytes).decode("utf-8"),
            }
            for filename, file_bytes in attachments.items()
        ]

    return resend.Emails.send(payload)