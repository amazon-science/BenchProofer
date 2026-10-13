# refinement.md — matplotlib__matplotlib-20826

The operation-by-operation correspondence between `model.py`'s implementation
(`reinit_tick_kw_major` / `reinit_tick_kw_minor`, plus the `dict_carry_over`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`, vs **A-reference**, a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `Axis.clear` (`lib/matplotlib/axis.py:788`, body 809-810)

Gold hunk:
```
-        self._reset_major_tick_kw()
-        self._reset_minor_tick_kw()
+        # whether the grids are on
+        self._major_tick_kw['gridOn'] = (
+                mpl.rcParams['axes.grid'] and
+                mpl.rcParams['axes.grid.which'] in ('both', 'major'))
+        self._minor_tick_kw['gridOn'] = (
+                mpl.rcParams['axes.grid'] and
+                mpl.rcParams['axes.grid.which'] in ('both', 'minor'))
         self.reset_ticks()
```

The two replaced calls each did `self._<which>_tick_kw.clear()` then set only
`gridOn` (`_reset_major_tick_kw`/`_reset_minor_tick_kw`, `axis.py:776-786`). The
fix replaces those CALLS with an in-place assignment of the `gridOn` key that
leaves every other previously-stored key intact.

The site is modelled as TWO functions (one per tick class), differing only in
which `which`-selection covers them (`'both'/'major'` vs `'both'/'minor'`), per
SPEC_GUIDE §3 (model each changed sub-site as its own function for more
differential witnesses). Both impls are the same skeleton over the abstract
inputs.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `tick_kw: Dict[int, bool]` parameter | `self._major_tick_kw` / `self._minor_tick_kw` (`dict` str→value) | R | str-keyed dict ↔ `Dict[int, bool]` token-keyed (mapping.md §2): only key membership and the boolean visibility values are observed. |
| A2 | `result = dict_carry_over(tick_kw)` | (no explicit op) the gold assignment does NOT clear the dict, so the existing keys are carried over implicitly | A-reference | the unchanged "keep the existing settings" effect is modelled deeply by `dict_carry_over` (a fresh equal mapping); the proof's preservation guarantee (clauses 2/3) is discharged by its `Ensures`, and the deep model is validated == the real `dict(d)` primitive by axiom_check.py (G-AX), not consumed as opaque behaviour. The real gold achieves the same carry-over by mutating the SAME object in place; the resulting content is identical (mapping.md §2, §3.1). |
| A3 | `result[refreshed_key()] = flag_enabled and selection_covers` | `self._<which>_tick_kw['gridOn'] = (mpl.rcParams['axes.grid'] and mpl.rcParams['axes.grid.which'] in ('both', '<which>'))` | R + I | `refreshed_key()` ↔ `'gridOn'` (R, token); the assigned value is the conjunction `flag_enabled and selection_covers` (I) where `flag_enabled` ↔ `mpl.rcParams['axes.grid']` and `selection_covers` ↔ the `which`-membership test outcome (R, mapping.md §2). |
| A4 | `return result` (the new mapping state) | the mutated `self._<which>_tick_kw` is left for `reset_ticks()` / `_get_tick` to read by content (`**tick_kw`) | R | returning the resulting state ↔ leaving the mutated object; the consumer reads by content, not identity (mapping.md §2). |

The discriminating content of the change — re-initialisation **must not drop**
the other tick-keyword settings (the side-hiding `tick*On`/`label*On` flags
shared axes store) — lives in clause (2)
`Forall k. (k in tick_kw and k != refreshed_key()) ⇒ k in Result and Result[k] ==
tick_kw[k]`. The pre-patch `_reset_*_tick_kw` did `dict.clear()` first;
`model_prepatch.py` reproduces that (a fresh empty `{}` carrying nothing over)
and **fails** exactly clause (2) for BOTH sites — the spec sensing the change
(G-DIFF). One prepatch covers both independently-fixed sites because they are
the same fix applied to two structurally identical mappings, and the prepatch
fails on each site's clause (2) independently (two reported errors).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed —
re-initialising the tick-keyword mapping so that only the grid key is updated and
all other keys survive — is modelled **deeply** (the explicit `dict_carry_over` +
grid-key assignment, with the preservation guarantee spelled out in the
postconditions). There is **no consumed axiom about the function under change**:
the only axiom, `dict_carry_over`, covers an **unchanged language primitive**
(mapping copy) and is an **A-reference** that G-AX validates against the real
`dict(d)`. It is NOT a dead axiom — the proof of clauses (2)/(3) consumes its
`Ensures` to establish that the carried-over keys are present and that no
spurious key is introduced.

## C. verify(model) ⇒ resolved

`reinit_tick_kw_major`/`reinit_tick_kw_minor` verify only if (1) the grid key is
set to the prescribed conjunction AND (2) every other entry present on entry is
preserved AND (3) no spurious entry is introduced. By R (str→token dict,
in-place-mutation ↔ fresh-equal-mapping, `gridOn` ↔ `refreshed_key()`, rcParam flags ↔
booleans) the verified operation equals the gold in-place `gridOn` assignment
that leaves the other keys intact; by G-AX the deep model `dict_carry_over`
equals the real mapping-copy primitive (A-reference) and the end-to-end fixed
re-initialisation matches the model's postconditions. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited primitive — and the gold patch resolves the F2P
`test_shared_axes_clear` (which renders shared-axis subplots after `ax.clear()`
and requires the hidden ticks/labels to stay hidden, i.e. the stored visibility
keys to survive) and the P2P suite (G-RESOLVE). The trust points are exactly the
two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
