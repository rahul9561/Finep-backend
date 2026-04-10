import os


def education_upload_path(instance, filename):

    loan_type = "unknown"
    student_name = "unknown"
    model_name = instance.__class__.__name__.lower()

    if instance.application:
        loan_type = instance.application.loan_type or "unknown"
        student_name = instance.application.name or "unknown"

    student_name = student_name.replace(" ", "_")

    return os.path.join(
        "educations",
        loan_type,
        student_name,
        model_name,
        filename,
    )
    
    
# utils.py
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_loan_application_email(loan_obj, agent, student):
    """
    Renders the HTML template and sends the notification email.
    """
    subject = "New Education Loan Lead"
    to_email = ["avmanagementpatiala23@gmail.com"] # Consider moving this to settings.py
    
    # Pass data to the HTML template
    context = {
        "loan": loan_obj,
        "agent": agent,
        "student": student
    }
    
    try:
        html_content = render_to_string("emails/new_loan_lead.html", context)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="A new education loan lead has been submitted. Please view this email in an HTML-compatible client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_email,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
    except Exception as e:
        # Using logger is more professional than print() in production
        logger.error(f"Failed to send loan application email: {e}", exc_info=True)