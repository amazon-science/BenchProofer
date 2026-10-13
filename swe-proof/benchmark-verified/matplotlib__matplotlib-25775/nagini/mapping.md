# mapping.md — matplotlib__matplotlib-25775

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 26224d96066b5c60882296c551f54ca7732c0af0`, states the type
abstraction, and (since the bundle has **no axioms**) records that the changed
behaviour is modelled deeply as per-object state with no callee provenance to
audit.

Repo files under change: `lib/matplotlib/text.py`,
`lib/matplotlib/backends/backend_agg.py`,
`lib/matplotlib/backends/backend_cairo.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Glyph` (class, field `pref`, field `dirty`) | `matplotlib.text.Text` — the per-object state `self._antialiased` (added at `text.py:138` in `__init__`) and the redraw flag `self.stale` | minimal class carrying only the one touched field plus the redraw flag |
| `build_glyph(default, supplied)` | `Text.__init__` — `lib/matplotlib/text.py:104` (new kwarg `antialiased=None`), threaded through `Text._reset_visual_defaults` — `text.py:155` (new param + guarded `set_antialiased`) | the modeled constructor behaviour (default-vs-supplied threading) |
| `set_pref(g, value)` | `Text.set_antialiased` — added method, `lib/matplotlib/text.py` (the `set_antialiased`/`get_antialiased` block follows `get_rotation_mode` at `text.py:308-310`) | the per-object update |
| `get_pref(g)` | `Text.get_antialiased` — added method, same block | the per-object read-back |
| `copy_state(dst, src)` | `Text.update_from` — `lib/matplotlib/text.py:312` (new line `self._antialiased = other._antialiased`, line ~324 post-patch) | the visual-state copy |

`Annotation` (`text.py:1592`, `__init__` at `text.py:1610`) subclasses `Text`
and forwards `antialiased` through `**kwargs` to `Text.__init__` (`text.py:1820`,
`Text.__init__(self, x, y, text, **kwargs)`) with no antialiasing-specific code
of its own, so the F2P `test_annotation_antialiased` exercises the *same*
`build_glyph` path — no separate model symbol is needed.

The backend rendering sites (see refinement.md §E) are pure consumers of the
modelled state and introduce no new decision logic:
- `backend_agg.RendererAgg.draw_text` — `backend_agg.py:200`; the call
  `font.draw_glyphs_to_bitmap(antialiased=mpl.rcParams['text.antialiased'])`
  (`backend_agg.py:208-209`) becomes `antialiased=gc.get_antialiased()`.
- `backend_cairo.RendererCairo.draw_text` — `backend_cairo.py:190`; the
  `opts.set_antialias(ANTIALIAS_DEFAULT if rcParams["text.antialiased"] else
  ANTIALIAS_NONE)` (`backend_cairo.py:207-208`) becomes
  `opts.set_antialias(gc.get_antialiased())`; a new
  `GraphicsContextCairo.get_antialiased` (`backend_cairo.py`, after
  `set_antialiased` at line 311) returns `self.ctx.get_antialias()`.
- `Text.draw` — `text.py:704`; a new `gc.set_antialiased(self._antialiased)`
  (after `gc.set_url(self._url)`, ~`text.py:739`) routes the stored per-object
  preference into the graphics context.

These are kind-R renames of "use the stored value" (refinement.md §E); the
verifiable behavioural core (the four F2P pure tests and the two
image-comparison tests, all of which reduce to "the per-object value is the
value honoured") lives in symbols above and is fully modelled.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Text._antialiased` (a `bool`) | `Glyph.pref` (`bool`) | `True`↔`True`, `False`↔`False`; identity on booleans |
| `mpl.rcParams['text.antialiased']` (the global default, a `bool`) | `default: bool` argument of `build_glyph` | the *value* of the global default; its origin (a global dict lookup) is unobservable to the tested behaviour, which only reads the resulting value. The two image-comparison F2P tests set the global default and compare to a per-object value, i.e. they relate the two `bool` values directly. |
| `antialiased=None` keyword (the `None`-default constructor argument) | `supplied: Optional[bool]` | "argument omitted / `None`" ↔ `None`; an explicit `True`/`False` ↔ `Optional[bool]` carrying that value |
| `Text.stale` (a `bool` redraw flag) | `Glyph.dirty` (`bool`) | identity on booleans; both are set `True` by the setter/copy |
| `Text` / `Annotation` instance | `Glyph` instance | only the touched fields `pref`,`dirty` are modelled; all other `Text` state (`_color`, `_fontproperties`, alignment, …) is unchanged by the patch and abstracted away |
| `self`/`other` of `update_from` | `dst`/`src` of `copy_state` | direct rename |

`bool` and `Optional[bool]` are first-class in Nagini's fragment; no string or
float modelling is needed (the value under change is a boolean flag, not text
or a numeric quantity).

## 3. Axiom provenance (kind-A — checked by G-AX / axiom_check.py)

**None.** This bundle ships **zero `@ContractOnly` axioms** and **zero
A-reference deep models of a callee**. The changed behaviour is entirely
per-object state — a stored boolean preference, its read-back, its update, and
its copy — which is modelled directly in Nagini (no opaque or inexpressible
callee is involved on the tested path). Consequently:
- there is no callee to cite provenance for;
- there is no `axiom_check.py` (G-AX is vacuous);
- the only soundness trust point is refinement fidelity (refinement.md, G-EQ).

The backend routing functions (`gc.get_antialiased`,
`cairo.Context.get_antialias`, `font.draw_glyphs_to_bitmap`) are NOT axiomatized
because they carry no decision logic relevant to the tested behaviour — they are
pass-throughs of the modelled `bool`, audited end-to-end by G-RESOLVE on the
real backends rather than by an axiom.
