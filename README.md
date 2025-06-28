# 🧠 Takku AI API

Takku 프로젝트의 AI 기능을 담당하는 백엔드 서비스입니다.
**FastAPI** 기반으로 동작하며, **추천 시스템**과 **리뷰 요약 기능**을 REST API로 제공합니다.

---

## 📌 주요 기능

* 🔍 **사용자 기반 펀딩 추천 API**
* 📝 **리뷰 요약 (TextRank 기반)**
* 🗄️ Oracle DB 연동

---

## 📁 프로젝트 구조

```
takku-ai-api/
├── app.py                # FastAPI 진입점
├── oracle_config.py      # Oracle 연결 및 쿼리 처리
├── recommender.py        # 추천 로직
├── summarizer.py         # 리뷰 요약 로직
├── requirements.txt      # Python 의존성 목록
├── .env                  # 환경 변수 파일 (로컬 실행용)
└── ...
```

---

## 🚀 실행 방법

### 🧪 로컬 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app:app --reload
```

---

## 🔐 환경 변수 (.env 예시)

```env
ORACLE_USER=your_oracle_username
ORACLE_PASSWORD=your_oracle_password
ORACLE_HOST=your_oracle_host
```

> Oracle은 `SID=XE` 또는 `SERVICE_NAME=XE`를 사용하도록 설정되어 있습니다.
> Windows에서는 Oracle Instant Client 설치 후 환경변수에 PATH 추가 필요.

---

## 📡 API 명세

| 기능    | URL                     | HTTP | 설명                       |
| ----- | ----------------------- | ---- | ------------------------ |
| 홈 확인  | `/`                     | GET  | 서버 정상 동작 확인용 응답          |
| 추천 결과 | `/recommend/{user_id}`  | GET  | 해당 유저의 관심 태그 기반 추천 결과 반환 |
| 리뷰 요약 | `/summary/{product_id}` | GET  | 해당 상품의 최신 리뷰 100개 요약 반환  |


---

## ⚙️ 기술 스택

* Python 3.10
* **FastAPI**
* cx\_Oracle
* Oracle Instant Client
* Pandas / scikit-learn / NumPy
* KoNLPy (Okt 형태소 분석기)
* networkx
* JPype1
* Docker (선택 사항)

---

## 📝 참고

* 본 서비스는 **한국어 리뷰 기반 분석**에 특화되어 있으며, 추천 시스템은 **콘텐츠 기반 필터링**을 사용합니다.
* TextRank 요약 알고리즘은 Konlpy를 기반으로 개선된 **중복 문장 제거 및 중요도 순 요약**을 포함합니다.
* 추천 시스템은 다음과 같은 방식으로 작동합니다:

  * 🧩 **사용자 관심 태그**와 과거 참여 펀딩 텍스트(제목 + 설명)를 기반으로 벡터 생성
  * 🧾 **TF-IDF**로 텍스트를 벡터화하고, **태그 벡터**와 함께 **하이브리드 벡터** 구성
  * 🧠 현재 진행 중인 펀딩들과 **코사인 유사도** 계산 → 유사도가 높은 펀딩 상위 10개 추천
  * ❄️ 신규 유저(콜드스타트)의 경우, **평점 + 마감 임박도**를 기준으로 정렬 추천
  * 📦 추천 결과에는 **이미지/태그/스토어 정보** 포함, DTO 규격에 맞게 camelCase로 포맷팅 처리

