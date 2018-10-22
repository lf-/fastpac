import pytest

import fastpac.download as download
from fastpac.search import PackageInfo


def test_download_assemble_package_url():
    assert download.assemble_package_url(
            PackageInfo(**{'mirror': '', 'name': '', 'size': 0, "repo": "core", "filename": "package.tar", "sha256": ""}), "https://a/", 'x86_64') == "https://a/core/os/x86_64/package.tar"
    assert download.assemble_package_url(
            PackageInfo(**{'mirror': '', 'name': '', 'size': 0, "repo": "extra", "filename": "package.tar.gz", "sha256": ""}), "https://b", 'armv7h') == "https://b/extra/os/armv7h/package.tar.gz"
