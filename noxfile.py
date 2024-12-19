import nox

ALL_PYTHON = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(reuse_venv=True)
@nox.parametrize("python", ALL_PYTHON)
def tests(session):
    session.run("python", "-m", "ensurepip", "--upgrade")
    session.install("pytest")
    session.install("-e", ".[all]")
    session.run("pytest", "tests/", *session.posargs)


@nox.session(python="3.9", reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run pre-commit linting."""
    session.install("pre-commit")
    session.run(
        "pre-commit",
        "run",
        "--all-files",
        "--show-diff-on-failure",
        "--hook-stage=manual",
        *session.posargs,
    )
