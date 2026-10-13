#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11490.

This bundle consumes NO @ContractOnly axioms. The two operations the modelled
function uses — producing a private per-compilation copy of a sub-query
(model.py ``detached_copy``) and applying a chosen column list to a query
(model.py ``with_columns``) — are modelled DEEPLY. They stand in for two
UNCHANGED Django callees the compilation invokes:

  * ``django.db.models.sql.query.Query.clone()``      (A-reference)
  * ``django.db.models.sql.query.Query.set_values()`` (A-reference)

G-AX validates those deep models against the REAL callees. Under the mapping
(mapping.md §1) a modelled ``Query`` carries

  * ``columns``  ↔ the ordered keys of ``values_select``,
  * ``leading``  ↔ the ordered keys of ``extra_select``  (rendered ahead of the
                   query's own columns, and consulted FIRST when a requested
                   name is classified),
  * ``trailing`` ↔ the ordered keys of ``annotation_select`` (rendered after),
  * ``state``    ↔ the accumulated row restriction together with the
                   DEFINITIONS of the derived columns (the where clause, the
                   ``extra`` dict, the ``annotations`` dict), abstracted to one
                   opaque token.

The load-bearing properties (the ones the refinement and the spec depend on):

  set_values(fields), for a non-empty ``fields`` — model.py ``with_columns``:
    - CLASSIFIES each requested name against the derived columns the query
      exposes AT THAT MOMENT and keeps as ``values_select`` exactly the
      requested names that name none of them, in the requested order:
          values_select == own_columns(fields, extra_select, annotation_select)
    - NARROWS the derived columns it goes on to expose to exactly the requested
      ones, each family in the query's own order, a requested name being
      claimed by the leading family first:
          extra_select      == kept_leading(extra_select, fields)
          annotation_select == kept_trailing(annotation_select, fields,
                                             extra_select)
    - leaves the accumulated state alone (where clause and both derived-column
      DEFINITION dicts unchanged), i.e. the model's ``q.state == Old(q.state)``.
    These three equalities are checked on the pristine shape the compilation
    actually meets AND on an ALREADY-NARROWED query, so the model is pinned off
    the gold path too, not only on it.

  clone() — model.py ``detached_copy``:
    - returns a FRESH, DISTINCT object mirroring the original's column
      selection (all three families) in INDEPENDENT containers, including
      independent narrowing masks;
    - CARRIES the accumulated state (where clause, ``extra``, ``annotations``)
      onto the copy — the model's ``Result().state == q.state``; a brand-new
      blank Query does NOT carry it, which is why the model distinguishes a
      per-compilation copy from a fresh object; and
    - does NOT mutate the original: a later ``set_values`` on the copy leaves
      the original's ``values_select`` AND both of its un-narrowed derived
      families untouched.

  Domain (model.py ``with_columns`` Requires ``len(fields) > 0``):
    an EMPTY chosen list is a different operation on the real callee (it selects
    every concrete column of the query's own table and leaves the narrowing
    masks alone). Leg C records that divergence explicitly, which is why the
    model excludes it by precondition rather than claiming it.

Run inside the official SWE-bench container for the instance, where Django is
importable and an in-memory sqlite database is available. Exit 0 iff every
obligation holds.
"""
import itertools
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    # NO broad except guard: if Django cannot be configured in this environment
    # the check MUST fail loudly (non-zero exit), never silently SKIP/pass.
    django.setup()


# ---------------------------------------------------------------------------
# Executable transcriptions of the model's @Pure functions. The model defines
# each one back-recursively (on ``s.take(len(s) - 1)``) so an append-loop can
# track it; each is exactly the order-preserving filter below, by induction on
# the length of the recursed-on sequence.
# ---------------------------------------------------------------------------
def own_columns(fields, leading, trailing):
    """model.py own_columns — requested names naming no derived column."""
    return [f for f in fields if f not in leading and f not in trailing]


def kept_leading(leading, fields):
    """model.py kept_leading — leading derived columns that were requested."""
    return [x for x in leading if x in fields]


def kept_trailing(trailing, fields, leading):
    """model.py kept_trailing — trailing derived columns that were requested
    and not already claimed by a leading one of the same name."""
    return [x for x in trailing if x in fields and x not in leading]


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    _configure_django()

    from django.db import connection, models
    from django.db.models import Q, Value, IntegerField
    from django.core.exceptions import FieldError
    from django.db.models.sql.query import Query

    # A minimal model carrying several plain columns so a restricted column
    # list (values_select) is observable. The structural twin of the test's
    # ``ReservedName`` (name, order) plus the implicit primary key. It is
    # registered under a real installed app (``contenttypes``) so model
    # registration and schema creation succeed in the eval image.
    class Reserved(models.Model):
        name = models.CharField(max_length=32)
        order = models.IntegerField()

        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(Reserved)

    OWN_FIELDS = ["name", "order"]
    EXTRA_SQL = {"e1": "1+1", "e2": "2+2"}
    ANNOT_VAL = {"a1": 3, "a2": 4}

    def build(extra_keys, annot_keys, where=True, group_by=False):
        """A component sub-query exposing the named derived columns, in the
        order given, over an accumulated row restriction."""
        q = Query(Reserved)
        if where:
            q.add_q(Q(order__gt=1))
        for k in extra_keys:
            q.add_extra({k: EXTRA_SQL[k]}, None, None, None, None, None)
        for k in annot_keys:
            q.add_annotation(Value(ANNOT_VAL[k], output_field=IntegerField()), k)
        if group_by:
            q.group_by = True
        return q

    def requests(pool, sizes=(1, 2, 3)):
        """Every ordered selection of 1..3 distinct names from ``pool``."""
        out, seen = [], set()
        for n in sizes:
            for c in itertools.permutations(pool, min(n, len(pool))):
                if c not in seen:
                    seen.add(c)
                    out.append(list(c))
        return out

    def check_application(q, req, where_tag):
        """Assert the three ``with_columns`` value postconditions plus the
        state-preservation clause on ONE real set_values call."""
        pre_leading = list(q.extra_select)
        pre_trailing = list(q.annotation_select)
        pre_extra = dict(q.extra)
        pre_annot = set(q.annotations)
        pre_where = len(q.where.children)
        q.set_values(tuple(req))                       # REAL set_values()
        exp_own = own_columns(req, pre_leading, pre_trailing)
        exp_lead = kept_leading(pre_leading, req)
        exp_trail = kept_trailing(pre_trailing, req, pre_leading)
        assert list(q.values_select) == exp_own, (
            "%s: set_values(%r) on leading=%r trailing=%r gave values_select "
            "%r, model own_columns says %r"
            % (where_tag, req, pre_leading, pre_trailing,
               list(q.values_select), exp_own))
        assert list(q.extra_select) == exp_lead, (
            "%s: set_values(%r) left extra_select %r, model kept_leading says %r"
            % (where_tag, req, list(q.extra_select), exp_lead))
        assert list(q.annotation_select) == exp_trail, (
            "%s: set_values(%r) left annotation_select %r, model kept_trailing "
            "says %r" % (where_tag, req, list(q.annotation_select), exp_trail))
        assert dict(q.extra) == pre_extra, (
            "%s: set_values disturbed the extra definitions" % where_tag)
        assert set(q.annotations) == pre_annot, (
            "%s: set_values disturbed the annotation definitions" % where_tag)
        assert len(q.where.children) == pre_where, (
            "%s: set_values disturbed the accumulated row restriction"
            % where_tag)
        return 6

    checked = 0
    assertions = 0

    # ---- leg A: the classification/narrowing, on the pristine shape --------
    # Every combination of exposed leading families (none, one, two, in both
    # orders) x trailing families x every ordered request of up to three names
    # drawn from the query's own columns and its derived columns.
    extra_shapes = [[], ["e1"], ["e2"], ["e1", "e2"], ["e2", "e1"]]
    annot_shapes = [[], ["a1"], ["a1", "a2"], ["a2", "a1"]]
    for eks in extra_shapes:
        for aks in annot_shapes:
            for req in requests(OWN_FIELDS + list(eks) + list(aks)):
                assertions += check_application(build(eks, aks), req, "leg-A")
                checked += 1
    leg_a = checked

    # A shape with no derived columns at all takes the callee's shortcut path;
    # the model must agree there too (own columns == the whole chosen list).
    for req in requests(OWN_FIELDS):
        q = build([], [])
        q.set_values(tuple(req))
        assert list(q.values_select) == req, (
            "shortcut: set_values(%r) gave %r" % (req, list(q.values_select)))
        assert list(q.extra_select) == [] and list(q.annotation_select) == []
        assertions += 2
        checked += 1

    # A grouped shape reaches the callee's group_by branch before the
    # classification; the three equalities must still hold.
    q = build(["e1"], ["a1"], group_by=True)
    assertions += check_application(q, ["e1", "name", "a1"], "group-by")
    checked += 1

    # ---- leg B: the same three equalities on an ALREADY-NARROWED query -----
    # This is what makes the model discriminating rather than gold-shaped: after
    # one application the exposed derived columns are narrowed, so a name that
    # was derived is no longer classified as derived. The model says exactly
    # that, and the real callee must agree (or reject the request outright,
    # because the name is then taken for one of the query's own columns and the
    # query's table has no such column — the domain restriction the spec's
    # own-column classification inherits).
    leg_b = 0
    leg_b_rejected = 0
    for eks in (["e1", "e2"], ["e1"]):
        for aks in (["a1", "a2"], ["a1"]):
            pool = OWN_FIELDS + list(eks) + list(aks)
            for first in itertools.permutations(pool, 2):
                for second in itertools.permutations(pool, 2):
                    q = build(eks, aks)
                    q.set_values(tuple(first))
                    try:
                        assertions += check_application(q, list(second), "leg-B")
                    except FieldError:
                        # a narrowed-away name became an own column the table
                        # cannot serve: outside the modelled domain, and still
                        # NOT the outcome a single application would give.
                        leg_b_rejected += 1
                    leg_b += 1
                    checked += 1

    # ---- leg C: the empty chosen list is a DIFFERENT operation -------------
    # Recorded, not claimed: the model's ``len(fields) > 0`` precondition exists
    # because of exactly this divergence.
    q = build(["e1"], ["a1"])
    pre_lead, pre_trail = list(q.extra_select), list(q.annotation_select)
    q.set_values(())
    empty_diverges = (list(q.values_select) != []
                      or list(q.extra_select) != []
                      or list(q.annotation_select) != [])
    assert empty_diverges, (
        "an empty chosen list behaved like the model's non-empty case; the "
        "len(fields) > 0 precondition would then be gratuitous")
    assert list(q.extra_select) == pre_lead and list(q.annotation_select) == pre_trail, (
        "an empty chosen list unexpectedly narrowed the derived columns")
    assertions += 2
    checked += 1

    # ---- leg D: a name exposed by BOTH families -> the leading one wins ----
    q = Query(Reserved)
    q.add_extra({"x": "1+1"}, None, None, None, None, None)
    q.add_annotation(Value(9, output_field=IntegerField()), "x")
    assertions += check_application(q, ["x"], "leg-D-collision")
    checked += 1

    # ---- leg E: clone() — distinctness, independence, state carry ----------
    stateful = build(["e1", "e2"], ["a1", "a2"])
    where_before = len(stateful.where.children)
    extra_before = dict(stateful.extra)
    annot_before = set(stateful.annotations)
    lead_before = list(stateful.extra_select)
    trail_before = list(stateful.annotation_select)
    sclone = stateful.clone()                          # REAL Query.clone()
    assert sclone is not stateful, "clone() must return a distinct object"
    assert sclone.extra is not stateful.extra, (
        "clone() must not share the extra container")
    assert sclone.annotations is not stateful.annotations, (
        "clone() must not share the annotations container")
    assert tuple(sclone.values_select) == tuple(stateful.values_select), (
        "clone() must copy values_select: original %r clone %r"
        % (stateful.values_select, sclone.values_select))
    assert list(sclone.extra_select) == lead_before, (
        "clone() lost the leading derived columns: %r != %r"
        % (list(sclone.extra_select), lead_before))
    assert list(sclone.annotation_select) == trail_before, (
        "clone() lost the trailing derived columns: %r != %r"
        % (list(sclone.annotation_select), trail_before))
    assert len(sclone.where.children) == where_before, (
        "clone() lost the accumulated row restriction: %d != %d"
        % (len(sclone.where.children), where_before))
    assert dict(sclone.extra) == extra_before, (
        "clone() lost the extra definitions: %r != %r"
        % (sclone.extra, extra_before))
    assert set(sclone.annotations) == annot_before, (
        "clone() lost the annotation definitions: %r != %r"
        % (set(sclone.annotations), annot_before))
    # applying a column list to the copy leaves the ORIGINAL untouched — in
    # particular its derived columns stay UN-NARROWED, which is what lets a
    # later compilation choose a different list (model.py clause (2)).
    sclone.set_values(("e1", "name"))                  # REAL set_values()
    assert tuple(stateful.values_select) == (), (
        "set_values on the copy leaked into the shared sub-query: %r"
        % (stateful.values_select,))
    assert list(stateful.extra_select) == lead_before, (
        "set_values on the copy narrowed the shared sub-query's leading "
        "derived columns: %r != %r"
        % (list(stateful.extra_select), lead_before))
    assert list(stateful.annotation_select) == trail_before, (
        "set_values on the copy narrowed the shared sub-query's trailing "
        "derived columns: %r != %r"
        % (list(stateful.annotation_select), trail_before))
    assert stateful.extra_select_mask is None and sclone.extra_select_mask is not None, (
        "the narrowing masks are not independent across clone()")
    assert len(sclone.where.children) == where_before, (
        "set_values disturbed the accumulated row restriction on the copy")
    assert dict(sclone.extra) == extra_before, (
        "set_values disturbed the extra definitions on the copy")
    blank = Query(Reserved)
    assert len(blank.where.children) != where_before or where_before == 0, (
        "a fresh Query unexpectedly carries the accumulated row restriction")
    assert not blank.extra and not blank.annotations, (
        "a fresh Query unexpectedly carries the derived-column definitions")
    assertions += 18
    checked += 1

    # ---- leg F: a second application NEVER agrees with a single one --------
    # The spec pins the compilation's outcome as a function of the SHARED
    # sub-query's UN-NARROWED derived columns and the chosen list. This leg
    # measures, on the real callee, that applying a narrower list first and the
    # chosen list second does not reach that outcome for ANY of these shapes —
    # so the specification is right to turn such an implementation down.
    diverged = agreed = 0
    for eks in (["e1", "e2"], ["e1"]):
        for aks in (["a1", "a2"], ["a1"]):
            pool = OWN_FIELDS + list(eks) + list(aks)
            for outer in itertools.permutations(pool, len(pool)):
                shared = build(eks, aks)
                pinned = own_columns(list(outer), list(shared.extra_select),
                                     list(shared.annotation_select))
                single = shared.clone()
                single.set_values(tuple(outer))
                assert list(single.values_select) == pinned, (
                    "leg-F: a single application to a faithful copy missed the "
                    "pinned outcome %r (got %r)"
                    % (pinned, list(single.values_select)))
                twice = shared.clone()
                twice.set_values((outer[-1],))
                try:
                    twice.set_values(tuple(outer))
                    reached = list(twice.values_select)
                except FieldError:
                    reached = "<rejected outright>"
                if reached == pinned:
                    agreed += 1
                else:
                    diverged += 1
                assertions += 1
                checked += 1
    assert agreed == 0, (
        "leg-F: %d of %d shapes reached the pinned outcome by applying the "
        "chosen list twice; the specification's rejection of that shape would "
        "then be too strong" % (agreed, agreed + diverged))
    assertions += 1

    # Anti-vacuity guard: a passing run MUST have executed a positive number of
    # assertions against the real callees. If nothing ran, fail loudly.
    if checked == 0 or assertions == 0 or leg_a == 0 or leg_b == 0 or diverged == 0:
        print("G-AX FAIL: no obligations executed (checked=%d, assertions=%d, "
              "leg_a=%d, leg_b=%d, diverged=%d)"
              % (checked, assertions, leg_a, leg_b, diverged))
        return 1

    print("G-AX OK: %d assertions over %d shapes, 0 violations. clone()/"
          "set_values() deep models (A-reference) sound against the real "
          "django.db.models.sql.query.Query: the classification/narrowing "
          "equalities (own_columns / kept_leading / kept_trailing) hold on %d "
          "pristine shapes AND on %d already-narrowed ones (%d of those the "
          "callee rejects outright, still not the pinned outcome); clone() "
          "returns a distinct object with independent containers and masks, "
          "carries the where/extra/annotation state, and never narrows the "
          "shared sub-query; an empty chosen list diverges (hence the "
          "len(fields) > 0 precondition); and %d/%d shapes show a second "
          "application never reaching the single-application outcome."
          % (assertions, checked, leg_a, leg_b, leg_b_rejected,
             diverged, diverged + agreed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
