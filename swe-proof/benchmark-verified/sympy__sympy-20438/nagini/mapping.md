# mapping.md — sympy__sympy-20438

Model ↔ repo symbol binding at `base_commit`
`33b47e4bd60e2302e42616141e76285038b724d6`.

## 1. Modeled functions

| model.py symbol | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `product_subset_of_finite(elems, finite_id) -> bool` | the new `is_subset_sets(ProductSet, FiniteSet)` multipledispatch rule, reached via `Set.is_subset` → `is_subset_sets(self, other)` | `sympy/sets/handlers/issubset.py` (new `@dispatch(ProductSet, FiniteSet)` rule, gold hunk 4); dispatcher entry `sympy/sets/sets.py:386-389`; `Set.is_subset` `sympy/sets/sets.py:349` | the changed containment decision: "ProductSet ⊆ FiniteSet iff every product element is a member" |
| `finite_sets_equal(elems_a,id_a,elems_b,id_b) -> bool` | the new `(Set, Set)` body of `_eval_is_eq`, reached via set-equality simplification | `sympy/sets/handlers/comparison.py:57-59` (gold hunk 3, `(Set,Set)` rule body changed `None` → `tfn[fuzzy_and(a.is_subset(b) …)]`) | the changed equality decision: "two sets are equal iff each is a subset of the other" |
| `simplify_equality_route(both_arith,elems_a,id_a,elems_b,id_b) -> int` | the `isinstance(_, Expr)` operand-kind guard added to `Relational._eval_simplify` and `Equality._eval_simplify` | `sympy/core/relational.py:303` (gold hunk 1) and `:558` (gold hunk 2): `if not isinstance(r.lhs, Expr) or not isinstance(r.rhs, Expr): return r` | the changed routing: a collection (non-`Expr`) equality is NOT routed through the arithmetic reduction (`lhs - rhs` / `.equals(0)`, which raised `AttributeError`) but defers to the collection-equality rule of `finite_sets_equal` |

## 2. Type abstraction

| repo reality | model as | bijection / justification |
|---|---|---|
| an element of a Cartesian product (a tuple such as `(1, 2)`) | opaque integer handle `int` | the decision uses each element only as the argument of a membership test (`b_fs.contains(x)`); identity of elements is irrelevant, only "which handle" matters. The ordered enumeration `iproduct(*self.sets)` (`ProductSet.__iter__`, `sympy/sets/sets.py:838-844`) becomes the ordered `List[int]` `elems`. |
| `ProductSet` / `FiniteSet` membership universe | a collection identifier `int` (`finite_id`, `id_a`, `id_b`) keying the `member` oracle | a `FiniteSet` is identified by an opaque id; `member(setid, el)` abstracts "`el ∈ set setid`". |
| `FiniteSet.contains(x)` (definite-bool branch) | `member(setid, el) -> bool` (axioms region) | the unchanged callee the new rule invokes; see §3. |
| `fuzzy_and(b_fs.contains(x) for x in a_ps)` over a fully-decidable concrete product | the boolean fold `all_in` (every handle is a member) | `fuzzy_and` returns a definite `True`/`False` exactly when every term is a definite bool; the F2P inputs are concrete integer tuples, so membership is always decidable and `fuzzy_and` is the boolean conjunction. The `tfn[...]` wrapper (`sympy/sets/sets.py:31-35`) maps `True→S.true`, `False→S.false`. (mapping.md §3.) |
| `isinstance(r.lhs, Expr) and isinstance(r.rhs, Expr)` (whether both operands support arithmetic reduction) | the `bool` flag `both_arith` | the guard branches solely on whether both operands are `Expr` (number-like, supporting `lhs - rhs` and `.equals(0)`); a `Set` operand is NOT `Expr`. The discriminator is exactly this two-way operand-kind test, so `both_arith` carries it faithfully. The two outcome tokens — `ARITH_PATH()` (the unchanged arithmetic path, opaque) and `collection_outcome(equal)` (the collection-equality value, distinct from `ARITH_PATH()`) — abstract "which path was taken / what the collection rule decided". |

## 3. Callee provenance

### 3.1 `member` (A-consumed) — models `FiniteSet.contains`

- **Real callee:** `Set.contains` / `FiniteSet._contains`, `sympy/sets/sets.py:293-337` and `1846-1873`. The new rule calls `b_fs.contains(x)` for each product element `x`.
- **Contract claimed (weakest sufficient):** `member` is a `@Pure @ContractOnly` function with **no value `Ensures`** — only purity (determinism) and totality are relied upon. The proof never assumes a particular membership value; it only needs that the impl loop reads the SAME membership fact the spec fold reads.
- **Why sound:** for concrete (numeric / tuple-of-numeric) elements, `FiniteSet.contains` returns a definite `S.true`/`S.false` deterministically (`_contains` does `other in self._args_set` else `fuzzy_or(Eq(e,other) …)`). An axiom that claims nothing about the value cannot be stronger than the real callee. G-AX (`axiom_check.py`) confirms determinism + definite-bool totality on the F2P witnesses and fuzz; it never asserts an exact value, matching the empty value-contract.
- **Flag dependency:** none.

### 3.2 Deep-model references (A-reference) — validated, not consumed

- **`product_subset_of_finite` deep fold (`all_in`)** models the new
  `is_subset_sets(ProductSet, FiniteSet)` rule
  (`sympy/sets/handlers/issubset.py`, gold hunk 4:
  `return fuzzy_and(b_fs.contains(x) for x in a_ps)`). The per-element
  conjunction over the enumerated product is spelled out in the model
  (`all_in`), NOT axiomatized. `axiom_check.py` asserts
  `ProductSet.is_subset(FiniteSet) == all(x ∈ finite for x in product)`
  directly on the enumerated elements (no double-mask: the membership predicate
  appears on only one side of the value being decided; the equivalence is
  asserted at the boolean-decision level).
- **`finite_sets_equal` deep fold** models the new `(Set, Set)` rule of
  `_eval_is_eq` (`sympy/sets/handlers/comparison.py:57-59`, gold hunk 3:
  `return tfn[fuzzy_and(a.is_subset(b) for a,b in [(lhs,rhs),(rhs,lhs)])]`),
  reached when `Eq(A,B).simplify()` is asked for two finite sets. The model
  spells out "each contains the other"; `axiom_check.py` asserts
  `Eq(A,B).simplify() is S.true ⇔ (A⊆B and B⊆A)` and `is S.false` otherwise.
- **`simplify_equality_route` routing** models the `isinstance(_, Expr)` guard
  added to `Relational._eval_simplify` (`sympy/core/relational.py:303`) and
  `Equality._eval_simplify` (`:558`). The model spells out "if both operands are
  arithmetic, take the arithmetic path; otherwise defer to the collection rule
  and never return the arithmetic-path token". `axiom_check.py`'s `check_route`
  asserts the real `Eq(A,B).simplify()` on collection (non-`Expr`) operands does
  NOT raise (pre-patch raised `AttributeError` on `lhs - rhs` / `.equals(0)`) and
  reaches a defined collection decision, and that the model flag `both_arith`
  matches `isinstance(lhs,Expr) and isinstance(rhs,Expr)`.

## 4. Additional gold-patch sites NOT separately modeled (covered by patch.diff verbatim)

- **`sympy/sets/handlers/comparison.py`** hunk 3 also deletes one of TWO
  byte-identical `@dispatch(FiniteSet, Interval)` rules (both `return False`,
  `:14-16` and `:27-29`); removing a duplicate is a behavioral no-op.
- **`sympy/sets/handlers/issubset.py`** hunk 4 also adds `ProductSet` to the
  module import list — a prerequisite of the new rule, no behavior of its own.

All of §4 is present in `patch.diff` (gold verbatim, applies cleanly at
base_commit, G-RESOLVE) and is the real correctness oracle.
