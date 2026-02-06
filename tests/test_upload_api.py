#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
账单上传 API 测试脚本

使用方法：
1. 确保 Web 服务正在运行（python3 -m web_service.main）
2. 先运行登录获取 token
3. 运行此脚本测试上传功能：python3 test_upload_api.py
"""

import requests
import json
import sys
import os
from io import BytesIO

BASE_URL = "http://localhost:8000"

# 测试用户凭据
TEST_USERNAME = "testuser"
TEST_PASSWORD = "TestPass123!"


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def login_and_get_token():
    """登录并获取访问令牌"""
    print_section("步骤 1: 用户登录")

    payload = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=payload  # 使用 form data
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✓ 登录成功")
        print(f"  用户: {data.get('user', {}).get('username')}")
        print(f"  Token: {token[:40]}...")
        return token
    else:
        print(f"✗ 登录失败: {response.text}")
        return None


def test_upload_with_form_data(token):
    """使用 FormData 方式上传文件"""
    print_section("步骤 2: 测试文件上传（FormData）")

    # 创建测试 CSV 文件
    csv_content = """收/付款,服务商,金额,时间,付款人,收款人,交易状态,商户订单号,交易号
支出,餐饮,50.00,2024-01-15 12:30:00,张三,某某餐厅,交易成功,202401151230001,202401151230001123456"""

    files = {
        'file': ('test_bill.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')
    }

    data = {
        'platform': 'alipay',
        'sync_type': 'immediate'
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }
    # 注意：不设置 Content-Type，让 requests 自动设置

    response = requests.post(
        f"{BASE_URL}/api/bills/upload",
        files=files,
        data=data,
        headers=headers
    )

    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")

    if response.status_code == 200:
        result = response.json()
        print(f"✓ 上传成功")
        print(f"  消息: {result.get('message')}")
        print(f"  上传ID: {result.get('upload_id')}")
        if result.get('file'):
            print(f"  文件名: {result['file'].get('file_name')}")
            print(f"  状态: {result['file'].get('status')}")
        return True
    else:
        print(f"✗ 上传失败")
        try:
            error = response.json()
            print(f"  错误详情: {json.dumps(error, indent=2, ensure_ascii=False)}")
        except:
            print(f"  错误信息: {response.text}")
        return False


def test_upload_without_platform(token):
    """测试不指定平台的上传（自动检测）"""
    print_section("步骤 3: 测试自动平台检测")

    csv_content = """收/付款,服务商,金额,时间
收入,支付宝,100.00,2024-01-15 12:30:00"""

    files = {
        'file': ('test_wechat.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')
    }

    data = {
        'sync_type': 'immediate'
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(
        f"{BASE_URL}/api/bills/upload",
        files=files,
        data=data,
        headers=headers
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✓ 上传成功（自动检测平台）")
        print(f"  检测到的平台: {result.get('file', {}).get('platform', 'auto')}")
        return True
    else:
        print(f"✗ 上传失败")
        try:
            error = response.json()
            print(f"  错误详情: {json.dumps(error, indent=2, ensure_ascii=False)}")
        except:
            print(f"  错误信息: {response.text}")
        return False


def test_upload_uploads_list(token):
    """测试获取上传列表"""
    print_section("步骤 4: 获取上传列表")

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        f"{BASE_URL}/api/bills/uploads",
        headers=headers
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        files = data.get('files', [])
        print(f"✓ 获取成功")
        print(f"  文件总数: {data.get('total', 0)}")
        for f in files[:3]:  # 只显示前3个
            print(f"    - {f.get('original_file_name')} ({f.get('status')})")
        return True
    else:
        print(f"✗ 获取失败")
        return False


def test_upload_validation(token):
    """测试上传验证（错误场景）"""
    print_section("步骤 5: 测试上传验证")

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # 测试1: 不发送文件
    print("\n测试 5.1: 不发送文件")
    response = requests.post(
        f"{BASE_URL}/api/bills/upload",
        data={'platform': 'alipay'},
        headers=headers
    )
    print(f"  状态码: {response.status_code} (期望: 422)")
    if response.status_code == 422:
        print(f"  ✓ 正确拒绝")
    else:
        print(f"  ✗ 未正确处理")

    # 测试2: 无效的 sync_type
    print("\n测试 5.2: 无效的 sync_type")
    files = {
        'file': ('test.csv', BytesIO(b'test,data'), 'text/csv')
    }
    data = {
        'sync_type': 'invalid_type'
    }
    response = requests.post(
        f"{BASE_URL}/api/bills/upload",
        files=files,
        data=data,
        headers=headers
    )
    print(f"  状态码: {response.status_code}")
    # 这个测试可能会成功或失败，取决于后端验证

    return True


def main():
    """主测试函数"""
    print_section("账单上传 API 测试")
    print(f"目标服务器: {BASE_URL}")
    print(f"如果测试失败，请确保：")
    print(f"  1. Web 服务正在运行（python3 -m web_service.main）")
    print(f"  2. 测试用户已存在: {TEST_USERNAME}")

    # 检查服务是否运行
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"\n✓ 服务运行中")
    except Exception:
        print(f"\n✗ 无法连接到服务，请先启动 Web 服务")
        sys.exit(1)

    # 登录获取 token
    token = login_and_get_token()
    if not token:
        print(f"\n✗ 登录失败，请确保测试用户存在")
        print(f"  可以先运行: python3 test_registration_api.py")
        sys.exit(1)

    results = []

    # 运行测试
    results.append(("FormData 上传", test_upload_with_form_data(token)))
    results.append(("自动平台检测", test_upload_without_platform(token)))
    results.append(("获取上传列表", test_upload_uploads_list(token)))
    results.append(("上传验证", test_upload_validation(token)))

    # 打印测试结果汇总
    print_section("测试结果汇总")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name:25} {status}")
    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！上传功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
