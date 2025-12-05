"""
AI 건강 분석 모듈
Perplexity AI를 사용하여 InBody 데이터 분석 및 건강 조언 생성
"""
import requests
from typing import Dict, List, Optional
from secrets_manager import SecretsManager

# Secrets 관리
try:
    from secrets_manager import get_secret
    PERPLEXITY_API_KEY = get_secret("PERPLEXITY_API_KEY")
except:
    import os
    api_key = SecretsManager.get_perplexity_api_key()
    if not api_key:
        st.warning("⚠️ Perplexity API 키 미설정. Mock 데이터 사용")

def analyze_inbody_data(
    inbody_data: Dict,
    user_name: str,
    analysis_focus: List[str],
    exercise_preference: str
) -> Optional[Dict]:
    """
    Perplexity AI로 InBody 데이터 분석
    
    Args:
        inbody_data: OCR로 추출된 InBody 데이터
        user_name: 사용자 이름
        analysis_focus: 분석 초점 리스트
        exercise_preference: 선호 운동 타입
    
    Returns:
        AI 분석 결과 딕셔너리
    """
    
    try:
        # Perplexity AI 프롬프트 생성
        prompt = create_analysis_prompt(inbody_data, user_name, analysis_focus, exercise_preference)
        
        # API 호출
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 전문 건강 트레이너이자 영양사입니다. InBody 체성분 분석 결과를 바탕으로 과학적이고 실용적인 건강 조언을 제공합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        
        # AI 응답을 구조화된 데이터로 파싱
        return parse_ai_response(ai_response, inbody_data)
        
    except Exception as e:
        print(f"❌ AI 분석 오류: {str(e)}")
        print("⚠️ Mock 데이터를 사용합니다.")
        return generate_mock_analysis(inbody_data, user_name, analysis_focus)


def create_analysis_prompt(
    inbody_data: Dict,
    user_name: str,
    analysis_focus: List[str],
    exercise_preference: str
) -> str:
    """AI 분석 프롬프트 생성"""
    
    prompt = f"""
다음은 {user_name}님의 InBody 체성분 분석 결과입니다:

📊 측정 데이터:
- 체중: {inbody_data.get('weight', 'N/A')} kg
- 체지방률: {inbody_data.get('body_fat_percentage', 'N/A')} %
- 골격근량: {inbody_data.get('skeletal_muscle_mass', 'N/A')} kg
- BMI: {inbody_data.get('bmi', 'N/A')}
- 체지방량: {inbody_data.get('body_fat_mass', 'N/A')} kg
- 기초대사량: {inbody_data.get('bmr', 'N/A')} kcal

🎯 분석 목표: {', '.join(analysis_focus)}
💪 선호 운동: {exercise_preference}

다음 항목들을 포함하여 분석해주세요:

1. **종합 평가** (2-3문장): 현재 체성분 상태에 대한 전체적인 평가
2. **주의 사항** (3-5개): 개선이 필요한 부분이나 건강상 주의할 점
3. **개선 목표** (3-5개): 구체적이고 달성 가능한 목표
4. **식단 가이드** (5-7개): 실천 가능한 식단 조언
5. **영양 보충** (3-5개): 필요한 영양소나 보충제
6. **기대 효과** (2-3문장): 계획을 잘 따를 경우 예상되는 결과

각 항목은 실용적이고 과학적 근거가 있어야 하며, {user_name}님의 목표({', '.join(analysis_focus)})에 맞춰 작성해주세요.
"""
    
    return prompt


def parse_ai_response(ai_response: str, inbody_data: Dict) -> Dict:
    """AI 응답을 구조화된 데이터로 파싱"""
    
    lines = ai_response.split('\n')
    
    analysis = {
        "overall_assessment": "",
        "health_concerns": [],
        "improvement_goals": [],
        "diet_recommendations": [],
        "supplement_recommendations": [],
        "expected_results": ""
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 섹션 감지
        if "종합 평가" in line or "종합평가" in line or "Overall" in line.lower():
            current_section = "overall"
        elif "주의" in line or "Concern" in line.lower() or "위험" in line:
            current_section = "concerns"
        elif "목표" in line or "Goal" in line.lower() or "개선" in line:
            current_section = "goals"
        elif "식단" in line or "Diet" in line.lower() or "영양" in line:
            current_section = "diet"
        elif "보충" in line or "Supplement" in line.lower():
            current_section = "supplements"
        elif "기대" in line or "Expected" in line.lower() or "효과" in line:
            current_section = "expected"
        
        # 데이터 추가
        elif line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.')):
            cleaned_line = line.lstrip('-•*123456789. ').strip()
            if len(cleaned_line) > 5:
                if current_section == "concerns":
                    analysis["health_concerns"].append(cleaned_line)
                elif current_section == "goals":
                    analysis["improvement_goals"].append(cleaned_line)
                elif current_section == "diet":
                    analysis["diet_recommendations"].append(cleaned_line)
                elif current_section == "supplements":
                    analysis["supplement_recommendations"].append(cleaned_line)
        elif current_section == "overall" and len(line) > 20:
            if analysis["overall_assessment"]:
                analysis["overall_assessment"] += " "
            analysis["overall_assessment"] += line
        elif current_section == "expected" and len(line) > 20:
            if analysis["expected_results"]:
                analysis["expected_results"] += " "
            analysis["expected_results"] += line
    
    # 데이터가 비어있으면 전체 응답을 종합 평가로 사용
    if not analysis["overall_assessment"]:
        analysis["overall_assessment"] = ai_response[:500] if len(ai_response) > 500 else ai_response
    
    if not analysis["health_concerns"]:
        analysis["health_concerns"] = ["체성분 분석 결과를 정기적으로 확인하세요"]
    
    if not analysis["improvement_goals"]:
        analysis["improvement_goals"] = ["건강한 생활 습관 유지", "규칙적인 운동", "균형잡힌 식단"]
    
    if not analysis["diet_recommendations"]:
        analysis["diet_recommendations"] = ["단백질 섭취 증가", "가공식품 줄이기", "충분한 수분 섭취"]
    
    if not analysis["supplement_recommendations"]:
        analysis["supplement_recommendations"] = ["종합 비타민", "오메가-3"]
    
    if not analysis["expected_results"]:
        analysis["expected_results"] = "꾸준한 실천으로 건강한 체성분 구성을 기대할 수 있습니다."
    
    return analysis


def generate_mock_analysis(inbody_data: Dict, user_name: str, analysis_focus: List[str]) -> Dict:
    """Mock AI 분석 데이터 생성 (API 오류시 사용)"""
    
    weight = inbody_data.get('weight', 70)
    body_fat = inbody_data.get('body_fat_percentage', 20)
    bmi = inbody_data.get('bmi', 23)
    muscle = inbody_data.get('skeletal_muscle_mass', 30)
    
    # BMI 기반 평가
    if isinstance(bmi, (int, float)):
        if bmi < 18.5:
            bmi_status = "저체중"
        elif bmi < 23:
            bmi_status = "정상"
        elif bmi < 25:
            bmi_status = "과체중"
        else:
            bmi_status = "비만"
    else:
        bmi_status = "정상"
    
    # 체지방률 기반 평가
    if isinstance(body_fat, (int, float)):
        if body_fat < 15:
            fat_status = "낮음"
        elif body_fat < 25:
            fat_status = "정상"
        else:
            fat_status = "높음"
    else:
        fat_status = "정상"
    
    return {
        "overall_assessment": f"{user_name}님의 체성분 분석 결과, BMI는 {bmi_status} 범위이며 체지방률은 {fat_status} 수준입니다. 전반적으로 {'건강한' if fat_status == '정상' else '개선이 필요한'} 상태로 평가됩니다. {', '.join(analysis_focus)} 목표를 위해 맞춤형 운동과 식단 관리가 필요합니다.",
        
        "health_concerns": [
            f"체지방률이 {body_fat}%로 {'관리가 필요합니다' if isinstance(body_fat, (int, float)) and body_fat > 25 else '양호합니다'}",
            "규칙적인 운동 습관 확립이 중요합니다",
            "충분한 수분 섭취와 수면이 필요합니다",
            "스트레스 관리에 주의하세요"
        ],
        
        "improvement_goals": [
            f"{'체중 감량' if '체중 감량' in analysis_focus else '체중 유지'}: 주 0.5-1kg 목표",
            f"{'근육량 증가' if '근육 증가' in analysis_focus else '근육량 유지'}: 골격근량 {muscle}kg에서 증가",
            "체지방률 건강 범위로 조정",
            "기초대사량 증가를 통한 건강한 체질 개선",
            "규칙적인 운동 습관 형성"
        ],
        
        "diet_recommendations": [
            "고단백 저지방 식단: 닭가슴살, 생선, 두부, 계란 흰자",
            "복합 탄수화물: 현미, 귀리, 고구마, 통밀",
            "신선한 채소와 과일 충분히 섭취",
            "하루 물 2L 이상 섭취",
            "가공식품과 당분 섭취 최소화",
            "식사 시간 규칙적으로 유지",
            "간식은 견과류나 과일로 대체"
        ],
        
        "supplement_recommendations": [
            "종합 비타민: 일일 영양소 보충",
            "오메가-3: 심혈관 건강 및 염증 관리",
            "프로틴 파우더: 운동 후 근육 회복 (선택사항)",
            "비타민 D: 골격 건강 및 면역력",
            "마그네슘: 근육 이완 및 수면 개선"
        ],
        
        "expected_results": f"제시된 운동과 식단 계획을 8-12주간 꾸준히 실천할 경우, {'체지방 감소와 근육량 증가' if '체중 감량' in analysis_focus or '근육 증가' in analysis_focus else '건강한 체성분 유지'}를 기대할 수 있습니다. 기초대사량이 증가하고 전반적인 체력과 건강 지표가 개선될 것입니다."
    }


if __name__ == "__main__":
    # 테스트 코드
    test_data = {
        "weight": 75,
        "body_fat_percentage": 22,
        "skeletal_muscle_mass": 32,
        "bmi": 24.5,
        "body_fat_mass": 16.5,
        "bmr": 1650
    }
    
    result = analyze_inbody_data(
        test_data,
        "테스트",
        ["체중 감량", "건강 유지"],
        "복합 운동"
    )
    
    print("✅ AI 분석 완료:")
    print(f"종합 평가: {result['overall_assessment'][:100]}...")
    print(f"주의 사항: {len(result['health_concerns'])}개")
    print(f"개선 목표: {len(result['improvement_goals'])}개")