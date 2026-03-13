@echo off
REM Usage: stop_agent.bat [SESSION_NAME]

set SESSION=%1
if "%SESSION%"=="" set SESSION=gemini_agent

wsl bash scripts/stop_agent.sh "%SESSION%"
