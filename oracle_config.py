# oracle_config.py
import os
from dotenv import load_dotenv
import cx_Oracle
import pandas as pd

load_dotenv()  # .env 파일에서 환경변수 불러오기

# Oracle Instant Client 경로
oracle_path = r"C:\oracle\instantclient_23_8"
os.environ["PATH"] = oracle_path + ";" + os.environ["PATH"]
os.environ["ORACLE_HOME"] = oracle_path
os.environ["NLS_LANG"] = "KOREAN_KOREA.AL32UTF8"

def get_connection():
    dsn = cx_Oracle.makedsn(
        os.getenv("ORACLE_HOST"), 1521, sid="XE"
    )

    conn = cx_Oracle.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )

    return conn

def run_queries(user_id):
    queries = {
        "user_df": f"""
            SELECT o.funding_id, f.funding_name, MIN(TO_CHAR(f.funding_desc)) AS funding_desc,
                   tft.tag_id, SUM(o.qty) AS qty
            FROM takku_order o
            JOIN takku_funding f ON o.funding_id = f.funding_id
            JOIN takku_funding_tag tft ON f.funding_id = tft.funding_id
            WHERE o.user_id = {user_id}
            GROUP BY o.funding_id, f.funding_name, tft.tag_id
        """,
        "funding_df": """
            SELECT f.funding_id, f.funding_name, TO_CHAR(f.funding_desc) AS funding_desc,
                   f.end_date, NVL(r.avg_rating, 0) AS avg_rating, NVL(r.review_cnt, 0) AS review_cnt
            FROM takku_funding f
            LEFT JOIN (
                SELECT p.product_id, AVG(r.rating) AS avg_rating, COUNT(*) AS review_cnt
                FROM takku_product p
                JOIN takku_review r ON p.product_id = r.product_id
                GROUP BY p.product_id
            ) r ON f.product_id = r.product_id
            WHERE f.status = '진행중'
        """,
        "tag_df": """
            SELECT funding_id, tag_id
            FROM takku_funding_tag
            WHERE funding_id IN (
                SELECT funding_id FROM takku_funding WHERE status = '진행중'
            )
        """
    }

    conn = get_connection()
    user_df = pd.read_sql(queries["user_df"], conn)
    funding_df = pd.read_sql(queries["funding_df"], conn)
    tag_df = pd.read_sql(queries["tag_df"], conn)
    conn.close()

    # 컬럼 소문자 변환
    user_df.columns = user_df.columns.str.lower()
    funding_df.columns = funding_df.columns.str.lower()
    tag_df.columns = tag_df.columns.str.lower()

    return user_df, funding_df, tag_df
