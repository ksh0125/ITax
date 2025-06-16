from vat_vector_search import VATVectorSearch
import os
import traceback

# 🚀 전역 검색 엔진 (서버 시작 시 한 번만 초기화)
search_engine = None

def initialize_vat_search_engine():
    """부가가치세법 검색 엔진 초기화"""
    global search_engine
    
    if search_engine is None:
        print("🚀 부가가치세법 RAG 검색 엔진 초기화 중...")
        
        # 전처리된 데이터 파일 확인
        if not os.path.exists("vat_law_processed.pkl"):
            print("❌ 전처리된 데이터가 없습니다!")
            print("   다음 명령을 실행해주세요: python vat_preprocessor.py")
            return False
        
        try:
            search_engine = VATVectorSearch()
            print("✅ 부가가치세법 RAG 검색 엔진 초기화 완료!")
            return True
        except Exception as init_error:
            print(f"❌ 검색 엔진 초기화 실패: {init_error}")
            print(f"❌ 상세 오류:\n{traceback.format_exc()}")
            return False
    
    return True

def search_vat_law(keyword: str, top_k: int = 5):
    """
    부가가치세법에서 키워드로 관련 조문 검색
    
    Args:
        keyword: 검색 키워드
        top_k: 반환할 결과 수
    
    Returns:
        검색 결과 딕셔너리
    """
    global search_engine
    
    # 검색 엔진이 초기화되지 않았으면 초기화
    if search_engine is None:
        if not initialize_vat_search_engine():
            return {
                "error": "검색 엔진을 초기화할 수 없습니다",
                "message": "전처리된 데이터가 없습니다. vat_preprocessor.py를 먼저 실행해주세요.",
                "keyword": keyword
            }
    
    try:
        print(f"🔍 부가가치세법 검색: '{keyword}'")
        
        # 벡터 검색 실행
        results = search_engine.search_and_aggregate(keyword, top_k=top_k)
        
        # 결과 포맷팅
        formatted_results = []
        for result in results['results']:
            # 관련 청크들을 하나의 문자열로 합치기
            relevant_chunks = result.get('relevant_chunks', [])
            relevant_text = " ".join(relevant_chunks) if relevant_chunks else ""
            
            formatted_results.append({
                "law_name": result['law_name'],
                "article_number": result['article_number'],
                "title": result['article_title'],
                "content": result['full_content'],
                "similarity": result['max_similarity'],
                "avg_similarity": result['avg_similarity'],
                "chunk_count": result['chunk_count'],
                "relevant_text": relevant_text[:500] + "..." if len(relevant_text) > 500 else relevant_text
            })
        
        print(f"✅ 부가가치세법 검색 완료: {len(formatted_results)}개 결과")
        
        return {
            "keyword": keyword,
            "results": formatted_results,
            "total_found": len(formatted_results),
            "search_method": "RAG (Vector Search)",
            "law_source": "부가가치세법",
            "status": "success"
        }
        
    except Exception as search_error:
        print(f"❌ 검색 오류: {search_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")
        return {
            "error": "검색 중 오류가 발생했습니다",
            "message": str(search_error),
            "keyword": keyword,
            "status": "error"
        }

def get_vat_search_statistics():
    """부가가치세법 검색 엔진 통계 정보"""
    global search_engine
    
    if search_engine is None or not search_engine.data:
        return {"error": "검색 엔진이 초기화되지 않았습니다"}
    
    try:
        stats = search_engine.get_statistics()
        stats["법령명"] = "부가가치세법"
        stats["설명"] = "부가가치세법 조문 기반 RAG 검색 시스템"
        
        return stats
    except Exception as stats_error:
        print(f"❌ 통계 조회 오류: {stats_error}")
        return {"error": f"통계 조회 실패: {str(stats_error)}"}

def find_related_articles(article_number: str, top_k: int = 3):
    """특정 조문과 관련된 다른 조문들 찾기"""
    global search_engine
    
    if search_engine is None:
        if not initialize_vat_search_engine():
            return {"error": "검색 엔진이 준비되지 않았습니다"}
    
    if not search_engine or not search_engine.data:
        return {"error": "검색 엔진이 준비되지 않았습니다"}
    
    try:
        # 해당 조문 찾기
        target_article = None
        for chunk in search_engine.data:
            if chunk['article_number'] == article_number:
                target_article = chunk
                break
        
        if not target_article:
            return {"error": f"{article_number}를 찾을 수 없습니다"}
        
        # 해당 조문의 내용으로 유사한 조문 검색
        results = search_vat_law(target_article['full_content'], top_k + 1)
        
        # 자기 자신 제외
        if 'results' in results:
            filtered_results = [r for r in results['results'] 
                              if r['article_number'] != article_number]
        else:
            filtered_results = []
        
        return {
            "base_article": article_number,
            "related_articles": filtered_results[:top_k],
            "total_found": len(filtered_results)
        }
        
    except Exception as related_error:
        print(f"❌ 관련 조문 검색 오류: {related_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")
        return {"error": f"관련 조문 검색 실패: {str(related_error)}"}

# 모듈 import 시 자동으로 초기화 시도
print("📚 부가가치세법 RAG 모듈 로딩 중...")
try:
    initialize_vat_search_engine()
except Exception as module_error:
    print(f"❌ 모듈 초기화 중 오류: {module_error}")

if __name__ == "__main__":
    # 직접 실행 시 테스트
    print("\n🧪 부가가치세법 RAG 시스템 테스트")
    print("="*60)
    
    # 통계 정보 출력
    stats = get_vat_search_statistics()
    if "error" not in stats:
        print(f"📊 부가가치세법 RAG 시스템 통계:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ 통계 오류: {stats['error']}")
    
    # 테스트 검색
    test_keywords = ["부가가치세 세율", "사업자", "재화의 공급", "납세의무"]
    
    for keyword in test_keywords:
        print(f"\n🔍 테스트: '{keyword}'")
        print("-" * 40)
        
        result = search_vat_law(keyword, top_k=3)
        
        if "error" in result:
            print(f"❌ 오류: {result['error']}")
            if "message" in result:
                print(f"   메시지: {result['message']}")
        else:
            print(f"📋 검색 결과: {result['total_found']}개 조문 발견")
            for i, item in enumerate(result['results'], 1):
                print(f"{i}. [{item['law_name']}] {item['article_number']} {item['title']}")
                print(f"   유사도: {item['similarity']:.4f}")
                print(f"   내용: {item['content'][:100]}...")
                print()
    
    # 관련 조문 검색 테스트
    print(f"\n🔗 관련 조문 검색 테스트: '제30조'와 관련된 조문들")
    print("-" * 50)
    
    related = find_related_articles("제30조", top_k=3)
    if "error" in related:
        print(f"❌ 오류: {related['error']}")
    else:
        print(f"📋 {related['base_article']}와 관련된 {len(related['related_articles'])}개 조문:")
        for i, article in enumerate(related['related_articles'], 1):
            print(f"{i}. {article['article_number']} {article['title']}")
            print(f"   유사도: {article['similarity']:.4f}")
            print(f"   내용: {article['content'][:100]}...")
            print()