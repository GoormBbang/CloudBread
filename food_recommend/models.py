from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# Request Models
class FoodHistory(BaseModel):
    mealType: str
    foodName: str
    intakePercent: int
    createdAt: datetime


class User(BaseModel):
    birthDate: str
    dueDate: str
    otherHealthFactors: Optional[List[str]] = []


class RecommendRequest(BaseModel):
    user: User
    healths: List[str] = []
    allergies: List[str] = []
    diets: List[str] = []
    foodHistory: List[FoodHistory] = []


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


class RecommendResult(BaseModel):
    planId: int
    planDate: str
    sections: List[MealSection]


class RecommendResponse(BaseModel):
    isSuccess: bool
    code: str
    message: str
    result: RecommendResult

