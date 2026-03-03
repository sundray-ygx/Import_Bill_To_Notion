#!/usr/bin/env python3
"""
163邮箱 IMAP 连接测试脚本

用于验证 163邮箱的 IMAP 服务是否已开启，以及授权码是否正确。
"""

import sys
from imap_tools import MailBox


def test_163_imap_connection(email: str, auth_code: str) -> bool:
    """
    测试163邮箱IMAP连接

    Args:
        email: 163邮箱地址
        auth_code: 授权码（16位）

    Returns:
        bool: 连接成功返回True，否则返回False
    """
    print("=" * 50)
    print("163邮箱 IMAP 连接测试")
    print("=" * 50)
    print(f"邮箱地址: {email}")
    print(f"IMAP服务器: imap.163.com:993")
    print("-" * 50)

    # 验证输入
    if not email.endswith('@163.com'):
        print("⚠️  警告: 邮箱地址不是 @163.com 结尾")
        return False

    if len(auth_code) != 16:
        print(f"⚠️  警告: 授权码长度应为16位，当前为 {len(auth_code)} 位")
        print("   请确认是否复制了完整的授权码")

    try:
        print("正在连接到 IMAP 服务器...")

        # 创建连接（端口993自动使用SSL）
        mailbox = MailBox('imap.163.com', 993)

        # 尝试登录
        print("正在验证授权码...")
        mailbox.login(email, auth_code)

        # 如果成功到这里，说明连接成功
        print("✓ 连接成功！")
        print("✓ IMAP 服务已开启")
        print("✓ 授权码验证通过")
        print("✓ 可以在系统中使用此配置")
        print("=" * 50)

        mailbox.logout()
        return True

    except Exception as e:
        error_msg = str(e)

        print("✗ 连接失败")
        print("-" * 50)

        # 根据错误信息给出具体建议
        if "Unsafe Login" in error_msg or "SELECT" in error_msg:
            print("错误原因: IMAP 服务未开启")
            print()
            print("解决方案:")
            print("1. 登录 https://mail.163.com")
            print("2. 点击 '设置' → 'POP3/SMTP/IMAP'")
            print("3. 开启 'IMAP/SMTP 服务'")
            print("4. 重新运行此脚本测试")

        elif "LOGIN error" in error_msg or "password error" in error_msg:
            print("错误原因: 授权码错误或使用了登录密码")
            print()
            print("解决方案:")
            print("1. 确认使用的是授权码，不是登录密码")
            print("2. 进入163邮箱设置")
            print("3. 在 '客户端授权密码' 部分重新生成授权码")
            print("4. 复制新的16位授权码")
            print("5. 重新运行此脚本测试")

        elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            print("错误原因: 连接超时")
            print()
            print("解决方案:")
            print("1. 检查网络连接")
            print("2. 确认防火墙未阻止 IMAP (端口993)")
            print("3. 稍后重试")

        else:
            print(f"错误原因: {error_msg}")
            print()
            print("建议:")
            print("1. 检查邮箱地址是否正确")
            print("2. 确认已开启 IMAP 服务")
            print("3. 确认使用的是最新的授权码")

        print("=" * 50)
        return False


def main():
    """主函数"""
    print()
    print("163邮箱 IMAP 连接测试工具")
    print()

    # 获取用户输入
    email = input("请输入163邮箱地址: ").strip()

    if not email:
        print("✗ 邮箱地址不能为空")
        sys.exit(1)

    auth_code = input("请输入16位授权码: ").strip()

    if not auth_code:
        print("✗ 授权码不能为空")
        sys.exit(1)

    print()

    # 执行测试
    success = test_163_imap_connection(email, auth_code)

    print()

    if success:
        print("🎉 测试通过！您可以在系统中保存此配置。")
        sys.exit(0)
    else:
        print("❌ 测试失败，请按照上面的提示解决问题后重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()
