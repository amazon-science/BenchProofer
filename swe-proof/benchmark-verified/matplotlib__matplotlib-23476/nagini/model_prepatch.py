"""Twin-artifact model for matplotlib__matplotlib-23476.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A figure's dpi must be STABLE under a save/restore round trip: taking a
  figure through such a round trip, repeatedly, must leave the recorded dpi at
  the value it already had, rather than letting it drift upwards on every cycle
  (doubling until it grows past what can be represented).

  What a round trip carries is a mapping of the figure's recorded values. That
  mapping always holds a dpi entry, and it may also hold a second entry recording
  a reference dpi. The behaviour required of the step specified here: whenever
  the reference entry is present, the dpi entry is recorded as that reference
  value; otherwise the dpi entry keeps the value it already held.

  Every entry of the mapping other than the dpi entry -- including the reference
  entry itself -- is left exactly as it was; only the dpi entry may change.

Modelling choices (Nagini fragment):
  * The mapping of recorded values is a ``Dict[int, int]`` from an entry-name
    token to that entry's value token. Only membership of, and the value at, the
    two relevant entry names is observed, so an integer-keyed mapping is the
    faithful carrier (mapping.md §2). ``key_dpi`` names the dpi entry;
    ``key_reference`` names the reference-dpi entry; they are distinct.
  * dpi values are modelled as ``int`` tokens. The specified behaviour SELECTS
    one of two stored dpi values by entry membership; it never computes on the
    value, so the tested behaviour is precision-independent and the value
    carrier need not be a real ``float`` (mapping.md §2).

The mapping is genuinely mutated in place (the dpi entry is reassigned), so it
is held at FULL permission with the post-state stated exactly via ``Old``. No
callee is axiomatised: the behaviour is pure mapping logic, modelled deeply.
Markers (machine-parsed) delimit the spec / proof / impl regions.

The operation is a bounded, loop-free selection carried out as one step of the
round trip: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges would
satisfy the value postconditions only vacuously while hanging the round trip
forever -- the cycle the behaviour is about would never complete.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def key_dpi() -> int:
    # The entry name of the dpi entry of the mapping.
    return 0


@Pure
def key_reference() -> int:
    # The entry name of the reference-dpi entry, when present. Distinct from the
    # dpi entry name.
    return 1
# pure-end


def normalize_state_dpi(state: Dict[int, int],
                        reference_present: bool,
                        reference_value: int) -> None:
    # pre-conditions-start
    # The mapping is mutated in place (the dpi entry is reassigned), so it is
    # held at FULL permission. A mapping of recorded values always holds a dpi
    # entry.
    Requires(Acc(dict_pred(state)))
    Requires(state is not None)
    Requires(key_dpi() in state)
    # ``reference_present`` / ``reference_value`` capture, AT ENTRY, whether the
    # reference-dpi entry exists and (if so) its value. They are pre-state facts
    # about the input -- bound before any mutation -- so the selection guarantee
    # below gates on the genuine entry record rather than on a query against the
    # (mutated-in-place) mapping, which an implementation could perturb.
    Requires(reference_present == (key_reference() in state))
    Requires(Implies(reference_present, reference_value == state[key_reference()]))
    # The selection is a bounded, loop-free step of the round trip: it MUST
    # terminate -- total correctness. A diverging implementation would satisfy
    # the value postconditions only vacuously while hanging the round trip
    # forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(state)))
    # The dpi entry remains present ...
    Ensures(key_dpi() in state)
    # ... and now holds the reference value when a reference entry was present at
    # entry, the value it already held otherwise. The antecedents are the
    # captured ENTRY facts, so each implication has teeth: the recorded value
    # must be PRODUCED by the selection, not merely left at whatever it happened
    # to be.
    Ensures(Implies(reference_present, state[key_dpi()] == reference_value))
    Ensures(Implies(not reference_present, state[key_dpi()] == Old(state[key_dpi()])))
    # No entry other than the dpi entry changes: every other name's membership is
    # preserved, and no new name is introduced. In particular the reference entry
    # itself is untouched.
    Ensures(Forall(int, lambda k: Implies(k != key_dpi(),
                                          (k in state) == Old(k in state))))
    Ensures(Forall(int, lambda k: Implies(k != key_dpi() and Old(k in state),
                                          state[k] == Old(state[k]))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the round trip's mapping is produced WITHOUT
    # selecting the reference value for the dpi entry. That entry is left at
    # whatever value it already held -- so when a reference entry is present and
    # differs, the recorded value is the non-reference one, and the stability
    # guarantee fails.
    pass
    # impl-end
