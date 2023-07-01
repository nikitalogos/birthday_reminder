PYTHON=venv/bin/python3
EXE=/usr/local/bin/birthday-reminder
DIRS=birthday_reminder tests

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
	mkdir -p .auth
	chmod 700 .auth
	cp -n birthday_reminder/configs/default_config.yaml main_config.yaml
	cp -n examples/example_birthdays.txt Birthdays.txt
	echo "#!/bin/sh\n$(realpath .)/venv/bin/python -m birthday_reminder \"\$$@\"" | sudo tee ${EXE}
	sudo chmod a+x ${EXE}

.PHONY: uninstall
uninstall:
	sudo rm ${EXE} || true
	rm -r .auth || true
	rm -r venv || true


.PHONY: tests
tests:
	${PYTHON} -m pytest tests/

.PHONY: check
check:
	${PYTHON} -m flake8 --max-line-length 120 ${DIRS}

	${PYTHON} -m mypy --install-types --non-interactive ${DIRS} > /dev/null 2>&1 || true
	${PYTHON} -m mypy --ignore-missing-imports --explicit-package-bases --check-untyped-defs ${DIRS}

.PHONY: format
format:
	${PYTHON} -m black -t py311 -l 120 ${DIRS}
	${PYTHON} -m isort -l 120 ${DIRS}

.PHONY: ci
ci:
	make format
	make check
	make tests

.PHONY: install_git_pre_commit_hook
install_git_pre_commit_hook:
	echo '#!/bin/sh\nmake ci' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

.PHONY: uninstall_git_pre_commit_hook
uninstall_git_pre_commit_hook:
	rm .git/hooks/pre-commit || true