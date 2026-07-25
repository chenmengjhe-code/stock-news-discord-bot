"""Create a Traditional-Chinese daily market briefing and post it to Discord."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable

import feedparser
import requests
import yfinance as yf
from dotenv import load_dotenv
from google import genai


INDEXES = {
    "道瓊工業指數": "^DJI",
    "S&P 500": "^GSPC",
    "NASDAQ 綜合指數": "^IXIC",
    "台股加權指數": "^TWII",
}

NEWS_FEEDS = {
    "全球市場": "https://news.google.com/rss/search?q=global+stock+markets+when:2d&hl=en-US&gl=US&ceid=US:en",
    "美股": "https://news.google.com/rss/search?q=US+stocks+earnings+Federal+Reserve+when:2d&hl=en-US&gl=US&ceid=US:en",
    "台股": "https://news.google.com/rss/search?q=Taiwan+stocks+TSMC+when:2d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "行事曆": "https://news.google.com/rss/search?q=US+economic+calendar+earnings+this+week+when:3d&hl=en-US&gl=US&ceid=US:en",
}


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少環境變數：{name}")
    return value


def market_snapshot() -> tuple[str, list[str]]:
    lines: list[str] = []
    source_dates: list[str] = []
    for label, symbol in INDEXES.items():
        history = yf.Ticker(symbol).history(period="10d", auto_adjust=False)
        closes = history["Close"].dropna()
        if len(closes) < 2:
            lines.append(f"• {label}：資料暫時無法取得")
            continue
        latest, previous = float(closes.iloc[-1]), float(closes.iloc[-2])
        change = (latest / previous - 1) * 100
        sign = "+" if change >= 0 else ""
        lines.append(f"• {label}：{sign}{change:.2f}%（收盤 {latest:,.2f}）")
        source_dates.append(str(closes.index[-1].date()))
    return "\n".join(lines), sorted(set(source_dates))


def headlines(limit: int = 6) -> str:
    blocks: list[str] = []
    for category, url in NEWS_FEEDS.items():
        feed = feedparser.parse(url)
        entries = feed.entries[:limit]
        if not entries:
            continue
        rows = [f"- {entry.title}" for entry in entries if getattr(entry, "title", None)]
        blocks.append(f"【{category}】\n" + "\n".join(rows))
    return "\n\n".join(blocks)


def create_briefing(index_text: str, dates: Iterable[str], news: str) -> str:
    today = datetime.now().strftime("%Y/%m/%d")
    prompt = f"""你是嚴謹的台灣市場晨報編輯。請只依據下列提供的指數資料與新聞標題，以繁體中文寫一則可直接貼到 Discord 的市場摘要。

規則：
1. 第一行必須是「📈 股市晨報｜{today}」。接著使用「📊 指數」並原樣列出所有指數資料。
2. 接著固定使用三個小節：🌍 國際市場、🇺🇸 美股、🇹🇼 台股。
3. 每節 2–3 個短條列，說明最重要的事件、可能影響或市場焦點；每點最多 60 個中文字。
4. 僅根據提供資料撰寫。資料不足時略過，不得杜撰數字、日期或新聞事實。
5. 以中性語氣呈現，不能提供買賣建議，也不要提及你是 AI 或資料來源。
6. 全文請控制在 1,300 個中文字元內；內容已簡短時不要為了湊格式而補充。

指數收盤日期：{", ".join(dates) or "未知"}

📊 指數表現
{index_text}

新聞標題：
{news}
"""
    client = genai.Client(api_key=required("GEMINI_API_KEY"))
    response = client.interactions.create(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        input=prompt,
    )
    return response.output_text.strip()


def post_discord(content: str) -> None:
    webhook = required("DISCORD_WEBHOOK_URL")
    # Discord accepts at most 2,000 characters per message.
    for start in range(0, len(content), 1900):
        response = requests.post(webhook, json={"content": content[start : start + 1900]}, timeout=30)
        response.raise_for_status()


def main() -> None:
    # For local runs, use the credentials in this project's .env file even if
    # an older value remains in the PowerShell session.
    load_dotenv(override=True)
    index_text, dates = market_snapshot()
    news = headlines()
    if not news:
        news = "新聞標題暫時無法取得；請以官方公告為準。"
    briefing = create_briefing(index_text, dates, news)
    post_discord(briefing)
    print("已成功發送 Discord 市場摘要。")


if __name__ == "__main__":
    main()
