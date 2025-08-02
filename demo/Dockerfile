# 경량 Python 이미지 사용
FROM python:3.12-slim

# 작업 디렉터리 설정
WORKDIR /app

# 애플리케이션 파일과 라이브러리 목록 복사
COPY . .

# 필요한 Python 라이브러리 설치
RUN pip install -r requirements.txt

# Streamlit 애플리케이션이 8501번 포트를 사용하도록 설정
EXPOSE 8501

# 컨테이너 실행 명령어
# Streamlit 애플리케이션을 0.0.0.0 주소와 8501 포트에서 실행
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]