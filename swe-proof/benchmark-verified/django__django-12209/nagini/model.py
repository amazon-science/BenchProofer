"""Twin-artifact model for django__django-12209.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single-table persistence routine decides how to store an instance that
  carries an identifier value. It may take a short-cut that *skips the
  existence check and goes straight to an insertion*. That short-cut is sound
  only when the instance is known to be genuinely new — when its identifier was
  produced by the field's own generating default rather than supplied by the
  caller.

  When instead the caller has explicitly supplied the identifier, the same
  identifier may already correspond to a stored row, so the short-cut MUST NOT
  be taken: the routine must first attempt to update the matching row, and
  insert only if none matched.

  Concretely the routine reports whether it updated an existing row. It reports
  an update exactly when an identifier is present, the insertion short-cut was
  not engaged, and the underlying update primitive matched a stored row. The
  short-cut engages only when ALL of the following hold together: the
  identifier was not caller-supplied, the caller did not already force an
  insertion, the instance is being added, and the identifier field carries a
  generating default.

The numerous data objects of the real routine are not touched by this change
and are abstracted away; the contract is entirely about the boolean decision of
whether the insertion short-cut engages. The unchanged update primitive (which
reports whether a stored row matched the identifier) is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def update_matched_row() -> bool:
    """Outcome reported by the unchanged update primitive for this instance's
    identifier: True iff it matched and updated a stored row. A single,
    instance-fixed observation (the primitive is only consulted along the
    update path). Provenance + executable soundness: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def shortcut_engaged(pk_explicit: bool, force_insert: bool, adding: bool,
                     pk_has_default: bool) -> bool:
    """Whether the straight-to-insertion short-cut engages. It engages exactly
    when ALL of the following hold: the identifier was not caller-supplied, the
    caller did not already force an insertion, the object is being added, and
    its identifier field carries a generating default. When the caller supplied
    the identifier explicitly the short-cut is suppressed, so a possibly
    pre-existing identifier is offered for update rather than blindly
    inserted."""
    return (not pk_explicit) and (not force_insert) and adding and pk_has_default


@Pure
def forces_insert(pk_explicit: bool, force_insert: bool, adding: bool,
                  pk_has_default: bool) -> bool:
    """The effective decision to go straight to insertion: either the caller
    forced it or the short-cut engaged. When this is False (and an identifier
    is present) the routine first attempts to update an existing row."""
    return force_insert or shortcut_engaged(pk_explicit, force_insert, adding,
                                            pk_has_default)
# pure-end


def store_single_table(pk_explicit: bool, force_insert: bool, pk_set: bool,
                       adding: bool, pk_has_default: bool) -> bool:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The routine reports an update exactly when an identifier is present, the
    # effective straight-to-insertion decision is NOT taken, and the update
    # primitive matched a stored row. In particular, when the identifier was
    # caller-supplied, an identifier is present, and the caller did not force an
    # insertion, the short-cut is suppressed, so an existing row IS updated
    # rather than re-inserted.
    Ensures(Result() == (
        pk_set
        and not forces_insert(pk_explicit, force_insert, adding, pk_has_default)
        and update_matched_row()))
    # When the identifier was caller-supplied, an identifier-bearing instance
    # that the caller did not force to insert MUST be offered to the update
    # primitive: the short-cut is suppressed, so the reported outcome is exactly
    # that primitive's result (an existing row is updated, not blindly
    # re-inserted).
    Ensures(Implies(pk_explicit and pk_set and not force_insert,
                    Result() == update_matched_row()))
    # post-conditions-end
    # impl-start
    force_insert_eff = force_insert
    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
        force_insert_eff = True
    updated = False
    if pk_set and not force_insert_eff:
        updated = update_matched_row()
    return updated
    # impl-end
