# refinement.md — django__django-16901

The operation-by-operation correspondence between `model.py`'s implementation
(the `xor_fallback_matches` impl region plus the deep arithmetic models
`count_true` / `any_true` / `derived_count` / `xor_holds` in the `pure` region)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == a real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `WhereNode.as_sql` (`django/db/models/sql/where.py:114`)

Gold hunk (the fallback for backends without native XOR):
```
- #   (a OR b OR c OR ...) AND (a + b + c + ...) == 1
+ #   (a OR b OR c OR ...) AND MOD(a + b + c + ..., 2) == 1
  lhs = self.__class__(self.children, OR)
  rhs_sum = reduce(operator.add,
                   (Case(When(c, then=1), default=0) for c in self.children))
+ if len(self.children) > 2:
+     rhs_sum = Mod(rhs_sum, 2)
  rhs = Exact(1, rhs_sum)
  return self.__class__([lhs, rhs], AND, self.negated).as_sql(compiler, connection)
```

The patch builds an SQL *expression tree*; the F2P test observes the boolean
the constructed predicate evaluates to for each row's truth assignment. The
model is the **evaluation** of that constructed predicate on an assignment of
per-operand truth values. The assignment is modelled as `List[int]` whose entry
is `1` for a true operand and otherwise contributes `0`.

| # | model.py impl op (`xor_fallback_matches`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `operands: List[int]`, entry `1` ⇔ a true operand | `self.children` (the operand predicates), each evaluating to true/false per row | R | the list of per-row operand truth values ↔ `self.children`; the only observable each child contributes to the constructed arithmetic is its 1/0 truth value (mapping.md §2). |
| A2 | `contribution = 1 if c == 1 else 0` (in the loop), summed into `total`; modelled by `count_true` | `Case(When(c, then=1), default=0)` for each child, combined by `reduce(operator.add, …)` into `rhs_sum` | R + I | `Case(When(c, then=1), default=0)` evaluates to `1` when the child is true and `0` otherwise; `reduce(operator.add, …)` is their integer sum. `count_true` is exactly that sum, spelled out (a front-recursive fold). The integer arithmetic is the SQL `+` semantics, modelled deeply — not axiomatized (mapping.md §3). |
| A3 | `any_t` (the running OR), modelled by `any_true` | `lhs = self.__class__(self.children, OR)` — the disjunction of the children | R + I | `any_true(s)` is the disjunction of the operands; its `Ensures` ties it to `count_true(s) >= 1`. The `OR`-node ↔ this disjunction. |
| A4 | `if len(operands) > 2: rhs = total % 2 else: rhs = total`; modelled by `derived_count` | `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` | I | **the changed operation.** The integer remainder `% 2` is the runtime semantics of `Mod(rhs_sum, 2)`; the `len > 2` guard is identical. Modelled deeply (integer `%`), not behind an axiom — there is no SQL callee whose unchanged behaviour the proof leans on; `Mod`'s denotation IS integer modulo. |
| A5 | `return any_t and rhs == 1`; modelled by `xor_holds` | `rhs = Exact(1, rhs_sum)`; final node `self.__class__([lhs, rhs], AND, …).as_sql(...)` | R + I | `Exact(1, rhs_sum)` is the predicate `rhs_sum == 1`; the outer `AND` conjoins it with `lhs` (the OR). `xor_holds(s) = any_true(s) and derived_count(s) == 1` is exactly `(OR of operands) AND (derived count == 1)`. The `self.negated` flag and the recursive `as_sql` lowering are SQL-rendering plumbing that do not change the predicate's truth value for a given assignment (mapping.md §2.1). |

### Termination (total-correctness clause)

The contract additionally carries `Requires(MustTerminate(2))`, and the model
loop discharges it with the strictly decreasing measure
`Invariant(MustTerminate(i))`. This is not an extra behaviour beyond the gold
patch: evaluating the constructed fallback predicate on one row's finite
operand assignment is a bounded computation (`reduce` over `len(self.children)`
terms, one `Mod`, one `Exact`, one `AND`) that always completes and returns the
match decision to the compiler. Nagini verifies partial correctness by default,
so without the obligation a same-spec implementation whose loop never exits
satisfies every `Ensures` vacuously while its faithful real patch — a fallback
that hangs instead of answering — would time out the F2P/P2P xor tests and NOT
resolve (the audit's P1 witness; properties.py `weak-nonterm` pins the
rejection). The obligation closes that vacuity hole and adds no constraint the
real code does not satisfy.

The discriminating content of the change — testing the **parity** of the true
operand count rather than whether it **equals one** — lives in step A4
(`derived_count`: `count % 2` when `len > 2`). For `len <= 2` the true count is
at most two, so `count == 1` and `count % 2 == 1` coincide (the spec proves
this); for `len > 2` they diverge and only parity is correct. `model_prepatch.py`
drops the `Mod` step (`rhs = total` unconditionally), reproducing the
exactly-one fallback, and **fails** the postcondition
`Result() == xor_holds(ToSeq(operands))` — exactly the spec sensing the change
(G-DIFF). The second postcondition `Result() == (count_true(...) % 2 == 1)`
states the issue's behavioural demand (odd ⇒ match) directly and is the F2P
oracle in spec form.

## B. No consumed axioms; no A-reference deep-model-vs-callee check

There is **no `@ContractOnly` axiom** in this bundle. The operation the patch
changes is purely integer arithmetic (a sum, a modulo, an equality and a
disjunction over 1/0 operand values). Nagini expresses these directly, so the
changed operation is modelled **deeply** with native integer arithmetic rather
than axiomatized. There is consequently no unchanged opaque callee for the
proof to consume, and no library callee to validate a deep model against.

`axiom_check.py` therefore does not validate an axiom; instead it documents and
checks the single soundness link that *is* external to Nagini: that the model's
predicate `xor_holds` over a 0/1 assignment equals the truth value the
constructed SQL predicate `(OR …) AND (MOD(sum,2) == 1 | sum == 1)` evaluates
to, including the `len > 2` branch and the `len <= 2` coincidence — i.e. that
"derived count == 1" denotes "an odd number of operands are true". It exits 0.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or a combination. The one operation that genuinely
*changed* — the parity reduction `Mod(rhs_sum, 2)` — is modelled **deeply** as
the integer remainder `% 2` (step A4), not hidden behind an axiom about a
callee. There is no consumed axiom and no A-reference.

## D. verify(model) ⇒ resolved

`xor_fallback_matches` verifies only if its result equals
`xor_holds(ToSeq(operands))` (A5) — i.e. `(OR of operands) AND (derived count
== 1)` with the parity reduction for `len > 2` (A4) — equivalently equals
`count_true % 2 == 1` (the odd-count behaviour the issue demands), and
TERMINATES on every input (`Requires(MustTerminate(2))`): the fallback actually
answers, matching the real bounded predicate evaluation. By R (the
operand list ↔ `self.children` via per-operand 1/0 truth values; the SQL
builder nodes ↔ the integer arithmetic they denote) the verified predicate is
the predicate the gold patch constructs, evaluated on any row. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because there is no axiom.
