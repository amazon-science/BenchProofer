#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13128 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`dispatchKind`,
              the resolve-time node-kind selection) transliterated to Python,
              over the abstract carrier (selfKind, connector, lt, rt) via the
              mapping.md bijection. There are NO A-tagged callees in the impl
              region (no axioms in this bundle); the operand output types
              `lt`/`rt` are R-tagged abstracted INPUTS (LESSONS:
              abstracted-input-not-axiom), supplied directly. So the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.models.expressions.CombinedExpression.resolve_expression`
              applied at base_commit, observed as the *node kind* the resolve
              step selects (the F2P-observable dispatch decision: which of
              CombinedExpression / DurationExpression / TemporalSubtraction the
              resolved node is). The harness applies patch.diff before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only
(no live DB — `resolve_expression` is a pure tree transform). The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 13128
N_FUZZ = 100_000

# ---- abstract carrier domains (Solution.lean inductives) --------------------
# FieldTag ∪ {None}: the resolvable output-type tag of an operand, or None for
# "no resolvable type" (the FieldError/AttributeError outcome).
FIELD_TAGS = ["date", "datetime", "time", "duration", "other", None]
CONNECTORS = ["+", "-"]          # Connector.plus / Connector.minus
NODE_KINDS = ["combined", "duration", "temporal"]  # NodeKind.*

_TEMPORAL = {"date", "datetime", "time"}


# ---- the R/I shadow: dispatchKind transliterated to Python ------------------
def shadow_dispatch(self_kind, conn, lt, rt):
    """`dispatchKind selfKind conn lt rt` (Solution.lean pure region)."""
    if self_kind != "combined":
        return self_kind
    # isIntervalMix lt rt
    if (lt == "duration" or rt == "duration") and lt != rt:
        return "duration"
    # conn = minus ∧ isTemporalTag lt ∧ lt = rt
    if conn == "-" and lt in _TEMPORAL and lt == rt:
        return "temporal"
    return "combined"


# ---- the oracle: the patched real resolve_expression ------------------------
def _build_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={})
        django.setup()
    from django.db.models.expressions import (
        CombinedExpression, DurationExpression, TemporalSubtraction, Value)
    from django.db.models import fields
    return CombinedExpression, DurationExpression, TemporalSubtraction, Value, fields


def _operand(tag, Value, fields):
    """mapping.md §2 bijection: a FieldTag ↔ a resolved operand carrying that
    output type. `None` ↔ an operand whose `output_field` raises FieldError."""
    table = {
        "date": fields.DateField,
        "datetime": fields.DateTimeField,
        "time": fields.TimeField,
        "duration": fields.DurationField,
        "other": fields.IntegerField,
    }
    if tag is None:
        return Value(1)                       # no output_field -> FieldError -> None
    return Value(1, output_field=table[tag]())


def make_oracle():
    CombinedExpression, DurationExpression, TemporalSubtraction, Value, fields = _build_django()
    name_to_kind = {
        "CombinedExpression": "combined",
        "DurationExpression": "duration",
        "TemporalSubtraction": "temporal",
    }

    def oracle(self_kind, conn, lt, rt):
        lhs = _operand(lt, Value, fields)
        rhs = _operand(rt, Value, fields)
        if self_kind == "combined":
            node = CombinedExpression(lhs, conn, rhs)
        elif self_kind == "duration":
            node = DurationExpression(lhs, conn, rhs)
        else:  # temporal
            node = TemporalSubtraction(lhs, rhs)
        resolved = node.resolve_expression(query=None)
        return name_to_kind[type(resolved).__name__]

    return oracle


def all_configs():
    """The full abstract product (3*2*6*6 = 216) — boundary enumeration."""
    return list(itertools.product(NODE_KINDS, CONNECTORS, FIELD_TAGS, FIELD_TAGS))


def fuzz_configs(n, rng):
    for _ in range(n):
        yield (rng.choice(NODE_KINDS), rng.choice(CONNECTORS),
               rng.choice(FIELD_TAGS), rng.choice(FIELD_TAGS))


def main():
    rng = random.Random(SEED)
    oracle = make_oracle()
    disagreements = []
    count = 0
    for cfg in itertools.chain(all_configs(), fuzz_configs(N_FUZZ, rng)):
        count += 1
        shadow = shadow_dispatch(*cfg)
        truth = oracle(*cfg)
        if shadow != truth:
            disagreements.append((cfg, shadow, truth))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, tr in disagreements:
            print("  cfg=%r shadow=%r oracle=%r" % (cfg, sh, tr))
        return 1
    print("G-CONF OK: R/I shadow of resolveCombined (dispatchKind) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
