import json
import requests

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from news_fetcher import NewsItem, format_news_for_ai


SYSTEM_PROMPT = """你是一个新闻编辑，任务是将以下新闻整理成一份有价值的摘要。

要求：
1. 先用 2-3 句概括今日新闻趋势/重点
2. 按主题分组（如 🌍 国际 💻 科技 📈 财经 🏛 政治 ⚽ 体育），每组选最重要的 2-3 条，其余放入简讯区
3. 每条新闻格式：• 一句话摘要 🔗 链接
4. 简讯区用一行列出其余新闻标题，用 | 分隔
5. 最后用 2-3 句做总结
6. 严禁使用任何 Markdown 符号（**、#、-、` 等），纯文本
7. 用 emoji 做视觉分隔
8. 每条新闻描述控制在 60 字以内
9. 保持客观中立，不添加个人评论
10. 使用中文输出
11. 总长度控制在 4000 字以内"""


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
