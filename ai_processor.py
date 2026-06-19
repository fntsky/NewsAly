import json
import re

import requests

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from news_fetcher import NewsItem, format_news_for_ai


SYSTEM_PROMPT = """你是一个新闻编辑，任务是将以下新闻整理成一份精炼的总结。

请严格按照以下JSON格式输出（必须是合法的JSON，不要添加任何额外说明）：

{
  "overview": "用2-3句概括今日新闻整体趋势和重点",
  "sections": [
    {"name": "国际", "body": "按主题总结核心内容，用连贯的段落"},
    {"name": "科技", "body": "..."},
    {"name": "财经", "body": "..."}
  ],
  "summary": "用2-3句做总结"
}

要求：
1. 只输出纯JSON对象，不要用Markdown代码块包裹
2. 保持客观中立，不添加个人评论
3. 使用中文输出，总长度控制在3000字以内
4. sections数量2-5个，按实际内容灵活调整主题
5. 如果某主题无内容，可去掉对应section"""


def extract_json(text: str) -> dict | None:
    """从 AI 响应中提取 JSON 对象"""
    if not text:
        return None
    text = text.strip()

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    start = text.find('{')
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except (json.JSONDecodeError, ValueError):
                        break
    return None


def summarize_news(items: list[NewsItem]) -> dict | None:
    """调用 OpenAI 兼容 API 对新闻进行 AI 摘要，返回结构化 JSON"""
    if not items:
        return None

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
        "response_format": {"type": "json_object"},
    }

    try:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        print(f"[AI] 正在调用 {OPENAI_MODEL} 处理 {len(items)} 条新闻...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[AI] 摘要生成完成 ({len(content)} 字符)")

        parsed = extract_json(content)
        if parsed:
            return parsed
        print("[警告] AI 返回非标准 JSON，使用原始文本作为 fallback")
        return {"overview": "", "sections": [{"name": "新闻", "body": content}], "summary": ""}
    except Exception as e:
        print(f"[错误] AI 处理失败: {e}")
        return None


AI_SYSTEM_PROMPT = """你是一个AI科技资讯编辑，任务是将以下素材整理成一份精炼的AI行业日报。

请严格按照以下JSON格式输出（必须是合法的JSON，不要添加任何额外说明）：

{
  "overview": "用2-3句概括今日AI领域整体动态趋势",
  "sections": [
    {"name": "模型发布", "body": "新模型、新架构的发布与开源动态"},
    {"name": "模型动态", "body": "已有模型的更新、迭代、能力升级、版本变化等"},
    {"name": "行业动态", "body": "企业投融资、政策监管、商业化落地、合作并购等行业事件"}
  ],
  "summary": "用2-3句做总结和展望"
}

要求：
1. 只输出纯JSON对象，不要用Markdown代码块包裹
2. 保持客观中立，不添加个人评论
3. 使用中文输出，总长度控制在3000字以内
4. 严格按照上述三个section分类：模型发布、模型动态、行业动态，无相关内容可省略该section"""


def summarize_ai_news(content: str) -> dict | None:
    if not content:
        return None

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
        "response_format": {"type": "json_object"},
    }

    try:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        print(f"[AI资讯] 正在调用 {OPENAI_MODEL} 处理 AI 资讯...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"[AI资讯] 摘要生成完成 ({len(content)} 字符)")

        parsed = extract_json(content)
        if parsed:
            return parsed
        print("[警告] AI 返回非标准 JSON，使用原始文本作为 fallback")
        return {"overview": "", "sections": [{"name": "AI资讯", "body": content}], "summary": ""}
    except Exception as e:
        print(f"[错误] AI 资讯处理失败: {e}")
        return None
