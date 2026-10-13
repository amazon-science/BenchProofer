#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12965.

This bundle has NO consumed axioms. Its single kind-A obligation is the
**A-reference** deep model `activate` (Solution.lean pure region), which models
the refcount-state side effect of the unchanged callee `Query.get_initial_alias`
— the callee the patch *adds a call to* inside `single_alias`. G-AX validates
that deep model against the REAL callee at base_commit:

    refcount state []        ->  [1]       (empty alias_map: base table joined fresh)
    refcount state (h :: t)  ->  (h+1)::t  (base table already present: ref bumped)

both of which are the single total equation
`withTarget rc = (rc.headD 0 + 1) :: rc.tail`,

where the refcount state is  [alias_refcount[t] for t in alias_map]  taken in
alias_map insertion order (head = base table; mapping.md §2).

IMPORTANT — G-AX runs against the UNPATCHED base_commit source (no `apply_gold`),
so it must NOT touch `SQLDeleteCompiler.single_alias`: that is the function under
spec / under change, and at base_commit it lacks the very `get_initial_alias()`
call the patch introduces. Per SPEC_GUIDE §0.7 the function under change is never
axiom-checked; its patched behaviour is the job of G-CONF (run WITH the gold
patch applied) and the agentic G-EQ. G-AX here checks ONLY the A-reference
callee.

On the tested paths the real callee reads ONLY `alias_map` (ordered keys; head =
base table) and `alias_refcount`, never the Join *values* (`get_initial_alias`
non-empty branch -> `base_table` + `ref_alias`). So non-empty reference-count
states are driven exactly via synthetic dicts. The empty state (the F2P
full-delete case) routes through the real `join(BaseTable(...))` branch and is
checked with a real model.

Imports only Django (the framework the gold patch lives in), configured against
in-memory sqlite. Exit 0 iff every observation matches the model.
"""
import sys


# ---- the deep model under check (lock-step with Solution.lean `withTarget`) ----
def activate(rc):
    """Reference impl of Solution.lean's
    `withTarget rc = (rc.headD 0 + 1) :: rc.tail`. On the empty list
    `List.headD 0` is 0 and `List.tail` is [], so this yields [1] there."""
    head = rc[0] if rc else 0                 # rc.headD 0
    return [head + 1] + list(rc[1:])          # (… + 1) :: rc.tail


def refcount_state(query):
    """The Lean carrier: [alias_refcount[t] for t in alias_map] in map order."""
    return [query.alias_refcount[t] for t in query.alias_map]


def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()

    from django.db import models

    class Author(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "ax_app"

    return Author


def make_query_with_state(Query, Author, refcounts):
    """Real Query whose refcount state == `refcounts` (alias_map order). Empty
    -> a genuinely empty Query so get_initial_alias hits its join(BaseTable)
    branch; non-empty -> synthetic dicts (values never read on tested paths)."""
    q = Query(Author)
    if not refcounts:
        return q
    alias_map, alias_refcount = {}, {}
    for i, c in enumerate(refcounts):
        t = "t%d" % i
        alias_map[t] = object()
        alias_refcount[t] = c
    q.alias_map = alias_map
    q.alias_refcount = alias_refcount
    q.__dict__.pop("base_table", None)
    return q


def main():
    Author = setup_django()
    from django.db.models.sql.query import Query

    checks = 0

    def check_activate(state):
        nonlocal checks
        q = make_query_with_state(Query, Author, state)
        pre = refcount_state(q)
        assert pre == state, ("state setup mismatch: wanted %r got %r"
                              % (state, pre))
        expected = activate(pre)
        q.get_initial_alias()                            # REAL unchanged callee
        post = refcount_state(q)
        assert post == expected, (
            "activate deep model unsound on pre=%r: real get_initial_alias "
            "post=%r, model activate(pre)=%r" % (pre, post, expected))
        checks += 1

    # Boundary + representative reference-count states (head = base table).
    states = [
        [],            # empty alias_map: the F2P full-table-delete case
        [0], [1], [2], [3],
        [0, 0], [1, 0], [0, 1], [1, 1], [2, 1],
        [1, 1, 1], [3, 0, 0], [0, 0, 1], [2, 0, 1, 0],
    ]
    for st in states:
        check_activate(st)

    print("G-AX OK: activate deep model (== Query.get_initial_alias refcount "
          "side effect) sound on %d real-Query observations" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
