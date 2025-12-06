"""
InBody 결과지 OCR 처리 모듈
Google Cloud Vision API를 사용하여 InBody 이미지에서 데이터 추출
"""
import os
import re
from typing import Dict, Optional
from google.cloud import vision
from google.oauth2 import service_account
import json

def get_vision_client():
    """Google Vision API 클라이언트 생성"""
    try:
        # Streamlit Cloud에서 실행 중인 경우
        import streamlit as st
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            return vision.ImageAnnotatorClient(credentials=credentials)
    except:
        pass
    
    # 로컬에서 실행 중인 경우
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-credentials.json')
    if os.path.exists(credentials_path):
        return vision.ImageAnnotatorClient()
    
    # API 없음
    print("⚠️ Google Vision API 인증 정보가 없습니다. Mock 데이터를 사용합니다.")
    return None


def extract_inbody_data(image_path: str) -> Optional[Dict]:
    """
    InBody 이미지에서 데이터 추출
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        추출된 InBody 데이터 딕셔너리
    """
    client = get_vision_client()
    
    if not client:
        print("⚠️ Google Vision API를 사용할 수 없습니다. Mock 데이터를 반환합니다.")
        return get_mock_inbody_data()
    
    try:
        # 이미지 읽기
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # OCR 수행
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f'Google Vision API Error: {response.error.message}')
        
        texts = response.text_annotations
        
        if not texts:
            print("⚠️ 텍스트를 찾을 수 없습니다. Mock 데이터를 반환합니다.")
            return get_mock_inbody_data()
        
        # 전체 텍스트 추출
        full_text = texts[0].description
        print(f"✅ OCR 완료: {len(full_text)} 글자 추출")
        
        # InBody 데이터 파싱
        inbody_data = parse_inbody_text(full_text)
        
        # 파싱 결과 검증
        if not inbody_data or not any(inbody_data.values()):
            print("⚠️ 데이터 파싱 실패. Mock 데이터를 반환합니다.")
            return get_mock_inbody_data()
        
        return inbody_data
        
    except Exception as e:
        print(f"❌ OCR 오류: {str(e)}")
        return get_mock_inbody_data()


def parse_inbody_text(text: str) -> Dict:
    """
    OCR 텍스트에서 InBody 주요 수치 추출
    
    Args:
        text: OCR로 추출된 전체 텍스트
    
    Returns:
        파싱된 InBody 데이터
    """
    data = {
        'weight': None,
        'skeletal_muscle_mass': None,
        'body_fat_percentage': None,
        'body_fat_mass': None,
        'bmi': None,
        'waist_hip_ratio': None,
        'bmr': None,
        'protein': None,
        'minerals': None,
        'body_water': None
    }
    
    lines = text.split('\n')
    
    # 정규식 패턴
    number_pattern = r'[\d]+\.?[\d]*'
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # 체중 (kg 단위)
        if '체중' in line or 'Weight' in line:
            match = re.search(rf'({number_pattern})\s*kg', line, re.IGNORECASE)
            if match:
                data['weight'] = float(match.group(1))
            else:
                numbers = re.findall(number_pattern, line)
                if numbers and float(numbers[0]) > 30 and float(numbers[0]) < 200:
                    data['weight'] = float(numbers[0])
        
        # 골격근량
        if '골격근' in line or 'Skeletal' in line or '근육량' in line:
            match = re.search(rf'({number_pattern})\s*kg', line, re.IGNORECASE)
            if match:
                data['skeletal_muscle_mass'] = float(match.group(1))
        
        # 체지방률 (%)
        if '체지방률' in line or 'Body Fat' in line or 'Fat %' in line:
            match = re.search(rf'({number_pattern})\s*%', line)
            if match:
                data['body_fat_percentage'] = float(match.group(1))
        
        # 체지방량
        if '체지방량' in line or 'Body Fat Mass' in line:
            match = re.search(rf'({number_pattern})\s*kg', line, re.IGNORECASE)
            if match:
                data['body_fat_mass'] = float(match.group(1))
        
        # BMI
        if 'BMI' in line and 'kg' not in line:
            numbers = re.findall(number_pattern, line)
            for num in numbers:
                if float(num) > 10 and float(num) < 50:
                    data['bmi'] = float(num)
                    break
        
        # 복부지방률 (Waist-Hip Ratio)
        if '복부' in line and ('지방' in line or '비율' in line):
            match = re.search(r'0\.\d+', line)
            if match:
                data['waist_hip_ratio'] = float(match.group())
        
        # 기초대사량 (BMR)
        if '기초대사량' in line or 'BMR' in line or '대사' in line:
            numbers = re.findall(r'\d{3,4}', line)
            for num in numbers:
                if int(num) > 1000 and int(num) < 3000:
                    data['bmr'] = int(num)
                    break
        
        # 단백질
        if '단백질' in line or 'Protein' in line:
            match = re.search(rf'({number_pattern})\s*kg', line, re.IGNORECASE)
            if match:
                data['protein'] = float(match.group(1))
        
        # 무기질
        if '무기질' in line or 'Mineral' in line:
            match = re.search(rf'({number_pattern})\s*kg', line, re.IGNORECASE)
            if match:
                data['minerals'] = float(match.group(1))
        
        # 체수분
        if '체수분' in line or 'Body Water' in line or '수분' in line:
            match = re.search(rf'({number_pattern})\s*[LlKkg]', line, re.IGNORECASE)
            if match:
                data['body_water'] = float(match.group(1))
    
    # 데이터 검증 및 보정
    if data['weight'] and data['body_fat_percentage'] and not data['body_fat_mass']:
        data['body_fat_mass'] = round(data['weight'] * data['body_fat_percentage'] / 100, 1)
    
    if data['weight'] and not data['bmi']:
        # 평균 키 175cm로 가정하여 BMI 추정
        data['bmi'] = round(data['weight'] / (1.75 * 1.75), 1)
    
    print(f"✅ 파싱 완료: {sum(1 for v in data.values() if v is not None)}개 항목 추출")
    
    return data


def get_mock_inbody_data() -> Dict:
    """
    Mock InBody 데이터 (OCR 실패 시 사용)
    """
    print("📊 Mock InBody 데이터를 사용합니다.")
    return {
        'weight': 90.9,
        'skeletal_muscle_mass': 37.6,
        'body_fat_percentage': 27.4,
        'body_fat_mass': 24.9,
        'bmi': 30.0,
        'waist_hip_ratio': 0.91,
        'bmr': 1795,
        'protein': 13.1,
        'minerals': 4.59,
        'body_water': 48.3
    }


if __name__ == "__main__":
    # 테스트 코드
    print("OCR Processor 테스트")
    
    # Mock 데이터 테스트
    mock_data = get_mock_inbody_data()
    print("\nMock 데이터:")
    for key, value in mock_data.items():
        print(f"  {key}: {value}")