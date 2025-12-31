import os
import sys
import logging

# 添加项目根目录到Python路径，以便能够导入importer.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from importer import import_bill

logger = logging.getLogger(__name__)

class ImportService:
    """导入服务，集成原有导入逻辑"""
    
    def __init__(self):
        """初始化导入服务"""
        logger.info("导入服务已初始化")
    
    def import_bill(self, file_path: str, platform: str = None) -> dict:
        """
        导入账单到Notion
        
        Args:
            file_path: 账单文件路径
            platform: 账单平台（可选）
        
        Returns:
            dict: 导入结果
        """
        logger.info(f"开始导入账单: {file_path}")
        
        try:
            # 调用原有导入逻辑
            success = import_bill(file_path, platform)
            
            if success:
                result = {
                    "success": True,
                    "message": "账单导入成功",
                    "file_path": file_path
                }
            else:
                result = {
                    "success": False,
                    "message": "账单导入失败",
                    "file_path": file_path
                }
            
            logger.info(f"账单导入完成: {file_path}, 结果: {result}")
            return result
        except Exception as e:
            logger.error(f"账单导入异常: {file_path}, 错误: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"导入过程中发生异常: {str(e)}",
                "file_path": file_path
            }
