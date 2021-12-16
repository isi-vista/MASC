"""Initializes model cache."""

import argparse
from pathlib import Path

from transformers import GPT2LMHeadModel, GPT2Tokenizer

from pycurator.gpt2_component.gpt2 import CACHE_DIR, MODEL_NAME


def init_cache(model_name: str, cache_dir: Path) -> None:
    """Initializes the cache for a model in a cache directory.

    Args:
        model_name: Name of model to load.
        cache_dir: Directory of cache.
    """
    _ = GPT2Tokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    _ = GPT2LMHeadModel.from_pretrained(model_name, cache_dir=cache_dir)


def main() -> None:
    """Initializes model cache."""
    p = argparse.ArgumentParser(description=__doc__)
    _ = p.parse_args()

    init_cache(MODEL_NAME, CACHE_DIR)


if __name__ == "__main__":
    main()
