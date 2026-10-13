# mapping.md — sympy__sympy-23824

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 39de9a2698ad4bb90681c0fdb70b30a78233145f`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/physics/hep/gamma_matrices.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `restore_leading(leading, tail)` | the leading-restore site inside `kahane_simplify(expression)` — `sympy/physics/hep/gamma_matrices.py:697-698` (function defined at `gamma_matrices.py:421`) | the modeled changed operation: prepend the leading uncontracted run onto one core-result term |
| `leading` (parameter) | `free_pos[0:first_dum_pos]` — `free_pos` built at `gamma_matrices.py:472-474`; `first_dum_pos` at `gamma_matrices.py:460` | the leading uncontracted gamma-factor index labels, in original left-to-right order |
| `tail` (parameter) | `ri` — one element of `resulting_indices` (initialized `[[]]` at `gamma_matrices.py:503`, populated by the core rewrite loops at `gamma_matrices.py:610-688`) | one additive term produced by the core simplification, as its list of factor index labels |
| `Result()` | the rebuilt entry `free_pos[0:first_dum_pos] + ri` assigned into `resulting_indices` at the patched line | the restored term: leading run in order, then the core term |

No symbol in `model.py` is axiomatized; there is no `@ContractOnly` declaration.

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the loop
`for i in range(0, first_dum_pos): [ri.insert(0, free_pos[i]) for ri in resulting_indices]`
(`gamma_matrices.py:697-698`), which prepends each leading factor at the front
of every term in turn and so leaves the leading run in reversed order.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `free_pos[0:first_dum_pos]` — a Python `list` of gamma-factor index labels | `leading: List[int]` | `leading[i]` ↔ `free_pos[i]` (each an integer index label); `len(leading)` ↔ `first_dum_pos`; empty leading run ↔ `[]` |
| `ri` — a Python `list` of index labels (one term) | `tail: List[int]` | `tail[j]` ↔ `ri[j]`; `len(tail)` ↔ `len(ri)` |
| Python `list` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `list` `+`/slice/`len`/index |
| `free_pos[0:first_dum_pos] + ri` (list concatenation) | `ToSeq(leading) + ToSeq(tail)` (sequence concatenation) | list `+` ↔ `PSeq` `+`; concatenation is associative and order-preserving in both |
| the comprehension `list(... for ri in resulting_indices)` | a single modeled term transformation (`restore_leading` on one `ri`) | the comprehension applies the same per-term transformation uniformly to every term; modeling one representative `ri` captures the entire observable change (refinement.md §A) |

Index labels are small non-negative integers (positions/identifiers of tensor
indices); modeling them as `int` is exact. `List[int]` is the natural carrier
for the algorithm's lists-of-index-labels (no `str` is involved at this site).

## 3. Callee provenance

None. The modeled operation is pure list/sequence concatenation with an order
constraint, modeled deeply in the impl. The surrounding `kahane_simplify`
machinery that produces `leading` and `tail` is unchanged by the patch and is
treated as the (read-only) inputs to the modeled site — an R-refinement of the
unchanged context, not an axiomatized callee. There is therefore nothing for
G-AX to check (no `@ContractOnly`, no `axiom_check.py`).

## 4. Test / behaviour evidence

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
