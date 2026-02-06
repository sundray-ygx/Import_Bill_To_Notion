import logging
from src.config import Config
from parsers import get_parser, get_parser_by_platform
from src.notion_api import NotionClient
from typing import Optional
import os
import pandas as pd

logger = logging.getLogger(__name__)


def import_bill(file_path: str, platform: Optional[str] = None, user_id: Optional[int] = None) -> dict:
    """Import bill file to Notion.

    支持单用户模式和多租户模式：
    - 单用户模式：使用全局配置的 Notion API key
    - 多租户模式：根据 user_id 使用用户的 Notion 配置

    Args:
        file_path: 账单文件路径
        platform: 支付平台（alipay, wechat, unionpay），不指定则自动检测
        user_id: 用户ID（多租户模式必需）

    Returns:
        包含导入结果和元数据的字典：
        {
            'success': bool,
            'detected_platform': str,  # 检测到的平台
            'total_records': int,
            'imported': int,
            'updated': int,
            'skipped': int
        }
    """
    try:
        # 在多租户模式下，验证 user_id 参数
        if Config.is_multi_tenant_mode():
            if not user_id:
                logger.error("user_id is required in multi-tenant mode")
                return {'success': False, 'error': 'user_id is required in multi-tenant mode'}
        else:
            # 单用户模式：验证全局配置
            Config.validate()

        # Get parser - auto-detect if platform not specified
        if platform:
            parser = get_parser_by_platform(file_path, platform)
            if not parser:
                logger.error(f"Unsupported platform: {platform}")
                return {'success': False, 'error': f"Unsupported platform: {platform}"}
        else:
            parser = get_parser(file_path)
            if not parser:
                logger.error("Failed to detect bill format. Please specify platform explicitly.")
                return {'success': False, 'error': 'Failed to detect bill format'}

        detected_platform = parser.get_platform()
        logger.info(f"Using {detected_platform} parser")

        # Parse bill file
        logger.info(f"Parsing bill file: {file_path}")
        notion_records = parser.to_notion_format()
        logger.info(f"Parsed {len(notion_records)} records")

        # Import to Notion - 传递 user_id
        logger.info("Importing records to Notion...")
        if Config.is_multi_tenant_mode():
            logger.info(f"Importing for user_id: {user_id}")
        notion_client = NotionClient(user_id=user_id)

        # Verify Notion connection
        if not notion_client.verify_connection():
            logger.error("Failed to connect to Notion. Please check your API key and database ID.")
            return {
                'success': False,
                'error': 'Failed to connect to Notion',
                'detected_platform': detected_platform
            }

        # Batch import
        result = notion_client.batch_import(notion_records)

        # Print import result
        logger.info(f"Import completed successfully!")
        logger.info(f"Imported: {result['imported']} records")
        logger.info(f"Updated: {result['updated']} records")
        logger.info(f"Skipped: {result['skipped']} records")

        return {
            'success': True,
            'detected_platform': detected_platform,
            'total_records': len(notion_records),
            'imported': result['imported'],
            'updated': result['updated'],
            'skipped': result['skipped']
        }

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'detected_platform': parser.get_platform() if 'parser' in locals() else None
        }


def parse_bill_only(file_path: str, platform: Optional[str] = None) -> Optional[list]:
    """仅解析账单文件，不导入到 Notion。

    用于预览或调试目的。

    Args:
        file_path: 账单文件路径
        platform: 支付平台（alipay, wechat, unionpay），不指定则自动检测

    Returns:
        解析后的记录列表（Notion 格式），失败返回 None
    """
    try:
        # Get parser
        if platform:
            parser = get_parser_by_platform(file_path, platform)
            if not parser:
                logger.error(f"Unsupported platform: {platform}")
                return None
        else:
            parser = get_parser(file_path)
            if not parser:
                logger.error("Failed to detect bill format.")
                return None

        # Parse bill file
        logger.info(f"Parsing bill file: {file_path}")
        notion_records = parser.to_notion_format()
        logger.info(f"Parsed {len(notion_records)} records")

        return notion_records

    except Exception as e:
        logger.error(f"Parse failed: {e}", exc_info=True)
        return None


def parse_bill_raw(file_path: str, platform: Optional[str] = None, max_rows: int = 500) -> Optional[dict]:
    """解析账单文件，返回原始 CSV 数据用于预览。

    Args:
        file_path: 账单文件路径
        platform: 支付平台（alipay, wechat, unionpay），不指定则自动检测
        max_rows: 最大返回行数

    Returns:
        包含原始数据的字典：
        {
            'detected_platform': str,
            'columns': list,
            'data': list,
            'total_rows': int
        }
        失败返回 None
    """
    try:
        # Get parser
        if platform:
            parser = get_parser_by_platform(file_path, platform)
            if not parser:
                logger.error(f"Unsupported platform: {platform}")
                return None
        else:
            parser = get_parser(file_path)
            if not parser:
                logger.error("Failed to detect bill format.")
                return None

        detected_platform = parser.get_platform()

        # Parse bill file to get raw DataFrame
        logger.info(f"Parsing bill file for preview: {file_path}")
        df = parser.parse()

        if df is None or df.empty:
            return {
                'detected_platform': detected_platform,
                'columns': [],
                'data': [],
                'total_rows': 0
            }

        total_rows = len(df)
        # 限制行数
        df_preview = df.head(max_rows)

        # 转换为字典列表（保持原始列名和数据）
        # 使用 to_dict('records') 并处理特殊类型
        data = []
        for _, row in df_preview.iterrows():
            record = {}
            for col in df_preview.columns:
                value = row[col]
                # 处理 NaN 值
                if pd.isna(value):
                    record[col] = None
                # 处理 Timestamp 类型
                elif isinstance(value, pd.Timestamp):
                    record[col] = str(value)
                # 处理其他类型，转换为字符串保持一致性
                else:
                    record[col] = str(value) if value is not None else None
            data.append(record)

        return {
            'detected_platform': detected_platform,
            'columns': list(df.columns),
            'data': data,
            'total_rows': total_rows
        }

    except Exception as e:
        logger.error(f"Parse raw failed: {e}", exc_info=True)
        return None

def generate_review(review_type, year, month=None, quarter=None, user_id=None):
    """Generate bill review report"""
    from src.review_service import ReviewService
    service = ReviewService(user_id)
    if review_type == "monthly":
        return service.generate_monthly_review(year, month)
    elif review_type == "quarterly":
        return service.generate_quarterly_review(year, quarter)
    else:
        return service.generate_yearly_review(year)
