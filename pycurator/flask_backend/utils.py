"""Module for utility functions."""

from typing import AbstractSet, Any, List, Mapping, MutableMapping, Sequence

from spacy.language import Language


def is_cyclic(
    v: int, neighbours: Mapping[int, List[int]], visited: List[bool], rec_stack: List[bool]
) -> bool:
    """Helper function for contains_cycle().

    Args:
        v: Vertex.
        neighbours: Graph adjacency list.
        visited: Whether vertices have been visited.
        rec_stack: ???

    Returns:
        True if ???, False otherwise.
    """
    visited[v] = True
    rec_stack[v] = True

    for neighbour in neighbours[v]:
        if not visited[neighbour] and is_cyclic(neighbour, neighbours, visited, rec_stack):
            return True
        elif rec_stack[neighbour]:
            return True
    rec_stack[v] = False
    return False


def contains_cycle(events: Sequence[Mapping[str, Any]], links: Sequence[Mapping[str, Any]]) -> bool:
    """Detects whether an event graph contains a cycle.

    Args:
        events: List of Event (refer to the TypeScript class Event in the frontend file for format)
            objects.
        links: List of (event_text, event_text) pairs corresponding to preceding and succeeding
            events.

    Returns:
        True if the graph contains a cycle, False otherwise.
    """
    V = {k: v for v, k in enumerate([e["event_text"] for e in events])}
    E = [(V[link["source"]], V[link["target"]]) for link in links]
    neighbours: Mapping[int, List[int]] = {k: [] for k in V.values()}

    for edge in E:
        neighbours[edge[0]].append(edge[1])
    visited = [False] * len(V)
    rec_stack = [False] * len(V)
    for node in range(len(V)):
        if not visited[node] and is_cyclic(node, neighbours, visited, rec_stack):
            return True
    return False


def consistent_refvars(events: Sequence[Mapping[str, Any]]) -> bool:
    """Detects whether all refvars with identical IDs use same constraints.

    Args:
        events: List of Event (refer to TypeScript class Event in the frontend file for format)
            objects.

    Returns:
        True if all refvars of same ID have consistent constraints, False otherwise.
    """
    refvar_dict: MutableMapping[str, AbstractSet[str]] = {}
    for event in events:
        if "args" in event and event["args"]:
            for arg in event["args"]:
                if "refvar" not in arg or arg["refvar"] is None:
                    continue
                if (
                    arg["refvar"] in refvar_dict
                    and set(arg["constraints"]) != refvar_dict[arg["refvar"]]
                ):
                    return False
                else:
                    refvar_dict[arg["refvar"]] = set(arg["constraints"])
    return True


def clean_refvar(refvar: str) -> str:
    """Cleans refvar string of characters that cause issues for filenames.

    Args:
        refvar: A string representing a refvar.

    Returns:
        A cleaned string.
    """
    refvar = refvar.replace(" ", "_")
    refvar = refvar.replace("/", "_")
    return refvar


def get_verb_lemma(nlp: Language, sentence: str) -> str:
    """Returns the lemma of the first verb in the sentence.

    Args:
        nlp: A spaCy English Language model.
        sentence: An event description.

    Returns:
        The lemma of the first verb, or an empty string if no verbs exist.
    """
    for token in nlp(sentence):
        if token.pos_ == "VERB":
            return str(token.lemma_)
    return ""
