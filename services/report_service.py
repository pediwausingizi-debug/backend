from utils.pdf_generator import generate_pdf_report
from utils.report_email import build_full_report_email
from utils.email_utils import send_email
import models


def send_reports_to_admins(db, farm_id, farm_name, report_data):
    livestock, crops, financial, inventory = report_data

    # Convert dicts → PDFs
    attachments = {
        "livestock_report.pdf": generate_pdf_report("Livestock Report", livestock),
        "crops_report.pdf": generate_pdf_report("Crops Report", crops),
        "financial_report.pdf": generate_pdf_report("Financial Report", financial),
        "inventory_report.pdf": generate_pdf_report("Inventory Report", inventory)
    }

    email_html = build_full_report_email(
        farm_name,
        livestock,
        crops,
        financial,
        inventory
    )

    admins = db.query(models.User).filter(
        models.User.farm_id == farm_id,
        models.User.role.in_(["Admin", "Manager"])
    ).all()

    for admin in admins:
        send_email(
            to=admin.email,
            subject=f"{farm_name} — Weekly Farm Report",
            html_body=email_html,
            attachments=attachments,
        )
