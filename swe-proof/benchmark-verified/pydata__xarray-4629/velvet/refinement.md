# refinement.md — pydata__xarray-4629

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineFirst` `do` block over the `store`/`fresh` heap model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs + this narrative are audited by **G-EQ**; the deep-model fidelity is
audited by **G-AX** (`axiom_check.py`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The combine site — the "override" branch of `merge_attrs`

Gold hunk (`xarray/core/merge.py:504`):
```
-        return variable_attrs[0]
+        return dict(variable_attrs[0])
```

The change replaces *returning the first source object directly* (a shared
reference) with *returning a fresh shallow copy* of it. The observable
difference is an **object-identity / aliasing** property: under the fix, mutating
the returned mapping does not affect any source.

| # | Solution.lean impl op (`combineFirst`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `sources : List Handle` | `variable_attrs: list[dict]` | R | each source dict *object* ↔ a `Handle`; distinct objects ↔ distinct handles (mapping.md §2). G-CONF bridges via real `dict` objects. |
| A2 | param `store : Handle → Entries` | the live heap: `store h` = contents of object `h` | R | object → current-contents map (mapping.md §2). Models the mutable state the aliasing property is about. |
| A3 | `store sources.head!` (read first source's contents) | `variable_attrs[0]` (the source dict whose contents are taken) | R + I | `sources.head!` ↔ `variable_attrs[0]`; reading `store head!` ↔ reading that dict's contents (mapping.md §2). The non-empty input is `require sources ≠ []`. |
| A4 | `let result := fresh`; `store := Function.update store fresh (store sources.head!)`; `fresh := fresh + 1` | `dict(variable_attrs[0])` | A-reference + I | the changed copy op is modeled **deeply**: allocate a fresh handle, copy the first source's contents into it, bump the allocator. The ops (`fresh`, `Function.update`, `+1`) are **I** (concrete, transliterated by G-CONF); the claim that this fresh-copy sequence equals the real `dict(...)` constructor's identity+contents+source-frame behaviour is the **A-reference** G-AX validates (mapping.md §3.1). |
| A5 | `return result` (the fresh `Handle`) | `return dict(variable_attrs[0])` | R | the returned object identity ↔ the returned `dict` object. |

### Discriminating content
The behavioural change lives in **freshness of the returned identity**, captured
by the postconditions:

- `ensures result ∉ sources` — the result is its own object, distinct from every
  source. The pre-patch impl returns `sources.head!`, so `result ∈ sources`; the
  clause is unprovable → `Solution_prepatch.lean` **fails** here (G-DIFF).
- `ensures ∀ h ∈ sources, store h = storeOld h` — combining does not mutate any
  source object's contents (the `mut store` frame, directive 5).
- `ensures store result = storeOld (sources.head!)` — the result carries exactly
  the first source's (pre-state) contents (equal contents, grounded in the
  input — directive 8).
- `ensures result = freshOld` ∧ `ensures fresh = freshOld + 1` — allocate
  exactly one fresh object; pins the allocator mechanics so a degenerate
  "allocator" (reuse a live handle / don't advance) cannot satisfy the spec
  (kills the G-MUT `+0` survivor).

Together these are exactly the property the F2P test
`test_merge_attrs_override_copy` checks: after `ds3 = merge([ds1,ds2],
combine_attrs="override")`, setting `ds3.attrs["x"]=2` leaves `ds1.x == 0`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the `dict(...)` shallow copy — is modeled **deeply** (the explicit
allocate-fresh + copy-contents sequence, A4, an A-reference + I), not hidden
behind an axiom about the function under change. There is **no consumed axiom**;
the `axioms` region is empty.

## C. verify(Solution) ⇒ resolved

`combineFirst` verifies only if its returned handle is fresh (`result ∉ sources`,
`result = freshOld`, `fresh = freshOld + 1`), carries the first source's
contents (`store result = storeOld head!`), and leaves every source's contents
unchanged (`store h = storeOld h`). By R (`dict` object ↔ `Handle`, contents ↔
`Entries`, mapping.md §2) the verified op equals `return dict(variable_attrs[0])`
on the tested inputs; by G-AX the deep fresh-copy model equals the real CPython
`dict(...)` (A-reference) on the three observables (identity-distinct,
equal-contents, source-frame-preserved), and the pre-patch direct-return fails
the identity-distinct observable; by G-CONF the R/I transliteration of the
allocate-copy sequence agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited copy callee — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model
fidelity (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
