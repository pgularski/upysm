import sys

sys.path.insert(0, '.')


OPTIONAL_MODULES = (
    'pysm.aio',
    'pysm.builder',
    'pysm.queued',
    'pysm.serialization',
)


def import_optional_modules():
    modules = {}
    missing = []

    for name in OPTIONAL_MODULES:
        try:
            modules[name] = __import__(
                name,
                globals(),
                locals(),
                ('__name__',),
            )
        except ImportError as exc:
            missing.append((name, exc))

    if len(missing) == len(OPTIONAL_MODULES):
        print('upysm all-module smoke skipped: optional modules not packaged')
        return None

    if missing:
        details = ', '.join(
            '{0}: {1}'.format(name, exc) for name, exc in missing
        )
        raise AssertionError('missing optional pysm modules: {0}'.format(
            details
        ))

    return modules


def test_queued_state_machine(queued_module):
    from pysm import Event, State

    machine = queued_module.QueuedStateMachine('queued')
    idle = State('idle')
    working = State('working')
    done = State('done')
    calls = []

    def start_action(state, event):
        calls.append(('start', state.name))
        event.state_machine.dispatch(Event('finish'))

    def finish_action(state, event):
        calls.append(('finish', state.name))

    machine.add_state(idle, initial=True)
    machine.add_state(working)
    machine.add_state(done)
    machine.add_transition(
        idle,
        working,
        events=['start'],
        action=start_action,
    )
    machine.add_transition(
        working,
        done,
        events=['finish'],
        action=finish_action,
    )
    machine.initialize()

    machine.dispatch(Event('start'))

    assert machine.state is done
    assert machine.leaf_state is done
    assert calls == [('start', 'idle'), ('finish', 'working')]


async def async_queued_state_machine_case(aio_module):
    from pysm import Event, State

    machine = aio_module.AsyncQueuedStateMachine('async-queued')
    idle = State('idle')
    working = State('working')
    done = State('done')
    calls = []

    async def start_action(state, event):
        calls.append(('start', state.name))
        await event.state_machine.dispatch(Event('finish'))

    async def finish_action(state, event):
        calls.append(('finish', state.name))

    machine.add_state(idle, initial=True)
    machine.add_state(working)
    machine.add_state(done)
    machine.add_transition(
        idle,
        working,
        events=['start'],
        action=start_action,
    )
    machine.add_transition(
        working,
        done,
        events=['finish'],
        action=finish_action,
    )

    await machine.async_initialize()
    await machine.dispatch(Event('start'))

    assert machine.state is done
    assert machine.leaf_state is done
    assert calls == [('start', 'idle'), ('finish', 'working')]


def run_async(coro):
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    if hasattr(asyncio, 'run'):
        return asyncio.run(coro)

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


def test_async_queued_state_machine(aio_module):
    run_async(async_queued_state_machine_case(aio_module))


def main():
    modules = import_optional_modules()
    if modules is None:
        return

    test_queued_state_machine(modules['pysm.queued'])
    test_async_queued_state_machine(modules['pysm.aio'])
    print('upysm all-module smoke ok')


main()
