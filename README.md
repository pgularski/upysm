# upysm
Versatile and flexible Python State Machine library - Micropython Port

This repository is basically a set of tools to build and deploy (to pypi) the
Micropython Port of the [pysm](https://github.com/pgularski/pysm) library.

It's successfully tested against the ESP-32S ESP-WROOM-32 NodeMCU board.

# Installation

```python
import upip
upip.install('upysm')
```

# Usage
Basic usage:

```python
import machine
from pysm import State, StateMachine, Event
import time

led = machine.Pin(2, machine.Pin.OUT)

test_list = []

def on_enter(state, event):
    test_list.append(('enter', state))
    led.value(1)
    time.sleep(0.1)

def on_exit(state, event):
    test_list.append(('exit', state))
    led.value(0)
    time.sleep(0.1)

on = State('on')
off = State('off')

sm = StateMachine('sm')
sm.add_state(on, initial=True)
sm.add_state(off)

sm.add_transition(on, off, events=['off'])
sm.add_transition(off, on, events=['on'])

on.handlers = {'enter': on_enter, 'exit': on_exit}
off.handlers = {'enter': on_enter, 'exit': on_exit}

sm.initialize()

assert sm.state == on
sm.dispatch(Event('off'))
assert sm.state == off
sm.dispatch(Event('on'))
assert sm.state == on
```

For more examples and API description refer to the [pysm documentation](http://pysm.readthedocs.io/).
