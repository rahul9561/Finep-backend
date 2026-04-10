from celery import shared_task
from loans.svatantr.service import SvatantrSyncService


@shared_task(bind=True)
def sync_svatantr(self):

    print("===== SYNC START =====")

    try:

        result = SvatantrSyncService().sync()

        print("SYNC RESULT:", result)

        print("===== SYNC DONE =====")

        return result

    except Exception as e:

        print("SYNC ERROR:", str(e))

        raise e