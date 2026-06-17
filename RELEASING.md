# Releasing upysm

`upysm` publishes MicroPython install artifacts from selected
[`pysm`](https://github.com/pgularski/pysm) releases.

A release build fetches the selected `pysm` source distribution, stages the
files that work on MicroPython, and produces matching `upip` and `mip`
artifacts with the same version number.

## Install Release Tools

```bash
python3 -m pip install -r requirements.txt
```

## Build

Build the latest published `pysm` release:

```bash
python3 -m scripts.build_upysm --pysm-version latest --check --smoke
```

Build a selected version:

```bash
python3 -m scripts.build_upysm --pysm-version 0.4.0 --check --smoke
```

The default `core` package profile copies only `pysm/__init__.py`,
`pysm/pysm.py`, and `pysm/version.py`, which keeps the device package aligned
with the small MicroPython runtime.

Use `--package-profile all` to copy every Python module from the selected
`pysm` package:

```bash
python3 -m scripts.build_upysm \
  --pysm-version 0.4.0 \
  --package-profile all \
  --check \
  --smoke
```

The build writes two install shapes:

```text
dist/upysm-<version>.tar.gz  # PyPI/upip source distribution
site/                        # static mip package tree for GitHub Pages
```

## Publish PyPI

PyPI publishing is manual. Build and check the selected `pysm` release, then
upload the matching `upysm` source distribution:

```bash
python3 -m scripts.build_upysm --pysm-version 0.4.0 --check --smoke
python3 -m twine upload dist/upysm-0.4.0.tar.gz
```

## Publish mip

The generated `site/` tree is the static `mip` package served from
<https://pgularski.github.io/upysm/>.

Publish it after the PyPI upload, using the same `pysm` version and package
profile. The published tree should include:

```text
/
/latest/
/<version>/
```

Each package directory contains `package.json` and the staged `pysm` package
files. Configure GitHub Pages once to serve the `gh-pages` branch from `/`.

## Repository Layout

- `scripts/build_upysm.py` builds `upysm` artifacts from a selected `pysm`
  release.
- `setup.py` and `sdist_upip.py` produce the `upip`-compatible source
  distribution.
- `site/` is generated output for the `mip` package tree and GitHub Pages.
- `test/upysm_smoke.py` checks that the staged package works on CPython and in
  the MicroPython Unix smoke job.
