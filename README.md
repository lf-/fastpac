# fastpac
Parallel pacman package downloader

## Manual installation (packaging to follow)

This package needs python 3.6 or later.

Create requisite directories and set up config file:

```
# python3 setup.py install
# useradd --system fastpac
# mkdir -p /var/cache/fastpac/{pkg,pkglists}
# chown -R fastpac:fastpac /var/cache/fastpac
# cp config.py /etc/fastpac.conf.py
```

## Usage

```
# su fastpac
$ pacman -Q > "/var/cache/fastpac/packagelists/$(hostname)"
$ fastpac
```

## Hacking

Contributions are welcome! We use pytest for testing all new code added to
fastpac, which you can use to test the codebase by running `py.test`.

To set up a development environment, run the following commands:

```
$ pip install --user -e .[dev]  # install all the fastpac deps to user profile, including dev deps
$ py.test  # run test suite to make sure everything is ok
```

