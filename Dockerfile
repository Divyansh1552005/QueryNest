# Stage - 1 : Build stage
FROM python:3.12-slim AS builder

# Stops Python from creating .pyc files coz they are useless inside a docker container
# 2nd command -> Forces Python to print logs immediately coz CLI tools must show the output immediately
# # 3rd command -> langchain issue resolution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore::FutureWarning


WORKDIR /app

# build tools for the debian based img we chose above
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

    
COPY pyproject.toml ./
COPY src ./src

# installing uv for faster (pip is slow af)
RUN pip install --no-cache-dir uv

# install querynest pacakge
# --system means it will be outside any virtualenv , since no venv needed for docker
RUN uv pip install --system .


# Stage-2 : Running stage

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only installed Python packages and CLI
COPY --from=builder /usr/local /usr/local

ENTRYPOINT ["querynest"]

