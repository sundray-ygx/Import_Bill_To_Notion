from .base_parser import BaseBillParser
from .alipay_parser import AlipayParser
from .wechat_parser import WeChatParser
from .unionpay_parser import UnionPayParser

# List of all available parsers
PARSERS = [
    AlipayParser,
    WeChatParser,
    UnionPayParser
]

def get_parser(file_path):
    """Auto-detect the bill format and return the appropriate parser"""
    # Auto-detection is not supported anymore, use get_parser_by_platform instead
    return None

def get_parser_by_platform(file_path, platform):
    """Get parser by platform name"""
    platform_mapping = {
        'alipay': AlipayParser,
        'wechat': WeChatParser,
        'unionpay': UnionPayParser
    }
    
    parser_class = platform_mapping.get(platform.lower())
    if parser_class:
        return parser_class(file_path)
    return None
