# refinement.md — sympy__sympy-13372

Operation-by-operation correspondence between `implementation_reduceComponentsToFloat`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH fallback branch of
`evalf` in `sympy/core/evalf.py`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if rePart.hasUneval \|\| imPart.hasUneval then return .error ()` | `if re.has(re_) or im.has(im_): raise NotImplementedError` | R |
| 2 | `if rePart.kind = .zero then reOut := .null; reprec := none` | `if re == 0: re = None; reprec = None` | R |
| 3 | `else if rePart.kind = .number then reOut := .num rePart.mpf; reprec := some prec` | `elif re.is_number: re = re._to_mpmath(prec, allow_ints=False)._mpf_; reprec = prec` | R |
| 4 | `else return .error ()` (real chain) | `else: raise NotImplementedError`  ← **the fix** (line ~1300) | I |
| 5 | `if imPart.kind = .zero then imOut := .null; imprec := none` | `if im == 0: im = None; imprec = None` | R |
| 6 | `else if imPart.kind = .number then imOut := .num imPart.mpf; imprec := some prec` | `elif im.is_number: im = im._to_mpmath(prec, allow_ints=False)._mpf_; imprec = prec` | R |
| 7 | `else return .error ()` (imag chain) | `else: raise NotImplementedError`  ← **the fix** (line ~1306) | I |
| 8 | `return .ok (reOut, imOut, reprec, imprec)` | `r = re, im, reprec, imprec` (normal return of the fallback branch) | R |

## Notes

- **Every step is R or I — no A.** The patch is a pure control-flow guard; it
  calls no new callee. The one callee on the changed lines,
  `._to_mpmath(...)._mpf_` (step 3/6), produces a value that the fix neither
  inspects nor re-derives — it is threaded through unchanged as the carried
  `EvalfPart.mpf` payload. SPEC_GUIDE §3 forbids axiomatizing it (it is not even
  a *changed* op needing deep modeling — it is a passthrough), so the `axioms`
  region is empty and **G-AX skips**.

- **The fix itself is steps 4 and 7** (tag **I**, exact transliteration of the
  added `else: raise NotImplementedError`). Pre-patch, the real/imaginary
  cascades have only the `if … elif …` arms; a component that is neither zero nor
  a concrete number (i.e. `.symbolic` — e.g. an unevaluated `Max(0, y)`) falls
  through with `reprec`/`imprec` (and `re`/`im`) **unassigned**. Python then
  raises `UnboundLocalError` at `r = re, im, reprec, imprec`; the modeled
  analogue is that the malformed four-tuple is still assembled and reported as
  `.ok` with a `.sym`/default in the unfilled positions. The pre-patch impl
  (`Solution_prepatch.lean`) drops steps 4 and 7, so on a `.symbolic` component it
  returns `.ok (…, .sym, …)` where the spec requires `.error ()`; its carried gold
  proof fails to typecheck (G-DIFF).

- **R vs I.** Steps 4, 7 are **I** (the added `else: raise` ↔ `return .error ()`,
  a literal control-flow transliteration). Steps 1–3, 5–6, 8 are **R**: the
  Python expression objects (`re`, `im`, the raise/return, the tuple) are refined
  to the `EvalfPart` classification carrier and the `Except Unit EvalfTuple`
  result per the mapping.md bijection (`re == 0` ↔ `.kind = .zero`,
  `re.is_number` ↔ `.kind = .number`, neither ↔ `.kind = .symbolic`;
  `re.has(re_)` ↔ `hasUneval`; the `_mpf_` value ↔ the `floatVal` payload;
  `None`/`prec` ↔ `none`/`some prec`).

- **G-CONF** mechanically refutes the R/I legs: an in-process replica of the
  POST-PATCH fallback branch (raising on the symbolic/uneval cases) is diffed
  against the impl shadow over ≥1e5 fuzzed classified inputs. No A legs.
