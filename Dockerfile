FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Tokyo \
    LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:en \
    LC_ALL=ja_JP.UTF-8 \
    UV_SYSTEM_PYTHON=1 \
    UV_BREAK_SYSTEM_PACKAGES=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        locales \
        make \
        python3 \
        python3-pip \
        python3-fontforge \
        fontforge \
        tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && locale-gen ja_JP.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# fontforge python bindings live in system dist-packages.
ENV PYTHONPATH=/usr/lib/python3/dist-packages:/app/src

# uv installed to /usr/local/bin so it is on PATH.
RUN curl -LsSf https://astral.sh/uv/install.sh \
    | env UV_INSTALL_DIR=/usr/local/bin sh

WORKDIR /app

# Install the package against the system python so importlib.metadata can read
# the project version. Source is mounted at runtime for local generation.
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY src /app/src
RUN uv pip install --system --break-system-packages .

CMD ["bash"]
