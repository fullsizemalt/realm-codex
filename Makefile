.PHONY: weave docs serve

weave:
	python3 scripts/apply_realm_config.py

docs:
	pip install mkdocs-material pyyaml
	mkdocs build

serve:
	pip install mkdocs-material pyyaml
	mkdocs serve -a 0.0.0.0:8000
