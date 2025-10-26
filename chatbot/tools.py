"""
Agent Tools for CloudBread Chatbot
임산부 영양 챗봇을 위한 도구 모음
"""

from typing import Dict, List, Optional, Any
import os
import httpx
from datetime import datetime, date
from sqlalchemy import create_engine, text
from langchain.tools import tool
from langchain_core.tools import Tool
import asyncio


# ============================================
# 1. VLM Service Tools (Photo Label)
# ============================================

@tool
async def call_photo_label_service(image_url: str) -> Dict[str, Any]:
    """
    음식 사진을 VLM으로 분석하여 음식명과 신뢰도를 반환합니다.
    
    Args:
        image_url: 분석할 이미지 URL
        
    Returns:
        Dict with keys: label (음식명), confidence (신뢰도)
    """
    photo_label_url = os.getenv("PHOTO_LABEL_URL", "http://photo-label-svc.ai-services.svc.cluster.local")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{photo_label_url}/v1/photo-label",
                json={
                    "photoAnalysisId": f"chatbot_{datetime.now().timestamp()}",
                    "imageUrl": image_url
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "label": result.get("label", "알 수 없는 음식"),
                "confidence": result.get("confidence", 0.0),
                "success": result.get("success", False)
            }
    except Exception as e:
        return {
            "label": "분석 실패",
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }


# ============================================
# 2. Nutrition Feedback Service Tools
# ============================================

@tool
async def call_nutrition_feedback_service(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자의 영양 섭취 데이터를 기반으로 AI 피드백을 생성합니다.
    
    Args:
        user_data: 사용자 정보 (user_id, birth_date, due_date 등)
        
    Returns:
        영양 피드백 결과
    """
    nutrition_url = os.getenv("NUTRITION_FEEDBACK_URL", "http://nutrition-feedback-svc.ai-services.svc.cluster.local")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{nutrition_url}/api/v1/feedback",
                json=user_data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "feedback": result.get("feedback", ""),
                "recommendations": result.get("recommendations", []),
                "success": True
            }
    except Exception as e:
        return {
            "feedback": "피드백 생성 실패",
            "recommendations": [],
            "success": False,
            "error": str(e)
        }


# ============================================
# 3. Food Recommendation Service Tools
# ============================================

@tool
async def call_food_recommend_service(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 프로필 기반 맞춤 식단을 추천합니다.
    
    Args:
        user_profile: 사용자 프로필 (allergies, diets, health conditions 등)
        
    Returns:
        추천 식단 목록
    """
    food_recommend_url = os.getenv("FOOD_RECOMMEND_URL", "http://food-recommend-svc.ai-services.svc.cluster.local")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{food_recommend_url}/api/v1/recommend",
                json=user_profile
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "recommended_foods": result.get("result", {}).get("sections", []),
                "success": result.get("isSuccess", False),
                "message": result.get("message", "")
            }
    except Exception as e:
        return {
            "recommended_foods": [],
            "success": False,
            "error": str(e)
        }


# ============================================
# 4. Database Query Tools
# ============================================

def get_db_connection():
    """MySQL 데이터베이스 연결 생성"""
    db_url = f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'cloudbread')}"
    return create_engine(db_url, pool_pre_ping=True)


@tool
def query_nutrition_db(food_name: str) -> Dict[str, Any]:
    """
    음식 이름으로 데이터베이스에서 영양 정보를 조회합니다.
    
    Args:
        food_name: 조회할 음식명
        
    Returns:
        음식의 영양 정보 (칼로리, 영양소 등)
    """
    try:
        engine = get_db_connection()
        
        with engine.connect() as conn:
            # 음식 기본 정보 조회
            query = text("""
                SELECT f.id, f.name, f.calories, f.category, f.image_url
                FROM foods f
                WHERE f.name LIKE :food_name
                LIMIT 1
            """)
            
            result = conn.execute(query, {"food_name": f"%{food_name}%"}).fetchone()
            
            if not result:
                return {
                    "found": False,
                    "message": f"'{food_name}'에 대한 정보를 찾을 수 없습니다."
                }
            
            food_id, name, calories, category, image_url = result
            
            # 영양소 정보 조회
            nutrient_query = text("""
                SELECT n.name, fn.value, n.unit
                FROM food_nutrients fn
                JOIN nutrients n ON fn.nutrient_id = n.id
                WHERE fn.food_id = :food_id
                ORDER BY fn.value DESC
                LIMIT 10
            """)
            
            nutrients = conn.execute(nutrient_query, {"food_id": food_id}).fetchall()
            
            return {
                "found": True,
                "food_id": food_id,
                "name": name,
                "calories": float(calories) if calories else 0,
                "category": category,
                "image_url": image_url,
                "nutrients": [
                    {
                        "name": n[0],
                        "value": float(n[1]),
                        "unit": n[2]
                    } for n in nutrients
                ]
            }
            
    except Exception as e:
        return {
            "found": False,
            "error": str(e),
            "message": "데이터베이스 조회 중 오류가 발생했습니다."
        }


@tool
def query_user_food_history(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """
    사용자의 최근 식사 기록을 조회합니다.
    
    Args:
        user_id: 사용자 ID
        days: 조회할 기간 (일)
        
    Returns:
        식사 기록 목록
    """
    try:
        engine = get_db_connection()
        
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    ufh.id,
                    ufh.meal_type,
                    f.name as food_name,
                    f.calories,
                    ufh.intake_percent,
                    ufh.created_at
                FROM user_food_history ufh
                JOIN foods f ON ufh.food_id = f.id
                WHERE ufh.user_id = :user_id
                AND ufh.created_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
                ORDER BY ufh.created_at DESC
            """)
            
            results = conn.execute(query, {"user_id": user_id, "days": days}).fetchall()
            
            history = []
            for row in results:
                history.append({
                    "id": row[0],
                    "meal_type": row[1],
                    "food_name": row[2],
                    "calories": float(row[3]) if row[3] else 0,
                    "intake_percent": row[4],
                    "created_at": row[5].isoformat() if row[5] else None
                })
            
            return history
            
    except Exception as e:
        return []


@tool
def persist_user_history(user_id: int, food_id: int, meal_type: str, intake_percent: int) -> Dict[str, Any]:
    """
    사용자의 식사 기록을 데이터베이스에 저장합니다.
    
    Args:
        user_id: 사용자 ID
        food_id: 음식 ID
        meal_type: 식사 타입 (BREAKFAST, LUNCH, DINNER)
        intake_percent: 섭취량 퍼센트 (0-100)
        
    Returns:
        저장 결과
    """
    try:
        engine = get_db_connection()
        
        with engine.connect() as conn:
            query = text("""
                INSERT INTO user_food_history 
                (user_id, food_id, meal_type, intake_percent, created_at)
                VALUES (:user_id, :food_id, :meal_type, :intake_percent, NOW())
            """)
            
            conn.execute(query, {
                "user_id": user_id,
                "food_id": food_id,
                "meal_type": meal_type,
                "intake_percent": intake_percent
            })
            conn.commit()
            
            return {
                "success": True,
                "message": "식사 기록이 저장되었습니다."
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "식사 기록 저장 중 오류가 발생했습니다."
        }


# ============================================
# Tool Collection
# ============================================

def get_all_tools() -> List[Tool]:
    """에이전트가 사용할 모든 도구 목록 반환"""
    return [
        call_photo_label_service,
        call_nutrition_feedback_service,
        call_food_recommend_service,
        query_nutrition_db,
        query_user_food_history,
        persist_user_history
    ]
