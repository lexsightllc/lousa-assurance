VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
PYTEST=$(VENV)/bin/pytest

.PHONY: assure venv clean

assure: venv
	@$(PIP) install -e .
	@$(PYTEST) -q
	@echo "ASSURANCE OK — pipeline testado ponta a ponta."

venv:
	@test -d $(VENV) || python -m venv $(VENV)

clean:
	@rm -rf $(VENV) .pytest_cache .coverage
