#!/usr/bin/env python3
"""
使用 imaplib 直接实现 IMAP ID 命令

根据 163 官方文档和 RFC 2971
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
import imaplib
from src.utils.crypto import PasswordEncryption

# 获取配置
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT email_address, password_encrypted, imap_server, imap_port FROM user_email_configs LIMIT 1')
row = cursor.fetchone()
conn.close()

if not row:
    print("没有找到配置")
    sys.exit(1)

email, encrypted_pwd, imap_server, imap_port = row

# 解密密码
crypto = PasswordEncryption()
password = crypto.decrypt(encrypted_pwd)

print("=" * 60)
print("163 邮箱 IMAP ID 命令测试（imaplib 原生实现）")
print("=" * 60)
print(f"邮箱: {email}")
print(f"服务器: {imap_server}:{imap_port}")
print()

try:
    # 步骤 1: 创建 IMAP SSL 连接
    print("【步骤 1】创建 IMAP SSL 连接...")
    client = imaplib.IMAP4_SSL(imap_server, imap_port)
    print("✓ 连接成功")

    # 读取服务器欢迎消息
    welcome_msg = client.welcome
    print(f"  服务器欢迎消息: {welcome_msg.decode() if isinstance(welcome_msg, bytes) else welcome_msg}")

    # 检查服务器能力
    print("\n【步骤 2】检查服务器能力...")
    capabilities = client.capability()
    print(f"✓ 服务器能力: {capabilities[1]}")

    # 步骤 3: 发送 IMAP ID 命令（在登录之前！）
    print("\n【步骤 3】发送 IMAP ID 命令...")

    # IMAP ID 参数（根据 163 官方文档）
    id_params = {
        "name": "NotionBillImporter",
        "version": "2.2.0",
        "vendor": "CustomClient",
        "support-email": "support@example.com"
    }

    print(f"  ID 参数: {id_params}")

    # 构建 ID 命令参数
    # RFC 2971 格式: ID ("name" "value" "name2" "value2" ...)
    id_args = []
    for key, value in id_params.items():
        id_args.append(f'"{key}"')
        id_args.append(f'"{value}"')

    id_command_str = '(' + ' '.join(id_args) + ')'

    print(f"  ID 命令: ID {id_command_str}")

    # 尝试发送 ID 命令
    try:
        # 方法 1: 使用 ID() 方法（Python 3.5+）
        result, data = client.ID(id_command_str)
        print(f"  结果: {result}")
        print(f"  响应: {data}")

        if result == 'OK':
            print("✓ ID 命令成功")

    except AttributeError:
        print("  当前 Python 版本不支持 ID() 方法")
        print("  尝试使用 xatom...")

        # 方法 2: 使用 xatom
        result, data = client.xatom('ID', id_command_str)
        print(f"  结果: {result}")
        print(f"  响应: {data}")

        if result == 'OK':
            print("✓ ID 命令成功")

    # 步骤 4: 登录
    print("\n【步骤 4】登录邮箱...")
    result, data = client.login(email, password)
    print(f"  结果: {result}")

    if result == 'OK':
        print("✓ 登录成功！")
    else:
        print(f"✗ 登录失败: {data}")
        sys.exit(1)

    # 步骤 5: 测试邮箱操作
    print("\n【步骤 5】测试邮箱操作...")

    # 选择 INBOX
    result, data = client.select('INBOX')
    print(f"  选择 INBOX: {result}")

    if result == 'OK':
        print("✓ 成功选择 INBOX")

        # 获取邮件数量
        result, data = client.search(None, 'ALL')
        if result == 'OK':
            email_count = len(data[0].split()) if data[0] else 0
            print(f"✓ INBOX 中有 {email_count} 封邮件")

    print("\n" + "=" * 60)
    print("🎉 测试成功！163 邮箱连接正常！")
    print("=" * 60)

    # 登出
    client.logout()

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
