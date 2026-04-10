from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_loan_application_email(application):


    subject = "Loan Application Submitted Successfully"

    context = {
        "customer": application.customer.first_name,
        "loan_type": application.loan_type.name,
        "amount": application.amount,
        "status": application.status,
    }

    html_content = render_to_string(
        "emails/loan_application_submitted.html",
        context
    )

    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [application.customer.email]
    )

    msg.attach_alternative(html_content, "text/html")
    msg.send()



import os


def send_document_uploaded_email(document):

    application = document.application

    subject = f"Document Uploaded - {document.document_type.name}"

    context = {
        "customer": application.customer.first_name,
        "loan_type": application.loan_type.name,
        "document_type": document.document_type.name,
    }

    html_content = render_to_string(
        "emails/document_uploaded.html",
        context
    )

    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [application.customer.email]
    )

    msg.attach_alternative(html_content, "text/html")

    # 🔥 Attach File
    if document.file:
        msg.attach_file(document.file.path)

    msg.send()