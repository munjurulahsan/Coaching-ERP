import os
import subprocess
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
requirements_path = os.path.join(BASE_DIR, "requirements.txt")

subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-r", requirements_path]
)
