#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKEA 庫存監控（門市＋Telegram）
— 勇成專用 —
功能：
    1. 追蹤多個 IKEA 商品
    2. 只關心五家門市：台北城市店、新莊店、桃園店、新店店、內湖店
    3. 一旦任何門市「有貨」就 Telegram 通知並列出「門市名稱＋庫存顆數」
"""

import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import cloudscraper
from bs4 import BeautifulSoup

# ---------- ❶ 追蹤清單 ----------
PRODUCTS = {
    "80586747": {
        "name": "MOLNART LED 甜甜圈燈泡",
        "url": "https://www.ikea.com.tw/zh/products/light-sources-and-smart-lighting/light-sources/molnart-art-80586747",
    },
    "80583720": {
        "name": "KÄLLARHÄLS 透明花瓶 15 cm",
        "url": "https://www.ikea.com.tw/zh/products/home-decoration/vases-bowls-and-accessories/kallarhals-art-80583720",
    },
    "80581919": {  # 你原本那把轉椅
        "name": "DYVLINGE 旋轉休閒椅，橘色",
        "url": "https://www.ikea.com.tw/zh/products/armchairs-footstool-and-sofa-tables/armchairs/dyvlinge-art-80581919",
    },
}

# ---------- ❷ 只看這五家 ----------
TARGET_STORES = {"台北城市店", "新莊店", "桃園店", "新店店", "內湖店"}

# ---------- ❸ Telegram 憑證 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
TG_API    = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ---------- ❹ HTTP Request 設定 ----------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

scraper = cloudscraper.create_scraper()      # 穿雲破盾神器


# ---------- ❺ 工具函式 ----------
def fetch_html(url: str) -> str:
    """繞過 Cloudflare，把整頁 HTML 抓回來"""
    r = scraper.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def parse_availability(html: str):
    """
    回傳：
        in_stock -> dict {門市: 顯示字串 (含件數)}
        full     -> dict {門市: 顯示字串 (含件數)}  (所有門市，含缺貨)
    """
    soup = BeautifulSoup(html, "html.parser")
    full = {
        d["data-shopname"].strip(): d.get_text(strip=True)
        for d in soup.find_all("div", attrs={"data-shopname": True})
        if d["data-shopname"].strip() in TARGET_STORES
    }
    in_stock = {s: t for s, t in full.items() if "缺貨" not in t}
    return in_stock, full


def send_telegram(text: str) -> None:
    """丟訊息到 Telegram"""
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    scraper.post(TG_API, data=data, timeout=15)   # 用同一支 scraper 發


# ---------- ❻ 主程式 ----------
def main() -> None:
    now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

    for art_no, item in PRODUCTS.items():
        html = fetch_html(item["url"])
        in_stock, full = parse_availability(html)

        if in_stock:
            store_lines = "\n".join(f"• {s}：{full[s]}" for s in in_stock)
            msg = (
                f"🟢 <b>IKEA 有貨</b>\n"
                f"{item['name']}（{art_no}）\n"
                f"{store_lines}\n"
                f"商品頁：{item['url']}\n"
                f"時間：{now}"
            )
            logging.info(msg.replace("<b>", "").replace("</b>", ""))  # log 用
            send_telegram(msg)

    logging.info(f"全部檢查完畢：{now}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
