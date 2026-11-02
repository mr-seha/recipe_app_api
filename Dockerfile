FROM docker.arvancloud.ir/python:3.14.7-alpine3.24
LABEL maintainer="Mohammadreza Souri"
ENV PYTHONUNBUFFERED 1
ENV PIP_INDEX_URL https://package-mirror.liara.ir/repository/pypi/simple
ARG DEV=false

RUN apk add --update --no-cache postgresql-client jpeg-dev gettext
RUN apk add --update --no-cache --virtual .tmp-build-deps \
     build-base postgresql-dev musl-dev zlib zlib-dev

RUN python -m venv /py
ENV PATH="/py/bin:$PATH"
RUN /py/bin/pip install --upgrade pip

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

RUN /py/bin/pip install -r /tmp/requirements.txt
RUN if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi
RUN rm -rf /tmp

COPY ./app /app
WORKDIR /app

EXPOSE 8000

RUN adduser --disabled-password --no-create-home django-user

RUN mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod 755 -R /vol

USER django-user