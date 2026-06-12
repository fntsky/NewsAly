import time


def format_news_message(ai_summary: str | None, news_count: int) -> str:
    """将 AI 摘要格式化为 QQ 群消息"""
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    header = f"📰 每日新闻摘要 ({timestamp})\n{'▔' * 20}\n"

    if ai_summary is None:
        body = "⚠️ 新闻处理失败，请稍后重试"
    elif ai_summary == "暂无新闻":
        body = "📭 暂时没有获取到新闻"
    else:
        body = ai_summary

    footer = f"\n{'▔' * 20}\n📊 共 {news_count} 条新闻 | {time.strftime('%H:%M')}"

    text = header + body + footer
    return text


def format_ai_news_message(ai_summary: str | None) -> str:
    """将 AI 资讯摘要格式化为 QQ 群消息"""
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    header = f"🤖 AI 资讯日报 ({timestamp})\n{'▔' * 20}\n"

    if ai_summary is None:
        body = "⚠️ AI 资讯处理失败，请稍后重试"
    elif ai_summary == "暂无 AI 资讯":
        body = "📭 今日暂无 AI 资讯更新"
    else:
        body = ai_summary

    footer = f"\n{'▔' * 20}\n{time.strftime('%H:%M')}"

    return header + body + footer


def get_help_message() -> str:
    """获取帮助消息"""
    return """📖 命令帮助

@机器人 新闻 - 手动触发新闻推送
@机器人 help / 帮助 - 显示此帮助"""
