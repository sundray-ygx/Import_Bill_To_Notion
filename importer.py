import logging
from config import Config
from parsers import get_parser, get_parser_by_platform
from notion_api import NotionClient
import os

logger = logging.getLogger(__name__)

def import_bill(file_path, platform=None):
    """Import bill file to Notion"""
    try:
        # Validate configuration
        Config.validate()
        
        # Get parser - auto-detect if platform not specified
        if platform:
            parser = get_parser_by_platform(file_path, platform)
            if not parser:
                logger.error(f"Unsupported platform: {platform}")
                return False
        else:
            parser = get_parser(file_path)
            if not parser:
                logger.error("Failed to detect bill format. Please specify platform explicitly.")
                return False
        
        logger.info(f"Using {parser.get_platform()} parser")
        
        # Parse bill file
        logger.info(f"Parsing bill file: {file_path}")
        notion_records = parser.to_notion_format()
        logger.info(f"Parsed {len(notion_records)} records")
        
        # Import to Notion
        logger.info("Importing records to Notion...")
        notion_client = NotionClient()
        
        # Verify Notion connection
        if not notion_client.verify_connection():
            logger.error("Failed to connect to Notion. Please check your API key and database ID.")
            return False
        
        # Batch import
        result = notion_client.batch_import(notion_records)
        
        # Print import result
        logger.info(f"Import completed successfully!")
        logger.info(f"Imported: {result['imported']} records")
        logger.info(f"Updated: {result['updated']} records")
        logger.info(f"Skipped: {result['skipped']} records")
        
        return True
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return False