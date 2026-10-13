# refinement.md — matplotlib__matplotlib-25775

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`textAntialiased` `do` block and the `resolveAA` pure model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. There are **no A
legs** in this bundle (no axioms, no deep-model references) — `resolveAA` is a
closed function of its inputs.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The resolution site — per-object antialiasing flag (`text.py`)

Gold hunks (`lib/matplotlib/text.py`):
```
+ antialiased=None,                                     # __init__ kwarg
+ self._antialiased = mpl.rcParams['text.antialiased']  # __init__ default
+ antialiased=antialiased                               # forwarded to _reset_visual_defaults
+ if antialiased is not None:                           # _reset_visual_defaults
+     self.set_antialiased(antialiased)
+ def set_antialiased(self, antialiased): self._antialiased = antialiased; ...
+ def get_antialiased(self): return self._antialiased
```

| # | Solution.lean impl op (`textAntialiased`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requested : Option Bool` | the `antialiased=None` kwarg of `__init__`/`_reset_visual_defaults` | R | `None`↔`none`, `True`/`False`↔`some true`/`some false` (mapping.md §2). |
| A2 | parameter `ambient : Bool` | `mpl.rcParams['text.antialiased']` | R | the global default, a `validate_bool` rcParam, ↔ `Bool` (mapping.md §2). |
| A3 | `let aa := match requested with \| none => ambient \| some b => b` | `self._antialiased = rcParams['text.antialiased']` then `if antialiased is not None: self.set_antialiased(antialiased)` | I | the two-line "default then override-if-supplied" of the patch is exactly the `match`: when the kwarg is `None` the rcParam default stands (`ambient`); when supplied it overwrites (`some b → b`). Concrete, transliterated by G-CONF. |
| A4 | `return aa` (`Bool`) | the value left in `self._antialiased`, returned by `get_antialiased()` | R + I | `Text.set_antialiased` stores the raw value (no `int(bool(...))` coercion); `get_antialiased()` returns it unchanged (mapping.md §3). `Bool`↔`bool` identity. |

Discriminating content of the change — an explicit per-object choice
(`some b`) must take effect over the ambient default — lives in
`resolveAA (some b) ambient = b` (model) ⇔ the
`if antialiased is not None: self.set_antialiased(antialiased)` override (real).
The pre-patch code had no per-object field at all and always used the ambient
default; `Solution_prepatch.lean` reproduces that (`return ambient`, ignoring
`requested`) and **fails** `out = resolveAA requested ambient` precisely on the
`requested = some b, b ≠ ambient` case (G-DIFF).

## B. The plumbing site — carry the resolved flag to the renderer (backends)

Gold hunks: `Text.draw` adds `gc.set_antialiased(self._antialiased)`
(`text.py:768`); `RendererAgg.draw_text` reads `gc.get_antialiased()` instead of
`rcParams['text.antialiased']` (`backend_agg.py:209`); `RendererCairo.draw_text`
likewise, and `GraphicsContextCairo` gains `get_antialiased`
(`backend_cairo.py`).

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node — folded into A4's `out`) | `gc.set_antialiased(self._antialiased)` → renderer reads `gc.get_antialiased()` | R | the GraphicsContext is a TRANSPORT for the already-resolved boolean: the value the renderer ultimately uses is identical to `Text._antialiased`. On the AGG path this is a plain `bool` round-trip through `gc`; the equality of "what the renderer uses" to "the resolved flag" is the type-only refinement, validated by G-CONF (which reads `Text.get_antialiased()`, the same field `draw` forwards). |

No separate failing prepatch for site B: the spec must stay byte-identical
(G-DIFF), and the plumbing carries no content beyond the resolved flag that
site A's prepatch already discriminates. Its fidelity is covered by G-CONF.

The Cairo `get_antialiased` returns a `cairo.Antialias` enum (not a bare bool),
but that path is only reachable from the image-comparison F2P tests
(`test_text_antialiased_*[pdf/png]`), which compare a manually-set value against
the same value set via rcParam — i.e. they too only assert the flag is honoured,
not its enum encoding. The state F2P tests (`test_set/get_antialiased`,
`test_annotation_antialiased`) observe `Text._antialiased`/`get_antialiased()`
directly, which is the bare boolean A4 returns.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is no operation Velvet cannot express: the changed
behavior is a scalar resolution `requested if not None else ambient`, modeled
directly by `resolveAA` (a total `match` on `Option Bool`). No axiom is consumed
and no deep-model reference is declared — `resolveAA` is closed over its inputs.

## D. verify(Solution) ⇒ resolved

`textAntialiased` verifies only if its output equals `resolveAA requested
ambient` — i.e. the explicit per-object choice when present (A3) and the ambient
default otherwise. By R (the `Option Bool`↔kwarg, `Bool`↔rcParam/field
bijections) the verified resolution equals the patched `Text`'s effective
`get_antialiased()` on every `{None,True,False}×{True,False}` configuration; by
G-CONF the R/I transliteration agrees with the real patched objects (`Text` and
`Annotation`) on ≥10⁵ fuzzed configurations; the plumbing (B1) carries that flag
unchanged to the renderer. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (no A legs); the sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF).
