"""Background scheduler for automated bill imports."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import Config
from src.importer import import_bill
from src.services.email_import_source import EmailImportSource
from src.models import EmailConfig
from datetime import datetime
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

    # Email checking methods

    def add_email_check_job(self, config_id: int, frequency: str = 'hourly'):
        """Add an email check job for a specific email config.

        Args:
            config_id: Email config ID
            frequency: Check frequency ('hourly', 'daily', 'weekly')

        Raises:
            ValueError: If frequency is not supported
        """
        # Map frequency to cron expression
        cron_map = {
            'hourly': '0 * * * *',
            'daily': '0 0 * * *',
            'weekly': '0 0 * * 0'
        }

        cron_expr = cron_map.get(frequency)
        if not cron_expr:
            raise ValueError(f"Unsupported frequency: {frequency}. Use: hourly, daily, or weekly")

        job_id = f"email_check_{config_id}"

        trigger = CronTrigger.from_crontab(cron_expr)

        self.scheduler.add_job(
            func=self._check_email,
            trigger=trigger,
            id=job_id,
            name=f"Email check job for config {config_id}",
            replace_existing=True,
            kwargs={'config_id': config_id}
        )

        logger.info(f"Added email check job for config {config_id} with frequency '{frequency}'")

    def remove_email_check_job(self, config_id: int):
        """Remove an email check job.

        Args:
            config_id: Email config ID
        """
        job_id = f"email_check_{config_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed email check job for config {config_id}")
        except Exception as e:
            logger.debug(f"Email check job for config {config_id} not found or already removed: {e}")

    def get_email_check_jobs(self):
        """Get all email check jobs.

        Returns:
            List of email check job objects
        """
        jobs = self.scheduler.get_jobs()
        return [job for job in jobs if job.id and job.id.startswith('email_check_')]

    def _check_email(self, config_id: int, db=None):
        """Check email and import bills (background job function).

        Args:
            config_id: Email config ID
            db: Database session (optional, for testing)
        """
        from src.services.database import get_db

        # Use provided db or get new session
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True

        try:
            # Get config
            config = db.query(EmailConfig).filter(
                EmailConfig.id == config_id
            ).first()

            if not config:
                logger.warning(f"Email config {config_id} not found")
                return

            logger.info(f"Checking email for config {config_id} ({config.email_address})")

            # Import bills from email
            source = EmailImportSource(config.user_id, db, config_id=config_id)
            result = source.import_bills()

            # Update config status
            config.last_check_at = datetime.utcnow()
            config.last_check_status = 'success' if result['failed'] == 0 else 'partial'

            db.commit()

            logger.info(
                f"Email check completed for config {config_id}: "
                f"{result['imported']} imported, {result['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Email check failed for config {config_id}: {e}", exc_info=True)

            # Try to update status on error
            try:
                config = db.query(EmailConfig).filter(
                    EmailConfig.id == config_id
                ).first()
                if config:
                    config.last_check_at = datetime.utcnow()
                    config.last_check_status = 'failed'
                    db.commit()
            except Exception:
                pass

        finally:
            if close_db:
                db.close()

