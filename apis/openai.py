#!/usr/bin/env python3
"""
OpenAI API 호출 관련 엔드포인트
"""
import os
import json
import uuid
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv

# 환경 변수 로드 (app.py에서 이미 로드했을 수 있지만 확실하게 하기 위해 다시 로드)
load_dotenv()

# OpenAI 라이브러리 가져오기
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("경고: OpenAI 라이브러리를 찾을 수 없습니다. OpenAI API 기능이 제한됩니다.")
    OPENAI_AVAILABLE = False

# PyMuPDF 선택적 로드
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("경고: PyMuPDF를 찾을 수 없습니다. PDF 파싱 기능이 제한됩니다.")
    PYMUPDF_AVAILABLE = False

# 네임스페이스 설정
ns = Namespace('openai', description='OpenAI API 호출 작업')

# OpenAI 클라이언트 설정 함수
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 응답 모델 정의
openai_response_model = ns.model('OpenAIResponse', {
    'response': fields.Raw(required=True, description='OpenAI API 응답'),
    'model': fields.String(required=True, description='사용된 모델'),
    'tokens': fields.Integer(required=True, description='사용된 토큰 수')
})

error_model = ns.model('Error', {
    'error': fields.String(required=True, description='오류 메시지')
})

# 텍스트 분석 요청 모델
text_analysis_model = ns.model('TextAnalysisRequest', {
    'text': fields.String(required=True, description='분석할 텍스트'),
    'model': fields.String(required=False, description='사용할 모델 (기본값: gpt-4o)', default='gpt-4o'),
    'prompt': fields.String(required=False, description='추가 프롬프트', default='')
})

# 문서 요약 요청 모델
summarize_model = ns.model('SummarizeRequest', {
    'text': fields.String(required=True, description='요약할 텍스트'),
    'model': fields.String(required=False, description='사용할 모델 (기본값: gpt-4o)', default='gpt-4o'),
    'max_tokens': fields.Integer(required=False, description='최대 토큰 수', default=500)
})

# 파일 업로드를 위한 파서
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='PDF 파일')
upload_parser.add_argument('model', location='form', type=str, required=False, default='gpt-4o', help='사용할 모델')

@ns.route('/analyze')
class TextAnalysis(Resource):
    @ns.doc('analyze_text')
    @ns.expect(text_analysis_model)
    @ns.response(200, '텍스트 분석 성공', openai_response_model)
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """텍스트 분석"""
        if not OPENAI_AVAILABLE:
            return {'error': 'OpenAI 라이브러리가 설치되지 않았습니다.'}, 500
            
        try:
            data = request.json
            text = data.get('text', '')
            model = data.get('model', 'gpt-4o')
            prompt = data.get('prompt', '')
            
            if not text:
                return {'error': '분석할 텍스트가 없습니다'}, 400
                
            # OpenAI 클라이언트 생성
            try:
                client = get_openai_client()
            except ValueError as e:
                return {'error': str(e)}, 500
            
            # OpenAI API 호출
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 텍스트 분석 전문가입니다. 제공된 텍스트를 분석하고 중요한 정보를 추출하여 구조화된 형태로 제공해주세요."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ]
            )
            
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            
            return {
                'response': response,
                'model': model,
                'tokens': tokens
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500

@ns.route('/summarize')
class Summarize(Resource):
    @ns.doc('summarize_text')
    @ns.expect(summarize_model)
    @ns.response(200, '텍스트 요약 성공', openai_response_model)
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """텍스트 요약"""
        if not OPENAI_AVAILABLE:
            return {'error': 'OpenAI 라이브러리가 설치되지 않았습니다.'}, 500
            
        try:
            data = request.json
            text = data.get('text', '')
            model = data.get('model', 'gpt-4o')
            max_tokens = data.get('max_tokens', 500)
            
            if not text:
                return {'error': '요약할 텍스트가 없습니다'}, 400
                
            # OpenAI 클라이언트 생성
            try:
                client = get_openai_client()
            except ValueError as e:
                return {'error': str(e)}, 500
            
            # OpenAI API 호출
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 텍스트 요약 전문가입니다. 제공된 텍스트를 간결하게 요약해주세요."},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens
            )
            
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            
            return {
                'response': response,
                'model': model,
                'tokens': tokens
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500

@ns.route('/analyze-registration')
class AnalyzeRegistration(Resource):
    @ns.doc('analyze_registration')
    @ns.expect(upload_parser)
    @ns.response(200, '등기부등본 분석 성공', openai_response_model)
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """PDF 등기부등본 파일 업로드 및 분석"""
        # OpenAI 사용 가능 여부 확인
        if not OPENAI_AVAILABLE:
            return {'error': 'OpenAI 라이브러리가 설치되지 않았습니다.'}, 500
            
        # PyMuPDF 사용 가능 여부 확인
        if not PYMUPDF_AVAILABLE:
            return {'error': 'PyMuPDF가 설치되지 않았습니다. PDF 파싱 기능을 사용할 수 없습니다.'}, 500
        
        # 파일 확인
        if 'file' not in request.files:
            return {'error': '파일이 없습니다'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': '선택된 파일이 없습니다'}, 400
        
        if not allowed_file(file.filename):
            return {'error': 'PDF 파일만 허용됩니다'}, 400
        
        try:
            # 모델 파라미터 가져오기
            model = request.form.get('model', 'gpt-4o')
            
            # OpenAI 클라이언트 생성
            try:
                client = get_openai_client()
            except ValueError as e:
                return {'error': str(e)}, 500
            
            # 임시 디렉토리 가져오기
            from app import TEMP_FOLDER
            
            # 파일 저장 (고유한 이름 사용)
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(TEMP_FOLDER, unique_filename)
            file.save(filepath)
            
            # PDF 텍스트 추출
            doc = fitz.open(filepath)
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            
            doc.close()  # 명시적으로 문서 닫기
            
            # 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"파일 삭제 실패: {e}")
            
            # 텍스트가 비어있는지 확인
            if not text_content.strip():
                return {'error': 'PDF에서 텍스트를 추출할 수 없습니다'}, 400
            
            # OpenAI API 호출
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": """
                      아래 등기사항전부증명서(말소사항 포함) 원문을 분석하고, 출력 형식은 반드시 JSON으로, 키는 모두 snake_case(띄어쓰기 대신 언더바)로 작성해 주세요.
 
 출력 예시 구조:
 
 {
   "basic_info": {
     "real_estate": "도로명주소 또는 지번",
     "identifier_number": "고유번호",
     "examination_datetime": "YYYY-MM-DD HH:MM:SS",
     "registry_office": "관할 등기소 명칭"
   },
   "building": {
     "structure": "철근콘크리트구조 등",
     "usage": "단독주택(다가구 6) 외1 등",
     "floor_areas": {
       "floor_1": "㎡",
       "floor_2": "㎡",
       "floor_3": "㎡",
       "floor_4": "㎡",
       "floor_5": "㎡",
       // ... 추가 층수 ...
       "floor_rooftop": "㎡ (연면적 제외 여부)"
     },
     "total_floor_area": "㎡",
     "total_floor_area_pyeong": "평"
   },
   "ownership_history": [
     {
       "event_date": "YYYY-MM-DD",
       "event_type": "소유권보존/이전 등기",
       "owner_name": "이름",
       "owner_id": "주민등록번호 앞6자리-**",
       "owner_address": "주소",
       "remarks": "매매일/등기원인/매매가액 등"
     }
     // …다른 변천 기록들
   ],
   "lien_history": [
     {
       "event_date": "YYYY-MM-DD",
       "lien_type": "압류 설정/해제",
       "lien_holder": "기관명",
       "remarks": "압류 사유 등"
     }
     // …
   ],
   "mortgage_history": [
     {
       "mortgage_number": 1,
       "registration_date": "YYYY-MM-DD",
       "max_loan_amount": "금액",
       "mortgagor": "채무자 이름",
       "mortgagee": "근저당권자 기관명",
       "cancellation_date": "YYYY-MM-DD"
     }
     // …다른 근저당권 기록
   ],
   "sale_list": [
     {
       "list_number": "목록번호",
       "transaction_date": "YYYY-MM-DD",
       "transaction_amount": "금액",
       "properties": {
         "land": "토지 주소",
         "building": "건물 주소"
       }
     }
   ],
   "risk_analysis": {
     "positive_factors": ["항목1", "항목2"],
     "caution_factors": ["항목1", "항목2"],
     "risk_factors": ["항목"]
   },
   "lease_checkpoints": ["확인사항1", "확인사항2"],
   "safe_deposit_levels": {
     "recommended_upper_limit": "금액",
     "maximum_safe_limit": "금액"
   },
   "insurance_and_protection": ["항목1", "항목2"],
   "overall_evaluation": {
     "risk_score": 0,
     "comment": "부동산의 전반적 안전성 및 권고사항"
   }
 }
                      """},
                    {"role": "user", "content": text_content}
                ],
                response_format={"type": "json_object"}
            )
            
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            
            # JSON 형식 검증
            try:
                json_response = json.loads(response)
                return {
                    'response': json_response,
                    'model': model,
                    'tokens': tokens
                }, 200
            except json.JSONDecodeError:
                return {'error': 'OpenAI API가 올바른 JSON 형식으로 응답하지 않았습니다'}, 500
        except Exception as e:
            # 오류 발생 시 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except:
                pass
            return {'error': str(e)}, 500
