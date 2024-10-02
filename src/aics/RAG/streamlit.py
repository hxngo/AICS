import streamlit as st
st.set_page_config(layout="wide")  # 페이지 레이아웃을 넓게 설정

from rag import load_docs_from_json, create_vectorstore, create_chain_for_role

st.title("RAG Q&A 시스템")

# 사용자 입력
topic = st.text_input("시뮬레이션 주제를 입력하세요:", key="topic_input")
question = st.text_input("판례 입력:", key="question_input")

# 말풍선 스타일 정의
bubble_style_judge = """
<div style="background-color:#DCF8C6; padding:10px; border-radius:10px; margin-bottom:10px; max-width:60%;">
    <b>판사:</b> {message}
</div>
"""

bubble_style_prosecutor = """
<div style="background-color:#FFEB3B; padding:10px; border-radius:10px; margin-bottom:10px; max-width:60%;">
    <b>검사:</b> {message}
</div>
"""

bubble_style_lawyer = """
<div style="background-color:#BBDEFB; padding:10px; border-radius:10px; margin-bottom:10px; max-width:60%;">
    <b>변호사:</b> {message}
</div>
"""

if topic and question:
    if st.button("답변 받기"):
        with st.spinner("처리 중..."):
            # 문서 로드 및 분할
            json_file_path = "/home/a202021038/workspace/projects/hong/AICS/src/aics/RAG/law.json"
            splits = load_docs_from_json(json_file_path)
            
            # 벡터 저장소 생성
            vectorstore = create_vectorstore(splits)
            
            # 각 역할별로 체인 생성 및 답변 받기
            judge_result = create_chain_for_role(vectorstore, "판사", question)
            prosecutor_result = create_chain_for_role(vectorstore, "검사", question)
            lawyer_result = create_chain_for_role(vectorstore, "변호사", question)

            # 대화 스타일로 출력
            st.subheader("대화")

            # 판사 의견
            st.markdown(bubble_style_judge.format(message=judge_result['result']), unsafe_allow_html=True)

            # 검사 의견
            st.markdown(bubble_style_prosecutor.format(message=prosecutor_result['result']), unsafe_allow_html=True)

            # 변호사 의견
            st.markdown(bubble_style_lawyer.format(message=lawyer_result['result']), unsafe_allow_html=True)

            # 출처 출력
            st.subheader("출처:")
            for doc in judge_result["source_documents"]:
                st.write(doc.page_content)
                st.write("---")
