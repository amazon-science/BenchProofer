# mapping.md — sympy__sympy-13974

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 84c125972ad535b2dfb245f8d311d347b45e5b8a`, states the type
abstraction, and gives the provenance of the one axiomatized callee.

Repo file under change: `sympy/physics/quantum/tensorproduct.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `power_of_collection(args, exp)` | `tensor_product_simp_Pow(e)` — the NEW helper the patch adds (`tensorproduct.py`, post-patch lines 351-359); its body `TensorProduct(*[ b**e.exp for b in e.base.args])` | the modeled changed behaviour: distribute one exponent over the tensor factors |
| `simp_pow_factor(is_pow_of_tp, factors, exp)` | the non-commutative-factor routing decision in `tensor_product_simp_Mul(e)` the patch adds (`tensorproduct.py`, post-patch lines 321-326 the `n_nc == 1` Pow case + 330-338 the leading-factor Pow case): `if isinstance(nc_part[0], Pow): return Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])` and `if isinstance(current, Pow): if isinstance(current.base, TensorProduct): current = tensor_product_simp_Pow(current)` | the modeled changed behaviour: route a `Pow`-of-`TensorProduct` factor of a product into the per-factor distribution (delegating to `power_of_collection`); pass a bare `TensorProduct` factor through unchanged |
| `pow_expr(base, exp)` *(axiom — A-consumed)* | the symbolic power constructor `b ** e.exp` (Python `**` → `sympy.core.power.Pow`), invoked once per tensor factor inside `tensor_product_simp_Pow` | unchanged callee the new helper CALLS but does not change |
| `args` (`List[int]`) | `e.base.args` — the argument tuple of the `TensorProduct` that is the power's base (`tensorproduct.py`, `TensorProduct.__new__`/`Expr.args`) | the tensor factors as opaque expression handles |
| `factors` (`List[int]`) | the tensor factors of the examined non-commutative factor's base — `current.base.args` (leading case) / `nc_part[0].base.args` (`n_nc == 1` case) when that factor is a `Pow` of a `TensorProduct`; or the args of the bare `TensorProduct` factor otherwise | the tensor factors of the in-product factor as opaque expression handles (same carrier as `args`) |
| `is_pow_of_tp` (`bool`) | the routing guard `isinstance(<factor>, Pow) and isinstance(<factor>.base, TensorProduct)` on the examined non-commutative factor | the boolean decision that selects the routing: `True` ↔ the factor is a power whose base is a tensor product (distribute), `False` ↔ the factor is already a bare tensor product (passthrough) |
| `exp` (`int`) | `e.exp` — the exponent of the `Pow` (`sympy.core.power.Pow.exp`) | the exponent as an opaque expression handle; the value `1` is the reserved handle for the identity exponent (sympy `Integer(1)`), excluded by `Requires(exp != 1)` because a `Pow` node never carries it |

The pre-patch behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): the `Pow` branch of
`tensor_product_simp` was `return tensor_product_simp(e.base) ** e.exp`
(`tensorproduct.py:384-385` @ base_commit). For a base that is already a bare
`TensorProduct`, `tensor_product_simp(e.base)` returns the SAME tensor product
unchanged, so the exponent stays OUTSIDE the tensor product — each tensor factor
is left as the original `args[i]`, never raised to `exp`. The fix routes such a
power through the new `tensor_product_simp_Pow`, which raises EACH tensor factor
to the exponent. Inside `tensor_product_simp_Mul` the pre-patch code had no place
for such a factor: the `n_nc == 1` case was a bare `return e` and the
leading-factor case `raise`d `TypeError` for a non-`TensorProduct`; the fix adds
the routing decision (`simp_pow_factor`) that detects a `Pow`-of-`TensorProduct`
factor and delegates it to the same per-factor distribution, leaving a bare
`TensorProduct` factor unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `TensorProduct` instance | the ordered tuple of its arguments `e.base.args`, modelled as `List[int]` of opaque expression handles | `args[k]` ↔ a distinct integer handle for the k-th tensor factor `e.base.args[k]`; `len(args)` ↔ the number of tensor factors; tensor-factor order is preserved |
| a symbolic expression (one tensor factor `A`, `B`, … or `Pauli(3)`) | a distinct `int` handle | equality of handles ↔ structural equality of the sympy expressions (`==` / `Eq` on `Expr`) |
| the exponent `e.exp` (`x`, `2`, …) | a single `int` handle `exp` | one handle for the whole exponent expression; held fixed across all factors |
| the power application `b ** e.exp` (sympy `Pow`) | `pow_expr(b_handle, exp)` | a deterministic binary map from (factor handle, exponent handle) to the handle of the resulting power expression |
| the type test on a non-commutative factor — `isinstance(f, Pow) and isinstance(f.base, TensorProduct)` | the boolean `is_pow_of_tp` | `True` ↔ the factor is a power whose base is a tensor product; `False` ↔ the factor is a bare tensor product; the two shapes `tensor_product_simp_Mul` routes between |
| the reconstructed `TensorProduct(*[...])` | the returned `List[int]` of per-factor result handles | element k of the result ↔ the k-th argument of the rebuilt tensor product |

A `TensorProduct` cannot be expressed in Nagini's fragment, so its content that
the operation touches — the ordered argument list — is the carrier; the
specification is phrased over `PSeq[int]` via `ToSeq`. The single per-factor
operation `b ** e.exp` is the unchanged power constructor, axiomatized as
`pow_expr`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `pow_expr` ↔ the symbolic power constructor `b ** e.exp` (A-consumed)
**Callee:** Python's `**` on a sympy `Expr` factor with a sympy exponent,
i.e. `sympy.core.power.Pow(b, e.exp)` (after sympify). The new helper
`tensor_product_simp_Pow` calls it once per tensor factor:
`TensorProduct(*[ b**e.exp for b in e.base.args])`. The power constructor is
UNCHANGED by the patch — the patch only changes WHERE it is applied (per tensor
factor instead of around the whole tensor product).

The axiom encodes only the two properties the proof consumes, and it carries the
precondition `Requires(exp != 1)` (the identity exponent, modelled as the
reserved handle `1`):

  * **determinism / functionality** (unconditional) — `b ** e.exp` is a
    deterministic function of `(b, e.exp)`: the impl loop and the spec fold read
    the SAME power handle for the same `(factor, exponent)` pair. (`Pow.__new__`
    is a pure constructor on canonicalised args.)
  * **non-triviality away from the identity exponent** — when `exp != 1`, raising
    a non-commutative symbol/operator factor to the exponent does NOT return the
    factor unchanged: `b ** e.exp != b`. This is the property that forces the
    per-factor power to be observable (it is what the prepatch violates: it leaves
    each factor equal to `b`). The axiom states this as `pow_expr(b, exp) != b`
    **under** `Requires(exp != 1)`.

The precondition is necessary AND faithful. **Necessary:** the real callee
returns the base unchanged at the identity exponent (`b ** 1 == b`), so an
*unconditional* `Result() != base` would over-claim there (directive 7). The
guard `exp != 1` is the weakest sufficient restriction — it removes exactly the
one input the real callee fails and nothing more (`b ** 0 = 1` and every other
exponent are non-trivial). **Faithful:** a `Pow` node never carries exponent `1`
(`b ** 1` canonicalises to `b`), so `tensor_product_simp_Pow` is never reached
with `exp == 1`; the modelled function `power_of_collection` therefore carries
the matching `Requires(exp != 1)`, which holds on every input it actually sees.
The narrative ("for the non-trivial exponents this behaviour concerns") is now
*encoded* by the precondition, not merely asserted in prose.

**Soundness check (G-AX):** `axiom_check.py` constructs sympy `Pow` expressions
`b ** exp` for non-commutative symbols `A, B, C, D, E` factors with exponents
`x, y, n, 2, 3, x+1, 2*x` (the F2P exponents and more), plus randomized fuzz over
factor / exponent pairs. It asserts (a) determinism (`b**exp` is reproducible and
equal to itself across repeated construction) and (b) `b ** exp != b` for every
exponent with `exp != 1`. It ALSO fuzzes the identity boundary `exp == 1`
explicitly and asserts the OPPOSITE (`b ** 1 == b`) — proving the precondition is
necessary and weakest-sufficient (not a masked over-claim: the falsifying
boundary is exercised, not omitted). It imports only `sympy` (the repo under
test) — nothing about the patched function. Exit 0 iff every observation meets
the axiom (confirmed RC=0 in the pinned eval container with the gold patch
applied: 35 non-trivial + 10 identity-boundary + 500 fuzz pairs).

The end-to-end behaviour the change adds is then exactly the per-factor map this
benchmark's F2P pins:
`tensor_product_simp(TP(a_1,…,a_n)**e) == TP(a_1**e, …, a_n**e)`, with the same
distribution reached through `tensor_product_simp_Mul` for the `Mul`-of-powers
cases (`x*TP(A,B)**2`, `x*(TP(A,B)**2)*TP(C,D)`) and through the `Add` recursion
for `TP(A,B) - TP(C,D)**x`. All routes funnel into `tensor_product_simp_Pow`'s
per-factor distribution, which is the modeled `power_of_collection`.

## G-CONF (differential conformance: MODEL vs the REAL patched repo function)

`conformance_check.py` refutes the refinement leg no other gate covers: that the
model actually agrees with the patched repository code it claims to model.

**Shadow.** Both `# impl-start` / `# impl-end` regions of `model.py`
(`power_of_collection`, `simp_pow_factor`) copied VERBATIM, with only the
contract calls (`Requires`, `Ensures`, `Invariant`, `Assert`, `MustTerminate`,
`Acc`) and the `# invariants-*` markers removed — no restructuring or renaming
(verified line-for-line against the regions). The `@Pure` helper
`pointwise_pow` is copied over too, so the spec-side fold is run as well: the
check is three-way (spec fold == impl loop == real repo function), which is
sharper than a two-way diff. `PSeq`/`ToSeq` are realized by an immutable
tuple shim exposing exactly `take`/`drop`/`+`/`len`/`[]`/`==`.

**Axiomatized callee.** `pow_expr` is `@ContractOnly` and has no body to copy,
so the check CALLS the real operation it axiomatizes — Python `**` on a sympy
`Expr` (`sympy.core.power.Pow`), the operation post-patch
`tensor_product_simp_Pow` applies once per tensor factor
(`tensorproduct.py:370`). The axiom is exercised here, not assumed.

**Oracle — called, never transliterated.** The gold patch is applied to
/testbed by the gate, so every oracle is the real patched function:
`tensor_product_simp_Pow` (§1's `power_of_collection` counterpart) driven on
`TP(*args) ** exp`; `tensor_product_simp_Mul` for the routing decision
(`simp_pow_factor`), driven at BOTH real routing sites — the `n_nc == 1` Pow
case and the leading-factor Pow case — with each generated product asserting via
`args_cnc()` that the intended site is genuinely reached (`site_not_reached`
counted and required to stay 0 for the sites in play); and the top-level
`tensor_product_simp` on the four FAIL_TO_PASS shapes as an end-to-end anchor.

**Type bridge (§2 inverted).** The opaque `int` handle is instantiated AT the
concrete sympy `Expr`, which is precisely §2's bijection (handle equality ↔
structural expression equality); the impl region is polymorphic in the handle
type, so it runs unchanged. The identity handle `1` is `Integer(1)` and
`Requires(exp != 1)` is enforced literally (the exponent pool excludes it).
Because the carrier is `e.base.args`, every carrier is read back off a REAL
constructed `TensorProduct` rather than assumed from the chosen factors —
`TensorProduct.flatten` frequently collapses them (`TP(2, A)` is a `Mul`). The
result list is mapped back via the §2 inverse `TensorProduct(*result)` and, when
the oracle kept a same-arity `TensorProduct`, compared element-wise on `.args`
(order-sensitive, the sharper comparison).

Routing results are compared on the observable the model specifies — the routed
non-commutative factor's argument list plus the scalar prefix — not the raw
`Mul` node: `tensor_product_simp_Mul` returns its argument object untouched on
the passthrough branch, so the oracle can be an unevaluated `(x*y)*TP` while a
rebuilt product is the flattened `x*y*TP`. Same expression, same c/nc parts,
differing only in `Mul` flattening; comparing nodes there would report sympy
constructor bookkeeping as a conformance failure.

**Domain.** Infinite (sympy expressions), so fuzzed, not enumerated. Kept IN
the domain rather than routed around: `exp == 0` (handle 0 ≠ identity handle 1,
so the model admits it; the node is built `evaluate=False` since the evaluating
constructor collapses it), negative and rational exponents, factors that
collapse under the power (`Pauli(3)**2 == 1`, `Integer(1)`), and a
single-factor carrier reached via `Expr.__new__(TensorProduct, A)` (the
evaluating constructor cannot make one). The ONLY `Requires`-satisfying shape
not driven is the EMPTY carrier: `TensorProduct()` raises `IndexError` in
`__new__`, so no repository `TensorProduct` has zero arguments and the model's
empty-list case has no real counterpart to disagree with.

**Inputs / seed.** 106584 `Requires`-satisfying checked inputs (90 boundary
incl. all four F2P shapes and the problem-statement `tp(1,1)` / `tp(1,Pauli(3))`
shapes, 12 single-factor, remainder seeded fuzz driving all three legs per
draw). Pinned seed **13974**, a module constant `SEED`. A `MIN_CHECKED =
100000` floor, per-leg coverage assertions, and an "element-wise comparison
actually ran" assertion all fail the script rather than let an under-covered run
report green.

**Self-refutation controls.** A green G-CONF that cannot fail certifies
nothing, so the script proves its own discriminating power before reporting
success: the pre-patch image (exponent left wrapping the whole tensor product)
must be detected as different from the distributed one, and factor-order-swap
and dropped-power mutations must disagree with the real helper. Verified out of
band that seeded mutants of the shadow are caught — `pow_expr` returning
`base**(exp+1)` (shadow and spec fold stay mutually consistent, so ONLY the
real-function comparison can catch it) fails via `tensor_product_simp_Pow`, and
an always-passthrough routing mutant fails via `tensor_product_simp_Mul`. Run
against the un-patched base commit the script errors out (no
`tensor_product_simp_Pow`) instead of passing.

**Recorded verdict.** `G-CONF=pass` (exit 0, 0 disagreements).
