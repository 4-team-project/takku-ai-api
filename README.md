# 🧠 Takku AI API

Takku 프로젝트의 AI 기능을 담당하는 백엔드 서비스입니다.  
Flask 기반으로 동작하며, 추천 시스템을 포함한 다양한 AI 기능을 REST API 형태로 제공합니다.

---

## 📌 주요 기능

- 사용자 기반 추천 API
- Oracle DB 연동
- 통계 모델 등의 AI 기능 확장 예정

---

## 📁 프로젝트 구조

```

takku-ai-api/
├── app.py                # Flask 진입점
├── oracle\_config.py      # Oracle 연결 및 쿼리 처리
├── requirements.txt      # Python 의존성 목록
├── Dockerfile            # Docker 컨테이너 정의
├── .env                  # 환경 변수 (로컬 전용)
└── ...

````

---

## 🚀 실행 방법

### 🧪 로컬 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
python app.py
````

### 🐳 Docker 실행

```bash
docker build -t takku-ai-api .
docker run -p 5000:5000 takku-ai-api
```

---

## 🔐 환경 변수 (.env)

`.env` 파일 예시:

```env
ORACLE_USER=your_oracle_username
ORACLE_PASSWORD=your_oracle_password
ORACLE_DSN=host:port/service_name
```

※ Render 환경에서는 Dashboard > Environment에서 직접 입력합니다.

---

## 📡 API 명세

| 기능     | URL                    | HTTP | 요청 파라미터        | 응답 모델       | 설명                |
| ------ | ---------------------- | ---- | -------------- | ----------- | ----------------- |
| 사용자 추천 | `/recommend/{user_id}` | GET  | `user_id: int` | `List[str]` | 해당 사용자에게 추천 결과 반환 |



## ⚙️ 기술 스택

* Python 3.10
* Flask
* cx\_Oracle
* Oracle Instant Client
* Pandas, Scikit-learn
* Docker

