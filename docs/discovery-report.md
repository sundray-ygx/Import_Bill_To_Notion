# 需求发现报告：邮箱账单自动导入功能

**报告版本**: v1.0
**生成时间**: 2026-03-02
**作者**: Discovery Agent
**功能需求**: 在当前功能的基础上，增加需求，可将账单发送至邮箱，在邮箱中提取账单文件和解压密码，然后完成自动上传，与当前手动上传账单的功能并存。

---

## 目录

1. [需求概述](#1-需求概述)
2. [需求澄清问题与建议答案](#2-需求澄清问题与建议答案)
3. [需求复杂度评估](#3-需求复杂度评估)
4. [基于模板维度的需求分析](#4-基于模板维度的需求分析)
5. [验收标准定义](#5-验收标准定义)
6. [评估标准](#6-评估标准)
7. [风险分析](#7-风险分析)
8. [数据模型设计](#8-数据模型设计)
9. [API 设计](#9-api-设计)
10. [技术实现要点](#10-技术实现要点)
11. [用户界面设计要点](#11-用户界面设计要点)
12. [测试计划](#12-测试计划)
13. [发布计划](#13-发布计划)
14. [总结](#14-总结)

---

## 1. 需求概述

### 1.1 功能描述
在现有手动上传账单功能的基础上，新增通过邮箱自动导入账单的功能。系统应能够：
- 连接到用户的邮箱账户
- 自动检测并下载账单邮件附件
- 从邮件内容中提取账单解压密码
- 自动解压并导入账单到 Notion
- 与现有手动上传功能并存

### 1.2 用户场景
**主要用户场景：**
- 用户在支付宝/微信/银联平台申请账单时，选择发送到邮箱
- 系统自动监控邮箱，收到账单邮件后自动处理
- 用户无需手动下载、解压、上传文件，实现完全自动化

**价值主张：**
- 减少手动操作步骤：从"下载→解压→上传"三步变为零操作
- 提高效率：账单导入完全自动化，节省用户时间
- 降低出错风险：避免手动选择错误文件或输入错误密码

### 1.3 目标用户
- 已有用户：希望简化账单导入流程的现有用户
- 新用户：追求高度自动化的记账用户
- 高频用户：每月/每周定期导入账单的用户

---

## 2. 需求澄清问题与建议答案

### 2.1 功能维度

| 问题 | 建议 | 说明 |
|------|------|------|
| **支持哪些邮件协议？** | IMAP (优先)，POP3 作为备选 | IMAP 支持多设备同步，更适合现代邮箱服务 |
| **如何识别账单邮件？** | 发件人白名单 + 主题关键词 | 支付宝、微信、银联官方发件人 + "账单"关键词 |
| **如何处理多个附件？** | 自动识别账单文件类型 (.csv, .zip) | 优先处理 CSV 文件，ZIP 文件需要解压 |
| **解压密码如何获取？** | 从邮件正文正则提取 | 支付宝邮件格式固定，可提取"密码：xxxx" |
| **导入频率如何控制？** | 可配置：实时/每小时/每天/手动 | 默认每小时检查一次新邮件 |
| **是否支持手动触发？** | 是 | 提供立即检查邮箱的按钮 |
| **已处理邮件如何标记？** | 添加自定义标签 (如 "NotionImported") | 避免重复导入同一封邮件 |

### 2.2 用户维度

| 问题 | 建议 | 说明 |
|------|------|------|
| **每个用户可配置多个邮箱？** | MVP 阶段支持1个，后续扩展 | 简化 MVP 实现，降低复杂度 |
| **邮箱凭证如何存储？** | 加密存储在数据库 | 使用现有加密机制，安全性高 |
| **用户如何知道导入状态？** | 通知 + 导入历史记录 | 复用现有 ImportHistory 机制 |
| **是否需要邮件预览功能？** | 否，MVP 阶段不需要 | 自动化处理，无需预览 |

### 2.3 技术维度

| 问题 | 建议 | 说明 |
|------|------|------|
| **使用哪些 Python 库？** | `imap-tools` (IMAP), `zipfile` | 成熟稳定的库，社区活跃 |
| **如何处理邮件编码？** | `email` 库自动检测 | 处理中文邮件内容 |
| **如何避免阻塞主线程？** | 异步任务或后台调度器 | 复用现有 APScheduler 或 Celery |
| **错误处理策略？** | 失败邮件单独标记，不中断流程 | 记录错误，支持重试 |

### 2.4 质量维度

| 问题 | 建议 | 说明 |
|------|------|------|
| **如何保证邮箱凭证安全？** | 数据库加密存储 + 传输加密 | 使用 AES 加密，HTTPS 传输 |
| **如何防止重复导入？** | 邮件 Message-ID 去重 | 存储已处理邮件 ID |
| **如何处理解压失败？** | 记录错误，通知用户，支持手动密码 | 容错机制，保证用户体验 |
| **性能要求？** | 单次检查不超过 30 秒 | 限制每次检查邮件数量 |

---

## 3. 需求复杂度评估

### 3.1 功能复杂度评估：6/10 (中复杂度)

**评估依据：**
- 涉及 **3 个新功能模块**：邮箱连接、邮件解析、附件处理
- 与 **5 个现有模块**集成：用户配置、调度器、导入器、历史记录、通知系统
- **数据流复杂度**：中等 (邮箱 → 邮件 → 附件 → 解压 → 导入)

**功能模块清单：**
| 模块 | 功能点 | 复杂度 |
|------|--------|--------|
| 邮箱配置管理 | 配置增删改查、凭证验证 | 低 |
| 邮件连接服务 | IMAP/POP3 连接、认证 | 中 |
| 邮件解析服务 | 识别账单邮件、提取附件和密码 | 中 |
| 附件处理服务 | 下载、解压、文件类型检测 | 中 |
| 调度集成 | 定时检查邮箱、手动触发 | 低 |

### 3.2 技术复杂度评估：7/10 (中高复杂度)

**评估依据：**
- **新技术栈引入**：IMAP/POP3 协议、邮件解析、加密存储
- **架构变更**：需要新增邮箱服务层，扩展调度器
- **集成难度**：需要与现有的多租户系统、Notion 集成深度整合

**技术挑战：**
| 挑战 | 难度 | 解决方案 |
|------|------|----------|
| 邮箱协议兼容性 | 高 | 使用 `imap-tools` 库，支持主流邮箱服务商 |
| 邮件内容解析 | 中 | 正则表达式 + 发件人白名单 |
| 密码加密存储 | 中 | 复用现有加密机制或使用 `cryptography` |
| 异步任务处理 | 中 | 扩展现有 APScheduler 或引入 Celery |
| 附件解压处理 | 低 | 使用标准库 `zipfile` |

### 3.3 规模复杂度评估：5/10 (中等规模)

**预估工作量：**
| 阶段 | 工作量 (人天) | 说明 |
|------|--------------|------|
| 数据库设计与迁移 | 1 | 新增邮箱配置表、已处理邮件表 |
| 后端开发 | 5-7 | 邮箱服务、API 路由、调度集成 |
| 前端开发 | 3-4 | 邮箱配置界面、导入状态显示 |
| 测试 | 2-3 | 单元测试、集成测试、端到端测试 |
| 文档 | 1 | API 文档、用户手册 |
| **总计** | **12-16** | 约 **2-3 周** |

**影响文件/模块：**
- 新增：5-7 个新文件
- 修改：8-10 个现有文件
- 数据库迁移：1-2 个新表

### 3.4 风险复杂度评估：6/10 (中等风险)

**风险评估：**
| 风险类别 | 风险等级 | 缓解措施 |
|----------|----------|----------|
| **安全风险** | 高 | 邮箱凭证加密存储、传输加密、审计日志 |
| **技术风险** | 中 | 邮箱服务商兼容性测试、错误处理机制 |
| **业务风险** | 低 | 与手动上传功能并存，不影响现有用户 |
| **时间风险** | 中 | MVP 优先，分阶段发布 |
| **依赖风险** | 中 | 第三方邮箱服务稳定性 |

### 3.5 综合评分与模式选择

```
综合得分 = (功能复杂度 6 × 1.0) + (技术复杂度 7 × 1.2) + (规模复杂度 5 × 1.0) + (风险复杂度 6 × 1.5)
         = 6 + 8.4 + 5 + 9
         = 28.4
```

| 总分 | 复杂度等级 | 开发模式 | 需求分析框架 |
|------|-----------|---------|-------------|
| **28.4** | **高复杂度** | **敏捷 (Agile)** | Epic → Feature → Story |

**选择敏捷模式的理由：**
- 虽然综合得分较高，但功能边界清晰，技术方案成熟
- 可采用 MVP 策略，分阶段交付价值
- 用户反馈循环快，便于迭代优化
- 邮箱功能相对独立，不影响核心导入流程

---

## 4. 基于模板维度的需求分析

### 4.1 Epic: 邮箱账单自动化导入

```markdown
## Epic: 邮箱账单自动化导入

### 交付周期
1~3 月（对外正式发布）

### 描述
Epic 是一个战略举措，通过邮箱自动化能力，将账单导入从"手动操作"升级为"完全自动化"，显著提升用户体验和产品竞争力。

### 【痛点】
1. **操作繁琐**：用户需要"下载账单→解压文件→手动上传"三步操作
2. **容易出错**：手动操作可能选错文件、输错解压密码
3. **效率低下**：高频用户每次导入都需要重复相同操作
4. **体验割裂**：账单已经在邮箱，却需要手动下载再上传

### 【价值】
1. **提升效率**：从三步操作变为零操作，节省用户时间
2. **降低门槛**：新用户无需学习手动上传流程
3. **提高留存**：自动化功能增加用户粘性
4. **竞争优势**：差异化功能，提升产品竞争力

### 【目标用户】
1. **高频用户**：每周/每月定期导入账单的记账用户
2. **效率追求者**：希望减少手动操作的自动化爱好者
3. **多平台用户**：同时使用支付宝、微信、银联多个平台的用户

### 【背景和现状】
1. **现有功能**：支持手动上传账单文件，需要用户下载和解压
2. **用户反馈**：部分用户反映操作繁琐，希望有更简单的导入方式
3. **技术基础**：已有完整的导入流程和调度器，易于扩展
4. **市场趋势**：自动化和智能化是产品发展的方向

### 【方案描述】
1. **邮箱配置**：用户在设置中配置邮箱账户和服务器信息
2. **自动监控**：系统定时检查邮箱，识别账单邮件
3. **智能解析**：提取邮件附件和解压密码
4. **自动导入**：解压并导入账单到 Notion
5. **状态通知**：通知用户导入结果，记录到历史

### 【MVP规划】
#### 目标
验证邮箱自动化导入的核心价值，收集用户反馈

#### 核心特性
1. **邮箱配置管理**：支持 IMAP 协议，加密存储凭证
2. **邮件自动识别**：支持支付宝、微信账单邮件识别
3. **附件自动下载**：支持 CSV 和 ZIP 格式附件
4. **密码自动提取**：从邮件正文提取解压密码
5. **自动导入集成**：与现有导入流程无缝集成
6. **导入状态跟踪**：记录每次邮箱导入的结果

#### 后续版本特性
- 支持 POP3 协议
- 支持多邮箱配置
- 支持更多账单平台
- 智能推荐和预测

### 【成效指标】
#### 定性
- 用户操作满意度提升
- 自动化导入成功率 > 95%
- 用户正面反馈增加

#### 定量
- 邮箱导入功能使用率 > 30%
- 手动上传次数减少 > 40%
- 用户留存率提升 > 15%
- 平均导入时间从 3 分钟减少到 0 分钟

### 【MVP工作量估算】
12-16 人月

### 【风险与依赖】
#### 风险
1. **安全风险**：邮箱凭证泄露风险
   - 缓解：加密存储、传输加密、审计日志
2. **兼容性风险**：不同邮箱服务商的差异
   - 缓解：支持主流邮箱，提供详细配置指南
3. **稳定性风险**：邮件解析失败
   - 缓解：容错机制、错误通知、手动重试

#### 依赖
1. **现有导入流程**：依赖 `importer.py` 和 `notion_api.py`
2. **多租户系统**：依赖现有的用户配置和管理
3. **调度器**：依赖 APScheduler 进行定时检查
```

### 4.2 Feature: 邮箱配置与连接

```markdown
## Feature: 邮箱配置与连接

### 交付周期
1~2 周（内部发布或灰度发布）

### 描述
Feature 是为用户提供完整价值的最小应用：用户能够安全地配置邮箱账户，系统建立稳定的邮箱连接并验证凭证有效性。

### 【需求场景 & 用户痛点】
**场景**：用户希望启用邮箱自动导入功能，需要配置自己的邮箱账户信息。
**痛点**：
- 邮箱服务器配置复杂，用户不知道如何填写
- 担心邮箱凭证的安全性
- 配置后不知道是否成功

### 【需求洞察 & 特性设计】
1. **简化配置流程**
   - 预设主流邮箱服务商配置模板（QQ、163、Gmail、Outlook）
   - 一键填充服务器地址和端口
   - 实时连接验证反馈

2. **安全凭证管理**
   - 使用 AES-256 加密存储邮箱密码
   - 传输过程使用 HTTPS 加密
   - 提供凭证删除和重置功能

3. **连接验证机制**
   - 配置保存前验证连接
   - 定期健康检查
   - 连接失败自动通知

**FAB 分析**：
- **Feature (功能)**：邮箱配置管理、连接验证、安全存储
- **Advantages (优势)**：一键配置模板、实时验证、加密存储
- **Benefit (收益)**：配置简单快捷，使用安全放心

### 【特性价值度量指标】
- 配置成功率 > 90%
- 配置平均耗时 < 2 分钟
- 连接验证准确率 = 100%

### 【依赖与风险】
#### 依赖
- 数据库加密服务
- 现有用户配置系统
- IMAP/POP3 客户端库

#### 风险
- 邮箱服务商 API 变更
- 用户凭证复杂度要求（如应用专用密码）

### 【技术思路/工作量】
**技术方案**：
- 使用 `imap-tools` 库实现 IMAP 连接
- 使用 `cryptography` 库实现凭证加密
- 新增 `EmailConfig` 数据库模型
- 新增邮箱配置 API 路由

**工作量**：2-3 人天
```

### 4.3 Feature: 邮件识别与解析

```markdown
## Feature: 邮件识别与解析

### 交付周期
2~3 周

### 描述
Feature 是为用户提供完整价值的最小应用：系统能够自动识别账单邮件，提取附件和解压密码，为自动导入做好准备。

### 【需求场景 & 用户痛点】
**场景**：邮箱中有各种类型的邮件，系统需要准确识别出账单邮件。
**痛点**：
- 邮件内容格式多样，难以准确识别
- 解压密码隐藏在邮件正文中，难以提取
- 附件格式不统一

### 【需求洞察 & 特性设计】
1. **智能邮件识别**
   - 发件人白名单：支付宝、微信、银联官方邮箱
   - 主题关键词匹配："账单"、"交易记录"
   - 附件类型过滤：CSV、ZIP 格式

2. **内容智能解析**
   - 正则表达式提取解压密码
   - 支持多种密码格式（"密码：xxx"、"密码是xxx"）
   - 附件文件名解析（平台识别、日期提取）

3. **容错处理**
   - 多种密码提取模式尝试
   - 无法解析时标记为待处理
   - 支持手动输入密码

**FAB 分析**：
- **Feature (功能)**：邮件识别、内容解析、密码提取
- **Advantages (优势)**：多模式匹配、智能容错、准确率高
- **Benefit (收益)**：自动化程度高，减少手动干预

### 【特性价值度量指标】
- 账单邮件识别准确率 > 95%
- 密码提取成功率 > 90%
- 平均解析时间 < 3 秒/邮件

### 【依赖与风险】
#### 依赖
- 邮箱配置与连接功能
- 现有账单解析器

#### 风险
- 邮件格式变更导致解析失败
- 特殊字符密码提取失败

### 【技术思路/工作量】
**技术方案**：
- 使用 `email` 库解析邮件内容
- 使用 `re` 库进行正则匹配
- 建立发件人白名单数据库
- 新增 `EmailParseService` 服务类

**工作量**：4-5 人天
```

### 4.4 Feature: 自动导入调度

```markdown
## Feature: 自动导入调度

### 交付周期
1~2 周

### 描述
Feature 是为用户提供完整价值的最小应用：系统能够按照用户设定的频率自动检查邮箱并导入账单，实现完全自动化。

### 【需求场景 & 用户痛点】
**场景**：用户配置好邮箱后，希望系统能够自动检查新账单并导入。
**痛点**：
- 需要手动触发检查
- 不知道上次检查时间
- 检查频率无法自定义

### 【需求洞察 & 特性设计】
1. **灵活调度策略**
   - 可配置频率：实时、每小时、每天、每周
   - 默认频率：每小时检查一次
   - 支持手动立即检查

2. **智能去重机制**
   - 基于 Message-ID 去重
   - 记录已处理邮件
   - 避免重复导入

3. **状态反馈**
   - 显示上次检查时间
   - 显示下次检查时间
   - 导入结果通知

**FAB 分析**：
- **Feature (功能)**：定时调度、去重机制、状态反馈
- **Advantages (优势)**：可配置频率、智能去重、实时反馈
- **Benefit (收益)**：真正的自动化，省心省力

### 【特性价值度量指标】
- 调度准确率 = 100%
- 去重准确率 > 99%
- 用户满意度 > 90%

### 【依赖与风险】
#### 依赖
- 邮箱配置与连接功能
- 邮件识别与解析功能
- 现有调度器系统

#### 风险
- 调度器稳定性
- 邮箱连接超时

### 【技术思路/工作量】
**技术方案**：
- 扩展现有 `BillScheduler`
- 新增 `EmailScheduler` 服务类
- 新增 `ProcessedEmail` 数据库模型（去重）
- 集成到现有 APScheduler

**工作量**：3-4 人天
```

### 4.5 Story: 邮箱配置界面

```markdown
## Story: 邮箱配置界面

### 交付周期
3~5 天（完成开发测试）

### 描述
User Story 是一个具体的用户操作场景：用户能够通过 Web 界面配置邮箱账户，验证连接，并管理现有配置。

### 【用户故事】
作为 记账用户，我想要 在设置页面配置我的邮箱账户，以便于 系统能够自动检查和导入我的账单

### 【A/C验收条件】
#### 一、功能性验收条件
1. **邮箱配置表单**
   - 必填项：邮箱地址、密码、IMAP 服务器、端口
   - 可选项：邮箱服务商（用于一键填充配置）
   - 验证：邮箱格式验证、服务器地址验证

2. **一键配置模板**
   - Given: 用户在邮箱服务商下拉框中选择"QQ邮箱"
   - When: 系统自动填充 IMAP 服务器为 "imap.qq.com"，端口为 "993"
   - Then: 用户只需填写邮箱地址和密码

3. **连接验证**
   - Given: 用户填写完邮箱配置，点击"测试连接"按钮
   - When: 系统尝试连接邮箱服务器并验证凭证
   - Then: 显示连接成功/失败的明确提示，成功则允许保存

4. **配置列表**
   - Given: 用户已配置邮箱，进入邮箱配置页面
   - When: 系统显示已配置的邮箱列表
   - Then: 显示邮箱地址、服务器、连接状态、最后检查时间

5. **配置删除**
   - Given: 用户不再使用某个邮箱配置
   - When: 用户点击"删除"按钮并确认
   - Then: 系统删除该配置并停止该邮箱的自动检查

#### 二、非功能性验收条件
1. **安全性**：密码使用 AES-256 加密后存储在数据库
2. **性能**：连接验证在 10 秒内完成
3. **可用性**：提供详细的配置帮助文档和常见问题解答

#### 三、DFX、可测试性
1. **可测试性**：提供测试连接功能，无需保存即可验证
2. **可维护性**：配置错误日志详细，便于排查问题

### 【依赖与风险】
1. **依赖**：邮箱配置与连接 Feature
2. **风险**：用户可能输入错误的配置信息导致连接失败

### 【技术思路】
- 前端：React/Vue 表单组件，实时验证反馈
- 后端：FastAPI 路由，邮箱配置 CRUD 接口
- 数据库：`EmailConfig` 模型，加密存储密码
```

### 4.6 Story: 邮件检查与导入

```markdown
## Story: 邮件检查与导入

### 交付周期
3~5 天（完成开发测试）

### 描述
User Story 是一个具体的用户操作场景：系统能够检查邮箱中的新账单邮件，并自动下载附件、解压、导入到 Notion。

### 【用户故事】
作为 记账用户，我想要 系统自动检查我的邮箱并导入新账单，以便于 我不需要手动操作就能完成账单导入

### 【A/C验收条件】
#### 一、功能性验收条件
1. **邮件识别**
   - Given: 邮箱中有来自支付宝的新账单邮件
   - When: 系统定时检查邮箱（如每小时一次）
   - Then: 系统识别出包含账单的邮件（发件人匹配、主题包含"账单"）

2. **附件下载**
   - Given: 系统识别到账单邮件
   - When: 邮件包含 CSV 或 ZIP 格式的附件
   - Then: 系统下载附件到临时目录

3. **密码提取与解压**
   - Given: 附件是加密的 ZIP 文件
   - When: 系统从邮件正文中提取到解压密码（如"密码：abc123"）
   - Then: 系统使用密码解压文件，获得 CSV 账单文件

4. **自动导入**
   - Given: 系统已成功下载并解压账单文件
   - When: 系统调用现有的导入流程
   - Then: 账单被成功导入到 Notion，并记录导入历史

5. **去重处理**
   - Given: 系统已经处理过某封邮件
   - When: 下次检查时再次遇到该邮件
   - Then: 系统跳过该邮件，避免重复导入

#### 二、非功能性验收条件
1. **性能**：单次检查处理不超过 50 封邮件，总耗时不超过 30 秒
2. **可靠性**：单封邮件处理失败不影响其他邮件
3. **安全性**：临时文件在处理后自动删除

#### 三、DFX、可测试性
1. **可测试性**：支持手动触发检查，方便测试
2. **可观测性**：详细的日志记录，包括邮件 ID、处理状态、错误信息

### 【依赖与风险】
1. **依赖**：邮箱配置、邮件识别与解析、自动导入调度
2. **技术风险**：邮件格式变更、密码提取失败

### 【技术思路】
- 后端：`EmailImportService` 服务类
- 调度：扩展 APScheduler，添加邮箱检查任务
- 去重：`ProcessedEmail` 模型记录已处理邮件
- 错误处理：失败邮件标记状态，支持重试
```

---

## 5. 验收标准定义

### 5.1 功能验收标准

#### 邮箱配置管理
- [ ] 用户可以添加邮箱配置（IMAP 协议）
- [ ] 支持主流邮箱一键配置（QQ、163、Gmail、Outlook）
- [ ] 邮箱密码使用 AES-256 加密存储
- [ ] 配置保存前验证连接有效性
- [ ] 用户可以查看、编辑、删除邮箱配置
- [ ] 显示连接状态和最后检查时间

#### 邮件识别与解析
- [ ] 自动识别支付宝、微信、银联账单邮件
- [ ] 基于发件人白名单和主题关键词过滤
- [ ] 自动下载 CSV 和 ZIP 格式附件
- [ ] 从邮件正文提取解压密码（支持多种格式）
- [ ] 解压密码提取成功率 > 90%
- [ ] 账单邮件识别准确率 > 95%

#### 自动导入调度
- [ ] 支持可配置的检查频率（实时/小时/天/周）
- [ ] 默认每小时检查一次邮箱
- [ ] 支持手动触发立即检查
- [ ] 基于 Message-ID 去重，避免重复导入
- [ ] 导入结果记录到历史
- [ ] 导入成功后发送通知

#### 与现有系统集成
- [ ] 邮箱导入与手动上传功能并存
- [ ] 复用现有账单解析器
- [ ] 复用现有 Notion 导入流程
- [ ] 导入历史统一管理

### 5.2 非功能验收标准

#### 安全性
- [ ] 邮箱凭证使用 AES-256 加密存储
- [ ] 传输过程使用 HTTPS 加密
- [ ] 敏感信息不在日志中暴露
- [ ] 支持用户删除邮箱凭证
- [ ] 邮箱操作审计日志

#### 性能
- [ ] 单次检查处理不超过 50 封邮件
- [ ] 单次检查总耗时不超过 30 秒
- [ ] 连接验证在 10 秒内完成
- [ ] 邮件解析时间 < 3 秒/邮件

#### 可靠性
- [ ] 单封邮件处理失败不影响其他邮件
- [ ] 连接失败自动重试（最多 3 次）
- [ ] 临时文件在处理后自动删除
- [ ] 错误详细记录，便于排查

#### 可用性
- [ ] 提供详细的配置帮助文档
- [ ] 配置错误时给出明确的错误提示
- [ ] 支持常见邮箱服务商的一键配置
- [ ] 导入状态实时反馈

---

## 6. 评估标准

### 6.1 Capability Evals (功能能力评估)

#### CE-01: 邮箱配置能力
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 添加 QQ 邮箱配置 | 配置成功，连接验证通过 | 自动化测试 |
| 添加 Gmail 配置 | 配置成功，连接验证通过 | 自动化测试 |
| 输入错误的服务器地址 | 连接失败，显示明确错误提示 | 手动测试 |
| 输入错误的密码 | 连接失败，显示凭证错误提示 | 手动测试 |
| 删除邮箱配置 | 配置删除成功，停止自动检查 | 自动化测试 |

#### CE-02: 邮件识别能力
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 支付宝账单邮件 | 识别成功，提取附件和密码 | 自动化测试 |
| 微信账单邮件 | 识别成功，提取附件和密码 | 自动化测试 |
| 非账单邮件 | 忽略，不处理 | 自动化测试 |
| 无密码的账单邮件 | 标记为待处理，通知用户 | 手动测试 |

#### CE-03: 自动导入能力
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 正常账单导入 | 导入成功，记录历史 | 自动化测试 |
| 重复邮件处理 | 跳过，不重复导入 | 自动化测试 |
| 附件解压失败 | 记录错误，支持手动密码 | 手动测试 |
| 大量邮件处理 | 在 30 秒内完成，不中断 | 性能测试 |

### 6.2 Regression Evals (回归评估)

#### RE-01: 手动上传功能不受影响
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 手动上传 CSV 文件 | 导入成功，功能正常 | 回归测试 |
| 手动上传 ZIP 文件 | 导入成功，功能正常 | 回归测试 |
| 平台自动检测 | 检测准确，功能正常 | 回归测试 |

#### RE-02: 多租户功能不受影响
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 用户隔离 | 用户只能访问自己的邮箱配置 | 安全测试 |
| Notion 配置隔离 | 用户只能导入到自己的 Notion | 集成测试 |

#### RE-03: 现有调度器不受影响
| 测试场景 | 预期结果 | 评估方法 |
|----------|----------|----------|
| 本地文件调度导入 | 功能正常，不受影响 | 回归测试 |
| 调度器状态查询 | 显示正确状态 | 回归测试 |

---

## 7. 风险分析

### 7.1 安全风险

#### 风险 1: 邮箱凭证泄露
**风险等级**: 高
**影响**: 用户邮箱可能被未授权访问
**缓解措施**:
- 使用 AES-256 加密存储邮箱密码
- 传输过程使用 HTTPS 加密
- 定期安全审计
- 提供凭证删除功能
- 审计日志记录所有邮箱操作

#### 风险 2: 中间人攻击
**风险等级**: 中
**影响**: 凭证在传输过程中被截获
**缓解措施**:
- 强制使用 HTTPS/TLS 连接
- 验证 SSL 证书
- 支持 OAuth 2.0 认证（后续版本）

### 7.2 技术风险

#### 风险 3: 邮箱服务商兼容性
**风险等级**: 中
**影响**: 部分邮箱无法连接或功能受限
**缓解措施**:
- 优先支持主流邮箱（QQ、163、Gmail、Outlook）
- 提供详细配置指南
- 收集用户反馈，持续优化
- 社区支持，用户贡献配置模板

#### 风险 4: 邮件格式变更
**风险等级**: 中
**影响**: 无法识别或解析账单邮件
**缓解措施**:
- 多种识别策略（发件人、主题、附件）
- 模块化解析器，易于更新
- 容错机制，解析失败标记待处理
- 手动触发重试功能

#### 风险 5: 连接稳定性
**风险等级**: 中
**影响**: 邮箱连接超时或失败
**缓解措施**:
- 连接超时配置（默认 10 秒）
- 自动重试机制（最多 3 次）
- 连接失败通知
- 健康检查和状态监控

### 7.3 业务风险

#### 风险 6: 重复导入
**风险等级**: 低
**影响**: Notion 数据库出现重复记录
**缓解措施**:
- 基于 Message-ID 去重
- 记录已处理邮件
- 导入前检查是否存在

#### 风险 7: 用户接受度
**风险等级**: 低
**影响**: 用户不愿意配置邮箱或担心安全
**缓解措施**:
- 与手动上传功能并存
- 详细的安全说明和保障
- 简化配置流程，提供一键配置
- 隐私政策透明化

### 7.4 时间风险

#### 风险 8: 开发周期超期
**风险等级**: 中
**影响**: 功能延迟上线
**缓解措施**:
- MVP 策略，分阶段交付
- 优先实现核心功能
- 持续集成和测试
- 定期进度检查

---

## 8. 数据模型设计

### 8.1 新增数据库表

#### EmailConfig (邮箱配置表)
```python
class EmailConfig(Base):
    """邮箱配置表"""
    __tablename__ = "email_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 邮箱服务器配置
    email_address = Column(String(255), nullable=False)  # 邮箱地址
    password_encrypted = Column(String(500), nullable=False)  # 加密后的密码
    imap_server = Column(String(255), nullable=False)  # IMAP 服务器地址
    imap_port = Column(Integer, default=993)  # IMAP 端口
    use_ssl = Column(Boolean, default=True)  # 是否使用 SSL

    # 配置元数据
    provider = Column(String(50))  # 邮箱服务商 (qq, gmail, etc.)
    config_name = Column(String(100), default="默认邮箱")  # 配置名称

    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    is_verified = Column(Boolean, default=False, nullable=False)  # 是否验证通过
    last_check_at = Column(DateTime(timezone=True))  # 最后检查时间
    last_check_status = Column(String(20))  # 最后检查状态 (success, failed)

    # 调度配置
    check_frequency = Column(String(20), default="hourly")  # 检查频率 (realtime, hourly, daily, weekly)
    next_check_at = Column(DateTime(timezone=True))  # 下次检查时间

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", backref="email_configs")
    processed_emails = relationship("ProcessedEmail", backref="email_config", cascade="all, delete-orphan")
```

#### ProcessedEmail (已处理邮件表)
```python
class ProcessedEmail(Base):
    """已处理邮件表（去重）"""
    __tablename__ = "processed_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_config_id = Column(Integer, ForeignKey("email_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 邮件标识
    message_id = Column(String(500), nullable=False, unique=True, index=True)  # 邮件 Message-ID
    message_date = Column(DateTime(timezone=True))  # 邮件日期

    # 处理信息
    platform = Column(String(20))  # 检测到的平台 (alipay, wechat, unionpay)
    attachment_name = Column(String(255))  # 附件文件名

    # 处理状态
    status = Column(String(20), nullable=False, index=True)  # success, failed, pending
    error_message = Column(Text)  # 错误信息

    # 导入结果
    import_history_id = Column(Integer, ForeignKey("import_history.id", ondelete="SET NULL"))  # 关联的导入记录

    # 时间戳
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    user = relationship("User", backref="processed_emails")
    import_history = relationship("ImportHistory", backref="processed_email")
```

---

## 9. API 设计

### 9.1 邮箱配置 API

#### POST /api/email/config - 创建邮箱配置
```json
// Request
{
  "email_address": "user@example.com",
  "password": "email_password",
  "imap_server": "imap.example.com",
  "imap_port": 993,
  "use_ssl": true,
  "provider": "custom",
  "config_name": "我的邮箱"
}

// Response
{
  "id": 1,
  "email_address": "user@example.com",
  "is_verified": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### GET /api/email/configs - 获取邮箱配置列表
```json
// Response
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
      "next_check_at": "2025-01-01T13:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### PUT /api/email/config/{config_id} - 更新邮箱配置
```json
// Request
{
  "check_frequency": "daily",
  "is_active": true
}

// Response
{
  "id": 1,
  "check_frequency": "daily",
  "is_active": true,
  "updated_at": "2025-01-01T12:00:00Z"
}
```

#### DELETE /api/email/config/{config_id} - 删除邮箱配置
```json
// Response
{
  "message": "邮箱配置已删除"
}
```

#### POST /api/email/config/{config_id}/verify - 验证邮箱连接
```json
// Response
{
  "success": true,
  "message": "连接成功"
}
```

### 9.2 邮件处理 API

#### POST /api/email/check - 手动触发邮件检查
```json
// Request
{
  "config_id": 1  // 可选，不指定则检查所有启用的配置
}

// Response
{
  "success": true,
  "processed": 5,
  "imported": 3,
  "skipped": 2,
  "failed": 0
}
```

#### GET /api/email/processed - 获取已处理邮件列表
```json
// Response
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

### 9.3 邮箱服务商模板 API

#### GET /api/email/providers - 获取邮箱服务商列表
```json
// Response
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
    },
    {
      "id": "gmail",
      "name": "Gmail",
      "imap_server": "imap.gmail.com",
      "imap_port": 993,
      "use_ssl": true,
      "help_url": "https://support.google.com/mail/"
    },
    {
      "id": "outlook",
      "name": "Outlook",
      "imap_server": "outlook.office365.com",
      "imap_port": 993,
      "use_ssl": true,
      "help_url": "https://support.microsoft.com/outlook"
    }
  ]
}
```

---

## 10. 技术实现要点

### 10.1 邮箱凭证加密

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
        """初始化加密器

        Args:
            master_key: 主密钥，如果不提供则从环境变量获取
        """
        self.master_key = master_key or os.getenv("PASSWORD_ENCRYPTION_KEY")
        if not self.master_key:
            raise ValueError("PASSWORD_ENCRYPTION_KEY not set")

        # 从主密钥派生 Fernet 密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'notion_bill_importer',  # 固定 salt，实际应该使用随机 salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, password: str) -> str:
        """加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码（Base64 编码）
        """
        encrypted = self.cipher.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码

        Args:
            encrypted_password: 加密的密码

        Returns:
            明文密码
        """
        encrypted = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
```

### 10.2 邮件解析服务

```python
# src/services/email_parse_service.py
import re
import logging
from email import message_from_string
from typing import Optional, Dict, List
from imap_tools import MailBox

logger = logging.getLogger(__name__)

class EmailParseService:
    """邮件解析服务"""

    # 发件人白名单
    SENDERS_WHITELIST = {
        'alipay': ['alipay@alipay.com', 'service@alipay.com'],
        'wechat': ['weixinpay@wechat.com', 'pay@wechat.com'],
        'unionpay': ['unionpay@95516.com', 'service@95516.com']
    }

    # 主题关键词
    SUBJECT_KEYWORDS = ['账单', '交易记录', '消费明细', '支付记录']

    # 密码提取正则表达式
    PASSWORD_PATTERNS = [
        r'密码[：:]\s*([A-Za-z0-9]{6,20})',
        r'解压密码[：:]\s*([A-Za-z0-9]{6,20})',
        r'password[：:]\s*([A-Za-z0-9]{6,20})',
        r'提取码[：:]\s*([A-Za-z0-9]{6,20})'
    ]

    @classmethod
    def is_bill_email(cls, email_msg) -> Optional[Dict]:
        """判断是否为账单邮件

        Args:
            email_msg: 邮件消息对象

        Returns:
            如果是账单邮件，返回平台信息；否则返回 None
        """
        # 检查发件人
        from_addr = email_msg.from_
        if not from_addr:
            return None

        from_email = from_addr.lower()

        # 匹配发件人白名单
        for platform, senders in cls.SENDERS_WHITELIST.items():
            if any(sender in from_email for sender in senders):
                return {'platform': platform}

        return None

    @classmethod
    def extract_password(cls, email_body: str) -> Optional[str]:
        """从邮件正文提取解压密码

        Args:
            email_body: 邮件正文

        Returns:
            提取到的密码，如果未找到则返回 None
        """
        for pattern in cls.PASSWORD_PATTERNS:
            match = re.search(pattern, email_body)
            if match:
                password = match.group(1)
                logger.info(f"找到密码: {password[:2]}***{password[-2:]}")
                return password

        logger.warning("未能从邮件正文中提取密码")
        return None

    @classmethod
    def extract_attachments(cls, email_msg) -> List[Dict]:
        """提取邮件附件

        Args:
            email_msg: 邮件消息对象

        Returns:
            附件列表，每个附件包含 filename 和 payload
        """
        attachments = []

        for att in email_msg.attachments:
            filename = att.filename
            if not filename:
                continue

            # 检查文件类型
            if not (filename.endswith('.csv') or filename.endswith('.zip') or
                    filename.endswith('.xls') or filename.endswith('.xlsx')):
                continue

            attachments.append({
                'filename': filename,
                'payload': att.payload,
                'content_type': att.content_type
            })

        return attachments
```

---

## 11. 用户界面设计要点

### 11.1 邮箱配置页面

**位置**: 设置页面 → 邮箱配置

**页面元素**:
1. **配置列表区域**
   - 已配置邮箱列表
   - 每个配置显示：邮箱地址、服务商、连接状态、最后检查时间
   - 操作按钮：编辑、删除、测试连接

2. **添加配置按钮**
   - 打开添加配置模态框

3. **添加配置模态框**
   - 邮箱服务商下拉框（一键填充配置）
   - 邮箱地址输入框
   - 密码输入框
   - IMAP 服务器输入框
   - 端口输入框
   - SSL/TLS 开关
   - 配置名称输入框
   - 测试连接按钮
   - 保存按钮

### 11.2 邮箱导入历史

**位置**: 历史记录页面 → 邮箱导入标签

**页面元素**:
1. **筛选器**
   - 邮箱配置筛选
   - 状态筛选（成功/失败/待处理）
   - 日期范围筛选

2. **导入记录列表**
   - 邮件日期
   - 发件人
   - 平台
   - 附件名
   - 状态
   - 错误信息（如果有）
   - 处理时间

### 11.3 邮箱导入设置

**位置**: 设置页面 → 邮箱导入设置

**页面元素**:
1. **检查频率选择**
   - 实时（不推荐，可能频繁检查）
   - 每小时（推荐）
   - 每天
   - 每周
   - 手动

2. **通知设置**
   - 导入成功通知
   - 导入失败通知
   - 通知方式（邮件/应用内通知）

---

## 12. 测试计划

### 12.1 单元测试

#### 邮箱凭证加密测试
```python
def test_password_encryption():
    crypto = PasswordEncryption()
    password = "test_password"

    # 测试加密
    encrypted = crypto.encrypt(password)
    assert encrypted != password
    assert len(encrypted) > 0

    # 测试解密
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == password
```

#### 邮件解析测试
```python
def test_is_bill_email():
    # 模拟支付宝邮件
    mock_email = Mock(from_='alipay@alipay.com', subject='您的账单')
    result = EmailParseService.is_bill_email(mock_email)
    assert result['platform'] == 'alipay'

def test_extract_password():
    email_body = "您的账单密码是：abc12345"
    password = EmailParseService.extract_password(email_body)
    assert password == "abc12345"
```

### 12.2 集成测试

#### 邮箱连接测试
```python
def test_email_connection():
    # 使用测试邮箱
    config = {
        'email_address': 'test@example.com',
        'password': 'test_password',
        'imap_server': 'imap.example.com',
        'imap_port': 993
    }

    service = EmailImportService(db)
    result = service.check_and_import(config['id'])
    assert result['success'] == True
```

### 12.3 端到端测试

1. **配置邮箱并导入**
   - 用户登录
   - 配置 QQ 邮箱
   - 发送测试账单邮件到邮箱
   - 等待系统检查
   - 验证账单导入成功

2. **去重测试**
   - 导入同一封邮件两次
   - 验证第二次被跳过

---

## 13. 发布计划

### 13.1 MVP 版本 (v2.3.0)

**功能范围**:
- 邮箱配置管理（IMAP 协议）
- 邮件识别与解析（支付宝、微信）
- 自动导入调度（每小时）
- 导入历史跟踪

**预计发布时间**: 开发开始后 3 周

### 13.2 增强版本 (v2.4.0)

**新增功能**:
- 支持 POP3 协议
- 支持银联账单邮件
- 多邮箱配置
- 更灵活的调度策略

**预计发布时间**: MVP 发布后 1 个月

### 13.3 高级版本 (v2.5.0)

**新增功能**:
- 智能密码提取（机器学习）
- 邮件内容预览
- 导入模板和规则
- OAuth 2.0 认证支持

**预计发布时间**: 增强版本发布后 2 个月

---

## 14. 总结

本需求发现报告全面分析了"邮箱账单自动导入"功能的需求、复杂度、风险和实现方案。主要结论如下：

### 核心价值
- 将账单导入从"手动操作"升级为"完全自动化"
- 减少用户操作步骤，提升产品竞争力
- 与现有功能并存，不影响现有用户体验

### 技术可行性
- 技术方案成熟，使用主流 Python 库
- 与现有架构兼容良好
- 安全机制完善，风险可控

### 实施建议
- 采用敏捷开发模式，分阶段交付
- MVP 优先实现核心功能
- 优先支持主流邮箱服务商
- 加强安全审计和监控

### 后续优化方向
- 引入机器学习优化邮件识别
- 支持更多邮箱协议和认证方式
- 智能推荐和预测功能

---

**报告生成时间**: 2025-01-02
**报告版本**: v1.0
**作者**: Discovery Agent
