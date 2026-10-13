#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16901 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`oddParityReduce`, routed through the pure model `trueCount` /
              `parityOdd`) transliterated to Python over the real repo carrier
              (`children : List Bool` ↔ the per-row truth values of the XOR
              node's operands, mapping.md §2). There are NO A-tagged callees in
              the impl region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched n-ary XOR rewrite in
              `WhereNode.as_sql`, exercised END-TO-END by running the real ORM
              against an in-memory SQLite database. SQLite reports
              `supports_logical_xor = False` (django/db/backends/base/features.py),
              so a `Q(...) ^ Q(...) ^ ...` filter takes EXACTLY the rewritten
              branch and the generated SQL is what the patch produces; we observe
              which rows the resulting WHERE clause selects (the only consumer-
              visible behaviour of the rewrite). The harness applies patch.diff
              at base_commit before this runs (G-RESOLVE).

Bridge (mapping.md §2): a fuzzed scenario is (k operand-columns, one row's
0/1 assignment over them). It is realised BOTH as a Lean-side `List Bool` (for
the shadow) and as a real database row + a k-ary `Q(c0=1) ^ … ^ Q(c{k-1}=1)`
filter (for the oracle). A single query covers every assignment at once: we
insert one row per bit-pattern and ask which rows the filter returns. Shadow and
oracle must agree on membership for every (query, row). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16901
N_FUZZ = 100_000          # number of (query, row) membership comparisons
MAXN = 7                  # operand columns c0..c{MAXN-1}; 2^MAXN rows inserted once


# --- Django bootstrap (in-memory SQLite: no native XOR -> the rewrite branch) -

def _bootstrap():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
            SECRET_KEY="conf-check-16901",
        )
    django.setup()


_bootstrap()

from django.db import connection, models  # noqa: E402


# --- the dynamic model: MAXN integer operand columns -------------------------
# Homed under the already-installed `contenttypes` app so the model has a
# registry home without a synthetic filesystem app (mapping.md is backend-only).

def _build_model():
    attrs = {"__module__": "django.contrib.contenttypes.models",
             "Meta": type("Meta", (), {"app_label": "contenttypes"})}
    for j in range(MAXN):
        attrs["c%d" % j] = models.IntegerField()
    return type("XorRow", (models.Model,), attrs)


XorRow = _build_model()


def _create_table_and_rows():
    """Create the table and insert one row per bit-pattern over MAXN columns.
    Row pk = pattern + 1; column cj = bit j of the pattern (0/1)."""
    with connection.schema_editor() as editor:
        editor.create_model(XorRow)
    objs = []
    for pattern in range(1 << MAXN):
        kwargs = {"id": pattern + 1}
        for j in range(MAXN):
            kwargs["c%d" % j] = (pattern >> j) & 1
        objs.append(XorRow(**kwargs))
    XorRow.objects.bulk_create(objs)


# --- the R/I shadow: trueCount / parityOdd transliterated --------------------

def shadow_parity(bits):
    """parityOdd (Solution.lean pure region): true iff an odd number of the
    selected operands hold. `bits` is the row's `List Bool` over the chosen
    columns (mapping.md §2)."""
    return (sum(1 for b in bits if b) % 2) == 1


# --- the oracle: the real gold-patched XOR rewrite, end-to-end via SQLite ----

from django.db.models import Q  # noqa: E402


def oracle_matches(columns):
    """Build `Q(c{columns[0]}=1) ^ … ^ Q(c{columns[k-1]}=1)`, run it against the
    real DB (SQLite -> the patched n-ary XOR fallback SQL), and return the set of
    matching row patterns. The membership of each row is the consumer-visible
    behaviour of the rewrite."""
    q = None
    for col in columns:
        leaf = Q(**{"c%d" % col: 1})
        q = leaf if q is None else (q ^ leaf)
    pks = XorRow.objects.filter(q).values_list("id", flat=True)
    return {pk - 1 for pk in pks}     # back to bit-patterns


def row_bits(pattern, columns):
    """The row's truth values over the chosen operand columns (the `List Bool`)."""
    return [bool((pattern >> col) & 1) for col in columns]


# --- fuzz: queries of varying arity; each covers all 2^MAXN rows -------------

def column_choices(rng):
    """Yield operand-column tuples. Boundary: arity 1..MAXN over the leading
    columns (the exactly-one vs parity divergence first appears at arity 3);
    then randomized distinct-column subsets of arity 1..MAXN."""
    for k in range(1, MAXN + 1):
        yield tuple(range(k))                      # leading-column k-ary XOR
    # the F2P shape: a 5-ary XOR (the reported failing case)
    yield (0, 1, 2, 3, 4)
    while True:
        k = rng.randint(1, MAXN)
        yield tuple(rng.sample(range(MAXN), k))


def main():
    _create_table_and_rows()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    patterns = range(1 << MAXN)

    for columns in column_choices(rng):
        matched = oracle_matches(columns)
        for pattern in patterns:
            count += 1
            bits = row_bits(pattern, columns)
            shadow = shadow_parity(bits)
            oracle = pattern in matched
            if shadow != oracle:
                disagreements.append((columns, bits, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if disagreements or count >= N_FUZZ:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for columns, bits, sh, orc in disagreements:
            print("  columns=%r bits=%r shadow=%r oracle=%r"
                  % (columns, bits, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of oddParityReduce agrees with patch.diff "
          "behaviour (real patched XOR rewrite over SQLite) on %d (query,row) "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
