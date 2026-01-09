"""Parser factory with auto-detection."""

from .base_parser import BaseBillParser
from .alipay_parser import AlipayParser
from .wechat_parser import WeChatParser
from .unionpay_parser import UnionPayParser

PARSERS = [AlipayParser, WeChatParser, UnionPayParser]


def get_parser(file_path):
    """Auto-detect bill format and return appropriate parser."""
    import logging
    from utils import read_file_lines

    logger = logging.getLogger(__name__)
    logger.info(f"Detecting bill format: {file_path}")

    lines = read_file_lines(file_path, 20)
    if not lines:
        logger.error(f"Cannot read file: {file_path}")
        return None

    content = '\n'.join(lines)

    # Detect platform by keywords
    if any(kw in content for kw in ['微信支付账单明细', '微信昵称']):
        logger.info("Detected WeChat Pay format")
        return WeChatParser(file_path)

    if any(kw in content for kw in ['支付宝支付科技有限公司', '支付宝账户']):
        logger.info("Detected Alipay format")
        return AlipayParser(file_path)

    if any(kw in content for kw in ['银联', 'unionpay']):
        logger.info("Detected UnionPay format")
        return UnionPayParser(file_path)

    logger.error(f"Cannot detect format: {file_path}")
    return None


def get_parser_by_platform(file_path, platform):
    """Get parser by platform name."""
    mapping = {
        'alipay': AlipayParser,
        'wechat': WeChatParser,
        'unionpay': UnionPayParser
    }
    parser_class = mapping.get(platform.lower())
    return parser_class(file_path) if parser_class else None
