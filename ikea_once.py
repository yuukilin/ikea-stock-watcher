#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKEA 庫存監控（多商品單次版，Cloudflare OK）
------------------------------------------------
* 支援多商品：80581919、80586747、80583720
* 每執行一次就檢查三品是否到貨，若任一門市有貨立即 Telegram 通知
* 交由 GitHub Actions 的 cron 來定時呼叫

環境變數：
    BOT_TOKEN — Telegram Bot Token
    CHAT_ID   — 接收聊天 ID
"""

import os
import re
import logging
import cloudscraper
from bs4 import BeautifulSoup

# --------------------------- 追蹤清單 ---------------------------
PRODUCTS = {
    "80581919": {
        "name": "DYVLINGE 旋轉休閒椅 (kelinge 橘色)",
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

# --------------------------- 抓取網頁 ---------------------------

def fetch_html(url: str) -> str:
    """用 Cloudflare Scraper 穿雲破盾，避免 403。"""
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

# --------------------------- 解析庫存 ---------------------------

def _extract_store_from_div(div):
    """IKEA 網頁有時用 data-shopname，有時用 data-shop_name。"""
    if div.has_attr("data-shopname"):
        return div["data-shopname"].strip()
    if div.has_attr("data-shop_name"):
        return div["data-shop_name"].strip()
    return None


def parse_availability(html: str):
    """回傳 qty 與 raw 兩個 dict。

    qty: {店名: 數量 (int) | -1 (有貨但沒寫數字) | 0 (缺貨)}
    raw: {店名: 原始文字}
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ 先嘗試從 data-* 屬性抓
    raw = {}
    for div in soup.find_all("div"):
        store = _extract_store_from_div(div)
        if store and store in TARGET_STORES:
            raw[store] = div.get_text(" ", strip=True)

    # 2️⃣ 補漏：如果改版導致缺資料，改用 regex 掃描整頁文字
    html_text = soup.get_text(" ", strip=True)
    for store in TARGET_STORES:
        if store in raw:  # 已抓到就跳過
            continue
        # 有庫存 + 數量
        m = re.search(rf"有庫存於\s*{store}\s*[\u4e00-\u9fffA-Za-z0-9 ]*?(\d+) 件庫存", html_text)
        if m:
            raw[store] = f"有庫存 {m.group(1)} 件庫存"
            continue
        # 有庫存但沒顯示數量
        if re.search(rf"有庫存於\s*{store}", html_text):
            raw[store] = "有庫存 (數量未知)"
            continue
        # 最後判定為缺貨
        raw[store] = "缺貨"

    # 3️⃣ 統一轉成 qty 數字
    qty = {}
    for store, txt in raw.items():
        if "缺貨" in txt:
            qty[store] = 0
        else:
            m = re.search(r"(\d+)", txt)
            qty[store] = int(m.group(1)) if m else -1
    return qty, raw

# --------------------------- 發送通知 ---------------------------

def notify(message: str):
    import requests

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

# --------------------------- 主流程 ---------------------------

def main():
    for pid, info in PRODUCTS.items():
        html = fetch_html(info["url"])
        qty, raw = parse_availability(html)
        avail = {s: q for s, q in qty.items() if q != 0}

        if avail:
            lines = [
                f"• {store}：{'有貨 (數量未知)' if q == -1 else f'{q} 件'}"
                for store, q in avail.items()
            ]
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
