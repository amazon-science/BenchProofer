# refinement.md — django__django-16901

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `oddParityReduce` `do` block + the pure `trueCount`/`parityOdd` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
Every step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1) — which runs the real gold-patched XOR rewrite against an in-memory SQLite
database (no native XOR ⇒ the rewrite branch); the narrative is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The XOR-fallback rewrite — `WhereNode.as_sql` (`django/db/models/sql/where.py:128`)

Gold hunk (the behavioural core):
```
              lhs = self.__class__(self.children, OR)
              rhs_sum = reduce(
                  operator.add,
                  (Case(When(c, then=1), default=0) for c in self.children),
              )
+             if len(self.children) > 2:
+                 rhs_sum = Mod(rhs_sum, 2)
              rhs = Exact(1, rhs_sum)
              return self.__class__([lhs, rhs], AND, self.negated)...
```
(plus the added `from django.db.models.functions import Mod` import).

The observable behaviour of this rewrite is *which rows the resulting WHERE
clause selects*. We model that row-level boolean directly: `oddParityReduce`
takes the per-row operand truth values `children : List Bool` and returns whether
the rewritten predicate matches.

| # | Solution.lean impl op (`oddParityReduce`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `children : List Bool` | `self.children` (the XOR node's operands) **evaluated on one row** | R | each SQL boolean child `c` ↔ the Bool "row satisfies `c`"; `len(self.children)` ↔ `children.length` (mapping.md §2). G-CONF bridges by inserting one DB row per bit-pattern. |
| A2 | `count := (if c then 1 else 0) + count`, summed by the backward `while` loop into `trueCount children` | `rhs_sum = reduce(operator.add, (Case(When(c, then=1), default=0) for c in self.children))` | I | the `CASE WHEN c THEN 1 ELSE 0` indicators summed by `reduce(add, …)` are exactly the per-element 1/0 tally `trueCount`. Concrete arithmetic, transliterated by G-CONF. Addition is commutative ⇒ the backward fold equals the left-to-right `reduce`. |
| A3 | `rhsVal := if children.length > 2 then count % 2 else count` | `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` | I | the discriminating change: for arity > 2 the tally is reduced mod 2 (`Mod(x,2)` ↔ `Nat` `% 2`, both 0/1 since summands are 0/1); for arity ≤ 2 it is left bare. mapping.md §2. |
| A4 | `decide (rhsVal = 1)` | `rhs = Exact(1, rhs_sum)` | R | `Exact(1, X)` renders the equality `X = 1`; selects the row iff the (possibly mod-reduced) tally equals 1. |
| A5 | `decide (0 < count)` (the left conjunct) | `lhs = self.__class__(self.children, OR)` | R | an OR clause over the children selects a row iff at least one child holds, i.e. `0 < trueCount` (mapping.md §2). |
| A6 | `return (decide (0 < count)) && decide (…)` | `self.__class__([lhs, rhs], AND, self.negated)` | R + I | the outer AND of `[lhs, rhs]` ↔ Bool `&&`; `self.negated` is the unchanged outer frame (omitted — wraps both pre- and post-patch identically; the tested XOR queries are non-negated, mapping.md §2). |

The whole verified value equals the pure model `parityOdd children` — true iff an
odd number of operands hold — via lemma `reduce_eq_parity`: for arity > 2 the
conjunction collapses to the parity bit `count % 2 = 1`; for arity ≤ 2 the tally
is bounded by the operand count (≤ 2) so "positive and == 1" already coincides
with "odd". This is the discriminator the issue demands ("a ^ b ^ c is true when
an odd number of the arguments are true").

`Solution_prepatch.lean` drops A3 (the `if … > 2` mod wrap), leaving the bare
tally — the pre-patch "exactly-one" semantics (`rhs = Exact(1, rhs_sum)` with no
`Mod`). Its `prove_correct` **fails** because the verified value becomes
`(0 < count) && (count = 1)` which is NOT `parityOdd` (it diverges at every row
where three or more operands hold — exactly the F2P 5-ary witness). G-DIFF.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — inserting
`Mod(rhs_sum, 2)` for wide arity — is modeled **directly** as the `count % 2`
branch (A3), an I-tagged concrete op, not hidden behind an axiom. There are no
A-tagged callees in the impl region.

## C. No axioms, no deep-model references

`meta.json axioms = []`, `deep_model_references = []`. The SQL constructors the
branch composes (`Case`, `When`, `Mod`, `Exact`, `reduce`, `operator.add`,
`self.__class__`) are unchanged and ASSEMBLE the predicate; the model depends on
none of their contracts beyond the value-level bijection of mapping.md §2 (which
G-CONF refutes end-to-end by executing the assembled SQL). Hence `axiom_check.py`
reports `status=skip` and G-AX is vacuous; the assembled-SQL fidelity is covered
by G-CONF (real patched rewrite over SQLite) and G-RESOLVE.

## D. verify(Solution) ⇒ resolved

`oddParityReduce` verifies only if its output equals `parityOdd children` — the
exact odd-parity reduction with the wide-arity `% 2` wrap (A3) — for every input.
By R (`List Bool` ↔ per-row operand truth values, OR ↔ positivity, AND ↔ `&&`,
`Exact(1,·)` ↔ `= 1`) the verified predicate equals the row-membership semantics
of `(a OR …) AND MOD(Σ,2)==1` (arity > 2) / `(a OR …) AND Σ==1` (arity ≤ 2) — the
SQL the gold patch generates (confirmed verbatim: G-CONF prints the rendered
`MOD(…, 2)` clause). By G-CONF the R/I transliteration agrees with the real
patched rewrite on 10⁵ (query,row) inputs over arities 1..7 (0 disagreements;
fails on the unpatched bug). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point of plan §1.1 reduces to refinement
fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust point.
