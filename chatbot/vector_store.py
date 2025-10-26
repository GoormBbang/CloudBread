"""
Vector Store for Pregnancy Nutrition Knowledge Base
임산부 영양 지식 베이스를 위한 벡터 스토어
"""

import os
from typing import List, Optional
from pathlib import Path
import pickle
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class PregnancyKnowledgeBase:
    """임산부 영양 지식 베이스 관리 클래스"""
    
    def __init__(
        self,
        knowledge_base_dir: str = "knowledge_base",
        vector_store_path: str = "vector_store",
        embedding_model: str = "text-embedding-3-small"
    ):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.vector_store_path = Path(vector_store_path)
        self.embedding_model = embedding_model
        
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.vectorstore: Optional[FAISS] = None
        
    def load_or_create_vectorstore(self) -> FAISS:
        """벡터 스토어를 로드하거나 새로 생성"""
        
        # 기존 벡터 스토어가 있으면 로드
        if self.vector_store_path.exists():
            print(f"📚 기존 벡터 스토어 로드 중: {self.vector_store_path}")
            try:
                self.vectorstore = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ 벡터 스토어 로드 완료")
                return self.vectorstore
            except Exception as e:
                print(f"⚠️ 벡터 스토어 로드 실패: {e}")
                print("새로운 벡터 스토어를 생성합니다.")
        
        # 새로운 벡터 스토어 생성
        print(f"🔨 새로운 벡터 스토어 생성 중...")
        documents = self._load_documents()
        
        if not documents:
            print("⚠️ 문서가 없습니다. 기본 지식으로 벡터 스토어 생성")
            documents = self._create_default_documents()
        
        chunks = self._split_documents(documents)
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # 벡터 스토어 저장
        self.save_vectorstore()
        
        return self.vectorstore
    
    def _load_documents(self) -> List[Document]:
        """지식 베이스 디렉토리에서 문서 로드"""
        
        if not self.knowledge_base_dir.exists():
            print(f"⚠️ 지식 베이스 디렉토리가 없습니다: {self.knowledge_base_dir}")
            return []
        
        documents = []
        
        # .txt 파일 로드
        try:
            loader = DirectoryLoader(
                str(self.knowledge_base_dir),
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            documents.extend(loader.load())
            print(f"📄 {len(documents)}개의 문서 로드 완료")
        except Exception as e:
            print(f"⚠️ 문서 로드 실패: {e}")
        
        return documents
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """문서를 작은 청크로 분할"""
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 한국어 특성 고려
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✂️ {len(chunks)}개의 청크로 분할 완료")
        
        return chunks
    
    def _create_default_documents(self) -> List[Document]:
        """기본 임산부 영양 지식 문서 생성"""
        
        default_knowledge = [
            Document(
                page_content="""
                임신 초기(1-3개월) 영양 가이드
                
                임신 초기는 태아의 신경관 형성이 이루어지는 중요한 시기입니다.
                
                필수 영양소:
                - 엽산(Folic Acid): 하루 600μg 권장. 신경관 결손 예방에 필수
                - 철분: 하루 24mg 권장. 빈혈 예방
                - 칼슘: 하루 930mg 권장. 태아 골격 형성
                
                권장 음식:
                - 시금치, 브로콜리 (엽산 풍부)
                - 붉은 살코기, 계란 (철분 풍부)
                - 우유, 요거트, 치즈 (칼슘 풍부)
                
                주의사항:
                - 날것이나 덜 익힌 육류 피하기
                - 고카페인 음료 제한 (하루 200mg 이하)
                - 알코올 완전 금지
                """,
                metadata={"category": "임신단계", "stage": "초기"}
            ),
            Document(
                page_content="""
                임신 중기(4-6개월) 영양 가이드
                
                임신 중기는 태아가 빠르게 성장하는 시기로 충분한 영양 섭취가 필요합니다.
                
                필수 영양소:
                - 단백질: 하루 71g 권장. 태아 성장에 필수
                - DHA: 하루 200-300mg 권장. 뇌 발달
                - 비타민 D: 하루 10μg 권장. 칼슘 흡수 촉진
                
                권장 음식:
                - 연어, 고등어 (DHA 풍부)
                - 닭가슴살, 두부 (단백질 풍부)
                - 달걀 노른자, 표고버섯 (비타민 D)
                
                체중 관리:
                - 정상 체중: 주당 0.4kg 증가 권장
                - 저체중: 주당 0.5kg 증가 권장
                - 과체중: 주당 0.2kg 증가 권장
                """,
                metadata={"category": "임신단계", "stage": "중기"}
            ),
            Document(
                page_content="""
                임신 후기(7-9개월) 영양 가이드
                
                임신 후기는 출산 준비와 태아의 최종 성장이 이루어지는 시기입니다.
                
                필수 영양소:
                - 철분: 하루 27mg 권장 (증량). 출산 시 혈액 손실 대비
                - 칼슘: 하루 1000mg 권장. 태아 뼈 강화
                - 오메가-3: 뇌 발달 마무리
                
                권장 음식:
                - 소고기, 시금치 (철분)
                - 멸치, 뱅어포 (칼슘)
                - 호두, 아마씨 (오메가-3)
                
                주의사항:
                - 부종 관리: 짠 음식 제한
                - 변비 예방: 섬유질 충분히 섭취
                - 소화 불편: 소량씩 자주 먹기
                """,
                metadata={"category": "임신단계", "stage": "후기"}
            ),
            Document(
                page_content="""
                임산부가 피해야 할 음식
                
                임신 중 섭취를 피하거나 제한해야 하는 음식들이 있습니다.
                
                완전 금지:
                - 생선회, 육회 등 날것
                - 덜 익힌 계란, 고기
                - 알코올 음료
                - 비살균 유제품
                - 리스테리아 위험 식품 (훈제 연어, 패스트푸드 샐러드)
                
                제한 필요:
                - 카페인: 하루 200mg 이하 (커피 2잔)
                - 참치 등 수은 함량 높은 생선: 주 1회 이하
                - 가공육: 최소화
                - 인스턴트 식품: 최소화
                
                대체 방안:
                - 카페인 → 디카페인 커피, 보리차
                - 생선회 → 구운 생선
                - 가공육 → 신선한 육류
                """,
                metadata={"category": "주의음식", "type": "금지"}
            ),
            Document(
                page_content="""
                입덧 대처 방법
                
                임신 초기 입덧은 많은 임산부가 겪는 증상입니다.
                
                식습관 조절:
                - 소량씩 자주 먹기 (5-6회 분할 섭취)
                - 아침 기상 시 크래커나 비스킷 먹기
                - 물을 충분히 마시기 (하루 8잔)
                - 기름진 음식, 향이 강한 음식 피하기
                
                도움이 되는 음식:
                - 생강차 (메스꺼움 완화)
                - 레몬물 (입맛 개선)
                - 바나나 (소화 편함)
                - 토스트, 크래커 (속 진정)
                
                심한 경우:
                - 수분 섭취가 어려운 경우 의사 상담
                - 체중 감소가 심한 경우 병원 방문
                - 비타민 B6 보충제 고려
                """,
                metadata={"category": "건강관리", "symptom": "입덧"}
            ),
            Document(
                page_content="""
                임산부 영양제 가이드
                
                균형잡힌 식사를 하더라도 영양제가 필요할 수 있습니다.
                
                필수 영양제:
                1. 종합비타민 (Prenatal Vitamin)
                   - 엽산 400-800μg 함유
                   - 철분, 칼슘, 비타민 D 포함
                   
                2. 엽산 (Folic Acid)
                   - 임신 전~임신 12주: 하루 400-600μg
                   - 신경관 결손 예방
                   
                3. 철분
                   - 임신 중~후기: 하루 30-60mg
                   - 빈혈 예방
                   
                선택적 영양제:
                - DHA: 하루 200-300mg (생선 섭취 부족 시)
                - 칼슘: 하루 500-1000mg (유제품 섭취 부족 시)
                - 비타민 D: 하루 10μg (햇빛 노출 부족 시)
                
                주의사항:
                - 의사와 상담 후 복용
                - 과다 복용 주의
                - 식후 복용 권장
                """,
                metadata={"category": "영양제", "type": "가이드"}
            )
        ]
        
        print(f"📝 {len(default_knowledge)}개의 기본 지식 문서 생성")
        return default_knowledge
    
    def save_vectorstore(self):
        """벡터 스토어를 디스크에 저장"""
        if self.vectorstore:
            self.vector_store_path.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(self.vector_store_path))
            print(f"💾 벡터 스토어 저장 완료: {self.vector_store_path}")
    
    def add_documents(self, documents: List[Document]):
        """새로운 문서를 벡터 스토어에 추가"""
        if not self.vectorstore:
            self.load_or_create_vectorstore()
        
        chunks = self._split_documents(documents)
        self.vectorstore.add_documents(chunks)
        self.save_vectorstore()
        print(f"✅ {len(chunks)}개의 청크 추가 완료")
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Document]:
        """유사도 검색 수행"""
        if not self.vectorstore:
            self.load_or_create_vectorstore()
        
        # 유사도 점수와 함께 검색
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # 점수 필터링
        filtered_docs = [
            doc for doc, score in docs_with_scores
            if score >= score_threshold
        ]
        
        return filtered_docs
    
    def get_retriever(self, k: int = 5):
        """Retriever 객체 반환 (LangChain 체인에서 사용)"""
        if not self.vectorstore:
            self.load_or_create_vectorstore()
        
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )


# 싱글톤 인스턴스
_knowledge_base_instance = None


def get_knowledge_base() -> PregnancyKnowledgeBase:
    """지식 베이스 싱글톤 인스턴스 반환"""
    global _knowledge_base_instance
    
    if _knowledge_base_instance is None:
        _knowledge_base_instance = PregnancyKnowledgeBase()
        _knowledge_base_instance.load_or_create_vectorstore()
    
    return _knowledge_base_instance


if __name__ == "__main__":
    # 테스트 코드
    kb = PregnancyKnowledgeBase()
    kb.load_or_create_vectorstore()
    
    # 검색 테스트
    results = kb.similarity_search("임신 초기 엽산 섭취량", k=3)
    
    print("\n=== 검색 결과 ===")
    for i, doc in enumerate(results, 1):
        print(f"\n[{i}] {doc.metadata}")
        print(doc.page_content[:200])
