#!/usr/bin/env python3
"""
数据库迁移脚本：修改 user_uploads 表

将 file_name, file_path, file_size 字段改为可为空
"""

import os
import sys
import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = "data/database.sqlite"

def migrate_database():
    """执行数据库迁移"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        return False

    # 备份数据库
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ 数据库已备份到: {backup_path}")
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 开启事务
        conn.execute("BEGIN IMMEDIATE")

        # 1. 创建新表
        print("创建新表 user_uploads_new...")
        cursor.execute("""
            CREATE TABLE user_uploads_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                file_name VARCHAR(255),
                original_file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500),
                file_size INTEGER,
                platform VARCHAR(20) NOT NULL,
                upload_type VARCHAR(20) DEFAULT 'immediate',
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 2. 迁移数据
        print("迁移数据...")
        cursor.execute("""
            INSERT INTO user_uploads_new
            (id, user_id, file_name, original_file_name, file_path, file_size, platform, upload_type, status, created_at)
            SELECT
                id, user_id, file_name, original_file_name, file_path, file_size, platform, upload_type, status, created_at
            FROM user_uploads
        """)

        migrated_rows = cursor.rowcount
        print(f"✓ 已迁移 {migrated_rows} 条记录")

        # 3. 删除旧表
        print("删除旧表...")
        cursor.execute("DROP TABLE user_uploads")

        # 4. 重命名新表
        print("重命名新表...")
        cursor.execute("ALTER TABLE user_uploads_new RENAME TO user_uploads")

        # 5. 重建索引
        print("重建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_uploads_user_id ON user_uploads (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_uploads_status ON user_uploads (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_uploads_created_at ON user_uploads (created_at)")

        # 提交事务
        conn.commit()
        print("\n✓ 迁移成功完成！")
        return True

    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"\n✗ 迁移失败: {e}")
        print(f"请从备份恢复: {backup_path}")
        return False

    finally:
        conn.close()


def verify_schema():
    """验证迁移后的 schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(user_uploads)")
    columns = cursor.fetchall()

    print("\n验证 user_uploads 表结构:")
    print("-" * 70)
    print(f"{'列名':<25} {'类型':<15} {'NOT NULL':<10}")
    print("-" * 70)

    for col in columns:
        cid, name, type_, notnull, default_value, pk = col
        nullable = "NOT NULL" if notnull else "NULL"
        print(f"{name:<25} {type_:<15} {nullable:<10}")

    conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("  数据库迁移工具")
    print("=" * 70)
    print(f"数据库路径: {DB_PATH}")
    print()

    if migrate_database():
        verify_schema()
        print("\n" + "=" * 70)
        print("  迁移完成！请重启 Web 服务。")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("  迁移失败！请检查错误信息。")
        print("=" * 70)
        sys.exit(1)
