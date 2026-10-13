"""Twin-artifact model for django__django-13417.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A result set's introspection flag answers "will this result set come back in
  a well-defined order?" It is decided from five independent conditions about
  the result set, each consumed purely as a yes/no signal:

    * `is_empty`        - the result set is statically empty;
    * `has_raw_order`   - an explicit raw / column ordering was attached;
    * `default_on`      - default ordering inherited from the model is active;
    * `model_has_order` - the model declares a default ordering at all;
    * `is_grouped`      - the result set collapses rows into groups.

  The flag is TRUE exactly when the result set is statically empty, OR an
  explicit ordering is attached, OR a model default ordering is both active and
  declared AND the result set is NOT grouped. When rows are collapsed into
  groups, an inherited model default ordering no longer governs the row order,
  so a grouped result set with only a default (non-explicit) ordering is NOT
  ordered.

The five conditions are read in the repository as attributes whose only use is
their truth value; they are modelled here as `bool` (the truthy-refinement is
recorded in refinement.md / mapping.md). The result is pinned exactly to the
boolean predicate above, so no implementation that disagrees on any of the
thirty-two input combinations can verify. There are no library callees to
axiomatize and no heap-carried mutable inputs: the operation is a pure boolean
decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
               model_has_order: bool, is_grouped: bool) -> bool:
    """The exact decision the flag must report: empty, or an explicit ordering,
    or an active+declared model default ordering on a result set that is not
    grouped. Grouping suppresses an inherited default ordering."""
    return (
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )
# pure-end


def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
            model_has_order: bool, is_grouped: bool) -> bool:
    # pre-conditions-start
    # Total correctness: this decision must TERMINATE, not merely satisfy the
    # postconditions on runs that reach the return. The level is an ordinal for
    # the obligation ordering, not a measure: there is no loop and no recursion
    # here, so nothing counts down. It is input-dependent (3 on the empty
    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
    # self-call on a non-empty input: Nagini requires callee level < caller
    # level, which a single literal level can never satisfy against itself.
    Requires(MustTerminate(3 if is_empty else 2))
    # pre-conditions-end
    # post-conditions-start
    # The flag equals the exact boolean decision over the five signals.
    Ensures(Result() == is_ordered(is_empty, has_raw_order, default_on,
                                    model_has_order, is_grouped))
    # Pinned consequences that any correct decision must exhibit, derived from
    # the desired behaviour above (each ties the result to a witnessed input):
    #   an empty result set is always ordered;
    Ensures(Implies(is_empty, Result()))
    #   an explicitly-ordered result set is always ordered;
    Ensures(Implies(has_raw_order, Result()))
    #   a grouped result set whose only ordering is an inherited model default
    #   (no emptiness, no explicit ordering) is NOT ordered;
    Ensures(Implies(not is_empty and not has_raw_order and is_grouped,
                    not Result()))
    #   the same default ordering on a non-grouped result set IS ordered.
    Ensures(Implies(not is_empty and not has_raw_order
                    and default_on and model_has_order and not is_grouped,
                    Result()))
    # post-conditions-end
    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end
