import os
from dotenv import load_dotenv
import cx_Oracle
import pandas as pd

# 환경 변수 로드
load_dotenv()

# Oracle Instant Client 경로 설정
oracle_path = r"C:\oracle\instantclient_23_8"
os.environ["PATH"] = oracle_path + ";" + os.environ.get("PATH", "")
os.environ["NLS_LANG"] = "KOREAN_KOREA.AL32UTF8"

def get_connection():
    host = os.getenv("ORACLE_HOST")
    port = os.getenv("ORACLE_PORT")
    user = os.getenv("ORACLE_USER")
    pw = os.getenv("ORACLE_PASSWORD")

    if not all([host, port, user, pw]):
        raise EnvironmentError("[ERROR] .env 파일에 ORACLE 환경변수가 올바르게 설정되지 않았습니다.")

    try:
        port = int(port)
    except ValueError:
        raise ValueError("[ERROR] ORACLE_PORT는 정수여야 합니다.")

    dsn = cx_Oracle.makedsn(host, port, service_name="xe")  
    return cx_Oracle.connect(user=user, password=pw, dsn=dsn)

def run_queries(user_id):
    queries = {
        "user_df": """
            SELECT 
                o.funding_id,
                f.funding_name,
                MIN(DBMS_LOB.SUBSTR(f.funding_desc, 4000, 1)) AS funding_desc,
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
                DBMS_LOB.SUBSTR(f.funding_desc, 4000, 1) AS funding_desc,
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

        for df in dfs.values():
            df.columns = df.columns.str.lower()

        return dfs["user_df"], dfs["funding_df"], dfs["tag_df"], dfs["image_df"]

    except Exception as e:
        print(f"[쿼리 실행 실패] {e}")
        raise

    finally:
        conn.close()
