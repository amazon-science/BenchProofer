#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11087 (nagini).

SHADOW
------
The two `# impl-start` / `# impl-end` regions of model.py, copied VERBATIM below
with only the contract calls deleted (`Requires`/`Ensures`/`Invariant`/`Assert`
and the `# invariants-start`/`-end` markers). Nothing is renamed, reordered or
"simplified": the two while-loops that materialise the result list are kept
element-by-element exactly as the model writes them, and the impl's call to
`rows_exposed_to_observers` is a real call to the shadow of that function (it is
under specification, not an axiom). The `@Pure` helper `exposed_to_observers` is
copied too, minus its contracts. After contract stripping the impl regions
contain no `ToSeq`/`PSeq` occurrence at all (every `ToSeq` in model.py sits
inside an `Invariant`/`Assert`/`Ensures`), so no PSeq carrier shim is required
here; see the "type bridge" note below for how the `List[int]` carrier is
bridged instead. There are no `@ContractOnly` axioms in this bundle
(model.py `# axioms-start` region is empty), so every shadowed line is
executable.

ORACLE — the REAL patched repo functions, CALLED, not transliterated
-------------------------------------------------------------------
The gate applies the gold patch to /testbed before this script runs, so
`django.db.models.deletion` is the patched module. Two oracles, both real:

  (O1) `Collector._has_signal_listeners` — the new helper added by hunk 2 of the
       patch (`django/db/models/deletion.py:120` post-patch). Called directly on
       a real `Collector`, with real receivers connected to/disconnected from the
       real `django.db.models.signals.{pre_delete,post_delete,m2m_changed}`
       registry. Models `rows_exposed_to_observers`.

  (O2) `Collector.collect`, the related-set branch rewritten by hunk 3
       (`deletion.py:223-224` pre-patch -> the new `else:` block post-patch).
       Models `select_cascade_fields`. Driven at TWO tiers:

       (O2a) END-TO-END, zero bridge: real Django models + a real in-memory
             sqlite schema; `Collector.collect([origin])` is called for real and
             the cascade SELECT's column set is read out of the REAL captured
             SQL via `CaptureQueriesContext`. This drives the entire patched
             function — the real `related_objects` queryset, the real
             `get_candidate_relations_to_delete` / `foreign_related_fields`
             referenced-field computation, the real `.only(*referenced_fields)`,
             the real SQL compiler. `all_fields` / `referenced` are whatever the
             real model graph yields; they are READ OFF the real metadata, never
             assumed. Covers the exact F2P shape plus graph shapes that place
             the pk inside / outside the referenced set and that make the
             referenced set empty.

       (O2b) FULL-DOMAIN, over the real components the patched branch composes:
             the real `Collector._has_signal_listeners` (real signal registry),
             the real `sub_objs.query.select_related` observation (a real
             `select_related()` queryset vs a real plain one), and the real
             `QuerySet.only(*tuple(referenced_fields))` whose resulting loaded
             column set is read from the REAL SQL compiler (`as_sql`). This is
             the patched branch's own data flow, statement for statement, with
             every step real repo code; it exists only so the abstract carrier
             domain can be swept exhaustively (O2a cannot reach an arbitrary
             (all_fields, referenced) pair, because a real model graph
             determines its own referenced set). O2b is cross-checked against
             O2a on every shape O2a covers: they must agree, and the script
             fails if they do not.

INCOMING-QUERY RESTRICTION AXIS (the dimension the earlier revision lacked)
-------------------------------------------------------------------------
The pending related-set query is NOT always unrestricted. `Collector.related_objects`
obtains it from `related_model._base_manager`, and a model may point
`Meta.base_manager_name` at a manager whose `get_queryset()` already narrowed the
column set; an overridden `related_objects` may narrow it too. A pending narrowing
changes the observable column set two ways, and BOTH are swept here:

  * it subtracts from what a further narrowing request can reach, because the
    query layer honours an existing deferral when a new immediate-loading set is
    named (`Query.add_immediate_loading` stores `field_names.difference(existing)`
    when the existing restriction is a deferral, `sql/query.py:1978`), so the
    consulted columns a request can still reach are `referenced - deferred`;
  * when no request is made at all, the pending query's own column set is what is
    fetched -- which need NOT be the full column set.

Generators therefore cross every oracle model with a family of pending query
states (unrestricted, `.defer(subset)`, `.only(subset)`, and the eager-fetch
observation), so `already_selected` ranges over strict parts of `all_fields`
rather than being pinned to it.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
mapping.md §2 abstracts a column (a `str` attname) to an `int` token and a
column SET to a `List[int]`, because Nagini bans `str` indexing. Inverted here:
for each real oracle model, its real concrete-field attnames are enumerated in a
fixed order, token `i` <-> the `i`-th real attname. A model-side `List[int]`
lowers to a `tuple` of real attnames handed to the real `.only(...)`; a real
loaded column set lifts back to the token set. Because mapping.md §2 states the
carrier preserves the *set* the SELECT fetches (column order is not observable
in the SQL column list the F2P test asserts on), both sides are compared as
sets. `select_related` bridges by truthiness (real falsy `False`/`{}` vs a real
truthy dict), and `pre`/`post` bridge by identity onto real connected receivers.

INPUT DOMAIN — every generated input satisfies the model's Requires
------------------------------------------------------------------
`select_cascade_fields`'s Requires is exactly: `referenced` and
`already_selected` are sub-collections of `all_fields`, and `pk` is one of
`all_fields` (plus fractional list permissions, which any distinct Python lists
satisfy). Generation therefore picks a real oracle model, takes `all_fields` =
its real attname tokens, picks the consulted set as a SUBSET of those tokens,
and takes `already_selected` from a REAL pending queryset's compiled column set
— so the Requires holds by construction and is asserted per input rather than
trusted. The domain is NOT narrowed to keep the check green: it deliberately
includes consulted sets that omit the pk token, the empty consulted set, and
pending querysets that already carry a narrowing, all of which are reachable in
the real repo (O2a drives them through the real `Collector.collect`).

For the smaller oracle models the (consulted-subset x flag x pending-state)
space is FINITE and is ENUMERATED EXHAUSTIVELY (all 2^|all_fields| consulted
subsets x all 8 flag triples x every pending state); seeded fuzz over the same
space then fills the count to >= 1e5. Exhaustive enumeration of a finite space
is a stronger check than 1e5 samples of it, not a weaker one.

Boundary cases forced first: the exact F2P shape, empty `all_fields`, singleton,
consulted empty / == `all_fields` / omitting the pk, a pending narrowing that
removes exactly the consulted columns (so nothing consulted is still reachable),
and each of the three impl branches taken under each of the four ways the
no-request guard can be released (whole_row_required, pre, post, pre+post).

Pinned fuzz seed: 110870 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements. On a disagreement the input and BOTH outputs are
printed and the exit status is 1. stdlib + django only.
"""
import json
import random
import re
import sys

SEED = 110870
N_FUZZ_TARGET = 100000
MAX_REPORT = 8


# =====================================================================
# SHADOW — model.py's impl regions, verbatim, contract calls deleted
# =====================================================================

# --- from model.py `# pure-start` region, contracts stripped ----------
def exposed_to_observers(pre, post):
    return pre or post


# --- from model.py `rows_exposed_to_observers` `# impl-start` region --
def rows_exposed_to_observers(pre, post):
    return pre or post


# --- from model.py `select_cascade_fields` `# impl-start` region ------
# Verbatim; only Invariant(...)/Assert(...) lines and the
# `# invariants-start`/`-end` markers are deleted.
def select_cascade_fields(all_fields, already_selected, referenced, pk,
                          whole_row_required, pre, post):
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    if leave_alone:
        i = 0
        while i < len(already_selected):
            result = result + [already_selected[i]]
            i = i + 1
    elif reduce_cols:
        n_ref = len(referenced)
        i = 0
        found = False
        while i < len(referenced):
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        i = 0
        while i < len(all_fields):
            result = result + [all_fields[i]]
            i = i + 1
    return result


# =====================================================================
# ORACLE plumbing — real Django, real patched deletion module
# =====================================================================

def bootstrap():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


APP_LABEL = "auth"


def _mk(name, attrs):
    from django.db import models
    a = dict(attrs)
    a["__module__"] = __name__
    a["Meta"] = type("Meta", (), {"app_label": APP_LABEL})
    return type(name, (models.Model,), a)


def build_oracle_models():
    """Real Django model graphs. Each entry is a (label, Origin, Related) triple
    whose cascade from Origin reaches Related; the referenced set is whatever the
    real graph yields, never assumed.

    The shapes are chosen to span the referenced/all relationship that the
    modelled decision discriminates on:
      F2P    - the exact test shape (pk AND a to_field target referenced)
      PKONLY - only the pk referenced
      TOFLD  - only a to_field target referenced: pk NOT in referenced
      TOFLD2 - two to_field targets, pk NOT in referenced
      GENREL - no incoming FK at all: referenced is EMPTY (a GenericRelation
               keeps can_fast_delete False so the SELECT still happens)
      WIDE   - the F2P shape with extra never-referenced columns
    """
    from django.db import models
    from django.contrib.contenttypes.fields import (
        GenericForeignKey, GenericRelation,
    )
    from django.contrib.contenttypes.models import ContentType

    specs = []
    created = []

    # --- F2P: Origin <- Referrer <- SecondReferrer{pk FK, to_field FK} -------
    O = _mk("CfO1", {})
    R = _mk("CfR1", {"origin": models.ForeignKey(O, models.CASCADE),
                     "unique_field": models.IntegerField(unique=True),
                     "large_field": models.TextField(default="")})
    S = _mk("CfS1", {
        "referrer": models.ForeignKey(R, models.CASCADE, related_name="+"),
        "other_referrer": models.ForeignKey(R, models.CASCADE,
                                            to_field="unique_field",
                                            related_name="+")})
    specs.append(("F2P", O, R))
    created += [O, R, S]

    # --- PKONLY: only the pk is a referenced FK target ----------------------
    O = _mk("CfO2", {})
    R = _mk("CfR2", {"origin": models.ForeignKey(O, models.CASCADE),
                     "unique_field": models.IntegerField(unique=True),
                     "large_field": models.TextField(default="")})
    S = _mk("CfS2", {"referrer": models.ForeignKey(R, models.CASCADE,
                                                   related_name="+")})
    specs.append(("PKONLY", O, R))
    created += [O, R, S]

    # --- TOFLD: pk NOT among the referenced FK targets ---------------------
    O = _mk("CfO3", {})
    R = _mk("CfR3", {"origin": models.ForeignKey(O, models.CASCADE),
                     "unique_field": models.IntegerField(unique=True),
                     "large_field": models.TextField(default="")})
    S = _mk("CfS3", {"other_referrer": models.ForeignKey(
        R, models.CASCADE, to_field="unique_field", related_name="+")})
    specs.append(("TOFLD", O, R))
    created += [O, R, S]

    # --- TOFLD2: two to_field targets, pk still NOT referenced -------------
    O = _mk("CfO4", {})
    R = _mk("CfR4", {"origin": models.ForeignKey(O, models.CASCADE),
                     "unique_field": models.IntegerField(unique=True),
                     "uf2": models.IntegerField(unique=True, null=True),
                     "large_field": models.TextField(default="")})
    S = _mk("CfS4", {
        "a": models.ForeignKey(R, models.CASCADE, to_field="unique_field",
                               related_name="+"),
        "b": models.ForeignKey(R, models.CASCADE, to_field="uf2",
                               related_name="+")})
    specs.append(("TOFLD2", O, R))
    created += [O, R, S]

    # --- GENREL: referenced is EMPTY, but the SELECT still happens ---------
    O = _mk("CfO5", {})
    G = _mk("CfG5", {"content_type": models.ForeignKey(ContentType,
                                                       models.CASCADE),
                     "object_id": models.PositiveIntegerField(),
                     "obj": GenericForeignKey()})
    R = _mk("CfR5", {"origin": models.ForeignKey(O, models.CASCADE),
                     "large_field": models.TextField(default=""),
                     "gens": GenericRelation(G)})
    specs.append(("GENREL", O, R))
    created += [O, G, R]

    # --- WIDE: F2P shape plus extra never-referenced columns ---------------
    O = _mk("CfO6", {})
    rattrs = {"origin": models.ForeignKey(O, models.CASCADE),
              "unique_field": models.IntegerField(unique=True)}
    for i in range(3):
        rattrs["extra%d" % i] = models.TextField(default="")
    R = _mk("CfR6", rattrs)
    S = _mk("CfS6", {
        "referrer": models.ForeignKey(R, models.CASCADE, related_name="+"),
        "other_referrer": models.ForeignKey(R, models.CASCADE,
                                            to_field="unique_field",
                                            related_name="+")})
    specs.append(("WIDE", O, R))
    created += [O, R, S]

    from django.db import connection
    with connection.schema_editor() as se:
        for m in created:
            se.create_model(m)
    return specs


def real_referenced_attnames(R):
    """The patched branch's own referenced-field expression, evaluated by the
    REAL repo helpers (`get_candidate_relations_to_delete` +
    `foreign_related_fields`) on real model metadata."""
    from itertools import chain
    from django.db.models.deletion import get_candidate_relations_to_delete
    return set(chain.from_iterable(
        (rf.attname for rf in rel.field.foreign_related_fields)
        for rel in get_candidate_relations_to_delete(R._meta)
    ))


def _receiver(instance=None, **kwargs):
    pass


class Signals(object):
    """Connect/disconnect real receivers on the real signal registry."""

    def __init__(self, sender, pre, post, m2m):
        from django.db.models import signals
        self.signals = signals
        self.sender = sender
        self.names = [n for n, on in (("pre_delete", pre), ("post_delete", post),
                                      ("m2m_changed", m2m)) if on]

    def __enter__(self):
        for n in self.names:
            getattr(self.signals, n).connect(_receiver, sender=self.sender)
        return self

    def __exit__(self, *exc):
        for n in self.names:
            getattr(self.signals, n).disconnect(_receiver, sender=self.sender)
        return False


# --- O1: the REAL patched Collector._has_signal_listeners -------------------

def oracle_has_signal_listeners(collector, R, pre, post, m2m):
    with Signals(R, pre, post, m2m):
        return bool(collector._has_signal_listeners(R))


# --- O2a: the REAL patched Collector.collect, end to end -------------------

def oracle_collect_columns(O, R, pre, post, m2m, pending):
    """Call the REAL patched `Collector.collect` and read the cascade SELECT's
    column set out of the REAL captured SQL. Returns a set of real attnames, or
    None if no SELECT over R's table was issued.

    `pending` is a callable mapping the real related-set queryset to the pending
    queryset the branch is to receive, installed by overriding
    `related_objects` — the same reachability the patch's own comment names
    ("this should only happen in the rare cases where .related_objects is
    overridden anyway") and the one `django.contrib.admin.utils.NestedObjects`
    already uses in-tree. `None` leaves the base-manager queryset untouched."""
    from django.db import connection
    from django.db.models.deletion import Collector
    from django.test.utils import CaptureQueriesContext

    if pending is None:
        collector = Collector(using="default")
    else:
        class _C(Collector):
            def related_objects(self, related, objs):
                return pending(super().related_objects(related, objs))
        collector = _C(using="default")

    fm = field_map(R)
    with Signals(R, pre, post, m2m):
        with CaptureQueriesContext(connection) as ctx:
            collector.collect([O(pk=1)])
        for q in ctx.captured_queries:
            sql = q["sql"]
            if not sql.startswith("SELECT") or " FROM " not in sql:
                continue
            head = sql[6:sql.index(" FROM ")]
            cols = set()
            for tbl, col in re.findall(r'"([^"]+)"\."([^"]+)"', head):
                if (tbl, col) in fm:
                    cols.add(fm[(tbl, col)])
            if cols and R._meta.db_table in sql:
                return cols
    return None


# --- O2b: the patched branch's data flow over the real components ----------

def oracle_branch_columns(collector, R, sub_objs, referenced_attnames,
                          pre, post, m2m):
    """The patched `collect` else-block, statement for statement, with every
    component the REAL repo's:

        if not (sub_objs.query.select_related or
                self._has_signal_listeners(related_model)):
            sub_objs = sub_objs.only(*tuple(referenced_fields))

    then the loaded column set is read from the REAL SQL compiler. `sub_objs`
    is a REAL pending queryset (possibly already carrying a narrowing of its
    own, see the incoming-query axis above); `referenced_attnames` is the RAW
    consulted set the branch itself computes, handed to the real `.only()`
    unfiltered — it is the query layer, not this script, that decides what a
    pending narrowing leaves reachable. Returns a set of real attnames."""
    with Signals(R, pre, post, m2m):
        if not (sub_objs.query.select_related
                or collector._has_signal_listeners(R)):
            sub_objs = sub_objs.only(*tuple(referenced_attnames))
    return compiled_columns(sub_objs, R)


def field_map(R):
    """(db_table, column) -> attname over EVERY concrete field of R, so the
    oracle's column universe is the same universe as `all_fields` even when the
    model spans more than one table."""
    return {(f.model._meta.db_table, f.column): f.attname
            for f in R._meta.concrete_fields}


def compiled_columns(qs, R):
    """The column set the REAL SQL compiler emits for R's own concrete fields."""
    fm = field_map(R)
    sql, _params = qs.query.get_compiler("default").as_sql()
    head = sql[6:sql.index(" FROM ")]
    out = set()
    for tbl, col in re.findall(r'"([^"]+)"\."([^"]+)"', head):
        if (tbl, col) in fm:
            out.add(fm[(tbl, col)])
    return out


def deferral_attnames(qs):
    """The pending queryset's own DEFERRAL set — the names the query layer
    subtracts when a new immediate-loading set is named
    (`Query.add_immediate_loading`: `field_names.difference(existing)` when the
    existing restriction is a deferral, `sql/query.py:1978`). Empty when the
    pending restriction is an immediate-loading set, which that call REPLACES."""
    existing, defer = qs.query.deferred_loading
    return set(existing) if defer else set()


# =====================================================================
# type bridge — mapping.md §2 inverted, plus the pending-query states
# =====================================================================

def subsets(items):
    n = len(items)
    for mask in range(1 << n):
        yield [items[i] for i in range(n) if mask >> i & 1]


class Bridge(object):
    """token i <-> the i-th real concrete-field attname of R, together with the
    family of REAL pending related-set querysets whose own column restriction
    the branch inherits."""

    def __init__(self, label, O, R):
        self.label = label
        self.O = O
        self.R = R
        self.attnames = [f.attname for f in R._meta.concrete_fields]
        self.tok = {a: i for i, a in enumerate(self.attnames)}
        self.all_tokens = list(range(len(self.attnames)))
        self.pk_token = self.tok[R._meta.pk.attname]
        self.real_referenced = real_referenced_attnames(R)
        self.referenced_tokens = sorted(self.tok[a]
                                        for a in self.real_referenced)
        self.pending = self._build_pending()

    def lower(self, tokens):
        """model List[int] -> real attnames"""
        return [self.attnames[t] for t in tokens]

    def lift(self, attnames):
        """real attname set -> model token set"""
        return set(self.tok[a] for a in attnames)

    # --- the pending-query axis -----------------------------------------
    def _restriction_subsets(self):
        """Which column subsets to use as pending restrictions. Enumerated
        EXHAUSTIVELY when the carrier is small enough that the whole product
        stays finite and affordable; otherwise a deterministic family that still
        contains every boundary the decision turns on (nothing, everything, each
        single column, the consulted set, and its complement)."""
        toks = self.all_tokens
        if len(toks) <= 4:
            return [tuple(s) for s in subsets(toks)]
        ref = set(self.referenced_tokens)
        fam = [(), tuple(toks), tuple(sorted(ref)),
               tuple(t for t in toks if t not in ref)]
        fam += [(t,) for t in toks]
        seen, out = set(), []
        for s in fam:
            if s not in seen:
                seen.add(s)
                out.append(s)
        return out

    def _build_pending(self):
        """(state_label, pending_qs, pending_fn) for every pending state.

        `pending_qs` is a REAL queryset off R's own base manager carrying that
        state (what O2b consumes); `pending_fn` is the same transform as a
        callable, so O2a can install it on the REAL `related_objects` result.
        """
        base = self.R._base_manager.using("default").all()
        out = [("plain", base, None)]
        has_origin = any(f.name == "origin"
                         for f in self.R._meta.concrete_fields)
        if has_origin:
            # the real eager-fetch observation the guard reads
            out.append(("select_related",
                        base.select_related("origin"),
                        lambda q: q.select_related("origin")))
        for s in self._restriction_subsets():
            names = tuple(self.lower(list(s)))
            out.append(("defer%s" % (sorted(names),),
                        base.defer(*names),
                        (lambda nm: (lambda q: q.defer(*nm)))(names)))
            out.append(("only%s" % (sorted(names),),
                        base.only(*names),
                        (lambda nm: (lambda q: q.only(*nm)))(names)))
        return out


# =====================================================================
# differential driver
# =====================================================================

class Checker(object):
    def __init__(self):
        bootstrap()
        from django.db.models.deletion import Collector
        self.collector = Collector(using="default")
        self.bridges = []
        for label, O, R in build_oracle_models():
            self.bridges.append(Bridge(label, O, R))
        self.by_label = {b.label: b for b in self.bridges}
        # Per (bridge, pending state) the pending query's OWN observables, read
        # once off the real queryset: the column set it already fetches, the
        # deferral set a further narrowing request would have subtracted from,
        # and the eager-fetch flag.
        self.pstate = {}
        for b in self.bridges:
            for slabel, qs, fn in b.pending:
                self.pstate[(b.label, slabel)] = {
                    "qs": qs, "fn": fn,
                    "already": sorted(b.lift(compiled_columns(qs, b.R))),
                    "deferred": b.lift(deferral_attnames(qs)),
                    "wrr": bool(qs.query.select_related),
                }
        self.failures = []
        self.n_failures = 0
        self.kinds = {}
        self.classes = {}
        self.checked = 0
        # Set only when the two oracle tiers disagree with EACH OTHER, or the
        # end-to-end oracle cannot be observed at all. That indicts this
        # script's bridge rather than the model, so the run aborts immediately
        # instead of reporting a model finding built on a broken oracle.
        self.bridge_fault = False
        self.branch_hits = {"reduced": 0, "full-reset": 0, "pending-stands": 0}
        self.guard_release = {"whole_row_required": 0, "pre": 0, "post": 0,
                              "pre+post": 0}
        self.pending_hits = {"unrestricted": 0, "narrowed": 0}

    # --- leg 1: rows_exposed_to_observers vs the real helper ---------------
    def check_exposure(self, b, pre, post, m2m):
        shadow = rows_exposed_to_observers(pre, post)
        real = oracle_has_signal_listeners(self.collector, b.R, pre, post, m2m)
        self.checked += 1
        if bool(shadow) != real:
            self.record("exposure-predicate",
                        {"model": b.label, "pre": pre, "post": post,
                         "m2m": m2m},
                        shadow, real,
                        "shadow rows_exposed_to_observers vs REAL "
                        "Collector._has_signal_listeners")
            return False
        # the pure helper the impl's postcondition is phrased over
        if bool(exposed_to_observers(pre, post)) != real:
            self.record("exposure-pure", {"model": b.label, "pre": pre,
                                          "post": post, "m2m": m2m},
                        exposed_to_observers(pre, post), real,
                        "shadow exposed_to_observers vs REAL helper")
            return False
        return True

    # --- leg 2: select_cascade_fields vs the real patched collect ----------
    def check_columns(self, b, raw_referenced_tokens, pre, post, m2m,
                      slabel, kind, end_to_end=False):
        """`raw_referenced_tokens` is the consulted set the patched branch
        itself computes and hands to `.only()` UNFILTERED. The model's
        `referenced` input is what a narrowing request can still REACH, i.e.
        that set minus the pending query's deferral set — the query layer's own
        subtraction (`sql/query.py:1978`), lifted through the bridge, never
        assumed of the oracle."""
        st = self.pstate[(b.label, slabel)]
        all_tokens = b.all_tokens
        already = st["already"]
        referenced = sorted(t for t in set(raw_referenced_tokens)
                            if t not in st["deferred"])
        whole_row_required = st["wrr"]

        # Requires of select_cascade_fields, asserted per input, not trusted.
        assert set(referenced) <= set(all_tokens), \
            "generated input violates Requires (referenced not a subset)"
        assert set(already) <= set(all_tokens), \
            "generated input violates Requires (already_selected not a subset)"
        assert b.pk_token in set(all_tokens), \
            "generated input violates Requires (pk not a column)"

        shadow = select_cascade_fields(list(all_tokens), list(already),
                                       list(referenced), b.pk_token,
                                       whole_row_required, pre, post)

        # census: which cell of the partition this input lands in
        if whole_row_required or pre or post:
            self.branch_hits["pending-stands"] += 1
            if whole_row_required:
                self.guard_release["whole_row_required"] += 1
            if pre and post:
                self.guard_release["pre+post"] += 1
            elif pre:
                self.guard_release["pre"] += 1
            elif post:
                self.guard_release["post"] += 1
        elif len(referenced) > 0:
            self.branch_hits["reduced"] += 1
        else:
            self.branch_hits["full-reset"] += 1
        self.pending_hits["unrestricted" if set(already) == set(all_tokens)
                          and not whole_row_required else "narrowed"] += 1

        raw_attnames = b.lower(sorted(set(raw_referenced_tokens)))
        real_attnames = oracle_branch_columns(
            self.collector, b.R, st["qs"], raw_attnames, pre, post, m2m)
        self.checked += 1

        shadow_set = set(shadow)
        real_set = b.lift(real_attnames)
        inp = {"model": b.label, "pending_state": slabel,
               "all_fields(tokens)": sorted(all_tokens),
               "all_fields(attnames)": b.attnames,
               "raw_consulted(attnames)": raw_attnames,
               "pending_deferred(attnames)": sorted(b.lower(sorted(st["deferred"]))),
               "referenced(tokens)": referenced,
               "referenced(attnames)": sorted(b.lower(referenced)),
               "already_selected(attnames)": sorted(b.lower(already)),
               "whole_row_required": whole_row_required,
               "pre": pre, "post": post, "m2m": m2m,
               "pk_token": b.pk_token,
               "pk_in_referenced": b.pk_token in set(referenced)}
        ok = True
        if shadow_set != real_set:
            self.record(kind, inp, sorted(shadow_set), sorted(real_set),
                        "shadow select_cascade_fields vs REAL patched collect "
                        "branch (real _has_signal_listeners + real pending "
                        "queryset + real .only + real SQL compiler)",
                        extra={"shadow(attnames)":
                                   sorted(b.lower(sorted(shadow_set))),
                               "real(attnames)": sorted(real_attnames)})
            ok = False

        # O2b vs O2a cross-check: whenever this input IS the real graph's own
        # consulted set, the full patched `Collector.collect` must produce the
        # same column set as the branch-level oracle. Guards the O2b bridge.
        if end_to_end:
            e2e = oracle_collect_columns(b.O, b.R, pre, post, m2m, st["fn"])
            self.checked += 1
            if e2e is None:
                self.record("oracle-no-select",
                            {"model": b.label, "pending_state": slabel,
                             "pre": pre, "post": post, "m2m": m2m},
                            None, None,
                            "REAL Collector.collect issued no SELECT over the "
                            "related table; the end-to-end oracle cannot be "
                            "observed for this shape")
                self.bridge_fault = True
                return False
            if e2e != real_attnames:
                self.record("oracle-disagreement",
                            {"model": b.label, "pending_state": slabel,
                             "pre": pre, "post": post, "m2m": m2m},
                            sorted(real_attnames), sorted(e2e),
                            "branch-level oracle (O2b) disagrees with the "
                            "end-to-end REAL Collector.collect (O2a): the "
                            "bridge, not the model, is at fault")
                self.bridge_fault = True
                return False
            if set(shadow_set) != b.lift(e2e):
                self.record(kind + "-end-to-end", inp,
                            sorted(shadow_set), sorted(b.lift(e2e)),
                            "shadow select_cascade_fields vs the FULL REAL "
                            "patched Collector.collect (no bridge: real SQL)",
                            extra={"shadow(attnames)":
                                       sorted(b.lower(sorted(shadow_set))),
                                   "real SELECT(attnames)": sorted(e2e)})
                ok = False
        return ok

    def record(self, kind, inp, shadow, real, what, extra=None):
        f = {"kind": kind, "what": what, "input": inp,
             "shadow": shadow, "real": real}
        if extra:
            f["detail"] = extra
        self.n_failures += 1
        self.kinds[kind] = self.kinds.get(kind, 0) + 1
        # Classify the divergence so the report characterises the whole class
        # rather than just the first few witnesses.
        if kind.startswith("columns") and "referenced(attnames)" in inp:
            if inp.get("whole_row_required") or inp.get("pre") or inp.get("post"):
                key = "pending-stands"
            elif not inp["referenced(attnames)"]:
                key = "referenced-empty"
            elif not inp.get("pk_in_referenced", True):
                key = "pk-not-in-referenced"
            else:
                key = "other"
            if inp.get("pending_deferred(attnames)"):
                key += "/pending-narrowed"
            self.classes[key] = self.classes.get(key, 0) + 1
        # Keep only the first MAX_REPORT witnesses in full detail; the run
        # continues to its full input budget so the census is complete.
        if len(self.failures) < MAX_REPORT:
            self.failures.append(f)


FLAGS = [(pre, post, m2m)
         for pre in (False, True)
         for post in (False, True)
         for m2m in (False, True)]


def main():
    try:
        import django  # noqa: F401
    except ImportError as exc:
        print("G-CONF ERROR: django not importable: %r" % (exc,))
        return 1

    ck = Checker()

    # ---- boundary / exhaustive phase -----------------------------------
    # (a) the exposure predicate over the full finite flag space, per model.
    for b in ck.bridges:
        for pre, post, m2m in FLAGS:
            ck.check_exposure(b, pre, post, m2m)
            if ck.bridge_fault:
                return report(ck)

    # (b) each real graph's OWN consulted set, driven END-TO-END through the
    #     full real patched Collector.collect, over the whole flag space and
    #     EVERY pending-query state. This is the zero-bridge leg; it includes
    #     the exact F2P shape, and it is the leg that exercises a pending
    #     related-set query which already carries a narrowing of its own.
    for b in ck.bridges:
        for slabel, _qs, _fn in b.pending:
            for pre, post, m2m in FLAGS:
                ck.check_columns(b, b.referenced_tokens, pre, post, m2m,
                                 slabel, "columns", end_to_end=True)
                if ck.bridge_fault:
                    return report(ck)

    # (c) EXHAUSTIVE enumeration of the finite carrier space for every oracle
    #     model: all 2^|all_fields| consulted subsets x all 8 flag triples x
    #     every pending-query state. Includes the empty subset, the full
    #     subset, every subset that omits the pk token, and every pending state
    #     that leaves the consulted set wholly, partly, or not at all reachable.
    exhaustive = 0
    for b in ck.bridges:
        for ref in subsets(b.all_tokens):
            for slabel, _qs, _fn in b.pending:
                for pre, post, m2m in FLAGS:
                    ck.check_columns(b, ref, pre, post, m2m, slabel, "columns")
                    exhaustive += 1
                    if ck.bridge_fault:
                        return report(ck)

    # (d) empty / singleton all_fields and a pending set strictly inside it:
    #     the model admits them, so pin them against the model's own cell
    #     contract directly (no real model has zero or one column, so there is
    #     nothing real to drive; the shadow is checked for internal consistency
    #     only and is NOT counted as an oracle comparison).
    DEGEN = [([0], [0], [], 0), ([0], [0], [0], 0),
             ([0, 1], [0, 1], [1], 0), ([0, 1], [0, 1], [0], 0),
             ([0, 1], [0, 1], [], 0), ([0, 1], [0], [1], 0),
             ([0, 1], [0], [], 0), ([0, 1], [1], [1], 1),
             ([0, 1, 2], [0, 2], [2], 0), ([0, 1, 2], [0], [], 0)]
    for all_f, already, ref, pk in DEGEN:
        for wrr in (False, True):
            for pre, post, m2m in FLAGS:
                got = select_cascade_fields(list(all_f), list(already),
                                            list(ref), pk, wrr, pre, post)
                # The model's own cell contract on a degenerate carrier: no
                # request is made when the whole row is required or the rows are
                # exposed, and then the pending set stands; otherwise the fetch
                # is narrowed when at least one consulted column is reachable,
                # with the row identity retained; and naming nothing resets to
                # the full set.
                if wrr or pre or post:
                    want = list(already)
                elif len(ref) > 0:
                    want = list(ref) if pk in ref else list(ref) + [pk]
                else:
                    want = list(all_f)
                if list(got) != list(want):
                    ck.record("shadow-degenerate",
                              {"all_fields": all_f,
                               "already_selected": already,
                               "referenced": ref, "pk": pk,
                               "whole_row_required": wrr,
                               "pre": pre, "post": post},
                              got, want,
                              "shadow disagrees with the model's own cell "
                              "contract on a degenerate carrier")
                    return report(ck)

    # ---- seeded fuzz over the SAME space, to reach >= 1e5 ---------------
    rng = random.Random(SEED)
    fuzz = 0
    while ck.checked < N_FUZZ_TARGET:
        b = ck.bridges[rng.randrange(len(ck.bridges))]
        toks = b.all_tokens
        # a uniformly random subset of the token set (Requires-satisfying)
        ref = [t for t in toks if rng.random() < 0.5]
        if rng.random() < 0.15:
            ref = list(b.referenced_tokens)          # the real graph's own set
        elif rng.random() < 0.10:
            ref = [t for t in toks if t != b.pk_token]   # pk deliberately out
        rng.shuffle(ref)
        pre, post, m2m = FLAGS[rng.randrange(len(FLAGS))]
        slabel = b.pending[rng.randrange(len(b.pending))][0]
        ck.check_columns(b, ref, pre, post, m2m, slabel, "columns")
        ck.check_exposure(b, pre, post, m2m)
        fuzz += 1
        if ck.bridge_fault:
            return report(ck, exhaustive=exhaustive, fuzz=fuzz)

    return report(ck, exhaustive=exhaustive, fuzz=fuzz)


def report(ck, exhaustive=0, fuzz=0):
    if ck.n_failures:
        print("G-CONF FAIL: %d disagreement(s) between the shadow of model.py's "
              "impl region and the REAL patched repo function, over %d checked "
              "inputs (seed=%d)." % (ck.n_failures, ck.checked, SEED))
        if ck.bridge_fault:
            print("  NOTE: a bridge fault was detected (the two oracle tiers "
                  "disagree with each other, or the end-to-end oracle could "
                  "not be observed). Fix the bridge before reading these as a "
                  "model finding.")
        print("")
        print("  witnesses (first %d of %d):" % (len(ck.failures),
                                                 ck.n_failures))
        for f in ck.failures:
            print("")
            print("  [%s] %s" % (f["kind"], f["what"]))
            print("    input : %s" % json.dumps(f["input"], sort_keys=True))
            print("    shadow: %s" % json.dumps(f["shadow"]))
            print("    real  : %s" % json.dumps(f["real"]))
            if "detail" in f:
                print("    detail: %s" % json.dumps(f["detail"], sort_keys=True))
        print("")
        print("  census by kind : %s" % json.dumps(ck.kinds, sort_keys=True))
        print("  divergence class: %s" % json.dumps(ck.classes, sort_keys=True))
        print("")
        print(json.dumps({"checked": ck.checked,
                          "disagreements": ck.n_failures,
                          "kinds": ck.kinds, "classes": ck.classes,
                          "bridge_fault": ck.bridge_fault,
                          "seed": SEED, "status": "fail"}))
        return 1

    print("G-CONF OK: shadow of model.py's impl regions "
          "(rows_exposed_to_observers, select_cascade_fields) == the REAL "
          "patched Collector._has_signal_listeners / Collector.collect on %d "
          "inputs (%d exhaustive carrier enumerations + %d fuzz, seed %d); "
          "cells reduced=%d full-reset=%d pending-stands=%d; pending query "
          "narrowed on %d inputs; 0 disagreements."
          % (ck.checked, exhaustive, fuzz, SEED,
             ck.branch_hits["reduced"], ck.branch_hits["full-reset"],
             ck.branch_hits["pending-stands"], ck.pending_hits["narrowed"]))
    print(json.dumps({"checked": ck.checked, "disagreements": 0, "seed": SEED,
                      "exhaustive": exhaustive, "fuzz": fuzz,
                      "cells": ck.branch_hits,
                      "guard_release": ck.guard_release,
                      "pending": ck.pending_hits,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "real patched Collector._has_signal_listeners "
                                "+ Collector.collect (called)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
