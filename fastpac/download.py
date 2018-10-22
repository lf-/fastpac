from requests import get as get_url


def assemble_package_url(package_info, base_url, arch):
    return "/".join((base_url.strip("/"), package_info.repo, f'os/{arch}', package_info.filename))


def download_file_to_path(url, path):
    request = get_url(url, stream=True)
    with open(path, mode='bw') as f:
        for part in request.iter_content(chunk_size=1024):
            if part:
                f.write(part)
