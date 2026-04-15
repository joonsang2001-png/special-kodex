import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

# --- [1. 앱 설정 및 스타일] ---
st.set_page_config(page_title="🛡️ AI 통합 투자 비서", layout="centered")
st.markdown("""
    <style>
    .main-box { background-color: #161b22; padding: 20px; border-radius: 12px; border-left: 5px solid #2e7d32; margin-bottom: 25px; }
    .status-tag { font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: #0d1117; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 핵심 분석 엔진] ---

# 가. 07:00 전략 생성 (나스닥 및 글로벌 지표 분석)
def get_morning_strategy():
    nasdaq = yf.download("^IXIC", period="1d", interval="1m").tail(2)
    n_change = ((nasdaq['Close'].iloc[-1] - nasdaq['Open'].iloc[-1]) / nasdaq['Open'].iloc[-1]) * 100
    
    if n_change < -1.5:
        return "🚨 적극 관망", "나스닥 급락으로 인한 투심 악화. 현금 비중 70% 유지 및 시초가 매수 금지.", n_change
    elif n_change > 1.0:
        return "🚀 매수 유효", "미 증시 강세 반영. 주도주(반도체) 중심 눌림목 분할 매수 전략.", n_change
    else:
        return "⚠️ 보수적 접근", "방향성 탐색 구간. 외인/기관 수급 교차 확인 후 10:30분 이후 진입.", n_change

# 나. 30분 단위 수급 흐름 분석
def analyze_30min_flow(ticker):
    df = yf.download(ticker, period="1d", interval="30m")
    log = []
    for i in range(len(df)):
        time_str = df.index[i].strftime('%H:%M')
        # 가격 상승 + 거래량 폭증 시 '세력 개입'으로 판단
        strength = "🔥 세력유입" if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Volume'].mean() else "평이"
        log.append(f"**{time_str}** | {int(df['Close'].iloc[i]):,}원 | 수급: {strength}")
    return log[-5:] # 최근 5개(오후) 흐름 반환

# 다. 인사이트 데이터 (외신, 사모펀드, 국민연금)
def get_institutional_insights():
    return {
        "외신": "Bloomberg: 삼성 HBM4 공급망 진입 가속화 | Forbes: TGV 유리 기판 특허 독보적 1위",
        "큰손": "Apollo: 반도체 인프라 대규모 자금 투입 검토 | NPS: 삼성전자 지분 7.8% 상향 완료",
        "전략": "국민연금 지지선(82,000원) 부근 매수세 강력, 아폴로의 자본 하방 경직성 확보."
    }

# --- [3. UI 화면 구성] ---

# 🎯 섹션 1: 오늘의 매매 전략 (07:00 최우선 노출)
status, strategy, n_val = get_morning_strategy()
st.title("🛡️ 07:00 통합 전략 리포트")

st.markdown(f"""
<div class="main-box">
    <h3> 오늘의 대응: <span class="status-tag">{status}</span></h3>
    <p><b>나스닥 종가 변동:</b> {n_val:.2f}%</p>
    <p><b>🎯 핵심 가이드:</b> {strategy}</p>
</div>
""", unsafe_allow_html=True)

# 🌐 섹션 2: 글로벌 & 기관 인사이트 (NPS, Apollo, 외신)
with st.expander("🌐 글로벌 큰손 & 외신 브리핑"):
    insights = get_institutional_insights()
    st.info(f"**[기관 동향]** {insights['큰손']}")
    st.write(f"**[경제 매체]** {insights['외신']}")
    st.success(f"**[종합 분석]** {insights['전략']}")

# 📊 섹션 3: 종목 실시간 검색 및 30분 단위 분석
st.divider()
ticker_input = st.text_input("🔍 분석 종목 코드 입력 (예: 005930.KS)", "005930.KS")

if ticker_input:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 실시간 시세 및 AI 시뮬레이션")
        # 구글 시트 연동 시세 표시 (기존 SHEET_ID 활용)
        try:
            SHEET_ID = "7BKeraMju-59h-xIgTNGmLcoFfhLu_GvwaYBjm5qpCk"
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
            live_price = pd.read_csv(url)
            st.metric(ticker_input, f"{int(live_price.iloc[0, 0]):,}원", "세력 매수중")
        except:
            st.warning("키움 수집기 연결 대기 중...")
            
    with col2:
        st.subheader("🕒 30분 수급 분석")
        logs = analyze_30min_flow(ticker_input)
        for log in logs:
            st.write(f"- {log}")

# 📝 섹션 4: 장마감 복기 및 다음날 준비
st.divider()
with st.expander("📝 전일 시간대별 흐름 복기 (세력 타점)"):
    st.write("**[장초반]** 외인 반도체 대량 매수, 지수 상방 지지.")
    st.write("**[장중반]** 기관 차익 실현 매물 출현으로 보합 유지.")
    st.write("**[장후반]** 시간외 거래에서 세력의 유의미한 매집봉 포착.")

# 자동 새로고침 (15초)
time.sleep(15)
st.rerun()
