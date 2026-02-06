#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
测试微信支付账单解析器
"""

import sys
import os
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.wechat_parser import WeChatParser

def test_wechat_parser(file_path):
    """测试微信支付账单解析器"""
    print(f"测试微信支付账单解析器，文件：{file_path}")
    
    try:
        # 创建解析器实例
        parser = WeChatParser(file_path)
        
        # 验证文件格式
        print("1. 验证文件格式...")
        is_valid = parser.validate_file()
        print(f"   文件格式验证结果：{is_valid}")
        
        if not is_valid:
            # 尝试直接解析，查看详细错误
            print("2. 尝试直接解析文件...")
            # 手动检查文件内容
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 尝试不同编码
            encodings = ['gbk', 'utf-8', 'gb2312']
            for encoding in encodings:
                try:
                    decoded_content = content.decode(encoding)
                    print(f"   编码 {encoding} 成功")
                    lines = decoded_content.split('\n')
                    print(f"   文件总行数：{len(lines)}")
                    
                    # 打印前20行，查看文件结构
                    print("   文件前20行：")
                    for i, line in enumerate(lines[:20]):
                        print(f"   {i+1:2d}: {line}")
                    
                    # 尝试直接用pandas读取
                    print("   尝试用pandas读取...")
                    for skip_rows in range(15, 18):
                        try:
                            df = pd.read_csv(
                                file_path, 
                                encoding=encoding,
                                skiprows=skip_rows,
                                header=0,
                                nrows=10
                            )
                            print(f"   skiprows={skip_rows} 成功，列名：{df.columns.tolist()}")
                            print(f"   前5行数据：")
                            print(df.head())
                        except Exception as e:
                            print(f"   skiprows={skip_rows} 失败：{e}")
                    break
                except UnicodeDecodeError:
                    print(f"   编码 {encoding} 失败")
            return
        
        # 解析文件
        print("2. 解析文件...")
        df = parser.parse()
        print(f"   解析成功，数据行数：{len(df)}")
        print(f"   数据列名：{df.columns.tolist()}")
        print(f"   前5行数据：")
        print(df.head())
        
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
        print("用法：python test_wechat_parser.py <微信支付账单文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        sys.exit(1)
    
    test_wechat_parser(file_path)
