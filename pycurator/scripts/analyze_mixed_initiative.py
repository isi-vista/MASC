"""Script for analyzing mixed initiative schemas."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from http import HTTPStatus
import itertools
from pathlib import Path
import re
import statistics
import textwrap
import time
from typing import Any, List, Optional, cast

from pydantic import BaseModel
from pydantic.tools import parse_obj_as
import requests
from sdf.yaml_schema import Schema
import yaml


class LogItem(BaseModel):
    """Item from schema tracking log.

    Attributes:
        date: Date and time of event.
        type: Type of event.
        author: Person triggering event.
        data: Additional data about event.
    """

    date: datetime
    type: str
    author: Optional[str]
    data: Any


def get_author(schema: Schema) -> str:
    """Extracts author initials from schema ID.

    Args:
        schema: Created schema.

    Returns:
        Initials of schema author.
    """
    match = re.match(r"mi_ComplexEvent0\d{2}_(\w{2}).*", schema.schema_id)
    if match is None:
        raise ValueError(f"Could not extract author from {schema.schema_id}.")
    author = cast(str, match.group(1))
    return author


def main() -> None:
    """Analyze mixed initiative schemas."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, required=True, help="Input schema directory path."
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise IOError(f"Schema directory {args.input_dir} does not exist or is not a directory")

    yaml_files = sorted(args.input_dir.glob("*.yaml"))

    yaml_schemas = []
    for yaml_file in yaml_files:
        with yaml_file.open() as file:
            yaml_data = yaml.safe_load(file)
        yaml_schemas.extend(yaml_data)
    schemas: List[Schema] = parse_obj_as(List[Schema], yaml_schemas)

    for schema in schemas:
        author = get_author(schema)
        schema.private_data["author"] = author
        schema.private_data["tracking"] = parse_obj_as(
            List[LogItem], schema.private_data["tracking"]
        )
        for log_item in schema.private_data["tracking"]:
            log_item.author = author

    wrapper = textwrap.TextWrapper(width=80, subsequent_indent=" " * 4)

    print("+++ General +++")

    log_items = list(
        itertools.chain.from_iterable(schema.private_data["tracking"] for schema in schemas)
    )
    log_types = sorted(set(log_item.type for log_item in log_items))
    print(wrapper.fill(f"Log types: {log_types}"))
    authors = sorted(set(schema.private_data["author"] for schema in schemas))
    print(f"Authors: {authors}")

    log_type_counts = dict(Counter(log_item.type for log_item in log_items).most_common())
    print("Log type counts:")
    for log_type, counts in log_type_counts.items():
        print(f"\t{log_type}: {counts}")
    log_type_counts_per_user = {
        log_type: dict(Counter(i.author for i in log_items if i.type == log_type).most_common())
        for log_type in log_types
    }
    print("Log type counts per user:")
    for log_type, counts_per_user in log_type_counts_per_user.items():
        print(f"\t{log_type}: {counts_per_user}")
    bad_reorders = sum(
        log_item.type == "reorder_event"
        and log_item.data["old_index"] != log_item.data["new_index"]
        for log_item in log_items
    )
    print(
        f"Percent actual re-orderings: {bad_reorders / log_type_counts['reorder_event']:.0%} "
        f"({bad_reorders}/{log_type_counts['reorder_event']})"
    )

    print("\n+++ Total step entering time +++")
    times_taken = []
    for schema in schemas:
        start_time = schema.private_data["tracking"][0].date
        end_time = schema.private_data["tracking"][-1].date
        times_taken.append(end_time - start_time)
    seconds_taken = [t.total_seconds() for t in times_taken]
    print(f"Minimum total step entering time: {timedelta(seconds=round(min(seconds_taken)))}")
    print(f"Maximum total step entering time: {timedelta(seconds=round(max(seconds_taken)))}")
    print(
        f"Mean total step entering time: {timedelta(seconds=round(statistics.mean(seconds_taken)))}"
    )
    print(
        f"Median total step entering time: "
        f"{timedelta(seconds=round(statistics.median(seconds_taken)))}"
    )

    print("\n+++ Schema lengths +++")
    script_lengths = sorted(len(schema.steps) for schema in schemas)
    print(f"Minimum schema length: {min(script_lengths)}")
    print(f"Maximum schema length: {max(script_lengths)}")
    print(f"Mean schema length: {statistics.mean(script_lengths):.1f}")
    print(f"Median schema length: {statistics.median(script_lengths):.1f}")

    print("\n+++ Suggestion usage +++")
    total_suggestions_given = 0
    total_events_added = 0
    total_suggestions_used_exact = 0
    total_suggestions_used_ignore_case = 0
    total_suggestions_used_rough = 0
    for schema in schemas:
        last_suggestion_selected: Optional[str] = None
        for log_item in schema.private_data["tracking"]:
            if log_item.type == "add_event":
                total_events_added += 1
                if last_suggestion_selected is not None:
                    suggested = last_suggestion_selected
                    added = log_item.data
                    if suggested == added:
                        total_suggestions_used_exact += 1
                    if suggested.lower() == added.lower():
                        total_suggestions_used_ignore_case += 1
                    if SequenceMatcher(None, suggested.lower(), added.lower()).ratio() > 0.8:
                        total_suggestions_used_rough += 1
            elif log_item.type == "gpt2_suggestion_output":
                total_suggestions_given += 1
                last_suggestion_selected = None
            elif log_item.type == "gpt2_suggestion_select":
                last_suggestion_selected = log_item.data
    print(f"Total suggestion sets given: {total_suggestions_given}")
    print(f"Total events added: {total_events_added}")
    print(
        f"Total suggestions used (exact match): {total_suggestions_used_exact} "
        f"({total_suggestions_used_exact/total_events_added:.1%})"
    )
    print(
        f"Total suggestions used (exact match, ignoring case): "
        f"{total_suggestions_used_ignore_case} "
        f"({total_suggestions_used_ignore_case/total_events_added:.1%})"
    )
    print(
        f"Total suggestions used (rough match): {total_suggestions_used_rough} "
        f"({total_suggestions_used_rough/total_events_added:.1%})"
    )

    # Although timing is recorded in the logs, this is to get benchmarks with the improved server
    print("\n+++ Suggestion generation time +++")
    times = []
    for log_item in log_items:
        if log_item.type != "gpt2_suggestion_input":
            continue
        gpt2_input = log_item.data["input"]
        request_url = "https://dev.example.org/api/get_gpt2_suggestions"
        start = time.time()
        request_response = requests.get(request_url, params=gpt2_input, timeout=30)
        end = time.time()
        times.append(end - start)
        # Abort script if GPT-2 server does not return suggestions properly
        if request_response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"GPT-2 server returned status code {request_response.status_code}")
        if "suggestions" not in request_response.json():
            raise RuntimeError("GPT-2 server returned malformed output")
    print(f"Total suggestion generation time: {sum(times):.1f} s")
    print(f"Minimum suggestion generation time: {min(times):.1f} s")
    print(f"Maximum suggestion generation time: {max(times):.1f} s")
    print(f"Mean suggestion generation time: {statistics.mean(times):.1f} s")
    print(f"Median suggestion generation time: {statistics.median(times):.1f} s")


if __name__ == "__main__":
    main()
