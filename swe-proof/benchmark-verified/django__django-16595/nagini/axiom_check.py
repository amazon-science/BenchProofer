#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16595.

This bundle has NO `@ContractOnly` axioms: the changed behaviour
(`AlterField.reduce`) is pure control flow over operation kinds and a
same-field test, modeled DEEPLY in model.py. G-AX therefore performs a
*structural* soundness check of the type-refinement (refinement.md steps 2-7):

  * a faithful, dependency-free transcription of the REAL repo logic
    (`AlterField.reduce` and `FieldOperation.is_same_field_operation`,
    `django/db/migrations/operations/fields.py`, plus the fall-through it
    delegates to) is exercised on boundary + randomized operation pairs. That
    fall-through is `FieldOperation.reduce` (`fields.py:69-72`) -- AlterField's
    MRO is [AlterField, FieldOperation, Operation, object], so `super()` binds
    FieldOperation, NOT Operation -- and it post-processes `Operation.reduce`'s
    bool (`base.py:129-139`) with `... or not operation.references_field(...)`.
    Both are transcribed, so the non-list answer here is the real FOUR-state's
    True or False and not a single merged tag;
  * the model's `reduce` semantics (model.py impl region, encoded below) is
    asserted to produce the same RESULT SHAPE ([op] vs [self] vs [op, alter] vs
    a reordering verdict, whose VALUE is compared) and the same identities
    (which operation survives) on every input;
  * the PRE-patch guard (`isinstance(operation, RemoveField)` only) is confirmed
    to genuinely DIFFER from the post-patch guard on the discriminating
    alter-then-alter case, so model_prepatch.py's failure is the real bug.

Imports nothing repo-specific (Django's real classes require the full app
registry to instantiate); the repo `reduce` control flow is transcribed
verbatim from fields.py. Exit 0 iff every obligation holds.
"""
import random
import sys

# Operation-kind tags, identical to model.py.
KIND_OTHER = 0
KIND_ALTER = 1
KIND_REMOVE = 2
KIND_RENAME = 3


class Op:
    """Minimal stand-in carrying exactly the attributes the reduce chain reads
    (fields.py's isinstance/name/db_column reads, plus base.py's `elidable`)."""
    def __init__(self, kind, model_name_lower, name_lower,
                 new_name_lower=-1, has_explicit_column=False,
                 elidable=False):
        self.kind = kind
        self.model_name_lower = model_name_lower
        self.name_lower = name_lower
        self.new_name_lower = new_name_lower
        self.has_explicit_column = has_explicit_column
        # Operation.elidable (base.py:32) is a class attribute defaulting to
        # False, overridden per-operation; the chain reads it on BOTH operands.
        self.elidable = elidable
        # Whether the later operand references the altered field is NOT stored
        # here: `references_field(model_name, name, app_label)` is a QUERY over
        # the pair (fields.py:43-65) and no operation carries its answer as
        # state, so it is threaded as an argument (`refs`) to the reductions
        # below, exactly as FieldOperation.reduce (fields.py:69-72) asks it.


def is_same_field(this, other):
    # FieldOperation.is_same_field_operation (fields.py:25-29): same model AND
    # same field name (lower-cased).
    return (this.model_name_lower == other.model_name_lower
            and this.name_lower == other.name_lower)


# ---- REAL repo logic (transcribed verbatim from fields.py @ base_commit) -----

def real_reduce_postpatch(this, operation, refs):
    """AlterField.reduce after the gold patch (fields.py:249-267, patched).
    Returns a list when it collapses, else whatever super().reduce yields."""
    if operation.kind in (KIND_ALTER, KIND_REMOVE) and is_same_field(this, operation):
        return [operation]
    elif (operation.kind == KIND_RENAME and is_same_field(this, operation)
          and not operation_db_column_is_none_proxy(this)):
        return [operation, Op(KIND_ALTER, this.model_name_lower,
                              operation.new_name_lower, operation.new_name_lower)]
    return _super_reduce(this, operation, refs)


def real_reduce_prepatch(this, operation, refs):
    """AlterField.reduce BEFORE the gold patch (only RemoveField collapses)."""
    if operation.kind == KIND_REMOVE and is_same_field(this, operation):
        return [operation]
    elif (operation.kind == KIND_RENAME and is_same_field(this, operation)
          and not operation_db_column_is_none_proxy(this)):
        return [operation, Op(KIND_ALTER, this.model_name_lower,
                              operation.new_name_lower, operation.new_name_lower)]
    return _super_reduce(this, operation, refs)


def operation_db_column_is_none_proxy(this):
    # `self.field.db_column is None` ↔ `not has_explicit_column` (mapping.md §1).
    return this.has_explicit_column


def _operation_reduce(this, operation):
    """Operation.reduce (base.py:129-139), transcribed verbatim:

        if self.elidable:        return [operation]
        elif operation.elidable: return [self]
        return False
    """
    if this.elidable:
        return [operation]
    elif operation.elidable:
        return [this]
    return False


def _super_reduce(this, operation, refs):
    """The REAL target of `super().reduce(...)` from AlterField.reduce.

    AlterField.__mro__ is [AlterField, FieldOperation, Operation, object], so
    super() binds `FieldOperation.reduce` (fields.py:69-72), transcribed
    verbatim:

        def reduce(self, operation, app_label):
            return super().reduce(operation, app_label) or not \
                operation.references_field(self.model_name, self.name, app_label)

    So the fall-through is a FOUR-state, not a tri-state: the two LIST arms of
    Operation.reduce pass straight through (a non-empty list is truthy), and
    the neither-elidable case yields `False or not references_field(...)` --
    i.e. TRUE when the later step does not reference the altered field and
    FALSE when it does. Both bools are reachable and the optimizer reads the
    difference (optimizer.py:46-47 keeps right-reduction alive only on True;
    optimizer.py:50 licenses a left reduction only when every in-between
    operation answers exactly True). Two earlier revisions of this check got
    this arm wrong: one hard-coded `return True`, and one stopped at
    Operation.reduce and returned a single merged `False`, which asserted a
    property the real chain does not have and blinded the check on exactly the
    axis the model had to get right.
    """
    base = _operation_reduce(this, operation)
    if isinstance(base, list):
        return base
    return not refs


# ---- model.py reduce semantics (impl region encoded as result SHAPE) ---------

def model_reduce_shape(this, operation, refs):
    """Returns ('flag', verdict) | ('one', survivor) | ('two', op) — the model's
    Tuple[Optional[List[Operation]], bool] result, abstracted to shape +
    identities. The 'one' tag carries WHICH operation survived, so the
    fall-through's [operation] and [self] arms are distinguished rather than
    merged; the 'flag' tag carries the reordering verdict's VALUE, so the two
    not-combined answers are distinguished too."""
    if (operation.kind in (KIND_ALTER, KIND_REMOVE)) and is_same_field(this, operation):
        return ('one', operation)
    elif (operation.kind == KIND_RENAME and is_same_field(this, operation)
          and not this.has_explicit_column):
        return ('two', operation)
    elif this.elidable:
        return ('one', operation)
    elif operation.elidable:
        return ('one', this)
    return ('flag', not refs)


def repo_result_shape(res, operation):
    if isinstance(res, list):
        if len(res) == 1:
            return ('one', res[0])
        if len(res) == 2:
            return ('two', res[0])
        return ('list', None)
    return ('flag', bool(res))


# ---- the checks --------------------------------------------------------------

def check_model_matches_repo(this, operation, refs):
    """Model's reduce shape == post-patch real reduce shape (R faithfulness).

    `refs` is the pair-level answer to whether the later operand references the
    altered field, supplied identically to both sides."""
    repo = repo_result_shape(real_reduce_postpatch(this, operation, refs),
                             operation)
    mod = model_reduce_shape(this, operation, refs)
    # shape labels agree
    assert repo[0] == mod[0], (
        "model/repo shape mismatch on (this=%s, op=%s): repo=%r model=%r"
        % (vars(this), vars(operation), repo, mod))
    # the surviving element agrees BY IDENTITY. For the collapse and
    # carry-across arms that survivor is `operation`; for the fall-through's
    # later-step-elidable arm it is `this`. Comparing identities rather than
    # shapes is what catches an impl that elides the wrong side.
    if mod[0] == 'flag':
        assert mod[1] == repo[1], (
            "reordering-verdict mismatch on (this=%s, op=%s): repo=%r model=%r"
            % (vars(this), vars(operation), repo, mod))
    if mod[0] in ('one', 'two'):
        assert mod[1] is repo[1], (
            "surviving-operation identity mismatch: repo=%r model=%r "
            "(this=%s, op=%s)" % (repo, mod, vars(this), vars(operation)))
        expected = this if (mod[0] == 'one' and not this.elidable
                            and operation.elidable
                            and not _joined_by_field_rule(this, operation)) \
            else operation
        assert mod[1] is expected, (
            "wrong operation survived: repo=%r model=%r" % (repo, mod))


def _joined_by_field_rule(this, operation):
    """True iff one of AlterField.reduce's own same-field arms resolves the
    pair (so the base-class fall-through is never reached)."""
    if not is_same_field(this, operation):
        return False
    return (operation.kind in (KIND_ALTER, KIND_REMOVE)
            or (operation.kind == KIND_RENAME
                and not this.has_explicit_column))


def check_prepatch_differs_on_alter_alter():
    """The pre-patch guard genuinely fails the alter-then-alter case.

    Both operands are left NON-elidable, which is what makes the differential
    discriminating: with either mark set the base-class fall-through would
    return a list on both sides of the patch and the pre/post difference would
    be masked.
    """
    a1 = Op(KIND_ALTER, 7, 11)
    # same model+field, so it references the altered field by naming it
    a2 = Op(KIND_ALTER, 7, 11)
    assert not a1.elidable and not a2.elidable
    # a same-field follow-up really does reference the altered field, so the
    # pair-level answer is True on both sides of the patch
    post = real_reduce_postpatch(a1, a2, True)
    pre = real_reduce_prepatch(a1, a2, True)
    assert isinstance(post, list) and len(post) == 1 and post[0] is a2, (
        "post-patch must collapse alter-then-alter to [op2]: %r" % (post,))
    assert not isinstance(pre, list), (
        "pre-patch must NOT collapse alter-then-alter (the bug): %r" % (pre,))


def check_fallthrough_fourstate():
    """The fall-through is a FOUR-state: two list arms keyed on the elidable
    marks (the EARLIER step's taking precedence), and — when neither mark is
    set — a reordering verdict that is TRUE when the later step does not
    reference the altered field and FALSE when it does. Both bools reachable."""
    this = Op(KIND_ALTER, 7, 11)
    other = Op(KIND_OTHER, 99, 88)                       # unrelated later step
    assert real_reduce_postpatch(this, other, False) is True, (
        "neither elidable and the later step does NOT reference the altered "
        "field: reordering must be GRANTED")
    toucher = Op(KIND_OTHER, 99, 88)
    assert real_reduce_postpatch(this, toucher, True) is False, (
        "neither elidable and the later step DOES reference the altered field: "
        "reordering must be WITHHELD")
    el_this = Op(KIND_ALTER, 7, 11, elidable=True)
    r = real_reduce_postpatch(el_this, other, False)
    assert isinstance(r, list) and len(r) == 1 and r[0] is other, (
        "an elidable earlier step must leave [operation]: %r" % (r,))
    el_other = Op(KIND_OTHER, 99, 88, elidable=True)
    r = real_reduce_postpatch(this, el_other, False)
    assert isinstance(r, list) and len(r) == 1 and r[0] is this, (
        "an elidable later step must leave [self]: %r" % (r,))
    r = real_reduce_postpatch(el_this, el_other, False)
    assert isinstance(r, list) and len(r) == 1 and r[0] is el_other, (
        "with both elidable the EARLIER step's mark wins: %r" % (r,))
    # A SAME-FIELD pair can still reach the fall-through: the rename arm is
    # rejected when the alteration pins an explicit stored column.
    pinned = Op(KIND_ALTER, 7, 11, has_explicit_column=True)
    el_rename = Op(KIND_RENAME, 7, 11, new_name_lower=3, elidable=True)
    r = real_reduce_postpatch(pinned, el_rename, False)
    assert isinstance(r, list) and len(r) == 1 and r[0] is pinned, (
        "a same-field rename the pinned column rejects falls through to the "
        "elidable arms: %r" % (r,))


def main():
    kinds = [KIND_OTHER, KIND_ALTER, KIND_REMOVE, KIND_RENAME]

    # --- boundary: all kind pairs x same/different field --------------------
    boundary = []
    for k_self in (KIND_ALTER,):                 # `reduce` is AlterField.reduce
        for k_op in kinds:
            for same_model in (True, False):
                for same_name in (True, False):
                    for col in (False, True):
                        # both elidable marks are part of the modeled input
                        for el_self in (False, True):
                            for el_op in (False, True):
                                this = Op(k_self, 1, 2,
                                          has_explicit_column=col,
                                          elidable=el_self)
                                op = Op(k_op,
                                        1 if same_model else 99,
                                        2 if same_name else 88,
                                        new_name_lower=3,
                                        elidable=el_op)
                                # the pair-level fact is an INPUT, so both
                                # answers are generated for every pair
                                for ref in (False, True):
                                    boundary.append((this, op, ref))
    for this, op, ref in boundary:
        check_model_matches_repo(this, op, ref)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(16595)
    for _ in range(50000):
        this = Op(KIND_ALTER,
                  rng.randint(0, 4), rng.randint(0, 4),
                  has_explicit_column=bool(rng.getrandbits(1)),
                  elidable=bool(rng.getrandbits(1)))
        op = Op(rng.choice(kinds),
                rng.randint(0, 4), rng.randint(0, 4),
                new_name_lower=rng.randint(0, 4),
                has_explicit_column=bool(rng.getrandbits(1)),
                elidable=bool(rng.getrandbits(1)))
        ref = bool(rng.getrandbits(1))
        check_model_matches_repo(this, op, ref)

    # --- the discriminating differential ------------------------------------
    check_prepatch_differs_on_alter_alter()
    # --- the fall-through's real four-state ---------------------------------
    check_fallthrough_fourstate()

    print("G-AX OK: model reduce == real AlterField.reduce (post-patch, "
          "including the FieldOperation.reduce fall-through it really "
          "delegates to) on %d boundary + 50000 fuzz operation pairs; the "
          "fall-through's four-state -- both elidable list arms with "
          "earlier-step precedence, and both values of the reordering verdict "
          "-- confirmed; pre-patch guard confirmed to differ on the "
          "alter-then-alter case." % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
