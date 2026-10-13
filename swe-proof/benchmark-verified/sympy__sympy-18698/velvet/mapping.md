# mapping.md — sympy__sympy-18698

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3dff1b98a78f28c953ae2140b69356b8391e399c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), records the
provenance of the unchanged upstream computation whose output is the modeled
function's read-only input, and pins the G-CONF fuzz seed.

Repo file under change: `sympy/polys/polytools.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineByTag (items : List Item)` | `_symbolic_factor_list(expr, opt, method)` — `sympy/polys/polytools.py:5898` (changed tail appended at the post-patch line shown in `patch.diff` hunk 2, just before `return coeff, factors` at `polytools.py:5953`) | the modeled changed function: the square-free factor-list builder whose returned `factors` list is the report passed up to `_generic_factor_list`/`sqf_list` |
| `items : List Item` (read-only input) | the value of the local `factors` list **as built by the unchanged factor-collection loop** (`polytools.py:5903-5950`, the `for arg in args:` body) immediately before the patched grouping tail runs | the pre-grouping `(square-free-factor, multiplicity)` list the changed tail consumes; see §3 |
| `combineAll (items)` *(deep model)* | the *post-patch* grouping tail (`patch.diff` hunk 2): `factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k) for k in set(i for _, i in factors)]` (guarded by `method == 'sqf'`) | pure spec: collapse the factor list by multiplicity, multiplying together all factors that share a multiplicity |
| `combineInto`, `combineStep` *(pure)* | one iteration of "for the next factor `(f, k)`, multiply it into the running product for multiplicity `k`" — the per-element realisation of the `reduce(mul, …)`-per-group expression | pure spec: one tag-keyed combine |
| `Content = List Int`, `Item = Content × Int` | a square-free factor polynomial (`Content`) paired with its integer multiplicity (`Int` tag) | the value/tag carrier; see §2 |

There are **no axioms** in this bundle and **no `axiom_check.py`**: the changed
function's new behavior (grouping its own factor list by multiplicity and
multiplying within each group) is modeled **deeply** by `combineAll`/`combineInto`
over the read-only input `items`. The upstream factor-collection loop is **not a
callee** and is **not axiomatized** — its entire relevant effect is the value of
`items` (§3). G-AX therefore reports `skip`; G-CONF carries the soundness load.

The pre-patch repo behavior the change removes (refinement audit only, not in
the consumer spec view): the factor list is returned **ungrouped**, so two
distinct square-free factors that happen to share a multiplicity are reported as
two separate entries instead of one combined entry. `Solution_prepatch.lean`
reproduces that "emit every factor raw" skeleton and fails both `ensures`
clauses.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one square-free factor: a polynomial `f` paired with multiplicity `k` (`(f, k)`, `f` a sympy `Poly`/`Expr`, `k` a positive `int`) | `Item = Content × Int` | `f` ↔ `Content` (a `List Int` of interned atom codes) via the **free-monoid bridge** below; `k` ↔ `snd : Int` identically (small positive int) |
| a polynomial that is a **product of distinct irreducible square-free factors** | `Content = List Int` | each distinct irreducible polynomial present in the case is assigned a unique atom code (an `Int`); a `Content` denotes the **product** of its atoms' polynomials. The model's value product (`++`, list concatenation) ↔ polynomial multiplication. Commutativity/associativity of polynomial `*` is reflected by comparing results as a **multiset of factors** (§3.3), since order among factors is not observable. |
| the pre-grouping factor list (a Python `list` of `(f, k)`) | `items : List Item` | element-wise via the row bijection; order preserved; `len` ↔ `.length` |
| the post-patch returned `factors` list | `out : List Item` | element-wise via the row bijection; compared as a multiset of `(expanded f, k)` (§3.3) |

The `coeff` returned alongside `factors`, and the `expr`/`opt`/`method`
arguments, are **not** carried into `Item`: the grouping tail keys/values only on
`(factor, multiplicity)`, and (for the G-CONF cases, which are monic products of
distinct irreducibles) `coeff` is the constant `1`. The free-monoid bridge is
faithful because the grouping logic observes only **multiplicity-equality** and
**which factors get multiplied together** — never the internal structure of a
factor polynomial; G-CONF then de-interns and asks the **real** `sqf_list`
whether the multiset of `(factor, multiplicity)` matches, so the interning never
has to be exact, only injective per case.

## 3. Provenance of the read-only input `items`

### 3.1 The upstream factor-collection loop is unchanged in behavior
`items` is the local `factors` list built by `_symbolic_factor_list`'s
`for arg in args:` loop **before** the patched grouping tail. The gold patch
touches this loop region in **hunk 1** (`polytools.py:5908`): it rewrites

```python
        if arg.is_Mul:
            args.extend(arg.args)
            continue
        if arg.is_Pow:
```
into
```python
        elif arg.is_Pow:
```

### 3.2 Hunk 1 is observably inert (fuzz-verified) — so `items` is faithful input
This refactor (dropping the `is_Mul` flatten branch and chaining the `is_Pow`
test with `elif`) is **behaviorally inert** on the inputs the issue and the F2P
tests exercise: `Mul.make_args(expr)` already returns the top-level factors of a
`Mul`, so the `arg.is_Mul` re-extend branch is dead for the polynomial products
in scope. **Verification (this bundle, not an oracle):** running the *full gold
patch* against a *grouping-only* variant (hunk 2 alone, hunk 1 reverted) over
**3000** randomly-generated factor products (`seed=20240617`, mixed bases and
exponents) produced **0** differences in `sqf_list` output, while the same fuzz
set distinguished base-vs-full on 2588/3000 cases (i.e. the fuzz genuinely
exercises the change). Therefore the changed tail consumes the **same**
pre-grouping `factors` list pre- and post-hunk-1, and modeling that list as the
read-only input `items` is sound. Hunk 1 is tagged a pure refactor (**I**, no
behavioral effect) in refinement.md.

### 3.3 What is observable
`_symbolic_factor_list`'s output is re-sorted downstream by `_sorted_factors`
(`polytools.py:5877`, called from `_generic_factor_list` at `polytools.py:5998`),
so the **order** of the factor list `combineByTag` returns is **not** observable
at the `sqf_list` boundary — only the **content**: which `(factor, multiplicity)`
pairs are present. G-CONF therefore compares the shadow and the real patched
`sqf_list` as a **multiset of `(expand(factor), multiplicity)`** pairs. The
`Nodup`-on-tags `ensures` is the structural witness of the fix: after grouping,
each multiplicity appears at most once.

## 4. G-CONF fuzz seed + flag dependency

- **Pinned fuzz seed:** `SEED = 18698` (`conformance_check.py`). `N_FUZZ = 100000`.
- **Flag dependency:** the grouping tail is guarded by `method == 'sqf'`. The
  modeled function and G-CONF both fix `method = 'sqf'` (via `sqf_list`); under
  `method == 'factor'` the tail does not run (and `factor_list` is unchanged —
  confirmed: `factor_list((x**2+1)*(x-1)**2*(x-2)**3*(x-3)**3)` is identical
  pre/post patch). This is the configuration G-CONF fuzzes.
- **Cases:** products of subsets of distinct monic irreducible (hence
  square-free) polynomials over one generator, multiplicities drawn from a small
  range so distinct factors frequently **share** a multiplicity (exercising the
  combine-on-shared-tag behaviour that is the fix). The boundary set includes
  the exact issue polynomial's square-free structure
  `(x**2+1)^1 (x-1)^2 (x-2)^3 (x-3)^3`.
