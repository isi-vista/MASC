default:
	@echo "an explicit target is required"

SHELL=/usr/bin/env bash

check:
	cd angular-frontend && \
	make check && \
	cd ../kairos-yaml && \
	make check && \
	cd ../pycurator && \
	make check

precommit:
	cd angular-frontend && \
	make precommit && \
	cd ../kairos-yaml && \
	make precommit && \
	cd ../pycurator && \
	make precommit

update:
	cd angular-frontend && \
	make update && \
	cd ../pycurator && \
	make update

install:
	cd angular-frontend && \
	make install && \
	cd ../pycurator && \
	make install
