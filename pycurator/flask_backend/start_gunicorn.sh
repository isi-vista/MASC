#!/usr/bin/env bash

set -euo pipefail

../venv/bin/gunicorn \
  --config ../gunicorn.conf.py \
  --access-logfile ../data/logs/app.log \
  --bind 127.0.0.1:5000 \
  --timeout 120 \
  app:app
