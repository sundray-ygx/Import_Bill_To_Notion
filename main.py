import argparse
import logging
import sys
from config import Config
import os

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bill_import.log', encoding='utf-8')
    ]
)

# 设置日志时区为北京时间
import logging.handlers
import time
import datetime

# 创建一个Formatter，使用北京时间
class BeijingFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # 获取UTC时间，然后转换为北京时间（UTC+8）
        dt = datetime.datetime.utcfromtimestamp(record.created) + datetime.timedelta(hours=8)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

# 重新配置日志，使用北京时间
for handler in logging.getLogger().handlers:
    handler.setFormatter(BeijingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

logger = logging.getLogger(__name__)

from importer import import_bill

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Import payment bills to Notion")
    parser.add_argument('--file', '-f', type=str, help='Path to bill file')
    parser.add_argument('--platform', '-p', type=str, choices=['alipay', 'wechat', 'unionpay'],
                        help='Bill platform (optional, auto-detected if not specified)')
    parser.add_argument('--schedule', action='store_true', help='Start scheduler as background service')
    
    args = parser.parse_args()
    
    # Check if we need to run scheduler
    if args.schedule:
        from scheduler import BillScheduler
        scheduler = BillScheduler()
        scheduler.start()
        return
    
    # Command line mode - require file path
    if not args.file:
        parser.print_help()
        sys.exit(1)
    
    # Check if file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # Run import
    success = import_bill(args.file, args.platform)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
