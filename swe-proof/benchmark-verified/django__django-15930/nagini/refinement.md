# refinement.md — django__django-15930

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_branch` impl region plus the deep `clause_text` / `clause_params`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The patched site — `When.as_sql` (`django/db/models/expressions.py:1297`)

Gold hunk (inserted after `condition_sql, condition_params = compiler.compile(self.condition)`):
```python
+ # Filters that match everything are handled as empty strings in the
+ # WHERE clause, but in a CASE WHEN expression they must use a predicate
+ # that's always True.
+ if condition_sql == "":
+     condition_sql, condition_params = compiler.compile(Value(True))
```
The surrounding (unchanged) body builds `template % template_params` and
`sql_params` from `condition_sql`/`condition_params` and
`result_sql`/`result_params`, where `template == "WHEN %(condition)s THEN %(result)s"`.

| # | model.py impl op (`render_branch`) | patch.diff / surrounding op | tag | justification |
|---|---|---|---|---|
| 1 | param `pred: List[int]` | `condition_sql: str` (= `compiler.compile(self.condition)[0]`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| 2 | param `pred_params: List[int]` | `condition_params: list` | R | param list ↔ `List[int]` of opaque tokens (mapping.md §2). |
| 3 | param `cons: List[int]` | `result_sql: str` (= `compiler.compile(self.result)[0]`) | R | `str` ↔ `List[int]`. |
| 4 | param `cons_params: List[int]` | `result_params: list` | R | param list ↔ `List[int]`. |
| 5 | `len(pred) == 0` | `condition_sql == ""` | I | the empty-fragment test; an empty string is the empty code-point list (mapping.md §2). |
| 6 | on the empty branch, predicate slot ← `true_predicate()` and its params ← `true_params()` | `condition_sql, condition_params = compiler.compile(Value(True))` | A-reference | the substituted always-true predicate is modeled DEEPLY as the constants `true_predicate()` (non-empty) / `true_params()` (one token). There is no consumed axiom. The deep model is validated **== the real callee**: G-AX (`axiom_check.py`) runs `compiler.compile(Value(True))` and asserts it is NON-empty (`('%s', [True])`), which is the only property the proof rides on. Provenance: `Value.as_sql` returns `("%s", [val])` for non-`None` `val` (mapping.md §3). |
| 7 | on the non-empty branch, predicate slot ← `pred` and its params ← `pred_params` (verbatim) | `condition_sql`/`condition_params` left unchanged | I | a non-empty supplied fragment is used verbatim (the `if` is not entered). |
| 8 | `text = lead() + <slot> + sep() + cons` | `template % template_params` with `template == "WHEN %(condition)s THEN %(result)s"`, `template_params["condition"] = condition_sql`, `template_params["result"] = result_sql` | R | named `%`-interpolation of the fixed template ↔ sequence concatenation with the constant literals `lead()` (`"WHEN "`) and `sep()` (`" THEN "`); the trailing template text is empty (mapping.md §1,§2). |
| 9 | `params = <slot params> + cons_params` | `sql_params.extend(condition_params); sql_params.extend(result_params)` | R/I | ordered concatenation: predicate-slot params then consequent params (`sql_params` starts empty). |
| 10 | `return text, params` (a `Tuple[List[int], List[int]]`) | `return template % template_params, sql_params` | R | tuple of (`str`, param list) ↔ tuple of (`List[int]`, `List[int]`). |

The discriminating content of the change — substitute a NON-EMPTY always-true
predicate when the supplied predicate fragment is empty — lives in the empty
branch of `clause_text` (step 6) and in the postcondition
`ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons))` together with the
slot-non-blank clause `len(Result()[0]) > len(lead()) + len(sep()) + len(cons)`.
`model_prepatch.py` reproduces the pre-patch skeleton (use `pred` verbatim, no
substitution) and **fails** that postcondition for the empty supplied predicate
— exactly the spec sensing the change (G-DIFF). This is the
`test_annotate_with_full_when` FAIL_TO_PASS behaviour: `~Q(pk__in=[])` compiles
to the empty fragment, and pre-patch the rendered clause is the malformed
`WHEN  THEN ...` (the SQL syntax error the issue reports).

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
splicing a non-empty always-true predicate for an empty supplied predicate — is
modeled **deeply** (the `clause_text` empty branch + the `render_branch` empty
branch, validated as the **A-reference** step 6), not hidden behind an axiom
about the function under change. There is no consumed `@ContractOnly` axiom.

## verify(model) ⇒ resolved

`render_branch` verifies only if its rendered text equals `clause_text` — which
on the empty supplied predicate splices the non-empty `true_predicate()` (step
6) so the predicate slot is never blank (the slot-non-blank postcondition) — and
only if its params equal `clause_params`. By R (str ↔ List[int], param-list ↔
List[int], template-interpolation ↔ concatenation) the verified renderer equals
the gold-patched `When.as_sql` on the tested inputs; by G-AX the deep-model
constant `true_predicate()` is non-empty == the real `compile(Value(True))`
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the one audited A-reference — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
