# mapping.md — symbol binding & type bijection (django__django-16901)

## Modeled function
- **Lean** `implementation_xorFallback : List Bool → Bool`
- **Python** `WhereNode.as_sql(self, compiler, connection)` — the
  XOR-without-native-support fallback branch,
  `django/db/models/sql/where.py:128-141 @ base_commit` (gold patch hunk at
  lines 129-141).

When the connector is `XOR` and the backend lacks `supports_logical_xor`,
`as_sql` rewrites the n-ary XOR over `self.children` into a combined predicate:

```python
lhs = self.__class__(self.children, OR)              # a OR b OR c OR ...
rhs_sum = reduce(operator.add,
    (Case(When(c, then=1), default=0) for c in self.children))   # sum of 1-per-true
# base (buggy):                       rhs = Exact(1, rhs_sum)               # sum == 1
# patched:    if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)
#                                       rhs = Exact(1, rhs_sum)             # MOD(sum,2) == 1
return self.__class__([lhs, rhs], AND, self.negated).as_sql(compiler, connection)
```

The observable **boolean semantics** of the constructed `WhereNode` (for the
non-negated case the F2P test exercises) is: a row matches iff
`(OR of operands) AND (count-of-true-operands test)`. Pre-patch the test is
`count == 1` (true only when exactly one operand holds); post-patch, for more
than two operands, the test is `count % 2 == 1` (true when an odd number hold),
which is the meaning of n-ary XOR. For ≤2 operands `count == 1` already coincides
with parity, so the fix changes behavior only for `len > 2`.

We model each child operand by the truth value of its condition on a given row.
The combined predicate is therefore a total boolean function of the list of
operand truth values — exactly what `implementation_xorFallback` computes.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.children` — list of child predicates | `cs : List Bool` | each child reduced to the truth value of its condition on one row; list length = number of operands |
| `Case(When(c, then=1), default=0)` per child | `if c then 1 else 0` summed | one-per-true contribution; `reduce(operator.add, …)` = sum |
| `lhs = OR(children)` row truth | `lhs : Bool` (`||`-fold) | the disjunction matches iff any operand holds |
| `len(self.children)` | `cs.length` | operand count |
| `Mod(rhs_sum, 2)` / `Exact(1, …)` | `rhsSum % 2 == 1` / `rhsSum == 1` | the rhs equality test on the (possibly mod-2'd) sum |
| combined `WhereNode([lhs, rhs], AND)` row truth | `lhs && rhs` (output `Bool`) | a row matches iff both legs hold |

The negation flag (`self.negated`) is threaded through unchanged by the patch and
is outside the modeled behavior (the F2P/issue scenario is non-negated); the model
fixes the non-negated combined-predicate truth.

## Callee provenance
- `Case`/`When`/`Exact`/`Mod`/`reduce(operator.add, …)` and the recursive
  `as_sql` are all **UNCHANGED** by the patch. The patch only inserts the
  `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` step. Each of these
  callees is reproduced concretely at the boolean-semantics level (a sum, a
  parity/equality test, a disjunction, a conjunction) as **I**/deeply-modeled
  ops, NOT axiomatized. The axioms region is therefore empty and G-AX is a skip
  stub.

## Flag dependency
The branch is taken only when `connection.features.supports_logical_xor` is
False (e.g. PostgreSQL/SQLite); on MySQL the native XOR is used and this code is
not reached. The model covers the fallback branch (the only one the patch
touches).

## G-CONF fuzz seed
Pinned seed: **16901** (recorded in meta.json `verifier_pins.conf_seed`).
