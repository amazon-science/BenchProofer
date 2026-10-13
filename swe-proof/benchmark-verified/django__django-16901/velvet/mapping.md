# mapping.md — django__django-16901

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ee36e101e8f8c0acde4bb148b738ab7034e902a0`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change: `django/db/models/sql/where.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `oddParityReduce (children : List Bool)` | the n-ary exclusive-or rewrite branch inside `WhereNode.as_sql` — `django/db/models/sql/where.py:128-145` (`if self.connector == XOR and not connection.features.supports_logical_xor:`) | the modeled changed function: the boolean value the rewritten predicate computes for one row |
| `trueCount (xs : List Bool)` | `reduce(operator.add, (Case(When(c, then=1), default=0) for c in self.children))` — `where.py:135-138` (post-patch) | pure spec: the integer sum of the per-operand 1/0 indicators (the `rhs_sum`) |
| `parityOdd (xs : List Bool)` | the row-level meaning of the whole rewritten predicate `(a OR b OR …) AND MOD(Σ, 2) == 1` for n>2 (and `(a OR …) AND Σ == 1` for n≤2, which coincides) | pure spec: the chained exclusive-or value (true iff an odd number of operands are true) |

There is **no axiom and no deep-model A-reference** in this bundle: the changed
operation is an arithmetic/boolean reduction over already-evaluated operand
truth values; the model takes those truth values as free inputs and assumes no
callee contract (refinement.md §C, like django__django-11141 / -14089). The SQL
builders the branch calls — `self.__class__(...)`, `Case`, `When`, `Mod`,
`Exact`, `reduce`, `operator.add` — are unchanged constructors that ASSEMBLE the
predicate; their fidelity (that the assembled SQL evaluates to exactly this
boolean per row) is exercised end-to-end by the G-CONF oracle, which runs the
real patched Django against an in-memory SQLite database (which lacks native
XOR, so it takes this very branch), and by G-RESOLVE.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate between the Lean value domain
and the repo's behaviour. The change rewrites an `XOR` `WhereNode` whose
`children` are SQL boolean expressions into a conjunction; the **observable**
behaviour of that rewrite is *which rows the resulting WHERE clause selects*. We
model that row-level semantics directly.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the list `self.children` of the XOR `WhereNode` (each child a boolean SQL condition) **evaluated on one database row** | `children : List Bool` | child `c` ↔ the Bool "does row satisfy `c`"; `len(self.children)` ↔ `children.length`; child order ↔ list order (addition is commutative, so the sum is order-independent) |
| `Case(When(c, then=1), default=0)` for child `c` on a row | `if c then 1 else 0 : Nat` | the SQL `CASE WHEN c THEN 1 ELSE 0` yields 1 iff the row satisfies `c` |
| `reduce(operator.add, …)` (`rhs_sum`) on a row | `trueCount children : Nat` | the integer sum of the indicators = number of satisfied children |
| `Mod(rhs_sum, 2)` (taken only when `len(children) > 2`) | `s % 2` (taken only when `children.length > 2`) | SQL `MOD(x, 2)` ↔ `Nat` `% 2`; both are 0/1 because the summands are 0/1 |
| `Exact(1, rhs_sum)` — the equality lookup `rhs_sum == 1` | `decide (rhsVal = 1)` | `Exact(1, X)` renders `X = 1`; selects the row iff the (possibly mod-reduced) sum equals 1 |
| the OR node `self.__class__(self.children, OR)` (`lhs`) on a row | `decide (0 < trueCount children)` | an OR clause selects a row iff at least one child is satisfied, i.e. the count is positive |
| the outer `AND` of `[lhs, rhs]` on a row | Bool `&&` | the conjunction selects a row iff both the OR clause and the equality hold |
| `self.negated` flag on the rebuilt AND node | (omitted — unchanged outer frame) | negation wraps the whole conjunction identically pre- and post-patch (`self.__class__([lhs, rhs], AND, self.negated)`); the change touches only `lhs`/`rhs` construction, so the modeled value is the pre-negation matched predicate. The F2P/P2P XOR tests are non-negated. |

`Nat`/`List Bool` indexing is total and sound. The carrier is `List Bool`
because the rewrite's observable content is a per-row boolean reduction over the
operand truth values; the integer arithmetic (`trueCount`, `% 2`) is modeled
exactly with `Nat`.

## 3. Callee provenance & flag dependencies

- **Branch guard `not connection.features.supports_logical_xor`.** The rewrite
  fires only on backends WITHOUT native XOR. `supports_logical_xor` defaults to
  `False` (`django/db/backends/base/features.py:355`) and is `True` only on
  MySQL (`.../mysql/features.py:58`). The G-CONF oracle uses the SQLite backend
  (default `False`) so it takes exactly this branch; recorded here so the gate
  fuzzes the right configuration (SPEC_GUIDE §3 flag-dependent callees).
- **No axiomatized callees.** `Case`/`When`/`Mod`/`Exact`/`reduce`/
  `operator.add`/`self.__class__` are unchanged SQL/stdlib constructors that the
  branch composes; the model does not depend on any contract of theirs beyond
  the value-level bijection in §2 (which G-CONF refutes end-to-end). Hence
  `meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py`
  reports `status=skip` (G-AX vacuous; see refinement.md §C).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16901`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`trueCount`/`parityOdd` and the impl's branch to Python and diffs the row-level
match decision against the ORACLE: the real gold-patched Django building and
executing the XOR `WhereNode` against an in-memory SQLite database (no native
XOR ⇒ the rewrite branch ⇒ the SQL the patch generates), over fuzzed
(n-children × per-row truth-assignment) inputs.
