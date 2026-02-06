"""
数据库迁移脚本：添加复盘配置字段到 UserNotionConfig 表
执行方式: python3 migrate_add_review_config.py
"""

import logging
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_context, engine
from models import UserNotionConfig
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    logger.info("Starting migration: Add review config fields to UserNotionConfig")

    try:
        with engine.connect() as conn:
            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(user_notion_configs)"))
            columns = [row[1] for row in result.fetchall()]

            # 添加复盘数据库ID字段
            review_fields = [
                ('notion_monthly_review_db', 'VARCHAR(100)'),
                ('notion_quarterly_review_db', 'VARCHAR(100)'),
                ('notion_yearly_review_db', 'VARCHAR(100)'),
                ('notion_monthly_template_id', 'VARCHAR(100)'),
                ('notion_quarterly_template_id', 'VARCHAR(100)'),
                ('notion_yearly_template_id', 'VARCHAR(100)')
            ]

            for field_name, field_type in review_fields:
                if field_name not in columns:
                    sql = f"ALTER TABLE user_notion_configs ADD COLUMN {field_name} {field_type}"
                    logger.info(f"Adding column: {field_name}")
                    conn.execute(text(sql))
                else:
                    logger.info(f"Column {field_name} already exists, skipping")

            conn.commit()
            logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate()
