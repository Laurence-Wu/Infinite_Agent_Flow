import subprocess
import os
import signal
import time

proc = subprocess.Popen(['python', 'orchestrator.py', '-w', 'workspace/', '--workflow', 'jobscrap_v2', '--version', 'v1'])
time.sleep(10)
print("Sending SIGINT to orchestrator...")
proc.send_signal(signal.SIGINT)
proc.wait()
print("Orchestrator exited.")
