# mapping.md — sympy__sympy-23824

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 39de9a2698ad4bb90681c0fdb70b30a78233145f`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), and records callee
provenance.

Repo file under change: `sympy/physics/hep/gamma_matrices.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `restoreLeading(leading, tail)` | the leading-restore site inside `kahane_simplify(expression)` — `sympy/physics/hep/gamma_matrices.py:697-698` (function defined at `gamma_matrices.py:421`) | the modeled changed operation: prepend the leading uncontracted run onto one core-result term, preserving the run's original order |
| `leading` (parameter) | `free_pos[0:first_dum_pos]` — `free_pos` built at `gamma_matrices.py:472-474`; `first_dum_pos` at `gamma_matrices.py:460` | the leading uncontracted gamma-factor index labels, in original left-to-right order |
| `tail` (parameter) | `ri` — one element of `resulting_indices` (initialized `[[]]` at `gamma_matrices.py:503`, populated by the core rewrite loops at `gamma_matrices.py:610-688`) | one additive term produced by the core simplification, as its list of factor index labels |
| `out` (return) | the rebuilt entry `free_pos[0:first_dum_pos] + ri` assigned into `resulting_indices` at the patched line | the restored term: leading run in order, then the core term |
| `restoreSeq` (pure helper) | n/a — the deep model of the per-term restoration (`leading ++ tail`); not a repo symbol | front-recursive concatenation; `restoreSeq leading tail = leading ++ tail` (proven) |

No symbol in `Solution.lean` is axiomatized; there is no `axiom` and no `:|`
imperative-callee stub.

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the loop
`for i in range(0, first_dum_pos): [ri.insert(0, free_pos[i]) for ri in resulting_indices]`
(`gamma_matrices.py:697-698`), which front-inserts each leading factor in turn
and so leaves the leading run in reversed order.

## 2. Type abstraction (R-refinements; the G-CONF bijection)

| repo reality | Lean carrier | bijection |
|---|---|---|
| `free_pos[0:first_dum_pos]` — a Python `list` of gamma-factor index labels | `leading : List Int` | `leading[i]` ↔ `free_pos[i]` (each an integer index label); `leading.length` ↔ `first_dum_pos`; empty leading run ↔ `[]` |
| `ri` — a Python `list` of index labels (one term) | `tail : List Int` | `tail[j]` ↔ `ri[j]`; `tail.length` ↔ `len(ri)` |
| Python `list` value inside a specification | Lean `List Int` | `List`-level `++` / `take` / `drop` / `length` / `[i]!` mirror Python `list` `+` / slice / `len` / index |
| `free_pos[0:first_dum_pos] + ri` (list concatenation) | `leading ++ tail` (list append) | Python `+` ↔ Lean `++`; concatenation is associative and order-preserving in both |
| the comprehension `list(... for ri in resulting_indices)` | a single modeled term transformation (`restoreLeading` on one `ri`) | the comprehension applies the same per-term transformation uniformly to every term; modeling one representative `ri` captures the entire observable change (refinement.md §A) |

Index labels are small non-negative integers (positions/identifiers of tensor
indices); modeling them as `Int` is exact. `List Int` is the natural carrier for
the algorithm's lists-of-index-labels (no `str` is involved at this site).

## 3. Callee provenance

None. The modeled operation is pure list concatenation with an order
constraint, modeled deeply in the impl (the backward prepend fold whose net
effect is `restoreSeq leading tail = leading ++ tail`). The surrounding
`kahane_simplify` machinery that produces `leading` and `tail` is unchanged by
the patch and is treated as the (read-only) inputs to the modeled site — an
R-refinement of the unchanged context, not an axiomatized callee. There is
therefore nothing for G-AX to check (no `axiom`, no `:|`-stub, no
`axiom_check.py`).

## 4. G-CONF fuzz seed

Pinned seed `23824`, `N = 100000`. The conformance check builds the R/I shadow
of the `restoreLeading` impl region in Python (`leading ++ tail`) and diffs it
against `patch.diff`'s rebuilt-entry behaviour
(`free_pos[0:first_dum_pos] + ri`) over the fuzzed inputs.

## 5. Test / behaviour evidence

The F2P test `test_kahane_simplify1`
(`sympy/physics/hep/tests/test_gamma_matrices.py`) adds, post-patch:
- `kahane_simplify(G(mu)*G(-mu)*G(rho)*G(sigma))` → `4*G(rho)*G(sigma)`
  (no leading uncontracted run before the contraction here, but exercises the
  contraction core), and
- `kahane_simplify(G(rho)*G(sigma)*G(mu)*G(-mu))` → `4*G(rho)*G(sigma)`,
  whose leading uncontracted run is `[rho, sigma]`. Pre-patch this returned
  `4*G(sigma)*G(rho)` (the run reversed) — the exact bug the model's order
  constraint forbids. The P2P tests `test_kahane_algorithm` and
  `test_gamma_matrix_class` (no multi-factor leading run, or order-insensitive
  scalar results) remain unaffected, consistent with the order-only change.
