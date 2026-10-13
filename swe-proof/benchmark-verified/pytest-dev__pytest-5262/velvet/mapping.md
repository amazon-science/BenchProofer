# mapping.md — pytest-dev__pytest-5262

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed. Read with `refinement.md`. All locations are at
`base_commit = 58e6a09db49f34886ff13f3b7520dd0bcd7063cd`.

## 1. Symbol binding

| Lean symbol (`Solution.lean`) | repo symbol | location @ base_commit |
|---|---|---|
| `method textStreamMode` | the `mode` property added to `EncodedFile` | `src/_pytest/capture.py`, `class EncodedFile` (def at line 425) — the property is newly introduced by the patch at line 447–449 |
| param `rawMode : List Char` | `self.buffer.mode` (the wrapped stream's mode descriptor, a `str`) | accessed inside the new property body |
| result `out : List Char` | the property's return value, a `str` | returned from the new property body |
| `stripped : List Char → List Char` (pure) | the substitution `str.replace("b", "")` | the `.replace("b", "")` call in the patch |
| `stripStep : Char → List Char` (pure) | the per-code-point image of that substitution | — (deep-model decomposition) |

The patched function is a NEW property; `EncodedFile` previously resolved
attribute `mode` via `__getattr__` (line 450), which delegates to
`object.__getattribute__(self, "buffer")` — i.e. it returned the wrapped byte
stream's mode descriptor **unchanged** (still carrying the binary marker). That
unchanged-delegation is the pre-patch behavior modeled in
`Solution_prepatch.lean` (the identity `do` block).

## 2. Type bijection (used by G-CONF and G-AX)

| repo reality (Python) | Lean model | bridge |
|---|---|---|
| `str` mode descriptor (per-code-point op) | `List Char` | `ch ↔ Char.ofNat (ord ch)`; `s : str ↔ s.toList`; SPEC_GUIDE §2 row 1 |
| `str.replace("b", "")` | `stripped : List Char → List Char` | per-code-point: drop code point 98 (`'b'`), keep others, order preserved |
| `len(s)` | `s.length` | — |
| the property is a read-only getter; mutates nothing | `method` with no `mut` carrier (directive 5: nothing declared `mut`, nothing to frame) | — |

`str.replace("b", "")` removes EVERY occurrence of the substring `"b"`. Since the
search string is a single code point, this is exactly the per-code-point fold
`stripped`: each `'b'` contributes `[]`, every other code point contributes
itself, order preserved. (`str.replace` with a single-char search and empty
replacement coincides with the per-code-point filter — no overlap subtleties,
verified by G-AX over the full boundary + fuzz set.)

## 3. Callee provenance & flag dependencies

- **No consumed axioms.** The only operation the new property performs is the
  string substitution `self.buffer.mode.replace("b", "")`. The accessor
  `self.buffer.mode` is the *input* to the modeled function (bound to `rawMode`),
  not a callee whose contract the proof consumes; we read it as data.
- **`str.replace("b", "")` is an A-reference**, not a consumed axiom: it is the
  changed operation, modeled DEEPLY as `stripped`/`stripStep` (spelled out, the
  verified loop IS the substitution). G-AX (`axiom_check.py`) validates that the
  deep model equals the real CPython `str.replace("b", "")` over boundary + fuzz.
  There is no flag dependency (no keyword arguments).

## 4. G-CONF fuzz seed

Pinned seed: **5262** (`conformance_check.py` `SEED = 5262`, `N_FUZZ = 100_000`).
Boundary set includes the F2P-relevant descriptors: `"rb+"` (the exact value the
issue reports, whose wrapped fileno is dup'd with mode `"rb+"`), `"rb"`, `"wb"`,
`"b"`, `"bb"`, `""`, and the binary-free `"r"`, `"w"`, `"r+"`, plus mixtures.
