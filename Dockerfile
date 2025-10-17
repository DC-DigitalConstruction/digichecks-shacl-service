FROM python:3.12-bookworm

# Install uv globally
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies, including Java
RUN apt update && apt upgrade -y
RUN apt-get install -y openjdk-17-jre

# Set environment variables for Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

WORKDIR /code

# Copy the backend directory structure
COPY pyproject.toml pyproject.toml
COPY README.md README.md

RUN uv pip compile pyproject.toml > requirement.txt 
RUN pip install -r requirement.txt

COPY ./api /code/api
COPY ./alembic /code/alembic
COPY init_database.py /code/init_database.py
COPY alembic.ini /code/alembic.ini

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
