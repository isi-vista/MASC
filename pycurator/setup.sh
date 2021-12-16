#!/usr/bin/env bash

set -euo pipefail

# Set up venv
if [[ ! -d venv/ ]]; then
  python -m venv --copies venv
  source venv/bin/activate
  pip install --upgrade pip==20.2.4 setuptools==59.6.0 wheel==0.37.0
  pip install -r requirements-lock.txt
  python -c 'import nltk; nltk.download("punkt", download_dir="venv/nltk_data")'
fi

# Download model weights
if [[ ! -d flask_backend/sent_model/pretrained_model/ ]]; then
  python -c 'from pycurator.flask_backend.event_prediction import init_ss_model; init_ss_model()'
fi

# Download GPT-2 model cache weights
if [[ ! -d gpt2_component/.model_cache/ ]]; then
  source venv/bin/activate
  cd gpt2_component/
  PYTHONPATH=../../ python -m pycurator.gpt2_component.init_cache
  cd -
fi

# Download bad words list
if [[ ! -f gpt2_component/bad_words_en.txt ]]; then
  cd gpt2_component/
  wget --output-document - https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en |
    grep -v " " >bad_words_en.txt # Filtering with individual words is much easier
  cd -
fi
