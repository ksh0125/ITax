import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import traceback

class VATVectorSearch:
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli", data_file: str = "vat_law_processed.pkl"):
        """부가가치세법 벡터 검색 엔진 초기화"""
        print("🚀 부가가치세법 벡터 검색 엔진 초기화 중...")
        
        # 모델 로딩
        print("⏳ AI 모델 로딩 중...")
        try:
            self.model = SentenceTransformer(model_name)
            print("✅ 모델 로딩 완료!")
        except Exception as model_error:
            print(f"❌ 모델 로딩 실패: {model_error}")
            raise
        
        # 전처리된 데이터 로딩
        self.data = self._load_data(data_file)
        self.embeddings_matrix = self._create_embeddings_matrix()
        
        print(f"✅ 검색 엔진 준비 완료: {len(self.data)}개 청크")
    
    def _load_data(self, data_file: str) -> List[Dict]:
        """전처리된 데이터 로드"""
        print(f"📂 '{data_file}' 로딩 중...")
        try:
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            print(f"✅ 데이터 로딩 완료: {len(data)}개 청크")
            return data
        except FileNotFoundError:
            print(f"❌ '{data_file}' 파일을 찾을 수 없습니다!")
            print("   먼저 'python vat_preprocessor.py'를 실행해주세요.")
            return []
        except Exception as load_error:
            print(f"❌ 데이터 로딩 오류: {load_error}")
            print(f"❌ 상세 오류:\n{traceback.format_exc()}")
            return []
    
    def _create_embeddings_matrix(self) -> np.ndarray:
        """임베딩을 numpy 행렬로 변환"""
        if not self.data:
            return np.array([])
        
        print("🔢 임베딩 행렬 생성 중...")
        try:
            embeddings = [chunk['embedding'] for chunk in self.data]
            matrix = np.array(embeddings)
            print(f"✅ 임베딩 행렬 생성 완료: {matrix.shape}")
            return matrix
        except Exception as matrix_error:
            print(f"❌ 임베딩 행렬 생성 오류: {matrix_error}")
            print(f"❌ 상세 오류:\n{traceback.format_exc()}")
            return np.array([])
    
    def search(self, query: str, top_k: int = 10, similarity_threshold: float = 0.1) -> List[Dict]:
        """쿼리와 유사한 청크 검색"""
        if not self.data or self.embeddings_matrix.size == 0:
            print("❌ 검색 데이터가 없습니다")
            return []
        
        print(f"🔍 '{query}' 검색 중...")
        
        try:
            # 쿼리 벡터화
            query_embedding = self.model.encode([query])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_embedding, self.embeddings_matrix)[0]
            
            # 유사도 순으로 정렬
            similar_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in similar_indices[:top_k]:
                similarity = similarities[idx]
                
                # 임계값 이상인 결과만 포함
                if similarity >= similarity_threshold:
                    chunk_data = self.data[idx].copy()
                    chunk_data['similarity'] = float(similarity)
                    results.append(chunk_data)
            
            print(f"✅ {len(results)}개 관련 청크 발견")
            return results
            
        except Exception as search_error:
            print(f"❌ 검색 오류: {search_error}")
            print(f"❌ 상세 오류:\n{traceback.format_exc()}")
            return []
    
    def search_and_aggregate(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """검색 후 조문별로 집계"""
        try:
            chunks = self.search(query, top_k * 2)  # 더 많이 검색해서 집계
            
            if not chunks:
                return {
                    'query': query,
                    'total_chunks_found': 0,
                    'unique_articles': 0,
                    'results': []
                }
            
            # 조문별로 그룹화
            article_groups = {}
            for chunk in chunks:
                article_key = f"{chunk['law_name']}_{chunk['article_number']}"
                
                if article_key not in article_groups:
                    article_groups[article_key] = {
                        'law_name': chunk['law_name'],
                        'article_number': chunk['article_number'],
                        'article_title': chunk['article_title'],
                        'full_content': chunk['full_content'],
                        'max_similarity': chunk['similarity'],
                        'avg_similarity': chunk['similarity'],
                        'chunk_count': 1,
                        'relevant_chunks': [chunk['chunk_content']]
                    }
                else:
                    group = article_groups[article_key]
                    group['max_similarity'] = max(group['max_similarity'], chunk['similarity'])
                    group['avg_similarity'] = (group['avg_similarity'] * group['chunk_count'] + chunk['similarity']) / (group['chunk_count'] + 1)
                    group['chunk_count'] += 1
                    group['relevant_chunks'].append(chunk['chunk_content'])
            
            # 최고 유사도 순으로 정렬
            aggregated_results = list(article_groups.values())
            aggregated_results.sort(key=lambda x: x['max_similarity'], reverse=True)
            
            return {
                'query': query,
                'total_chunks_found': len(chunks),
                'unique_articles': len(aggregated_results),
                'results': aggregated_results[:top_k]
            }
            
        except Exception as aggregate_error:
            print(f"❌ 집계 오류: {aggregate_error}")
            print(f"❌ 상세 오류:\n{traceback.format_exc()}")
            return {
                'query': query,
                'total_chunks_found': 0,
                'unique_articles': 0,
                'results': [],
                'error': str(aggregate_error)
            }
    
    def get_statistics(self):
        """검색 엔진 통계"""
        try:
            if not self.data:
                return {"error": "데이터가 로딩되지 않았습니다"}
            
            article_count = len(set(chunk['article_number'] for chunk in self.data))
            
            return {
                "총_청크수": len(self.data),
                "총_조문수": article_count,
                "임베딩_차원": self.data[0]['embedding_dim'] if self.data else 0,
                "모델명": "jhgan/ko-sbert-nli",
                "상태": "준비완료"
            }
        except Exception as stats_error:
            print(f"❌ 통계 조회 오류: {stats_error}")
            return {"error": f"통계 조회 실패: {str(stats_error)}"}

def test_search_engine():
    """검색 엔진 테스트"""
    try:
        search_engine = VATVectorSearch()
        
        if not search_engine.data:
            print("❌ 데이터가 없습니다. 먼저 전처리를 실행해주세요.")
            return
        
        # 테스트 쿼리들
        test_queries = [
            "부가가치세 세율",
            "사업자 정의",
            "재화 공급",
            "납세의무자"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 테스트 쿼리: '{query}'")
            print('='*60)
            
            results = search_engine.search_and_aggregate(query, top_k=3)
            
            if 'error' in results:
                print(f"❌ 검색 오류: {results['error']}")
                continue
            
            print(f"📊 검색 결과: {results['total_chunks_found']}개 청크, {results['unique_articles']}개 조문")
            
            for i, result in enumerate(results['results'], 1):
                print(f"\n{i}. [{result['law_name']}] {result['article_number']}")
                print(f"   📋 제목: {result['article_title']}")
                print(f"   🎯 최대 유사도: {result['max_similarity']:.4f}")
                print(f"   📊 평균 유사도: {result['avg_similarity']:.4f}")
                print(f"   🔢 매칭 청크 수: {result['chunk_count']}")
                print(f"   📄 내용: {result['full_content'][:200]}...")
                
    except Exception as test_error:
        print(f"❌ 테스트 오류: {test_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")

def main():
    """메인 실행"""
    print("🧪 부가가치세법 벡터 검색 엔진 테스트")
    print("="*60)
    
    try:
        search_engine = VATVectorSearch()
        
        # 통계 출력
        stats = search_engine.get_statistics()
        if "error" not in stats:
            print(f"📊 검색 엔진 통계:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ 통계 오류: {stats['error']}")
            return
        
        # 대화형 검색
        print("\n💬 대화형 검색 시작 (종료: 'quit')")
        while True:
            try:
                query = input("\n🔍 검색어를 입력하세요: ").strip()
                
                if query.lower() in ['quit', 'exit', '종료', 'q']:
                    print("👋 검색을 종료합니다.")
                    break
                
                if not query:
                    continue
                
                results = search_engine.search_and_aggregate(query, top_k=3)
                
                if 'error' in results:
                    print(f"❌ 검색 오류: {results['error']}")
                    continue
                
                if not results['results']:
                    print("❌ 검색 결과가 없습니다.")
                    continue
                
                print(f"\n📋 '{query}' 검색 결과:")
                print("-" * 50)
                
                for i, result in enumerate(results['results'], 1):
                    print(f"\n{i}. {result['article_number']} {result['article_title']}")
                    print(f"   유사도: {result['max_similarity']:.3f}")
                    print(f"   내용: {result['full_content'][:150]}...")
                    
            except KeyboardInterrupt:
                print("\n👋 검색을 종료합니다.")
                break
            except Exception as input_error:
                print(f"❌ 입력 처리 오류: {input_error}")
                
    except Exception as main_error:
        print(f"❌ 메인 실행 오류: {main_error}")
        print(f"❌ 상세 오류:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()