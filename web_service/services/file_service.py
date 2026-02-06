import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class FileService:
    """文件管理服务"""
    
    def __init__(self):
        """初始化文件服务"""
        # 获取当前目录的绝对路径
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # 上传目录在web_service/uploads
        self.upload_dir = os.path.join(self.current_dir, "..", "uploads")
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # 允许的文件类型
        self.allowed_extensions = {".csv", ".txt", ".xls", ".xlsx"}
        # 最大文件大小 (50MB)
        self.max_file_size = 50 * 1024 * 1024
    
    async def save_file(self, upload_file) -> str:
        """
        保存上传的文件
        
        Args:
            upload_file: 上传的文件对象
        
        Returns:
            str: 保存后的文件路径
        
        Raises:
            ValueError: 文件类型或大小不合法
        """
        # 验证文件类型
        file_extension = os.path.splitext(upload_file.filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"不支持的文件类型: {file_extension}，仅支持 {', '.join(self.allowed_extensions)}")
        
        # 验证文件大小
        file_size = 0
        content = await upload_file.read()
        file_size = len(content)
        if file_size > self.max_file_size:
            raise ValueError(f"文件大小超过限制: {file_size} bytes，最大支持 {self.max_file_size} bytes")
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(self.upload_dir, file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"文件保存成功: {file_path}")
        return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 删除是否成功
        """
        try:
            os.remove(file_path)
            logger.info(f"文件删除成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {file_path}, 错误: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            Optional[dict]: 文件信息，包括文件名、大小、创建时间等
        """
        try:
            if os.path.exists(file_path):
                file_stats = os.stat(file_path)
                return {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
            return None
    
    def list_files(self) -> list:
        """
        列出所有上传的文件
        
        Returns:
            list: 文件信息列表
        """
        files = []
        try:
            for file_name in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, file_name)
                if os.path.isfile(file_path):
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            # 按创建时间倒序排序
            files.sort(key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
        return files
