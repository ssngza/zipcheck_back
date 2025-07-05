FROM python:3.10-slim

WORKDIR /app

# 필요한 시스템 패키지 설치
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libffi-dev \
#     && rm -rf /var/lib/apt/lists/*

# 앱 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p temp/images images_output

# 환경 변수 설정
ENV PORT=5000
ENV DEBUG=False
ENV TEMP_FOLDER=/app/temp
ENV IMAGES_FOLDER=/app/temp/images

# 포트 노출
EXPOSE 5000

# 앱 실행
CMD ["python", "app.py"] 