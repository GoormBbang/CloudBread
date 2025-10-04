# Food Recommend Server

Gemini AI 기반 임산부 맞춤 식단 추천 서비스

## 🚀 로컬 개발

```bash
# 의존성 설치
uv pip install -r requirements.txt

# 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 빌드 & 배포

```bash
# 1. 멀티 아키텍처 이미지 빌드 & 푸시
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yunseocloud/food-recommend-server:latest \
  --push .

# 2. K8s 배포
kubectl apply -f deployment.yaml

# 3. 강제 재배포
kubectl rollout restart deployment food-recommend-server -n ai-services
```

## 🌐 API 문서

- **API Base**: `http://cloudbread.133.186.213.185.nip.io/api/food`
- **Docs**: `http://cloudbread.133.186.213.185.nip.io/api/food/docs`
- **ReDoc**: `http://cloudbread.133.186.213.185.nip.io/api/food/redoc`

## 📋 주요 엔드포인트

- `POST /recommend` - 식단 추천
- `GET /health` - 헬스 체크
