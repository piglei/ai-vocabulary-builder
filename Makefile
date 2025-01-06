.PHONY: help lint build-frontend build start stop update

COMPOSE_FILE = infra/docker/docker-compose.yml

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  make lint              - Run formatters and linters"
	@echo "  make build-frontent    - Build frontend"
	@echo "  make build             - Build Docker image"
	@echo "  make start             - Start container"
	@echo "  make stop              - Stop container"
	@echo "  make update            - Update to latest version"

lint:
	isort --settings-path=./pyproject.toml --recursive .
	black --config=./pyproject.toml .
	flake8 .
	mypy ./voc_builder ./tests

build-frontend:
	rm -rf voc_builder/notepad/dist
	cd voc_frontend && VITE_AIVOC_API_ENDPOINT='' npm run build-only && mv dist ../voc_builder/notepad

build:
	docker-compose -f $(COMPOSE_FILE) build --no-cache

start:
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "Application available at http://127.0.0.1:16093"

stop:
	docker-compose -f $(COMPOSE_FILE) down
	@echo "Application stopped"

update:
	@echo "Updating to latest version..."
	@make stop
	@make build
	@make start
	@echo "Updated to latest version"
