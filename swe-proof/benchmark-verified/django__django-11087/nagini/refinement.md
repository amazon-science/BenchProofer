# refinement.md — django__django-11087

The operation-by-operation correspondence between `model.py`'s implementation
(`rows_exposed_to_observers` and `select_cascade_fields`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no consumed `@ContractOnly`
axioms** — both changed operations are modelled DEEPLY. The behavioural facts
the deep models rest on are A-references validated by G-AX (mapping.md §3).

## A. The new exposure helper — `_has_signal_listeners` (gold hunk 2)

Gold hunk:
```
+    def _has_signal_listeners(self, model):
+        return (
+            signals.pre_delete.has_listeners(model) or
+            signals.post_delete.has_listeners(model)
+        )
```
and `can_fast_delete` is rewritten to call it (dropping `m2m_changed` from the
deletion-graph path):
```
-        if (signals.pre_delete.has_listeners(model) or
-                signals.post_delete.has_listeners(model) or
-                signals.m2m_changed.has_listeners(model)):
+        if self._has_signal_listeners(model):
```

| # | model.py impl op (`rows_exposed_to_observers`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `pre: bool` | `signals.pre_delete.has_listeners(model)` | R | `bool` ↔ `bool`; True iff a `pre_delete` receiver is connected for `model` (mapping.md §2, §3.1). |
| A2 | param `post: bool` | `signals.post_delete.has_listeners(model)` | R | `bool` ↔ `bool`; True iff a `post_delete` receiver is connected (mapping.md §2, §3.1). |
| A3 | `return pre or post` | `return (pre_delete.has_listeners(model) or post_delete.has_listeners(model))` | I + A-reference | the disjunction is the identical boolean operation; that `has_listeners(model)` reports a connected receiver, and that the helper is exactly the **two-term** OR (no `m2m_changed`), are the facts G-AX validates against the real Signal objects (mapping.md §3.1). |

## B. The reduced-column cascade SELECT — `collect` (gold hunk 3)

Gold hunk (the `elif sub_objs:` branch becomes an `else:` block):
```
-                    elif sub_objs:
-                        field.remote_field.on_delete(self, field, sub_objs, self.using)
+                    else:
+                        related_model = related.related_model
+                        ...
+                        if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):
+                            referenced_fields = set(chain.from_iterable(
+                                (rf.attname for rf in rel.field.foreign_related_fields)
+                                for rel in get_candidate_relations_to_delete(related_model._meta)
+                            ))
+                            sub_objs = sub_objs.only(*tuple(referenced_fields))
+                        if sub_objs:
+                            field.remote_field.on_delete(self, field, sub_objs, self.using)
```

| # | model.py impl op (`select_cascade_fields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `all_fields: List[int]`, `pk: int` | the related model's full concrete-column set and `related_model._meta.pk.attname` | R | column `attname` (`str`) ↔ `int` token; a column **set** ↔ `List[int]` with set-equal contents (mapping.md §2). The precondition `pk in all_fields` mirrors that the row-identity column is one of the model's columns. |
| B1a | param `already_selected: List[int]` | the column set the PENDING related-set query — `self.related_objects(related, batch)` — compiles on its own | R | the branch does not build its query, it receives one; `related_objects` takes it from `related_model._base_manager`, which a documented `Meta.base_manager_name` (or an override, as `admin.utils.NestedObjects` does in-tree) may already have narrowed. So the pending column set is an independent input, not `all_fields`. The precondition `already_selected[k] in all_fields` mirrors that it is a sub-collection of the model's columns (mapping.md §1.1, §2). |
| B1b | param `referenced: List[int]` | `referenced_fields` (the `attname`s of the FK targets over the candidate relations) MINUS the pending query's own deferral set | R + A-reference | `add_immediate_loading` stores `field_names.difference(existing)` when the pending restriction is a deferral (`sql/query.py:1978`), so a consulted column the pending query already defers is NOT brought back by naming it. `referenced` is therefore bound to the consulted columns a narrowing request can still REACH. The precondition `referenced[k] in all_fields` mirrors that it is a sub-collection of the model's columns. |
| B2 | `whole_row_required: bool` | `sub_objs.query.select_related` truthiness | R | truthiness ↔ `bool` (mapping.md §2). |
| B3 | `pre`, `post` → `rows_exposed_to_observers(pre, post)` (the call into modeled fn A) | `self._has_signal_listeners(related_model)` | I | the same helper, **under specification** (not an axiom): `select_cascade_fields` calls the verified `rows_exposed_to_observers`, exactly as `collect` calls `_has_signal_listeners`. (In the postcondition the equivalent `@Pure exposed_to_observers` is used, since a non-pure callee inside an `Ensures` is illegal in Nagini; `rows_exposed_to_observers == exposed_to_observers` by A's spec.) |
| B4 | `leave_alone = whole_row_required or exposed`, i.e. the negation of the request guard | `if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):` | I | the identical guard expression, taken positively: the guard's FALSE case is exactly "no request is made". |
| B5 | the narrowing branch, guarded on `len(referenced) > 0`: copy the reachable consulted tokens, then append `pk` if it was not among them | `sub_objs = sub_objs.only(*tuple(referenced_fields))` where at least one consulted field is still reachable | R + A-reference | the resulting immediate-loading set is non-empty, and the compiler's `deferred_to_data` seeds `must_include` with `orig_opts.pk` (`sql/query.py:660`), so the SELECT fetches `reachable ∪ {pk}`; the model result equals `referenced` when `pk` is one of them and `referenced + [pk]` otherwise. G-AX validates that loaded-column rule against a mirror of the real `deferred_loading`/`deferred_to_data` semantics (itself cross-validated against the real compiler on all 528 pending×request pairs), and G-CONF against the real emitted SQL (mapping.md §2, §3.2). |
| B5e | the same guard's FALSE case for an empty `referenced`: fall into the keep-everything branch, `result := all_fields` | `sub_objs.only(...)` whose resulting immediate-loading set is EMPTY — either no consulted field exists, or every consulted field was already deferred by the pending query | R + A-reference | `add_immediate_loading` stores an empty `field_names` and `deferred_to_data` returns at `if not field_names` (`sql/query.py:656`), so NO restriction is applied and every concrete column is fetched — including any the pending query had been deferring. Naming nothing is a RESET, not a narrowing to nothing. The model reaches the same column set by taking the keep-everything branch when nothing consulted is reachable — the observable column set is what is refined, not the branch taken to reach it. |
| B6 | `result := already_selected` (the `leave_alone` branch: no request made) | `sub_objs` left unchanged → `on_delete(self, field, sub_objs, ...)` with the pending queryset | R + A-reference | with no `.only` call the pending query's `deferred_loading` stands untouched, so what it already fetches is what is fetched — which need NOT be every column, since the pending query may carry a narrowing of its own (B1a). The model result equals `already_selected`. The subsequent `if sub_objs: on_delete(...)` is the unchanged downstream call, not part of the column-set decision under spec. |

The discriminating content of the change — *only the columns the deletion
actually consults are fetched when the rows are not exposed* — lives in the
postcondition `Implies(not whole_row_required and not exposed_to_observers(pre, post)
and len(referenced) > 0 and Exists(k: referenced[k] == pk),
ToSeq(Result()) == ToSeq(referenced))` and its sibling cell for the case where
the row identity is outside the consulted set. The pre-patch `collect` passed
`sub_objs` on untouched, so the pending query's own column set was fetched and no
narrowing was ever requested; `model_prepatch.py` reproduces that (always returns
`already_selected`) and **fails** exactly that postcondition when the
consulted-plus-identity set is not what the pending query already fetches — which
is precisely the spec sensing the change (G-DIFF). This is the F2P scenario: the
pending query is the plain base-manager one, so `already_selected == all_fields`,
and `large_field` (unreferenced) must be absent from the SELECT unless a
`pre_delete`/`post_delete` receiver is connected.

Note that B6 is what makes the prepatch's failure *specific*: because the
no-request cell states `already_selected` rather than `all_fields`, a rival that
returns `already_selected` everywhere is wrong exactly on cells 1–3, and a rival
that returns `all_fields` in the no-request cell is wrong exactly whenever the
pending query carries its own narrowing. Both are rejected by the property
battery (`partial-prepatch-passthrough`, `partial-cell4-returns-full-set`,
`partial-cell3-returns-pending-set`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. Both operations that genuinely
*changed* are modelled **deeply**, not hidden behind an axiom about the function
under change:
- the exposure helper is the spelled-out boolean disjunction (`exposed_to_observers`);
- the column decision is the spelled-out branch over the abstract column tokens,
  including the row-identity retention, the empty-request reset, and the
  no-request pass-through (`select_cascade_fields`).
There is **no consumed `@ContractOnly` axiom**. The real callees the new code
invokes (`has_listeners`, `.only` / `add_immediate_loading` / `deferred_to_data`)
appear only as **A-references** that G-AX validates the deep models against
(mapping.md §3) — never as contracts the proof consumes.

## D. verify(model) ⇒ resolved

`rows_exposed_to_observers` verifies only if it returns exactly `pre or post` (A3);
`select_cascade_fields` verifies only if it returns, on each cell of the
partition, exactly that cell's value: the reachable consulted columns together
with the row identity when no eager fetch is required, the rows are not exposed,
and at least one consulted column is reachable (B5); the full column set when
nothing consulted is reachable (B5e); and the pending query's own column set when
no request is made at all (B6) — with the guard being the exact
`not (whole_row_required or pre or post)` (B4). By R (bool ↔ bool, column
`attname` ↔ token, column set ↔ `List[int]`, pending column set ↔
`already_selected`, reachable consulted set ↔ `referenced`) the verified
decisions equal the gold patch's `_has_signal_listeners` and `collect` branch on
the tested inputs; by G-AX the deep models equal the real `has_listeners`
disjunction (A-reference, §3.1) and the real column decision over the real
deferred-loading semantics (A-reference, §3.2) — a correspondence G-CONF
independently confirms against the real emitted SQL on 100000 inputs, 48645 of
which give the pending query a restriction of its own.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(here: the A-reference validations, G-AX) and refinement fidelity (this
document, G-EQ).
