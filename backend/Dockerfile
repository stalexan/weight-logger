FROM python:3.11-bullseye
ARG ENV

# Install Debian packages.
USER root
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        gosu \
        locales; \
    if [ "$ENV" = "dev" ]; then \
        apt-get install -y --no-install-recommends \
            apt-utils \
            bash-completion \
            htop \
            iproute2 \
            iputils-ping \
            less \
            net-tools \
            postgresql-client \
            tmux \
            tree \
            vim; \
    fi; \
    rm -rf /var/lib/apt/lists/*

# Create user wls
RUN set -eux; \
    groupadd wls; \
    useradd --gid wls --create-home --shell /bin/bash wls;

# Install pip dependencies.
USER wls
RUN set -eux; \
    pip install --no-warn-script-location \
        argon2_cffi \
        fastapi[all] \
        loguru \
        matplotlib \
        mypy \
        passlib \
        psycopg2 \
        pydantic \
        pylint \
        pytest \
        python-jose \
        python-multipart \
        sqlalchemy \
        tabulate \
        types-tabulate;
ENV PATH /home/wls/.local/bin:$PATH

# Install any available types.
#RUN mypy --install-types

# Set the locale
USER root
RUN set -eux; \
    rm -rf /var/lib/apt/lists/*; \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8;
ENV LANG en_US.utf8

# USER environment variables is needed by some scripts.
USER wls
ENV USER=wls

# Create app directory.
USER wls
WORKDIR /opt/wl-backend

# Install entrypoint.
USER root
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod ugo+rx /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "--host", "0.0.0.0", "backend:app"]
