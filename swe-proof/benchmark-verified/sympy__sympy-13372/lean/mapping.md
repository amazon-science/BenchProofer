# mapping.md — sympy__sympy-13372

## Symbol binding (file:line @ base_commit `30379ea6e2`)

The modeled routine is the fallback (`except KeyError`) branch of
`evalf(x, prec, options)` in `sympy/core/evalf.py`, lines **1289–1312** @
base_commit. Specifically the block that reduces the real and imaginary parts of
`x._eval_evalf(prec)` to the four-tuple `r = re, im, reprec, imprec` (lines
1295–1310). The gold patch inserts two `else: raise NotImplementedError` clauses
at lines 1300+ (after the `elif re.is_number` chain) and 1306+ (after the
`elif im.is_number` chain).

| Python (evalf.py @ base) | Lean (Solution.lean) |
|---|---|
| `re, im = xe.as_real_imag()` (the two components) | the inputs `rePart imPart : EvalfPart` |
| `if re.has(re_) or im.has(im_): raise NotImplementedError` (line 1296–1297) | `rePart.hasUneval \|\| imPart.hasUneval` ⇒ `.error ()` |
| `re == 0` / `im == 0` | `EvalfPart.kind = .zero` |
| `re.is_number` / `im.is_number` (and not `== 0`) | `EvalfPart.kind = .number` |
| neither zero nor number (the unhandled case) | `EvalfPart.kind = .symbolic` |
| `re = re._to_mpmath(prec, allow_ints=False)._mpf_` | `evalfPartOut p = .num p.floatVal` (the mpf value carried as the `floatVal` field) |
| `re = None` (the `re == 0` leg) | `evalfPartOut p = .null` |
| `reprec = prec` / `reprec = None` | `evalfPartPrec p prec = some prec` / `none` |
| `r = re, im, reprec, imprec` | `.ok (reOut, imOut, reprec, imprec) : EvalfTuple` |
| (post-patch) `else: raise NotImplementedError` | `.symbolic` ⇒ `.error ()` |
| the whole reduction succeeding vs raising `NotImplementedError` | `Except Unit EvalfTuple` (`.ok` vs `.error ()`) |

## Type bijection (Lean ↔ Python)

- `EvalfPart` is the abstract classification of one component of
  `xe.as_real_imag()`. Its three fields capture exactly the observables the
  Python branch reads:
  - `kind : EvalfPartKind` — the trichotomy `{re == 0 ; re.is_number ; neither}`.
    `.is_number` is checked only when `!= 0`, so the three kinds are mutually
    exclusive, matching the `if/elif/else` cascade.
  - `mpf : Int` — the machine-float value `re._to_mpmath(...)._mpf_` reduces to,
    used only on the `.number` leg. Modeled as `Int` because the value is an
    opaque carried payload — the fix never inspects it; we only require it be
    threaded through unchanged. (G-CONF treats it as an opaque token.)
  - `hasUneval : Bool` — whether the component still contains an unevaluated
    symbolic real/imaginary marker, i.e. `re.has(re_) or im.has(im_)` is true for
    *that* component. The Python `if` short-circuits on the OR of both
    components; the Lean impl ORs `rePart.hasUneval || imPart.hasUneval`,
    identical.
- `EvalfTuple = EvalfPartOut × EvalfPartOut × Option Nat × Option Nat` ↔ the
  Python tuple `(re, im, reprec, imprec)` where `re`/`im` ∈ {`None`, an mpf
  value} and `reprec`/`imprec` ∈ {`None`, `prec`}. `EvalfPartOut.sym` is the
  out-of-band "value was never assigned" marker that the pre-patch code would
  leave (`UnboundLocalError` in Python = referencing an unassigned local); a
  `.sym` in any position, or the whole result being malformed, is the modeled
  bug.
- `Except Unit EvalfTuple` ↔ {return the tuple normally} vs {raise
  `NotImplementedError`}. `Unit` because the raised exception carries no payload
  the caller inspects (it is caught as a fallback signal).

## Callee provenance / flag deps

None consumed. The only callee on the changed lines is `._to_mpmath(...)._mpf_`,
whose *result* is modeled as the carried `floatVal` payload and is NOT
re-derived/inspected by the fix — the patch is purely a control-flow guard
(adding `else: raise`). There is therefore no unchanged-callee contract the proof
consumes (no A-consumed) and no deeply-modeled changed callee (no A-reference).
G-AX skips.

## G-CONF fuzz seed

Pinned seed: **13372** (also recorded in meta.json `verifier_pins.conf_seed`).
