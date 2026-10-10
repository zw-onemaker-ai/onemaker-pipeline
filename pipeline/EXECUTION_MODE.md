# 执行模式标准 v4.4.0 — OneMaker Pipeline
> 与 agent_core.md 互补：agent_core 定义规则，本文件定义"具体怎么做"。
> 独立化标准——验证拦截 · 场景策略 · 安全门禁链。
> v4.4.0：断链类型分类+安全门禁链图+上下文预算阈值上调(12KB/20KB)+CTO定向回环触发。

## 核心原则
> **每个角色产出必须是下游能接手、出问题能排查的实际产物。代码类产出必须通过 Bash 验证含 EXIT_CODE 指纹。不同场景使用不同的技术策略——绿地项目快速迭代，遗留集成必须对接现有系统，AI 项目必须对话可交互。**

## 验证拦截（每个角色产出后强制）
```
[ ] Part A 是否为实际文件（不是方案描述）？
[ ] 代码类产出：Bash 验证 + EXIT_CODE 指纹（echo "EXIT:$?"）
[ ] 文档类产出：产出验证指纹（见 agent_core.md 速查表）
[ ] Orchestrator 是否执行了 quality_gate 外部校验？
[ ] R4 起：Step 0.5 验收锚定（逐条对照 R1 验收标准）
[ ] R6 安全：HIGH 清零 + STRIDE 建模
[ ] 🔴 面向客户的 Part A 是否脱敏？（无管线术语泄漏）
[ ] Part B 含 Context Card 段（R1-R10 强制）
[ ] 🔴 已写入 memory/projects/{name}.json + 同步 memory/_index.json
[ ] 🔴 ContextPackage 已物化到 memory/projects/{name}/context_r{n}.json
```

## 角色执行标准 v4.4.0

| 角色 | 合格产出 | 场景适配 | Bash验证 |
|------|---------|---------|----------|
| R1 需求分析 | `docs/requirements.md` ≥3用户故事+验收标准+场景初判 | 场景初判→写入 | — |
| R2 产品设计 | `docs/product_spec.md` + 安全架构+场景确认 | 场景确认+技术选型 | — |
| R3 视觉创意 | `docs/creative_brief.md` + Mood Board 3方向+色彩推导 | web_fetch ≥3 URL | — |
| R4 后端开发 | `backend/` 含健康检查+DB Schema+API契约 | 按场景切换DB策略 | `python backend/main.py` |
| R5 前端开发 | `frontend/` 含CSS变量(遵循R3宪法)+五态完整 | 按场景调整UI复杂度 | `npm run build` |
| R6 质量+安全 | 测试代码+安全加固+STRIDE+OWASP10 | 全场景回归 | `pytest backend/` |
| R8 运维部署 | Dockerfile+nginx配置+回滚方案 | greenfield: bare_metal | `docker build` |
| R9 AI+提示词 | AI集成代码+Prompt+降级+成本估算 | AI场景:权重↑ | `python ai_test.py` |
| R10 CTO审查 | `CTO_REVIEW_REPORT.md` + 五维评分 | 按类型维度映射 | `python backend/main.py` |
| R11 运营推广 | 推广文案+渠道策略+内容日历 | 仅public激活 | — |
| R12 集成验证 | 验收报告+MVP放行+业务指标采集 | 全场景P0验收 | `bash验收脚本` |

## 🔴 场景 × 验证策略对照表

| 场景 | R3 视觉权重 | R4 后端策略 | R6 安全深度 | R8 部署策略 | R10 CTO门禁 |
|------|:--:|-----------|:--:|-----------|:--:|
| **绿地项目** | 正常 | clean_slate | 基础安全 | bare_metal_first | ≥6/10 |
| **遗留集成** | 正常 | adapter_heavy | 凭据安全优先 | 对接优先 | ≥6/10 |
| **AI 驱动** | 正常 | ai_ux | Prompt注入优先 | 轻量部署 | ≥6/10 |
| **全栈产品** | 正常 | all_equal | 全OWASP覆盖 | 完整部署 | ≥6/10 |
| **个人工具** | 简化 | simplified | 基础安全 | minimal | ≥6/10 |

```
失败 → 修复 → 重试（最多 3 轮）→ 仍失败 = quality_gate FAIL
```

## 🔴 断链类型分类（v4.4.0）

`[UPSTREAM_BROKEN]` ≠ quality_gate FAIL — 不回环，不回退角色重做。中断 = 上游产出物理缺失，不是质量问题。

| 断链类型 | 检测方法 | 处理方式 |
|---------|---------|---------|
| **ContextPackage 缺失** | `context_r{n-1}.json` 文件不存在 | orchestrator 检查是否上游未生成 → 退回上游重新生成 |
| **产出文件缺失** | ContextPackage 内引用的文件不存在 | 可能被误删 → 报告缺失清单 → 等待 Owner 决策 |
| **验收基线缺失** | `context_r01.json` 或 `requirements.md` 不存在 | 阻塞全部下游 → 紧急修复 → 退回 R1 重新生成 |
| **Handoff 契约断裂** | Structured Handoff JSON 与源文件矛盾 | 以源文件为准 → Handoff 标记为 stale → 上游质量降级 |

处理流程：orchestrator 暂停管线 → 报告缺失文件清单 + 断链类型 → 等待 Owner 决策（手动修复 / 跳过该角色 / 放弃项目 / 退回上游重生成 ContextPackage）

## 🔴 安全门禁链（v4.4.0 形式化）

```
R1 标注安全节点 → R2 设计安全架构 → R4 标注敏感字段
  → R5/R6 实现安全控制 → R8 验证部署安全
    → R6 独立安全审计（STRIDE+OWASP）+ HIGH清零 ← 🔴 不可绕过
      → R10 CTO安全评分(安全性维度25%权重) → R12 安全验收
```

**各角色安全职责速查：**
| 角色 | 安全职责 | 关键产出 |
|------|---------|---------|
| R1 | 标注安全关键流程（🔒标记） | requirements.md 中标注涉敏节点 |
| R2 | 安全架构设计（认证/授权/加密） | 安全选型方案 |
| R4 | 敏感字段标注（PII/机密数据） | 数据分类标签 |
| R5 | XSS/CSRF/Token管理/输入校验 | 前端安全5项 |
| R6 | STRIDE+OWASP+安全加固+测试脱敏 | 安全审计报告+HIGH清零 |
| R8 | 密钥管理+最小权限+安全监控 | 部署安全检查 |
| R10 | 安全性维度25%权重 | CTO安全评分 |
| R12 | 安全验收 | 安全门禁通过确认 |

## 🔴 CTO 定向回环路由表（v4.4.0）

| 问题类型 | 回环目标 | 示例 |
|---------|:--:|------|
| 代码Bug/安全漏洞为主 | → R4/R5/R6 | 内存泄漏、SQL注入、XSS |
| 架构/设计问题为主 | → R2 | 技术选型错误、架构不合理 |
| 视觉/前端问题为主 | → R3/R5 | 视觉宪法偏离、UI不专业 |
| 数据模型问题为主 | → R4 | DB Schema缺陷、数据冗余 |
| 安全合规问题为主 | → R6 | OWASP不通过、STRIDE缺失 |
| 混合问题 | → R2（架构层面解决） | 多维度缺陷根因在方案设计 |

> 回环 >2 次 → 自动触发 Pipeline Doctor（不再回环执行）

## 场景类型切换协议（R1→R2→下游）
```
1. R1 Step 4.5: 根据用户描述判定初步场景类型 → 写入 requirements.md
2. R2 Step 0: 读取 R1 场景类型 → 确认或修正 → 写入 project memory
3. R4-R12 Step 0: 从 project memory 读取 scenario_type → 按场景调整策略
4. R13 检查: 场景类型在下游角色的实际执行中是否一致
```
