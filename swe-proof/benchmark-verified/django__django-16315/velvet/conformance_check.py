#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-16315 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled operation (`conflictColumns` + the pure
              `dbColumns` fold over the `Field` structure) transliterated to
              Python over the real repo types, via the mapping.md §2 bijection:
                  Field.column (List Char)  <->  Field.column (str)
                  dbColumns fields          <->  [f.column for f in fields]
              There are NO A-tagged ops (no consumed axioms, no deep-model
              references), so the shadow is pure R/I (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `SQLInsertCompiler.as_sql` passes `(f.column for f in
              self.query.update_fields)` / `(... for f in unique_fields)` to the
              conflict-suffix builder. We reproduce the changed operation with
              REAL Django `Field` objects: each fuzzed (name, db_column) pair is
              turned into a genuine `IntegerField(db_column=...)` whose
              `set_attributes_from_name(name)` computes the real `.column`
              (`get_attname_column`: `column = self.db_column or attname`), then
              we read the real `(f.column for f in fields)` comprehension —
              exactly the patched expression at compiler.py:1728.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: we construct `Field` objects and read attributes only.
stdlib + django. Fuzz seed pinned (mapping.md §4).
"""
import random
import string
import sys

SEED = 16315
N_FUZZ = 100_000


def _bootstrap_django():
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
        )
    django.setup()


# --- ORACLE: build a real Django Field and read its real .column -------------

def _real_field(name, db_column):
    """A genuine django Field with the real .column computed the same way the
    patched code observes it. `db_column=None` ⇒ column falls back to attname."""
    from django.db.models import IntegerField
    f = IntegerField(db_column=db_column)
    f.set_attributes_from_name(name)   # sets .attname and .column (real code)
    return f


def oracle_columns(specs):
    """patch.diff's behaviour: `(f.column for f in fields)` materialised, where
    each f is a real Django Field. This is the patched expression compiler.py:1728."""
    fields = [_real_field(name, db_column) for (name, db_column) in specs]
    return list(f.column for f in fields)   # the gold comprehension, verbatim


# --- SHADOW: the R/I transliteration of dbColumns / conflictColumns ----------

def _shadow_field(name, db_column):
    """The `Field` structure of Solution.lean built via mapping.md §2: only the
    two observable attributes. `column = db_column or name` mirrors the carried
    value (NOT the patch logic — this is the structure's `column` field, which by
    the bijection holds the real field's column)."""
    column = db_column if db_column else name
    return {"attr": name, "column": column}


def shadow_columns(specs):
    """dbColumns fields transliterated: the per-field column, in order. The
    backward `while` fold of conflictColumns computes exactly this left-to-right
    per-field expansion."""
    fields = [_shadow_field(name, db_column) for (name, db_column) in specs]
    out = []
    for f in fields:           # dbColumns (f :: fs) = [f.column] ++ dbColumns fs
        out.append(f["column"])
    return out


# --- fuzz: (field_name, db_column) specs -------------------------------------

def _ident(rng, k):
    if k == 0:
        return ""
    alpha = string.ascii_letters + string.digits + "_"
    first = rng.choice(string.ascii_letters + "_")
    return first + "".join(rng.choice(alpha) for _ in range(k - 1))


def fuzz_specs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []                                                   # empty field list
    yield [("rank", "rAnK")]                                   # F2P: mixed-case column
    yield [("name", "oTheRNaMe")]                              # F2P
    yield [("rank", "rAnK"), ("name", "oTheRNaMe")]            # F2P pair
    yield [("blacklistid", "BlacklistID"), ("sectorid", "SectorID")]  # issue example
    yield [("sectorid", None)]                                 # no db_column ⇒ column == attname
    yield [("a", None), ("b", "B"), ("c", None)]               # mixture
    yield [("pk", "ID")]                                       # pk-ish name remapped
    yield [("x", "x")]                                         # column == name
    for _ in range(n):
        m = rng.randint(0, 6)
        specs = []
        for _ in range(m):
            name = _ident(rng, rng.randint(1, 12))
            # ~half the time give an explicit (possibly mixed-case) db_column
            if rng.random() < 0.5:
                db = _ident(rng, rng.randint(1, 12))
                # mixed-case / differing from name is the interesting case
            else:
                db = None
            specs.append((name, db))
        yield specs


def main():
    _bootstrap_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for specs in fuzz_specs(N_FUZZ, rng):
        count += 1
        shadow = shadow_columns(specs)
        oracle = oracle_columns(specs)
        if shadow != oracle:
            disagreements.append((specs, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sp, sh, orc in disagreements:
            print("  specs=%r shadow=%r oracle=%r" % (sp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of conflictColumns agrees with patch.diff "
          "behaviour (real Django Field.column) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
