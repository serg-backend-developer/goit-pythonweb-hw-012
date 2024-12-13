FROM python:3.12-alpine

WORKDIR /app

EXPOSE 8000

COPY poetry.lock pyproject.toml /app/

RUN apk add --no-cache --virtual .build-deps \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi \
    && apk del .build-deps

COPY . /app

CMD alembic upgrade head && fastapi run --host 0.0.0.0