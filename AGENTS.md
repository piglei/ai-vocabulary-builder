## Purpose

* These brief instructions help LLM agents navigate working in the ai-vocabulary-builder repo.
* **Humans** are always responsible for changes being proposed and must pre-review all agentic work before turning it into a PR.

## Context

You are in the ai-vocabulary-builder repo, helping implement features, fix bugs, and refactor existing code.

Use the `gh` tool to get information about an issue or PR in the repo.

Source files in this repo can be very long.  Check their size to consider if
you really need to read the entire thing.

If tools such as `rg` (ripgrep), `gh`, `jq`, or `prek` are not found, ask
the user to install them. ALWAYS prefer using `rg` rather than `find` or `grep`.

## Source code

The repo consists of two parts: voc_builder(the backend) and voc_frontend(the frontend).

### voc_builder

* voc_builder is a REST API service implemented in Python and FastAPI.
* The source code is in the `voc_builder/` directory.
* Unit tests for this module are in the `tests/` directory at the root of the repository.
* We use poetry to manage the service's virtual environment, so make sure to use `poetry run {command}` to execute any Python commands, such as running unit tests(`poetry run pytest tests/`).

### voc_frontend

* voc_frontend is implemented in vue.js.
* The source code is in the `voc_frontend/` directory.

## Coding style

* For Python, follow PEP-8. For vue.js, follow eslint rules in the `voc_frontend/`.
* We use ruff to auto-format our file, the configuration for ruff can be found in `pyproject.toml`.
* Be consistent with existing nearby code style unless asked to do otherwise.
* NEVER leave trailing whitespace on any line.
* ALWAYS preserve the newline at the end of files.
* ALWAYS add Python type annotations to Python code.

### Running our tests

* ALWAYS use sub-agents when running tests
* ALWAYS use `pytest`. The tests are `pytest` based.

### Common workflows

* After editing Python code, format the code: `ruff format`
* After editing Python code, checking the code: `ruff check`
* After editing Python code, run tests: `pytest tests/`
