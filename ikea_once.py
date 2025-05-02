#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKEA 庫存監控（台灣站）
執行一次就檢查所有產品，有貨就寄信 / 傳訊息通知
作者：勇成（原始碼 by you）＋毒舌改良版
"""

import os
import re
import smtplib
import requests
from datetime import datetime
from email.message import EmailMessage
from bs4 import BeautifulSoup
import pytz

# ----------- 你要追蹤的商品清單 -----------
PRODUCTS = {
    # ★ 新加的兩個
    "80586747": {
        "name": "MOLNART LED 甜甜圈燈泡",
        "url": "https://www.ikea.com.tw/zh/products/light-sources-and-smart-lighting/light-sources/molnart-art-80586747",
    },
    "80583720": {
        "name": "KÄLLARHÄLS 透明花瓶 15 cm",
        "url": "https://www.ikea.com.tw/zh/products/home-decoration/vases-bowls-and-accessories/kallarhals-art-80583720",
    },

    # ↓ 下面留著你原本就追蹤的舊貨，照抄就好
    # "60468813": {"name": "VÅRDANDE 亞加力盒", "url": "..."},
}

# ----------- 通知設定（用環境變數裝私密資料）-----------
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
MAIL_TO   = os.environ["MAIL_TO"]      # 逗號分隔可多人

# ----------- 兩個小工具函式 -----------
def is_available(url: str) -> bool:
    """
    粗暴判斷「線上購物」是不是還在顯示『缺貨』。
    有貨→傳 True，缺貨→False
    IKEA 網頁用詞固定，直接關鍵字最省事。
    """
    html = requests.get(url, timeout=10).text
    return "缺貨 線上購物" not in html   # 網站範例見 :contentReference[oaicite:0]{index=0}


def send_mail(subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"]   = MAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)


# ----------- 主程式 -----------
def main() -> None:
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    for art_no, item in PRODUCTS.items():
        if is_available(item["url"]):
            subject = f"⚡IKEA 有貨：{item['name']}"
            body    = f"{item['name']}（編號 {art_no}）現在有貨！\n{item['url']}\n時間：{now}"
            print(body)            # log 給 GitHub Actions 看
            send_mail(subject, body)

    print(f"全部檢查完畢：{now}")


if __name__ == "__main__":
    main()
