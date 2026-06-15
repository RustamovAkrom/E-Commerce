# Run before every Claude Code session:
#   powershell -ExecutionPolicy Bypass -File scripts/new_session.ps1
# Then paste the output into Claude Code as your first message.

Write-Output "============================================"
Write-Output "  E-COMMERCE - Claude Code Session Starter"
Write-Output "============================================"
Write-Output ""

# Update snapshot
powershell -ExecutionPolicy Bypass -File scripts/update_claude_snapshot.ps1 | Out-Null

# Count files
$pyCount = (Get-ChildItem -Recurse "backend/src" -Filter "*.py" -ErrorAction SilentlyContinue | Measure-Object).Count
$tsCount = (Get-ChildItem -Recurse "frontend/src" -Include "*.ts","*.tsx" -ErrorAction SilentlyContinue | Measure-Object).Count
$botCount = (Get-ChildItem -Recurse "bot" -Filter "*.py" -ErrorAction SilentlyContinue | Measure-Object).Count

# Read current status from CLAUDE.md
$claudeContent = Get-Content "CLAUDE.md" -Raw
$current = ($claudeContent | Select-String -Pattern "CURRENT:\s*(.+)" -AllMatches).Matches.Groups[1].Value
$next = ($claudeContent | Select-String -Pattern "NEXT:\s*(.+)" -AllMatches).Matches.Groups[1].Value

Write-Output "--------------------------------------------"
Write-Output "PASTE THIS INTO CLAUDE CODE:"
Write-Output "--------------------------------------------"
Write-Output ""
Write-Output "Read CLAUDE.md and PROJECT_SNAPSHOT.md."
Write-Output "DO NOT scan filesystem - snapshot has current state."
Write-Output "Project has $pyCount backend .py files, $botCount bot .py files, $tsCount frontend .ts/tsx files."
Write-Output "CURRENT: $current"
Write-Output "NEXT: $next"
Write-Output "Continue building from CURRENT task. Complete working code only."
Write-Output ""
Write-Output "--------------------------------------------"
Write-Output "Session starter ready. Paste the text above."
Write-Output "--------------------------------------------"
