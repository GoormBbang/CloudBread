from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Image processing
from PIL import Image
import io
import base64
import asyncio

# Agent imports
from agent import get_agent
from vector_store import get_knowledge_base

load_dotenv()

# 벡터 스토어 초기화 (앱 시작 시)
try:
    kb = get_knowledge_base()
    print("✅ 지식 베이스 초기화 완료")
except Exception as e:
    print(f"⚠️ 지식 베이스 초기화 실패: {e}")

app = FastAPI(
    title="CloudBread ChatBot API",
    version="1.0.0",
    root_path="/api/chatbot"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델 정의
class ChatMessage(BaseModel):
    role: str  # "user" 또는 "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_history: List[ChatMessage]

class MultiModalRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    image_base64: Optional[str] = None

# 세션 기반 메모리 관리 (에이전트 기반으로 간소화)
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.agent = get_agent()
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "message_history": []
            }
        
        return session_id
    
    def get_session(self, session_id: str):
        return self.sessions.get(session_id)
    
    def add_message_to_history(self, session_id: str, role: str, content: str):
        if session_id in self.sessions:
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat()
            )
            self.sessions[session_id]["message_history"].append(message)

# 세션 매니저 인스턴스
session_manager = SessionManager()

@app.get("/")
async def root():
    return {"message": "CloudBread ChatBot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "chatbot"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    텍스트 기반 채팅 엔드포인트 (에이전트 기반)
    """
    try:
        # 세션 생성 또는 가져오기
        session_id = session_manager.get_or_create_session(request.session_id)
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=500, detail="세션을 생성할 수 없습니다.")
        
        # 사용자 메시지를 히스토리에 추가
        session_manager.add_message_to_history(session_id, "user", request.message)
        
        # 에이전트 실행
        agent_result = await session_manager.agent.run(
            user_message=request.message,
            thread_id=session_id
        )
        
        response_text = agent_result.get("response", "답변을 생성할 수 없습니다.")
        
        # AI 응답을 히스토리에 추가
        session_manager.add_message_to_history(session_id, "assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            message_history=session_data["message_history"]
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/chat/multimodal")
async def multimodal_chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    멀티모달 채팅 엔드포인트 (텍스트 + 이미지) - 에이전트 기반
    """
    try:
        # 세션 생성 또는 가져오기
        session_id = session_manager.get_or_create_session(session_id)
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=500, detail="세션을 생성할 수 없습니다.")
        
        # 이미지 처리
        image_description = ""
        image_base64 = None
        image_url = None
        
        if image:
            # 이미지 파일 읽기
            image_content = await image.read()
            
            # PIL로 이미지 처리
            try:
                pil_image = Image.open(io.BytesIO(image_content))
                
                # 이미지를 base64로 인코딩
                image_base64 = base64.b64encode(image_content).decode('utf-8')
                
                # 이미지 정보 추출
                image_description = f"\n[업로드된 이미지 정보: 크기 {pil_image.size}, 포맷 {pil_image.format}]\n"
                
            except Exception as img_error:
                image_description = f"이미지 처리 중 오류가 발생했습니다: {str(img_error)}"
        
        # 메시지에 이미지 정보 포함
        full_message = message
        if image_description:
            full_message += image_description
        
        # 사용자 메시지를 히스토리에 추가
        session_manager.add_message_to_history(session_id, "user", full_message)
        
        # 이미지가 있는 경우 Vision 모델로 직접 분석
        if image_base64:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            # GPT-4 Vision 모델 사용
            vision_llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # 이미지와 함께 분석 요청
            vision_message = HumanMessage(
                content=[
                    {"type": "text", "text": f"""
당신은 임산부 영양 전문가입니다.
이미지를 분석하고 사용자의 질문에 답변해주세요.

사용자 질문: {message}

임산부 관점에서 이 음식의:
1. 영양 정보
2. 임산부에게 좋은 점
3. 주의사항
을 알려주세요.
"""},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            )
            
            response = vision_llm.invoke([vision_message]).content
        else:
            # 텍스트만 있는 경우 에이전트 사용
            agent_result = await session_manager.agent.run(
                user_message=full_message,
                thread_id=session_id
            )
            response = agent_result.get("response", "답변을 생성할 수 없습니다.")
        
        # AI 응답을 히스토리에 추가
        session_manager.add_message_to_history(session_id, "assistant", response)
        
        return {
            "response": response,
            "session_id": session_id,
            "message_history": session_data["message_history"],
            "image_processed": image is not None
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"멀티모달 채팅 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    특정 세션의 채팅 히스토리 조회
    """
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return {
        "session_id": session_id,
        "message_history": session_data["message_history"],
        "created_at": session_data["created_at"].isoformat()
    }

@app.delete("/chat/session/{session_id}")
async def clear_session(session_id: str):
    """
    특정 세션 삭제
    """
    if session_id in session_manager.sessions:
        del session_manager.sessions[session_id]
        return {"message": f"세션 {session_id}가 삭제되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

@app.get("/chat/sessions")
async def list_sessions():
    """
    활성 세션 목록 조회
    """
    sessions_info = []
    for session_id, session_data in session_manager.sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "created_at": session_data["created_at"].isoformat(),
            "message_count": len(session_data["message_history"])
        })
    
    return {"active_sessions": sessions_info}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)