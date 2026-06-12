import re
import time

import requests


BILIBILI_UID = 285286947
WECHAT_URL = "https://mp.weixin.qq.com/s/YjM_o9OGoJzjhbQ6wMvCYQ"

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def _is_today(timestamp: int) -> bool:
    today = time.localtime()
    t = time.localtime(timestamp)
    return (t.tm_year == today.tm_year
            and t.tm_mon == today.tm_mon
            and t.tm_mday == today.tm_mday)


def fetch_bilibili_today(uid: int = BILIBILI_UID) -> str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": MOBILE_UA,
        "Referer": "https://m.bilibili.com/",
    })
    try:
        resp = session.get(
            f"https://api.bilibili.com/x/space/arc/search?mid={uid}&ps=30",
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            vlist = data["data"]["list"]["vlist"]
            today_videos = [v for v in vlist if _is_today(v["created"])]
            if today_videos:
                lines = []
                for v in today_videos:
                    lines.append(f"【{v['title']}】")
                    if v.get("description"):
                        lines.append(v["description"])
                    lines.append(f"https://www.bilibili.com/video/{v['bvid']}")
                    lines.append("---")
                result = "\n".join(lines)
                print(f"[B站] 获取到 {len(today_videos)} 个今日视频")
                return result
            return "今日无更新视频"
    except Exception as e:
        print(f"[B站] 请求失败: {e}")

    return ""


def fetch_wechat_article(url: str = WECHAT_URL) -> str:
    WEIXIN_UA = (
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    headers = {
        "User-Agent": WEIXIN_UA,
        "Referer": "https://mp.weixin.qq.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        html = resp.text

        match = re.search(
            r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL
        )
        if match:
            content = match.group(1)
            content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
            content = re.sub(r"<br\s*/?>", "\n", content)
            content = re.sub(r"</p>", "\n", content)
            content = re.sub(r"<p[^>]*>", "", content)
            content = re.sub(r"<[^>]+>", "", content)
            content = re.sub(r"&nbsp;", " ", content)
            content = re.sub(r"&lt;", "<", content)
            content = re.sub(r"&gt;", ">", content)
            content = re.sub(r"&amp;", "&", content)
            content = re.sub(r"&quot;", '"', content)
            content = re.sub(r"\n{3,}", "\n\n", content).strip()
            if content:
                print(f"[公众号] 成功提取文章 ({len(content)} 字符)")
                return content[:3000]

        match = re.search(
            r'class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script',
            html,
            re.DOTALL,
        )
        if match:
            content = match.group(1)
            content = re.sub(r"<[^>]+>", "", content)
            content = re.sub(r"\n{3,}", "\n\n", content).strip()
            if content:
                return content[:3000]

        return ""
    except Exception as e:
        print(f"[公众号] 请求失败: {e}")
        return ""


def fetch_ai_sources() -> str:
    """获取所有 AI 资讯源，合并为一段文本"""
    parts = []
    print("[AI资讯] 正在获取 B站 UP主今日视频简介...")
    bili_text = fetch_bilibili_today()
    if bili_text and "无更新" not in bili_text:
        parts.append("【B站 UP主今日视频】\n" + bili_text)
    else:
        print(f"[AI资讯] B站: {bili_text}")

    print("[AI资讯] 正在获取微信公众号文章...")
    wx_text = fetch_wechat_article()
    if wx_text:
        parts.append("【微信公众号文章】\n" + wx_text)
    else:
        print("[AI资讯] 公众号: 无内容")

    return "\n\n==========\n\n".join(parts)
