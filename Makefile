EXE=/usr/local/bin/birthday-reminder

.PHONY: install_python
install_python:
	sudo apt-get install python3.11 python3.11-venv
	rm -r venv || true
	python3.11 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -e .

.PHONY: install
install:
	make install_python
	echo "#!/bin/bash\n$(realpath .)/venv/bin/python -m birthday_reminder \"\$$@\"" | sudo tee ${EXE}
	sudo chmod a+x ${EXE}

.PHONY: uninstall
uninstall:
	sudo rm ${EXE} || true
	rm -r venv || true


.PHONY: tests
tests:
	venv/bin/python3 -m pytest tests/

.PHONY: check
check:
	venv/bin/python3 -m flake8 --max-line-length 120 birthday_reminder/ tests/

	venv/bin/python3 -m mypy --install-types --non-interactive || true
	venv/bin/python3 -m mypy --ignore-missing-imports --explicit-package-bases --check-untyped-defs birthday_reminder/ tests/

.PHONY: format
format:
	venv/bin/python3 -m black -t py311 -l 120 birthday_reminder/ tests/
	venv/bin/python3 -m isort -l 120 birthday_reminder/ tests/

.PHONY: ci
ci:
	make format
	make check
	make tests
