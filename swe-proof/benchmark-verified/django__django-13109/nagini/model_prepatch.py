"""Twin-artifact model for django__django-13109.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that points at rows of another model validates a candidate
  reference value by asking whether some row of that other model actually
  carries the referenced key. The other model exposes two row collections:

    * the COMPLETE collection of every stored row (its unfiltered set), and
    * a curated, possibly-narrower collection that ordinary application code
      sees by default, which may hide some genuinely-stored rows behind an
      extra standing filter (for example rows flagged as retired).

  The behaviour pinned here is which collection the reference check must
  consult. The check exists to confirm the referenced row is genuinely STORED,
  so that a later write cannot dangle. It must therefore consult the COMPLETE
  collection: a reference to a row that is stored — even one the curated default
  collection hides — is a valid reference and must pass. The curated narrowing
  is a presentation concern, not an integrity concern, so it must not influence
  whether a reference to a stored row is accepted.

  Concretely: the check succeeds (returns normally) exactly when the COMPLETE
  collection contains the referenced key AND that key satisfies the additional
  per-field choice restriction that the check always applies; otherwise it
  rejects the reference by raising. The curated default collection does NOT
  enter this decision.

Row keys are modelled as integers; a collection of rows is a `List[int]` of the
keys present. The additional per-field choice restriction (an unchanged callee
the check always applies) is axiomatised as a pure predicate on the key. The
rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

The check must ANSWER (return or raise): Nagini verifies partial correctness by
default, so without an explicit obligation a non-terminating implementation
(bare self-recursion, or an endless loop) satisfies every `Ensures`/`Exsures`
vacuously while never delivering a decision. The real check is one bounded
lookup that always completes; the obligation is carried as `MustTerminate` in
the precondition (measure 2 — the impl may call the pure helpers but may NOT
re-invoke itself) and consumed by the scan loop with the strictly decreasing,
bounded-below measure `i + 1`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ReferenceInvalid(Exception):
    """Signals a rejected reference (no genuinely-stored, choice-permitted row
    carries the referenced key). Stands in for the `ValidationError` the desired
    behaviour raises; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def choice_permitted(key: int) -> bool:
    """The additional per-field choice restriction the reference check always
    applies, independent of which row collection is consulted (the unchanged
    `complex_filter(get_limit_choices_to())` narrowing). A deterministic
    predicate of the key alone. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def present(key: int, rows: PSeq[int]) -> bool:
    """Whether some row in `rows` carries `key`. Front-recursive over the
    sequence so a single membership unfold is available per loop step."""
    if len(rows) == 0:
        return False
    return rows[0] == key or present(key, rows.drop(1))


@Pure
def reference_holds(key: int, complete_rows: PSeq[int]) -> bool:
    """The reference is valid exactly when the COMPLETE collection holds a row
    carrying `key` AND that key satisfies the choice restriction."""
    return present(key, complete_rows) and choice_permitted(key)
# pure-end


def validate_reference(value: int,
                       complete_rows: List[int],
                       curated_rows: List[int]) -> None:
    # pre-conditions-start
    # Both collections are read-only here (the check never mutates either);
    # fractional permission, required and ensured, so no caller can satisfy a
    # postcondition vacuously by overwriting an input.
    Requires(Acc(list_pred(complete_rows), 1 / 2))
    Requires(Acc(list_pred(curated_rows), 1 / 2))
    # Total-correctness obligation: the check must ANSWER (return normally or
    # raise). The real operation is one bounded queryset probe that always
    # completes; without this a diverging impl (bare self-recursion, endless
    # loop) satisfies the Ensures/Exsures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(complete_rows), 1 / 2))
    Ensures(Acc(list_pred(curated_rows), 1 / 2))
    # Returns normally exactly when the COMPLETE collection holds the referenced
    # key and that key is choice-permitted. The curated collection is absent
    # from this condition: a reference to a stored row the curated view hides
    # still passes.
    Ensures(reference_holds(value, ToSeq(complete_rows)))
    # Rejects (raises) exactly when no genuinely-stored, choice-permitted row
    # carries the key — again decided over the COMPLETE collection only.
    Exsures(ReferenceInvalid,
            Acc(list_pred(complete_rows), 1 / 2)
            and Acc(list_pred(curated_rows), 1 / 2)
            and (not reference_holds(value, ToSeq(complete_rows))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the reference check consults the CURATED
    # default collection rather than the complete one. A key that names a
    # genuinely-stored, choice-permitted row hidden by the curated narrowing is
    # then rejected, contradicting the postcondition (which decides over the
    # complete collection). Scan back-to-front to match the front-recursive
    # `present`.
    found = False  # type: bool
    i = len(curated_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(curated_rows), 1 / 2))
        Invariant(0 <= i and i <= len(curated_rows))
        Invariant(found == present(value, ToSeq(curated_rows).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(curated_rows).drop(i - 1)[0] == curated_rows[i - 1])
        Assert(ToSeq(curated_rows).drop(i - 1).drop(1) == ToSeq(curated_rows).drop(i))
        if curated_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
    # impl-end
