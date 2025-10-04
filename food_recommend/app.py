from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import RecommendRequest, RecommendResponse
from service import generate_food_recommendation

app = FastAPI(
    title="Food Recommendation API",
    description="임산부를 위한 식단 추천 API",
    version="1.0.0",
    root_path="/api/food"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Food Recommendation API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/recommend", response_model=RecommendResponse)
def recommend_food(request: RecommendRequest):
    """
    유저 정보를 기반으로 추천 식단을 제공하는 엔드포인트
    """
    return generate_food_recommendation(request)

