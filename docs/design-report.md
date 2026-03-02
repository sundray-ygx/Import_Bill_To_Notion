# 架构设计报告：邮箱账单自动导入功能

**报告版本**: v1.0
**生成时间**: 2025-01-02
**作者**: Design Agent
**设计方法**: 多方案对比 + 维度分析

---

## 目录

1. [方案对比与选择](#1-方案对比与选择)
2. [推荐方案详细设计](#2-推荐方案详细设计)
3. [数据库设计 (database-reviewer)](#3-数据库设计-database-reviewer)
4. [接口设计](#4-接口设计)
5. [安全设计](#5-安全设计)
6. [性能设计](#6-性能设计)
7. [技术选型](#7-技术选型)
8. [实施蓝图](#8-实施蓝图)

---

## 1. 方案对比与选择

### 1.1 三个架构方案

| 维度 | 方案 A: 独立模块 | 方案 B: 集成扩展 | 方案 C: 重构优化 |
|------|----------------|----------------|----------------|
| **侵入程度** | 最小 (~5%) | 中等 (~20%) | 深度 (~60%) |
| **开发周期** | 2-3 周 | 3-4 周 | 6-8 周 |
| **代码复用** | 低 | 高 | 很高 |
| **可维护性** | 中 | 高 | 很高 |
| **扩展性** | 中 | 高 | 很高 |
| **风险** | 低 | 中 | 高 |
| **适用场景** | 快速 MVP | **推荐** | 长期最优 |

### 1.2 方案 A: 独立模块架构

**架构图**:
```
┌─────────────────────────────────────────────────┐
│              Existing System                    │
│  (Web Service, Parsers, Importer, Scheduler)    │
└─────────────────────────────────────────────────┘
                    ▲
                    │ 调用
                    │
┌───────────────────┴─────────────────────────────┐
│          Email Module (Standalone)              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │Email Config │  │Email Import │  │ Scheduler│ │
│  │  Service    │  │  Service    │  │ Extension│ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
```

**特点**:
- 邮箱功能完全独立
- 通过调用现有 `importer.import_bill()` 集成
- 最小化对现有代码的修改

**优点**:
- 开发速度快
- 风险低
- 易于测试

**缺点**:
- 代码复用率低
- 可能存在功能重复
- 长期维护成本高

### 1.3 方案 B: 集成扩展架构 (推荐)

**架构图**:
```
┌─────────────────────────────────────────────────────────┐
│                    Web Service Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Auth   │  │  Users   │  │  Bills   │  │  Email  │ │
│  │  Routes  │  │  Routes  │  │  Routes  │  │ Routes  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌───────────────────────────┴─────────────────────────────┐
│                    Service Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ ImportSource│  │  Parser     │  │   Notion        │ │
│  │  (ABC)      │  │  System     │  │   Client        │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│         ▲                                               │
│         │ implements                                    │
│  ┌──────┴──────────┐  ┌─────────────┐                 │
│  │FileUploadSource │  │EmailImport  │                 │
│  │  (Existing)     │  │   Source    │                 │
│  └─────────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌───────────────────────────┴─────────────────────────────┐
│                    Data Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Users   │  │   User   │  │   Email  │  │Processed│ │
│  │          │  │ Configs  │  │ Configs  │  │ Emails  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

**特点**:
- 引入 `ImportSource` 抽象统一导入源
- 现有文件上传作为 `FileUploadSource`
- 新邮箱功能作为 `EmailImportSource`
- 深度复用解析器和 Notion 客户端

**优点**:
- 代码复用率高
- 架构清晰，扩展性强
- 长期维护成本低
- 支持未来多种导入源

**缺点**:
- 需要重构部分现有代码
- 开发周期较长
- 测试工作量较大

### 1.4 方案 C: 重构优化架构

**架构图**:
```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐ │
│  │    Web     │  │    CLI     │  │   API      │  │ Future │ │
│  │   UI       │  │  Interface │  │  Gateway   │  │   UI   │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌───────────────────────────┴─────────────────────────────────┐
│                      Application Layer                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Import Orchestrator                        ││
│  │  (Coordinates: ImportSource → Parser → Notion)          ││
│  └─────────────────────────────────────────────────────────┘│
│                           ▲                                 │
│                           │ implements                      │
│  ┌──────────────┬─────────┴──────────┬──────────────┐      │
│  │   File       │      Email         │    Future     │      │
│  │   Upload     │      Import        │    Sources    │      │
│  │   Source     │      Source        │              │      │
│  └──────────────┴────────────────────┴──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌───────────────────────────┴─────────────────────────────────┐
│                      Domain Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Parser    │  │  Notion     │  │   Crypto            │ │
│  │   Factory   │  │  Client     │  │   Service           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌───────────────────────────┴─────────────────────────────────┐
│                  Infrastructure Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │Database  │  │Scheduler │  │  File    │  │  Logging   │ │
│  │(ORM)     │  │          │  │  System  │  │            │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**特点**:
- 完整的 DDD (Domain-Driven Design) 分层架构
- 统一的导入抽象层
- 支持多种导入源
- 清晰的依赖方向

**优点**:
- 架构最优
- 扩展性最强
- 长期维护成本最低

**缺点**:
- 开发周期最长
- 工作量最大
- 风险最高

### 1.5 方案选择

**推荐方案**: 方案 B - 集成扩展架构

**选择理由**:
1. **平衡性最佳**: 在开发周期、代码复用、可维护性之间取得最佳平衡
2. **风险可控**: 中等侵入程度，不影响现有功能
3. **扩展性强**: 通过 `ImportSource` 抽象，易于添加新的导入源
4. **团队友好**: 架构清晰，易于理解和维护

---

## 2. 推荐方案详细设计

### 2.1 核心模块设计

#### 2.1.1 ImportSource 抽象

```python
# src/services/import_source.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path

class ImportSource(ABC):
    """导入源抽象基类"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    @abstractmethod
    def fetch_bills(self) -> List[Dict]:
        """
        获取账单文件列表

        Returns:
            List[Dict]: 账单文件列表，每项包含:
                - file_path: 文件路径
                - platform: 平台标识
                - metadata: 元数据（如邮件 ID、发件人等）
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """返回导入源类型"""
        pass

    def import_bills(self) -> Dict:
        """
        导入账单（模板方法）

        Returns:
            Dict: 导入结果统计
        """
        from src.importer import import_bill

        bills = self.fetch_bills()

        results = {
            'total': len(bills),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for bill in bills:
            try:
                result = import_bill(
                    file_path=bill['file_path'],
                    platform=bill.get('platform'),
                    user_id=self.user_id
                )
                results['success'] += 1
                results['details'].append({
                    'file': bill['file_path'],
                    'status': 'success',
                    'imported': result.get('imported_count', 0)
                })
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'file': bill['file_path'],
                    'status': 'failed',
                    'error': str(e)
                })

        return results
```

#### 2.1.2 FileUploadSource (现有功能封装)

```python
# src/services/file_upload_source.py
from src.services.import_source import ImportSource
from src.services.user_file_service import UserFileService
from typing import List, Dict

class FileUploadSource(ImportSource):
    """文件上传导入源（封装现有功能）"""

    def __init__(self, user_id: int, db: Session, upload_id: str = None):
        super().__init__(user_id, db)
        self.upload_id = upload_id
        self.file_service = UserFileService(db)

    def fetch_bills(self) -> List[Dict]:
        """获取用户上传的账单文件"""
        uploads = self.file_service.list_uploads(
            self.user_id,
            self.upload_id
        )

        return [
            {
                'file_path': upload.file_path,
                'platform': upload.platform if upload.platform else None,
                'metadata': {
                    'upload_id': upload.upload_id,
                    'filename': upload.filename,
                    'uploaded_at': upload.uploaded_at.isoformat()
                }
            }
            for upload in uploads
        ]

    def get_source_type(self) -> str:
        return "file_upload"
```

#### 2.1.3 EmailImportSource (新增)

```python
# src/services/email_import_source.py
from src.services.import_source import ImportSource
from src.models import EmailConfig, ProcessedEmail
from typing import List, Dict
import tempfile

class EmailImportSource(ImportSource):
    """邮箱导入源"""

    def __init__(self, user_id: int, db: Session, config_id: int = None):
        super().__init__(user_id, db)
        self.config_id = config_id

    def fetch_bills(self) -> List[Dict]:
        """从邮箱获取账单"""
        # 获取邮箱配置
        configs = []
        if self.config_id:
            config = self.db.query(EmailConfig).filter(
                EmailConfig.id == self.config_id,
                EmailConfig.user_id == self.user_id,
                EmailConfig.is_active == True
            ).first()
            if config:
                configs = [config]
        else:
            configs = self.db.query(EmailConfig).filter(
                EmailConfig.user_id == self.user_id,
                EmailConfig.is_active == True,
                EmailConfig.is_verified == True
            ).all()

        bills = []

        for config in configs:
            # 处理每个邮箱配置
            config_bills = self._fetch_from_config(config)
            bills.extend(config_bills)

        return bills

    def _fetch_from_config(self, config: EmailConfig) -> List[Dict]:
        """从单个邮箱配置获取账单"""
        from src.services.email_service import EmailService
        from src.services.email_parse_service import EmailParseService

        email_service = EmailService()
        mailbox = email_service.connect(config)

        # 获取最近 50 封邮件
        emails = list(mailbox.fetch(limit=50))

        bills = []

        for msg in emails:
            # 检查是否已处理
            if self._is_processed(msg.uid, config.id):
                continue

            # 判断是否为账单邮件
            bill_info = EmailParseService.is_bill_email(msg)
            if not bill_info:
                continue

            # 提取附件
            attachments = EmailParseService.extract_attachments(msg)
            if not attachments:
                continue

            # 下载附件到临时文件
            for att in attachments:
                temp_file = self._download_attachment(att)

                bills.append({
                    'file_path': temp_file,
                    'platform': bill_info['platform'],
                    'metadata': {
                        'message_id': msg.uid,
                        'config_id': config.id,
                        'from_addr': str(msg.from_),
                        'subject': msg.subject,
                        'date': msg.date_str,
                        'attachment_name': att['filename']
                    }
                })

        mailbox.logout()
        return bills

    def _download_attachment(self, attachment: Dict) -> str:
        """下载附件到临时文件"""
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=attachment['filename']
        ) as f:
            f.write(attachment['payload'])
            return f.name

    def _is_processed(self, message_id: str, config_id: int) -> bool:
        """检查邮件是否已处理"""
        processed = self.db.query(ProcessedEmail).filter(
            ProcessedEmail.message_id == message_id,
            ProcessedEmail.email_config_id == config_id
        ).first()
        return processed is not None

    def get_source_type(self) -> str:
        return "email"
```

### 2.2 辅助服务设计

#### 2.2.1 EmailService (邮箱连接服务)

```python
# src/services/email_service.py
from imap_tools import MailBox
from src.models import EmailConfig
from src.utils.crypto import PasswordEncryption

class EmailService:
    """邮箱连接服务"""

    def connect(self, config: EmailConfig) -> MailBox:
        """
        连接到邮箱

        Args:
            config: 邮箱配置

        Returns:
            MailBox: IMAP 连接对象

        Raises:
            ConnectionError: 连接失败
        """
        # 解密密码
        crypto = PasswordEncryption()
        password = crypto.decrypt(config.password_encrypted)

        # 连接邮箱
        mailbox = MailBox(config.imap_server)
        try:
            mailbox.login(config.email_address, password)
            return mailbox
        except Exception as e:
            raise ConnectionError(f"邮箱连接失败: {e}")

    def verify_connection(self, config: EmailConfig) -> Dict:
        """
        验证邮箱连接

        Args:
            config: 邮箱配置

        Returns:
            Dict: 验证结果
        """
        try:
            mailbox = self.connect(config)
            mailbox.logout()
            return {
                'success': True,
                'message': '连接成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接失败: {e}'
            }
```

#### 2.2.2 EmailParseService (邮件解析服务)

```python
# src/services/email_parse_service.py
import re
from typing import Optional, Dict, List
from imap_tools import MailMessage

class EmailParseService:
    """邮件解析服务"""

    # 发件人白名单
    SENDERS_WHITELIST = {
        'alipay': ['alipay@alipay.com', 'service@alipay.com'],
        'wechat': ['weixinpay@wechat.com', 'pay@wechat.com'],
        'unionpay': ['unionpay@95516.com', 'service@95516.com']
    }

    # 密码提取正则表达式
    PASSWORD_PATTERNS = [
        r'密码[：:]\s*([A-Za-z0-9]{6,20})',
        r'解压密码[：:]\s*([A-Za-z0-9]{6,20})',
        r'password[：:]\s*([A-Za-z0-9]{6,20})',
    ]

    @classmethod
    def is_bill_email(cls, msg: MailMessage) -> Optional[Dict]:
        """判断是否为账单邮件"""
        from_addr = msg.from_
        if not from_addr:
            return None

        from_email = str(from_addr).lower()

        for platform, senders in cls.SENDERS_WHITELIST.items():
            if any(sender in from_email for sender in senders):
                return {'platform': platform}

        return None

    @classmethod
    def extract_password(cls, email_body: str) -> Optional[str]:
        """从邮件正文提取解压密码"""
        for pattern in cls.PASSWORD_PATTERNS:
            match = re.search(pattern, email_body)
            if match:
                return match.group(1)
        return None

    @classmethod
    def extract_attachments(cls, msg: MailMessage) -> List[Dict]:
        """提取邮件附件"""
        attachments = []

        for att in msg.attachments:
            filename = att.filename
            if not filename:
                continue

            if not (filename.endswith('.csv') or filename.endswith('.zip')):
                continue

            attachments.append({
                'filename': filename,
                'payload': att.payload,
                'content_type': att.content_type
            })

        return attachments
```

#### 2.2.3 CryptoService (加密服务)

```python
# src/utils/crypto.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class PasswordEncryption:
    """密码加密工具"""

    def __init__(self, master_key: str = None):
        """初始化加密器"""
        self.master_key = master_key or os.getenv("PASSWORD_ENCRYPTION_KEY")
        if not self.master_key:
            raise ValueError("PASSWORD_ENCRYPTION_KEY not set")

        # 从主密钥派生 Fernet 密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'notion_bill_importer',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, password: str) -> str:
        """加密密码"""
        encrypted = self.cipher.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码"""
        encrypted = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
```

### 2.3 调度器扩展

```python
# src/scheduler.py (扩展)

class BillScheduler:
    """账单导入调度器（扩展邮箱支持）"""

    def add_email_check_job(self, config_id: int, frequency: str):
        """添加邮箱检查任务"""
        cron_map = {
            'hourly': '0 * * * *',
            'daily': '0 0 * * *',
            'weekly': '0 0 * * 0'
        }

        cron_expr = cron_map.get(frequency, '0 * * * *')
        job_id = f"email_check_{config_id}"

        self.scheduler.add_job(
            func=self._check_email,
            trigger=CronTrigger.from_crontab(cron_expr),
            id=job_id,
            name=f"Email check job for config {config_id}",
            replace_existing=True,
            kwargs={'config_id': config_id}
        )

    def remove_email_check_job(self, config_id: int):
        """移除邮箱检查任务"""
        job_id = f"email_check_{config_id}"
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass

    def _check_email(self, config_id: int):
        """检查邮箱并导入账单"""
        from src.services.email_import_source import EmailImportSource
        from src.services.database import get_db

        db = next(get_db())
        try:
            # 获取配置所属用户
            config = db.query(EmailConfig).filter(
                EmailConfig.id == config_id
            ).first()

            if not config:
                return

            # 执行导入
            source = EmailImportSource(config.user_id, db, config_id)
            result = source.import_bills()

            # 更新配置状态
            config.last_check_at = datetime.utcnow()
            config.last_check_status = 'success' if result['failed'] == 0 else 'partial'
            db.commit()

        finally:
            db.close()
```

---

## 3. 数据库设计 (database-reviewer)

### 3.1 表结构设计

#### 3.1.1 user_email_configs (邮箱配置表)

```sql
CREATE TABLE user_email_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    password_encrypted VARCHAR(500) NOT NULL,
    imap_server VARCHAR(255) NOT NULL,
    imap_port INTEGER DEFAULT 993,
    use_ssl BOOLEAN DEFAULT TRUE,
    provider VARCHAR(50),
    config_name VARCHAR(100) DEFAULT '默认邮箱',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_check_at DATETIME,
    last_check_status VARCHAR(20),
    check_frequency VARCHAR(20) DEFAULT 'hourly',
    next_check_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_email_configs_user_id ON user_email_configs(user_id);
CREATE INDEX idx_email_configs_is_active ON user_email_configs(is_active);
```

**Database-Reviewer 分析**:

1. **规范化分析**: 5/5
   - 符合第三范式 (3NF)
   - 无传递依赖
   - 主键选择合理

2. **索引策略**:
   - `user_id`: 高频查询条件 ✅
   - `is_active`: 过滤活跃配置 ✅
   - 建议添加复合索引: `(user_id, is_active)`

3. **查询优化**:
   - 常见查询: `WHERE user_id = ? AND is_active = TRUE`
   - 建议复合索引提升性能

4. **安全建议**:
   - `password_encrypted` 使用 AES-256-GCM
   - 密钥从环境变量读取
   - 不在日志中记录密码

#### 3.1.2 email_processing_history (邮件处理历史表)

```sql
CREATE TABLE email_processing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_config_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_id VARCHAR(500) NOT NULL UNIQUE,
    message_date DATETIME,
    platform VARCHAR(20),
    attachment_name VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    import_history_id INTEGER,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_config_id) REFERENCES user_email_configs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (import_history_id) REFERENCES import_history(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_email_history_user_id ON email_processing_history(user_id);
CREATE INDEX idx_email_history_message_id ON email_processing_history(message_id);
CREATE INDEX idx_email_history_status ON email_processing_history(status);
CREATE INDEX idx_email_history_config_id ON email_processing_history(email_config_id);
```

**Database-Reviewer 分析**:

1. **规范化分析**: 5/5
   - 符合第三范式 (3NF)
   - 外键关系清晰
   - 级联删除策略合理

2. **索引策略**:
   - `message_id`: UNIQUE 约束防止重复处理 ✅
   - `user_id`: 用户查询历史 ✅
   - `status`: 状态过滤 ✅
   - `email_config_id`: 配置关联查询 ✅

3. **查询优化**:
   - 去重查询: `WHERE message_id = ?` 使用唯一索引
   - 历史查询: `WHERE user_id = ? ORDER BY processed_at DESC`

4. **数据归档建议**:
   - 建议定期归档 6 个月前的成功记录
   - 保留失败记录用于问题排查

### 3.2 现有表扩展

#### 3.2.1 user_uploads (用户上传表)

```sql
-- 添加字段
ALTER TABLE user_uploads ADD COLUMN source_type VARCHAR(20) DEFAULT 'file_upload';
ALTER TABLE user_uploads ADD COLUMN source_metadata TEXT;

-- 索引
CREATE INDEX idx_uploads_source_type ON user_uploads(source_type);
```

**说明**:
- `source_type`: 标识来源 ('file_upload' 或 'email')
- `source_metadata`: JSON 格式的元数据

---

## 4. 接口设计

### 4.1 邮箱配置 API

#### 4.1.1 创建邮箱配置

```
POST /api/email/config

Request:
{
  "email_address": "user@example.com",
  "password": "email_password",
  "imap_server": "imap.example.com",
  "imap_port": 993,
  "use_ssl": true,
  "provider": "custom",
  "config_name": "我的邮箱"
}

Response (200):
{
  "id": 1,
  "email_address": "user@example.com",
  "is_verified": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}

Response (400):
{
  "detail": "邮箱地址格式无效"
}
```

#### 4.1.2 获取邮箱配置列表

```
GET /api/email/configs

Response (200):
{
  "configs": [
    {
      "id": 1,
      "email_address": "user@example.com",
      "imap_server": "imap.example.com",
      "provider": "custom",
      "config_name": "我的邮箱",
      "is_active": true,
      "is_verified": true,
      "last_check_at": "2025-01-01T12:00:00Z",
      "last_check_status": "success",
      "check_frequency": "hourly",
      "next_check_at": "2025-01-01T13:00:00Z"
    }
  ]
}
```

#### 4.1.3 验证邮箱连接

```
POST /api/email/config/{config_id}/verify

Response (200):
{
  "success": true,
  "message": "连接成功"
}

Response (400):
{
  "success": false,
  "message": "认证失败，请检查邮箱地址和密码"
}
```

### 4.2 邮件处理 API

#### 4.2.1 手动触发邮件检查

```
POST /api/email/check

Request:
{
  "config_id": 1  // 可选，不指定则检查所有启用的配置
}

Response (200):
{
  "success": true,
  "processed": 5,
  "imported": 3,
  "skipped": 2,
  "failed": 0
}
```

#### 4.2.2 获取已处理邮件列表

```
GET /api/email/processed?page=1&page_size=20

Response (200):
{
  "emails": [
    {
      "id": 1,
      "message_id": "message-id@example.com",
      "message_date": "2025-01-01T00:00:00Z",
      "platform": "alipay",
      "attachment_name": "alipay_bill.csv",
      "status": "success",
      "processed_at": "2025-01-01T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 4.3 邮箱服务商模板 API

```
GET /api/email/providers

Response (200):
{
  "providers": [
    {
      "id": "qq",
      "name": "QQ邮箱",
      "imap_server": "imap.qq.com",
      "imap_port": 993,
      "use_ssl": true,
      "help_url": "https://service.mail.qq.com/cgi-bin/help"
    },
    {
      "id": "163",
      "name": "网易163邮箱",
      "imap_server": "imap.163.com",
      "imap_port": 993,
      "use_ssl": true,
      "help_url": "http://help.mail.163.com/"
    }
  ]
}
```

---

## 5. 安全设计

### 5.1 凭证加密

**算法**: AES-256-GCM

**密钥派生**: PBKDF2-SHA256

```python
# 密钥派生
kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'notion_bill_importer',  # 生产环境应使用随机 salt
    iterations=100000,
)
key = kdf.derive(master_key.encode())

# 加密
cipher = Cipher(
    algorithms.AES(key),
    modes.GCM(nonce),
)
encryptor = cipher.encryptor()
ciphertext = encryptor.update(plaintext) + encryptor.finalize()
```

### 5.2 传输加密

- **IMAP**: 强制使用 IMAPS (SSL/TLS)
- **API**: 强制使用 HTTPS
- **证书验证**: 启用 SSL 证书验证

### 5.3 权限控制

- **JWT 认证**: 所有 API 需要 token
- **用户隔离**: 用户只能访问自己的邮箱配置
- **审计日志**: 记录所有敏感操作

---

## 6. 性能设计

### 6.1 异步处理

```python
from fastapi import BackgroundTasks

@router.post("/api/email/check")
async def check_email(
    config_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """异步检查邮箱"""
    background_tasks.add_task(
        _check_email_background,
        current_user.id,
        config_id
    )
    return {"message": "邮箱检查已启动"}
```

### 6.2 连接池管理

```python
# 使用 IMAP 连接复用
class EmailConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.pool = {}
        self.max_connections = max_connections

    def get_connection(self, config_id: int):
        # 复用现有连接
        pass

    def release_connection(self, config_id: int):
        # 释放连接
        pass
```

### 6.3 批处理优化

- 邮件批量获取 (每次 50 封)
- Notion 批量导入 (每批 10 条)
- 数据库批量插入

---

## 7. 技术选型

### 7.1 Python 库

| 功能 | 推荐库 | 版本 | 理由 |
|------|--------|------|------|
| IMAP 客户端 | imap-tools | 0.51+ | 现代 Pythonic API，支持上下文管理器 |
| 加密 | cryptography | 41.0+ | 官方推荐，支持 AES-256-GCM |
| HTML 解析 | beautifulsoup4 | 4.12+ | 解析邮件 HTML 内容 |

### 7.2 更新 requirements.txt

```txt
# 新增依赖
imap-tools==0.51.0
cryptography==41.0.0
beautifulsoup4==4.12.0
```

---

## 8. 实施蓝图

### 8.1 六阶段实施计划

#### 阶段 1: 基础设施 (3-4 天)

**目标**: 建立数据基础和核心抽象

**任务**:
1. 创建数据库迁移脚本
2. 添加 `ImportSource` 抽象类
3. 实现 `FileUploadSource` 封装
4. 添加加密工具 `CryptoService`

**交付物**:
- 数据库迁移脚本
- `import_source.py`
- `file_upload_source.py`
- `crypto.py`

#### 阶段 2: 邮箱核心功能 (5-6 天)

**目标**: 实现邮箱连接和解析

**任务**:
1. 实现 `EmailService`
2. 实现 `EmailParseService`
3. 实现 `EmailImportSource`
4. 单元测试

**交付物**:
- `email_service.py`
- `email_parse_service.py`
- `email_import_source.py`
- 单元测试

#### 阶段 3: 调度和自动化 (2-3 天)

**目标**: 实现自动检查

**任务**:
1. 扩展 `BillScheduler`
2. 实现邮箱检查任务
3. 错误恢复机制

**交付物**:
- 更新的 `scheduler.py`
- 集成测试

#### 阶段 4: Web API 和 UI (4-5 天)

**目标**: 实现用户界面

**任务**:
1. 创建 `email.py` 路由
2. 扩展设置页面
3. 添加邮箱配置表单
4. 前端交互逻辑

**交付物**:
- `routes/email.py`
- 更新的 `settings.html`
- 更新的 `settings.js`
- 更新的 `settings.css`

#### 阶段 5: 测试和优化 (3-4 天)

**目标**: 确保质量

**任务**:
1. 单元测试
2. 集成测试
3. 端到端测试
4. 性能测试
5. 安全测试

**交付物**:
- 测试报告
- 性能报告

#### 阶段 6: 部署和监控 (1-2 天)

**目标**: 上线

**任务**:
1. 部署配置
2. 监控配置
3. 文档更新
4. 用户手册

**交付物**:
- 部署文档
- 用户手册

### 8.2 时间估算

| 阶段 | 工作量 | 累计 |
|------|--------|------|
| 阶段 1 | 3-4 天 | 4 天 |
| 阶段 2 | 5-6 天 | 10 天 |
| 阶段 3 | 2-3 天 | 13 天 |
| 阶段 4 | 4-5 天 | 18 天 |
| 阶段 5 | 3-4 天 | 22 天 |
| 阶段 6 | 1-2 天 | 24 天 |

**总计**: 约 3-4 周

### 8.3 依赖关系

```
阶段 1 (基础设施)
    │
    ├─→ 阶段 2 (邮箱核心功能)
    │       │
    │       └─→ 阶段 3 (调度和自动化)
    │               │
    │               └─→ 阶段 4 (Web API 和 UI)
    │                       │
    │                       └─→ 阶段 5 (测试和优化)
    │                               │
    │                               └─→ 阶段 6 (部署和监控)
```

---

## 9. 总结

本架构设计报告为"邮箱账单自动导入"功能提供了：

1. **三个方案对比**: 独立模块、集成扩展、重构优化
2. **推荐方案**: 集成扩展架构 (方案 B)
3. **核心模块设计**: ImportSource 抽象、邮箱服务、解析服务
4. **数据库设计**: 完整的表结构和索引策略
5. **接口设计**: RESTful API 规范
6. **安全设计**: 加密、传输、权限控制
7. **性能设计**: 异步、连接池、批处理
8. **实施蓝图**: 6 个阶段，约 3-4 周

---

**报告生成时间**: 2025-01-02
**报告版本**: v1.0
**作者**: Design Agent
