FROM ghcr.io/astral-sh/uv:0.11.25 AS uv

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=uv /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fontforge \
    locales \
    python-is-python3 \
    python3-fontforge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -fs /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && sed -i 's/^# *\\(ja_JP.UTF-8 UTF-8\\)/\\1/' /etc/locale.gen \
    && locale-gen

ENV LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:en \
    LC_ALL=ja_JP.UTF-8

WORKDIR /app
