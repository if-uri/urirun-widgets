# Part of the ifURI solution.
PY ?= python3
HOST ?= ../urirun/adapters/python/urirun/host

.PHONY: test single-source build check install

install: ## editable install with test extras
	$(PY) -m pip install -e ".[test]"

test: ## pytest (render parity + render single-source gate)
	$(PY) -m pytest tests/ -q

single-source: ## host must not vendor widget-view renderers (consume the bundle, not copy it)
	$(PY) ci/check_render_single_source.py $(HOST) --strict

build: ## sdist + wheel + twine metadata check
	$(PY) -m build && $(PY) -m twine check dist/*

check: test single-source build ## tests + render gate + publish-readiness
