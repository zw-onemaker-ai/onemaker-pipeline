#!/bin/bash
# OneMaker Pipeline v4.4.0 — 管线验证器（14 角色：R1-R12 + R13审计 + R13文案）
# 用法:
#   手动: bash pipeline/tools/validate.sh <project_name> [--role R{n}] [--check-loopback] [--check-desensitize]
#   自动: bash pipeline/tools/validate.sh <project_name> --auto [--role R{n}] [--check-context]
#   Orchestrator 调用: bash pipeline/tools/validate.sh <project_name> --auto --role R{n} --check-context

set -euo pipefail
PROJECT_NAME="${1:-}"
ROLE=""
CHECK_LOOPBACK=false
CHECK_DESENSITIZE=false
CHECK_CONTEXT=false
AUTO_MODE=false

shift 2>/dev/null || true
for arg in "$@"; do
  case "$arg" in
    --check-loopback) CHECK_LOOPBACK=true ;;
    --check-desensitize) CHECK_DESENSITIZE=true ;;
    --check-context) CHECK_CONTEXT=true ;;
    --auto) AUTO_MODE=true ;;
    --role) ROLE="$2"; shift ;;
  esac
  shift 2>/dev/null || true
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MEMORY_DIR="$AGENT_ROOT/memory"
PROJECTS_DIR="$MEMORY_DIR/projects"
INDEX_FILE="$MEMORY_DIR/_index.json"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# ── 辅助函数 ──
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); if ! $AUTO_MODE; then echo -e "${RED}❌ FAIL: $*${NC}"; fi; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); if ! $AUTO_MODE; then echo -e "${YELLOW}⚠️ WARN: $*${NC}"; fi; }
pass() { PASS_COUNT=$((PASS_COUNT + 1)); if ! $AUTO_MODE; then echo -e "${GREEN}✅ PASS: $*${NC}"; fi; }
info() { if ! $AUTO_MODE; then echo "$*"; fi; }

# ── 仅在非自动模式下打印头部 ──
if ! $AUTO_MODE; then
  echo "╔══════════════════════════════════════════╗"
  echo "║  🔍 OneMaker Pipeline Validator v4.4.0   ║"
  echo "╚══════════════════════════════════════════╝"
  echo ""
fi

# ── 校验 1: _index.json 大小门禁 ──
info "📋 校验 1/5: _index.json 大小门禁（上限 2048B）"
INDEX_SIZE=$(wc -c < "$INDEX_FILE" 2>/dev/null || echo "0")
if [ "$INDEX_SIZE" -gt 2048 ]; then
  fail "_index.json 大小 ${INDEX_SIZE}B > 2KB 硬上限"
  echo "   建议: 裁剪旧项目摘要，仅保留最近 5 个活跃项目"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  pass "_index.json = ${INDEX_SIZE}B (上限 2048B)"
  PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# ── 校验 2: _index.json JSON 合法性 ──
info "📋 校验 2/5: _index.json JSON 合法性"
if python3 -c "import json; json.load(open('$INDEX_FILE')); print('valid')" 2>/dev/null | grep -q valid; then
  pass "_index.json 是合法 JSON"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  fail "_index.json 不是合法 JSON"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# ── 校验 3: project memory 完整性 ──
info "📋 校验 3/5: Project Memory 完整性"
if [ -n "$PROJECT_NAME" ]; then
  PROJ_FILE="$PROJECTS_DIR/${PROJECT_NAME}.json"
  if [ -f "$PROJ_FILE" ]; then
    PROJ_SIZE=$(wc -c < "$PROJ_FILE")
    if [ "$PROJ_SIZE" -gt 8192 ]; then
      warn "${PROJECT_NAME}.json = ${PROJ_SIZE}B > 8KB 上限"
    else
      pass "${PROJECT_NAME}.json = ${PROJ_SIZE}B"
    fi
    
    # 关键字段检查
    python3 -c "
import json
d = json.load(open('$PROJ_FILE'))
status = d.get('status', '?')
cto = d.get('cto_latest_score', 'N/A')
mvp = d.get('mvp_status', '?')
launch = d.get('launch_type', '?')
print(f'   状态: {status} | CTO: {cto} | MVP: {mvp} | 类型: {launch}')
ctos = len(d.get('cto_reviews', []))
loopbacks = sum(1 for r in d.get('cto_reviews', []) if r.get('loopback'))
print(f'   CTO审查: {ctos}次 | 回环: {loopbacks}次')
" 2>/dev/null
  else
    warn "project memory 不存在: $PROJ_FILE"
  fi
else
  warn "未指定 project_name——跳过此校验"
fi
echo ""

# ── 校验 4: EXIT_CODE 指纹检查 ──
info "📋 校验 4/5: EXIT_CODE 指纹检查"
if [ -n "$ROLE" ] && [ -n "$PROJECT_NAME" ]; then
  ROLE_DIR="${AGENT_ROOT}/projects/${PROJECT_NAME}"
  
  case "$ROLE" in
    R4) SEARCH_DIR="backend"; SEARCH_PAT="*.py" ;;
    R5) SEARCH_DIR="frontend"; SEARCH_PAT="*.html" ;;
    R6) SEARCH_DIR="backend"; SEARCH_PAT="test_*.py" ;;
    R10) SEARCH_DIR="."; SEARCH_PAT="CTO_REVIEW_REPORT.md" ;;
    R12) SEARCH_DIR="docs"; SEARCH_PAT="mvp_validation.*" ;;
    *) SEARCH_DIR="."; SEARCH_PAT="*" ;;
  esac
  
  FOUND_EXIT=false
  if [ -d "$ROLE_DIR/$SEARCH_DIR" ]; then
    while IFS= read -r f; do
      if grep -q 'EXIT:[0-9]' "$f" 2>/dev/null; then
        COUNT=$(grep -c 'EXIT:[0-9]' "$f" 2>/dev/null || echo "0")
        echo -e "   ${GREEN}✅ $f: ${COUNT} 处 EXIT_CODE 指纹${NC}"
        FOUND_EXIT=true
      fi
    done < <(find "$ROLE_DIR/$SEARCH_DIR" -name "$SEARCH_PAT" -type f 2>/dev/null | head -20)
  fi
  
  if ! $FOUND_EXIT; then
    fail "$ROLE: 未找到 EXIT_CODE 指纹"
  fi
else
  warn "使用 --role R{n} <project_name> 指定角色"
fi
echo ""

# ── 校验 5: 文档脱敏检查 ──
if $CHECK_DESENSITIZE && [ -n "$PROJECT_NAME" ]; then
  info "📋 校验 5/5: 客户文档脱敏检查"
  PROJ_DIR="${AGENT_ROOT}/projects/${PROJECT_NAME}"
  FORBIDDEN="管线|pipeline|R[0-9]|Bash验证|CTO审查|quality_gate|orchestrator|agent_core|verification_evidence|Part [AB]|审计报告|记忆写入|ContextPackage"
  
  LEAKS=0
  for f in $(find "$PROJ_DIR/frontend" -name "*.html" -o -name "*.css" -o -name "*.js" 2>/dev/null | head -20); do
    if grep -qnE "$FORBIDDEN" "$f" 2>/dev/null; then
      echo -e "   ${RED}❌ $f 含内部术语${NC}"
      LEAKS=$((LEAKS + 1))
    fi
  done
  
  if [ -f "$PROJ_DIR/README.md" ]; then
    if grep -qnE "$FORBIDDEN" "$PROJ_DIR/README.md" 2>/dev/null; then
      echo -e "   ${RED}❌ README.md 含内部术语${NC}"
      LEAKS=$((LEAKS + 1))
    fi
  fi
  
  if [ "$LEAKS" -eq 0 ]; then
    echo -e "   ${GREEN}✅ 客户文档脱敏通过${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "   ${RED}❌ 脱敏失败: ${LEAKS} 处泄露${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
else
  info "📋 校验 5/5: 文档脱敏检查 (使用 --check-desensitize 启用)"
fi
echo ""

# ── 校验 6: ContextPackage 物化检查 ──
if $CHECK_CONTEXT && [ -n "$PROJECT_NAME" ]; then
  info "📋 校验 6/6: ContextPackage 物化检查（v4.4.0"
  CTX_DIR="$MEMORY_DIR/projects/${PROJECT_NAME}"
  CTX_FILES=$(ls "$CTX_DIR"/context_r*.json 2>/dev/null || echo "")
  if [ -z "$CTX_FILES" ]; then
    echo -e "   ${YELLOW}⚠️ 无 ContextPackage 文件（可能尚未物化或为旧项目）${NC}"
  else
    CTX_COUNT=$(echo "$CTX_FILES" | wc -l)
    echo "   发现 ${CTX_COUNT} 个 ContextPackage"
    BROKEN_CTX=0
    for ctx in $CTX_FILES; do
      CTX_SIZE=$(wc -c < "$ctx")
      ROLE_NAME=$(basename "$ctx" .json)
      if [ "$CTX_SIZE" -gt 2048 ]; then
        echo -e "   ${YELLOW}⚠️ ${ROLE_NAME} = ${CTX_SIZE}B > 2KB${NC}"
      fi
      if python3 -c "import json; json.load(open('$ctx'))" 2>/dev/null; then
        echo -e "   ${GREEN}✅ ${ROLE_NAME} = ${CTX_SIZE}B 合法JSON${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
      else
        echo -e "   ${RED}❌ ${ROLE_NAME} JSON损坏${NC}"
        BROKEN_CTX=$((BROKEN_CTX + 1))
        FAIL_COUNT=$((FAIL_COUNT + 1))
      fi
    done
  fi
else
  info "📋 校验 6/6: ContextPackage 物化检查 (使用 --check-context <project_name> 启用)"
fi
echo ""

# ── Loopback 门禁 ──
if $CHECK_LOOPBACK && [ -n "$PROJECT_NAME" ]; then
  info "🚪 Loopback 硬门禁检查"
  PROJ_FILE="$PROJECTS_DIR/${PROJECT_NAME}.json"
  if [ -f "$PROJ_FILE" ]; then
    python3 -c "
import json
d = json.load(open('$PROJ_FILE'))
cto = d.get('cto_latest_score')
cto_reviews = d.get('cto_reviews', [])
loopback_count = sum(1 for r in cto_reviews if r.get('loopback'))
print(f'   CTO评分: {cto}/10 (门槛 ≥6)' if cto else '   CTO: 未审查')
print(f'   回环次数: {loopback_count}')
if cto and cto < 6:
    print('   🔴 CTO<6 → 必须回环')
if loopback_count >= 2:
    print('   🔴 回环≥2 → 建议 Pipeline Doctor')
if loopback_count >= 4:
    print('   ⛔ 回环≥4 → 硬终止')
" 2>/dev/null
  fi
else
  info "🚪 Loopback 门禁 (使用 --check-loopback <project_name> 启用)"
fi

echo ""

# ── 输出汇总（所有模式）──
if $AUTO_MODE; then
  # JSON 输出供 Orchestrator 消费
  if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
    echo "{\"status\":\"PASS\",\"fails\":0,\"warns\":0,\"project\":\"${PROJECT_NAME}\",\"role\":\"${ROLE}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
  else
    echo "{\"status\":\"FAIL\",\"fails\":${FAIL_COUNT},\"warns\":${WARN_COUNT},\"project\":\"${PROJECT_NAME}\",\"role\":\"${ROLE}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
  fi
else
  echo "═══════════════════════════════════════════"
  echo "  验证完成: ${PASS_COUNT} PASS / ${FAIL_COUNT} FAIL / ${WARN_COUNT} WARN"
  echo "  用法: bash pipeline/tools/validate.sh <project> [--auto] [--role R{n}] [--check-loopback] [--check-desensitize] [--check-context]"
  echo "═══════════════════════════════════════════"
fi

# ── 退出码：给调用方（Orchestrator / CI）用的信号 ──
[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
