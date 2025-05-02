#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKEA 庫存監控（Telegram 通知版）
— 勇成專用／無外部依賴 —
"""

import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ 標準庫，取代 pytz

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
    "60468813": {
        "name": "DYVLINGE 旋轉休閒椅, kelinge 橘色",
        "url": "https://www.ikea.com.tw/zh/products/armchairs-footstool-and-sofa-tables/armchairs/dyvlinge-art-80581919",
    },
}

# ---------- ❷ Telegram 憑證 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
TG_API    = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ---------- ❸ 工具函式 ----------
def is_available(url: str) -> bool:
    html = requests.get(url, timeout=10).text
    return "缺貨 線上購物" not in html

def send_telegram(text: str) -> None:
    requests.post(TG_API, json={"chat_id": CHAT_ID, "text": text})

# ---------- ❹ 主程式 ----------
def main() -> None:
    now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

    for art_no, item in PRODUCTS.items():
        if is_available(item["url"]):
            msg = f"⚡IKEA 有貨\n{item['name']}（{art_no}）\n{item['url']}\n時間：{now}"
            print(msg)
            send_telegram(msg)

    print(f"全部檢查完畢：{now}")

if __name__ == "__main__":
    main()
