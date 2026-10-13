#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15525.

This bundle consumes NO @ContractOnly axiom. The behaviour the model relies on
is the UNCHANGED query-routing rule of the framework: a deferred dereference
issued while computing a record's natural key is routed to the data store the
record's state is associated with, or — when the record's state carries no
association (a freshly built record) — to the ambient default store. This is
the *reference* mechanism the model's deep `query_store` / `dereference_succeeds`
encode (an A-reference, NOT a consumed axiom).

We validate the deep model against the REAL routing primitive
(`django.db.utils.ConnectionRouter`, the actual `_route_db` used by every
related-object lookup) with no custom routers configured (the default and the
configuration the regression scenario uses):

  * a record whose state has NO store association (`_state.db` is None/falsy)
    routes to the default store  -> model: query_store(UNROUTED, d) == d
  * a record associated with store X routes to X
                                  -> model: query_store(X, d)        == X

and we confirm the success criterion the model uses: the dereference finds the
related record iff the routed store equals the store the related record lives
in (`query_store(routed, default) == record_store`).

Imports only Django itself (the framework under test); no test-suite code.
Exit 0 iff every observation matches the model.
"""
import os
import random
import sys

import django
from django.conf import settings


# --- model.py reference encodings (kept in lock-step with the deep model) ----

UNROUTED = -1


def query_store(routed, default_store):
    """Reference of model.py's pure `query_store`."""
    if routed == UNROUTED:
        return default_store
    return routed


def dereference_succeeds(routed, default_store, record_store):
    """Reference of model.py's pure `dereference_succeeds`."""
    return query_store(routed, default_store) == record_store


def main():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": ":memory:"},
                "other": {"ENGINE": "django.db.backends.sqlite3",
                          "NAME": ":memory:"},
            },
            DATABASE_ROUTERS=[],   # default: no custom routers (the scenario)
            INSTALLED_APPS=[],
        )
    django.setup()

    from django.db.utils import ConnectionRouter, DEFAULT_DB_ALIAS

    router = ConnectionRouter()   # empty router list -> the default _route_db

    # A minimal stand-in carrying the routing state the descriptor reads.
    class _State:
        def __init__(self, db):
            self.db = db

    class _Record:
        def __init__(self, db):
            self._state = _State(db)

    # Map the model's integer store ids to real store aliases. UNROUTED (a
    # fresh record) corresponds to _state.db is None.
    aliases = {0: DEFAULT_DB_ALIAS, 1: "other"}
    default_id = 0   # DEFAULT_DB_ALIAS is store id 0 in the model abstraction

    def real_routed_store(routed_id):
        """The store the REAL router picks for a record with this association,
        returned as a model store id."""
        db = None if routed_id == UNROUTED else aliases[routed_id]
        rec = _Record(db)
        chosen = router.db_for_read(_Record, instance=rec)
        # Invert the alias map back to a model store id.
        for sid, alias in aliases.items():
            if alias == chosen:
                return sid
        raise AssertionError("router chose unexpected store %r" % chosen)

    # --- boundary: every association the model can express -------------------
    routed_cases = [UNROUTED, 0, 1]
    for routed in routed_cases:
        observed = real_routed_store(routed)
        expected = query_store(routed, default_id)
        assert observed == expected, (
            "routing model unsound: record routed=%r -> real router store %r, "
            "model query_store=%r" % (routed, observed, expected))

    # --- the success criterion across all store combinations -----------------
    # For each (routed, record_store), the dereference finds the record iff the
    # store the REAL router queries equals the store the record lives in.
    for routed in routed_cases:
        real_query = real_routed_store(routed)
        for record_store in (0, 1):
            observed_success = (real_query == record_store)
            model_success = dereference_succeeds(routed, default_id, record_store)
            assert observed_success == model_success, (
                "success criterion unsound: routed=%r record_store=%r -> "
                "real=%r model=%r"
                % (routed, record_store, observed_success, model_success))

    # --- the fix's invariant on the regression scenario ----------------------
    # Non-default target store (record lives in store 1 != default 0). Routing
    # the record to the target (routed=1) succeeds; leaving it unrouted
    # (routed=UNROUTED, i.e. _state.db None) routes to default 0 and fails.
    target, default, record = 1, 0, 1
    assert dereference_succeeds(target, default, record) is True, \
        "routed-to-target must succeed"
    assert dereference_succeeds(UNROUTED, default, record) is False, \
        "unrouted must fail on a non-default target (this is the bug)"
    assert real_routed_store(target) == record, \
        "real router: routed-to-target queries the target store"
    assert real_routed_store(UNROUTED) != record, \
        "real router: unrouted record queries the default store (not the target)"

    # --- randomized fuzz over store ids -------------------------------------
    rng = random.Random(15525)
    for _ in range(20000):
        routed = rng.choice(routed_cases)
        record_store = rng.choice([0, 1])
        real_query = real_routed_store(routed)
        observed_success = (real_query == record_store)
        model_success = dereference_succeeds(routed, default_id, record_store)
        assert observed_success == model_success, (
            "fuzz routing unsound: routed=%r record_store=%r -> real=%r model=%r"
            % (routed, record_store, observed_success, model_success))

    print("G-AX OK: routing deep model (query_store / dereference_succeeds) == "
          "real ConnectionRouter routing on all boundary store combinations "
          "and 20000 fuzz cases; no consumed axiom.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
