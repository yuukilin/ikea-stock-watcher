#!/usr/bin/env python3
"""
IKEA 80581919 庫存監控（單次版）
只負責：抓一次 → 有貨就丟 Telegram → 結束
交由 GitHub Actions 的 cron 來定時呼叫
IKEA 80581919 庫存監控（單次版，Cloudflare OK）
"""
import os, requests, logging
import os, logging, cloudscraper
from bs4 import BeautifulSoup

PRODUCT_URL = (
@@ -13,40 +11,44 @@
)
TARGET_STORES = {"桃園店", "新莊店", "新店店", "內湖店", "台北城市店"}

BOT_TOKEN = os.environ["BOT_TOKEN"]   # 由 GitHub Secrets 提供
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]

HEADERS = {"User-Agent": "Mozilla/5.0"}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=15)
    """用 cloudscraper 穿雲破盾，避免 403"""
    scraper = cloudscraper.create_scraper()
    r = scraper.get(url, headers=HEADERS, timeout=20)
r.raise_for_status()
return r.text

def parse_availability(html: str):
soup = BeautifulSoup(html, "html.parser")
    status = {}
    for div in soup.find_all("div", attrs={"data-shopname": True}):
        name = div["data-shopname"].strip()
        if name not in TARGET_STORES:
            continue
        status[name] = div.get_text(strip=True)
    status = {
        d["data-shopname"].strip(): d.get_text(strip=True)
        for d in soup.find_all("div", attrs={"data-shopname": True})
        if d["data-shopname"].strip() in TARGET_STORES
    }
in_stock = [s for s, t in status.items() if "缺貨" not in t]
return in_stock, status

def notify_telegram(msg: str):
def notify(msg: str):
    import requests
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
        timeout=10,
    )
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)

def main():
avail, full = parse_availability(fetch_html(PRODUCT_URL))
if avail:
detail = "\n".join(f"• {s}：{full[s]}" for s in avail)
        notify_telegram(f"🟢 IKEA 庫存警報\n{detail}\n商品頁：{PRODUCT_URL}")
        notify(f"🟢 IKEA 庫存警報\n{detail}\n商品頁：{PRODUCT_URL}")

if __name__ == "__main__":
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
