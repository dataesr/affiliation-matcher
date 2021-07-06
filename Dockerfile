FROM ubuntu:18.04

RUN  apt-get update \
  && apt-get install -y wget \
     gnupg2

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.6 \
    python3-pip \
    libpython3.6 \
    locales \
    locales-all \
    python3-setuptools \
    g++ \
    python3-dev \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

COPY requirements.txt /src/requirements.txt
RUN pip3 install --upgrade pip
RUN     pip3     install -r requirements.txt --proxy=${HTTP_PROXY}

COPY . /src
