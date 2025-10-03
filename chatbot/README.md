# 🤖 CloudBread ChatBot

LangChain을 활용한 멀티턴 대화가 가능한 AI 챗봇 서비스입니다. FastAPI 기반으로 구축되었으며, 텍스트와 이미지를 모두 처리할 수 있는 멀티모달 기능을 제공합니다.

## ✨ 주요 기능

- **멀티턴 대화**: LangChain의 ConversationBufferMemory를 사용한 대화 히스토리 관리
- **세션 관리**: UUID 기반 세션별 독립적인 대화 컨텍스트
- **멀티모달 지원**: 텍스트와 이미지를 함께 처리하는 대화 기능
- **RESTful API**: FastAPI 기반의 직관적인 API 엔드포인트
- **쿠버네티스 배포**: Helm 차트를 통한 간편한 쿠버네티스 배포
- **Health Check**: 서비스 상태 모니터링을 위한 헬스 체크 엔드포인트

## 🛠 기술 스택

- **Backend**: FastAPI, Python 3.12
- **AI Framework**: LangChain, OpenAI GPT-4o-mini
- **Image Processing**: Pillow (PIL)
- **Containerization**: Docker
- **Orchestration**: Kubernetes, Helm
- **HTTP Client**: CORS 지원을 통한 웹 브라우저 호환

## 📋 사전 요구사항

- Python 3.12+
- Docker
- Kubernetes 클러스터 (배포 시)
- Helm 3.x (배포 시)
- OpenAI API 키

## 🚀 로컬 개발

### 1. 환경 설정

```bash
# 저장소 클론 (상위 디렉터리에서)
cd chatbot

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY를 실제 값으로 수정
```

### 2. 애플리케이션 실행

```bash
# 개발 서버 실행
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 또는 Python으로 직접 실행
python app.py
```

서비스는 `http://localhost:8000`에서 실행됩니다.

### 3. API 문서 확인

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📡 API 엔드포인트

### 기본 엔드포인트

- `GET /`: 서비스 상태 확인
- `GET /health`: 헬스 체크

### 채팅 엔드포인트

#### 텍스트 채팅
```bash
POST /chat
Content-Type: application/json

{
  "message": "안녕하세요!",
  "session_id": "optional-session-id",
  "system_prompt": "당신은 친근한 AI 어시스턴트입니다."
}
```

#### 멀티모달 채팅 (텍스트 + 이미지)
```bash
POST /chat/multimodal
Content-Type: multipart/form-data

message: "이 이미지에 대해 설명해주세요"
session_id: optional-session-id
image: [이미지 파일]
```

#### 채팅 히스토리 조회
```bash
GET /chat/history/{session_id}
```

#### 세션 관리
```bash
# 활성 세션 목록
GET /chat/sessions

# 세션 삭제
DELETE /chat/session/{session_id}
```

## 🐳 Docker 배포

### 이미지 빌드

```bash
# 이미지 빌드
docker build -t chatbot-server:latest .

# 컨테이너 실행
docker run -d \
  --name chatbot-server \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  chatbot-server:latest
```

## ☸️ 쿠버네티스 배포

### 전제 조건

1. 쿠버네티스 클러스터 접근 권한
2. `backend` 네임스페이스 존재
3. Docker 이미지가 레지스트리에 푸시됨

### Secret 생성

```bash
# OpenAI API 키를 위한 Secret 생성
kubectl create secret generic chatbot-server-env \
  --from-literal=OPENAI_API_KEY=your-openai-api-key \
  --namespace=backend
```

### Helm 배포

```bash
# Helm 차트로 배포
helm install chatbot-server ./chatbot-server \
  --namespace backend \
  --create-namespace

# 배포 상태 확인
helm status chatbot-server --namespace backend

# 업그레이드
helm upgrade chatbot-server ./chatbot-server --namespace backend

# 삭제
helm uninstall chatbot-server --namespace backend
```

### 직접 YAML 배포

```bash
# YAML 파일로 직접 배포
kubectl apply -f chatbot-backend-deployment.yaml
```

## 🔧 설정 옵션

### Helm Values 커스터마이징

`chatbot-server/values.yaml` 파일을 수정하여 배포 설정을 변경할 수 있습니다:

```yaml
# 복제본 수 조정
replicaCount: 3

# 이미지 설정
image:
  repository: your-registry/chatbot-server
  tag: "v1.0.0"

# 리소스 제한
resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi
```

## 📊 모니터링

### 헬스 체크

서비스 상태는 `/health` 엔드포인트를 통해 확인할 수 있습니다:

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "service": "chatbot"}
```

### 로그 확인

```bash
# 쿠버네티스 Pod 로그 확인
kubectl logs -f deployment/chatbot-server-deployment -n backend

# Docker 컨테이너 로그 확인
docker logs -f chatbot-server
```

## 🔒 보안 고려사항

1. **API 키 보안**: OpenAI API 키는 반드시 Secret으로 관리
2. **CORS 설정**: 프로덕션에서는 특정 도메인만 허용하도록 CORS 설정 조정
3. **네트워크 정책**: 클러스터 내부 통신만 허용하도록 NetworkPolicy 설정 권장

## 🐛 문제 해결

### 일반적인 문제

1. **OpenAI API 키 오류**
   ```bash
   # Secret 확인
   kubectl get secret chatbot-server-env -n backend -o yaml
   ```

2. **이미지 풀 오류**
   ```bash
   # 이미지 레지스트리 접근 권한 확인
   docker pull yunseocloud/chatbot-server:latest
   ```

3. **메모리 부족**
   ```bash
   # Pod 리소스 사용량 확인
   kubectl top pod -n backend
   ```

## 🔄 업데이트

새 버전 배포 시:

1. 새 이미지 빌드 및 푸시
2. `values.yaml`에서 이미지 태그 업데이트
3. Helm 업그레이드 실행

```bash
helm upgrade chatbot-server ./chatbot-server --namespace backend
```

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**CloudBread Team** 🍞✨