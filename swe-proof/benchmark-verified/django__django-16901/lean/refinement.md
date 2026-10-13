# refinement.md — operation correspondence (django__django-16901)

Maps every op in `implementation_xorFallback` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`WhereNode.as_sql`, XOR fallback branch) builds a combined
`WhereNode` `(OR of children) AND (test on the count of true children)`. We model
its boolean semantics directly: the disjunction, the count of true operands, the
rhs test (parity for `len > 2`, equality to one otherwise), and the conjunction.

| # | Lean impl op | patch.diff / base counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `cs : List Bool` | `self.children` (each child's row truth value) | R | list-of-children ↔ `List Bool` bijection (mapping.md); each operand reduced to the truth of its condition |
| 2 | `let mut lhs := false; for c in cs do lhs := lhs \|\| c` | `lhs = self.__class__(self.children, OR)` row truth | R/I | OR over the children modeled as the boolean `\|\|`-fold; unchanged by the patch |
| 3 | `let mut rhsSum := 0; for c in cs do if c then rhsSum := rhsSum + 1` | `rhs_sum = reduce(operator.add, (Case(When(c, then=1), default=0) for c in children))` | R/I | the per-child `1`-if-true / `0`-otherwise summed; the `reduce(add, …)` over `Case/When` is exactly the count of true operands |
| 4 | `if cs.length > 2 then rhs := (rhsSum % 2 == 1) else rhs := (rhsSum == 1)` | `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` then `rhs = Exact(1, rhs_sum)` | R | **the changed op**, modeled deeply: for more than two operands the sum is reduced mod 2 before the equality-to-one test (= parity = odd count); otherwise the sum is compared to one directly. The `Mod(…, 2)` wrap is the fix. NOT axiomatized. |
| 5 | `return lhs && rhs` | `self.__class__([lhs, rhs], AND, self.negated).as_sql(...)` row truth | R/I | the final AND of the two legs modeled as boolean `&&`; the recursive `as_sql` rendering and `self.negated` threading are unchanged and outside model scope (mapping.md) |

No **A-consumed** rows: the proof discharges the parity computation and boolean
algebra directly; no UNCHANGED callee property is assumed (axioms region empty,
G-AX is a skip stub). No **A-reference** rows: every callee (`Case`/`When`/
`Exact`/`Mod`/`reduce(add)`/recursive `as_sql`) is reproduced concretely as a
deeply-modeled boolean/arithmetic op, not abstracted behind a model needing G-AX
validation. No changed-inexpressible op.

## Discriminating clause (G-DIFF)
Row 4 is the discriminator. For `cs.length > 2`, the post-patch test is
`rhsSum % 2 == 1` (odd count); the prepatch test is always `rhsSum == 1` (exactly
one). They disagree on, e.g., `cs = [true, true, true]`: the patched impl yields
`true && (3 % 2 == 1) = true`, the spec demands `countTrue cs % 2 == 1 = true`,
but the prepatch yields `true && (3 == 1) = false`. Hence the prepatch
`correct_xorFallback` cannot close against the frozen `problem_spec_xorFallback`
— exactly the G-DIFF signal, and exactly the issue's reported bug
(`Q^Q^Q` over an all-true row counted as not-matching).
