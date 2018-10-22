import argparse
import logging
from threading import Lock
from typing import Any, Dict, List, Set
from pathlib import Path
import runpy
from hashlib import sha256
from os import remove as remove_file

from fastpac.mirror import get_mirrorlist_online, get_mirrorlist_offline
from fastpac.search import find_package, download_repos
from fastpac.util import HybridGenerator, ThreadPoolExecutorStackTraced
from fastpac.download import assemble_package_url, download_file_to_path
from fastpac.picker import *


log = logging.getLogger('fastpac.__main__')


def download_package(name, dest, databases, databases_lock, mirrorpicker, mirrorpicker_lock, arch):
    # find_package returns the filename for the current version and
    # its repo of residence. Both are needed to make the download url
    with databases_lock:
        package_info = find_package(name, databases)

    # find_package will return None if no package is in the database
    if not package_info:
        log.warning('%r could not be found', name)
        return

    filename = package_info.filename
    # If it is already present we skip this package
    file_path = dest / filename
    if file_path.is_file():
        log.info('%r already exists', filename)
        log.debug("file_path %r", file_path)

        # Calculate current file's hash

        # If the sha256 hash is not provided skip
        if not package_info.sha256:
            return

        # Hash from repo
        remote_hash = package_info.sha256

        with open(file_path, mode='rb') as package_file:
            current_hash = sha256(package_file.read()).hexdigest()

        # Hashs match skip package
        log.debug("Remote hash %r", remote_hash)
        log.debug("Local hash  %r", current_hash)
        if remote_hash == current_hash:
            log.info("%r has matching hashs", name)
            return

        log.warning("Local package file %r does not have matching hashs", name)
        remove_file(file_path)
        log.info("Removed local copy of package %r", file_path)

    # Try downloading a package from a mirror until one works
    while True:
        # Picking a mirror to use
        with mirrorpicker_lock:
            mirror = mirrorpicker.next(size=int(package_info.size))

        # Combine the mirror url with info from databases to make a download url
        package_mirror = assemble_package_url(package_info, mirror, arch=arch)

        # Download
        log.info('Downloading %r from %s', filename, package_mirror)
        try:
            download_file_to_path(package_mirror, dest / filename)
        except Exception as e:
            log.exception(e)
            # Go to next mirror

        log.info('Finished downloading %s', package_mirror)
        # Next package
        break


def load_config(path: Path) -> Dict[str, Any]:
    """
    Load a runpy based config from a Path

    Parameters:
    path -- Path object to load the config from
    """
    init_globals = {k: v for (k, v) in globals().items()
                    if k.endswith('Picker') or k.endswith('Generator')
                    or k.startswith('get_mirrorlist')
                    or k == "download_repos"}
    return runpy.run_path(path, init_globals=init_globals)


def make_package_list(path: Path) -> Set[str]:
    """
    Makes the package list from a directory with newline delimited
    files.

    Parameters:
    path -- Path object to directory with package list files
    """
    packages = set()
    for child in path.iterdir():
        with child.open('r') as h:
            packages.update(s.partition(' ')[0] for s in h.readlines())
    return packages


class PathFileType:
    def __init__(self):
        pass

    def __call__(self, string):
        path = Path(string)
        if not path.is_file():
            raise argparse.ArgumentTypeError(f'{string} is not a file')
        return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--config-file', type=PathFileType(),
                   default='/etc/fastpac.conf.py', help='Path to config file')
    p.add_argument('--log-level', default=None, help='Log level')
    return p.parse_args()


def main(args: argparse.Namespace):
    config = load_config(args.config_file)
    if args.log_level:
        logging.getLogger('fastpac').setLevel(args.log_level.upper())
    package_names = make_package_list(Path(config['package_list_dir']))
    package_names = sorted(package_names)

    databases_lock = Lock()
    mirrorpicker_lock = Lock()

    dest = Path(config['download_dir'])

    if not dest.is_dir():
        raise ValueError(f'download_dir {dest} is not a directory')

    with ThreadPoolExecutorStackTraced(max_workers=config['workers']) as pool:
        futures = []
        for package_name in package_names:
            futures.append(pool.submit(
                download_package,
                package_name,
                dest,
                config['databases'],
                databases_lock,
                config['mirrorpicker'],
                mirrorpicker_lock,
                config.get('architecture', 'x86_64')
                ))

        for future in futures:
            future.result()


if __name__ == "__main__":
    try:
        main(parse_args())
    except KeyboardInterrupt:
        log.info("Stopped")
