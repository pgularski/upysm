# upysm

`upysm` is the MicroPython publishing wrapper for
[`pysm`](https://github.com/pgularski/pysm). It does not maintain a fork of the
library source. A release build fetches the selected `pysm` source
distribution, copies the MicroPython package files into a temporary staging
tree, and publishes matching `upip` and `mip` artifacts with the same version
number.

## Build

Install the release tools:

```bash
python3 -m pip install -r requirements.txt
```

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
with the small MicroPython runtime. Use `--package-profile all` to copy every
Python module from the selected `pysm` package.

The build writes two install shapes:

```text
dist/upysm-<version>.tar.gz  # PyPI/upip source distribution
site/                        # static mip package tree for GitHub Pages
```

## Publish

Publishing is handled by the `Publish` GitHub Actions workflow. Run it
manually, select `latest` or an explicit `pysm` version, and the workflow will
build, check, smoke test, publish the matching `upysm` sdist to PyPI using
trusted publishing, and publish the `mip` package tree to the `gh-pages`
branch.

Configure GitHub Pages once to serve the `gh-pages` branch from `/`.

For a local upload:

```bash
python3 -m scripts.build_upysm --pysm-version 0.4.0 --check
python3 -m twine upload dist/upysm-0.4.0.tar.gz
```

## Install on MicroPython

Modern `mip`/`mpremote` install:

```bash
mpremote mip install https://pgularski.github.io/upysm/
mpremote mip install https://pgularski.github.io/upysm/0.4.0/
```

From the REPL:

```python
import mip
mip.install('https://pgularski.github.io/upysm/')
```

Legacy `upip` install:

```python
import upip
upip.install('upysm')
```

## Smoke Example

```python
from pysm import Event, State, StateMachine

on = State('on')
off = State('off')

sm = StateMachine('sm')
sm.add_state(on, initial=True)
sm.add_state(off)
sm.add_transition(on, off, events=['off'])
sm.add_transition(off, on, events=['on'])
sm.initialize()

assert sm.state == on
sm.dispatch(Event('off'))
assert sm.state == off
sm.dispatch(Event('on'))
assert sm.state == on
```

For full API docs, see the
[`pysm` documentation](http://pysm.readthedocs.io/).
