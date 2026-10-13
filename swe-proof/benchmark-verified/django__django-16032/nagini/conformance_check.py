#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16032 (nagini).

SHADOW: the impl regions of model.py's three operations
(``project_columns`` / ``attach_auxiliary_expressions`` / ``prepare_in_rhs``)
and the ``Query`` twin constructor, copied VERBATIM below with only the
contract calls (Requires / Ensures / Acc / Old / ToSeq clauses) stripped.
There are no @Pure helpers and no @ContractOnly callees (mapping.md section 3:
no consumed axioms; the operations are modelled deeply).

ORACLE: the REAL patched repo operations per mapping.md section 1 —
  * ``project_columns(q, col)``       ~ ``Query.set_values([name])``
  * ``attach_auxiliary_expressions``  ~ ``Query.add_annotation(..., select=True)``
                                        then ``add_annotation(..., select=False)``
                                        (the QuerySet.annotate / .alias funnel)
  * ``prepare_in_rhs(q, tc, uniq)``   ~ ``RelatedIn.get_prep_lookup``'s
                                        rhs-narrowing branch, driven through a
                                        real ``build_filter(("<fk>__in", qs))``.
The gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before
this script runs, so ``import django`` resolves to the patched module.

MODELING BOUNDARY (mapping.md section 3.3): the modeled operation is the
RelatedIn branch only; after it, control flows into the generic
``In.get_prep_lookup`` (unchanged code, outside the modeled edit), which for an
unprojected Query rhs performs its own pk-narrowing. To observe the modeled
branch's effect exactly at its documented boundary, the driver wraps
``In.get_prep_lookup`` with a snapshot probe that records the rhs state
(flag / selected columns / mask non-emptiness) on entry and then calls the
ORIGINAL function, so the full real code path still runs unchanged.

TYPE BRIDGE (mapping.md section 2): the rich Query is reduced to the three
touched fields —
  * ``has_select_fields``            <-> ``restricted_to_explicit_columns`` (bool)
  * ``values_select`` (column names) <-> ``selected_columns`` (List[int]) via a
                                         fixed column-name <-> int-id table
  * ``annotation_select_mask``       <-> ``aux_expr_materialized`` = bool(mask)
                                         (None or empty set <-> False)

INPUT PLAN (state-machine differential, >= 1e5 Requires-satisfying inputs):
the preconditions demand only field access, so every twin state reachable by
the modelled operations from the constructor is Requires-satisfying, and each
operation application is one checked input. Both sides start from a fresh
query and apply the SAME operation sequence; after every operation the real
query's abstraction must equal the twin. Boundary sequences enumerate: every
projectable column, attach/project interleavings, and the membership-filter
preparation across a non-unique-key target FK, a second non-unique-key target
FK (different target column), a unique-key (pk) target FK, an
already-projected rhs, and the one-to-one self-model special case — each on
top of every shaping prefix. Fuzz: 40000 random sequences (0-4 shaping ops
then, usually, a terminal filter-preparation with a random FK) — well over
1e5 checks total. Pinned fuzz seed: 16032. Exit 0 iff zero disagreements; on
disagreement prints the operation trace and both states and exits 1.
stdlib only (hypothesis not required).
"""
import json
import random
import sys

SEED = 16032
N_FUZZ = 40000


# --- SHADOW: model.py twin + impl regions, verbatim, contracts stripped ------

class TwinQuery(object):
    def __init__(self):
        self.restricted_to_explicit_columns = False  # type: bool
        self.selected_columns = []  # type: List[int]
        self.aux_expr_materialized = False  # type: bool


def project_columns(q, column):
    q.selected_columns = []
    q.selected_columns = [column]
    q.restricted_to_explicit_columns = True
    # projection re-derives the expression-tracking structure for the chosen
    # ordinary columns, which leaves it empty.
    q.aux_expr_materialized = False


def attach_auxiliary_expressions(q):
    # attaching the returned-column kind and the non-returned (helper) kind
    # materializes the auxiliary expression-tracking structure; it touches no
    # other state.
    q.aux_expr_materialized = True


def prepare_in_rhs(q, target_column, target_is_unique_key):
    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
        # narrow the rhs to the single relevant column via the projection
        # operation (1) — which also establishes the property as true.
        project_columns(q, target_column)


# --- bridge: fixed column-name <-> int-id table -------------------------------

COL_NAMES = ["id", "code", "code2", "n", "m", "place", "x", "y"]
COL_ID = dict((name, i) for i, name in enumerate(COL_NAMES))


def twin_state(t):
    return (t.restricted_to_explicit_columns,
            list(t.selected_columns),
            t.aux_expr_materialized)


def real_state(q):
    return (bool(q.has_select_fields),
            [COL_ID[name] for name in q.values_select],
            bool(q.annotation_select_mask))


# --- oracle setup: real Django, minimal models, boundary snapshot probe -------

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()

    from django.db import models

    class Parent(models.Model):
        code = models.IntegerField(unique=True)
        code2 = models.IntegerField(unique=True)
        n = models.IntegerField()
        m = models.IntegerField()

        class Meta:
            app_label = "auth"

    class ChildA(models.Model):
        # forward FK whose target column is a unique NON-key-of-record column
        parent = models.ForeignKey(
            Parent, to_field="code", on_delete=models.CASCADE
        )

        class Meta:
            app_label = "auth"

    class ChildB(models.Model):
        # a second non-unique-key-target FK, different target column
        parent = models.ForeignKey(
            Parent, to_field="code2", on_delete=models.CASCADE
        )

        class Meta:
            app_label = "auth"

    class ChildPk(models.Model):
        # FK whose target column IS the unique key of record
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

        class Meta:
            app_label = "auth"

    class Place(models.Model):
        code = models.IntegerField(unique=True)
        y = models.IntegerField()

        class Meta:
            app_label = "auth"

    class Restaurant(models.Model):
        # one-to-one that is itself the key of record, targeting a
        # non-key column of Place: the self-model special case inside the
        # narrowing branch resolves the target to the local column name.
        place = models.OneToOneField(
            Place, primary_key=True, to_field="code", on_delete=models.CASCADE
        )
        x = models.IntegerField()

        class Meta:
            app_label = "auth"

    return {
        "Parent": Parent, "ChildA": ChildA, "ChildB": ChildB,
        "ChildPk": ChildPk, "Place": Place, "Restaurant": Restaurant,
    }


def install_boundary_probe():
    """Snapshot the rhs state exactly where the modeled operation ends: on
    entry to the generic In.get_prep_lookup (unchanged downstream code,
    outside the modeled edit — mapping.md section 3.3). The original function
    is still called, so real behaviour is untouched."""
    from django.db.models import lookups as dj_lookups
    from django.db.models.fields.related_lookups import RelatedIn
    from django.db.models.sql.query import Query

    box = []
    orig = dj_lookups.In.get_prep_lookup

    def probe(self):
        if isinstance(self, RelatedIn):
            rq = self.rhs.query if hasattr(self.rhs, "query") else self.rhs
            if isinstance(rq, Query):
                box.append(real_state(rq))
        return orig(self)

    dj_lookups.In.get_prep_lookup = probe
    return box


# --- oracle operations ---------------------------------------------------------

_ALIAS_N = [0]


def real_fresh(model_cls):
    from django.db import models
    return models.sql.Query(model_cls)


def real_project(q, col_id):
    q.set_values([COL_NAMES[col_id]])


def real_attach(q):
    from django.db.models import Value
    _ALIAS_N[0] += 1
    q.add_annotation(Value(1), "aux_r%d" % _ALIAS_N[0], select=True)
    _ALIAS_N[0] += 1
    q.add_annotation(Value(1), "aux_h%d" % _ALIAS_N[0], select=False)


def real_prepare(box, rhs_query, rhs_model, child_model, fk_name):
    """Build the membership filter on a fresh outer query so the real
    narrowing branch runs on the (cloned) rhs; return the boundary snapshot."""
    qs = rhs_model.objects.all()
    qs.query = rhs_query
    outer = child_model.objects.all().query
    del box[:]
    outer.build_filter(("%s__in" % fk_name, qs), can_reuse=set())
    if len(box) != 1:
        raise AssertionError(
            "expected exactly 1 related-IN boundary snapshot, got %d" % len(box))
    return box[0]


# --- differential driver --------------------------------------------------------

class Mismatch(Exception):
    pass


def run_sequence(models_d, box, ops, counter):
    """Apply one operation sequence to twin and real from fresh; compare the
    abstraction after every operation. ops is a list of tuples:
      ("rhs_model", name)           — choose the query's model (first op only)
      ("project", col_id)
      ("attach",)
      ("prepare", fk_key)           — terminal; fk_key in PREPARE_TABLE
    """
    rhs_model_name = "Parent"
    if ops and ops[0][0] == "rhs_model":
        rhs_model_name = ops[0][1]
        ops = ops[1:]
    rhs_model = models_d[rhs_model_name]

    twin = TwinQuery()
    real = real_fresh(rhs_model)
    if twin_state(twin) != real_state(real):
        raise Mismatch((ops, "fresh", twin_state(twin), real_state(real)))

    for op in ops:
        kind = op[0]
        if kind == "project":
            col_id = op[1]
            project_columns(twin, col_id)
            real_project(real, col_id)
            got = real_state(real)
        elif kind == "attach":
            attach_auxiliary_expressions(twin)
            real_attach(real)
            got = real_state(real)
        elif kind == "prepare":
            child_name, fk_name, target_col, uniq = PREPARE_TABLE[op[1]]
            prepare_in_rhs(twin, COL_ID[target_col], uniq)
            got = real_prepare(box, real, rhs_model,
                               models_d[child_name], fk_name)
        else:
            raise ValueError(kind)
        counter[0] += 1
        want = twin_state(twin)
        if (want[0], want[1], want[2]) != (got[0], got[1], got[2]):
            raise Mismatch((ops, op, want, got))
        if kind == "prepare":
            break  # terminal: downstream effects are outside the modeled op


# fk_key -> (child model, fk attr, target column name, target_is_unique_key)
PREPARE_TABLE = {
    "nonpk": ("ChildA", "parent", "code", False),
    "nonpk2": ("ChildB", "parent", "code2", False),
    "pk": ("ChildPk", "parent", "id", True),
    "o2o": ("Restaurant", "place", "place", False),
}

PARENT_COLS = [COL_ID[c] for c in ("id", "code", "code2", "n", "m")]


def boundary_sequences():
    seqs = []
    shaping_prefixes = [
        [],
        [("attach",)],
        [("attach",), ("attach",)],
    ]
    for c in PARENT_COLS:
        shaping_prefixes.append([("project", c)])
        shaping_prefixes.append([("project", c), ("attach",)])
        shaping_prefixes.append([("attach",), ("project", c)])
    shaping_prefixes.append(
        [("attach",), ("project", COL_ID["n"]), ("attach",),
         ("project", COL_ID["code"])])
    for prefix in shaping_prefixes:
        seqs.append(list(prefix))
        for fk in ("nonpk", "nonpk2", "pk"):
            seqs.append(list(prefix) + [("prepare", fk)])
    # the one-to-one self-model special case (Restaurant rhs)
    for prefix in ([], [("attach",)], [("project", COL_ID["x"])],
                   [("attach",), ("project", COL_ID["x"])]):
        seqs.append([("rhs_model", "Restaurant")] + list(prefix)
                    + [("prepare", "o2o")])
    return seqs


def main():
    models_d = setup_django()
    box = install_boundary_probe()

    counter = [0]
    try:
        for seq in boundary_sequences():
            run_sequence(models_d, box, seq, counter)

        rng = random.Random(SEED)
        fuzz_fks = ("nonpk", "nonpk2", "pk")
        for _ in range(N_FUZZ):
            ops = []
            for _k in range(rng.randint(0, 4)):
                if rng.random() < 0.5:
                    ops.append(("project", rng.choice(PARENT_COLS)))
                else:
                    ops.append(("attach",))
            if rng.random() < 0.8:
                ops.append(("prepare", rng.choice(fuzz_fks)))
            if not ops:
                ops.append(("attach",))
            run_sequence(models_d, box, ops, counter)
    except Mismatch as m:
        ops, at, want, got = m.args[0]
        print("DISAGREEMENT after %d checks" % counter[0])
        print("  operation sequence: %r" % (ops,))
        print("  at operation:       %r" % (at,))
        print("  shadow (impl region) state: restricted=%r selected=%r aux=%r"
              % want)
        print("  real (patched repo)  state: restricted=%r selected=%r aux=%r"
              % got)
        return 1

    print("G-CONF OK: shadow impl == real patched Django query machinery on "
          "%d operation checks (boundary sequences + %d fuzz sequences, "
          "seed %d); 0 disagreements." % (counter[0], N_FUZZ, SEED))
    print(json.dumps({"checked": counter[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
