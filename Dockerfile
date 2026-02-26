FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN pip install --upgrade pip pipenv

WORKDIR /jenkins

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy --dev

COPY . .
