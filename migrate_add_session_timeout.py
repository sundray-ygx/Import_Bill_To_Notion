#!/usr/bin/env python3
"""数据库迁移脚本：添加会话超时字段到用户表。

运行此脚本以添加 session_timeout_minutes 字段到 users 表。
"""

import sys
import sqlite3
from pathlib import Path


def migrate_database(db_path: str):
    """执行数据库迁移。

    Args:
        db_path: 数据库文件路径
    """
    if not Path(db_path).exists():
        print(f"错误：数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'session_timeout_minutes' in columns:
            print("字段 session_timeout_minutes 已存在，跳过迁移")
            return True

        # 添加字段
        print(f"正在迁移数据库: {db_path}")
        cursor.execute(
            "ALTER TABLE users ADD COLUMN session_timeout_minutes INTEGER NOT NULL DEFAULT 15"
        )

        conn.commit()
        print("迁移完成：已添加 session_timeout_minutes 字段（默认值：15分钟）")
        return True

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    """主函数。"""
    # 默认数据库路径
    default_db = "data/database.sqlite"

    # 支持命令行参数
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = default_db

    print("=" * 60)
    print("数据库迁移：添加会话超时字段")
    print("=" * 60)

    success = migrate_database(db_path)

    if success:
        print("\n✓ 迁移成功")
        return 0
    else:
        print("\n✗ 迁移失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
