import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"
CONFIG_EXAMPLE = {
    "group_id": 123456789,
    "api_port": 3000,
    "rss_urls": ["https://news.google.com/rss", "https://plink.anyfeeder.com/zaobao/realtime/china"],
    "openai_api_key": "sk-your-key-here",
    "openai_base_url": "https://api.deepseek.com",
    "openai_model": "deepseek-chat",
    "push_time_hour": 22,
    "push_time_minute": 0,
    "max_news_items": 50,
}

if not CONFIG_FILE.exists():
    print(f"[错误] 配置文件不存在: {CONFIG_FILE}")
    print(f"[提示] 请复制 config.example.json 为 config.json 并修改配置")
    exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

GROUP_ID = config["group_id"]
API_PORT = config.get("api_port", 3000)
API_URL = f"http://127.0.0.1:{API_PORT}"
WS_URL = f"ws://127.0.0.1:{API_PORT}"
RSS_URLS = config.get("rss_urls", [config.get("rss_url", CONFIG_EXAMPLE["rss_url"])])
OPENAI_API_KEY = config["openai_api_key"]
OPENAI_BASE_URL = config.get("openai_base_url", CONFIG_EXAMPLE["openai_base_url"])
OPENAI_MODEL = config.get("openai_model", CONFIG_EXAMPLE["openai_model"])
PUSH_TIME_HOUR = config.get("push_time_hour", 12)
PUSH_TIME_MINUTE = config.get("push_time_minute", 0)
MAX_NEWS_ITEMS = config.get("max_news_items", 50)

IMAGE_WIDTH = 800
IMAGE_PADDING = 40
_default_font = str(Path(__file__).parent / "fonts" / "NotoSansCJKsc-Regular.otf")
if not Path(_default_font).exists():
    _fallback = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
    if Path(_fallback).exists():
        _default_font = _fallback
FONT_PATH = config.get("font_path", _default_font)
