"""Main entry point for CLI and scheduler modes."""

import argparse
import logging
import os
import sys
from config import Config
from utils import setup_logging
from importer import import_bill


# Setup logging
setup_logging(Config.LOG_LEVEL, 'bill_import.log')
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import payment bills to Notion")
    parser.add_argument('--file', '-f', type=str, help='Path to bill file')
    parser.add_argument('--platform', '-p', type=str,
                        choices=['alipay', 'wechat', 'unionpay'],
                        help='Bill platform (auto-detected if not specified)')
    parser.add_argument('--schedule', action='store_true',
                        help='Start scheduler as background service')

    args = parser.parse_args()

    if args.schedule:
        from scheduler import BillScheduler
        scheduler = BillScheduler()
        scheduler.start()
        return

    # CLI mode - require file
    if not args.file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    success = import_bill(args.file, args.platform)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
