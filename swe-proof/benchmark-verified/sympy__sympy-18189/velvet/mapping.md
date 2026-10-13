# mapping.md — sympy__sympy-18189

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1923822ddf8265199dbd9ef9ce09641d3fd042b9`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `sympy/solvers/diophantine.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reorderSolutions (order : List Nat) (permute : Bool)` | the variable-reordering branch of `diophantine(eq, param, syms, permute)` — `sympy/solvers/diophantine.py:182-185` (the `if syms != var:` block returning the reindexed set) | the modeled changed function: the dispatch that, when the requested variable order differs from canonical, solves and reindexes |
| `baseSolve (permute : Bool)` *(deep model — A-reference, opaque)* | the recursive call `diophantine(eq, param, permute=permute)` — i.e. `diophantine` invoked with `syms=None` (`sympy/solvers/diophantine.py:185` post-patch) | the UNCHANGED base solver: `diophantine` on the same equation with no `syms`, returning the full solution set; the only argument that varies between branches is the variant flag |
| `reorderTuple (order : List Nat) (t : List Int)` | `tuple([t[dict_sym_index[i]] for i in var])` — `sympy/solvers/diophantine.py:184` | pure spec: reindex one solution tuple into the requested order |
| `reorderAll (order : List Nat) (ts : List (List Int))` | `{ <reindexed tuple> for t in <base set> }` — `sympy/solvers/diophantine.py:184-185` | pure spec: reindex every tuple in the produced set |

The pre-patch repo expression the change fixes (refinement audit only, not in the
consumer spec view): the recursive call was `diophantine(eq, param)` — `permute`
omitted, so it defaulted to `False`, dropping the caller's request
(`diophantine.py:185` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a solution `tuple` of integers (one component per variable, in the solver's canonical order) | `List Int` | Python `t = (v0, v1, …)` ↔ `[v0, v1, …] : List Int`; `len(t)` ↔ `l.length`; `t[k]` ↔ `l[k]!` |
| the result `set` of solution tuples | `List (List Int)` | the Python `set` of tuples ↔ a `List` of `List Int`; membership/cardinality are the observations the F2P test makes (order within the list is immaterial — both `reorderAll` and the gold set-comprehension are *per-tuple* maps, so the carrier is compared as a set, mapping.md §4) |
| `dict_sym_index`/`[dict_sym_index[i] for i in var]` (the positional permutation) | `order : List Nat` | the permutation `[dict_sym_index[i] for i in var]` ↔ `order`; `order[p]` is the canonical index of the variable wanted at requested position `p` |
| the `permute` keyword (Bool) | `permute : Bool` | `True` ↔ `true`, `False` ↔ `false`; identity |

The permutation `order` and the result tuples are the only data the reorder
branch manipulates; the equation, parameter, and symbol objects are upstream
machinery (unchanged input) summarized by the fact that the base solver returns a
fixed set per `permute` value (modeled by `baseSolve`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `baseSolve` ↔ `diophantine(eq, param, permute=permute)` with `syms=None` (A-reference, opaque)
**Callee:** `diophantine` itself, called recursively with no `syms` argument
(`sympy/solvers/diophantine.py:185`). When `syms` is `None`/falsy the reorder
branch at line 182 is never entered, so this base call is **not on the changed
path** — the patch changes only which `permute` is forwarded *into* it, never the
callee's own body. It returns the full solution set in the canonical variable
order; with `permute=True` it additionally includes the sign/value variant
solutions (the `do_permute_signs` / `do_permute_signs_var` / `permute_few_signs`
families). The modeled `baseSolve` is **opaque** with NO asserted `ensures`: the
spec assumes nothing about *which* tuples it returns, only that the SAME flag the
caller passed reaches it. This is the discriminator: pre-patch it received
`False` unconditionally.

**Flag dependency (directive §3 flag-dependent callees):** the variant solutions
exist only for `permute=True` and only for equation families that admit them
(`general_sum_of_even_powers`, `general_sum_of_squares`, and the even-power
binary/ternary quadratics). G-AX fuzzes both flag values and over such families
so the `baseSolve true ≠ baseSolve false` distinction is genuinely exercised
(e.g. `m**4 + n**4 - 97`: 1 solution at `False`, 8 at `True`).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `diophantine(eq, param,
permute=p)` (with `syms=None`) in-container on boundary and fuzzed equations for
both `p ∈ {False, True}`, asserting (a) it is a pure function of `(eq, p)` — the
opaque-handle assumption — and (b) the variant flag is load-bearing: there exist
equations where the `True` set strictly contains the `False` set, so the modeled
`baseSolve true ≠ baseSolve false` divergence the spec hinges on is real, not
vacuous. Imports only `sympy` (the repo under test). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`18189`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`reorderAll`/`reorderTuple` (R/I-tagged ops) to Python and leaves `baseSolve`'s
callee as the REAL recursive `diophantine(eq, param, permute=permute)` with
`syms=None` (A-tagged → run real callee, not a model). The oracle is the
gold-patched `diophantine(eq, syms=syms, permute=permute)`. Both result sets are
compared as Python `set`s of tuples (membership equality), the observation the
F2P `test_diophantine` makes.
