FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
        xsltproc \
        libxml2-utils \
        subversion \
        default-jre-headless \
        fop \
        docbook-xsl \
        docbook-xsl-ns \
        zip \
        python3 \
        git \
        wget \
        ca-certificates \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Allow overriding JVM heap for FOP at runtime.
ENV FOP_OPTS="-Xms512m -Xmx1024m"
