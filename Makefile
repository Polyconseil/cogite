#
# Makefile (for developers)
#

.PHONY: coverage
coverage:
	pytest --cov cogite

.PHONY: coverage-html
coverage-html:
	pytest --cov cogite --cov-report html
	python -c "import webbrowser; webbrowser.open('htmlcov/index.html')"

.PHONY: test
test:
	pytest

.PHONY: docs
docs:
	SPHINXOPTS="-W -n" $(MAKE) -C docs html

.PHONY: quality
quality:
	isort --check-only --diff .
	pylint --reports=no --score=no setup.py src/cogite tests
	mypy src/cogite
	check-branches
	check-fixmes
	check-manifest
	python setup.py sdist >/dev/null 2>&1 && twine check dist/*

.PHONY: clean
clean:
	rm -rf .coverage
	find . -name "*.pyc" | xargs rm -f
	find . -name "__pycache__" | xargs rm -rf
	$(MAKE) -C docs clean
