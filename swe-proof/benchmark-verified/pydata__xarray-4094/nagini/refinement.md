# refinement.md — pydata__xarray-4094

The operation-by-operation correspondence between `model.py`'s implementation
(the `to_unstacked` impl region, plus the live axioms `carried`, `shared_value`,
`assemble`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement) / **A-consumed** (the proof uses this axiom's contract) / **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reconstruction — `to_unstacked_dataset` (`xarray/core/dataarray.py:1901`)

Gold hunk (body line 1964):
```
- data_dict[k] = self.sel({variable_dim: k}).squeeze(drop=True)
+ data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
```

| # | model.py impl op (`to_unstacked`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `n, data, resid` | `self` (the stacked `DataArray`) + the `for k in variables` loop over the MultiIndex level | R | the stacked array is abstracted to `n` members `0..n-1` with per-member value `data[k]` and residual coordinate value `resid[k]` (mapping.md §2). |
| A2 | `discard = True`; `selected = data[i-1]` appended to `data_dict` | `self.sel({variable_dim: k}, drop=True).squeeze(drop=True)` storing into `data_dict[k]` | A-consumed (`carried`/`shared_value`) + R | the selection-and-collapse is the unchanged callee: the patch passes `drop=True`, modeled by `discard = True`, so the slice's carried annotation is `carried(True, resid[k]) = shared_value()` (no distinguishing position). The data value is copied verbatim (the `ToSeq(data_dict)==ToSeq(data).drop(i)` invariant). |
| A3 | `result = assemble(data_dict, resid, discard)` | `return Dataset(data_dict)` | A-consumed (`assemble`, `combined_collection`) | the `Dataset` constructor is the unchanged callee: it `Requires(all_equal(carried_seq(discard, resid)))` over the SAME `discard` and the members' distinct positions (`MergeError` otherwise), `Ensures` the data is recovered verbatim, AND grants the `combined_collection` token on its output. With `discard==True` every slice carries `shared_value()`, the guard holds, the merge succeeds, `ToSeq(Result())==ToSeq(data)` (the roundtrip identity), and `result` holds the token that `to_unstacked`'s postcondition requires. The token makes this step MANDATORY: there is no other producer of the token, so no verifying impl can skip the merge. |
| A4 | `return result` | the returned `Dataset` | R | the reconstructed collection ↔ the result `List[int]` of recovered per-member values (mapping.md §2). |

The discriminating content of the change — passing `drop=True` to the per-member
selection so the residual stacked coordinate is **not** left behind — lives in
the single `discard` knob threaded through the whole reconstruction:
`discard = True` (model) ⇔ the literal `drop=True` argument of `.sel` (real). The
pre-patch code omits `drop` (defaults to `False`); `model_prepatch.py` reproduces
that (`discard = False`) and **fails** the `assemble` precondition
`all_equal(carried_seq(discard, ToSeq(resid)))`: with `discard==False` and members
at distinct positions (`distinct_residuals`, `n >= 2`), each slice carries its
own distinct position, so the carried annotations are NOT all-equal, the merge is
rejected — exactly the `MergeError: conflicting values for variable 'y'` the issue
reports (G-DIFF).

## B. Why the spec admits NO wrong implementation (the soundness fix)

There is a **single** selection knob `discard`, and it governs BOTH what each
slice carries (`carried(discard, .)`) AND the merge guard `assemble` checks
(`all_equal(carried_seq(discard, resid))`). The guard is over the members' real
positions `resid`, which `assemble` REQUIRES to be `distinct_residuals`. Hence:

- An impl passing `discard=False` (the bug) fails the guard
  `all_equal(carried_seq(False, resid))` — distinct positions are not all-equal.
- An impl trying to fabricate an all-equal position list to slip past the guard
  fails the `distinct_residuals(resid)` precondition.
- **An impl that builds the verbatim values and returns them WITHOUT the merge**
  (the re-audit's named counterexample `atk_7`) fails the postcondition
  `combined_collection(Result(), ToSeq(resid))`: that abstract token is
  granted ONLY by `assemble`'s postcondition and is unforgeable (Nagini rejects
  `Fold` of an abstract predicate; an object not produced by `assemble` lacks the
  token). An impl that calls `assemble` to obtain the token but then returns a
  different/fresh list (`atk_fresh`), or a value-identical list built alongside
  the merged one (`atk_launder`), also fails — the token is keyed by the OBJECT
  `assemble` returned (a `List[int]` reference, not a value sequence), so it
  sits on `assemble`'s own output and on nothing value-equal to it. (An earlier
  revision keyed the token by `ToSeq(Result())`; a Viper predicate is value-
  keyed over its arguments, so a value-equal list that never went through the
  merge could mint the token via a side call to `assemble` and discharge the
  postcondition — the `atk_launder` hole. Reference-keying closes it.)
- The only verifying choice is `discard=True` with the result routed through
  `assemble`, which by A2/A3 refines to `.sel(..., drop=True)` +
  `return Dataset(data_dict)` = the gold patch = resolves.

This closes BOTH the v1 hole (prior free `keep` — fixed by the single-`discard`
guard + `distinct_residuals`) and the re-audit's residual hole (the merge was
OPTIONAL because the value-only postcondition is dischargeable without it). The
key fact: the per-member values are identical whether or not the merge happens
(the bug is "raises vs returns", not "wrong value"), so no value-level
postcondition can separate gold from a merge-skipping impl; the
`combined_collection` capability token forces the merge onto the result path.
Re-checked against `atk_7` (named CE), `atk_fresh`, `atk_launder` (side-call
mint + value-equal return), the prepatch (`discard=False`), `atk_4` (wrong
data), `atk_empty` — all FAIL to verify; the gold-shaped impl still verifies
(non-vacuity). The token is a capability, NOT an answer-key oracle: it carries
no value the impl can echo.

Every step above is R, A-consumed, or I — no kind-3 (unexpressible-changed-op)
step. The operation that genuinely *changed* (the `drop` argument) is captured by
the `carried`/`shared_value` axioms evaluated at the discard the impl chooses; its
downstream effect (whether the merge is rejected) is captured by the `assemble`
axiom's `all_equal(carried_seq(discard, resid))` precondition. All axioms are
about **unchanged** community callees (`DataArray.sel`/`.squeeze`, the `Dataset`
constructor/merge); none axiomatizes the function under change.

## C. verify(model) ⇒ resolved

`to_unstacked` verifies only if it copies each member's value verbatim (A2
invariant) AND its result holds `combined_collection` — which only `assemble`'s
own output object carries (reference-keyed) — so it must reach a **successful**
`assemble` and return that very output; i.e. it discharges `all_equal(carried_seq(discard, ToSeq(resid)))` over
the distinct member positions (A3). That holds only when `discard == True`, i.e.
only when the per-member selection discarded the residual annotation
(`discard == True`, the patch's `drop=True`). By R the verified reconstruction equals
`Dataset({k: self.sel({variable_dim: k}, drop=True).squeeze(drop=True)})` on the
tested single-position-axis input; by G-AX the axioms match the real callees
(`carried(False, .) = position`, `carried(True, .) = shared_value()`; the
`Dataset` merge rejects conflicting kept residuals and recovers the data verbatim
otherwise — validated in the pinned container). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
