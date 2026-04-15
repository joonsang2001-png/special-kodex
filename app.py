import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

# --- [1. 앱 설정] ---
st.set_page_config(page_title="🛡️ 07:00 AI 투자 비서", layout="centered")

# --- [2. 핵심 분석 함수] ---
def get_market_strategy():
    try:
        nasdaq = yf.download("^IXIC", period="2d", interval="1h")
        n_change = ((nasdaq['Close'].iloc[-1] - nasdaq['Close'].iloc[-2]) / nasdaq['Close'].iloc[-2]) * 100
    except:
        n_change = 0 
    if n_change < -1.0: return "🚨 보수적 관망", f"나스닥 {n_change:.2f}% 하락. 시초가 추격 금지.", n_change
    elif n_change > 1.0: return "🚀 공격적 매수", f"나스닥 {n_change:.2f}% 상승. 눌림목 매수 유효.", n_change
    else: return "⚠️ 중립 대응", f"나스닥 {n_change:.2f}% 보합. 수급 확인 후 진입.", n_change

def analyze_30min_step(ticker):
    df = yf.download(ticker, period="1d", interval="30m")
    if df.empty: return []
    logs = []
    for i in range(len(df)):
        time_label = df.index[i].strftime('%H:%M')
        is_strong = df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Volume'].mean()
        status = "🔥 세력매집" if is_strong else "평이"
        logs.append(f"**{time_label}** | {int(df['Close'].iloc[i]):,}원 | {status}")
    return logs[-5:]

# --- [3. UI 구성] ---
status, msg, n_val = get_market_strategy()
st.title("🛡️ 07:00 데일리 리포트")
st.error(f"### 오늘의 포지션: {status}")
st.info(f"📍 **핵심 전략:** {msg}")

with st.expander("🌐 글로벌 인사이트 (NPS, Apollo, 외신)"):
    st.markdown("* **NPS:** 지분 유지 및 하방 지지 | **Apollo:** 반도체 인프라 투자 긍정적")

st.divider()
target = st.text_input("🔍 종목 코드 입력", "005930.KS")
if target:
    c1, c2 = st.columns([1, 1])
    with c1:
        ticker_data = yf.Ticker(target).fast_info
        st.metric(target, f"{int(ticker_data.last_price):,}원", "실시간 연동중")
    with c2:
        for log in analyze_30min_step(target): st.write(log)

time.sleep(15)
st.rerun()
