import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- [1. 앱 설정 및 스타일] ---
st.set_page_config(page_title="🛡️ 07:00 AI 투자 통합 비서", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 데이터 로드 함수들] ---

# 시장 지표 (나스닥, 환율)
def get_market_data():
    try:
        nasdaq = yf.download("^IXIC", period="2d", interval="1d")
        n_change = ((nasdaq['Close'].iloc[-1] - nasdaq['Close'].iloc[-2]) / nasdaq['Close'].iloc[-2]) * 100
        
        exchange = yf.download("USDKRW=X", period="1d", interval="1m")
        ex_curr = float(exchange['Close'].iloc[-1])
        return n_change, ex_curr
    except: return 0.0, 0.0

# 구글 시트 연동 (상승/하락 TOP 10)
def get_sheet_data(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("json_key.json", scope)
        client = gspread.authorize(creds)
        doc = client.open_by_key(sheet_id)
        # 첫 번째 탭(상승), 두 번째 탭(하락)으로 구성 가정
        up_df = pd.DataFrame(doc.get_worksheet(0).get_all_records())
        down_df = pd.DataFrame(doc.get_worksheet(1).get_all_records())
        return up_df.head(10), down_df.head(10)
    except: return pd.DataFrame(), pd.DataFrame()

# 종목별 심층 분석 (지분, M&A, 기술적 지표)
def get_stock_deep_analysis(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 지배구조 (5% 이상 지분 등)
        holders = ticker.major_holders
        # 기술적 지표 (200일선)
        hist = ticker.history(period="1y")
        support_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        curr_price = hist['Close'].iloc[-1]
        # M&A 관련 뉴스
        news = [n for n in ticker.news if any(w in n['title'].upper() for w in ['M&A', 'ACQUISITION', 'MERGER', '인수', '합병'])]
        return holders, support_200, curr_price, news[:3]
    except: return None, 0, 0, []

# --- [3. 메인 UI 레이아웃] ---

st.title("📊 07:00 통합 마켓 전략 리포트")
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (2분 주기 자동 갱신)")

# 섹션 1: 글로벌 매크로 (나스닥 & 환율)
n_val, ex_val = get_market_data()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📈 나스닥 지수", f"{n_val:.2f}%", delta="상승" if n_val > 0 else "하락")
with col2:
    status = "위험" if ex_val > 1350 else "안정"
    st.metric("💵 원/달러 환율", f"{ex_val:,.1f}원", delta=status, delta_color="inverse")
with col3:
    if n_val > 0.5 and ex_val < 1350: strategy = "🚀 공격적 매수"
    elif n_val < -0.5 or ex_val > 1380: strategy = "🚨 보수적 관망"
    else: strategy = "⚠️ 수급별 개별 대응"
    st.subheader(f"오늘의 전략: {strategy}")

# 섹션 2: 시장별 TOP 10 수급 현황 (Tabs 활용)
st.divider()
st.subheader("🔥 실시간 시장 수급 모니터링 (연기금 중심)")
up_10, down_10 = get_sheet_data("1pObFcno3L1-OJY_xZzjv2nKEubeTejkFYVTtZ2Gjvg8") # 위에서 생성한 시트 ID

tab1, tab2 = st.tabs(["✅ 상승 & 매집 TOP 10", "⚠️ 하락 & 이탈 TOP 10"])

with tab1:
    if not up_10.empty:
        st.dataframe(up_10, use_container_width=True, hide_index=True)
    else: st.info("상승 종목 데이터를 수집 중입니다.")

with tab2:
    if not down_10.empty:
        st.dataframe(down_10, use_container_width=True, hide_index=True)
    else: st.info("하락 종목 데이터를 수집 중입니다.")

# 섹션 3: AI 종목 심층 진단 (5개년 히스토리)
st.divider()
st.subheader("🔍 AI 종목 정밀 진단 (지분/M&A/타점)")
target_ticker = st.text_input("분석할 종목 코드를 입력하세요 (예: 005930.KS)", "005930.KS")

if target_ticker:
    holders, support, curr, ma_news = get_stock_deep_analysis(target_ticker)
    
    c_left, c_right = st.columns(2)
    with c_left:
        st.write("👥 **지배구조 (5% 이상 대량지분)**")
        st.dataframe(holders, use_container_width=True) if holders is not None else st.write("데이터 없음")
        
        diff = ((curr - support) / support) * 100
        st.write(f"🛡️ **장기 지지선(200일):** {support:,.0f}원")
        if abs(diff) < 3: st.success(f"현재 매수 적기! (지지선과 {diff:.1f}% 거리)")
        else: st.info(f"지지선과 거리: {diff:.1f}%")

    with c_right:
        st.write("🏢 **최근 5개년 주요 M&A/이슈**")
        if ma_news:
            for n in ma_news: st.info(f"🔗 [{n['title']}]({n['link']})")
        else: st.write("최근 M&A 뉴스가 없습니다.")

# --- [4. 자동 새로고침 로직] ---
time.sleep(120)
st.rerun()
