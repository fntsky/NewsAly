import json
import requests

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from news_fetcher import NewsItem, format_news_for_ai


SYSTEM_PROMPT = """你是一个新闻编辑助手。你的任务是将以下多条新闻整理成一份简洁的新闻摘要。

要求：
1. 按主题对新闻进行分类（如：科技、国际、财经、社会等）
2. 每个主题下列出新闻条目，每条附 1-2 句摘要
3. 在摘要末尾保留原文链接 (格式：🔗 短标题)
4. 保持客观中立，不添加个人评论
5. 使用中文输出
6. 整体控制在 3000 字以内"""


def summarize_news(items: list[NewsItem]) -> str | None:
    """调用 OpenAI 兼容 API 对新闻进行 AI 摘要"""
    if not items:
        return "暂无新闻"

    news_text = format_news_for_ai(items)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"以下是今日要闻 ({len(items)} 条)，请整理成新闻摘要：\n\n{news_text}"},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    try:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        print(f"[AI] 正在调用 {OPENAI_MODEL} 处理 {len(items)} 条新闻...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[AI] 摘要生成完成 ({len(content)} 字符)")
        return content
    except Exception as e:
        print(f"[错误] AI 处理失败: {e}")
        return None
