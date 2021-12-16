"""Paths to common directories and files."""

from pathlib import Path

TOP_LEVEL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TOP_LEVEL_DIR / "data"

EF_REQUESTS_DIR = DATA_DIR / "requests"
EF_RESPONSES_DIR = DATA_DIR / "responses"
KGTK_CACHE = DATA_DIR / "kgtk_cache"
KGTK_EVENT_CACHE = KGTK_CACHE / "events"
KGTK_REFVAR_CACHE = KGTK_CACHE / "refvars"
EVENT_REC_DIR = DATA_DIR / "gpt2_recommendations"
LOG_DIR = DATA_DIR / "logs"
SCHEMA_DIR = DATA_DIR / "submitted_schemas"

dirs = [
    EF_REQUESTS_DIR,
    EF_RESPONSES_DIR,
    EVENT_REC_DIR,
    KGTK_EVENT_CACHE,
    KGTK_REFVAR_CACHE,
    LOG_DIR,
    SCHEMA_DIR,
]
for directory in dirs:
    directory.mkdir(parents=True, exist_ok=True)

STATUS_FILE = DATA_DIR / "status"

DOTENV_PATH = TOP_LEVEL_DIR / ".env"
