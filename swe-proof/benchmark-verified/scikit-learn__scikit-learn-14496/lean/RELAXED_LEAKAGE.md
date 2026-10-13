# RELAXED_LEAKAGE — scikit-learn__scikit-learn-14496 (lean)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

The relaxed-leakage policy lives in the binding spec-construction rules: for a
proven `problem_statement ↔ gold` mismatch where a faithful spec MUST name the
discriminator, the instance is kept with the leak allowed
(`meta.json gates.G-LEAK.status = "relaxed"`). The G-LEAK gate honors it
mechanically (`src/swebench_unified/gates/leak.py`, via the `relaxed_leakage`
meta flag plus this file).

## The mismatch

The public `problem_statement` does not merely omit the discriminating behavior —
it proposes the OPPOSITE one. Quoted from `instance.json`, the statement's own
suggested remedy:

```python
if min_samples <= 1:
    min_samples = int(round(max(2, min_samples * n_samples)))  # round to get the closest integer
```

The gold edit (`patch.diff`, `sklearn/cluster/optics_.py`) instead truncates:

```python
if min_samples <= 1:
    min_samples = max(2, int(min_samples * n_samples))
```

So a solver reading only the public statement is told to ROUND TO NEAREST, with
the comment "round to get the closest integer" spelling it out. Gold takes the
whole-number part downward. The two disagree on every scaled amount whose
fractional part is at least one half.

## Why naming the discriminator is unavoidable

The rounding mode is **faithfulness-forced**, not test-forced. Both directions
were measured against the real patched callee at the base commit:

| reduction modeled | divergences vs. real patched callee (13 inputs) |
|---|---|
| whole-number part downward (gold) | **0** |
| round to nearest (what the statement proposes) | 4 |
| round upward | 6 |
| downward, then `+1` | 13 |

So any spec that models the statement's proposal is UNFAITHFUL: it predicts a
count the real function never produces (e.g. a scaled amount of `28.5` — gold
delivers `28`, the statement's proposal delivers `29`).

The F2P test does not pin the mode either — `round`, `ceil`, `floor±1` and even a
constant `2` all pass it — so the obligation cannot be shifted onto the test
suite and left implicit in the spec.

Dropping the direction from the spec view is **battery-blocked**, not merely
inconvenient. Two floor-free weakenings are available in principle, and this
cell's own adversarial battery already requires the implementations each of them
admits to be REJECTED. All three cases below are declared in `properties.py` with
`kind: "uniqueness"` and `expect: "reject"`, the pairing the G-PBT kinds table
reads as SPEC-TOO-WEAK when it stops holding (`docs/architecture.md`):

| battery case | reduction it substitutes | witness threshold, population, scaled | count real / rival |
|---|---|---|---|
| `weak-min-floor-of-two-only` (`properties.py:1061`) | `.count 2` (`:489`) | `1/2`, `7`, `7/2` (`:1076`) | 3 / 2 |
| `weak-min-round-to-nearest` (`properties.py:1100`) | `.count (max 2 ⌊scaled + 1/2⌋)` (`:515`) | `1/2`, `5`, `5/2` (`:1118`) | 2 / 3 |
| `weak-min-overcount-ceiling` (`properties.py:1042`) | `.count (max 2 ⌊scaled⌋ + 1)` (`:477`) | `1/2`, `7`, `7/2` (`:1058`) | 3 / 4 |

The weaker weakening -- drop the reduction and pin only "reduce a fractional
threshold to a count of at least two", saying nothing about WHICH whole number --
admits the first rival by inspection: a constant `.count 2` is a count of at
least two.

The stronger weakening keeps the count FORM and the clamp at two and, instead of
a direction, ties the count to within one of the scaled amount -- a window, so no
direction is named. Any such window admits the other two rivals at the very
inputs the battery uses to refute them. At `5/2` the integers within one of the
amount are `2` and `3`, so the round rival's `3` is admitted; at `7/2` they are
`3` and `4`, so the ceiling rival's `4` is admitted. Round-to-nearest is admitted
not just there but everywhere, since `⌊scaled + 1/2⌋` is strictly within one of
`scaled` at every amount, so against a window spec that rival VERIFIES rather
than merely losing its witness.

As the cell stands, `meta.json gates.G-PBT` records `status = "pass"` and `SOUND:
29 spec case(s) behaved as expected` with `n_failed = 0`, and all three cases
above carry `outcome = "rejected (witness refutes the rival)"` with
`witness_checked = true`; `meta.json pbt_audit` separately records each as
`earned`. So neither weakening buys silence -- it trades the disclosure for a
spec-too-weak failure in the one gate that attacks spec strength from this side.
The reduction direction is pinned twice over, by the divergence table above
against the real callee and by the battery, and a spec that declines to name it
fails one of the two.

This is also why a floor-free clause that provably admits both a `round` and a
ceiling implementation is not a counterexample to unavoidability: admitting those
two IS the spec-too-weak defect here, because they are exactly the rivals
`properties.py` requires to be rejected. Such a clause does reject the pre-patch
shape and the constant-`.count 2` rival -- this cell's audit record proves both in
Lean, in `DeLeak.lean` -- and that is what makes it look like a repair until the
battery is consulted.

Faithful and silent is therefore impossible here. The spec view discloses the
direction of the reduction (`⌊·⌋` in the `pure` region, and the prose "take the
whole-number part of the amount"), and that disclosure is the relaxation.

## Scope of the relaxation

Only the reduction DIRECTION is disclosed beyond the public statement. The
narration was otherwise de-glossed: the spec view names no repo symbol
(`optics_`, `min_samples`, `min_cluster_size`, `_validate_size`,
`compute_optics_graph`, `cluster_optics_xi`, `sklearn`), quotes no diff line, and
carries no helper named after the discriminator. The mechanical lexical screen
passes on its own terms (`leakage.screen` → `passed: True`, `hard_failures: []`);
the relaxation covers the semantic residue the lexical screen cannot see.

The other facets the spec pins are all derivable from the public statement: that
a threshold at most one is a fraction to be scaled by the sample count, that the
count floor is two, and that the range check refuses out-of-range thresholds are
each visible in the statement's own quoted remedy and in the `ValueError` text it
reports.
