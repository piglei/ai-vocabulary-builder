# Run formatters and linters
lint:
	isort --settings-path=./pyproject.toml --recursive .
	black --config=./pyproject.toml .
	flake8 .
	mypy ./voc_builder ./tests
