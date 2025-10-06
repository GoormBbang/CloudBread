# 식단 추천 시스템 설계

## 1. 개요

임산부를 위한 개인화된 식단 추천 시스템으로, 사용자의 건강 상태, 알레르기, 식단 선호도, 섭취 이력을 기반으로 하루 3끼 식단을 추천합니다.

## 2. DB 구조

### 2.1 사용 테이블
- **foods**: 음식 기본 정보
  - id, name, calories, category, source_name (portion label로 사용)
- **nutrients**: 영양소 정보  
  - name (SODIUM, SUGARS, PROTEINS 등)
- **food_nutrients**: 음식별 영양소 함량
  - food_id, nutrient_id, value

### 2.2 필요한 정보 추출
- `foods.id` → `FoodItem.foodId`
- `foods.name` → `FoodItem.name`
- `foods.source_name` → `FoodItem.portionLabel` (예: "100g")
- `foods.calories` → `FoodItem.estCalories`
- `foods.category` → `FoodItem.foodCategory`

## 3. 추천 로직

### 3.1 필터링 단계

#### 단계 1: 알레르기 필터링
- request.allergies에 포함된 키워드가 음식명에 있으면 제외
- 예: "땅콩", "견과류" → "땅콩버터", "호두" 제외

#### 단계 2: 건강 상태 기반 필터링
- **고혈압**: SODIUM 낮은 음식 우선 (저염식)
- **임신성 당뇨**: SUGARS 낮은 음식 우선 (저당식)

#### 단계 3: 식단 선호도 반영
- **채식**: 육류 카테고리 제외 ("육류", "고기" 키워드 필터링)
- **저염식**: SODIUM 낮은 순으로 정렬
- **저당식**: SUGARS 낮은 순으로 정렬

#### 단계 4: 다양성 확보
- foodHistory에서 최근 섭취한 음식은 추천에서 제외
- 각 끼니마다 다른 카테고리의 음식 선택

### 3.2 끼니별 구성 로직

각 끼니는 3가지 기준으로 구성:
1. **주식 (밥류)**: 1개 필수
2. **국/탕**: 1개 
3. **반찬**: 1-2개

**칼로리 목표**:
- 아침: 450-550 kcal
- 점심: 550-650 kcal  
- 저녁: 500-600 kcal

### 3.3 추천 순서

1. 필터링된 음식 목록 생성
2. 카테고리별로 음식 분류
3. 각 끼니별로:
   - 밥류에서 1개 선택
   - 국/탕류에서 1개 선택
   - 나머지 반찬류에서 1-2개 선택
   - 총 칼로리가 목표 범위에 맞도록 조정
4. 최근 섭취 이력과 중복 최소화

## 4. 구현 모듈

### 4.1 모듈 구조

```
service.py
├── generate_food_recommendation()  # 메인 추천 함수
├── fetch_foods_from_db()           # DB에서 음식 조회
├── filter_by_allergies()           # 알레르기 필터링
├── filter_by_health()              # 건강 상태 필터링
├── filter_by_diet()                # 식단 선호도 필터링
├── exclude_recent_foods()          # 최근 섭취 음식 제외
├── select_meal_items()             # 끼니별 음식 선택
└── build_meal_section()            # MealSection 생성
```

### 4.2 DB 연결
- `db_example/db_connection.py`의 `get_connection()` 재사용
- pymysql DictCursor 사용으로 dict 형태로 결과 반환

## 5. 제약 사항 및 고려사항

### 5.1 준수 사항
- ✅ Request/Response 형식 유지
- ✅ 실제 DB 데이터 사용 (foodId는 foods.id)
- ✅ Request의 모든 정보 활용 (user, healths, allergies, diets, foodHistory)

### 5.2 단순화 원칙
- 복잡한 ML 모델 사용 안 함
- 규칙 기반(rule-based) 추천
- 필터링 + 랜덤 선택으로 구현

### 5.3 확장 가능성
- 향후 협업 필터링, 영양소 최적화 등 고도화 가능
- 현재는 최소 기능으로 동작하는 시스템 구축

## 6. 응답 예시

```json
{
  "isSuccess": true,
  "code": "MEALPLAN_200",
  "message": "AI 추천 식단 생성 요청 완료",
  "result": {
    "planId": 6569,
    "planDate": "2025-10-06",
    "sections": [
      {
        "mealType": "BREAKFAST",
        "totalKcal": 520,
        "items": [
          {
            "foodId": 14588,
            "name": "기장밥",
            "portionLabel": "100g",
            "estCalories": 166,
            "foodCategory": "밥류"
          }
        ]
      }
    ]
  }
}
```

