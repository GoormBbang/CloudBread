# Chatbot Server

**CRAG (Corrective RAG) 기반 임산부 건강 상담 AI 에이전트**

LangGraph를 활용한 자율 에이전트 시스템으로, LLM이 능동적으로 도구를 선택하고 검색 결과를 자체 평가하며 최적의 답변을 제공합니다.

## 🌟 주요 기능

### 🤖 자율 에이전트
- **능동적 도구 선택**: LLM이 상황에 맞는 도구를 자동 선택
- **CRAG 워크플로우**: 검색 결과 품질을 스스로 평가하고 교정
- **멀티 소스 통합**: 벡터 DB, 데이터베이스, 웹 검색 결과 종합

### � 지식 베이스 (RAG)
- **FAISS 벡터 스토어**: 임산부 영양 전문 지식 저장
- **의미 기반 검색**: 사용자 질문의 의도 파악
- **지속적 업데이트**: 새로운 지식 추가 가능

### 🔍 검색 품질 보장
- **관련성 평가**: LLM이 검색 결과 품질 자체 평가
- **재시도 메커니즘**: 부적절하거나 애매한 결과 시 재검색
- **지식 베이스 집중**: 전문적이고 검증된 임산부 영양 정보만 제공

### 🛠️ 통합 도구
- Photo Label Service (VLM 음식 분석)
- Nutrition Feedback Service (영양 피드백)
- Food Recommend Service (식단 추천)
- MySQL 영양 데이터베이스

## 📁 프로젝트 구조

```
chatbot/
├── app.py                    # FastAPI 메인 애플리케이션
├── agent.py                  # LangGraph 에이전트 (CRAG 워크플로우)
├── tools.py                  # 에이전트 도구 모음
├── vector_store.py           # FAISS 벡터 스토어 관리
├── knowledge_base/           # 임산부 영양 지식 베이스
│   ├── pregnancy_early.txt   # 임신 초기 가이드
│   ├── pregnancy_mid.txt     # 임신 중기 가이드
│   ├── pregnancy_late.txt    # 임신 후기 가이드
│   ├── essential_nutrients.txt # 필수 영양소
│   └── foods_to_avoid.txt    # 피해야 할 음식
├── vector_store/             # 벡터 DB 저장 경로 (자동 생성)
├── requirements.txt          # Python 의존성
├── .env                      # 환경 변수
└── README.md
```

## 🚀 로컬 개발

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env.example`을 참고하여 `.env` 파일 생성:

```bash
# 필수
OPENAI_API_KEY='your-openai-api-key'

# 선택 (DB 연동 시)
DB_HOST='localhost'
DB_USER='root'
DB_PASSWORD='your-password'
DB_NAME='cloudbread'
```

### 3. 벡터 스토어 초기화 (최초 1회)

```bash
python vector_store.py
```

### 4. 서버 실행

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker 빌드 & 배포

### 1. Secret 생성 (최초 1회)

```bash
kubectl create secret generic chatbot-server-env -n ai-services \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --from-literal=DB_PASSWORD='your-db-password'
```

### 2. 멀티 아키텍처 이미지 빌드 & 푸시

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yunseocloud/chatbot-server:latest \
  --push .
```

### 3. K8s 배포

```bash
kubectl apply -f deployment.yaml
```

### 4. 강제 재배포

```bash
kubectl rollout restart deployment chatbot-server -n ai-services
```

## 🌐 API 문서

- **API Base**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot`
- **Docs**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot/docs`
- **ReDoc**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot/redoc`

## 📋 API 엔드포인트

### POST /chat
**텍스트 기반 대화**

```json
{
  "message": "임신 초기에 엽산을 얼마나 먹어야 하나요?",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "response": "임신 초기에는 하루 600μg의 엽산 섭취가 권장됩니다...",
  "session_id": "generated-or-provided-id",
  "message_history": [...]
}
```

### POST /chat/multimodal
**이미지 + 텍스트 대화**

```bash
curl -X POST http://localhost:8000/chat/multimodal \
  -F "message=이 음식은 임산부가 먹어도 되나요?" \
  -F "image=@food.jpg"
```

### GET /chat/history/{session_id}
**대화 히스토리 조회**

### DELETE /chat/session/{session_id}
**세션 삭제**

### GET /chat/sessions
**활성 세션 목록**

### GET /health
**헬스 체크**

## 🔄 에이전트 워크플로우

```
┌──────────────┐
│  1. Planner  │  사용자 질문 분석 & 실행 계획 수립
└──────┬───────┘
       ↓
┌──────────────────┐
│ 2. RAG Retrieval │  벡터 DB에서 임산부 영양 지식 검색
└──────┬───────────┘
       ↓
┌─────────────────┐
│ 3. Grade Docs   │  LLM이 검색 결과 품질 자체 평가
└──────┬──────────┘
       ↓
┌──────────────────┐
│ 4. Decision Node │  평가 결과에 따라 분기
└──────┬───────────┘
       ├─ Irrelevant → 2. RAG Retrieval (재시도)
       ├─ Ambiguous  → 2. RAG Retrieval (재시도)
       └─ Relevant   → 5. DB Query (선택적)
              ↓
┌────────────────┐
│ 6. Synthesize  │  모든 정보를 종합하여 최종 답변 생성
└────────────────┘
```

## 🛠️ 도구 설명

### 1. RAG 검색 (retrieve_vector_kb)
- FAISS 벡터 스토어에서 유사 문서 검색
- 임산부 영양 전문 지식 활용
- 검증된 정보만 제공

### 2. 영양 DB 조회 (query_nutrition_db)
- MySQL에서 음식별 영양 정보 조회
- 칼로리, 영양소 데이터

### 3. 식사 기록 조회 (query_user_food_history)
- 사용자의 최근 식사 기록
- 맞춤형 조언에 활용

### 4. VLM 서비스 (call_photo_label_service)
- 음식 사진 분석
- 음식명 및 신뢰도 반환

### 5. 영양 피드백 (call_nutrition_feedback_service)
- AI 기반 영양 피드백 생성

### 6. 식단 추천 (call_food_recommend_service)
- 개인 맞춤 식단 추천

## 📝 지식 베이스 업데이트

새로운 지식 추가:

```python
from vector_store import get_knowledge_base
from langchain_core.documents import Document

kb = get_knowledge_base()

new_doc = Document(
    page_content="새로운 임산부 영양 정보...",
    metadata={"category": "영양소", "source": "연구 논문"}
)

kb.add_documents([new_doc])
```

## 🔍 테스트

```bash
# 벡터 스토어 테스트
python vector_store.py

# API 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "임신 중 철분 섭취량은?"}'
```

## 📊 모니터링

에이전트 실행 과정 확인:

```python
{
  "intermediate_steps": [
    "계획 수립: rag_search",
    "RAG 검색 완료: 5개 문서 검색",
    "문서 평가: Relevant",
    "DB 조회: 철분",
    "최종 답변 생성 완료"
  ],
  "relevance_grade": "Relevant"
}
```

## ⚙️ 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| OPENAI_API_KEY | ✅ | OpenAI API 키 |
| DB_HOST | ❌ | MySQL 호스트 |
| DB_USER | ❌ | DB 사용자명 |
| DB_PASSWORD | ❌ | DB 비밀번호 |
| DB_NAME | ❌ | DB 이름 (기본: cloudbread) |
| PHOTO_LABEL_URL | ❌ | Photo Label 서비스 URL |
| NUTRITION_FEEDBACK_URL | ❌ | Nutrition Feedback 서비스 URL |
| FOOD_RECOMMEND_URL | ❌ | Food Recommend 서비스 URL |

## 🎯 주요 특징

### 기존 시스템 vs 업그레이드

| 기능 | 기존 | 업그레이드 |
|------|------|------------|
| 역할 | 단순 응답 생성기 | 자율 에이전트 |
| 지식 소스 | LLM 사전 학습 | RAG + DB (검증된 정보) |
| 도구 사용 | 없음 | 6개 도구 자동 선택 |
| 품질 검증 | 없음 | CRAG 자체 평가 + 재시도 |
| 서비스 통합 | 없음 | 3개 AI 서비스 연동 |
| 정보 신뢰성 | 제한적 | 전문 지식 베이스 기반 |

## 🚨 주의사항

1. **OPENAI_API_KEY**: 반드시 설정 필요
2. **벡터 스토어**: 최초 실행 시 자동 생성
3. **메모리**: 인메모리 세션 (재시작 시 소실)
4. **비용**: GPT-4o 사용 시 API 비용 발생

## 📚 참고 자료

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
