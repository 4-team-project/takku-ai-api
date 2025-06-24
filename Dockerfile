# Python 3.10 베이스 이미지
FROM python:3.10

# Oracle Instant Client 21.9 설치
RUN apt-get update && apt-get install -y libaio1 unzip wget && \
    wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    unzip instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    mv instantclient_21_9 /opt/oracle && \
    echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

# Oracle 라이브러리 경로 설정
ENV LD_LIBRARY_PATH=/opt/oracle
ENV ORACLE_HOME=/opt/oracle

# 작업 디렉토리 설정
WORKDIR /app
COPY . /app

# 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# 포트 설정 (Render는 10000 포트 사용)
ENV PORT=10000

# FastAPI 앱 실행 (uvicorn으로)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
