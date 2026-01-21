FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /jenkins
