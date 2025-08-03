# broker_scraper.py

import os
import time
from typing import List, Dict

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

RTI_EMAIL = os.getenv("RTI_EMAIL")
RTI_PASS = os.getenv("RTI_PASS")
CACHE = {}

def fetch_broker_summary(symbol: str, max_rows: int = 5, timeout_secs: int = 15) -> List[Dict]:
    """
    Login ke RTI Investor dan ambil broker summary untuk <symbol>.JK board RG.
    Mengembalikan list broker teratas (aver buy/sell).
    Cache per process runtime untuk menghindari login berkali.
    """
    sym = symbol.upper()
    # Jika sudah pernah diambil, return dari cache
    if sym in CACHE:
        return CACHE[sym]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto("https://rti.co.id/investor", timeout=timeout_secs * 1000)
        page.fill("input[name='email']", RTI_EMAIL)
        page.fill("input[name='password']", RTI_PASS)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle", timeout=timeout_secs * 1000)

        # Setelah login, navigasi ke halaman broker summary
        page.goto(
            f"https://rti.co.id/investor/stock-summary/{sym}?board=RG&brokerScreen=true",
            timeout=timeout_secs * 1000)
        # Tunggu table muncul
        page.wait_for_selector("table.broker-summary tbody tr", timeout=timeout_secs * 1000)

        rows = page.query_selector_all("table.broker-summary tbody tr")
        data = []
        for row in rows[:max_rows]:
            cells = row.query_selector_all("td")
            if len(cells) < 5:
                continue
            brk = cells[1].inner_text().strip()
            try:
                buy = int(cells[2].inner_text().replace(",", "").strip())
                sell = int(cells[3].inner_text().replace(",", "").strip())
                net_sign = 1 if cells[4].inner_text().strip().startswith('+') else -1
                net = abs(int(cells[4].inner_text().replace("+", "").replace("-", "").replace(",", "").strip())) * net_sign
            except Exception:
                continue
            data.append({"broker": brk, "buy_lot": buy, "sell_lot": sell, "net_lot": net})
        ctx.close()
        browser.close()
        CACHE[sym] = data
        return data
