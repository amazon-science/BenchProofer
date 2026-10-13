# refinement.md — django__django-10554

Maps every op in `implementation_resolveOrderColumn` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses callee
axiom · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

Throughout, note which of the two lists each op touches. The loop SCANS the
compiler's `self.select` (modeled as `q.resultCols`); the helper APPENDS TO and
the position is MEASURED OFF the query's own `self.query.select` (modeled as
`q.querySelect`). See mapping.md §"Two distinct lists".

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let mut cur : OrderSrc := src` | `src = resolved.get_source_expressions()[0]` (initial compared expr) | R | expression object ↔ `QExpr` = (identity, the value label it contributes); a term standing under names ↔ a STACK of `RefLink`s over the expression no name stands over, peeled by the same test the realiasing step makes. `cur.compared` is the term as `==` and `.output_field` see it: the outermost wrapper's identity carrying the BASE's label, since `Ref.output_field` delegates to its source |
| 2 | `let mut idx := 0` / `for col in q.resultCols` | `for idx, (sel_expr, _, col_alias) in enumerate(self.select):` | R | the COMPILER's list (`extra_select ++ query.select|default_cols ++ annotation_select`) ↔ `List SelCol`; `sql` slot unused |
| 2b | `if isRef && cur.refs?.isNone then return OrderByOutcome.aborted q` | there is no such statement: on each iteration `col_alias == src.refs` reads `.refs` off whatever `src` currently is, which raises `AttributeError` exactly when that object carries no such attribute — i.e. when it is not a named reference | R | the name belongs to the wrapper, so it is unreadable once nothing wraps the term; a raise with nothing mutated ↔ `aborted q`. It is NOT "unreadable after one realiasing": `src.source` may itself be a `Ref`, and then `.refs` is still readable and the scan realiases again (measured, `probe1`/`probe2`) |
| 3 | `let aliasMatch := isRef && cur.refs? == some col.colAlias` | `if is_ref and col_alias == src.refs:` | R | bool guard; alias `Optional[str]` ↔ `Option String`; the name compared is the one the term stands under RIGHT NOW, which changes as the term is realiased |
| 4 | `if aliasMatch then cur := cur.stripped` | `src = src.source` | R | realiasing the compared expr: drop the OUTERMOST name only, one step per matching column; mutation persists across iterations, so a term standing under n names can be realiased n times |
| 5 | `if (aliasMatch ‖ !hasAlias col.colAlias) && cur.compared.sameExpr col.expr` | `elif col_alias: continue` then `if src == sel_expr:` | I | "compare only the referenced column or an unaliased column"; `elif col_alias:` tests the alias FOR TRUTH, so the skip condition is `¬aliasMatch ∧ hasAlias colAlias` — a present-but-empty name is no alias and the column IS compared. `src == sel_expr` is `BaseExpression.__eq__`, i.e. `self.identity == other.identity`, and `identity` replaces a `fields.Field` argument by `type(value)`, so the test reads the expression's IDENTITY and not the value label it would contribute ↔ `QExpr.sameExpr` (`a.id == b.id`), NOT structural equality on `(id, label)`. See "What the third panel repair changed" |
| 6 | `return OrderByOutcome.resolved (idx+1) q` | `resolved.set_source_expressions([RawSQL('%d' % (idx+1), ())]); break` | R | 1-based ordinal IN THE SCANNED LIST; `q` unchanged — the match path touches neither query-side list |
| 7 | `match q.resultCols.getLast? with … some lastCol =>` | the `for … else:` suite; `col_alias` is left bound to the **last** iterated entry of `self.select` | R | CPython loop-variable leak ↔ `getLast?` **of the scanned list**; equal because the scan visits every entry when no `break` fires |
| 7b | `| none => return OrderByOutcome.aborted q` | the same `else:` suite when `self.select` was EMPTY: the loop never bound `col_alias`, so `if col_alias:` raises `UnboundLocalError` before anything is added | R | measured in the container; the scan visited no column, so there is no alias to consult and none can be obtained ↔ a stop with the state untouched. NOT `noMatch`, which is the `DatabaseError` the suite raises deliberately |
| 8 | `if hasAlias lastCol.colAlias then return noMatch` | `if col_alias: raise DatabaseError('ORDER BY term does not match any column in the result set.')` | R | **the preserved branch** — aliased trailing SCANNED entry ⇒ genuine no-match (raise ↔ `noMatch`) |
| 9a | `querySelect := q.querySelect ++ [cur.compared]` | `self.query.add_select_col(src)` → `self.select += col,` where `self` is the **Query** | R | **the change, first half** — the order column joins the QUERY's selected columns |
| 9b | `addedOutcome`, `name`/`anonymous` legs: `valuesSelect := q.valuesSelect ++ [lab]` | `self.query.add_select_col(src)` → `self.values_select += col.output_field.name,` | R | **the change, second half** — the same column is named in the label list, so the query-side pair stays in correspondence. The value is `Optional[str]`: `None` for an output field with no name ↔ `OutputLabel.anonymous ↦ none` |
| 9d | `addedOutcome`, `undetermined` leg: `aborted (withPartialResultCol q cur.compared)` | the same statement when `col.output_field` raises `FieldError` (an expression whose output type is not determined, e.g. `Value(1)`, or a chain of names over one, on this base commit) | R | the two appends are separate statements, so the raise lands BETWEEN them: measured in the container as `select` grown by the column and `values_select` untouched — the state the stop carries |
| 9c | `resultCols := q.resultCols` (unchanged) | — nothing in the patch reassembles `self.select`; it is built once in `setup_query` (`compiler.py:43`) | I | the scanned list is NOT refreshed when a term adds a column (measured: two extending terms leave `self.select` at length 1 while `query.select` goes 1→3) |
| 10 | `return OrderByOutcome.resolved newCols.querySelect.length newCols` | `resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])` | R | **the change** — the position is `len` of the QUERY's list, not of the scanned one |

Every op is R or I. **No A-tagged rows** — the only callee, the column-adding
helper, has its effect spelled out **completely**: ops #9a and #9b are its two
assignments, and op #10 is the position read off the extended query list.
Nothing of its observable behaviour is discarded by fiat.

### What the previous revision got wrong (and why rows #9c and #2 changed)

The earlier table tagged rows #2, #9a and #10 as if `self.select` and
`self.query.select` were ONE list: the model scanned, appended to, and measured a
single `q.select`. That is only correct on the degenerate slice where
`extra_select` and `annotation_select` are both empty — which is exactly the F2P
tests, so nothing in the battery or the shadow could see it. An audit exploited
it, and the divergence was measured against real patched Django:

```
union + extra(select={'foo':'1'}).values_list('order','foo').order_by('pk')
  self.select len 2, self.query.select len 1
  real emits ORDER BY (2) ;   one-list model said 3
union + annotate(x=Value(1)).values_list('order','x').order_by('pk')
  self.select trailing entry ALIASED ('x'), self.query.select len 1
  real RAISES DatabaseError ; one-list model said resolved 2
```

The first is a wrong POSITION (op #10 counted the wrong list); the second is a
wrong OUTCOME (op #7/#8 read the trailing alias off the wrong list). Splitting
`QueryCols` into `resultCols` (scanned, indexed, never grown) and
`querySelect`/`valuesSelect` (appended to, measured) fixes both, and adds row #9c
to record that the scanned list is deliberately left alone.

An earlier revision before that one had also dropped op #9b entirely, justifying
it with "`values_select` is a downstream label list that does not affect the
resolved position". That is false and is not restored: `values_select` is a
load-bearing input to `SQLCompiler.get_combinator_sql`, untouched by the change,
at `compiler.py:427-433` — `if not compiler.query.values_select and
self.query.values_select: … compiler.query.set_values(…)` is what pushes the
outer query's column list into each arm. Extending `self.query.select` alone
leaves every arm selecting N columns while the outer query selects N+1, so the
emitted `ORDER BY <N+1>` points past the end of each arm's list.

Because the impl region is entirely R/I (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this impl's R/I shadow against the
patched `get_order_by` combinator suite ITSELF — `conformance_check.py` slices that
suite out of the installed `compiler.py` and runs it over real expression objects
and a real `Query`, so rows 2b, 5, 7b, 8, 9b and 9d are checked against executing
code rather than against a second reading of it — over both lists, with the
scanned length and the query length fuzzed INDEPENDENTLY and all six outcome
classes required to be reached.

### What the third panel repair changed (rows 1, 5)

Row 5 previously modelled the scan's match test as structural equality on the
whole modeled expression — `cur.compared == col.expr`, i.e. identity AND value
label. A panel reviewer found the divergent input and it reproduces in the patched
container:

```python
app_label = ContentType._meta.get_field("app_label")   # CharField
username  = User._meta.get_field("username")           # CharField
A   = Col("t", app_label)     # .output_field.name == 'app_label'
SRC = Col("t", username)      # .output_field.name == 'username'
A == SRC          # -> True
Ref("a", A) == Ref("a", SRC)  # -> True
```

`django/db/models/expressions.py` at base commit
`14d026cccb144c6877294ba4cd4e03ebf0842498` settles it:
`BaseExpression.identity` builds its tuple with `if isinstance(value,
fields.Field): value = type(value)`, and `__eq__` is `other.identity ==
self.identity`. So `==` sees the field's CLASS, never the instance, and two columns
over same-typed fields of one alias are equal while contributing different labels.
Measured through the extracted suite with `select=[(A, sql, None)]` and `src=SRC`:
`('resolved', 1, (), [])` — the real scan MATCHES A, reports position 1, and leaves
the query state untouched. The old model predicted no match and the added-column
outcome.

The reviewer read this as a defect in the CARRIER — one `QExpr` cannot be both
"equal by identity" and "distinct by label" — and concluded no bridge could repair
it. That conclusion does not follow, and the repair is the reason: the two
observations are only in conflict if the SAME test consumes both, and nothing in
this region reads the label of a column the scan MET. The trailing dispatch
consults `col_alias`; the add path appends `src.output_field.name`, the label of the
term IN HAND. So the faithful model keeps both components and separates the two
uses: `QExpr.sameExpr a b := a.id == b.id` is the match test, and `label` is read
only by `addedOutcome`. `id` is correspondingly re-read as the equivalence class of
the real object under the callee's own `==`, and the G-CONF bridge is now that
QUOTIENT, asserted exact in both directions rather than asserted injective.

Nothing was narrowed to make this fit. The postcondition is byte-identical
(`result = resolveOutcome q isRef src ∧ (inCorrespondence q = true → outcomeUsable
q result = true)`), the domain is still all column states, and the model got
STRICTLY more permissive at the match test — it now matches inputs it used to send
down the add path, which is what the real code does.

Two measurements hold the leg, both in `conformance_check.py`. The pool now
deliberately CONTAINS a collapsed class (`Col("t0", app_label)`,
`Col("t0", username)`, `Col("t0", model)` — one `==` class, three labels), where the
previous revision asserted the pool PAIRWISE UNEQUAL and thereby put the whole
witnessing class out of the fuzzed domain; that assertion is what let a
200000/200000 agreement coexist with the divergence, and it is gone. The run now
FAILS unless (a) it drew a match the real code decided inside one class with
differing labels and (b) a `structural` CONTROL shadow — the same transliteration
with full-view equality substituted for `sameExpr` — disagrees with the real code
somewhere. Measured: 200000/200000 agree, mismatches 0, 949 collapsed matches, 949
structural-control disagreements. One new reject lane, `label-in-match-test`, is
the previous revision of the guard exactly; its witness is one unaliased column of
the term's identity carrying a different label (gold resolves 1 with the state
untouched, the rival falls through and resolves 2 over a grown state), built both
ways and with the forgery control run.

### What the second panel repair changed (rows 1, 2b, 3, 4)

Rows 2b/3/4 previously modelled the realiasing step as a single substitution
guarded by a boolean "already realiased" flag: one `refs`/`source` pair, and the
`AttributeError` stop taken on the first iteration after any substitution. That
predicts a stop where the real scan carries on. `Ref.source` is whatever the
named SELECT entry held, and a named entry may hold a `Ref` — `resolve_ref`
returns it unchanged — so the substituted-in term can itself carry `.refs`,
which is then read and matched and substituted again. Reproduced through the
public API against real patched Django in the instance container:

```python
qv = lambda: ReservedName.objects.extra(select={'y': '"order"+100'}).annotate(s=Count('id'))
qv().union(qv()).order_by('y')[:5].aggregate(y=F('s'), c=Count('id'))
```

`self.select = [('y', RawSQL), ('s', Count)]`, `is_ref` true, and the term is
`Ref('y', Ref('s', Count))`: the real call realiases at column 1, reads `'s'` off
what it substituted in, realiases again at column 2 and RESOLVES there — measured
`('resolved', 2, [], [])`, and the query returns `{'c': 2}`. The single-flag model
said `aborted`. The repair replaces the pair-plus-flag with a STACK of named
wrappers (`OrderSrc.links`): `refs?` is the name the term stands under right now
and is absent only when nothing wraps it, `stripped` drops one name, and
`compared` is the term as `==` sees it — the outer wrapper's own identity (a `Ref`
is never `==` its source) carrying the base's label, because `Ref.output_field`
delegates (measured: `Ref(Col)` → name `app_label`, `Ref(Ref(Value(1)))` → no
label at all, so a chain of names over an undetermined expression takes row 9d's
leg). The postcondition is unchanged: the repair is to the model of the callee,
not to what the spec claims about it. Extending `conformance_check.py`'s pool to
depth-3 chains and its scanned columns to wrappers, the previous model disagrees
with the extracted suite on 1629 of 20000 fuzzed inputs, all at depth ≥ 2, across
`resolved`, `noMatch` and the label-less stop; the repaired model agrees on
200000/200000. Two new reject lanes hold the leg: `substitute-once` (the previous
model exactly — stop after one realiasing) and `substitute-to-base` (realiase
straight to the bottom of the chain).

### What the first panel repair changed (rows 2b, 5, 7b, 9b, 9d)

Rows 1, 5, 8, 9b were previously written as if the alias were tested for PRESENCE,
as if `col.output_field.name` always yielded a string, and as if the `for/else`
suite always had a `col_alias` to read; rows 2b, 7b and 9d did not exist. All four
readings predict behaviour the callee does not have, and the harness above
measures the difference: the previous model disagrees with the extracted suite on
9327 of 20000 fuzzed inputs, spread across five of the six outcome classes
(the empty-scanned-list stop, the label-less stop, the post-substitution stop,
and both resolved legs, which the presence-vs-truth reading gets wrong on an empty
name).

## Prepatch (the real bug)

The pre-patch impl (`Solution_prepatch.lean`) replaces ops #7–#10 with an
unconditional `return OrderByOutcome.noMatch` — exactly the original
`else: raise DatabaseError(...)`, which fired for **every** unmatched term
regardless of whether the trailing scanned entry was aliased, and never added the
column. The discriminating input is an unmatched term whose scanned list ends in
an **unaliased** entry (the values_list/ORDER BY-by-`pk` scenario of the F2P test
`test_union_with_values_list_and_order`): the patched/spec outcome is
`resolved (len(querySelect)+1)` over a query column state extended in both parts,
whereas the prepatch yields `noMatch` (the `ORDER BY position N is not in select
list` crash from the issue). On that input `problem_spec_resolveOrderColumn`
forces `resolveOutcome … = resolved …` while the prepatch impl returns `noMatch`,
so `correct_resolveOrderColumn` is unprovable for the prepatch impl (G-DIFF).

The aliased-trailing case (`test_order_raises_on_non_selected_column`,
PASS_TO_PASS) is preserved by both: op #8 still yields `noMatch`, so the spec
does not over-correct. Reproduced in the container: that test's
`order_by('id')` shape has `self.select = [(Value,'ann'), (Col,'num2')]`, a
trailing ALIASED entry, and both base and patched Django raise.

## The usability conjunct

The postcondition's second conjunct — on a state whose query-side pair arrives in
correspondence, a reported position is a genuine 1-based ordinal **of the list it
counts**, and the resulting query column state is still in correspondence — is not
a restatement of the first. It is the property the real function has for a reason,
and the proof gives that reason: `scanCols_bound` shows a matched position is only
ever emitted for a scanned entry the loop actually visited, and the extend leg
grows the query list by exactly one and maintains correspondence because ops #9a
and #9b fire together. It is what an implementation performing only half of the
helper's effect violates, and — since it distinguishes the two lists — it is also
what refutes an implementation that counts the extend position off the scanned
list. Confirmed independently of the Lean model by G-CONF, which checks it against the
extracted patched suite's own result, on every fuzzed input that arrives in
correspondence, with the two lengths fuzzed independently. Its `aborted` leg is
what pins the three stops: the result columns and the label list are exactly as
they arrived and the selected columns have grown by at most one — which is the
observable difference between the stop that lands between the helper's two appends
and the two that land before either.
