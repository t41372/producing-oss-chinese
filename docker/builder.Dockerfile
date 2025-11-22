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
    && rm -rf /var/lib/apt/lists/*

# Download Noto Sans SC (Simplified Chinese) fonts manually to avoid FOP issues with TTC/CFF
RUN mkdir -p /usr/share/fonts/opentype/noto && \
    wget -P /usr/share/fonts/opentype/noto \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Bold.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKsc-Regular.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKsc-Bold.otf

WORKDIR /workspace

# Allow overriding JVM heap for FOP at runtime.
ENV FOP_OPTS="-Xms512m -Xmx1024m"
