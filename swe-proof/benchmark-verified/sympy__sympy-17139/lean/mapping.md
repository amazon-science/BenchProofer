# mapping.md — sympy__sympy-17139

## Symbol binding (file:line @ base_commit 1d3327b8e90a186df6972991963a5ae87053259d)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_powerRewrite` / `problem_spec_powerRewrite` / `correct_powerRewrite` | the inner rewrite function `_f(rv)` defined inside `_TR56` | `sympy/simplify/fu.py:496-522` |
| `rv` (input) | the argument `rv` of `_f` (a candidate power expression) | fu.py:496 |
| `isMatchingPow rv` (opaque callee) | `rv.is_Pow and rv.base.func == f` | fu.py:502 |
| `expIsReal rv` (opaque callee) | `rv.exp.is_real` | fu.py:504 (the ADDED guard) |
| `transform rv` (opaque callee) | the entire sign/magnitude-driven rewrite body (`rv.exp < 0`, `rv.exp > max`, `rv.exp == 2`, the perfect-power branch, `h(g(...)**2)**e`) | fu.py:506-521 |
| `result` | the value `_f` returns | fu.py:496-521 |

## The modeled behavior

`_f` is `bottom_up`'s per-node rewrite inside `_TR56` (the shared helper for `TR5`
and `TR6`). Post-patch (`fu.py:496-522`):

```python
def _f(rv):
    if not (rv.is_Pow and rv.base.func == f):
        return rv
    if not rv.exp.is_real:                 # <-- the added guard
        return rv
    if (rv.exp < 0) == True:
        return rv
    if (rv.exp > max) == True:
        return rv
    if rv.exp == 2:
        return h(g(rv.base.args[0])**2)
    else:
        ...                                # perfect-power / even-power rewrite
        return h(g(rv.base.args[0])**2)**e
```

The function makes an early-exit decision tree:

1. if `rv` is not a matching power (`is_Pow` and base head `== f`) → return `rv`
   unchanged;
2. **(added)** else if `rv.exp` is not real → return `rv` unchanged;
3. else apply the exponent-driven rewrite (sign / magnitude / perfect-power
   comparisons, producing `h(g(...)**2)**e` or leaving `rv` unchanged for
   sub-cases).

### The defect

Pre-patch `_f` lacked step 2. When `rv` is a matching power whose exponent is
COMPLEX (e.g. `cos(x)**I`, `cos(x)**(2 + 3*I)`), control fell straight into
`if (rv.exp < 0) == True:`. SymPy raises `TypeError: Invalid comparison of
complex I` when ordering a non-real number, so `simplify(cos(x)**I)` crashed
inside `TR6 → _TR56 → _f`. The fix adds the `rv.exp.is_real` guard so a matching
power with a non-real exponent is returned untouched, exactly matching the F2P
assertions `T(sin(x)**I, ...) == sin(x)**I` and `simplify(cos(x)**I) == cos(x)**I`.

### Lean modeling

The touched region is a control-flow guard inserted between an existing
structural test and an existing exponent-comparison body. The observable
soundness-critical behavior is *which of the three branches an input takes*. The
two branch conditions and the rewrite body are UNCHANGED callees; only their
ORCHESTRATION changed (a new short-circuit was inserted). Per SPEC_GUIDE §3, the
changed control flow is modeled DEEPLY (spelled out as the guarded `Id.run do`
early-return chain); the unchanged conditions/body are carried as opaque
signature-only callees that appear identically on spec and impl and so cancel:

- `rv : Expr`               — the candidate expression, an opaque `Nat` tag (only
  equality and the two boolean queries below are observed);
- `isMatchingPow : Expr → Bool` — the structural test `rv.is_Pow and rv.base.func == f`;
- `expIsReal : Expr → Bool`     — the added guard `rv.exp.is_real`;
- `transform : Expr → Expr`     — the exponent-driven rewrite body (whatever it
  returns for a matching real-exponent power, including the sub-cases that leave
  `rv` unchanged).

Post-patch decision (modeled op-for-op):

```
if not isMatchingPow rv then rv
else if not expIsReal rv then rv
else transform rv
```

Pre-patch (the bug):

```
if not isMatchingPow rv then rv
else transform rv                 # no realness guard: transform is entered for a
                                  # non-real exponent, which crashes in reality
```

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a candidate expression `rv` | `Expr` (`Nat` tag) | identity on the equivalence class observed via the two queries + `transform` |
| `rv.is_Pow and rv.base.func == f` | `isMatchingPow rv : Bool` | identity |
| `rv.exp.is_real` (as a definite truth value; `not X` where `X` is `True`/`False`) | `expIsReal rv : Bool` | identity — `True` when the exponent is a real quantity |
| the rewrite body's return value for a matching real-exponent power | `transform rv : Expr` | identity |
| `_f`'s return value | `result : Expr` | identity |

Note on `is_real`: in SymPy `rv.exp.is_real` is a fuzzy-bool (True/False/None);
`not rv.exp.is_real` is truthy for both `False` and `None`. The modeled boolean
`expIsReal` collapses this to the two observable outcomes that matter for branch
selection — "definitely real" (take the rewrite) vs "not definitely real" (skip),
which is exactly the branch `_f` takes. The F2P inputs have `is_real == True`
(real exponents unchanged behavior preserved) or `is_real == False`
(`cos(x)**I`), both cleanly represented.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The operation the patch changes
  is a CONTROL-FLOW guard (a new early return), modeled DEEPLY and structurally
  as the guarded `Id.run do` chain over the observable queries. SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed decision; the `axioms` region
  carries only opaque SIGNATURES (no `_prop`), so **G-AX skips**.
- `isMatchingPow`, `expIsReal`, `transform` are UNCHANGED operations (the patch
  adds a guard but does not alter the structural test, the realness query, or the
  rewrite body). They appear identically in the spec and the impl, so they cancel
  in the differential test; no property of any is consumed.
- Flag dependency: `_TR56` is parameterised by `f, g, h, max, pow`. These
  parameterise the structural test (`f`) and the rewrite body (`g, h, max, pow`),
  both folded into the opaque `isMatchingPow` / `transform`; the added realness
  guard is independent of all of them, so no flag needs fuzzing for the modeled
  decision. Recorded for G-AX completeness.

## G-CONF fuzz seed

Pinned LCG seed: **17139** (see `conformance_check.py` `SEED`). Corpus: randomized
expression tags each tagged with `(is_matching: bool, exp_real: bool)` plus a
`transform` result, so all three branches are exercised, with hand-picked edge
cases: a non-matching expression (unchanged), a matching real-exponent power (must
be transformed), and a matching NON-real-exponent power (the F2P case — must be
returned unchanged). The R/I shadow of `implementation_powerRewrite` is diffed
against an in-process replica of the POST-PATCH `_f` decision tree over ≥1e5
fuzzed inputs.
