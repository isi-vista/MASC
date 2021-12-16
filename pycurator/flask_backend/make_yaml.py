"""Module for converting front-end schema objects into a YAML schema."""

from collections import Counter
import datetime
from pathlib import Path
from typing import Any, Counter as tCounter, Mapping, MutableMapping, Sequence

from sdf import yaml2sdf
from sdf.yaml_schema import Before, Order, Schema, Slot, Step
import yaml


def populate_slots(events: Sequence[Mapping[str, Any]]) -> Sequence[Slot]:
    """Populates schema-level slots from event arguments.

    This function uses some simple heuristics to generate slots:
    - If a refvar appears at least twice, a slot is made for it.
    - If there are no refvars that appear at least twice, refvars that appear once will be used
        instead.
    - The slot role name is the refvar converted to PascalCase.
    - The slot constraints are from the first appearance of the refvar, because the constraints have
        already been validated.

    Args:
        events: List of Event (refer to the TypeScript class Event in the frontend file for format)
            objects.

    Returns:
        List of schema Slot objects.
    """
    refvar_counts: tCounter[str] = Counter()
    refvar_types: MutableMapping[str, Sequence[str]] = {}
    refvar_references: MutableMapping[str, str] = {}

    # Get all refvars from step slots
    for event in events:
        if "args" in event and event["args"]:
            for arg in event["args"]:
                if "refvar" in arg and arg["refvar"] is not None:
                    refvar = arg["refvar"]
                    if refvar not in refvar_types:
                        refvar_types[refvar] = arg["constraints"]
                    if refvar not in refvar_references and "reference" in arg:
                        refvar_references[refvar] = arg["reference"]
                    refvar_counts[refvar] += 1

    # Determine which refvars to make schema-level slots from
    if not refvar_counts:
        refvars = []
    elif refvar_counts.most_common()[0][1] >= 2:
        refvars = [refvar for refvar, count in refvar_counts.most_common() if count >= 2]
    else:
        refvars = list(refvar_counts.keys())
    refvars.sort()

    # Create schema-level slots
    slots = []
    for refvar in refvars:
        slot = Slot(
            role="".join(w.capitalize() for w in refvar.split()),
            refvar=refvar,
            constraints=sorted(refvar_types[refvar]),
        )
        if refvar in refvar_references:
            slot.reference = refvar_references[refvar]
        slots.append(slot)

    return slots


def populate_steps(events: Sequence[Mapping[str, Any]]) -> Sequence[Step]:
    """Populates the steps key of the schema dict with events.

    Args:
        events: List of Event (refer to the TypeScript class Event in the frontend file for format)
            objects.

    Returns:
        List of schema Step objects.
    """
    steps = []
    for event in events:
        slots = (
            [Slot.parse_obj(s) for s in event["args"]] if "args" in event and event["args"] else []
        )
        step = Step(
            id=event["event_text"],
            primitive=event["event_primitive"],
            slots=slots,
            comment=event.get("comment", None),
            required=event.get("required", None),
            reference=event.get("reference", None),
        )
        steps.append(step)
    return steps


def populate_order(links: Sequence[Mapping[str, str]]) -> Sequence[Order]:
    """Creates the order dict from the graph links passed.

    Args:
        links: List of (event_text, event_text) pairs corresponding to preceding and succeeding
            events.

    Returns:
        List of schema Order objects.
    """
    order = []
    for link in links:
        order.append(Before(before=link["source"], after=link["target"]))
    return order


def create_schema(
    events: Sequence[Mapping[str, Any]],
    links: Sequence[Mapping[str, str]],
    tracking: Sequence[Mapping[str, Any]],
    schema_id: str,
    schema_name: str,
    schema_dscpt: str,
) -> Schema:
    """Takes the events and links lists from the applications and creates a schema for it.

    Args:
        events: List of Event (refer to the TypeScript class Event in the frontend file for format)
            objects.
        links: List of (event_text, event_text) pairs corresponding to preceding and succeeding
            events.
        links: List of tracking objects.
        schema_id: Schema ID.
        schema_name: Schema name.
        schema_dscpt: Schema description.

    Returns:
        Schema object created.
    """
    datetime_now = (
        str(datetime.datetime.now()).replace(" ", "-").replace(":", "-").replace(".", "-")
    )
    return Schema(
        schema_id=schema_id,
        schema_name=schema_name,
        schema_dscpt=schema_dscpt,
        schema_version=datetime_now,
        slots=populate_slots(events),
        steps=populate_steps(events),
        order=populate_order(links),
        private_data={"tracking": tracking},
    )


def save_schema(schema: Schema, output_directory: Path) -> Path:
    """Save Schema object as YAML file.

    Args:
        schema: Schema to be saved.
        output_directory: Location on the NAS or local drive at which to store the schema.

    Returns:
        Path to the newly-created YAML file.
    """
    schemas = [schema.dict(exclude_none=True)]
    yaml_fname = output_directory / f"{schema.schema_id}_{schema.schema_version}.yaml"
    with yaml_fname.open("w") as y_file:
        yaml.dump(schemas, y_file, sort_keys=False)

    yaml2sdf.convert_all_yaml_to_sdf(schemas, "isi", "https://example.org/kairos/", yaml_fname.stem)

    return yaml_fname
