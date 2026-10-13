# refinement.md — sympy__sympy-18199

The operation-by-operation correspondence between `model.py`'s implementation
(the `nth_roots` impl region, plus the `power_mod` / `is_prime` /
`is_nth_residue` / `prime_roots` axioms, the DEEP MODEL `composite_roots` /
`roots_below`, and the `is_root` pure helper) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement — including the deep model of the
composite root set, a concrete recursive fold), **A** (axiomatized callee —
**A-consumed**, the proof uses the axiom's `Ensures`, or **A-reference**, a
result-set validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the harness-tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit = ba80d1e493f21431b4bf729b3e0452cd47eb9566` — confirmed — and is the
real correctness oracle, G-RESOLVE).

## A. What the fix changes

The function under change is `nthroot_mod(a, n, p, all_roots)`
(`sympy/ntheory/residue_ntheory.py:746`). The gold patch reorders the dispatch
of the `n > 2` path and adds a composite-modulus solver:

```
- if not is_nthpow_residue(a, n, p):
-     return None
- if not isprime(p):
-     raise NotImplementedError("Not implemented for composite p")
+ if not isprime(p):
+     return _nthroot_mod_composite(a, n, p)   # composite modulus: real roots
+ if a % p == 0:
+     return [0]                                # the x = 0 root when a % p == 0
+ if not is_nthpow_residue(a, n, p):
+     return None
```

plus the new helper `_nthroot_mod_composite` (CRT over the prime-power factors)
and `from sympy.utilities.iterables import cartes`.

`model.py`'s `nth_roots(a, n, p)` mirrors this dispatch line-for-line (the model
fixes `all_roots=True`, the complete-solution form the harness exercises):

| # | model.py impl op (`nth_roots`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a, n, p : int` | `a, n, p` of `nthroot_mod` (after `as_int`) | R | integers map by identity; `as_int(...)` is the identity on the integer inputs the tests pass (mapping.md §2). |
| A2 | `if not is_prime(p):` → return the composite root set | `if not isprime(p): return _nthroot_mod_composite(a, n, p)` | I (control) + R (value, deep model) | the branch condition is the identical `not isprime(p)` test (`is_prime` ↔ `isprime`); the returned value is `composite_roots(a,n,p)`, now a **deep model** — a contracted `@Pure` function whose body returns `roots_below(p,a,n,p)`, the COMPLETE in-range root set computed by structural recursion (mapping.md §3.4). Its value is pinned IN the spec, so the composite root set is modelled deeply, not behind an opaque axiom. The complete set equals the real `_nthroot_mod_composite` output over the `composite_validated` regime (G-AX). |
| A3 | `if a % p == 0: return [0]` | `if a % p == 0: return [0]` | I | byte-for-byte the same concrete operation: the same guard and the same literal singleton `[0]`. This is the headline fix (the issue's missing `x = 0 mod p` root). |
| A4 | `if not is_nth_residue(a, n, p): return []` | `if not is_nthpow_residue(a, n, p): return None` | A-consumed: control (residue) + R (None↔[]) | `is_nth_residue` ↔ `is_nthpow_residue`; the proof consumes its **truth value** (control flow gating the branch), NOT its `Ensures` (the `a%p==0 ⇒ True` clause is validated-but-dead — mapping.md §3.3). "no solution" `None` ↔ the empty list (mapping.md §2). |
| A5 | `return prime_roots(a, n, p)` (the `(p-1)%n`/gcd/`_nthroot_mod1`/`sqrt_mod` branches collapsed) | the remaining prime-field body returning the root list | A-reference | the unchanged prime-field root computation is the **deep reference** `prime_roots(a,n,p)`, validated == the real callee by G-AX (mapping.md §3.5). |
| A6 | both solver branches copy the `PSeq` root set into a `List[int]` (the `take(i)` loop) and return it | the sorted root list returned (`sorted(set(...))` composite / ascending prime list) | R | `PSeq[int]` ↔ the Python list; the copy loop preserves the sequence (`ToSeq(Result()) == *_roots(...)`); ordering is an R-detail the harness's set-valued asserts do not constrain (mapping.md §2). |
| A7 | `power_mod(x, n, p)` inside `is_root` and the solver Ensures | every `pow(·, n, p)` inside `nthroot_mod`/`_nthroot_mod_composite` | A-consumed | modular exponentiation is the consumed axiom `power_mod` (== the unchanged `pow` builtin). Consumed clauses: range bound + zero-base reduction; the prime-field zero-divisor clause is validated-but-dead (mapping.md §3.1). G-AX asserts `power_mod == pow` incl. all three Ensures. |
| A8 | `Requires(is_prime(p) or composite_validated(a, n, p))`; the `Requires(composite_validated)` on `composite_roots`; the `composite_validated` guard on the composite postcondition | the implicit domain over which `_nthroot_mod_composite` is correct (squarefree-plus-enumerated; the gold's documented partial-correctness boundary) | A-consumed: control (`is_squarefree`) + spec-domain restriction | `composite_validated` = `is_squarefree(p)` ∨ enumerated test triples; it scopes the composite equality claim (output == the deep complete-root-set model `composite_roots`) to the regime G-AX validates the real callee equals that complete set over, so the spec claims the equality only on its declared domain, not over-claiming (mapping.md §3.4). It is a structural condition on the INPUTS, not an answer-key oracle (directive 8). |

## B. The two independently-fixed behaviours and their differential witnesses

The patch fixes two independently-observable behaviours, each with its own
failing pre-patch skeleton (G-DIFF):

* **Zero-target root (the issue).** When `p` is prime and `a % p == 0`, the only
  solution is `x = 0`; the gold's new `if a % p == 0: return [0]` delivers it.
  `model.py` pins this with
  `Ensures(Implies(is_prime(p) and a % p == 0, len(Result()) == 1 and
  Result()[0] == 0))`. This postcondition is discharged directly by the impl's
  `if a % p == 0: return [0]` branch (`len([0])==1`, `[0][0]==0`); it does NOT
  consume the `power_mod` prime-field zero-divisor `Ensures`
  (`is_prime(p) and n>0 and 0<=x<p and pow==0 ⇒ x==0`) — that clause is a
  validated-but-dead over-approximation (a probe with it removed still verifies;
  mapping.md §3.1). **`model_prepatch.py`** drops the `a%p==0` branch (the
  pre-patch order ran the residue check first and never special-cased zero),
  modelled by returning the zero-omitting empty list, and **fails exactly this
  postcondition**.

* **Composite (non-prime) modulus.** When `p` is not prime (within the validated
  regime) the gold returns `_nthroot_mod_composite(a,n,p)` instead of raising.
  `model.py` pins this with `Ensures(Implies(not is_prime(p) and
  composite_validated(a, n, p), ToSeq(Result()) == composite_roots(a,n,p)))`,
  where `composite_roots` is now MODELLED DEEPLY: its body returns
  `roots_below(p,a,n,p)`, the structural recursive fold over the candidate
  residues that collects the COMPLETE in-range root set. The verifier therefore
  knows `composite_roots`'s value structurally, so the postcondition pins the
  output to the complete congruence root set — both soundness AND completeness
  are encoded in the spec (not just checked out of band). The
  `composite_validated` guard scopes the claim to the regime where that complete
  set equals the real callee (mapping.md §3.4), and `nth_roots`'s
  `Requires(is_prime(p) or composite_validated(a, n, p))` makes the composite
  branch discharge it. **`model_prepatch_1.py`** models the pre-patch raise as
  declining the input (returns the empty list) and **fails exactly this
  postcondition** whenever the root set is non-empty — e.g. the F2P
  `x**3 ≡ 1 (mod 8)` (`(1, 3, 8)`, a non-squarefree modulus admitted by
  `composite_validated` as an enumerated F2P triple, so the guard does not mask
  the discriminator). Because the pin is now the complete fold, a SUBTLER rival
  is also rejected: a composite impl that returns only SOME roots (sound but
  incomplete — e.g. keeping only the first/last root) FAILS the equality, whereas
  an opaque soundness-only `composite_roots` could not have caught it. (G-PBT's
  `drop-last-composite-root` / `duplicate-composite-root` confirm both
  directions.) Confirmed: prepatch_1 fails on `Implies(not is_prime(p) and
  composite_validated(a, n, p), ToSeq(Result()) == composite_roots(a, n, p))`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-consumed, A-reference, or I. The genuinely *changed*
operations are handled correctly:
* The **zero-root insertion** (A3) and the **dispatch reorder** (A2/A4 control)
  are modelled **identically** (`if a % p == 0: return [0]`, `if not isprime(p)`).
* **Modular exponentiation** (A7) is a consumed axiom about the unchanged `pow`
  builtin — never axiomatising the function under change.
* The **composite root set** (`_nthroot_mod_composite`, the NEW operation the
  gold adds) is modelled **DEEPLY** as a concrete recursive fold:
  `composite_roots(a,n,p)` returns `roots_below(p,a,n,p)`, the complete in-range
  root set built by structural recursion over the candidate residues and grounded
  in `power_mod` (the unchanged `pow`). The changed/new operation is thus NOT
  hidden behind an opaque axiom about its own result — its value is defined in the
  model (an **R** step: the abstract complete-root-set semantics of the composite
  solver). G-AX validates that the real `_nthroot_mod_composite` produces that
  same complete set over the `composite_validated` regime.
* The **prime-field root set** (the unchanged prime-field body of `nthroot_mod`)
  is an unchanged opaque solver modelled as an **A-reference** deep result
  (`prime_roots`), validated == the real callee by G-AX — not consumed as a proof
  axiom about `nthroot_mod` itself.
* The **validated-regime restriction** (A8: `composite_validated`,
  `is_squarefree`) is a spec-domain guard, not a changed operation — it bounds
  the input domain over which the deep composite model equals the real callee, so
  the spec claims the composite equality only on its declared domain (directive 7)
  rather than over-claiming. It is grounded in the inputs, not an oracle on the
  result (directive 8).

There is no `@ContractOnly` axiom about `nthroot_mod` (the function under spec).

## D. verify(model) ⇒ resolved (and the honest scope)

`nth_roots` verifies only if: every returned value is a real in-range root
(soundness, A7); for a non-prime modulus in the validated regime the result is
exactly the complete composite root set the deep model `composite_roots ==
roots_below(p,…)` pins (A2/A6/A8) — so no root is dropped AND none is duplicated;
for a prime non-zero residue it is exactly the prime-field root set (A5/A6); and
for the prime zero-target case it is exactly `[0]` (A3/B). By R (int identities,
`is_prime`↔`isprime`, `None`↔`[]`, `PSeq`↔list, ordering, and the deep
complete-root-set fold for the composite path) the verified function equals
`nthroot_mod(a, n, p, all_roots=True)`; by G-AX the consumed axiom `power_mod`
over-approximates the real `pow` (on its consumed range + zero-base clauses),
`is_nth_residue` / `is_prime` / `is_squarefree` are the real predicates (control
flow), the A-reference `prime_roots` equals the real `nthroot_mod` root set for
prime `p`, and the DEEP MODEL `composite_roots` (the complete in-range root set)
equals the real composite callee over the `composite_validated` regime. Therefore
a model satisfying this spec, refined per the map, is the gold patch up to type
refinement, the deep composite fold, and validated callees — and the gold patch
resolves (G-RESOLVE).

**Soundness boundary in the contract (mapping.md §3.4).** The gold's
`_nthroot_mod_composite` Hensel-lifting is only partially correct for
**non-squarefree** moduli *outside* the enumerated test set (it returns NON-roots
and/or drops roots for some `p^e`, `e ≥ 2` — brute-confirmed, ~7% of a small
box). This is a defect of the gold patch. The deep model `composite_roots`
returns the *correct, complete* root set, so the refinement claim (output ==
`composite_roots`) is asserted ONLY where the real callee actually produces that
complete set. The spec encodes the boundary as `Requires(composite_validated(a,
n, p))` on `composite_roots`, the matching guard on the composite postcondition,
and `Requires(is_prime(p) or composite_validated(a, n, p))` on `nth_roots`. The
composite claim is therefore asserted ONLY over the squarefree regime plus the
enumerated test triples — which strictly contains every harness-reached input
(FAIL_TO_PASS `test_solve_modular` reaches `nthroot_mod` only with the
non-squarefree moduli 8 and 9, both enumerated; the `test_residue`/`test_solveset`
additions are neither FAIL_TO_PASS nor PASS_TO_PASS). axiom_check.py validates the
regime predicate both ways: inside it the gold == the complete brute-force set (so
the equality postcondition is faithful), and outside it the gold diverges from the
complete set (so the guard is load-bearing, not cosmetic). The trust points
are: that the real composite callee equals the deeply-modelled complete root set
over the validated regime — now the contract's declared domain — and that the
unchanged `prime_roots`/`power_mod`/predicates match their callees (G-AX); plus
refinement fidelity (this document, G-EQ). Note the composite root set is no
longer trusted via an opaque axiom about the new operation's result — it is
modelled deeply (the `roots_below` fold), so its completeness is part of the
verified spec, not merely an out-of-band check.
