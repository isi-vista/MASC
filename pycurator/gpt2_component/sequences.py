"""Extract sequences from YAML schemas."""

from pathlib import Path
from typing import Any, List, Mapping, Sequence

import networkx as nx
from pydantic import parse_obj_as
from sdf.yaml_schema import Before, Schema
import yaml


def load_schemas(yaml_path: Path) -> Sequence[Schema]:
    """Loads a schema file.

    Args:
        yaml_path: Path to YAML schema file.

    Returns:
        List of schemas.
    """
    with yaml_path.open() as file:
        schemas: Sequence[Schema] = parse_obj_as(List[Schema], yaml.safe_load(file))
    return schemas


def schema_to_sequences(
    schema: Schema, min_length: int = 1, max_length: int = 4, starting_steps_only: bool = True
) -> Mapping[str, Any]:
    """Converts schema to sequences, alongside schema metadata.

    Args:
        schema: Schema.
        min_length: Minimum sequence length to include.
        max_length: Maximum sequence length to include.
        starting_steps_only: Only include sequences that begin with a starting step.

    Returns:
        Mapping containing extracted sequences, alongside the schema's ID, name, and description.
    """
    # Generate event graph
    edges = []
    for order in schema.order:
        if not isinstance(order, Before):
            continue
        edges.append((order.before, order.after))
    graph = nx.DiGraph(edges)

    # Extract paths
    all_paths = []
    if starting_steps_only:
        seq_start_nodes = [n for n, d in graph.in_degree if d == 0]
    else:
        seq_start_nodes = graph.nodes
    if min_length <= 1:
        all_paths.extend([[n] for n in seq_start_nodes])
    for node in seq_start_nodes:
        other_nodes = set(graph.nodes) - {node}
        paths = [
            p
            for p in nx.all_simple_paths(graph, node, other_nodes, cutoff=max_length + 1)
            if min_length <= len(p) <= max_length
        ]
        all_paths.extend(paths)
    all_paths.sort()

    # Format output
    sequences = {
        "schema_id": schema.schema_id,
        "name": schema.schema_name,
        "description": schema.schema_dscpt,
        "sequences": all_paths,
    }

    return sequences
