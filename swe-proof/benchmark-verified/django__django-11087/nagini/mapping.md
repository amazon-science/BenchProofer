# mapping.md — django__django-11087

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8180ffba21bf10f4be905cb0d4890dc2bcff2788`, states the type
abstraction, and gives the provenance of the behavioural facts the deep models
rest on (checked by axiom_check.py / G-AX).

Repo file under change: `django/db/models/deletion.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rows_exposed_to_observers(pre, post)` | the new helper `Collector._has_signal_listeners(self, model)` (added by the patch; the OR of `signals.pre_delete.has_listeners(model)` and `signals.post_delete.has_listeners(model)`) | modeled changed function #1 — the exposure predicate |
| `exposed_to_observers(pre, post)` *(pure spec)* | the body of `_has_signal_listeners`: `pre_delete.has_listeners(model) or post_delete.has_listeners(model)` | pure spec: the disjunction the helper computes |
| `select_cascade_fields(all_fields, already_selected, referenced, pk, whole_row_required, pre, post)` | the changed branch of `Collector.collect`, `django/db/models/deletion.py:223-224` pre-patch → the new `else:` block post-patch | modeled changed function #2 — which columns the cascade SELECT fetches for a related set |
| `pre` / `post` (bool params) | `signals.pre_delete.has_listeners(related_model)` / `signals.post_delete.has_listeners(related_model)` results | abstract per-model observation flags |
| `whole_row_required` (bool param) | `sub_objs.query.select_related` truthiness | whether the pending related-set query already asks for a whole row plus further relations, so no narrowing of it is attempted |
| `pk` (`int` param) | `related_model._meta.pk.attname` — the related model's row-identity column | the identity column the compiler always keeps (`deferred_to_data`'s `must_include`, `sql/query.py:660`) |
| `all_fields` (`List[int]`) | the full concrete-column set of `related_model` (`[f.attname for f in related_model._meta.concrete_fields]`) | full column set |
| `already_selected` (`List[int]`) | the column set the PENDING related-set query — `self.related_objects(related, batch)`, i.e. `related_model._base_manager.using(...).filter(...)`, possibly narrowed before the branch sees it — compiles on its own when no further request is made to it | the pending query's own column set |
| `referenced` (`List[int]`) | `referenced_fields = set(chain.from_iterable((rf.attname for rf in rel.field.foreign_related_fields) for rel in get_candidate_relations_to_delete(related_model._meta)))`, MINUS the pending query's own deferral set | the consulted columns that a narrowing request applied to the pending query can still reach |
| `Result()` of `select_cascade_fields` (`List[int]`) | the column set the cascade SELECT loads | the observable SELECT column set |

The pre-patch repo symbols the change rewrites (for the refinement audit, not
referenced from the consumer spec view): the inline three-term guard in
`can_fast_delete` (`deletion.py:138-140`, the `pre_delete or post_delete or
m2m_changed` disjunction the helper factors out — dropping the `m2m_changed`
term for the deletion-graph path) and the `elif sub_objs:` branch of `collect`
(`deletion.py:223-224`, which passed `sub_objs` on untouched, so the pending
query's own column set was what was fetched).

### 1.1 Why the pending query need not be unrestricted

`already_selected` is a real degree of freedom, not a decoration: the branch does
not construct its related-set query, it receives one. `Collector.related_objects`
takes it from `related_model._base_manager`, and

* `Meta.base_manager_name` (documented public API) can point that at a manager
  whose `get_queryset()` already called `.defer(...)` / `.only(...)`, so the
  DEFAULT `Collector` reaches this state with no subclassing at all;
* `related_objects` is itself overridable — `django.contrib.admin.utils.NestedObjects`
  overrides it in-tree, and the gold patch's own comment observes that a
  `select_related` on the pending query "should only happen in the rare cases
  where `.related_objects` is overridden anyway".

Both routes are exercised for real by conformance_check.py (§G-CONF below).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `signals.pre_delete.has_listeners(model)` / `post_delete.has_listeners(model)` (a `bool`) | `pre` / `post` (`bool`) | identity on booleans; True iff a receiver of that signal is connected for `model` |
| `sub_objs.query.select_related` (falsy `False`/`{}` or a truthy dict) | `whole_row_required` (`bool`) | truthiness; the guard only consults its boolean value |
| a column / model field (identified by its `attname`, a `str`) | an `int` token | each distinct column gets a distinct integer id; equality of tokens ↔ equality of attnames (Nagini bans `str` indexing) |
| a column **set** (`set` of `attname`s, or the loaded-column set of a queryset) | `List[int]` of tokens; specification over `PSeq[int]` via `ToSeq` | set membership ↔ sequence membership; the model preserves the abstract set the SELECT fetches (order is not observable in the SQL column list the test asserts on, so a list carrier with set-equal contents is faithful) |
| the pending query's compiled column set — `deferred_to_data` over its own `Query.deferred_loading` pair | `already_selected` (`List[int]`) | the columns that query fetches when no further request is made to it; equals `all_fields` exactly when it carries no restriction |
| the pending query's own DEFERRAL set (`existing` when `Query.deferred_loading == (existing, True)`; empty when the pending restriction is an immediate-loading set) | subtracted from the consulted set to give `referenced` | `add_immediate_loading` stores `field_names.difference(existing)` when the existing restriction is a deferral and REPLACES it otherwise (`sql/query.py:1959-1981`), so a column the pending query defers is not brought back by naming it, while an immediate-loading set is overridden wholesale |
| `sub_objs.only(*cols)` for a **non-empty** reachable `cols` | the result list equals `referenced`, or `referenced + [pk]` when `pk not in referenced` | the compiler's `deferred_to_data` seeds `must_include` with `orig_opts.pk` (`sql/query.py:660`), so the loaded set is `cols ∪ {pk}` — the pk is retained even when it is not one of the referenced FK targets |
| `sub_objs.only()` whose resulting immediate-loading set is **empty** (nothing consulted was reachable) | the result list equals `all_fields` | an empty `field_names` is not a narrowing but a reset: `deferred_to_data` returns at `if not field_names` (`sql/query.py:656`), so NO restriction is applied and every concrete column is fetched — including any the pending query had been deferring |
| `sub_objs` left unchanged (no request made) | the result list equals `already_selected` | with no `.only`, the pending query's `deferred_loading` stands, so what it already fetches is what is fetched — which need not be every column |

`str` indexing/iteration is banned in Nagini, so columns are `int` tokens and a
column set is a `List[int]`; the specification is phrased over `PSeq[int]` via
`ToSeq`. The `set` → ordered `List[int]` move is sound because the tested
observable is the *set* of columns in the SELECT (the F2P test asserts the
presence/absence of `large_field`, never a column order).

## 3. Behavioural facts the deep models rest on (checked by G-AX / axiom_check.py)

There is **no `@ContractOnly` axiom**: both decisions are pure boolean / set
logic spelled out in full, so nothing is consumed as an opaque callee contract.
The facts the deep models rest on are validated against the REAL runtime
semantics (A-reference):

### 3.1 `exposed_to_observers` ↔ the real `_has_signal_listeners` (A-reference)
**Callees:** `django.db.models.signals.pre_delete.has_listeners` /
`post_delete.has_listeners` (`django/dispatch/dispatcher.py:149`,
`Signal.has_listeners`). The new helper is
```python
def _has_signal_listeners(self, model):
    return (signals.pre_delete.has_listeners(model) or
            signals.post_delete.has_listeners(model))
```
The model encodes this as `exposed_to_observers(pre, post) == pre or post`.
The single behavioural fact: `has_listeners(model)` is True iff a receiver of
that signal is connected for `model`, and the helper is the **two-term**
disjunction over `pre_delete`/`post_delete` — it deliberately drops the
`m2m_changed` term that the pre-patch `can_fast_delete` guard carried, because
the rows reached along a single-valued relation are never handed to an
`m2m_changed` receiver. axiom_check.py drives the real `pre_delete` /
`post_delete` / `m2m_changed` Signal objects through connect/disconnect cycles
and asserts the disjunction is True iff a `pre_delete` or `post_delete` receiver
is connected (and is unaffected by an `m2m_changed` receiver).

### 3.2 `select_cascade_fields` ↔ the real column decision (A-reference)
**Callees:** `QuerySet.only(*fields)` (`django/db/models/query.py:1109`) →
`Query.add_immediate_loading` (`sql/query.py:1959`), the compiler's
`Query.deferred_to_data` (`sql/query.py:645`), and the referenced-field
computation
`set(chain.from_iterable((rf.attname for rf in rel.field.foreign_related_fields)
for rel in get_candidate_relations_to_delete(related_model._meta)))`. The
behavioural facts, all of them observable in the emitted SQL:

* **the row identity is always retained.** `deferred_to_data` seeds
  `must_include` with `orig_opts.pk` (`sql/query.py:660`), so a restricted SELECT
  fetches the pk even when it is not one of the referenced FK targets;
* **an empty restriction is a reset, not a narrowing.** `deferred_to_data`
  returns at `if not field_names` (`sql/query.py:656`), so `.only()` whose
  resulting immediate-loading set is empty applies NO restriction and every
  concrete column is fetched — not none, and not the pending query's narrower
  set;
* **a new immediate-loading set respects an existing deferral.**
  `add_immediate_loading` stores `field_names.difference(existing)` when the
  pending state is a deferral (`sql/query.py:1978`), and replaces it outright
  when the pending state is itself an immediate-loading set. So the consulted
  columns a narrowing request can still REACH are the consulted set minus the
  pending deferral set — which is why `referenced` is bound to that difference in
  §1, and why a request naming only already-deferred columns degenerates to the
  reset above;
* **deferring every column also restricts nothing.** The defer branch of
  `deferred_to_data` builds `workset` from the local fields NOT deferred and
  never enters the model when that is empty, and "an empty set means include all
  fields" (`sql/query.py:700-703`);
* **with no request at all, the pending query's own set stands.** `deferred_loading`
  is untouched, so what the pending query compiles is what is fetched — which
  need not be every column (§1.1).

axiom_check.py reconstructs the patched `collect` branch verbatim over a mirror
of `Query.deferred_loading` + `deferred_to_data` faithful to those facts and
asserts the model's cell postconditions, over the F2P column configuration
(`{id, unique_field, large_field}` with `{id, unique_field}` referenced),
boundary cases (pk outside the consulted set; an empty consulted set; a pending
deferral of a consulted column, of a non-consulted column, of every consulted
column; a pending immediate-loading set; and each of those with no request
made), and 20000 randomized configurations spanning every pending-query state.
It also asserts the pre-patch branch (pass `sub_objs` on untouched) violates the
narrowing clause exactly when the reachable-plus-identity set differs from what
the pending query fetches (the F2P over-fetch bug).

**The mirror is itself cross-validated against the real query layer**, not
merely internally consistent: a scratch harness drove all 528 (pending state ×
requested set) pairs on a real 4-column model through both the real compiler and
the mirror, comparing the pending column set and the post-request column set —
0 mismatches. That check is what caught the last fact above; the mirror's first
draft had `defer(everything)` fetching only the pk, where the real layer fetches
all four columns.

## G-CONF (differential conformance: MODEL vs the REAL patched repo function)

`conformance_check.py` diffs the contract-stripped `# impl-start`/`# impl-end`
regions of `model.py` (the SHADOW, copied verbatim — checked AST-identical to
the impl regions modulo the contract calls) against the REAL patched repo
functions, in-container with the gold patch applied.

**Pinned fuzz seed: `110870`** (module constant `SEED`).
Input count: **100000** checked inputs (exhaustive carrier enumeration first,
then seeded fuzz over the same space to reach the count).

Oracles, both CALLED (never transliterated):

* `Collector._has_signal_listeners` (patch hunk 2) — called on a real
  `Collector` with real receivers connected to the real
  `django.db.models.signals` registry. Models `rows_exposed_to_observers`.
* `Collector.collect`, the related-set branch (patch hunk 3) — driven at two
  tiers: **(O2a)** end-to-end with zero bridge (real models, real sqlite schema,
  `collect()` called for real, column set read out of the REAL captured SQL via
  `CaptureQueriesContext`), and **(O2b)** the patched branch's own data flow over
  the real components it composes (real `_has_signal_listeners`, real
  `sub_objs.query.select_related`, real `QuerySet.only`, real SQL compiler), so
  the abstract carrier domain can be swept exhaustively. O2b is cross-checked
  against O2a on every shape O2a covers; a disagreement between the two tiers
  sets `bridge_fault` and aborts, so a model finding is never reported on top of
  a broken oracle.

**Pending-query axis.** Every oracle model is crossed with a family of REAL
pending related-set querysets — unrestricted, `.defer(subset)`, `.only(subset)`
over every column subset, and the eager-fetch observation — so
`already_selected` ranges over strict parts of `all_fields` rather than being
pinned to it, and the consulted set is handed to the real `.only()` UNFILTERED
(it is the query layer, not the harness, that decides what a pending narrowing
leaves reachable). On the O2a tier the same states are installed by overriding
`related_objects`, the reachability §1.1 documents. The consulted set the model
receives is derived by the §2 bridge as `raw_consulted - pending_deferrals`.

Type bridge (§2 inverted): token `i` <-> the `i`-th real concrete-field attname
of the oracle model, over EVERY table of the model (so an MTI join's parent
columns land in the same universe as `all_fields`); a model `List[int]` lowers to
a `tuple` of attnames for the real `.only(...)`, and a real loaded column set
lifts back to tokens. Compared as **sets**, per §2 (column order is not
test-observable).

### Recorded verdict: **G-CONF = pass** — 0 disagreements / 100000 inputs

Same pinned seed (`110870`) and same input count (100000: 30592 exhaustive
carrier enumerations + 33384 fuzz draws). All three impl cells exercised —
narrowed 13089, empty-request reset 2504, no-request 49679 — with all four ways
of releasing the no-request guard hit (`whole_row_required` 2627, `pre` 16296,
`post` 16461, `pre+post` 16290), and the pending query carrying a restriction of
its own on 48645 of the inputs.

#### What the earlier artifacts got wrong (history, for the audit trail)

Two successive revisions of this spec were refuted here, both because the model
was a function of too few of the real inputs:

1. **`.only(cols) ⇒ loaded == cols`** — refuted with 3379 disagreements /
   100000 in two classes: the row identity is retained even when it is not a
   referenced FK target (witness: the `TOFLD` graph, a related model reached
   only by a `to_field=` reverse FK, real SELECT `{id, unique_field}` vs the
   model's `{unique_field}`), and an empty `.only()` restricts nothing rather
   than everything (witness: the `GENREL` graph, real SELECT all three columns
   vs the model's `{}`). Fixed by splitting the decision into cells and taking
   `pk` as an explicit parameter.
2. **the pending query assumed unrestricted** — the revision that fixed (1)
   still had no `already_selected` input, so it predicted `all_fields` whenever
   no request was made, and predicted a narrowing reaching consulted columns the
   pending query had already deferred. Refuted on two witnesses:
   `defer('unique_field').only('id','unique_field')` loads `{id}`, not
   `{id, unique_field}` (the `difference(existing)` subtraction); and a base
   manager deferring `large_field` with a `pre_delete` receiver connected loads
   `{id, origin_id, unique_field}`, not all four columns (no request made, so the
   pending query's own set stands). Fixed by taking `already_selected` as an
   explicit parameter, binding `referenced` to the reachable consulted set, and
   stating the no-request cell as `ToSeq(Result()) == ToSeq(already_selected)`.

The F2P configuration is the special case where the pending query is
unrestricted AND the pk is a consulted FK target, so both wrong models happened
to hold there — which is why G-RESOLVE and the F2P test never noticed either.
The spec now states the real column set on the whole domain, not just on the
tested shape. G-AX's mirror was corrected in step (§3.2) so that lane no longer
encodes the false facts either.
