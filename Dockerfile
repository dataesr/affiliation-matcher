# syntax=docker/dockerfile:1
FROM ubuntu:18.04

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    locales-all \
    python3-pip \
    python3-setuptools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

WORKDIR /src

COPY requirements.txt .
RUN pip3 install --upgrade pip setuptools && pip3 install -r requirements.txt --proxy=${HTTP_PROXY}

COPY . .
