"""Twin-artifact model for django__django-11820.

Behaviour under specification (stated as desired behaviour, not as an edit):

A model declares an ordering by a sequence of lookup paths.  A *related* path
is a chain of names joined by the lookup separator, e.g. ``a __ b __ c``.  The
validator walks the chain one name at a time, starting from the declaring
model, and decides whether the whole path is a legitimate ordering target (no
error) or refers to something that does not exist (one validation error).

The walk maintains a "current model" and the "last field that was found":

  * Resolving a name against the current model yields one of three outcomes:
    the name is a RELATION field (the walk advances to the related model), the
    name is an ordinary NON-RELATION field, or the name resolves to nothing on
    the current model.

  * The primary-key alias.  The literal name ``pk`` is an alias that always
    designates the current model's primary-key field (it is NOT an ordinary
    field that name-resolution would find).  So a ``pk`` step is resolved
    against the model's primary key directly, yielding that field's
    relation/non-relation kind.

  * After a name resolves to a NON-RELATION field there is no model to continue
    from: the current model becomes "none".  Any subsequent name therefore
    resolves to nothing (there is nothing to resolve it against).

  * When a name resolves to nothing, the path is in error UNLESS the last field
    that was found admits that trailing name as a registered transform (a
    registered lookup such as ``__lower``), in which case the trailing name is
    a transform of that field and the path is acceptable.

The desired result is the single boolean: does walking this related path
produce a validation error.

The model graph (which name is which kind of field on which model, the related
target, the primary-key kind/target, and which trailing transforms a field
admits) is the unchanged name-resolution machinery, modelled as referentially
transparent pure functions over integer model/name identifiers.  Names are
modelled as ``int`` identifiers (Nagini bans ``str`` indexing); the reserved
identifier ``0`` denotes the literal alias name ``pk``.  The path is a
``List[int]`` of name identifiers; the specification is carried by ``PSeq[int]``
via ``ToSeq``.

The walk itself is modelled deeply as a front-recursive fold (`walk_err`) over
the path, so a single unfold is available per loop step.

Validation is a bounded computation: the walk visits each name of the finite
path once and MUST return its verdict (a total-correctness obligation, carried
as MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postcondition only vacuously and would never
deliver a verdict to the caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def resolve_kind(model: int, name: int) -> int:
    """Outcome of resolving an ordinary (non-alias) name against a model:
    0 = resolves to nothing, 1 = a relation field, 2 = a non-relation field.
    Referentially transparent (the unchanged name-resolution machinery).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)


@Pure
@ContractOnly
def relation_target(model: int, name: int) -> int:
    """The model reached after stepping through a relation field `name` of
    `model` (the unchanged related-model lookup)."""
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def pk_kind(model: int) -> int:
    """Kind of a model's primary-key field: 1 = relation, 2 = non-relation.
    A model always has a primary key, so this never resolves to nothing."""
    Ensures(Result() == 1 or Result() == 2)


@Pure
@ContractOnly
def pk_target(model: int) -> int:
    """The model reached after stepping through a relational primary key."""
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def transform_present(field_model: int, field_name: int, name: int) -> bool:
    """Whether the field identified by (field_model, field_name) admits `name`
    as a registered trailing transform (the unchanged transform lookup)."""
# axioms-end


# pure-start
@Pure
def walk_err(path: PSeq[int], model: int, fld_model: int, fld_name: int) -> bool:
    """Does walking the remaining `path` from `model`, having last found the
    field (fld_model, fld_name) (with fld_name == -1 meaning "no field found
    yet"), produce a validation error.  Front-recursive: peels one name.

    Reserved name identifier 0 is the primary-key alias ``pk``; model identifier
    -1 is the "none" current model (nothing left to resolve against)."""
    if len(path) == 0:
        return False
    name = path[0]
    rest = path.drop(1)
    if model == -1:
        # Nothing to resolve the name against: in error unless the last field
        # that was found admits the name as a registered transform.
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, -1, fld_model, fld_name)
    if name == 0:
        # The ``pk`` alias resolves to the model's primary-key field directly.
        if pk_kind(model) == 1:
            return walk_err(rest, pk_target(model), model, name)
        return walk_err(rest, -1, model, name)
    k = resolve_kind(model, name)
    if k == 0:
        # Resolves to nothing: error unless rescued by a transform on the last
        # field that was found (the current name was not assigned as a field).
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, model, fld_model, fld_name)
    if k == 1:
        return walk_err(rest, relation_target(model, name), model, name)
    # k == 2: ordinary non-relation field; no model to continue from.
    return walk_err(rest, -1, model, name)
# pure-end


def check_related_path(path: List[int], root: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(root >= 0)
    # TERMINATION: the validator must actually ANSWER — walking a finite
    # related path is a bounded computation (one step per name). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before returning)
    # satisfies the value postcondition vacuously; the real validator always
    # returns its per-path verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The result is exactly the deep walk: an error iff walking the related
    # path from the root model produces one.
    Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
    # post-conditions-end
    # impl-start
    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
    n = len(path)
    i = 0
    acc = False
    model = root
    fld_model = root
    fld_name = -1
    Assert(ToSeq(path).drop(0) == ToSeq(path))
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(path))
        Invariant(whole == walk_err(ToSeq(path), root, root, -1))
        Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(path).drop(i)[0] == path[i])
        Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
        name = path[i]
        if model == -1:
            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                acc = True
            # model stays -1; fld unchanged
        elif name == 0:
            # pk alias: the field is found on the current model.
            fld_model = model
            fld_name = name
            if pk_kind(model) == 1:
                model = pk_target(model)
            else:
                model = -1
        else:
            k = resolve_kind(model, name)
            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                fld_model = model
                fld_name = name
                # model UNCHANGED after a non-relation field
        i = i + 1
    Assert(len(ToSeq(path).drop(n)) == 0)
    Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
    return acc
    # impl-end
