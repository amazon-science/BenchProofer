#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12965 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Old/Implies/Acc) stripped. The model IS plain Python:
`TableRefs` is an ordinary two-field object, the @Pure helper `active_tables`
copies over as a plain function, and the two modeled functions
(`references_single_table`, `delete_uses_subquery`) run directly. There are no
@ContractOnly callees and no PSeq usage, so no sequence shim is needed.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`django.db.models.sql.compiler.SQLDeleteCompiler.single_alias` (the changed
predicate) and its unchanged caller `SQLDeleteCompiler.as_sql` (whose
direct-vs-subquery choice is the modeled observable). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched modules importable. Django is configured with an in-memory sqlite
database; SQL is only compiled, never executed, so no schema is created.

Type bridge (mapping.md section 2): the rich `sql.Query` alias bookkeeping is
abstracted to the two quantities the predicate reads —
  primary_present  <->  base table alias present in query.alias_map with
                        query.alias_refcount[base] > 0
  extra_active     <->  count of non-base aliases t in query.alias_map with
                        query.alias_refcount[t] > 0
A concrete delete-query state realizing a given abstract (primary_present,
extra_active) pair is built by direct alias-map manipulation, with fuzzed
UNOBSERVED concrete detail: base/extra reference-count magnitudes and any
number of inactive (zero-refcount) extra aliases. The oracle observations are
lifted back through the same abstraction:
  references_single_table(q) <-> compiler.single_alias  (bool, identical)
  post-state of q            <-> abstraction of the real query after the
                                 predicate is read (the Ensures-visible frame)
  delete_uses_subquery(q)    <-> whether the compiled DELETE SQL contains a
                                 nested SELECT (the F2P discriminator)

Input domain: the Requires are access permissions plus extra_active >= 0, so
every (primary_present, extra_active) pair with extra_active >= 0 is
Requires-satisfying; the fuzz additionally varies the concrete realization.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz states.
Pinned fuzz seed: 12965.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import re
import sys

SEED = 12965
N_FUZZ = 100_000
SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)


# --- shadow: model.py impl regions, verbatim, contract calls stripped --------

class TableRefs:
    def __init__(self, primary_present, extra_active):
        self.primary_present = primary_present
        self.extra_active = extra_active


def active_tables(primary_present, extra_active):
    return (1 if primary_present else 0) + extra_active


def references_single_table(query):
    query.primary_present = True
    return active_tables(query.primary_present, query.extra_active) == 1


def delete_uses_subquery(query):
    if references_single_table(query):
        return False
    return True


# --- oracle plumbing: drive the REAL patched delete compiler ------------------

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

    from django.db import models

    class Thing(models.Model):
        name = models.CharField(max_length=10)

        class Meta:
            app_label = "confcheck"

    return Thing


def build_state(Thing, primary_present, extra_active, extra_inactive,
                base_bumps, extra_bump_plan):
    """Build a real DeleteQuery whose alias bookkeeping abstracts to
    (primary_present, extra_active). extra_inactive / base_bumps /
    extra_bump_plan vary the UNOBSERVED concrete detail: zero-refcount
    aliases in the map, and refcount magnitudes above 1."""
    from django.db.models.sql.subqueries import DeleteQuery
    from django.db.models.sql.datastructures import BaseTable

    q = DeleteQuery(Thing)
    base = Thing._meta.db_table
    need_base_entry = (primary_present or extra_active or extra_inactive
                       or base_bumps)
    if need_base_entry:
        # register the base alias first so extras are genuinely additional
        q.get_initial_alias()
        for _ in range(base_bumps):
            q.ref_alias(base)
        if not primary_present:
            # keep the base alias IN the map but with a zero refcount
            while q.alias_refcount[base] > 0:
                q.unref_alias(base)
    # else: the pristine whole-table delete — alias map entirely empty
    idx = 0
    for k in range(extra_active):
        alias = q.join(BaseTable("xt_%d" % idx, None))
        idx += 1
        for _ in range(extra_bump_plan[k % len(extra_bump_plan)]
                       if extra_bump_plan else 0):
            q.ref_alias(alias)
    for _ in range(extra_inactive):
        alias = q.join(BaseTable("xt_%d" % idx, None))
        idx += 1
        q.unref_alias(alias)
    return q, base


def abstract(q, base):
    """Lift a real query's alias bookkeeping to the model carrier."""
    pp = bool(q.alias_map) and q.alias_refcount.get(base, 0) > 0
    ea = sum(1 for t in q.alias_map
             if t != base and q.alias_refcount[t] > 0)
    return pp, ea


def check_state(Thing, connection, pp, ea, ei, bb, ebp):
    """Run shadow and oracle on one abstract state (with one concrete
    realization); return an error string on disagreement, else None."""
    q, base = build_state(Thing, pp, ea, ei, bb, ebp)
    got_pp, got_ea = abstract(q, base)
    if (got_pp, got_ea) != (pp, ea):
        return ("STATE-CONSTRUCTION ERROR: wanted (%r,%r) built (%r,%r) "
                "refcounts=%r" % (pp, ea, got_pp, got_ea,
                                  dict(q.alias_refcount)))
    q_for_sql = q.clone()

    # (1) the changed predicate itself
    shadow_q = TableRefs(pp, ea)
    shadow_single = references_single_table(shadow_q)
    compiler = q.get_compiler(using="default", connection=connection)
    real_single = compiler.single_alias
    if shadow_single is not real_single:
        return ("DISAGREEMENT (predicate)\n  input: primary_present=%r "
                "extra_active=%r (inactive=%r base_bumps=%r)\n"
                "  shadow=%r\n  real=%r  refcounts=%r"
                % (pp, ea, ei, bb, shadow_single, real_single,
                   dict(q.alias_refcount)))

    # (2) the Ensures-visible post-state frame
    real_pp2, real_ea2 = abstract(q, base)
    if (shadow_q.primary_present, shadow_q.extra_active) != (real_pp2, real_ea2):
        return ("DISAGREEMENT (post-state)\n  input: primary_present=%r "
                "extra_active=%r (inactive=%r base_bumps=%r)\n"
                "  shadow=(%r,%r)\n  real=(%r,%r)"
                % (pp, ea, ei, bb, shadow_q.primary_present,
                   shadow_q.extra_active, real_pp2, real_ea2))

    # (3) the caller's observable: direct form vs nested-SELECT subquery form
    shadow_sub = delete_uses_subquery(TableRefs(pp, ea))
    compiler2 = q_for_sql.get_compiler(using="default", connection=connection)
    sql, _params = compiler2.as_sql()
    real_sub = bool(SELECT_RE.search(sql))
    if shadow_sub is not real_sub:
        return ("DISAGREEMENT (caller observable)\n  input: "
                "primary_present=%r extra_active=%r (inactive=%r "
                "base_bumps=%r)\n  shadow uses_subquery=%r\n"
                "  real uses_subquery=%r  sql=%r"
                % (pp, ea, ei, bb, shadow_sub, real_sub, sql))
    return None


def boundary_states():
    states = []
    for pp in (False, True):
        for ea in (0, 1, 2, 3, 7):
            for ei in (0, 1, 3):
                for bb in (0, 1, 4):
                    states.append((pp, ea, ei, bb, [0, 2]))
    return states


def main():
    Thing = setup_django()
    from django.db import connection

    checked = 0
    boundary = boundary_states()
    for pp, ea, ei, bb, ebp in boundary:
        err = check_state(Thing, connection, pp, ea, ei, bb, ebp)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        pp = rng.random() < 0.5
        ea = rng.choice((0, 0, 0, 1, 1, 2, 3, rng.randint(0, 10)))
        ei = rng.choice((0, 0, 1, 2, rng.randint(0, 5)))
        bb = rng.choice((0, 0, 1, rng.randint(0, 6)))
        ebp = [rng.randint(0, 3) for _ in range(rng.randint(1, 3))]
        err = check_state(Thing, connection, pp, ea, ei, bb, ebp)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched delete compiler on %d "
          "states (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
