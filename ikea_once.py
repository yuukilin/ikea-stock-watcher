#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKEA 庫存監控（多商品單次版，Cloudflare OK）
功能：
    1. 支援多商品：80581919、80586747、80583720
    2. 每執行一次就檢查三品是否到貨，若任一店點有貨則立刻 Telegram 通知
    3. 交由 GitHub Actions cron 定時呼叫

環境變數：
    BOT_TOKEN — Telegram Bot Token
    CHAT_ID   — 接收聊天 ID
"""

import os
import re
import logging
import cloudscraper
from bs4 import BeautifulSoup

# -------------- 追蹤清單 --------------
PRODUCTS = {
    "80581919": {
        "name": "DYVLINGE 旋轉休閒椅, kelinge 橘色",
        "url": "https://www.ikea.com.tw/zh/products/armchairs-footstool-and-sofa-tables/armchairs/dyvlinge-art-80581919",
    },
    "80586747": {
        "name": "MOLNART LED 甜甜圈燈泡",
        "url": "https://www.ikea.com.tw/zh/products/light-sources-and-smart-lighting/light-sources/molnart-art-80586747",
    },
    "80583720": {
        "name": "KÄLLARHÄLS 透明花瓶 15 cm",
        "url": "https://www.ikea.com.tw/zh/products/home-decoration/vases-bowls-and-accessories/kallarhals-art-80583720",
    },
}

TARGET_STORES = {"桃園店", "新莊店", "新店店", "內湖店", "台北城市店"}

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/123.0"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def fetch_html(url: str) -> str:
    """用 cloudscraper 穿雲破盾，避免 403"""
    scraper = cloudscraper.create_scraper()
    r = scraper.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def parse_availability(html: str):
    """回傳兩個 dict：qty 與 raw_status。
    qty: {店名: 數量(int) | -1(有貨但抓不到數字) | 0(缺貨)}
    raw_status: {店名: 原始文字}
    """
    soup = BeautifulSoup(html, "html.parser")
    raw_status = {
        div["data-shopname"].strip(): div.get_text(strip=True)
        for div in soup.find_all("div", attrs={"data-shopname": True})
        if div["data-shopname"].strip() in TARGET_STORES
    }

    qty = {}
    for store, txt in raw_status.items():
        if "缺貨" in txt:
            qty[store] = 0
        else:
            m = re.search(r"(\d+)", txt)
            qty[store] = int(m.group(1)) if m else -1  # -1 = 有貨但無數字
    return qty, raw_status


def notify(msg: str):
    import requests

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=10,
    )


def main():
    for pid, info in PRODUCTS.items():
        html = fetch_html(info["url"])
        qty, raw = parse_availability(html)
        avail = {s: q for s, q in qty.items() if q != 0}
        if avail:
            lines = []
            for store, q in avail.items():
                if q == -1:
                    lines.append(f"• {store}：有貨 (數量未知)")
                else:
                    lines.append(f"• {store}：{q} 件")
            detail = "\n".join(lines)
            notify(
                f"🟢 <b>{info['name']}（{pid}）</b>\n{detail}\n<a href='{info['url']}'>商品頁面</a>"
            )
            logging.info("%s 有貨！已通知：%s", pid, detail.replace("\n", " | "))
        else:
            logging.info("%s 全缺貨。", pid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
