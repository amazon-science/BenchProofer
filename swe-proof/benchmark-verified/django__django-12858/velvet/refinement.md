# refinement.md — django__django-12858

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`checkOrderingRef` `do` block + the deep `stepWalk`/`orderingRefInvalid` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I; no kind-3 (changed inexpressible op).

There are **NO axioms** in this bundle: the four schema accessors are free
inputs (mapping.md §2/§3), so no row is A-consumed or A-reference, and G-AX is
`skip`. The whole impl region is R/I, mechanically refuted by **G-CONF**
(`conformance_check.py`); the narrative below is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The walk site — `_check_ordering`'s related-reference loop (`django/db/models/base.py:1735-1758`)

Gold hunk (the changed lines):
```
                 except (FieldDoesNotExist, AttributeError):
-                    if fld is None or fld.get_transform(part) is None:
+                    if fld is None or (
+                        fld.get_transform(part) is None and fld.get_lookup(part) is None
+                    ):
                         errors.append(
                             checks.Error( ... id='models.E015' ))
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `cls0 : Model`, seed `initState cls0 = (some cls0, none, false)` | `_cls = cls; fld = None` (loop pre-state) before `for part in field.split(LOOKUP_SEP)` | R | `_cls` ↔ `Option Model` (`None` = off the model graph), `fld` ↔ `Option Field`, the appended-error flag ↔ `Bool`. mapping.md §2. |
| 2 | `while i < parts.length … st := stepWalk … st parts[i]!` (forward fold of `stepWalk` over `parts`) | `for part in field.split(LOOKUP_SEP):` body | I | one loop iteration per part; the `take`-fold computes the same `foldl`. The proof's `walk_take_step` lemma is the per-step unfold. |
| 3 | `if p.isAlias then let f := aliasField m …` | `if part == 'pk': fld = _cls._meta.pk` then the `is_relation` branch | R + I | the alias part resolves through `aliasField` (= `_cls._meta.pk`). `isAlias ↔ part == 'pk'`. Unchanged by THIS patch; present at base_commit. |
| 4 | `else match lookup m p with \| some f => (if f.isRel then some f.relModel else none, some f, flag)` | `else: fld = _cls._meta.get_field(part)`; `if fld.is_relation: _cls = … else: _cls = None` | R + I | on a non-relation field the chain steps off the model graph (`_cls = None`, modeled `none`); on a relation it descends to `relModel`. Unchanged by THIS patch. |
| 5 | `\| none => (some m, last, flag ‖ flagOnUnresolved hasTransform hasLookup last p)` and the `cur = none` arm | `except (FieldDoesNotExist, AttributeError): if fld is None or (fld.get_transform(part) is None and fld.get_lookup(part) is None): errors.append(E015)` | R + I | **the fixed behavior.** A part `get_field` cannot resolve raises `FieldDoesNotExist` (or `AttributeError` once off the graph); `_cls` is unchanged (`some m`) and the reference is flagged unless the part is hosted by `last`. `flagOnUnresolved` models the patched condition exactly: `none ↦ true` (`fld is None`), `some f ↦ !(hasTransform f p) && !(hasLookup f p)` (`get_transform(part) is None and get_lookup(part) is None`). `hasLookup f p ↔ f.get_lookup(part) is not None` — the accessor the patch newly consults. |
| 6 | `return st.2.2` (the final flag) | "an `E015` error was appended for this reference" | R | the modeled observable is exactly *did this reference raise E015* — what the F2P test asserts (`Model.check()` equals `[]`). |

### Why the spec sees the bug (G-DIFF)

`Solution_prepatch.lean` inlines the except-branch decision with the PRE-patch
condition: it flags unless the part is a registered **transform** of `last`
(`!(hasTransform f p)`), with NO `hasLookup` escape hatch. For a part that is a
registered lookup-but-not-transform of `last`, the inlined step returns flag
`true`, while the frozen `stepWalk` (via `flagOnUnresolved`, which also clears on
`hasLookup`) returns `false`. The loop-body invariant
`st = (parts.take …).foldl stepWalk (initState cls0)` therefore becomes
unprovable → `prove_correct` fails on exactly the discriminating clause
(`!(hasLookup f p)`). This is the F2P `test_ordering_pointing_to_lookup_not_transform`
(`test__isnull` ⇒ wrongly invalid pre-patch). G-CONF independently confirms the
buggy shadow diverges from the gold oracle precisely on this scenario
(`test__isnull`: oracle=valid, buggy=invalid).

The prepatch keeps the spec byte-identical (G-DIFF `same_spec`); it fails on the
`stepWalk` loop-body clause, the discriminating content of its bug.

## No kind-3

Every changed op is expressible: the patch is a pure refinement of the
except-branch's boolean invalidity decision over the abstracted accessors
(`hasTransform f p` → `hasTransform f p || hasLookup f p` as the escape hatch).
Nothing inexpressible; no BLOCKED.

## verify(Solution) ⇒ resolved

`checkOrderingRef` verifies only if its output equals `orderingRefInvalid`, whose
`flagOnUnresolved` clears the flag exactly when the unresolved part is a
registered transform OR lookup of the last resolved field (the patched
condition). By R (`_cls ↔ Option Model`, `fld ↔ Option Field`, the four
accessors ↔ the real callees) the verified walk is the gold-patched
`_check_ordering` related-reference walk on every schema; by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ inputs
incl. the F2P scenario. There are no axioms (G-AX skip). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE).
