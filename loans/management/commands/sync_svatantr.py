# loans/management/commands/sync_svatantr.py

from django.core.management.base import BaseCommand
from loans.svatantr.service import SvatantrSyncService


# class Command(BaseCommand):

#     def handle(self, *args, **kwargs):

#         SvatantrSyncService().sync()

#         print("Svatantr sync done")
        
        
class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        print("SYNC START")

        result = SvatantrSyncService().sync()

        print("RESULT:", result)

        print("SYNC DONE")