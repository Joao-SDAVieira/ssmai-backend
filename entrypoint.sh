#!/bin/sh

poetry run alembic upgrade head

poetry run uvicorn --host 0.0.0.0 src.ssmai_backend.app:app