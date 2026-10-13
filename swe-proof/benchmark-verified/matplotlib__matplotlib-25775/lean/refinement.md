# refinement.md — matplotlib__matplotlib-25775

Maps every operation in `implementation_textAntialiased` to its `patch.diff`
counterpart. Tags: **R** = type refinement, **A-consumed** = proof uses an axiom
property, **A-reference** = deep model validated == real callee (G-AX), **I** =
identical concrete op.

The modeled function is the per-object antialiasing resolution: how a text
artist's `_antialiased` field gets its value (default → ctor arg → later set),
which the getter returns and the draw stage hands to the graphics context.

| # | impl op (Solution.lean) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut acc := rcDefault` | `text.py __init__`: `self._antialiased = mpl.rcParams['text.antialiased']` | R | `rcParams['text.antialiased']` (python bool) ↔ `rcDefault : Bool`. The field is seeded with the global default at construction. |
| 2 | `if let some b := ctorArg then acc := b` | `text.py _reset_visual_defaults`: `if antialiased is not None: self.set_antialiased(antialiased)` (driven by new `antialiased=None` ctor kwarg threaded through `__init__`) | R | `antialiased` kwarg, `None`=unset ↔ `ctorArg : Option Bool`, `none`=unset. `set_antialiased` stores the value verbatim into `_antialiased`. |
| 3 | `if let some b := laterSet then acc := b` | `text.py set_antialiased`: `self._antialiased = antialiased` (a post-construction call) | R | A later explicit `set_antialiased(b)` call, or none ↔ `laterSet : Option Bool`. Overrides whatever was in effect. |
| 4 | `return acc` | `text.py get_antialiased`: `return self._antialiased`; consumed at draw by `gc.set_antialiased(self._antialiased)` and read by backends via `gc.get_antialiased()` | R | The resolved field value is exactly what the getter returns and what reaches the graphics context. |

Refinement (R) notes:
- `Option Bool` ↔ python `bool | None` sentinel bijection (`none ↔ None`,
  `some true ↔ True`, `some false ↔ False`).
- The backend edits (`backend_agg.py`, `backend_cairo.py` + new
  `GraphicsContextCairo.get_antialiased`) and `Text.update_from`'s
  `self._antialiased = other._antialiased` are pure plumbing that *propagates*
  this same resolved value; they introduce no new resolution logic, so they are
  outside the modeled kernel (no separate impl op). G-CONF validates the
  resolution at the `Text` get/set boundary, which is where the F2P tests
  observe it.
- `Annotation` inherits the resolution unchanged (subclass of `Text`); the
  modeled function covers `test_annotation_antialiased` identically.

No op is A-consumed or A-reference: the resolution is fully structural over the
three inputs, so no callee axiom is used and there are no opaque callees. No
changed op is inexpressible.

conf_skip = false (the impl region is all-R, mechanically checkable by G-CONF).
