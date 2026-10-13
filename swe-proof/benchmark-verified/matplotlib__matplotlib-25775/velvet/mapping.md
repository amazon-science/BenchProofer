# mapping.md — matplotlib__matplotlib-25775

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 26224d96066b5c60882296c551f54ca7732c0af0`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo files under change: `lib/matplotlib/text.py`,
`lib/matplotlib/backends/backend_agg.py`,
`lib/matplotlib/backends/backend_cairo.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `textAntialiased (requested : Option Bool) (ambient : Bool)` | the per-object antialiasing-flag resolution performed in `Text._reset_visual_defaults` / `Text.set_antialiased` and exposed by `Text.get_antialiased` — `lib/matplotlib/text.py` (post-patch: `__init__` line 138 `self._antialiased = mpl.rcParams['text.antialiased']`; `_reset_visual_defaults` lines 194-195 `if antialiased is not None: self.set_antialiased(antialiased)`; `set_antialiased`/`get_antialiased` lines 318-340) | the modeled new behavior: resolve the effective antialiasing flag a `Text` carries |
| `resolveAA (requested : Option Bool) (ambient : Bool)` | the resolution rule "`antialiased` argument if it is not `None`, else `rcParams['text.antialiased']`" implemented across `__init__`/`_reset_visual_defaults`/`set_antialiased` | pure spec: the effective flag for one object |
| `requested : Option Bool` | the `antialiased=None` keyword argument of `Text.__init__` / `_reset_visual_defaults` (`lib/matplotlib/text.py:118,173`) | per-object explicit choice; `None` ⇒ unspecified |
| `ambient : Bool` | `mpl.rcParams['text.antialiased']` (a global `validate_bool`, default `True`; `lib/matplotlib/rcsetup.py:952`, `mpl-data/matplotlibrc:302`) | ambient/global default |
| `out : Bool` | the value stored in `Text._antialiased` and returned by `Text.get_antialiased()` (`lib/matplotlib/text.py:339-340`) | the resolved effective flag |

The pre-patch repo behavior the change replaces (refinement audit only, not in
the consumer spec view): there was no `Text._antialiased` field, no
`get/set_antialiased` on `Text`, and the renderer read the flag straight from
`mpl.rcParams['text.antialiased']` in `RendererAgg.draw_text`
(`backend_agg.py:209`) and `RendererCairo.draw_text` (`backend_cairo.py:206`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `antialiased` kwarg of `Text.__init__` (`bool` or `None`) | `Option Bool` | Python `None` ↔ Lean `none`; Python `True`/`False` ↔ Lean `some true`/`some false` |
| `mpl.rcParams['text.antialiased']` (`bool`, `validate_bool`) | `Bool` (the `ambient` arg) | Python `True`/`False` ↔ Lean `true`/`false`; `validate_bool` guarantees the rcParam is a genuine `bool` |
| `Text._antialiased` field / `Text.get_antialiased()` return | `Bool` (the `out` result) | Python `True`/`False` ↔ Lean `true`/`false` |
| `gc.set_antialiased(self._antialiased)` → `gc.get_antialiased()` plumbing in `draw()` and the backends | identity (omitted) | the GraphicsContext only TRANSPORTS the resolved boolean from the text object to the renderer; on the value it carries it is the identity (see refinement.md §B). Validated against the real objects by G-CONF. |

`bool` is a closed two-value domain; `Option Bool` is its faithful carrier with
the "unspecified" sentinel made explicit as `none`. No string/list modeling is
needed — the operation is a single scalar resolution.

## 3. Callee provenance and flag dependencies

No axioms and no deep-model references: `resolveAA` is a closed function of its
two boolean inputs (the explicit per-object choice and the ambient default).
There is no external callee whose behavior must be assumed.

The only repo callees touched by the patch are:
  * `GraphicsContextBase.set_antialiased` / a new `get_antialiased` — these
    STORE and return the boolean unchanged for the value content the F2P tests
    observe (the Cairo `get_antialiased` returns a `cairo.Antialias` enum, but
    that path is exercised only by image-comparison tests, see refinement.md §B);
  * `Text.set_antialiased` — stores the raw value into `Text._antialiased`
    (no `int(bool(...))` coercion, unlike the artist base class), so
    `get_antialiased()` returns exactly what was set.

**Flag dependency:** the resolution consults the explicit `antialiased`
argument FIRST (`is not None`), falling back to `rcParams['text.antialiased']`
only when it is `None`. G-CONF fuzzes both the argument over
`{None, True, False}` and the rcParam over `{True, False}` so every
configuration of the resolution is covered.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25775`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`textAntialiased`/`resolveAA` to Python and compares against the real patched
`Text` (and `Annotation`) object's `get_antialiased()` across the full
`{None,True,False} × {True,False}` argument/rcParam matrix plus fuzzed draws.
