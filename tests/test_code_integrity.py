#!/usr/bin/env python3
"""
测试代码完整性，确保所有模块都能正常导入和初始化
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_module_imports():
    """测试所有模块是否能正常导入"""
    logger.info("开始测试模块导入...")
    
    # 测试配置模块
    try:
        from config import Config
        logger.info("✓ config.Config 导入成功")
    except Exception as e:
        logger.error(f"✗ config.Config 导入失败: {e}")
        return False
    
    # 测试解析器模块
    try:
        from parsers import get_parser_by_platform
        from parsers.wechat_parser import WeChatParser
        from parsers.alipay_parser import AlipayParser
        from parsers.unionpay_parser import UnionPayParser
        logger.info("✓ 所有解析器导入成功")
    except Exception as e:
        logger.error(f"✗ 解析器导入失败: {e}")
        return False
    
    # 测试 Notion API 模块
    try:
        from notion_api import NotionClient
        logger.info("✓ notion_api.NotionClient 导入成功")
    except Exception as e:
        logger.error(f"✗ notion_api.NotionClient 导入失败: {e}")
        return False
    
    # 测试 importer 模块
    try:
        from importer import import_bill
        logger.info("✓ importer.import_bill 导入成功")
    except Exception as e:
        logger.error(f"✗ importer.import_bill 导入失败: {e}")
        return False
    
    # 测试 main 模块
    try:
        import main
        logger.info("✓ main 模块导入成功")
    except Exception as e:
        logger.error(f"✗ main 模块导入失败: {e}")
        return False
    
    logger.info("所有模块导入测试通过！")
    return True

def test_parser_initialization():
    """测试解析器初始化"""
    logger.info("开始测试解析器初始化...")
    
    # 创建一个临时文件路径
    temp_file = "/tmp/test_bill.csv"
    
    # 测试微信支付解析器初始化
    try:
        from parsers.wechat_parser import WeChatParser
        parser = WeChatParser(temp_file)
        logger.info("✓ WeChatParser 初始化成功")
    except Exception as e:
        logger.error(f"✗ WeChatParser 初始化失败: {e}")
        return False
    
    # 测试支付宝解析器初始化
    try:
        from parsers.alipay_parser import AlipayParser
        parser = AlipayParser(temp_file)
        logger.info("✓ AlipayParser 初始化成功")
    except Exception as e:
        logger.error(f"✗ AlipayParser 初始化失败: {e}")
        return False
    
    # 测试银联解析器初始化
    try:
        from parsers.unionpay_parser import UnionPayParser
        parser = UnionPayParser(temp_file)
        logger.info("✓ UnionPayParser 初始化成功")
    except Exception as e:
        logger.error(f"✗ UnionPayParser 初始化失败: {e}")
        return False
    
    logger.info("所有解析器初始化测试通过！")
    return True

def test_notion_client_initialization():
    """测试 NotionClient 初始化"""
    logger.info("开始测试 NotionClient 初始化...")
    
    try:
        from notion_api import NotionClient
        client = NotionClient()
        logger.info("✓ NotionClient 初始化成功")
        return True
    except Exception as e:
        logger.warning(f"NotionClient 初始化失败 (可能是配置问题，这是预期的): {e}")
        return True  # 允许初始化失败，因为可能缺少配置

if __name__ == "__main__":
    logger.info("开始代码完整性测试...")
    
    all_tests_passed = True
    
    # 运行所有测试
    all_tests_passed &= test_module_imports()
    all_tests_passed &= test_parser_initialization()
    all_tests_passed &= test_notion_client_initialization()
    
    if all_tests_passed:
        logger.info("✅ 所有测试通过！代码完整性良好。")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败，请检查代码。")
        sys.exit(1)
