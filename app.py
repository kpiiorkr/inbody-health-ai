"""
InBody AI 건강관리 시스템 - 메인 애플리케이션
Streamlit 기반 웹 인터페이스
"""
import streamlit as st
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

# 모듈 임포트
from ocr_processor import extract_inbody_data
from ai_analyzer import analyze_inbody_data
from harmony_search import generate_optimal_schedule
from report_generator import generate_inbody_report

# 페이지 설정
st.set_page_config(
    page_title="InBody AI 건강관리 시스템",
    page_icon="💪",
    layout="wide"
)

# 커스텀 CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.8rem;
    color: #2E86AB;
    text-align: center;
    font-weight: bold;
    margin-bottom: 1rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #6c757d;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin: 0.5rem 0;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
}
.metric-label {
    font-size: 1rem;
    opacity: 0.9;
}
.recommendation-box {
    background-color: #f8f9fa;
    border-left: 5px solid #28a745;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.warning-box {
    background-color: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.schedule-card {
    background-color: #e3f2fd;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #2196f3;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<h1 class="main-header">💪 InBody AI 건강관리 시스템</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">체성분 분석 기반 개인 맞춤형 건강관리 솔루션</p>', unsafe_allow_html=True)
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📤 InBody 분석", "📊 결과 대시보드", "🎯 맞춤 플랜", "ℹ️ 가이드"])
    
    with tab1:
        upload_and_analyze()
    
    with tab2:
        if 'analysis_result' in st.session_state:
            show_dashboard()
        else:
            st.info("👆 먼저 'InBody 분석' 탭에서 결과지를 업로드해주세요.")
    
    with tab3:
        if 'analysis_result' in st.session_state:
            show_personalized_plan()
        else:
            st.info("👆 먼저 'InBody 분석' 탭에서 결과지를 업로드해주세요.")
    
    with tab4:
        show_guide()


def upload_and_analyze():
    """InBody 결과지 업로드 및 분석"""
    st.markdown("### 📋 InBody 결과지 업로드")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("#### ⚙️ 분석 옵션")
        
        user_name = st.text_input("이름", "사용자")
        
        analysis_focus = st.multiselect(
            "분석 초점",
            ["체중 감량", "근육 증가", "체력 향상", "건강 유지"],
            default=["건강 유지"]
        )
        
        exercise_preference = st.selectbox(
            "선호 운동",
            ["유산소", "근력 운동", "복합 운동", "요가/필라테스"]
        )
        
        available_time = st.slider("일일 운동 가능 시간(분)", 0, 180, 60, 30)
    
    with col1:
        uploaded_file = st.file_uploader(
            "InBody 결과지를 업로드하세요",
            type=['jpg', 'jpeg', 'png', 'pdf'],
            help="InBody 측정 결과지 사진을 업로드해주세요"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="업로드된 InBody 결과지", use_container_width=True)
            
            if st.button("🚀 AI 분석 시작", type="primary", use_container_width=True):
                analyze_inbody(
                    uploaded_file,
                    user_name,
                    analysis_focus,
                    exercise_preference,
                    available_time
                )


def analyze_inbody(uploaded_file, user_name, analysis_focus, exercise_preference, available_time):
    """InBody 결과 분석 메인 프로세스"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: 이미지 저장
        status_text.text("💾 이미지 저장 중...")
        progress_bar.progress(15)
        
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Step 2: OCR 처리
        status_text.text("🔍 InBody 데이터 추출 중... (Google Vision API)")
        progress_bar.progress(35)
        
        inbody_data = extract_inbody_data(file_path)
        
        if not inbody_data:
            st.error("❌ 데이터 추출 실패. InBody 결과지가 선명한지 확인해주세요.")
            return
        
        st.success(f"✅ 데이터 추출 완료!")
        with st.expander("🔎 추출된 InBody 데이터"):
            st.json(inbody_data)
        
        # Step 3: AI 분석
        status_text.text("🤖 Perplexity AI로 체성분 분석 중...")
        progress_bar.progress(60)
        
        analysis = analyze_inbody_data(
            inbody_data,
            user_name,
            analysis_focus,
            exercise_preference
        )
        
        if not analysis:
            st.warning("⚠️ AI 분석 실패. Mock 데이터로 진행합니다.")
        
        # Step 4: 하모니서치 최적 일정
        status_text.text("🎯 하모니서치로 최적 일정 생성 중...")
        progress_bar.progress(80)
        
        optimal_schedule = generate_optimal_schedule(
            analysis,
            available_time,
            exercise_preference
        )
        
        # Step 5: 결과 통합
        status_text.text("📊 결과 생성 중...")
        progress_bar.progress(90)
        
        final_result = {
            "user_info": {
                "name": user_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "goals": analysis_focus,
                "exercise_preference": exercise_preference,
                "available_time": available_time
            },
            "inbody_data": inbody_data,
            "ai_analysis": analysis,
            "optimal_schedule": optimal_schedule
        }
        
        st.session_state.analysis_result = final_result
        
        # Step 6: PDF 생성
        status_text.text("📄 PDF 레포트 생성 중...")
        progress_bar.progress(95)
        
        pdf_path = generate_inbody_report(final_result)
        
        progress_bar.progress(100)
        status_text.text("✅ 분석 완료!")
        
        st.balloons()
        st.success("🎉 분석이 완료되었습니다! '결과 대시보드' 탭으로 이동하세요.")
        
        # PDF 다운로드
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📥 건강관리 레포트 다운로드",
                    data=pdf_file,
                    file_name=f"InBody_Report_{user_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
        
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        import traceback
        with st.expander("오류 상세"):
            st.code(traceback.format_exc())


def show_dashboard():
    """결과 대시보드"""
    result = st.session_state.analysis_result
    
    st.markdown("### 📊 InBody 분석 결과")
    
    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    inbody = result['inbody_data']
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">체중</div>
            <div class="metric-value">{inbody.get('weight', 'N/A')} kg</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">체지방률</div>
            <div class="metric-value">{inbody.get('body_fat_percentage', 'N/A')} %</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">골격근량</div>
            <div class="metric-value">{inbody.get('skeletal_muscle_mass', 'N/A')} kg</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">BMI</div>
            <div class="metric-value">{inbody.get('bmi', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # AI 분석 결과
    analysis = result['ai_analysis']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 종합 평가")
        st.markdown(f'<div class="recommendation-box">{analysis.get("overall_assessment", "N/A")}</div>',
                   unsafe_allow_html=True)
        
        st.markdown("#### ⚠️ 주의 사항")
        for concern in analysis.get('health_concerns', []):
            st.markdown(f'<div class="warning-box">• {concern}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 💡 개선 목표")
        for goal in analysis.get('improvement_goals', []):
            st.info(f"🎯 {goal}")
        
        st.markdown("#### 📈 기대 효과")
        st.success(analysis.get('expected_results', 'N/A'))


def show_personalized_plan():
    """맞춤 플랜"""
    result = st.session_state.analysis_result
    schedule = result['optimal_schedule']
    analysis = result['ai_analysis']
    
    st.markdown("### 🎯 개인 맞춤 건강관리 플랜")
    
    # 운동 계획
    st.markdown("#### 🏃 운동 프로그램 (하모니서치 최적화)")
    
    for day in schedule['exercise_plan']:
        st.markdown(f"""
        <div class="schedule-card">
            <h4>📅 {day['day']}</h4>
            <p><strong>운동:</strong> {day['exercise']}</p>
            <p><strong>시간:</strong> {day['duration']}분</p>
            <p><strong>강도:</strong> {day['intensity']}</p>
            <p><strong>목표:</strong> {day['goal']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 식단 계획
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🥗 식단 가이드")
        for meal in analysis.get('diet_recommendations', []):
            st.markdown(f'<div class="recommendation-box">• {meal}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 💊 영양 보충")
        for supplement in analysis.get('supplement_recommendations', []):
            st.markdown(f'<div class="recommendation-box">• {supplement}</div>', unsafe_allow_html=True)
    
    # 일정 요약
    st.markdown("---")
    st.markdown("#### 📆 주간 일정 요약")
    
    summary = schedule['weekly_summary']
    st.info(f"""
**총 운동 시간**: {summary['total_exercise_time']}분/주  
**예상 칼로리 소모**: {summary['estimated_calories']} kcal/주  
**목표 달성 예상 기간**: {summary['goal_timeframe']}
    """)


def show_guide():
    """가이드"""
    st.markdown("""
## 📖 시스템 사용 가이드

### 🎯 시스템 개요
이 시스템은 InBody 체성분 분석 결과를 기반으로 AI가 개인 맞춤형 건강관리 플랜을 제공합니다.

### 📋 사용 방법

1. **InBody 결과지 촬영** - 모든 수치가 선명하게 보이도록
2. **업로드 및 설정** - 이름, 목표, 선호 운동 입력
3. **AI 분석** - 자동으로 체성분 분석 및 건강 평가
4. **최적 플랜** - 하모니서치 알고리즘이 맞춤 일정 생성
5. **실행** - PDF 다운로드 후 계획 실천

### 🔬 핵심 기술

- **OCR**: Google Cloud Vision API
- **AI 분석**: Perplexity AI
- **최적화**: Harmony Search Algorithm

### ⚠️ 주의사항

- 본 시스템은 참고용이며 의료 진단을 대체하지 않습니다
- 건강 문제 시 반드시 전문의 상담 필요

### 📞 문의사항

시스템 사용 중 문제가 발생하면 개발팀에 문의해주세요.
    """)


if __name__ == "__main__":
    main()