#!/usr/bin/env python3
"""
Health 관련 API 엔드포인트
"""
from flask_restx import Namespace, Resource, fields

# PyMuPDF 선택적 로드
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("경고: PyMuPDF를 찾을 수 없습니다. PDF 파싱 기능이 제한됩니다.")
    PYMUPDF_AVAILABLE = False

# 네임스페이스 설정
ns = Namespace('health', description='Health 관련 작업')

# 응답 모델 정의
health_model = ns.model('Health', {
    'status': fields.String(required=True, description='서버 상태'),
    'pymupdf_available': fields.Boolean(required=True, description='PyMuPDF 사용 가능 여부')
})

@ns.route('')
class Health(Resource):
    @ns.doc('health_check')
    @ns.response(200, '정상 작동 중', health_model)
    def get(self):
        """서버 상태 확인"""
        return {
            'status': 'healthy',
            'pymupdf_available': PYMUPDF_AVAILABLE
        }
