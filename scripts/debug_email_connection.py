#!/usr/bin/env python3
"""
邮箱连接调试脚本

用于诊断 163 邮箱 IMAP 连接问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from imap_tools import MailBox
from src.utils.crypto import PasswordEncryption

print("=" * 60)
print("邮箱连接诊断工具")
print("=" * 60)

# 步骤 1: 检查环境变量
print("\n【步骤 1】检查环境变量")
print("-" * 60)
key = os.getenv('PASSWORD_ENCRYPTION_KEY')
if key:
    print(f"✓ PASSWORD_ENCRYPTION_KEY 存在 (长度: {len(key)})")
else:
    print("✗ PASSWORD_ENCRYPTION_KEY 不存在")
    sys.exit(1)

# 步骤 2: 测试密码加密解密
print("\n【步骤 2】测试密码加密解密")
print("-" * 60)
try:
    crypto = PasswordEncryption()
    test_password = "TEST123456789012"
    encrypted = crypto.encrypt(test_password)
    decrypted = crypto.decrypt(encrypted)
    if decrypted == test_password:
        print(f"✓ 加密解密测试通过")
        print(f"  原密码: {test_password}")
        print(f"  加密后: {encrypted[:50]}...")
        print(f"  解密后: {decrypted}")
    else:
        print("✗ 加密解密测试失败")
        sys.exit(1)
except Exception as e:
    print(f"✗ 加密解密测试出错: {e}")
    sys.exit(1)

# 步骤 3: 从数据库读取配置
print("\n【步骤 3】从数据库读取配置")
print("-" * 60)
conn = sqlite3.connect('data/database.sqlite')
cursor = conn.cursor()

cursor.execute('''
    SELECT id, email_address, password_encrypted,
           imap_server, imap_port, use_ssl, provider
    FROM user_email_configs
    LIMIT 1
''')

row = cursor.fetchone()
conn.close()

if not row:
    print("✗ 没有找到邮箱配置")
    sys.exit(1)

config_id, email, encrypted_pwd, imap_server, imap_port, use_ssl, provider = row
print(f"✓ 找到配置:")
print(f"  ID: {config_id}")
print(f"  邮箱: {email}")
print(f"  IMAP服务器: {imap_server}:{imap_port}")
print(f"  使用SSL: {use_ssl}")
print(f"  服务商: {provider}")
print(f"  加密密码: {encrypted_pwd[:50]}...")

# 步骤 4: 解密密码
print("\n【步骤 4】解密密码")
print("-" * 60)
try:
    password = crypto.decrypt(encrypted_pwd)
    print(f"✓ 密码解密成功")
    print(f"  解密后密码长度: {len(password)}")
    print(f"  解密后密码: {password[:4]}...{password[-4:]}")
except Exception as e:
    print(f"✗ 密码解密失败: {e}")
    print("\n可能的原因:")
    print("1. PASSWORD_ENCRYPTION_KEY 与加密时使用的密钥不同")
    print("2. 加密数据已损坏")
    print("3. 数据库中的密码格式不正确")
    sys.exit(1)

# 步骤 5: 测试 IMAP 连接
print("\n【步骤 5】测试 IMAP 连接")
print("-" * 60)
print(f"正在连接到 {imap_server}:{imap_port}...")

try:
    # 创建连接
    mailbox = MailBox(imap_server, imap_port)

    # 尝试登录
    mailbox.login(email, password)

    print("✓ 连接成功！")
    print(f"✓ IMAP 服务已开启")
    print(f"✓ 授权码正确")
    print("\n" + "=" * 60)
    print("🎉 诊断通过！邮箱配置完全正常。")
    print("=" * 60)

    # 登出
    mailbox.logout()

except Exception as e:
    error_msg = str(e)
    print(f"✗ 连接失败: {error_msg}")
    print("\n" + "=" * 60)
    print("【错误分析】")
    print("=" * 60)

    if "Unsafe Login" in error_msg or "SELECT" in error_msg:
        print("\n错误类型: IMAP 服务未开启")
        print("\n解决方案:")
        print("1. 登录 163 邮箱: https://mail.163.com")
        print("2. 点击 '设置' → 'POP3/SMTP/IMAP'")
        print("3. 开启 'IMAP/SMTP 服务'")
        print("4. 重新运行此脚本测试")

    elif "LOGIN error" in error_msg or "password error" in error_msg:
        print("\n错误类型: 授权码错误")
        print("\n解决方案:")
        print("1. 确认使用的是授权码，不是登录密码")
        print("2. 进入163邮箱设置")
        print("3. 在 '客户端授权密码' 部分重新生成授权码")
        print("4. 在系统中更新配置")

    elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
        print("\n错误类型: 连接超时")
        print("\n解决方案:")
        print("1. 检查网络连接")
        print("2. 确认防火墙未阻止 IMAP (端口993)")

    else:
        print(f"\n错误类型: 未知错误")
        print(f"\n原始错误: {error_msg}")
        print("\n建议:")
        print("1. 检查邮箱地址是否正确")
        print("2. 确认已开启 IMAP 服务")
        print("3. 确认使用的是最新的授权码")

    print("\n" + "=" * 60)
    sys.exit(1)
