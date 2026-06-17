# upysm

`upysm` is the MicroPython distribution channel for
[`pysm`](https://github.com/pgularski/pysm), a finite state machine library.

Use `pysm` directly on regular Python. Use `upysm` when installing the same
library on MicroPython.

The library source still belongs to `pysm`. `upysm` is not a fork and does not
carry separate application code; it publishes MicroPython install artifacts
from selected `pysm` releases.

## Install on MicroPython

Modern `mip`/`mpremote` install:

```bash
mpremote mip install https://pgularski.github.io/upysm/
```

Pin a specific version when you want repeatable device builds:

```bash
mpremote mip install https://pgularski.github.io/upysm/0.4.0/
```

From the MicroPython REPL:

```python
import mip
mip.install('https://pgularski.github.io/upysm/')
```

Legacy `upip` install:

```python
import upip
upip.install('upysm')
```

The installed package imports as `pysm`, because the API is the upstream
library API:

```python
from pysm import Event, State, StateMachine
```

## Example

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

For the full API, see the
[`pysm` documentation](http://pysm.readthedocs.io/).

Maintainer release notes live in [RELEASING.md](RELEASING.md).
