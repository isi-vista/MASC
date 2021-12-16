"""Module for main Flask application."""

from http import HTTPStatus
import json
import logging
import os
from pathlib import Path
from typing import Any, Tuple
import urllib

from flask import Flask, abort, jsonify, request
from flask_cors import CORS
from pyinflect import getInflection
import requests
from requests import RequestException
from sdf.ontology import ontology
import spacy
import yaml

from pycurator.common.config import settings
from pycurator.common.logger import return_logger
from pycurator.common.paths import (
    EVENT_REC_DIR,
    KGTK_EVENT_CACHE,
    KGTK_REFVAR_CACHE,
    LOG_DIR,
    SCHEMA_DIR,
)
from pycurator.flask_backend import make_yaml
from pycurator.flask_backend.event_prediction import init_embeddings, init_ss_model, request_top_n
from pycurator.flask_backend.utils import consistent_refvars, contains_cycle, get_verb_lemma
from pycurator.flask_backend.wikidata_linking import (
    filter_duplicate_candidates,
    get_request_kgtk,
    wikidata_topk,
)
from pycurator.gpt2_component.filter import DefaultCriteria
from pycurator.gpt2_component.gpt2 import convert_sequence_to_text

PARENT_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

nlp = spacy.load("en_core_web_md")

logger = return_logger(LOG_DIR / Path("app.log"))

# Resources initialization for sentence similarity model
SS_MODEL = init_ss_model()
DEFINITION_EMBEDDINGS, TEMPLATE_EMBEDDINGS = init_embeddings(SS_MODEL)


@app.route("/")
def index() -> str:
    """Root page of Flask API.

    Returns:
        A test message.
    """
    return "What I think a REST API is supposed to be in flask (probably wrong)!"


@app.route("/api/get_slots", methods=["GET"])
def get_slots() -> Any:
    """Gets slots and their type constraints, for a given primitive subtype.

    Returns:
        A JSON response.
    """
    if not request.args:
        abort(HTTPStatus.BAD_REQUEST)
    event_primitive = request.args.get("event_primitive")
    primitive = ontology.get_default_event(event_primitive)
    event_args = ontology.events[primitive].args
    slots = list(event_args)
    constraints = [sorted(arg.constraints) for arg in event_args.values()]
    return {"slots": slots, "constraints": constraints}


@app.route("/api/get_all_primitives", methods=["GET"])
def get_all_primitives() -> Any:
    """Gets all primitive subtypes, along with their subsubtypes and default description.

    Returns:
        A JSON response.
    """
    primitives = []
    default_subtypes = sorted(set((e.type, e.subtype) for e in ontology.events.values()))
    for event_type, subtype in default_subtypes:
        type_subtype = f"{event_type}.{subtype}"
        primitives.append(
            {
                "type": type_subtype,
                "subsubtypes": ontology.get_event_subcats(event_type, subtype),
                "description": ontology.events[ontology.get_default_event(type_subtype)].definition,
            }
        )
    return {"primitives": primitives}


@app.route("/api/get_top3", methods=["GET"])
def get_top3() -> Any:
    """Gets top 3 primitive subtypes, given an English phrase.

    This currently relies on a sentence similarity model.

    Returns:
        A JSON response.
    """
    if not request.args:
        abort(HTTPStatus.BAD_REQUEST)

    description: str = request.args.get("event_description", default="")
    if not description:
        abort(HTTPStatus.BAD_REQUEST)

    json_return = request_top_n(
        description,
        n=3,
        ss_model=SS_MODEL,
        definition_embeddings=DEFINITION_EMBEDDINGS,
        template_embeddings=TEMPLATE_EMBEDDINGS,
    )

    return jsonify(json_return)


@app.route("/api/save_schema", methods=["POST"])
def save_schema() -> Tuple[Any, int]:
    """Creates a schema from collected information.

    Returns:
        A JSON response of the schema filename and the schema itself. If the provided schema
        contains a cycle, an error message is returned instead.
    """
    if not request.json:
        abort(HTTPStatus.BAD_REQUEST)
    schema_id = request.json["schema_id"]
    schema_name = request.json["schema_name"]
    schema_dscpt = request.json["schema_dscpt"]
    events = request.json["events"]
    for event in events:
        if "args" in event and event["args"]:
            for arg in event["args"]:
                if "reference" in arg and arg["reference"] is None:
                    del arg["reference"]
    links = request.json["links"]
    tracking = request.json["tracking"]

    if contains_cycle(events, links):
        json_return = {"fname": "err", "output": "cycle in graph"}
        return json_return, HTTPStatus.BAD_REQUEST
    if not consistent_refvars(events):
        json_return = {"fname": "err", "output": "refvar constraints not consistent"}
        return json_return, HTTPStatus.BAD_REQUEST

    yaml_file = make_yaml.save_schema(
        make_yaml.create_schema(
            events=events,
            links=links,
            tracking=tracking,
            schema_id=schema_id,
            schema_name=schema_name,
            schema_dscpt=schema_dscpt,
        ),
        output_directory=SCHEMA_DIR,
    )

    yaml_output = yaml_file.read_text()
    json_return = {"fname": yaml_file.stem, "output": yaml_output}
    return json_return, HTTPStatus.CREATED


@app.route("/api/get_saved_schemas", methods=["GET"])
def get_saved_schemas() -> Any:
    """Lists file and display names of all saved schemas.

    File extensions are stripped, and the names are sorted.

    Returns:
        A JSON response.
    """
    schema_paths = sorted(p for p in SCHEMA_DIR.glob("*.yaml"))
    display_files = []
    for schema_path in schema_paths:
        with open(schema_path) as f:
            content = yaml.safe_load(f)[0]
        schema_id = content["schema_id"]
        schema_name = content["schema_name"]
        schema_dscpt = content["schema_dscpt"]
        timestamp = content["schema_version"].split("-")
        time_stamp = "-".join(timestamp[:3]) + ", " + ":".join(timestamp[3:6])

        augmentation_flag = os.path.exists(EVENT_REC_DIR / f"{schema_path.stem}.json")
        display_files.append(
            {
                "file": schema_path.stem,
                "schema_id": schema_id,
                "schema_name": schema_name,
                "schema_dscpt": schema_dscpt,
                "timestamp": time_stamp,
                "augmentation_flag": augmentation_flag,
            }
        )
    return {"schemaFiles": display_files}


@app.route("/api/get_schema", methods=["GET"])
def get_schema() -> Any:
    """Loads a saved schema and event recommendations (if any) from two files.

    Returns:
        A JSON response.
    """
    if not request.args:
        abort(HTTPStatus.BAD_REQUEST)
    requested_file = request.args.get("schemaFile")
    with (SCHEMA_DIR / f"{requested_file}.yaml").open() as y_file:
        yaml_output = yaml.safe_load(y_file)[0]
    events = []
    for event_index, step in enumerate(yaml_output["steps"], start=1):
        if "required" not in step:
            step["required"] = True
        event = {
            "event_primitive": step["primitive"],
            "event_text": step["id"],
            "id_num": event_index,
            "args": step["slots"],
            "required": step["required"],
            "comment": step.get("comment", None),
            "reference": step.get("reference", None),
        }
        events.append(event)
    order = []
    for order_pair in yaml_output["order"]:
        order.append([order_pair["before"], order_pair["after"]])

    rec_events = []
    try:
        with (EVENT_REC_DIR / f"{requested_file}.json").open() as rec_file:
            recommendations = json.load(rec_file)
            for key in recommendations["events"].keys():
                rec_list = [key]
                rec_list.extend(recommendations["events"][key])
                rec_events.append(rec_list)
    except IOError:
        print(f"Recommendations not found for {requested_file}")

    yaml_response = {
        "schema_id": yaml_output["schema_id"],
        "schema_name": yaml_output["schema_name"],
        "schema_dscpt": yaml_output["schema_dscpt"],
        "events": events,
        "order": order,
        "rec_events": rec_events,
    }
    return yaml_response


@app.route("/api/disambiguate_verb_kgtk", methods=["POST"])
def disambiguate_verb_kgtk() -> Any:
    """Disambiguates verbs from event description and return candidate qnodes.

    Returns:
        A JSON response.
    """
    if not request.json:
        abort(HTTPStatus.BAD_REQUEST)
    event_description = request.json["event_description"]
    cleaned_description = event_description.replace("/", " ").replace("_", " ")
    event_verb = get_verb_lemma(nlp, cleaned_description)
    cached_file = KGTK_EVENT_CACHE / f"{event_verb}.json"
    if cached_file.is_file():
        with open(cached_file) as f:
            return json.load(f)
    kgtk_json = get_request_kgtk(event_verb)
    event_verb_participle = getInflection(event_verb, tag="VBG")
    if event_verb_participle and event_verb_participle != event_verb:
        kgtk_json += get_request_kgtk(event_verb_participle[0])
    if not kgtk_json:
        return {"event_verb": kgtk_json, "options": []}
    unique_candidates = filter_duplicate_candidates(kgtk_json)
    options = []
    top3 = wikidata_topk(SS_MODEL, cleaned_description, unique_candidates, k=3)
    for candidate in top3:
        option = {
            "qnode": candidate["qnode"],
            "rawName": candidate["label"][0],
            "definition": candidate["description"][0],
        }
        if option not in options:
            options.append(option)
    response = {"event_verb": event_verb, "options": options}
    with open(cached_file, "w") as f:
        json.dump(response, f)
    return response


@app.route("/api/disambiguate_refvar_kgtk", methods=["POST"])
def disambiguate_refvar_kgtk() -> Any:
    """Disambiguates refvar with KGTK webserver API.

    Returns:
        A JSON response.
    """
    if not request.json:
        abort(HTTPStatus.BAD_REQUEST)
    refvar = request.json["refvar"].lower()
    cleaned_refvar = refvar.replace("/", " ").replace("_", " ")
    cached_file = KGTK_REFVAR_CACHE / f"{cleaned_refvar}.json"
    if cached_file.is_file():
        with open(cached_file) as f:
            return json.load(f)
    kgtk_json = get_request_kgtk(cleaned_refvar)
    if not kgtk_json:
        return {"event_verb": kgtk_json, "options": []}
    if len(cleaned_refvar.split()) < 2:
        lemma_refvar = nlp(cleaned_refvar)[0].lemma_
        if lemma_refvar != cleaned_refvar:
            kgtk_json += get_request_kgtk(lemma_refvar)
    unique_candidates = filter_duplicate_candidates(kgtk_json)
    options = []
    top3 = wikidata_topk(SS_MODEL, refvar, unique_candidates, k=3)
    for candidate in top3:
        # description can be empty sometimes on less popular qnodes
        definition = "" if len(candidate["description"]) < 1 else candidate["description"][0]
        option = {
            "qnode": candidate["qnode"],
            "rawName": candidate["label"][0],
            "definition": definition,
        }
        if option not in options:
            options.append(option)
    response = {"refvar": refvar, "options": options}
    with open(cached_file, "w") as f:
        json.dump(response, f)
    return response


@app.route("/api/get_gpt2_suggestions", methods=["GET"])
def get_gpt2_suggestions() -> Any:
    """Gets suggestions from GPT-2 server.

    Returns:
        A JSON response.
    """
    if not request.args:
        logging.error("Request missing URL parameters")
        abort(HTTPStatus.BAD_REQUEST)
    schema_name = request.args.get("schema_name")
    schema_dscpt = request.args.get("schema_dscpt")
    events = request.args.getlist("events")
    if not schema_name or not schema_dscpt:
        logging.error("Request missing name or description")
        abort(HTTPStatus.BAD_REQUEST)

    text = convert_sequence_to_text(
        schema_name=schema_name,
        schema_desc=schema_dscpt,
        sequence=events,
    )
    text_formatted = urllib.parse.quote(text)

    request_url = (
        f"http://{settings.gpt2_server}.example.org:5001/api/get_prediction?text={text_formatted}"
    )
    try:
        request_response = requests.get(request_url, timeout=30)
    except RequestException as ex:
        logger.error(ex)
        abort(HTTPStatus.INTERNAL_SERVER_ERROR)
    if request_response.status_code != HTTPStatus.OK:
        logger.error("GPT-2 server returned status code %d", request_response.status_code)
        abort(HTTPStatus.INTERNAL_SERVER_ERROR)
    predictions = request_response.json()["predictions"]

    gpt2_filter = DefaultCriteria(existing_events=set(events), keep=5)
    suggestions = sorted(gpt2_filter.meet_criteria(predictions))

    response = {"suggestions": suggestions}
    return response


if __name__ == "__main__":
    app.run(debug=True, load_dotenv=False)
else:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    logger.level = gunicorn_logger.level
