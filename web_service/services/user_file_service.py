"""User file service for multi-tenant file management."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import os
import shutil
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from src.config import Config

logger = logging.getLogger(__name__)


class UserFileService:
    """用户文件服务，支持用户文件隔离。

    文件存储结构:
    uploads/
    └── {user_id}/
        └── {upload_id}/
            ├── original/
            │   └── {timestamp}_{original_filename}
            └── processed/
                └── {timestamp}_{original_filename}.json
    """

    def __init__(self, upload_dir: str = None):
        """初始化用户文件服务。

        Args:
            upload_dir: 上传文件根目录，默认为 web_service/uploads
        """
        if upload_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.upload_dir = os.path.normpath(os.path.join(current_dir, "..", "uploads"))
        else:
            self.upload_dir = upload_dir

        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)

        # 允许的文件类型
        self.allowed_extensions = set(Config.ALLOWED_FILE_EXTENSIONS)
        # 最大文件大小
        self.max_file_size = Config.MAX_UPLOAD_SIZE

    def get_user_upload_dir(self, user_id: int, upload_id: int) -> str:
        """获取用户上传目录的路径。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID

        Returns:
            上传目录路径
        """
        return os.path.join(
            self.upload_dir,
            str(user_id),
            str(upload_id),
            "original"
        )

    def get_user_processed_dir(self, user_id: int, upload_id: int) -> str:
        """获取用户处理后文件目录的路径。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID

        Returns:
            处理后文件目录路径
        """
        return os.path.join(
            self.upload_dir,
            str(user_id),
            str(upload_id),
            "processed"
        )

    def get_user_temp_dir(self, user_id: int) -> str:
        """获取用户临时文件目录的路径。

        Args:
            user_id: 用户ID

        Returns:
            临时文件目录路径
        """
        return os.path.join(
            self.upload_dir,
            str(user_id),
            "temp"
        )

    async def save_file(self, user_id: int, upload_id: int, file, original_filename: str) -> str:
        """保存文件到用户专属目录。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID
            file: 上传的文件对象
            original_filename: 原始文件名

        Returns:
            保存后的文件路径

        Raises:
            ValueError: 文件类型或大小不合法
        """
        # 验证文件类型
        file_extension = os.path.splitext(original_filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(
                f"不支持的文件类型: {file_extension}，仅支持 {', '.join(self.allowed_extensions)}"
            )

        # 创建用户上传目录
        user_dir = self.get_user_upload_dir(user_id, upload_id)
        os.makedirs(user_dir, exist_ok=True)

        # 读取文件内容
        content = await file.read()
        file_size = len(content)

        # 验证文件大小
        if file_size > self.max_file_size:
            raise ValueError(
                f"文件大小超过限制: {file_size} bytes，最大支持 {self.max_file_size} bytes"
            )

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = self._sanitize_filename(original_filename)
        filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(user_dir, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved for user {user_id}: {file_path}")
        return file_path

    def delete_user_files(self, user_id: int, upload_id: int) -> bool:
        """删除用户上传的所有相关文件。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID

        Returns:
            是否删除成功
        """
        user_upload_dir = os.path.join(
            self.upload_dir,
            str(user_id),
            str(upload_id)
        )

        try:
            if os.path.exists(user_upload_dir):
                shutil.rmtree(user_upload_dir)
                logger.info(f"User files deleted: user_id={user_id}, upload_id={upload_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete user files: {e}")
            return False

    def get_file_path(self, user_id: int, upload_id: int, filename: str) -> str:
        """获取用户文件的完整路径。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID
            filename: 文件名

        Returns:
            文件完整路径
        """
        return os.path.join(
            self.get_user_upload_dir(user_id, upload_id),
            filename
        )

    def file_exists(self, user_id: int, upload_id: int, filename: str) -> bool:
        """检查文件是否存在。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID
            filename: 文件名

        Returns:
            文件是否存在
        """
        file_path = self.get_file_path(user_id, upload_id, filename)
        return os.path.isfile(file_path)

    def get_file_size(self, user_id: int, upload_id: int, filename: str) -> int:
        """获取文件大小。

        Args:
            user_id: 用户ID
            upload_id: 上传记录ID
            filename: 文件名

        Returns:
            文件大小（字节），文件不存在返回0
        """
        file_path = self.get_file_path(user_id, upload_id, filename)
        if os.path.isfile(file_path):
            return os.path.getsize(file_path)
        return 0

    def list_user_upload_dirs(self, user_id: int) -> List[str]:
        """列出用户的所有上传目录。

        Args:
            user_id: 用户ID

        Returns:
            上传记录ID列表
        """
        user_base_dir = os.path.join(self.upload_dir, str(user_id))
        if not os.path.exists(user_base_dir):
            return []

        upload_dirs = []
        for item in os.listdir(user_base_dir):
            item_path = os.path.join(user_base_dir, item)
            if os.path.isdir(item_path):
                upload_dirs.append(item)

        return upload_dirs

    def cleanup_old_files(self, days: int = 30, db: Session = None) -> int:
        """清理超过指定天数的已完成上传文件。

        Args:
            days: 保留天数
            db: 数据库session（可选）

        Returns:
            清理的文件数量
        """
        from datetime import timedelta

        if db is None:
            logger.warning("Database session not provided, skipping cleanup")
            return 0

        try:
            from src.models import UserUpload
            cutoff_date = datetime.now() - timedelta(days=days)

            # 查询过期上传记录
            old_uploads = db.query(UserUpload).filter(
                UserUpload.created_at < cutoff_date,
                UserUpload.status == "completed"
            ).all()

            count = 0
            for upload in old_uploads:
                # 删除文件
                if self.delete_user_files(upload.user_id, upload.id):
                    count += 1
                    logger.info(f"Cleaned up old upload: user_id={upload.user_id}, upload_id={upload.id}")

            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0

    def get_total_user_storage(self, user_id: int) -> int:
        """获取用户使用的总存储空间（字节）。

        Args:
            user_id: 用户ID

        Returns:
            总存储空间（字节）
        """
        user_base_dir = os.path.join(self.upload_dir, str(user_id))
        if not os.path.exists(user_base_dir):
            return 0

        total_size = 0
        try:
            for root, dirs, files in os.walk(user_base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Failed to calculate user storage: {e}")

        return total_size

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名，移除不安全字符。

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 保留扩展名
        name, ext = os.path.splitext(filename)

        # 移除不安全字符
        safe_chars = "-_."
        name = ''.join(
            c for c in name
            if c.isalnum() or c in safe_chars or c.isspace()
        )

        # 替换空格为下划线
        name = name.replace(' ', '_')

        # 限制长度
        max_length = 100
        if len(name) > max_length:
            name = name[:max_length]

        return f"{name}{ext}"


# 向后兼容：保留原有的 FileService
class FileService:
    """原始文件服务（单用户模式，向后兼容）。

    保留此服务以支持单用户模式。
    """

    def __init__(self):
        """初始化文件服务"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.upload_dir = os.path.normpath(os.path.join(current_dir, "..", "uploads"))
        os.makedirs(self.upload_dir, exist_ok=True)

        self.allowed_extensions = {".csv", ".txt", ".xls", ".xlsx"}
        self.max_file_size = 50 * 1024 * 1024

    async def save_file(self, upload_file) -> str:
        """保存上传的文件"""
        file_extension = os.path.splitext(upload_file.filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"不支持的文件类型: {file_extension}")

        content = await upload_file.read()
        file_size = len(content)
        if file_size > self.max_file_size:
            raise ValueError(f"文件大小超过限制")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(self.upload_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"文件保存成功: {file_path}")
        return file_path

    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            os.remove(file_path)
            logger.info(f"文件删除成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {file_path}, 错误: {str(e)}")
            return False

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """获取文件信息"""
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
        """列出所有上传的文件"""
        files = []
        try:
            for file_name in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, file_name)
                if os.path.isfile(file_path):
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            files.sort(key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
        return files
