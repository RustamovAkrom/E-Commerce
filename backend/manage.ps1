#!/usr/bin/env pwsh
# Convenience launcher for the project management CLI.
#
#   .\manage.ps1            -> interactive menu
#   .\manage.ps1 test       -> run the test suite
#   .\manage.ps1 migrate    -> apply migrations
#
# Thin wrapper around `uv run python manage.py` so you never type the long form.
uv run python "$PSScriptRoot/manage.py" @args
