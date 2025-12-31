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
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"尝试自动检测账单格式: {file_path}")
    
    # 读取文件前20行进行检测
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            lines = [f.readline().strip() for _ in range(20)]
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [f.readline().strip() for _ in range(20)]
        except UnicodeDecodeError:
            logger.error(f"无法读取文件: {file_path}")
            return None
    
    # 合并所有行，方便检测
    content = '\n'.join(lines)
    
    # 检测微信支付账单
    if any(keyword in content for keyword in ['微信支付账单', '微信支付交易明细', '交易时间', '交易类型', '交易对方']):
        logger.info(f"检测到微信支付账单格式")
        return WeChatParser(file_path)
    
    # 检测支付宝账单
    if any(keyword in content for keyword in ['支付宝', 'alipay', '交易时间', '交易对方', '商品名称', '金额（元）']):
        logger.info(f"检测到支付宝账单格式")
        return AlipayParser(file_path)
    
    # 检测银联账单
    if any(keyword in content for keyword in ['银联', 'unionpay', '交易日期', '交易时间', '交易类型', '交易商户']):
        logger.info(f"检测到银联账单格式")
        return UnionPayParser(file_path)
    
    # 如果无法检测，返回None
    logger.error(f"无法检测账单格式: {file_path}")
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
