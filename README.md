# :zap: Fastapi api template

Template API with FastApi

## :floppy_disk: Installation

Create virtual enviroment:

```bash
python -m venv env
```

Activate enviroment:

- Windows:

```bash
. env/scripts/activate
```

- Mac/Linux:

```bash
. env/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install requirements:
```bash
pip install -r requirements.txt
```

## :wrench: Config

Create `.env` file. Check the example `.env.example`

:globe_with_meridians: Google Auth credentials:

Create your app and obtain your `client_id` and `secret`:

```http
https://developers.google.com/workspace/guides/create-credentials
```

:lock: How to create a secret key:

```bash
openssl rand -base64 64
```

:construction: Before first run:

Run `docker-compose` :whale: to start the database server

```bash
docker compose -f "compose.yaml" up -d --build adminer db
```

and init the database with alembic:

```bash
alembic upgrade head
```

:key: Create a self-signed certificate with openssl:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

## :runner: Run

```bash
uvicorn app.main:app --reload --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

## :pushpin: Features

- Basic login
- Google Auth login
- Create users
- Examples endpoints CRUD
  - Posts
  - Users
  - Votes
- API healthcheck
- JWT tokens
- Middlewares
- CORS
- Complete swagger Api info
- Postgres
