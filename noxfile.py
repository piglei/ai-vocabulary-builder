import nox

ALL_PYTHON = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(reuse_venv=True)
@nox.parametrize("python", ALL_PYTHON)
def tests(session):
    session.run("python", "-m", "ensurepip", "--upgrade")
    session.install("pytest")
    session.install("pytest-asyncio")
    session.install("-e", ".[all]")
    session.run("pytest", "tests/", *session.posargs)


@nox.session(python="3.9", reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run pre-commit linting."""
    session.install("prek")
    session.run(
        "prek",
        "run",
        "--all-files",
        "--show-diff-on-failure",
        "--hook-stage=manual",
        *session.posargs,
    )
