
# 🧠 Takku AI API

Takku 프로젝트의 AI 기능을 담당하는 백엔드 서비스입니다.
**FastAPI** 기반으로 동작하며, **추천 시스템**과 **리뷰 요약 기능**을 REST API 형태로 제공합니다.

---

## 📌 주요 기능

* 🔍 사용자 기반 펀딩 추천 API
* ✂️ 최신 리뷰 요약 (TextRank 기반, 긍정/부정 분리)
* 🗄️ Oracle DB 연동

---

## 📁 프로젝트 구조

```
takku-ai-api/
├── app.py                # FastAPI 엔트리포인트
├── oracle_config.py      # Oracle DB 연결 및 쿼리 처리
├── recommender.py        # 추천 로직 (텍스트+태그 기반)
├── summarizer.py         # 리뷰 요약 로직 (TextRank 기반)
├── requirements.txt      # 패키지 의존성 목록
├── .env                  # 환경변수 파일 (로컬 실행용)
└── ...
```

---

## 🚀 실행 방법

### 🧪 로컬 개발 환경

```bash
# 가상환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# FastAPI 실행
uvicorn app:app --reload
```

---

## 🔐 .env 설정 예시

```env
ORACLE_USER=your_oracle_username
ORACLE_PASSWORD=your_oracle_password
ORACLE_HOST=your_oracle_host
```

> Oracle은 `SID=XE` 또는 `SERVICE_NAME=XE` 기반으로 연결됩니다.
> Windows에서는 Oracle Instant Client 경로를 `PATH`에 추가해 주세요.

---

## 📡 API 명세

| 메서드 | URL                     | 설명                                             |
| --- | ----------------------- | ---------------------------------------------- |
| GET | `/`                     | 서버 상태 확인용 기본 엔드포인트                             |
| GET | `/recommend/{user_id}`  | 사용자 기반 펀딩 추천 결과 반환 (태그+텍스트 하이브리드, 콜드스타트 처리 포함) |
| GET | `/summary/{product_id}` | 해당 상품의 최신 리뷰 100개를 긍정/부정으로 나누어 요약 후 반환         |

---

## ⚙️ 기술 스택

* Python 3.10
* FastAPI
* cx\_Oracle
* Oracle Instant Client
* pandas / numpy / scikit-learn
* networkx
---

## 🔍 추천 시스템 작동 방식

1. **사용자 기반 추천**

   * 사용자 주문 내역 기반 **관심 태그 벡터 생성**
   * 펀딩 텍스트(TF-IDF) + 태그 피처를 하이브리드 벡터로 구성
   * **코사인 유사도**로 유사 펀딩 상위 10개 추천
   * 결과에는 **태그 리스트 + 이미지 리스트 포함**

2. **콜드스타트 처리**

   * 사용자 데이터가 없는 경우:
     `평점(70%) + 마감 임박 점수(30%)` 기반 정렬 후 추천

3. **추천 결과 포맷**

   * camelCase 형식
   * 주요 필드: `fundingId`, `fundingName`, `tagList`, `images`, `score` 등

---

## ✂️ 리뷰 요약 작동 방식

1. **데이터 수집**

   * 최신 리뷰 최대 100개 수집
   * `rating` 기준으로 **긍정(4~~5점) / 부정(1~~3점)** 리뷰 분리

2. **텍스트 처리 및 요약**

   * 문장 단위로 분리
   * TF-IDF 기반 **코사인 유사도 행렬 생성**
   * **TextRank** 알고리즘으로 중요 문장 추출 (중복 제거 포함)

3. **반환 포맷**

   ```json
   {
     "productId": 123,
     "summary": {
       "positive": ["긍정 요약 문장1", "문장2", "문장3"],
       "negative": ["부정 요약 문장1", "문장2", "문장3"]
     }
   }
   ```

   > 긍정/부정 리뷰가 없는 경우: `"긍정 리뷰가 없습니다."` 또는 `"부정 리뷰가 없습니다."`

---

