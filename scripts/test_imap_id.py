#!/usr/bin/env python3
"""
测试发送 IMAP ID 命令到 163 邮箱

根据 163 官方文档和 RFC 2971，IMAP ID 命令用于客户端标识
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from imap_tools import MailBox
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
print("163 邮箱 IMAP ID 命令测试")
print("=" * 60)
print(f"邮箱: {email}")
print(f"服务器: {imap_server}:{imap_port}")
print()

try:
    # 创建 MailBox 对象
    print("【步骤 1】创建 IMAP 连接...")
    mailbox = MailBox(imap_server, imap_port)

    # 登录
    print("【步骤 2】登录邮箱...")
    mailbox.login(email, password)
    print("✓ 登录成功")

    # 获取底层的 imaplib 客户端
    print("【步骤 3】获取底层 imaplib 客户端...")
    client = mailbox.client
    print(f"✓ 客户端类型: {type(client).__name__}")

    # 发送 IMAP ID 命令
    print("\n【步骤 4】发送 IMAP ID 命令...")

    # IMAP ID 参数（根据 163 官方文档）
    # RFC 2971 定义 ID 命令格式
    id_params = {
        "name": "NotionBillImporter",
        "version": "2.2.0",
        "vendor": "CustomClient",
        "support-email": "support@example.com",
        "os": "Python",
        "os-version": sys.version.split()[0]
    }

    print(f"  ID 参数: {id_params}")

    # 构建并发送 ID 命令
    # IMAP ID 命令格式: ID ("name" "value" "name2" "value2" ...)
    # 或者使用 NIL 表示没有值

    # 方法 1: 尝试直接使用 ID 命令（如果 Python 版本支持）
    try:
        # Python 3.5+ 的 imaplib 可能支持
        result, data = client.ID(
            f'("name" "{id_params["name"]}" '
            f'"version" "{id_params["version"]}" '
            f'"vendor" "{id_params["vendor"]}" '
            f'"support-email" "{id_params["support-email"]}")'
        )
        print(f"  方法 1 结果: {result} {data}")
    except AttributeError:
        print("  方法 1 不可用（当前 Python 版本不支持 client.ID()）")

        # 方法 2: 使用 xatom 发送自定义命令
        print("\n  尝试方法 2: 使用 xatom 发送 ID 命令...")

        # IMAP ID 命令格式
        id_command = f'ID ("name" "{id_params["name"]}" "version" "{id_params["version"]}" "vendor" "{id_params["vendor"]}" "support-email" "{id_params["support_email"]}")'

        result, data = client.xatom('ID', f'("name" "{id_params["name"]}" "version" "{id_params["version"]}" "vendor" "{id_params["vendor"]}" "support-email" "{id_params["support_email"]}")')

        print(f"  方法 2 结果: {result}")
        print(f"  服务器响应: {data}")

    # 测试选择邮箱（验证连接是否正常）
    print("\n【步骤 5】测试邮箱操作...")
    mailbox.folder.set('INBOX')
    print(f"✓ 成功选择 INBOX")

    # 列出邮件数量
    messages = list(mailbox.fetch(limit=1))
    print(f"✓ INASET 中有 {len(messages)} 封邮件（显示前1封）")

    print("\n" + "=" * 60)
    print("🎉 测试成功！IMAP ID 命令发送成功！")
    print("=" * 60)

    # 登出
    mailbox.logout()

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
