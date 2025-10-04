from datetime import date
import random
from models import RecommendRequest, RecommendResponse, MealSection, FoodItem


def generate_food_recommendation(request: RecommendRequest) -> RecommendResponse:
    """
    유저 정보를 기반으로 추천 식단을 생성하는 비즈니스 로직
    현재는 더미 데이터를 반환
    """
    
    # 더미 음식 데이터
    breakfast_foods = [
        {"foodId": 101, "name": "현미밥", "portionLabel": "1공기 (210g)", "estCalories": 320, "foodCategory": "밥류"},
        {"foodId": 102, "name": "미역국", "portionLabel": "1그릇 (250ml)", "estCalories": 80, "foodCategory": "국 및 탕류"},
        {"foodId": 103, "name": "계란말이", "portionLabel": "2조각 (80g)", "estCalories": 120, "foodCategory": "구이류"},
    ]
    
    lunch_foods = [
        {"foodId": 201, "name": "연어덮밥", "portionLabel": "1인분 (300g)", "estCalories": 540, "foodCategory": "밥류"},
        {"foodId": 202, "name": "시금치나물", "portionLabel": "1접시 (100g)", "estCalories": 40, "foodCategory": "나물류"},
    ]
    
    dinner_foods = [
        {"foodId": 301, "name": "닭가슴살 샐러드", "portionLabel": "1인분 (250g)", "estCalories": 350, "foodCategory": "샐러드류"},
        {"foodId": 302, "name": "현미밥", "portionLabel": "1/2공기 (105g)", "estCalories": 160, "foodCategory": "밥류"},
        {"foodId": 303, "name": "두부된장국", "portionLabel": "1그릇 (250ml)", "estCalories": 90, "foodCategory": "국 및 탕류"},
    ]
    
    # 식단 섹션 생성
    breakfast = MealSection(
        mealType="BREAKFAST",
        totalKcal=sum(f["estCalories"] for f in breakfast_foods),
        items=[FoodItem(**f) for f in breakfast_foods]
    )
    
    lunch = MealSection(
        mealType="LUNCH",
        totalKcal=sum(f["estCalories"] for f in lunch_foods),
        items=[FoodItem(**f) for f in lunch_foods]
    )
    
    dinner = MealSection(
        mealType="DINNER",
        totalKcal=sum(f["estCalories"] for f in dinner_foods),
        items=[FoodItem(**f) for f in dinner_foods]
    )
    
    return RecommendResponse(
        planId=random.randint(1000, 9999),
        planDate=str(date.today()),
        sections=[breakfast, lunch, dinner]
    )

