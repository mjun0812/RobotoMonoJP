FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libfreetype6-dev \
    libgif-dev \
    libgtk-3-dev \
    libxml2-dev \
    libpango1.0-dev \
    libcairo2-dev \
    libspiro-dev \
    libwoff-dev \
    python3-dev \
    python3-pip \
    python-is-python3 \
    ninja-build \
    cmake \
    build-essential \
    gettext \
    locales \
    git \
    curl \
    ca-certificates \
    vim \
    && apt-get clean  \
    && rm -rf /var/lib/apt/lists/*

# Set time zone
RUN ln -fs /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# Set locale
RUN locale-gen ja_JP.UTF-8
ENV LANG ja_JP.UTF-8 \
    LANGUAGE ja_JP:en \
    LC_ALL ja_JP.UTF-8

# Install fontforge
ENV PYTHON=python3
ENV PYTHONPATH=/usr/local/lib/python3/dist-packages/
RUN git config --global http.postBuffer 157286400 \
    && git clone https://github.com/fontforge/fontforge.git \
    && cd fontforge \
    && mkdir build \
    && cd build \
    && cmake -GNinja -DENABLE_DOCS=off .. \
    && ninja \
    && ninja install \
    && cd ../.. \
    && rm -rf fontforge

# Install fonttools
RUN pip install fonttools
