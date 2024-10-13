import streamlit as st
import time
import random

st.set_page_config(layout="wide")

st.title("RAG Q&A 다중 참여자 토론 시스템")

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    roles = ["판사", "검사", "변호사", "피해자 대표", "KT 회사 대표", "개인정보보호 전문가", "사이버보안 전문가"]
    opinions = {}
    for role in roles:
        opinions[role] = st.text_area(f"{role} 의견:", f"{role}의 초기 의견입니다.")
    simulation_speed = st.slider("토론 속도 (초)", 0.5, 3.0, 1.0)
    rounds = st.number_input("토론 라운드 수", min_value=1, max_value=5, value=3)

# 토론 진행 함수
def conduct_discussion(round_num):
    st.subheader(f"라운드 {round_num}")
    for role, opinion in opinions.items():
        with st.spinner(f"{role}의 의견을 기다리는 중..."):
            time.sleep(simulation_speed)
            if round_num == 1:
                message = f"{role} (초기 의견): {opinion}"
            else:
                message = f"{role} (추가 의견): {opinion}에 대한 {random.choice(['보완', '반박', '동의'])}"
            st.markdown(f"<div style='background-color:{random.choice(['#DCF8C6', '#FFEB3B', '#BBDEFB'])}; padding:10px; border-radius:10px;'>{message}</div>", unsafe_allow_html=True)
        
        # 사용자 상호작용 추가
        agree = st.button(f"{role}의 의견에 동의", key=f"agree_{role}_{round_num}")
        disagree = st.button(f"{role}의 의견에 반대", key=f"disagree_{role}_{round_num}")
        if agree:
            st.write(f"사용자가 {role}의 의견에 동의했습니다.")
        if disagree:
            st.write(f"사용자가 {role}의 의견에 반대했습니다.")

# 시뮬레이션 시작 버튼
if st.button("토론 시작"):
    for round in range(1, rounds + 1):
        conduct_discussion(round)
    
    st.success("토론이 완료되었습니다.")
    
    # 사용자 최종 판단
    user_judgment = st.text_area("토론에 대한 귀하의 최종 판단을 입력해주세요:")
    if st.button("최종 판단 제출"):
        st.write("사용자의 최종 판단:", user_judgment)

    # AI 요약 및 분석 (예시)
    st.subheader("AI 요약 및 분석")
    st.write("1. 주요 쟁점: 개인정보보호법 위반, 손해배상 책임, 보안 기술 개선 필요성")
    st.write("2. 입장 변화: KT 회사 대표의 입장이 점차 수용적으로 변화")
    st.write("3. 결론: 보안 강화와 피해자 보상이 필요하며, 재발 방지 대책 마련이 시급함")