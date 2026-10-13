# 投稿物料 · OneMaker Pipeline（2026-10-13 准备）

> 目标渠道：HelloGitHub（月刊收录）+ 阮一峰科技周刊（issue 直投）
> payload 已就绪（hg_onemaker.json / weekly_onemaker.json）——确认后可一键提交

## 1. HelloGitHub 投稿

**标题**：`[开源推荐] OneMaker Pipeline：给多 Agent 团队编一条交付管线`

### 项目地址

https://github.com/zw-onemaker-ai/onemaker-pipeline

### 类别

Python

### 项目标题

给多 Agent 管线装上工程制度：14 角色 · 三道闸门 · 三层记忆

### 项目描述

一条把工程团队 14 个角色编成有状态交付管线的协议集：每个交接点三道验证闸门（文件存在 / EXIT_CODE 指纹 / 脱敏检查），不通过不路由；审查失败按问题类型定向回环；三层记忆硬上限防膨胀。零依赖，附 3 个可运行 Demo，clone 下来 1 分钟看到全部机制。

### 亮点

- **把「验证」做进每个交接点**：Agent 说「完成」不算完成——三道闸门不过，产出不交给下一个角色
- **定向回环，不盲目重跑**：按问题类型回退到对应角色（Bug → 开发、架构 → 设计、安全 → 测试），回环超过 2 次自动升级诊断
- **三层记忆 + 防膨胀**：索引 ≤4KB / 项目 ≤8KB / 会话 ≤10KB，自动裁剪前先快照，可从快照恢复
- **RSI 自我迭代**：失误下班登记 → 修正 → 上班自动跑闸门验证 → 连续通过才归档
- **零第三方依赖**：3 个可运行 Demo + GitHub Actions CI 全绿；一份可直接被 Claude Code 使用的协议集

### 示例代码

```bash
git clone https://github.com/zw-onemaker-ai/onemaker-pipeline
cd onemaker-pipeline
python3 examples/01_quality_gate/demo.py        # 三道闸门如何拦截「假装完成」
python3 examples/02_memory_guard/check.py memory --self-test  # 三层记忆门禁
python3 examples/03_pipeline_walkthrough/run.py # 完整管线漫游（含一次定向回环）
```

### 截图或演示视频

![OneMaker Pipeline 架构图](https://raw.githubusercontent.com/zw-onemaker-ai/onemaker-pipeline/main/docs/images/pipeline.png)


## 2. 阮一峰周刊投稿

**标题**：`【开源自荐】OneMaker Pipeline：给多 Agent 团队编一条交付管线`

阮老师好，自荐一个开源项目：

https://github.com/zw-onemaker-ai/onemaker-pipeline

一句话：把完整工程团队的 14 个角色和工序，编成一条多 Agent 的交付管线。我不缺会用 AI 写代码的工具，缺的是「工序」——谁先谁后、什么算完成、出错了往哪退。这三个问题不解决，交付质量就只能靠运气。

这个项目的思路是把「制度」做进管线：每个角色的产出必须过三道闸门才能交给下一个角色（① 文件真实存在且非空 ② 所有验证命令必须贴出 EXIT_CODE——Agent 编得了话，编不了退出码 ③ 面向用户的产出过脱敏检查）；审查不通过不盲目重跑，而是按问题类型回环到对应角色；三层记忆给上下文装硬上限，防膨胀。

几个我觉得有意思的点：它不是新的 Agent 框架，而是「跑在 Agent 之上的制度」——一份可直接被 Claude Code 等编程 Agent 使用的协议集；零第三方依赖，仓库里 3 个 Demo（门禁 / 记忆 / 管线漫游）clone 下来 1 分钟跑完；最近还给它加了 RSI 自我迭代——失误登记 → 预防闸门 → 自动验证，管线会自己修自己的流程。

这是继 AgentGate（管线可靠性层）后的第二条线：一个管「点」（每个产出可不可信），这个管「面」（整条交付线有没有工序），可以配合使用。MIT 协议，欢迎拍砖。

