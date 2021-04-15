FROM ubuntu:18.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.6 \
    python3-pip \
    libpython3.6 \
    locales \
    locales-all \
    python3-setuptools \
    g++ \
    python3-dev \
    x11-utils \
    alsa-utils \
    x11-apps \
    libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \ 
    libfreetype6 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \ 
    libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \ 
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \ 
    libnss3 libxcomposite1 libgtk2.0-0 libgtk-3-0 xvfb xorg xterm libatk-bridge2.0-0 \ 
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

COPY requirements.txt /src/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt --proxy=${HTTP_PROXY}

COPY . /src
#CMD [ "app.py" ]
#CMD ["/bin/sh", "start.sh"]
