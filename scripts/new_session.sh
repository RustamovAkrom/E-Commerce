#!/usr/bin/env bash
# Run before every Claude Code session:
#   bash scripts/new_session.sh
# Then paste the output into Claude Code as your first message.

set -e

echo "============================================"
echo "  E-COMMERCE — Claude Code Session Starter"
echo "============================================"
echo ""

# Update snapshot
bash scripts/update_claude_snapshot.sh > /dev/null 2>&1

# Count files
PY_COUNT=$(find backend/src -type f -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
TS_COUNT=$(find frontend/src -type f \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | wc -l | tr -d ' ')
BOT_COUNT=$(find bot -type f -name "*.py" 2>/dev/null | wc -l | tr -d ' ')

# Read current status from CLAUDE.md
CURRENT=$(grep "^CURRENT:" CLAUDE.md 2>/dev/null | head -1 || echo "CURRENT: unknown")
NEXT=$(grep "^NEXT:" CLAUDE.md 2>/dev/null | head -1 || echo "NEXT: unknown")

echo "--------------------------------------------"
echo "PASTE THIS INTO CLAUDE CODE:"
echo "--------------------------------------------"
echo ""
echo "Read CLAUDE.md and PROJECT_SNAPSHOT.md."
echo "DO NOT scan filesystem — snapshot has current state."
echo "Project has $PY_COUNT backend .py files, $BOT_COUNT bot .py files, $TS_COUNT frontend .ts/tsx files."
echo "$CURRENT"
echo "$NEXT"
echo "Continue building from CURRENT task. Complete working code only."
echo ""
echo "--------------------------------------------"
echo "Session starter ready. Paste the text above."
echo "--------------------------------------------"
