"""Module for querying and selecting KGTK candidates."""

from typing import Any, Callable, List, Mapping, Sequence
import urllib

import numpy as np
import requests
from sentence_transformers import SentenceTransformer, util as ss_util


def make_kgtk_candidates_filter(source_str: str) -> Callable[[Mapping[str, Any]], bool]:
    """Generates filter function for filtering out unwanted candidates for particular string.

    Args:
        source_str: The source_str used to query and to use for filtering candidates.

    Returns:
        A filter function particular to source_str.
    """

    def kgtk_candidate_filter(candidate: Mapping[str, Any]) -> bool:
        str_found = source_str in candidate["label"][0]
        str_found = str_found or any(source_str in alias for alias in candidate["alias"])
        description_and_casematch = candidate["description"] and candidate["label"][0].islower()
        return str_found and description_and_casematch

    return kgtk_candidate_filter


def get_ss_model_similarity(
    ss_model: SentenceTransformer, source_str: str, candidates: List[Mapping[str, Any]]
) -> Any:
    """Computes cosine similarity between source string (event description or refvar) and candidate descriptions.

    Args:
        ss_model: A SentenceTransformer model.
        source_str: The source string for comparing embedding similarity.
        candidates: A list of JSON (dict) objects representing candidates.

    Returns:
        A tensor of similarity scores.
    """
    all_strings = [source_str] + [candidate["description"][0] for candidate in candidates]
    all_encodings = ss_model.encode(all_strings, convert_to_tensor=True)
    source_emb, candidate_emb = all_encodings[0], all_encodings[1:]
    sim_scores = ss_util.pytorch_cos_sim(source_emb, candidate_emb)[0]
    return sim_scores


def get_request_kgtk(query: str) -> List[Mapping[str, Any]]:
    """Submits a GET request to KGTK's API.

    Args:
        query: A string to query against KGTK's Wikidata.

    Returns:
        A list of candidates, or an empty list.
    """
    formatted_query = urllib.parse.quote(query)
    kgtk_request_url = f"https://kgtk.isi.edu/api?q={formatted_query}&extra_info=true&language=en&type=exact&is_class=true"
    try:
        kgtk_response = requests.get(kgtk_request_url, timeout=5, verify=False)
    except requests.exceptions.RequestException:
        return []
    if kgtk_response.status_code != 200:
        return []
    else:
        candidates = list(kgtk_response.json())
        filtered_candidates = list(filter(make_kgtk_candidates_filter(query), candidates))
        return filtered_candidates


def wikidata_topk(
    ss_model: SentenceTransformer,
    source_str: str,
    candidates: List[Mapping[str, Any]],
    k: int,
    thresh: float = 0.15,
) -> Sequence[Mapping[str, Any]]:
    """Returns top k candidates for string according to scoring function.

    Args:
        ss_model: A SentenceTransformer model.
        source_str: A string that candidates will be generated for.
        candidates: A list of JSON (dict) objects representing candidates.
        k: The maximum number of top candidates to return.
        thresh: The minimum cosine similarity to be selected.

    Returns:
        A list of k candidates.
    """
    sent_sim_scores = get_ss_model_similarity(ss_model, source_str, candidates)
    top_k_idx = np.argsort(-sent_sim_scores)[:k]
    top_k_scores = list(zip(top_k_idx, sent_sim_scores[top_k_idx]))
    top_k = [candidates[idx] for idx, score in top_k_scores if score >= thresh]
    return top_k


def filter_duplicate_candidates(candidates: List[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    """Filters duplicate candidates from concatenated list of KGTK queries.

    Args:
        candidates: A list of JSON (dict) objects representing candidates.

    Returns:
        A list of unique list of candidates.
    """
    label_description_set = set()
    unique_candidates = []
    for candidate in candidates:
        label_description_tuple = (candidate["label"][0], candidate["description"][0])
        if label_description_tuple not in label_description_set:
            unique_candidates.append(candidate)
            label_description_set.add(label_description_tuple)
    return unique_candidates
