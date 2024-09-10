import os
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatPerplexity
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 환경 변수 설정
pplx_api_key = os.getenv("PERPLEXITY_API_KEY")
#os.environ["OPENAI_API_BASE"] = "https://api.perplexity.ai/chat/completions"

def load_docs(query):
    # 위키피디아 문서를 로드
    #loader = WikipediaLoader(query=query, load_max_docs=1)
    pdf_loader = PyPDFLoader("/home/hong/workspace/projects/AICS/src/aics/RAG/2312.17432v4.pdf")
    documents = pdf_loader.load()
    
    # 텍스트를 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)
    
    return splits

def create_vectorstore(splits):
    # 임베딩 생성
    

    # 고유한 ID 생성
    ids = [f"doc_{i}" for i in range(len(splits))]

    # Chroma 벡터스토어 생성, ID와 함께 제공
    vectorstore = Chroma.from_documents(documents=splits, embedding=HuggingFaceBgeEmbeddings(), ids=ids)
    return vectorstore

def create_rag_chain(vectorstore):
    # LLM 생성
    llm = ChatPerplexity(model="llama-3.1-sonar-small-128k-online", temperature=0, pplx_api_key=pplx_api_key)
    
    # 프롬프트 템플릿 설정
    prompt_template = """아래의 문맥을 사용하여 질문에 답하십시오.
    만약 답을 모른다면, 모른다고 말하고 답을 지어내지 마십시오.
    최대한 세 문장으로 답하고 가능한 한 간결하게 유지하십시오.
    {context}
    질문: {question}
    유용한 답변:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    chain_type_kwargs = {"prompt": PROMPT}
    
    # RetrievalQA 체인 생성
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs=chain_type_kwargs,
        return_source_documents=True
    )
    
    return qa_chain

