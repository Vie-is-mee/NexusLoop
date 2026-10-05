#!/usr/bin/env bash
set -e
PY=python
[ -x .venv/bin/python ] && PY=.venv/bin/python
[ -x venv/bin/python ] && PY=venv/bin/python
exec "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8000
