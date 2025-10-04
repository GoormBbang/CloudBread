from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MealType(str, Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"


# Request Models
class FoodHistory(BaseModel):
    meal_type: str
    food_name: str
    intake_percent: int
    created_at: datetime


class User(BaseModel):
    birth_date: str
    due_date: str
    other_health_factors: Optional[List[str]] = []


class RecommendRequest(BaseModel):
    user: User
    healths: List[str] = []
    allergies: List[str] = []
    diets: List[str] = []
    food_history: List[FoodHistory] = []


# Response Models
class FoodItem(BaseModel):
    foodId: int
    name: str
    portionLabel: str
    estCalories: int
    foodCategory: str


class MealSection(BaseModel):
    mealType: str
    totalKcal: int
    items: List[FoodItem]


class RecommendResponse(BaseModel):
    planId: int
    planDate: str
    sections: List[MealSection]

