PYTHON=venv/bin/python3
PYINSTALLER=venv/bin/pyinstaller
EXE=/usr/local/bin/birthday-reminder
DIRS=birthday_reminder tests

.PHONY: install_python
install_python:
	sudo apt-get install python3.11 python3.11-venv python3.11-dev
	rm -r venv || true
	python3.11 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -e .

.PHONY: install
install:
	mkdir -p auth
	chmod 700 auth
	cp -n birthday_reminder/configs/default_config.yaml main_config.yaml
	cp -n birthday_reminder/assets/example_birthdays.txt Birthdays.txt
	echo "#!/bin/sh\n$(realpath .)/venv/bin/python -m birthday_reminder \"\$$@\"" | sudo tee ${EXE}
	sudo chmod a+x ${EXE}

.PHONY: uninstall
uninstall:
	sudo rm ${EXE} || true
	rm -r auth || true
	rm -r venv || true


.PHONY: build_windows
build_windows:
	if (Test-Path dist) { Remove-Item -Recurse -Force dist }
	${PYINSTALLER} birthday_reminder/__main__.py -n birthday-reminder -y --clean --onefile --distpath dist/birthday-reminder
	md dist/birthday-reminder/auth -Force
	cp birthday_reminder/configs/default_config.yaml dist/birthday-reminder/main_config.yaml
	cp birthday_reminder/assets/example_birthdays.txt dist/birthday-reminder/Birthdays.txt

	md dist/birthday-reminder/release_info -Force
	cp LICENCE dist/birthday-reminder/release_info/LICENCE
	cp VERSION dist/birthday-reminder/release_info/VERSION
	cp README.md dist/birthday-reminder/release_info/README.md

	Compress-Archive -Path dist/birthday-reminder -DestinationPath dist/windows.zip


.PHONY: build_linux_macos
build_linux_macos:
	rm -r dist || true
	${PYINSTALLER} birthday_reminder/__main__.py -n birthday-reminder -y --clean --onefile --distpath dist/birthday-reminder
	mkdir -p dist/birthday-reminder/auth
	chmod 700 dist/birthday-reminder/auth
	cp birthday_reminder/configs/default_config.yaml dist/birthday-reminder/main_config.yaml
	cp birthday_reminder/assets/example_birthdays.txt dist/birthday-reminder/Birthdays.txt

	mkdir -p dist/birthday-reminder/release_info
	cp LICENCE dist/birthday-reminder/release_info/LICENCE
	cp VERSION dist/birthday-reminder/release_info/VERSION
	cp README.md dist/birthday-reminder/release_info/README.md

	cd dist && tar czvf linux_macos.tar.gz birthday-reminder  # tar preserves permissions


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