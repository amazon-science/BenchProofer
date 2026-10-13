# mapping.md — sympy__sympy-21847

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d9b18c518d64d0ebe8e35a98c2fb519938b9b151`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee.

Repo file under change: `sympy/polys/monomials.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectMonomials (candidates : List (List Nat)) (minDeg : Nat)` | the total-degree branch of `itermonomials` — the candidate-keeping loop, `sympy/polys/monomials.py:118-126` (commutative) and `:130-138` (non-commutative) | the modeled changed function: keep the enumerated candidates whose total degree meets the lower bound |
| `totalDegree (p : List Nat)` | `sum(powers.values())` over the per-candidate `powers` dict (`monomials.py:133` post-patch, both branches) | pure spec: the total degree of one candidate = sum of its component multiplicities |
| `selectByDegree (minDeg) (candidates)` | the body of the `for item in …:` loop that builds `monomials_list_comm` / `monomials_list_non_comm` (`monomials.py:119-126`, `:131-138`) | pure spec: the order-preserving sublist of candidates whose total degree ≥ `minDeg` |

The candidate-enumeration machinery and the term constructor that the change
does **not** touch are NOT separate symbols in the spec; they are abstracted
into the free `candidates` input (see §3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one enumerated candidate `item` (a tuple of `max_degree` factors drawn from `variables + [S.One]`), summarised by its `powers` dict | `List Nat` — the multiset of per-variable multiplicities | a candidate ↔ `[powers[v] for v in variables]` (the `S.One` slot is dropped: `powers[1]` counts the padding factors and `1 != 1` is false, so `S.One` never increments any count and never contributes degree). `len` of the vector ↔ number of distinct generators. |
| `min_degree` (an `int`, the integer `min_degrees` argument; `0` when omitted) | `minDeg : Nat` | identity on non-negative integers (the function raises `ValueError` for `min_degrees < 0` before this branch, so the live domain is `≥ 0`) |
| `sum(powers.values())` (post-patch threshold, `monomials.py:133`) | `totalDegree p = p.sum` | identity: the sum of the dict values = the sum of the multiplicity vector (the `S.One` slot contributes `0`) |
| the kept-candidates list `monomials_list_comm` / `_non_comm` before `set(...)`/`Mul(*item)` | `List (List Nat)` (the kept candidates' multiplicity vectors, in enumeration order) | order-preserving; `Mul(*item)` and the final `set(...)` dedup are a content-preserving R-postprocess applied equally pre/post-patch (mapping.md §3) |

There is no aliasing concern: `candidates` and `minDeg` are read-only and not
`mut` (directive 5).

## 3. Callee provenance — NO axioms, NO A-reference (G-AX skip)

The total-degree branch enumerates candidates with
`combinations_with_replacement(variables, max_degree)` (commutative) or
`product(variables, repeat=max_degree)` (non-commutative), counts each
candidate's factors into a `powers` dict, **applies the degree threshold**
(the changed op), then maps the survivors through `Mul(*item)` and `set(...)`.

- The enumerator (`itertools`), the per-candidate counting loop, `Mul`, and the
  final `set(...)` dedup are **UNCHANGED** by the patch and are identical on both
  legs. They are abstracted into the free input `candidates : List (List Nat)`
  (each entry = one enumerated candidate's multiplicity vector) and a
  content-preserving R-postprocess (`Mul`/`set`). The spec makes **no**
  behavioural claim about them and holds for **every** `candidates` list.
- The **only** changed operation — the per-candidate keep decision — is modeled
  **deeply** (`totalDegree`/`selectByDegree`, pure region), entirely from
  concrete arithmetic over the input. Per directive 7 the changed op is never
  axiomatized.

Therefore there is **no `axiom`** and **no A-reference deep model of an outside
callee** to validate against a real callee: `axiom_check.py` is a skip stub
(`meta.json gates.G-AX.status = "skip"`). The deep model's fidelity to the
patched behaviour is exercised mechanically by `conformance_check.py` (G-CONF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`21847`** so the
consumer-side verdict is reproducible. Its R/I shadow transliterates
`selectByDegree` (the kept-candidates filter) to Python and drives the REAL
patched `itermonomials` as the oracle, bridging via the `item ↔ powers-vector`
correspondence above (it reconstructs each yielded monomial's degree from the
real candidate enumeration and the real post-patch behaviour). No A-tagged
callee is involved (there are none), so the shadow is pure R/I.
