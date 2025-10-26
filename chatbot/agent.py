"""
CRAG (Corrective Retrieval-Augmented Generation) Agent
LangGraph 기반 자율 에이전트 구현
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
import operator
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from tools import (
    query_nutrition_db,
    query_user_food_history
)
from vector_store import get_knowledge_base

import os


# ============================================
# State Definition
# ============================================

class AgentState(TypedDict):
    """에이전트의 상태를 정의"""
    
    # 입력
    user_message: str
    user_id: Optional[int]
    image_url: Optional[str]
    image_base64: Optional[str]
    
    # 대화 히스토리
    chat_history: Annotated[List[BaseMessage], operator.add]
    
    # 실행 계획
    plan: List[str]
    
    # 도구 실행 결과
    db_results: Dict[str, Any]
    rag_results: List[Document]
    
    # CRAG 관련
    relevance_grade: str  # 'Relevant' | 'Ambiguous' | 'Irrelevant'
    retry_count: int
    
    # 최종 응답
    final_answer: str
    intermediate_steps: List[str]


# ============================================
# LLM 초기화
# ============================================

def get_llm(temperature: float = 0.7):
    """OpenAI LLM 초기화"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )


# ============================================
# Node Functions
# ============================================

def planner_node(state: AgentState) -> AgentState:
    """
    Step 1: 사용자 입력을 분석하고 실행 계획 수립
    """
    llm = get_llm(temperature=0.3)
    
    system_prompt = """
당신은 임산부 영양 상담 전문가입니다.
사용자의 질문을 분석하여 어떤 정보가 필요한지 계획을 세우세요.

가능한 정보 소스:
1. 임산부 영양 지식 베이스 (RAG)
2. 내부 영양 데이터베이스 (음식의 영양 정보)
3. 사용자 식사 기록

질문의 유형에 따라 필요한 정보를 나열하세요.
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"사용자 질문: {state['user_message']}\n\n필요한 정보 소스를 나열하세요.")
    ]
    
    response = llm.invoke(messages)
    
    # 간단한 계획 추출 (실제로는 더 정교하게 구현 가능)
    plan = ["rag_search"]  # 기본적으로 RAG 검색 수행
    
    if any(keyword in state['user_message'] for keyword in ['칼로리', '영양', '성분', '음식']):
        plan.append("db_search")
    
    state['plan'] = plan
    state['intermediate_steps'] = [f"계획 수립: {', '.join(plan)}"]
    
    return state


def rag_retrieval_node(state: AgentState) -> AgentState:
    """
    Step 2: Vector DB에서 관련 지식 검색
    """
    kb = get_knowledge_base()
    
    # 사용자 메시지로 검색
    results = kb.similarity_search(state['user_message'], k=5)
    
    state['rag_results'] = results
    state['intermediate_steps'].append(f"RAG 검색 완료: {len(results)}개 문서 검색")
    
    return state


def grade_documents_node(state: AgentState) -> AgentState:
    """
    Step 3: LLM이 검색된 문서의 품질 평가 (Self-Correction)
    """
    llm = get_llm(temperature=0.0)
    
    if not state['rag_results']:
        state['relevance_grade'] = 'Irrelevant'
        state['intermediate_steps'].append("문서 평가: 검색 결과 없음 (Irrelevant)")
        return state
    
    # 검색된 문서 내용 결합
    docs_content = "\n\n".join([doc.page_content for doc in state['rag_results'][:3]])
    
    grade_prompt = f"""
다음 문서들이 사용자 질문에 답하기에 적절한지 평가하세요.

사용자 질문: {state['user_message']}

검색된 문서:
{docs_content}

평가 기준:
- Relevant: 질문에 직접적으로 답할 수 있는 정보 포함
- Ambiguous: 관련은 있으나 불충분한 정보
- Irrelevant: 질문과 무관한 내용

평가 결과만 출력하세요 (Relevant, Ambiguous, Irrelevant 중 하나):
"""
    
    response = llm.invoke([HumanMessage(content=grade_prompt)])
    grade = response.content.strip()
    
    # 응답 정규화
    if 'Relevant' in grade:
        state['relevance_grade'] = 'Relevant'
    elif 'Ambiguous' in grade:
        state['relevance_grade'] = 'Ambiguous'
    else:
        state['relevance_grade'] = 'Irrelevant'
    
    state['intermediate_steps'].append(f"문서 평가: {state['relevance_grade']}")
    
    return state


def db_query_node(state: AgentState) -> AgentState:
    """
    Step 5: 데이터베이스 조회
    """
    # 음식 이름 추출 (간단한 구현)
    food_keywords = ['닭가슴살', '시금치', '연어', '우유', '계란', '바나나', '브로콜리']
    
    found_food = None
    for keyword in food_keywords:
        if keyword in state['user_message']:
            found_food = keyword
            break
    
    if found_food:
        result = query_nutrition_db.invoke({"food_name": found_food})
        state['db_results'] = result
        state['intermediate_steps'].append(f"DB 조회: {found_food}")
    else:
        state['db_results'] = {"found": False}
        state['intermediate_steps'].append("DB 조회: 음식명 미발견")
    
    return state


def synthesize_node(state: AgentState) -> AgentState:
    """
    Step 6: 모든 정보를 종합하여 최종 답변 생성
    """
    llm = get_llm(temperature=0.7)
    
    # 컨텍스트 구성
    context_parts = []
    
    # RAG 결과
    if state.get('rag_results'):
        rag_content = "\n\n".join([doc.page_content for doc in state['rag_results'][:3]])
        context_parts.append(f"[임산부 영양 지식]\n{rag_content}")
    
    # DB 결과
    if state.get('db_results', {}).get('found'):
        db_data = state['db_results']
        db_content = f"음식명: {db_data['name']}\n칼로리: {db_data['calories']}kcal\n"
        if db_data.get('nutrients'):
            db_content += "주요 영양소:\n"
            for n in db_data['nutrients'][:5]:
                db_content += f"- {n['name']}: {n['value']}{n['unit']}\n"
        context_parts.append(f"[영양 데이터베이스]\n{db_content}")
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "관련 정보를 찾지 못했습니다."
    
    # 시스템 프롬프트
    system_prompt = """
당신은 CloudBread의 친근하고 전문적인 임산부 영양 상담 AI 어시스턴트입니다.

역할:
- 임산부의 건강과 영양에 최적화된 맞춤형 답변 제공
- 과학적 근거와 최신 정보를 바탕으로 조언
- 친근하고 이해하기 쉬운 한국어 사용
- 안전을 최우선으로 고려

답변 원칙:
1. 제공된 컨텍스트 정보를 우선 활용
2. 의학적 판단이 필요한 경우 의사 상담 권유
3. 긍정적이고 격려하는 톤 유지
4. 구체적이고 실용적인 조언 제공
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
다음 정보를 참고하여 사용자의 질문에 답변해주세요.

=== 참고 정보 ===
{context}

=== 사용자 질문 ===
{state['user_message']}

답변:
""")
    ]
    
    response = llm.invoke(messages)
    state['final_answer'] = response.content
    state['intermediate_steps'].append("최종 답변 생성 완료")
    
    return state


# ============================================
# Decision Functions
# ============================================

def decide_next_step(state: AgentState) -> str:
    """
    문서 평가 결과에 따라 다음 단계 결정
    """
    grade = state.get('relevance_grade', 'Relevant')
    retry_count = state.get('retry_count', 0)
    
    # Irrelevant나 Ambiguous 모두 한 번 더 재시도
    if (grade == 'Irrelevant' or grade == 'Ambiguous') and retry_count < 1:
        state['retry_count'] = retry_count + 1
        return 'rag_retrieval'  # RAG 재시도
    
    else:
        return 'synthesize'  # 최종 답변 생성 (지식 베이스 결과 활용)


def should_query_db(state: AgentState) -> str:
    """DB 조회 필요 여부 판단"""
    if 'db_search' in state.get('plan', []):
        return 'db_query'
    else:
        return 'synthesize'


# ============================================
# Graph Construction
# ============================================

def create_agent_graph():
    """LangGraph 워크플로우 생성"""
    
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("planner", planner_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("db_query", db_query_node)
    workflow.add_node("synthesize", synthesize_node)
    
    # 엣지 설정
    workflow.set_entry_point("planner")
    
    workflow.add_edge("planner", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "grade_documents")
    
    # 조건부 라우팅
    workflow.add_conditional_edges(
        "grade_documents",
        decide_next_step,
        {
            "rag_retrieval": "rag_retrieval",  # 재시도
            "synthesize": "db_query"  # DB 조회 여부 확인
        }
    )
    
    # DB 조회 후 최종 답변
    workflow.add_conditional_edges(
        "db_query",
        lambda state: "synthesize",
        {"synthesize": "synthesize"}
    )
    
    workflow.add_edge("synthesize", END)
    
    # 체크포인터 (세션 영속화) - MemorySaver 사용
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)


# ============================================
# Agent Runner
# ============================================

class ChatbotAgent:
    """챗봇 에이전트 래퍼 클래스"""
    
    def __init__(self):
        self.graph = create_agent_graph()
    
    async def run(
        self,
        user_message: str,
        user_id: Optional[int] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        thread_id: str = "default"
    ) -> Dict[str, Any]:
        """
        에이전트 실행
        
        Args:
            user_message: 사용자 메시지
            user_id: 사용자 ID (옵션)
            image_url: 이미지 URL (옵션)
            image_base64: 이미지 base64 (옵션)
            thread_id: 세션 ID
            
        Returns:
            최종 응답 및 중간 단계 정보
        """
        
        # 초기 상태 설정
        initial_state = {
            "user_message": user_message,
            "user_id": user_id,
            "image_url": image_url,
            "image_base64": image_base64,
            "chat_history": [],
            "plan": [],
            "db_results": {},
            "rag_results": [],
            "relevance_grade": "",
            "retry_count": 0,
            "final_answer": "",
            "intermediate_steps": []
        }
        
        # 그래프 실행
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = None
        for state in self.graph.stream(initial_state, config):
            final_state = state
        
        # 최종 노드의 상태 추출
        if final_state:
            last_node_state = list(final_state.values())[0]
            
            return {
                "response": last_node_state.get("final_answer", "답변을 생성할 수 없습니다."),
                "intermediate_steps": last_node_state.get("intermediate_steps", []),
                "plan": last_node_state.get("plan", []),
                "relevance_grade": last_node_state.get("relevance_grade", "")
            }
        
        return {
            "response": "답변을 생성할 수 없습니다.",
            "intermediate_steps": [],
            "plan": [],
            "relevance_grade": ""
        }


# 싱글톤 인스턴스
_agent_instance = None


def get_agent() -> ChatbotAgent:
    """에이전트 싱글톤 인스턴스 반환"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = ChatbotAgent()
    
    return _agent_instance
