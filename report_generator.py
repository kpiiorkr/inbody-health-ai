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
    
    def header(self):
        """페이지 헤더"""
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
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
    
    def add_text(self, text: str, indent=0):
        """본문 텍스트 추가 (한글 제거)"""
        self.set_font('Arial', '', 10)
        if indent > 0:
            self.cell(indent)
        
        # 한글 제거 및 영문으로 변환
        safe_text = self._make_safe_text(text)
        self.multi_cell(0, 6, safe_text)
    
    def _make_safe_text(self, text: str) -> str:
        """한글을 영문으로 안전하게 변환"""
        # ASCII가 아닌 문자는 제거하되 기본 정보는 유지
        try:
            return text.encode('ascii', 'ignore').decode('ascii')
        except:
            return "[Korean text - See web interface]"
    
    def add_section_header(self, text: str):
        """섹션 헤더 추가"""
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 250)
        safe_text = self._make_safe_text(text)
        self.cell(0, 8, safe_text, 0, 1, 'L', True)
        self.ln(3)
    
    def add_metric_box(self, label: str, value: str, unit: str = ''):
        """측정값 박스 추가"""
        self.set_font('Arial', '', 10)
        # 라벨
        self.cell(50, 8, label, 1, 0, 'C')
        # 값
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, f'{value} {unit}', 1, 1, 'C')
    
    def add_bullet_list(self, items: list):
        """불릿 리스트 추가"""
        for item in items:
            self.set_font('Arial', '', 10)
            self.cell(5)
            self.cell(5, 6, '-', 0, 0)
            safe_text = self._make_safe_text(item)
            if not safe_text.strip():
                safe_text = "[Korean content - Please check web interface]"
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
        # 한글 이름은 영문으로 표시
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
        pdf.add_text("Please check the web interface for detailed Korean analysis.")
        pdf.add_text(f"Assessment length: {len(analysis.get('overall_assessment', ''))} characters")
        
        # 4. 주의 사항
        pdf.add_section_header('4. Health Concerns')
        concerns = analysis.get('health_concerns', [])
        pdf.add_text(f"Number of concerns identified: {len(concerns)}")
        pdf.add_bullet_list([f"Concern {i+1}" for i in range(len(concerns))])
        
        # 5. 개선 목표
        pdf.add_section_header('5. Improvement Goals')
        goals = analysis.get('improvement_goals', [])
        pdf.add_text(f"Number of goals set: {len(goals)}")
        pdf.add_bullet_list([f"Goal {i+1}" for i in range(len(goals))])
        
        # 6. 운동 계획
        pdf.add_section_header('6. Weekly Exercise Plan')
        exercise_plan = schedule.get('exercise_plan', [])
        days_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day_plan in enumerate(exercise_plan[:7]):
            day = days_en[i]
            duration = day_plan['duration']
            intensity = day_plan['intensity']
            pdf.add_text(f"{day}: {duration} min, Intensity: {intensity}")
        
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
        pdf.add_text(f"Number of diet recommendations: {len(diet)}")
        
        # 9. 영양 보충
        pdf.add_section_header('9. Supplement Recommendations')
        supplements = analysis.get('supplement_recommendations', [])
        pdf.add_text(f"Number of supplements recommended: {len(supplements)}")
        
        # 면책 조항
        pdf.add_section_header('Disclaimer')
        pdf.set_font('Arial', 'I', 8)
        pdf.multi_cell(0, 5,
            "This report is for reference purposes only and does not replace "
            "professional medical advice. Please consult with healthcare professionals "
            "for any health concerns. For detailed Korean content, please check the web interface.")
        
        # 한글 컨텐츠 안내
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, "IMPORTANT NOTICE", 0, 1, 'C')
        pdf.set_font('Arial', '', 9)
        pdf.multi_cell(0, 5,
            "This PDF contains summary information in English. "
            "For complete Korean content including detailed recommendations, "
            "exercise plans, and dietary guidelines, please visit the web interface at: "
            "https://inbody-health-ai.streamlit.app/")
        
        # PDF 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"InBody_Report_{timestamp}.pdf"
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
            "name": "Test User",
            "analysis_date": "2024-01-15 10:30",
            "goals": ["Weight Loss", "Health Maintenance"],
            "exercise_preference": "Complex Exercise",
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
            "overall_assessment": "Overall good condition",
            "health_concerns": ["Body fat management needed", "Muscle increase recommended"],
            "improvement_goals": ["Exercise 3 times a week", "Increase protein intake"],
            "diet_recommendations": ["High protein diet", "Increase vegetable intake"],
            "supplement_recommendations": ["Multivitamin", "Omega-3"],
            "expected_results": "Improvement expected in 8-12 weeks"
        },
        "optimal_schedule": {
            "exercise_plan": [
                {"day": "Monday", "exercise": "Running", "duration": 60, "intensity": "Medium", "goal": "Improve fitness"},
                {"day": "Tuesday", "exercise": "Rest", "duration": 0, "intensity": "None", "goal": "Recovery"},
            ],
            "weekly_summary": {
                "total_exercise_time": 180,
                "estimated_calories": 1500,
                "workout_days": 3,
                "goal_timeframe": "8-10 weeks"
            }
        }
    }
    
    pdf_path = generate_inbody_report(test_result)
    if pdf_path:
        print(f"✅ Test PDF created: {pdf_path}")