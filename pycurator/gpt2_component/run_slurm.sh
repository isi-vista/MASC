#!/usr/bin/env bash

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=16G
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-task=1
#SBATCH --job-name=GPT2_COM
#SBATCH --output=slurm_logs/%x-%j.out    # %x-%j means JOB_NAME-JOB_ID.

set -euo pipefail

source ../venv/bin/activate

echo "Current node: $(hostname)"
echo "Current working directory: $(pwd)"
echo "Starting run at: $(date)"
echo "Job ID: $SLURM_JOB_ID"

# Run GPT-2 script
echo
time PYTHONPATH=../../ python -m pycurator.gpt2_component.gpt2 --input-file "$1" --output-file "$2"
echo

# Finish up the job
echo "Job finished with exit code $? at: $(date)"
