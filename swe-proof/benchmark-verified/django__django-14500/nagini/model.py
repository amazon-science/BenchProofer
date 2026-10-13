"""Twin-artifact model for django__django-14500.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored migration is rolled back, the migration-state bookkeeper must
  record every bookkeeping key that should leave the "applied" set as a result
  of that roll-back. A migration is identified by its own key. Some migrations
  are *replacement* migrations: they stand in for a set of other (replaced)
  migrations whose individual keys are listed.

  Rolling a migration back records the following keys as no-longer-applied:

    * the keys of all migrations it stands in for (when it is a replacement;
      the run visits them in their listed order), AND
    * the migration's OWN key.

  The own key is recorded UNCONDITIONALLY -- a replacement migration that is
  rolled back leaves the applied set exactly like any other migration would,
  i.e. its own key is no longer applied, in addition to the keys it stands in
  for.
  A non-replacement migration (empty replaced-key list) records only its own
  key. So the recorded keys are precisely the replaced keys, in listed order,
  followed by the migration's own key.

Each migration bookkeeping key (a migration's identity key) is modelled as an
integer code; the list of keys recorded as no-longer-applied is a `List[int]`.
The replaced-key list is a `PSeq[int]`. The recorded-key sequence is the only
observable behaviour; it is modelled deeply as a front-recursive build, so no
callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: recording a key as no-longer-applied is a pure
# append against the bookkeeper, modelled deeply below as the sequence of keys
# recorded. The schema-existence check and the underlying row deletion the
# bookkeeper performs are unchanged by, and independent of, which keys this
# operation chooses to record, and are unobserved by the behaviour pinned here.)
# axioms-end


# pure-start
# (no pure helpers needed: the recorded-key sequence is pinned exactly by
# sequence equality, which needs no recursive predicate.)
# pure-end


def keys_leaving_applied_set(own_key: int, replaced_keys: PSeq[int]) -> List[int]:
    # pre-conditions-start
    # `replaced_keys` is a pure sequence value (the keys this migration stands in
    # for); the result is a freshly-built list of the keys recorded as
    # no-longer-applied. No object is mutated, so nothing needs full permission.
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The recorded keys are exactly: each replaced key (in listed order),
    # followed by the migration's OWN key. The own key is appended
    # UNCONDITIONALLY -- whether or not the migration is a replacement. This is
    # the discriminating behaviour: a replacement migration's own key must leave
    # the applied set when it is rolled back, not only the keys it stands in for;
    # and it is recorded last, after the replaced ones.
    Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # For replacement migrations, record each replaced key as no-longer-applied,
    # in listed order.
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        # The recorded keys so far are exactly the first `i` replaced keys.
        Invariant(ToSeq(result) == replaced_keys.take(i))
        Invariant(MustTerminate(len(replaced_keys) - i + 1))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    # Then record the migration's own key as no-longer-applied -- always.
    result = result + [own_key]
    return result
    # impl-end
