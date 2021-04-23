# syntax=docker/dockerfile:1
FROM python:3.6-alpine

RUN apk add --update g++ libxslt-dev

WORKDIR /src

COPY requirements.txt .
RUN pip3 install --upgrade pip setuptools && pip3 install -r requirements.txt --proxy=${HTTP_PROXY}

COPY . .
