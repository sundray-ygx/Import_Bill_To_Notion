"""Authentication and authorization utilities."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
import bcrypt
from config import Config
import secrets
import logging

logger = logging.getLogger(__name__)

# bcrypt 配置
BCRYPT_ROUNDS = 12  # 计算成本，数值越高越安全但越慢


# ==================== 密码管理 ====================

def _prepare_password_for_bcrypt(password: str) -> bytes:
    """准备密码用于 bcrypt 哈希。

    bcrypt 算法限制密码最多 72 字节。对于 UTF-8 编码的字符串，
    需要确保字节长度不超过限制。

    Args:
        password: 原始密码

    Returns:
        密码的字节表示（确保长度 <= 72 字节）
    """
    # 将密码编码为 UTF-8 字节
    password_bytes = password.encode('utf-8')
    # 截断到 72 字节
    return password_bytes[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    try:
        # 准备密码
        password_bytes = _prepare_password_for_bcrypt(plain_password)
        # 将哈希字符串编码为字节
        hashed_bytes = hashed_password.encode('utf-8')
        # 验证密码
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希值。

    Args:
        password: 明文密码

    Returns:
        哈希后的密码（字符串格式）
    """
    try:
        # 准备密码
        password_bytes = _prepare_password_for_bcrypt(password)
        # 生成盐值并哈希
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        # 返回字符串格式的哈希
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """验证密码强度。

    Args:
        password: 待验证的密码

    Returns:
        (是否通过, 错误消息) - 错误消息为 None 表示通过
    """
    if len(password) < 8:
        return False, "至少8个字符"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not has_upper:
        return False, "至少一个大写字母"
    if not has_lower:
        return False, "至少一个小写字母"
    if not has_digit:
        return False, "至少一个数字"

    return True, None


def generate_random_password(length: int = 16) -> str:
    """生成随机密码。

    Args:
        length: 密码长度

    Returns:
        随机密码
    """
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


# ==================== Token管理 ====================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None, expires_minutes: Optional[int] = None) -> str:
    """创建访问token。

    Args:
        data: 要编码到token中的数据
        expires_delta: 过期时间增量（与 expires_minutes 二选一）
        expires_minutes: 过期分钟数（优先于 expires_delta）

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()

    if expires_minutes is not None:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    elif expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # 添加过期时间和签发时间
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # 生成token
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新token。

    Args:
        data: 要编码到token中的数据
        expires_delta: 过期时间增量（默认7天）

    Returns:
        JWT refresh token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    # 添加过期时间和类型标识
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    # 生成token
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码并验证token。

    Args:
        token: JWT token字符串

    Returns:
        解码后的payload，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            Config.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        logger.debug(f"Token decode failed: {e}")
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """验证访问token。

    Args:
        token: JWT access token字符串

    Returns:
        解码后的payload，验证失败返回None
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """验证刷新token。

    Args:
        token: JWT refresh token字符串

    Returns:
        解码后的payload，验证失败返回None
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """获取token的过期时间。

    Args:
        token: JWT token字符串

    Returns:
        过期时间（datetime），解析失败返回None
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


# ==================== 会话管理 ====================

class SessionManager:
    """会话管理器。"""

    @staticmethod
    def is_session_valid(expires_at: datetime) -> bool:
        """检查会话是否有效。

        Args:
            expires_at: 过期时间

        Returns:
            会话是否有效
        """
        return datetime.utcnow() < expires_at

    @staticmethod
    def revoke_session(db_session) -> bool:
        """撤销会话。

        Args:
            db_session: 数据库会话对象

        Returns:
            是否成功撤销
        """
        try:
            db_session.is_revoked = True
            return True
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

    @staticmethod
    def revoke_all_user_sessions(user_id: int, db) -> int:
        """撤销用户的所有会话。

        Args:
            user_id: 用户ID
            db: 数据库session

        Returns:
            撤销的会话数量
        """
        try:
            from models import UserSession

            count = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_revoked == False
            ).update({"is_revoked": True})

            db.commit()
            logger.info(f"Revoked {count} sessions for user {user_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to revoke user sessions: {e}")
            db.rollback()
            return 0

    @staticmethod
    def cleanup_expired_sessions(db, days: int = 7) -> int:
        """清理过期的会话记录。

        Args:
            db: 数据库session
            days: 保留天数

        Returns:
            删除的记录数
        """
        try:
            from models import UserSession
            from sqlalchemy import and_

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            count = db.query(UserSession).filter(
                and_(
                    UserSession.is_revoked == True,
                    UserSession.expires_at < cutoff_date
                )
            ).delete()

            db.commit()
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            db.rollback()
            return 0


# ==================== 密钥管理 ====================

def generate_secret_key() -> str:
    """生成随机的SECRET_KEY。

    Returns:
        64字符的随机密钥
    """
    return secrets.token_urlsafe(48)


def ensure_secret_key() -> str:
    """确保SECRET_KEY存在。

    如果配置中没有SECRET_KEY，生成一个新的并建议用户保存。

    Returns:
        SECRET_KEY
    """
    if not Config.SECRET_KEY:
        logger.warning("SECRET_KEY not configured, generating a temporary one")
        logger.warning("Please set SECRET_KEY in your .env file for production")
        return generate_secret_key()
    return Config.SECRET_KEY


# ==================== 登录安全 ====================

class LoginSecurity:
    """登录安全管理。"""

    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    @staticmethod
    def check_account_locked(user) -> Tuple[bool, Optional[datetime]]:
        """检查账户是否被锁定。

        Args:
            user: 用户对象

        Returns:
            (是否锁定, 锁定到期时间)
        """
        if not user.locked_until:
            return False, None

        if user.locked_until > datetime.utcnow():
            return True, user.locked_until

        # 锁定已过期，清除锁定状态
        user.locked_until = None
        user.login_attempts = 0
        return False, None

    @staticmethod
    def record_login_attempt(user, success: bool, db):
        """记录登录尝试。

        Args:
            user: 用户对象
            success: 是否登录成功
            db: 数据库session
        """
        if success:
            user.login_attempts = 0
            user.locked_until = None
        else:
            user.login_attempts = (user.login_attempts or 0) + 1

            # 达到最大尝试次数，锁定账户
            if user.login_attempts >= LoginSecurity.MAX_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=LoginSecurity.LOCKOUT_DURATION_MINUTES
                )
                logger.warning(f"User {user.username} locked due to too many failed attempts")

        db.commit()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试密码哈希
    password = "TestPass123"
    hashed = get_password_hash(password)
    print(f"Password hash: {hashed}")
    print(f"Verify: {verify_password(password, hashed)}")

    # 测试token
    Config.SECRET_KEY = "test-secret-key-for-development-only"
    data = {"sub": "123", "username": "test"}
    token = create_access_token(data)
    print(f"Token: {token}")

    payload = verify_access_token(token)
    print(f"Payload: {payload}")
