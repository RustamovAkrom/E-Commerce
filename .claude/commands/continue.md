# Continue E-Commerce Build

## Step 1 — Orient (read only, do NOT scan filesystem)
Read CLAUDE.md → check "PROJECT STATUS" section for CURRENT task.
Read PROJECT_SNAPSHOT.md → know what files exist already.
DO NOT run `find` or `ls` — the snapshot already has this.

## Step 2 — Verify current task state
Read the IN PROGRESS module files to understand what's done.
Identify exactly which files are missing.

## Step 3 — Build
Generate missing files. Complete working code only.
No placeholders. No `# TODO`. No `pass` in logic methods.

## Step 4 — Verify import
After completing backend work always run:
`uv run python -c "from src.main import app; print('OK')"`
Fix any import errors before moving to next task.

## Step 5 — Update CLAUDE.md
Move completed module from CURRENT to DONE in the PROJECT STATUS section.
Set next module as CURRENT.
