#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
测试微信支付账单解析器（简化版）
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

from parsers.wechat_parser import WeChatParser

def test_wechat_parser(file_path):
    """测试微信支付账单解析器"""
    print(f"测试微信支付账单解析器，文件：{file_path}")
    
    try:
        # 创建解析器实例
        parser = WeChatParser(file_path)
        
        # 解析文件
        print("1. 解析文件...")
        df = parser.parse()
        print(f"   解析成功，数据行数：{len(df)}")
        print(f"   数据列名：{df.columns.tolist()}")
        print(f"   前5行数据：")
        print(df.head())
        
        # 检查是否包含必要字段
        print("2. 检查必要字段...")
        required_fields = ['transaction_time', 'amount']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            print(f"   缺少必要字段：{missing_fields}")
            return False
        else:
            print(f"   所有必要字段都存在：{required_fields}")
        
        # 转换为Notion格式
        print("3. 转换为Notion格式...")
        notion_records = parser.to_notion_format()
        print(f"   转换成功，Notion记录数：{len(notion_records)}")
        if notion_records:
            print(f"   第一条记录：")
            for key, value in notion_records[0].items():
                print(f"     {key}: {value}")
        
        print("\n测试完成，解析器工作正常！")
        return True
        
    except Exception as e:
        print(f"\n测试失败，错误信息：")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python test_wechat_parser_simple.py <微信支付账单文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        sys.exit(1)
    
    success = test_wechat_parser(file_path)
    sys.exit(0 if success else 1)
