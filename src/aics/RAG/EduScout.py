import streamlit as st
import os
from datetime import datetime
import pandas as pd
from backend_youtube6 import VideoProcessor, BookmarkManager, NoteManager, TranscriptManager, YouTubeExtractor
from bookmark_sidebar import show_bookmark_sidebar
from search_history_sidebar import show_search_history_sidebar
from streamlit_extras.let_it_rain import rain
from watch_history_sidebar import show_watch_history_sidebar

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

def initialize_session_state():
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

def format_time(seconds: float) -> str:
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes:02d}:{seconds:02d}"

def search_content():
    try:
        if not st.session_state.search_query:
            st.warning('검색어를 입력해주세요.')
            return None
            
        if st.session_state.current_video is None:
            st.warning('먼저 영상을 처리해주세요.')
            return None
            
        with st.spinner('검색 중...'):
            result = st.session_state.processor.search_content(
                st.session_state.current_video['vectorstore'],
                st.session_state.search_query
            )
            
            # 검색 기록만 저장
            if 'search_history' not in st.session_state:
                st.session_state.search_history = []
                
            st.session_state.search_history.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'query': st.session_state.search_query,
                'answer': result['answer']
            })
            
            return result
            
    except Exception as e:
        st.error(f'검색 중 오류가 발생했습니다: {str(e)}')
        return None
    
def process_video(youtube_url, processor):
    if youtube_url:
        with st.spinner('영상 처리 중...'):
            try:
                result = processor.process_video(youtube_url)
                if 'transcription' in result and result['transcription']:
                    st.session_state.current_video = result
                    # 시청 기록 저장
                    st.session_state.watch_history.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'video_info': result['video_info'],
                        'url': youtube_url
                    })
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

def show_full_transcript(youtube_url):
    with st.expander("📝 전체 자막 보기"):
        if not youtube_url:
            st.info('영상 URL을 입력해주세요.')
            return
            
        try:
            if st.session_state.current_video and 'transcription' in st.session_state.current_video:
                segments = st.session_state.current_video['transcription'].get('segments', [])
                if segments:
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
        
        st.divider()
        # 2. 검색
        st.subheader('🔍 검색')
        search_query = st.text_input(
            '검색어를 입력하세요',
            key='sidebar_search_query',
            placeholder='궁금한 내용을 입력하세요'
        )
        st.session_state.search_query = search_query
        
        if st.button('검색', key='sidebar_search_button_main', use_container_width=True):
            if st.session_state.current_video is None:
                st.warning('먼저 영상을 처리해주세요.')
            else:
                st.session_state.search_result = search_content()
        
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
                    # 검색 결과 표시
                    if 'search_result' in st.session_state and st.session_state.search_result:
                        st.subheader('🔍 검색 결과')
                        result = st.session_state.search_result
                        st.markdown(f"**답변:**\n{result['answer']}")
                
                with tabs[3]:  # 전체 자막 탭
                    show_full_transcript(youtube_url)

if __name__ == "__main__":
    main()