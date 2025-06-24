import os
from dotenv import load_dotenv
import oracledb  # ✅ 최신 Oracle 드라이버
import pandas as pd

# .env 파일에서 환경 변수 로드
load_dotenv()

# Oracle Instant Client 경로 설정
oracle_path = r"C:\oracle\instantclient_23_8"
oracledb.init_oracle_client(lib_dir=oracle_path)

# Oracle DB 연결 함수
def get_connection():
    dsn = f"{os.getenv('ORACLE_HOST')}:1521/XE"
    conn = oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )
    return conn

# 쿼리 실행 함수
def run_queries(user_id):
    queries = {
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
        "tag_df": """
            SELECT 
                ft.funding_id,
                t.tag_name
            FROM takku_funding_tag ft
            JOIN takku_tag t ON ft.tag_id = t.tag_id
            JOIN takku_funding f ON ft.funding_id = f.funding_id
            WHERE f.status = '진행중'
        """,
        "image_df": """
            SELECT 
                funding_id,
                image_url
            FROM takku_image
            WHERE funding_id IS NOT NULL
        """
    }

    conn = get_connection()

    try:
        dfs = {}
        for key, sql in queries.items():
            if key == "user_df":
                dfs[key] = pd.read_sql(sql, conn, params={"user_id": user_id})
            else:
                dfs[key] = pd.read_sql(sql, conn)

        # 컬럼 소문자 통일
        for df in dfs.values():
            df.columns = df.columns.str.lower()

        return dfs["user_df"], dfs["funding_df"], dfs["tag_df"], dfs["image_df"]
    except Exception as e:
        print(f"[쿼리 실행 실패] {e}")
        raise
    finally:
        conn.close()
