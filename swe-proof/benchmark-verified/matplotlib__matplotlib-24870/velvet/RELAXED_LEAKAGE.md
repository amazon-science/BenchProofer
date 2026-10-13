# Relaxed-leakage acceptance — matplotlib__matplotlib-24870 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true`; `gates.G-LEAK` records `status: "relaxed"`
pointing at this file. The mechanical G-LEAK screen is clean (the leak is
semantic, not lexical); the residual is a *semantic* leak accepted under the
project relaxed-leakage policy. In this unified repo the policy lives in the
binding spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`, via
the `relaxed_leakage` meta flag + this file). The same instance is already
dispositioned identically — and regated GREEN — in the sibling `lean/` bundle
(`lean/RELAXED_LEAKAGE.md`). (A former `RELAXED_LEAKAGE.md` was a
source-repo-only doc that does not exist here; references to it in older
in-bundle text mean this policy.)

## The instance

`_process_contour_level_args` (`lib/matplotlib/contour.py`, shared by
`contour`/`contourf` via `QuadContourSet._contour_args` and by
`tricontour`/`tricontourf` via `TriContourSet._contour_args`) selects the
levels argument. The gold special-cases a boolean (two-valued) field with no
caller-provided levels into TWO coupled defaults:

```python
elif np.issubdtype(z_dtype, bool):
    if self.filled:
        levels_arg = [0, .5, 1]     # contourf(bool) — FILLED facet
    else:
        levels_arg = [.5]           # contour(bool)  — LINE facet
```

* the LINE contour single midpoint level `[.5]` is the PUBLICLY-requested
  facet;
* the FILLED contour three bracketing levels `[0, .5, 1]` is the facet that
  relaxes.

## The leak is genuinely unavoidable

**The public `problem_statement` names only the line facet.** It shows
`plt.contour(boolean_2d_array, levels=[.5], ...)`, proposes "Autodetect
boolean inputs to contour, and default levels to [0.5]", and discusses "the
default 8 levels". Token scan of `problem_statement` (mechanically verified
against `../instance.json`): `contourf` 0, `filled` 0, `[0, .5, 1]` /
`0, .5, 1` 0; `[.5]` / `0.5` / `bool` present.

**The filled facet lives only in `hints_text` and the gold/`test_patch`.**
`hints_text`: "For contourf(bool_array) the natural levels would be
[0, .5, 1]; sure that can go together with fixing contour."

| token | in `problem_statement` | in `hints_text` | in `test_patch` |
|---|---|---|---|
| `[0, .5, 1]` | **no** | yes | yes |
| `contourf` | **no** | yes | yes |
| `[.5]`, `0.5`, `bool` | yes | — | yes |

**The F2P test pins BOTH facets.** The sole FAIL_TO_PASS,
`test_bool_autolevel`, has 10 level assertions; 5 pin the filled default:

```python
assert plt.contourf(z).levels.tolist() == [0, .5, 1]
assert plt.tricontourf(x, y, z).levels.tolist() == [0, .5, 1]
# (+ list / masked-array variants, 5 total `== [0, .5, 1]` assertions)
```

A spec that omitted the filled `[0, 1/2, 1]` branch (e.g. dropped the
`filled` distinction, left the filled result unconstrained, or returned
`[1/2]` in both sub-branches) would admit a wrong implementation that
verifies yet fails these `contourf`/`tricontourf` assertions — a
`verify ⟹ correct` violation (G-EQ / G-DIFF break). So a faithful spec MUST
pin the filled three-level default, and no `problem_statement`-derivable
reformulation can express it: the value, the filled/line distinction, and the
"filled contours require at least 2 levels" rationale are all absent from the
`problem_statement`. The leak is in the *behavior itself*, not in narration
that could be removed.

Only the FILLED facet relaxes; the LINE `[1/2]` facet is PS-derivable ("a
single level at 0.5") and does not leak. The non-boolean default `count 7` is
PS-derivable too ("the default 8 levels" = 7 inner boundaries via the
downstream count path, reconciled by G-CONF). The priority ordering
keyword > positional > default is generic argument-handling, not
gold-specific.

## Core soundness (policy requirement 1) — all clean

* **G-VERIFY pass** — `Solution.lean` verifies (exit 0) via
  `scripts/lean_verify.sh`.
* **G-DIFF pass** — `Solution_prepatch.lean` (no bool autodetection; falls
  through to the default count) fails verification on exactly the two
  `boolField = true` clauses, including the filled discriminator;
  `same_spec(Solution, Solution_prepatch) = True` (spec region
  byte-identical).
* **G-EQ sound/tight** — the spec is a total deterministic 5-clause contract
  over the flag cube; every branch pins `out` by exact equality on decidable
  `LevelArg`, so any verifying impl is extensionally the gold-faithful one;
  panel attacks (prepatch, swapped filled/line outputs, count 8, `[1/2]` in
  both branches, …) all fail verification while the positive control
  verifies.
* **G-AX vacuous** — empty axioms region (`axioms: []`,
  `deep_model_references: []`); the `np.issubdtype`/`self.filled` tests are
  modeled as inputs, not axiomatized callees.
* **G-CONF pass** — all-R/I shadow of `chooseLevelArg` agrees with the real
  patched selection on 100020 inputs (seed 24870), 0 disagreements.
* **G-RESOLVE pass** — `patch.diff` == gold verbatim; official harness
  resolves.
* **G-MUT pass** — killed 15/15.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the filled-contour default `[0, 1/2, 1]`). The verify ⟹ correct
contract is unaffected.

## Scope of what is disclosed

The spec view discloses: bool fields get a fixed boundary level
specification, which is `[1/2]` for line plots and `[0, 1/2, 1]` for filled
plots. The `[1/2]` half is public; the filled `[0, 1/2, 1]` half is the
relaxed disclosure. Nothing about the patched file, the `np.issubdtype`
mechanism, the `z_dtype` plumbing, or the `_process_contour_level_args`
symbol is named in the spec view; the mechanical lexical G-LEAK screen
passes (the spec view writes the rational `[0, 1/2, 1]` and uses `filled`
only as a generic behavioral parameter).
