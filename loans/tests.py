from django.test import TestCase
from django.contrib.auth import get_user_model

from agent.models import Agent
from customer.models import Customer
from loans.models import (
    LoanType,
    DocumentMaster,
    LoanRequiredDocument,
    LoanApplication,
    LoanDocument,
)

User = get_user_model()


class LoanModelTests(TestCase):

    def setUp(self):
        """
        Create basic test data used in all tests
        """

        # Create user + agent
        self.user = User.objects.create_user(
            username="agent1",
            password="test1234"
        )

        self.agent = Agent.objects.create(
            user=self.user,
            agent_code="AG001",
            mobile="9999999999"
        )

        # Customer
        self.customer = Customer.objects.create(
            first_name="Rahul",
            mobile="8888888888"
        )

        # Loan type
        self.loan_type = LoanType.objects.create(
            name="New Car Loan"
        )

        # Documents
        self.doc1 = DocumentMaster.objects.create(name="Aadhaar Card")
        self.doc2 = DocumentMaster.objects.create(name="PAN Card")

        # Required docs mapping
        LoanRequiredDocument.objects.create(
            loan_type=self.loan_type,
            document=self.doc1
        )
        LoanRequiredDocument.objects.create(
            loan_type=self.loan_type,
            document=self.doc2
        )

    # -----------------------------------------------------
    # TEST 1: Loan type and required docs
    # -----------------------------------------------------
    def test_required_documents_relation(self):
        docs = self.loan_type.required_docs.all()
        self.assertEqual(docs.count(), 2)

    # -----------------------------------------------------
    # TEST 2: Loan application creation
    # -----------------------------------------------------
    def test_create_loan_application(self):
        application = LoanApplication.objects.create(
            agent=self.agent,
            customer=self.customer,
            loan_type=self.loan_type,
            amount=500000
        )

        self.assertEqual(application.status, "draft")
        self.assertEqual(application.loan_type.name, "New Car Loan")

    # -----------------------------------------------------
    # TEST 3: Upload document to loan
    # -----------------------------------------------------
    def test_loan_document_creation(self):
        application = LoanApplication.objects.create(
            agent=self.agent,
            customer=self.customer,
            loan_type=self.loan_type,
            amount=500000
        )

        loan_doc = LoanDocument.objects.create(
            application=application,
            document=self.doc1,
            file="loan_docs/test.pdf"
        )

        self.assertEqual(
            loan_doc.application.customer.first_name,
            "Rahul"
        )
