# mapping.md — matplotlib__matplotlib-25775

## Instance
- repo: matplotlib/matplotlib
- base_commit: 26224d96066b5c60882296c551f54ca7732c0af0
- modeled behavior: the effective antialiasing flag carried by a text artist —
  its value as read back by the getter and as handed to the graphics context at
  draw time.

## Symbol binding (file:line @ base_commit)
- `Text.__init__`            — lib/matplotlib/text.py:104-153 (gains `antialiased=None` kwarg, sets default field, threads arg through)
- `Text._reset_visual_defaults` — lib/matplotlib/text.py:155-189 (gains `antialiased=None` param; `if antialiased is not None: self.set_antialiased(antialiased)`)
- `Text.set_antialiased`     — lib/matplotlib/text.py (added by patch) — `self._antialiased = antialiased`
- `Text.get_antialiased`     — lib/matplotlib/text.py (added by patch) — `return self._antialiased`
- `Text.draw`               — lib/matplotlib/text.py:~765 — adds `gc.set_antialiased(self._antialiased)`
- backend hookups (consume the per-object flag, not part of the modeled kernel):
  - lib/matplotlib/backends/backend_agg.py:206-209 — `antialiased=gc.get_antialiased()`
  - lib/matplotlib/backends/backend_cairo.py:203-209,309-311 — `opts.set_antialias(gc.get_antialiased())` + new `GraphicsContextCairo.get_antialiased`
- `rcParams['text.antialiased']` — the global default boolean (unchanged callee; modeled as the input `rcDefault : Bool`).

## Lean ↔ Python type bijection (G-CONF / G-AX)
| Python | Lean |
|---|---|
| `rcParams['text.antialiased']` (bool) | `rcDefault : Bool` |
| `antialiased` ctor kwarg, `None`=unset | `ctorArg : Option Bool` (`none`=unset) |
| a later `set_antialiased(b)` call, or none | `laterSet : Option Bool` (`none`=not called) |
| `get_antialiased()` return / value passed to `gc.set_antialiased` at draw | `result : Bool` |

Note: Python `set_antialiased`/the GC store `int(bool(b))`; `Text._antialiased`
itself stores the python bool unchanged (the int coercion happens only inside the
GraphicsContext, downstream of the modeled getter). The F2P tests assert
`txt._antialiased is True/False` (python bools), so the modeled value is `Bool`.

## Callee provenance / flag deps
- No UNCHANGED callee is consumed by the proof. The resolution is fully
  structural over `(rcDefault, ctorArg, laterSet)`. `rcParams['text.antialiased']`
  is not axiomatized — it is supplied as the input `rcDefault`. Hence the axioms
  region declares nothing and `axiom_check.py` is a skip stub.
- Annotation: `Annotation` subclasses `Text` and inherits `__init__` /
  get/set_antialiased unchanged, so its behavior is the SAME modeled function
  (test_annotation_antialiased exercises the identical resolution).

## G-CONF fuzz seed
- pinned seed: 25775. Input space is finite (rcDefault∈{T,F} × ctorArg∈{None,T,F}
  × laterSet∈{None,T,F} = 18 combinations); conformance enumerates it
  exhaustively against the REAL patched `Text` object (construct + get/set, no
  rendering needed), then fuzzes ≥10^5 random draws from the same space.
