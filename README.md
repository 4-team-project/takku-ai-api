
# 🧠 Takku AI API

Takku 프로젝트의 AI 기능을 담당하는 백엔드 서비스입니다.  
**FastAPI** 기반으로 동작하며, **추천 시스템**과 **리뷰 요약 기능**을 REST API 형태로 제공합니다.

---

## 📌 주요 기능

* 🔍 사용자 기반 펀딩 추천 API
* ✂️ 최신 리뷰 요약 (TextRank 기반 요약 알고리즘)
* 🗄️ Oracle DB 연동

---

## 📁 프로젝트 구조

```

takku-ai-api/
├── app.py                # FastAPI 엔트리포인트
├── oracle\_config.py      # Oracle DB 연결 및 쿼리 처리
├── recommender.py        # 추천 로직
├── summarizer.py         # 리뷰 요약 로직 (TextRank 기반)
├── requirements.txt      # 패키지 의존성 목록
├── .env                  # 환경변수 파일 (로컬 실행용)
└── ...

````

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
````

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

| 메서드 | URL                     | 설명                              |
| --- | ----------------------- | ------------------------------- |
| GET | `/`                     | 서버 상태 확인용 기본 엔드포인트              |
| GET | `/recommend/{user_id}`  | 사용자 기반 펀딩 추천 결과 반환              |
| GET | `/summary/{product_id}` | 해당 상품의 최신 리뷰 100개를 요약하여 리스트로 반환 |

---

## ⚙️ 기술 스택

* Python 3.10
* FastAPI
* cx\_Oracle
* Oracle Instant Client
* pandas / numpy / scikit-learn
* networkx
* **(Konlpy 제거됨 - Render 호환성 문제로 JVM 불필요)**
* Render 배포 가능

---

## 📝 작동 방식 요약

### 🔍 추천 시스템

* 사용자 주문 내역에서 **관심 태그 벡터** 생성
* 펀딩 데이터의 \*\*텍스트(TF-IDF)\*\*와 **태그**를 하이브리드 벡터로 구성
* 사용자 벡터와 코사인 유사도 계산하여 상위 10개 추천
* 콜드스타트 유저는 평점 + 마감 임박도 기반 추천
* 결과는 camelCase로 포맷 후 반환 (이미지, 태그 포함)

### ✂️ 리뷰 요약 시스템

* 최신 리뷰 100개를 수집하여 문장 단위 분리
* **TF-IDF 기반 코사인 유사도**로 문장 중요도 그래프 구성
* **TextRank 알고리즘**을 통해 요약 문장 선택
* 유사 문장 제거로 중복 방지, 최종 3문장 리스트 반환

