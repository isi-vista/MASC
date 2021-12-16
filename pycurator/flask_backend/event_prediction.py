"""Resources for event primitive prediction."""
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple, Union

from sdf.ontology import ontology
from sentence_transformers import SentenceTransformer, util
import torch

SENT_MODEL_DIR = Path(__file__).resolve().parent / "sent_model"

DEFINITION_EMB_FILE = SENT_MODEL_DIR / "definition.emb"
TEMPLATE_EMB_FILE = SENT_MODEL_DIR / "template.emb"
TEMPLATE_JSON_FILE = SENT_MODEL_DIR / "templates.json"
PRETRAINED_MODEL_DIR = SENT_MODEL_DIR / "pretrained_model"

NUM_EVENTS = len(ontology.events)


def init_embeddings(ss_model: SentenceTransformer) -> Tuple[torch.FloatTensor, torch.FloatTensor]:
    """Initialize embeddings using the SentenceTransformer model.

    Arguments:
        ss_model: SentenceTransformer model (currently RoBERTa-base) used to encode the information.

    Returns:
        The tensors representing the definition embeddings and template embeddings in that order.
    """
    if DEFINITION_EMB_FILE.exists() and TEMPLATE_EMB_FILE.exists():
        definition_embeddings = torch.load(DEFINITION_EMB_FILE)
        template_embeddings = torch.load(TEMPLATE_EMB_FILE)
        return definition_embeddings, template_embeddings

    with open(TEMPLATE_JSON_FILE) as handle:
        template_sentences = json.load(handle)

    db_definitions = [event.definition for event in ontology.events.values()]

    definition_embeddings = ss_model.encode(db_definitions, convert_to_tensor=True)
    torch.save(definition_embeddings, DEFINITION_EMB_FILE)

    template_embeddings = ss_model.encode(template_sentences, convert_to_tensor=True)
    torch.save(template_embeddings, TEMPLATE_EMB_FILE)

    return definition_embeddings, template_embeddings


def init_ss_model() -> SentenceTransformer:
    """Load RoBERTa-base model."""
    return SentenceTransformer(
        "usc-isi/sbert-roberta-large-anli-mnli-snli", cache_folder=str(PRETRAINED_MODEL_DIR)
    )


def request_top_n(
    description: str,
    *,
    n: int,
    ss_model: Optional[SentenceTransformer] = None,
    definition_embeddings: Optional[torch.FloatTensor] = None,
    template_embeddings: Optional[torch.FloatTensor] = None,
) -> Sequence[Mapping[str, Union[str, Sequence[str]]]]:
    """Get the top *n* predicted event primitives from the *ss_model* provided.

    Arguments:
        description: Text to be the basis of the prediction.
        n: Number of top predictions to be returned.
        ss_model: SentenceTransformer model to make the predictions.
        definition_embeddings: Embeddings of the definitions for event primitives.
        template_embeddings: Embeddings of the templates for the event primitives.

    Returns:
        List of predictions (in order of most similar -> least similar) in a dictionary containing the primitive,
        possible primitive subsubtypes, and the text that formed the basis of the prediction.
    """
    # Initialize model and embeddings
    if ss_model is None:
        ss_model = init_ss_model()

    if definition_embeddings is None or template_embeddings is None:
        definition_embeddings, template_embeddings = init_embeddings(ss_model)

    # Similarity scoring
    event_embedding = ss_model.encode([description], convert_to_tensor=True)
    def_cosine_scores = util.pytorch_cos_sim(event_embedding, definition_embeddings)
    template_cosine_scores = util.pytorch_cos_sim(event_embedding, template_embeddings)
    cat_scores = torch.cat((def_cosine_scores, template_cosine_scores), 1)
    sorted_indices = cat_scores.argsort(descending=True)
    recommended_primitives = []

    # Get top n recommendations
    for idx in sorted_indices[0]:
        event = ontology.events[ontology.get_event_by_id(int(idx) % NUM_EVENTS + 1)]
        type_subtype = (event.type, event.subtype)
        if type_subtype not in recommended_primitives:
            recommended_primitives.append(type_subtype)
        if len(recommended_primitives) == n:
            break

    # Format recommendations
    json_return = []
    for rec_prim_type, rec_prim_subtype in recommended_primitives:
        primitive = f"{rec_prim_type}.{rec_prim_subtype}"
        subsubtypes = ontology.get_event_subcats(rec_prim_type, rec_prim_subtype)
        description = ontology.events[ontology.get_default_event(primitive)].definition
        json_return.append(
            {"type": primitive, "subsubtypes": subsubtypes, "description": description}
        )

    return json_return
