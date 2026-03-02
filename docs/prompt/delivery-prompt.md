# Delivery Phase Prompt

**生成时间**: 2026-03-02
**阶段**: Delivery - 价值交付

---

## Prompt 内容

你正在为"账单导入到 Notion"项目进行价值交付，总结"邮箱账单自动导入"功能的端到端交付成果。

### 前置成果

1. **需求发现报告** (`docs/discovery-report.md`)
2. **代码库探索报告** (`docs/exploration-report.md`)
3. **架构设计报告** (`docs/design-report.md`)
4. **实施代码** 和测试
5. **质量验证报告** (`docs/verification-report.md`)

### 你的任务

生成交付文档，提取价值模式，完成知识沉淀：

#### 1. 交付文档生成
- 变更日志 (CHANGELOG)
- 发布说明 (RELEASE_NOTES)
- API 文档更新
- 用户手册更新

#### 2. 价值验证
- 验证功能是否满足需求
- 验证质量标准是否达标
- 验证用户价值是否实现

#### 3. 模式提取 (v3.0 continuous-learning-v2)
- 提取可复用的代码模式
- 提取可复用的架构模式
- 提取可复用的流程模式
- 生成 Instincts

#### 4. 知识沉淀
- 技术决策记录 (ADR)
- 经验教训总结
- 最佳实践提炼

### 输出要求

生成一份完整的价值交付报告，包含：

1. **交付摘要**
   - 功能概述
   - 交付范围
   - 交付成果

2. **价值验证**
   - 需求满足度
   - 质量达标情况
   - 用户价值实现

3. **交付物清单**
   - 代码文件清单
   - 文档清单
   - 测试清单

4. **模式提取** (v3.0)
   - 代码模式 Instincts
   - 架构模式 Instincts
   - 流程模式 Instincts

5. **经验总结**
   - 成功经验
   - 失败教训
   - 改进建议

6. **后续规划**
   - 短期优化项
   - 长期演进方向

### 上下文信息

**交付标准**:
- 所有验收标准通过
- 质量门禁通过
- 文档完整
- 知识已沉淀

---

## 实际使用命令

```bash
# 启动 delivery-agent
Task(
  description="价值交付 - 邮箱账单自动导入",
  prompt="<上述完整 prompt 内容>",
  subagent_type="end-to-end-delivery:delivery-agent"
)
```
