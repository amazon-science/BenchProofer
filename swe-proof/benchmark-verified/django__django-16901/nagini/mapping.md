# mapping.md — django__django-16901

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ee36e101e8f8c0acde4bb148b738ab7034e902a0`, states the type
abstraction, and (there being no axioms) documents why no callee is
axiomatized.

Repo file under change: `django/db/models/sql/where.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `xor_fallback_matches(operands)` | the exclusive-disjunction fallback branch inside `WhereNode.as_sql` — `django/db/models/sql/where.py:114` (the `if self.connector == XOR and not connection.features.supports_logical_xor:` block, body lines 128-141) | the modeled changed function: the boolean the constructed fallback predicate evaluates to for one row's operand truth assignment |
| `count_true(s)` | the value of `rhs_sum = reduce(operator.add, (Case(When(c, then=1), default=0) for c in self.children))` (`where.py:134-137`) | pure spec: number of true operands = the running sum of the per-operand 1/0 contributions |
| `any_true(s)` | the value of `lhs = self.__class__(self.children, OR)` (`where.py:133`) | pure spec: the disjunction of the operands ("at least one true") |
| `derived_count(s)` | `rhs_sum` after the (added) `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` (`where.py:138`, the gold-added lines) | pure spec: the count compared to one — raw sum for ≤2 operands, parity for >2 |
| `xor_holds(s)` | the truth value of the final node `self.__class__([lhs, rhs], AND, self.negated)` with `rhs = Exact(1, rhs_sum)` (`where.py:138-141`) | pure spec: `(OR of operands) AND (derived count == 1)` |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): the fallback built `rhs = Exact(1,
rhs_sum)` directly from the raw sum, so the predicate was `(OR …) AND (sum ==
1)` — "exactly one operand true" — for every operand count. The gold inserts
the parity reduction `Mod(rhs_sum, 2)` when there are more than two operands.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.children` — a list of operand predicates, each evaluating to true/false for a given row | `operands: List[int]`, entry `1` ⇔ a true operand (any other entry contributes 0) | `operands[k] == 1` ⇔ child `k` is true for the row; `len(operands)` ↔ `len(self.children)` |
| `Case(When(c, then=1), default=0)` (an SQL expression) | the integer `1 if c == 1 else 0` | the SQL `CASE` evaluates to 1 when the child is true, 0 otherwise — its runtime denotation is this integer |
| `reduce(operator.add, …)` over the per-child cases | integer sum (`count_true`) | SQL `+` of the case values ↔ integer addition |
| `Mod(rhs_sum, 2)` (an SQL function call) | integer remainder `rhs_sum % 2` | `Mod` denotes integer modulo at evaluation time |
| `Exact(1, rhs_sum)` (an SQL lookup) | the predicate `rhs_sum == 1` | `Exact(a, b)` denotes the equality `a == b` |
| `self.__class__([lhs, rhs], AND, …)` (an SQL `AND` node) | boolean `and` (`xor_holds`) | SQL conjunction ↔ boolean `and` of the two sub-predicate truth values |
| `self.__class__(self.children, OR)` (an SQL `OR` node) | boolean disjunction (`any_true`) | SQL disjunction ↔ boolean `or` over the operands |
| the evaluation COMPLETES: the fallback predicate is a finite expression (a `reduce` over `len(self.children)` CASE terms, one `Mod`, one `Exact`, one `AND`/`OR`) whose per-row evaluation always finishes and yields the match decision | `Requires(MustTerminate(2))` on `xor_fallback_matches`, discharged in the loop by the strictly decreasing measure `Invariant(MustTerminate(i))` | the real evaluation is bounded, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering (Nagini checks partial correctness by default, so without it a non-terminating same-spec body satisfies every `Ensures` vacuously — the audit's P1 witness; its faithful real patch would hang the F2P/P2P xor tests and not resolve). |

### 2.1 Plumbing modelled as identity / omitted
- `self.negated` and the recursive `.as_sql(compiler, connection)` lowering are
  SQL-rendering steps: they determine how the predicate is *spelled* in SQL
  (and, for `negated`, whether the whole node is wrapped in `NOT`), but the
  F2P test `test_filter_multiple` exercises the non-negated path and observes
  only the rows the predicate selects. For a fixed operand assignment the
  selected/not-selected outcome is the truth value of `xor_holds`, which is
  what the model pins. (The negated path is a uniform `NOT` over this same
  predicate and is covered by the existing P2P `test_filter_negated`, whose
  ≤3-operand cases the parity/exactly-one branches agree on.)
- `EmptyResultSet` / `FullResultSet` short-circuits in `as_sql` concern empty or
  always-true children, not the arithmetic the patch changes.

`str`/SQL-AST objects are not indexed in the model; the carrier is `List[int]`
of operand truth values, and the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance — none axiomatized

There is **no `@ContractOnly` axiom** in this bundle, so there is no callee
provenance to cite for an axiom. The operations the patch composes — `Case` /
`When` (a 1/0 choice), `reduce(operator.add, …)` (a sum), `Mod` (a modulo),
`Exact` (an equality), and the `OR`/`AND` connectors — are SQL *expression
builders* whose **runtime denotation** is ordinary integer/boolean arithmetic.
The changed operation (inserting `Mod(rhs_sum, 2)`) is precisely a change in
that arithmetic, so per SPEC_GUIDE §3 / PLAN §3 kind-I it is modelled **deeply**
with native Nagini integer arithmetic (`%`, `+`, `==`, `and`, `or`), never
axiomatized. Modelling it behind an axiom would be axiomatizing the operation
the patch changes — forbidden by directive 7.

Source for the denotations (every supported backend lacking native XOR, e.g.
PostgreSQL/SQLite): `Mod` — `django/db/models/functions/math.py:124`
(`class Mod`), rendering SQL `MOD(a, b)` / `a %% b`, integer remainder;
`Case`/`When` — `django/db/models/expressions.py:1433` / `:1353`, the standard
SQL `CASE WHEN … THEN 1 ELSE 0 END`; `Exact` —
`django/db/models/lookups.py:329`, the `=` lookup. These render to SQL whose
arithmetic is the integer arithmetic the model spells out.

## 4. Soundness check (axiom_check.py / G-AX)

With no axiom to validate, `axiom_check.py` validates the one external
soundness link: that the model's predicate `xor_holds` over a 0/1 operand
assignment equals "an odd number of operands are true" — the truth value the
constructed SQL `(a OR b OR …) AND (MOD(sum, 2) == 1 | sum == 1)` evaluates to —
across all assignments up to a bound and randomized fuzz, including the
`len > 2` parity branch and the `len ≤ 2` coincidence (`count == 1` ⇔
`count % 2 == 1`). It imports only the standard library; exit 0 iff sound.

## 5. Conformance check (conformance_check.py / G-CONF)

Differential gate: the contract-stripped impl region (shadow) against the
real patched fallback branch, driven through `WhereNode.as_sql` on the
in-container SQLite connection (which lacks the native connective, so the
branch under check is the one compiled) and evaluated by executing the
produced SQL. ≥ 1e5 Requires-satisfying inputs: exhaustive 0/1 assignments
for 1..12 operands, non-binary/long boundary lists, 100000 fuzz lists.
Pinned fuzz seed: **16901**.
