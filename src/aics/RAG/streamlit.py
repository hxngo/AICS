import streamlit as st
from rag import load_docs, create_vectorstore, create_rag_chain

st.title("RAG Q&A 시스템")

# 사용자 입력
topic = st.text_input("위키피디아 주제를 입력하세요:")
question = st.text_input("해당 주제에 대해 질문하세요:")

if topic and question:
    if st.button("답변 받기"):
        with st.spinner("처리 중..."):
            # 문서 로드 및 분할
            splits = load_docs(topic)
            
            # 벡터 저장소 생성
            vectorstore = create_vectorstore(splits)
            
            # RAG 체인 생성
            qa_chain = create_rag_chain(vectorstore)
            
            # 질문에 대한 답변 생성
            result = qa_chain({"query": question})
            
            st.subheader("답변:")
            st.write(result["result"])
            
            st.subheader("출처:")
            for doc in result["source_documents"]:
                st.write(doc.page_content)
                st.write("---")

st.sidebar.title("소개")
st.sidebar.info(
    "이 앱은 RAG(검색 증강 생성) 시스템을 시연합니다. "
    "위키피디아를 지식 소스로 사용하고 OpenAI의 GPT 모델을 통해 답변을 생성합니다."
)