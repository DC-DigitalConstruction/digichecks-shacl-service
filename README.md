# DigiChecks SHACL Compliancy Check Service

The DigiChecks SHACL Compliancy Check Service is part of the DigiChecks framework. This specific service implements a SHACL Compliancy Check engine to check data from a permitting process against predefined SHACL rules. The tool was developed within the DigiChecks project.

## Prerequisites

- Python 3.12
- Docker and Docker Compose (for containerized deployment)
- uv (Python package manager)

## Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd digichecks-shacl-service
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set the required values

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Start services**
   ```bash
   docker compose up -d
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Initialize database with super user**
   ```bash
   uv run python init_database.py
   ```

   Save the generated `client_id` and `client_secret` for authentication.

The API will be available at `http://localhost:8000`. API documentation is accessible at `http://localhost:8000/docs`.

## Architecture

The service uses a multi-schema PostgreSQL database:
- `core` schema: Authentication and authorization (companies, applications)
- `compliance` schema: Validation entities (checks, connectors)

SHACL rules can be sourced from:
- Hosted: Rules stored directly in the database
- API: Rules fetched dynamically from external APIs via connectors

## References

- [www.digichecks.eu](https://digichecks.eu/)
- [CORDIS EU Database](https://cordis.europa.eu/project/id/101058541/results)

This Project has received Funding from the European Union´s Horizon Europe research and innovation programme - Project 101058541 — DigiChecks