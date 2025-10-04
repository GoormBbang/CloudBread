# Food Recommendation API

임산부를 위한 식단 추천 더미 API

## 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 가상환경 생성 및 패키지 설치
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

## 실행

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 Swagger UI 확인:
- http://localhost:8000/docs

## 엔드포인트

### POST /api/v1/recommend
유저 정보를 기반으로 추천 식단 제공

**Request Body:**
```json
{
  "user": {
    "birth_date": "1998-05-12",
    "due_date": "2025-02-01",
    "other_health_factors": ["임신성 당뇨 전단계"]
  },
  "healths": ["고혈압", "임신성 당뇨"],
  "allergies": ["땅콩", "견과류"],
  "diets": ["채식", "저염식"],
  "food_history": [...]
}
```

**Response:**
```json
{
  "planId": 5678,
  "planDate": "2025-01-16",
  "sections": [...]
}
```

## NKS(NHN Kubernetes Service) 배포

### 1. Docker 이미지 빌드 및 푸시

```bash
# Docker 이미지 빌드
docker build -t yunseocloud/food-recommend-server:latest .

# Docker Hub에 푸시
docker push yunseocloud/food-recommend-server:latest
```

### 2. kubectl로 직접 배포

```bash
# backend 네임스페이스에 배포
kubectl apply -f food-recommend-deployment.yaml

# 배포 상태 확인
kubectl get pods -n backend
kubectl get svc -n backend
```

### 3. Helm으로 배포

```bash
# Helm 차트 설치
helm install food-recommend-server ./food-recommend-server --namespace backend

# 또는 패키지된 차트 사용
helm install food-recommend-server ./food-recommend-server-0.1.0.tgz --namespace backend

# 배포 상태 확인
helm list -n backend
kubectl get pods -n backend

# 업그레이드
helm upgrade food-recommend-server ./food-recommend-server --namespace backend

# 삭제
helm uninstall food-recommend-server --namespace backend
```

### 4. 서비스 접근

```bash
# ClusterIP 서비스 (내부 접근)
# 다른 파드에서 http://food-recommend-server-service.backend.svc.cluster.local 로 접근

# NodePort 서비스 (외부 접근, Helm 사용 시)
# http://<노드IP>:30668 로 접근
```

## 배포 구조

```
food_recommend/
├── Dockerfile                              # 컨테이너 이미지
├── food-recommend-deployment.yaml         # K8s 배포 YAML (Deployment + Service)
├── food-recommend-server/                 # Helm 차트
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       └── service.yaml
└── food-recommend-server-0.1.0.tgz       # 패키지된 Helm 차트
```

