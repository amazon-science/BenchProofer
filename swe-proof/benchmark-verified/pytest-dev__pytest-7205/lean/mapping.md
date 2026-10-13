# mapping.md — symbol binding & type bijection (pytest-dev__pytest-7205)

## Modeled function
- **Lean** `implementation_actionLine : List Char → Option (List Char) → List Char`
- **Python** `_show_fixture_action(fixturedef, msg)` in
  `src/_pytest/setuponly.py:46-71 @ 5e7f1ab4bf` — specifically the parameter-
  rendering tail (lines 68-69 pre-patch / 68-69 post-patch):

  ```python
  if hasattr(fixturedef, "cached_param"):
      tw.write("[{}]".format(saferepr(fixturedef.cached_param, maxsize=42)))
  ```

The function builds a one-line textual report for a fixture setup/teardown
action. It writes a fixed header (step / scope / fixture name, and optionally a
"fixtures used: …" suffix), then — *only if the action carries a parameter
value* (`hasattr(fixturedef, "cached_param")`) — appends that value's
representation enclosed in `[` … `]`. The modeled function captures exactly this
tail: a header (everything written before the bracketed parameter) plus the
optional bracketed parameter rendering.

The change replaces the implicit textual coercion of the parameter
(`"[{}]".format(value)`, i.e. `str(value)`) with a safe, size-limited
representation `saferepr(value, maxsize=42)`. The header and the
present-vs-absent branch are unchanged (frame, directive 5).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| header text written before the bracket (`step scope fixture …`) | `header : List Char` | unchanged framing input; passed through verbatim |
| `hasattr(fixturedef, "cached_param")` | `param : Option (List Char)` | `some p` ⇔ attribute present with value `p`; `none` ⇔ absent |
| `fixturedef.cached_param` (the parameter value) | `p : List Char` | the value's own textual content (its `str` form), as a code-point sequence |
| `str(value)` (pre-patch implicit coercion) | `p` (identity) | for a textual value, implicit `str()` is the identity on its characters |
| `saferepr(value, maxsize=42)` | `safeDisplay p` | the safe, size-limited canonical representation; opaque callee. The reporter's fixed size budget (the `maxsize` argument) is absorbed into the opaque symbol — it is an internal formatting detail of the callee application, not an observable the spec needs to (or may) pin. |
| literal `[` / `]` | `['[']` / `[']']` | bracket delimiters, unchanged |

`fixturedef.cached_param` may be any Python object (str, bytes, int, …). The
modeled `List Char` is the *textual content* of that value as fed to the
representation step; `safeDisplay` is the opaque transformation applied to it.
The discriminating observable (F2P) is that a string parameter `foo` is rendered
`'foo'` (quoted repr) rather than `foo` (bare), and a `bytes` parameter no longer
raises under `-bb`.

## Callee provenance
- `safeDisplay` ← `_pytest._io.saferepr.saferepr`
  (`src/_pytest/_io/saferepr.py:75-82 @ 5e7f1ab4bf`), as applied with the
  reporter's fixed size budget. An **UNCHANGED** callee the fix newly *calls*
  but does not modify. Declared `opaque safeDisplay : List Char → List Char`
  (signature only) per §0.7; it is **A-consumed** (the proof only needs that
  the bracketed rendering equals `safeDisplay p`; no concrete formatting
  property is asserted, and the callee's size budget is internal to the opaque
  symbol). G-AX validates the opaque signature is total / well-typed against
  the real `saferepr` application (it accepts a value and returns a string) on
  boundary + fuzz inputs.
- No other callees.

## Flag dependency
None for the modeled tail. (The surrounding `_show_fixture_action` is only
reached under `--setup-show` / `--setup-only`, but that gating is outside the
modeled parameter-rendering tail.)

## G-CONF fuzz seed
Pinned seed: **7205**. ≥10^5 fuzzed inputs: random headers, present/absent
parameter, and parameter values drawn from strings, bytes-like, and arbitrary
code points. The single A-consumed op (`safeDisplay`) is left as the REAL
`saferepr(..., maxsize=42)` builtin in the shadow.
