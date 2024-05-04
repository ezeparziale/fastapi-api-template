FROM python:3.12

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app/ ./app

ENTRYPOINT [ "uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "3000" ]

HEALTHCHECK --interval=10s --timeout=5s CMD curl -k --fail https://localhost/health || exit 1