default:
	@echo "an explicit target is required"

SHELL=/usr/bin/env bash

BASH_FILES=$(shell find .. -name '*.sh' | grep -v '/node_modules/' | grep -v '/venv/' | sort | tr '\n' ' ')
PRETTIER_FILES=. ../*.md ../pycurator/flask_backend/sent_model/templates.json

shellcheck:
	node_modules/.bin/shellcheck --exclude=SC1091 --shell=bash $(BASH_FILES)

stylelint:
	npx stylelint "src/**/*.css"

lint:
	npx ng lint

prettier-fix:
	npx prettier --write $(PRETTIER_FILES)

prettier-check:
	npx prettier --check $(PRETTIER_FILES)

check: prettier-check lint stylelint shellcheck

precommit: prettier-fix check

update:
	npm install

install:
	npm install
