@echo off
REM Usage: scripts\start.bat [1|2]
REM Windows wrapper — runs start.sh inside WSL2.
REM Reads configure_user.json for ngrok, workspace, workflow, port settings.

set AGENT_NUM=%1
if "%AGENT_NUM%"=="" set AGENT_NUM=1

wsl bash scripts/start.sh %AGENT_NUM%
