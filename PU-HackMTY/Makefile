PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
SEED ?= 7
override SEED := $(value SEED)
export SEED

.PHONY: test lint gen score

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q

gen:
	@case "$$SEED" in \
		''|*[!0-9]*) echo "SEED must be a non-negative integer" >&2; exit 1 ;; \
	esac
	@if [ "$$SEED" = "42" ]; then \
		echo "company_42 is frozen; choose another SEED" >&2; \
		exit 1; \
	fi
	$(PYTHON) -m data_estate.generate --seed "$$SEED" --out "data_estate/out/company_$$SEED"

score:
	$(PYTHON) -m data_estate.score data_estate/out/company_42 data_estate/out/example_case_file_for_seed42.json
