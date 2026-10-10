#!/usr/bin/env python3
"""
质量门禁演示 — 三道闸门如何拦截「假装完成」的产出
===================================================
对应管线机制（pipeline/agent_core.md · 验证拦截）:
  · 闸门① 文件存在性     — Agent 说「文件写好了」，磁盘上必须真的有、且非空
  · 闸门② EXIT_CODE 指纹 — Agent 说「测试全过」，必须贴出退出码
                            （Agent 可以编话，编不了退出码）
  · 闸门③ 文档脱敏       — 面向客户的产出不能含内部术语

核心规则：不通过 → 不路由给下游。

运行: python3 examples/01_quality_gate/demo.py   （零依赖，5 秒内跑完）
"""
import os
import re
import tempfile

GREEN, RED, DIM, RESET = "\033[0;32m", "\033[0;31m", "\033[2m", "\033[0m"

# ── 闸门实现（极简版，完整协议见 pipeline/agent_core.md）──

def gate_file_exists(claims, root):
    """闸门①：声称产出的每个文件，必须真实存在且非空。"""
    missing = [c for c in claims
               if not os.path.isfile(os.path.join(root, c))
               or os.path.getsize(os.path.join(root, c)) == 0]
    if missing:
        return False, f"磁盘上缺少或为空: {missing} → 「已完成」不成立"
    return True, f"{len(claims)} 个文件全部真实存在且非空"

EXIT_RE = re.compile(r"EXIT:(\d+)")

def gate_exit_fingerprint(report):
    """闸门②：验证输出必须带 EXIT:<code> 指纹，且退出码为 0。"""
    codes = EXIT_RE.findall(report)
    if not codes:
        return False, "未找到 EXIT_CODE 指纹 → 该验证视为未执行"
    bad = [f"EXIT:{c}" for c in codes if int(c) != 0]
    if bad:
        return False, f"退出码非零: {bad}"
    return True, f"发现 {len(codes)} 处 EXIT:0 指纹"

FORBIDDEN = ["管线", "quality_gate", "CTO审查", "orchestrator", "agent_core"]

def gate_desensitize(doc):
    """闸门③：客户可见文档不得含内部术语。"""
    hits = sorted({w for w in FORBIDDEN if w in doc})
    if hits:
        return False, f"含内部术语: {hits}"
    return True, "无内部术语，可以交付"

# ── 演示编排 ──

CASES = []  # (描述, 期望结果, 实际结果)

def case(desc, expect, fn, *args):
    ok, detail = fn(*args)
    CASES.append((desc, expect, ok))
    tag = f"{GREEN}✅ 放行{RESET}" if ok else f"{RED}⛔ 拦截{RESET}"
    print(f"  {tag}  {desc}")
    print(f"       {DIM}{detail}{RESET}")

def main():
    print("=" * 66)
    print("  质量门禁演示 · 三道闸门（不通过不路由）")
    print("=" * 66)

    with tempfile.TemporaryDirectory() as tmp:
        print("\n▌场景 1 · 闸门①：文件存在性")
        open(os.path.join(tmp, "main.py"), "w").write("print('hi')\n")
        claims = ["main.py", "config.json"]
        case("Agent 声称产出 [main.py, config.json]，实际只写了 1 个",
             False, gate_file_exists, claims, tmp)
        open(os.path.join(tmp, "config.json"), "w").write("{}\n")
        case("补齐 config.json 后", True, gate_file_exists, claims, tmp)

    print("\n▌场景 2 · 闸门②：EXIT_CODE 指纹")
    fake = "Ran 42 tests... OK\n所有测试通过！"
    case("「测试全过」但没有任何退出码", False, gate_exit_fingerprint, fake)
    real = '$ pytest\nRan 42 tests... OK\n$ echo "EXIT:$?"\nEXIT:0'
    case("贴出 EXIT:0 指纹", True, gate_exit_fingerprint, real)
    failed = "$ pytest\n2 failed, 40 passed\nEXIT:1"
    case("退出码非零（测试真的挂了）", False, gate_exit_fingerprint, failed)

    print("\n▌场景 3 · 闸门③：文档脱敏")
    leaky = "本页面由 CTO审查 通过，quality_gate: PASS，管线运行正常"
    case("客户文档混入内部术语", False, gate_desensitize, leaky)
    clean = "本产品已通过上线前的质量检查与安全审查"
    case("清理后的客户文档", True, gate_desensitize, clean)

    total = len(CASES)
    good = sum(1 for _, exp, got in CASES if exp == got)
    print("\n" + "=" * 66)
    print(f"  演示完成：{good}/{total} 个用例行为符合预期"
          f"（拦截 {sum(1 for _, e, g in CASES if not g)} 次 · 放行 {sum(1 for _, e, g in CASES if g)} 次）")
    print("  真实系统中：拦截 → 定向回环给对应角色修复，而不是把问题传给下游")
    print("=" * 66)

if __name__ == "__main__":
    main()
