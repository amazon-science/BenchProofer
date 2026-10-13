#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of the three modeled decisions
against an independent reconstruction of the post-patch behaviour.

The impl regions are all R/I (no A-tagged op), so this runs a real fuzz. For
each decision the shadow reproduces the Lean impl op-for-op, and `patched`
reconstructs the post-patch Python semantics independently:

  A. fkColumnParams — a referencing column's params: type/check are its own,
     collation is the referenced column's collation
     (`target_db_parameters.get("collation")`).
  B. rebuildIncomingFks — the `drop_foreign_keys` predicate, with the
     collation-aware disjunct in the last conjunct.
  C. relatedColumnAlterKind — collation branch iff the two collations differ,
     else the type branch.

`None` models a missing collation; collation values are drawn from a small pool
(incl. the F2P non-default collation shape). Zero disagreements required over
>= 10^5 fuzzed inputs. stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 15629          # pinned in mapping.md
N = 120_000           # >= 10^5

COLLATIONS = [None, "utf8_bin", "utf8_general_ci", "C", "en_US", ""]
TYPES = ["varchar(22)", "varchar(10)", "integer", "bigint", "varchar(255)"]
CHECKS = [None, "", "value > 0", "len <= 10"]


# ---- A: fkColumnParams ----
def shadow_fk(fk_type, fk_check, target_params):
    params = {"colType": fk_type, "checkExpr": fk_check, "collation": None}
    params = {**params, "collation": target_params.get("collation")}
    return params


def patched_fk(fk_type, fk_check, target_params):
    return {
        "colType": fk_type,
        "checkExpr": fk_check,
        "collation": target_params.get("collation"),
    }


# ---- B: rebuildIncomingFks ----
def shadow_rebuild(supports_fk, old_pk, new_pk, old_uniq, new_uniq,
                   old_type, new_type, old_coll, new_coll):
    decision = supports_fk
    decision = decision and ((old_pk and new_pk) or (old_uniq and new_uniq))
    decision = decision and ((old_type != new_type) or (old_coll != new_coll))
    return decision


def patched_rebuild(supports_fk, old_pk, new_pk, old_uniq, new_uniq,
                    old_type, new_type, old_coll, new_coll):
    return (
        supports_fk
        and ((old_pk and new_pk) or (old_uniq and new_uniq))
        and ((old_type != new_type) or (old_coll != new_coll))
    )


# ---- C: relatedColumnAlterKind ----
def shadow_kind(old_rel_coll, rel_coll):
    if old_rel_coll != rel_coll:
        return "collationAlter"
    return "typeAlter"


def patched_kind(old_rel_coll, rel_coll):
    return "collationAlter" if old_rel_coll != rel_coll else "typeAlter"


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the F2P collation-change shape.
    fixed_fk = [
        ("varchar(22)", None, {"collation": "utf8_bin"}),
        ("varchar(10)", None, {"collation": None}),
        ("integer", "v>0", {"collation": ""}),
    ]
    for fk_type, fk_check, tp in fixed_fk:
        if shadow_fk(fk_type, fk_check, tp) != patched_fk(fk_type, fk_check, tp):
            disagreements += 1
            examples.append(("A", (fk_type, fk_check, tp)))

    n_each = N // 3
    for _ in range(n_each):
        fk_type = rng.choice(TYPES)
        fk_check = rng.choice(CHECKS)
        tp = {"colType": rng.choice(TYPES), "checkExpr": rng.choice(CHECKS),
              "collation": rng.choice(COLLATIONS)}
        if shadow_fk(fk_type, fk_check, tp) != patched_fk(fk_type, fk_check, tp):
            disagreements += 1
            if len(examples) < 10:
                examples.append(("A", (fk_type, fk_check, tp)))

    for _ in range(n_each):
        args = (
            rng.random() < 0.5, rng.random() < 0.5, rng.random() < 0.5,
            rng.random() < 0.5, rng.random() < 0.5,
            rng.choice(TYPES), rng.choice(TYPES),
            rng.choice(COLLATIONS), rng.choice(COLLATIONS),
        )
        if shadow_rebuild(*args) != patched_rebuild(*args):
            disagreements += 1
            if len(examples) < 10:
                examples.append(("B", args))

    for _ in range(n_each):
        a, b = rng.choice(COLLATIONS), rng.choice(COLLATIONS)
        if shadow_kind(a, b) != patched_kind(a, b):
            disagreements += 1
            if len(examples) < 10:
                examples.append(("C", (a, b)))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for tag, inp in examples:
            print(f"  decision={tag} in={inp!r}")
        return 1

    print(f"G-CONF OK: ~{N} inputs across 3 decisions, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
