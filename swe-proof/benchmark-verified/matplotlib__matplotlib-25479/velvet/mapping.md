# mapping.md — matplotlib__matplotlib-25479

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7fdf772201e4c9bafbc16dfac23b5472d6a53fa2`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. This bundle consumes **no axiom** and ships **no A-reference**
deep model: both modeled behaviours are total decisions over a colormap's own
fields, so there is nothing for G-AX to validate.

Repo files under change: `lib/matplotlib/cm.py`, `lib/matplotlib/colors.py`.

Semantics: `Solution.lean` sets `loom.semantics.termination "total"`
(TotalCorrectness). Both real counterparts terminate on every input — the
patched `register` addition is a guarded field assignment and the patched
`__eq__` is a finite field/array comparison — so total correctness is the
faithful semantics, and it closes the vacuous-divergence hole (under partial
correctness a non-terminating same-spec impl would satisfy every
postcondition vacuously while its faithful Python refinement hangs the
FAIL_TO_PASS tests).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Colormap` (structure) | `matplotlib.colors.Colormap` — `lib/matplotlib/colors.py:606` (class) | model of the colormap object, restricted to the fields the two behaviours touch |
| `registeredColormap (cmap, name)` | `ColormapRegistry.register(self, cmap, *, name, force)` — `lib/matplotlib/cm.py:113` (changed body lines 153–156) | the modeled changed function (site 1): the colormap value finally stored under the chosen registration name |
| `colormapsEqual (a, b)` | `Colormap.__eq__(self, other)` — `lib/matplotlib/colors.py:776` | the modeled changed function (site 2): colormap value-equality |
| `colormapEqSpec` | the boolean `__eq__` computes post-patch (`colors.py:777–786`) | pure spec: name-independent value-equality |

The pre-patch repo content the change removes (refinement audit only, not in the
consumer spec view): the `self.name != other.name` disjunct in `__eq__`
(`colors.py:777`, removed), and the absence of any name-stamping after
`self._cmaps[name] = cmap.copy()` in `register` (`cm.py:153`, the post-patch
adds lines 154–156).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Colormap.name : str` | `Colormap.name : String` | Python `str` ↔ Lean `String`, identity on content |
| `Colormap.colorbar_extend : bool` | `Colormap.extendStyle : Bool` | the boolean flag `__eq__` compares; Python `bool` ↔ Lean `Bool` |
| `Colormap._lut` (the initialized colour lookup table, a NumPy array of shape `(N+3, 4)` of integer-castable rows) compared by `np.array_equal` | `Colormap.lookupTable : List (List Int)` | row-major: the `(N+3)`×4 LUT ↔ a `List` of fixed-width `List Int` rows; `np.array_equal(self._lut, other._lut)` ↔ `decide (a.lookupTable = b.lookupTable)`. Distinct LUTs (different ends, different sizes) map to distinct `List (List Int)`; equal LUTs to equal lists. |
| `cmap.copy()` then store (`cm.py:153`) | identity on the modeled `Colormap` fields | `copy()` is a content copy: it preserves `name`, `colorbar_extend`, and `_lut`. Modeled as identity on the carried fields (the registry stamps the name afterwards, which is what `registeredColormap` returns). |
| object identity (`is`) vs value (`==`) | not modeled | the registry stores a COPY (distinct object id); the modeled behaviour is the value `==`, which the F2P `test_set_cmap_mismatched_name` asserts (`cmap_returned == cmap`). Identity is irrelevant to the modeled value. |

`np.array_equal` returns `True` for arrays of equal shape and equal elements,
`False` otherwise (incl. different shapes) — exactly Lean `=` on
`List (List Int)`. The F2P `test_colormap_equals` exercises the different-shape
case (`cm_copy._lut = cm_copy._lut[:10, :]`), which maps to lists of different
length, decided `≠`.

## 3. Callee provenance

**None.** Neither modeled behaviour calls a foreign function whose contract the
proof assumes. `register`'s post-patch addition is a direct field assignment
(`self._cmaps[name].name = name`) guarded by a string comparison; `__eq__`'s
post-patch body is a conjunction of an `isinstance` guard (modeled away — both
operands are `Colormap` by construction in every F2P call), a boolean-field
comparison, and an `np.array_equal` on the LUT. Both are spelled out **directly**
(I/R-tagged), so there is no consumed axiom and no A-reference deep model — hence
no `axiom_check.py` (G-AX is vacuous; meta.json records `G-AX.status = "skip"`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25479`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `registeredColormap` and `colormapsEqual` (all I/R-tagged ops)
to Python and diffs them against the patched repo's real
`ColormapRegistry.register` (observed via the stored copy's `.name`) and real
`Colormap.__eq__`. There are no A-tagged callees to leave as real.
