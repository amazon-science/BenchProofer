# refinement.md — scikit-learn__scikit-learn-14496

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the two `do` blocks plus the deep `asAbsoluteCount` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated ==
real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs + this narrative by **G-EQ**. `patch.diff` is the gold patch
**verbatim** (G-RESOLVE).

The behaviour-changing hunks of the gold patch are three textually-identical
edits (the rest of the patch is docstring-only):
```
- min_samples       = max(2, min_samples       * n_samples)
+ min_samples       = max(2, int(min_samples   * n_samples))     # optics_.py:440, 622
- min_cluster_size  = max(2, min_cluster_size  * n_samples)
+ min_cluster_size  = max(2, int(min_cluster_size * n_samples))  # optics_.py:627
```
i.e. add `int(...)` — truncate the scaled fraction to an integer count.

## A. Site #1 — `compute_optics_graph` conditioning (`optics_.py:439-440`)

| # | Solution.lean impl op (`conditionSizeParameter`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `value : Rat`, `population : Nat` | `min_samples`, `n_samples` | R | numeric ↔ `Rat`, `int` ↔ `Nat` (mapping.md §2). |
| A1b | param `scaled : Rat` with `require scaledFromPopulation scaled value population` | the sub-expression `min_samples * n_samples`, evaluated in IEEE double | R | the scaling is NOT the changed op and is NOT exactly representable in `Rat` — its rounding can cross an integer boundary in either direction (mapping.md §2.1). Modeled as an input constrained by the `2^-53` relative band IEEE multiplication guarantees, so the contract applies to the real product rather than to an idealized one. |
| A2 | `if value ≤ 1 then …` | `if min_samples <= 1:` | I | same branch guard, same comparison. |
| A3 | `size := ((max 2 (Rat.floor scaled)) : Int)` | `min_samples = max(2, int(min_samples * n_samples))` | A-reference + I | the changed op — the `int(·)` the patch ADDS — is modeled **deeply**: `Rat.floor scaled` ⇔ `int(<the machine product>)`, exact on a non-negative value (mapping.md §3.1, G-AX leg 2, zero tolerated divergences), `max 2` ⇔ `max(2, …)`. No consumed axiom for the op under change. |
| A4 | else branch leaves `size := value` | (no edit: `min_samples` unchanged when `> 1`) | I | identity on the absolute-count path. |
| A5 | return `size : Rat` | `min_samples` (now `int`) flows on to `NearestNeighbors(n_neighbors=…)` | R | the result is the integer count the downstream consumer requires; the bug was a non-integral residue reaching that consumer. |

`Solution_prepatch.lean` reverts A3 to `max 2 scaled` (no `Rat.floor`) and
**fails** `out = asAbsoluteCount value scaled` on exactly
`2 ⊔ scaled = ↑(max 2 scaled.floor)` (G-DIFF) — the missing truncation. Note the
discriminator is unchanged by the faithfulness repair: hoisting the scaled value
moved the *unchanged* scaling out of the model and left the *changed* truncation
pinned exactly where it was.

## B. Site #2 — `cluster_optics_xi` conditioning (`optics_.py:619-627`)

| # | Solution.lean impl op (`resolvePairedSizes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | condition `primary` from `value` via the A3 op | `if min_samples <= 1: min_samples = max(2, int(min_samples*n_samples))` | A-reference + I | same deep model as A3, first parameter. |
| B2 | `secondary := primary` unless `secondaryGiven` | `if min_cluster_size is None: min_cluster_size = min_samples` | R + I | `None` ⇔ `secondaryGiven = false`; default-to-conditioned-primary dataflow preserved (mapping.md §2, row 5). |
| B3 | when `secondaryGiven`, `secondary := secondaryValue` | the supplied `min_cluster_size` argument | I | identity assignment of the supplied value. |
| B4 | condition `secondary` via the A3 op | `if min_cluster_size <= 1: min_cluster_size = max(2, int(min_cluster_size*n_samples))` | A-reference + I | same deep model as A3, second parameter. |
| B5 | return `{primary, secondary}` | the two integer counts flow into `_xi_cluster(…, min_samples, min_cluster_size, …)` | R | both are integer counts downstream consumers require. |

`Solution_prepatch_2.lean` reverts B1 and B4 to the non-truncating
`max 2 scaledPrimary` / `max 2 scaledSecondary` and **fails** on the same
discriminating clause (G-DIFF), for each independently-conditioned parameter.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
adding the integer-part truncation — is modeled **deeply** (`Rat.floor` inside
`asAbsoluteCount`, validated == the real `int(·)` expression by G-AX, §3.1),
never hidden behind an axiom about the function under change. The one operation
that did NOT change and is not exactly representable — the IEEE scaling — is
abstracted to a precondition stating what it guarantees (`scaledFromPopulation`),
which is the honest treatment of an over-strong claim: the postcondition now
states what the callee guarantees rather than what an idealized product would
(mapping.md §2.1). There are **no
consumed axioms** in this bundle: the only callee touching the result
(`_validate_size`) is unchanged and captured as a `require`, not an axiom.

## D. verify(Solution) ⇒ resolved

`conditionSizeParameter` / `resolvePairedSizes` verify only if their outputs
equal `asAbsoluteCount` — i.e. the scaled value is *reduced to a whole count*
(A3/B1/B4) and the optional-secondary dataflow is the `None`-defaults
behaviour (B2). By R (`numeric ↔ Rat`, `int ↔ Nat`, and the scaled value's
`2^-53` band) and G-AX (the deep model == the patched `max(2, int(·))` on the
documented domain, with the real machine product supplied and zero tolerated
divergences) the verified routines
equal the patched conditioning at all three sites; by G-CONF the R/I
transliteration of the skeletons agrees with `patch.diff`'s behaviour over ≥10⁵
fuzzed inputs. The F2P test `test_extract_xi` passes a fractional
`min_samples=0.1, min_cluster_size=0.08` (`n_samples = 31`): the patched code
yields the integer counts `3` and `2`, which is exactly `asAbsoluteCount`; the
pre-patch leaves `3.1` / `2.48`, which the spec rejects. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). Trust points: the single
deep-model fidelity check (G-AX, §3.1) and refinement fidelity (this doc,
G-EQ + G-CONF).
