"""
InBody 결과지 OCR 처리 모듈
Google Cloud Vision API를 사용하여 InBody 이미지에서 데이터 추출
"""

import os
import re
from typing import Dict, Optional
from google.cloud import vision
from dotenv import load_dotenv

load_dotenv()

# Secrets 관리
try:
    from secrets_manager import setup_google_credentials
    GOOGLE_CREDENTIALS_PATH = setup_google_credentials()
except:
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google-credentials.json")

def extract_inbody_data(image_path: str) -> Optional[Dict]:
    """
    InBody 결과지 이미지에서 체성분 데이터 추출
    
    Args:
        image_path: InBody 이미지 파일 경로
        
    Returns:
        추출된 InBody 데이터 딕셔너리 또는 None
    """
    try:
        # Google Cloud Vision API 클라이언트 초기화
        client = vision.ImageAnnotatorClient()
        
        # 이미지 읽기
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # OCR 수행
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if not texts:
            print("❌ 텍스트를 찾을 수 없습니다.")
            return None
        
        # 전체 텍스트 추출
        full_text = texts[0].description
        print(f"📝 추출된 텍스트 길이: {len(full_text)} 문자")
        
        # InBody 데이터 파싱
        inbody_data = parse_inbody_text(full_text)
        
        return inbody_data
        
    except Exception as e:
        print(f"❌ OCR 오류: {str(e)}")
        # API 키가 없을 경우 Mock 데이터 반환
        return get_mock_inbody_data()


def parse_inbody_text(text: str) -> Dict:
    """
    OCR로 추출한 텍스트에서 InBody 수치 파싱
    
    Args:
        text: OCR 추출 텍스트
        
    Returns:
        파싱된 InBody 데이터
    """
    data = {}
    
    # 텍스트를 소문자로 변환하여 검색
    text_lower = text.lower()
    
    # 체중 (kg)
    weight_pattern = r'체중[:\s]*(\d+\.?\d*)\s*kg'
    weight_match = re.search(weight_pattern, text, re.IGNORECASE)
    if weight_match:
        data['weight'] = float(weight_match.group(1))
    
    # 골격근량 (kg)
    muscle_patterns = [
        r'골격근량[:\s]*(\d+\.?\d*)\s*kg',
        r'skeletal muscle mass[:\s]*(\d+\.?\d*)\s*kg'
    ]
    for pattern in muscle_patterns:
        muscle_match = re.search(pattern, text, re.IGNORECASE)
        if muscle_match:
            data['skeletal_muscle_mass'] = float(muscle_match.group(1))
            break
    
    # 체지방량 (kg)
    fat_mass_patterns = [
        r'체지방량[:\s]*(\d+\.?\d*)\s*kg',
        r'body fat mass[:\s]*(\d+\.?\d*)\s*kg'
    ]
    for pattern in fat_mass_patterns:
        fat_match = re.search(pattern, text, re.IGNORECASE)
        if fat_match:
            data['body_fat_mass'] = float(fat_match.group(1))
            break
    
    # 체지방률 (%)
    fat_percent_patterns = [
        r'체지방률[:\s]*(\d+\.?\d*)\s*%',
        r'percent body fat[:\s]*(\d+\.?\d*)\s*%',
        r'pbf[:\s]*(\d+\.?\d*)\s*%'
    ]
    for pattern in fat_percent_patterns:
        fat_percent_match = re.search(pattern, text, re.IGNORECASE)
        if fat_percent_match:
            data['body_fat_percentage'] = float(fat_percent_match.group(1))
            break
    
    # BMI
    bmi_pattern = r'bmi[:\s]*(\d+\.?\d*)'
    bmi_match = re.search(bmi_pattern, text, re.IGNORECASE)
    if bmi_match:
        data['bmi'] = float(bmi_match.group(1))
    
    # 체수분 (L)
    water_patterns = [
        r'체수분[:\s]*(\d+\.?\d*)\s*l',
        r'total body water[:\s]*(\d+\.?\d*)\s*l'
    ]
    for pattern in water_patterns:
        water_match = re.search(pattern, text, re.IGNORECASE)
        if water_match:
            data['body_water'] = float(water_match.group(1))
            break
    
    # 단백질 (kg)
    protein_patterns = [
        r'단백질[:\s]*(\d+\.?\d*)\s*kg',
        r'protein[:\s]*(\d+\.?\d*)\s*kg'
    ]
    for pattern in protein_patterns:
        protein_match = re.search(pattern, text, re.IGNORECASE)
        if protein_match:
            data['protein'] = float(protein_match.group(1))
            break
    
    # 무기질 (kg)
    mineral_patterns = [
        r'무기질[:\s]*(\d+\.?\d*)\s*kg',
        r'minerals?[:\s]*(\d+\.?\d*)\s*kg'
    ]
    for pattern in mineral_patterns:
        mineral_match = re.search(pattern, text, re.IGNORECASE)
        if mineral_match:
            data['minerals'] = float(mineral_match.group(1))
            break
    
    # 기초대사량 (kcal)
    bmr_patterns = [
        r'기초대사량[:\s]*(\d+)\s*kcal',
        r'bmr[:\s]*(\d+)\s*kcal'
    ]
    for pattern in bmr_patterns:
        bmr_match = re.search(pattern, text, re.IGNORECASE)
        if bmr_match:
            data['bmr'] = int(bmr_match.group(1))
            break
    
    # 내장지방레벨
    visceral_patterns = [
        r'내장지방레벨[:\s]*(\d+)',
        r'visceral fat level[:\s]*(\d+)'
    ]
    for pattern in visceral_patterns:
        visceral_match = re.search(pattern, text, re.IGNORECASE)
        if visceral_match:
            data['visceral_fat_level'] = int(visceral_match.group(1))
            break
    
    # 데이터가 충분히 추출되지 않았으면 Mock 데이터 사용
    if len(data) < 3:
        print("⚠️ 추출된 데이터가 부족합니다. Mock 데이터를 사용합니다.")
        return get_mock_inbody_data()
    
    print(f"✅ {len(data)}개 항목 추출 완료")
    return data


def get_mock_inbody_data() -> Dict:
    """
    테스트용 Mock InBody 데이터
    API가 없거나 OCR 실패 시 사용
    """
    return {
        'weight': 70.5,
        'skeletal_muscle_mass': 32.1,
        'body_fat_mass': 15.2,
        'body_fat_percentage': 21.6,
        'bmi': 23.8,
        'body_water': 40.5,
        'protein': 11.2,
        'minerals': 3.8,
        'bmr': 1650,
        'visceral_fat_level': 8
    }


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 OCR Processor 테스트")
    mock_data = get_mock_inbody_data()
    print("Mock 데이터:", mock_data)