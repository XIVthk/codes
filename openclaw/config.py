# config.py
import os

# API 配置
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("请设置环境变量 API_KEY")

BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"

# 应用配置
DEBUG = True
SECRET_KEY = "your-secret-key-here"

# 文件路径
BOTS_FILE = "bots.json"
CHATS_DIR = "data/chats"
MEMORIES_DIR = "data/memories"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR = os.path.join(BASE_DIR, "data/chats")
BOTS_FILE = os.path.join(BASE_DIR, "bots.json")
MEMORIES_DIR = os.path.join(BASE_DIR, "data/memories")
API_KEY = os.environ.get("API_KEY")
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "deepseek-ai/DeepSeek-V3"