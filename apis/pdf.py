#!/usr/bin/env python3
"""
PDF 파싱 관련 API 엔드포인트
"""
import os
import uuid
import re
from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# PyMuPDF 선택적 로드
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("경고: PyMuPDF를 찾을 수 없습니다. PDF 파싱 기능이 제한됩니다.")
    PYMUPDF_AVAILABLE = False

# 네임스페이스 설정
ns = Namespace('pdf', description='PDF 파싱 작업')

# 응답 모델 정의
text_response_model = ns.model('TextResponse', {
    'filename': fields.String(required=True, description='파일명'),
    'text_content': fields.String(required=True, description='추출된 텍스트 내용')
})

image_info_model = ns.model('ImageInfo', {
    'image_id': fields.Integer(required=True, description='이미지 ID'),
    'filename': fields.String(required=True, description='이미지 파일명'),
    'page': fields.Integer(required=True, description='페이지 번호')
})

images_response_model = ns.model('ImagesResponse', {
    'filename': fields.String(required=True, description='파일명'),
    'image_count': fields.Integer(required=True, description='추출된 이미지 수'),
    'images': fields.List(fields.Nested(image_info_model), required=True, description='이미지 정보 목록')
})

error_model = ns.model('Error', {
    'error': fields.String(required=True, description='오류 메시지')
})

# 파일 업로드를 위한 파서
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='PDF 파일')

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ns.route('/extract-text')
class ExtractText(Resource):
    @ns.doc('extract_text')
    @ns.expect(upload_parser)
    @ns.response(200, '텍스트 추출 성공', text_response_model)
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """PDF 파일에서 텍스트 추출"""
        from app import app, TEMP_FOLDER  # 앱 설정 가져오기
        
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
            
            return {
                'filename': filename,
                'text_content': text_content
            }, 200
        except Exception as e:
            # 오류 발생 시 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except:
                pass
            return {'error': str(e)}, 500

@ns.route('/extract-images')
class ExtractImages(Resource):
    @ns.doc('extract_images')
    @ns.expect(upload_parser)
    @ns.response(200, '이미지 추출 성공', images_response_model)
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """PDF 파일에서 이미지 추출"""
        from app import app, TEMP_FOLDER, IMAGES_FOLDER  # 앱 설정 가져오기
        
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
            # 파일 저장 (고유한 이름 사용)
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(TEMP_FOLDER, unique_filename)
            file.save(filepath)
            
            # PDF 이미지 추출
            doc = fitz.open(filepath)
            image_info = []
            
            for page_index in range(len(doc)):
                page = doc[page_index]
                images = page.get_images(full=True)
                
                for img_index, img in enumerate(images, start=1):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    img_filename = f"{uuid.uuid4().hex}_page{page_index+1}_img{img_index}.png"
                    img_path = os.path.join(IMAGES_FOLDER, img_filename)
                    
                    if pix.n < 5:
                        pix.save(img_path)
                    else:
                        pix0 = fitz.Pixmap(fitz.csRGB, pix)
                        pix0.save(img_path)
                        pix0 = None
                    
                    pix = None
                    image_info.append({
                        'image_id': len(image_info) + 1,
                        'filename': img_filename,
                        'page': page_index + 1
                    })
            
            doc.close()  # 명시적으로 문서 닫기
            
            # 임시 PDF 파일 삭제 시도
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"파일 삭제 실패: {e}")
            
            return {
                'filename': filename,
                'image_count': len(image_info),
                'images': image_info
            }, 200
        except Exception as e:
            # 오류 발생 시 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except:
                pass
            return {'error': str(e)}, 500

@ns.route('/extract-structured')
class ExtractStructured(Resource):
    @ns.doc('extract_structured')
    @ns.expect(upload_parser)
    @ns.response(200, '구조화된 데이터 추출 성공')
    @ns.response(400, '잘못된 요청', error_model)
    @ns.response(500, '서버 오류', error_model)
    def post(self):
        """PDF 파일에서 구조화된 데이터 추출"""
        from app import app, TEMP_FOLDER  # 앱 설정 가져오기
        
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
            # 파일 저장 (고유한 이름 사용)
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(TEMP_FOLDER, unique_filename)
            file.save(filepath)
            
            # PDF 텍스트 추출
            doc = fitz.open(filepath)
            
            # 기본 정보 추출
            structured_data = {
                "filename": filename,
                "page_count": len(doc),
                "document_type": None,
                "property_info": {
                    "address": None,
                    "unique_number": None,
                    "building_type": None,
                    "area": None
                },
                "ownership_info": [],
                "mortgage_info": [],
                "transaction_info": None
            }
            
            # 전체 텍스트 추출
            all_text = ""
            for page_index in range(len(doc)):
                page = doc[page_index]
                all_text += page.get_text()
            
            doc.close()  # 명시적으로 문서 닫기
            
            # 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"파일 삭제 실패: {e}")
            
            # 문서 유형 추출
            if "등기사항전부증명서" in all_text:
                structured_data["document_type"] = "등기사항전부증명서"
                
                # 부동산 주소 추출
                address_pattern = r"\[건물\]\s*(.*?)\n"
                address_match = re.search(address_pattern, all_text)
                if address_match:
                    structured_data["property_info"]["address"] = address_match.group(1).strip()
                
                # 고유번호 추출
                unique_number_pattern = r"고유번호\s*(.*?)\n"
                unique_number_match = re.search(unique_number_pattern, all_text)
                if unique_number_match:
                    structured_data["property_info"]["unique_number"] = unique_number_match.group(1).strip()
                
                # 건물 유형 추출
                building_type_pattern = r"단독주택|아파트|연립주택|다세대주택|오피스텔|상가"
                building_type_match = re.search(building_type_pattern, all_text)
                if building_type_match:
                    structured_data["property_info"]["building_type"] = building_type_match.group(0)
                
                # 면적 정보 추출
                area_pattern = r"(\d+층\s*\d+\.?\d*㎡)"
                area_matches = re.findall(area_pattern, all_text)
                if area_matches:
                    structured_data["property_info"]["area"] = area_matches
                
                # 소유권 정보 추출
                ownership_pattern = r"소유자\s+([^\s]+)\s+(\d{6}-\*+)"
                ownership_matches = re.findall(ownership_pattern, all_text)
                for match in ownership_matches:
                    owner_info = {
                        "name": match[0],
                        "id": match[1]
                    }
                    structured_data["ownership_info"].append(owner_info)
                
                # 근저당권 정보 추출
                mortgage_pattern = r"근저당권설정.*?채권최고액\s+금([\d,]+)원"
                mortgage_matches = re.findall(mortgage_pattern, all_text, re.DOTALL)
                for match in mortgage_matches:
                    mortgage_info = {
                        "amount": match.replace(",", "")
                    }
                    structured_data["mortgage_info"].append(mortgage_info)
                
                # 거래 정보 추출
                transaction_pattern = r"거래가액\s*금([\d,]+)원"
                transaction_match = re.search(transaction_pattern, all_text)
                if transaction_match:
                    structured_data["transaction_info"] = {
                        "amount": transaction_match.group(1).replace(",", ""),
                        "date": None
                    }
                    
                    # 거래 날짜 추출
                    date_pattern = r"(\d{4})년(\d{1,2})월(\d{1,2})일\s*매매"
                    date_match = re.search(date_pattern, all_text)
                    if date_match:
                        year = date_match.group(1)
                        month = date_match.group(2).zfill(2)
                        day = date_match.group(3).zfill(2)
                        structured_data["transaction_info"]["date"] = f"{year}-{month}-{day}"
            
            return structured_data, 200
        except Exception as e:
            # 오류 발생 시 임시 파일 삭제 시도
            try:
                os.remove(filepath)
            except:
                pass
            return {'error': str(e)}, 500 