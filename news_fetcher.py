import feedparser
from dataclasses import dataclass, field


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    pub_date: str
    source: str = ""


def fetch_news(rss_url: str, max_items: int = 50) -> list[NewsItem]:
    """从 Google News RSS 抓取新闻"""
    feed = feedparser.parse(rss_url)

    if feed.bozo and not feed.entries:
        print(f"[错误] RSS 解析失败: {feed.bozo_exception}")
        return []

    items: list[NewsItem] = []
    for entry in feed.entries[:max_items]:
        source = ""
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source = entry.source.title

        items.append(NewsItem(
            title=entry.get("title", ""),
            link=entry.get("link", ""),
            summary=entry.get("summary", ""),
            pub_date=entry.get("published", ""),
            source=source,
        ))

    print(f"[抓取] 从 RSS 获取到 {len(items)} 条新闻")
    return items


def format_news_for_ai(items: list[NewsItem]) -> str:
    """将新闻列表格式化为 AI 可处理的文本"""
    lines = []
    for i, item in enumerate(items, 1):
        source_tag = f" [{item.source}]" if item.source else ""
        lines.append(f"{i}. {item.title}{source_tag}")
        lines.append(f"   简介: {item.summary[:200]}")
        lines.append(f"   链接: {item.link}")
        lines.append("")
    return "\n".join(lines)
