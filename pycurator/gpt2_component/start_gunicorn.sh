#!/usr/bin/env bash

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16G
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-task=1
#SBATCH --job-name=GPT2_SERVER
#SBATCH --output=slurm_logs/%x-%j.out    # %x-%j means JOB_NAME-JOB_ID.

set -euo pipefail

# Indefinite timeout used to keep the model in memory for a long time

../venv/bin/gunicorn \
  --config ../gunicorn.conf.py \
  --access-logfile ../data/logs/gpt2_server.log \
  --bind "$(hostname)".isi.edu:5001 \
  --timeout 0 \
  server:app
