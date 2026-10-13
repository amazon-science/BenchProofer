#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15957 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none inside the impl region itself; the @Pure helper
`is_sliced` copies over as a plain function, the PrefetchQuery carrier as a
plain class). The single @ContractOnly callee `apply_membership` calls the
REAL repo callee it models per mapping.md section 3: `QuerySet.filter` with the
membership predicate, invoked on a real queryset carrying the shadow carrier's
CURRENT slice marks at application time — so the real raise-on-sliced guard is
exercised, not simulated (a shadow that reached the application step while
still sliced would hit the real TypeError and count as a disagreement).

ORACLE: the REAL patched helper `_filter_prefetch_queryset` from
`django.db.models.fields.related_descriptors` (the function the model models
per mapping.md section 1), driven on real querysets over an in-memory sqlite
schema. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable.

TYPE BRIDGE (mapping.md section 2):
  * queryset/queryset.query <-> PrefetchQuery carrier: the input queryset's
    slice marks (Query.low_mark / Query.high_mark) become the carrier's
    offset_mark / limit_mark; the real output is projected back onto the
    carrier by walking the output query's where-tree:
      - membership_applied <-> a non-window leaf lookup is present (the
        field__in membership predicate);
      - lower_bound <-> the integer RHS of the GreaterThan lookup whose LHS is
        a RowNumber Window (None when absent);
      - upper_bound <-> the RHS of the LessThanOrEqual window lookup likewise;
      - offset_mark / limit_mark after the call <-> the output query's
        low_mark / high_mark.
  * field_name (str) <-> member_code (int): a fixed injection over the two
    relation names exercised (both are opaque to the tested behaviour).
  * instances (list) <-> instance_count (int): its length; contents opaque.
The bridge builds each real input directly from (low, high) mark pairs
satisfying the Requires (offset >= 0; limit None or >= 0), so every generated
input is Requires-satisfying by construction.

INPUT DOMAIN: mark pairs (low >= 0, high in {None} U {0,1,...}), including the
unsliced pair (0, None), zero-width and inverted windows, large marks, crossed
with two relation field names and instance lists of length 0 / 1 / 3.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz pairs.
Pinned fuzz seed: 15957.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random).
"""
import json
import random
import sys

SEED = 15957
N_FUZZ = 100_000


# --- shadow carrier: PrefetchQuery, contracts stripped -------------------------

class PrefetchQuery:
    def __init__(self, offset_mark, limit_mark):
        self.offset_mark = offset_mark          # slice start offset
        self.limit_mark = limit_mark            # slice stop limit (None = unbounded)
        self.membership_applied = False         # has the membership predicate been ANDed on?
        self.lower_bound = None                 # type: Optional[int]  # opaque lower position restriction
        self.upper_bound = None                 # type: Optional[int]  # opaque upper position restriction


# --- pure helper from model.py, decorator/contracts stripped -------------------

def is_sliced(query):
    return query.offset_mark != 0 or query.limit_mark is not None


# --- @ContractOnly callee bridge: calls the REAL repo function -----------------

# Context for the bridged callee: (field_name, instances, base queryset factory)
# for the current input, set by the driver before each shadow run.
_BRIDGE_CTX = [None]


def apply_membership(query):
    """Bridge for the modeled @ContractOnly callee: applies the membership
    predicate through the REAL QuerySet.filter (mapping.md section 3), on a
    real queryset carrying the shadow carrier's current slice marks. The real
    guard (filtering a query that still has a slice window raises TypeError)
    therefore applies for real; on success the carrier records the predicate
    as applied."""
    field_name, instances, make_qs = _BRIDGE_CTX[0]
    probe = make_qs()
    probe.query.low_mark = query.offset_mark
    probe.query.high_mark = query.limit_mark
    from django.db.models import Q
    predicate = Q(**{"%s__in" % field_name: instances})
    probe.filter(predicate)  # REAL callee; raises if the window is still set
    query.membership_applied = True


# --- impl region of bounded_prefetch, verbatim (contracts stripped) ------------

def bounded_prefetch(query, member_code, instance_count):
    if is_sliced(query):
        low = query.offset_mark
        high = query.limit_mark      # type: Optional[int]
        # record the start offset as the lower position restriction
        query.lower_bound = low
        # record a finite stop limit as the upper position restriction
        if high is not None:
            query.upper_bound = high
        # remove the slice so the membership predicate can be applied
        query.offset_mark = 0
        query.limit_mark = None
    # at this point the query is no longer sliced; the membership predicate is
    # applicable and is ANDed on (apply_membership requires not is_sliced).
    apply_membership(query)
    return query


# --- real-side projection helpers -----------------------------------------------

def _collect_lookups(node, acc):
    """Walk a WhereNode tree collecting leaf lookup objects."""
    children = getattr(node, "children", None)
    if children is None:
        acc.append(node)
        return
    for child in children:
        _collect_lookups(child, acc)


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    _configure_django()

    from django.db import connection, models
    from django.db.models import Window
    from django.db.models.functions import RowNumber
    from django.db.models.lookups import GreaterThan, LessThanOrEqual
    from django.db.models.fields.related_descriptors import (
        _filter_prefetch_queryset,
    )

    # minimal related models: two FK relations so field_name varies
    class Parent(models.Model):
        class Meta:
            app_label = "confcheck"

    class Child(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE,
                                   related_name="children")
        owner = models.ForeignKey(Parent, on_delete=models.CASCADE,
                                  related_name="owned", null=True)
        rank = models.IntegerField(default=0)

        class Meta:
            app_label = "confcheck"
            ordering = ["rank"]

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    parents = [Parent.objects.create() for _ in range(3)]
    for r in range(4):
        Child.objects.create(parent=parents[0], owner=parents[1], rank=r)

    # field_name (str) <-> member_code (int): fixed injection
    FIELD_CODE = {"parent": 0, "owner": 1}
    INSTANCE_POOLS = [[], parents[:1], parents]

    def make_qs():
        return Child.objects.all()

    def lookups_of(qs):
        acc = []
        _collect_lookups(qs.query.where, acc)
        return acc

    def window_bound_value(acc, lookup_cls):
        # Integer RHS of the row-position bound of the given lookup class whose
        # LHS is a RowNumber Window; None when no such bound is present.
        for lk in acc:
            if isinstance(lk, lookup_cls):
                lhs = getattr(lk, "lhs", None)
                if isinstance(lhs, Window):
                    inner = lhs.source_expression
                    if not isinstance(inner, RowNumber):
                        raise AssertionError(
                            "window bound wraps %r, expected RowNumber"
                            % (type(inner).__name__,))
                    return lk.rhs
        return None

    def membership_present(acc):
        # the field__in membership lookup: at least one non-window leaf lookup
        for lk in acc:
            if not isinstance(getattr(lk, "lhs", None), Window):
                return True
        return False

    def run_real(field_name, instances, low, high):
        qs = make_qs()
        qs.query.low_mark = low
        qs.query.high_mark = high
        out = _filter_prefetch_queryset(qs, field_name, instances)
        acc = lookups_of(out)
        return {
            "membership": membership_present(acc),
            "lower": window_bound_value(acc, GreaterThan),
            "upper": window_bound_value(acc, LessThanOrEqual),
            "low_mark": out.query.low_mark,
            "high_mark": out.query.high_mark,
        }

    def run_shadow(field_name, instances, low, high):
        q = PrefetchQuery(low, high)
        _BRIDGE_CTX[0] = (field_name, instances, make_qs)
        result = bounded_prefetch(q, FIELD_CODE[field_name], len(instances))
        if result is not q:
            raise AssertionError("shadow did not return its input carrier")
        return {
            "membership": bool(q.membership_applied),
            "lower": q.lower_bound,
            "upper": q.upper_bound,
            "low_mark": q.offset_mark,
            "high_mark": q.limit_mark,
        }

    def check_one(field_name, instances, low, high, label):
        real = run_real(field_name, instances, low, high)
        try:
            shadow = run_shadow(field_name, instances, low, high)
        except TypeError as exc:
            print("DISAGREEMENT on %s\n  input: field=%r n_instances=%d "
                  "low=%r high=%r\n  shadow raised at the membership step: %r\n"
                  "  real=%r"
                  % (label, field_name, len(instances), low, high, exc, real))
            return False
        if shadow != real:
            print("DISAGREEMENT on %s\n  input: field=%r n_instances=%d "
                  "low=%r high=%r\n  shadow=%r\n  real=%r"
                  % (label, field_name, len(instances), low, high, shadow, real))
            return False
        return True

    checked = 0

    # --- boundary grid ----------------------------------------------------------
    lows = [0, 1, 2, 5, 100, 10**6]
    highs = [None, 0, 1, 2, 3, 10, 100, 10**6]
    n_boundary = 0
    for fname in ("parent", "owner"):
        for pool in INSTANCE_POOLS:
            for low in lows:
                for high in highs:
                    if not check_one(fname, pool, low, high,
                                     "boundary(%s,%d,%r,%r)"
                                     % (fname, len(pool), low, high)):
                        return 1
                    checked += 1
                    n_boundary += 1

    # --- randomized fuzz ----------------------------------------------------------
    rng = random.Random(SEED)
    fields = ["parent", "owner"]
    for it in range(N_FUZZ):
        fname = fields[rng.random() < 0.3]
        pool = INSTANCE_POOLS[rng.randrange(len(INSTANCE_POOLS))]
        r = rng.random()
        if r < 0.2:
            low = 0
        elif r < 0.9:
            low = rng.randint(0, 60)
        else:
            low = rng.randint(0, 10**7)
        r = rng.random()
        if r < 0.35:
            high = None
        elif r < 0.9:
            high = rng.randint(0, 80)
        else:
            high = rng.randint(0, 10**7)
        if not check_one(fname, pool, low, high, "fuzz #%d" % it):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched helper on %d mark/relation/"
          "instance combinations (%d boundary + %d fuzz, seed %d); membership "
          "step routed through the real filter callee."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee bridged to the real "
                                "filter)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
