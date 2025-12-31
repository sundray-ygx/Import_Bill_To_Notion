from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import Config
from parsers import get_parser
from notion_api import NotionClient
import logging
import os
import glob
from datetime import datetime

logger = logging.getLogger(__name__)

class BillScheduler:
    """Bill import scheduler"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = BackgroundScheduler()
        self.config = Config
    
    def start(self):
        """Start the scheduler"""
        try:
            if not self.config.SCHEDULER_ENABLED:
                logger.info("Scheduler is disabled in config")
                return
            
            # Add cron job
            trigger = CronTrigger.from_crontab(self.config.SCHEDULER_CRON)
            self.scheduler.add_job(
                func=self.auto_import_bills,
                trigger=trigger,
                id="bill_import_job",
                name="Bill import job",
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            logger.info(f"Scheduler started with cron: {self.config.SCHEDULER_CRON}")
            
            # Keep the scheduler running
            print("Bill import scheduler started. Press Ctrl+C to exit.")
            try:
                # This is here to simulate application activity (which keeps the main thread alive).
                while True:
                    pass
            except (KeyboardInterrupt, SystemExit):
                # Not strictly necessary if daemonic mode is enabled but should be done if possible
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def restart(self):
        """Restart the scheduler"""
        self.stop()
        self.start()
    
    def auto_import_bills(self):
        """Automatically import bills from default directory"""
        logger.info("Starting auto import...")
        
        try:
            # Get default bill directory
            bill_dir = self.config.DEFAULT_BILL_DIR
            
            # Create directory if it doesn't exist
            if not os.path.exists(bill_dir):
                logger.warning(f"Default bill directory not found: {bill_dir}")
                return
            
            # Find all CSV files in the directory
            csv_files = glob.glob(os.path.join(bill_dir, "*.csv"))
            if not csv_files:
                logger.info(f"No CSV files found in: {bill_dir}")
                return
            
            # Get the latest file by modification time
            latest_file = max(csv_files, key=os.path.getmtime)
            logger.info(f"Found latest bill file: {latest_file}")
            
            # Try to parse and import the file
            self.import_single_file(latest_file)
            
        except Exception as e:
            logger.error(f"Auto import failed: {e}", exc_info=True)
    
    def import_single_file(self, file_path):
        """Import a single bill file"""
        try:
            # Get parser - auto-detect
            parser = get_parser(file_path)
            if not parser:
                logger.error(f"Failed to detect format for file: {file_path}")
                return False
            
            logger.info(f"Using {parser.get_platform()} parser for file: {file_path}")
            
            # Parse bill file
            notion_records = parser.to_notion_format()
            logger.info(f"Parsed {len(notion_records)} records from {file_path}")
            
            # Import to Notion
            notion_client = NotionClient()
            
            # Verify Notion connection
            if not notion_client.verify_connection():
                logger.error("Failed to connect to Notion")
                return False
            
            # Batch import
            result = notion_client.batch_import(notion_records)
            
            logger.info(f"Auto import completed successfully for {file_path}!")
            logger.info(f"Imported: {result['imported']} records")
            logger.info(f"Updated: {result['updated']} records")
            logger.info(f"Skipped: {result['skipped']} records")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import file {file_path}: {e}", exc_info=True)
            return False
    
    def get_next_run_time(self):
        """Get the next run time of the job"""
        job = self.scheduler.get_job("bill_import_job")
        if job:
            return job.next_run_time
        return None
    
    def get_job_status(self):
        """Get the status of the scheduler"""
        return {
            "running": self.scheduler.running,
            "enabled": self.config.SCHEDULER_ENABLED,
            "cron": self.config.SCHEDULER_CRON,
            "next_run": self.get_next_run_time()
        }
