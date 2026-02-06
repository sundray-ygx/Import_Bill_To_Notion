#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
测试微信支付账单导入功能
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from src.importer import import_bill

def test_import(file_path, platform=None):
    """测试账单导入功能"""
    logger.info(f"开始测试账单导入，文件：{file_path}")
    
    try:
        success = import_bill(file_path, platform)
        logger.info(f"导入结果：{success}")
        return success
    except Exception as e:
        logger.error(f"导入失败，错误信息：")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python test_import.py <账单文件路径> [平台]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        sys.exit(1)
    
    success = test_import(file_path, platform)
    sys.exit(0 if success else 1)
