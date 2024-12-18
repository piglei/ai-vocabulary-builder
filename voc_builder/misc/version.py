"""Many functions of this module are copied from https://github.com/wimglenn/johnnydep"""

import logging
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import unearth
from packaging import version
from packaging.requirements import Requirement
from packaging.tags import parse_tag
from packaging.version import Version

from voc_builder import __version__
from voc_builder.infras.store import get_internal_state_store

logger = logging.getLogger()

DEFAULT_INDEX = "https://pypi.org/simple/"

PACKAGE_NAME = "ai-vocabulary-builder"

# Perform version checking only after 8 hours have passed since the last action.
VERSION_CHECKING_INTERVAL = 3600 * 8


def get_new_version() -> Optional[str]:
    """Check if there's a new versions available."""
    current = __version__
    state_store = get_internal_state_store()
    state = state_store.get_internal_state()
    if time.time() - state.last_ver_checking_ts < VERSION_CHECKING_INTERVAL:
        latest = state.server_latest_version
        if not latest:
            return None
        if version.parse(current) < version.parse(latest):
            return latest
        return None

    state.last_ver_checking_ts = time.time()
    state_store.set_internal_state(state)

    try:
        latest = JohnnyDist(
            PACKAGE_NAME, index_urls=(DEFAULT_INDEX,)
        ).versions_available()[-1]
    finally:
        # Alway set last version checking time
        state_store.set_internal_state(state)

    # Save the latest version to the state
    state.server_latest_version = latest
    state_store.set_internal_state(state)

    assert latest
    if version.parse(current) < version.parse(latest):
        return latest
    return None


class JohnnyDist:
    def __init__(self, req_string, index_urls=(), env=None):
        if isinstance(req_string, Path):
            req_string = str(req_string)
        self._index_urls = index_urls
        self._env = env
        self.req = Requirement(req_string)

    def versions_available(self):
        versions = _get_versions(self.req, self._index_urls, self._env)
        return versions


def _get_package_finder(index_urls, env):
    trusted_hosts = ()
    for index_url in index_urls:
        host = urlparse(index_url).hostname
        if host != "pypi.org":
            trusted_hosts += (host,)  # type: ignore
    target_python = None
    if env is not None:
        envd = dict(env)
        target_python = unearth.TargetPython(
            py_ver=envd["py_ver"],
            impl=envd["impl"],
        )
        valid_tags: List = []
        for tag in envd["supported_tags"].split(","):
            valid_tags.extend(parse_tag(tag))
        target_python._valid_tags = valid_tags
    package_finder = unearth.PackageFinder(
        index_urls=index_urls,
        target_python=target_python,
        trusted_hosts=trusted_hosts,
    )
    return package_finder


def _get_packages(project_name: str, index_urls: tuple, env: tuple):
    finder = _get_package_finder(index_urls, env)
    seq = finder.find_all_packages(project_name, allow_yanked=True)
    result = list(seq)
    return result


def _get_versions(req: Requirement, index_urls: tuple, env: tuple):
    packages = _get_packages(req.name, index_urls, env)
    versions = {p.version for p in packages}
    version_list = sorted(versions, key=Version)
    return version_list
