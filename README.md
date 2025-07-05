# PDF 파싱 API

PDF 파일에서 텍스트와 이미지를 추출하고 OpenAI를 활용한 분석 기능을 제공하는 API 서버입니다.

## 기능

- PDF 파일에서 텍스트 추출
- PDF 파일에서 이미지 추출
- PDF 텍스트 구조화 (등기부등본 정보 추출)
- OpenAI API를 활용한 텍스트 분석
- OpenAI API를 활용한 텍스트 요약

## 설치 및 설정

### 요구사항

- Python 3.9 이상
- pip (Python 패키지 관리자)
- OpenAI API 키 (OpenAI 기능 사용 시)

### 설치 방법

1. 저장소 클론

```bash
git clone <repository-url>
cd pdf-parsing-api
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정

```bash
cp env.sample .env
```

`.env` 파일을 열고 필요한 설정을 수정합니다. 특히 OpenAI API 키를 설정해야 합니다.

### 실행 방법

```bash
python app.py
```

서버가 기본적으로 http://localhost:5000 에서 실행됩니다.
API 문서는 http://localhost:5000/docs 에서 확인할 수 있습니다.

## API 엔드포인트

### 상태 확인

- `GET /health`: 서버 상태 확인

### PDF 파싱

- `POST /pdf/extract-text`: PDF 파일에서 텍스트 추출
- `POST /pdf/extract-images`: PDF 파일에서 이미지 추출
- `POST /pdf/extract-structured`: PDF 파일에서 구조화된 데이터 추출 (등기부등본)

### OpenAI 분석

- `POST /openai/analyze`: 텍스트 분석
- `POST /openai/summarize`: 텍스트 요약
- `POST /openai/analyze-registration`: 등기부등본 분석

## 사용 예시

### PDF 텍스트 추출

```bash
curl -X POST "http://localhost:5000/pdf/extract-text" -F "file=@example.pdf"
```

### OpenAI를 활용한 텍스트 분석

```bash
curl -X POST "http://localhost:5000/openai/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "분석할 텍스트 내용",
    "model": "gpt-4o"
  }'
```

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.
