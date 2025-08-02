# 경량 Python 이미지 사용
FROM python:3.12-slim

# 필요한 시스템 패키지 설치
# tesseract-ocr과 이미지 처리 라이브러리를 설치합니다.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    tesseract-ocr-kor \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /app

# 애플리케이션 파일 복사
COPY . .

# 필요한 Python 라이브러리 설치
RUN pip install -r requirements.txt

# 컨테이너 실행 시, 5000번 포트를 열도록 설정
EXPOSE 5000

# 컨테이너 실행 명령어
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]