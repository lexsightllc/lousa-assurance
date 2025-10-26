# SPDX-License-Identifier: MPL-2.0
SHELL := /bin/bash
ROOT_DIR := $(realpath .)
ARGS ?=
INCREMENT ?= patch
GROUP ?= all

.PHONY: bootstrap dev lint fmt typecheck test e2e coverage build package release update-deps security-scan sbom gen-docs migrate clean check

bootstrap:
	$(ROOT_DIR)/scripts/bootstrap $(ARGS)

dev:
	$(ROOT_DIR)/scripts/dev $(ARGS)

lint:
	$(ROOT_DIR)/scripts/lint $(ARGS)

fmt:
	$(ROOT_DIR)/scripts/fmt $(ARGS)

typecheck:
	$(ROOT_DIR)/scripts/typecheck $(ARGS)

test:
	$(ROOT_DIR)/scripts/test $(ARGS)

e2e:
	$(ROOT_DIR)/scripts/e2e $(ARGS)

coverage:
	$(ROOT_DIR)/scripts/coverage $(ARGS)

build:
	$(ROOT_DIR)/scripts/build $(ARGS)

package:
	$(ROOT_DIR)/scripts/package $(ARGS)

release:
	$(ROOT_DIR)/scripts/release $(INCREMENT) $(ARGS)

update-deps:
	$(ROOT_DIR)/scripts/update-deps $(GROUP)

security-scan:
	$(ROOT_DIR)/scripts/security-scan $(ARGS)

sbom:
	$(ROOT_DIR)/scripts/sbom $(ARGS)

gen-docs:
	$(ROOT_DIR)/scripts/gen-docs $(ARGS)

migrate:
	$(ROOT_DIR)/scripts/migrate $(ARGS)

clean:
	$(ROOT_DIR)/scripts/clean $(ARGS)

check:
	$(ROOT_DIR)/scripts/check $(ARGS)
