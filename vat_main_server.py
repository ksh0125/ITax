from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional

# vat_rag 모듈 import
try:
    from vat_rag import search_vat_law, get_vat_search_statistics, find_related_articles
    print("✅ 부가가치세법 RAG 모듈 로딩 성공")
except Exception as e:
    print(f"❌ 부가가치세법 RAG 모듈 로딩 실패: {e}")
    def search_vat_law(keyword, top_k=5):
        return {"error": "RAG 모듈을 불러올 수 없습니다", "message": str(e)}
    def get_vat_search_statistics():
        return {"error": "RAG 모듈을 불러올 수 없습니다"}
    def find_related_articles(article_number, top_k=3):
        return {"error": "RAG 모듈을 불러올 수 없습니다"}

app = FastAPI(
    title="부가가치세법 RAG 검색 시스템",
    description="AI 기반 부가가치세법 조문 검색 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    keywords: str
    max_results: Optional[int] = 5

class RelatedArticleRequest(BaseModel):
    article_number: str
    max_results: Optional[int] = 3

@app.get("/")
def home():
    """서비스 홈"""
    return {
        "service": "부가가치세법 RAG 검색 시스템",
        "description": "AI 기반 부가가치세법 조문 검색 서비스",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "/search-law",
            "related": "/related-articles",
            "stats": "/statistics",
            "docs": "/docs"
        }
    }

@app.get("/statistics")
def get_statistics():
    """검색 엔진 통계 정보"""
    try:
        stats = get_vat_search_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@app.post("/search-law")
def search_law(request: SearchRequest):
    """부가가치세법 조문 검색"""
    try:
        keyword = request.keywords.strip()
        if not keyword:
            raise HTTPException(status_code=400, detail="검색 키워드를 입력해주세요")
        
        max_results = min(request.max_results, 20)  # 최대 20개로 제한
        
        print(f"🔍 검색 요청: '{keyword}' (최대 {max_results}개)")
        
        results = search_vat_law(keyword, top_k=max_results)
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "query": keyword,
            "results": results["results"],
            "total_found": results["total_found"],
            "search_method": results["search_method"],
            "law_source": results["law_source"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.post("/related-articles")
def get_related_articles(request: RelatedArticleRequest):
    """특정 조문과 관련된 다른 조문들 검색"""
    try:
        article_number = request.article_number.strip()
        if not article_number:
            raise HTTPException(status_code=400, detail="조문 번호를 입력해주세요")
        
        max_results = min(request.max_results, 10)
        
        print(f"🔗 관련 조문 검색: '{article_number}' (최대 {max_results}개)")
        
        results = find_related_articles(article_number, top_k=max_results)
        
        if "error" in results:
            raise HTTPException(status_code=404, detail=results["error"])
        
        return {
            "success": True,
            "base_article": results["base_article"],
            "related_articles": results["related_articles"],
            "total_found": results["total_found"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 관련 조문 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"관련 조문 검색 중 오류 발생: {str(e)}")

@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    try:
        # 간단한 검색으로 시스템 상태 확인
        test_result = search_vat_law("부가가치세", top_k=1)
        
        return {
            "status": "healthy",
            "service": "부가가치세법 RAG 검색 시스템",
            "search_engine": "ready" if "error" not in test_result else "error",
            "timestamp": "2025-06-16"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-06-16"
        }

@app.get("/sample-queries")
def get_sample_queries():
    """샘플 검색 쿼리 제공"""
    return {
        "sample_queries": [
            "부가가치세 세율",
            "사업자 정의",
            "재화의 공급",
            "납세의무자",
            "세금계산서",
            "면세 대상",
            "과세표준",
            "간이과세자"
        ],
        "sample_articles": [
            "제1조",
            "제2조", 
            "제30조",
            "제31조"
        ],
        "usage_tips": [
            "구체적인 키워드를 사용하세요 (예: '부가가치세 세율')",
            "조문 번호로도 검색 가능합니다 (예: '제30조')",
            "관련 조문 기능을 활용해보세요",
            "검색 결과는 유사도 순으로 정렬됩니다"
        ]
    }

if __name__ == "__main__":
    print("🚀 부가가치세법 RAG 검색 서버 시작...")
    print("📍 서버 주소: http://127.0.0.1:8000")
    print("📍 API 문서: http://127.0.0.1:8000/docs")
    print("📍 대화형 문서: http://127.0.0.1:8000/redoc")
    print("🔄 서버를 중지하려면 Ctrl+C를 누르세요")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )