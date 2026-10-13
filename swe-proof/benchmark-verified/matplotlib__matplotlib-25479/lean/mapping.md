# mapping.md — matplotlib__matplotlib-25479

Cold construction (`spec_provenance: cold`): derived only from `problem_statement`,
the gold `patch`, and the repo source at `base_commit`
`7fdf772201e4c9bafbc16dfac23b5472d6a53fa2`.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_colormapEq` / `problem_spec_colormapEq` / `correct_colormapEq` | `Colormap.__eq__(self, other)` | `lib/matplotlib/colors.py:775-789` |
| `implementation_register` / `problem_spec_register` / `correct_register` | `ColormapRegistry.register(self, cmap, *, name=None, force=False)` — the `self._cmaps[name] = cmap.copy()` store + name-propagation tail | `lib/matplotlib/cm.py:143-150` (register), patched tail `cm.py:148-151` |

Both functions are on the fix list and are **independently observable** (each has
its own FAIL_TO_PASS test), so each gets its own triple and its own prepatch.

## What the fix changes

* `Colormap.__eq__` (colors.py): the pre-patch guard was
  `if (not isinstance(other, Colormap) or self.name != other.name or self.colorbar_extend != other.colorbar_extend): return False`.
  The patch **removes the `self.name != other.name` disjunct**, so equality no
  longer depends on the display name — only on `colorbar_extend` and the lookup
  table `np.array_equal(self._lut, other._lut)`.
* `ColormapRegistry.register` (cm.py): after `self._cmaps[name] = cmap.copy()`,
  the patch adds
  `if self._cmaps[name].name != name: self._cmaps[name].name = name`, forcing the
  stored copy's `.name` to the registration `name`.

The two interact (test_set_cmap_mismatched_name): registering `viridis`-derived
cmap under `wrong-cmap` makes the looked-up object both report `name ==
"wrong-cmap"` AND compare `== cmap` (the latter only because `__eq__` no longer
checks the name).

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| `Colormap` object (touched fields only) | `structure Colormap` | field-wise, below |
| `cmap.name : str` | `Colormap.name : String` | identity on the byte string |
| `cmap.colorbar_extend` (comparable scalar attr in `__eq__`) | `Colormap.flag : Int` | one comparable auxiliary attribute; encode `colorbar_extend` as an `Int` code (e.g. `False↦0`, `True↦1`, or any injective code). Only `==`/`!=` is observed, so any injective `obj → Int` bijection is faithful. |
| `np.array_equal(self._lut, other._lut)` (lut comparison) | `a.table == b.table` (`List (List Int)`) | `np.array_equal` is shape-then-elementwise: it returns `False` if the two arrays differ in shape, else `True` iff every entry matches. Modeling the lut as a list of rows (`List (List Int)`) makes Lean `==` capture BOTH shape (number of rows and each row's width) and entries, so `a.table == b.table ⇔ np.array_equal`. (A flattened `List Int` would lose shape; rows are faithful.) |
| `cmap.copy()` then store | structural copy `let mut stored := cmap` | `__copy__` duplicates `__dict__` and copies `_lut`; for the modeled fields (name/flag/table) it is the identity, so the copy is omitted as a no-op structural duplicate (R). |
| `result.name = name` (post-patch) | `result.name = name` | identity |
| `bool` (`__eq__` result) | `Bool` | `True↦true`, `False↦false` |

`np.array_equal` returns `False` for differently-shaped arrays — matched by Lean
`List (List Int)` `==` returning `false` when the row count or any row width
differs. The PASS_TO_PASS `test_colormap_equals` line "compare different sizes
without failure" (`cm_copy._lut = cm_copy._lut[:10,:]`) is exactly this:
different shape ⇒ not equal, preserved by the model.

## Callee provenance / flag deps

* **No consumed callee axiom.** `__copy__` is structural (preserves every modeled
  field) and is modeled as the identity on the modeled fields (R). The lut
  comparison `np.array_equal` is modeled deeply as `List (List Int)` equality
  (R/I — shape-then-elementwise). Neither is axiomatized.
* No flag-dependent callee.

## G-CONF fuzz seed (pinned)

`conf_seed = 25479` (also in meta.json `verifier_pins.conf_seed`).
