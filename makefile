.PHONY:	init install install-dev

init:
	pip install -r	requirements.txt

install:
	pip install .

install-dev:
	pip install -e .
