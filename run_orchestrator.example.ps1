# Copy this file to run_orchestrator.ps1 (gitignored) and fill in your values.
# run_orchestrator.ps1 is NEVER committed — it may contain credentials.

python orchestrator.py `
  -w "C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room" `
  --workflow "jobscrap_v2" `
  --ngrok-auth "YOUR_USER:YOUR_PASSWORD"

# Alternative: source credentials from an env file to avoid any plaintext in scripts:
#   $env:NGROK_AUTH = (Get-Content .env | Select-String "^NGROK_AUTH=").Line.Split("=",2)[1]
#   python orchestrator.py -w "..." --workflow "jobscrap_v2" --ngrok-auth $env:NGROK_AUTH
