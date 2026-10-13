# mapping.md — sympy__sympy-19040

## Instance
- repo: sympy/sympy @ `b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9`
- changed file: `sympy/polys/factortools.py`
- changed function: `dmp_ext_factor(f, u, K)` (lines 1138–1165 @ base_commit)
- gold hunk: line 1150, `dmp_sqf_norm(f, u, K)` → `dmp_sqf_norm(F, u, K)`

## Modeled function
`implementation_extFactor` / `problem_spec_extFactor` / `correct_extFactor`
models the multivariate branch (`u > 0`) of `dmp_ext_factor` — factorization of
a multivariate polynomial over an algebraic number field. The univariate
dispatch (`if not u: return dup_ext_factor(...)`, line 1140) is OUT of the modeled
configuration: the gold patch only touches the multivariate body, so the modeled
precondition is "multivariate input" (`u > 0`).

## Symbol binding (file:line @ base_commit)
| Lean | Python | site |
|---|---|---|
| `Poly` | dmp polynomial over `K` (algebraic field) | carrier |
| `GPoly` | dmp polynomial over `K.dom` (ground domain) | carrier (norm `r`, factor list) |
| `Coeff` | element of `K` (the leading coefficient `lc`) | carrier |
| `groundLC f` | `dmp_ground_LC(f, u, K)` | factortools.py:1143 |
| `groundMonic f` | `dmp_ground_monic(f, u, K)` | factortools.py:1144 |
| `degreeList f` | `dmp_degree_list(f, u)` | factortools.py:1146 |
| `degreesNonpos ds` | `all(d <= 0 for d in ds)` (pure helper) | factortools.py:1146 |
| `sqfPart f` | `dmp_sqf_part(f, u, K)` | factortools.py:1149 |
| `sqfNorm f` → `(s,g,r)` | `dmp_sqf_norm(f, u, K)` | sqfreetools.py:122 (callee) |
| `factorListInclude r` | `dmp_factor_list_include(r, u, K.dom)` | factortools.py:1152, 1331 (callee) |
| `raiseShift s` | `dmp_raise([K.one, s*K.unit], u, 0, K)` | factortools.py:1157 |
| `recoverOne H g entry` | one loop body: `dmp_convert` ∘ `dmp_inner_gcd` ∘ `dmp_compose`, returns `(h, g')` | factortools.py:1159–1162 |
| `trialDivision F factors` | `dmp_trial_division(F, factors, u, K)` | factortools.py:103 (callee) |

## Lean ↔ Python type bijection (for G-CONF / G-AX)
- `Poly` / `GPoly` / `Coeff` are OPAQUE identity carriers: only the algebra
  callees observe their structure. No structural predicate over them is asserted
  by the spec, so no fuzzing bijection is required (conf_skip — see below).
- `(Coeff × List (Poly × Nat))` ↔ the `(lc, factors)` return of `dmp_ext_factor`
  where `factors` is a list of `(factor, multiplicity)` pairs.

## Callee provenance + flag deps
All algebra callees are UNCHANGED by the gold patch (the patch only reroutes one
argument). They are declared `opaque` (signatures only) so they can appear in the
executable skeleton. The fix is the choice of which polynomial flows into
`sqfNorm`: the full monic original (`groundMonic f`) rather than its square-free
part (`sqfPart (groundMonic f)`). No flag-dependent callees.

## Axioms
The proof obligation is a structural unfolding (the spec restates the modeled
data flow; the one inductive step is loop = front-recursive fold over the factor
list, a list-shape lemma needing NO callee property). The construction agent
declares only `opaque` signatures and ships NO `axiom _prop`. If the proof agent
gets stuck it may propose `_prop` axioms (then G-AX gains teeth); as shipped,
axiom_check.py is a skip stub.

## G-CONF fuzz seed
conf_skip = true. The impl region is ALL-A-tagged (every operation is an opaque
unchanged callee; the fix is pure data routing among them, encoded directly in
patch.diff). There is no R/I concrete computation in Lean to differentially test,
so conformance_check.py is a skip stub (seed unused, pinned 19040).
