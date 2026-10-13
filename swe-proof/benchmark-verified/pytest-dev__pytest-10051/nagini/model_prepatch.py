"""Twin-artifact model for pytest-dev__pytest-10051.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture buffer holds a list of captured items. Earlier, while a phase was
  being prepared, an external observer was handed a reference to that very list
  object (the per-phase view of the captured items): the observer's reference
  and the buffer's list are, from that moment on, two names for the SAME list
  object.

  Discarding the buffer's captured items must leave that shared list EMPTY while
  keeping it the SAME object, so that the observer that still holds the earlier
  reference agrees with the buffer afterwards:

    (1) after the discard, the buffer's captured-items list is empty;

    (2) after the discard, the buffer's captured-items list is the SAME object it
        was before the discard (its identity is preserved, not replaced by a
        fresh empty list);

  and consequently the previously-handed-out observer reference, which named
  that object before the discard, still names the buffer's live list afterwards:

    (3) the observer's reference and the buffer's captured-items list are the
        same object after the discard, the observer sees it as empty, and any
        item subsequently captured into the buffer is visible through the
        observer's reference as well.

  A discard that rebinds the buffer to a brand-new empty list would satisfy "the
  buffer is now empty" but would orphan the observer's reference — it would
  point at the old, detached list and diverge from the buffer permanently. The
  identity clause (2)/(3) is exactly what forbids that.

The buffer is modelled as a minimal object exposing only the touched field: its
list of captured items (`items`), where each captured item is abstracted to
an `int` identity (the tested behaviour observes only how many items are present
and that the observer's list tracks the buffer's, not the items' internals). The
observer reference is a second name (`view`) required to alias the buffer's list
on entry. The in-place list-emptying primitive this discard builds on (an unchanged
language builtin that empties a list WITHOUT replacing the object) is
axiomatized: `empty_in_place`. Its identity-preserving contract is the crux and
is validated against real Python out-of-band by axiom_check.py (G-AX).

Termination (total correctness): both modelled operations are single bounded
steps on one shared list object (one in-place emptying; one append) that must
actually ANSWER — return to their caller with the discard/append performed.
Nagini is a partial-correctness verifier by default, so without an explicit
obligation a non-terminating implementation (e.g. bare self-recursion before
or after doing the work) satisfies every `Ensures` vacuously while never
actually delivering the emptied/extended list to its caller; the real
`clear`/`emit` always return. The obligation is carried as `MustTerminate` in
each precondition, with a strictly smaller measure on the consumed
`empty_in_place` axiom (the builtin always terminates) so a routine may invoke
the primitive but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CaptureBuffer:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        self.items = []  # type: List[int]


# axioms-start
@ContractOnly
def empty_in_place(xs: List[int]) -> None:
    """The unchanged language builtin that empties a list IN PLACE: it removes
    every element of `xs` while leaving `xs` the SAME object (it does not bind a
    fresh empty list). This is the primitive this discard is built on; its
    object-identity-preserving behaviour is the crux. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(xs)))
    # The builtin is a single bounded step: it always terminates (measure 1,
    # strictly below the callers' measure 2, so callers may consume it but a
    # self-recursive caller cannot discharge its own obligation).
    Requires(MustTerminate(1))
    Ensures(Acc(list_pred(xs)))
    Ensures(len(xs) == 0)
    Ensures(xs is Old(xs))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def discard_captured(buf: CaptureBuffer, view: List[int]) -> None:
    # pre-conditions-start
    # The buffer fully owns its captured-items list (it is about to mutate it).
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    # `view` is the reference an external observer was handed earlier: on entry
    # it is the SAME object as the buffer's captured-items list (full ownership
    # of that one object is held under the single `buf.items` name).
    Requires(view is buf.items)
    # TERMINATION: the discard is one bounded in-place emptying that must
    # actually ANSWER (return with the shared list emptied). Without the
    # obligation a diverging implementation satisfies every Ensures vacuously
    # while never actually handing the emptied list back to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    # (1) the captured-items list is now empty ...
    Ensures(len(buf.items) == 0)
    # (2) ... and it is the SAME list object it was before the discard (its
    # identity is preserved; it was emptied in place, not replaced).
    Ensures(buf.items is Old(buf.items))
    # (3) therefore the observer's earlier reference still names the buffer's
    # live list: `view` is the buffer's captured-items list afterwards, and the
    # observer sees it as empty (the same emptiness the buffer sees).
    Ensures(view is buf.items)
    # post-conditions-end
    # impl-start
    # buf.items = []  -- the buggy discard: rebind to a BRAND-NEW empty list.
    # The buffer ends up empty, but its captured-items list is now a DIFFERENT
    # object, so the observer's earlier reference is orphaned (left pointing at
    # the old, detached list). This breaks the identity clause (2)/(3).
    buf.items = []
    return
    # impl-end


def append_then_visible(buf: CaptureBuffer, view: List[int], item: int) -> None:
    # pre-conditions-start
    # After a discard the observer reference still aliases the live list; capturing
    # a new item into the buffer must be visible through that observer reference.
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    Requires(view is buf.items)
    Requires(len(buf.items) == 0)
    # TERMINATION: capturing one item is a single bounded append that must
    # actually ANSWER (return with the item visible through the alias); a
    # diverging implementation would satisfy the Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    Ensures(view is buf.items)
    # the newly captured item is now in the buffer's list ...
    Ensures(len(buf.items) == 1)
    Ensures(buf.items[0] == item)
    # ... and, because the observer reference is the same object, it is visible
    # through the observer's view too.
    Ensures(len(view) == 1)
    Ensures(view[0] == item)
    # post-conditions-end
    # impl-start
    buf.items.append(item)
    return
    # impl-end
