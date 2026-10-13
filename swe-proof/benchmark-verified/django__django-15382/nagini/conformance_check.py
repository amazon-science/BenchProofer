#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15382 (nagini).

SHADOW: the impl region of model.py `render_exists`, copied verbatim below
with the contract calls stripped (one `Assert(...)` line removed; the
Requires/Ensures/Exsures live outside the impl region). The model IS Python:
a try/except case analysis over the axiomatized sub-selection renderer. The
sole @ContractOnly callee, `render_inner`, calls the REAL repo function per
the contract: `Subquery.as_sql`, invoked exactly as the predicate renderer
invokes it (build the inner existence query for the current inner selection,
then call the super-class renderer on it), with Django's matches-nothing
signal translated to the shadow's `EmptyResultSet` and the returned fragment
translated to code points.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.db.models.expressions.Exists.as_sql` (the gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable).

TYPE BRIDGE (mapping.md section 2):
  * SQL fragment str <-> List[int] of code points: s <-> [ord(c) for c in s];
    the empty str '' <-> [] (len == 0).
  * `negated: int` in {0,1} <-> the predicate's negation flag (bool).
  * `satisfiable: int` in {0,1} <-> whether the concrete inner selection
    compiles (1) or signals matches-nothing (0). Bridged by binding, per
    trial, a concrete SATISFIABLE inner queryset for satisfiable == 1 and a
    concrete UNSATISFIABLE one (an empty selection, e.g. .none() or an
    empty-in filter) for satisfiable == 0. Both the shadow's real callee and
    the oracle are driven with the SAME bound queryset, so the abstract input
    and the concrete run agree by construction.
  * only the sql component of the (sql, params) 2-tuple is modeled; params is
    unobserved.
  * Django's EmptyResultSet <-> the shadow's user-defined EmptyResultSet
    (observationally the same raise).

INPUT DOMAIN: Requires(satisfiable in {0,1} and negated in {0,1}) -- a
4-point abstract domain. Boundary = all four combinations over every
(satisfiable-pool x unsatisfiable-pool) pairing of structurally distinct
concrete inner querysets. Fuzz = randomly generated filter/exclude/values
chains for the satisfiable slot and randomly built empty selections for the
unsatisfiable slot, all four abstract combinations checked per trial.

>= 1e5 Requires-satisfying inputs: 4 checks x (boundary pairings + 25_000
fuzz trials) > 100_000. Pinned fuzz seed: 15382 (recorded here; plain
`random`, no hypothesis needed for a 4-point abstract domain).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import json
import random
import sys

SEED = 15382
N_FUZZ_TRIALS = 25_000


# --- the shadow's matches-nothing signal (model.py user-defined stand-in) ----

class EmptyResultSet(Exception):
    pass


# --- real-callee plumbing -----------------------------------------------------

_ctx = {}


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
    from django.db import connection
    from django.db.models import Exists
    from django.contrib.auth.models import User
    from django.core.exceptions import EmptyResultSet as DjangoEmptyResultSet
    from django.db.models.expressions import Subquery
    _ctx.update(
        connection=connection,
        Exists=Exists,
        User=User,
        DjangoEmptyResultSet=DjangoEmptyResultSet,
        Subquery=Subquery,
        compiler=User.objects.all().query.get_compiler(using='default'),
        # per-trial binding: abstract satisfiable value -> concrete queryset
        current={},
    )


def _inner_query(qs):
    """Build the inner existence query exactly as the predicate renderer does
    before delegating to the super-class renderer."""
    ex = _ctx['Exists'](qs)
    try:
        return ex, ex.query.exists(using=_ctx['connection'].alias)
    except TypeError:
        # signature drift guard (parameter named ``using`` at this version)
        return ex, ex.query.exists(_ctx['connection'].alias)


def render_inner(satisfiable):
    """The @ContractOnly callee of the shadow: calls the REAL, UNCHANGED
    super-class sub-selection renderer (Subquery.as_sql) on the concrete
    queryset bound for this trial's `satisfiable` value, bridging str ->
    List[int] and the Django signal -> the shadow's EmptyResultSet."""
    qs = _ctx['current'][satisfiable]
    ex, query = _inner_query(qs)
    try:
        sql, params = _ctx['Subquery'].as_sql(
            ex, _ctx['compiler'], _ctx['connection'], query=query)
    except _ctx['DjangoEmptyResultSet']:
        raise EmptyResultSet()
    return [ord(ch) for ch in sql]


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def render_exists(satisfiable, negated):
    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        # Inner selection is unsatisfiable. A negated existence predicate over an
        # empty selection is universally true -> return normally (here, the empty
        # always-true fragment). A non-negated one can never hold -> re-propagate.
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
    return sql


# --- oracle: the REAL patched Exists.as_sql -----------------------------------

def oracle_render_exists(satisfiable, negated):
    """Run the real modeled function on the same bound queryset. Returns
    (raised, codes): raised == the matches-nothing signal escaped; codes ==
    the bridged sql component (params unobserved per mapping.md)."""
    qs = _ctx['current'][satisfiable]
    ex = _ctx['Exists'](qs, negated=bool(negated))
    try:
        sql, params = ex.as_sql(_ctx['compiler'], _ctx['connection'])
    except _ctx['DjangoEmptyResultSet']:
        return True, None
    return False, [ord(ch) for ch in sql]


def shadow_render_exists(satisfiable, negated):
    try:
        return False, render_exists(satisfiable, negated)
    except EmptyResultSet:
        return True, None


# --- input generators: concrete querysets behind the abstract 4-point domain --

def satisfiable_pool(User):
    return [
        lambda: User.objects.all(),
        lambda: User.objects.filter(username='alice'),
        lambda: User.objects.filter(id__gt=7),
        lambda: User.objects.exclude(email='a@b.c'),
        lambda: User.objects.filter(is_active=True, id__lt=100),
        lambda: User.objects.filter(id__in=[1, 2, 3]),
        lambda: User.objects.filter(username__startswith='q').exclude(id=5),
        lambda: User.objects.order_by('-id'),
    ]


def unsatisfiable_pool(User):
    return [
        lambda: User.objects.none(),
        lambda: User.objects.filter(username='bob').none(),
        lambda: User.objects.none().filter(id__gt=3),
        lambda: User.objects.filter(id__in=[]),
    ]


def fuzz_satisfiable(User, rng):
    qs = User.objects.all()
    for _ in range(rng.randint(0, 3)):
        pick = rng.randrange(5)
        if pick == 0:
            qs = qs.filter(id__gt=rng.randint(-5, 500))
        elif pick == 1:
            qs = qs.filter(username='u%d' % rng.randint(0, 999))
        elif pick == 2:
            qs = qs.exclude(id=rng.randint(0, 500))
        elif pick == 3:
            qs = qs.filter(id__in=[rng.randint(0, 99)
                                   for _ in range(rng.randint(1, 4))])
        else:
            qs = qs.filter(is_active=bool(rng.getrandbits(1)))
    return qs


def fuzz_unsatisfiable(User, rng):
    pick = rng.randrange(3)
    if pick == 0:
        return fuzz_satisfiable(User, rng).none()
    if pick == 1:
        return User.objects.none().filter(id__gt=rng.randint(0, 99))
    return fuzz_satisfiable(User, rng).filter(id__in=[])


# --- differential driver -------------------------------------------------------

def check_all_combos():
    """Compare shadow vs oracle over the full 4-point abstract domain for the
    currently bound querysets. Returns the number of checks, or aborts."""
    for satisfiable in (0, 1):
        for negated in (0, 1):
            s_raised, s_codes = shadow_render_exists(satisfiable, negated)
            r_raised, r_codes = oracle_render_exists(satisfiable, negated)
            if (s_raised, s_codes) != (r_raised, r_codes):
                print("DISAGREEMENT\n  satisfiable=%d negated=%d\n"
                      "  inner querysets: sat=%r unsat=%r\n"
                      "  shadow: raised=%s codes=%r\n"
                      "  real:   raised=%s codes=%r"
                      % (satisfiable, negated,
                         str(_ctx['current'][1].query)
                         if satisfiable == 1 else '<bound sat qs>',
                         '<empty selection>',
                         s_raised, s_codes, r_raised, r_codes))
                sys.exit(1)
    return 4


def main():
    _setup_django()
    User = _ctx['User']
    checked = 0

    # boundary: every satisfiable-pool x unsatisfiable-pool pairing
    for mk_sat in satisfiable_pool(User):
        for mk_unsat in unsatisfiable_pool(User):
            _ctx['current'] = {1: mk_sat(), 0: mk_unsat()}
            checked += check_all_combos()

    # fuzz (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_TRIALS):
        _ctx['current'] = {1: fuzz_satisfiable(User, rng),
                           0: fuzz_unsatisfiable(User, rng)}
        checked += check_all_combos()

    print("G-CONF OK: shadow impl == real patched renderer on %d checks "
          "(boundary + %d fuzz trials x 4 combos, seed %d)."
          % (checked, N_FUZZ_TRIALS, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee -> real Subquery.as_sql)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
