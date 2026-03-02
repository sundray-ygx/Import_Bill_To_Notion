# Implementation Phase Prompt

**生成时间**: 2026-03-02
**阶段**: Implementation - 实施执行

---

## Prompt 内容

你正在为"账单导入到 Notion"项目实施"邮箱账单自动导入"功能。

### 前置成果

1. **需求发现报告** (`docs/discovery-report.md`):
   - Epic → Feature → Story 完整拆解
   - 验收标准和评估标准
   - 数据模型和 API 设计

2. **代码库探索报告** (`docs/exploration-report.md`):
   - 30+ 关键文件已标注
   - 6 种核心设计模式已识别
   - 4 个主要扩展点已确定

3. **架构设计报告** (`docs/design-report.md`):
   - 方案 B：集成扩展架构
   - 核心模块详细设计
   - 数据库设计
   - 接口设计
   - 实施蓝图（6 阶段）

### 你的任务

按照 TDD 原则和**编码规范 checklist** 进行实施：

#### 实施原则

1. **TDD 红绿重构**:
   - 先写测试，再写代码
   - 测试覆盖率 ≥ 80%
   - 频繁重构，保持代码简洁

2. **两阶段审查**:
   - 第一阶段：自审（使用 checklist）
   - 第二阶段：peer review

3. **编码规范 checklist** (Python):
   - 遵循 PEP 8 风格指南
   - 使用类型注解
   - 编写 docstring
   - 函数不超过 50 行
   - 避免过度工程化
   - 适当的错误处理
   - 敏感信息不记录日志

4. **多语言支持** (v3.0):
   - Python 3.12+ 特性
   - 类型提示 (Type Hints)
   - 异步编程 (asyncio)

#### 实施阶段

按照架构设计报告的 6 个阶段实施：

**阶段 1: 基础设施** (3-4 天)
- 创建数据库迁移脚本
- 添加 `ImportSource` 抽象类
- 实现 `FileUploadSource` 封装
- 添加加密工具 `CryptoService`

**阶段 2: 邮箱核心功能** (5-6 天)
- 实现 `EmailService`
- 实现 `EmailParseService`
- 实现 `EmailImportSource`
- 单元测试

**阶段 3: 调度和自动化** (2-3 天)
- 扩展 `BillScheduler`
- 实现邮箱检查任务
- 错误恢复机制

**阶段 4: Web API 和 UI** (4-5 天)
- 创建 `routes/email.py`
- 扩展设置页面
- 添加邮箱配置表单
- 前端交互逻辑

**阶段 5: 测试和优化** (3-4 天)
- 单元测试
- 集成测试
- 端到端测试
- 性能测试
- 安全测试

**阶段 6: 部署和监控** (1-2 天)
- 部署配置
- 监控配置
- 文档更新

### 上下文信息

**项目技术栈**:
- 后端: Python 3.12 + FastAPI
- 数据库: SQLite (SQLAlchemy ORM)
- 认证: JWT + bcrypt
- 调度: APScheduler
- Notion: notion-client SDK

**新增依赖**:
- imap-tools==0.51.0
- cryptography==41.0.0
- beautifulsoup4==4.12.0

### 输出要求

1. **代码实现**:
   - 符合 PEP 8 规范
   - 有完整的类型注解
   - 有详细的 docstring
   - 有对应的单元测试

2. **自审报告**:
   - 使用编码规范 checklist
   - 记录所有问题和修复

3. **提交记录**:
   - 频繁提交
   - 清晰的 commit message

---

## 实际使用命令

```bash
# 启动 implementation-agent
Task(
  description="实施执行 - 邮箱账单自动导入",
  prompt="<上述完整 prompt 内容>",
  subagent_type="end-to-end-delivery:implementation-agent"
)
```
