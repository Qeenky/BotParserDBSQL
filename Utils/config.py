User = ""
Password = ""
Host = ""
DataBase = ""
Port = ""
ConnectSring = f"postgresql://{User}:{Password}@{Host}:{Port}/{DataBase}"
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TXT_FILES_DIR = PROJECT_ROOT / 'Scripts' / 'TxtFilesSrc'