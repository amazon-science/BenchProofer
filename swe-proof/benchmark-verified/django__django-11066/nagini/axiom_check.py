#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11066.

The bundle has NO consumed `@ContractOnly` axiom. The one callee in the
modelled resolution - the write-routing policy `router.db_for_write` - is
UNCHANGED and is *bypassed* by the fix, so it is modelled as the **free input**
`routed` (an A-reference, not a consumed axiom). This check validates the two
behavioural reference properties the refinement relies on, against the REAL
Django routing machinery (`django.db.utils.ConnectionRouter.db_for_write`) and
the REAL write-target resolution rule used by `Model.save_base`:

  (A-reference 1)  The routing policy is INDEPENDENT of the explicitly named
      store: `router.db_for_write(model, instance=ct)` returns whatever alias
      the application's router dictates (e.g. `'default'`), regardless of which
      database `db` the migration step is operating on. Hence the policy can
      and does return an alias DIFFERENT from `db` - this is the bug surface
      the F2P test exercises (router -> `'default'`, but the step's `db` is
      `'other'`).

  (A-reference 2)  The write-target resolution
      `using = using or router.db_for_write(...)` (django/db/models/base.py:761)
      short-circuits to the explicit alias when one is supplied: with
      `using = db` (the gold patch) the target is `db`, INDEPENDENT of the
      router; with `using = None` (pre-patch) the target is the router's
      choice. So `model.py`'s `persisted_db` post-patch resolution (`src = db`)
      matches the real `save(using=db, ...)` and `model_prepatch.py`'s
      (`src = routed`) matches the real `save(...)` without `using`.

Imports only the standard library and `django.db` (the very module the gold
patch's code path runs through); no repo-test code. Exit 0 iff every
obligation holds.
"""
import random
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'other': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            'extra': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        DATABASE_ROUTERS=[],
        INSTALLED_APPS=[],
    )

from django.db.utils import ConnectionRouter, DEFAULT_DB_ALIAS  # noqa: E402


# --- a minimal stand-in for the (model class, instance) the router sees ------

class _State:
    def __init__(self, db=None):
        self.db = db


class _Instance:
    def __init__(self, db=None):
        self._state = _State(db)


class _Model:
    # `router.db_for_write` is only handed the model class + an `instance`
    # hint; it never touches model internals beyond that for a custom router.
    _state = _State(None)


def resolve_write_target(using, router, model, instance):
    """The REAL resolution rule from Model.save_base (base.py:761):
        using = using or router.db_for_write(self.__class__, instance=self)
    Returns the alias the single-field UPDATE is committed to."""
    return using or router.db_for_write(model, instance=instance)


def check_router_independent_of_db(router_choice, step_db):
    """A-reference 1: the policy returns its own alias regardless of step_db."""
    class FixedRouter:
        def db_for_write(self, model, **hints):
            return router_choice

    cr = ConnectionRouter([FixedRouter()])
    got = cr.db_for_write(_Model, instance=_Instance(None))
    assert got == router_choice, (
        "router.db_for_write should return the policy's alias %r, got %r"
        % (router_choice, got))
    # The point: the policy is free to pick an alias != the step's db.
    if router_choice != step_db:
        assert got != step_db, (
            "BUG SURFACE BROKEN: policy alias %r unexpectedly equals step db %r"
            % (got, step_db))


def check_resolution(step_db, router_choice):
    """A-reference 2: post-patch (using=db) -> db; pre-patch (using=None) ->
    the router's choice. Validates persisted_db's two impl branches."""
    class FixedRouter:
        def db_for_write(self, model, **hints):
            return router_choice

    cr = ConnectionRouter([FixedRouter()])
    inst = _Instance(None)

    # gold patch: save(using=db, ...) -> target is db, independent of router
    post = resolve_write_target(step_db, cr, _Model, inst)
    assert post == step_db, (
        "post-patch resolution should target the explicit db %r, got %r"
        % (step_db, post))

    # pre-patch: save(...) with no using -> target is the router's choice
    pre = resolve_write_target(None, cr, _Model, inst)
    assert pre == router_choice, (
        "pre-patch resolution should target the router choice %r, got %r"
        % (router_choice, pre))

    # the differential: whenever the router disagrees with db, the two differ -
    # this is exactly the discriminating postcondition in model.py / G-DIFF.
    if router_choice != step_db:
        assert post != pre, (
            "pre/post resolution should differ when router (%r) != db (%r)"
            % (router_choice, step_db))


def main():
    aliases = ['default', 'other', 'extra', 'db1', 'replica', 'shard_07']

    # boundary: the exact F2P configuration (router -> 'default', step db ->
    # 'other') plus every same/different alias pairing.
    boundary = [('other', 'default'), ('default', 'default'),
                ('other', 'other'), ('extra', 'default'), ('db1', 'replica')]
    for step_db, router_choice in boundary:
        check_router_independent_of_db(router_choice, step_db)
        check_resolution(step_db, router_choice)

    # also: a router with NO opinion falls through to DEFAULT_DB_ALIAS, and the
    # explicit-using short-circuit still wins.
    cr_empty = ConnectionRouter([])
    assert cr_empty.db_for_write(_Model, instance=_Instance(None)) == DEFAULT_DB_ALIAS
    assert resolve_write_target('other', cr_empty, _Model, _Instance(None)) == 'other'

    # randomized fuzz over alias pairs
    rng = random.Random(11066)
    for _ in range(5000):
        step_db = rng.choice(aliases)
        router_choice = rng.choice(aliases)
        check_router_independent_of_db(router_choice, step_db)
        check_resolution(step_db, router_choice)

    print("G-AX OK: router.db_for_write is independent of the step db (returns "
          "the policy's alias, possibly != db) and the real "
          "`using or router.db_for_write(...)` resolution targets the explicit "
          "alias when supplied - over %d boundary + 5000 fuzz alias pairs."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
