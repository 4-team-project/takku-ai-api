# Dockerfile 
FROM python:3.10

# Oracle Instant Client 23.8 설치
RUN apt-get update && apt-get install -y libaio1 unzip wget && \
    wget https://download.oracle.com/otn_software/linux/instantclient/238000/instantclient-basiclite-linux.x64-23.8.0.0.0dbru.zip && \
    unzip instantclient-basiclite-linux.x64-23.8.0.0.0dbru.zip && \
    mv instantclient_23_8 /opt/oracle && \
    echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle

# 앱 설정
WORKDIR /app
COPY . /app

# Python 패키지 설치
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 실행
CMD ["python", "app.py"]
