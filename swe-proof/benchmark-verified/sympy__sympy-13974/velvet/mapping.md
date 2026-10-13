# mapping.md — sympy__sympy-13974

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 84c125972ad535b2dfb245f8d311d347b45e5b8a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the deep-model callees. TWO repository behaviours are modeled: the
whole-expression power (`distributePow`) and the factor-position routing
(`simplifyFactor`); both are edited by the reference patch and both are required
for the failing test to pass (§1).

**No axioms / no G-AX.** The gold patch *adds* a new helper
(`tensor_product_simp_Pow`); there is **no unchanged external callee to
axiomatize**. The single callee — the `Pow` constructor `**` — is modeled
**opaquely** (`powF`) and runs for real on **both** sides of G-CONF, so it is an
I-leg primitive, not an A-reference. Consequently this bundle ships **no
`axiom_check.py`** and **G-AX skips** (the documented no-axiom path). The deep
model's fidelity to the gold patch is validated mechanically by **G-CONF on the
gold-patched tree** — the correct mechanism, since (a) directive 7 forbids G-AX
validating the function *under change*, and (b) G-AX runs at `base_commit`, where
`tensor_product_simp_Pow` does not yet exist.

Repo file under change: `sympy/physics/quantum/tensorproduct.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `distributePow (factors : List Factor) (n : Factor)` | the new `tensor_product_simp_Pow(e)` helper (added by the gold patch; the dispatch that reaches it is `tensor_product_simp`'s `Pow` branch, `tensorproduct.py:384` pre-patch / `:410-412` post-patch) | the modeled changed behavior AT THE WHOLE-EXPRESSION SITE: evaluate a power whose base is an aggregate by distributing the exponent across the aggregate's factor sequence |
| `simplifyFactor (isPowOfAggregate : Bool) (factors : List Factor) (n : Factor)` | the FACTOR-POSITION routing the gold patch adds inside `tensor_product_simp_Mul` — the single-non-commutative-factor site (`tensorproduct.py:322-325` post-patch), the leading-factor site (`:328-333`), the trailing-factor site (`:346-355`) and the all-`Pow` fallback (`:358-360`) | the second modeled changed behavior: for ONE factor of a product, route a power-of-aggregate factor to the per-position raise and hand a bare-aggregate factor back untouched. Every one of those four sites performs exactly this routing, which is why one contracted method models them all |
| `powAll (n) (factors)` *(deep model — I-leg, G-CONF-validated)* | the body of `tensor_product_simp_Pow`: `TensorProduct(*[ b**e.exp for b in e.base.args ])` (`tensorproduct.py:364-372`, post-patch) | pure spec: position-wise raise of every factor; deep model of the changed op, validated `powAll == real tensor_product_simp_Pow` by conformance_check.py (G-CONF LANE 1) on the patched tree |
| `factorImage (isPowOfAggregate) (n) (factors)` *(deep model — I-leg, G-CONF-validated)* | the routed image of one factor: `tensor_product_simp_Pow(f).args` when `f` is a `Pow` over an aggregate, else `f.args` (`tensorproduct.py:322-325`, `:328-333`, `:346-355`, post-patch) | pure spec: the flag-selected image of one factor position; validated against the real patched behaviour by conformance_check.py (G-CONF LANE 2) on the patched tree |
| `powF (b n : Factor)` *(opaque — I-leg primitive)* | the exponentiation constructor `b ** e.exp` (sympy `Pow`, imported `tensorproduct.py:5`) | the UNCHANGED per-factor callee both deep models compose; uninterpreted in Lean (no consumed `ensures`) — run for real on both sides of G-CONF |

The pre-patch repo behavior the change replaces (refinement audit only, not in the
consumer spec view), at BOTH modeled sites:

* whole-expression: `tensor_product_simp`'s `Pow` branch returned
  `tensor_product_simp(e.base) ** e.exp` (`tensorproduct.py:384-385` pre-patch) —
  the exponent was left on the aggregate as a whole, never distributed across its
  factors.
* factor position: `tensor_product_simp_Mul` returned `e` unchanged whenever the
  product had 0 or 1 non-commutative factors (`if n_nc == 0 or n_nc == 1: return
  e`, `:319-320` pre-patch), and multiplied a non-`TensorProduct` factor into
  every position wholesale in the multi-factor loop
  (`new_args[i] = new_args[i] * next`, `:338-341` pre-patch) while raising
  `TypeError` if such a factor came FIRST (`:323-324` pre-patch). So a
  power-of-aggregate factor was never routed to the per-position raise from any
  factor position.

**Why the second method is modeled, stated as the finding it answers.** An
earlier revision of this bundle modeled only `distributePow`. Three of the four
assertions in the failing test exercise a power of an aggregate occupying one
FACTOR POSITION of a product, and those reach the routing sites above rather than
`tensor_product_simp`'s `Pow` branch. Measured: a patch that adds
`tensor_product_simp_Pow` and the `Pow`-branch dispatch ONLY — a faithful
implementation of `distributePow` and nothing else — leaves the failing test RED
(`FAIL_TO_PASS: test_tensor_product_simp` fails, `PASS_TO_PASS` 4/4 pass), while
the same patch plus the `tensor_product_simp_Mul` routing edits is RESOLVED by
the official harness. So a spec contracting only the whole-expression site admits
implementations that do not resolve the task; `simplifyFactor` is the obligation
that closes it.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered argument sequence `base.args` of the aggregate (a tuple of symbolic factors) | `List Factor` | `args` (Python tuple) ↔ a `List Factor`; `len(args)` ↔ `factors.length`; position `i` ↔ `factors[i]`; the empty tuple ↔ `[]`; order is preserved |
| one symbolic factor `a` | `Factor` (`abbrev Factor := Nat`) | each distinct factor ↔ a distinct `Nat` tag; identity is positional/structural only — G-CONF uses real sympy factors and never depends on the tag's numeric value |
| the exponent `e.exp` | `n : Factor` | the shared exponent ↔ `n`; held fixed across all positions |
| `b ** e.exp` (the `Pow` constructor on one factor) | `powF b n` | opaque binary op ↔ sympy `**`; the model asserts NO algebraic identity about it, only that it is applied position-wise (so the bijection is structural, not arithmetic) |
| `TensorProduct(*new_args)` (rebuilding the aggregate) | the returned `List Factor` | the result tuple ↔ the result `List`; G-CONF compares the two factor sequences element-wise |
| the routing test on ONE factor `f` of a product: `isinstance(f, Pow) and isinstance(f.base, TensorProduct)` | `isPowOfAggregate : Bool` | `True` ↔ `true` (the factor is a power of an aggregate, and `n` ↔ `f.exp`, `factors` ↔ `f.base.args`); `False` ↔ `false` (the factor is a bare aggregate, and `factors` ↔ `f.args`). The flag is the whole content of the routing decision, so the bijection is a plain boolean one — no other repo state participates |
| the commutative part `Mul(*c_part)` travelling alongside the examined factor | *(not modeled)* | the routing decision does not read or alter it and the reference patch does not change how it is reattached, so it is outside the modeled surface; G-CONF LANE 2 carries it identically on BOTH sides (`c * …`) so it cannot mask a disagreement |

`Factor` is a `Nat` tag rather than a modeled algebra because the changed behavior
is purely *structural* — "raise every position by the same exponent, preserving
order and arity" — and assumes nothing about how `**` evaluates. Pinning `powF`
opaque keeps the spec honest: a verifying impl must distribute element-wise, it
cannot exploit any property of exponentiation.

## 3. Callee provenance (deep model — validated by G-CONF / conformance_check.py)

### 3.1 `powAll` deep model ↔ `tensor_product_simp_Pow` (I-leg, G-CONF)
**Changed op:** `tensor_product_simp_Pow(e)` where `e` is a power whose base is a
`TensorProduct`. Post-patch body (gold):

```python
def tensor_product_simp_Pow(e):
    if not isinstance(e, Pow):
        return e
    if isinstance(e.base, TensorProduct):
        return TensorProduct(*[ b**e.exp for b in e.base.args])
    else:
        return e
```

The changed operation is modeled **deeply** by `powAll`/`powF` in the `pure`
region; there is **no consumed axiom** about it. `powAll n [a₀,…,a_{k-1}]`
produces `[powF a₀ n, …, powF a_{k-1} n]` — exactly the position-wise
`b**e.exp` over `e.base.args`. The per-factor callee `powF` corresponds to the
**unchanged** `Pow` constructor `**`; it is kept **opaque** and is executed for
real on both sides of G-CONF (it is an I-leg primitive, not an A-reference).

**Why there is no G-AX / `axiom_check.py` (directive 7).** G-AX exists to validate
the WEAKEST contract on an UNCHANGED callee against that callee's real behavior at
`base_commit`. This patch introduces **no** such unchanged-callee axiom: it *adds*
`tensor_product_simp_Pow`. Validating `powAll == tensor_product_simp_Pow` under
G-AX would mean (a) checking the **function under change**, which directive 7
explicitly forbids, and (b) importing a symbol that does **not exist at
base_commit** (G-AX runs without the gold patch applied) — exactly the
`ImportError` a naive `axiom_check.py` would hit. The honest mechanism is G-CONF.

**Soundness check (G-CONF, the correct gate):** `conformance_check.py` runs the
REAL patched `tensor_product_simp` (gold applied via `apply_gold=True`) on boundary
aggregates (arity 1/2/3+, distinct vs repeated factors, symbolic & integer
exponents, the issue's degenerate `tp(1,1)`/`tp(1,a)`) plus ≥10⁵ randomized fuzz
inputs, asserting `TP(*[powF b n]) == tensor_product_simp(TP(*args)**n)` (the deep
model `powAll`) on every genuine Pow-of-TensorProduct node. It restricts to that
modeled domain (excluding inputs sympy auto-collapses upstream: `n ∈ {0,1}`,
commutative-scalar aggregates) — the exact branch the spec claims. Imports only
`sympy` (the repo under test). Exit 0 iff zero disagreements.

### 3.2 `factorImage` deep model ↔ the factor-position routing (I-leg, G-CONF)

**Changed op:** the routing the gold patch adds at every place
`tensor_product_simp_Mul` examines ONE factor of a product. Post-patch (gold), the
same decision in four spellings:

```python
elif n_nc == 1:                                     # :322-325
    if isinstance(nc_part[0], Pow):
        return  Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])
    return e
...
    if not isinstance(current, TensorProduct):      # :328-333 (leading factor)
        if isinstance(current, Pow):
            if isinstance(current.base, TensorProduct):
                current = tensor_product_simp_Pow(current)
...
        if isinstance(next, Pow):                   # :346-355 (trailing factor)
            if isinstance(next.base, TensorProduct):
                new_tp = tensor_product_simp_Pow(next)
                for i in range(len(new_args)):
                    new_args[i] = new_args[i] * new_tp.args[i]
...
elif e.has(Pow):                                    # :358-360 (fallback)
    new_args = [ tensor_product_simp_Pow(nc) for nc in nc_part ]
```

Every one is the same operation on the examined factor: **if it is a power of an
aggregate, its image is that aggregate's positions each raised to the power's
exponent; otherwise its image is its own positions, untouched.** That operation is
modeled **deeply** by `factorImage`/`powAll`/`powF` in the `pure` region and
contracted by `simplifyFactor`; there is **no consumed axiom** about it. What each
site then DOES with the image (return it scaled by the commutative part, seed the
combining loop with it, multiply it position-wise into the accumulated positions)
is downstream of the modeled decision and is not modeled — see §2's last row.

**Soundness check (G-CONF LANE 2):** `conformance_check.py` runs the REAL patched
`tensor_product_simp` on `c * TP(*args)**n` (raise arm) and `c * TP(*args)`
(passthrough arm) — genuine `Mul` nodes with one non-commutative factor, so they
enter `tensor_product_simp_Mul` and reach the `:322-325` routing site — and
asserts the shadow `c * TP(*factorImage(flag, n, args))` equals it, over boundary
aggregates plus ≥10⁵ randomized fuzz inputs. The lane FAILS LOUDLY if either arm
was never reached, so a domain filter cannot quietly turn an untested arm into
apparent agreement. Measured while authoring: against a tree carrying the
whole-expression `Pow`-branch edit ONLY, the raise arm disagrees within the
boundary cases (`shadow=2*(A**x)x(B**x)` vs `oracle=2*AxB**x`), so the lane is a
live discriminator and not a tautology.

There are **no A-consumed axioms** in this bundle: `powF` carries no `ensures`,
and the proof consumes no algebraic fact about exponentiation — only the
structural front-recursive unfold of `powAll` and the case split on the routing
flag.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13974`** so the
consumer-side verdict is reproducible; each lane seeds its own generator from that
same constant, so adding LANE 2 does not perturb LANE 1's input stream. LANE 1's
R/I shadow transliterates the `distributePow` loop (the element-wise raise) to
Python — `[b**n for b in args]`, then rebuilds the aggregate — and diffs it against
`patch.diff`'s public behavior (`tensor_product_simp` applied to the corresponding
`Pow` node) over ≥10⁵ fuzzed aggregate/exponent pairs. LANE 2's R/I shadow
transliterates `simplifyFactor` (the flag-selected image of one factor position)
and diffs it against `tensor_product_simp` applied to the corresponding product
node, over ≥10⁵ fuzzed flag/aggregate/exponent/scalar tuples, both arms required
to be reached. Neither impl region contains an A-tagged callee in its computed
output (`powF`'s `**` is the I-leg's own primitive, run for real on both sides),
so both shadows are pure R/I and `conf_skip=false`.
