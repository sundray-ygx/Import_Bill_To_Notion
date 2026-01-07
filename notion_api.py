from notion_client import Client as NotionApiClient
from config import Config
import logging

logger = logging.getLogger(__name__)

class NotionClient:
    """Notion API client for bill management"""
    
    def __init__(self):
        """Initialize Notion client"""

        logger.info(f"初始化Notion客户端，API密钥: {'***' if Config.NOTION_API_KEY else '未配置'}")
        logger.info(f"收入数据库ID: {'***' if Config.NOTION_INCOME_DATABASE_ID else '未配置'}")
        logger.info(f"支出数据库ID: {'***' if Config.NOTION_EXPENSE_DATABASE_ID else '未配置'}")
        
        # 检查API密钥和数据库ID是否配置
        if not Config.NOTION_API_KEY:
            logger.error("Notion API密钥未配置")
        if not Config.NOTION_INCOME_DATABASE_ID:
            logger.error("Notion收入数据库ID未配置")
        if not Config.NOTION_EXPENSE_DATABASE_ID:
            logger.error("Notion支出数据库ID未配置")
        
        # 初始化Notion客户端
        self.client = NotionApiClient(auth=Config.NOTION_API_KEY)
        self.income_database_id = Config.NOTION_INCOME_DATABASE_ID
        self.expense_database_id = Config.NOTION_EXPENSE_DATABASE_ID
        self.config = Config
    
    def create_page(self, properties):
        """Create a new page in the Notion database"""
        try:
            # 清理properties中的无效值，确保符合Notion API要求
            cleaned_properties = {}
            
            # 提取收入/支出类型
            income_expense_type = ""
            if 'Income Expense' in properties:
                ie_prop = properties['Income Expense']
                if ie_prop and 'select' in ie_prop:
                    select_value = ie_prop['select']
                    if select_value and 'name' in select_value:
                        income_expense_type = select_value['name'].strip()
            
            for prop_name, prop_value in properties.items():
                if prop_value is None:
                    continue
                
                # 跳过空对象
                if isinstance(prop_value, dict) and not prop_value:
                    continue
                
                # 收支字段 不处理
                if prop_name == 'Income Expense':
                    # logger.info(f"跳过Income Expense字段: {prop_value}")
                    continue
                
                cleaned_prop = {}
                
                # 处理不同类型的属性
                if 'select' in prop_value:
                    # 确保select属性只包含name，且name是有效的字符串
                    select_value = prop_value['select']
                    if select_value:
                        name_value = str(select_value.get('name', '')).strip()
                        if name_value:
                            cleaned_prop['select'] = {'name': name_value}
                        else:
                            # 如果name无效，跳过该属性
                            continue
                    else:
                        # 如果select_value无效，跳过该属性
                        continue
                elif 'title' in prop_value:
                    # 确保title属性有效
                    title_value = prop_value['title']
                    if title_value and isinstance(title_value, list) and len(title_value) > 0:
                        cleaned_prop['title'] = title_value
                elif 'rich_text' in prop_value:
                    # 确保rich_text属性有效
                    cleaned_prop['rich_text'] = prop_value['rich_text']
                elif 'number' in prop_value:
                    # 确保number属性有效
                    number_value = prop_value['number']
                    if number_value is not None:
                        try:
                            cleaned_prop['number'] = float(number_value)
                        except (ValueError, TypeError):
                            # 如果无法转换为浮点数，跳过该属性
                            continue
                elif 'date' in prop_value:
                    # 确保date属性有效
                    date_value = prop_value['date']
                    if date_value and isinstance(date_value, dict) and 'start' in date_value:
                        cleaned_prop['date'] = date_value
                
                if cleaned_prop:
                    cleaned_properties[prop_name] = cleaned_prop
            
            # 确保至少有一个属性，否则添加Name属性
            if not cleaned_properties:
                cleaned_properties['Name'] = {'title': [{'text': {'content': 'Unknown Record'}}]}
            
            # 根据收入/支出类型选择数据库
            if income_expense_type == '收入':
                database_id = self.income_database_id
            else:
                database_id = self.expense_database_id
            
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=cleaned_properties
            )
            logger.info(f"Created page: {response['id']} in database: {'income' if income_expense_type == '收入' else 'expense'}")
            return response
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            logger.error(f"Properties: {properties}")
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
            
            # Test income database access
            income_response = self.client.databases.retrieve(database_id=self.income_database_id)
            logger.info(f"成功访问收入数据库，数据库名称: {income_response.get('title', [{}])[0].get('text', {}).get('content', '未知')}")
            
            # Test expense database access
            expense_response = self.client.databases.retrieve(database_id=self.expense_database_id)
            logger.info(f"成功访问支出数据库，数据库名称: {expense_response.get('title', [{}])[0].get('text', {}).get('content', '未知')}")
            
            logger.info("Notion API连接验证成功")
            return True
        except Exception as e:
            logger.error(f"Notion API连接失败: {e}")
            return False
