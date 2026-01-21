FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip pipenv

WORKDIR /jenkins
