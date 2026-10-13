# mapping.md — django__django-10554

## Symbol binding (base_commit 14d026cccb144c6877294ba4cd4e03ebf0842498)

The modeled function is the **combinator branch of one ORDER BY term** in
`SQLCompiler.get_order_by`, together with the new column-adding helper on
`Query` it calls.

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resolveOrderColumn` / `problem_spec_resolveOrderColumn` | the `if self.query.combinator:` block inside the `for expr, is_ref in order_by:` loop of `get_order_by`, for a single term | `django/db/models/sql/compiler.py:343-359` (patched: `:343-364`) |
| (impl) `for col in q.resultCols` scan with `cur`/`idx` | `for idx, (sel_expr, _, col_alias) in enumerate(self.select):` | `compiler.py:350-357` |
| (impl) `if aliasMatch then cur := cur.stripped` | `if is_ref and col_alias == src.refs: src = src.source` | `compiler.py:351-352` |
| (impl) `else if hasAlias col.colAlias → skip` | `elif col_alias: continue` — a TRUTH test, so a present-but-empty name is no alias | `compiler.py:353-354` |
| (impl) `cur == col.expr → resolved (idx+1)` | `if src == sel_expr: resolved.set_source_expressions([RawSQL('%d' % (idx+1), ())]); break` | `compiler.py:355-357` |
| (impl) trailing-column branch (`q.resultCols.getLast?`) | the `for ... else:` suite — `col_alias` is the loop variable left bound to the **last** iterated column of `self.select`; where that list is empty the name is never bound at all | `compiler.py:358-363` |
| (impl) `if hasAlias lastCol.colAlias → noMatch` | `if col_alias: raise DatabaseError('ORDER BY term does not match any column in the result set.')` | `compiler.py:359-360` (patched) |
| (impl) extend `q.querySelect`, `resolved newCols.querySelect.length` | `self.query.add_select_col(src); resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])` | `compiler.py:361-363` (patched) |
| (impl) `q.querySelect ++ [cur]` inside the helper | `Query.add_select_col`: `self.select += col,` (`self` is the **Query**) | `django/db/models/sql/query.py:1777-1779` (patched) |
| (impl) `q.valuesSelect ++ [lab]` inside the helper (`addedOutcome`) | `Query.add_select_col`: `self.values_select += col.output_field.name,` — the SECOND of the helper's two appends, and the one that can raise | `django/db/models/sql/query.py:1777-1780` (patched) |
| (impl) `| none => OrderByOutcome.aborted q` in the trailing dispatch | the `else:` suite reading `col_alias` when `self.select` was empty: `UnboundLocalError`, nothing added, nothing reported | `compiler.py:359` (patched) |
| (impl) `if isRef && cur.refs?.isNone then aborted q` at the head of the scan | `col_alias == src.refs` on an iteration where the current `src` carries no `refs` attribute at all: `AttributeError: 'Col' object has no attribute 'refs'`. `src = src.source` replaces the term by whatever the named entry held, which may itself be a `Ref` — in which case `.refs` is still readable and the scan realiases again | `compiler.py:351` |
| (impl) `aborted (withPartialResultCol q cur)` | `col.output_field` raising `FieldError` inside the helper, AFTER `self.select += col,` has landed | `query.py:1779` (patched) |
| (pure) `inCorrespondence` / `outcomeUsable` | the standing relation between `self.query.select` and `self.query.values_select` that `get_combinator_sql` relies on to push the column list into each arm | `compiler.py:427-433` |

### Two distinct lists, and which one each observable comes from

This is the correction the previous revision of this file got wrong, and it is
the reason `QueryCols` now has three fields instead of two. The scanned list and
the mutated/measured list are **different Python objects**:

* The loop **scans `self.select`**, the COMPILER's list, assembled by
  `SQLCompiler.get_select()` (`compiler.py:184-251`, called from `setup_query` at
  `compiler.py:43`) as

      extra_select  ++  (query.select | get_default_columns())  ++  annotation_select

  each entry a `(sel_expr, sql, col_alias)` triple. The matched position `idx+1`
  comes from here, and so does the `col_alias` the `for/else` suite tests — that
  is the leaked binding of the **last entry of this list**.
* `add_select_col` **appends to `self.query.select`**, the QUERY's own tuple, and
  the extend position is `len(self.query.select)`. This list is neither the
  scanned one nor a prefix of it: `extra_select` entries precede it,
  `annotation_select` entries follow it, and under `default_cols` it is EMPTY
  while the scanned list holds every model column.

The previous revision bound one `q.select` to both, which is only correct on the
degenerate slice where `extra_select` and `annotation_select` are both empty —
exactly the F2P tests. Three measurements against real patched Django in the
instance container, none of them expressible under that binding:

```
union + extra(select={'foo':'1'}).values_list('order','foo').order_by('pk')
  self.select = [(RawSQL,'foo'), (Col,None)] len 2 ; self.query.select len 1
  real emits ORDER BY (2)        -- len(query.select)+1, NOT len(self.select)+1
union + annotate(x=Value(1)).values_list('order','x').order_by('pk')
  self.select = [(Col,None), (Value,'x')] -> trailing entry ALIASED
  real RAISES DatabaseError     -- the alias test reads the SCANNED list
union.order_by(Lower('name'))   (default_cols)
  self.select len 3 ; self.query.select len 0
  real emits ORDER BY (1)       -- len(query.select)+1
```

`self.select` is also **not refreshed** when a term adds a column (it is built
once in `setup_query`), so across two extending terms in one `get_order_by` call
the scanned list stays put while the query list grows — measured: `query.select`
1→3 with `self.select` still length 1, positions `(2)` and `(3)`.

**Both** parts of the helper's effect are inside the modeled observable.
`values_select` is a load-bearing input to `SQLCompiler.get_combinator_sql`,
which the change does not touch, at `compiler.py:427-433`:

```python
if not compiler.query.values_select and self.query.values_select:
    compiler.query = compiler.query.clone()
    compiler.query.set_values((*self.query.extra_select, *self.query.values_select,
                               *self.query.annotation_select))
```

That is what propagates the outer query's column list into every combined
sub-query. Adding the ORDER BY column to `self.query.select` **without** also
naming it in `values_select` leaves each arm selecting N columns while the outer
query selects N+1, so the `ORDER BY <N+1>` that gets emitted points past the end
of every arm's column list and the database rejects it. `values_select` is
therefore *inside* the causal cone of the resolved position, and the model
carries it: `inCorrespondence` is the invariant the query-side pair maintains,
and `outcomeUsable` is the consequence the spec asserts.

## Type bijection (G-CONF / G-AX use this)

| Python | Lean | notes |
|---|---|---|
| the compiler's scanned list + the query's column state | `q : QueryCols` | three fields, because the scanned list and the mutated list are different objects |
| `self.select` — list of `(sel_expr, sql, col_alias)` triples, = `extra_select ++ (query.select \| default_cols) ++ annotation_select` | `QueryCols.resultCols : List SelCol` | the list SCANNED and INDEXED; only `sel_expr` and `col_alias` are touched, the `sql` slot is unused here. Never grown by resolving a term |
| `self.query.select` — the query's own tuple of expressions | `QueryCols.querySelect : List QExpr` | the list APPENDED TO and MEASURED. Carries no alias: `add_select_col` appends a bare column |
| `self.query.values_select` — tuple of label values | `QueryCols.valuesSelect : List (Option String)` | the labels naming `querySelect`, pushed into each arm. Optional because `col.output_field.name` is `None` for an output field that carries no name (`Random()`, a bare `RawSQL`) |
| `len(values_select) == len(query.select)` (the standing relation) | `inCorrespondence q` | one label per query-selected column |
| an expression object (compared by `==`, appended, and read via `.output_field.name`) | `SelCol.expr` / `QExpr` = `(id, label)` | TWO INDEPENDENT observations of one object, neither determining the other: `id` is the equivalence class of the object under the callee's own `==`, and `label` is what `.output_field.name` yields for it. `==` is `self.identity == other.identity` and `identity` replaces a `fields.Field` argument by `type(value)` (`django/db/models/expressions.py`, base commit `14d026cccb144c6877294ba4cd4e03ebf0842498`), so `==` is COARSER than the label: `Col("t", app_label) == Col("t", username)` is true while the labels are `app_label` and `username`. The bridge is therefore the QUOTIENT of the pool by `==`, asserted exact in both directions (`_quotient` in `conformance_check.py`: `(a == b) == (mid[a] == mid[b])` for every ordered pair), NOT an injection |
| `src == sel_expr` (the scan's match test) | `QExpr.sameExpr` = `a.id == b.id` | the comparison reads the identity ONLY. The label of a column the scan MET is never observed by this region: it is `col_alias` that the trailing dispatch consults and the TERM's own label that the add path appends. So `sameExpr` holds of two expressions contributing different labels as readily as of two contributing the same one — pinned by the `label-in-match-test` rival, and required non-vacuously by G-CONF (see below) |
| what `col.output_field.name` yields for that expression | `QExpr.label : OutputLabel` | `name s` ↔ a non-null `.name`; `anonymous` ↔ `.name is None`; `undetermined` ↔ `.output_field` itself raising `FieldError` (`Value(1)`), i.e. NO label can be produced |
| `if col_alias:` / `elif col_alias:` (truth, not presence) | `hasAlias : Option String → Bool` | `none ↦ false`, `some "" ↦ false`, `some name ↦ true` |
| `col_alias` (`Optional[str]`) | `SelCol.colAlias : Option String` | `None` ↔ `none`; a name ↔ `some name` |
| `is_ref` (bool) | `isRef : Bool` | the order term is a reference to a named SELECT column |
| `src` (the compared expression, and every `.source` under it) | `OrderSrc` = (`links`, `base`) | the term as a STACK of named wrappers over the expression no wrapper stands over: `links` are the `Ref`s peeled outermost-first by exactly the test the realiasing loop makes, `base` is the first non-`Ref`. An empty stack is a term that is no reference at all. The chain can be any length: `Ref.source` may itself be a `Ref` |
| one named wrapper: its identity, and `.refs` read off it | `RefLink` = (`id`, `refs`) | `refs` is the name that wrapper stands under; only consulted when `isRef` |
| `src` as `==` compares it, and as `.output_field` reads it | `OrderSrc.compared` | the outermost wrapper's own identity (a `Ref` is never `==` its source) carrying the BASE's value label, because `Ref.output_field` delegates to its source — measured: `Ref(Col('t','app_label'))` reports name `app_label`, `Ref(Ref(Value(1)))` reports no label at all. With no wrapper left it is the base itself |
| `src.refs` where `src` is whatever the scan currently carries | `OrderSrc.refs?` | `some name` while a wrapper remains, and NOTHING once none does — the state in which reading `.refs` raises |
| `src = src.source` (one realiasing step) | `OrderSrc.stripped` | drops the OUTERMOST wrapper only, so a term wrapped n times can be realiased n times, once per iteration whose column carries the name the term then stands under |
| `idx + 1` (a matched ordinal in `self.select`) | `idx + 1` | 1-based `RawSQL('%d')` ORDER BY position |
| `len(self.query.select)` (the extend ordinal) | `newCols.querySelect.length` | counted off the QUERY list, not the scanned one |
| raise `DatabaseError(...)` | `OrderByOutcome.noMatch` | the code's own signal that the term matches no result column |
| the call stopping with no position for a reason other than that signal — `AttributeError` on `src.refs` where the term stands under no name at all, `UnboundLocalError` where the scanned list was empty, `FieldError` from the helper's second append | `OrderByOutcome.aborted q'` | `q'` is the state as the raise left it: untouched for the first two, `querySelect` grown and `valuesSelect` behind for the third |
| resolved to a position (`set_source_expressions`) | `OrderByOutcome.resolved pos q` | `q` carries the (possibly extended) column state |
| "the emitted position is a genuine ordinal of the list it counts, readable by every arm" | `outcomeUsable q result` | ordinal of `resultCols` when the query state is untouched; the new trailing ordinal of `querySelect` when it grew, which stays in correspondence |

No precondition is assumed, and none is needed. `q.resultCols` is fuzzed from
length 0: the empty scanned list is IN the bridged domain, because the `for/else`
suite is well defined there — it reads a loop variable that was never bound and
the call stops with nothing added, which is `aborted q`. (An earlier revision put
that case out of precondition and let the two legs return `noMatch`; measured
against the real suite, `noMatch` is the wrong outcome there — it is the
`DatabaseError` the code raises deliberately, not the stop it takes.)
`q.querySelect` is fuzzed INDEPENDENTLY at length 0–5 — including the empty
`default_cols` shape and lengths above and below the scanned list — with
`valuesSelect` at its length 85% of the time and at an unrelated length otherwise,
since the equality conjunct is claimed unconditionally while the usability
conjunct is stated under `inCorrespondence`, the relation the caller maintains.
The `correct_resolveOrderColumn` theorem is therefore stated for **all** column
states.

One shape the model admits that the fuzz does NOT produce, because the real
callee cannot assemble it: a named wrapper whose identity coincides with a
scanned column's (a `Ref` is never `==` a `Col`). The carrier is total over it, so
the spec is an over-approximation there — a strictly larger domain than the
callee's, which the implementation must and does handle.

A previous revision of this file also listed a term whose wrapper stands over
another wrapper as such an over-approximation. That was wrong twice over: the
callee assembles those routinely (a named SELECT entry may itself hold a `Ref`,
which `resolve_ref` hands straight back), and the model of the day could not
represent one at all — it carried a single `refs`/`source` pair and a boolean
"already realiased" flag, so it predicted a stop where the real scan realiases
again and resolves. Measured against the extracted suite over a pool extended to
depth-3 chains, that model disagreed on 1629 of 20000 fuzzed inputs, across
`resolved`, `noMatch` and the label-less stop. The wrapper stack above is the
repair, and the pool and the depth counters in `conformance_check.py` are what
keep the leg exercised: a run that draws no multiply-wrapped term now FAILS
instead of reading as agreement.

## Callee provenance / flag deps

None consumed. The change is modeled deeply: the only "callee" is the
column-adding helper, and its ENTIRE observable effect is spelled out —
`q.querySelect ++ [cur]` **and** `q.valuesSelect ++ [cur.fieldName]`, with
`newCols.querySelect.length` as the reported position, and `q.resultCols` left
untouched. No `opaque`/`axiom` declaration is needed; `axiom_check.py` is a skip
stub.

Flag dependency: the whole branch is guarded by `self.query.combinator` being
set (UNION/INTERSECT/DIFFERENCE). The change only alters the no-match
(`for/else`) behaviour; the matching path is unchanged.

## G-CONF fuzz seed (pinned)

`seed = 10554` (used in `conformance_check.py`). The oracle is **not** a
transliteration: `conformance_check.py` slices the `for idx, (sel_expr, _,
col_alias) in enumerate(self.select):` suite and its `else:` out of the installed
`compiler.py` with `inspect.getsource`, compiles it in a copy of that module's own
globals, and runs it over real expression objects against a real `Query` whose
`add_select_col` is the real helper. The three facts a transliteration cannot
carry — the alias truth test, the helper's two appends and the raise between
them, and the loop variable's CPython scoping — are therefore exercised as code,
not as prose. Extraction asserts guard every one of those landmarks and the
helper's two lines, so a repo that does not contain the patched suite fails the
check instead of passing it.

Dimensions fuzzed: `len(self.select) ∈ [0,5]`, `len(query.select) ∈ [0,5]`
INDEPENDENTLY (with `values_select` at that length 85% of the time), expressions
drawn from a 146-element pool of real ones — `Col`s over bound model fields (named
labels, two of them sharing a label with distinct identities, and THREE of them —
`Col("t0", app_label)`, `Col("t0", username)`, `Col("t0", model)` — that the real
`==` COLLAPSES into one class while contributing three different labels),
`Random()` and
`RawSQL` (an output field with no name), `Value(1)`/`Value(2)` (no output field at
all), every `Ref(refs, source)` over them, and `Ref` CHAINS to depth three built
by wrapping pool members that are themselves wrappers (so a realiased term can
meet the very wrapper below it in a scanned column). The pool is NOT asserted
pairwise unequal — that assertion, which an earlier revision made, silently put the
whole collapsed class out of the fuzzed domain. Instead every object is assigned
the index of its `==` CLASS and the quotient is asserted EXACT in both directions
(`(a == b) == (mid[a] == mid[b])` over all 146² ordered pairs, 102 classes), so
decidable equality on the model's `id` is exactly the callee's `==` and the
collapse is IN the domain. The pool is also asserted to contain both a
same-class/different-label pair (88 of them) and a different-class/same-label pair
(4594). Scanned columns are drawn from the wrappers as well as the plain
expressions;
`col_alias` and each wrapper's name `∈ {None,"","a","b","c"}` (the empty name included, which is
where presence and truth differ); `is_ref ∈ {True,False}`, and a reference term is
always a real `Ref`, as it is in the callee, at any depth the pool holds. 2·10⁵
cases.

The shadow compares the resolved position, BOTH mutated lists AS FULL VIEWS (`id`
AND `label` per element, so a wrong column appended from inside one `==` class is
still visible), and WHICH of the
six outcome classes came out (`resolved-match`, `resolved-added`, `noMatch`, and
the three stops); every class must be reached or the run fails, so a leg that was
never exercised cannot read as agreement. The usability property is additionally
checked OF THE ORACLE — of the real code's own result — on every input arriving in
correspondence. Every run must also draw terms wrapped twice and three times, or it fails.

Two further requirements keep the identity-only match test from reading as
agreement by default. The run FAILS unless (a) the fuzz drew a match the real code
decided INSIDE one `==` class where the two expressions contribute DIFFERENT
labels, and (b) a `structural` CONTROL shadow — the same transliteration with
full-view equality substituted for `QExpr.sameExpr` — DISAGREES with the real code
somewhere. Without (a) the collapse is out of the drawn domain; without (b) the two
candidate match tests were never told apart and agreement would say nothing about
which one the callee makes.

Measured: 200000/200000 agree, mismatches 0, usability breaks 0, all six classes
reached (match 2602, added 51372, noMatch 90977, no-column-visited 33618,
refs-after-switch 12398, no-label 9033), wrapping depths
{0: 6802, 1: 70634, 2: 99660, 3: 22904}, collapsed matches 949, structural-control
disagreements 949 — i.e. on all 949 draws where one identity carried two labels,
the real code matched and the label-comparing control did not. The same harness run
against the revision of the model that carried a single `refs`/`source` pair
disagrees on 1629 of 20000 cases, all of them at
depth 2 or 3, spread over `resolved`, `noMatch` and the label-less stop.
