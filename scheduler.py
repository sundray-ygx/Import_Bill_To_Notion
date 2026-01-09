"""Background scheduler for automated bill imports."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import Config
from importer import import_bill
import logging
import os
import glob


logger = logging.getLogger(__name__)


class BillScheduler:
    """Bill import scheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start the scheduler."""
        if not Config.SCHEDULER_ENABLED:
            logger.info("Scheduler disabled in config")
            return

        trigger = CronTrigger.from_crontab(Config.SCHEDULER_CRON)
        self.scheduler.add_job(
            func=self.auto_import_bills,
            trigger=trigger,
            id="bill_import_job",
            name="Bill import job",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started with cron: {Config.SCHEDULER_CRON}")

        try:
            while True:
                pass
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def restart(self):
        """Restart the scheduler."""
        self.stop()
        self.start()

    def auto_import_bills(self):
        """Automatically import bills from default directory."""
        logger.info("Starting auto import...")

        try:
            bill_dir = Config.DEFAULT_BILL_DIR
            if not os.path.exists(bill_dir):
                logger.warning(f"Bill directory not found: {bill_dir}")
                return

            csv_files = glob.glob(os.path.join(bill_dir, "*.csv"))
            if not csv_files:
                logger.info(f"No CSV files in: {bill_dir}")
                return

            latest_file = max(csv_files, key=os.path.getmtime)
            logger.info(f"Found latest file: {latest_file}")

            import_bill(latest_file)

        except Exception as e:
            logger.error(f"Auto import failed: {e}", exc_info=True)

    def get_next_run_time(self):
        """Get next scheduled run time."""
        job = self.scheduler.get_job("bill_import_job")
        return job.next_run_time if job else None

    def get_job_status(self):
        """Get scheduler status."""
        return {
            "running": self.scheduler.running,
            "enabled": Config.SCHEDULER_ENABLED,
            "cron": Config.SCHEDULER_CRON,
            "next_run": self.get_next_run_time()
        }
