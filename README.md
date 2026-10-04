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
uvicorn app.main:app --reload --port 8000 --env-file .env --ssl-keyfile key.pem --ssl-certfile cert.pem
```

`--env-file .env` is what puts `OTEL_*` in the environment, the monitoring stack needs it.

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

## :bar_chart: Monitoring

Traces, metrics and logs with **Grafana**, **Tempo**, **Prometheus**, **Loki** and **Alloy**.

FastAPI has OpenTelemetry built in, so the app only needs `OTEL_EXPORTER_OTLP_ENDPOINT`
in `.env`. It sends OTLP to Alloy, and Alloy routes each signal to its store:

```
app ──OTLP────> alloy ──traces──> tempo
   stdout ──> alloy ──metrics─> prometheus
             └──logs───> loki
grafana reads tempo + prometheus + loki
```

### :rocket: Setup

1. **Start the stack**:

   ```bash
   docker compose up -d alloy tempo prometheus loki grafana
   ```

2. **Open Grafana** on [http://localhost:3000](http://localhost:3000) with `admin` / `admin`.
   The data sources and the dashboards are provisioned automatically.

3. **Send some traffic** so there is something to look at:

   ```bash
   curl http://localhost:8000/health
   ```

4. **Explore** the provisioned dashboards:
   - `App Logs`: log lines plus the share of logs per level
   - `Request Metrics`: throughput, latency percentiles and error rate

   Or query the data sources by hand from Grafana > **Explore**: `Tempo` for
   traces, `Prometheus` for metrics, `Loki` for logs.

:bar_chart: Useful endpoints:

| Service    | URL                    |
| ---------- | ---------------------- |
| Grafana    | http://localhost:3000  |
| Alloy UI   | http://localhost:12345 |
| Prometheus | http://localhost:9090  |
| Tempo      | http://localhost:3200  |
| Loki       | http://localhost:3100  |

:mag_right: How the dashboards work:

The app writes one JSON object per line (loguru with `serialize=True`), so the
level is nested at `record.level.name` and the message at `record.message`. The
logs panel queries use `| json`, and Loki exposes those nested fields flattened
with underscores, which is where `record_level_name` comes from.

`Request Metrics` is built on `http.server.request.duration`, the histogram
FastAPI records for every request. Percentiles come from
`histogram_quantile()` over the buckets, and error rate is the share of `5xx`
responses. Two details worth knowing:

- Paths that match no route, such as a `404`, carry no `http_route` label, so
  they are grouped as `unmatched` with `label_replace()`.
- Both error rate panels read `0%` while healthy instead of showing no data, so
  a quiet dashboard never looks broken.

:warning: The OTLP receiver in Prometheus scrapes every **60s** and ignores
`global.scrape_interval`, so the Prometheus data source declares
`timeInterval: 60s`. That matters because `$__rate_interval` is derived from it:
at the 15s default it lands near 1m, which is too short to hold two samples, and
every `rate()` in the dashboards returns nothing. Leave it in sync if you ever
change the receiver cadence.

:warning: Alloy reads the host Docker socket to collect container logs. It grants
root equivalent access to the host, fine for local work, and must be replaced by
a scoped socket proxy anywhere shared.

:hammer_and_wrench: Configuration files:

```
observability/
├── docker/
│   ├── alloy/config.alloy                # OTLP and Docker logs in, traces, metrics and logs out
│   ├── prometheus/prometheus.yml
│   ├── tempo/tempo.yaml
│   └── loki/loki-config.yaml
└── grafana/
    ├── dashboards/
    │   ├── app-logs.json                 # log lines and share per level
    │   └── request-metrics.json          # throughput, latency percentiles, error rate
    └── provisioning/
        ├── dashboards/dashboards.yaml
        └── datasources/datasources.yaml
```
