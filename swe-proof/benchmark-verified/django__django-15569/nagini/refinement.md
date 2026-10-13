# refinement.md — django__django-15569

The operation-by-operation correspondence between `model.py`'s implementation
(the `remove_registration` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real operation by `axiom_check.py` /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — `RegisterLookupMixin._unregister_lookup`

Gold hunk (`django/db/models/query_utils.py:212-219`):
```
     def _unregister_lookup(cls, lookup, lookup_name=None):
         if lookup_name is None:
             lookup_name = lookup.lookup_name
         del cls.class_lookups[lookup_name]
+        cls._clear_cached_lookups()
```

The model spells out the post-fix operation over the local backing store `store`
(the target's own `class_lookups`), the enclosing registration layer `inherited`
(what the levels above it provide, merged by the real `merge_dicts`), the
derived resolved view `view` (what `cls.get_lookups()` reports), and the SAME
PAIR ONE LEVEL OUT for an arbitrary component `R` that reads through `cls`:
`reader_view` (what `R.get_lookups()` reports) and `reader_rest` (what `R`'s own
remaining levels provide once `cls`'s store is set aside), mapping.md §1–2:
```python
store[name]       = unregistered()      # del cls.class_lookups[lookup_name]
view[name]        = inherited[name]     # cls._clear_cached_lookups(), own entry
reader_view[name] = reader_rest[name]   # ... and its subclasses() walk
```
The third line is not redundant with the second. `_clear_cached_lookups` is
```python
@classmethod
def _clear_cached_lookups(cls):
    for subclass in subclasses(cls):
        subclass.get_lookups.cache_clear()
```
(`query_utils.py:196-199`, `subclasses` at `query_utils.py:26-29`), and
`get_lookups` is `@functools.lru_cache(maxsize=None)` on the classmethod
(`query_utils.py:157-163`): every class in the hierarchy is a distinct cache key
holding a distinct merged dict. Evicting `cls`'s entry alone therefore satisfies
`view[name] == inherited[name]` and leaves every subclass still answering reads
from its own stale dict — which is precisely the state
`custom_lookups.tests.LookupTests.test_lookups_caching` fails on, since it
registers "exactly" on `ForeignObject` and then asserts
`assertNotIn("exactly", field.get_lookups())` for a `ForeignKey` field
(`tests/custom_lookups/tests.py:315-325` + test_patch). Step 9 below is that
half of the added line.

| # | model.py impl op (`remove_registration`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `store: Dict[int,int]` | `cls.__dict__["class_lookups"]` (the per-class registered-lookup dict the removal deletes from) | R | local backing store str→Lookup ↔ `Dict[int,int]` name-token→identity-token; "name registered locally" ↔ `store[name] != unregistered()` (mapping.md §2). |
| 2 | param `view: Dict[int,int]` | the value memoised by the lru_cache classmethod `get_lookups` — the effective mapping a read observes | R | the derived resolved view str→Lookup ↔ `Dict[int,int]`; "a read of name resolves" ↔ `view[name] != unregistered()` (mapping.md §2). `view` models the EFFECTIVE post-recompute answer, not raw cache internals. |
| 3 | param `inherited: Dict[int,int]`, held read-only under `Acc(dict_pred(inherited), 1/2)` | `merge_dicts` over the `class_lookups` of the classes `cls.get_lookups()` merges, minus `cls` — the fallback answers a read of `cls` uses | R | same tokenization; `inherited[name] == unregistered()` ↔ nothing in `cls`'s own read-fallback range registers that name. The range is NOT unconditionally `inspect.getmro(cls)[1:]`: `get_lookups` is overridable and `ForeignObject` (`related.py:858-864`) truncates it, so an ancestor above the cut is in the MRO yet invisible to a read. The real removal touches only `cls`'s own dict, so the enclosing layer is unchanged by the operation — hence the fractional (read-only) permission, which also forbids any verifying impl from writing it. |
| 4 | param `name: int` | `lookup_name` | R | lookup name `str` ↔ `int` token; only equality/inequality observed (mapping.md §2). |
| 5 | `store[name] = unregistered()` | `del cls.class_lookups[lookup_name]` | R | "mark name unregistered in the local backing store" ↔ key deletion from `class_lookups`; Nagini bans dict key deletion, so absence is modelled as the `unregistered()` value (mapping.md §2). This op is present in BOTH the gold and the pre-patch code. |
| 6 | `view[name] = inherited[name]` | `cls._clear_cached_lookups()` | A-reference | the cache invalidation is modelled DEEPLY as "a read of the removed name now reports exactly what the enclosing registration layer provides" (and other names unchanged). `_clear_cached_lookups` evicts the whole `get_lookups` lru_cache for the class and its subclasses; the next read re-enters `cls.get_lookups()`, which recomputes `merge_dicts` over the classes THAT method actually merges — `inspect.getmro(cls)` for the base implementation, but only the truncated prefix `bases[: bases.index(ForeignObject) + 1]` for `ForeignObject` and its subclasses (`related.py:858-864`) — so the removed name resolves to whatever the levels inside that read range still register for it — nothing when none does (`inherited[name] == unregistered()`, the case both F2P tests exercise), and the ANCESTOR's lookup class when one does. Every other name resolves exactly as before. There is NO consumed axiom; the deep model is validated == the real `_clear_cached_lookups` + lru_cache recompute by `axiom_check.py` (G-AX) over both families, and mechanically by G-CONF against the called patched function on 100 022 real states, 34 675 of them with an ancestor registering the removed name -- including 5 shapes played on the real classes whose `get_lookups` override truncates the merge range, 2 of which would have disagreed under a full-MRO binding of `inherited`: mapping.md §3. This is the op the gold patch ADDS. |
| 7 | param `reader_view: Dict[int,int]`, held at FULL permission | `R.get_lookups()` for an arbitrary class `R` whose read range includes `cls` — a DIFFERENT `functools.lru_cache` entry from `cls`'s, holding a different merged dict | R | same tokenization as `view`. The reader is universally quantified by being a PARAMETER: the contract must hold for every dictionary pair the precondition admits, hence for every component through which the registry can be read, at any depth. Held at full permission because the real invalidation does move it (the `subclasses(cls)` walk), which also makes "leave every reader's answers alone" unverifiable. |
| 8 | param `reader_rest: Dict[int,int]`, held read-only under `Acc(dict_pred(reader_rest), 1/2)` | `merge_dicts` over the `class_lookups` of the classes `R.get_lookups()` merges, with `cls` SET ASIDE — what `R`'s own remaining levels provide | R | same tokenization; `reader_rest[name] == unregistered()` ↔ nothing in `R`'s read range other than `cls` registers that name. `R`'s range is probed exactly as `cls`'s is, so the `ForeignObject` truncation (`related.py:858-864`) is honoured on the reader side too. The real removal touches only `cls.class_lookups`, so this is unchanged by the operation — hence the read-only permission, which additionally forbids a verifying impl from bringing the reader's answers in line by editing the READER's own registrations instead of invalidating its view. |
| 9 | `reader_view[name] = reader_rest[name]` | the `for subclass in subclasses(cls): subclass.get_lookups.cache_clear()` loop inside `cls._clear_cached_lookups()` (`query_utils.py:196-199`) | A-reference | the SECOND half of the added line, modelled deeply and for every reader at once. Because `get_lookups`' lru_cache is keyed per class, evicting `cls`'s entry leaves each dependent class's merged dict in place; only this walk reaches them, and after it the reader's next read re-enters `R.get_lookups()`, which recomputes `merge_dicts` over ITS OWN range and no longer finds the name in `cls.class_lookups` — so the read reports exactly what the reader's remaining levels provide: nothing when none of them registers it (the case `test_lookups_caching` asserts), and that level's lookup class when one does. There is NO consumed axiom; validated == the real code by `axiom_check.py` (G-AX), which exercises a THIRD patch state — a COMPONENT-ONLY removal that brings only `cls`'s own memo in line — on 513 sequences (3 of them on the real `ForeignObject`/`ForeignKey` pair) and asserts that it satisfies steps 5 and 6 yet STILL leaves a read through the subclass reporting the removed lookup; and mechanically by G-CONF against the called patched function, whose component-only mutation control must disagree with the shadow on every input where the reader reports `cls`'s local registration and its own remaining levels provide something else. mapping.md §1, §3. |

The discriminating content of the change — *invalidate the derived view on
removal so a subsequent read stops answering from the stale mapping and instead
reports the remaining registration levels, through the component itself AND
through every component that reads via it* — lives in steps 6 and 9. It is sensed
by the postconditions `view[name] == inherited[name]` and
`reader_view[name] == reader_rest[name]` of `remove_registration`. The
pre-patch code omits the cache clear entirely (only the delete, step 5);
`model_prepatch.py` reproduces that (the impl region performs only
`store[name] = unregistered()`) and **fails** exactly those postconditions
(G-DIFF: `Assertion (view[name] == inherited[name]) might not hold`). The
backing-store deletion (clause `store[name] == unregistered()`) and the frame
clauses still verify in the prepatch — the failure is sharply localized to the one
fixed behaviour (the cache clear).

**Why the reader clause is a separate obligation.** A removal that performs step 6
and not step 9 is a reachable, non-strawman implementation: it is what an
invalidation that clears one lru_cache entry rather than walking
`cls.__subclasses__()` does, and it satisfies every other clause in the contract
(`store[name] == unregistered()`, `view[name] == inherited[name]`, and every frame
clause). It nevertheless leaves `"exactly" in field.get_lookups()` TRUE for a
`ForeignKey` field and so FAILS the F2P `assertNotIn`. Without step 9 the spec
would admit it — that admission is the refutation this bundle was repaired to
close, and it is a frozen reject case in `properties.py`
(`weak-reader-blind-component-only`, `weak-reader-blind-via-temp` — the exact
shape of the refuting attack, which reached the same post-state through a local
temporary — plus `weak-reader-frame-other-clobber`, `weak-write-reader-rest` and
`weak-reader-echo-incoming`) as well as the third mutation
control in `conformance_check.py` and the third patch state in `axiom_check.py`.
Conversely the clause is not over-strong: it says the reader reports what ITS OWN
remaining levels provide, not that the name stops resolving for the reader, so a
reader that registers the name itself, or inherits it from a level other than
`cls`, keeps resolving it — which is what the real recompute does.

**Why the clause is the fallback and not unconditional absence.** Stating step 6
as `view[name] == unregistered()` would be an over-strong claim: the recomputed
view cannot drop a name the class's own read-fallback range still registers, so
whenever a class in that range registers the removed name the gold patch produces
`view[name] == inherited[name] != unregistered()` and a spec demanding absence
would be unsatisfiable by the real code. (Note this is stated over the FALLBACK
RANGE, not the full MRO: for `ForeignObject` and its subclasses the truncated
`get_lookups` genuinely does drop a name that an ancestor above the cut registers,
and there `inherited[name] == unregistered()` — which is why binding `inherited`
to the full MRO would invert the claim on that family) (G-CONF disagreement, boundary case 11:
oracle `view[name]` = the ancestor's identity token, `unregistered()` claimed).
Nor is the weaker clause a licence for laxity in the other direction: an impl that
forces absence unconditionally corresponds to the real patch
`del class_lookups[n]; class_lookups[n] = None; _clear_cached_lookups()`, which
leaves `"exactly" in field.get_lookups()` TRUE and so FAILS the F2P
`assertNotIn`. That impl is a frozen reject case
(`weak-view-unconditional-unresolve`) and does not verify.

## Frame fidelity

The frame — that the operation disturbs only the affected name's resolution —
is enforced IN THE SPEC at two levels:

1. **Per-key witness**: a representative unrelated name `other_name()` keeps
   its exact state — `store[other_name()] == Old(store[other_name()])` and
   `view[other_name()] == Old(view[other_name()])`.
2. **Whole-structure quantified frame**: four `Forall(int, ...)` postconditions
   pin EVERY name `k != name` — its membership in each structure is unchanged
   (`(k in store) == Old(k in store)`, likewise for `view`) and, when present,
   its bound state is unchanged (`store[k] == Old(store[k])`, likewise for
   `view`). Explicit triggers (`[[k in store]]`, `[[store[k]]]`, …) keep the
   quantifiers tractable, and the clauses are empirically DISCRIMINATING on
   Nagini 1.2.0: an impl that additionally rebinds any unrelated key in either
   structure fails verification on precisely these clauses, while
   behaviourally-equal reshapes (write-order swap, idempotent repeat of the
   same-key writes) still verify.

An earlier revision of this bundle carried only level 1 and claimed the
whole-structure frame followed from the impl skeleton performing no other
write. That claim was a property of the reference impl, not of the frozen
spec: a same-spec impl adding an extra unrelated-key store write verified yet
its faithful refinement (removing an additional genuinely-registered name from
the backing store) does not resolve. The quantified frame (level 2) closes that
gap in the spec itself — no faithful refinement of any impl verifying against
this spec can disturb any other name. G-AX confirms the real cache
invalidation (clear + lazy recompute) leaves every other name resolving to the
same lookup, matching the quantified view frame.

3. **Read-only enclosing layer**: `inherited` is held under
   `Acc(dict_pred(inherited), 1/2)`, a fractional permission that admits reads and
   forbids writes. This is frame fidelity for the third carrier: the real removal
   deletes from `cls`'s own `class_lookups` and never touches an ancestor's, so an
   impl that mutated the enclosing layer would have no faithful refinement. The
   clause is discriminating, not decorative — the frozen reject case
   `weak-write-inherited` performs the gold writes plus `inherited[name] =
   unregistered()` and fails verification for insufficient permission.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the cache invalidation after the delete — is modelled
**deeply** and in BOTH its halves (the spelled-out `view[name] = inherited[name]`
for the class's own cache entry and `reader_view[name] = reader_rest[name]` for the
`subclasses(cls)` walk), not hidden behind an axiom about the function under
change. There is no consumed `@ContractOnly` axiom; the two A-tagged steps (6 and
9) are **A-references** whose deep model `axiom_check.py` validates == the real
`_clear_cached_lookups` + memoised `get_lookups` recompute, on hierarchies in both
families and against all three patch states (gold, pre-patch, component-only).

## verify(model) ⇒ resolved

`remove_registration` verifies only if, after the operation, the removed name is
no longer registered in the local store (step 5; `store[name] ==
unregistered()`) AND a read of the removed name reports exactly what the
enclosing registration layer provides (step 6; `view[name] == inherited[name]`)
AND a read *through a dependent component* reports exactly what THAT component's
own remaining levels provide (step 9; `reader_view[name] == reader_rest[name]`,
with the reader's other names framed), while the representative unrelated name
still resolves to its exact item (frame) and neither the enclosing layer nor the
reader's own registrations are touched. By R (`class_lookups` ↔ `store`, the
levels `cls.get_lookups()` actually merges minus `cls` itself — the full MRO tail
for the base implementation, the `ForeignObject`-truncated prefix for that family
(`related.py:858-864`) — ↔ `inherited`, the memoised lookup view ↔ `view`,
deletion ↔ `unregistered()`-marking) the verified operation equals the gold
`del cls.class_lookups[lookup_name]; cls._clear_cached_lookups()` on the
observable resolution; by G-AX the deep cache-invalidation model equals the real
`_clear_cached_lookups` + lru_cache recompute at BOTH levels (the A-references,
steps 6 and 9 — including 513 sequences in which the component-only state
satisfies steps 5 and 6 and is still caught by step 9), and by
G-CONF the contract-stripped impl region agrees with the CALLED patched function
on 100 022 reachable states with zero disagreements. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited A-references — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
