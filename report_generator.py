"""
PDF 건강관리 레포트 생성 모듈
InBody 분석 결과와 운동 계획을 PDF로 출력
"""
from fpdf import FPDF
from datetime import datetime
from typing import Dict
import os


class HealthReportPDF(FPDF):
    """건강 레포트 PDF 생성 클래스"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        # 한글 폰트 설정 시도 (없으면 기본 폰트 사용)
        self.font_available = self._setup_korean_font()
    
    def _setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            # Windows 기본 한글 폰트 경로
            font_paths = [
                'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
                'C:/Windows/Fonts/gulim.ttc',   # 굴림
                '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # Mac
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.add_font('Korean', '', font_path, uni=True)
                    return True
            
            return False
        except Exception as e:
            print(f"⚠️ 한글 폰트 로드 실패: {e}")
            return False
    
    def header(self):
        """페이지 헤더"""
        if self.font_available:
            self.set_font('Korean', '', 16)
            self.cell(0, 10, 'InBody AI Health Report', 0, 1, 'C')
        else:
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'InBody AI Health Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """페이지 푸터"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def add_title(self, title: str):
        """제목 추가"""
        if self.font_available:
            self.set_font('Korean', '', 14)
        else:
            self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
    
    def add_text(self, text: str, indent=0):
        """본문 텍스트 추가"""
        if self.font_available:
            self.set_font('Korean', '', 10)
        else:
            self.set_font('Arial', '', 10)
        
        if indent > 0:
            self.cell(indent)
        
        # 긴 텍스트는 여러 줄로 분할
        self.multi_cell(0, 6, text)
    
    def add_section_header(self, text: str):
        """섹션 헤더 추가"""
        self.ln(5)
        if self.font_available:
            self.set_font('Korean', '', 12)
        else:
            self.set_font('Arial', 'B', 12)
        
        self.set_fill_color(230, 230, 250)
        self.cell(0, 8, text, 0, 1, 'L', True)
        self.ln(3)
    
    def add_metric_box(self, label: str, value: str, unit: str = ''):
        """측정값 박스 추가"""
        if self.font_available:
            self.set_font('Korean', '', 10)
        else:
            self.set_font('Arial', '', 10)
        
        # 라벨
        self.cell(50, 8, label, 1, 0, 'C')
        # 값
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, f'{value} {unit}', 1, 1, 'C')
    
    def add_bullet_list(self, items: list):
        """불릿 리스트 추가"""
        for item in items:
            if self.font_available:
                self.set_font('Korean', '', 10)
                self.cell(5)
                self.cell(5, 6, '•', 0, 0)
                self.multi_cell(0, 6, item)
            else:
                self.set_font('Arial', '', 10)
                self.cell(5)
                self.cell(5, 6, '-', 0, 0)
                # 한글이 포함된 경우 ASCII로 변환하거나 제거
                safe_text = item.encode('ascii', 'ignore').decode('ascii')
                if not safe_text.strip():
                    safe_text = "[Korean text]"
                self.multi_cell(0, 6, safe_text)


def generate_inbody_report(result: Dict) -> str:
    """
    InBody 분석 결과로 PDF 레포트 생성
    
    Args:
        result: 전체 분석 결과 딕셔너리
    
    Returns:
        생성된 PDF 파일 경로
    """
    try:
        pdf = HealthReportPDF()
        pdf.add_page()
        
        user_info = result['user_info']
        inbody_data = result['inbody_data']
        analysis = result['ai_analysis']
        schedule = result['optimal_schedule']
        
        # 1. 사용자 정보
        pdf.add_section_header('1. User Information')
        pdf.add_text(f"Name: {user_info['name']}")
        pdf.add_text(f"Analysis Date: {user_info['analysis_date']}")
        pdf.add_text(f"Goals: {', '.join(user_info['goals'])}")
        pdf.add_text(f"Preferred Exercise: {user_info['exercise_preference']}")
        pdf.add_text(f"Available Time: {user_info['available_time']} min/day")
        
        # 2. InBody 측정 결과
        pdf.add_section_header('2. InBody Measurement Results')
        pdf.add_metric_box('Weight', str(inbody_data.get('weight', 'N/A')), 'kg')
        pdf.add_metric_box('Body Fat %', str(inbody_data.get('body_fat_percentage', 'N/A')), '%')
        pdf.add_metric_box('Skeletal Muscle', str(inbody_data.get('skeletal_muscle_mass', 'N/A')), 'kg')
        pdf.add_metric_box('BMI', str(inbody_data.get('bmi', 'N/A')), '')
        pdf.add_metric_box('Body Fat Mass', str(inbody_data.get('body_fat_mass', 'N/A')), 'kg')
        pdf.add_metric_box('BMR', str(inbody_data.get('bmr', 'N/A')), 'kcal')
        
        # 3. AI 종합 평가
        pdf.add_section_header('3. Overall Assessment')
        assessment_text = analysis.get('overall_assessment', 'N/A')
        if pdf.font_available:
            pdf.add_text(assessment_text)
        else:
            # 한글 폰트 없으면 영문으로 대체
            pdf.add_text("AI analysis completed. Please check the web interface for detailed Korean text.")
        
        # 4. 주의 사항
        pdf.add_section_header('4. Health Concerns')
        concerns = analysis.get('health_concerns', [])
        if pdf.font_available:
            pdf.add_bullet_list(concerns)
        else:
            pdf.add_text(f"Number of concerns identified: {len(concerns)}")
        
        # 5. 개선 목표
        pdf.add_section_header('5. Improvement Goals')
        goals = analysis.get('improvement_goals', [])
        if pdf.font_available:
            pdf.add_bullet_list(goals)
        else:
            pdf.add_text(f"Number of goals set: {len(goals)}")
        
        # 6. 운동 계획
        pdf.add_section_header('6. Weekly Exercise Plan')
        exercise_plan = schedule.get('exercise_plan', [])
        
        for day_plan in exercise_plan:
            day = day_plan['day']
            exercise = day_plan['exercise']
            duration = day_plan['duration']
            intensity = day_plan['intensity']
            
            if pdf.font_available:
                pdf.add_text(f"{day}: {exercise} ({duration} min, {intensity})")
            else:
                # 영문으로 변환
                day_en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][exercise_plan.index(day_plan)]
                pdf.add_text(f"{day_en}: {duration} min, Intensity: {intensity}")
        
        # 7. 주간 요약
        pdf.add_section_header('7. Weekly Summary')
        summary = schedule.get('weekly_summary', {})
        pdf.add_text(f"Total Exercise Time: {summary.get('total_exercise_time', 0)} min/week")
        pdf.add_text(f"Estimated Calories: {summary.get('estimated_calories', 0)} kcal/week")
        pdf.add_text(f"Workout Days: {summary.get('workout_days', 0)} days/week")
        pdf.add_text(f"Goal Timeframe: {summary.get('goal_timeframe', 'N/A')}")
        
        # 8. 식단 가이드
        pdf.add_section_header('8. Diet Recommendations')
        diet = analysis.get('diet_recommendations', [])
        if pdf.font_available:
            pdf.add_bullet_list(diet[:5])  # 상위 5개만
        else:
            pdf.add_text(f"Number of diet recommendations: {len(diet)}")
        
        # 9. 영양 보충
        pdf.add_section_header('9. Supplement Recommendations')
        supplements = analysis.get('supplement_recommendations', [])
        if pdf.font_available:
            pdf.add_bullet_list(supplements)
        else:
            pdf.add_text(f"Number of supplements recommended: {len(supplements)}")
        
        # 10. 기대 효과
        pdf.add_section_header('10. Expected Results')
        expected = analysis.get('expected_results', 'N/A')
        if pdf.font_available:
            pdf.add_text(expected)
        else:
            pdf.add_text("Please check the web interface for detailed results in Korean.")
        
        # 면책 조항
        pdf.add_section_header('Disclaimer')
        pdf.set_font('Arial', 'I', 8)
        pdf.multi_cell(0, 5, 
            "This report is for reference purposes only and does not replace professional medical advice. "
            "Please consult with healthcare professionals for any health concerns.")
        
        # PDF 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"InBody_Report_{user_info['name']}_{timestamp}.pdf"
        filepath = f"results/{filename}"
        
        # results 폴더가 없으면 생성
        os.makedirs('results', exist_ok=True)
        
        pdf.output(filepath)
        print(f"✅ PDF 레포트 생성 완료: {filepath}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ PDF 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 테스트 코드
    test_result = {
        "user_info": {
            "name": "테스트",
            "analysis_date": "2024-01-15 10:30",
            "goals": ["체중 감량", "건강 유지"],
            "exercise_preference": "복합 운동",
            "available_time": 60
        },
        "inbody_data": {
            "weight": 75,
            "body_fat_percentage": 22,
            "skeletal_muscle_mass": 32,
            "bmi": 24.5,
            "body_fat_mass": 16.5,
            "bmr": 1650
        },
        "ai_analysis": {
            "overall_assessment": "전반적으로 양호한 상태입니다.",
            "health_concerns": ["체지방률 관리 필요", "근육량 증가 권장"],
            "improvement_goals": ["주 3회 운동", "단백질 섭취 증가"],
            "diet_recommendations": ["고단백 식단", "채소 섭취 증가"],
            "supplement_recommendations": ["종합 비타민", "오메가-3"],
            "expected_results": "8-12주 후 개선 예상"
        },
        "optimal_schedule": {
            "exercise_plan": [
                {"day": "월요일", "exercise": "러닝", "duration": 60, "intensity": "중간", "goal": "체력 향상"},
                {"day": "화요일", "exercise": "휴식", "duration": 0, "intensity": "없음", "goal": "회복"},
            ],
            "weekly_summary": {
                "total_exercise_time": 180,
                "estimated_calories": 1500,
                "workout_days": 3,
                "goal_timeframe": "8-10주"
            }
        }
    }
    
    pdf_path = generate_inbody_report(test_result)
    if pdf_path:
        print(f"✅ 테스트 PDF 생성: {pdf_path}")