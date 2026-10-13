#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11087.

The bundle models ONE decision: which columns the cascade-deletion collector's
fetch for the related objects of a relation ends up loading
(`Collector.collect`, the field-selection arm the gold patch adds at
django/db/models/deletion.py:225-244). The modeled value is a pure function of
seven observables (mapping.md §1), all read off the real `sub_objs` queryset as
it ARRIVES at that arm:

    guardA             : bool   (sub_objs.query.select_related truthiness)
    guardB             : bool   (self._has_signal_listeners(related_model))
    pkColumn           : str    (related_model._meta.pk.attname)
    allFields          : list[str]   (every concrete column of the model)
    defaultColumns     : list[str]   (the columns THAT queryset loads if it is
                                      handed on untouched)
    skippedNames       : list[str]   (sub_objs.query.deferred_loading[0] when
                                      its flag says "these are deferred", else
                                      empty — the RAW stored names)
    candidateRelations : list[list[str]]
                          (per candidate relation, its foreign_related_fields
                           attnames)

Post-patch rule:

    if not (select_related or has_signals):
        referenced = set(chain.from_iterable(
            (rf.attname for rf in rel.field.foreign_related_fields)
            for rel in get_candidate_relations_to_delete(related_model._meta)))
        sub_objs = sub_objs.only(*tuple(referenced))
    # -> load = whatever that queryset actually selects

WHY THE ORACLE DRIVES THE REAL `.only()` ON THE REAL INCOMING QUERYSET.

An early version of this check used an in-process replica that returned the
`referenced` set itself as the loaded column set. That made the check vacuous in
the one place it mattered: the shadow also computes `referenced`, so
oracle == shadow by construction and any drift between `referenced` and what
`QuerySet.only()` genuinely loads was invisible. A later version drove the real
`.only()` but always on a FRESH `model._base_manager.all()`, which is blind to a
different drift: the incoming queryset may already carry a deferral state, and
`.only()` INTERACTS with it. Three drifts exist and all are reachable from
ordinary models:

  * `.only(*cols)` ALWAYS retains the primary-key column, even when no relation
    points at it (`Query.deferred_to_data` seeds `must_include` with
    `orig_opts.pk`, django/db/models/sql/query.py:660). A relation declared with
    `to_field=` targets a non-pk column, so `referenced` need not contain the pk
    and the real load is `referenced | {pk}`.
  * `.only()` with ZERO columns is a NO-OP: `add_immediate_loading` stores an
    empty field-name set and `deferred_to_data` returns early on it
    (query.py:656), so the whole row is loaded. A related model that nothing
    points at has `referenced == set()`, and gets the full row rather than
    nothing.
  * when the incoming queryset is in the DEFER state (`deferred_loading ==
    (names, True)` — e.g. a model whose base manager defers a column),
    `add_immediate_loading` requests `field_names.difference(existing)`
    (query.py:1971-1976): the names already deferred are REMOVED from the
    request, as a raw set difference over the stored strings. So a referenced
    column that was already deferred does not come back, and if that empties the
    request the `.only()` degenerates into the no-op above and the WHOLE ROW is
    loaded — including the deferred column. `skippedNames` and
    `restrictionNames` model exactly this step, and the raw-string reading is
    what makes `defer('origin')` fail to cancel the referenced attname
    `origin_id` in the model as it does in the real machinery.
  * on the pass-through branch the arm hands `sub_objs` on UNTOUCHED, so the load
    is that queryset's own default column set — `defaultColumns`, which is the
    whole row only when nothing had been deferred.

So the ORACLE below builds real Django models, puts their `_base_manager`
queryset into many prior deferral states, runs the patched arm's own expression
on the real `_meta`, hands the result to the real `QuerySet.only(...)`, and reads
the column set back off the real SQL compiler. Leg 0 goes further and runs REAL
`.delete()` cascades, reading the columns off the SQL the cascade actually
emitted. The SHADOW is the op-for-op transliteration of
`implementation_collectFieldSelection` (refinement.md). They are independent: the
oracle goes through Django's deferred-loading machinery, the shadow through
`flatten`/`dedup`/`filter`/`isEmpty`/`cons`.

The column choice is membership-determined (a SET), so the two legs are compared
AS SETS (mapping.md's list↔set bijection).

stdlib + Django only. Pinned seed: 11087 (also in mapping.md).
"""
from itertools import chain
import random
import re
import sys

SEED = 11087
N_FUZZ = 4000          # each fuzz case builds + compiles a real queryset
N_PURE = 120_000       # pure-leg cases over the validated column-set rule


# --------------------------------------------------------------------------
# Django bootstrap (in-container, patched repo)
# --------------------------------------------------------------------------
def _boot():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,        # leg 0 reads the emitted SQL off connection.queries
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "conf_app"],
        USE_TZ=False,
    )
    import os
    import tempfile
    d = tempfile.mkdtemp(prefix="conf_app_")
    pkg = os.path.join(d, "conf_app")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    open(os.path.join(pkg, "models.py"), "w").close()
    sys.path.insert(0, d)
    django.setup()
    return django


# --------------------------------------------------------------------------
# ORACLE — the real patched decision, driven through real Django objects
# --------------------------------------------------------------------------
def real_referenced(related_model):
    """The EXACT gather expression from the patch."""
    from django.db.models.deletion import get_candidate_relations_to_delete
    return set(chain.from_iterable(
        (rf.attname for rf in rel.field.foreign_related_fields)
        for rel in get_candidate_relations_to_delete(related_model._meta)
    ))


def loaded_of(qs):
    """The column set the SELECT for `qs` actually loads."""
    compiler = qs.query.get_compiler("default")
    compiler.pre_sql_setup()
    return {col[0].target.attname for col in compiler.select}


def oracle_select(guard_a, guard_b, model, qs0):
    """The patched arm, transliterated, run on the real incoming queryset."""
    sub_objs = qs0
    if not (guard_a or guard_b):
        referenced = real_referenced(model)
        sub_objs = sub_objs.only(*tuple(referenced))
    return loaded_of(sub_objs)


# --------------------------------------------------------------------------
# SHADOW of implementation_collectFieldSelection (the R/I leg)
# --------------------------------------------------------------------------
def _flatten(xss):
    out = []
    for xs in xss:
        out.extend(xs)
    return out


def _dedup(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _referenced_columns(candidate_relations):
    """Lean: candidateRelations.flatten.dedup"""
    return _dedup(_flatten(candidate_relations))


def _restriction_names(skipped_names, candidate_relations):
    """Lean: (referencedColumns cands).filter (fun c => !skipped.contains c)"""
    return [c for c in _referenced_columns(candidate_relations)
            if c not in skipped_names]


def _loaded_columns(pk_column, all_fields, skipped_names, candidate_relations):
    """Lean: let named := restrictionNames skippedNames cands
             if named.isEmpty then allFields else (pkColumn :: named).dedup"""
    named = _restriction_names(skipped_names, candidate_relations)
    if not named:
        return list(all_fields)
    return _dedup([pk_column] + named)


def shadow_select(guard_a, guard_b, pk_column, all_fields, default_columns,
                  skipped_names, candidate_relations):
    loaded = list(default_columns)
    if not (guard_a or guard_b):
        loaded = _loaded_columns(pk_column, all_fields, skipped_names,
                                 candidate_relations)
    return set(loaded)


# --------------------------------------------------------------------------
# Model zoo
# --------------------------------------------------------------------------
CREATED = []


def _M(models, name, bases=None, meta=None, **attrs):
    attrs["__module__"] = "conf_app.models"
    mattrs = {"app_label": "conf_app"}
    mattrs.update(meta or {})
    attrs["Meta"] = type("Meta", (), mattrs)
    cls = type(name, bases or (models.Model,), attrs)
    CREATED.append(cls)
    return cls


def _deferring_manager(models, *names):
    class _Mgr(models.Manager):
        def get_queryset(self):
            return super().get_queryset().defer(*names)
    return _Mgr


def build_zoo():
    """Real models covering: plain pk, custom pk, to_field (non-pk target),
    multi-relation gathers, empty gathers, both halves of an MTI pair, and
    base managers that arrive with a column already deferred."""
    from django.db import models, connection
    from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                    GenericRelation)
    from django.contrib.contenttypes.models import ContentType

    M = lambda *a, **kw: _M(models, *a, **kw)     # noqa: E731

    Origin = M("Origin")

    # nothing points at Leaf -> empty gather
    Leaf = M("Leaf",
             origin=models.ForeignKey(Origin, models.CASCADE),
             big=models.TextField(null=True))

    # pk-targeting + to_field-targeting relations point at Target
    Target = M("Target",
               origin=models.ForeignKey(Origin, models.CASCADE),
               unique_field=models.IntegerField(unique=True, null=True),
               u2=models.IntegerField(unique=True, null=True),
               big=models.TextField(null=True))
    M("RefPk", target=models.ForeignKey(Target, models.CASCADE))
    M("RefToField",
      target=models.ForeignKey(Target, models.SET_NULL, null=True,
                               to_field="unique_field", related_name="+"))

    # ONLY a to_field relation points at OnlyToField -> gather excludes the pk
    OnlyToField = M("OnlyToField",
                    unique_field=models.IntegerField(unique=True, null=True),
                    big=models.TextField(null=True))
    M("RefOnlyToField",
      t=models.ForeignKey(OnlyToField, models.SET_NULL, null=True,
                          to_field="unique_field", related_name="+"))

    # custom (non-'id') pk, targeted only through a non-pk column
    CustomPk = M("CustomPk",
                 code=models.CharField(max_length=12, primary_key=True),
                 unique_field=models.IntegerField(unique=True, null=True),
                 big=models.TextField(null=True))
    M("RefCustom",
      t=models.ForeignKey(CustomPk, models.SET_NULL, null=True,
                          to_field="unique_field", related_name="+"))

    # MTI: child's pk attname is the parent link
    MtiBase = M("MtiBase", b1=models.IntegerField(null=True))
    MtiChild = M("MtiChild", bases=(MtiBase,),
                 c1=models.IntegerField(null=True),
                 big=models.TextField(null=True))
    M("RefChild", t=models.ForeignKey(MtiChild, models.CASCADE))

    # ---- leg-0 (end-to-end) models -------------------------------------
    # A generic relation is a private field with bulk_related_objects, so its
    # owner can NOT be fast-deleted and the modeled arm is really reached.
    Tag = M("Tag",
            content_type=models.ForeignKey(ContentType, models.CASCADE),
            object_id=models.PositiveIntegerField(),
            content_object=GenericForeignKey("content_type", "object_id"))

    def e2e(name, defer_names=None, with_generic=False):
        attrs = dict(origin=models.ForeignKey(Origin, models.CASCADE),
                     unique_field=models.IntegerField(unique=True, null=True),
                     large_field=models.TextField(null=True))
        if with_generic:
            attrs["tags"] = GenericRelation(Tag)
        meta = {}
        if defer_names:
            attrs["objects"] = models.Manager()
            attrs["bm"] = _deferring_manager(models, *defer_names)()
            meta["base_manager_name"] = "bm"
        return M(name, meta=meta, **attrs)

    E2ePlain = e2e("E2ePlain")
    E2eDeferRef = e2e("E2eDeferRef", ["unique_field"])
    E2eDeferOther = e2e("E2eDeferOther", ["large_field"])
    E2eGenDefer = e2e("E2eGenDefer", ["large_field"], with_generic=True)
    E2eGenPlain = e2e("E2eGenPlain", with_generic=True)
    for i, t in enumerate([E2ePlain, E2eDeferRef, E2eDeferOther]):
        M("E2eSec%d" % i,
          r=models.ForeignKey(t, models.SET_NULL, null=True,
                              to_field="unique_field", related_name="+"))

    for m in [ContentType] + CREATED:
        with connection.schema_editor() as se:
            se.create_model(m)

    shadowed = [Leaf, Target, OnlyToField, CustomPk, MtiBase, MtiChild]
    e2e_cases = [
        (E2ePlain, False, "no prior skip -> restricted"),
        (E2eDeferRef, False, "prior skip empties the request -> whole row"),
        (E2eDeferOther, False, "prior skip misses the request -> restricted"),
        (E2eDeferRef, True, "guard set + prior skip -> pass-through"),
        (E2ePlain, True, "guard set, no prior skip -> pass-through"),
        (E2eGenPlain, False, "empty gather, no prior skip -> whole row"),
        (E2eGenDefer, False, "empty gather + prior skip -> whole row"),
        (Origin, False, "the deletion root itself (out of the arm)"),
    ]
    return shadowed, e2e_cases


def observables(model, qs0):
    """The seven observables, read off a real model and a real queryset."""
    from django.db.models.deletion import get_candidate_relations_to_delete
    cands = [[rf.attname for rf in rel.field.foreign_related_fields]
             for rel in get_candidate_relations_to_delete(model._meta)]
    stored, defer_flag = qs0.query.deferred_loading
    return dict(
        pk=model._meta.pk.attname,
        all_fields=[f.attname for f in model._meta.concrete_fields],
        default_columns=sorted(loaded_of(qs0)),
        skipped=sorted(stored) if defer_flag else [],
        cands=cands,
    )


def prior_states(model, rng):
    """Deferral states an incoming `sub_objs` can arrive in. Field NAMES, as the
    public `.defer()`/`.only()` API takes them (which is also why the stored
    skip names live in the name namespace, not the attname one)."""
    names = [f.name for f in model._meta.concrete_fields]
    out = [("none", ())]
    for n in names:
        out.append(("defer", (n,)))
    if len(names) >= 2:
        out.append(("defer", (names[0], names[1])))
        out.append(("defer", tuple(names)))
        out.append(("only", (names[-1],)))
        out.append(("only", (names[0], names[-1])))
        out.append(("defer-defer", ((names[0],), (names[-1],))))
        out.append(("only-defer", ((names[0], names[-1]), (names[0],))))
    return out


def build_qs(model, kind, args):
    base = model._base_manager.all()
    if kind == "none":
        return base
    if kind == "defer":
        return base.defer(*args)
    if kind == "only":
        return base.only(*args)
    if kind == "defer-defer":
        return base.defer(*args[0]).defer(*args[1])
    if kind == "only-defer":
        return base.only(*args[0]).defer(*args[1])
    raise AssertionError(kind)


# --------------------------------------------------------------------------
# leg 0 — end-to-end: real cascade deletes, columns read off the emitted SQL
# --------------------------------------------------------------------------
def cascade_columns(table, log):
    for q in log:
        sql = q["sql"]
        if sql.startswith("SELECT") and f'FROM "{table}"' in sql:
            head = sql.split(" FROM ")[0]
            return set(re.findall(r'"%s"\."(\w+)"' % table, head))
    return None


def run_e2e(cases):
    """Delete an Origin, let the cascade run, and compare the shadow (driven by
    the observables captured at the arm) with the columns the real cascade
    SELECT listed. Returns (checked, out_of_domain, failed)."""
    from django.db import connection, reset_queries
    from django.db.models import signals
    from django.db.models.deletion import Collector

    Origin = next(m for m in CREATED if m.__name__ == "Origin")
    seen = []
    orig_related_objects = Collector.related_objects

    def spy(self, related, objs):
        qs = orig_related_objects(self, related, objs)
        rm = related.related_model
        obs = observables(rm, qs)
        obs["model"] = rm.__name__
        obs["guard_a"] = bool(qs.query.select_related)
        obs["guard_b"] = bool(self._has_signal_listeners(rm))
        seen.append(obs)
        return qs

    Collector.related_objects = spy
    checked = out_of_domain = failed = 0
    try:
        for model, with_receiver, label in cases:
            seen.clear()
            rcv = None
            if with_receiver:
                def rcv(sender, **kw):
                    pass
                signals.pre_delete.connect(rcv, sender=model)
            try:
                o = Origin.objects.create()
                kw = {}
                names = {f.name for f in model._meta.concrete_fields}
                if "origin" in names:
                    kw["origin"] = o
                if "large_field" in names:
                    kw["large_field"] = "x"
                if kw:
                    model._default_manager.create(**kw)
                reset_queries()
                Origin.objects.filter(pk=o.pk).delete()
                log = list(connection.queries)
            finally:
                if with_receiver:
                    signals.pre_delete.disconnect(rcv, sender=model)
            obs = [x for x in seen if x["model"] == model.__name__]
            real = cascade_columns(model._meta.db_table, log)
            if not obs or real is None:
                # the arm was not reached for this model (fast-delete path, or
                # the model is the deletion root): outside the modeled domain
                out_of_domain += 1
                print(f"  out-of-domain e2e {model.__name__} ({label}): "
                      f"arm not reached")
                continue
            ob = obs[0]
            want = shadow_select(ob["guard_a"], ob["guard_b"], ob["pk"],
                                 ob["all_fields"], ob["default_columns"],
                                 ob["skipped"], ob["cands"])
            if real != want:
                failed += 1
                print(f"DISAGREE e2e {model.__name__} ({label}) "
                      f"guards=({ob['guard_a']},{ob['guard_b']}) "
                      f"skipped={ob['skipped']} default={ob['default_columns']} "
                      f"cands={ob['cands']}: real={sorted(real)} "
                      f"shadow={sorted(want)}")
            checked += 1
    finally:
        Collector.related_objects = orig_related_objects
    return checked, out_of_domain, failed


def main() -> int:
    try:
        _boot()
        models_under_test, e2e_cases = build_zoo()
    except Exception as exc:  # pragma: no cover
        print(f"oracle bootstrap failed: {type(exc).__name__}: {exc}")
        print("status=fail")
        return 1

    checked = 0
    rng = random.Random(SEED)

    # ---- leg 0: real cascade deletes vs the shadow -------------------------
    try:
        n, skipped, failed = run_e2e(e2e_cases)
    except Exception as exc:
        print(f"e2e leg failed: {type(exc).__name__}: {exc}")
        print("status=fail")
        return 1
    if failed:
        print("status=fail")
        return 1
    checked += n
    print(f"leg0 end-to-end deletes: checked={n} out-of-domain={skipped}")

    # ---- leg 1: the patched arm vs the shadow, over the real model zoo -----
    # Every model x every prior deferral state x all four guard combinations.
    for model in models_under_test:
        for kind, args in prior_states(model, rng):
            qs0 = build_qs(model, kind, args)
            try:
                ob = observables(model, qs0)
            except Exception as exc:
                print(f"  unsupported prior state {model.__name__} {kind}{args}:"
                      f" {type(exc).__name__}: {exc}")
                print("status=fail")
                return 1
            for ga in (True, False):
                for gb in (True, False):
                    got = oracle_select(ga, gb, model,
                                        build_qs(model, kind, args))
                    want = shadow_select(ga, gb, ob["pk"], ob["all_fields"],
                                         ob["default_columns"], ob["skipped"],
                                         ob["cands"])
                    if got != want:
                        print(f"DISAGREE arm {model.__name__} "
                              f"guards=({ga},{gb}) prior={kind}{args} "
                              f"skipped={ob['skipped']} "
                              f"default={ob['default_columns']} "
                              f"cands={ob['cands']}: oracle={sorted(got)} "
                              f"shadow={sorted(want)}")
                        print("status=fail")
                        return 1
                    checked += 1

    # ---- leg 2: real .only() over arbitrary requests x prior states --------
    # The restricted branch's value is what `qs0.only(*S)` loads for the gathered
    # set S. Drive the REAL .only() on many (prior state, S) pairs the zoo's own
    # relations do not produce, and check the shadow's rule against it. This is
    # the leg that pins pk retention, the raw-name difference against
    # `skippedNames`, and the empty-request no-op.
    per_model = max(1, N_FUZZ // len(models_under_test))
    for model in models_under_test:
        states = prior_states(model, rng)
        attnames = [f.attname for f in model._meta.concrete_fields]
        for _ in range(per_model):
            kind, args = states[rng.randrange(len(states))]
            qs0 = build_qs(model, kind, args)
            ob = observables(model, qs0)
            k = rng.randint(0, len(attnames))
            S = set(rng.sample(attnames, k))
            try:
                got = loaded_of(build_qs(model, kind, args).only(*tuple(S)))
            except Exception as exc:
                print(f"  unsupported request {model.__name__} {kind}{args} "
                      f"S={sorted(S)}: {type(exc).__name__}: {exc}")
                print("status=fail")
                return 1
            # cands shaped so that flatten.dedup == S
            cands = [[c] for c in sorted(S)]
            want = shadow_select(False, False, ob["pk"], ob["all_fields"],
                                 ob["default_columns"], ob["skipped"], cands)
            if got != want:
                print(f"DISAGREE only {model.__name__} prior={kind}{args} "
                      f"skipped={ob['skipped']} S={sorted(S)}: "
                      f"oracle={sorted(got)} shadow={sorted(want)}")
                print("status=fail")
                return 1
            checked += 1

    # ---- leg 3: the pure list->set refinement, at fuzz volume --------------
    # Legs 0-2 established the column-set RULE against the real callee. This leg
    # exercises the shadow's own flatten/dedup/filter/isEmpty/cons plumbing
    # against that rule over many candidateRelations and skippedNames SHAPES
    # (nesting, repeats across relations, empty inner lists, skips that hit,
    # miss, or cover the whole request), which real models cannot enumerate.
    COL_POOL = ["id", "unique_field", "large_field", "origin_id", "code",
                "mtibase_ptr_id", "attname0", "attname1", "u2", "col_x"]
    for _ in range(N_PURE):
        ga = rng.choice([True, False])
        gb = rng.choice([True, False])
        pk = rng.choice(COL_POOL)
        all_fields = rng.sample(COL_POOL, rng.randint(1, len(COL_POOL)))
        default_columns = rng.sample(all_fields, rng.randint(1, len(all_fields)))
        skipped = rng.sample(COL_POOL, rng.randint(0, 3))
        cands = [[rng.choice(COL_POOL) for _ in range(rng.randint(0, 3))]
                 for _ in range(rng.randint(0, 5))]
        referenced = set(chain.from_iterable(cands))     # the patch's gather
        if not (ga or gb):
            request = referenced - set(skipped)          # add_immediate_loading
            expect = set(all_fields) if not request else request | {pk}
        else:
            expect = set(default_columns)
        got = shadow_select(ga, gb, pk, all_fields, default_columns, skipped,
                            cands)
        if got != expect:
            print(f"DISAGREE pure guards=({ga},{gb}) pk={pk!r} "
                  f"all={all_fields} default={default_columns} "
                  f"skipped={skipped} cands={cands}: "
                  f"shadow={sorted(got)} rule={sorted(expect)}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
