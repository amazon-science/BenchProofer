"""Twin-artifact model for django__django-13964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When persisting an object that holds a reference to another, already-saved
  object, the reference is carried locally by a stored-key attribute. If that
  local attribute currently holds an EMPTY PLACEHOLDER value, the persisting
  object adopts the referenced object's stored key into it before the row is
  written, so the two ends agree.

  An "empty placeholder" is any of the recognized empty values a freshly
  initialized key attribute can take: the absent marker (``None``) AND the empty
  textual value (the empty character sequence used by a textual key). Both must
  be treated as unset and overwritten with the referenced object's key. This is
  the crux: a textual key initialized to the empty sequence is just as unset as
  an absent numeric key, and must likewise be filled.

  If, on the other hand, the local attribute ALREADY holds a non-empty stored
  key, it is a deliberate value and must be left exactly as it is.

The local stored-key attribute is modelled as an ``Optional[List[int]]`` of
Unicode code points: the absent marker is ``None`` (an unset numeric key), the
empty sequence ``[]`` is the empty textual value, and a non-empty list is a
concrete textual key. These three are genuinely distinct — ``None`` is NOT the
empty sequence. The referenced object's stored key is a non-empty ``List[int]``
(it has been saved, so it carries a real key).

No callee is axiomatized: the behaviour is emptiness/membership logic over the
object's own attribute and the referenced key, modelled deeply. The set of
recognized empty placeholders is a well-known constant collection; its two
members relevant here (the absent marker and the empty sequence) are spelled out
in the ``is_empty_placeholder`` predicate. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_empty_placeholder(value: Optional[List[int]]) -> bool:
    """True iff `value` is one of the recognized empty placeholder values that
    a not-yet-assigned stored-key attribute can hold: the absent marker
    (`None`) or the empty character sequence (`[]`). A non-empty sequence is a
    concrete key and is NOT an empty placeholder. The absent marker and the
    empty sequence are distinct values that BOTH count as empty."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return True
    return len(value) == 0


@Pure
def stored_seq(value: Optional[List[int]]) -> PSeq[int]:
    """The character sequence currently stored: the value's own sequence when a
    concrete key is present, the empty sequence for the absent marker."""
    Requires(Implies(value is not None, Acc(list_pred(value), 1 / 4)))
    if value is None:
        return PSeq(0).take(0)
    return ToSeq(value)
# pure-end


class SaveTarget:
    def __init__(self, fk: Optional[List[int]]) -> None:
        Requires(Implies(fk is not None, Acc(list_pred(fk))))
        Ensures(Acc(self.fk) and self.fk is fk)  # type: ignore
        Ensures(Implies(self.fk is not None, Acc(list_pred(self.fk))))  # type: ignore
        self.fk = fk


def adopt_referenced_key_if_unset(target: SaveTarget, related_key: List[int]) -> None:
    # pre-conditions-start
    # The local stored-key attribute is the only mutated object (full
    # permission, exact post-state stated below). `related_key` is read-only:
    # required AND ensured at fractional permission (directive 5).
    Requires(Acc(target.fk))
    Requires(Implies(target.fk is not None, Acc(list_pred(target.fk))))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The referenced object has been saved, so it carries a real (non-empty)
    # stored key — this is the branch reached once the referenced key is known.
    Requires(len(related_key) > 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(target.fk))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    # The attribute always ends holding a concrete, non-empty stored key.
    Ensures(target.fk is not None)
    Ensures(Acc(list_pred(target.fk)))
    Ensures(len(target.fk) > 0)
    # (1) The discriminating guarantee: if the attribute held an empty
    # placeholder on entry — the absent marker OR the empty character sequence —
    # it now holds the referenced object's stored key. The empty-sequence case
    # is exactly the one that must be filled here.
    Ensures(Implies(Old(is_empty_placeholder(target.fk)),
                    stored_seq(target.fk) == ToSeq(related_key)))
    # (2) Faithfulness: a deliberately-set, non-empty stored key is preserved
    # untouched (same object, same contents).
    Ensures(Implies(not Old(is_empty_placeholder(target.fk)),
                    target.fk is Old(target.fk) and
                    stored_seq(target.fk) == Old(stored_seq(target.fk))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: only the absent marker (`None`) is treated as
    # unset. A stored-key attribute initialized to the empty character sequence
    # (`[]`) is left untouched — so the referenced key is never adopted into it,
    # which is exactly the data-loss the fix addresses.
    if target.fk is None:
        adopted = []  # type: List[int]
        i = 0
        while i < len(related_key):
            # invariants-start
            Invariant(Acc(list_pred(related_key), 1 / 2))
            Invariant(Acc(list_pred(adopted)))
            Invariant(len(related_key) > 0)
            Invariant(0 <= i and i <= len(related_key))
            Invariant(len(adopted) == i)
            Invariant(ToSeq(adopted) == ToSeq(related_key).take(i))
            Invariant(MustTerminate(len(related_key) - i + 1))
            # invariants-end
            adopted.append(related_key[i])
            i = i + 1
        Assert(ToSeq(related_key).take(len(related_key)) == ToSeq(related_key))
        target.fk = adopted
    # impl-end
