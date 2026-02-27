#!/usr/bin/env python3
"""数据库迁移脚本

用于更新数据库结构到最新版本。

用法:
    python3 migrate_database.py
"""

import sqlite3
import os
import sys
from pathlib import Path

# 数据库路径
DB_PATH = "data/database.sqlite"


def get_current_version(db_path: str) -> int:
    """获取当前数据库版本。

    Returns:
        当前版本号，如果未设置返回0
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查 schema_version 表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='schema_version'
    """)

    if not cursor.fetchone():
        conn.close()
        return 0

    # 获取版本号
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0


def set_version(db_path: str, version: int):
    """设置数据库版本。

    Args:
        db_path: 数据库文件路径
        version: 版本号
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建 schema_version 表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 插入版本记录
    cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()
    conn.close()

    print(f"✅ 数据库版本已更新到: {version}")


def migrate_to_v1(db_path: str):
    """迁移到版本 1 - 添加用户会话超时字段。

    Args:
        db_path: 数据库文件路径
    """
    print("执行迁移 v1: 添加 users.session_timeout_minutes 字段...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if "session_timeout_minutes" not in columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN session_timeout_minutes INTEGER DEFAULT 30
        """)
        conn.commit()
        print("  ✅ 添加 session_timeout_minutes 字段")
    else:
        print("  ⏭️  session_timeout_minutes 字段已存在，跳过")

    conn.close()


def migrate_to_v2(db_path: str):
    """迁移到版本 2 - 添加复盘配置字段。

    Args:
        db_path: 数据库文件路径
    """
    print("执行迁移 v2: 添加复盘配置字段...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(user_notion_configs)")
    columns = [col[1] for col in cursor.fetchall()]

    review_fields = [
        ("notion_monthly_review_db", "VARCHAR(100)"),
        ("notion_quarterly_review_db", "VARCHAR(100)"),
        ("notion_yearly_review_db", "VARCHAR(100)"),
        ("notion_monthly_template_id", "VARCHAR(100)"),
        ("notion_quarterly_template_id", "VARCHAR(100)"),
        ("notion_yearly_template_id", "VARCHAR(100)"),
    ]

    for field_name, field_type in review_fields:
        if field_name not in columns:
            cursor.execute(f"""
                ALTER TABLE user_notion_configs
                ADD COLUMN {field_name} {field_type}
            """)
            print(f"  ✅ 添加 {field_name} 字段")
        else:
            print(f"  ⏭️  {field_name} 字段已存在，跳过")

    conn.commit()
    conn.close()


def run_migrations():
    """运行所有待执行的迁移。"""
    db_path = DB_PATH

    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        print("   请先运行服务初始化数据库")
        sys.exit(1)

    # 获取当前版本
    current_version = get_current_version(db_path)
    print(f"当前数据库版本: v{current_version}")
    print()

    # 定义所有迁移
    migrations = [
        (1, migrate_to_v1),
        (2, migrate_to_v2),
    ]

    # 执行待执行的迁移
    for version, migrate_func in migrations:
        if version > current_version:
            try:
                migrate_func(db_path)
                set_version(db_path, version)
            except Exception as e:
                print(f"❌ 迁移到 v{version} 失败: {e}")
                sys.exit(1)

    print()
    if current_version >= len(migrations):
        print("✅ 数据库已是最新版本！")
    else:
        print(f"✅ 迁移完成！数据库版本: v{len(migrations)}")


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移脚本")
    print("=" * 50)
    print()

    run_migrations()

    print()
    print("提示: 如果仍有问题，请重启 web 服务")
