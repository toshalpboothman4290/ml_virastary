import subprocess
import sys

if __name__ == "__main__":
    # اجرای main.py به صورت ماژول از روت پروژه
    subprocess.run([sys.executable, "-m", "bot.main"])
