FROM python:3.10

RUN apt-get update && apt-get install -y libaio1 unzip wget && \
    wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    unzip instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    mv instantclient_21_9 /opt/oracle && \
    echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "app.py"]
