import json
import requests

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from news_fetcher import NewsItem, format_news_for_ai


SYSTEM_PROMPT = """你是一个新闻编辑，任务是将以下新闻整理成一份精炼的总结。

要求：
1. 先用 2-3 句概括今日新闻整体趋势和重点
2. 按主题（如国际、科技、财经、政治、体育）用连贯的段落总结核心内容，不要列条目
3. 最后用 2-3 句做总结
4. 严禁使用任何 Markdown 符号（**、#、-、` 等），纯文本
5. 用 emoji 做视觉分隔
6. 保持客观中立，不添加个人评论
7. 使用中文输出
8. 总长度控制在 3000 字以内"""


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


AI_SYSTEM_PROMPT = """你是一个AI科技资讯编辑，任务是将以下素材整理成一份精炼的AI行业日报。

要求：
1. 先用 2-3 句概括今日AI领域整体动态趋势
2. 按主题（如模型发布、工具更新、行业动态、企业新闻、研究进展）用连贯的段落总结核心内容，不要列条目
3. 最后用 2-3 句做总结和展望
4. 严禁使用任何 Markdown 符号（**、#、-、` 等），纯文本
5. 用 emoji 做视觉分隔
6. 保持客观中立，不添加个人评论
7. 使用中文输出
8. 总长度控制在 3000 字以内"""


def summarize_ai_news(content: str) -> str | None:
    if not content:
        return "暂无 AI 资讯"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user",
             "content": f"以下是今日 AI 领域资讯素材，请整理成 AI 行业日报：\n\n{content}"},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    try:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        print(f"[AI资讯] 正在调用 {OPENAI_MODEL} 处理 AI 资讯...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[AI资讯] 摘要生成完成 ({len(content)} 字符)")
        return content
    except Exception as e:
        print(f"[错误] AI 资讯处理失败: {e}")
        return None
