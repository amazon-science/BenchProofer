# refinement.md — django__django-15382

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_exists` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`/`Exsures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The predicate-render site — `Exists.as_sql` (`django/db/models/expressions.py:1212`)

Gold hunk (the `super().as_sql(...)` call is wrapped in a `try/except`):
```
     def as_sql(self, compiler, connection, template=None, **extra_context):
         query = self.query.exists(using=connection.alias)
-        sql, params = super().as_sql(
-            compiler, connection, template=template, query=query, **extra_context,
-        )
+        try:
+            sql, params = super().as_sql(
+                compiler, connection, template=template, query=query, **extra_context,
+            )
+        except EmptyResultSet:
+            if self.negated:
+                return '', ()
+            raise
         if self.negated:
             sql = 'NOT {}'.format(sql)
         return sql, params
```

| # | model.py impl op (`render_exists`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `satisfiable: int`, `negated: int` | the inner-query satisfiability (does `super().as_sql(...)` raise `EmptyResultSet`?) and `self.negated` | R | satisfiability ↔ `satisfiable ∈ {0,1}` (0 ⇔ raises, 1 ⇔ returns SQL); `self.negated` ↔ `negated ∈ {0,1}` (mapping.md §2). The line `query = self.query.exists(using=connection.alias)` is the unchanged set-up of the inner query; its only observable for the pinned behaviour is whether the subsequent render raises, captured by `satisfiable`. |
| A2 | `sql = render_inner(satisfiable)` inside `try:` | `sql, params = super().as_sql(compiler, connection, template=template, query=query, **extra_context)` inside the new `try:` | A-consumed + R | `render_inner` is the axiom standing in for the UNCHANGED `Subquery.as_sql` super-call (mapping.md §3.1): satisfiable ⇒ returns the fragment whose content is `inner_fragment(satisfiable)` (its `@Pure` companion), unsatisfiable ⇒ raises `EmptyResultSet`. The proof CONSUMES its `Ensures`/`Exsures`, and the satisfiable postcondition pins `ToSeq(Result())` to `inner_fragment(...)` so the returned fragment is the renderer's actual output (directive 8). The `(sql, params)` tuple ↔ the `List[int]` fragment (R: only `sql` is observed; mapping.md §2). |
| A3 | `except EmptyResultSet as exc:` | `except EmptyResultSet:` | I | the new exception handler around the super-call. `EmptyResultSet` (model) ↔ `EmptyResultSet` (Django) — a user-defined stand-in (builtin/library exception in `Exsures` crashes the translator; mapping.md §2). The named `exc` is the Nagini-supported form of the bare re-raise (step A5). |
| A4 | `if negated == 1: return []` | `if self.negated: return '', ()` | R + I | the FIX. On the unsatisfiable+negated path RETURN NORMALLY the EMPTY fragment (rather than propagate the signal); an empty fragment contributes no restriction, so the surrounding WHERE compiler treats it as "matches everything" (always-true). Gold returns the empty fragment `''`; `[]` (model, `len == 0`) ↔ `''` (real). The SPEC pins both the normal return AND `len(Result()) == 0` on this case (`Ensures(Implies(satisfiable == 0 and negated == 1, len(Result()) == 0))`): the F2P observes result-set equality, so the fragment must contribute NO restriction — a non-empty fragment here (e.g. `'0 = 1'` always-false, or junk `'XYZ'` invalid SQL) would change the observed rows and NOT resolve, so the empty fragment is the discriminating, grounded behaviour `patch.diff == gold` produces. The dropped `params` ↔ `()` (R: params unobserved; mapping.md §2). `if negated == 1` ↔ `if self.negated`. |
| A5 | `raise exc` (the non-negated unsatisfiable path) | `raise` (re-raise) | I | re-propagate the matches-nothing signal: a non-negated existence test over an empty selection can never hold. `raise exc` is the explicit re-raise (Nagini bans bare `raise`); observationally identical. |
| A6 | `if negated == 1: sql = [78,79,84,32] + sql` | `if self.negated: sql = 'NOT {}'.format(sql)` | R + I | the UNCHANGED negation prefix on the satisfiable path. `[78,79,84,32]` is `'NOT '` as code points; list prepend ↔ str prefixing (mapping.md §2). |
| A7 | `return sql` | `return sql, params` | R | return the (optionally prefixed) fragment; `params` dropped (unobserved, mapping.md §2). |

The discriminating content of the change — when the inner selection is
unsatisfiable AND the predicate is negated, the renderer must RETURN normally
with an empty (always-true) fragment instead of letting `EmptyResultSet`
propagate — lives in the new `try/except` + `if self.negated: return '', ()`
(real) ⇔ the `except EmptyResultSet` handler that returns `[]` when `negated == 1`
(model, step A4). The pre-patch code had no handler; `model_prepatch.py`
reproduces that (calls `render_inner` unguarded) and **fails** verification on
the exceptional postcondition

  `Exsures(EmptyResultSet, satisfiable == 0 and negated == 0)`

because on `satisfiable == 0 and negated == 1` it lets `EmptyResultSet` escape,
yet the spec's `Exsures` permits the signal ONLY when `negated == 0`. That is
exactly the spec sensing the change (G-DIFF), and exactly the F2P observation:
`~Exists(Manager.objects.none()) & Q(pk=manager.pk)` must return the manager
(the `~Exists(empty)` is always true, so the WHERE reduces to `pk=manager.pk`),
not the empty queryset the pre-patch produced when the propagated signal erased
the WHERE block.

## B. The consumed axiom + its @Pure content companion; no A-reference, no kind-3

The `@ContractOnly` axiom `render_inner` (**A-consumed**) covers the UNCHANGED
super-class renderer `Subquery.as_sql` the new code invokes (step A2); the proof
consumes its normal `Ensures` (satisfiable ⇒ returns the fragment whose content
is `inner_fragment(satisfiable)`) and its `Exsures` (unsatisfiable ⇒ raises). It
is the weakest contract sufficient for the case analysis (mapping.md §3.1) and is
NOT the function under change.

`inner_fragment(satisfiable) -> PSeq[int]` is a `@Pure @ContractOnly` companion
(**A-consumed**) that NAMES the content of the satisfiable inner fragment as a
pure function of the input. It is the same unchanged callee's output viewed as a
value; its only properties are the weakest the proof needs — non-empty, and not
itself beginning with the negation marker. Its purpose is directive-8 grounding:
the satisfiable postcondition pins `ToSeq(Result())` to `inner_fragment(...)`
(and, when negated, `not_prefix() + inner_fragment(...)`), so a verifying impl
MUST return a fragment whose content EQUALS the shared renderer's actual output —
it cannot fabricate a *different* fragment (the `atk_3_echo` cheat, which returned
`'X'`/`'NOT X'`, FAILS this clause). `inner_fragment` is NOT an answer-key oracle:
its value is opaque (no hardcoded table). Echo-resistance comes from
**witness-uniqueness**, NOT from "`render_inner` is the only way to materialize
the sequence": Nagini DOES let an impl read `inner_fragment(...)` element-wise into
a fresh `List[int]` (an "echo-reconstruct"), so the materialization step alone is
not the barrier. The barrier is that `inner_fragment(satisfiable)` has exactly ONE
real-world witness — the value the unchanged `Subquery.as_sql` actually returns on
that satisfiable inner selection (mapping.md §3.1) — so ANY `List[int]` whose
`ToSeq` equals it, however it was assembled, *is* the renderer's real SQL content
under the refinement. The result is therefore *produced by* (equal to) the modeled
renderer's output, never an arbitrary fabricated constant; an echo-reconstruct is
behaviourally indistinguishable from calling `render_inner` and so refines to the
same resolving SQL.

There is no deep model and hence no A-reference. The postcondition clauses are all
expressible structural predicates over the actual result carrier
(`ToSeq(Result()) == inner_fragment(...)`, the `NOT` prefix relation,
`len(Result()) == 0` on the negated-unsatisfiable case, `Acc(list_pred(Result()))`)
plus the return-vs-raise discriminator (`not (sat==0 and neg==0)` / the `Exsures`).
The negated-unsatisfiable case is pinned to a normal return AND `len(Result())==0`
(the empty fragment): the F2P test `test_negated_empty_exists` observes result-set
equality, and an empty fragment is exactly what makes `~Exists(empty)` contribute
no restriction (so the surrounding WHERE reduces to `pk=manager.pk` and yields
`[manager]`). A non-empty fragment on this case — gold returns `''`, but a wrong
impl could return an always-false `'0 = 1'` or junk `'XYZ'` — would impose a
spurious restriction (or invalid SQL) and change the observed rows, so it does NOT
resolve; pinning `len(Result())==0` (a grounded structural predicate on the actual
result carrier, NOT an oracle) is the minimal sound clause that closes that hole.
`patch.diff == gold` returns `''`, so this pin is exactly faithful to the shipped
patch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed* —
catching the matches-nothing signal on the negated path and returning normally
instead of propagating it — is modeled **directly** as the `try/except` +
`if negated == 1: return []` control flow in `render_exists` (steps A3–A5), not
hidden behind an axiom about the function under change. The function under change
(`Exists.as_sql`) is the modeled function itself; the axioms (`render_inner` and
its `@Pure` content companion `inner_fragment`) describe only the unchanged callee
it invokes.

## D. verify(model) ⇒ resolved

`render_exists` verifies only if it (i) RETURNS NORMALLY the EMPTY fragment when
`satisfiable == 0 and negated == 1` (the `not (satisfiable==0 and negated==0)`
reachability + the `Exsures` excluding the signal there + `len(Result())==0`) —
the discriminating return-vs-raise-AND-empty-fragment behaviour of the fix, so
gold's `''` verifies while an always-false `'0 = 1'` or junk `'XYZ'` (which would
not resolve the F2P) FAILS the `len==0` clause; (ii) raises
`EmptyResultSet` ONLY when `satisfiable == 0 and negated == 0` (the `Exsures`);
(iii) on the satisfiable cases returns EXACTLY the inner fragment the shared
renderer produced (`ToSeq(Result()) == inner_fragment(satisfiable)`), NOT-prefixed
iff negated (`== not_prefix() + inner_fragment(satisfiable)`) — so it cannot
fabricate a different fragment. By R (`str`/`bool`/satisfiability ↔
`List[int]`/`int`; `'NOT '` ↔ `[78,79,84,32]`; `''` ↔ `[]`; inner-fragment
content ↔ `inner_fragment`; `EmptyResultSet` ↔ the stand-in) the verified renderer
equals the post-patch `Exists.as_sql` on the tested inputs; by G-AX (A-consumed)
the real `Subquery.as_sql` meets the `render_inner`/`inner_fragment` axiom and the
real post-patch `Exists.as_sql` matches the model case table (incl. sat=0,neg=1
returning normally with the EMPTY fragment). Therefore a model satisfying this
spec, refined by the map
above, is the gold patch up to type refinement and the audited callee — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
