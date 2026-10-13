#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15525 (nagini backend).

Refutation target
-----------------
Does the MODEL (`model.py:build_with_natural_key`) agree with the REAL PATCHED
repository function it claims to model? No other gate covers that leg.

ORACLE CHOICE: the REAL patched function is CALLED, not transliterated.
------------------------------------------------------------------------
Oracle = `django.core.serializers.base.build_instance(Model, data, db)`
(`django/core/serializers/base.py:325` at base_commit
fbacaa58ffc5a62456ee68b90efa13957f761ce4; the gold hunk rewrites body lines
339-342 to `obj = Model(**data); obj._state.db = db; natural_key =
obj.natural_key()`).  The gate applies the gold patch to /testbed before this
script runs and puts /testbed on PYTHONPATH, so `build_instance` imported here
IS the patched source; the script asserts that (`_assert_oracle_is_patched`)
and exits 1 if it is looking at unpatched code.

The velvet/lean siblings transliterated the control flow and (velvet) skipped,
on the grounds that observing the fix needs ">=2 Django databases, a model
whose natural_key() follows a foreign key, and a fixture whose related row
exists only in the non-default database -- i.e. the F2P integration test
itself".  That premise is false for a *unit* driver: everything it names is
constructible in-container with stdlib sqlite3 `:memory:` databases and
`settings.configure(...)`, with no test-suite code, no fixtures on disk and no
migrations (tables are created through the real `schema_editor`).  This script
therefore drives the real function directly, which is strictly stronger: the
store-routing mechanism the model abstracts (`ConnectionRouter._route_db` ->
the forward-FK descriptor's `db_manager(hints={'instance': obj})` queryset) is
EXERCISED by real Django rather than re-encoded by hand.  Nothing about
`build_instance` is copied into this file.

The only repo-side code written here is the *model definition* the F2P test
adds (`tests/fixtures_regress/models.py`,
`NaturalKeyWithFKDependency.natural_key = (self.name,) +
self.author.natural_key()`), reproduced as `Book`, plus two pure OBSERVATION
hooks inside it (record `self._state.db`, record the author row actually
dereferenced).  Observation is not reimplementation: the routing decision, the
queryset, the query and the exception are all real Django.

SHADOW: the impl region of model.py, copied verbatim
----------------------------------------------------
`_shadow_build_with_natural_key` below is `model.py:232-243` character for
character, together with the classes and `@Pure` helpers it depends on
(`ModelInstance`, `Deployment`, `query_store`, `dereference_succeeds`,
`KeyedRecord`), each minus its `Requires`/`Ensures`/`Acc`.  No restructuring,
renaming or simplification; no `PSeq`/`ToSeq` carriers appear in this model, so
no sequence shim is needed.  There is no `@ContractOnly` callee in this bundle
(mapping.md section 3: the routing rule is modelled DEEPLY by the two pure
helpers), so every line of the shadow is executable and every line is diffed.

`Deployment` carries the two routing facts of the deployment the loader runs in
(the ambient fallback store, and the store the related record actually resides
in).  In the model its constructor is unavailable to any loader, which is a
CONTRACT; stripping contracts leaves the two field stores, so here it is simply
the record the driver fills in from the case's alias bijection.  That is the
point of the bridge below: those two facts are supplied by the HARNESS -- the
alias `DEFAULT_DB_ALIAS` resolves to, and the alias whose `Person` row is the
intended related record -- exactly as, in the repo, they are supplied by the
settings and the fixture rather than chosen by `build_instance`.

`KeyedRecord` is the model's carrier for the OUTCOME of computing one record's
natural key: constructing it is the natural-key computation, and its two fields
record what that computation observed (the record's association at that moment,
and the store the dereference behind the key was routed to).  Stripping its
contracts leaves exactly those two field stores, so the shadow's observables are
the same values the spec pins -- which is the point: the diff below asks whether
those values match what real patched Django does.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
model carrier                -> repo reality
  `int` store id             -> a database alias `str`; the id chosen for the
                                ambient default alias is `default_store`
  `UNROUTED = -1`            -> `instance._state.db is None`
  `ModelInstance.routed`     -> `obj._state.db` at the moment
                                `obj.natural_key()` derefs the FK
  `target_store`             -> the `db` argument of `build_instance`
  `Deployment.record_store`  -> the alias whose `Person` row is THE related
                                record the natural key needs
  `Deployment.default_store` -> the id of `DEFAULT_DB_ALIAS`, the alias an
                                unrouted query falls back to
  `dereference_succeeds(...)`-> the FK deref returned the intended related
                                record (not a same-pk row from another store,
                                and not `RelatedObjectDoesNotExist`)

The alias<->id bijection is arbitrary, so it is RE-DRAWN per case (a random
permutation of ids over the aliases).  Only the *identity* of the ambient
default alias is fixed by the framework (`DEFAULT_DB_ALIAS == "default"`), so
`default_store` ranges over many different ints across the run while remaining
realizable.

Every store holds a `Person` at every pk, but with a store-stamped `name`, so
the resolved author name identifies WHICH store the real deref actually read.
That makes the observable discriminate every possible misroute, not just
"default instead of target": a deref sent to the wrong non-default store finds
a row, but not the intended one.

INPUT DOMAIN: finite, enumerated exhaustively, then fuzzed
---------------------------------------------------------
`Requires`: `target_store != UNROUTED`, `world.record_store == target_store`.
`world.default_store` is FREE -- the spec claims its obligations for a target
store that IS the ambient default one as well as for one that differs -- so the
realizable, Requires-satisfying model domain is `target_store in {ids of ALL
aliases}`, the ambient default alias INCLUDED.  It is FINITE and far smaller
than 1e5, and is therefore ENUMERATED EXHAUSTIVELY (every target alias, the
ambient default one included, under an exhaustive set of id permutations),
which is a stronger check than 1e5 samples of it; the run then fuzzes over the same domain, varying the
record identity (author pk, book name, whether the target store already holds
a matching Book row so the real function's inner
`get_by_natural_key`/`to_python` succeeds instead of raising `DoesNotExist`),
to reach N_CASES >= 1e5.  Boundary cases run first, including the exact F2P
shape (`database="other"`, author "J.R.R. Tolkien", book "The Lord of the
Rings").

DISCRIMINATION SELF-TEST
------------------------
A green G-CONF that cannot go red certifies nothing, so before the diff the
script runs `_assert_discriminating`: it exercises the PRE-PATCH shape of the
same repo line (`Model(**data).natural_key()`, base.py:332 at base_commit --
no store association) through the same real Django objects and requires that
the resulting observation DISAGREES with the shadow.  If the harness cannot
tell patched from unpatched behaviour it exits 1 instead of reporting a pass.

stdlib + Django only (hypothesis not required).  Exit 0 iff zero
disagreements; on a disagreement the input and both outputs are printed.
Seed: SEED = 15525 (recorded in mapping.md, section "G-CONF").
"""
import importlib.machinery
import json
import os
import random
import sys
import types

SEED = 15525
N_CASES = 100_000

# The concrete stores. "default" is the ambient default alias (DEFAULT_DB_ALIAS
# is a framework constant); "other" is the alias the F2P test loads into.
DEFAULT_ALIAS = "default"
EXTRA_ALIASES = ["other", "shard_a", "shard_b", "replica"]
ALL_ALIASES = [DEFAULT_ALIAS] + EXTRA_ALIASES

AUTHOR_PKS = [1, 2, 3]
F2P_AUTHOR = "J.R.R. Tolkien"
F2P_BOOK = "The Lord of the Rings"


# ---------------------------------------------------------------------------
# SHADOW -- model.py, contracts stripped, otherwise verbatim.
# ---------------------------------------------------------------------------

# model.py:66
UNROUTED = -1


# model.py:69-81 (Requires/Ensures/Acc stripped)
class ModelInstance:
    """A built record. ``routed`` is the store identifier the record is
    associated with for query routing; ``UNROUTED`` means no association."""

    def __init__(self, routed: int) -> None:
        self.routed = routed  # type: int


# model.py:84-109 (Requires/Ensures/Acc stripped). The two routing facts of the
# deployment the loader runs in, as one given world. In the model a loader can
# neither mint one (the constructor's precondition is unsatisfiable) nor write
# its fields (a read-only share); both of those are CONTRACTS, so stripping them
# leaves the two field stores. Here the harness fills it in from the case's alias
# bijection, which is what makes the diff below meaningful: the world is supplied
# from outside, as the settings and the fixture supply it in the repo.
class Deployment:
    """``default_store``: the ambient store an unrouted query falls back to.
    ``record_store``: the store the related record actually resides in."""

    def __init__(self, default_store: int, record_store: int) -> None:
        self.default_store = default_store  # type: int
        self.record_store = record_store    # type: int


# model.py:117-132, the `# pure-start` / `# pure-end` region (@Pure stripped).
def query_store(routed: int, default_store: int) -> int:
    """The store a dereference query is routed to: the record's own
    association if it has one, otherwise the ambient default store."""
    if routed == UNROUTED:
        return default_store
    return routed


def dereference_succeeds(routed: int, default_store: int, record_store: int) -> bool:
    """A routed dereference of the related record succeeds iff the store the
    query is routed to is the store the related record actually lives in."""
    return query_store(routed, default_store) == record_store
# end pure region


# model.py:135-190 (Requires/Ensures/Acc stripped). The outcome of computing one
# record's natural key: constructing it IS that computation, and its two fields
# record what the computation observed. Contracts stripped, the body is the two
# field stores.
class KeyedRecord:
    """The outcome of resolving one record's identity: its natural key has been
    computed, and this value carries the two observables of that computation --
    ``routed``, the store association the record carried at the moment its key
    was computed, and ``queried_store``, the store the related-record
    dereference behind that key was therefore sent to."""

    def __init__(self, record: ModelInstance, world: Deployment) -> None:
        self.routed = record.routed  # type: int
        self.queried_store = query_store(record.routed,
                                         world.default_store)  # type: int


def _shadow_build_with_natural_key(
    target_store: int, world: Deployment
) -> KeyedRecord:
    """model.py:232-243 -- the `# impl-start` / `# impl-end` region, verbatim
    (the region contains no contract call, so nothing is removed here)."""
    # impl-start
    # Build the instance (fresh: no store association yet).
    obj = ModelInstance(UNROUTED)
    # Associate it with the target store BEFORE computing the natural key, so
    # the dereference inside natural-key computation routes to the target.
    obj.routed = target_store
    # Compute the natural key of the now-associated instance: the dereference it
    # performs reaches the store the related record lives in, so the key -- and
    # with it the resolved outcome -- exists.
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end


def shadow_observables(target_store, default_store, record_store):
    """The model's observables for one input: the `Ensures` clauses of
    `build_with_natural_key` (model.py:216-230), read off the outcome the impl
    returns -- the association the record carried when its key was computed, the
    store that key's dereference was sent to, and that the dereference
    succeeds. The two routing facts are handed in as the world, as the spec has
    them handed in."""
    world = Deployment(default_store, record_store)
    res = _shadow_build_with_natural_key(target_store, world)
    return {
        "routed": res.routed,                    # Ensures :222
        "queried_store": res.queried_store,      # Ensures :226
        "deref_ok": dereference_succeeds(        # Ensures :229
            res.routed, world.default_store, world.record_store),
    }


# ---------------------------------------------------------------------------
# ORACLE -- the REAL patched repo function, driven against real databases.
# ---------------------------------------------------------------------------

def _configure_django():
    """Stand up real Django with len(ALL_ALIASES) sqlite `:memory:` stores and
    a synthetic app holding the F2P test's natural-key-with-FK models."""
    import django
    from django.conf import settings

    here = os.path.dirname(os.path.abspath(__file__))
    app = types.ModuleType("confapp")
    app.__path__ = [here]
    spec = importlib.machinery.ModuleSpec("confapp", None, is_package=True)
    spec.submodule_search_locations = [here]
    app.__spec__ = spec
    sys.modules["confapp"] = app
    models_mod = types.ModuleType("confapp.models")
    models_mod.__spec__ = importlib.machinery.ModuleSpec("confapp.models", None)
    sys.modules["confapp.models"] = models_mod
    app.models = models_mod

    databases = {}
    for alias in ALL_ALIASES:
        databases[alias] = {"ENGINE": "django.db.backends.sqlite3",
                            "NAME": ":memory:"}
    settings.configure(
        DATABASES=databases,
        DATABASE_ROUTERS=[],          # the default: no custom routers
        INSTALLED_APPS=["confapp"],
        USE_TZ=False,
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    django.setup()
    return models_mod


def _assert_oracle_is_patched(observed_routed_at_deref, target_alias):
    """The gate applies the gold patch before running us; fail loudly rather
    than silently comparing against unpatched code."""
    import django.core.serializers.base as base
    src = ""
    try:
        import inspect
        src = inspect.getsource(base.build_instance)
    except Exception:                                     # pragma: no cover
        pass
    if "_state.db" not in src:
        print("ERROR: oracle build_instance is NOT the patched source "
              "(no `_state.db` assignment in "
              "django/core/serializers/base.py:build_instance); the gold patch "
              "did not reach /testbed, so this check would compare against "
              "pre-patch code.", file=sys.stderr)
        return False
    if observed_routed_at_deref != target_alias:
        print("ERROR: oracle sanity probe: patched build_instance derefed with "
              "_state.db=%r for db=%r" % (observed_routed_at_deref, target_alias),
              file=sys.stderr)
        return False
    return True


def build_oracle():
    """Returns (call, prepatch_call, aliases). `call(target_alias, author_pk,
    book_name)` invokes the REAL patched `build_instance` and reports what the
    real ORM did."""
    models_mod = _configure_django()
    from django.db import models, connections

    # --- the F2P test's models (tests/fixtures_regress/models.py, added by
    # --- test_patch: Person + NaturalKeyWithFKDependency). Reproduced here
    # --- because /testbed's test suite is not importable as a library; the
    # --- OBSERVATION hooks (`_probe`) are the only additions.
    probe = {}

    class Person(models.Model):
        name = models.CharField(max_length=255)

        class Meta:
            app_label = "confapp"

        def natural_key(self):
            return (self.name,)

    class BookManager(models.Manager):
        def get_by_natural_key(self, name, author):
            return self.get(name=name, author__name=author)

    class Book(models.Model):
        name = models.CharField(max_length=255)
        author = models.ForeignKey(Person, models.CASCADE)
        objects = BookManager()

        class Meta:
            app_label = "confapp"

        def natural_key(self):
            # OBSERVATION ONLY: which store is this record associated with at
            # the moment the FK deref happens (the model's `Result().routed`)?
            probe["routed"] = self._state.db
            author = self.author            # <-- the real store-routed deref
            # OBSERVATION ONLY: the author row's store-stamped name identifies
            # WHICH store the real deref actually read from.
            probe["author_name"] = author.name
            return (self.name,) + author.natural_key()

        natural_key.dependencies = ["confapp.Person"]

    models_mod.Person = Person
    models_mod.Book = Book

    for alias in ALL_ALIASES:
        with connections[alias].schema_editor() as editor:
            editor.create_model(Person)
            editor.create_model(Book)

    # Every store holds a Person at every pk, but store-stamped, so a misrouted
    # deref finds a row that is NOT the intended related record.
    def author_name(alias, pk):
        if alias == "other" and pk == AUTHOR_PKS[0]:
            return F2P_AUTHOR           # the exact F2P fixture row
        return "author-%s-%d" % (alias, pk)

    name_to_alias = {}
    for alias in ALL_ALIASES:
        for pk in AUTHOR_PKS:
            Person.objects.using(alias).create(pk=pk, name=author_name(alias, pk))
            name_to_alias[author_name(alias, pk)] = alias

    def call(target_alias, author_pk, book_name, seed_book=False):
        """Drive the REAL patched build_instance; report the real observables."""
        if seed_book:
            # Make the inner get_by_natural_key(*nk) SUCCEED on the target, so
            # the real function's `to_python` branch is exercised too.
            Book.objects.using(target_alias).get_or_create(
                name=book_name, author_id=author_pk)
        probe.clear()
        data = {"name": book_name, "author_id": author_pk}
        deref_raised = False
        try:
            from django.core.serializers.base import build_instance
            build_instance(Book, data, target_alias)
        except Person.DoesNotExist:
            # RelatedObjectDoesNotExist: the routed store had no such row.
            deref_raised = True
        found = probe.get("author_name")
        return {
            "routed_alias": probe.get("routed"),
            "queried_alias": (None if deref_raised
                              else name_to_alias.get(found, "?%s" % found)),
            "deref_found_intended": (
                (not deref_raised) and found == author_name(target_alias, author_pk)),
            "pk_resolved": data.get("id"),
        }

    def prepatch_call(target_alias, author_pk, book_name):
        """The PRE-PATCH shape of the same repo line
        (`Model(**data).natural_key()`, base.py:332 @ base_commit): no store
        association. Used only for the discrimination self-test."""
        probe.clear()
        obj = Book(name=book_name, author_id=author_pk)
        try:
            obj.natural_key()
        except Person.DoesNotExist:
            pass
        found = probe.get("author_name")
        return {
            "routed_alias": probe.get("routed"),
            "queried_alias": name_to_alias.get(found, None),
            "deref_found_intended": found == author_name(target_alias, author_pk),
        }

    return call, prepatch_call


# ---------------------------------------------------------------------------
# BRIDGE + DIFF
# ---------------------------------------------------------------------------

def bridge(perm):
    """`perm` maps alias -> model store id (an arbitrary bijection, redrawn per
    case). Returns (alias->id, id->alias)."""
    return perm, {v: k for k, v in perm.items()}


def compare(case, shadow, oracle):
    """The three observables, translated into one another's language."""
    a2i, i2a = case["a2i"], case["i2a"]
    real = {
        "routed": (UNROUTED if oracle["routed_alias"] is None
                   else a2i.get(oracle["routed_alias"], -999)),
        "queried_store": (a2i.get(oracle["queried_alias"], -999)
                          if oracle["queried_alias"] is not None else None),
        "deref_ok": oracle["deref_found_intended"],
    }
    if real["routed"] != shadow["routed"]:
        return ("routed (model Ensures Result().routed == target_store <-> real "
                "obj._state.db at natural_key())", shadow, real)
    if real["queried_store"] != shadow["queried_store"]:
        return ("queried_store (model query_store(routed, default) <-> the store "
                "the real FK deref read from)", shadow, real)
    if real["deref_ok"] != shadow["deref_ok"]:
        return ("deref_ok (model Ensures dereference_succeeds(...) <-> the real "
                "deref returned the intended related record)", shadow, real)
    return None


def main():
    rnd = random.Random(SEED)
    call, prepatch_call = build_oracle()

    # --- oracle provenance: we must be looking at the PATCHED function -------
    probe0 = call("other", AUTHOR_PKS[0], F2P_BOOK)
    if not _assert_oracle_is_patched(probe0["routed_alias"], "other"):
        return 1

    # --- discrimination self-test: the check must be able to go red ----------
    ids = list(range(len(ALL_ALIASES)))
    rnd.shuffle(ids)
    perm0 = dict(zip(ALL_ALIASES, ids))
    a2i0, i2a0 = bridge(perm0)
    case0 = {"a2i": a2i0, "i2a": i2a0}
    sh0 = shadow_observables(a2i0["other"], a2i0[DEFAULT_ALIAS], a2i0["other"])
    pre0 = prepatch_call("other", AUTHOR_PKS[0], F2P_BOOK)
    if compare(case0, sh0, pre0) is None:
        print("ERROR: discrimination self-test FAILED -- the harness cannot "
              "distinguish the patched function (associates the record with the "
              "target store) from the pre-patch shape (leaves it unassociated); "
              "a pass would certify nothing.", file=sys.stderr)
        return 1

    checked = 0
    disagreements = 0
    covered_targets = set()
    covered_default_ids = set()
    seeded_book_cases = 0
    first_bad = None

    def run_case(target_alias, author_pk, book_name, perm, seed_book):
        nonlocal checked, disagreements, first_bad, seeded_book_cases
        a2i, i2a = bridge(perm)
        target_store = a2i[target_alias]
        default_store = a2i[DEFAULT_ALIAS]
        record_store = target_store            # Requires: world.record_store == target
        # Requires guard: never diff an input outside the model's domain. Note
        # what is NOT asserted: nothing separates default_store from
        # record_store. The spec leaves the ambient default free, so the target
        # alias BEING the ambient default one is inside the domain and is
        # enumerated below -- the sub-domain a driver that excluded it could not
        # see at all.
        assert target_store != UNROUTED
        assert record_store == target_store
        sh = shadow_observables(target_store, default_store, record_store)
        orc = call(target_alias, author_pk, book_name, seed_book=seed_book)
        checked += 1
        covered_targets.add(target_alias)
        covered_default_ids.add(default_store)
        if seed_book:
            seeded_book_cases += 1
        bad = compare({"a2i": a2i, "i2a": i2a}, sh, orc)
        if bad is not None:
            disagreements += 1
            if first_bad is None:
                first_bad = (target_alias, author_pk, book_name, dict(perm), bad)
            if disagreements <= 5:
                print("DISAGREE on %s: target=%r author_pk=%r book=%r perm=%r\n"
                      "  observable: %s\n  shadow(model)=%r\n  real(patched)=%r"
                      % (bad[0], target_alias, author_pk, book_name, perm,
                         bad[0], bad[1], bad[2]), file=sys.stderr)

    # --- BOUNDARY: the exact F2P shape first --------------------------------
    f2p_perm = dict(zip(ALL_ALIASES, range(len(ALL_ALIASES))))
    run_case("other", AUTHOR_PKS[0], F2P_BOOK, f2p_perm, False)
    run_case("other", AUTHOR_PKS[0], F2P_BOOK, f2p_perm, True)

    # --- EXHAUSTIVE enumeration of the realizable Requires-satisfying domain:
    # --- every target alias -- the AMBIENT DEFAULT one included, since the spec
    # --- leaves the ambient default store free -- x every id-permutation of the
    # --- alias bijection x every author pk x both inner-lookup outcomes.
    import itertools
    n = len(ALL_ALIASES)
    for ids in itertools.permutations(range(n)):
        perm = dict(zip(ALL_ALIASES, ids))
        for target_alias in ALL_ALIASES:
            for author_pk in AUTHOR_PKS:
                for seed_book in (False, True):
                    run_case(target_alias, author_pk,
                             "enum-%s-%d" % (target_alias, author_pk),
                             perm, seed_book)
    enumerated = checked

    # --- FUZZ over the same domain to reach N_CASES -------------------------
    while checked < N_CASES:
        ids = list(range(n))
        rnd.shuffle(ids)
        perm = dict(zip(ALL_ALIASES, ids))
        target_alias = rnd.choice(ALL_ALIASES)
        author_pk = rnd.choice(AUTHOR_PKS)
        book_name = "b%06d" % rnd.randrange(1000)   # collides -> reuses rows
        run_case(target_alias, author_pk, book_name, perm,
                 rnd.random() < 0.25)

    ok = (disagreements == 0
          and covered_targets == set(ALL_ALIASES)
          and len(covered_default_ids) == n
          and seeded_book_cases > 0)
    if disagreements == 0 and not ok:
        print("ERROR: coverage assertion failed: targets=%r default_ids=%r "
              "seeded=%d" % (sorted(covered_targets), sorted(covered_default_ids),
                             seeded_book_cases), file=sys.stderr)
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "django__django-15525",
        "backend": "nagini",
        "status": "pass" if ok else "fail",
        "shadow": "model.py impl-start/impl-end region verbatim (contracts "
                  "stripped) + ModelInstance/KeyedRecord + pure "
                  "query_store/dereference_succeeds",
        "oracle": "CALLED django.core.serializers.base.build_instance "
                  "(patched, django/core/serializers/base.py:325) against "
                  "%d real sqlite databases" % n,
        "observables": ["routed (_state.db at natural_key)",
                        "queried_store (store the real FK deref read)",
                        "deref_ok (intended related record found)"],
        "n": checked,
        "enumerated_exhaustive": enumerated,
        "fuzzed": checked - enumerated,
        "seed": SEED,
        "domain": "finite: target_store in ids(ALL aliases, the ambient default "
                  "one included -- the spec leaves default_store free), "
                  "world.record_store == target_store, world.default_store == "
                  "id(default); enumerated exhaustively then fuzzed",
        "target_aliases": sorted(covered_targets),
        "distinct_default_store_ids": len(covered_default_ids),
        "inner_lookup_success_cases": seeded_book_cases,
        "discrimination_self_test": "pass (pre-patch shape disagrees)",
        "disagreements": disagreements,
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
