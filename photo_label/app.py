from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from models import PhotoLabelRequest, PhotoLabelResponse
from service import analyze_food_image, send_result_to_backend

load_dotenv()

app = FastAPI(
    title="Photo Label API",
    description="음식 사진 라벨링 AI 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 백엔드 URL (클러스터 내부 Service DNS)
BACKEND_URL = os.getenv("BACKEND_URL", "http://cloudbread-backend-svc.backend.svc.cluster.local")


@app.get("/")
def root():
    return {"message": "Photo Label API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/v1/photo-label", response_model=PhotoLabelResponse)
async def label_photo(request: PhotoLabelRequest):
    """
    음식 사진을 받아서 VLM으로 분석하고 백엔드에 결과를 전송
    """
    try:
        # 1. 이미지 분석
        label, confidence = await analyze_food_image(request.imageUrl)
        
        # 2. 백엔드로 결과 전송
        try:
            send_result_to_backend(
                request.photoAnalysisId,
                label,
                confidence,
                BACKEND_URL
            )
        except Exception as backend_error:
            # 백엔드 전송 실패시 로그만 남기고 계속 진행
            print(f"백엔드 전송 실패: {backend_error}")
        
        return PhotoLabelResponse(
            success=True,
            photoAnalysisId=request.photoAnalysisId,
            label=label,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 분석 중 오류 발생: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

