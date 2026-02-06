"""Main entry point"""

import argparse
import logging
import os
import sys
from config import Config
from utils import setup_logging
from importer import import_bill, generate_review

setup_logging(Config.LOG_LEVEL, "bill_import.log")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f")
    parser.add_argument("--platform", "-p", choices=["alipay", "wechat", "unionpay"])
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--review", choices=["monthly", "quarterly", "yearly"])
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int, choices=range(1, 13))
    parser.add_argument("--quarter", type=int, choices=range(1, 5))
    parser.add_argument("--user-id", type=int)
    args = parser.parse_args()

    # 复盘生成
    if args.review:
        if not args.year:
            parser.error("--year is required when --review is specified")
        if args.review == "monthly" and not args.month:
            parser.error("--month is required for monthly review")
        if args.review == "quarterly" and not args.quarter:
            parser.error("--quarter is required for quarterly review")

        r = generate_review(args.review, args.year, args.month, args.quarter, args.user_id)
        if r.get("success"):
            logger.info(f"Review generated successfully: {r.get('page_id')}")
            sys.exit(0)
        else:
            logger.error(f"Review generation failed: {r.get('error')}")
            sys.exit(1)

    # 定时任务
    if args.schedule:
        from scheduler import BillScheduler
        BillScheduler().start()
        return

    # 账单导入
    if not args.file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    result = import_bill(args.file, args.platform, args.user_id)
    if result.get("success"):
        logger.info("Import completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Import failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
