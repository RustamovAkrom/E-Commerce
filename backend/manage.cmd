@echo off
REM Convenience launcher for the project management CLI (cmd.exe).
REM   manage              -> interactive menu
REM   manage test         -> run the test suite
REM   manage migrate      -> apply migrations
uv run python "%~dp0manage.py" %*
