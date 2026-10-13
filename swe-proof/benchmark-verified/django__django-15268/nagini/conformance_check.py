#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15268 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the single `Assert(...)` in `pair_collapses_through` is a
proof annotation, dropped; everything else is unchanged Python). The @Pure
helpers (`is_constraint_alteration`, `touches_model`,
`base_commutes_through`, `alter_commutes_through`) are copied over as plain
functions. No PSeq / @ContractOnly / axioms in this bundle, so no shims and
no real-callee axiom calls inside the shadow.

ORACLE: the REAL patched repo decision the model models per mapping.md —
`AlterTogetherOptionOperation.can_reduce_through(self, operation, app_label)`
in `django/db/migrations/operations/models.py` (for `commutes_through`),
cross-checked against the boolean path of `ModelOperation.reduce` whenever
`reduce` returns a bool; and the optimizer's left-reduction guard
`between.reduce(second, app_label) is True` (for `pair_collapses_through`).
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched module imports directly.

Type bridge (mapping.md section 2):
  * `kind: int` <-> the operation's concrete class. 0 <-> AlterUniqueTogether,
    1 <-> AlterIndexTogether (the two constraint families, distinct
    option_name); any negative tag <-> a model-scoped operation that is NOT
    an AlterTogetherOptionOperation. For negative tags this script
    instantiates AlterModelTable or AlterModelOptions (chosen by parity of
    the tag): mapping.md scopes `touches_model` to the operations whose
    neighbour predicate is the exact name-equality comparison, and both of
    these inherit precisely that comparison (operations that conservatively
    report always-touching are outside the modeled bijection).
  * `model_id: int` <-> the target model name; distinct ints map to distinct
    lowercase names ("m<i>" / "mneg<i>"), so `op_model == name` <->
    `name.lower() == self.name_lower` exactly.
  * `app_label` is unused by these operations; a fixed label is passed.
  * results are plain bools on both sides; compared with `==` after a bool
    type check.

Input domain (Requires-satisfying under the bijection):
  * commutes_through: self.kind in {0, 1} (the modeled operation is a
    constraint-altering operation, and the repo has exactly two families);
    other.kind in {0, 1} or negative; model_ids arbitrary ints.
  * pair_collapses_through: first/between/second kinds in {0, 1} with
    first.kind == second.kind; all three model_ids equal.

>= 1e5 Requires-satisfying inputs: exhaustive small-domain boundary sweeps
plus 100000 fuzz cases for commutes_through and 20000 for
pair_collapses_through. Pinned fuzz seed: 15268.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15268
N_FUZZ_CT = 100_000
N_FUZZ_PC = 20_000
APP_LABEL = "app"

# Family tags (model.py constants).
FAMILY_UNIQUE = 0
FAMILY_INDEX = 1


# --- pure helpers from model.py, decorators stripped ---------------------------

def is_constraint_alteration(kind):
    return kind >= 0


def touches_model(op_model, name):
    return op_model == name


def base_commutes_through(self_model, other_kind, other_model):
    return not touches_model(other_model, self_model)


def alter_commutes_through(self_kind, self_model, other_kind, other_model):
    return (
        base_commutes_through(self_model, other_kind, other_model) or
        (is_constraint_alteration(other_kind) and other_kind != self_kind)
    )


# --- the Operation carrier from model.py, contracts stripped --------------------

class Operation:
    def __init__(self, kind, model_id):
        # impl-start (verbatim)
        self.kind = kind          # type: int
        self.model_id = model_id  # type: int
        # impl-end


# --- the impl regions of model.py, verbatim (contract calls stripped) -----------

def commutes_through(self_op, other):
    # impl-start (verbatim)
    if not touches_model(other.model_id, self_op.model_id):
        return True
    return is_constraint_alteration(other.kind) and other.kind != self_op.kind
    # impl-end


def pair_collapses_through(first, between, second):
    # impl-start (verbatim; the proof-only Assert(...) call is stripped)
    res = is_constraint_alteration(second.kind) and \
        second.kind != between.kind
    return res
    # impl-end


# --- bridge: model carrier -> real migration operations -------------------------

def model_name(model_id):
    # distinct ints -> distinct all-lowercase names, so the repo's
    # case-insensitive name comparison is exactly int equality.
    if model_id >= 0:
        return "m%d" % model_id
    return "mneg%d" % (-model_id)


def make_real_op(ops_mod, kind, model_id):
    name = model_name(model_id)
    if kind == FAMILY_UNIQUE:
        return ops_mod.AlterUniqueTogether(name, [("a", "b")])
    if kind == FAMILY_INDEX:
        return ops_mod.AlterIndexTogether(name, [("a", "b")])
    # negative tag: a model-scoped operation of neither constraint family,
    # carrying the plain name-equality neighbour predicate (per mapping.md,
    # the bijection covers exactly these; conservative always-touching
    # operations are outside the modeled domain).
    if kind % 2 == 0:
        return ops_mod.AlterModelOptions(name, {})
    return ops_mod.AlterModelTable(name, "tbl")


# --- differential checks ---------------------------------------------------------

def check_ct(ops_mod, self_kind, self_model, other_kind, other_model):
    """One commutes_through case; return error string on disagreement."""
    shadow_out = commutes_through(Operation(self_kind, self_model),
                                  Operation(other_kind, other_model))
    real_self = make_real_op(ops_mod, self_kind, self_model)
    real_other = make_real_op(ops_mod, other_kind, other_model)
    real_out = real_self.can_reduce_through(real_other, APP_LABEL)
    if not isinstance(real_out, bool) or shadow_out != real_out:
        return ("DISAGREEMENT commutes_through\n"
                "  self=(kind=%r, model=%r) other=(kind=%r, model=%r)\n"
                "  shadow=%r\n  real=%r"
                % (self_kind, self_model, other_kind, other_model,
                   shadow_out, real_out))
    # cross-check: whenever the real reduce returns a bool, it must be the
    # same decision (the boolean path the modeled function feeds).
    red = real_self.reduce(real_other, APP_LABEL)
    if isinstance(red, bool) and red != shadow_out:
        return ("DISAGREEMENT commutes_through (reduce boolean path)\n"
                "  self=(kind=%r, model=%r) other=(kind=%r, model=%r)\n"
                "  shadow=%r\n  real reduce=%r"
                % (self_kind, self_model, other_kind, other_model,
                   shadow_out, red))
    return None


def check_pc(ops_mod, pair_kind, between_kind, model_id):
    """One pair_collapses_through case (preconditions: same-family pair on
    one model, constraint-altering in-between step on the same model)."""
    first = Operation(pair_kind, model_id)
    between = Operation(between_kind, model_id)
    second = Operation(pair_kind, model_id)
    shadow_out = pair_collapses_through(first, between, second)
    real_between = make_real_op(ops_mod, between_kind, model_id)
    real_second = make_real_op(ops_mod, pair_kind, model_id)
    # the optimizer's left-reduction guard for the single in-between step.
    real_out = real_between.reduce(real_second, APP_LABEL) is True
    if shadow_out != real_out:
        return ("DISAGREEMENT pair_collapses_through\n"
                "  pair_kind=%r between_kind=%r model=%r\n"
                "  shadow=%r\n  real=%r"
                % (pair_kind, between_kind, model_id, shadow_out, real_out))
    return None


def boundary_models():
    return [0, 1, 2, -1, -2, 7, 10 ** 6, -(10 ** 6), 2 ** 31, -(2 ** 31)]


def rand_model(rng):
    k = rng.random()
    if k < 0.6:
        return rng.randint(0, 3)            # heavy collision zone
    if k < 0.9:
        return rng.randint(-64, 64)
    return rng.randint(-2 ** 40, 2 ** 40)


def rand_other_kind(rng):
    k = rng.random()
    if k < 0.4:
        return FAMILY_UNIQUE
    if k < 0.8:
        return FAMILY_INDEX
    if k < 0.95:
        return -rng.randint(1, 8)           # small negative tags
    return -rng.randint(9, 2 ** 30)         # large negative tags


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure()
            try:
                django.setup()
            except Exception:
                pass
    except Exception:
        pass
    # REAL patched module: the migration-operation classes whose commute
    # decision the model abstracts.
    from django.db.migrations.operations import models as ops_mod

    checked = 0

    # --- boundary sweeps: exhaustive over small kind x model grids ---
    kinds_self = (FAMILY_UNIQUE, FAMILY_INDEX)
    kinds_other = (FAMILY_UNIQUE, FAMILY_INDEX, -1, -2, -7, -(2 ** 20))
    for sk in kinds_self:
        for sm in boundary_models():
            for ok in kinds_other:
                for om in boundary_models():
                    err = check_ct(ops_mod, sk, sm, ok, om)
                    if err:
                        print(err)
                        return 1
                    checked += 1
    for pk in kinds_self:
        for bk in kinds_self:
            for m in boundary_models():
                err = check_pc(ops_mod, pk, bk, m)
                if err:
                    print(err)
                    return 1
                checked += 1

    # --- fuzz ---
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_CT):
        err = check_ct(ops_mod,
                       rng.choice(kinds_self), rand_model(rng),
                       rand_other_kind(rng), rand_model(rng))
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FUZZ_PC):
        err = check_pc(ops_mod, rng.choice(kinds_self),
                       rng.choice(kinds_self), rand_model(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched commute decision on %d "
          "inputs (boundary sweeps + %d fuzz, seed %d)."
          % (checked, N_FUZZ_CT + N_FUZZ_PC, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
