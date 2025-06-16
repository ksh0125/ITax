# -*- coding: utf-8 -*-
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import re
import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform.startswith('win'):
    os.system('chcp 65001')  # UTF-8 코드페이지로 변경

class VATLawProcessor:
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli"):
        """부가가치세법 전처리기 초기화"""
        print(f"모델 '{model_name}' 로딩 중...")
        self.model = SentenceTransformer(model_name)
        print("모델 로딩 완료!")
        
    def extract_articles_from_docx(self, docx_content: str) -> List[Dict[str, str]]:
        """업로드된 부가가치세법 문서에서 조문 추출"""
        articles = []
        
        # 실제 부가가치세법 조문들을 추출
        # 조문 패턴: **제X조(제목)**
        lines = docx_content.split('\n')
        current_article = None
        current_title = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 조문 시작 패턴 찾기
            article_match = re.match(r'\*\*제(\d+(?:조의\d+)?조)\(([^)]+)\)\*\*', line)
            if article_match:
                # 이전 조문 저장
                if current_article and current_content:
                    content_text = ' '.join(current_content).strip()
                    if len(content_text) > 30:  # 의미있는 내용만
                        articles.append({
                            'article_number': current_article,
                            'title': current_title,
                            'content': content_text,
                            'law_name': '부가가치세법'
                        })
                
                # 새 조문 시작
                current_article = f"제{article_match.group(1)}"
                current_title = article_match.group(2)
                current_content = []
            else:
                # 조문 내용 추가
                if current_article and line:
                    # 불필요한 마크다운 제거
                    cleaned_line = re.sub(r'\*\*|`|#', '', line)
                    if cleaned_line and len(cleaned_line) > 5:
                        current_content.append(cleaned_line)
        
        # 마지막 조문 저장
        if current_article and current_content:
            content_text = ' '.join(current_content).strip()
            if len(content_text) > 30:
                articles.append({
                    'article_number': current_article,
                    'title': current_title,
                    'content': content_text,
                    'law_name': '부가가치세법'
                })
        
        return articles
    
    def chunk_article_content(self, content: str, max_length: int = 400) -> List[str]:
        """조문 내용을 청킹"""
        if len(content) <= max_length:
            return [content]
        
        chunks = []
        
        # 1. 항목별 분할 (①, ②, ③ 등)
        item_pattern = r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]'
        items = re.split(f'({item_pattern})', content)
        
        current_chunk = ""
        
        for item in items:
            if not item.strip():
                continue
                
            test_chunk = current_chunk + item
            
            if len(test_chunk) <= max_length:
                current_chunk = test_chunk
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = item
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def create_sample_data(self) -> List[Dict[str, str]]:
        """샘플 부가가치세법 데이터 생성"""
        return [
            {
                'article_number': '제1조',
                'title': '목적',
                'content': '이 법은 부가가치세의 과세(課稅) 요건 및 절차를 규정함으로써 부가가치세의 공정한 과세, 납세의무의 적정한 이행 확보 및 재정수입의 원활한 조달에 이바지함을 목적으로 한다.',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제2조',
                'title': '정의',
                'content': '이 법에서 사용하는 용어의 뜻은 다음과 같다. 1. "재화"란 재산 가치가 있는 물건 및 권리를 말한다. 물건과 권리의 범위에 관하여 필요한 사항은 대통령령으로 정한다. 2. "용역"이란 재화 외에 재산 가치가 있는 모든 역무(役務)와 그 밖의 행위를 말한다. 용역의 범위에 관하여 필요한 사항은 대통령령으로 정한다. 3. "사업자"란 사업 목적이 영리이든 비영리이든 관계없이 사업상 독립적으로 재화 또는 용역을 공급하는 자를 말한다.',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제3조',
                'title': '납세의무자',
                'content': '다음 각 호의 어느 하나에 해당하는 자로서 개인, 법인(국가·지방자치단체와 지방자치단체조합을 포함한다), 법인격이 없는 사단·재단 또는 그 밖의 단체는 이 법에 따라 부가가치세를 납부할 의무가 있다. 1. 사업자 2. 재화를 수입하는 자',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제4조',
                'title': '과세대상',
                'content': '부가가치세는 다음 각 호의 거래에 대하여 과세한다. 1. 사업자가 행하는 재화 또는 용역의 공급 2. 재화의 수입',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제30조',
                'title': '세율',
                'content': '부가가치세의 세율은 10퍼센트로 한다.',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제31조',
                'title': '거래징수',
                'content': '사업자가 재화 또는 용역을 공급하는 경우에는 제29조제1항에 따른 공급가액에 제30조에 따른 세율을 적용하여 계산한 부가가치세를 재화 또는 용역을 공급받는 자로부터 징수하여야 한다.',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제32조',
                'title': '세금계산서 등',
                'content': '사업자가 재화 또는 용역을 공급(부가가치세가 면제되는 재화 또는 용역의 공급은 제외한다)하는 경우에는 다음 각 호의 사항을 적은 계산서(이하 "세금계산서"라 한다)를 그 공급을 받는 자에게 발급하여야 한다. 1. 공급하는 사업자의 등록번호와 성명 또는 명칭 2. 공급받는 자의 등록번호 3. 공급가액과 부가가치세액 4. 작성 연월일',
                'law_name': '부가가치세법'
            },
            {
                'article_number': '제26조',
                'title': '재화 또는 용역의 공급에 대한 면세',
                'content': '다음 각 호의 재화 또는 용역의 공급에 대하여는 부가가치세를 면제한다. 1. 가공되지 아니한 식료품(식용으로 제공되는 농산물, 축산물, 수산물과 임산물을 포함한다) 2. 수돗물 3. 연탄과 무연탄 4. 여성용 생리 처리 위생용품 5. 의료보건 용역 6. 교육 용역 7. 여객운송 용역 8. 도서, 신문, 잡지',
                'law_name': '부가가치세법'
            }
        ]
    
    def process_vat_law_data(self) -> List[Dict[str, Any]]:
        """부가가치세법 데이터 전처리"""
        print("부가가치세법 데이터 처리 중...")
        
        # 샘플 데이터 사용 (실제 환경에서는 docx 파일 파싱)
        articles = self.create_sample_data()
        print(f"총 {len(articles)}개 조문 추출 완료")
        
        # 청킹 및 벡터화
        processed_data = []
        total_chunks = 0
        
        for article_idx, article in enumerate(articles):
            print(f"처리 중: {article['article_number']} {article['title']} ({article_idx + 1}/{len(articles)})")
            
            # 조문 청킹
            chunks = self.chunk_article_content(article['content'])
            
            for chunk_idx, chunk in enumerate(chunks):
                # 벡터화
                try:
                    embedding = self.model.encode(chunk, convert_to_tensor=False)
                    
                    # 메타데이터와 함께 저장
                    chunk_data = {
                        'id': f"vat_{article_idx}_{chunk_idx}",
                        'law_name': article['law_name'],
                        'article_number': article['article_number'],
                        'article_title': article['title'],
                        'full_content': article['content'],
                        'chunk_content': chunk,
                        'chunk_index': chunk_idx,
                        'embedding': embedding.tolist(),
                        'embedding_dim': len(embedding)
                    }
                    
                    processed_data.append(chunk_data)
                    total_chunks += 1
                except Exception as e:
                    print(f"벡터화 오류 (건너뜀): {e}")
                    continue
        
        print(f"전처리 완료: {len(articles)}개 조문, {total_chunks}개 청크 생성")
        return processed_data
    
    def save_processed_data(self, processed_data: List[Dict], output_file: str):
        """처리된 데이터 저장"""
        print(f"'{output_file}'에 저장 중...")
        
        try:
            with open(output_file, 'wb') as f:
                pickle.dump(processed_data, f)
            
            print(f"저장 완료: {len(processed_data)}개 청크")
        except Exception as e:
            print(f"저장 오류: {e}")

def main():
    """부가가치세법 전처리 실행"""
    try:
        print("=" * 60)
        print("부가가치세법 RAG 시스템 데이터 전처리")
        print("=" * 60)
        
        # 전처리기 초기화
        processor = VATLawProcessor()
        
        # 데이터 처리
        processed_data = processor.process_vat_law_data()
        
        if not processed_data:
            print("처리된 데이터가 없습니다. 오류를 확인해주세요.")
            return
        
        # 저장
        processor.save_processed_data(processed_data, 'vat_law_processed.pkl')
        
        print("\n" + "=" * 60)
        print("처리 통계:")
        print(f"   총 청크 수: {len(processed_data)}")
        print(f"   임베딩 차원: {processed_data[0]['embedding_dim']}")
        print(f"   모델: jhgan/ko-sbert-nli")
        print(f"   저장 파일: vat_law_processed.pkl")
        print("=" * 60)
        print("전처리 완료! 이제 'python main.py'를 실행하세요.")
        
    except Exception as e:
        print(f"전처리 중 오류 발생: {e}")
        print("오류 해결 후 다시 시도해주세요.")

if __name__ == "__main__":
    main()