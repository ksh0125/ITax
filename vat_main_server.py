from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional
import traceback

# vat_rag_service 모듈 import (정확한 파일명 사용)
try:
    from vat_rag_service import search_vat_law, get_vat_search_statistics, find_related_articles
    print("✅ 부가가치세법 RAG 모듈 로딩 성공")
except Exception as import_error:
    print(f"❌ 부가가치세법 RAG 모듈 로딩 실패: {import_error}")
    print(f"❌ 상세 오류:\n{traceback.format_exc()}")
    
    def search_vat_law(keyword, top_k=5):
        return {"error": "RAG 모듈을 불러올 수 없습니다", "message": str(import_error)}
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
    except Exception as stats_error:
        print(f"❌ 통계 조회 오류: {stats_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(stats_error)}")

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
            print(f"❌ 검색 중 오류: {results['error']}")
            if "message" in results:
                print(f"❌ 오류 메시지: {results['message']}")
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "success": True,
            "query": keyword,
            "results": results.get("results", []),
            "total_found": results.get("total_found", 0),
            "search_method": results.get("search_method", "RAG"),
            "law_source": results.get("law_source", "부가가치세법")
        }
        
    except HTTPException:
        raise
    except Exception as search_error:
        print(f"❌ 검색 API 오류: {search_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(search_error)}")

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
            print(f"❌ 관련 조문 검색 오류: {results['error']}")
            raise HTTPException(status_code=404, detail=results["error"])
        
        return {
            "success": True,
            "base_article": results.get("base_article"),
            "related_articles": results.get("related_articles", []),
            "total_found": results.get("total_found", 0)
        }
        
    except HTTPException:
        raise
    except Exception as related_error:
        print(f"❌ 관련 조문 검색 API 오류: {related_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"관련 조문 검색 중 오류 발생: {str(related_error)}")

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
    except Exception as health_error:
        print(f"❌ 헬스체크 오류: {health_error}")
        return {
            "status": "unhealthy",
            "error": str(health_error),
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