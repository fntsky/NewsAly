import asyncio
import json
import sys
import threading
import time

import requests
import websockets

from news_fetcher import fetch_news
from ai_processor import summarize_news, summarize_ai_news
from formatter import (
    format_news_message,
    format_ai_news_message,
    save_news_image,
    save_ai_news_image,
    get_help_message,
)
from ai_source_fetcher import fetch_ai_sources
from config import (
    GROUP_ID, API_URL, WS_URL, RSS_URLS,
    PUSH_TIME_HOUR, PUSH_TIME_MINUTE, MAX_NEWS_ITEMS,
)


class OneBotAPI:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def send_group_message(self, group_id: int, message: str) -> bool:
        try:
            response = requests.post(
                f"{self.api_url}/send_group_msg",
                json={"group_id": group_id, "message": message},
                timeout=10
            )
            result = response.json()
            if result.get("status") == "ok":
                print(f"[发送] 消息已发送到群 {group_id}")
                return True
            else:
                print(f"[错误] 发送失败: {result}")
                return False
        except Exception as e:
            print(f"[错误] 发送消息异常: {e}")
            return False

    def get_login_info(self) -> dict | None:
        try:
            response = requests.get(f"{self.api_url}/get_login_info", timeout=10)
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data")
        except Exception as e:
            print(f"[错误] 获取登录信息失败: {e}")
        return None


bot = OneBotAPI(API_URL)
self_qq = None


def push_news(send: bool = True):
    """获取新闻、AI处理、推送"""
    print("[推送] 开始获取新闻...")
    items = fetch_news(RSS_URLS, MAX_NEWS_ITEMS)

    if not items:
        print("[推送] 未获取到新闻，跳过")
        return

    print(f"[推送] 获取到 {len(items)} 条新闻，正在 AI 处理...")
    ai_result = summarize_news(items)
    msg1 = format_news_message(ai_result, len(items))

    if send:
        bot.send_group_message(GROUP_ID, msg1)
    else:
        path = save_news_image(ai_result, "test_news.png", len(items))
        if path:
            print(f"[测试] 新闻卡片已保存到: {path}")
        else:
            print("[测试] 新闻卡片生成失败")

    print("[推送] 开始获取 AI 资讯...")
    ai_raw = fetch_ai_sources()
    if not ai_raw:
        print("[推送] 无 AI 资讯来源，跳过第二条消息")
        print("[推送] 完成")
        return

    ai_result = summarize_ai_news(ai_raw)
    msg2 = format_ai_news_message(ai_result)

    if send:
        bot.send_group_message(GROUP_ID, msg2)
    else:
        path = save_ai_news_image(ai_result, "test_ai_news.png")
        if path:
            print(f"[测试] AI 资讯卡片已保存到: {path}")
        else:
            print("[测试] AI 资讯卡片生成失败")

    print("[推送] 完成")


def handle_event(data: dict):
    global self_qq

    post_type = data.get("post_type")

    if post_type == "meta_event" and data.get("meta_event_type") == "lifecycle":
        if data.get("sub_type") == "connect":
            self_qq = data.get("self_id")
            print(f"[连接] WebSocket 已连接，机器人QQ: {self_qq}")

    if post_type == "message" and data.get("message_type") == "group":
        handle_group_message(data)


def handle_group_message(data: dict):
    global self_qq

    group_id = data.get("group_id")
    user_id = data.get("user_id")
    message = data.get("message", "")

    if group_id != GROUP_ID:
        return

    is_at_bot = False
    text_content = ""

    if isinstance(message, list):
        for msg in message:
            if msg.get("type") == "at":
                qq = msg.get("data", {}).get("qq")
                if qq == str(self_qq):
                    is_at_bot = True
            elif msg.get("type") == "text":
                text_content += msg.get("data", {}).get("text", "")
    elif isinstance(message, str):
        text_content = message

    text_content = text_content.strip()

    if is_at_bot and ("help" in text_content.lower() or "帮助" in text_content):
        print(f"[消息] 用户 {user_id} 在群 {group_id} 查询帮助")
        text = get_help_message()
        bot.send_group_message(group_id, text)

    if is_at_bot and "新闻" in text_content:
        print(f"[消息] 用户 {user_id} 在群 {group_id} 触发新闻指令")
        push_news()


def check_and_push():
    """定时检查并推送"""
    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min

    if hour == PUSH_TIME_HOUR and minute == PUSH_TIME_MINUTE:
        print(f"[定时] 到达推送时间 {PUSH_TIME_HOUR}:{PUSH_TIME_MINUTE:02d}")
        push_news()


async def websocket_client():
    print(f"[连接] 正在连接 WebSocket: {WS_URL}")

    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                print("[连接] WebSocket 连接成功")

                async for message in ws:
                    try:
                        data = json.loads(message)
                        handle_event(data)
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"[错误] WebSocket 连接失败: {e}")
            print("[重试] 5秒后重连...")
            await asyncio.sleep(5)


def run_websocket():
    asyncio.run(websocket_client())


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[测试模式] 执行一次完整流程，不发送 QQ 消息")
        print(f"[配置] 推送时间: 每日 {PUSH_TIME_HOUR}:{PUSH_TIME_MINUTE:02d}")
        push_news(send=False)
        return

    print(f"[配置] 目标群: {GROUP_ID}")
    print(f"[配置] API地址: {API_URL}")
    print(f"[配置] WebSocket: {WS_URL}")
    for i, url in enumerate(RSS_URLS, 1):
        print(f"[配置] RSS源{i}: {url}")
    print(f"[配置] 推送时间: 每日 {PUSH_TIME_HOUR}:{PUSH_TIME_MINUTE:02d}")
    print(f"[配置] 最大新闻数: {MAX_NEWS_ITEMS}")

    login_info = bot.get_login_info()
    if login_info:
        print(f"[连接] 已连接，机器人QQ: {login_info.get('user_id')}, 昵称: {login_info.get('nickname')}")
    else:
        print("[警告] 无法连接到 NapCat API，请确认 NapCat 已启动")

    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    print("[运行] 开始定时检查...")
    while True:
        time.sleep(60)
        check_and_push()


if __name__ == "__main__":
    main()
