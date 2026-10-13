#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15569.

This bundle has NO consumed axioms: keeping the backing store and the derived
resolved view consistent is modelled DEEPLY (the store deletion and the
view invalidation spelled out in model.py's impl region). G-AX therefore
validates the single **A-reference** -- that the deep model equals the real
operation it mirrors -- by executing the REAL repository code
(`django.db.models.query_utils.RegisterLookupMixin`: `register_lookup`,
`_unregister_lookup`, the lru_cache-memoised `get_lookups`) in the evaluation
container and asserting the observable lookup-resolution matches the deep model.

Deep model under check (model.py impl region), over the local backing store
`store` (the target class's own `class_lookups`), the enclosing registration
layer `inherited` (what the classes ABOVE the target provide), the derived view
`view` (what a read through the target -- `target.get_lookups()` -- reports), and
the same pair one level out for a DEPENDENT READER: `reader_view` (what a read
through a subclass reports) and `reader_rest` (what that reader's own remaining
levels provide once the target's store is set aside):

    store[name]       = unregistered()      # drop the name's local registration
    view[name]        = inherited[name]     # the target's own read falls back
    reader_view[name] = reader_rest[name]   # and so does EVERY reader's

The last line is not a restatement of the second. `get_lookups` is decorated
`@functools.lru_cache` on the classmethod (`query_utils.py:157-163` @
base_commit), so each class in the hierarchy is a DISTINCT cache key holding a
DISTINCT merged dict: a subclass's memoised answers are a separate observable
from the target's, and bringing the target's in line says nothing about them.
That is exactly why the gold `_clear_cached_lookups` walks `cls.__subclasses__()`
(`query_utils.py:196-199`) rather than dropping one entry, and it is the
observable `custom_lookups.tests.LookupTests.test_lookups_caching` reads -- it
registers "exactly" on `ForeignObject` and asserts `assertNotIn("exactly",
field.get_lookups())` through a `ForeignKey` field. The third PATCH-STATE below
(COMPONENT-ONLY) is what gives that line observable content here.

Mapping to the real operation (mapping.md §1, §3):
  * `store[name] != unregistered()`  <->  `name in cls.__dict__["class_lookups"]`
    (the target's OWN backing store still registers the name -- this is the dict
    `_unregister_lookup` deletes from).
  * `view[name]  != unregistered()`  <->  `name in field.get_lookups()`
    (a read currently resolves the name; `get_lookups` is the memoised view).
  * `inherited[name]`  <->  what `merge_dicts` over the target's own read-fallback
    range (its `get_lookups` merge range minus itself) provides for `name` --
    `unregistered()` when nothing in that range registers it.
  * removal sets `store[name]` to `unregistered()` and `view[name]` to
    `inherited[name]`  <->  `del class_lookups[name]` followed by
    `_clear_cached_lookups()`, so the next `get_lookups()` recomputes the merge
    over the class's OWN read range (probed by `fallback_bases`, not assumed to
    be `inspect.getmro`): the name stops resolving when nothing in that range
    registers it, and resolves to that level's lookup when something does.
  * the frame clause `view[other] == Old(view[other])`  <->  a name OTHER than
    the removed one still resolves to the SAME lookup after the removal (the
    cache clear + lazy recompute does not change what other names resolve to).

HIERARCHY COVERAGE. Because the derived view is the merge over the class's own
`get_lookups` range, the removal's effect on a read depends on whether a class in
that FALLBACK RANGE also registers the removed name. (The range is not always the
whole MRO: `ForeignObject` overrides `get_lookups` and truncates it, so an ancestor
above the cut is invisible to a read -- `fallback_bases` discovers the real range
by probing rather than assuming `inspect.getmro(cls)[1:]`.) A check played only on a single flat class can never observe that
-- it silently pins the special case `inherited[name] == unregistered()` and
would accept an A-reference claiming the read reports nothing unconditionally.
So every sequence below is run on a real four-level `RegisterLookupMixin`
hierarchy, in both families:
  * NON-SHADOWING -- no ancestor registers the removed name, so
    `inherited[name] == unregistered()` and the read must stop resolving;
  * SHADOWING -- the parent and/or the grandparent registers the removed name
    under a DIFFERENT lookup class, so `inherited[name] != unregistered()` and
    the read must resurface exactly the lookup `merge_dicts` prefers.
Both families are counted and the counts are printed; a run in which the
shadowing family never occurred fails, since the interesting half of the
A-reference would be untested.

A synthetic hierarchy cannot reach the TRUNCATING branch, though: every level of
it subclasses `RegisterLookupMixin` directly and so inherits the unoverridden
`get_lookups`, whose range is the whole MRO. So a third family
(`read_range_shapes` / `check_fixed_read_range`) plays the same sequence on the
REAL classes that override the method -- `ForeignObject`, `ForeignKey`,
`OneToOneField` -- with the same name registered on an ancestor ABOVE the cut (in
the MRO, never consulted by a read) and INSIDE it, plus `CharField` as a
non-truncating contrast. Each shape records whether a full-MRO binding of the
enclosing layer would have differed from the real recomputed view; if none does,
the run fails, because then the truncating branch was never witnessed and the
A-reference would be unchecked exactly where it used to over-claim.

PATCH-STATE CONTROL (the load-bearing correctness property of this script).
The SWE-bench instance image is checked out at `base_commit`, i.e. the
UNPATCHED tree whose `_unregister_lookup` deletes from `class_lookups` but does
NOT clear the cache -- so a read after removal answers from the STALE memoised
view and still reports the removed name. A check that asserted the *fixed*
behaviour against that ambient code would (correctly) fail. So this script does
NOT trust the ambient `_unregister_lookup`. It explicitly exercises BOTH code
states by performing the unregister two ways at runtime:

  * FIXED state -- the gold behaviour self-applied: after deleting the name from
    `class_lookups` we also call `cls._clear_cached_lookups()`. The deep model's
    claims must HOLD here (a read of the removed name reports exactly the
    enclosing layer; other names still resolve to the same lookup). This
    reproduces the gold patch irrespective of whether the live tree is pre- or
    post-fix.
  * BUGGY state -- the base_commit removal: delete from `class_lookups` only,
    leave the cache untouched. A read must STILL report the TARGET'S OWN removed
    lookup (the stale view) -- in the shadowing family too, where the correct
    answer would have been the ancestor's lookup. This turns the implicit
    discrimination into an explicit two-state check and proves the observable the
    deep model relies on genuinely distinguishes the fixed behaviour from the
    buggy one (G-DIFF made concrete against real Django).
  * COMPONENT-ONLY state -- the delete plus an invalidation that reaches ONLY the
    target's own memoised read (`component_only_unregister` mutates the very dict
    object the target's lru_cache entry holds, so exactly one class's memo moves).
    This state SATISFIES both of the first two lines of the deep model and is
    still wrong: a read through a dependent subclass answers from its own cache
    entry and keeps reporting the target's removed lookup. Asserting that is what
    makes `reader_view[name] == reader_rest[name]` an obligation with observable
    content rather than a restatement of `view[name] == inherited[name]` -- the
    gold and component-only post-states differ ONLY in the reader's answers. A run
    in which this state was never witnessed exits 1, on the synthetic hierarchy
    and on the real classes the F2P test uses (`ForeignObject` read through
    `ForeignKey`) separately.

All three paths reuse the REAL repository internals (`class_lookups`, the
lru_cache-memoised `get_lookups`, `merge_dicts`, `_clear_cached_lookups`,
`register_lookup`) -- only WHICH memo entries the invalidation reaches is
controlled, which is exactly what the line the gold patch adds decides. Imports:
the standard library plus the repository package under evaluation. Exit 0 iff
every observation matches in ALL THREE states.
"""
import inspect
import random
import sys

import django
from django.conf import settings

# Minimal Django configuration so model fields / lookups can be used.
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={},
    )
    django.setup()

from django.db.models.query_utils import RegisterLookupMixin  # noqa: E402
from django.db.models.lookups import Lookup  # noqa: E402


def make_lookup(name, tag=""):
    """Construct a distinct real Lookup subclass with the given lookup_name.
    `tag` only varies the class object's identity, so "resolves to the SAME
    lookup" and "resolves to the ANCESTOR's lookup" have observable content."""
    return type("L_%s%s" % (name, tag), (Lookup,), {"lookup_name": name})


def make_hierarchy():
    """A fresh FOUR-LEVEL real RegisterLookupMixin hierarchy
    (grandparent -> parent -> target -> child), each level with its own
    `class_lookups` and its own memoised `get_lookups` cache, so sequences are
    independent. Returned as (grand, parent, target, child); the removal is
    always performed on `target`, whose derived view is the real `merge_dicts`
    over the range its own `get_lookups` merges -- here, since every level
    subclasses `RegisterLookupMixin` directly and inherits the unoverridden
    method, `inspect.getmro(target)`, i.e. it consults the levels above it."""
    grand = type("Grand", (RegisterLookupMixin,), {})
    parent = type("Parent", (grand,), {})
    target = type("Target", (parent,), {})
    child = type("Child", (target,), {})
    for cls in (grand, parent, target, child):
        cls.class_lookups = {}
    return grand, parent, target, child


def fallback_bases(cls):
    """The classes whose `class_lookups` a read of `cls` ACTUALLY merges, in the
    real preference order, EXCLUDING `cls` itself.

    Not `inspect.getmro(cls)[1:]`: `get_lookups` is overridable, and
    `ForeignObject` overrides it (`django/db/models/fields/related.py:858-864` @
    base_commit) to merge only `bases[: bases.index(ForeignObject) + 1]`. So for
    `ForeignObject` / `ForeignKey` / `OneToOneField` an ancestor above that cut is
    in the MRO yet is NEVER consulted by a read, and a full-MRO merge would claim
    a resolution the real read never produces.

    The range is DISCOVERED by probing the real `get_lookups`, not by
    re-implementing any base-selection rule: a fresh sentinel name is registered
    on one MRO class at a time (through the real `register_lookup`) and we ask
    whether a read of `cls` sees it. That uses only registration + read, never the
    removal under test, so there is no circularity."""
    out = []
    for i, k in enumerate(inspect.getmro(cls)):
        if not (isinstance(k, type) and issubclass(k, RegisterLookupMixin)):
            continue
        sentinel = "__ax_probe_%d_%d" % (id(cls) % 9973, i)
        created = "class_lookups" not in k.__dict__
        k.register_lookup(make_lookup(sentinel, "_probe"), sentinel)
        try:
            if sentinel in cls.get_lookups():
                out.append(k)
        finally:
            k.__dict__["class_lookups"].pop(sentinel, None)
            if created and not k.__dict__["class_lookups"]:
                del k.class_lookups
            _clear_cached(k)
    return tuple(out)


def inherited_of(cls, name):
    """What the enclosing registration layer provides for `name`: the REAL
    `merge_dicts` over the classes a read of `cls` falls back to (its own
    `get_lookups` merge range minus `cls`), in the same preference order
    `get_lookups` uses. `None` <-> the model's `unregistered()`."""
    above = RegisterLookupMixin.merge_dicts(
        [parent.__dict__.get("class_lookups", {})
         for parent in fallback_bases(cls)[1:]])
    return above.get(name)


def resolves(cls, name):
    """The real read a consumer performs: does `name` resolve in the memoised
    lookup view? `get_lookups()` is the lru_cache-memoised merged view."""
    return name in cls.get_lookups()


def _clear_cached(cls):
    """Invoke the real cache-invalidation classmethod. At this instance's
    base_commit (Django 4.1) it is named `_clear_cached_lookups`; later releases
    renamed it to `_clear_cached_class_lookups`. Resolve whichever the tree under
    evaluation provides so the check reuses the REAL invalidation, not a re-impl."""
    for attr in ("_clear_cached_lookups", "_clear_cached_class_lookups"):
        fn = getattr(cls, attr, None)
        if fn is not None:
            fn()
            return
    raise AssertionError("no cache-invalidation classmethod on RegisterLookupMixin")


def fixed_unregister(cls, lookup):
    """The gold behaviour, self-applied: delete the registration AND invalidate
    the memoised view (exactly `del class_lookups[name]; _clear_cached_lookups()`)."""
    name = lookup.lookup_name
    del cls.class_lookups[name]
    _clear_cached(cls)


def buggy_unregister(cls, lookup):
    """The base_commit behaviour: delete the registration only; leave the
    memoised view stale (no cache clear)."""
    name = lookup.lookup_name
    del cls.class_lookups[name]


def rest_of_range(levels, name, skip=None):
    """What the REAL `merge_dicts` over `levels` (a probed read range) provides
    for `name`, optionally with one level set aside. `None` <-> the model's
    `unregistered()`. Reads `class_lookups` only, so it is unaffected by cache
    state."""
    return RegisterLookupMixin.merge_dicts(
        [k.__dict__.get("class_lookups", {})
         for k in levels if k is not skip]).get(name)


def component_only_unregister(cls, lookup, own_range):
    """The COMPONENT-ONLY removal: delete the registration and bring ONLY `cls`'s
    OWN memoised read back in line, leaving every class that reads THROUGH `cls`
    with the answers it already had.

    `get_lookups` is `@functools.lru_cache`-decorated on the classmethod
    (`query_utils.py:157-163` @ base_commit), so each class is a DISTINCT cache
    key holding a DISTINCT merged dict, and `get_lookups()` hands back the very
    object the cache holds -- mutating it in place moves exactly one class's memo.
    That is what makes this a genuine per-class-invalidation mutant of the gold
    behaviour rather than a re-implementation of it, and it is why the real
    `_clear_cached_lookups` walks `cls.__subclasses__()`
    (`query_utils.py:196-199`) instead of clearing one entry.

    `own_range` is `cls`'s already-probed read range: recomputing it here would
    clear the very memos this mutant must leave alone.
    """
    name = lookup.lookup_name
    del cls.class_lookups[name]
    own_memo = cls.get_lookups()                 # the memoised dict object
    correct = rest_of_range(own_range, name)
    if correct is None:
        own_memo.pop(name, None)
    else:
        own_memo[name] = correct


def _build(name, other, shadow_parent, shadow_grand):
    """Set up the real four-level hierarchy through the REAL `register_lookup`:
    the target registers `other` and `name`; optionally the parent and/or the
    grandparent ALSO register `name`, under a different lookup class. Returns
    (grand, parent, target, child, l_name)."""
    grand, parent, target, child = make_hierarchy()
    if shadow_grand:
        grand.register_lookup(make_lookup(name, "_grand"))
    if shadow_parent:
        parent.register_lookup(make_lookup(name, "_parent"))
    l_name = make_lookup(name, "_target")
    target.register_lookup(make_lookup(other, "_other"))   # other resolving
    target.register_lookup(l_name)                         # name resolving
    return grand, parent, target, child, l_name


def check_fixed(name, other, shadow_parent=False, shadow_grand=False):
    """A-reference: under the gold behaviour, on the real hierarchy, after
    register(other), register(name) [plus optional ancestor registrations of
    `name`], a read (to populate the caches), then unregister(name) on the
    target:
      * the target's own backing store no longer has name (store[name] ==
        unregistered());
      * a read of the removed name now reports exactly what the ENCLOSING layer
        provides -- nothing when no ancestor registers it, and the ancestor's
        lookup when one does (view[name] == inherited[name]);
      * a read of the removed name THROUGH A DEPENDENT SUBCLASS likewise reports
        exactly what THAT reader's own remaining levels provide
        (reader_view[name] == reader_rest[name]) -- a separate lru_cache entry
        over the same registration layer, so this is a second observable and not
        a restatement of the previous one;
      * the other name still resolves to its same lookup (view[other] preserved).
    Matches the deep model (model.py impl region). Returns True iff this sequence
    was in the SHADOWING family."""
    grand, parent, target, child, l_name = _build(
        name, other, shadow_parent, shadow_grand)
    # The read ranges are probed FIRST: the probe registers and unregisters a
    # sentinel and so clears the caches it touches, which would undo the priming
    # below.
    t_range = fallback_bases(target)
    c_range = fallback_bases(child)
    # What the enclosing layer provides for the removed name, read through the
    # REAL merge_dicts over the target's own probed read range: inherited[name].
    inherited_before = rest_of_range(t_range[1:], name)
    # What the DEPENDENT READER's own remaining levels provide once the target's
    # backing store is set aside: reader_rest[name].
    reader_rest_before = rest_of_range(c_range, name, skip=target)
    # populate the memoised views (prior reads) at every level, as the
    # precondition assumes -- a stale view is then observable if not cleared.
    for cls in (grand, parent, target, child):
        cls.get_lookups()
    assert resolves(target, name), "precondition: name should resolve before removal"
    assert resolves(target, other), "precondition: other should resolve before removal"
    other_target_before = target.get_lookups()[other]
    # the reader's incoming answers satisfy the model's per-reader read-through
    # law: it either reports the target's own registration or its own remaining
    # levels' answer.
    reader_before = child.get_lookups().get(name)
    assert reader_before is l_name or reader_before is reader_rest_before, (
        "precondition (per-reader read-through law) broken: a read through the "
        "subclass reports %r, which is neither the target's registration %r nor "
        "the reader's remaining levels' answer %r"
        % (reader_before, l_name, reader_rest_before))
    assert inherited_before is not l_name, (
        "setup: the ancestors' lookup must be a distinct class object")
    assert reader_rest_before is not l_name, (
        "setup: the reader's remaining levels must not provide the target's own "
        "lookup object")

    fixed_unregister(target, l_name)       # the operation under test (FIXED)

    # (1) the target's OWN backing store no longer registers name.
    assert name not in target.__dict__.get("class_lookups", {}), (
        "deep model unsound (FIXED): name still in the target's class_lookups "
        "after removal")
    # (2) a read of the removed name reports exactly the enclosing layer.
    after = target.get_lookups().get(name)
    assert after is inherited_before, (
        "deep model unsound (FIXED): after the gold removal a read of %r "
        "reports %r, but the enclosing registration layer provides %r -- the "
        "model's view[name] == inherited[name] does not hold"
        % (name, after, inherited_before))
    if inherited_before is None:
        # the non-shadowing family: the name stops resolving altogether.
        assert not resolves(target, name), (
            "deep model unsound (FIXED): removed name %r still resolves via the "
            "memoised view after the gold removal" % name)
    else:
        # the shadowing family: the read resurfaces the ANCESTOR's lookup, and
        # a model claiming it reports nothing would be unsound here.
        assert resolves(target, name), (
            "deep model unsound (FIXED): removed name %r stopped resolving even "
            "though an ancestor registers it -- a read must fall back to the "
            "enclosing layer" % name)
        assert after is not l_name, (
            "deep model unsound (FIXED): the read still reports the target's own "
            "removed lookup for %r" % name)
    # (2b) a read of the removed name THROUGH THE DEPENDENT SUBCLASS reports
    #      exactly what that reader's own remaining levels provide. This is a
    #      SEPARATE lru_cache entry from the target's, so it is a genuinely
    #      different observable; the gold `_clear_cached_lookups` reaches it only
    #      because it walks `cls.__subclasses__()` (query_utils.py:196-199).
    reader_after = child.get_lookups().get(name)
    assert reader_after is reader_rest_before, (
        "deep model unsound (FIXED): after the gold removal a read of %r THROUGH "
        "THE SUBCLASS reports %r, but the reader's own remaining registration "
        "levels provide %r -- the model's reader_view[name] == reader_rest[name] "
        "does not hold" % (name, reader_after, reader_rest_before))
    assert reader_after is not l_name, (
        "deep model unsound (FIXED): a read through the subclass still reports "
        "the target's own removed lookup for %r" % name)
    # frame: the other name still resolves to the SAME lookup.
    assert resolves(target, other), (
        "deep model unsound (FIXED): unrelated name %r stopped resolving" % other)
    assert target.get_lookups()[other] is other_target_before, (
        "deep model unsound (FIXED): unrelated name %r now resolves to a "
        "different lookup" % other)
    return inherited_before is not None


def check_buggy_keeps_stale(name, other, shadow_parent=False, shadow_grand=False):
    """Differential: under the base_commit removal (no cache clear), a read after
    removal STILL reports the TARGET'S OWN removed lookup from the stale memoised
    view -- not the enclosing layer's. Proves the observable discriminates fixed
    from buggy (the bug the F2P test pins) in both families."""
    grand, parent, target, child, l_name = _build(
        name, other, shadow_parent, shadow_grand)
    for cls in (grand, parent, target, child):
        cls.get_lookups()
    assert resolves(target, name), "precondition: name should resolve before removal"

    buggy_unregister(target, l_name)       # the base_commit removal (BUGGY)

    # backing store DID lose the name ...
    assert name not in target.__dict__.get("class_lookups", {}), (
        "buggy removal did not even delete from the target's class_lookups")
    # ... but the stale memoised view STILL reports the removed lookup itself
    # (this is the bug) -- in the shadowing family too, where the correct answer
    # would have been the ancestor's lookup rather than nothing.
    assert resolves(target, name), (
        "the base_commit removal did NOT leave a stale view for %r: the "
        "observable cannot witness the fix -- the two-state check is not "
        "discriminating" % name)
    assert target.get_lookups().get(name) is l_name, (
        "the stale view does not report the target's own removed lookup for %r, "
        "so the observable does not witness the missing cache clear" % name)


def check_component_only_leaves_reader_stale(name, other, shadow_parent=False,
                                            shadow_grand=False):
    """THIRD code state, and the one that gives the per-reader clause its content.

    A removal that deletes the local registration AND brings only the TARGET'S
    OWN memoised read back in line satisfies both of the previous clauses
    (`store[name] == unregistered()` and `view[name] == inherited[name]`) and is
    still wrong: `get_lookups` is memoised per class, so a read through a
    dependent subclass answers from ITS OWN cache entry and keeps reporting the
    target's removed lookup. That is exactly the state
    `custom_lookups.tests.LookupTests.test_lookups_caching` fails on -- it
    registers "exactly" on `ForeignObject` and asserts `assertNotIn("exactly",
    field.get_lookups())` through a `ForeignKey` field.

    Asserting that here is what makes `reader_view[name] == reader_rest[name]` an
    obligation with observable content rather than a restatement of clause (2):
    the two states differ ONLY in the reader's answers. Returns True iff this
    sequence witnessed it."""
    grand, parent, target, child, l_name = _build(
        name, other, shadow_parent, shadow_grand)
    # ranges probed BEFORE priming: the probe clears the caches it touches, and
    # this state is defined by which memos are left alone.
    t_range = fallback_bases(target)
    c_range = fallback_bases(child)
    inherited_before = rest_of_range(t_range[1:], name)
    reader_rest_before = rest_of_range(c_range, name, skip=target)
    for cls in (grand, parent, target, child):
        cls.get_lookups()
    assert resolves(target, name), "precondition: name should resolve before removal"
    assert child.get_lookups().get(name) is l_name, (
        "precondition: a read through the subclass should report the target's "
        "registration of %r before the removal" % name)
    assert reader_rest_before is not l_name, (
        "setup: the reader's remaining levels must not provide the target's own "
        "lookup object, or the two post-states could not differ")

    component_only_unregister(target, l_name, t_range)   # THIRD state

    # the target's own answers ARE in line -- clauses (1) and (2) both hold ...
    assert name not in target.__dict__.get("class_lookups", {}), (
        "component-only removal did not delete from the target's class_lookups")
    assert target.get_lookups().get(name) is inherited_before, (
        "the component-only state was not constructed as intended: a read of the "
        "TARGET reports %r rather than the enclosing layer's %r, so it does not "
        "satisfy clause (2) and would be rejected for the wrong reason"
        % (target.get_lookups().get(name), inherited_before))
    # ... and the removal is STILL wrong, in the reader's answers alone.
    stale = child.get_lookups().get(name)
    assert stale is l_name, (
        "the component-only removal did NOT leave a read through the subclass "
        "reporting the target's removed lookup for %r (it reports %r), so the "
        "per-reader observable does not witness the subclass half of the real "
        "invalidation and reader_view[name] == reader_rest[name] would be "
        "vacuous" % (name, stale))
    assert stale is not reader_rest_before, (
        "the component-only state is indistinguishable from the gold one for %r: "
        "the reader's remaining levels provide the same lookup object it already "
        "reported" % name)
    return True


def read_range_shapes():
    """(label, owner, ancestor, ancestor_is_consulted) for the READ-RANGE family.

    `make_hierarchy` builds four classes that subclass `RegisterLookupMixin`
    DIRECTLY, so each inherits the unoverridden `get_lookups` and its read range is
    always the full MRO: on those sequences `fallback_bases` can only return the
    full MRO tail and the truncating branch is unreachable. These shapes reach it on
    the REAL classes that override the method -- `ForeignObject` and its subclasses,
    whose override (`django/db/models/fields/related.py:858-864` @ base_commit)
    merges only `bases[: bases.index(ForeignObject) + 1]` -- pairing each with a
    second registration of the same name on an ancestor ABOVE the cut (in the MRO,
    never consulted by a read) and INSIDE it (a real resurfacing), plus `CharField`
    in the same shape as a non-truncating contrast.
    """
    from django.db import models
    return [
        ("fo-ancestor-above-cut", models.ForeignObject, models.Field, False),
        ("fk-ancestor-above-cut", models.ForeignKey, models.Field, False),
        ("fk-ancestor-inside-cut", models.ForeignKey, models.ForeignObject, True),
        ("o2o-ancestor-inside-cut", models.OneToOneField, models.ForeignKey, True),
        ("charfield-ancestor-consulted", models.CharField, models.Field, True),
    ]


def _rr_levels(owner):
    return [k for k in inspect.getmro(owner)
            if isinstance(k, type) and issubclass(k, RegisterLookupMixin)]


def _rr_cleanup(owner, ancestor, names):
    for k in (ancestor, owner):
        own = k.__dict__.get("class_lookups", {})
        for n in names:
            own.pop(n, None)
        _clear_cached(k)


def check_fixed_read_range(owner, ancestor, name, consulted):
    """A-reference on the read-range family: register `name` on an ancestor AND on
    `owner`, read (so the caches are warm), then apply the GOLD removal to
    `owner`'s registration. A read of the removed name must report exactly what
    the rest of OWNER's OWN read range provides -- which for a truncating owner and
    an ancestor above the cut is NOTHING, even though the ancestor still registers
    it and is in `inspect.getmro(owner)`.

    Returns (was_in_the_shadowing_family, the_full_MRO_binding_would_have_differed).
    The second flag is the coverage witness: on the shapes where it is True, a
    version of this check that merged `inspect.getmro(owner)[1:]` unconditionally
    would have asserted a resolution the real read does not produce."""
    other = "ax_rr_other_" + name
    l_anc = make_lookup(name, "_rr_anc")
    l_own = make_lookup(name, "_rr_own")
    l_other = make_lookup(other, "_rr_other")
    assert name not in owner.get_lookups(), (
        "read-range setup: %r already resolves on %s" % (name, owner.__name__))
    try:
        ancestor.register_lookup(l_anc, name)
        owner.register_lookup(l_other, other)
        owner.register_lookup(l_own, name)
        # `fallback_bases` probes by registering and unregistering a sentinel,
        # which CLEARS the caches it touches, so the enclosing layer is read
        # BEFORE the priming reads and the priming below is what the removal is
        # then measured against.
        inherited_before = inherited_of(owner, name)
        full_mro_binding = RegisterLookupMixin.merge_dicts(
            [k.__dict__.get("class_lookups", {})
             for k in _rr_levels(owner)[1:]]).get(name)
        for k in _rr_levels(owner):
            k.get_lookups()
        assert resolves(owner, name), "precondition: name should resolve before removal"
        assert resolves(owner, other), "precondition: other should resolve before removal"
        other_before = owner.get_lookups()[other]
        assert inherited_before is not l_own, (
            "setup: the ancestor's lookup must be a distinct class object")

        fixed_unregister(owner, l_own)          # the operation under test (FIXED)

        assert name not in owner.__dict__.get("class_lookups", {}), (
            "deep model unsound (FIXED, read-range): name still in %s's "
            "class_lookups after removal" % owner.__name__)
        after = owner.get_lookups().get(name)
        assert after is inherited_before, (
            "deep model unsound (FIXED, read-range %s): after the gold removal a "
            "read of %r reports %r, but the rest of the class's own read range "
            "provides %r -- the model's view[name] == inherited[name] does not "
            "hold" % (owner.__name__, name, after, inherited_before))
        assert (after is not None) == consulted, (
            "READ-RANGE EXPECTATION BROKEN (%s, ancestor %s): the ancestor was "
            "expected to be %s by a read of the owner, but the recomputed view "
            "reports %r" % (owner.__name__, ancestor.__name__,
                            "consulted" if consulted else "outside the read range",
                            after))
        assert resolves(owner, other), (
            "deep model unsound (FIXED, read-range): unrelated name %r stopped "
            "resolving" % other)
        assert owner.get_lookups()[other] is other_before, (
            "deep model unsound (FIXED, read-range): unrelated name %r now "
            "resolves to a different lookup" % other)
        return (inherited_before is not None), (full_mro_binding is not after)
    finally:
        _rr_cleanup(owner, ancestor, (name, other))


def _rr_reader(owner):
    """A REAL Django field class that reads THROUGH `owner`, for the read-range
    family; None when the shape has no distinct dependent reader.
    `models.ForeignObject` pairs with `models.ForeignKey`, which is exactly the
    pair `test_lookups_caching` exercises (it registers on `ForeignObject` and
    asserts through a `ForeignKey` field)."""
    from django.db import models
    for cand in (models.ForeignKey, models.OneToOneField, models.TextField,
                 models.BigIntegerField):
        if cand is not owner and issubclass(cand, owner):
            return cand
    return None


def check_component_only_read_range(owner, ancestor, name):
    """The component-only state on the READ-RANGE family, i.e. on the REAL classes
    the F2P test uses. Returns True iff the shape had a dependent reader and the
    state was witnessed: the owner's own memoised read is correct and a read
    through the reader still reports the owner's removed lookup."""
    reader = _rr_reader(owner)
    if reader is None:
        return False
    other = "ax_rr_other_" + name
    l_anc = make_lookup(name, "_rr_anc")
    l_own = make_lookup(name, "_rr_own")
    l_other = make_lookup(other, "_rr_other")
    try:
        ancestor.register_lookup(l_anc, name)
        owner.register_lookup(l_other, other)
        owner.register_lookup(l_own, name)
        o_range = fallback_bases(owner)
        r_range = fallback_bases(reader)
        inherited_before = rest_of_range(o_range[1:], name)
        reader_rest_before = rest_of_range(r_range, name, skip=owner)
        for k in set(_rr_levels(owner)) | set(_rr_levels(reader)):
            k.get_lookups()
        if reader.get_lookups().get(name) is not l_own:
            # the reader does not read through the owner for this name (it
            # registers it itself, or the owner is outside its read range): the
            # two post-states coincide and nothing could witness the difference.
            return False
        if reader_rest_before is l_own:
            return False

        component_only_unregister(owner, l_own, o_range)

        assert owner.get_lookups().get(name) is inherited_before, (
            "the component-only state was not constructed as intended on %s: a "
            "read of the owner reports %r rather than %r"
            % (owner.__name__, owner.get_lookups().get(name), inherited_before))
        stale = reader.get_lookups().get(name)
        assert stale is l_own, (
            "the component-only removal did NOT leave a read through %s "
            "reporting %s's removed lookup for %r (it reports %r), so the "
            "per-reader observable is not witnessed on the real classes the F2P "
            "test uses" % (reader.__name__, owner.__name__, name, stale))
        return True
    finally:
        _rr_cleanup(owner, ancestor, (name, other))
        _clear_cached(reader)


def check_buggy_read_range(owner, ancestor, name):
    """Differential on the same shape: under the base_commit removal (no cache
    clear) a read of the removed name STILL reports OWNER's own removed lookup
    from the stale memoised view, so these shapes witness the added line too."""
    other = "ax_rr_other_" + name
    l_anc = make_lookup(name, "_rr_anc")
    l_own = make_lookup(name, "_rr_own")
    l_other = make_lookup(other, "_rr_other")
    try:
        ancestor.register_lookup(l_anc, name)
        owner.register_lookup(l_other, other)
        owner.register_lookup(l_own, name)
        for k in _rr_levels(owner):
            k.get_lookups()
        assert resolves(owner, name), "precondition: name should resolve before removal"

        buggy_unregister(owner, l_own)           # the base_commit removal (BUGGY)

        assert name not in owner.__dict__.get("class_lookups", {}), (
            "buggy removal did not even delete from %s's class_lookups"
            % owner.__name__)
        assert resolves(owner, name), (
            "the base_commit removal did NOT leave a stale view for %r on %s: the "
            "observable cannot witness the fix on the read-range family"
            % (name, owner.__name__))
        assert owner.get_lookups().get(name) is l_own, (
            "the stale view does not report %s's own removed lookup for %r, so "
            "the observable does not witness the missing cache clear"
            % (owner.__name__, name))
    finally:
        _rr_cleanup(owner, ancestor, (name, other))


def main():
    # (name, other, shadow_parent, shadow_grand): both families, and both
    # ancestor levels, so merge_dicts' preference order is pinned as well.
    boundary = [
        ("exactly", "iexact", False, False),
        ("lt", "gt", False, False),
        ("my_transform", "year", False, False),
        ("a", "b", False, False),
        # SHADOWING: the parent also registers the removed name.
        ("exactly", "iexact", True, False),
        ("lt", "gt", True, False),
        # SHADOWING: only the grandparent does.
        ("my_transform", "year", False, True),
        ("a", "b", False, True),
        # SHADOWING at BOTH levels: the read must resurface whichever lookup the
        # real merge_dicts prefers.
        ("exactly", "iexact", True, True),
        ("lt", "gt", True, True),
    ]
    shadowing = 0
    comp_only = 0
    for name, other, sp, sg in boundary:
        shadowing += bool(check_fixed(name, other, sp, sg))
        check_buggy_keeps_stale(name, other, sp, sg)
        comp_only += bool(check_component_only_leaves_reader_stale(
            name, other, sp, sg))

    # randomized fuzz over distinct lookup-name pairs, both hierarchy families,
    # both code states.
    rng = random.Random(15569)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    n_fuzz = 2000
    for i in range(n_fuzz):
        n = "n_" + "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
        o = "o_" + "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
        sp = rng.random() < 0.5
        sg = rng.random() < 0.5
        shadowing += bool(check_fixed(n, o, sp, sg))
        check_buggy_keeps_stale(n, o, sp, sg)
        if i % 4 == 0:
            comp_only += bool(check_component_only_leaves_reader_stale(
                n, o, sp, sg))

    # --- the READ-RANGE family, on the real classes that OVERRIDE get_lookups.
    # The synthetic hierarchy above cannot reach the truncating branch (every
    # level inherits the unoverridden method), so this family is where the
    # binding of `inherited` to the class's OWN read range is actually tested.
    rr_shapes = read_range_shapes()
    rr_refuted = 0
    rr_comp_only = 0
    for label, owner, ancestor, consulted in rr_shapes:
        rr_name = "ax_rr_%s" % label.replace("-", "_")
        sh, refuted = check_fixed_read_range(owner, ancestor, rr_name, consulted)
        shadowing += bool(sh)
        rr_refuted += bool(refuted)
        check_buggy_read_range(owner, ancestor, rr_name)
        rr_comp_only += bool(check_component_only_read_range(
            owner, ancestor, rr_name))
    comp_only += rr_comp_only

    total = len(boundary) + n_fuzz + len(rr_shapes)
    if not rr_refuted:
        print("G-AX FAIL: on none of the %d read-range shapes would the REFUTED "
              "full-MRO binding of the enclosing layer have differed from the "
              "real recomputed view, so the truncating get_lookups override "
              "(related.py:858-864) was never witnessed and the A-reference is "
              "unchecked on that family." % len(rr_shapes))
        return 1

    if not comp_only:
        print("G-AX FAIL: not one sequence witnessed the COMPONENT-ONLY state -- "
              "a removal that deletes the local registration and brings only the "
              "target's OWN memoised read back in line, leaving a read through a "
              "dependent subclass still reporting the removed lookup. Without it "
              "the A-reference's reader_view[name] == reader_rest[name] has no "
              "observable content beyond view[name] == inherited[name], and the "
              "state the F2P test actually fails on would be unmeasured.")
        return 1

    if not rr_comp_only:
        print("G-AX FAIL: the component-only state was never witnessed on the "
              "READ-RANGE family, i.e. on the real Django field classes the F2P "
              "test uses (register on ForeignObject, read through ForeignKey), so "
              "the per-reader clause is checked only on the synthetic hierarchy.")
        return 1

    if not shadowing:
        print("G-AX FAIL: not one sequence had an ancestor registering the "
              "removed name, so the A-reference's view[name] == inherited[name] "
              "was only ever exercised in its inherited[name] == unregistered() "
              "special case -- the clause is untested where it bites.")
        return 1

    print("G-AX OK: under the gold behaviour (delete + clear cache, self-applied "
          "at runtime), the deep model (A-reference) == real "
          "RegisterLookupMixin lookup resolution on %d boundary + %d fuzz + %d "
          "read-range sequences (%d of the latter refuting a full-MRO binding of "
          "the enclosing layer, i.e. played on the real classes whose get_lookups "
          "override truncates the merge range; the other two families on a fresh "
          "real four-level hierarchy) (the target's own backing store loses the "
          "name; a read of "
          "the removed name reports exactly what the enclosing registration "
          "layer provides, via the real merge_dicts over the target's own probed "
          "read range -- nothing in the %d non-shadowing sequences, the ANCESTOR's "
          "lookup in the %d sequences where an ancestor registers it too; "
          "unrelated names still resolve to the same lookup); under the "
          "base_commit removal (no cache clear) the stale memoised view STILL "
          "reports the target's own removed lookup, so the observable "
          "discriminates fixed from buggy in both families. A THIRD state was "
          "exercised on %d sequences (%d of them on the real classes the F2P test "
          "uses): a COMPONENT-ONLY removal that deletes the local registration "
          "and brings only the target's own memoised read in line -- it satisfies "
          "both of the previous clauses and STILL leaves a read through a "
          "dependent subclass reporting the removed lookup, because get_lookups "
          "is memoised per class and only the real _clear_cached_lookups' walk "
          "over cls.__subclasses__() reaches those entries; so the A-reference's "
          "reader_view[name] == reader_rest[name] has observable content that "
          "view[name] == inherited[name] does not."
          % (len(boundary), n_fuzz, len(rr_shapes), rr_refuted,
             total - shadowing, shadowing, comp_only, rr_comp_only))
    return 0


if __name__ == "__main__":
    sys.exit(main())
