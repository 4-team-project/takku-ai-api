
# 🧠 Takku AI API

Takku 프로젝트의 AI 기능을 담당하는 백엔드 서비스입니다.
**FastAPI** 기반으로 동작하며, **추천 시스템**과 **리뷰 요약 기능**을 제공합니다.

---

## 📁 프로젝트 구조

```
takku-ai-api/
├── app.py                # FastAPI 엔트리포인트
├── oracle_config.py      # Oracle DB 연결
├── recommender.py        # 추천 로직 (태그+텍스트 하이브리드)
├── summarizer.py         # 리뷰 요약 로직 (TextRank)
├── requirements.txt
└── .env
```

---

## 🚀 실행 방법

### 로컬 개발 환경

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt
uvicorn app:app --reload
```

### 환경 변수(.env)

```env
ORACLE_USER=...
ORACLE_PASSWORD=...
ORACLE_HOST=...
ORACLE_PORT=1521
```

> 현재 구현은 **SERVICE NAME = XE** 기반 연결을 사용합니다.
> Windows 환경에서는 Oracle Instant Client 경로를 `PATH`에 추가해야 할 수 있습니다.

---

## 📡 API 개요

* `/` → 서버 상태 확인
* `/recommend/{user_id}` → 사용자 기반 펀딩 추천
* `/summary/{product_id}` → 해당 상품 리뷰 요약

---

## 🔍 추천 시스템 개요

* 사용자 주문 이력 기반으로 **태그(tag\_name 기준)** 및 **텍스트(TF-IDF)** 특징을 결합
* **코사인 유사도**로 상위 펀딩 추천
* 콜드스타트 시 `평점(70%) + 마감 임박 점수(30%)` 기반 정렬
* 응답은 camelCase 포맷, `tagList`, `score` 등 주요 정보 포함

---

## ✂️ 리뷰 요약 개요

* 최신 리뷰 최대 100개 수집
* 평점 4점 이상은 긍정, 미만은 부정으로 분리
* TextRank 기반 중요 문장 추출 (긍정/부정 각각 요약)
* 리뷰가 없으면 `"긍정/부정 리뷰가 없습니다."` 반환

---

## ⚠️ 한계 및 아쉬운 점

* 무료 배포 서비스 환경을 고려해 **경량 ML 기법**(TF-IDF, TextRank 등) 사용
* 한국어 문장 분할은 단순 정규식 기반이라 한계 존재

### 향후 개선 가능성

* GPU 리소스 확보 시 **BERT 기반 요약**, **딥러닝 추천 모델** 적용 가능
* 한국어 문장 분할기/형태소 분석기 연계로 정확도 개선
* 대규모 데이터 처리를 위한 캐시 및 벡터라이저 최적화

