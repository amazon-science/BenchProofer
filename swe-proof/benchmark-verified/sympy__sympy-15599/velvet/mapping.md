# mapping.md — sympy__sympy-15599

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5e17a90c19f7eecfa10c1ab872648ae7e2131323`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), records the
provenance of the unchanged upstream computation whose output is the modeled
function's read-only input, and pins the G-CONF fuzz seed.

Repo file under change: `sympy/core/mod.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceModFactors (factors : List Factor) (q : Int)` | the added block in `Mod.eval.doit`'s product branch — `sympy/core/mod.py` (the `elif isinstance(p, Mul):` arm, `mod.py:120`); the new code is appended just before `# XXX other possibilities?` (`mod.py:140`), see `patch.diff` hunk 3 | the modeled changed behavior: rewrite the list of non-modular factors of a product by replacing each integer-literal factor with its residue mod `q` |
| `factors : List Factor` (read-only input) | the local `non_mod_l` list — the non-`Mod` factors of the product `p`, as split by the unchanged `for arg in p.args: both_l[isinstance(arg, cls)].append(arg)` loop (`mod.py:117-119`) immediately before the patched block runs | the pre-reduction `non_mod_l` the changed block consumes; see §3 |
| `q : Int` | the modulus `q` of `Mod(p, q)`, restricted to the branch guard `q.is_Integer and q is not S.One` | the integer modulus |
| `reduced (q) (factors)` *(deep model)* | the *post-patch* loop body: `_ = []; for i in non_mod_l: if i.is_Integer and (i % q is not S.Zero): _.append(i%q) else: _.append(i); non_mod_l = _` (`patch.diff` hunk 3) | pure spec: per-factor residue rewrite of the factor list |
| `reduceFactor (q) (f)` *(pure)* | one iteration of that loop body for a single factor `i` | pure spec: residue rewrite of one factor |
| `Factor` (`.num n` / `.sym k`) | one factor of `non_mod_l`: either a SymPy `Integer` literal (`.num`) or any non-integer factor — a symbol, power, rational, etc. (`.sym`) | the factor carrier; see §2 |

There are **no axioms** in this bundle and **no `axiom_check.py`**: the changed
behavior (residue-rewriting the product's own factor list) is modeled **deeply**
by `reduced`/`reduceFactor` over the read-only input `factors`. The upstream
factor-split loop is **not a callee** and is **not axiomatized** — its entire
relevant effect is the value of `factors` (§3). G-AX therefore reports `skip`;
G-CONF carries the soundness load.

The pre-patch repo behavior the change adds (refinement audit only, not in the
consumer spec view): before the patch the non-modular factors are left **as
they are** — no integer factor is reduced modulo `q` — so a product such as
`3*i (mod 2)` keeps its `3` instead of collapsing it to `1`.
`Solution_prepatch.lean` reproduces that "pass every factor through unchanged"
skeleton and fails the `out = reduced q factors` clause.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one factor of `non_mod_l` that is a SymPy `Integer` literal `n` | `Factor.num n` | the SymPy `Integer(n)` ↔ `Factor.num n`; `n` ranges over `Int` |
| one factor of `non_mod_l` that is **not** an `Integer` (symbol, power, rational, …) | `Factor.sym k` | each distinct non-integer factor is assigned a unique opaque code `k : Int`; only its **identity** (it is not an integer literal, and equal factors stay equal) is observable to the reduction, which never inspects its structure |
| the modulus `q` (a SymPy `Integer`, `q ≠ 0`, `q ≠ 1`) | `q : Int` | identically; `Integer(q) ↔ q` |
| the pre-reduction `non_mod_l` (a Python `list` of factors) | `factors : List Factor` | element-wise via the row bijection; order preserved; `len` ↔ `.length` |
| the rewritten factor list `non_mod_l = _` | `out : List Factor` | element-wise via the row bijection; order and length preserved |
| Python `i % q` on integer `i`, integer `q` (floored, sign-of-divisor) | `Int.fmod i q` | exact: Python's `%` on `int` is the floored remainder, which is `Int.fmod` (verified: `7%3=1, -7%3=2, 7%-3=-2, -7%-3=-1` match `Int.fmod`); Lean's `Int.%` (`emod`, always ≥0) would be **wrong** for negative `q`, so the model uses `Int.fmod` |
| `i % q is not S.Zero` (the residue is non-zero) | `Int.fmod n q ≠ 0` | a non-zero residue triggers the rewrite; a zero residue keeps the factor unchanged |

The reduction observes only whether a factor **is an integer literal** and, if
so, its **residue mod `q`**; it never inspects a non-integer factor's internal
structure, so coding non-integer factors as opaque `.sym k` is faithful. The
`mod_l` factors (those that are themselves `Mod` instances) are **not** in the
modeled regime (see §3) and are kept out of the G-CONF fuzz; the model carrier
is `non_mod_l` only.

## 3. Provenance of the read-only input `factors`

### 3.1 The factor-split loop is unchanged
`factors` is the local `non_mod_l` list built by the **unchanged** split
```python
both_l = non_mod_l, mod_l = [], []
for arg in p.args:
    both_l[isinstance(arg, cls)].append(arg)
```
(`mod.py:117-119`). The gold patch does **not** touch this loop; it only appends
the residue-rewrite block after it. So `non_mod_l` is identical pre/post patch,
and modeling it as the read-only input `factors` is faithful. (Directive 5:
`factors` is **not** `mut`; the impl builds a fresh `result`.)

### 3.2 Regime / branch guard
The patched block runs only when control is in the `elif isinstance(p, Mul):`
arm AND the earlier `if mod_l and all(inner.args[1] == q ...)` sub-block did
**not** return (`mod.py:122-138`). For the modeled regime — and the G-CONF fuzz
— `mod_l` is **empty** (the product has no `Mod` factor), so that sub-block is
skipped and the reduction runs. The block's own guard is
`q.is_Integer and q is not S.One`, captured by the preconditions
`require q ≠ 0` (Mod-by-zero is raised earlier, `mod.py:39`) and
`require q ≠ 1` (`q is not S.One`). `q` is always integral in the modeled
regime, matching the `Int` carrier.

### 3.3 What is observable
The rewritten `non_mod_l` is reassembled into `p = Mul(*(non_mod_l + mod_l))`
and falls through to the unchanged gcd/denest tail of `doit`, which yields the
final `Mod(p, q)` value. The public observable is therefore the **SymPy
expression `Mod(p, q)`**. G-CONF compares, for a product `p` of integer literals
and symbols, the **real patched** `Mod(p, q)` (oracle) against
`Mod(Mul(*reduced_factors), q)` where `reduced_factors` is the R/I shadow's
per-factor reduction of `p.args` (shadow), both evaluated by the real patched
SymPy. Because the gold reduction is value-preserving and idempotent, equality
holds iff the shadow's `reduceFactor` matches the patch's per-factor rewrite — a
genuine refutation of a wrong R/I leg.

## 4. G-CONF fuzz seed + flag dependency

- **Pinned fuzz seed:** `SEED = 15599` (`conformance_check.py`). `N_FUZZ = 100000`.
- **Branch/flag dependency:** the reduction runs under `q.is_Integer and
  q is not S.One`, in the `Mul` branch with `mod_l` empty. G-CONF fixes that
  regime: products of integer literals and integer-assumption symbols (so `p`
  stays a `Mul` and reaches the branch), with integer `q`, `|q| ≥ 2`, both signs
  (to exercise the floored-mod sign convention).
- **Cases:** the boundary set includes the exact F2P assertions
  `Mod(3*i, 2) == Mod(i, 2)`, `Mod(8*i, 4) == 0`, `Mod(8*i/j, 4) ==
  4*Mod(2*i/j, 1)`, and `Mod(4*i, 4) == 0`, plus negative-`q` and
  zero-residue (factor kept) shapes.
