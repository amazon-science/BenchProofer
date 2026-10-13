# refinement.md — sympy__sympy-23534

Operation-by-operation correspondence between `model.py`'s implementation (the
`symbols_on_sequence` impl region + the deep `expand_entry` / `all_tag` /
`all_nonneg` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by `axiom_check.py`
/ G-AX), or **I** (identical concrete operation). The claim: any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change

Gold hunk (`sympy/core/symbol.py`, the container `else:` branch):
```
     else:
         for name in names:
-            result.append(symbols(name, **args))
+            result.append(symbols(name, cls=cls, **args))

         return type(names)(result)
```

The container branch recurses on each entry but at base_commit fails to forward
the requested output class `cls`, so each recursive call defaults `cls` back to
`Symbol`. The fix forwards `cls=cls`, so every entry is processed under the
caller's requested class.

## What the result looks like (grounding the structural clauses)

The container branch builds **one group per entry** and returns
`type(names)(result)` — the grouped shape the caller deconstructs:

```
symbols(('q:2','u:2'), cls=Function) == ((q0, q1), (u0, u1))   # F2P: [0][0] -> UndefinedFunction
symbols(('aa:d','x:z'))              == ((aa, ab, ac, ad), (x, y, z))   # P2P
symbols(('q:2','x:0'), cls=Function) == ((q0, q1), ())          # null range -> empty group
```

A range entry produces a tuple group of its multiplicity (>= 2 for `'q:2'`); a
null range (`'x:0'`, `'x:c'`) produces an EMPTY group (multiplicity 0); a single
non-range entry produces multiplicity 1. The F2P test reads `[0][0]`, which
requires (a) the result to be grouped one-per-entry and (b) the first entry's
group to be a multi-object subsequence — both modeled below.

## Correspondence table

| # | model.py impl op (`symbols_on_sequence`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| R1 | parameter `names: List[int]` (read-only, `Acc(list_pred(names), 1/2)`), each entry token a non-negative count (`all_nonneg`) | the `names` container of the `else:` branch | R | container of name strings ↔ `List[int]` of opaque entry tokens; an entry's token value is its expansion multiplicity (number of objects it produces — `mapping.md §2`). Read-only ⇒ fractional permission (directive 5). |
| R2 | parameter `cls: int` (class tag) | the `cls` keyword (default `Symbol`) | R | requested output class ↔ integer class tag; `DEFAULT_CLS() == 0` ↔ `Symbol` (mapping.md §2). |
| I1 | `while i < len(names): ... i = i + 1` | `for name in names:` | I | iterate every container entry exactly once, in order. |
| A-reference | `sub = expand_entry(cls, names[i])` — process entry `i` under the requested class, yielding exactly `names[i]` objects all carrying tag `cls` | `symbols(name, cls=cls, **args)` — the recursive call, now forwarding `cls` | A-reference | the per-entry processing is modeled DEEPLY by `expand_entry` (its `Ensures`: `len(Result())==n ∧ all_tag(Result(), cls)`). The real recursive `symbols(name, cls=cls, ...)` reaches the single-name branch, which constructs every object with the SAME `cls` it was passed and produces exactly that entry's multiplicity of objects (`sympy/core/symbol.py:744/782/784`). `axiom_check.py` (G-AX) validates the deep model == the real callee: per entry the multiplicity matches and every leaf has type `type(X(probe))`. The load-bearing transcription: the FIRST argument passed to `expand_entry` is `cls` (the forwarded class), exactly mirroring `cls=cls`. |
| R-group | `res = res + PSeq(grp)` building `res: PSeq[PSeq[int]]`, one group per entry; postcondition `len(Result()) == len(names)` and `len(Result()[k]) == names[k]` | `result.append(symbols(...))` building the per-entry result list, then `return type(names)(result)` | R | the model represents the grouped output `type(names)(result)` as a sequence-of-sequences `PSeq[PSeq[int]]`: group `k` ↔ entry `k`'s own result. A range entry's tuple of `m` objects ↔ a model group of length `m`; a single-name entry's scalar ↔ a model group of length 1; a null range's `()` ↔ a model group of length 0. The grouping is **NOT abstracted away** (it is read by the F2P test via `[0][0]`); it is modeled by the one-group-per-entry shape + per-entry multiplicity clause, which a flat one-object-per-entry implementation cannot discharge. |
| R-class | postcondition `all_tag(Result()[k], cls)` per group, via the `all_tag`/`all_tag_concat` fold and the loop invariant | the cumulative fact that, with `cls` forwarded, every appended group carries `cls` | R | the changed property: every leaf of every group carries the requested class tag. Pinned element-wise over the grouped structure. |
| I2 (proof) | `all_tag_concat`, `nonneg_at` lemmas + the loop invariants | the cumulative facts internal to the loop | I | pure proof bookkeeping (front-fold distribution over concatenation; per-index non-negativity extraction); no repo counterpart, internal to discharging the postcondition. |

## The discriminator (G-DIFF)

The postcondition `Forall k: len(Result()[k]) == names[k] ∧ all_tag(Result()[k], cls)`
holds only if (a) the result is grouped one-per-entry with each entry's
multiplicity AND (b) every produced object carries the *requested* class tag.
`model_prepatch.py` reproduces the bug by passing `DEFAULT_CLS()` (the `Symbol`
default) into the per-entry processing instead of `cls` (mirroring the missing
`cls=cls`), so it builds objects with the default tag and **fails** the loop
invariant `all_tag(res[k], cls)` whenever `cls != DEFAULT_CLS()` — exactly the
case the F2P test exercises (`cls=Function`). The spec senses the bug on
precisely the line the gold patch edits.

## Why a verifying-but-non-resolving implementation is excluded

A flat implementation that appends **one** object per entry (ignoring per-entry
multiplicity) cannot discharge `len(Result()[k]) == names[k]` whenever some
entry's multiplicity `≠ 1` (e.g. the range entry `'q:2'` with multiplicity 2 in
the F2P input) — it verifies neither the grouping shape nor the multiplicity.
An implementation that flattens the groups (loses the per-entry nesting) cannot
discharge the one-group-per-entry shape `len(Result()) == len(names)` together
with the per-group `Result()[k]` structure. Thus the prior `verify ⟹ resolved`
break (a flat `result.append(cls)` impl whose `[0][0]` raises `TypeError`) no
longer verifies: the structure the F2P test reads is now pinned, not abstracted.

## Soundness on null ranges (no over-claim)

Each clause is sound on empty ranges. A null range entry has multiplicity
`names[k] == 0`; then `expand_entry(cls, 0)` returns `[]`,
`len(Result()[k]) == 0 == names[k]`, and `all_tag([], cls)` is vacuously true.
The real callee agrees: `symbols('x:c', seq=True) == ()` and
`symbols(('q:2','x:0'), cls=Function) == ((q0,q1), ())`. The model never claims
`len > 0` (the prior unsound over-claim, removed); it claims the exact per-entry
multiplicity, which is `0` for a null range. `axiom_check.py` exercises this
subdomain explicitly (null-range single entries and containers + null-range
fuzz suffixes).

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed —
*which class flows into the per-entry processing* — is modeled explicitly as
the `cls` argument threaded into `expand_entry` (the A-reference). The grouped
structure the F2P test reads is modeled as `PSeq[PSeq[int]]` (one group per
entry, per-entry multiplicity), not abstracted away. There is no consumed
`@ContractOnly` axiom and no axiom about the function under change.

## verify(model) ⇒ resolved

`symbols_on_sequence` verifies only if (i) the output is grouped one-group-per-
entry with each entry's multiplicity (`len(Result())==len(names)`,
`len(Result()[k])==names[k]`) and (ii) every leaf of every group carries the
requested class tag `cls` (`all_tag(Result()[k], cls)`), which is dischargeable
only by passing `cls` (not the default) into each entry's processing. By R
(container ↔ `List[int]`, class ↔ tag, grouped result ↔ `PSeq[PSeq[int]]`) and
the A-reference (deep `expand_entry` == real single-name branch, G-AX), the
verified impl equals the gold patch's `symbols(name, cls=cls, **args)` recursion
collected into `type(names)(result)`, up to type refinement and the audited
reference. The gold patch resolves (G-RESOLVE). Trust points: refinement
fidelity (this document, G-EQ) and the single A-reference's soundness
(`axiom_check.py`, G-AX).
