# analytics.py

import os
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from broker_scraper import fetch_broker_summary

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_RATIO_THRESHOLD = float(os.getenv("VOLUME_SPIKE", default="1.5"))
BROKER_NET_THRESHOLD = int(os.getenv("BROKER_NET_THRESHOLD", default="100000"))

def analyze_stock(symbol: str) -> (dict, str):
    """
    Ambil data teknikal & broker summary lalu tentukan rekomendasi.
    Returns: summary (dict), decision (str).
    """
    sym = symbol.upper() + ".JK"
    df = yf.download(sym, period="6mo", progress=False, auto_adjust=False)
    if df.empty or len(df) < 50:
        raise ValueError(f"Data tidak cukup untuk {symbol}")

    df.ta.rsi(length=14, append=True)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VolMA20"] = df["Volume"].rolling(20).mean()
    df.dropna(inplace=True)

    last = df.iloc[-1]
    rsi = float(last["RSI_14"])
    price = float(last["Close"])
    ma20 = float(last["MA20"])
    vol_ratio = float(last["Volume"] / df["VolMA20"].iloc[-1]) if df["VolMA20"].iloc[-1] else 0.0

    # Broker summary
    broker_data = fetch_broker_summary(symbol)
    broker_summary = []
    for b in broker_data:
        if abs(b["net_lot"]) >= BROKER_NET_THRESHOLD:
            mode = "AKUMULASI" if b["net_lot"] > 0 else "DISTRIBUSI"
            broker_summary.append(f"{mode} oleh {b['broker']}: net {b['net_lot']:,} lot")

    decision = "NEUTRAL (Tahan)"
    if price > ma20 and 50 < rsi < RSI_OVERBOUGHT and vol_ratio > 1 and len(broker_summary) > 0:
        decision = "SPECULATIVE BUY"
    elif rsi < RSI_OVERSOLD:
        decision = "WAIT & SEE (Oversold area)"
    elif price < ma20 and rsi < 50 and any(b["net_lot"] < 0 for b in broker_data):
        decision = "CAUTION / DISTRIBUTION TREND"

    summary = {
        "symbol": symbol.upper(),
        "price": price,
        "rsi": rsi,
        "vol_ratio": vol_ratio,
        "broker_summary": broker_summary
    }
    return summary, decision
