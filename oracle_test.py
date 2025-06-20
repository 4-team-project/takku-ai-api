import cx_Oracle
import os
import sys

# 1. Oracle Instant Client 경로 지정 (Windows용)
instant_client_dir = r"C:\oracle\instantclient_23_8"

# 2. 환경 변수 설정 (런타임 중에도)
os.environ["PATH"] = instant_client_dir + ";" + os.environ["PATH"]
os.environ["ORACLE_HOME"] = instant_client_dir
os.environ["NLS_LANG"] = "KOREAN_KOREA.AL32UTF8"  # ORA-01804 방지용

# 3. 연결 정보 설정
dsn = cx_Oracle.makedsn("43.202.1.56", 1521, sid="XE")

try:
    conn = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
    cur = conn.cursor()
    cur.execute("SELECT SYSDATE FROM dual")
    result = cur.fetchone()
    print("✅ Oracle 연결 성공! 현재 시간:", result[0])
    cur.close()
    conn.close()
except cx_Oracle.DatabaseError as e:
    print("❌ Oracle 연결 실패:", e)
