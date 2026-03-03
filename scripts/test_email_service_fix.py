#!/usr/bin/env python3
"""
测试更新后的 EmailService 与 163 邮箱连接
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.services.email_service import EmailService
from src.models import EmailConfig
import sqlite3

# 获取配置
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()
cursor.execute('''
    SELECT id, email_address, password_encrypted,
           imap_server, imap_port, use_ssl,
           config_name, provider, check_frequency
    FROM user_email_configs
    LIMIT 1
''')
row = cursor.fetchone()
conn.close()

if not row:
    print("没有找到配置")
    sys.exit(1)

config_id, email, encrypted_pwd, imap_server, imap_port, use_ssl, config_name, provider, check_frequency = row

print("=" * 60)
print("测试 EmailService IMAP ID 修复")
print("=" * 60)
print(f"邮箱: {email}")
print(f"服务器: {imap_server}:{imap_port}")
print()

# 创建 EmailConfig 对象
config = EmailConfig(
    id=config_id,
    email_address=email,
    password_encrypted=encrypted_pwd,
    imap_server=imap_server,
    imap_port=imap_port,
    use_ssl=bool(use_ssl),
    config_name=config_name,
    provider=provider,
    check_frequency=check_frequency
)

try:
    # 创建 EmailService 实例
    service = EmailService()

    # 测试连接
    print("【测试 1】测试邮箱连接...")
    mailbox = service.connect(config)
    print("✓ 连接成功！")

    # 测试邮箱操作
    print("\n【测试 2】测试邮箱操作...")

    # 获取邮箱列表
    folders = mailbox.folder.list()
    print(f"✓ 找到 {len(folders)} 个邮箱")

    # 选择 INBOX
    mailbox.folder.set('INBOX')
    print("✓ 成功选择 INBOX")

    # 获取邮件
    emails = list(mailbox.fetch(limit=5))
    print(f"✓ 获取到 {len(emails)} 封邮件")

    if emails:
        print(f"\n最新邮件主题:")
        for i, msg in enumerate(emails, 1):
            print(f"  {i}. {msg.subject}")

    # 断开连接
    service.disconnect(mailbox)
    print("\n✓ 已断开连接")

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
    print()
    print("修复验证:")
    print("✓ IMAP ID 命令已成功发送")
    print("✓ 163 邮箱连接正常")
    print("✓ Unsafe Login 错误已解决")

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
