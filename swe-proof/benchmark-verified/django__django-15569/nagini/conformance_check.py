#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15569 (nagini).

SHADOW
------
The impl region of ``model.py``, copied VERBATIM below with the contract calls
stripped -- for this bundle the region is exactly

    store[name]       = unregistered()
    view[name]        = inherited[name]
    reader_view[name] = reader_rest[name]

and the two ``@Pure`` helpers it depends on (``unregistered`` / ``other_name``,
the pure region) are copied over minus their ``@Pure`` decorator. Nothing is
restructured, renamed or re-derived; there is no ``PSeq`` in this model (the
carriers are ``Dict[int, int]``), so no sequence shim is needed. ``model.py``
has NO ``@ContractOnly`` callee (the view update is modelled deeply;
refinement.md step 5 is an A-reference, not a consumed axiom), so there is no
axiom to delegate -- the whole region is executed directly.

ORACLE
------
The REAL patched repo function, CALLED (not transliterated):
``django.db.models.query_utils.RegisterLookupMixin._unregister_lookup``
(``django/db/models/query_utils.py:212-220`` post-patch; mapping.md section 1).
The gate applies ``patch.diff`` (the gold patch, which adds
``cls._clear_cached_lookups()`` after the ``del``) to /testbed and sets
PYTHONPATH before this script runs, so the import resolves to the patched
module and the call below IS the gold operation. Its observables are read
through the real collaborators, never re-implemented:

  * the LOCAL backing store  -> ``cls.__dict__["class_lookups"]`` (the per-class
    dict ``_unregister_lookup`` deletes from),
  * the ENCLOSING registration layer -> the real ``merge_dicts`` applied to the
    ``class_lookups`` of the target's own read-FALLBACK range (the classes its
    ``get_lookups`` merges, minus itself -- NOT unconditionally
    ``inspect.getmro(cls)[1:]``, since ``ForeignObject`` overrides ``get_lookups``
    and truncates the range; ``fallback_bases`` discovers it by probing the real
    read), merged by the SAME staticmethod ``get_lookups`` uses, in the same
    preference order), and
  * the derived view -> ``cls.get_lookups()``, the real
    ``functools.lru_cache``-memoised classmethod (``query_utils.py:155-161``)
    that ``_get_lookup`` / ``get_lookup`` / ``get_transform`` answer reads from,
    recomputed through the real ``merge_dicts`` over the real read range (the
    range ``cls.get_lookups`` itself merges, which ``fallback_bases`` probes
    rather than assuming to be ``inspect.getmro(cls)``),
  * A DEPENDENT READER'S derived view -> ``reader.get_lookups()`` for a real
    class that reads THROUGH ``cls`` (``Descendant`` on the synthetic hierarchy,
    ``models.ForeignKey`` on the ``test_lookups_caching`` shape). ``get_lookups``
    is decorated ``@functools.lru_cache`` on the classmethod, so each class in the
    hierarchy is a DISTINCT cache key holding a DISTINCT merged dict: the reader's
    memoised answers are a separate observable from ``cls``'s own, and bringing
    ``cls``'s in line says nothing about the reader's. This is why
    ``_clear_cached_lookups`` walks ``cls.__subclasses__()``
    (``query_utils.py:196-199``) instead of clearing one entry, and it is the
    observable ``test_lookups_caching`` actually reads (it registers on
    ``ForeignObject`` and asserts through a ``ForeignKey`` instance's field), and
  * what the READER'S OWN remaining levels provide -> the real ``merge_dicts``
    over ``fallback_bases(reader)`` with ``cls`` itself set aside, in the reader's
    own preference order.

Before every removal the memoised view is PRIMED by an actual read
(``get_lookups()`` on the class, its ancestors and its subclasses), so an oracle
that failed to bring the view in line would answer the post-removal read from
the out-of-date mapping and still report the removed local registration. That is
precisely the branch the gold patch changes, and it is exercised on every single
input -- see the mutation control below, which proves it. ``fallback_bases``'
probe is warmed BEFORE those priming reads (it registers and unregisters a
sentinel, which clears the caches it touches), so priming is never undone by the
bridge.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model works over abstract ``Dict[int, int]`` (name token -> identity token,
with the distinguished value ``unregistered() == 0`` standing for "absent from
the real dict", since Nagini cannot delete dict keys). The real function works
over ``dict[str, LookupClass]``. Inversion:

  name token t  <->  the lookup name ``NAME_OF[t]`` ("conf_lk_<t>"; the model's
                     ``other_name() == -1`` is bound to "conf_lk_m1");
  identity token <-> a distinct REAL ``Lookup`` subclass carrying that
                     ``lookup_name`` and an identity marker ``_conf_tok``
                     (several variants per name, so "the unrelated name still
                     resolves to the SAME lookup" has content);
  key absent in the real dict  <->  the value ``unregistered()``.

Inputs are generated on the CONCRETE side (a real ``RegisterLookupMixin``
hierarchy with real ``Lookup`` subclasses registered through the real
``register_lookup``), then abstracted; this guarantees every input is a
reachable repo state, and the model's ``Requires`` are asserted (not assumed) on
the abstracted pre-state of every input.

DOMAIN
------
Five carriers, so every registration layer a read consults is carried AT TWO
LEVELS OF THE HIERARCHY: the target's own ``class_lookups`` (``store``), what the
REST OF ITS OWN READ RANGE provides (``inherited``, computed over
``fallback_bases(cls)[1:]``), the memoised merged answer of a read THROUGH THE
TARGET (``view``), the memoised merged answer of a read through a DEPENDENT
READER (``reader_view``), and what that reader's own remaining levels provide
(``reader_rest``, computed over ``fallback_bases(reader)`` minus ``cls``). The
last two are not derivable from the first three: they are a different lru_cache
entry over a shared registration layer. The scenario space
is therefore UNRESTRICTED with respect to inherited shadowing: hierarchies where
an ancestor ALSO registers the removed name are generated in the ordinary
stream, not excluded. On those inputs the real recomputed view resurfaces the
ancestor's lookup and the model predicts exactly that (``view[name] ==
inherited[name]``). Their frequency is counted and reported in the final JSON
line (``inherited_shadowing_*``) so the coverage of that family is visible
rather than assumed. Both F2P shapes are non-shadowing ("exactly" is registered
only on ``ForeignObject``, "my_transform" only on ``JSONField``), i.e. the
special case ``inherited[name] == unregistered()``, and are run explicitly.

INPUTS (>= 1e5 satisfying the Requires)
---------------------------------------
Boundary first: the minimal store (only the removed name plus the model's
``other_name()``), a no-ancestor and a singleton-ancestor hierarchy, a subclass
present (so the real ``_clear_cached_lookups`` subclass walk runs), an ancestor
whose names are disjoint from the removed one, ancestors that DO shadow the
removed name (one level up and two levels up, and both shadowing at once so
``merge_dicts``' preference order is pinned), both call shapes of the patched
function (``_unregister_lookup(lookup)``, taking the ``lookup_name is None``
branch, and ``_unregister_lookup(None, name)``, taking the other), and the two
exact F2P shapes against real Django classes (a ``Lookup`` named "exactly" on
``models.ForeignObject``, per ``custom_lookups.tests.LookupTests.
test_lookups_caching``; a ``Transform`` named "my_transform" on
``models.JSONField``, per ``model_fields.test_jsonfield.TestMethods.
test_get_transforms``). Then the READ-RANGE family (``truncating_shapes`` /
``check_truncating``), which is the one family the synthetic hierarchy cannot
reach: every class above subclasses ``RegisterLookupMixin`` directly and so
inherits the unoverridden ``get_lookups``, whose read range is the full MRO. These
shapes are played on the real classes that OVERRIDE it -- ``ForeignObject``,
``ForeignKey``, ``OneToOneField`` (``related.py:858-864`` truncates the merge range
at ``ForeignObject``) -- with a second registration of the same name on an ancestor
ABOVE the cut (in the MRO, never consulted by a read) and INSIDE it (a genuine
resurfacing), plus ``CharField`` in the same shape as a non-truncating contrast.
Each shape records whether the REFUTED full-MRO binding of ``inherited`` would
have disagreed with the real recomputed view; if none does, the run exits 1 as a
coverage failure, because then the truncating branch was never witnessed. Then
seeded fuzz over the hierarchy shape, the registered name sets, the identity
variants and the call shape to fill the count. The impl region itself is
branch-free (two unconditional writes), so "every branch taken" is discharged by
the two oracle call shapes.

Pinned seed: 15569 (recorded in mapping.md, section "G-CONF").

MUTATION CONTROL (this check is built to be capable of failing)
--------------------------------------------------------------
On the boundary cases and a sample of the fuzz cases the same scenario is
additionally run through the PRE-PATCH removal (``del class_lookups[name]``
only, no cache clear, self-applied at runtime) and the shadow is required to
DISAGREE with it, since otherwise the observables would not witness the added
line and a green verdict would certify nothing.

There is exactly one family of inputs where NO observable can witness it, and it
is a property of the real repository rather than of the shadow: if an ancestor
registers the removed name to the very SAME lookup class object the target
registered, then "the stale view still reports the target's lookup" and "the
recomputed view reports the ancestor's lookup" name the same object, so the gold
and pre-patch post-states are literally equal. Such states are reachable (the
same ``Lookup`` subclass may legitimately be registered at two levels), so they
stay in-domain and are NOT skipped: instead, every agreement between the shadow
and the pre-patch removal must be PROVEN degenerate in that precise sense
(``inherited[name] == Old(store[name])``). An agreement that is not so
explained, or a run in which no control discriminated at all, fails the check
(exit 1) exactly like a real disagreement; the two counts are reported.

A SECOND control guards the repaired clause specifically. On the same cadence
the scenario is run through an OVER-EAGER removal that forces a read of the
removed name to report nothing regardless of what the MRO above provides
(``del class_lookups[n]; class_lookups[n] = None; _clear_cached_lookups()`` --
which under this bridge abstracts to ``view[name] = unregistered()``, the
predecessor model's claim). Whenever the scenario HAS an inherited registration
for the removed name the shadow must disagree with it; if it never did over the
whole run, the inputs would not witness the difference between "the view reports
the remaining registration levels" and "the view reports nothing", and the
repaired postcondition would be untested. That, too, exits 1.

A THIRD control guards the per-reader clause, and it is the one that closes the
hole a two-level abstraction left open. On the same cadence the scenario is run
through a COMPONENT-ONLY removal (``_component_only_removal``): the local
registration is deleted and the component's OWN memoised read is brought back in
line -- by mutating the very dict object its lru_cache entry holds, so exactly
one class's memo moves -- while every component that reads THROUGH it keeps the
answers it had. Such a removal satisfies ``store[name] == unregistered()`` and
``view[name] == inherited[name]`` and still leaves a read through a subclass
reporting the removed registration, which is exactly what
``custom_lookups.tests.LookupTests.test_lookups_caching`` catches: it registers
"exactly" on ``ForeignObject`` and asserts ``assertNotIn("exactly",
field.get_lookups())`` for a ``ForeignKey`` field. The shadow must DISAGREE with
it whenever the reader genuinely reports the component's local registration and
the reader's own remaining levels provide something else
(``reader_view[name] == store[name] != reader_rest[name]``); when the reader
registers the name itself the two post-states coincide in the real repo and
nothing could witness the difference, so those inputs carry no obligation and are
counted separately. The control is ALSO run on the exact ``test_lookups_caching``
shape (``ForeignObject`` read through ``ForeignKey``) in ``check_f2p``. A run in
which no component-only control discriminated, or in which no input ever put the
reader in the position of reporting the component's local registration, exits 1
as a coverage failure -- otherwise the two reader carriers would be decoration.

Exit 0 iff zero disagreements; on disagreement the input and both outputs are
printed and the exit status is 1. Imports: stdlib + the Django package under
evaluation.
"""
import inspect
import json
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={},
    )
    django.setup()

from django.db import models                                       # noqa: E402
from django.db.models.lookups import Lookup, Transform             # noqa: E402
from django.db.models.query_utils import RegisterLookupMixin       # noqa: E402

SEED = 15569
N_FUZZ = 100000
CONTROL_EVERY = 250            # mutation control cadence over the fuzz stream


# ---------------------------------------------------------------------------
# pure region of model.py, copied over, @Pure stripped
# ---------------------------------------------------------------------------

def unregistered():
    # The distinguished registration state meaning "this name is not registered
    # at this level" / "a read of this name does not resolve".
    return 0


def other_name():
    # A representative pre-existing, unrelated registered name.
    return -1


# ---------------------------------------------------------------------------
# the impl region of model.py, VERBATIM, contracts stripped
# ---------------------------------------------------------------------------

def remove_registration(store, view, inherited, reader_view, reader_rest, name):
    # impl-start
    store[name] = unregistered()
    view[name] = inherited[name]
    reader_view[name] = reader_rest[name]
    # impl-end


# ---------------------------------------------------------------------------
# type bridge (mapping.md section 2, inverted)
# ---------------------------------------------------------------------------

NAME_TOKENS = [other_name()] + list(range(1, 13))
VARIANTS = 3


def _name_of(t):
    return "conf_lk_m%d" % (-t,) if t < 0 else "conf_lk_%d" % (t,)


NAME_OF = {t: _name_of(t) for t in NAME_TOKENS}

# For each name token, several REAL Lookup subclasses sharing that lookup_name
# but carrying distinct identity tokens (the model's dict VALUES).
POOL = {}
for _t in NAME_TOKENS:
    POOL[_t] = []
    for _v in range(VARIANTS):
        _idt = (_t + 2) * 100 + _v + 1          # nonzero, distinct, != unregistered()
        POOL[_t].append(type(
            "ConfLookup_%s_%d" % (NAME_OF[_t], _v),
            (Lookup,),
            {"lookup_name": NAME_OF[_t], "_conf_tok": _idt},
        ))


def _tok_of(lookup_cls):
    """Concrete -> abstract for a single dict value."""
    if lookup_cls is None:
        return unregistered()                    # key absent in the real dict
    tok = getattr(lookup_cls, "_conf_tok", None)
    if tok is None:
        raise AssertionError(
            "bridge failure: %r resolves to a lookup with no identity token"
            % (lookup_cls,))
    return tok


_FALLBACK_CACHE = {}


def fallback_bases(cls):
    """The classes whose ``class_lookups`` a read of ``cls`` ACTUALLY merges, in the
    real preference order, INCLUDING ``cls`` at index 0.

    Not ``inspect.getmro(cls)[1:]``: ``get_lookups`` is overridable, and
    ``ForeignObject`` overrides it (``django/db/models/fields/related.py:858-864``
    @ base_commit) to merge only ``bases[: bases.index(ForeignObject) + 1]``. For
    ``ForeignObject`` / ``ForeignKey`` / ``OneToOneField`` an ancestor above that
    cut is in the MRO yet is NEVER consulted by a read, so a full-MRO merge would
    abstract the enclosing layer to a value the real read never falls back to --
    and the model's ``view[name] == inherited[name]`` would over-claim there.

    The range is DISCOVERED by probing the real ``get_lookups`` rather than by
    re-implementing any base-selection rule: a fresh sentinel is registered on one
    MRO class at a time through the real ``register_lookup``, and we ask whether a
    read of ``cls`` sees it. Registration + read only -- never the removal under
    test -- so the bridge is not derived from the operation it measures.
    """
    if cls in _FALLBACK_CACHE:
        return _FALLBACK_CACHE[cls]
    out = []
    for i, k in enumerate(inspect.getmro(cls)):
        if not (isinstance(k, type) and issubclass(k, RegisterLookupMixin)):
            continue
        sentinel = "__conf_probe_%d_%d" % (id(cls) % 9973, i)
        created = "class_lookups" not in k.__dict__
        k.register_lookup(type("ConfProbe_%d" % i, (Lookup,),
                               {"lookup_name": sentinel}), sentinel)
        try:
            if sentinel in cls.get_lookups():
                out.append(k)
        finally:
            k.__dict__["class_lookups"].pop(sentinel, None)
            if created and not k.__dict__["class_lookups"]:
                del k.class_lookups
            _clear_cached(k)
    _FALLBACK_CACHE[cls] = tuple(out)
    return _FALLBACK_CACHE[cls]


def abstract(cls, tokens, reader=None):
    """Concrete repo state -> the model's five carriers, over `tokens`.

    store       <- the per-class backing dict `class_lookups` (what
                   _unregister_lookup deletes from);
    view        <- the REAL memoised `get_lookups()` read of cls;
    inherited   <- what the rest of cls's OWN READ RANGE provides
                   (``fallback_bases(cls)[1:]``), merged by the REAL
                   `merge_dicts` in the same preference order `get_lookups` uses.
    reader_view <- the REAL memoised `get_lookups()` read of ANOTHER component
                   through which this registry can be read. `get_lookups` is
                   memoised PER CLASS, so this is a genuinely separate observable
                   from `view`: a removal can leave it stale while `view` is
                   correct.
    reader_rest <- what the reader's OWN read range provides with cls's backing
                   dict set aside, merged by the REAL `merge_dicts` in the
                   reader's own preference order. A reader that does not reach
                   cls at all abstracts to reader_rest == reader_view.

    `reader is None` means the reader IS cls (the two pairs coincide, which the
    model admits): used where the shape under test has no distinct dependent
    reader.
    """
    if reader is None:
        reader = cls
    own = cls.__dict__.get("class_lookups", {})
    # BOTH memoised reads are captured FIRST, before any `fallback_bases`
    # probing. The probe registers and unregisters a sentinel and therefore
    # CLEARS the lru_cache it touches; taking a read after it would recompute
    # the merge and so could launder exactly the staleness these carriers exist
    # to expose. Holding the dict objects is enough: a later `cache_clear()`
    # drops the cache's reference to them, it does not alter them.
    seen = cls.get_lookups()                     # the real read-through view
    rseen = reader.get_lookups()                 # the reader's own memoised read
    above = RegisterLookupMixin.merge_dicts(
        [parent.__dict__.get("class_lookups", {})
         for parent in fallback_bases(cls)[1:]])
    rrest = RegisterLookupMixin.merge_dicts(
        [p.__dict__.get("class_lookups", {})
         for p in fallback_bases(reader) if p is not cls])
    store = {}
    view = {}
    inherited = {}
    reader_view = {}
    reader_rest = {}
    for t in tokens:
        n = NAME_OF[t]
        store[t] = _tok_of(own.get(n))
        view[t] = _tok_of(seen.get(n))
        inherited[t] = _tok_of(above.get(n))
        reader_view[t] = _tok_of(rseen.get(n))
        reader_rest[t] = _tok_of(rrest.get(n))
    return store, view, inherited, reader_view, reader_rest


# ---------------------------------------------------------------------------
# the real hierarchy the scenarios are played on
# ---------------------------------------------------------------------------

class GrandAncestor(RegisterLookupMixin):
    pass


class Ancestor(GrandAncestor):
    pass


class Target(Ancestor):
    pass


class Descendant(Target):
    pass


LEVELS = (GrandAncestor, Ancestor, Target, Descendant)


def _clear_cached(cls):
    """The REAL cache-invalidation classmethod (named `_clear_cached_lookups` at
    this base_commit, `_clear_cached_class_lookups` in later releases)."""
    for attr in ("_clear_cached_lookups", "_clear_cached_class_lookups"):
        fn = getattr(cls, attr, None)
        if fn is not None:
            fn()
            return
    raise AssertionError("no cache-invalidation classmethod on RegisterLookupMixin")


def setup(scn):
    """Build the concrete pre-state with the REAL register_lookup, then PRIME the
    memoised view with real reads (so a missing update stays observable)."""
    for cls in LEVELS:
        cls.class_lookups = {}
    _clear_cached(GrandAncestor)
    for cls, regs in zip(LEVELS, scn["regs"]):
        for t, v in regs:
            cls.register_lookup(POOL[t][v], NAME_OF[t])
    # prior reads memoise the view at every level of the hierarchy
    for cls in LEVELS:
        cls.get_lookups()


def run_oracle(scn):
    """Call the REAL patched _unregister_lookup and abstract the observables."""
    t = scn["name_tok"]
    setup(scn)
    pre = abstract(Target, NAME_TOKENS, Descendant)
    if scn["by_lookup"]:
        # lookup_name is None -> derived from lookup.lookup_name (patched branch A)
        Target._unregister_lookup(POOL[t][scn["name_var"]])
    else:
        # explicit lookup_name (patched branch B)
        Target._unregister_lookup(None, NAME_OF[t])
    post = abstract(Target, NAME_TOKENS, Descendant)
    return pre, post


def run_prepatch(scn):
    """The base_commit removal, self-applied: delete only, no cache clear.
    Used as the mutation control -- the shadow MUST disagree with this."""
    setup(scn)
    del Target.class_lookups[NAME_OF[scn["name_tok"]]]
    return abstract(Target, NAME_TOKENS, Descendant)


def run_overeager(scn):
    """The OVER-EAGER removal: force a read of the removed name to report
    nothing, whatever the rest of its read range provides. Abstracts to the
    predecessor
    model's `view[name] = unregistered()`. The shadow must disagree with it
    whenever the scenario has an inherited registration for the removed name."""
    setup(scn)
    n = NAME_OF[scn["name_tok"]]
    del Target.class_lookups[n]
    Target.class_lookups[n] = None
    _clear_cached(Target)
    return abstract(Target, NAME_TOKENS, Descendant)


def run_component_only(scn):
    """The COMPONENT-ONLY removal: delete the local registration and bring the
    component's OWN memoised read back in line, WITHOUT the invalidation
    reaching the other components that read through it.

    Expressed against the real repo by recomputing what a read of Target should
    now report and patching Target's own memoised dict in place. `get_lookups` is
    memoised per class, so every dependent reader (Descendant here) keeps the
    answers it had -- which is precisely the residual defect. The shadow must
    disagree with this, or the per-reader observable is not witnessed.
    """
    setup(scn)
    _component_only_removal(Target, NAME_OF[scn["name_tok"]])
    return abstract(Target, NAME_TOKENS, Descendant)


def _component_only_removal(owner, n):
    """Delete `owner`'s local registration of `n` and bring ONLY `owner`'s own
    memoised read back in line, leaving every component that reads THROUGH owner
    with the answers it had.

    Uses the real internals: `class_lookups`, the real `merge_dicts` over
    `owner`'s own probed read range, and the fact that `get_lookups` hands back
    the very dict object the lru_cache holds -- mutating it in place updates
    exactly one class's memo. That is what makes this a genuine
    per-class-invalidation mutant of the gold behaviour rather than a
    re-implementation of it.
    """
    del owner.__dict__["class_lookups"][n]
    own_memo = owner.get_lookups()               # the memoised dict object
    correct = RegisterLookupMixin.merge_dicts(
        [p.__dict__.get("class_lookups", {}) for p in fallback_bases(owner)])
    if n in correct:
        own_memo[n] = correct[n]
    else:
        own_memo.pop(n, None)


def run_shadow(pre, scn):
    store, view, inherited = dict(pre[0]), dict(pre[1]), dict(pre[2])
    reader_view, reader_rest = dict(pre[3]), dict(pre[4])
    remove_registration(store, view, inherited, reader_view, reader_rest,
                        scn["name_tok"])
    return store, view, inherited, reader_view, reader_rest


def check_requires(pre, scn):
    """The model's Requires, asserted (never assumed) on the abstracted pre-state."""
    store, view, inherited, reader_view, reader_rest = pre
    name = scn["name_tok"]
    assert name in store and name in view and name in inherited, \
        "Requires: name in store/view/inherited"
    assert name in reader_view and name in reader_rest, \
        "Requires: name in reader_view/reader_rest"
    assert other_name() in store and other_name() in view, \
        "Requires: other_name present"
    assert other_name() in reader_view, "Requires: other_name in reader_view"
    assert other_name() != name, "Requires: other_name() != name"
    assert store[name] != unregistered(), "Requires: name registered in the store"
    assert view[name] != unregistered(), "Requires: name resolves in the view"
    # the READ-THROUGH LAWS, on every abstracted name at once
    for k in store:
        if store[k] != unregistered():
            assert view[k] == store[k], "Requires: read-through (local) at %r" % (k,)
        elif k in inherited:
            assert view[k] == inherited[k], \
                "Requires: read-through (fallback) at %r" % (k,)
        # the PER-READER law: what a reader reports is either the component's
        # local registration (it reaches the component and that registration
        # wins its merge) or what its own remaining levels provide.
        assert reader_view[k] == store[k] or reader_view[k] == reader_rest[k], \
            ("Requires: per-reader read-through at %r (reader_view=%r, store=%r, "
             "reader_rest=%r)" % (k, reader_view[k], store[k], reader_rest[k]))


def diff(scn, shadow, oracle):
    """Compare the WRITTEN carriers (store, view, reader_view). `inherited` and
    `reader_rest` are read-only for the operation, so they are compared too as
    frame checks: the real removal must not have altered what the rest of any
    reader's read range provides."""
    if shadow == oracle:
        return None
    sst, svw, sih, srv, srr = shadow
    ost, ovw, oih, orv, orr = oracle
    bad = [t for t in NAME_TOKENS
           if sst[t] != ost[t] or svw[t] != ovw[t] or sih[t] != oih[t]
           or srv[t] != orv[t] or srr[t] != orr[t]]
    return ("DISAGREEMENT: shadow (model.py impl region) != real patched "
            "_unregister_lookup\n  scenario = %r\n  removed name = %r (token %d)\n"
            "  differing name tokens = %r\n"
            "  shadow store = %r\n  oracle store = %r\n"
            "  shadow view  = %r\n  oracle view  = %r\n"
            "  shadow inherited = %r\n  oracle inherited = %r\n"
            "  shadow reader_view = %r\n  oracle reader_view = %r\n"
            "  shadow reader_rest = %r\n  oracle reader_rest = %r"
            % (scn, NAME_OF[scn["name_tok"]], scn["name_tok"], bad,
               {t: sst[t] for t in bad}, {t: ost[t] for t in bad},
               {t: svw[t] for t in bad}, {t: ovw[t] for t in bad},
               {t: sih[t] for t in bad}, {t: oih[t] for t in bad},
               {t: srv[t] for t in bad}, {t: orv[t] for t in bad},
               {t: srr[t] for t in bad}, {t: orr[t] for t in bad}))


# ---------------------------------------------------------------------------
# scenario generation
# ---------------------------------------------------------------------------

def scenario(name_tok, name_var, grand, ancestor, target, descendant, by_lookup):
    return {"name_tok": name_tok, "name_var": name_var,
            "regs": [list(grand), list(ancestor), list(target), list(descendant)],
            "by_lookup": by_lookup}


def boundary_scenarios():
    o = other_name()
    out = []
    # minimal store: only the removed name and the model's other_name(); no
    # ancestor and no descendant registrations at all.
    out.append(scenario(1, 0, [], [], [(1, 0), (o, 0)], [], False))
    out.append(scenario(1, 0, [], [], [(1, 0), (o, 0)], [], True))
    # other_name() is the only companion but bound to a different identity
    out.append(scenario(2, 2, [], [], [(2, 1), (o, 2)], [], True))
    # singleton ancestor, disjoint name
    out.append(scenario(3, 0, [], [(4, 0)], [(3, 0), (o, 1)], [], False))
    # ancestor also registers other_name() (child shadows it: view keeps child's)
    out.append(scenario(3, 1, [], [(o, 0), (5, 0)], [(3, 1), (o, 2)], [], True))
    # descendant present -> the real _clear_cached_lookups subclass walk runs
    out.append(scenario(6, 0, [], [], [(6, 0), (o, 0)], [(7, 0)], False))
    out.append(scenario(6, 1, [], [(8, 1)], [(6, 1), (o, 1)], [(6, 2), (9, 0)], True))
    # many companions in the store, removed name in the middle
    mid = [(t, t % VARIANTS) for t in range(1, 13)] + [(o, 0)]
    out.append(scenario(5, 5 % VARIANTS, [], [], mid, [], False))
    out.append(scenario(12, 0, [], [(1, 1), (2, 2)], mid, [(3, 0)], True))
    # removed name is the only one the view resolves besides other_name()
    out.append(scenario(11, 2, [], [], [(11, 2), (o, 1)], [], False))
    # --- INHERITED SHADOWING of the removed name (the family the two-carrier
    # --- predecessor could not carry): the parent, the grandparent, and both.
    out.append(scenario(1, 0, [], [(1, 1)], [(1, 0), (o, 0)], [], False))
    out.append(scenario(2, 2, [], [(2, 0), (3, 0)], [(2, 2), (o, 1)], [], True))
    out.append(scenario(4, 1, [(4, 2)], [], [(4, 1), (o, 2)], [(5, 0)], False))
    # both levels register it -> merge_dicts' preference order decides which
    # lookup a read resurfaces; the shadow must predict the same one.
    out.append(scenario(7, 0, [(7, 2)], [(7, 1)], [(7, 0), (o, 0)], [], True))
    out.append(scenario(8, 1, [(8, 0)], [(8, 2)], [(8, 1), (o, 1)], [(8, 0)], False))
    return out


def fuzz_scenario(rng):
    name_tok = rng.choice([t for t in NAME_TOKENS if t != other_name()])
    name_var = rng.randrange(VARIANTS)
    # Ancestors and descendants are UNRESTRICTED: they may register the removed
    # name (inherited shadowing) as well as other_name() or each other, so the
    # real merge_dicts and the _clear_cached_lookups subclass walk are fully
    # exercised and the third carrier is genuinely varied.
    regs = []
    for _ in range(4):
        k = rng.randrange(0, min(6, len(NAME_TOKENS)))
        regs.append([(t, rng.randrange(VARIANTS))
                     for t in rng.sample(NAME_TOKENS, k)])
    # Requires: the removed name and other_name() are registered on the target
    regs[2] = [r for r in regs[2] if r[0] != name_tok and r[0] != other_name()]
    regs[2].append((name_tok, name_var))
    regs[2].append((other_name(), rng.randrange(VARIANTS)))
    rng.shuffle(regs[2])
    return scenario(name_tok, name_var, regs[0], regs[1], regs[2], regs[3],
                    rng.random() < 0.5)


# ---------------------------------------------------------------------------
# the exact F2P shapes, against real Django field classes
# ---------------------------------------------------------------------------

def f2p_shapes():
    """(label, owner, lookup class, call-by-lookup?, reader) for the two F2P
    tests. `reader` is the component the test reads through (None => the owner
    itself)."""
    exactly = type("ConfExactly", (Lookup,),
                   {"lookup_name": "exactly", "_conf_tok": 424242})
    my_transform = type("ConfMyTransform", (Transform,),
                        {"lookup_name": "my_transform", "_conf_tok": 515151})
    return [
        # custom_lookups.tests.LookupTests.test_lookups_caching
        # the reader is the class the test actually READS THROUGH: this test
        # registers on ForeignObject and asserts through a ForeignKey, so the
        # dependent reader's own memoised view is the observable that bites.
        ("test_lookups_caching", models.ForeignObject, exactly, False,
         models.ForeignKey),
        # model_fields.test_jsonfield.TestMethods.test_get_transforms
        ("test_get_transforms", models.JSONField, my_transform, True, None),
    ]


def check_f2p():
    """Same shadow / same oracle, on the real classes the F2P tests touch.
    Token universe = the single real lookup name; identity token = _conf_tok."""
    errors = []
    checked = 0
    comp_controls = 0
    comp_discriminating = 0

    def _prime(owner, lk, name, reader):
        owner.register_lookup(lk, name)
        _ = owner.get_lookups()                  # prime the memoised view
        if reader is not None:
            _ = reader.get_lookups()             # prime the READER's memo too
        pre = abstract(owner, [0], reader)
        shadow = (dict(pre[0]), dict(pre[1]), dict(pre[2]),
                  dict(pre[3]), dict(pre[4]))
        remove_registration(shadow[0], shadow[1], shadow[2],
                            shadow[3], shadow[4], 0)
        return pre, shadow

    for label, owner, lk, by_lookup, reader in f2p_shapes():
        name = lk.lookup_name
        assert name not in owner.get_lookups(), (
            "F2P setup: %r already resolves on %s" % (name, owner.__name__))
        NAME_OF[0] = name                        # transient bridge for token 0
        try:
            pre, shadow = _prime(owner, lk, name, reader)
            assert pre[0][0] != unregistered() and pre[1][0] != unregistered(), \
                "F2P setup: Requires not met"
            if by_lookup:
                owner._unregister_lookup(lk)     # REAL patched function
            else:
                owner._unregister_lookup(None, name)
            post = abstract(owner, [0], reader)
            checked += 1
            if shadow != post:
                errors.append(
                    "DISAGREEMENT on F2P shape %s (%s.%s):\n"
                    "  shadow = %r\n  oracle = %r"
                    % (label, owner.__name__, name, shadow, post))
        finally:
            own = owner.__dict__.get("class_lookups", {})
            own.pop(name, None)
            _clear_cached(owner)
            if reader is not None:
                _clear_cached(reader)
        # COMPONENT-ONLY control on the SAME shape. `test_lookups_caching`
        # registers on ForeignObject and asserts through ForeignKey, so on that
        # shape a removal that brings only ForeignObject's own memoised read back
        # in line still leaves the test's own read reporting the removed lookup.
        # The shadow must disagree with it, or the reader carriers are decoration
        # on the very shape the F2P test measures.
        try:
            if reader is not None:
                NAME_OF[0] = name
                pre2, shadow2 = _prime(owner, lk, name, reader)
                _component_only_removal(owner, name)
                comp = abstract(owner, [0], reader)
                comp_controls += 1
                if shadow2 != comp:
                    comp_discriminating += 1
                else:
                    errors.append(
                        "NON-DISCRIMINATING COMPONENT-ONLY CONTROL on F2P shape "
                        "%s (%s.%s, read through %s): the shadow agrees with a "
                        "removal that leaves the reader's memoised answers "
                        "stale.\n  shadow = %r\n  component-only = %r"
                        % (label, owner.__name__, name, reader.__name__,
                           shadow2, comp))
        finally:
            owner.__dict__.get("class_lookups", {}).pop(name, None)
            _clear_cached(owner)
            if reader is not None:
                _clear_cached(reader)
            NAME_OF.pop(0, None)
    return checked, comp_controls, comp_discriminating, errors


# ---------------------------------------------------------------------------
# the READ-RANGE boundary family, against the real classes that OVERRIDE
# get_lookups (so the truncating branch of `fallback_bases` is reachable)
# ---------------------------------------------------------------------------

def truncating_shapes():
    """(label, owner, ancestor, ancestor_is_consulted) for the read-range family.

    Every class in the synthetic hierarchy above subclasses ``RegisterLookupMixin``
    DIRECTLY, so it inherits the unoverridden ``get_lookups`` and its read range is
    always the full MRO: the truncating branch is unreachable there, and a bridge
    that merged ``inspect.getmro(cls)[1:]`` unconditionally would be right by
    construction on every one of those inputs. These shapes make the branch
    reachable on the REAL classes that override the method -- ``ForeignObject`` and
    its subclasses, whose override (``django/db/models/fields/related.py:858-864``
    @ base_commit) merges only ``bases[: bases.index(ForeignObject) + 1]``:

      * an ancestor ABOVE the cut: in ``inspect.getmro(owner)[1:]`` yet never
        consulted by a read, so the removal makes the name stop resolving even
        though an ancestor still registers it;
      * an ancestor INSIDE the cut: a genuine resurfacing on the same family;
      * a NON-truncating real class in the same shape as the first rows, where the
        ancestor above IS consulted -- so a harness that got the range wrong
        cannot agree with the oracle on both groups.
    """
    return [
        ("fo-ancestor-above-cut", models.ForeignObject, models.Field, False),
        ("fk-ancestor-above-cut", models.ForeignKey, models.Field, False),
        ("fk-ancestor-inside-cut", models.ForeignKey, models.ForeignObject, True),
        ("o2o-ancestor-inside-cut", models.OneToOneField, models.ForeignKey, True),
        ("charfield-ancestor-consulted", models.CharField, models.Field, True),
    ]


def _read_range_levels(owner):
    return [k for k in inspect.getmro(owner)
            if isinstance(k, type) and issubclass(k, RegisterLookupMixin)]


def _trunc_state(owner, ancestor, name, lk_own, lk_anc):
    """Build the concrete pre-state for one read-range shape with the REAL
    ``register_lookup`` and PRIME the memoised view at every level of the real
    MRO, then abstract it. The ``fallback_bases`` probe is warmed BEFORE the
    priming reads, because probing registers and unregisters a sentinel and so
    clears the caches it touches -- priming afterwards is what keeps a removal
    that fails to invalidate the view observable."""
    for k in (ancestor, owner):
        k.__dict__.get("class_lookups", {}).pop(name, None)
    _clear_cached(ancestor)
    ancestor.register_lookup(lk_anc, name)
    owner.register_lookup(lk_own, name)
    fallback_bases(owner)
    for k in _read_range_levels(owner):
        k.get_lookups()
    return abstract(owner, [0], _rr_reader(owner))


def _rr_reader(owner):
    """A REAL component that reads through `owner`, for the read-range shapes:
    the first Django field subclass of owner in the same family, or None when
    the shape has no distinct dependent reader."""
    for cand in (models.ForeignKey, models.OneToOneField, models.TextField,
                 models.BigIntegerField):
        if cand is not owner and issubclass(cand, owner):
            return cand
    return None


def check_truncating():
    """Same shadow / same called oracle, on the read-range family. Also records
    two controls per shape: whether the REFUTED full-MRO binding of `inherited`
    would have disagreed with the oracle (coverage of the truncating branch), and
    whether the base_commit delete-without-cache-clear disagrees with the shadow
    (that these shapes witness the added line at all)."""
    errors = []
    checked = 0
    resurfacing = 0
    old_binding_refuted = 0
    controls = 0
    controls_discriminating = 0
    for label, owner, ancestor, consulted in truncating_shapes():
        name = "conf_rr_%s" % label.replace("-", "_")
        lk_own = type("ConfRROwn_%s" % name, (Lookup,),
                      {"lookup_name": name, "_conf_tok": 717171})
        lk_anc = type("ConfRRAnc_%s" % name, (Lookup,),
                      {"lookup_name": name, "_conf_tok": 818181})
        assert name not in owner.get_lookups(), (
            "read-range setup: %r already resolves on %s" % (name, owner.__name__))
        NAME_OF[0] = name                        # transient bridge for token 0
        try:
            pre = _trunc_state(owner, ancestor, name, lk_own, lk_anc)
            assert pre[0][0] != unregistered() and pre[1][0] != unregistered(), \
                "read-range setup: Requires not met on %s" % label
            if pre[2][0] != unregistered():
                resurfacing += 1
            # what the REFUTED binding (merge over the full inspect.getmro tail)
            # would have called `inherited[name]` on this very state:
            old_inh = _tok_of(RegisterLookupMixin.merge_dicts(
                [p.__dict__.get("class_lookups", {})
                 for p in _read_range_levels(owner)[1:]]).get(name))
            shadow = (dict(pre[0]), dict(pre[1]), dict(pre[2]),
                      dict(pre[3]), dict(pre[4]))
            remove_registration(shadow[0], shadow[1], shadow[2],
                                shadow[3], shadow[4], 0)
            owner._unregister_lookup(None, name)          # REAL patched function
            post = abstract(owner, [0], _rr_reader(owner))
            checked += 1
            if shadow != post:
                errors.append(
                    "DISAGREEMENT on read-range shape %s (owner %s, ancestor %s):\n"
                    "  shadow = %r\n  oracle = %r"
                    % (label, owner.__name__, ancestor.__name__, shadow, post))
            if (post[1][0] != unregistered()) != consulted:
                errors.append(
                    "READ-RANGE EXPECTATION BROKEN on %s (owner %s, ancestor %s): "
                    "the ancestor was expected to be %s by a read of the owner, "
                    "but the recomputed view reports %r"
                    % (label, owner.__name__, ancestor.__name__,
                       "consulted" if consulted else "outside the read range",
                       post[1][0]))
            if old_inh != post[1][0]:
                old_binding_refuted += 1
            # mutation control on this shape: the base_commit removal (delete
            # only, no cache clear) must not look like the shadow.
            _trunc_state(owner, ancestor, name, lk_own, lk_anc)
            del owner.class_lookups[name]
            buggy = abstract(owner, [0], _rr_reader(owner))
            controls += 1
            if shadow != buggy:
                controls_discriminating += 1
        finally:
            for k in (ancestor, owner):
                k.__dict__.get("class_lookups", {}).pop(name, None)
                _clear_cached(k)
            rdr = _rr_reader(owner)
            if rdr is not None:
                _clear_cached(rdr)
            NAME_OF.pop(0, None)
    return (checked, resurfacing, old_binding_refuted, controls,
            controls_discriminating, errors)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def main():
    checked = 0
    controls = 0
    controls_discriminating = 0
    controls_degenerate = 0
    non_discriminating = []
    non_discriminating_comp = []
    shadowing = 0
    overeager_controls = 0
    overeager_discriminating = 0
    comp_controls = 0
    comp_discriminating = 0
    reader_sees_local = 0
    errors = []

    def controls_for(scn, pre, shadow):
        """The three mutation controls for one scenario.

        Control 1 -- the shadow vs the PRE-PATCH removal. It must differ, UNLESS
        the state is the degenerate one in which an ancestor registers the
        removed name to the very same lookup object the target did
        (inherited[name] == Old(store[name])), where the real repository itself
        produces identical gold and pre-patch post-states and no observable
        could witness the added line. Agreement that is not explained that way is
        recorded as a control failure.

        Control 2 -- the shadow vs an OVER-EAGER removal that ignores the
        enclosing layer. Only has content when the scenario carries an inherited
        registration for the removed name.

        Control 3 -- the shadow vs the COMPONENT-ONLY removal: the local
        registration goes and the component's OWN memoised read is brought back
        in line, but the invalidation never reaches the components that read
        THROUGH it. This is the residual defect a two-carrier abstraction cannot
        see, and it is the shape the F2P test actually catches (it registers on
        ForeignObject and asserts through ForeignKey). It has content exactly when
        the reader's own remaining levels provide something OTHER than the local
        registration the reader currently reports (reader_view[name] ==
        store[name] != reader_rest[name]); when the reader registers the name
        itself the two post-states coincide in the real repo and nothing could
        witness the difference.
        """
        nonlocal controls, controls_discriminating, controls_degenerate
        nonlocal overeager_controls, overeager_discriminating
        nonlocal comp_controls, comp_discriminating, reader_sees_local
        name = scn["name_tok"]
        buggy = run_prepatch(scn)
        controls += 1
        if shadow != buggy:
            controls_discriminating += 1
        elif pre[2][name] == pre[0][name]:
            # degenerate by the repo's own semantics, not by the shadow's choice
            controls_degenerate += 1
        else:
            non_discriminating.append(scn)
        if pre[2][name] != unregistered():
            over = run_overeager(scn)
            overeager_controls += 1
            if shadow != over:
                overeager_discriminating += 1
        if pre[3][name] == pre[0][name] and pre[4][name] != pre[0][name]:
            reader_sees_local += 1
            comp = run_component_only(scn)
            comp_controls += 1
            if shadow != comp:
                comp_discriminating += 1
            else:
                non_discriminating_comp.append(scn)
        return None

    # --- boundary cases -----------------------------------------------------
    boundary = boundary_scenarios()
    for scn in boundary:
        pre, post = run_oracle(scn)
        check_requires(pre, scn)
        shadow = run_shadow(pre, scn)
        checked += 1
        if pre[2][scn["name_tok"]] != unregistered():
            shadowing += 1
        err = diff(scn, shadow, post)
        if err:
            errors.append(err)
            break
        controls_for(scn, pre, shadow)

    # --- the exact F2P shapes on real Django classes ------------------------
    if not errors:
        n_f2p, f2p_comp, f2p_comp_disc, f2p_errors = check_f2p()
        checked += n_f2p
        comp_controls += f2p_comp
        comp_discriminating += f2p_comp_disc
        errors.extend(f2p_errors)

    # --- the read-range family on the real overriding classes ---------------
    if not errors:
        (n_rr, rr_resurfacing, rr_old_refuted, rr_controls, rr_discriminating,
         rr_errors) = check_truncating()
        checked += n_rr
        shadowing += rr_resurfacing
        controls += rr_controls
        controls_discriminating += rr_discriminating
        errors.extend(rr_errors)

    # --- seeded fuzz --------------------------------------------------------
    rng = random.Random(SEED)
    if not errors:
        for i in range(N_FUZZ):
            scn = fuzz_scenario(rng)
            pre, post = run_oracle(scn)
            check_requires(pre, scn)
            shadow = run_shadow(pre, scn)
            checked += 1
            if pre[2][scn["name_tok"]] != unregistered():
                shadowing += 1
            err = diff(scn, shadow, post)
            if err:
                errors.append(err)
                break
            if i % CONTROL_EVERY == 0:
                controls_for(scn, pre, shadow)

    if errors:
        for e in errors[:5]:
            print(e)
        print("G-CONF FAIL: %d disagreement(s) between the model.py impl region "
              "and the real patched RegisterLookupMixin._unregister_lookup over "
              "%d inputs (seed=%d)." % (len(errors), checked, SEED))
        return 1

    if non_discriminating:
        print("NON-DISCRIMINATING CONTROL: the shadow agrees with the PRE-PATCH "
              "removal (del only, no cache clear) on %d scenario(s) that are NOT "
              "degenerate (the enclosing layer provides a different lookup than "
              "the target had, so the gold and pre-patch post-states do differ in "
              "the real repo), e.g. %r -- the observables do not witness the "
              "added _clear_cached_lookups() call there."
              % (len(non_discriminating), non_discriminating[0]))
        print("G-CONF FAIL: mutation control did not discriminate over %d "
              "controls (seed=%d)." % (controls, SEED))
        return 1

    if not controls_discriminating:
        print("NON-DISCRIMINATING CONTROL: not one of the %d controls "
              "distinguished the shadow from the PRE-PATCH removal (del only, no "
              "cache clear), so the observables never witnessed the added "
              "_clear_cached_lookups() call and a green verdict would certify "
              "nothing." % controls)
        print("G-CONF FAIL: mutation control did not discriminate (seed=%d)." % SEED)
        return 1

    if not shadowing:
        print("COVERAGE FAIL: not one input had an inherited registration for the "
              "removed name, so the postcondition view[name] == inherited[name] was "
              "only ever exercised in its inherited[name] == unregistered() special "
              "case and the clause is untested where it bites.")
        return 1

    if not rr_old_refuted:
        print("COVERAGE FAIL: on none of the %d read-range shapes would the "
              "REFUTED full-MRO binding of `inherited` have disagreed with the "
              "real recomputed view, so the truncating get_lookups override "
              "(related.py:858-864) was never actually witnessed and a green "
              "verdict says nothing about that family." % n_rr)
        return 1

    if rr_controls and not rr_discriminating:
        print("NON-DISCRIMINATING CONTROL (read-range): on all %d read-range "
              "shapes the shadow agreed with the base_commit "
              "delete-without-cache-clear, so those inputs do not witness the "
              "added _clear_cached_lookups() call." % rr_controls)
        return 1

    if overeager_controls and not overeager_discriminating:
        print("NON-DISCRIMINATING CONTROL (over-eager): on all %d scenario(s) with "
              "an inherited registration for the removed name, the shadow agreed "
              "with a removal that forces a read to report NOTHING regardless of "
              "the enclosing registration layer -- so the observables do not "
              "witness the difference between 'the view reports the remaining "
              "registration levels' and 'the view reports nothing'."
              % overeager_controls)
        print("G-CONF FAIL: over-eager mutation control did not discriminate "
              "(seed=%d)." % SEED)
        return 1

    if non_discriminating_comp:
        print("NON-DISCRIMINATING CONTROL (component-only): the shadow agrees "
              "with a removal that brings only the COMPONENT'S OWN memoised read "
              "back in line on %d scenario(s) where the dependent reader does "
              "report the component's local registration and its own remaining "
              "levels provide something else, e.g. %r -- the per-reader "
              "observable is not witnessing the subclass half of the "
              "invalidation." % (len(non_discriminating_comp),
                                 non_discriminating_comp[0]))
        print("G-CONF FAIL: component-only mutation control did not discriminate "
              "(seed=%d)." % SEED)
        return 1

    if not reader_sees_local:
        print("COVERAGE FAIL: not one input had the dependent reader reporting "
              "the component's own local registration for the removed name while "
              "the reader's remaining levels provide something else, so the "
              "per-reader clause reader_view[name] == reader_rest[name] was never "
              "exercised where it adds anything over view[name] == "
              "inherited[name].")
        return 1

    if not comp_discriminating:
        print("NON-DISCRIMINATING CONTROL (component-only): none of the %d "
              "component-only controls distinguished the shadow from a removal "
              "that leaves every dependent reader's memoised answers stale, so "
              "the reader carriers observe nothing and a green verdict would not "
              "cover the F2P shape (register on ForeignObject, assert through "
              "ForeignKey)." % comp_controls)
        print("G-CONF FAIL: component-only mutation control did not discriminate "
              "(seed=%d)." % SEED)
        return 1

    print("G-CONF OK: the contract-stripped impl region of model.py "
          "(store[name]=unregistered(); view[name]=inherited[name]; "
          "reader_view[name]=reader_rest[name]) agrees with "
          "the REAL patched RegisterLookupMixin._unregister_lookup (called, "
          "observed via class_lookups, the real merge_dicts over the target's own "
          "probed read range, and the lru_cache-memoised get_lookups() of BOTH the "
          "target and a dependent reader, each primed by a "
          "prior read) on %d Requires-satisfying inputs "
          "(%d boundary + 2 F2P shapes + %d read-range shapes on the real "
          "classes that OVERRIDE get_lookups (%d of them refuting the full-MRO "
          "binding) + %d fuzz, seed=%d), 0 disagreements; "
          "%d of those inputs had an ancestor registering the removed name; "
          "of %d mutation controls %d distinguished the pre-patch "
          "delete-without-cache-clear and the remaining %d were proven degenerate "
          "(an ancestor registers the removed name to the SAME lookup object, so "
          "the real repo's gold and pre-patch post-states coincide); %d/%d "
          "over-eager controls distinguished a removal that ignores the enclosing "
          "layer; and %d/%d COMPONENT-ONLY controls distinguished a removal that "
          "brings only the component's own memoised read back in line and leaves "
          "every dependent reader stale (%d inputs had the reader reporting the "
          "component's local registration with its own remaining levels providing "
          "something else, which is where the per-reader clause adds strength)."
          % (checked, len(boundary), n_rr, rr_old_refuted, N_FUZZ, SEED,
             shadowing, controls,
             controls_discriminating, controls_degenerate,
             overeager_discriminating, overeager_controls,
             comp_discriminating, comp_controls, reader_sees_local))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": "called: RegisterLookupMixin._unregister_lookup "
                  "(django/db/models/query_utils.py, gold-patched)",
        "boundary": len(boundary),
        "f2p_shapes": 2,
        "read_range_shapes": n_rr,
        "read_range_shapes_refuting_full_mro_binding": rr_old_refuted,
        "read_range_prepatch_controls": rr_controls,
        "read_range_prepatch_discriminating": rr_discriminating,
        "fuzz": N_FUZZ,
        "mutation_controls": controls,
        "mutation_controls_discriminating": controls_discriminating,
        "mutation_controls_degenerate_same_lookup_object": controls_degenerate,
        "inherited_shadowing_inputs": shadowing,
        "inherited_shadowing_overeager_controls": overeager_controls,
        "inherited_shadowing_overeager_discriminating": overeager_discriminating,
        "reader_sees_local_registration_inputs": reader_sees_local,
        "component_only_controls": comp_controls,
        "component_only_discriminating": comp_discriminating,
        "f2p_component_only_controls": f2p_comp,
        "f2p_component_only_discriminating": f2p_comp_disc,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
