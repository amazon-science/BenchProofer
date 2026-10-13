"""Twin-artifact model for django__django-16950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an inline child form is being prepared for a parent object that is still
  in the process of being added (not yet persisted), the parent's in-memory
  value for the related key may carry a model-supplied default that was
  generated client-side. That generated value must be discarded (reset to the
  empty/None state, so the persistence layer regenerates or fills it) ONLY in
  the cases where keeping it would wrongly trigger validation against a value
  the parent does not yet really own. Concretely the related-key value is
  cleared exactly when ALL of the following hold:

    (1) the parent is being added (not an existing, persisted parent); and
    (2) the related key actually carries a model-supplied default; and
    (3) EITHER the related key IS the parent's own primary identifier,
        OR no submitted form data accompanies the request.

  In every other situation the parent's related-key value is preserved
  unchanged. In particular, when the relation targets a non-primary alternate
  key that carries a default AND submitted form data is present, the
  generated value is KEPT, so the child can be related to the parent by that
  freshly generated alternate key.

The parent object is modelled as a minimal class carrying only the one touched
field — the related-key value (``Optional[int]``; a generated default is a
concrete value, the cleared state is ``None``). The three conditions are
modelled as read-only booleans.

The clearing decision is a bounded, straight-line operation: it MUST terminate
and return to its caller (a total-correctness obligation, carried as
MustTerminate in the precondition). A decision step that diverges never
delivers the (cleared or preserved) key to the form machinery that reads it
next, so it does not implement the behaviour either.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ParentObject:
    def __init__(self, key: Optional[int]) -> None:
        # Constructing the minimal parent object is bounded work; the strictly
        # smaller measure (1 < 2) lets a caller holding MustTerminate(2)
        # construct a fresh parent without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.key) and self.key is key)  # type: ignore
        self.key = key


# axioms-start
# (no axiomatized callees: the changed operation is the clearing decision
# itself, modelled deeply over booleans + the in-memory key field.)
# axioms-end


# pure-start
@Pure
def should_clear(adding: bool, key_has_default: bool,
                 key_is_primary: bool, form_data_present: bool) -> bool:
    """The decision the prepared inline child form makes about the parent's
    related-key value: the generated default is discarded exactly when the
    parent is being added, the key carries a default, and either the key is the
    parent's primary identifier or no form data was submitted."""
    return (adding and key_has_default
            and (key_is_primary or not form_data_present))
# pure-end


def reset_default_related_key(instance: ParentObject, adding: bool,
                              key_has_default: bool, key_is_primary: bool,
                              form_data_present: bool) -> None:
    # pre-conditions-start
    Requires(Acc(instance.key))
    # The clearing decision is a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass`) or a same-measure self-call
    # would satisfy both value postconditions only vacuously, yet would never
    # return the (cleared or preserved) key to the form machinery; this
    # obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(instance.key))
    # The related-key value is cleared to None exactly in the discarding case,
    # and preserved unchanged in every other case.
    Ensures(Implies(should_clear(adding, key_has_default, key_is_primary,
                                  form_data_present),
                    instance.key is None))
    Ensures(Implies(not should_clear(adding, key_has_default, key_is_primary,
                                     form_data_present),
                    instance.key is Old(instance.key)))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: while adding, the generated default is discarded
    # whenever the key merely carries a default, ignoring whether the key is
    # the parent's primary identifier or whether form data was submitted.
    if adding:
        if key_has_default:
            instance.key = None
    # impl-end
