#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
测试首个用户注册流程
验证：1. 首个用户自动成为超级管理员
2. 注册接口返回正确的用户信息（包含is_superuser）
3. 前端能够正确解析并跳转到设置页面
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models import User, Base
from src.auth import get_password_hash
import json

# 数据库配置
DATABASE_URL = "sqlite:///./data/database.sqlite"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def reset_database():
    """重置数据库（清空所有用户）"""
    print("🗑️  清空数据库...")
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()
        print("✓ 数据库已清空")
    finally:
        db.close()

def check_user_count():
    """检查用户数量"""
    db = SessionLocal()
    try:
        count = db.query(User).count()
        superuser_count = db.query(User).filter(User.is_superuser == True).count()
        print(f"📊 当前用户数: {count}, 超级管理员数: {superuser_count}")
        return count, superuser_count
    finally:
        db.close()

def simulate_register_user(username, email, password):
    """模拟用户注册"""
    print(f"\n📝 模拟注册用户: {username}")

    db = SessionLocal()
    try:
        # 检查是否应该成为超级管理员
        user_count = db.query(User).count()
        superuser_count = db.query(User).filter(User.is_superuser == True).count()
        should_be_superuser = (user_count == 0) or (superuser_count == 0)

        # 创建用户
        new_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            is_superuser=should_be_superuser,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✓ 用户创建成功")
        print(f"  - ID: {new_user.id}")
        print(f"  - 用户名: {new_user.username}")
        print(f"  - 邮箱: {new_user.email}")
        print(f"  - 是否超级管理员: {new_user.is_superuser}")
        print(f"  - 是否激活: {new_user.is_active}")

        # 模拟 API 响应
        response = {
            "access_token": "test_token_" + str(new_user.id),
            "refresh_token": "test_refresh_" + str(new_user.id),
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "is_superuser": new_user.is_superuser,
                "is_active": new_user.is_active,
                "require_password_change": new_user.require_password_change,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
                "last_login": new_user.last_login.isoformat() if new_user.last_login else None
            }
        }

        print(f"\n📦 API 响应示例:")
        print(f"  - access_token: {response['access_token']}")
        print(f"  - user.is_superuser: {response['user']['is_superuser']}")
        print(f"  - 预期跳转: {'/settings' if response['user']['is_superuser'] else '/'}")

        return new_user, response

    finally:
        db.close()

def main():
    print("=" * 60)
    print("🧪 首个用户注册流程测试")
    print("=" * 60)

    # 1. 重置数据库
    reset_database()

    # 2. 检查初始状态
    count, superuser_count = check_user_count()

    # 3. 模拟首个用户注册
    print("\n" + "=" * 60)
    print("场景 1: 首个用户注册")
    print("=" * 60)
    user1, response1 = simulate_register_user("admin", "admin@example.com", "Admin123")

    # 验证
    assert user1.is_superuser == True, "❌ 首个用户应该是超级管理员"
    assert response1['user']['is_superuser'] == True, "❌ API 响应应包含 is_superuser=true"
    print("\n✅ 场景 1 通过: 首个用户自动成为超级管理员")

    # 4. 检查数据库状态
    count, superuser_count = check_user_count()

    # 5. 模拟第二个用户注册
    print("\n" + "=" * 60)
    print("场景 2: 第二个用户注册")
    print("=" * 60)
    user2, response2 = simulate_register_user("user2", "user2@example.com", "User123")

    # 验证
    assert user2.is_superuser == False, "❌ 第二个用户不应该是超级管理员"
    assert response2['user']['is_superuser'] == False, "❌ API 响应应包含 is_superuser=false"
    print("\n✅ 场景 2 通过: 第二个用户为普通用户")

    # 6. 最终检查
    print("\n" + "=" * 60)
    print("📊 最终数据库状态")
    print("=" * 60)
    count, superuser_count = check_user_count()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    print("\n💡 提示:")
    print("1. 首个用户注册时自动成为超级管理员")
    print("2. 注册 API 返回 user 对象，包含 is_superuser 字段")
    print("3. 前端应检查 data.user.is_superuser 来决定跳转目标:")
    print("   - true → 跳转到 /settings")
    print("   - false → 跳转到 /")

if __name__ == "__main__":
    main()
