"""Parser factory with auto-detection."""

from .base_parser import BaseBillParser
from .alipay_parser import AlipayParser
from .wechat_parser import WeChatParser
from .unionpay_parser import UnionPayParser

PARSERS = [AlipayParser, WeChatParser, UnionPayParser]


def get_parser(file_path):
    """Auto-detect bill format and return appropriate parser."""
    import logging
    import pandas as pd
    import os

    logger = logging.getLogger(__name__)
    logger.info(f"Detecting bill format: {file_path}")

    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()

    # Read file content based on format
    content = ""

    if file_ext in ['.xlsx', '.xls']:
        # For Excel files, read with pandas
        try:
            # Try to import required libraries
            if file_ext == '.xlsx':
                import openpyxl
                df = pd.read_excel(file_path, engine='openpyxl', nrows=20, header=None)
            else:  # .xls
                import xlrd
                df = pd.read_excel(file_path, engine='xlrd', nrows=20, header=None)

            # Convert DataFrame to string content for keyword detection
            for idx, row in df.iterrows():
                row_content = ' '.join([str(v) for v in row.values if pd.notna(v)])
                content += row_content + '\n'

                # Early exit if we found enough content
                if idx >= 20:
                    break

        except ImportError as e:
            logger.error(f"Excel support requires additional libraries: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read Excel file {file_path}: {e}")
            return None
    else:
        # For CSV/TXT files, use the original method
        from utils import read_file_lines
        lines = read_file_lines(file_path, 20)
        if not lines:
            logger.error(f"Cannot read file: {file_path}")
            return None
        content = '\n'.join(lines)

    # Detect platform by keywords
    if any(kw in content for kw in ['微信支付账单明细', '微信昵称', '微信号']):
        logger.info("Detected WeChat Pay format")
        return WeChatParser(file_path)

    if any(kw in content for kw in ['支付宝支付科技有限公司', '支付宝账户', '支付宝（中国）网络技术有限公司']):
        logger.info("Detected Alipay format")
        return AlipayParser(file_path)

    if any(kw in content for kw in ['银联', 'unionpay', '中国银联']):
        logger.info("Detected UnionPay format")
        return UnionPayParser(file_path)

    logger.error(f"Cannot detect format: {file_path}")
    logger.error(f"Content preview: {content[:200]}")  # Log first 200 chars for debugging
    return None


def get_parser_by_platform(file_path, platform):
    """Get parser by platform name.

    Supports multiple name formats:
    - Simple: 'alipay', 'wechat', 'unionpay'
    - Full: 'Alipay', 'WeChatPay', 'UnionPay'
    - Chinese: '支付宝', '微信支付', '银联'
    """
    if not platform:
        return None

    # Normalize platform name
    platform_lower = platform.lower().strip()

    # Create mapping with multiple name variants
    mapping = {
        # Alipay variants
        'alipay': AlipayParser,
        '支付宝': AlipayParser,

        # WeChat Pay variants
        'wechat': WeChatParser,
        'wechatpay': WeChatParser,
        '微信': WeChatParser,
        '微信支付': WeChatParser,

        # UnionPay variants
        'unionpay': UnionPayParser,
        '银联': UnionPayParser,
    }

    parser_class = mapping.get(platform_lower)
    if parser_class:
        return parser_class(file_path)

    # If direct mapping failed, try fuzzy matching
    for key, parser_cls in mapping.items():
        if platform_lower in key or key in platform_lower:
            return parser_cls(file_path)

    logger.warning(f"Unsupported platform: {platform}")
    return None
