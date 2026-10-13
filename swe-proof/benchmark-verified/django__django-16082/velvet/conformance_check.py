#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16082 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types. The impl scans the
              registered remainder-combination rules (`modCombinators`) first-
              match; this is exactly `combinedNumeric`, transliterated below as
              `shadow_resolve`. Operand/result numeric kinds bridge to the
              concrete field classes via the mapping.md bijection
              (integer-kind = any subclass of IntegerField; float-kind =
              FloatField; dec-kind = DecimalField). There are no A-tagged
              callees, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real
              `django.db.models.expressions._resolve_combined_type(MOD, lhs, rhs)`
              applied at base_commit with the gold patch applied (apply_gold=True,
              the harness applies patch.diff before this runs). This is the real
              correctness oracle the F2P tests observe (via
              CombinedExpression.output_field).

They must agree on every modeled (numeric-operand) input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16082
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()


# --- the R/I shadow: Solution.lean lookup/combinedNumeric, transliterated -----
# NumKind = {"int", "float", "dec"}.  combinedNumeric (Solution.lean pure region)
# is the first-match scan of modCombinators; transliterated directly:
def shadow_resolve(lk, rk):
    """combinedNumeric lk rk : Option NumKind (None == Lean `none`)."""
    table = {
        ("int", "int"): "int",
        ("float", "float"): "float",
        ("dec", "dec"): "dec",
        ("int", "dec"): "dec",
        ("dec", "int"): "dec",
        ("int", "float"): "float",
        ("float", "int"): "float",
    }
    return table.get((lk, rk))  # None for the unlisted pairs (e.g. float/dec)


def main():
    _setup_django()
    from django.db.models import fields
    from django.db.models.expressions import Combinable, _resolve_combined_type

    # mapping.md §2 bijection: concrete operand field class -> abstract NumKind.
    # Integer-kind covers every IntegerField subclass; the resolver's first-match
    # scan resolves any integer-subclass pair to the canonical IntegerField.
    KIND_TO_RESULT_CLS = {
        "int": fields.IntegerField,
        "float": fields.FloatField,
        "dec": fields.DecimalField,
    }
    # operand field classes that map into the modeled numeric slice, with the
    # kind each maps to (includes IntegerField subclasses to exercise the kind
    # bijection robustly).
    OPERANDS = [
        (fields.IntegerField, "int"),
        (fields.BigIntegerField, "int"),
        (fields.SmallIntegerField, "int"),
        (fields.PositiveIntegerField, "int"),
        (fields.AutoField, "int"),
        (fields.FloatField, "float"),
        (fields.DecimalField, "dec"),
    ]

    def oracle_result_name(lhs_cls, rhs_cls):
        cls = _resolve_combined_type(Combinable.MOD, lhs_cls, rhs_cls)
        return cls.__name__ if cls is not None else None

    def shadow_result_name(lk, rk):
        k = shadow_resolve(lk, rk)
        return KIND_TO_RESULT_CLS[k].__name__ if k is not None else None

    disagreements = []
    count = 0

    def check(lhs_cls, lk, rhs_cls, rk):
        nonlocal count
        count += 1
        shadow = shadow_result_name(lk, rk)
        oracle = oracle_result_name(lhs_cls, rhs_cls)
        if shadow != oracle:
            disagreements.append(
                (lhs_cls.__name__, rhs_cls.__name__, shadow, oracle))

    # boundary: every operand-class pair at least once (exhaustive over the
    # modeled domain), then randomized fuzz to the budget.
    for lhs_cls, lk in OPERANDS:
        for rhs_cls, rk in OPERANDS:
            check(lhs_cls, lk, rhs_cls, rk)
            if len(disagreements) >= 5:
                break
        if len(disagreements) >= 5:
            break

    rng = random.Random(SEED)
    while count < N_FUZZ and len(disagreements) < 5:
        lhs_cls, lk = rng.choice(OPERANDS)
        rhs_cls, rk = rng.choice(OPERANDS)
        check(lhs_cls, lk, rhs_cls, rk)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lh, rh, sh, orc in disagreements:
            print("  lhs=%s rhs=%s shadow=%r oracle=%r" % (lh, rh, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveModType agrees with patch.diff "
          "behaviour (_resolve_combined_type MOD) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
