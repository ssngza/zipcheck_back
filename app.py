#!/usr/bin/env python3
"""
PDF 파싱 API 서버 (flask-restx 사용)
"""
import os
from flask import Flask
from flask_restx import Api
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 모듈 가져오기
from apis.health import ns as health_ns
from apis.pdf import ns as pdf_ns
from apis.openai import ns as openai_ns

# PyMuPDF 선택적 로드
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("경고: PyMuPDF를 찾을 수 없습니다. PDF 파싱 기능이 제한됩니다.")
    PYMUPDF_AVAILABLE = False

app = Flask(__name__)

# 최대 콘텐츠 길이 설정 (16MB 기본값)
try:
    max_content_length = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
except (ValueError, TypeError):
    max_content_length = 16 * 1024 * 1024
    print(f"경고: MAX_CONTENT_LENGTH 환경 변수 형식이 잘못되었습니다. 기본값 {max_content_length}(16MB)를 사용합니다.")
app.config['MAX_CONTENT_LENGTH'] = max_content_length

# 임시 디렉토리 설정
TEMP_FOLDER = os.environ.get('TEMP_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp'))
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)
app.config['UPLOAD_FOLDER'] = TEMP_FOLDER

# 이미지 저장 디렉토리 설정
IMAGES_FOLDER = os.environ.get('IMAGES_FOLDER', os.path.join(TEMP_FOLDER, 'images'))
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

# API 설정
api = Api(
    app,
    version='1.0',
    title='PDF 파싱 API',
    description='PDF 파일에서 텍스트와 이미지를 추출하고 OpenAI를 활용한 분석 기능을 제공하는 API',
    doc='/docs',
    default='pdf',
    default_label='PDF 파싱 작업'
)

# 네임스페이스 등록
api.add_namespace(health_ns, path='/health')
api.add_namespace(pdf_ns, path='/pdf')
api.add_namespace(openai_ns, path='/openai')

if __name__ == '__main__':
    # DEBUG 환경 변수 처리
    debug = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')
    
    # PORT 환경 변수 처리
    try:
        port = int(os.environ.get('PORT', 5000))
    except (ValueError, TypeError):
        port = 5000
        print(f"경고: PORT 환경 변수 형식이 잘못되었습니다. 기본값 {port}을 사용합니다.")
    
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )
