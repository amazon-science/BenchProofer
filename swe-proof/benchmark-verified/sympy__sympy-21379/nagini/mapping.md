# mapping.md — sympy__sympy-21379

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 624217179aaf8d094e6ff75b7493ad1ee47599b0`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/core/mod.py` (the `Mod.eval` classmethod, the
"extract gcd" block).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_extract_common_factor(code, p, q)` | the "extract gcd" block of `Mod.eval(cls, p, q)` — `sympy/core/mod.py:38` (block at body lines 168–172) | the modeled changed code: the optional common-factor extraction the reduction performs before finishing, plus the value the block feeds into the tail (`return G*cls(p, q, …)`) |
| `common_factor(code)` *(axiom — A-consumed, value facet)* | `sympy.gcd` — `sympy/polys/polytools.py:5281`, called as `gcd(p, q)` at `sympy/core/mod.py:169` | the unchanged `gcd` call's *value* on a shape it can handle; usable inside `Ensures`. The impl rebinds `G = common_factor(code)` after the raising-facet call so the factor is syntactically the value facet (Nagini does not apply function congruence from a *derived* `G == common_factor(code)` to a `@ContractOnly` callee's arguments). |
| `common_factor_compute(code)` *(axiom — A-consumed, raising facet)* | the same `gcd(p, q)` call at `sympy/core/mod.py:169` | the unchanged `gcd` call as actually CALLED — it may RAISE on the case-split shape. Same call as `common_factor`; the two facets split one `gcd(p, q)`. |
| `divide_out(value, factor)` *(axiom — A-consumed)* | `gcd_terms(i/G, clear=False, fraction=False)` — `sympy.core.exprtools.gcd_terms` (`sympy/core/exprtools.py:989`), called at `sympy/core/mod.py:171–172` | the unchanged divide-and-regroup helper applied to each operand when the factor is non-trivial; OPAQUE value (makes the operand rewrite observable, §4.2) |
| `build_result(factor, p, q)` *(axiom — A-consumed)* | the value the block feeds into `Mod.eval`'s tail: `G*cls(p, q, …)` (the unchanged `Mul`/`Mod` construction at `sympy/core/mod.py` after the block) | the result the block produces from the factor and the (possibly rewritten) operands; OPAQUE so the value depends observably on whether each operand was rewritten (§4.3) |
| `FactorUnavailable` (exception) | `sympy.polys.polyerrors.PolynomialError` (`sympy/polys/polyerrors.py:115`), raised by `gcd` via `_parallel_poly_from_expr` at `sympy/polys/polytools.py:4399` ("Piecewise generators do not make sense") | the `gcd` call's raise on the case-split shape; a user-defined exception stands in (a builtin exception in `Exsures` crashes the translator, SPEC_GUIDE §2) |

The pre-patch code the change wraps (for the refinement audit, not referenced
from the consumer spec view):

```python
# sympy/core/mod.py:168-172 @ base_commit
# extract gcd; any further simplification should be done by the user
G = gcd(p, q)
if G != 1:
    p, q = [
        gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]
```

The `gcd(p, q)` call is UNGUARDED: when `p` or `q` is built from a `Piecewise`
(a case-split construct), `gcd` raises `PolynomialError`, which propagates out
of `Mod.eval` and up through whatever assumptions query triggered the `Mod`
(e.g. `sinh._eval_is_real` doing `(im % pi).is_zero`), surfacing as the
reported error. The gold patch wraps the block in `try/except PolynomialError`
and sets `G = S.One` on the exception.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the dividend/divisor pair `(p, q)` (SymPy `Expr`) | an integer operand-shape `code` (0/1/2) plus two integer value carriers `p`, `q` | the pair `(p, q)` ↔ `code`, which records only the one facet deciding the branch: whether the common-factor routine is well-defined for the shape and whether the factor it yields is trivial (see §3). The operand *values* `p`, `q` are opaque integer carriers — only their (un)changed-ness matters to the tested behaviour. |
| `G = gcd(p, q)` (a SymPy `Expr` factor) | an `int` factor `G` | the multiplicative identity `S.One` ↔ `1`; any genuine common factor ↔ an opaque value `!= 1`. The F2P observes only whether `G` is trivial (so the division is skipped) and that no error escapes — not the concrete factor. |
| `p, q = [gcd_terms(i/G, …) for i in (p, q)]` | `p = divide_out(p, G); q = divide_out(q, G)` | each operand is rewritten by dividing the non-trivial factor out via the unchanged helper; the rewritten value is opaque (the tested behaviour does not read it on the Piecewise path, where this branch is not taken at all). |
| `raise PolynomialError(...)` from `gcd` | `raise FactorUnavailable()` from `common_factor_compute` | the routine's refusal; user-defined exception per SPEC_GUIDE §2. |
| `G = S.One` (the fix's except body) | `G = 1` | the trivial factor; with `G == 1` the `if G != 1` branch is skipped and the operands are left unchanged — exactly the gold patch's behaviour on the refusal. |

SymPy `Expr` objects cannot be indexed/inspected in Nagini specs, so the operand
pair is abstracted to the integer shape code carrying exactly the facet the
branch reads, plus opaque value carriers for the operands.

## 3. The operand-shape code table

Each `(p, q)` operand pair is abstracted to one of three shape codes over
`(common-factor routine well-defined?, factor trivial?)`:

| code | `gcd(p, q)` behaviour | factor | example pair | model facet |
|---|---|---|---|---|
| 0 | returns NORMALLY a non-trivial factor | `!= 1` | `(2*x, 2*y)` → `2`; `(6, 9)` → `3`; `(x**2-1, x**2-3*x+2)` → `x-1` | `common_factor(0) != 1` |
| 1 | returns NORMALLY the trivial factor | `1` | `(x, y)` → `1`; `(7, 13)` → `1` | `common_factor(1) == 1` |
| 2 | REFUSES — raises `PolynomialError` | (none) | `(Piecewise((x,y>x),(y,True))/z, 1)`; `(Piecewise(...), x)` | `Exsures(FactorUnavailable, code==2)` |

- **The case-split shape (code 2)** is exactly the operand pair from the issue:
  a `Piecewise` (case-split) construct, possibly divided by a symbol, handed to
  `gcd`. `gcd` builds polynomial generators and rejects a `Piecewise` generator
  ("Piecewise generators do not make sense", `polytools.py:4399`).
- The fix's behaviour on code 2 — `G = S.One`, operands unchanged, no error —
  is `Result() == 1` with `p`, `q` not rewritten (the `if G != 1` branch is
  unreachable because `G == 1`).

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `common_factor` / `common_factor_compute` ↔ `sympy.gcd` (A-consumed)
**Callee:** `sympy.gcd(f, g)` (`sympy/polys/polytools.py:5281`), unchanged by the
fix. It forms polynomial generators from its arguments
(`parallel_poly_from_expr` → `_parallel_poly_from_expr`, `polytools.py:4340/4399`)
and, for any generator that is a `Piecewise`, raises
`PolynomialError("Piecewise generators do not make sense")`. For ordinary
algebraic operands it returns the GCD as an `Expr` (the multiplicative identity
`S.One` when the operands share no factor).

The axiom is split into the WEAKEST two facets the proof needs:

  - `common_factor(code)` — `@Pure @ContractOnly`, usable inside `Ensures`:
    encodes only the *value* on the handleable shapes: `common_factor(1) == 1`
    (trivial), `common_factor(0) != 1` (a genuine, OPAQUE non-trivial factor —
    the exact value is unpinned so a caller can obtain it only by invoking the
    routine, never by fabricating a literal, SPEC_GUIDE §8).
  - `common_factor_compute(code)` — non-pure `@ContractOnly` (it may refuse):
    `Ensures(code != 2)` and `Ensures(Result() == common_factor(code))` for the
    normal-return shapes, and `Exsures(FactorUnavailable, code == 2)` for the
    case-split shape. This is the call as the reduction makes it.

It does **not** claim the concrete factor value on code 0 (not needed by the
tested behaviour) — only that the call is well-defined and the result equals the
routine's own (opaque) output, so the result is grounded in the modeled
computation rather than a hardcoded tag. Sound precisely because the change
never touches `gcd`; it only wraps the *call site* in `try/except`.

### 4.2 `divide_out` ↔ `gcd_terms` (A-consumed)
**Callee:** `sympy.core.exprtools.gcd_terms(terms, clear=False, fraction=False)`
(`sympy/core/exprtools.py:989`), unchanged by the fix. Applied to `i/G` for each
operand `i` when the extracted factor `G` is non-trivial (`mod.py:171–172`). The
axiom requires only `factor != 1` (the guard under which the real call is made)
and pins NO value — the result is OPAQUE. Soundness needs nothing more than that
`gcd_terms` is total under the guard (it is). The opacity is load-bearing for
*spec strength*, not soundness: because the model cannot prove
`divide_out(p, G) == p`, only an impl that actually performs the regroup can
discharge clause (3a) — closing the G-EQ hole the verdict found. Sound: the
change does not touch `gcd_terms`; it only reaches it under the unchanged
`if G != 1` guard.

### 4.3 `build_result` ↔ the block's `G*cls(p, q, …)` construction (A-consumed)
**Callee:** the unchanged `Mul`/`Mod` construction `Mod.eval` performs after the
block (`G*cls(p, q, …)`), built from the factor `G` and the (possibly rewritten)
operands `p`, `q`. Modeled as the OPAQUE `build_result(factor, p, q)`
(`Ensures(True)`): two applications are equal only when all three arguments are
provably equal. This is what makes the operand rewrite *observable* in the
postcondition — the abstraction no longer discards the operand post-state (the
exact defect the verdict flagged). Sound: the construction is unchanged by the
fix; the model only needs that the produced value is a function of `(G, p, q)`.

**Soundness check (G-AX):** `axiom_check.py` imports `sympy` (the patched repo,
on PYTHONPATH in-container) and exercises the real `gcd` + the real regroup:
  * 7 code-0 operand pairs (shared factor): asserts `gcd` returns normally and
    `!= 1` (the `common_factor(0) != 1` Ensures);
  * 6 code-1 pairs (coprime): asserts `gcd` returns normally and `== 1`
    (the `common_factor(1) == 1` Ensures);
  * 5 code-2 pairs (a `Piecewise` / case-split argument, incl. the issue's
    `Piecewise/z`): asserts `gcd` RAISES `PolynomialError` — so the raise branch
    and the fix's `try/except` are load-bearing;
  * end-to-end refusal path (gold fix applied): asserts the FAIL_TO_PASS
    operations — the `Mod` over a `Piecewise/z` argument and the `is_zero`
    queries that trigger it (via `sinh/cosh/tanh._eval_is_real` doing
    `(im % pi).is_zero`) — COMPLETE without raising, and that `(Piecewise/z) % 1`
    stays an unevaluated `Mod` (G == 1, operands unchanged);
  * end-to-end transform path (gold fix applied): asserts the code-0 operand
    rewrite is real — `(12*x + 18*y) % (3*x) == 3*Mod(6*y, x)` (the F2P
    `test_Mod`'s own pre-existing assertion: factor 3 is divided out of each
    operand before the result is built) and a second corroborating case. These
    witness that `divide_out` / `build_result` faithfully model the regroup that
    the strengthened spec now makes load-bearing.
Exit 0 iff every observation holds. Imports only `sympy`; nothing
bundle-specific.

## 5. Termination obligation (total correctness)

The real block is a bounded, straight-line computation: one `gcd` call, an
optional pair of `gcd_terms` calls, one construction — it always finishes
(normally pre-fix on codes 0/1, by raising on code 2; always normally
post-fix). Nagini is a **partial-correctness** verifier by default, so a value
postcondition alone admits an implementation that DIVERGES before returning
(e.g. an unbounded loop inserted ahead of the `gcd` call): every `Ensures` is
then satisfied vacuously, yet the faithful real patch would hang `Mod.eval` —
and the F2P — forever (the audit's divergence attack). The spec therefore
carries the obligation explicitly:

  * `reduce_extract_common_factor` — `Requires(MustTerminate(2))`: the
    operation must terminate and actually deliver its value to the caller.
  * `common_factor_compute` — `Requires(MustTerminate(1))`: the single
    factor-producing call is one bounded step of the real `gcd` (which always
    returns or raises on in-domain shapes); the strictly smaller measure
    (1 < 2) lets the contracted caller invoke it without leaking its own
    obligation. The `@Pure` axioms (`common_factor`, `divide_out`,
    `build_result`) are mathematical functions and need no obligation (pure
    calls are terminating by construction in Nagini).

Soundness: asserting that the real block terminates claims nothing beyond what
the real callees provide — `gcd`/`gcd_terms`/the `Mul`/`Mod` construction are
all terminating library routines (G-AX exercises each of them to completion on
every shape code), and the block itself contains no loop or recursion.

## G-CONF (differential conformance)

`conformance_check.py` refutes the REFINEMENT leg: does the MODEL agree with the
REAL patched repo code? (G-VERIFY checks impl-vs-spec and G-PBT checks
spec-strength; neither one looks at the repository.)

**Pinned seed: `SEED = 21379`.** Inputs: **100 000** Requires-satisfying operand
pairs — a 39-case boundary catalogue first, then seeded fuzz — of which a sample
(the whole catalogue) is additionally observed *in situ*.

**Shadow.** The `# impl-start` … `# impl-end` region of `model.py`, copied
VERBATIM — byte-for-byte including comments, with ONLY the two `Assert(...)`
contract calls removed (no other contract call occurs inside the region, and the
`pure` region is empty per model.py lines 118-121, so no `@Pure` helper needed
copying). The `G = common_factor(code)` rebinding §1 explains is kept as
written, so the shadow re-invokes the real `gcd` twice exactly as the model does.
No `PSeq`/`ToSeq` carrier appears in this model, so no sequence shim is needed.
(Checked mechanically: the region, contract-stripped, is line-identical to the
shadow.)

**@ContractOnly bridges — the REAL callees (§1/§4), not models of them.**

| model callee | real repo callee it is bridged to |
|---|---|
| `common_factor_compute(code)` | `sympy.gcd(p, q)` as called at `sympy/core/mod.py:169` @ base_commit (raising facet; `PolynomialError` re-signalled as `FactorUnavailable`) |
| `common_factor(code)` | the same `sympy.gcd(p, q)` (value facet) |
| `divide_out(value, factor)` | `gcd_terms(value/factor, clear=False, fraction=False)` at `sympy/core/mod.py:171-172` |
| `build_result(factor, p, q)` | the tail construction `G*cls(p, q, …)`, performed by calling the real `Mod` |

So the §4 axioms are EXERCISED, not assumed.

**Oracle — the real patched block, extracted/driven, never reimplemented.** The
modeled unit is a block *inside* `Mod.eval` (§1), not a callable, and `Mod.eval`
keeps rewriting `G`/`p`/`q` afterwards, so its final return value would compare
the model against a dozen unmodeled statements. Two legs instead:

* **ORACLE-A** (all 100 000 inputs): `inspect.getsourcelines(Mod.eval)` on the
  PATCHED module, slice the block between the `extract gcd` comment and
  `pwas, qwas = p, q`, then `compile`/`exec` those exact source bytes per input.
  The oracle is the repository's own characters; the callee namespace comes from
  exec'ing `Mod.eval`'s OWN local `from sympy… import` lines, so `gcd`,
  `gcd_terms`, `S` and `PolynomialError` are the very objects the real function
  binds. `_assert_patched()` aborts unless the patched `except PolynomialError`
  recovery is present, so a green verdict cannot come from unpatched code
  (verified: on an unpatched /testbed the script refuses with `G-CONF ERROR` and
  exit 2 — it does not pass).
* **ORACLE-B** (the boundary catalogue): the real `Mod.eval` **called**, under a
  line tracer that reads `(G, p, q)` out of its live outermost frame at
  `pwas, qwas = p, q` and records whether the patched `G = S.One` recovery line
  executed. ~13 ms/input vs ~25 µs for ORACLE-A, hence the sample; it is what
  licenses ORACLE-A as a faithful driver rather than a convenient paraphrase.
  Any A/B disagreement fails the run, as does a recovery arm taken on any shape
  other than code 2.

**Type bridge (§2, inverted).** `(p, q)` `Expr` pair → shape `code` by OBSERVING
the real `gcd` (raises `PolynomialError` → 2, returns 1 → 1, else → 0: exactly
§3's table), via a probe call separate from the shadow's own call; the opaque
operand carriers `p`, `q` → the real `Expr` operands themselves (§2: only their
(un)changed-ness matters, and the impl never inspects them), with structural
`Expr` equality as carrier equality; factor `1` → `S.One` (and any `G == 1`,
including the `Float(1.0)` a Float pair yields); `FactorUnavailable` →
`PolynomialError`. Generation runs in the CONCRETE direction (draw a real pair,
read its code off the real `gcd`), so **every** input satisfies
`Requires(0 <= code <= 2)` by construction and none is manufactured to fit a
branch. Pairs whose `gcd` raises something other than `PolynomialError` fall
outside §3's table, and are counted as `out_of_domain` rather than silently
dropped (observed: 0).

**Comparison.** Per input, the `(factor, p, q, built)` tuple — the arguments
handed to the tail construction plus the value it constructs — compared by
`srepr` structural identity, not mathematical `==`, so `S.One` vs `Float(1.0)`
is a disagreement rather than an excused difference. A shadow raise is itself a
disagreement (the spec has no `Exsures`).

**Anti-vacuity.** The run FAILS unless every shape code and every impl branch
carries ≥ 1 % of the checked inputs, and unless both F2P dividend shapes
(`Piecewise((x, y > x), (y, True))/z` and the `z ** -1.0` variant) are observed
taking the patched recovery arm inside the real `Mod.eval`. Mutation controls
confirm the check can fail — each of these was CAUGHT: shadow skipping the
`if G != 1` transform; shadow letting the refusal escape (the pre-patch
behaviour, i.e. the bug); shadow returning a non-identity factor on the refusal
path; a `divide_out` bridge that reimplements `value/factor` instead of calling
`gcd_terms`; a generator that dodges the Piecewise leg (fails the 1 % floor);
and an unpatched oracle module.

**Recorded run** (the gate's own stamped report, seed 21379): 100 000 inputs,
shape codes {0: 44031, 1: 21700, 2: 34269}, branches {transform: 44031,
no_transform: 21700, refusal: 34269}, 39 boundary cases traced in situ (24
reaching the block; the rest are pairs `Mod.eval` returns early on), 2/2 F2P
shapes observed recovering in situ, 0 out-of-domain, **0 disagreements**
(exit 0, ~194 s in-container).
