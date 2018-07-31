"""
All functionality relating to searching package databases
"""
from io import BytesIO
from tarfile import open as TarOpen

from requests import get

from fastpac.database import Repo

def gen_repos(mirrors, repos):
    """
    Return a generator with paths to different repos

    Args:
        mirrors: A list of mirror urls eg: ["https://mirror1.com/", https://mirror2.com"]
        repos: A list of repo names eg: ["core", "extra"]

    Example:
        1. https://mirror1.com/core/os/x86_64/
        2. https://mirror1.com/extra/os/x86_64/
        3. https://mirror2.com/core/os/x86_64/
        4. https://mirror2.com/extra/os/x86_64/
    """
    for mirror in mirrors:
        for repo in repos:
            yield [
                "/".join([e.strip("/") for e in [mirror, repo, "os/x86_64"]]) + "/",
                repo,
                mirror.strip("/")
                ]

def gen_dbs(name, url):
    """
    Return a generator with different names the repo databases goes by
    """
    for db_name in [".db.tar.gz", ".files.tar.gz", ".db", ".files"]:
        yield url + name + db_name

def download_tar(url):
    # Why this small function?
    # Unit testing and future centralized downloader
    # TODO: Centralized downloading
    try:
        return TarOpen(fileobj=BytesIO(get(url).content))
    except Exception: # TODO: Less broad exception
        pass

def repos_provider(mirrorlist, repo_names):
    """
    Downloading now repos
    """
    # gen_repos provides a list of urls to search for databases
    for repo_base_url, repo_name, mirror_name in gen_repos(mirrorlist, repo_names):

        # Package databases go by different names, this loop iterates thru them
        for repo_db_url in gen_dbs(repo_name, repo_base_url):

            # Download the tar package database then check if anything us there
            repo_tar = download_tar(repo_db_url)
            if repo_tar:

                # Parse the package database into a repo
                new_repo = Repo(repo_tar)

                # Metadata is stored outside of Repo class
                # TODO: Store the metadata inside the class?
                repo = {"name": repo_name, "mirror": mirror_name, "db": new_repo}

                # Add to cache for future use
                yield repo

                # No point downloading the same repo under a different name
                break

def find_package(name, repos, limit=-1):
    """
    Find a package filename and repo

    Arguments:
        name: package name
        repos: a list of repo data (or a generator that is indexable. See hybrid.HybridGenerator)
        limit: limit the number of repos to search

    Return:
        var["mirror"]: The mirror this databases was downloaded from
        var["repo"]: Name of the repo eg. "core"
        var["name"]: Package name
        var["filename"]: Current filename found in databases
        var["size"]: Compressed size of the package
    """ #TODO: Better return type
    for repo in repos:
        if limit == 0:
            break

        if name in repo["db"]:
            info = {
                "mirror": repo["mirror"],
                "repo": repo["name"],
                "name": name,
                "filename": repo["db"][name]["filename"],
                "size": repo["db"][name]["csize"]
                }
            return info
        limit -= 1
    return None

class Search:
    """
    Search a mirror list for package filename and repository name

    Note:
        This is now deprecated in favour of find_package function
    """

    def __init__(self, mirrors, repo_types):
        self._mirrors = mirrors
        self.repo_cache = []
        self.repo_gen = gen_repos(mirrors, repo_types)

    def _return_package(self, package_name, repo):
        """
        Format the return dict
        """
        info = {}
        info["name"] = package_name
        info["repo"] = repo["name"]
        info["mirror"] = repo["mirror"]

        info["filename"] = repo["db"][package_name]["filename"]

        return info

    def find_package(self, package_name, max_repos=-1):
        """
        Search repos and mirrors for a package name

        Return:
            A dict containing
            -Mirrors base url
            -Name of the repo
            -Filename
            -Package name
            See Search._return_package
        """
        # Check the repos that are already downloaded
        for repo in self.repo_cache:

            # Check if the maximum searched repos is there
            if max_repos == 0:
                return

            # Is the package there
            if package_name in repo["db"]:
                return self._return_package(package_name, repo)

            # One less repos to search
            max_repos -= 1

        # Start adding new mirrors if they are not in cache
        # self.repo_gen is a generator from gen_repos(), it is created at the
        # start of the search, it generates a list of repos as needed
        # Examples at gen_repos() declaration
        for repo_base_url, repo_name, mirror_name in self.repo_gen:

            # Check if the maximum searched repos is there
            if max_repos == 0:
                return

            # Package databases go by different names, this loop iterates thru them
            for repo_db_url in gen_dbs(repo_name, repo_base_url):

                # Download the tar package database then check if anything us there
                repo_tar = download_tar(repo_db_url)
                if repo_tar:

                    # Parse the package database into a repo
                    new_repo = Repo(repo_tar)

                    # Metadata is stored outside of Repo class
                    # TODO: Store the metadata inside the class?
                    repo = {"name": repo_name, "mirror": mirror_name, "db": new_repo}

                    # Add to cache for future use
                    self.repo_cache.append(repo)

                    # Check for package in repo
                    if package_name in repo["db"]:
                        return self._return_package(package_name, repo)
                    else:
                        # Not there, so no point downloading the same database
                        break

        # One less repo to search
        max_repos -= 1