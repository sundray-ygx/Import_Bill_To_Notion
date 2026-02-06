"""
Dashboard API路由 - 财务指挥中心数据接口
提供统计数据、最近活动等信息
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db
from dependencies import get_current_user
from models import User, ImportHistory
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取仪表板统计数据

    返回数据：
    - monthlyIncome: 本月收入
    - monthlyExpense: 本月支出
    - netBalance: 净余额
    - transactionCount: 交易笔数
    - incomeTrend: 收入趋势（对比上月）
    - expenseTrend: 支出趋势（对比上月）
    """
    try:
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)

        # 获取用户的导入历史
        import_history = db.query(ImportHistory).filter(
            ImportHistory.user_id == current_user.id
        ).all()

        # 初始化统计数据
        monthly_income = 0.0
        monthly_expense = 0.0
        last_month_income = 0.0
        last_month_expense = 0.0
        transaction_count = 0

        # 统计本月数据
        for history in import_history:
            if history.created_at and history.created_at >= current_month_start:
                if history.income_count:
                    monthly_income += history.income_total or 0
                if history.expense_count:
                    monthly_expense += history.expense_total or 0
                if history.total_count:
                    transaction_count += history.total_count

        # 统计上月数据
        for history in import_history:
            if history.created_at and last_month_start <= history.created_at < current_month_start:
                if history.income_count:
                    last_month_income += history.income_total or 0
                if history.expense_count:
                    last_month_expense += history.expense_total or 0

        # 计算净余额
        net_balance = monthly_income - monthly_expense

        # 计算趋势
        income_trend = last_month_income if last_month_income > 0 else None
        expense_trend = last_month_expense if last_month_expense > 0 else None

        return {
            "success": True,
            "data": {
                "monthlyIncome": round(monthly_income, 2),
                "monthlyExpense": round(monthly_expense, 2),
                "netBalance": round(net_balance, 2),
                "transactionCount": transaction_count,
                "incomeTrend": income_trend,
                "expenseTrend": expense_trend
            }
        }
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")


@router.get("/activity")
async def get_recent_activity(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最近活动列表

    返回最近的活动记录，包括：
    - 账单导入
    - 复盘生成
    - 配置更新等
    """
    try:
        # 获取最近的导入历史记录
        recent_history = db.query(ImportHistory).filter(
            ImportHistory.user_id == current_user.id
        ).order_by(ImportHistory.started_at.desc()).limit(limit).all()

        activities = []
        for history in recent_history:
            # 根据状态确定活动类型和状态
            if history.status == "success":
                activity_type = "import"
                status = "success"
                platform_name = history.platform or "未知平台"
                title = f"成功导入{platform_name}账单"
                record_count = history.total_count or 0
                description = f"导入 {record_count} 条记录"
            elif history.status == "failed":
                activity_type = "error"
                status = "error"
                platform_name = history.platform or "未知平台"
                title = f"{platform_name}账单导入失败"
                description = history.error_message or "文件格式不正确"
            else:
                activity_type = "import"
                status = "pending"
                platform_name = history.platform or "未知平台"
                title = f"正在导入{platform_name}账单"
                description = "处理中..."

            # 计算时间差
            if history.started_at:
                time_diff = datetime.now(timezone.utc) - history.started_at
                if time_diff.days > 0:
                    time_str = f"{time_diff.days}天前"
                elif time_diff.seconds >= 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours}小时前"
                elif time_diff.seconds >= 60:
                    minutes = time_diff.seconds // 60
                    time_str = f"{minutes}分钟前"
                else:
                    time_str = "刚刚"
            else:
                time_str = "未知"

            activities.append({
                "type": activity_type,
                "title": title,
                "description": description,
                "time": time_str,
                "status": status
            })

        # 如果没有活动，返回默认欢迎信息
        if not activities:
            activities.append({
                "type": "info",
                "title": "欢迎使用账单管理系统",
                "description": "上传您的第一个账单文件开始使用",
                "time": "刚刚",
                "status": "info"
            })

        return {
            "success": True,
            "data": activities[:limit]
        }
    except Exception as e:
        logger.error(f"获取活动记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取活动记录失败")


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取仪表板概览信息

    返回系统整体概况：
    - 总导入次数
    - 成功率
    - 最近活动时间
    """
    try:
        # 统计总导入次数
        total_imports = db.query(func.count(ImportHistory.id)).filter(
            ImportHistory.user_id == current_user.id
        ).scalar()

        # 统计成功次数
        success_imports = db.query(func.count(ImportHistory.id)).filter(
            and_(
                ImportHistory.user_id == current_user.id,
                ImportHistory.status == "success"
            )
        ).scalar()

        # 计算成功率
        success_rate = (success_imports / total_imports * 100) if total_imports > 0 else 0

        # 获取最近活动时间
        latest_history = db.query(ImportHistory).filter(
            ImportHistory.user_id == current_user.id
        ).order_by(ImportHistory.created_at.desc()).first()

        latest_activity = None
        if latest_history and latest_history.created_at:
            latest_activity = latest_history.created_at.isoformat()

        return {
            "success": True,
            "data": {
                "totalImports": total_imports,
                "successImports": success_imports,
                "successRate": round(success_rate, 2),
                "latestActivity": latest_activity
            }
        }
    except Exception as e:
        logger.error(f"获取概览信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取概览信息失败")
