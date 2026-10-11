#!/usr/bin/env bash
# RSI 闸门验证器（OneMaker Pipeline v4.4.1）
# 用法: bash pipeline/tools/rsi_check.sh     ← 「上班打卡」时执行
# 机制: memory/lessons.md 中每条教训的「预防闸门」在此注册为一条检查；有失败项 → 优先修正后重新打卡。
cd "$(dirname "$0")/../.." || exit 1
FAIL=0
ok(){ echo "  ✅ $1"; }
bad(){ echo "  ❌ $1"; FAIL=1; }

echo "== RSI 闸门验证 · $(date '+%F %T') =="

# ── 示例闸门 1 · 记忆索引必须合法 ──
if python3 -c "import json; json.load(open('memory/_index.json'))" 2>/dev/null; then
  ok "闸门 1  memory/_index.json 合法"
else
  bad "闸门 1  memory/_index.json 非法 JSON"
fi

# ── 示例闸门 2 · 登记册与硬规则必须在岗 ──
if [ "$(grep -c '硬规则' memory/lessons.md 2>/dev/null)" -ge 1 ]; then
  ok "闸门 2  memory/lessons.md 登记册在岗"
else
  bad "闸门 2  memory/lessons.md 缺失或损坏"
fi

# ── 在此追加新闸门（每条 lessons.md 教训的「预防闸门」对应一个检查块）──

echo "──────────────────────────────────────────"
if [ $FAIL -eq 0 ]; then echo "RSI 结果: 无失败项"; else echo "RSI 结果: 有失败项 → 优先修正后重新打卡"; fi
exit $FAIL
