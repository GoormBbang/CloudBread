from datetime import date
import random
from typing import List, Dict
from models import RecommendRequest, RecommendResponse, RecommendResult, MealSection, FoodItem
from db_connection import get_connection


def fetch_foods_from_db() -> List[Dict]:
    """DB에서 모든 음식 정보 조회"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, calories, category, source_name
                FROM foods
                WHERE calories IS NOT NULL AND calories > 0
            """)
            foods = cursor.fetchall()
            return foods
    finally:
        conn.close()


def filter_by_allergies(foods: List[Dict], allergies: List[str]) -> List[Dict]:
    """알레르기 음식 제외"""
    if not allergies:
        return foods
    
    filtered = []
    for food in foods:
        has_allergy = False
        for allergy in allergies:
            if allergy.lower() in food['name'].lower():
                has_allergy = True
                break
        if not has_allergy:
            filtered.append(food)
    
    return filtered


def filter_by_diet(foods: List[Dict], diets: List[str]) -> List[Dict]:
    """식단 선호도 반영 (채식 등)"""
    if not diets:
        return foods
    
    # 채식인 경우 육류 제외
    if any('채식' in diet for diet in diets):
        meat_keywords = ['고기', '육', '소고기', '돼지', '닭', '오리', '양고기', '삼겹살', '갈비']
        foods = [f for f in foods if not any(kw in f['name'] for kw in meat_keywords)]
    
    return foods


def exclude_recent_foods(foods: List[Dict], food_history: List) -> List[Dict]:
    """최근 섭취한 음식 제외하여 다양성 확보"""
    if not food_history:
        return foods
    
    recent_names = [h.foodName for h in food_history]
    return [f for f in foods if f['name'] not in recent_names]


def categorize_foods(foods: List[Dict]) -> Dict[str, List[Dict]]:
    """음식을 카테고리별로 분류"""
    categories = {
        '밥류': [],
        '국/탕': [],
        '반찬': []
    }
    
    for food in foods:
        category = food.get('category', '')
        if '밥' in category:
            categories['밥류'].append(food)
        elif '국' in category or '탕' in category or '찌개' in category:
            categories['국/탕'].append(food)
        else:
            categories['반찬'].append(food)
    
    return categories


def select_meal_items(categorized: Dict[str, List[Dict]], target_kcal: int) -> List[Dict]:
    """끼니별 음식 선택"""
    selected = []
    current_kcal = 0
    
    # 1. 밥류 1개 선택
    if categorized['밥류']:
        rice = random.choice(categorized['밥류'])
        selected.append(rice)
        current_kcal += int(rice['calories'])
    
    # 2. 국/탕 1개 선택
    if categorized['국/탕']:
        soup = random.choice(categorized['국/탕'])
        selected.append(soup)
        current_kcal += int(soup['calories'])
    
    # 3. 반찬 추가 (목표 칼로리에 맞춰)
    if categorized['반찬']:
        side_dishes = categorized['반찬'].copy()
        random.shuffle(side_dishes)
        
        for dish in side_dishes:
            if current_kcal >= target_kcal:
                break
            if len(selected) >= 4:  # 최대 4개까지
                break
            selected.append(dish)
            current_kcal += int(dish['calories'])
    
    return selected


def build_meal_section(meal_type: str, foods: List[Dict]) -> MealSection:
    """MealSection 생성"""
    items = []
    total_kcal = 0
    
    for food in foods:
        item = FoodItem(
            foodId=food['id'],
            name=food['name'],
            portionLabel=food.get('source_name', '100g'),
            estCalories=int(food['calories']),
            foodCategory=food.get('category', '기타')
        )
        items.append(item)
        total_kcal += item.estCalories
    
    return MealSection(
        mealType=meal_type,
        totalKcal=total_kcal,
        items=items
    )


def generate_food_recommendation(request: RecommendRequest) -> RecommendResponse:
    """
    유저 정보를 기반으로 추천 식단을 생성하는 비즈니스 로직
    """
    
    # 1. DB에서 음식 조회
    foods = fetch_foods_from_db()
    
    # 2. 필터링
    foods = filter_by_allergies(foods, request.allergies)
    foods = filter_by_diet(foods, request.diets)
    foods = exclude_recent_foods(foods, request.foodHistory)
    
    # 3. 카테고리별 분류
    categorized = categorize_foods(foods)
    
    # 4. 끼니별 선택
    breakfast_items = select_meal_items(categorized, target_kcal=500)
    
    # 선택된 음식 제외하고 다시 분류 (중복 방지)
    remaining_foods = [f for f in foods if f not in breakfast_items]
    categorized_lunch = categorize_foods(remaining_foods)
    lunch_items = select_meal_items(categorized_lunch, target_kcal=600)
    
    remaining_foods = [f for f in remaining_foods if f not in lunch_items]
    categorized_dinner = categorize_foods(remaining_foods)
    dinner_items = select_meal_items(categorized_dinner, target_kcal=550)
    
    # 5. MealSection 생성
    breakfast = build_meal_section("BREAKFAST", breakfast_items)
    lunch = build_meal_section("LUNCH", lunch_items)
    dinner = build_meal_section("DINNER", dinner_items)
    
    # 6. Response 생성
    result = RecommendResult(
        planId=random.randint(1000, 9999),
        planDate=str(date.today()),
        sections=[breakfast, lunch, dinner]
    )
    
    return RecommendResponse(
        isSuccess=True,
        code="MEALPLAN_200",
        message="AI 추천 식단 생성 요청 완료",
        result=result
    )

