"""Twin-artifact model for django__django-14792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A time-zone object exposes two textual observations: a short per-instant
  abbreviation/offset label (which may be absent — modelled as ``None`` — for
  zones that do not define one), and a full textual rendering that is always
  present. The helper that resolves a single canonical name for such an object
  must prefer the short label whenever it is present and non-empty, and fall
  back to the full rendering only when the short label is absent or empty.

  Concretely, for a fixed-offset zone whose short label is e.g. ``"+10"`` while
  its full rendering is e.g. ``"Etc/GMT-10"``, the resolved name is the short
  label ``"+10"`` (the offset-bearing form), NOT the full rendering. For a zone
  whose short label is absent (``None``) or empty, the resolved name is the
  full rendering.

The time-zone object is modelled as a minimal class carrying only the two
touched observations. Strings are modelled as ``PSeq[int]`` of Unicode code
points (Nagini bans ``str`` indexing); the short label is ``Optional[PSeq[int]]``
(``None`` ↔ absent, the empty sequence ↔ the empty string ``''``). The two
observations are the unchanged object queries the resolution selects between;
their content is opaque, so the resolved name is pinned structurally to be
exactly one of the two carried observations, chosen by the present-and-non-empty
predicate.

The resolution is a bounded, straight-line selection between the two carried
observations: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges —
e.g. hangs instead of returning one of the two observations — would satisfy
the value postconditions only vacuously and would hang every caller (and the
F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TimeZone:
    def __init__(self, short_label: Optional[PSeq[int]], full_name: PSeq[int]) -> None:
        Ensures(Acc(self.short_label) and self.short_label is short_label)  # type: ignore
        Ensures(Acc(self.full_name) and self.full_name is full_name)        # type: ignore
        self.short_label = short_label  # type: Optional[PSeq[int]]   # short label
        self.full_name = full_name      # type: PSeq[int]             # full rendering


# axioms-start
# (No callee is axiomatized. The two textual observations the resolution selects
#  between are carried directly as the object's fields — the model's inputs —
#  with opaque content, and the resolved name is pinned to be exactly one of
#  them. The selection between them is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def present_and_nonempty(label: Optional[PSeq[int]]) -> bool:
    """A textual label counts as usable iff it is present (not ``None``) and
    non-empty — exactly Python's truthiness of an ``Optional[str]``."""
    return label is not None and len(label) > 0
# pure-end


def resolve_timezone_name(tz: TimeZone) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(tz.short_label, 1 / 2))
    Requires(Acc(tz.full_name, 1 / 2))
    # Total correctness: the real operation is a bounded, straight-line
    # selection between the two carried observations — it must TERMINATE.
    # Without this obligation a diverging impl (e.g. an infinite loop)
    # satisfies every value postcondition vacuously yet would hang every
    # caller (and the F2P test) forever.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tz.short_label, 1 / 2))
    Ensures(Acc(tz.full_name, 1 / 2))
    # The resolved name is the short label when it is present and non-empty,
    # otherwise the full rendering. (The discriminating clause: a present,
    # non-empty short label wins over the full rendering.)
    Ensures(Implies(present_and_nonempty(tz.short_label),
                    Result() == tz.short_label))
    Ensures(Implies(not present_and_nonempty(tz.short_label),
                    Result() == tz.full_name))
    # post-conditions-end
    # impl-start
    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
    if label is not None and len(label) > 0:
        return label
    return tz.full_name                                   # str(timezone)
    # impl-end
