#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15368 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real repo values: `wrapPlan attrs`, i.e. per
              assignment value the bit `! isDbExpr` where
              `isDbExpr = hasattr(value, 'resolve_expression')` (the post-patch
              predicate; mapping.md §2). There are NO A-tagged callees in the
              impl region, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `QuerySet.bulk_update`,
              run end-to-end against an in-memory SQLite database (the harness
              applies patch.diff before this runs). The observable per element is
              whether the value was applied DIRECTLY (a database-side expression
              resolved on the DB side — the row's stored value becomes the
              resolved source column) or was WRAPPED as a literal (stored as its
              literal/string form). A per-row distinct sentinel in the source
              column makes "resolved on DB side" vs "stored literally"
              unambiguous.

They must agree per element: SHADOW's wrap bit == ORACLE's observed wrap bit.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
django.setup()

from django.db import connection, models  # noqa: E402
from django.db.models import F, Value  # noqa: E402

SEED = 15368
N_FUZZ = 100_000
BATCH = 20


class Row(models.Model):
    target = models.CharField(max_length=120)
    src = models.CharField(max_length=120)

    class Meta:
        app_label = "auth"


def setup_db():
    with connection.schema_editor() as se:
        se.create_model(Row)


# --- the R/I shadow: wrapPlan transliterated ---------------------------------

def shadow_wrap_bit(value):
    """wrapPlan's per-element rule on a real assignment value: wrap-as-literal
    iff the value is NOT a database-side expression (mapping.md §2)."""
    is_db_expr = hasattr(value, "resolve_expression")
    return not is_db_expr


# --- the ORACLE: real patched bulk_update, observed end-to-end ---------------

def oracle_wrap_bits(values):
    """Run the REAL patched bulk_update over one batch of assignment values and
    return, per element, whether the value was WRAPPED as a literal (True) vs
    applied DIRECTLY as a resolved DB-side expression (False).

    Each row gets a distinct sentinel in `src`. A db-side expression `F('src')`
    applied directly resolves the row to its own sentinel; a value wrapped in
    `Value(...)` stores the literal form, which never equals the sentinel."""
    Row.objects.all().delete()
    objs = []
    sentinels = []
    for k, _ in enumerate(values):
        sent = "SENTINEL_%d_zzq" % k
        sentinels.append(sent)
        objs.append(Row.objects.create(target="init_%d" % k, src=sent))
    for obj, value in zip(objs, values):
        obj.target = value
    Row.objects.bulk_update(objs, ["target"])
    bits = []
    for obj, sent in zip(objs, sentinels):
        obj.refresh_from_db()
        # Applied directly (db-side expr F('src') resolved) => stored == sentinel
        # => NOT wrapped. Otherwise the value was stored as its literal form.
        wrapped = (obj.target != sent)
        bits.append(wrapped)
    return bits


def fuzz_values(n, rng):
    """Yield batches (lists) of assignment values mixing db-side expressions
    (F over the source column) and plain literals."""
    # boundary batch first: each kind alone + mixed
    yield [F("src")]
    yield ["hello"]
    yield [F("src"), "hello", 42, F("src")]
    yield ["F(src)", F("src")]   # a plain str that looks like F's repr
    yield []  # empty batch (no-op loop)

    literals = ["test_note", "test_misc", "hello", "", "0", "F(src)",
                "x", "42", "Joe's", "a&b"]
    produced = 0
    while produced < n:
        k = rng.randint(1, BATCH)
        batch = []
        for _ in range(k):
            kind = rng.randint(0, 2)
            if kind == 0:
                batch.append(F("src"))            # db-side expr -> direct
            elif kind == 1:
                batch.append(rng.choice(literals))  # plain str -> wrapped
            else:
                batch.append(rng.randint(-999, 999))  # plain int -> wrapped
        produced += len(batch)
        yield batch


def main():
    setup_db()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for batch in fuzz_values(N_FUZZ, rng):
        if not batch:
            continue
        shadow = [shadow_wrap_bit(v) for v in batch]
        oracle = oracle_wrap_bits(batch)
        for idx, (sh, orc) in enumerate(zip(shadow, oracle)):
            count += 1
            if sh != orc:
                disagreements.append((repr(batch[idx]), sh, orc))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d elements:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  value=%s shadow_wrap=%r oracle_wrap=%r" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of routeOperands (wrapPlan = `! isDbExpr`) "
          "agrees with patch.diff behaviour on %d elements (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
