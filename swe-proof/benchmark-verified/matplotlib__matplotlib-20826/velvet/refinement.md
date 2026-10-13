# refinement.md — matplotlib__matplotlib-20826

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resetAxisTickKeywords` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — none here), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reset site — inside `Axis.clear()` (`lib/matplotlib/axis.py:806-818`)

Gold hunk (the two `_reset_*_tick_kw()` calls become two in-place writes):
```
- self._reset_major_tick_kw()           # each: dict.clear() then set only gridOn
- self._reset_minor_tick_kw()
+ self._major_tick_kw['gridOn'] = (
+         mpl.rcParams['axes.grid'] and
+         mpl.rcParams['axes.grid.which'] in ('both', 'major'))
+ self._minor_tick_kw['gridOn'] = (
+         mpl.rcParams['axes.grid'] and
+         mpl.rcParams['axes.grid.which'] in ('both', 'minor'))
```

| # | Solution.lean impl op (`resetAxisTickKeywords`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `mut majorKw : String → Bool` parameter | `self._major_tick_kw` (`dict[str,bool]`) | R | dict-of-bool ↔ total `String → Bool` map (mapping.md §2). G-CONF bridges via a Python dict copy; the frame quantifier ↔ "every other entry preserved, none added/dropped". |
| A2 | `mut minorKw : String → Bool` parameter | `self._minor_tick_kw` | R | as A1, for the minor map. |
| A3 | `key : String` (= the recomputed entry name) | the literal `'gridOn'` | R | identity on the string literal (mapping.md §1). |
| A4 | `majorVal : Bool`, `minorVal : Bool` inputs | `mpl.rcParams['axes.grid'] and ... in ('both', {'major','minor'})` | R + I | the recomputed flag value; its `rcParams` expression is transliterated I-tag in the G-CONF shadow (`expected_grid_on`) and read from the same `rcParams` the oracle reads. Not a callee contract — a config lookup. |
| A5 | `majorKw := Function.update majorKw key majorVal` | `self._major_tick_kw['gridOn'] = (...)` | I | identical concrete op: write one entry of the major map in place. G-CONF transliterates to `major[KEY] = val`. |
| A6 | `minorKw := Function.update minorKw key minorVal` | `self._minor_tick_kw['gridOn'] = (...)` | I | as A5, for the minor map. |

Discriminating content of the change — **every entry other than `'gridOn'` is
PRESERVED** by the reset (the per-side tick/label visibility flags shared axes
turned off) — lives in the two frame postconditions
`∀ k, k ≠ key → majorKw k = majorKwOld k` and the minor analogue. The pre-patch
`clear()` called `_reset_major_tick_kw`/`_reset_minor_tick_kw`, each of which did
`dict.clear()` (dropping every entry) before re-writing only `gridOn`;
`Solution_prepatch.lean` reproduces that by emptying each map to the blank
default (`fun _ => false`) before the single write, and so **fails** the frame
postconditions (G-DIFF). This is the directive-5 `mut`-frame obligation made the
discriminating clause: an impl that does not pin the unchanged frame admits the
bug.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — replacing a
clear-then-repopulate with an in-place single-entry write — is modeled **directly**
by `Function.update` on a total settings map, with the survival of the other
entries pinned by the frame postconditions. There is **no axiom**: no unchanged
repository callee is consulted. (`Function.update_of_ne` / `Function.update_self`
are Mathlib library facts, not assumptions about the repo.)

## C. verify(Solution) ⇒ resolved

`resetAxisTickKeywords` verifies only if, after it, each map has its `key` entry
equal to the recomputed value (A5/A6) **and** every other entry equal to its old
value (the frame). By R (dict ↔ total map, `'gridOn'` ↔ `key`, the `rcParams`
expression ↔ `majorVal`/`minorVal`) this is exactly the post-patch
`self._{major,minor}_tick_kw['gridOn'] = (...)` with the rest of each dict
untouched — which is what the gold patch does in `Axis.clear`. By G-CONF the R/I
transliteration agrees with the patched `Axis.clear`'s observable dict state on
≥10⁵ inputs. The F2P test `test_shared_axes_clear` renders two shared-axis grids,
one built with `ax.clear()` between subplots, and asserts the images are equal;
that holds iff `clear()` preserves the visibility flags the shared-axis machinery
set — exactly the frame this spec pins. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement, and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
