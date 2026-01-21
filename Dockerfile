FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless xvfb && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip pipenv

WORKDIR /jenkins
