import subprocess
import time

print("Starting AI Security OpenEnv...")

subprocess.run(["python", "inference.py"])

# keep container alive

while True:
    time.sleep(60)