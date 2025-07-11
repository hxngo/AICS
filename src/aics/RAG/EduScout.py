import streamlit as st
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from backend_youtube6 import (VideoProcessor, BookmarkManager, NoteManager, TranscriptManager, YouTubeExtractor,Translator)
from bookmark_sidebar import show_bookmark_sidebar
from streamlit_extras.let_it_rain import rain

HISTORY_DIR = Path("history")
SEARCH_HISTORY_FILE = HISTORY_DIR / "search_history.json"
WATCH_HISTORY_FILE = HISTORY_DIR / "watch_history.json"

# 디렉토리가 없으면 생성
HISTORY_DIR.mkdir(exist_ok=True)

# 환경 변수 설정
if 'OPENAI_API_KEY' not in os.environ:
    os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']

# 페이지 설정
st.set_page_config(
    page_title="YouTube 강의 도우미",
    page_icon="🎓",
    layout="wide"
)

# 스타일 설정
st.markdown("""
   <style>
   /* 다크 모드 */
   @media (prefers-color-scheme: dark) {
       :root {
           --primary-color: #4A90E2;
           --secondary-color: #2C3E50;
           --accent-color: #E74C3C;
           --text-color: #ECF0F1;
           --background-color: #34495E;
           --original-text-color: #A0A0A0;  /* 다크모드에서의 원문 텍스트 색상 */
       }
   }

   /* 라이트 모드 */
   @media (prefers-color-scheme: light) {
       :root {
           --primary-color: #2980B9;
           --secondary-color: #7F8C8D;
           --accent-color: #C0392B;
           --text-color: #2C3E50;
           --background-color: #F5F5F5;
           --original-text-color: #666;  /* 라이트모드에서의 원문 텍스트 색상 */
       }
   }
   
   .transcript-segment {
       background: var(--background-color);
       border-radius: 10px;
       padding: 15px;
       margin: 10px 0;
       border-left: 4px solid var(--primary-color);
       color: var(--text-color);
       box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
   }
   
   .timestamp {
       background: var(--primary-color);
       color: white;
       padding: 4px 10px;
       border-radius: 15px;
       font-weight: bold;
       margin-right: 10px;
       font-size: 0.9em;
       display: inline-block;
   }

   .original-text {
       color: var(--original-text-color);
       font-style: italic;
       margin-top: 8px;
       display: block;
       border-top: 1px solid rgba(128, 128, 128, 0.2);
       padding-top: 8px;
       font-size: 0.95em;
   }
   
   /* 라이트 모드에서 timestamp 텍스트 색상 조정 */
   @media (prefers-color-scheme: light) {
       .timestamp {
           color: #FFFFFF;  /* 밝은 배경에서도 잘 보이는 흰색 유지 */
       }
       .transcript-segment {
           border-left-color: var(--primary-color);
           box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
       }
   }
   
   .transcript-segment:hover {
       transform: translateX(5px);
       transition: transform 0.2s ease;
       border-left-color: var(--accent-color);
   }

   /* 라이트/다크 모드 전환 시 부드러운 전환 효과 */
   * {
       transition: background-color 0.3s ease, color 0.3s ease;
   }
   </style>
""", unsafe_allow_html=True)

def save_search_history():
    """검색 기록을 파일로 저장"""
    try:
        with open(SEARCH_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.search_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"검색 기록 저장 실패: {str(e)}")

def save_watch_history():
    """시청 기록을 파일로 저장"""
    try:
        with open(WATCH_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.watch_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"시청 기록 저장 실패: {str(e)}")

def load_history():
    """저장된 기록 불러오기"""
    # 검색 기록 불러오기
    if SEARCH_HISTORY_FILE.exists():
        try:
            with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                st.session_state.search_history = json.load(f)
        except Exception as e:
            st.error(f"검색 기록 불러오기 실패: {str(e)}")
            st.session_state.search_history = []
    else:
        st.session_state.search_history = []
    
    # 시청 기록 불러오기
    if WATCH_HISTORY_FILE.exists():
        try:
            with open(WATCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                st.session_state.watch_history = json.load(f)
        except Exception as e:
            st.error(f"시청 기록 불러오기 실패: {str(e)}")
            st.session_state.watch_history = []
    else:
        st.session_state.watch_history = []

def initialize_session_state():
    if 'search_history' not in st.session_state or 'watch_history' not in st.session_state:
        load_history()
    if 'bookmark_manager' not in st.session_state:
        st.session_state.bookmark_manager = BookmarkManager()
    if 'note_manager' not in st.session_state:
        st.session_state.note_manager = NoteManager()
    if 'transcript_manager' not in st.session_state:
        st.session_state.transcript_manager = TranscriptManager()
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'watch_history' not in st.session_state:
        st.session_state.watch_history = []
    if 'processor' not in st.session_state:
        try:
            youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            if not youtube_api_key:
                st.error('YouTube API 키가 설정되지 않았습니다.')
                st.stop()
            st.session_state.processor = VideoProcessor()
        except Exception as e:
            st.error(f'VideoProcessor 초기화 실패: {str(e)}')
            st.stop()

def show_search_history_sidebar():
    st.subheader("🔍 검색 기록")
    
    if 'search_history' not in st.session_state or not st.session_state.search_history:
        st.info("검색 기록이 없습니다.")
        return

    # 전체 삭제 버튼을 상단에 배치
    if st.button("전체 기록 삭제", key="clear_all_search_history", type="secondary"):
        st.session_state.search_history = []
        save_search_history()  # 변경사항 저장
        st.rerun()
        
    for idx, item in enumerate(reversed(st.session_state.search_history)):
        with st.expander(f"🔍 {item.get('query', '')[:30]}... ({item.get('timestamp', '')})"):
            st.write(f"**질문:** {item.get('query', '')}")
            st.write(f"**답변:** {item.get('answer', '')}")
            st.write(f"**RAG 사용:** {'✅' if item.get('rag_used', False) else '❌'}")
            
            # 개별 항목 삭제 버튼 (필요한 경우)
            if st.button("삭제", key=f"delete_search_{idx}"):
                st.session_state.search_history.remove(item)
                save_search_history()
                st.rerun()

def show_watch_history_sidebar():
    st.subheader("📺 시청 기록")
    
    if not st.session_state.watch_history:
        st.info("시청 기록이 없습니다.")
        return
        
    for idx, item in enumerate(reversed(st.session_state.watch_history)):
        try:
            # video_info가 있는지 확인하고, title이 없으면 대체 텍스트 사용
            video_title = (item.get('video_info', {}).get('title', '제목 없음') 
                         if isinstance(item.get('video_info'), dict) 
                         else '제목 없음')
            video_url = item.get('url', '#')
            timestamp = item.get('timestamp', 'N/A')
            
            with st.expander(f"📺 {video_title[:30]}... ({timestamp})"):
                st.write(f"**제목:** {video_title}")
                st.write(f"🎥 [영상 보기]({video_url})")
                
                if st.button(f"삭제", key=f"del_watch_{idx}"):
                    st.session_state.watch_history.remove(item)
                    st.rerun()
                    
        except Exception as e:
            st.error(f"시청 기록 표시 중 오류 발생: {str(e)}")
            continue
            
    if st.button("전체 기록 삭제", key="clear_watch_history", type="secondary"):
        st.session_state.watch_history = []
        save_watch_history()  # 변경사항 저장
        st.rerun()

def format_time(seconds: float) -> str:
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes:02d}:{seconds:02d}"

def process_video(youtube_url, processor):
    if youtube_url:
        with st.spinner('영상 처리 중...'):
            try:
                result = processor.process_video(youtube_url)
                if 'transcription' in result and result['transcription']:
                    st.session_state.current_video = result
                    
                    # video_info에서 필요한 정보 추출
                    video_info = {
                        'title': result.get('video_info', {}).get('snippet', {}).get('title', '제목 정보 없음'),
                        'author': result.get('video_info', {}).get('snippet', {}).get('channelTitle', '작성자 정보 없음'),
                        'views': result.get('video_info', {}).get('statistics', {}).get('viewCount', '0'),
                        'description': result.get('video_info', {}).get('snippet', {}).get('description', '')
                    }
                    
                    # 시청 기록 저장
                    watch_record = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'video_info': video_info,
                        'url': youtube_url
                    }
                    st.session_state.watch_history.append(watch_record)
                    save_watch_history()  # 시청 기록 저장
                    
                    st.success('영상 처리가 완료되었습니다!')
                else:
                    st.warning('자막 데이터를 가져오지 못했습니다.')
            except Exception as e:
                st.error(f'영상 처리 중 오류가 발생했습니다: {str(e)}')
    else:
        st.warning('YouTube URL을 입력해주세요.')

def show_summary():
    st.subheader('📝 영상 요약')
    summary = st.session_state.current_video['summary']
    st.write("**요약 내용:**")
    st.write(summary['summary'])
    st.markdown(f"""
    <div style='font-size: 0.8em; color: #666;'>
    원본 길이: {summary['original_length']} 단어 → 요약 길이: {summary['summary_length']} 단어
    </div>
    """, unsafe_allow_html=True)

def show_recommendations():
    st.subheader('🎯 추천 컨텐츠')
    recommendations = st.session_state.current_video['recommendations']
    if recommendations:
        for idx, rec in enumerate(recommendations):
            with st.expander(f"추천 {idx+1}: {rec['title']}"):
                st.markdown(f"""
                    **비디오 정보:**
                    - 제목: {rec['title']}
                    - 채널: {rec.get('channel_title', '정보 없음')}
                    - 설명: {rec.get('description', '설명 없음')}
                    - 조회수: {f"{rec.get('view_count', 0):,d} 회" if rec.get('view_count') else '정보 없음'}
                """)
                video_url = f"https://www.youtube.com/watch?v={rec['video_id']}"
                st.markdown(f"[이 영상 보기]({video_url})")

def show_transcript_search(youtube_url):
    st.subheader('🔍 자막 검색')
    transcript_search = st.text_input(
        '검색할 키워드를 입력하세요',
        key='transcript_search',
        placeholder='자막에서 검색할 키워드를 입력하세요...'
    )
    
    if transcript_search:
        try:
            if st.session_state.current_video and 'transcription' in st.session_state.current_video:
                segments = st.session_state.current_video['transcription'].get('segments', [])
                search_results = []
                for segment in segments:
                    if transcript_search.lower() in segment['text'].lower():
                        search_results.append({
                            'start_time': segment['start'],
                            'end_time': segment['end'],
                            'text': segment['text']
                        })
                
                if search_results:
                    st.write(f"🎯 검색 결과: {len(search_results)}개 구간 발견")
                    for idx, result in enumerate(search_results):
                        show_search_result(idx, result, youtube_url)
                else:
                    st.info('검색 결과가 없습니다.')
        except Exception as e:
            st.error(f'검색 중 오류가 발생했습니다: {str(e)}')

def show_search_result(idx, result, youtube_url):
    with st.expander(f"구간 {idx + 1} ({format_time(result['start_time'])} ~ {format_time(result['end_time'])})"):
        st.write(result['text'])
        timestamp_url = f"{youtube_url}&t={int(result['start_time'])}"
        st.markdown(f"🎥 [이 구간으로 이동]({timestamp_url})")
        
        if st.button(f'이 구간 북마크 추가 #{idx}', key=f'segment_bookmark_{idx}'):
            add_bookmark_for_segment(result, youtube_url)

def add_bookmark_for_segment(result, youtube_url):
    st.session_state.bookmark_manager.add_bookmark(
        timestamp=format_time(result['start_time']),
        content=result['text'],
        video_info={
            'title': st.session_state.current_video['video_info'].get('title', ''),
            'url': youtube_url,
            'timestamp': int(result['start_time'])
        }
    )
    st.success('북마크가 추가되었습니다!')

def show_search_section():
    st.subheader('🔍 검색')
    
    # RAG 토글 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            '검색어를 입력하세요',
            key='search_query',
            placeholder='궁금한 내용을 입력하세요...'
        )
    with col2:
        st.session_state.use_rag = st.toggle('RAG 사용', value=True, help='RAG를 사용하면 더 정확한 검색이 가능하지만 속도가 느려질 수 있습니다.')

    if st.button('검색', use_container_width=True):
        if st.session_state.current_video is None:
            st.warning('먼저 영상을 처리해주세요.')
        else:
            result = search_content()
            if result:
                st.markdown("### 검색 결과")
                st.write(f"**답변:**\n{result['answer']}")
                
                if result.get('rag_used', False) and result['source_documents']:
                    with st.expander("참고한 영상 구간"):
                        for doc in result['source_documents']:
                            st.markdown(f"```\n{doc['content']}\n```")

def show_full_transcript(youtube_url):
    with st.expander("📝 전체 자막 보기"):
        if not youtube_url:
            st.info('영상 URL을 입력해주세요.')
            return
            
        try:
            if st.session_state.current_video and 'transcription' in st.session_state.current_video:
                segments = st.session_state.current_video['transcription'].get('segments', [])
                
                if 'translator' not in st.session_state:
                    try:
                        st.session_state.translator = Translator()
                    except Exception as e:
                        st.error(f"번역 서비스 초기화 실패: {str(e)}")
                        return

                target_language = st.selectbox(
                    "번역 언어 선택:",
                    options=list(st.session_state.translator.supported_languages.keys()),
                    format_func=lambda x: st.session_state.translator.supported_languages[x],
                    key="transcript_translation_language"
                )
                
                show_original = st.checkbox("원문 같이 보기", value=True)
                
                if segments:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        translate_button = st.button("자막 번역", use_container_width=True)
                    
                    if translate_button:
                        with st.spinner("번역 중..."):
                            try:
                                # 첫 번째 세그먼트로 API 상태 확인
                                first_translation = st.session_state.translator.translate_text(
                                    segments[0]['text'], target_language
                                )
                                if first_translation is None:
                                    st.error("현재 번역 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.")
                                    return

                                for segment in segments:
                                    translated_text = st.session_state.translator.translate_text(
                                        segment['text'], target_language
                                    )
                                    if translated_text:
                                        st.markdown(f"""
                                        <div class="transcript-segment">
                                            <span class="timestamp">[{format_time(segment['start'])}]</span>
                                            {translated_text}
                                            {f"<br><small class='original-text'>{segment['text']}</small>" if show_original else ""}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        # 번역 실패 시 원문 표시
                                        st.markdown(f"""
                                        <div class="transcript-segment">
                                            <span class="timestamp">[{format_time(segment['start'])}]</span>
                                            {segment['text']}
                                            <br><small class="original-text">(번역 실패)</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"번역 중 오류가 발생했습니다: {str(e)}")
                    else:
                        # 원본 자막 표시
                        for segment in segments:
                            st.markdown(f"""
                            <div class="transcript-segment">
                                <span class="timestamp">[{format_time(segment['start'])}]</span> 
                                {segment['text']}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info('자막 정보를 찾을 수 없습니다.')
                    
        except Exception as e:
            st.error(f'자막 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}')


def show_guide():
    with st.expander("ℹ️ 사용 가이드", expanded=False):
        st.markdown("""
        ### 🎓 YouTube 강의 도우미 사용법
        
        1. **영상 설정**
           - YouTube URL을 입력하고 '영상 처리 시작' 버튼을 클릭합니다.
           - 자막이 있는 영상을 권장합니다.
        
        2. **메모 작성**
           - 사이드바의 메모 입력창에 내용을 작성합니다.
           - 관련 태그를 선택하여 메모를 분류할 수 있습니다.
        
        3. **검색 기능**
           - 영상 내용에 대해 질문하면 AI가 답변합니다.
           - 자막에서 특정 키워드를 검색할 수 있습니다.
        
        4. **북마크와 기록**
           - 중요한 부분을 북마크하여 나중에 다시 볼 수 있습니다.
           - 시청 기록과 검색 기록이 자동으로 저장됩니다.
        """)

def main():
    initialize_session_state()
    processor = st.session_state.processor
    st.title('🎓 YouTube 강의 도우미')
    show_guide()
    
    # 사이드바 구성
    with st.sidebar:
        st.subheader('✏️ 메모하기')
    
        # 메모 입력
        note_content = st.text_area(
            '메모를 입력하세요:',
            height=200,
            placeholder='여기에 메모를 작성하세요...',
            key='sidebar_note_content'
        )
    
        # 태그 선택
        default_tags = ['중요', '질문', '복습필요', '개념', '예시', '기타']
        custom_tag = st.text_input('새로운 태그 추가:', key='new_tag')
        if custom_tag:
            if custom_tag not in default_tags:
                default_tags.append(custom_tag)
    
        selected_tags = st.multiselect(
            '태그 선택:',
            options=default_tags,
            key='note_tags'
        )
    
        # 메모 저장 버튼
        if st.button('메모 저장', key='sidebar_save_note', use_container_width=True):
            try:
                if not note_content or not note_content.strip():
                    st.warning('메모를 작성해 주세요!')
                    return
            
                video_info = None
                if st.session_state.current_video and 'video_info' in st.session_state.current_video:
                    video_info = st.session_state.current_video['video_info']
            
                if st.session_state.note_manager.save_note(
                    note_content, 
                    tags=selected_tags,
                    video_info=video_info
                ):
                    st.success('메모가 저장되었습니다!')
                
                    rain(
                        emoji="✅",
                        font_size=54,
                        falling_speed=5,
                        animation_length="3"
                    )
            except Exception as e:
                st.error(f'메모 저장 중 오류가 발생했습니다: {str(e)}')
        
        # 2. 검색
        st.divider()
        st.subheader('🔍 검색')
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                '검색어를 입력하세요',
                key='sidebar_search_query',
                placeholder='궁금한 내용을 입력하세요'
            )
        with col2:
            st.session_state.use_rag = st.toggle(
                'RAG 사용', 
                value=True,
                key='sidebar_rag_toggle', 
                help='RAG를 사용하면 더 정확한 검색이 가능하지만 속도가 느려질 수 있습니다.'
            )

        st.session_state.search_query = search_query

        if st.button('검색', key='sidebar_search_button_main', use_container_width=True):
            if st.session_state.current_video is None:
                st.warning('먼저 영상을 처리해주세요.')
            else:
                with st.spinner('검색 중...'):
                    result = st.session_state.processor.search_content(
                        st.session_state.current_video['vectorstore'],
                        search_query,
                        use_rag=st.session_state.use_rag
                    )
                    if result:
                        # 검색 기록 저장
                        search_record = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'query': search_query,
                            'answer': result.get('answer', ''),
                            'rag_used': st.session_state.use_rag
                        }
                        st.session_state.search_history.append(search_record)
                        save_search_history()  # 검색 기록 저장
                
                        st.write(f"**답변:**\n{result.get('answer', '')}")
                        if result.get('rag_used', False) and result.get('source_documents', []):
                            with st.expander("참고한 영상 구간"):
                                for doc in result.get('source_documents', []):
                                    st.markdown(f"```\n{doc.get('content', '')}\n```")
        
        st.divider()
        show_search_history_sidebar()
        st.divider()
        show_watch_history_sidebar()
        st.divider()
        show_bookmark_sidebar()

    # 좌우 컬럼 분할
    left_col, right_col = st.columns([1, 4])
    
    # URL 입력 및 처리
    with left_col:
        st.header('🎥 영상 설정')
        youtube_url = st.text_input(
            'YouTube URL을 입력하세요',
            key='youtube_url',
            placeholder='https://www.youtube.com/watch?v=...'
        )
        if st.button('영상 처리 시작', key='process_button'):
            process_video(youtube_url, processor)
    
    # 메인 컨텐츠
    with right_col:
        if youtube_url:
            st.video(youtube_url)
            if st.session_state.current_video:
                tabs = st.tabs(["📝 요약", "🎯 추천", "🔍 검색", "📚 전체 자막"])
               
                with tabs[0]:  # 요약 탭
                    if 'summary' in st.session_state.current_video:
                        show_summary()
               
                with tabs[1]:  # 추천 탭
                    if 'recommendations' in st.session_state.current_video:
                        show_recommendations()
               
                with tabs[2]:  # 검색 탭
                    show_transcript_search(youtube_url)
               
                with tabs[3]:  # 전체 자막 탭
                    show_full_transcript(youtube_url)

if __name__ == "__main__":
   main()