.PHONY: install_python
install_python:
	sudo apt-get install python3.11 python3.11-venv
	rm -r venv || true
	python3.11 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

.PHONY: test
test:
	venv/bin/python3 -m pytest tests/

.PHONY: check
check:
	venv/bin/python3 -m flake8 --max-line-length 120 src/

	venv/bin/python3 -m mypy --install-types --non-interactive || true
	venv/bin/python3 -m mypy --ignore-missing-imports --explicit-package-bases --check-untyped-defs src/

.PHONY: format
format:
	venv/bin/python3 -m black -t py311 -l 120 src/
	venv/bin/python3 -m isort -l 120 src/
