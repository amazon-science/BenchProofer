# refinement.md — sympy__sympy-21379

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduce_extract_common_factor` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed**, the proof uses the axiom's `Ensures`/`Exsures`; or
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural hunk — `Mod.eval`, the "extract gcd" block (`sympy/core/mod.py:168-172`)

Gold hunk:
```
- G = gcd(p, q)
- if G != 1:
-     p, q = [
-         gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]
+ try:
+     G = gcd(p, q)
+     if G != 1:
+         p, q = [gcd_terms(i/G, clear=False, fraction=False)
+                 for i in (p, q)]
+ except PolynomialError:  # issue 21373
+     G = S.One
```
(plus a one-line import `from sympy.polys.polyerrors import PolynomialError`.)

The modeled function returns the value the block ultimately feeds into
`Mod.eval`'s tail (`pwas, qwas = p, q; … return G*cls(p, q, …)`): a value built
from the factor `G` together with the (possibly rewritten) operands `p`, `q`.
Modeling that value (rather than just `G`) is what makes the operand rewrite an
*observable* part of the postcondition — the fix the verdict required (G-EQ).

| # | model.py impl op (`reduce_extract_common_factor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `code: int`, `p: int`, `q: int` | the `(p, q)` operand pair of `Mod.eval` at the block | R | the `(p, q)` SymPy pair ↔ the integer case `code` (the one facet the branch reads: helper-defined? factor identity?) + opaque value carriers `p`, `q` (mapping.md §2–3). `p`, `q` are read-only (never reassigned in the impl; directive 5). |
| A2 | `G = common_factor_compute(code)` (inside `try`); `G = common_factor(code)` rebind | `G = gcd(p, q)` (inside `try`) | A-consumed | the SINGLE unchanged `gcd(p, q)` call, split into its two facets of the SAME call: the raising facet `common_factor_compute` (`Exsures(FactorUnavailable, code==2)`, consumed to prove the `try/except` catches the only possible exception) and the value facet `common_factor` (the normal return, `Ensures(Result()==common_factor(code))`). The proof rebinds `G = common_factor(code)` so the factor is syntactically the pure-facet value — needed because Nagini does not apply function congruence from a *derived* equality `G == common_factor(code)` to a `@ContractOnly` callee's arguments (measured 2026-06-15). This introduces no new value (`common_factor_compute` already ensures the two are equal); it only makes the value available to the postcondition. G-AX runs the real `gcd` (mapping.md §4.1). |
| A3 | `if G != 1: pr = divide_out(p, G); qr = divide_out(q, G)` | `if G != 1: p, q = [gcd_terms(i/G, …) for i in (p, q)]` | R + A-consumed | identical guard `G != 1`; the list-comprehension rewrite of each operand ↔ two calls of the unchanged `gcd_terms` helper, axiomatized as `divide_out` (`Requires(factor != 1)`, value OPAQUE; mapping.md §4.2). The opaque value is what forces a verifying impl to actually perform the rewrite (see §B). |
| A4 | `return build_result(G, pr, qr)` (inside `try`) | the block ends; `G`, `p`, `q` flow into `pwas, qwas = p, q; … return G*cls(p, q, …)` | R + A-consumed | the value the block produces is built from the factor and the (possibly rewritten) operands, axiomatized as the OPAQUE `build_result` (the unchanged `Mul`/`Mod` construction; mapping.md §4.3). Two applications are equal only when their three arguments are provably equal, so the value observably depends on whether each operand was rewritten. |
| A5 | `except FactorUnavailable: return build_result(1, pr, qr)` | `except PolynomialError: G = S.One` (then the block's tail builds the value from the unchanged operands) | R + I | `FactorUnavailable` ↔ `PolynomialError` (mapping.md §1); `1` ↔ `S.One`. On the raise the factor becomes the identity, the `if G != 1` branch is unreachable, the operands stay unchanged, and — crucially — NO exception escapes. |

The discriminating content of the change — wrapping the factor-producing call so
the helper's raise **no longer escapes** to the caller and instead yields the
identity factor — lives in the `try/except` around A2–A4 and the no-`Exsures`
postcondition. The pre-patch code performs A2 UNGUARDED; `model_prepatch.py`
reproduces that (`G = common_factor_compute(code)` with no `try/except`) and
**fails** the frozen spec's no-exception obligation, exactly the spec sensing the
bug (G-DIFF):

```
model_prepatch.py: error: Exhale might fail.
Assertion "method raises no exceptions" might not hold.
```

For the unanswerable input (`code == 2`, the issue's `Piecewise/z`): pre-patch
the raise propagates out of `Mod.eval` (and up through the `is_zero` assumptions
query that triggered the `Mod`), surfacing as the reported `PolynomialError`.
Post-patch the exception is caught, `G` becomes the identity factor `1`, the
operands are left unchanged, and the operation completes — precisely
`(Piecewise(...)/z) % 1` evaluating to an unevaluated `Mod` without error.

## B. Spec strength — why no wrong impl verifies

The precondition additionally carries `Requires(MustTerminate(2))` (with
`common_factor_compute` holding the strictly smaller `MustTerminate(1)`): the
block is a bounded, straight-line computation and must terminate and DELIVER
its value. Nagini is a partial-correctness verifier by default, so without
this obligation an impl that diverges before returning (an unbounded loop
inserted ahead of the factor-producing call — the audit's divergence attack,
whose faithful real patch hangs `Mod.eval` and the F2P forever) discharges
every value clause vacuously. With the obligation, a `while True`-shaped loop
has no strictly decreasing measure and fails the termination check
(mapping.md §5; PBT case `diverge-before-return`).

The frozen postcondition pins FOUR things, jointly tight:
  - **no `Exsures`** ⇒ the method must raise on NO input (kills the pre-patch
    unguarded call, which raises on code 2);
  - `Implies(code == 2, Result() == build_result(1, p, q))` ⇒ on the unanswerable
    input the value uses the identity factor and the unchanged operands (kills a
    "swallow but return garbage" impl, and any impl that returns the real factor
    without recognising the raise);
  - `Implies(code != 2 and common_factor(code) == 1, Result() == build_result(common_factor(code), p, q))`
    ⇒ on an answerable identity-factor input the factor is the helper's own
    (identity) output and the operands enter the value unchanged;
  - `Implies(code != 2 and common_factor(code) != 1, Result() == build_result(common_factor(code), divide_out(p, common_factor(code)), divide_out(q, common_factor(code))))`
    ⇒ on an answerable non-identity-factor input the factor is the helper's own
    OPAQUE output (kills hardcode/echo cheats — a literal cannot be proven equal
    to it, SPEC_GUIDE §8) **and EACH operand is rewritten via `divide_out`**.

**The fourth clause closes the verdict's G-EQ hole.** Because `divide_out` and
`build_result` are opaque, an impl that drops the operand rewrite (the `atk_6`
attack: keep the `try/except`, delete the `if G != 1: …gcd_terms…` block)
produces `build_result(G, p, q)` and cannot prove
`p == divide_out(p, common_factor(code))` — so it FAILS to verify (re-confirmed
2026-06-15: clause 3a "Postcondition might not hold"). Independently, the
`atk_6` *faithful real patch* fails the F2P `test_Mod` at the pre-existing
code-0 assertion `(12*x + 18*y) % (3*x) == 3*Mod(6*y, x)` (re-confirmed
in-container: gold passes, atk_6 fails). The two now agree: a verifying impl
resolves; a non-resolving impl does not verify. (Other attacks killed:
hardcode-trivial-always and swallow-and-fabricate-literal both fail clause 3a.)

A read-only abstraction here: `code`, `p`, `q` are integers passed by value, and
the impl never reassigns `p`/`q` (only the locals `pr`/`qr`), so the postcondition
witnesses `divide_out(p, …)` / `divide_out(q, …)` refer to the operands as given
— directive-5 fractional-permission vacuity is not reachable.

## C. No second prepatch needed

There is a single independently-fixed behaviour (the unguarded factor-producing
call in the block); one `model_prepatch.py` exercises it. The `gcd`, `gcd_terms`
and `Mul`/`Mod` construction are not changed, so they are not separately modeled
as fixed behaviours — they are the axiomatized callees whose soundness G-AX
checks.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
exception-handling control flow that converts the helper's raise into the
identity factor instead of propagating it — is modeled **directly** as the
`try/except` in the impl with a no-`Exsures` postcondition (A2–A5), not hidden
behind an axiom about the function under change. The only consumed axioms cover
**unchanged** callees the code invokes: `gcd` (`common_factor` /
`common_factor_compute`, A2) , `gcd_terms` (`divide_out`, A3) and the `Mul`/`Mod`
construction (`build_result`, A4); the change never touches any of them — it only
wraps the call site. There is no A-reference (no changed operation is modeled as
a deep equivalence to a callee).

## E. verify(model) ⇒ resolved

`reduce_extract_common_factor` verifies only if (A2/A5) it CATCHES the helper's
raise (the no-`Exsures` obligation, dischargeable only because the `try` wraps
the lone raising call and the `except` handles `FactorUnavailable`), (A5) it
uses the identity factor `1` with unchanged operands on that raise
(`code == 2 ⇒ Result() == build_result(1, p, q)`), and (A2/A3/A4) otherwise
builds the value from the helper's own opaque factor and rewrites EACH operand
exactly under `G != 1` (the two `code != 2` clauses). By R (operand pair ↔ case
code; `S.One` ↔ `1`; `PolynomialError` ↔ `FactorUnavailable`;
`gcd`/`gcd_terms`/`Mul`-`Mod` ↔ the axiomatized callees) the verified block
equals the gold "extract gcd" block on the tested inputs; by G-AX the real `gcd`
meets the `common_factor`/`common_factor_compute` axioms (including the
Piecewise-raise `Exsures`) and the real `gcd_terms` regroup meets `divide_out` /
`build_result` (the code-0 operand-transform assertions, incl. the F2P's own
`(12*x + 18*y) % (3*x) == 3*Mod(6*y, x)`). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
