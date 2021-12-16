"""Runs GPT-2 component on SAGA with one job per schema."""

import argparse
from pathlib import Path
import subprocess

from pycurator.common.paths import EVENT_REC_DIR, SCHEMA_DIR

SLURM_LOG_DIR = Path("slurm_logs")


def main() -> None:
    """Starts jobs for each schema."""
    p = argparse.ArgumentParser(description=__doc__)
    args = p.parse_args()

    if not SCHEMA_DIR.is_dir():
        raise IOError(f"Schema directory {SCHEMA_DIR} is not an existing directory")

    EVENT_REC_DIR.mkdir(parents=True, exist_ok=True)
    SLURM_LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Read in file paths
    input_paths = sorted(SCHEMA_DIR.glob("*.yaml"))

    total = 0
    for yaml_path in input_paths:
        # Determine output path
        json_path = EVENT_REC_DIR / f"{yaml_path.stem}.json"

        # Don't re-run on existing schemas
        if json_path.exists():
            continue

        # Submit Slurm job for each partition
        command_tokens = ["sbatch"]
        command_tokens.extend(("run_slurm.sh", str(yaml_path), str(json_path)))
        command = " ".join(command_tokens)
        print(f"Submitting `{command}`")
        subprocess.run(command, shell=True, check=True)

        total += 1

    print(f"{total} schema runs started on {args.slurm_partition}")


if __name__ == "__main__":
    main()
