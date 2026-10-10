#!/usr/bin/env python3
"""
记忆守卫 — 三层记忆的重量级门禁（启动健康检查）
=================================================
对应管线机制（pipeline/agent_core.md · 记忆防膨胀）:
  L1 _index.json      ≤ 4 KB    （>3KB 提醒归档；裁剪前先快照到 archive/）
  L2 projects/*.json  ≤ 8 KB    （超限归档旧审查记录）
  L3 sessions/*.json  ≤ 10 KB
  全部 JSON 必须合法；active_project 的记忆文件必须存在。

运行:
  python3 examples/02_memory_guard/check.py memory              # 检查记忆目录
  python3 examples/02_memory_guard/check.py memory --self-test  # 附「违规样例被拦截」自检
"""
import json
import os
import sys
import tempfile

L1_MAX, L1_WARN, L2_MAX, L3_MAX = 4096, 3072, 8192, 10240
GREEN, RED, YELLOW, DIM, RESET = "\033[0;32m", "\033[0;31m", "\033[1;33m", "\033[2m", "\033[0m"
ICON = {"ok": f"{GREEN}✅{RESET}", "warn": f"{YELLOW}⚠️{RESET}", "fail": f"{RED}❌{RESET}"}


def validate(memdir):
    """检查记忆目录，返回 [(level, label, detail)]，level ∈ ok/warn/fail"""
    res = []
    idx = os.path.join(memdir, "_index.json")
    if not os.path.isfile(idx):
        return [("fail", "L1 _index.json 存在", "未找到")]

    size = os.path.getsize(idx)
    res.append(("ok" if size <= L1_MAX else "fail", "L1 _index.json ≤ 4KB", f"{size}B"))
    if size > L1_WARN:
        res.append(("warn", "L1 体积提醒（>3KB 建议归档）", f"{size}B"))

    data = {}
    try:
        data = json.load(open(idx, encoding="utf-8"))
        res.append(("ok", "L1 JSON 合法", ""))
    except Exception as e:
        res.append(("fail", "L1 JSON 合法", str(e)[:60]))

    projdir = os.path.join(memdir, "projects")
    n = 0
    if os.path.isdir(projdir):
        for fn in sorted(os.listdir(projdir)):
            if not fn.endswith(".json"):
                continue
            n += 1
            p = os.path.join(projdir, fn)
            try:
                json.load(open(p, encoding="utf-8"))
            except Exception as e:
                res.append(("fail", f"L2 JSON 非法: {fn}", str(e)[:60]))
                continue
            size = os.path.getsize(p)
            res.append(("ok" if size <= L2_MAX else "fail", f"L2 尺寸: {fn}",
                        f"{size}B" + (" → 超限，需归档旧审查" if size > L2_MAX else "")))
    res.append(("ok", "L2 项目记忆数", f"{n} 个"))

    active = None
    if isinstance(data, dict):
        active = (data.get("meta", {}).get("session", {}) or {}).get("active_project")
    if active:
        af = os.path.join(projdir, active + ".json")
        ok = os.path.isfile(af)
        res.append(("ok" if ok else "fail", f"active_project 记忆存在: {active}",
                    "找到" if ok else "缺失 → 启动健康检查不通过"))
    else:
        res.append(("ok", "active_project", "未设置（空记忆库，正常）"))

    sessdir = os.path.join(memdir, "sessions")
    if os.path.isdir(sessdir):
        for fn in sorted(os.listdir(sessdir)):
            if fn.endswith(".json"):
                size = os.path.getsize(os.path.join(sessdir, fn))
                res.append(("ok" if size <= L3_MAX else "fail", f"L3 尺寸: {fn}", f"{size}B"))

    arch = os.path.isdir(os.path.join(memdir, "archive"))
    res.append(("ok" if arch else "warn", "archive/ 归档保险目录",
                "存在" if arch else "缺失（裁剪前需先快照到这里）"))
    return res


def self_test():
    """构造违规样例，验证守卫真的能拦截。"""
    print("▌自检：构造违规样例，验证守卫能拦截")
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "projects"))
        os.makedirs(os.path.join(tmp, "sessions"))
        os.makedirs(os.path.join(tmp, "archive"))
        json.dump({"meta": {"session": {"active_project": "ghost"}}, "pad": "x" * 4300},
                  open(os.path.join(tmp, "_index.json"), "w"))
        open(os.path.join(tmp, "projects", "broken.json"), "w").write("{ not valid json")
        json.dump({"pad": "y" * 8600}, open(os.path.join(tmp, "projects", "huge.json"), "w"))

        res = validate(tmp)
        checks = [
            ("L1 超 4KB 被拦截", "fail", "L1 _index.json ≤ 4KB"),
            ("L1 体积提醒触发", "warn", "L1 体积提醒"),
            ("L2 非法 JSON 被拦截", "fail", "L2 JSON 非法: broken.json"),
            ("L2 超 8KB 被拦截", "fail", "L2 尺寸: huge.json"),
            ("幽灵 active_project 被拦截", "fail", "active_project 记忆存在: ghost"),
        ]
        ok_all = True
        for name, lv, label in checks:
            hit = any(r[0] == lv and label in r[1] for r in res)
            ok_all = ok_all and hit
            print(f"  {'✅ 已拦截' if hit else '❌ 漏检'}  {name}")
        return ok_all


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    memdir = args[0] if args else "memory"
    print("=" * 62)
    print("  记忆守卫 · 三层记忆门禁（启动健康检查）")
    print("=" * 62)
    if not os.path.isdir(memdir):
        print(f"{RED}目录不存在: {memdir}{RESET}")
        sys.exit(2)

    res = validate(memdir)
    fails = warns = 0
    print(f"\n▌扫描: {memdir}")
    for lv, label, detail in res:
        line = f"  {ICON[lv]} {label}"
        if detail:
            line += f"  {DIM}{detail}{RESET}"
        print(line)
        fails += lv == "fail"
        warns += lv == "warn"

    ok_self = True
    if "--self-test" in sys.argv:
        print()
        ok_self = self_test()

    print()
    if fails:
        print(f"{RED}❌ 发现 {fails} 个硬性问题——记忆层不健康，需先处理{RESET}")
        sys.exit(1)
    tail = "；自检通过" if ok_self else "；⚠ 自检未通过，请检查守卫逻辑"
    print(f"{GREEN}✅ 记忆层健康{RESET}（{warns} 条提醒{tail}）")
    sys.exit(0 if ok_self else 1)


if __name__ == "__main__":
    main()
