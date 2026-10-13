# refinement.md — pytest-dev__pytest-5631

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`countSentinelArgs` `do` block plus the deep `hitsMarker`/`sentinelCount` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (axiomatized / deeply
modeled callee — **none here**), or **I** (identical concrete op). EVERY step is
R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The count site — `compat.py:62` (the sentinel-argument counter)

Gold hunk (pre → post):
```
- mock_modules = [sys.modules.get("mock"), sys.modules.get("unittest.mock")]
- if any(mock_modules):
-     sentinels = [m.DEFAULT for m in mock_modules if m is not None]
-     return len([p for p in patchings if not p.attribute_name and p.new in sentinels])
- return len(patchings)
+ mock_sentinel = getattr(sys.modules.get("mock"), "DEFAULT", object())
+ ut_mock_sentinel = getattr(sys.modules.get("unittest.mock"), "DEFAULT", object())
+ return len([p for p in patchings
+             if not p.attribute_name
+             and (p.new is mock_sentinel or p.new is ut_mock_sentinel)])
```

| # | Solution.lean impl op (`countSentinelArgs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entries : List ArgEntry` | `patchings = getattr(function, "patchings", None)` then iterated | R | the patch list ↔ `List ArgEntry`, element-wise (mapping.md §2); a function with no `patchings` ↔ `[]`, on which both sides return 0. |
| A2 | `markerA`, `markerB` (two opaque ids) | `mock_sentinel`, `ut_mock_sentinel` resolved via `getattr(..., "DEFAULT", object())` | R | the two sentinels as object identities (mapping.md §1). When a mock module is absent the real code installs a *fresh* `object()` whose id no `p.new` shares — the entry simply never matches, exactly as `valueId == marker` is false for an absent marker. |
| A3 | `hitsMarker e = (!e.isAttribute) && (e.valueId == markerA \|\| e.valueId == markerB)` | the comprehension predicate `not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)` | I | identical concrete predicate, decided by **identity**: `not attribute_name` ↔ `!isAttribute`; `p.new is s` ↔ `valueId == marker`. Identity inspects no value contents, so it is total — never aborts (the fix). G-CONF transliterates this op directly. |
| A4 | result `n = sentinelCount entries` computed by the backward `while` fold over `contrib` | `len([p for p in patchings if <predicate>])` | I | the fold sums `contrib e ∈ {0,1}` over the list = the comprehension's length. The fold ops (`contrib`, `+`, the loop) are concrete, transliterated by G-CONF. |
| A5 | result `err = false` (unconditionally; the spec `ensures out.err = false`) | the patched function returns an `int` and never raises on these inputs | I | the identity predicate evaluates no `__eq__`, so no input — array-like included — can make it raise. This is the discriminating clause (see below). |

## B. The bug the spec sees — pre-patch vs post-patch

Pre-patch, `p.new in sentinels` evaluates `p.new == sentinel`, invoking
`p.new.__eq__`. For an array-like `p.new` (problem statement: `np.array([...])`,
or the F2P `NumpyLike` whose `__eq__` raises) the comparison aborts with
`ValueError`, so the whole collection raises.

`Solution_prepatch.lean` reproduces exactly this: its impl tests the non-attribute
entries by value equality and, for an entry whose equality is **not total**
(`!e.eqTotal`), sets `err := true`. It therefore **cannot** prove the frozen
clause `ensures out.err = false` — `prove_correct` fails with the unsolved goal
`⊢ err = false` on the `ensures_2` postcondition (G-DIFF). The post-patch impl
decides membership by identity (`hitsMarker`), never sets `err`, and verifies.

The discriminating input is precisely the F2P case
(`test_mock_sentinel_check_against_numpy_like`): a single non-attribute entry
whose replacement value has a non-total `__eq__` and whose identity is *not* a
sentinel. Post-patch: counted-membership is `false`, no error, count 0.
Pre-patch: equality membership aborts.

## C. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom and no A-reference deep
model**: the function under change calls no unchanged external operation — it
does attribute-name truthiness, object-identity comparison, and a length count,
all modeled concretely. `axiom_check.py` is consequently a documented no-axiom
pass. The one operation that genuinely *changed* — membership-by-equality →
membership-by-identity — is modeled directly as the `valueId == marker` identity
test (step A3, an **I** op), with the abort-on-non-total-equality behaviour of
the old path captured by the prepatch's `eqTotal` branch.

## D. verify(Solution) ⇒ resolved

`countSentinelArgs` verifies only if (i) `out.n` equals the identity-decided
count `sentinelCount entries` (A3/A4) and (ii) `out.err = false` for every input
(A5). By R (`patchings ↔ List ArgEntry`, sentinels ↔ markers, id ↔ `valueId`)
the verified scan equals the patched `num_mock_patch_args` on the tested inputs;
by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed inputs (including array-like values). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms to trust.
