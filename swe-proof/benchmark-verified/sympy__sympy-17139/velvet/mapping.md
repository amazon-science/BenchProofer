# mapping.md — sympy__sympy-17139

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1d3327b8e90a186df6972991963a5ae87053259d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records callee
provenance and flag dependencies.

Repo file under change: `sympy/simplify/fu.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `powerRewriteStep (rv exp matchesPow transformed)` | the nested `_f(rv)` rewrite inside `_TR56` — `sympy/simplify/fu.py:498` (body of `def _f`, lines 498–522), driven by `bottom_up(rv, _f)` at `fu.py:524` | the modeled changed function (one rewrite step on a candidate power) |
| `matchesPow : Bool` | `rv.is_Pow and rv.base.func == f` (`fu.py:499`) | the unchanged first guard: is the node a power of the targeted trig function `f`? Modeled as a FREE Bool (unchanged sub-step, directive 7). |
| `exp : Cexp` / `expIsReal exp` | `rv.exp` / `rv.exp.is_real` (`fu.py`, exponent of the `Pow`) | the exponent and its reality predicate — the property the new guard consults |
| `transformed : Expr` | the value the downstream of `_f` produces for a targeted power with a real, in-range exponent (`fu.py:504–522`: the `rv.exp < 0` / `> max` / `== 2` / `h(g**2)**e` ladder) | the unchanged downstream rewrite. Modeled as a FREE `Expr` (unchanged sub-step, directive 7). |

The change under spec is the inserted guard at `fu.py:502–503`:
`if not rv.exp.is_real: return rv`. It is NOT axiomatized — it is modeled
directly in the method body (the second `if`). `_TR56`, `TR5`, `TR6`, `_f`,
`is_real`, `rv.exp` are repo-internal names and do NOT appear in the spec view.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real sympy types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a sympy expression node `rv` (whatever `_f` is handed) | `Expr` (opaque, identity-only) | only equality is observed: `out == rv` (unchanged) vs `out == transformed` (rewritten). G-CONF compares the real `_TR56(rv,…)` output object against `rv` or the downstream value, never inspecting internal structure. |
| `rv.exp` (the exponent, a sympy `Expr`) | `Cexp {re, im}` | a number with real/imaginary components; only `expIsReal` is read |
| `bool(rv.exp.is_real)` truthiness | `expIsReal exp = (exp.im == 0)` | **`expIsReal exp = true` ↔ `rv.exp.is_real is True` (proceed); `expIsReal exp = false` ↔ `rv.exp.is_real is False OR None` (return unchanged).** The patch guard `if not rv.exp.is_real: return rv` treats `False` and `None` (undetermined) alike, both leaving the expression untouched; the model's two-valued `expIsReal` collapses both to `false`. A purely/partly imaginary exponent (nonzero imaginary part) has `is_real = False`; the model's `im ≠ 0` mirrors this. |
| `rv.is_Pow and rv.base.func == f` | `matchesPow : Bool` (free) | the targeted-power guard, unchanged by the patch; free Bool (every value admitted). |
| the downstream rewrite value (`h(g(...)**2)**e`, or `rv` when out-of-range) | `transformed : Expr` (free) | the unchanged downstream; free `Expr` (every value admitted). In G-CONF it is left as the real callee: the actual `_TR56` downstream output. |

## 3. Callee provenance & flags

- **No consumed axioms; no deep-model reference.** The two unchanged sub-steps
  (`matchesPow`, `transformed`) are modeled as free values (strictly weaker than
  any concrete contract — directive 7), so neither is owed an axiom and G-AX is
  skipped (no `axiom_check.py`). The only behaviour pinned — non-real exponent ⇒
  unchanged — is decided structurally in the `pure`/method body (`expIsReal`).
- **Flag dependency:** `_TR56` takes `f, g, h, max, pow`. The modeled guard is
  independent of `max`/`pow` (they only affect the downstream `transformed`).
  G-CONF nonetheless fuzzes over `f ∈ {sin, cos}`, `max ∈ {4,6,10}`,
  `pow ∈ {False,True}` so the unchanged-frame of the guard is exercised under
  every configuration.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`17139`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the
`powerRewriteStep` `do` block to Python over the real sympy types
(`matchesPow := rv.is_Pow and rv.base.func == f`; the new guard
`not rv.exp.is_real`); the unchanged downstream (`transformed`) is left as the
real callee, i.e. the actual `_TR56(rv, …)` output. Oracle = the patched
`_TR56` behaviour (`patch.diff` applied at `base_commit`).
