# :zap: FastAPI API Template


This template provides a robust starting point for building APIs with FastAPI. It includes user authentication, CRUD operations, JWT token-based authentication, and PostgreSQL integration. The setup is streamlined with Docker and includes comprehensive documentation and testing tools.

## :pushpin: Features

- :closed_lock_with_key: User authentication with basic login and Google Auth
- :busts_in_silhouette: User management with creation and CRUD operations
- :page_facing_up: Example endpoints for Posts, Users, and Votes
- :heartbeat: API healthcheck endpoint
- :key: JWT token-based authentication
- :gear: Middleware support
- :earth_americas: CORS configuration
- :memo: Comprehensive Swagger API documentation
- :elephant: PostgreSQL database integration
- :lock: Field encryption for sensitive data

## :floppy_disk: Installation

> [!IMPORTANT]
> Min Python version: 3.14

Clone this repo:

```bash
git clone https://github.com/ezeparziale/fastapi-api-template
```

Create virtual environment:

```bash
python -m venv env
```

Activate environment:

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
pip install -r requirements-dev.txt
```

Install pre-commit:

```bash
pre-commit install
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

:closed_lock_with_key: How to create an encryption key:

To create an encryption key for securing sensitive data, you can use the `generate_key.py` script provided in the repository. Run the following command:

```bash
python generate_key.py
```

This will generate a secure encryption key.

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

## :rotating_light: Lint

Run linter and formatter

```bash
scripts/lint.sh
```

```bash
scripts/format.sh
```

## :technologist: Coverage

Run coverage

```bash
coverage run -m pytest
```

```bash
coverage report --show-missing
```

```bash
coverage html
```

Or run all in one with:

```bash
scripts/coverage.sh
```

## :test_tube: Test

Run pytest with coverage

```bash
coverage run -m pytest
```

or

```bash
scripts/test.sh
```

## :hammer_and_wrench: Alembic

Alembic is used for database migrations. Below are some common commands to manage your database schema.

### Autogenerate a revision

To autogenerate a new revision based on the changes detected in your models, run:

```bash
alembic revision --autogenerate -m "your message here"
```

### Generate a blank revision

To create a blank revision for custom migrations, run:

```bash
alembic revision -m "your message here"
```

### Upgrade the database

To apply the latest migrations and upgrade the database schema, run:

```bash
alembic upgrade head
```

### Downgrade the database

To revert the last migration and downgrade the database schema, run:

```bash
alembic downgrade -1
```

After creating a revision, you can edit the generated script to define your custom migrations.
