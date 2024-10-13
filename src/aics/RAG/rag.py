import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

# 환경 변수에서 OpenAI API 키를 불러옵니다.
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API 키가 설정되지 않았습니다. 환경 변수를 설정해주세요.")

def load_docs_from_json(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        documents = [Document(page_content=json.dumps(item, ensure_ascii=False), metadata={}) for item in data["데이터셋"]]
    except Exception as e:
        raise RuntimeError(f"JSON 로드 중 오류 발생: {e}")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    return splits

def create_vectorstore(splits):
    try:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=HuggingFaceEmbeddings(),
            persist_directory="db"
        )
    except Exception as e:
        raise RuntimeError(f"벡터스토어 생성 중 오류 발생: {e}")
    
    return vectorstore

def create_chain_for_role(vectorstore, role, question):
    if role == "판사":
        llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=openai_api_key)
        prompt_template = "당신은 판사입니다. {context} 질문: {question} 판사의 답변:"
    elif role == "검사":
        llm = ChatOpenAI(model="gpt-4", temperature=0.7, openai_api_key=openai_api_key)
        prompt_template = "당신은 검사입니다. {context} 질문: {question} 검사의 답변:"
    elif role == "변호사":
        llm = ChatOpenAI(model="gpt-4", temperature=0.5, openai_api_key=openai_api_key)
        prompt_template = "당신은 변호사입니다. {context} 질문: {question} 변호사의 답변:"
    
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )

    result = qa_chain({"query": question})
    
    return result
