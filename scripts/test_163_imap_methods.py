#!/usr/bin/env python3
"""
测试不同的 163 邮箱 IMAP 连接方式
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
print("163 邮箱 IMAP 连接方式测试")
print("=" * 60)
print(f"邮箱: {email}")
print(f"密码长度: {len(password)}")
print(f"密码: {password[:4]}...{password[-4:]}")
print()

# 方法 1: 标准 IMAPS (端口 993)
print("【方法 1】标准 IMAPS 连接 (端口 993)")
print("-" * 60)
try:
    with MailBox(imap_server, 993).login(email, password) as mailbox:
        print("✓ 方法 1 成功！")
        mailbox.logout()
        sys.exit(0)
except Exception as e:
    print(f"✗ 方法 1 失败: {e}")

# 方法 2: 显式使用 SSL 上下文
print("\n【方法 2】使用 SSL 上下文")
print("-" * 60)
try:
    import ssl
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with MailBox(imap_server, 993, ssl_context=context).login(email, password) as mailbox:
        print("✓ 方法 2 成功！")
        mailbox.logout()
        sys.exit(0)
except Exception as e:
    print(f"✗ 方法 2 失败: {e}")

# 方法 3: 尝试端口 143 (非加密)
print("\n【方法 3】尝试端口 143 (STARTTLS)")
print("-" * 60)
try:
    with MailBox(imap_server, 143).login(email, password) as mailbox:
        print("✓ 方法 3 成功！")
        mailbox.logout()
        sys.exit(0)
except Exception as e:
    print(f"✗ 方法 3 失败: {e}")

# 方法 4: 尝试使用不同的登录顺序
print("\n【方法 4】手动连接流程")
print("-" * 60)
try:
    mailbox = MailBox(imap_server, 993)
    mailbox.login(email, password)
    print("✓ 方法 4 成功！")
    mailbox.logout()
    sys.exit(0)
except Exception as e:
    print(f"✗ 方法 4 失败: {e}")

print("\n" + "=" * 60)
print("所有连接方法都失败了")
print("=" * 60)
print("\n这表明问题不在代码，而在于:")
print("1. IMAP 服务确实未开启")
print("2. 授权码已过期或不正确")
print("3. 163 邮箱账户有其他限制")
print("\n请检查:")
print("- 登录 163 邮箱网页版")
print("- 设置 → POP3/SMTP/IMAP")
print("- 确认 'IMAP/SMTP 服务' 显示为 '已开启'")
print("- 重新生成授权码")
print("=" * 60)
