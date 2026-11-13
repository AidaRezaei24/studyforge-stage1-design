.PHONY: test check run
PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -v

check: test
	$(PYTHON) -m compileall -q studyforge tests
	$(PYTHON) scripts/check_submission.py

run:
	$(PYTHON) -m studyforge serve
