#!/usr/bin/env python3
"""
用户注册 API 测试脚本

使用方法：
1. 确保 Web 服务正在运行（python3 -m web_service.main）
2. 运行此脚本：python3 test_registration_api.py
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def test_setup_check():
    """测试检查是否需要初始设置"""
    print_section("测试 1: 检查系统设置状态")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/setup/check")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_register_user(username, email, password):
    """测试用户注册"""
    print(f"\n注册用户: {username}")
    print(f"  邮箱: {email}")
    print(f"  密码长度: {len(password)} 字符, {len(password.encode('utf-8'))} 字节")

    try:
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  用户 ID: {data.get('id')}")
            print(f"  创建时间: {data.get('created_at')}")
            print(f"  状态: ✓ 注册成功")
        else:
            print(f"  错误: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"  错误: {e}")
        return False

def test_register_duplicate_user(username, email, password):
    """测试重复注册"""
    print(f"\n测试重复注册: {username}")
    try:
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 400:
            print(f"  状态: ✓ 正确拒绝重复用户")
            return True
        else:
            print(f"  错误: 应该返回 400，实际返回 {response.status_code}")
            return False
    except Exception as e:
        print(f"  错误: {e}")
        return False

def test_password_validation(username, email, password, expected_reason=""):
    """测试密码验证"""
    print(f"\n测试密码验证: {username}")
    print(f"  密码: {password[:20]}{'...' if len(password) > 20 else ''}")
    print(f"  预期: {expected_reason}")

    try:
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 400:
            print(f"  状态: ✓ 正确拒绝弱密码")
            return True
        else:
            print(f"  错误: 应该返回 400，实际返回 {response.status_code}")
            return False
    except Exception as e:
        print(f"  错误: {e}")
        return False

def main():
    """主测试函数"""
    print_section("用户注册 API 测试")
    print(f"目标服务器: {BASE_URL}")
    print(f"如果测试失败，请确保 Web 服务正在运行：")
    print(f"  python3 -m web_service.main")

    # 检查服务是否运行
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"\n✓ 服务运行中")
    except Exception:
        print(f"\n✗ 无法连接到服务，请先启动 Web 服务")
        sys.exit(1)

    results = []

    # 测试 1: 检查系统状态
    results.append(("系统状态检查", test_setup_check()))

    # 测试 2: 注册正常用户
    print_section("测试 2: 注册正常用户")
    results.append(("正常用户注册", test_register_user(
        "testuser",
        "test@example.com",
        "TestPass123!"
    )))

    # 测试 3: 注册超长密码用户
    print_section("测试 3: 注册超长密码用户")
    results.append(("超长密码注册", test_register_user(
        "longpassuser",
        "longpass@example.com",
        "a" * 100  # 100 字符，超过 72 字节
    )))

    # 测试 4: 注册 Unicode 密码用户
    print_section("测试 4: 注册 Unicode 密码用户")
    results.append(("Unicode密码注册", test_register_user(
        "unicodeuser",
        "unicode@example.com",
        "测试密码Test123!"
    )))

    # 测试 5: 重复注册
    print_section("测试 5: 重复注册检测")
    results.append(("重复注册拒绝", test_register_duplicate_user(
        "testuser",
        "test@example.com",
        "TestPass123!"
    )))

    # 测试 6: 弱密码检测
    print_section("测试 6: 弱密码检测")
    results.append(("弱密码拒绝-太短", test_password_validation(
        "shortuser",
        "short@example.com",
        "Short1!",
        "密码太短"
    )))
    results.append(("弱密码拒绝-无数字", test_password_validation(
        "nodigituser",
        "nodigit@example.com",
        "TestPassword!",
        "缺少数字"
    )))

    # 打印测试结果汇总
    print_section("测试结果汇总")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name:25} {status}")
    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！注册功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
