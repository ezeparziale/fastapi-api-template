FROM python:3.10

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app
COPY key.pem cert.pem ./

ENTRYPOINT [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--ssl-keyfile", "key.pem", "--ssl-certfile", "cert.pem" ]