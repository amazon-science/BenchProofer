#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12708 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `selected`/`keep` over the flattened constraint list
              (`out = the constraints with isIndex AND NOT isUnique, in order`),
              via the mapping.md bijection (column-matched constraint map ↔
              List Constraint; infodict['index']/['unique'] ↔ Bool fields;
              selected names ↔ kept constraints). There are NO A-tagged callees
              in this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, unchanged
              `BaseDatabaseSchemaEditor._constraint_names` selection loop
              (`django/db/backends/base/schema.py`) invoked with the POST-PATCH
              kwargs `index=True, unique=False` (the only thing patch.diff
              changes). This is the genuine repo callee — it is NOT axiomatized;
              we drive it through a shim whose introspection returns the fuzzed
              constraint map, so the real selection logic at schema.py:1148-1168
              decides which names are returned. The post-patch
              `_delete_composed_index` then operates on exactly this selection
              (it requires |selection| == 1 and deletes it).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import contextlib
import random
import sys

# Be robust to a container whose stdout defaults to the ASCII codec: force UTF-8
# so any non-ASCII byte in a diagnostic string can never raise UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SEED = 12708
N_FUZZ = 100_000

# --- Django bootstrap (minimal settings so the schema module imports) --------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
    django.setup()

from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# The real, unchanged selection loop. patch.diff does not touch this function;
# it only changes the kwargs the caller passes (this is the soundness point of
# the refinement: the changed op is the filter kwargs, modeled by `keep`).
_real_constraint_names = BaseDatabaseSchemaEditor._constraint_names


# --- shims so the real _constraint_names runs over our fuzzed constraint map -
class _Introspection:
    def __init__(self, constraints):
        self._constraints = constraints

    def identifier_converter(self, name):
        return name

    def get_constraints(self, cursor, table_name):
        return self._constraints


class _Connection:
    def __init__(self, constraints):
        self.introspection = _Introspection(constraints)

    @contextlib.contextmanager
    def cursor(self):
        yield object()


class _Meta:
    db_table = "fuzz_table"


class _Model:
    _meta = _Meta()


class _Shim:
    """A minimal schema-editor self whose connection.introspection returns the
    fuzzed constraint map. `_constraint_names` uses `self` only for
    `self.connection.{cursor,introspection}`."""
    def __init__(self, constraints):
        self.connection = _Connection(constraints)


def _infodict(is_index, is_unique):
    """A get_constraints-shaped infodict. Only 'index'/'unique' vary; the other
    dimensions are held at the fixed values the modeled selection assumes
    (mapping.md §2): columns matched (we pass column_names=None so the column
    test is a no-op), no primary_key/check/foreign_key, plain type."""
    return {
        "columns": ["pink", "weight"],
        "primary_key": False,
        "unique": bool(is_unique),
        "index": bool(is_index),
        "check": False,
        "foreign_key": None,
        "type": "idx",
        "definition": None,
        "options": None,
        "orders": None,
    }


def shadow_selected(cs):
    """selected (cs) transliterated to Python: the kept constraint names, in
    order. keep c = c.isIndex AND NOT c.isUnique."""
    return [name for (name, is_index, is_unique) in cs
            if is_index and not is_unique]


def oracle_selected(cs):
    """The REAL _constraint_names run with the POST-PATCH kwargs
    {'index': True, 'unique': False}. Returns the selected constraint names."""
    constraints = {}
    for (name, is_index, is_unique) in cs:
        constraints[name] = _infodict(is_index, is_unique)
    shim = _Shim(constraints)
    # column_names=None => the per-column match is a no-op (all on target cols);
    # exclude=None; the post-patch kwargs are index=True, unique=False.
    return list(_real_constraint_names(
        shim, _Model(), column_names=None, index=True, unique=False, exclude=None,
    ))


def _rand_cs(rng):
    n = rng.randint(0, 6)
    cs = []
    for k in range(n):
        cs.append(("c%d" % k, rng.random() < 0.5, rng.random() < 0.5))
    return cs


def _boundary_cases():
    # the F2P scenario: one plain index (idx) + one unique-backed index (uniq)
    # over the same columns. Pre-patch selects BOTH (crash); post-patch selects
    # only the plain index.
    return [
        [],                                            # nothing on the columns
        [("idx", True, False)],                        # lone index -> select it
        [("uniq", True, True)],                        # lone unique-backed -> exclude
        [("uniq", False, True)],                       # unique, non-index -> exclude
        [("plain", False, False)],                     # neither -> exclude
        # THE BUG: index + unique-backed index on the same columns.
        [("idx", True, False), ("uniq", True, True)],
        [("uniq", True, True), ("idx", True, False)],  # order swapped
        # multiple plain indexes (selection has >1 -> delete would still raise,
        # but the SELECTION must match: shadow and oracle agree on the set).
        [("idx1", True, False), ("idx2", True, False)],
        # mixture
        [("idx", True, False), ("uniq", True, True),
         ("fk", False, False), ("idx2", True, False)],
    ]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cs in _boundary_cases():
        count += 1
        sh, orc = shadow_selected(cs), oracle_selected(cs)
        if sh != orc:
            disagreements.append((cs, sh, orc))
    for _ in range(N_FUZZ):
        cs = _rand_cs(rng)
        count += 1
        sh, orc = shadow_selected(cs), oracle_selected(cs)
        if sh != orc:
            disagreements.append((cs, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cs, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (cs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectIndexConstraints agrees with the real "
          "_constraint_names selection under the post-patch kwargs on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
