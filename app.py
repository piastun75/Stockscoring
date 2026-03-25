import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Stock Scoring App", layout="wide")

st.title("📊 Stock Scoring PRO")

# === INPUT ===
tickers_input = st.text_input("Tickery (oddzielone przecinkami)", "AAPL,MSFT,CDR.WA")
tickers = [t.strip() for t in tickers_input.split(",") if t.strip() != ""]

# === CACHE (żeby nie pobierać w kółko tych samych danych)
@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        time.sleep(1)  # 🔥 zabezpieczenie przed blokadą

        if len(hist) > 30:
            ret_12m = (hist["Close"][-1] / hist["Close"][0]) - 1
            ret_1m = (hist["Close"][-1] / hist["Close"][-22]) - 1
            momentum = ret_12m - ret_1m
        else:
            momentum = 0

        return {
            "ticker": ticker,
            "pe": info.get("trailingPE"),
            "ps": info.get("priceToSalesTrailing12Months"),
            "roe": info.get("returnOnEquity"),
            "debt": info.get("debtToEquity"),
            "rev_growth": info.get("revenueGrowth"),
            "earn_growth": info.get("earningsGrowth"),
            "momentum": momentum
        }

    except Exception:
        return {
            "ticker": ticker,
            "pe": None,
            "ps": None,
            "roe": None,
            "debt": None,
            "rev_growth": None,
            "earn_growth": None,
            "momentum": 0
        }

# === SCORING ===
def score(d):
    s = 0

    # VALUE
    if d["pe"] and d["pe"] < 15: s += 1
    if d["ps"] and d["ps"] < 2: s += 1

    # GROWTH
    if d["rev_growth"] and d["rev_growth"] > 0.08: s += 1
    if d["earn_growth"] and d["earn_growth"] > 0.10: s += 1

    # QUALITY
    if d["roe"] and d["roe"] > 0.12: s += 1
    if d["debt"] and d["debt"] < 1: s += 1

    # MOMENTUM
    if d["momentum"] > 0: s += 2

    return s

# === ANALIZA ===
results = []

if st.button("🔍 Analizuj"):
    with st.spinner("Pobieranie danych..."):
        for t in tickers:
            data = fetch_data(t)
            data["score"] = score(data)

            if data["score"] >= 7:
                data["decision"] = "BUY"
            elif data["score"] >= 5:
                data["decision"] = "HOLD"
            else:
                data["decision"] = "AVOID"

            results.append(data)

    if results:
        df = pd.DataFrame(results).sort_values("score", ascending=False)

        st.subheader("🏆 Ranking spółek")
        st.dataframe(df, use_container_width=True)

        # === wykres ===
        selected = st.selectbox("📈 Wybierz spółkę do wykresu", df["ticker"])
        hist = yf.Ticker(selected).history(period="1y")

        st.line_chart(hist["Close"])

        # === market timing ===
        st.subheader("📉 Market Timing")

        sp = yf.Ticker("^GSPC").history(period="1y")
        ma200 = sp["Close"].rolling(200).mean()

        if sp["Close"][-1] > ma200[-1]:
            st.success("Rynek: BULL → można inwestować")
        else:
            st.error("Rynek: BEAR → ostrożność")

    else:
        st.warning("Brak danych do wyświetlenia")
