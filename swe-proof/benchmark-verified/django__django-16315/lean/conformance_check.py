#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_renderUpsertClause against the patch.diff behaviour (post-patch
ON CONFLICT / DO UPDATE SET suffix rendering).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: for each conflict-target field render
`quote_name(field.column)`, join with ", "; for each update field render
`q = EXCLUDED.q` with `q = quote_name(field.column)`, join with ", "; wrap in the
literal template "ON CONFLICT(%s) DO UPDATE SET %s".

We diff that against an independent reconstruction of the post-patch rendering:
the unchanged `on_conflict_suffix_sql` UPDATE template fed by the *columns* of the
resolved fields, exactly as the patched `compiler.py` passes
`(f.column for f in self.query.{unique,update}_fields)`. Zero disagreements
required over >= 10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16315          # pinned in mapping.md
N = 120_000           # >= 10^5

# Identifier alphabet: mixed case (so column != name is observable), plus the
# pre-quote char so quote_name's idempotence shortcut is exercised.
IDENT_ALPHABET = list("abcDEFghiRANkOteMz_0129")


def quote_name(name: str) -> str:
    """Reproduces sqlite/postgres quote_name (operations.py:187-190)."""
    if name.startswith('"') and name.endswith('"'):
        return name
    return '"%s"' % name


def gen_ident(rng) -> str:
    n = rng.randint(1, 8)
    s = "".join(rng.choice(IDENT_ALPHABET) for _ in range(n))
    # ~5% of the time hand back an already-quoted identifier.
    if rng.random() < 0.05:
        s = '"%s"' % s
    return s


def gen_field(rng):
    """A resolved FieldRef: (name, column). ~50% have column != name (db_column)."""
    name = gen_ident(rng)
    if rng.random() < 0.5:
        column = gen_ident(rng)        # distinct db_column
    else:
        column = name                  # no db_column -> column == name
    return {"name": name, "column": column}


def shadow(unique_fields, update_fields) -> str:
    """R/I shadow of implementation_renderUpsertClause (keyed by .column)."""
    unique_cols = []
    for f in unique_fields:
        unique_cols.append(quote_name(f["column"]))
    assigns = []
    for f in update_fields:
        q = quote_name(f["column"])
        assigns.append("%s = EXCLUDED.%s" % (q, q))
    return "ON CONFLICT(%s) DO UPDATE SET %s" % (
        ", ".join(unique_cols),
        ", ".join(assigns),
    )


def patched_render(unique_fields, update_fields) -> str:
    """Independent reconstruction: the unchanged on_conflict_suffix_sql UPDATE
    template fed by the resolved fields' .column values, exactly as patched
    compiler.py passes them."""
    unique = [f["column"] for f in unique_fields]          # (f.column for f in ...)
    update = [f["column"] for f in update_fields]
    return "ON CONFLICT(%s) DO UPDATE SET %s" % (
        ", ".join(map(quote_name, unique)),
        ", ".join(
            ["%s = EXCLUDED.%s" % (q, q) for q in map(quote_name, update)]
        ),
    )


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        # F2P: unique=[rank/rAnK], update=[name/oTheRNaMe]
        ([{"name": "rank", "column": "rAnK"}],
         [{"name": "name", "column": "oTheRNaMe"}]),
        # two unique, two update, all column != name
        ([{"name": "a", "column": "A"}, {"name": "b", "column": "B"}],
         [{"name": "c", "column": "C"}, {"name": "d", "column": "D"}]),
        # column == name everywhere (latent-bug regime)
        ([{"name": "x", "column": "x"}], [{"name": "y", "column": "y"}]),
        # pre-quoted identifier
        ([{"name": "q", "column": '"Q"'}], [{"name": "r", "column": "r"}]),
    ]
    cases = list(fixed)
    for _ in range(N):
        nu = rng.randint(0, 6)
        ng = rng.randint(0, 6)
        cases.append(
            ([gen_field(rng) for _ in range(nu)],
             [gen_field(rng) for _ in range(ng)])
        )

    for unique_fields, update_fields in cases:
        got = shadow(unique_fields, update_fields)
        want = patched_render(unique_fields, update_fields)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((unique_fields, update_fields), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
