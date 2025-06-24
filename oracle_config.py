import os
from dotenv import load_dotenv  # .env 파일에서 환경변수를 불러오는 모듈
import cx_Oracle                # Oracle DB에 연결하기 위한 모듈
import pandas as pd            # 데이터 프레임 처리를 위한 pandas

# .env 파일로부터 환경 변수 로드 (예: ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST 등)
load_dotenv()

# Oracle Instant Client 경로 설정 (Oracle DB 접속에 필요한 클라이언트 라이브러리 위치)
oracle_path = r"C:\oracle\instantclient_23_8"
os.environ["PATH"] = oracle_path + ";" + os.environ.get("PATH", "")
os.environ["ORACLE_HOME"] = oracle_path
os.environ["NLS_LANG"] = "KOREAN_KOREA.AL32UTF8"  # 한글 데이터 깨짐 방지 (UTF-8 설정)

# Oracle DB 연결 함수 정의
def get_connection():
    # DSN(Data Source Name) 구성 (호스트, 포트, SID 이용)
    dsn = cx_Oracle.makedsn(
        os.getenv("ORACLE_HOST"), 1521, sid="XE"
    )
    # 환경 변수에 저장된 유저 정보로 DB 접속
    conn = cx_Oracle.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )
    return conn

# 여러 개의 쿼리를 실행하여 데이터프레임으로 반환하는 함수
def run_queries(user_id):
    # 실행할 쿼리들을 딕셔너리 형태로 정의
    queries = {
        # 특정 사용자가 참여한 펀딩 정보 및 태그 수량 집계
        "user_df": """
            SELECT 
                o.funding_id,
                f.funding_name,
                MIN(TO_CHAR(f.funding_desc)) AS funding_desc,
                tft.tag_id,
                SUM(o.qty) AS qty
            FROM takku_order o
            JOIN takku_funding f ON o.funding_id = f.funding_id
            JOIN takku_funding_tag tft ON f.funding_id = tft.funding_id
            WHERE o.user_id = :user_id
            GROUP BY o.funding_id, f.funding_name, tft.tag_id
        """,

        # 현재 진행 중인 펀딩 전체 목록 및 리뷰 통계, 스토어 정보 포함
        "funding_df": """
            SELECT 
                f.funding_id,
                f.product_id,
                f.store_id,
                f.funding_type,
                f.funding_name,
                TO_CHAR(f.funding_desc) AS funding_desc,
                f.start_date,
                f.end_date,
                f.sale_price,
                f.target_qty,
                f.max_qty,
                f.current_qty,
                f.per_qty,
                f.status,
                f.created_at,
                s.store_name,
                f.sale_price AS price,
                NVL(r.avg_rating, 0) AS avg_rating,
                NVL(r.review_cnt, 0) AS review_cnt
            FROM takku_funding f
            LEFT JOIN (
                SELECT 
                    p.product_id,
                    AVG(r.rating) AS avg_rating,
                    COUNT(*) AS review_cnt
                FROM takku_product p
                JOIN takku_review r ON p.product_id = r.product_id
                GROUP BY p.product_id
            ) r ON f.product_id = r.product_id
            JOIN takku_store s ON f.store_id = s.store_id
            WHERE f.status = '진행중'
        """,

        # 진행 중인 펀딩에 연결된 태그 목록
        "tag_df": """
            SELECT 
                ft.funding_id,
                t.tag_name
            FROM takku_funding_tag ft
            JOIN takku_tag t ON ft.tag_id = t.tag_id
            JOIN takku_funding f ON ft.funding_id = f.funding_id
            WHERE f.status = '진행중'
        """,

        # 펀딩별 이미지 목록
        "image_df": """
            SELECT 
                funding_id,
                image_url
            FROM takku_image
            WHERE funding_id IS NOT NULL
        """
    }

    # DB 연결
    conn = get_connection()

    try:
        dfs = {}
        for key, sql in queries.items():
            # user_df 쿼리에는 user_id 파라미터를 넘김
            if key == "user_df":
                dfs[key] = pd.read_sql(sql, conn, params={"user_id": user_id})
            else:
                dfs[key] = pd.read_sql(sql, conn)

        # 모든 데이터프레임 컬럼명을 소문자로 통일
        for df in dfs.values():
            df.columns = df.columns.str.lower()

        # 네 개의 데이터프레임을 반환
        return dfs["user_df"], dfs["funding_df"], dfs["tag_df"], dfs["image_df"]
    except Exception as e:
        print(f"[쿼리 실행 실패] {e}")
        raise
    finally:
        # 연결 종료
        conn.close()
