# Food Recommend Server

DB 기반 규칙형 임산부 맞춤 식단 추천 서비스

## 📖 추천 시스템

실제 음식 DB를 조회하여 사용자의 건강 상태, 알레르기, 식단 선호도, 섭취 이력을 기반으로 개인화된 식단을 추천합니다.

**주요 기능:**
- 알레르기 음식 자동 제외
- 건강 상태 고려 (고혈압 → 저염식, 당뇨 → 저당식)
- 식단 선호도 반영 (채식, 저염식 등)
- 최근 섭취 이력 기반 다양성 확보
- 끼니별 균형잡힌 칼로리 구성

자세한 설계는 [RECOMMENDATION_DESIGN.md](./RECOMMENDATION_DESIGN.md) 참고

## ⚙️ 설정

### 1. 환경 변수 설정

```bash
# env.template을 복사하여 .env 생성
cp env.template .env

# .env 파일 편집 (DB 비밀번호 입력)
```

### 2. DB 접근

- **내부 IP**: `192.168.1.8` (K8s 클러스터 내부)
- **플로팅 IP**: `133.186.240.xxx` (외부)

## 🚀 로컬 개발

```bash
# 의존성 설치
uv pip install -r requirements.txt

# .env 파일 설정 필수!

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
