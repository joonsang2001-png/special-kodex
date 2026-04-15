import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- [1. 앱 설정] ---
st.set_page_config(page_title="🛡️ 07:00 AI 투자 비서", layout="wide")

# --- [2. 구글 시트 데이터 로드 함수] ---
def get_sheet_data(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_key.json", scope)
        client = gspread.authorize(creds)
        doc = client.open_by_key(sheet_id)
        sheet = doc.get_worksheet(0) 
        
        # 데이터를 가져오되, 비어있을 경우를 대비해 get_all_values 사용 후 가공
        all_values = sheet.get_all_values()
        
        if len(all_values) > 1: # 제목줄 외에 데이터가 있는 경우
            df = pd.DataFrame(all_values[1:], columns=all_values[0])
            return df
        else:
            return pd.DataFrame() # 데이터가 1행(제목)만 있는 경우 빈 데이터프레임 반환
    except Exception as e:
        st.error(f"⚠️ 시트 연결 확인 중: {e}")
        return pd.DataFrame()

# --- [3. 나스닥 분석 함수] ---
def get_market_strategy():
    try:
        nasdaq = yf.download("^IXIC", period="5d", interval="1d")
        close_data = nasdaq['Close']
        # 최신 yfinance 버전 대응 (단일 숫자 추출)
        current_close = float(close_data.iloc[-1].iloc[0]) if hasattr(close_data.iloc[-1], "__len__") else float(close_data.iloc[-1])
        prev_close = float(close_data.iloc[-2].iloc[0]) if hasattr(close_data.iloc[-2], "__len__") else float(close_data.iloc[-2])
        n_change = ((current_close - prev_close) / prev_close) * 100
        return n_change
    except:
        return 0

# --- [4. 메인 화면 구성] ---
n_val = get_market_strategy()

st.title("🛡️ 07:00 데일리 리포트")

# 나스닥 요약 대시보드
col1, col2 = st.columns([1, 2])
with col1:
    status = "🚀 공격적 매수" if n_val > 1.0 else "🚨 보수적 관망" if n_val < -1.0 else "⚠️ 중립 대응"
    st.metric("나스닥 등락률", f"{n_val:.2f}%", status)

with col2:
    st.info(f"📍 **전략 가이드:** 현재 나스닥 지수는 {n_val:.2f}%입니다. 구글 시트에 데이터가 입력되면 아래 표에 실시간으로 표시됩니다.")

# 데이터 표 출력 섹션
st.divider()
st.subheader("📊 실시간 종목 현황 (2분 주기 업데이트)")

SHEET_ID = "1uQshZ6Jrgfwv47Qwn3mK1NDhvJeJmSuQc3v9aYYaL5c"
df = get_sheet_data(SHEET_ID)

if not df.empty:
    # 데이터가 있을 때 출력
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    # 데이터가 없을 때 사용자 친화적인 메시지 출력
    st.warning("🔄 현재 구글 시트에서 데이터를 기다리고 있습니다. (수집기 실행 확인 필요)")
    st.write("💡 **팁:** 구글 시트 2행에 데이터를 입력하면 여기에 즉시 나타납니다.")

# 하단 정보 및 자동 갱신
st.divider()
st.caption(f"최근 동기화: {datetime.now().strftime('%H:%M:%S')} (2분 후 자동 새로고침)")

# 2분 대기 후 리런
time.sleep(120)
st.rerun()
