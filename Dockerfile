FROM python:3.10

# Oracle Instant Client 설치 (Basic Full 버전 사용)
RUN apt-get update && apt-get install -y libaio1 unzip wget && \
    wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basic-linux.x64-21.9.0.0.0dbru.zip && \
    unzip instantclient-basic-linux.x64-21.9.0.0.0dbru.zip && \
    mv instantclient_21_9 /opt/oracle && \
    echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

# Oracle 환경 설정
ENV LD_LIBRARY_PATH=/opt/oracle

# 앱 설정
WORKDIR /app
COPY . /app

# 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# Render용 포트 환경 변수
ENV PORT=10000

# FastAPI 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
