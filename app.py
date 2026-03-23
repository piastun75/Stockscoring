import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 Stock Scoring App")

tickers_input = st.text_input("Tickery", "AAPL,MSFT,CDR.WA")
tickers = [t.strip() for t in tickers_input.split(",")]

def get_data(t):
    s = yf.Ticker(t)
    i = s.info
    h = s.history(period="1y")
    
    try:
        r12 = (h["Close"][-1] / h["Close"][0]) - 1
        r1 = (h["Close"][-1] / h["Close"][-22]) - 1
        mom = r12 - r1
    except:
        mom = 0

    return {
        "ticker": t,
        "pe": i.get("trailingPE"),
        "ps": i.get("priceToSalesTrailing12Months"),
        "roe": i.get("returnOnEquity"),
        "debt": i.get("debtToEquity"),
        "rev_growth": i.get("revenueGrowth"),
        "earn_growth": i.get("earningsGrowth"),
        "momentum": mom
    }

def score(d):
    s = 0
    if d["pe"] and d["pe"] < 15: s+=1
    if d["ps"] and d["ps"] < 2: s+=1
    if d["rev_growth"] and d["rev_growth"] > 0.08: s+=1
    if d["earn_growth"] and d["earn_growth"] > 0.10: s+=1
    if d["roe"] and d["roe"] > 0.12: s+=1
    if d["debt"] and d["debt"] < 1: s+=1
    if d["momentum"] > 0: s+=2
    return s

data = []

for t in tickers:
    d = get_data(t)
    d["score"] = score(d)
    d["decision"] = "BUY" if d["score"]>=7 else "HOLD" if d["score"]>=5 else "AVOID"
    data.append(d)

df = pd.DataFrame(data).sort_values("score", ascending=False)

st.dataframe(df)

sel = st.selectbox("Wykres", df["ticker"])
hist = yf.Ticker(sel).history(period="1y")
st.line_chart(hist["Close"])
