import os
import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()


async def analyze_food_image(image_url: str) -> tuple[str, float]:
    """
    VLM을 사용하여 음식 이미지를 분석하고 음식명과 신뢰도를 반환
    """
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """이 이미지에 있는 음식의 이름을 한국어로 정확하게 알려주세요. 
                
응답 형식:
음식명: [음식 이름]
신뢰도: [0.0~1.0 사이의 숫자]

예시:
음식명: 김치찌개
신뢰도: 0.95"""
            },
            {
                "type": "image_url",
                "image_url": {"url": image_url}
            }
        ]
    )
    
    response = await llm.ainvoke([message])
    content = response.content
    
    # 응답 파싱
    label = ""
    confidence = 0.8
    
    lines = content.strip().split('\n')
    for line in lines:
        if '음식명:' in line or '음식명 :' in line:
            label = line.split(':', 1)[1].strip()
        elif '신뢰도:' in line or '신뢰도 :' in line:
            try:
                confidence_str = line.split(':', 1)[1].strip()
                confidence = float(confidence_str)
            except:
                confidence = 0.8
    
    # 라벨이 추출되지 않은 경우 전체 응답을 라벨로 사용
    if not label:
        label = content.strip()
    
    return label, confidence


def send_result_to_backend(photo_analysis_id: int, label: str, confidence: float, backend_url: str):
    """
    분석 결과를 백엔드로 전송
    """
    response = requests.post(
        f"{backend_url}/api/ai/photo-analyses/{photo_analysis_id}/label",
        json={
            "label": label,
            "confidence": confidence
        },
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()

