@echo off
REM Usage: start_agent.bat [WORKSPACE] [SESSION_NAME] [AGENT_CMD] [STARTUP_WAIT]
REM Windows wrapper — runs start_agent.sh inside WSL2.
REM Requires: WSL2 with tmux installed (sudo apt-get install -y tmux)

set WORKSPACE=%1
if "%WORKSPACE%"=="" set WORKSPACE=./workspace

set SESSION=%2
if "%SESSION%"=="" set SESSION=gemini_agent

set AGENT_CMD=%3
if "%AGENT_CMD%"=="" set AGENT_CMD=gemini

set STARTUP_WAIT=%4
if "%STARTUP_WAIT%"=="" set STARTUP_WAIT=20

wsl bash scripts/start_agent.sh "%WORKSPACE%" "%SESSION%" "%AGENT_CMD%" "%STARTUP_WAIT%"
