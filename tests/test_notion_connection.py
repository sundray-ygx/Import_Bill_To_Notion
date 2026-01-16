#!/usr/bin/env python3
"""
测试Notion API连接
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from config import Config
from notion_client import Client as NotionApiClient

def test_notion_connection():
    """测试Notion API连接"""
    logger.info("开始测试Notion API连接...")
    
    try:
        # 加载配置
        Config.validate()
        logger.info("配置验证成功")
        
        # 初始化Notion客户端
        notion_client = NotionApiClient(auth=Config.NOTION_API_KEY)
        logger.info("Notion客户端初始化成功")
        
        # 测试API密钥有效性
        logger.info("测试API密钥有效性...")
        user_info = notion_client.users.me()
        logger.info(f"API密钥有效，当前用户: {user_info.get('name', '未知')}")
        
        # 测试数据库访问
        logger.info(f"测试数据库访问，数据库ID: {Config.NOTION_DATABASE_ID}")
        database_info = notion_client.databases.retrieve(database_id=Config.NOTION_DATABASE_ID)
        logger.info(f"成功访问数据库，响应内容: {list(database_info.keys())}")
        
        # 检查数据库响应结构
        if "properties" in database_info:
            logger.info(f"数据库包含 {len(database_info['properties'])} 个属性")
            logger.info(f"属性列表: {list(database_info['properties'].keys())}")
        else:
            logger.error(f"数据库响应中没有 'properties' 字段")
            return False
        
        logger.info("Notion API连接测试成功")
        return True
        
    except Exception as e:
        logger.error(f"Notion API连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_notion_connection()
    sys.exit(0 if success else 1)
