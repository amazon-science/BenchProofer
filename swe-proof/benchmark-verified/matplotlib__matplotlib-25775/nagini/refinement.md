# refinement.md — matplotlib__matplotlib-25775

The operation-by-operation correspondence between `model.py`'s implementation
(the `Glyph` constructor, `build_glyph`, `set_pref`, `get_pref`, `copy_state`
impl regions) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-consumed** (proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

There are **no axioms** in this bundle and **no A-reference deep models of a
callee**: the changed behaviour is entirely per-object state (a stored boolean
preference, its read-back, its update, and its copy), modelled directly. The
backend rendering hunks are pure consumers of that state (see §E) and add no
new differential behaviour beyond "the per-object preference is honoured".

The model abstracts the bool-valued attribute `Text._antialiased` and the
optional constructor argument; everything else in the patched methods is
matplotlib bookkeeping (alignment, colour, fonts) that is unchanged by the gold
patch and irrelevant to the tested antialiasing behaviour.

## A. Construction — `Text.__init__` + `_reset_visual_defaults`

Gold hunks (`lib/matplotlib/text.py`):
```
  __init__(..., parse_math=None,
+          antialiased=None,    # defaults to rcParams['text.antialiased']
           **kwargs):
      ...
      self._text = ''
+     self._antialiased = mpl.rcParams['text.antialiased']
      self._reset_visual_defaults(
          ...,
+         antialiased=antialiased)

  _reset_visual_defaults(..., rotation_mode=None,
+                        antialiased=None):
      ...
      self.set_rotation_mode(rotation_mode)
+     if antialiased is not None:
+         self.set_antialiased(antialiased)
```

| # | model.py impl op (`build_glyph` / `Glyph.__init__`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `default: bool` parameter | `mpl.rcParams['text.antialiased']` (a bool) read in `__init__` | R | the global default is a `bool`; modelled as the `bool` argument `default`. mapping.md §2. The default's *origin* (a global lookup) is irrelevant to the tested behaviour, which observes only its value. |
| A2 | `supplied: Optional[bool]` parameter | the keyword argument `antialiased=None` of `__init__` (and the `antialiased` parameter of `_reset_visual_defaults`) | R | `None`-default optional bool ↔ `Optional[bool]`; "absent" ↔ `None`. mapping.md §2. |
| A3 | `g = Glyph(default)` sets `g.pref = default` | `self._antialiased = mpl.rcParams['text.antialiased']` | I + R | the field is initialised to the global default first (same control flow); `_antialiased` ↔ `pref`. |
| A4 | `if supplied is not None: set_pref(g, supplied)` | `if antialiased is not None: self.set_antialiased(antialiased)` (inside `_reset_visual_defaults`, called from `__init__` with `antialiased=antialiased`) | I | identical guarded override; `set_pref` ↔ `set_antialiased` (site B). |
| A5 | `return g` | the constructed `Text`/`Annotation` instance | R | object identity; only `pref`/`_antialiased` is observed by the F2P tests. |

`Annotation.__init__` forwards `antialiased` to `Text.__init__` via `**kwargs`
(no antialiasing-specific code of its own), so `test_annotation_antialiased`
exercises exactly the same `build_glyph` path; no separate model function is
needed (mapping.md §1).

## B. Update — `Text.set_antialiased`

Gold hunk (added method):
```
+ def set_antialiased(self, antialiased):
+     self._antialiased = antialiased
+     self.stale = True
```

| # | model.py impl op (`set_pref`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `g.pref = value` | `self._antialiased = antialiased` | I + R | identical store; `_antialiased` ↔ `pref`, `antialiased` arg ↔ `value`. |
| B2 | `g.dirty = True` | `self.stale = True` | I + R | identical redraw-flag set; `stale` ↔ `dirty`. mapping.md §2. |

## C. Read-back — `Text.get_antialiased`

Gold hunk (added method):
```
+ def get_antialiased(self):
+     return self._antialiased
```

| # | model.py impl op (`get_pref`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `return g.pref` | `return self._antialiased` | I + R | identical read; `_antialiased` ↔ `pref`. The read-only fractional permission (`Acc(g.pref, 1/2)`) is the directive-5 frame: a wrong impl cannot satisfy the postcondition by overwriting the input. |

## D. Copy — `Text.update_from`

Gold hunk:
```
      self._linespacing = other._linespacing
+     self._antialiased = other._antialiased
      self.stale = True
```

| # | model.py impl op (`copy_state`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| D1 | `dst.pref = src.pref` | `self._antialiased = other._antialiased` | I + R | identical field copy; `dst`/`src` ↔ `self`/`other`. The other `update_from` assignments (`_color`, `_linespacing`, …) are unchanged by the patch and abstracted away (mapping.md §2). |
| D2 | `dst.dirty = True` | `self.stale = True` (already present in `update_from`) | I + R | the redraw flag is set; identical. |

## E. Backend rendering hunks — pure consumers of the modelled state

Gold hunks in `backend_agg.py`, `backend_cairo.py`, and `Text.draw`:
```
  Text.draw:        + gc.set_antialiased(self._antialiased)
  backend_agg:      - antialiased=mpl.rcParams['text.antialiased']
                    + antialiased=gc.get_antialiased()
  backend_cairo:    - opts.set_antialias(ANTIALIAS_DEFAULT if rcParams[...] else NONE)
                    + opts.set_antialias(gc.get_antialiased())
                    + def get_antialiased(self): return self.ctx.get_antialias()
```

These hunks route the **per-object** stored preference (modelled as `pref`,
read by `get_pref` ↔ `get_antialiased`) into the drawing stage in place of the
**global** `rcParams['text.antialiased']` lookup. They introduce no behaviour
beyond "the value the object stores is the value used to render", which is
precisely what the state model (A–D) pins: `get_pref(g) == g.pref`, and `g.pref`
equals the supplied/`default` value per A. The two image-comparison F2P tests
(`test_text_antialiased_{off,on}_default_vs_manual`) assert exactly that a glyph
built with `antialiased=v` renders identically to one built under the default
when the global default is set to `v` — i.e. the figure produced from the
per-object value equals the figure produced from the global value `v`. Under
the state model this is the equality `get_pref(build_glyph(v, None)) ==
get_pref(build_glyph(default, v))` whenever `default == v`, which the spec
guarantees. The routing itself (`gc.set_antialiased`/`gc.get_antialiased`,
cairo's `get_antialias`) is a plain `bool`/enum pass-through with no decision
logic, so it is a kind-R rename of "use the stored value", not a changed
operation needing a deep model or an axiom. (G-RESOLVE confirms the routing on
the real backends.)

## F. No kind-3 (unexpressible-changed-op) steps; no dead axioms

Every step above is R or I. The one operation that genuinely *changed* — where
the antialiasing value comes FROM (a per-object stored preference rather than a
global default) — is modelled **deeply and directly** as object state (A–D);
there is no axiom standing in for it, hence no A-consumed or A-reference row and
no `axiom_check.py` (G-AX is vacuous: the bundle ships zero `@ContractOnly`).

## G. verify(model) ⇒ resolved

`build_glyph` verifies only if a supplied value overrides the default
(`Implies(supplied is not None, Result().pref == supplied)`) and an absent value
falls back to it (`Implies(supplied is None, Result().pref == default)`);
`set_pref` verifies only if the store takes effect (`g.pref == value`) and the
redraw flag is set; `get_pref` verifies only if it returns the stored value;
`copy_state` verifies only if the destination adopts the source's value. By the
R-refinements (mapping.md §2: `_antialiased`↔`pref`, `stale`↔`dirty`,
`rcParams['text.antialiased']`↔`default`, `Optional[bool]`↔the `None`-default
kwarg) these are exactly the gold patch's per-object antialiasing semantics on
the `bool` values the F2P tests use. The pre-patch behaviour (no per-object
preference — always the global default; no working setter) is reproduced by
`model_prepatch.py` (constructor ignores `supplied`, fails A's override clause)
and `model_prepatch_2.py` (setter is a no-op, fails B1), the two
independently-observable fixed behaviours (G-DIFF). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this document, G-EQ); axiom soundness (G-AX) is vacuous.
