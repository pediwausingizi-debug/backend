import os
import resend
from typing import Dict, Optional

resend.api_key = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "FarmXpat <noreply@farmxpat.com>")


def send_email(
    to: str,
    subject: str,
    html_body: str,
    attachments: Optional[Dict[str, bytes]] = None,
):
    payload = {
        "from": EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }

    # Attach PDFs if provided
    if attachments:
        payload["attachments"] = [
            {
                "filename": filename,
                "content": file_bytes,
            }
            for filename, file_bytes in attachments.items()
        ]

    resend.Emails.send(payload)
