# Relaxed-leakage acceptance — matplotlib__matplotlib-24870

**Disposition: KEEP (relaxed leakage)** — the mechanical G-LEAK screen is clean
(the leak is semantic, not lexical; `gates.G-LEAK` records `status: "relaxed"`
pointing at this file); the residual is a *semantic* leak accepted under the
project relaxed-leakage policy. In this unified repo the policy lives in the
binding spec-construction rules, `prompts/lean/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`).
(The former `RELAXED_LEAKAGE.md` was a source-repo-only doc that does not
exist here — see `prompts/README.md` on dangling source-repo refs.)

## The instance

`_process_contour_level_args` (`lib/matplotlib/contour.py`, shared by
`contour`/`contourf` via `QuadContourSet._contour_args` and by
`tricontour`/`tricontourf` via `TriContourSet._contour_args`) selects the
levels argument. The gold special-cases a boolean (two-valued) field with no
caller-provided levels into TWO coupled defaults:

* a LINE contour gets the single midpoint level `[.5]` — the PUBLICLY-requested
  facet;
* a FILLED contour gets the three bracketing levels `[0, .5, 1]` — the facet
  that relaxes.

## The leak is genuinely unavoidable

**The public `problem_statement` names only the line facet.** It shows
`plt.contour(boolean_2d_array, levels=[.5], ...)`, proposes "Autodetect boolean
inputs to contour, and default levels to [0.5]", and discusses "the default 8
levels". Token scan: `contourf` 0, `filled` 0, `[0, .5, 1]` / `0, .5, 1` 0,
"at least 2 levels" 0.

**The filled facet lives only in `hints_text` and the gold/`test_patch`.**
`hints_text`: "I tried your code with `contourf()`, but that raises 'Filled
contours require at least 2 levels'. ... For contourf(bool_array) the natural
levels would be [0, .5, 1]".

**The F2P test pins BOTH facets.** `test_bool_autolevel` has 10 assertions; 5
of them pin the filled default:

```python
assert plt.contourf(z.tolist()).levels.tolist() == [0, .5, 1]
assert plt.contourf(z).levels.tolist() == [0, .5, 1]
assert plt.contourf(np.ma.array(z, mask=m)).levels.tolist() == [0, .5, 1]
...
assert plt.tricontourf(x, y, z.tolist()).levels.tolist() == [0, .5, 1]
assert plt.tricontourf(x, y, z).levels.tolist() == [0, .5, 1]
```

A spec that omitted the filled `[0, 1/2, 1]` branch (e.g. left the filled
result unconstrained, or gave filled the line default `[1/2]`) would admit an
implementation that verifies yet fails these assertions — a `verify ⟹ correct`
violation. So a faithful spec MUST pin the filled three-level default, and no
PS-derivable reformulation can express it: the value, the filled/line
distinction, and the "filled contours need ≥2 levels" rationale are all absent
from the `problem_statement`.

Only the FILLED facet relaxes; the LINE `[1/2]` facet is PS-derivable ("a
single level at 0.5") and does not leak. The non-boolean default `count 7` is
PS-derivable too ("the default 8 levels" = 7 inner boundaries via the
downstream `_autolev` count path, reconciled by G-CONF).

## Core soundness (policy requirement 1) — all clean

* G-VERIFY pass — `correct_chooseLevels` closes; `#print axioms` =
  `[propext, Classical.choice, Quot.sound]`, no `sorryAx`.
* G-DIFF pass — `Solution_prepatch.lean` (no boolean special-case; falls
  through to the default count) fails to verify against the identical spec.
* G-EQ sound/tight — the spec is a total deterministic functional relation
  (every branch pins `result` by exact equality), so any closing impl is
  extensionally equal to the gold-faithful one; independent panel attacks
  (wrong default count 8, swapped filled/line outputs) fail to close.
* Faithfulness clean — G-CONF pass (110014 checks, 0 disagreements) driving the
  real patched `contour`/`contourf`/`tricontour`/`tricontourf` API.
* G-RESOLVE pass — `patch.diff` == gold, official harness reports resolved.
