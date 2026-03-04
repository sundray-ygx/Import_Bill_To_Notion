# 代码检查报告

**项目名称**: Import_Bill_To_Notion
**报告生成时间**: 2026-03-04
**检查模式**: 全量检查 (Full Scope)
**执行模式**: 快速模式 (Fast Mode)

---

## 1. 检查概览

| 检查类型 | 检查工具 | 结果 |
|---------|---------|------|
| 外部 Lint 工具 | flake8, black | 发现 150+ 个问题 |
| AI 规范检查 | python-pro | 符合度 87/100 |
| 安全编码检查 | security-reviewer | 安全评分 72/100 |

---

## 2. 综合评分

```
整体代码质量评分: 80/100

├─ 代码规范性: 87/100 (良好)
├─ 安全性: 72/100 (需改进)
└─ 可维护性: 85/100 (良好)
```

---

## 3. 外部 Lint 工具检查结果

### flake8 检查结果

**工具版本**: 7.1.2
**问题数量**: 150+

**主要问题分布**:

| 错误代码 | 数量 | 描述 |
|---------|------|------|
| F401 | 56 | 未使用的导入 |
| E402 | 5 | 模块级导入不在文件顶部 |
| F541 | 20 | f-string 中缺少占位符 |
| E712 | 9 | 布尔值比较不规范 |
| E722 | 3 | 使用裸 except |
| F841 | 10 | 未使用的局部变量 |
| F821 | 1 | 未定义的名称 |

### black 检查结果

**工具版本**: 24.8.0
**结果**: 发现代码格式问题，需要重新格式化

---

## 4. AI 规范检查结果

### 检查统计

| 指标 | 数值 |
|------|------|
| 检查的文件数量 | 21 |
| 发现的问题总数 | 105 |
| 规范符合度评分 | **87/100** |
| 每 1000 行代码问题数 | 25.0 |

### 高优先级问题 (需立即修复)

#### 未定义的名称 (F821)
- **parsers/__init__.py:123** - `logger` 未定义

#### 裸 except (E722) - 潜在的严重问题
- **src/auth.py:434** - 使用裸 `except`
- **src/review_service.py:319** - 使用裸 `except`
- **src/review_service.py:1061** - 使用裸 `except`

### 中优先级问题 (建议修复)

#### 布尔值比较错误 (E712) - 9 处
应使用 `is True` 或 `is False` 而非 `== True` 或 `== False`：
- **src/auth.py:301, 331**
- **web_service/routes/admin.py:151, 154, 337**
- **web_service/routes/auth.py:76, 308, 438**
- **src/services/dependencies.py:228**

#### 未使用的局部变量 (F841) - 10 处
- **web_service/main.py** - 6 处 `payload` 变量未使用
- **src/review_service.py:1066, 1067** - `income_wan`, `expense_wan` 未使用
- **web_service/routes/review.py:591** - `cache_key` 未使用
- **web_service/routes/upload.py:241** - `best_encoding` 未使用

### 低优先级问题 (代码清理)

#### 未使用的导入 (F401) - 56 处
主要分布文件：
- **src/services/database.py** - 9 处
- **web_service/routes/** - 多个文件存在未使用的导入
- **src/review_service.py** - 3 处

#### f-string 缺少占位符 (F541) - 20 处
应移除不必要的 `f` 前缀

---

## 5. 安全编码检查结果

### 安全检查摘要

| 指标 | 数值 |
|------|------|
| 检查的文件数量 | 26 |
| 发现的问题总数 | 14 |
| 安全评分 | **72/100** |

### 安全类别检查结果

| 安全类别 | 状态 | 发现问题数 |
|---------|------|-----------|
| SQL 注入 | PASS | 0 |
| 命令注入 | PASS | 0 |
| XSS (跨站脚本) | PASS | 0 |
| CSRF (跨站请求伪造) | PASS | 0 |
| 敏感信息泄露 | FAIL | 3 |
| 不安全的随机数 | PASS | 0 |
| 不安全的哈希 | PASS | 0 |
| 不安全的反序列化 | PASS | 0 |
| 路径遍历 | FAIL | 2 |
| 不安全的 SSL/TLS | PASS | 0 |
| 硬编码密钥 | PASS | 0 |
| 不安全的会话管理 | FAIL | 2 |
| 不安全的文件上传 | FAIL | 2 |
| 不安全的依赖 | WARN | 2 |
| 日志注入 | FAIL | 2 |
| 不安全的重定向 | PASS | 0 |

### 严重问题 (CRITICAL)

#### 1. 路径遍历漏洞 - 文件删除操作

**文件**: `web_service/routes/upload.py:197-209`
**类别**: 路径遍历

文件删除操作未充分验证用户提供的文件名，攻击者可能通过 `../` 路径遍历序列删除系统中的任意文件。

#### 2. CORS 配置过于宽松

**文件**: `web_service/main.py:51-58`
**类别**: 安全配置

CORS 配置允许所有来源访问 API (`allow_origins=["*"]`)，在多租户模式下可能导致跨域攻击。

### 高危问题 (HIGH)

#### 3. 日志中的敏感信息泄露
**文件**: `web_service/routes/review.py:748`

#### 4. 缺少速率限制
**文件**: `web_service/routes/auth.py:139-243`

#### 5. 用户文件服务中的路径遍历风险
**文件**: `web_service/services/user_file_service.py:99-146`

#### 6. 文件上传缺少魔数验证
**文件**: `web_service/services/user_file_service.py:99-146`

#### 7. 管理员页面权限检查缺失
**文件**: `web_service/main.py:249-327`

### 中危问题 (MEDIUM)

#### 8. API Key 脱敏不够完整
**文件**: `src/notion_api.py:49-50`

#### 9. 依赖包缺少安全审计
**文件**: `requirements.txt`

#### 10. 审计日志失败静默处理
**文件**: `web_service/routes/auth.py:494-495`

#### 11. SECRET_KEY 临时生成警告
**文件**: `src/config.py:154-163`

### 低危问题 (LOW)

#### 12. 审计日志中的用户输入未清理
**文件**: `web_service/routes/auth.py:488-489`

#### 13. 缺少 Content-Type 验证
**文件**: 多个路由文件

#### 14. 缺少安全响应头
**文件**: `web_service/main.py`

---

## 6. 问题文件汇总

### 按问题数量排序

| 文件 | 代码规范问题 | 安全问题 | 总计 |
|------|-------------|---------|------|
| src/review_service.py | 21 | 0 | 21 |
| src/services/database.py | 16 | 0 | 16 |
| web_service/main.py | 9 | 3 | 12 |
| web_service/routes/auth.py | 8 | 2 | 10 |
| web_service/routes/users.py | 7 | 0 | 7 |
| web_service/routes/admin.py | 5 | 1 | 6 |
| web_service/services/user_file_service.py | 0 | 2 | 2 |
| web_service/routes/upload.py | 5 | 2 | 7 |
| src/auth.py | 2 | 0 | 2 |

---

## 7. 修复建议

### 立即修复 (P0)

1. **路径遍历漏洞** - upload.py 和 user_file_service.py
2. **CORS 配置** - main.py
3. **logger 未定义** - parsers/__init__.py

### 高优先级 (P1)

4. 添加速率限制 - auth.py
5. 文件上传魔数验证 - user_file_service.py
6. 管理员页面权限检查 - main.py
7. 裸 except 修复 - auth.py, review_service.py

### 中优先级 (P2)

8. SECRET_KEY 验证逻辑改进 - config.py
9. 日志脱敏加强 - notion_api.py
10. 依赖版本固定 - requirements.txt
11. 布尔值比较修复 - 多个文件

### 低优先级 (P3)

12. 未使用的导入清理
13. f-string 修复
14. 添加安全响应头

---

## 8. 自动修复状态

**当前模式**: 快速模式 (Fast Mode)

根据快速模式要求，以下问题将尝试自动修复：
- [ ] 未使用的导入 (F401)
- [ ] f-string 缺少占位符 (F541)
- [ ] 布尔值比较 (E712)
- [ ] 代码格式问题 (black)

**注意**: 安全问题和裸 except (E722) 需要手动修复。

---

**报告生成者**: /role-lint 命令
**下一步**: 执行 /role-fix 命令进行自动修复
