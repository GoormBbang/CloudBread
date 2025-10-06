# Photo Label API

음식 사진을 받아서 VLM(Vision Language Model)을 이용해 음식명을 추출하는 AI 서비스

## 기능

- POST `/v1/photo-label`: 음식 사진 URL을 받아서 음식명과 신뢰도를 분석
- 분석 결과를 자동으로 백엔드 API로 전송

## 기술 스택

- FastAPI
- LangChain
- OpenAI GPT-4o (Vision)
- Python 3.11

## 설정

1. `.env` 파일 생성:
```bash
cp .env.example .env
```

2. OpenAI API 키 설정:
```
OPENAI_API_KEY=your-api-key
BACKEND_URL=http://cloudbread-backend-svc.backend.svc.cluster.local
```

## 실행

### 로컬 실행
```bash
uv pip install -r requirements.txt
uvicorn app:app --reload
```

### Docker 실행
```bash
docker build -t photo-label .
docker run -p 8000:8000 --env-file .env photo-label
```

## API 명세

### POST /v1/photo-label

음식 사진을 분석하여 음식명을 추출합니다.

**Request Body:**
```json
{
  "photoAnalysisId": 2,
  "imageUrl": "http://cloudbread.133.186.213.185.nip.io/uploads/u/1/photos/2.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "photoAnalysisId": 2,
  "label": "김치찌개",
  "confidence": 0.87
}
```

## 아키텍처

### 모듈 구조

```
photo_label/
├── app.py          # FastAPI 애플리케이션 (Presentation Layer)
├── service.py      # 비즈니스 로직 (Business Logic Layer)
├── models.py       # 데이터 모델
└── requirements.txt
```

### 모듈 역할

1. **app.py (Presentation Layer)**
   - FastAPI 엔드포인트 정의
   - 요청/응답 처리
   - 에러 핸들링

2. **service.py (Business Logic Layer)**
   - `analyze_food_image()`: VLM을 이용한 음식 이미지 분석
   - `send_result_to_backend()`: 백엔드 API 호출

3. **models.py**
   - Pydantic 모델 정의
   - 요청/응답 스키마

### 처리 흐름

1. 백엔드 → AI 서비스: POST `/v1/photo-label` (photoAnalysisId, imageUrl)
2. AI 서비스: VLM으로 이미지 분석 (음식명 추출)
3. AI 서비스 → 백엔드: POST `/api/ai/photo-analyses/{photoAnalysisId}/label` (label, confidence)
4. AI 서비스 → 백엔드: 응답 반환 (success, label, confidence)

## 배포

### 쿠버네티스 Service DNS 구조

**백엔드 → AI 서비스 호출:**
```
POST http://food-recommend-server-svc.ai-services.svc.cluster.local/v1/photo-label
```

**AI 서비스 → 백엔드 응답:**
```
POST http://cloudbread-backend-svc.backend.svc.cluster.local/api/ai/photo-analyses/{photoAnalysisId}/label
```

- AI 서비스: `ai-services` 네임스페이스
- 백엔드 서비스: `backend` 네임스페이스

