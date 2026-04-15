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
        # 파일명이 정확히 json_key.json인지 확인하세요.
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_key.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"⚠️ 구글 시트 인증 실패: {e}")
        return None

# --- [3. 나스닥 시장 분석 함수 (ValueError 해결 버전)] ---
def get_market_strategy():
    try:
        # 나스닥 지수 데이터 추출
        nasdaq = yf.download("^IXIC", period="5d", interval="1d")
        
        # 최신 yfinance 구조 대응: 단일 숫자(Scalar)로 강제 변환
        close_data = nasdaq['Close']
        
        # 데이터가 Series/DataFrame 형태일 경우 마지막 값만 추출
        current_close = float(close_data.iloc[-1].iloc[0]) if hasattr(close_data.iloc[-1], "__len__") else float(close_data.iloc[-1])
        prev_close = float(close_data.iloc[-2].iloc[0]) if hasattr(close_data.iloc[-2], "__len__") else float(close_data.iloc[-2])
        
        n_change = ((current_close - prev_close) / prev_close) * 100
    except Exception as e:
        st.warning(f"데이터 분석 중 알림: {e}")
        n_change = 0 
    
    # 등락률에 따른 포지션 결정
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
        # 사용자님의 실제 시트 ID 적용 완료
        sheet = client.open_by_key("1uQshZ6Jrgfwv47Qwn3mK1NDhvJeJmSuQc3v9aYYaL5c").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        st.divider()
        st.subheader("📊 키움 수집기 실시간 데이터 (2분 주기)")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("구글 시트에 표시할 데이터가 없습니다.")
    except Exception as e:
        st.warning(f"시트 데이터를 불러오는 중 오류 발생: {e}")

# 개별 종목 현재가 조회 섹션
st.divider()
target = st.text_input("🔍 종목 코드 입력 (예: 005930.KS)", "005930.KS")
if target:
    try:
        ticker_data = yf.Ticker(target).fast_info
        st.metric(f"{target} 현재가", f"{int(ticker_data.last_price):,}원")
    except:
        st.write("정확한 종목 코드를 입력해 주세요.")

# --- [5. 실시간 갱신 설정 (2분)] ---
time.sleep(120)
st.rerun()
