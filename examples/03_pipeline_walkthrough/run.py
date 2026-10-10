#!/usr/bin/env python3
"""
管线漫游 — 跟着一条真实管线走完 R1 → R12
==========================================
无模型的「虚拟运行」，展示调度引擎（00_orchestrator.md）的核心行为：
  角色交接 · 质量门禁 · 定向回环 · 三级上下文预算 · CTO 五维评分 · 记忆写入

运行: python3 examples/03_pipeline_walkthrough/run.py   （零依赖，2 秒）
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
GREEN, RED, YELLOW, DIM, RESET = "\033[0;32m", "\033[0;31m", "\033[1;33m", "\033[2m", "\033[0m"

STAGES = [
    ("R1",  "需求分析",  "docs/requirements.md",   "3 条用户故事 + 验收标准"),
    ("R2",  "产品设计",  "docs/product_spec.md",   "功能清单 + MVP 边界"),
    ("R3",  "视觉创意",  "docs/creative_brief.md", "3 个 Mood Board 方向 + 外部参考"),
    ("R4",  "后端开发",  "backend/",               "API 全绿 + 健康检查"),
    ("R5",  "前端开发",  "frontend/",              "五态完整界面"),
    ("R6",  "测试+安全", "tests/",                 "pytest 全绿 + 安全加固"),
    ("R8",  "运维部署",  "deploy/",                "Dockerfile + 回滚方案"),
    ("R9",  "AI+提示词", "prompts/",               "AI 集成 + 降级逻辑"),
    ("R10", "CTO 审查",  "CTO_REVIEW_REPORT.md",   "五维评分 + 修复"),
    ("R12", "集成验证",  "docs/mvp_validation.md", "验收脚本全 PASS"),
]

# 上游产出累计体积（KB）→ 触发三级上下文预算
CTX_KB = {"R1": 2.1, "R2": 4.8, "R3": 7.2, "R4": 9.6, "R5": 11.4,
          "R6": 13.1, "R8": 15.0, "R9": 16.8, "R10": 18.4, "R12": 20.5}


def tier(kb):
    if kb > 20:
        return "CTX_CRITICAL", RED, "仅消费摘要；需显式声明才读源文件"
    if kb > 12:
        return "CTX_WARNING", YELLOW, "摘要优先；源文件按需深读"
    return "CTX_NORMAL", GREEN, "正常加载全部交接物"


def read_name():
    p = ROOT / "plans" / "active_plan.md"
    if p.is_file():
        m = re.search(r"项目名[：:]\s*(.+)", p.read_text(encoding="utf-8"))
        if m and m.group(1).strip():
            return m.group(1).strip()
    return "示例项目"


def main():
    name = read_name()
    print("=" * 68)
    print(f"  管线漫游 · 「{name}」的一个完整交付周期（虚拟运行）")
    print("=" * 68)

    for r, role, art, note in STAGES:
        kb = CTX_KB[r]
        t, color, hint = tier(kb)
        print(f"\n  {r:<4} {role:<7} → {art}")
        print(f"       {DIM}产出: {note}{RESET}")
        print(f"       {color}上下文预算: 上游累计 {kb:.1f}KB [{t}] — {hint}{RESET}")

        if r == "R10":
            print(f"\n       {RED}R10 ◀ CTO 首轮: 5.8/10（< 6 不放过）{RESET}")
            print(f"       {DIM}问题分类: 代码 Bug（HIGH ×1）→ 定向回环 R4，而不是回退到起点{RESET}")
            print(f"\n  R4   (回环修复) → 补齐错误处理 · Bash 验证 EXIT:0")
            print(f"       {GREEN}R10 ▶ CTO 复审: 8.2/10 · 五维 [正确性 8 · 安全 7 · 维护 8 · 性能 7 · UX 9] ✅ 放行{RESET}")

        print(f"       {DIM}记忆写入: _index 摘要更新 · project 记忆追加 · 会话边界自动保存{RESET}")

    print(f"\n  🏁 R12 验收脚本: 4 / 4 PASS → merge to main → tag v1.0.0-mvp")
    print(f"  {DIM}上线后由「工程模式」接管：健康检查 → 快照 → 依赖分析 → 修改 → 回归 → 记录{RESET}")
    print()
    print("=" * 68)
    print("  演示结束 — 完整规则见 pipeline/agent_core.md · pipeline/00_orchestrator.md")
    print("=" * 68)


if __name__ == "__main__":
    main()
