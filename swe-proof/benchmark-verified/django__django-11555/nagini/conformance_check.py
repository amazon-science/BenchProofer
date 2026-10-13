#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11555 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped; List[int] carriers stay
plain Python lists. The single @ContractOnly callee `resolve_name(item_id)`
(the unchanged name-resolution machinery) is realized by replaying the REAL
repo callee — the recursive `SQLCompiler.find_ordering_name(item, opts, alias,
order, already_seen)` call — with exactly the arguments the real loop passed
for that item (recorded during the oracle run; mapping.md section 3.2 defines
the axiom to BE whatever the real machinery produces, so the recorded real
call is its faithful realization).

ORACLE: the REAL patched repo region per mapping.md section 1 — the
related-model default-ordering expansion of `SQLCompiler.find_ordering_name`
(django/db/models/sql/compiler.py), driven through its public entry: a child
model's auto-created parent pointer is resolved with the parent's
`Meta.ordering` set to the input under test, which routes control into the
`for item in opts.ordering:` loop and returns that loop's `results` list
directly. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed resolves the patched module.

Type bridge (mapping.md section 2): each ordering item maps to a (kind, id)
pair — kind 1 for an already-formed ordering-expression object, kind 0 for a
textual name; ids are interned per item occurrence. The shadow's output id
list maps back to (expression, is_ref) targets: a kind-1 id maps to the very
Meta item (identity must be preserved, is_ref False); a kind-0 id's targets
are the entries of the replayed real machinery call. Real vs shadow entries
compare by object identity for pass-through targets and by structural
signature (class, repr, direction/null flags, is_ref) for name-resolved
targets — replay and oracle run in the same compiler state, so signatures of
matching entries coincide exactly.

Input domain: Requires demands only two equal-length carriers, i.e. any
default ordering sequence; the modeled loop runs when the related model's
default ordering is non-empty, so inputs are orderings of 1..6 items mixing
textual names over the parent's local fields (with optional leading direction
prefix) and already-formed ordering expressions (varying field, direction,
nulls placement), plus both requested default orders. Boundary inputs cover a
lone expression item, expression-first / name-first mixes, duplicates, and
all-expression / all-name orderings.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz orderings.
Pinned fuzz seed: 11555.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (Django is the system under test).
"""
import json
import random
import sys

SEED = 11555
N_FUZZ = 100_000


# --- interning: ordering item / produced target <-> int id --------------------

_ID2VAL = {}
_NEXT = [1]


def intern(val):
    i = _NEXT[0]
    _NEXT[0] += 1
    _ID2VAL[i] = val
    return i


# --- @ContractOnly callee bridged to the REAL recorded machinery call ---------
# During the oracle run a wrapper records every depth-1 recursive call the
# real loop makes (its full argument tuple). The shadow's resolve_name(item_id)
# consumes the next recorded call, checks it targets this very item (bridge
# sanity), replays the REAL callee with those arguments, and returns fresh ids
# for the produced targets.

_RECORDED = []          # queue of (name, opts, alias, order, seen) tuples
_REPLAY = {"orig": None, "compiler": None}


class BridgeMismatch(Exception):
    pass


def resolve_name(item_id):
    # The shadow's impl loop walks the ordering back-to-front, so it consumes
    # name items in reverse; the real loop records front-to-back — pop from
    # the end to align the two orders.
    _tag, item = _ID2VAL[item_id]
    if not _RECORDED:
        raise BridgeMismatch(
            "shadow expands name item %r but the real loop made no further "
            "machinery call" % (item,))
    name, opts, alias, order, seen = _RECORDED.pop()
    if name is not item:
        raise BridgeMismatch(
            "shadow expands name item %r but the real loop's next machinery "
            "call was for %r" % (item, name))
    entries = _REPLAY["orig"](
        _REPLAY["compiler"], name, opts, alias, order,
        set(seen) if seen is not None else None)
    return [intern(("resolved", e)) for e in entries]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def expand_default_ordering(kinds, ids):
    result = []
    i = len(kinds)
    while i > 0:
        k = kinds[i - 1]
        d = ids[i - 1]
        if k == 1:
            # An already-formed ordering expression: pass it through verbatim
            # as a single target carrying its own identity.
            piece = [d]
        else:
            # A textual name: expand it through the name-resolution machinery.
            piece = resolve_name(d)
        result = piece + result
        i = i - 1
    return result


# --- comparison of produced targets --------------------------------------------

def signature(entry):
    expr, is_ref = entry
    return (type(expr).__name__, repr(expr),
            getattr(expr, "descending", None),
            getattr(expr, "nulls_first", None),
            getattr(expr, "nulls_last", None),
            bool(is_ref))


def main():
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
    from django.db.models import F
    from django.db.models.expressions import OrderBy
    from django.db.models.sql.compiler import SQLCompiler

    class Parent(models.Model):
        name = models.CharField(max_length=20)
        rank = models.IntegerField()

        class Meta:
            app_label = "confcheck"
            ordering = ("name",)

    class Child(Parent):
        class Meta:
            app_label = "confcheck"

    orig = SQLCompiler.find_ordering_name
    _REPLAY["orig"] = orig
    depth = [0]

    def recorder(self, name, opts, alias=None, default_order="ASC",
                 already_seen=None):
        if depth[0] == 1:
            _RECORDED.append((name, opts, alias, default_order,
                              set(already_seen) if already_seen is not None
                              else None))
        depth[0] += 1
        try:
            return orig(self, name, opts, alias, default_order, already_seen)
        finally:
            depth[0] -= 1

    fields = ["name", "rank", "pk", "id"]

    def rand_item(rng):
        if rng.random() < 0.45:
            # an already-formed ordering-expression item
            f = F(rng.choice(fields))
            desc = rng.random() < 0.5
            nulls = rng.choice([None, "first", "last"])
            kw = {}
            if nulls == "first":
                kw["nulls_first"] = True
            elif nulls == "last":
                kw["nulls_last"] = True
            return f.desc(**kw) if desc else f.asc(**kw)
        # a textual name item, optionally direction-prefixed
        return rng.choice(["", "-"]) + rng.choice(fields)

    checked = [0]

    def check_one(ordering, default_order):
        Parent._meta.ordering = tuple(ordering)
        qs = Child.objects.order_by("parent_ptr")
        compiler = qs.query.get_compiler(using="default")
        _REPLAY["compiler"] = compiler
        del _RECORDED[:]

        # --- oracle: the REAL patched region, recording its depth-1 calls ---
        # (the class attribute is swapped so the loop's recursive self-calls
        # route through the recorder; the top-level call enters at depth 0)
        SQLCompiler.find_ordering_name = recorder
        try:
            real = recorder(compiler, "parent_ptr", Child._meta,
                            default_order=default_order)
        finally:
            SQLCompiler.find_ordering_name = orig
        recorded_calls = list(_RECORDED)

        # --- shadow over the bridged carriers --------------------------------
        kinds = [1 if isinstance(it, OrderBy) else 0 for it in ordering]
        ids = [intern(("item", it)) for it in ordering]
        try:
            shadow_ids = expand_default_ordering(kinds, ids)
        except BridgeMismatch as e:
            return ("DISAGREEMENT ordering=%r default_order=%r\n"
                    "  control-flow mismatch: %s\n  real=%r"
                    % (ordering, default_order, e, real))

        if _RECORDED:
            return ("DISAGREEMENT ordering=%r default_order=%r\n"
                    "  real loop made %d machinery call(s) the shadow's name "
                    "items do not account for\n  real=%r"
                    % (ordering, default_order, len(_RECORDED), real))

        # --- map shadow ids back to targets and compare -----------------------
        if len(shadow_ids) != len(real):
            return ("DISAGREEMENT ordering=%r default_order=%r\n"
                    "  shadow produced %d target(s), real produced %d\n"
                    "  real=%r" % (ordering, default_order,
                                   len(shadow_ids), len(real), real))
        for pos, (sid, rentry) in enumerate(zip(shadow_ids, real)):
            tag, val = _ID2VAL[sid]
            if tag == "item":
                # pass-through: the very expression object, is_ref False
                if rentry[0] is not val or bool(rentry[1]) is not False:
                    return ("DISAGREEMENT ordering=%r default_order=%r pos=%d\n"
                            "  shadow: pass-through of the ordering item %r\n"
                            "  real:   %r (identity preserved: %s, is_ref=%r)"
                            % (ordering, default_order, pos, val, rentry,
                               rentry[0] is val, rentry[1]))
            else:
                if signature(val) != signature(rentry):
                    return ("DISAGREEMENT ordering=%r default_order=%r pos=%d\n"
                            "  shadow (replayed machinery): %r\n"
                            "  real:                        %r"
                            % (ordering, default_order, pos,
                               signature(val), signature(rentry)))
        checked[0] += 1
        _ID2VAL.clear()
        _NEXT[0] = 1
        return None

    def run(ordering, default_order):
        err = check_one(ordering, default_order)
        if err:
            print(err)
            sys.exit(1)

    # --- boundary inputs -------------------------------------------------------
    ob = lambda f, **kw: F(f).asc(**kw)  # noqa: E731
    boundary = [
        ([F("rank").asc(nulls_first=True)], "ASC"),           # lone expression
        ([F("rank").asc(nulls_first=True), "name"], "ASC"),   # expr first
        (["name", F("rank").desc(nulls_last=True)], "ASC"),   # name first
        (["-rank", F("name").desc(nulls_last=True), "pk"], "DESC"),
        ([F("name").desc(), F("rank").asc()], "ASC"),         # all expressions
        (["name", "-rank", "pk"], "DESC"),                    # all names
        (["name", "name"], "ASC"),                            # duplicate names
        ([F("rank").asc(), F("rank").asc()], "ASC"),          # equal-shaped exprs
        (["-pk"], "DESC"),
        ([ob("id"), "-id", ob("name", nulls_first=True), "rank"], "DESC"),
    ]
    for ordering, do in boundary:
        run(ordering, do)

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(1, 6)
        ordering = [rand_item(rng) for _ in range(n)]
        run(ordering, rng.choice(["ASC", "DESC"]))

    print("G-CONF OK: shadow impl == real default-ordering expansion on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked[0], len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
