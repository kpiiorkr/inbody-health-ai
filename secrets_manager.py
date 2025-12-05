"""
Secrets 관리 모듈
로컬에서는 .env, 배포 시에는 Streamlit Secrets 사용
"""
import os
import streamlit as st
from pathlib import Path

def get_secret(key: str, default: str = None) -> str:
    """
    로컬/배포 환경에 맞게 시크릿 가져오기
    """
    # Streamlit Cloud 환경
    if hasattr(st, 'secrets'):
        try:
            return st.secrets.get(key, default)
        except:
            pass
    
    # 로컬 환경 (.env)
    return os.getenv(key, default)

def setup_google_credentials():
    """
    Google 인증 설정
    """
    # Streamlit Cloud 환경
    if hasattr(st, 'secrets') and 'GOOGLE_CREDENTIALS_JSON' in st.secrets:
        import json
        credentials = st.secrets['GOOGLE_CREDENTIALS_JSON']
        
        # 임시 파일로 저장
        creds_path = 'google-credentials-temp.json'
        with open(creds_path, 'w') as f:
            json.dump(json.loads(credentials), f)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        return creds_path
    
    # 로컬 환경
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-credentials.json')
    if os.path.exists(creds_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        return creds_path
    
    return None