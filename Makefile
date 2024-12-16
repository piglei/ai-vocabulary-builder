# Run formatters and linters
.PONY: lint
lint:
	isort --settings-path=./pyproject.toml --recursive .
	black --config=./pyproject.toml .
	flake8 .
	mypy ./voc_builder ./tests

.PONY: build-frontend
build-frontend:
	rm -rf voc_builder/notepad/dist
	cd voc_frontend && VITE_AIVOC_API_ENDPOINT='' npm run build-only && mv dist ../voc_builder/notepad