import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- [1. 앱 설정] ---
st.set_page_config(page_title="🛡️ 07:00 AI 투자 비서", layout="centered")

# --- [2. 구글 시트 인증 함수] ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # GitHub에 업로드한 json_key.json 파일을 읽어옵니다.
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_key.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"⚠️ 구글 시트 인증 실패: {e}")
        return None

# --- [3. 나스닥 시장 분석 함수] ---
def get_market_strategy():
    try:
        nasdaq = yf.download("^IXIC", period="5d", interval="1d")
        current_close = nasdaq['Close'].iloc[-1].item()
        prev_close = nasdaq['Close'].iloc[-2].item()
        n_change = ((current_close - prev_close) / prev_close) * 100
    except Exception as e:
        st.warning(f"데이터 분석 중 알림: {e}")
        n_change = 0 
    
    if n_change < -1.0:
        return "🚨 보수적 관망", f"나스닥 {n_change:.2f}% 하락. 시초가 추격 금지.", n_change
    elif n_change > 1.0:
        return "🚀 공격적 매수", f"나스닥 {n_change:.2f}% 상승. 눌림목 매수 유효.", n_change
    else:
        return "⚠️ 중립 대응", f"나스닥 {n_change:.2f}% 보합. 수급 확인 후 진입.", n_change

# --- [4. 메인 화면 UI 표시] ---
status, msg, n_val = get_market_strategy()

st.title("🛡️ 07:00 데일리 리포트")
st.error(f"### 오늘의 포지션: {status}")
st.info(f"📍 **핵심 전략:** {msg}")

# 구글 시트 데이터 불러오기 및 표시
client = get_gspread_client()
if client:
    try:
        # 사용자님의 실제 시트 ID (1uQsh...L5c)
        sheet = client.open_by_key("1uQshZ6Jrgfwv47Qwn3mK1NDhvJeJmSuQc3v9aYYaL5c").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        st.divider()
        st.subheader("📊 키움 수집기 실시간 데이터 (2분 주기 갱신)")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("구글 시트에 표시할 데이터가 없습니다.")
    except Exception as e:
        st.warning(f"시트 데이터를 불러오는 중 오류 발생: {e}")

# 개별 종목 간편 조회
st.divider()
target = st.text_input("🔍 개별 종목 현재가 조회 (예: 005930.KS)", "005930.KS")
if target:
    try:
        ticker_data = yf.Ticker(target).fast_info
        st.metric(f"{target} 현재가", f"{int(ticker_data.last_price):,}원")
    except:
        st.write("정확한 종목 코드를 입력해 주세요.")

# --- [5. 실시간 갱신 설정] ---
# 120초(2분)마다 앱 자동 새로고침
time.sleep(60)
st.rerun()
