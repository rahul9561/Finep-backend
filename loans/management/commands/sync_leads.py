from django.core.management.base import BaseCommand
from loans.services.lead_sync import update_all_pending_leads


class Command(BaseCommand):

    help = "Sync pending leads with PaySprint"

    def handle(self, *args, **kwargs):

        self.stdout.write("Starting lead sync...")

        update_all_pending_leads()

        self.stdout.write(self.style.SUCCESS("Lead sync completed"))