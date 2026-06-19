import os
import time

from PIL import Image, ImageDraw, ImageFont

from config import FONT_PATH, IMAGE_WIDTH, IMAGE_PADDING

WIDTH = IMAGE_WIDTH
PADDING = IMAGE_PADDING
CONTENT_WIDTH = WIDTH - 2 * PADDING
ACCENT_HEIGHT = 4


def _sanitize_text(text: str) -> str:
    """移除 BMP 外的 emoji 字符及变体选择器，保留中日韩等常用文本"""
    result = []
    for ch in text:
        cp = ord(ch)
        if cp > 0xFFFF:
            continue
        if 0xFE00 <= cp <= 0xFE0F:
            continue
        if cp == 0x200D:
            continue
        result.append(ch)
    return "".join(result)


def _wrap_cjk(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """按字符宽度对中文文本换行"""
    lines = []
    current = ""
    for ch in text:
        if ch == '\n':
            if current:
                lines.append(current)
            current = ""
            continue
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def _measure_line_height(font, draw: ImageDraw.Draw, ratio: float = 1.5) -> int:
    bbox = draw.textbbox((0, 0), "测试Ag", font=font)
    return int((bbox[3] - bbox[1]) * ratio)


def render_news_card(
    data: dict,
    output_path: str,
    accent_color: str = "#3B82F6",
    card_title: str = "每日新闻摘要",
    news_count: int = 0,
) -> str:
    """将结构化新闻数据渲染为 PNG 卡片，返回输出路径"""
    font_title = ImageFont.truetype(FONT_PATH, 28)
    font_section = ImageFont.truetype(FONT_PATH, 20)
    font_body = ImageFont.truetype(FONT_PATH, 16)
    font_small = ImageFont.truetype(FONT_PATH, 14)

    measure_img = Image.new("RGB", (WIDTH, 100))
    measure_draw = ImageDraw.Draw(measure_img)

    card_title = _sanitize_text(card_title)
    overview_text = _sanitize_text(data.get("overview", ""))
    summary_text = _sanitize_text(data.get("summary", ""))
    sections = data.get("sections", [])

    overview_lines = _wrap_cjk(overview_text, font_body, CONTENT_WIDTH, measure_draw)
    summary_lines = _wrap_cjk(summary_text, font_body, CONTENT_WIDTH, measure_draw)

    section_data = []
    for sec in sections:
        name = _sanitize_text(sec.get("name", ""))
        body = _sanitize_text(sec.get("body", ""))
        body_lines = _wrap_cjk(body, font_body, CONTENT_WIDTH - 24, measure_draw)
        section_data.append((name, body_lines))

    ln_body = _measure_line_height(font_body, measure_draw)
    ln_small = _measure_line_height(font_small, measure_draw)
    title_h = font_title.size

    timestamp = time.strftime("%Y-%m-%d %H:%M")
    date_text = timestamp

    # ── height calculation ──
    y = 0
    y += ACCENT_HEIGHT
    y += 30
    y += title_h + 8
    y += font_small.size + 10
    y += 10
    y += 10
    y += len(overview_lines) * ln_body
    y += 15
    for _name, body_lines in section_data:
        y += font_section.size + 8
        y += len(body_lines) * ln_body
        y += 16
    y += 4
    y += 10
    y += len(summary_lines) * ln_body
    y += 10
    y += 10
    y += font_small.size + 15
    y += ACCENT_HEIGHT + 10

    TOTAL_HEIGHT = max(int(y), 400)

    img = Image.new("RGB", (WIDTH, TOTAL_HEIGHT), "#F8F9FA")
    draw = ImageDraw.Draw(img)

    y = 0

    # top accent bar
    draw.rectangle([(0, 0), (WIDTH, ACCENT_HEIGHT)], fill=accent_color)
    y += ACCENT_HEIGHT

    # title
    y += 30
    draw.text((PADDING, y), card_title, font=font_title, fill="#1F2937")
    y += title_h + 8

    # date
    draw.text((PADDING, y), date_text, font=font_small, fill="#9CA3AF")
    y += font_small.size + 10

    # divider
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill="#E5E7EB", width=1)
    y += 10

    # overview
    y += 10
    for line in overview_lines:
        draw.text((PADDING, y), line, font=font_body, fill="#374151")
        y += ln_body
    y += 15

    # sections
    dot_r = 5
    dot_x = PADDING + dot_r
    indent = 24
    for name, body_lines in section_data:
        dot_y = y + font_section.size // 2
        draw.ellipse(
            [(dot_x - dot_r, dot_y - dot_r), (dot_x + dot_r, dot_y + dot_r)],
            fill=accent_color,
        )
        draw.text((PADDING + 16, y), name, font=font_section, fill="#1F2937")
        y += font_section.size + 8
        for line in body_lines:
            draw.text((PADDING + indent, y), line, font=font_body, fill="#4B5563")
            y += ln_body
        y += 16

    # divider
    y += 4
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill="#E5E7EB", width=1)
    y += 10

    # summary
    y += 10
    for line in summary_lines:
        draw.text((PADDING, y), line, font=font_body, fill="#374151")
        y += ln_body
    y += 10

    # divider
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill="#E5E7EB", width=1)
    y += 10

    # footer
    footer_text = f"共 {news_count} 条新闻 | {timestamp}" if news_count > 0 else timestamp
    draw.text((PADDING, y), footer_text, font=font_small, fill="#9CA3AF")
    y += font_small.size + 15

    # bottom accent bar
    draw.rectangle(
        [(0, TOTAL_HEIGHT - ACCENT_HEIGHT), (WIDTH, TOTAL_HEIGHT)],
        fill=accent_color,
    )

    # border
    draw.rectangle([(0, 0), (WIDTH - 1, TOTAL_HEIGHT - 1)], outline="#E5E7EB", width=1)

    img.save(output_path, "PNG", optimize=True)
    return output_path


def render_ai_news_card(
    data: dict,
    output_path: str,
) -> str:
    """将结构化 AI 资讯数据渲染为 PNG 卡片"""
    return render_news_card(
        data=data,
        output_path=output_path,
        accent_color="#10B981",
        card_title="AI 资讯日报",
        news_count=0,
    )


def image_to_cq(image_path: str) -> str:
    """将本地图片转为 OneBot CQ 码 (file://)"""
    abs_path = os.path.abspath(image_path)
    return f"[CQ:image,file=file://{abs_path}]"


def format_news_message(ai_data: dict | None, news_count: int) -> str:
    """生成新闻卡片图片并返回 CQ 码"""
    if ai_data is None:
        return "⚠️ 新闻处理失败，请稍后重试"

    output_path = f"/tmp/newsget_news_{int(time.time())}.png"
    render_news_card(ai_data, output_path, news_count=news_count)
    return image_to_cq(output_path)


def format_ai_news_message(ai_data: dict | None) -> str:
    """生成 AI 资讯卡片图片并返回 CQ 码"""
    if ai_data is None:
        return "⚠️ AI 资讯处理失败，请稍后重试"

    output_path = f"/tmp/newsget_ai_{int(time.time())}.png"
    render_ai_news_card(ai_data, output_path)
    return image_to_cq(output_path)


def save_news_image(ai_data: dict | None, save_path: str, news_count: int = 0) -> str | None:
    """渲染新闻卡片并保存到指定路径（用于 --test 模式）"""
    if ai_data is None:
        return None
    return render_news_card(ai_data, save_path, news_count=news_count)


def save_ai_news_image(ai_data: dict | None, save_path: str) -> str | None:
    """渲染 AI 资讯卡片并保存到指定路径（用于 --test 模式）"""
    if ai_data is None:
        return None
    return render_ai_news_card(ai_data, save_path)


def get_help_message() -> str:
    """获取帮助消息"""
    return """📖 命令帮助

@机器人 新闻 - 手动触发新闻推送
@机器人 help / 帮助 - 显示此帮助"""
