#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11734 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the Requires/Ensures blocks live outside the impl markers, so
only the decorators/contract imports are dropped). The @Pure helpers
(kind_value / kind_local / kind_outer / is_query_expression / target_level /
resolved_level_in_inner) copy over as plain functions. No PSeq and no
@ContractOnly callee exist in this bundle; the carrier is a small int tag.

ORACLES (the REAL patched repo functions the model models, per mapping.md):

  (1) rebind_into_inner_subquery  <->  Query.split_exclude
      (django/db/models/sql/query.py). The REAL method is invoked on a real
      Query over a real model; the first thing it does with the condition is
      re-anchor its right-hand side and hand the result to the fresh inner
      query via add_filter. A spy installed on Query.add_filter captures that
      re-anchored condition and aborts the rest of the (DB-bound) method via
      a sentinel exception, so the observed value is produced entirely by the
      real repo code. The observable compared against the shadow is the
      number of additional outer-reference wrapping hops applied: the
      OuterRef nesting depth of the captured right-hand side minus the depth
      of the input right-hand side (depth read back by walking the real
      OuterRef.name chain). The base field name and the left-hand side must
      also be preserved, and a plain value must be carried through untouched.

  (2) normalize_only_concrete_value  <->  RelatedLookupMixin.get_prep_lookup
      (django/db/models/fields/related_lookups.py). A real related lookup
      (RelatedExact over a genuine single-column relation) is constructed,
      which runs the REAL get_prep_lookup. Whether the right-hand side was
      routed through the relation's value coercion is observed by a
      recording wrapper around the module's get_normalized_value that
      delegates to the original; the boolean "coercion ran" is diffed
      against the shadow decision.

TYPE BRIDGE (mapping.md section 2): the int tag rhs_kind in {0,1,2} maps to a
concrete right-hand-side object: 0 (value) <-> a plain Python value; 1 (local)
<-> a real F(name); 2 (outer) <-> a real OuterRef (fuzzed at nesting depths
1..5 -- every OuterRef, nested or not, is one tag). The hop count maps to the
depth delta as described above; the normalisation decision maps to the
"coercion ran" boolean directly.

INPUT DOMAIN: Requires admits exactly rhs_kind in {0,1,2}. Each tag is
realised by many concrete objects (random field names, values, nesting
depths), giving a genuine fuzz space over Requires-satisfying inputs.

>= 1e5 inputs: boundary matrix + 100000 fuzz draws, each draw exercising BOTH
modeled functions on a fresh realisation. Pinned seed: 117340.

Runs inside the instance image with the gold patch applied by the gate
(PYTHONPATH=/testbed); this script applies nothing itself. Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs, exit 1.
stdlib only.
"""
import random
import string
import sys

SEED = 117340
N_FUZZ = 100_000


# --- @Pure helpers from model.py, decorators stripped ---------------------

def kind_value():
    return 0


def kind_local():
    return 1


def kind_outer():
    return 2


def is_query_expression(kind):
    return kind == kind_local() or kind == kind_outer()


def target_level(kind):
    if kind == kind_outer():
        return -1
    return 0


def resolved_level_in_inner(kind):
    if kind == kind_local():
        return 1
    if kind == kind_outer():
        return 0
    return 0


# --- impl regions of model.py, verbatim (contracts stripped) ---------------

def rebind_into_inner_subquery(rhs_kind):
    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # level +1 in inner must become level 0 -> one outward hop.
        return 1
    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
    return 1


def normalize_only_concrete_value(rhs_kind):
    return not is_query_expression(rhs_kind)


# --- Django bootstrap -------------------------------------------------------

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


class _CaptureDone(Exception):
    """Sentinel: the re-anchored condition has been captured; abort the rest
    of the real method (which would need a database)."""


def main():
    setup_django()
    from django.db.models import F
    from django.db.models.expressions import OuterRef
    from django.db.models.sql.query import Query
    from django.db.models.fields import related_lookups
    from django.contrib.auth.models import Permission, User

    # ---- oracle (1): the REAL Query.split_exclude re-anchor ----------------
    # Spy on Query.add_filter: the real method hands the (already re-anchored)
    # condition to the fresh inner query through it. Installed once, restored
    # at the end.
    captured = {}
    orig_add_filter = Query.add_filter

    def spy_add_filter(self, filter_expr, *a, **kw):
        captured["expr"] = filter_expr
        raise _CaptureDone()

    def outer_depth(obj):
        """Nesting depth of real outer-reference wrappers, and the base."""
        depth = 0
        cur = obj
        while isinstance(cur, OuterRef):
            depth += 1
            cur = cur.name
        return depth, cur

    def real_rebind(lhs_name, rhs_obj):
        """Run the REAL split_exclude on a real Query and return the captured
        re-anchored condition (lhs, rhs)."""
        q = Query(User)
        captured.clear()
        try:
            q.split_exclude((lhs_name, rhs_obj), set(), [])
        except _CaptureDone:
            pass
        if "expr" not in captured:
            raise RuntimeError("inner-query condition was never captured")
        return captured["expr"]

    # ---- oracle (2): the REAL RelatedLookupMixin.get_prep_lookup -----------
    # Recording wrapper around the module's value-coercion entry point;
    # delegates to the original so the real behaviour is unchanged.
    coercion_ran = {"flag": False}
    orig_gnv = related_lookups.get_normalized_value

    def recording_gnv(value, lhs):
        coercion_ran["flag"] = True
        return orig_gnv(value, lhs)

    # A genuine single-column relation for the lookup's left-hand side.
    rel_field = Permission._meta.get_field("content_type")
    rel_col = rel_field.get_col(Permission._meta.db_table)

    def real_normalizes(rhs_obj):
        """Construct a real related lookup (this runs the REAL
        get_prep_lookup) and report whether the value coercion ran."""
        coercion_ran["flag"] = False
        related_lookups.RelatedExact(rel_col, rhs_obj)
        return coercion_ran["flag"]

    # ---- concrete realisations of the int-tag domain ------------------------
    rng = random.Random(SEED)
    KIND_NAMES = {0: "value", 1: "local", 2: "outer"}

    def rand_name():
        return "".join(rng.choice(string.ascii_lowercase)
                       for _ in range(rng.randint(1, 8)))

    def realize(kind, name, depth, value):
        """One concrete right-hand-side object for the given tag."""
        if kind == 0:
            return value
        if kind == 1:
            return F(name)
        ref = OuterRef(name)
        for _ in range(depth - 1):
            ref = OuterRef(ref)
        return ref

    def check_one(kind, name, depth, value, label):
        rhs_in = realize(kind, name, depth, value)
        in_depth, in_base = outer_depth(rhs_in)

        # (1) re-anchor hop count
        lhs_name = rand_name()
        out_lhs, rhs_out = real_rebind(lhs_name, rhs_in)
        out_depth, out_base = outer_depth(rhs_out)
        real_hops = out_depth - in_depth
        shadow_hops = rebind_into_inner_subquery(kind)
        # Structural sanity from the bridge: lhs untouched; the reference
        # (or value) itself preserved under the added wrappers.
        if kind == 0:
            preserved = rhs_out is rhs_in
        elif kind == 1:
            # a local reference's field name must survive the re-anchor
            preserved = (out_base == rhs_in.name)
        else:
            preserved = (out_base == in_base)
        if real_hops != shadow_hops or out_lhs != lhs_name or not preserved:
            print("DISAGREEMENT (rebind_into_inner_subquery) on %s" % label)
            print("  input : kind=%d (%s) rhs=%r lhs=%r"
                  % (kind, KIND_NAMES[kind], rhs_in, lhs_name))
            print("  shadow: hops=%d" % shadow_hops)
            print("  real  : hops=%d captured=(%r, %r) preserved=%r"
                  % (real_hops, out_lhs, rhs_out, preserved))
            return False

        # (2) normalisation decision
        rhs_in2 = realize(kind, name, depth, value)
        real_norm = real_normalizes(rhs_in2)
        shadow_norm = normalize_only_concrete_value(kind)
        if real_norm != shadow_norm:
            print("DISAGREEMENT (normalize_only_concrete_value) on %s" % label)
            print("  input : kind=%d (%s) rhs=%r"
                  % (kind, KIND_NAMES[kind], rhs_in2))
            print("  shadow: %r" % shadow_norm)
            print("  real  : %r" % real_norm)
            return False
        return True

    Query.add_filter = spy_add_filter
    related_lookups.get_normalized_value = recording_gnv
    checked = 0
    try:
        # boundary matrix: every tag, several names/values/nesting depths
        boundary = []
        for name in ("pk", "id", "name", "job", "a"):
            for v in (0, 1, -1, 7, None, "7", 2 ** 31, 3.5):
                boundary.append((0, name, 1, v))
            boundary.append((1, name, 1, None))
            for depth in (1, 2, 3, 4, 5):
                boundary.append((2, name, depth, None))
        for i, (kind, name, depth, value) in enumerate(boundary):
            if not check_one(kind, name, depth, value, "boundary[%d]" % i):
                return 1
            checked += 1

        for i in range(N_FUZZ):
            kind = rng.randrange(3)
            name = rand_name()
            depth = rng.randint(1, 5)
            r = rng.random()
            if r < 0.5:
                value = rng.randint(-10 ** 6, 10 ** 6)
            elif r < 0.7:
                value = None
            elif r < 0.85:
                value = str(rng.randint(0, 10 ** 6))
            else:
                value = rng.uniform(-1000.0, 1000.0)
            if not check_one(kind, name, depth, value, "fuzz[%d]" % i):
                return 1
            checked += 1
    finally:
        Query.add_filter = orig_add_filter
        related_lookups.get_normalized_value = orig_gnv

    print("status=pass conformance OK: %d inputs, 0 disagreements "
          "(both modeled functions diffed against the real repo callees)"
          % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
