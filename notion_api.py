from notion_client import Client as NotionApiClient
from config import Config
import logging

logger = logging.getLogger(__name__)

class NotionClient:
    """Notion API client for bill management"""
    
    def __init__(self):
        """Initialize Notion client"""
        logger.info(f"初始化Notion客户端，API密钥: {'***' if Config.NOTION_API_KEY else '未配置'}")
        logger.info(f"数据库ID: {'***' if Config.NOTION_DATABASE_ID else '未配置'}")
        
        # 检查API密钥和数据库ID是否配置
        if not Config.NOTION_API_KEY:
            logger.error("Notion API密钥未配置")
        if not Config.NOTION_DATABASE_ID:
            logger.error("Notion数据库ID未配置")
        
        # 初始化Notion客户端
        self.client = NotionApiClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        self.config = Config
    
    def create_page(self, properties):
        """Create a new page in the Notion database"""
        try:
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            logger.info(f"Created page: {response['id']}")
            return response
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise
    
    def batch_import(self, records, batch_size=10):
        """Import records in batches to optimize API calls"""
        logger.info(f"开始批量导入记录，共 {len(records)} 条，批次大小：{batch_size}")
        
        imported_count = 0
        skipped_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_number = i//batch_size + 1
            total_batches = (len(records)-1)//batch_size + 1
            
            logger.info(f"处理批次 {batch_number}/{total_batches}，包含 {len(batch)} 条记录")
            
            for record in batch:
                try:
                    # Validate record structure
                    if 'Date' not in record or 'Price' not in record:
                        logger.error(f"记录缺少必要字段: {record}")
                        skipped_count += 1
                        continue
                    
                    # Create new record
                    self.create_page(record)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"处理记录失败: {e}")
                    logger.error(f"记录内容: {record}")
                    skipped_count += 1
            
            logger.info(f"批次 {batch_number}/{total_batches} 处理完成")
        
        logger.info(f"批量导入完成")
        logger.info(f"导入: {imported_count} 条记录")
        logger.info(f"跳过: {skipped_count} 条记录")
        
        return {
            "imported": imported_count,
            "updated": 0,
            "skipped": skipped_count
        }
    
    def verify_connection(self):
        """Verify connection to Notion API"""
        logger.info("开始验证Notion API连接...")
        
        try:
            # Test API key validity
            test_response = self.client.users.me()
            logger.info(f"API密钥有效，当前用户: {test_response.get('name', '未知')}")
            
            # Test database access
            response = self.client.databases.retrieve(database_id=self.database_id)
            logger.info(f"成功访问数据库，数据库名称: {response.get('title', [{}])[0].get('text', {}).get('content', '未知')}")
            
            logger.info("Notion API连接验证成功")
            return True
        except Exception as e:
            logger.error(f"Notion API连接失败: {e}")
            return False
