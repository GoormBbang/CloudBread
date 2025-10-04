# Chatbot Server

Gemini AI 기반 임산부 건강 상담 챗봇 서비스

## 🚀 로컬 개발

```bash
# 의존성 설치
uv pip install -r requirements.txt

# 환경변수 설정
export GEMINI_API_KEY='your-api-key'

# 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 빌드 & 배포

```bash
# 1. Secret 생성 (최초 1회)
kubectl create secret generic chatbot-server-env -n ai-services \
  --from-literal=GEMINI_API_KEY='your-api-key'

# 2. 멀티 아키텍처 이미지 빌드 & 푸시
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yunseocloud/chatbot-server:latest \
  --push .

# 3. K8s 배포
kubectl apply -f deployment.yaml

# 4. 강제 재배포
kubectl rollout restart deployment chatbot-server -n ai-services
```

## 🌐 API 문서

- **API Base**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot`
- **Docs**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot/docs`
- **ReDoc**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot/redoc`

## 📋 주요 엔드포인트

- `POST /chat` - 챗봇 대화
- `GET /health` - 헬스 체크
