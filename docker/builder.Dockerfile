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

# Download Noto Sans SC + Noto Serif SC (Simplified Chinese) and the
# Noto Sans Mono CJK SC fonts manually.  We pull the SubsetOTF builds
# rather than TTC/CFF because FOP's font subsystem misbehaves on those.
# Typography recipe:
#   - body     = Noto Serif SC   (思源宋体, serif body for long-form reading)
#   - headings = Noto Sans SC    (思源黑体, sans for crisp hierarchy)
#   - code     = Noto Sans Mono CJK SC (monospace, CJK-aware)
RUN mkdir -p /usr/share/fonts/opentype/noto && \
    wget -P /usr/share/fonts/opentype/noto \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Bold.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Serif/SubsetOTF/SC/NotoSerifSC-Regular.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Serif/SubsetOTF/SC/NotoSerifSC-Bold.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKsc-Regular.otf \
    https://github.com/notofonts/noto-cjk/raw/main/Sans/Mono/NotoSansMonoCJKsc-Bold.otf

WORKDIR /workspace

# Allow overriding JVM heap for FOP at runtime.
ENV FOP_OPTS="-Xms512m -Xmx1024m"
