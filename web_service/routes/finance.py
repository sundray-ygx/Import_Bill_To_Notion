"""财务分析API路由 - 提供个人财务分析数据接口（带缓存）"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from collections import defaultdict
import statistics
import time

from src.services.dependencies import get_current_active_user, get_db
from src.models import User

router = APIRouter()

# ==================== 内存缓存 ====================
_cache = {}
CACHE_TTL = 3600  # 1小时

YEARS = ["2022", "2023", "2024", "2025", "2026"]

def _cache_key(user_id, api_name, year=None):
    parts = [str(user_id), api_name]
    if year:
        parts.append(str(year))
    return ":".join(parts)

def _get_cached(key):
    entry = _cache.get(key)
    if entry and entry["expire"] > time.time():
        return entry["data"]
    if entry:
        del _cache[key]
    return None

def _set_cached(key, data):
    _cache[key] = {"data": data, "expire": time.time() + CACHE_TTL}

# ==================== Notion API ====================
import urllib.request
import json

NOTION_KEY = os.getenv("NOTION_API_KEY", "")
EXPENSE_DB = os.getenv("NOTION_EXPENSE_DATABASE_ID", "")
INCOME_DB = os.getenv("NOTION_INCOME_DATABASE_ID", "")

EXCLUDE_CATEGORIES = {"购买理财通", "转入零钱通-来自零钱", "零钱通转出"}
FIXED_CATEGORIES = {"房贷", "公积金还贷", "物业费", "保险", "日常生活费"}


def _get_notion_key(user_id=None):
    if user_id:
        from src.services.database import get_db_context
        from src.models import UserNotionConfig
        with get_db_context() as db:
            config = db.query(UserNotionConfig).filter(
                UserNotionConfig.user_id == user_id
            ).first()
            if config and config.notion_api_key:
                return config.notion_api_key, config.notion_income_database_id, config.notion_expense_database_id
    return NOTION_KEY, INCOME_DB, EXPENSE_DB


def _query_notion(db_id, year, api_key, category=None):
    """Query Notion with raw data cache."""
    raw_key = f"raw:{api_key[-8:]}:{db_id[-8:]}:{year}:{category or 'all'}"
    cached = _get_cached(raw_key)
    if cached is not None:
        return cached

    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    results = []
    filters = [
        {"property": "Date", "date": {"on_or_after": f"{year}-01-01"}},
        {"property": "Date", "date": {"before": f"{int(year)+1}-01-01"}}
    ]
    if category:
        filters.append({"property": "Category", "select": {"equals": category}})
    body = {"page_size": 100, "filter": {"and": filters}}
    cursor = None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(url, method="POST",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    _set_cached(raw_key, results)
    return results


def _ext(props, key, ptype):
    p = props.get(key, {})
    if ptype == "number": return p.get("number") or 0
    elif ptype == "select":
        s = p.get("select"); return s.get("name", "") if s else ""
    elif ptype == "date":
        d = p.get("date"); return d.get("start", "") if d else ""
    elif ptype == "title":
        t = p.get("title", []); return t[0].get("plain_text", "") if t else ""
    return ""


def _is_prepayment(name, category, price):
    return "提前还贷" in str(name) or (category == "房贷" and price > 20000)


def _parse_expense(pages):
    """Parse expense pages into monthly/category data."""
    monthly = defaultdict(float)
    cats = defaultdict(float)
    total = 0; prepay = 0; excluded = 0; fixed = 0; variable = 0
    for p in pages:
        props = p.get("properties", {})
        price = _ext(props, "Price", "number")
        date = _ext(props, "Date", "date")
        cat = _ext(props, "Category", "select")
        name = _ext(props, "Name", "title")
        if not date: continue
        m = date[:7]
        if cat in EXCLUDE_CATEGORIES:
            excluded += price
        elif _is_prepayment(name, cat, price):
            prepay += price
        else:
            total += price
            monthly[m] += price
            cats[cat] += price
            if cat in FIXED_CATEGORIES:
                fixed += price
            else:
                variable += price
    return {"total": total, "monthly": dict(monthly), "cats": dict(cats),
            "excluded": excluded, "prepay": prepay, "fixed": fixed, "variable": variable}


def _parse_income(pages):
    """Parse income pages into monthly/category data."""
    monthly = defaultdict(float)
    cats = defaultdict(float)
    total = 0; excluded = 0
    for p in pages:
        props = p.get("properties", {})
        price = _ext(props, "Price", "number")
        date = _ext(props, "Date", "date")
        cat = _ext(props, "Category", "select")
        if not date: continue
        m = date[:7]
        if cat in EXCLUDE_CATEGORIES:
            excluded += price
        else:
            total += price
            monthly[m] += price
            cats[cat] += price
    return {"total": total, "monthly": dict(monthly), "cats": dict(cats), "excluded": excluded}


# ==================== 合并的历年对比接口 ====================

@router.get("/all-years")
async def all_years_data(
    refresh: int = Query(0),
    current_user: User = Depends(get_current_active_user)
):
    """一次性返回所有历年对比数据（收入结构、支出结构、房贷、稳定性）"""
    cache_k = _cache_key(current_user.id, "all-years")
    if not refresh:
        cached = _get_cached(cache_k)
        if cached is not None:
            return cached

    api_key, inc_db, exp_db = _get_notion_key(current_user.id)

    # 批量查询所有年份数据（raw cache 会命中后续请求）
    income_structure = {}
    expense_structure = {}
    mortgage = {}
    stability = {}

    for year in YEARS:
        # Income
        inc_pages = _query_notion(inc_db, year, api_key)
        inc = _parse_income(inc_pages)
        income_structure[year] = {k: round(v, 2) for k, v in
            sorted(inc["cats"].items(), key=lambda x: x[1], reverse=True)}

        # Expense
        exp_pages = _query_notion(exp_db, year, api_key)
        exp = _parse_expense(exp_pages)
        expense_structure[year] = {k: round(v, 2) for k, v in
            sorted(exp["cats"].items(), key=lambda x: x[1], reverse=True)}

        # Mortgage
        mort_pages = _query_notion(exp_db, year, api_key, category="房贷")
        m_total = 0; m_normal = 0; m_prepay = 0; m_count = 0
        for p in mort_pages:
            props = p.get("properties", {})
            price = _ext(props, "Price", "number")
            name = _ext(props, "Name", "title")
            m_total += price
            if _is_prepayment(name, "房贷", price):
                m_prepay += price
            else:
                m_normal += price
                m_count += 1
        n_months = 12 if year != "2026" else 5
        mortgage[year] = {
            "total": round(m_total, 2), "normal": round(m_normal, 2),
            "prepayment": round(m_prepay, 2),
            "monthly_avg": round(m_normal / n_months, 2) if n_months > 0 else 0,
            "count": m_count
        }

        # Stability
        monthly_vals = list(exp["monthly"].values())
        if monthly_vals:
            stability[year] = {
                "avg": round(statistics.mean(monthly_vals), 2),
                "std_dev": round(statistics.stdev(monthly_vals), 2) if len(monthly_vals) > 1 else 0,
                "min": round(min(monthly_vals), 2),
                "max": round(max(monthly_vals), 2),
                "months": len(monthly_vals)
            }

    result = {
        "income_structure": income_structure,
        "expense_structure": expense_structure,
        "mortgage": mortgage,
        "stability": stability
    }
    _set_cached(cache_k, result)
    return result


# ==================== 年度概览 ====================

@router.get("/overview")
async def finance_overview(
    year: str = Query("2025"),
    refresh: int = Query(0),
    current_user: User = Depends(get_current_active_user)
):
    """年度财务概览"""
    api_key, inc_db, exp_db = _get_notion_key(current_user.id)

    cache_k = _cache_key(current_user.id, "overview", year)
    if not refresh:
        cached = _get_cached(cache_k)
        if cached is not None:
            return cached

    exp_pages = _query_notion(exp_db, year, api_key)
    inc_pages = _query_notion(inc_db, year, api_key)

    exp = _parse_expense(exp_pages)
    inc = _parse_income(inc_pages)

    total_inc = inc["total"]
    total_exp = exp["total"]
    balance = total_inc - total_exp
    savings_rate = balance / total_inc * 100 if total_inc > 0 else 0

    all_months = sorted(set(list(inc["monthly"].keys()) + list(exp["monthly"].keys())))
    n_months = len(all_months) or 1

    result = {
        "year": year,
        "total_income": round(total_inc, 2),
        "total_expense": round(total_exp, 2),
        "balance": round(balance, 2),
        "savings_rate": round(savings_rate, 1),
        "monthly_income": {k: round(v, 2) for k, v in sorted(inc["monthly"].items())},
        "monthly_expense": {k: round(v, 2) for k, v in sorted(exp["monthly"].items())},
        "category_expense": {k: round(v, 2) for k, v in sorted(exp["cats"].items(), key=lambda x: x[1], reverse=True)},
        "avg_monthly_income": round(total_inc / n_months, 2),
        "avg_monthly_expense": round(total_exp / n_months, 2),
        "fixed_expense": round(exp["fixed"], 2),
        "variable_expense": round(exp["variable"], 2),
        "excluded": round(exp["excluded"] + inc["excluded"], 2),
        "prepayment": round(exp["prepay"], 2),
        "reserve_months": round((total_inc / n_months) / (total_exp / n_months), 1) if total_exp > 0 else 0
    }
    _set_cached(cache_k, result)
    return result


# ==================== 保留旧接口（兼容，内部走缓存） ====================

@router.get("/income-structure")
async def income_structure(current_user: User = Depends(get_current_active_user)):
    return (await all_years_data(0, current_user))["income_structure"]

@router.get("/expense-structure")
async def expense_structure(current_user: User = Depends(get_current_active_user)):
    return (await all_years_data(0, current_user))["expense_structure"]

@router.get("/mortgage")
async def mortgage_analysis(current_user: User = Depends(get_current_active_user)):
    return (await all_years_data(0, current_user))["mortgage"]

@router.get("/stability")
async def stability(current_user: User = Depends(get_current_active_user)):
    return (await all_years_data(0, current_user))["stability"]


@router.get("/fixed-variable")
async def fixed_variable(current_user: User = Depends(get_current_active_user)):
    """固定vs可变支出历年对比"""
    api_key, inc_db, exp_db = _get_notion_key(current_user.id)
    cache_k = _cache_key(current_user.id, "fixed-variable")
    cached = _get_cached(cache_k)
    if cached is not None:
        return cached

    result = {}
    for year in YEARS:
        pages = _query_notion(exp_db, year, api_key)
        exp = _parse_expense(pages)
        total = exp["fixed"] + exp["variable"]
        result[year] = {
            "fixed": round(exp["fixed"], 2),
            "variable": round(exp["variable"], 2),
            "fixed_pct": round(exp["fixed"] / total * 100, 1) if total > 0 else 0,
            "variable_pct": round(exp["variable"] / total * 100, 1) if total > 0 else 0
        }
    _set_cached(cache_k, result)
    return result


@router.get("/monthly-cashflow")
async def monthly_cashflow(current_user: User = Depends(get_current_active_user)):
    """月度现金流历年对比"""
    api_key, inc_db, exp_db = _get_notion_key(current_user.id)
    cache_k = _cache_key(current_user.id, "monthly-cashflow")
    cached = _get_cached(cache_k)
    if cached is not None:
        return cached

    result = {}
    for year in YEARS:
        exp_pages = _query_notion(exp_db, year, api_key)
        inc_pages = _query_notion(inc_db, year, api_key)
        exp = _parse_expense(exp_pages)
        inc = _parse_income(inc_pages)
        months = sorted(set(list(inc["monthly"].keys()) + list(exp["monthly"].keys())))
        result[year] = [{"month": m, "income": round(inc["monthly"].get(m, 0), 2),
                         "expense": round(exp["monthly"].get(m, 0), 2),
                         "cashflow": round(inc["monthly"].get(m, 0) - exp["monthly"].get(m, 0), 2)} for m in months]
    _set_cached(cache_k, result)
    return result


@router.get("/prediction")
async def prediction(current_user: User = Depends(get_current_active_user)):
    """2026年预测"""
    api_key, inc_db, exp_db = _get_notion_key(current_user.id)
    cache_k = _cache_key(current_user.id, "prediction")
    cached = _get_cached(cache_k)
    if cached is not None:
        return cached

    exp_pages = _query_notion(exp_db, "2026", api_key)
    inc_pages = _query_notion(inc_db, "2026", api_key)
    exp = _parse_expense(exp_pages)
    inc = _parse_income(inc_pages)
    all_months = set(list(inc["monthly"].keys()) + list(exp["monthly"].keys()))
    n_months = len(all_months) or 1
    pred_inc = inc["total"] / n_months * 12
    pred_exp = exp["total"] / n_months * 12
    pred_bal = pred_inc - pred_exp

    result = {
        "actual_months": n_months,
        "actual_income": round(inc["total"], 2),
        "actual_expense": round(exp["total"], 2),
        "predicted_income": round(pred_inc, 2),
        "predicted_expense": round(pred_exp, 2),
        "predicted_balance": round(pred_bal, 2),
        "predicted_savings_rate": round(pred_bal / pred_inc * 100, 1) if pred_inc > 0 else 0
    }
    _set_cached(cache_k, result)
    return result
