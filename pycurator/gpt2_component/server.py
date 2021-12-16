"""Module for GPT-2 server."""

from http import HTTPStatus
import logging
from pathlib import Path
from typing import Any

from flask import Flask, abort, request
from flask_cors import CORS

from pycurator.common.logger import return_logger
from pycurator.common.paths import LOG_DIR
from pycurator.gpt2_component.gpt2 import MODEL_NAME, get_device, load_gpt2, make_predictions

PARENT_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

logger = return_logger(LOG_DIR / Path("gpt2_server.log"))

# Initialize GPT-2 model
DEVICE = get_device()
TOKENIZER, MODEL = load_gpt2(MODEL_NAME, DEVICE)


@app.route("/api/get_prediction", methods=["GET"])
def get_prediction() -> Any:
    """Gets predictions from GPT-2, given a text string.

    Returns:
        A JSON response.
    """
    if not request.args:
        abort(HTTPStatus.BAD_REQUEST)
    text = request.args.get("text")
    if not text:
        abort(HTTPStatus.BAD_REQUEST)
    logger.info("text: %s", text)

    predictions = make_predictions(
        text=text,
        tokenizer=TOKENIZER,
        gpt2=MODEL,
        device=DEVICE,
        max_output_length=50,
    )
    logger.info("predictions: %s", predictions)

    return {"predictions": predictions}


if __name__ == "__main__":
    app.run(debug=True, load_dotenv=False)
else:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    logger.level = gunicorn_logger.level
