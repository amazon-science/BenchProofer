# refinement.md — scikit-learn__scikit-learn-14496

The operation-by-operation correspondence between `model.py`'s implementation
(the `neighborhood_size` impl region and the deep floor loop) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed** / **A-reference**), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The conversion — `int(max(2, value * n_samples))`

Gold code hunk (the three sites are byte-identical; one shown):
```
-        min_samples = max(2, min_samples * n_samples)
+        min_samples = max(2, int(min_samples * n_samples))
```
(The patch wraps the *product* in `int(...)`; the product itself — a float64
multiplication — is **unchanged** by the patch and sits outside the model
boundary (mapping.md §0). The model takes that repo-computed double `scaled`
as its input and computes the whole-number floor of `max(2.0, scaled)`, which
equals the gold `max(2, int(scaled))` on every non-negative double — note D.)

| # | model.py impl op (`neighborhood_size`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `scaled: float` | the float64 product `min_samples * n_samples` / `min_cluster_size * n_samples` on the `value <= 1` branch, exactly as the interpreter computed it | R | **exact injection** of the repo's double into the interpreted-real carrier (`--float-encoding=real`); no value is altered and the model never re-multiplies, so float64 rounding of the upstream multiply (unchanged by the patch) is inherited identically by model and repo (mapping.md §0, §2). The admitted range `scaled > 0` comes from `_validate_size` + the branch guard (mapping.md §2, §4). |
| A2 | `clamp_low(scaled)` = `max(2.0, …)` | `max(2, …)` | I/R | identical concrete `max` against the floor of two; integer `2` ↔ real `2.0` (mapping.md §2). |
| A3 | the floor loop returning a whole `float` with `Result() ≤ clamp_low(scaled) < Result()+1` and `is_whole(Result())` | `int(...)` (the wrap) | A-reference | the changed operation is modelled **deeply**: the loop spells out `floor(max(2.0, scaled))`. There is **no consumed `int`/`floor` axiom** — the proof depends on no `@ContractOnly`. The deep model is validated **== the real `int(max(2, scaled))` on the SAME repo-computed double** out-of-band by `axiom_check.py` (G-AX): for a non-negative real `v`, Python's `int(v)` truncates toward zero, i.e. equals `floor(v)`, which is exactly what the loop computes (note D ties the two `int`-placements). |

The discriminating content of the change — the result must be a **whole number**
— lives in `is_whole(Result())` (model) ⇔ the `int(...)` wrap (real). The
pre-patch left `max(2, value * n_samples)` as a possibly-fractional value;
`model_prepatch.py` reproduces that (`return clamp_low(scaled)`) and **fails**
the postcondition `is_whole(Result())` (a fractional product such as
`0.08 * 31 = 2.48` is not whole) — exactly the spec sensing the change
(G-DIFF). The floor-bound clauses `Result() ≤ clamp_low(scaled) < Result()+1`
additionally pin the *value* so the result cannot be any other whole number
(e.g. a ceiling or a round): they forbid `2.48 → 3`.

## B. The three sites (multi-site, one modeled function)

All three gold hunks (`min_samples` in `compute_optics_graph`, and `min_samples`
+ `min_cluster_size` in `cluster_optics_xi`) are the **identical** operation
`int(max(2, x * n_samples))` (mapping.md §3). Every step A1–A3 is therefore the
same R/I/A-reference correspondence at each site; a single contracted function
`neighborhood_size` (taking each site's already-computed scaled value) is the
faithful skeleton of all three, and a single `model_prepatch.py` is a
sufficient differential witness because the three sites share one fixed
behaviour (the missing whole-number reduction). No site needs its own
`model_prepatch_<k>` — there is exactly one independently-observable fixed
behaviour.

The remaining gold hunks are doc-string-only (parameter descriptions of
`min_samples`/`min_cluster_size` in `compute_optics_graph`, `cluster_optics_xi`,
`_xi_cluster`, and the `OPTICS` class). They carry no modeled operation (no
tag); they are non-semantic and do not affect `resolved`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — wrapping the scaled, clamped value in `int(...)` — is modelled
**deeply** (the verified floor loop, A3), not hidden behind an axiom about the
function under change: there is **no consumed `int`/`floor`/`max` axiom**. The
supporting `max` is spelled out (`clamp_low`, A2); the upstream float64
multiplication is unchanged by the patch and lies outside the model boundary
(A1, mapping.md §0). The only kind-A item is the A-reference of A3, which G-AX
validates the deep model against.

## D. Why `max(2, int(s))` (gold) == `floor(max(2.0, s))` (model), and why the
## model's input is the repo's double

Let `s` be the float64 product the repo computed (`s ≥ 0` on the admitted
domain). The gold wraps it in `int`: `max(2, int(s))`. The model floors the
*clamped* value: `floor(max(2.0, s))`. These coincide for every non-negative
double `s`:
- If `s ≥ 2`: `int(s) = floor(s) ≥ 2`, so `max(2, int(s)) = floor(s) =
  floor(max(2, s))` (the clamp is inert).
- If `s < 2`: `int(s) ∈ {0, 1}` (`s ≥ 0`), so `max(2, int(s)) = 2`; and
  `floor(max(2.0, s)) = floor(2.0) = 2`.
Both give the same whole number, `2` when the product is below two and the
truncated product otherwise. `axiom_check.py` checks this equality directly
(both placements of `int`) on boundary + F2P + fuzz inputs, **feeding both
sides the same repo-computed double**.

The model-boundary point (the earlier G-PANEL-2 finding, now fixed): float64
can round the product *across* a whole number. `0.11165523996082272 * 1021`
rounds UP to exactly `114.0`, so the repo computes `int(114.0) = 114`, while
the *exact rational* product is strictly below `114` (its true floor is
`113`). A model that re-multiplied in exact real arithmetic would therefore
disagree with the repo on such inputs. This model does **not** re-multiply:
its input IS the repo's double (`114.0` here), so it returns `114` exactly as
the repo does. `axiom_check.py` pins this fixture explicitly and fuzzes
near-whole doubles (`nextafter` neighbours of whole values).

## E. verify(model) ⇒ resolved

`neighborhood_size` verifies only if its output is a whole number (A3 /
`is_whole`) equal to `floor(max(2.0, scaled))` (the floor-bound clauses). By R
(the repo's double injected exactly; the three sites are the same operation)
and by note D, the verified result equals the gold
`int(max(2, value*n_samples))` at every site — on every double the repo can
produce, including whole-rounded products; by G-AX the deep floor model equals
the real `int(...)` (A-reference). The F2P test (`test_extract_xi`) feeds
`min_samples=0.1`, `min_cluster_size=0.08` on 31 samples: the repo's doubles
are `3.1` and `2.48`; the gold yields `int(max(2, 3.1)) = 3` and
`int(max(2, 2.48)) = 2`, matching the integer-parameter run it is asserted
equal to; the model yields the same `3` and `2` (`floor` of `3.1`/`2.48`), and
the pre-patch's `3.1`/`2.48` (non-whole) crashes the integer-only neighbour
search — the very `TypeError` the issue reports. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the single audited A-reference — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
