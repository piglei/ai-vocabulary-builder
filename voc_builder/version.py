"""Many functions of this module are copied from https://github.com/wimglenn/johnnydep
"""
import logging
import sys
import time
from subprocess import STDOUT, CalledProcessError, check_output
from urllib.parse import urlparse

import pkg_resources
from packaging import version
from rich.console import Console

from voc_builder import __version__
from voc_builder.store import get_internal_state_store

log = logging.getLogger(__name__)


DEFAULT_INDEX = "https://pypi.org/simple/"

PACKAGE_NAME = 'ai-vocabulary-builder'

# Perform version checking only after 24 hours have passed since the last action.
VERSION_CHECKING_INTERVAL = 3600 * 24


def check_for_new_versions(console: Console):
    """Check if there's a new versions available, will output messages to the given
    console object.
    """
    state_store = get_internal_state_store()
    last_ver_checking_ts = state_store.get_last_ver_checking_ts()
    if last_ver_checking_ts and time.time() - last_ver_checking_ts < VERSION_CHECKING_INTERVAL:
        return None

    try:
        current = __version__
        latest = get_versions(PACKAGE_NAME)[-1]
    finally:
        # Alway set last version checking time
        state_store.set_last_ver_checking_ts()

    if version.parse(current) < version.parse(latest):
        console.print(
            rf'\[notice] A new release of "AI vocabulary builder" is available, {current}(current) -> {latest}(latest)',  # noqa: E501
            style='chartreuse2',
        )
        console.print(
            r'\[notice] To update, run "pip install --upgrade ai-vocabulary-builder"',
            style='chartreuse2',
        )


def _get_pip_version():
    # try to get pip version without actually importing pip
    # setuptools gets upset if you import pip before importing setuptools..
    try:
        import importlib.metadata  # Python 3.8+

        return importlib.metadata.version("pip")
    except Exception:
        pass
    import pip

    return pip.__version__


def _get_wheel_args(index_url, env, extra_index_url):
    args = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "-vvv",  # --verbose x3
        "--no-deps",
        "--no-cache-dir",
        "--disable-pip-version-check",
    ]
    if index_url is not None:
        args += ["--index-url", index_url]
        if index_url != DEFAULT_INDEX:
            hostname = urlparse(index_url).hostname
            if hostname:
                args += ["--trusted-host", hostname]
    if extra_index_url is not None:
        args += [
            "--extra-index-url",
            extra_index_url,
            "--trusted-host",
            urlparse(extra_index_url).hostname,
        ]
    if env is None:
        pip_version = _get_pip_version()
    else:
        pip_version = dict(env)["pip_version"]
        args[0] = dict(env)["python_executable"]
    pip_major, pip_minor = pip_version.split(".")[0:2]
    pip_major = int(pip_major)
    pip_minor = int(pip_minor)
    if pip_major >= 10:
        args.append("--progress-bar=off")
    if (20, 3) <= (pip_major, pip_minor) < (21, 1):
        # See https://github.com/pypa/pip/issues/9139#issuecomment-735443177
        args.append("--use-deprecated=legacy-resolver")
    return args


def get_versions(dist_name, index_url=None, env=None, extra_index_url=None):
    bare_name = pkg_resources.Requirement.parse(dist_name).name  # type: ignore
    log.debug("checking versions available, dist: %s", bare_name)
    args = _get_wheel_args(index_url, env, extra_index_url) + [dist_name + "==showmethemoney"]
    try:
        out = check_output(args, stderr=STDOUT)
    except CalledProcessError as err:
        # expected. we forced this by using a non-existing version number.
        out = getattr(err, "output", b"")
    else:
        log.warning(out)
        raise Exception("Unexpected success:" + " ".join(args))
    out_str = out.decode("utf-8")
    lines = []
    msg = "Could not find a version that satisfies the requirement"
    for line in out_str.splitlines():
        if msg in line:
            lines.append(line)
    try:
        [line] = lines
    except ValueError:
        log.warning("failed to get versions")
        raise
    prefix = "(from versions: "
    start = line.index(prefix) + len(prefix)
    stop = line.rfind(")")
    versions = line[start:stop]
    if versions.lower() == "none":
        return []
    versions = [v.strip() for v in versions.split(",") if v.strip()]
    log.debug("found versions, dist: %s, versions: %s", bare_name, versions)
    return versions
