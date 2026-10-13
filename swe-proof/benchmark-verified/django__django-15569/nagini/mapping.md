# mapping.md — django__django-15569

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 884b4c27f506b3c29d58509fc83a35c30ea10d94`, states the type
abstraction, and gives the provenance of the A-reference (the deep model is
validated against the real callee by `axiom_check.py` / G-AX). There are NO
consumed `@ContractOnly` axioms.

Repo file under change: `django/db/models/query_utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `remove_registration(store, view, inherited, reader_view, reader_rest, name)` | `RegisterLookupMixin._unregister_lookup(cls, lookup, lookup_name=None)` — `django/db/models/query_utils.py:212-219` | the modeled changed operation (drop a local registration AND bring the derived lookup view of EVERY component that reads through this one back in line with the remaining registration levels) |
| `store` (param) | `cls.__dict__["class_lookups"]` — the per-class backing dict of registered lookups, i.e. the dict `_unregister_lookup` deletes from (`query_utils.py:206-207, 219`) | the LOCAL backing store mapping a lookup name to the registered lookup class |
| `view` (param) | the value memoised by `RegisterLookupMixin.get_lookups` (the `@functools.lru_cache(maxsize=None)` classmethod, `query_utils.py:157-163`) — the effective merged lookup mapping a read observes | the derived resolved view: what `cls.get_lookups()` / `_get_lookup(name)` reports |
| `inherited` (param, `Acc(...,1/2)` read-only) | `merge_dicts` over the `class_lookups` of the classes `cls.get_lookups()` actually merges, EXCLUDING `cls` itself — i.e. `merge_dicts` over the `class_lookups` of exactly the classes `cls.get_lookups()` merges, minus `cls` itself. For most classes that is `inspect.getmro(cls)[1:]`, but `get_lookups` is OVERRIDABLE and `ForeignObject` overrides it (`django/db/models/fields/related.py:858-864` @ base_commit) to merge only `bases[: bases.index(ForeignObject) + 1]`, so for `ForeignObject` / `ForeignKey` / `OneToOneField` the fallback range is a STRICT SUBSET of the full MRO. Binding `inherited` to the full MRO would make the spec claim a resolution those classes' reads never produce | the ENCLOSING registration layer THIS component's reads fall back to; unchanged by the operation, hence read-only |
| `reader_view` (param, full permission) | the value memoised by `get_lookups` for a DIFFERENT class `R` that reads through `cls` — i.e. `R.get_lookups()` where `cls in` the range `R.get_lookups` merges. `get_lookups` is `@functools.lru_cache(maxsize=None)`-decorated on the classmethod (`query_utils.py:157-163`), so **each class is a distinct cache key holding a distinct merged dict**: `R`'s memoised answers are a separate object from `cls`'s and are NOT recomputed when `cls`'s entry is evicted alone. This is why `_clear_cached_lookups` (`query_utils.py:196-199`) walks `cls.__subclasses__()` (via `subclasses()`, `query_utils.py:26-29`) instead of dropping one entry | the memoised answers of an ARBITRARY reader of this registry. Universally quantified by being a parameter, so a claim about it is a claim about every reader. Mutated by the operation ⇒ full permission. It is the observable `custom_lookups.tests.LookupTests.test_lookups_caching` reads: the test registers "exactly" on `ForeignObject` and asserts `assertNotIn("exactly", field.get_lookups())` for a `ForeignKey` field, i.e. through a SUBCLASS's cache entry |
| `reader_rest` (param, `Acc(...,1/2)` read-only) | `merge_dicts` over the `class_lookups` of the classes `R.get_lookups()` actually merges, with `cls` itself SET ASIDE — the answer `R`'s own remaining registration levels provide. `R`'s range is probed the same way `inherited`'s is, so the `ForeignObject` truncation (`related.py:858-864`) is respected on the reader side too | what the reader's OWN read range provides once this component's local store is removed from it; unchanged by the operation (which touches only `cls.class_lookups`), hence read-only — which also forbids a verifying impl from repairing the reader's answers by editing the reader's own registrations |
| `name` (param) | `lookup_name` (the `del cls.class_lookups[lookup_name]` key, `query_utils.py:217-219`) | the lookup name being removed |
| `unregistered()` | sentinel for "name not present in `class_lookups`" / "name not present in `get_lookups()`" / "no ancestor provides the name" | distinguished registration state |
| `other_name()` | a representative OTHER registered lookup name (any other key in `class_lookups`) | frame witness: an unrelated lookup keeps resolving to its same lookup |

The unchanged collaborators the operation relies on (not referenced from the
consumer spec view; cited here for the refinement audit):
- `RegisterLookupMixin._clear_cached_lookups` (`query_utils.py:196-199`) — clears
  the `get_lookups` lru_cache for the class and its subclasses; the call the gold
  patch ADDS. (Renamed `_clear_cached_class_lookups` in later Django releases;
  `axiom_check.py` resolves whichever the tree under evaluation provides.)
- `RegisterLookupMixin.register_lookup` (`query_utils.py:201-209`) — the already
  correct sibling: it sets `class_lookups[name]` then ALSO calls
  `_clear_cached_lookups()`. The issue cites it as the symmetry the removal must
  mirror.
- `RegisterLookupMixin.get_lookups` (`query_utils.py:157-163`) — the
  lru_cache-memoised read; `merge_dicts` (`query_utils.py:185-194`) merges the
  `class_lookups` of the classes that method passes it, most-derived winning. The
  base implementation passes `inspect.getmro(cls)`; the method is overridable and
  `ForeignObject` (`related.py:858-864`) passes only
  `bases[: bases.index(ForeignObject) + 1]`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `cls.__dict__["class_lookups"]` (a `dict` str→Lookup class) | `store: Dict[int, int]` | a lookup `name` (str) ↔ an `int` name token; the registered lookup CLASS ↔ an `int` identity token; only "is this name registered locally, and to which lookup" is observed |
| the memoised `get_lookups()` mapping (a `dict` str→Lookup class) | `view: Dict[int, int]` | same name/identity tokenization; `view` models the EFFECTIVE answer a read returns after any internal lru_cache invalidation + recompute, NOT raw cache internals |
| `merge_dicts` over the `class_lookups` of the classes `cls.get_lookups()` merges minus `cls` itself (a `dict` str→Lookup class) | `inherited: Dict[int, int]` | same tokenization; the fallback answer THIS component's own reads use for a name, in `get_lookups`' own preference order. NOT the full `inspect.getmro(cls)[1:]`: `ForeignObject` overrides `get_lookups` (`related.py:858-864`) and truncates the merge range, so on `ForeignObject`/`ForeignKey`/`OneToOneField` a registration above the cut is in the full MRO but is never consulted by a read. Held under `Acc(dict_pred(inherited), 1/2)`: the operation READS it and must not write it (the real removal touches only `cls`'s own dict). |
| the memoised `get_lookups()` mapping of a class `R` that reads THROUGH `cls` (a `dict` str→Lookup class) | `reader_view: Dict[int, int]` | same tokenization. A DISTINCT lru_cache entry from `cls`'s, hence a distinct observable: `view` and `reader_view` are two derived views over one shared registration layer, and constraining one leaves the other free. Held at FULL permission because the real invalidation (`_clear_cached_lookups`' walk over `cls.__subclasses__()`) does move it. |
| `merge_dicts` over the `class_lookups` of the classes `R.get_lookups()` merges, with `cls` set aside (a `dict` str→Lookup class) | `reader_rest: Dict[int, int]` | same tokenization; the answer `R`'s own remaining levels provide for a name. Held under `Acc(dict_pred(reader_rest), 1/2)`: the operation reads it and must not write it. A reader that does not reach `cls` at all has `reader_rest == reader_view` on every name, so it is admitted by the precondition and the postcondition is a no-op for it — which is correct, since such a reader's answers do not depend on `cls`'s store. |
| `lookup_name` (str) | `name: int` | name-token; only equality/inequality observed |
| "name NOT in `class_lookups`" / "name NOT in `get_lookups()`" / "no ancestor provides name" (key absence) | the value `unregistered()` held for that name in `store` / `view` / `inherited` | Nagini does not support dict key deletion; key absence is modelled as the name mapping to the distinguished `unregistered()` value. `k in d and d[k] != unregistered()` ⟺ "k present in the real dict"; `d[k] == unregistered()` ⟺ "k absent in the real dict". |
| `del cls.class_lookups[name]` (`query_utils.py:219`) | `store[name] = unregistered()` | the deletion (mark name unregistered in the LOCAL backing store) |
| `cls._clear_cached_lookups()` (the ADDED line) | `view[name] = inherited[name]` | bring the derived view back in line with the remaining registration levels. `_clear_cached_lookups` evicts the WHOLE lru_cache for the class and its subclasses; on the next read `cls.get_lookups` recomputes `merge_dicts` over the classes IT merges (the full MRO for the base implementation, the `ForeignObject`-truncated prefix for that family, `related.py:858-864`). So a read of the removed name reports **exactly what the rest of that read range still provides**: nothing when no class in it registers the name (the common case, and both F2P shapes), and the ANCESTOR's lookup class when one does. Every OTHER name resolves exactly as before. `view[name] = inherited[name]` is the faithful observable abstraction of that clear+recompute — it covers both cases in one clause, since `inherited[name] == unregistered()` in the no-ancestor case (§3; validated by G-AX and mechanically by G-CONF over 100 022 real states). |
| the SUBCLASS WALK inside `cls._clear_cached_lookups()` — `for subclass in subclasses(cls): subclass.get_lookups.cache_clear()` (`query_utils.py:196-199`, `subclasses` at `query_utils.py:26-29`) | `reader_view[name] = reader_rest[name]` | the same clear+recompute one level out, for EVERY component that reads through `cls`. `get_lookups`' lru_cache is keyed per class, so evicting `cls`'s entry leaves each subclass's merged dict in place; only this walk reaches them, and after it the subclass's next read recomputes `merge_dicts` over ITS OWN range, which no longer finds the name in `cls.class_lookups` — so the read reports exactly what the reader's remaining levels provide. Since `reader_view`/`reader_rest` are universally quantified parameters (any dictionary pair the precondition admits), this single clause is the claim for all readers at once. This is the half of the added line that `view[name] = inherited[name]` does NOT cover: a removal that recomputed only `cls`'s own entry satisfies that clause and still fails `test_lookups_caching`, which reads through a `ForeignKey`. Witnessed as a third patch-state by `axiom_check.py` and as a third mutation control by `conformance_check.py`. |

`str` indexing/iteration is banned in Nagini, so name/identity are `int` tokens
throughout; only membership/identity is observed, never character content.

## 3. The A-reference (checked by G-AX / axiom_check.py)

**Deep model ↔ `RegisterLookupMixin` lookup resolution.** The changed operation
is modelled **deeply** (the store deletion and the view invalidation spelled out
in `remove_registration`'s impl region); there is **no consumed axiom**. The
deep model is validated equal to the real operation out-of-band by
`axiom_check.py` (G-AX).

Real fixed behaviour (post-patch `_unregister_lookup`):
```python
@classmethod
def _unregister_lookup(cls, lookup, lookup_name=None):
    if lookup_name is None:
        lookup_name = lookup.lookup_name
    del cls.class_lookups[lookup_name]
    cls._clear_cached_lookups()        # the line the gold patch ADDS
```
`get_lookups` is `@functools.lru_cache(maxsize=None)`-memoised; its base
implementation returns
`merge_dicts([parent.__dict__.get("class_lookups", {}) for parent in mro])`, but
it is OVERRIDABLE and `ForeignObject.get_lookups` (`related.py:858-864`) truncates
the merge range to `bases[: bases.index(ForeignObject) + 1]`, so on that family a
class above the cut is in the MRO yet contributes nothing to a read.
Reads (`_get_lookup` → `get_lookups().get(name)`) answer from that memoised
mapping. `_clear_cached_lookups` calls `subclass.get_lookups.cache_clear()` for
the class and every subclass, so the next read re-enters `cls.get_lookups()` and
recomputes its merge from the current `class_lookups` dicts. Hence after the fixed
removal:
  * a read of the removed name reports exactly what the levels `cls`'s OWN
    `get_lookups` still merges, other than `cls` itself, provide
    (⟺ `view[name] == inherited[name]`) — nothing when no such level registers
    that name, and that level's lookup class when one does. Because the merge
    always walks a range of ancestors, the recomputed view cannot be "the removed
    name is absent" unconditionally: it is "the removed name is absent from
    `cls`'s own level", which is absence in the view only when the rest of the
    read range is silent about it too;
  * a read of the removed name **through any OTHER class `R` that reaches `cls`'s
    registrations** likewise reports exactly what the levels `R`'s OWN
    `get_lookups` still merges, other than `cls`, provide
    (⟺ `reader_view[name] == reader_rest[name]`). This is a SEPARATE claim, not a
    corollary of the previous one: `get_lookups`' lru_cache is keyed per class, so
    `R.get_lookups()` holds its own merged dict and is untouched when only `cls`'s
    entry is evicted. It is reached solely by the `for subclass in
    subclasses(cls)` walk inside `_clear_cached_lookups`
    (`query_utils.py:196-199`, `subclasses` at `query_utils.py:26-29`). A removal
    that recomputed `cls`'s own entry alone satisfies the first bullet and still
    fails `test_lookups_caching`, because that test reads through a `ForeignKey`
    field after registering on `ForeignObject`;
  * every OTHER registered name still resolves to its same lookup class, through
    `cls` and through every reader
    (⟺ `view[other] == Old(view[other])`, `reader_view[other] == Old(reader_view[other])`),
  * `cls`'s own `class_lookups` no longer has the name
    (⟺ `store[name] == unregistered()`).

`axiom_check.py` exercises THREE code states, not two: the gold behaviour, the
base_commit delete-without-clear, and a COMPONENT-ONLY removal that brings only
`cls`'s own memoised read back in line. The third satisfies
`store[name] == unregistered()` and `view[name] == inherited[name]` and still
leaves a read through a subclass reporting the removed lookup, so it is the state
that gives `reader_view[name] == reader_rest[name]` observable content. A run in
which it was never witnessed — on the synthetic hierarchy or on the real
`ForeignObject`/`ForeignKey` pair the F2P test uses — exits 1.

The two F2P shapes are both instances of the `inherited[name] == unregistered()`
case (`"exactly"` is registered only on `ForeignObject`, `"my_transform"` only on
`JSONField`), which is why they read as "the name no longer resolves at all"; the
clause above is the general statement that specialises to it.

Pre-patch (base_commit): the cache is NOT cleared, so a read after removal
answers from the STALE memoised mapping and still reports the removed name —
exactly the bug the F2P tests pin (`test_lookups_caching` asserts
`assertNotIn("exactly", field.get_lookups())` after the removal;
`test_get_transforms` drops its now-redundant manual `_clear_cached_lookups()`
call and relies on `_unregister_lookup` doing it).

**Soundness check (G-AX):** `axiom_check.py` builds a fresh FOUR-LEVEL real
`RegisterLookupMixin` hierarchy (grandparent → parent → target → child) with real
`Lookup` subclasses, registers two names on the target — optionally registering
the removed name on the parent and/or the grandparent under a DIFFERENT lookup
class — reads at every level (to populate the memoised views), then unregisters
one name on the target THREE ways at runtime:
  * FIXED — `del class_lookups[name]; _clear_cached_lookups()` (the gold
    behaviour, resolved dynamically): asserts the target's own `class_lookups`
    lost the name, that a read of the removed name reports **exactly** what the
    enclosing layer provides (`inherited_of(target, name)`, computed through the
    real `merge_dicts` over the target's own fallback range) — nothing in the
    non-shadowing family, the ancestor's lookup object in the shadowing one — and
    that the other name still resolves to the SAME lookup, AND that a read
    THROUGH THE DEPENDENT SUBCLASS reports exactly what that reader's own
    remaining levels provide (`reader_view[name] == reader_rest[name]`) — a
    different lru_cache entry, hence a second observable (the deep model holds);
  * BUGGY — `del class_lookups[name]` only: asserts a read STILL reports the
    TARGET'S OWN removed lookup from the stale view, in both families (the
    observable discriminates fixed from buggy);
  * COMPONENT-ONLY — `del class_lookups[name]` plus an invalidation that reaches
    only the TARGET's own memo (`component_only_unregister` mutates the dict
    object the target's lru_cache entry holds): asserts the target's own read IS
    in line (so clauses (1) and (2) both hold) and that a read through the
    subclass STILL reports the target's removed lookup. This is the state that
    gives the per-reader clause observable content; a run in which it was never
    witnessed FAILS, separately for the synthetic hierarchy and for the real
    `ForeignObject`/`ForeignKey` pair the F2P test uses.
10 boundary configurations (both families, both ancestor levels, and both levels
at once so `merge_dicts`' preference order is pinned) + 2000 randomized fuzz
sequences with the shadowing flags drawn at random + 5 READ-RANGE sequences
(`read_range_shapes` / `check_fixed_read_range`), which is the family a synthetic
hierarchy cannot reach: every level of it subclasses `RegisterLookupMixin` directly
and inherits the unoverridden `get_lookups`, so its read range is always the whole
MRO. Those 5 are played on the real classes that OVERRIDE the method
(`ForeignObject`, `ForeignKey`, `OneToOneField`) with the same name also registered
on an ancestor ABOVE the cut and INSIDE it, plus `CharField` as a non-truncating
contrast; each records whether a full-MRO binding of the enclosing layer would have
differed from the real recomputed view, and a run in which none does FAILS. Exit 0
iff every observation matches in ALL THREE states, and a run in which the shadowing
family never occurred FAILS (the clause would only have been exercised in its
`inherited[name] == unregistered()` special case). Recorded run: 526
non-shadowing and 1489 shadowing sequences, 2 of the 5 read-range shapes
refuting a full-MRO binding, and 513 sequences witnessing the component-only
state (3 of them on the real F2P classes). Playing the sequences on a hierarchy
rather than a single flat class is load-bearing — a flat registry can only ever
observe the special case. It imports only the standard library plus the Django
package under evaluation. The check does NOT trust the ambient (base_commit,
unpatched) `_unregister_lookup`; it drives the precise removal policy under test.

## G-CONF (differential conformance: `conformance_check.py`)

**Shadow.** The impl region of `model.py` copied VERBATIM with the contract calls
stripped — for this bundle exactly `store[name] = unregistered()` /
`view[name] = inherited[name]` / `reader_view[name] = reader_rest[name]` — plus the two `@Pure` helpers it depends on
(`unregistered`, `other_name`; the pure region) minus their decorators. Nothing is
restructured or re-derived.
There is no `PSeq` in this model (the carriers are `Dict[int, int]`), so no
sequence shim is needed, and there is no `@ContractOnly` callee to delegate:
the cache invalidation is modelled DEEPLY, at both levels (refinement.md steps 6
and 9 are A-references, not consumed axioms), so the whole region executes
directly.

**Oracle.** The REAL patched repo function, **called** (not transliterated):
`RegisterLookupMixin._unregister_lookup` (`django/db/models/query_utils.py:212-220`
post-patch, §1). The gate applies `patch.diff` to /testbed before the script
runs, so the import resolves to the patched module and the call IS the gold
operation. All FIVE observables are read through the real collaborators, never
re-implemented: the local backing store via `cls.__dict__["class_lookups"]`, the
enclosing layer via the real `merge_dicts` applied to the `class_lookups` of
the target's own read-fallback range, the derived view via the real
`functools.lru_cache`-memoised `get_lookups()` (`query_utils.py:155-161`),
recomputed through the real `merge_dicts` over the real read range (the real
`fallback_bases` probe, so a truncating `get_lookups` override is honoured rather
than assumed away), and the reader pair via `R.get_lookups()` for a real class `R`
that reads through the target (`Descendant` on the synthetic hierarchy,
`models.ForeignKey` on the `test_lookups_caching` shape) plus the real
`merge_dicts` over `R`'s own probed range with the target set aside. Both
memoised reads are captured BEFORE any `fallback_bases` probing, since the probe
clears the caches it touches and a read taken after it would launder exactly the
staleness those carriers exist to expose. Every scenario PRIMES
the memoised view with actual reads at every level of the hierarchy before the
removal, so a removal that failed to invalidate the cache answers the
post-removal read from the stale mapping — i.e. the branch the gold patch
changes is exercised on every input.

**Third mutation control (the per-reader clause).** Besides the pre-patch and
over-eager controls, every sampled scenario is also run through a COMPONENT-ONLY
removal (`_component_only_removal`): the local registration is deleted and only
the component's OWN lru_cache entry is brought in line, by mutating the very dict
object `get_lookups()` returns. The shadow must DISAGREE with it whenever the
reader genuinely reports the component's local registration and the reader's own
remaining levels provide something else
(`reader_view[name] == store[name] != reader_rest[name]`); the count of such
inputs is reported as `reader_sees_local_registration_inputs`, and a run with
none, or with no discriminating component-only control, exits 1. The control is
run on the exact `test_lookups_caching` pair as well (`ForeignObject` read through
`ForeignKey`), reported as `f2p_component_only_*`.

**Type bridge (§2 inverted).** name token `t` ↔ the lookup name `"conf_lk_<t>"`
(the model's `other_name() == -1` ↔ `"conf_lk_m1"`); identity token ↔ a distinct
REAL `Lookup` subclass carrying that `lookup_name` and an identity marker
`_conf_tok` (3 variants per name, so "the unrelated name still resolves to the
SAME lookup" has content); "key absent from the real dict" ↔ the value
`unregistered()`. Inputs are generated on the CONCRETE side — a real four-level
`RegisterLookupMixin` hierarchy (`GrandAncestor` → `Ancestor` → `Target` →
`Descendant`) populated through the real `register_lookup` — then abstracted, so
every input is a reachable repo state; the model's `Requires` are then
**asserted** (not assumed) on the abstracted pre-state of every input.

**Bridge domain.** Five carriers, so every registration level a read consults is
carried, at BOTH the component and the dependent-reader level: the target's own
`class_lookups` (`store`), what the rest of the target's own read range provides
(`inherited`, computed over `fallback_bases(cls)[1:]` — the classes a read of
`cls` actually consults, probed rather than assumed to be
`inspect.getmro(cls)[1:]`), the memoised merged answer (`view`), and the same pair
one level out for a class `R` that reads through the target: `R`'s own
lru_cache entry (`reader_view`) and what `R`'s remaining levels provide once the
target is set aside (`reader_rest`, the real `merge_dicts` over
`fallback_bases(R)` minus the target). The
scenario space is therefore UNRESTRICTED with respect to inherited shadowing —
hierarchies in which an ancestor ALSO registers the removed name are generated in
the ordinary stream, and on them the real recomputed view resurfaces the
ancestor's lookup, which is exactly what the model predicts
(`view[name] == inherited[name]`). Their frequency is counted and reported in the
final JSON line (`inherited_shadowing_inputs`) so the coverage of that family is
visible rather than assumed; the recorded run has **34 675** of 100 022 inputs in
it. Both F2P shapes are instances of the non-shadowing special case
(`"exactly"` is registered only on `ForeignObject`, `"my_transform"` only on
`JSONField`) and are run explicitly.

**Inputs.** 100 022 Requires-satisfying inputs = 15 boundary + 2 F2P shapes +
5 read-range shapes + 100 000 seeded fuzz. The read-range shapes
(`truncating_shapes` / `check_truncating`) are the family the synthetic hierarchy
cannot generate: they are played on the real classes whose `get_lookups` override
TRUNCATES the merge range (`ForeignObject`, `ForeignKey`, `OneToOneField`,
`related.py:858-864`), each with the removed name also registered on an ancestor
ABOVE the cut (in the MRO, never consulted by a read → the name stops resolving)
and INSIDE it (a real resurfacing), plus `CharField` in the same shape as a
non-truncating contrast. Two of the five would have DISAGREED with the oracle under
a full-MRO binding of `inherited`, and a run in which none of them does exits 1 as
a coverage failure, so the truncating branch is witnessed rather than assumed. Boundary: minimal store (removed name + `other_name()`
only), no-ancestor and singleton-ancestor hierarchies, an ancestor that shadows
`other_name()`, a descendant present (so the real subclass cache-walk runs), a
12-name store with the removed name in the middle, five configurations in which
the removed name IS shadowed from above (parent only, grandparent only, and both
levels at once so `merge_dicts`' preference order is pinned), and BOTH call
shapes of the patched function (`_unregister_lookup(lookup)` → the
`lookup_name is None` branch; `_unregister_lookup(None, name)` → the other). The
impl region is branch-free (two unconditional writes), so "every branch taken" is
discharged by those two oracle call shapes. F2P shapes are run against the real
Django classes the F2P tests touch: a `Lookup` named `"exactly"` on
`models.ForeignObject` (`custom_lookups.tests.LookupTests.test_lookups_caching`)
and a `Transform` named `"my_transform"` on `models.JSONField`
(`model_fields.test_jsonfield.TestMethods.test_get_transforms`).

**Pinned seed: `SEED = 15569`** (module constant `conformance_check.py`;
`N_FUZZ = 100000`).

**Mutation controls.** Three (the third described above), on every boundary case
and every 250th fuzz case.

*Control 1 — the pre-patch removal.* The scenario is re-run through `del
class_lookups[name]` only (no cache clear, self-applied at runtime) and the shadow
must DISAGREE with it. There is exactly one family where no observable can
witness the added line, and it is a property of the repository rather than of the
shadow: if an ancestor registers the removed name to the very SAME lookup class
object the target registered, then "the stale view still reports the target's
lookup" and "the recomputed view reports the ancestor's lookup" name the same
object, so the gold and pre-patch post-states are literally equal. Those states are
reachable, so they stay in-domain and are not skipped; instead every agreement must
be PROVEN degenerate in that precise sense (`inherited[name] == Old(store[name])`).
An unexplained agreement, or a run where no control discriminated at all, exits 1.
Recorded run: 367 of 420 controls discriminated, the other 53 were proven
degenerate (the 5 read-range shapes carry a pre-patch control each, 5/5
discriminating).

*Control 2 — the over-eager removal.* On the same cadence, scenarios that DO have
an inherited registration for the removed name are also re-run through `del
class_lookups[n]; class_lookups[n] = None; _clear_cached_lookups()`, which under
this bridge abstracts to `view[name] = unregistered()` — a removal that forces a
read to report nothing regardless of the enclosing layer. The shadow must disagree
with it; if it never did, the inputs would not witness the difference between "the
view reports the remaining registration levels" and "the view reports nothing",
and the `view[name] == inherited[name]` clause would be untested where it bites.
Recorded run: 142/142 discriminated. Note this control is not hypothetical — a
real patch of that shape leaves `"exactly" in field.get_lookups()` true and so
FAILS the F2P `assertNotIn`, which is why the clause must state the fallback
rather than unconditional absence.

A non-discriminating control exits 1 just like a real disagreement, so the script
cannot go green on observables that fail to witness the added line. Verified
out-of-band during construction: the check exits 1 against the unpatched
(base_commit) tree, exits 1 when the shadow's `view[name]` write is deleted, exits
1 when that write is changed to `unregistered()` (the over-eager shape), and exits
0 only against the gold-patched tree.
