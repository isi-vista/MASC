default:
	@echo "an explicit target is required"

SHELL=/usr/bin/env bash

PYTHON_FILES=*.py common/*.py flask_backend/*.py gpt2_component/*.py scripts/*.py

export PATH := venv/bin:$(PATH)
export PYTHONPATH := ..

test:
	python -m unittest

lint:
	pylint $(PYTHON_FILES)

docstyle:
	pydocstyle --convention=google $(PYTHON_FILES)

mypy:
	mypy $(PYTHON_FILES)

flake8:
	flake8 $(PYTHON_FILES)

SORT=LC_ALL=C sort --ignore-case --key=1,1 --key=3V --field-separator="="

reqs-fix:
	$(SORT) --output=requirements.txt requirements.txt
	$(SORT) --output=requirements-dev.txt requirements-dev.txt

reqs-check:
	$(SORT) --check requirements.txt
	$(SORT) --check requirements-dev.txt

reqs-freeze:
	pip freeze >requirements-lock.txt

black-fix:
	isort $(PYTHON_FILES)
	black --config pyproject.toml $(PYTHON_FILES)

black-check:
	isort --check $(PYTHON_FILES)
	black --config pyproject.toml --check $(PYTHON_FILES)

check: reqs-check black-check flake8 mypy lint docstyle test

precommit: reqs-fix reqs-freeze black-fix check

update:
	# Limiting pip version to allow old resolver because new resolver can't upgrade kairos-yaml
	# This will be no longer needed once https://github.com/pypa/pip/issues/5780 is resolved
	pip install --upgrade pip==20.2.4 setuptools==59.6.0 wheel==0.37.0
	pip install --upgrade -r requirements-lock.txt

install:
	bash setup.sh
