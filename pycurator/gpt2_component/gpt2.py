"""Execute GPT-2 with extracted sequences."""

import argparse
import json
from pathlib import Path
import re
from typing import MutableMapping, MutableSequence, Sequence, Set, Tuple
import unicodedata

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from pycurator.common.logger import return_logger
from pycurator.common.paths import LOG_DIR
from pycurator.gpt2_component.filter import DefaultCriteria, get_only_k, result_replace
from pycurator.gpt2_component.sequences import load_schemas, schema_to_sequences

CACHE_DIR = Path(__file__).resolve().parent / ".model_cache"
MODEL_NAME = "gpt2-large"
logging = return_logger(LOG_DIR / "gpt2_component.log")


def get_device() -> torch.device:
    """Gets device to use for PyTorch.

    Returns:
        Device.
    """
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    logging.info("Model device: %s", device)
    return device


def load_gpt2(name: str, device: torch.device) -> Tuple[GPT2Tokenizer, GPT2LMHeadModel]:
    """Loads GPT-2 into memory.

    Args:
        name: Model name.
        device: GPT-2 device.

    Returns:
        GPT-2 tokenizer and model.
    """
    logging.info("Loading model")
    tokenizer = GPT2Tokenizer.from_pretrained(name, cache_dir=CACHE_DIR)
    gpt2 = GPT2LMHeadModel.from_pretrained(
        name, pad_token_id=tokenizer.eos_token_id, cache_dir=CACHE_DIR
    ).to(device)
    gpt2.half()  # Convert to FP16
    return tokenizer, gpt2


def convert_sequence_to_text(
    schema_name: str,
    schema_desc: str,
    sequence: Sequence[str],
) -> str:
    """Converts sequence to text to use as GPT-2 input.

    Args:
        schema_name: Name of schema to run on.
        schema_desc: Description / definition of the schema.
        sequence: Sequence of steps.

    Returns:
        Text to use as input.
    """
    formatted_desc = re.sub(r"\s+", " ", schema_desc)
    initial_input = f"{formatted_desc} Describe steps of {schema_name.replace('_', ' ')}. "
    last_number = f"{len(sequence) + 1}. "
    sentences = [f"{i + 1}. {p}." for i, p in enumerate(sequence)] + [last_number]
    text = initial_input + " ".join(sentences)
    return text


def make_predictions(
    text: str,
    tokenizer: GPT2Tokenizer,
    gpt2: GPT2LMHeadModel,
    device: torch.device,
    max_output_length: int = 100,
) -> Sequence[str]:
    """Make predictions for text using GPT-2.

    Args:
        text: Input text.
        tokenizer: GPT-2 tokenizer.
        gpt2: GPT-2 model.
        device: GPT-2 device.
        max_output_length: Maximum length of generated sequence.

    Returns:
        List of predicted strings after the provided text, or an empty list if the input is over 300
        tokens long.
    """
    text = unicodedata.normalize("NFKC", text)
    input_ids = tokenizer.encode(text)
    input_ids = torch.tensor([input_ids]).to(device)  # pylint: disable=not-callable
    input_id_length = len(input_ids[0])

    # Long inputs usually result in useless outputs, so no predictions are acceptable
    if input_id_length > 300:
        return []

    # Enforce maximum generated length to prevent memory issues
    max_length = min(input_id_length + max_output_length, 350)

    with torch.cuda.amp.autocast():  # Run with FP16
        sample_outputs = gpt2.generate(
            input_ids,
            do_sample=True,
            max_length=max_length,
            min_length=2,  # We want output that is at least two words
            temperature=0.8,
            top_k=50,
            top_p=0.8,
            num_return_sequences=40,
        )

    suggestions = []
    for output in sample_outputs:
        decoded_output = result_replace(tokenizer.decode(output[input_id_length:]))
        suggestions.append(decoded_output)

    return suggestions


def run_gpt2(
    tokenizer: GPT2Tokenizer,
    gpt2: GPT2LMHeadModel,
    sequences: Sequence[str],
    device: torch.device,
    schema_name: str,
    schema_desc: str,
) -> MutableMapping[str, MutableSequence[str]]:
    """Executes GPT-2 to generate recommendations for each event.

    Recommendations for each event consist of recommendations from multiple step context.
    For example, assume that there are three sequences toward "set fire":
        obtain-fuel -> prepare-fuel -> set-fire
        prepare-fuel -> set-fire
        search-for-target -> set-fire
    We collect 3 recommendations for each sequence and show the list as a recommendation for "set
    fire".

    Args:
        tokenizer: GPT-2 tokenizer.
        gpt2: GPT-2 model.
        sequences: All sequences to work with.
        device : GPT-2 device.
        schema_name: Name of schema to run on.
        schema_desc: Description / definition of the schema.

    Returns:
        List of schemas, containing events and corresponding recommendations.
    """
    logging.info("Processing %d sequences", len(sequences))
    suggested_events: MutableMapping[str, MutableSequence[str]] = {}

    for seq_index, sequence in enumerate(sequences, start=1):
        preceding_step = sequence[-1]
        if preceding_step not in suggested_events:
            suggested_events[preceding_step] = []

        text = convert_sequence_to_text(
            schema_name=schema_name,
            schema_desc=schema_desc,
            sequence=sequence,
        )
        suggestions = make_predictions(
            text=text,
            tokenizer=tokenizer,
            gpt2=gpt2,
            device=device,
        )

        suggested_events[preceding_step].extend(suggestions)

        logging.info("Finished processing sequence %d / %d", seq_index, len(sequences))

    return suggested_events


def filter_suggestions(
    suggestions: MutableMapping[str, MutableSequence[str]], existing_events: Set[str]
) -> MutableMapping[str, MutableSequence[str]]:
    """Filters suggestions using multiple filters.

    Args:
        suggestions: Suggestions to filter.
        existing_events: Existing events in the schema.

    Returns:
        Filtered suggestions.
    """
    suggestions_to_keep = {}
    events_kept = existing_events
    for k, es in suggestions.items():
        # Re-instantiate to update the reference for no-duplicates
        es_to_keep = DefaultCriteria(existing_events, 3).meet_criteria(es)
        if es_to_keep:
            suggestions_to_keep[k] = es_to_keep
            events_kept = events_kept.union(es_to_keep)
    return suggestions_to_keep


def main() -> None:
    """Executes GPT-2 with extracted sequences."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, required=True, help="Input YAML file path.")
    parser.add_argument("--output-file", type=Path, required=True, help="Output JSON file path.")
    args = parser.parse_args()
    logging.info(args)

    device = get_device()

    tokenizer, gpt2 = load_gpt2(MODEL_NAME, device)

    schemas = load_schemas(args.input_file)
    schema = schemas[0]
    sequences_from_schema = schema_to_sequences(schema)
    existing_events: Set[str] = {s.id for s in schema.steps}
    schema_id = sequences_from_schema["schema_id"]
    schema_name = sequences_from_schema["name"]
    schema_dscpt = sequences_from_schema["description"]
    all_sequences = sequences_from_schema["sequences"]
    suggestions = run_gpt2(
        tokenizer=tokenizer,
        gpt2=gpt2,
        sequences=all_sequences,
        device=device,
        schema_name=schema_name,
        schema_desc=schema_dscpt,
    )

    suggestions_to_keep = filter_suggestions(suggestions, existing_events)
    suggestions_to_keep = get_only_k(suggestions_to_keep, 12)

    output_json = {
        "format_version": "1.0",
        "schema_id": schema_id,
        "schema_name": schema_name,
        "events": suggestions_to_keep,
    }
    with open(args.output_file, "w") as outfile:
        json.dump(output_json, outfile, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
