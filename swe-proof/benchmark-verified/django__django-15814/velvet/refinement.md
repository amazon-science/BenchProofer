# refinement.md — django__django-15814

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolveKeys` `do` block, the deep `keysOf`/`canonOf` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** / **A-reference** (axiomatized callee — none here), or **I**
(identical concrete op).

This bundle has **no axioms and no A-reference deep models**, so every step is
R or I; G-CONF is skipped (mapping.md §4). Soundness rests on G-VERIFY +
G-DIFF, as in the django__django-13109 / -13315 / -13089 precedents.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The keying site — `Query.deferred_to_data` (`django/db/models/sql/query.py:751`)

Gold hunk:
```
                else:
                    cur_model = source.remote_field.model
+                cur_model = cur_model._meta.concrete_model
                 opts = cur_model._meta
```

The one-line fix rebinds `cur_model` to its concrete model immediately after the
model for the next chain step is chosen, BEFORE `opts = cur_model._meta` and
before `add_to_dict(must_include, cur_model, opts.pk)` use `cur_model` as the map
key (`query.py:757`). Effect: every model reached while walking the relation
chain is recorded under its canonical/concrete identity, so a proxy model and the
underlying base it proxies collapse to one key — the key the downstream
related-populator (`django/db/models/query.py:2243`,
`init_list.index(self.model_cls._meta.pk.attname)`) actually indexes by.

| # | Solution.lean impl op (`resolveKeys`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entities : List Entity` | the sequence of models `cur_model` takes along the inner `for name in parts[:-1]` loop, each paired with its `_meta.concrete_model` | R | model class ↔ `Entity.ident`; its concrete model ↔ `Entity.canon` (mapping.md §2). One `Entity` per reached model, in chain order. |
| A2 | `canonOf e = e.canon` recorded per entity | the inserted `cur_model = cur_model._meta.concrete_model` (`query.py:751`) feeding the `add_to_dict(must_include, cur_model, …)` key (`query.py:757`) | I | the changed key-selection is modeled **deeply**: `canonOf`/`keysOf` (pure region) and the verified loop ARE the canonical-key recording. The op `canonOf e` (project the canonical identity) is concrete/transliterated; no axiom about `concrete_model`. |
| A3 | result is `keysOf entities` — the canonical key of every reached model, in order, computed by the backward `while` fold | the ordered keys accumulated into `must_include` across the chain | I | the loop op (`canonOf e :: keys`, the backward walk) is the concrete transliteration of recording one key per chain step. |

Discriminating content of the change — a derived view (proxy) keys under its
**canonical/concrete** identity, not its surface identity — lives in
`canonOf e = e.canon` (model) ⇔ the inserted `cur_model = cur_model._meta.concrete_model`
(real). The pre-patch code keyed by the surface `cur_model` (`= e.ident`);
`Solution_prepatch.lean` reproduces that (`keys := e.ident :: keys`) and **fails**
`out = keysOf entities` (G-DIFF) on any input containing a proxy
(`ident ≠ canon`).

## B. No axioms, no A-references, no kind-3 steps

Every step is R or I. The one operation that genuinely *changed* — selecting the
canonical model identity as the map key — is modeled **deeply** (the spelled-out
`canonOf`/`keysOf`, step A2/A3, I-tagged with the `Entity.canon` carrier), not
hidden behind an axiom about the function under change or about `concrete_model`.
There is no consumed axiom and no A-reference deep model of an outside callee
(so no `axiom_check.py`). There is no *changed-op-inexpressible* (kind-3) step.

## C. verify(Solution) ⇒ resolved

`resolveKeys` verifies only if `out = keysOf entities` — i.e. every reached model
is recorded under its CANONICAL identity (`canonOf e = e.canon`), so a proxy and
its concrete base collapse to one key. By the R bijection (mapping.md §2) the
verified result corresponds to the patched keying step: the field-restriction map
is keyed by the concrete model, so the downstream related-populator finds the
concrete model's `init_list` / pk column instead of crashing with `'id' is not in
list`. This is precisely what the F2P test `test_select_related_only` demands: a
`select_related("assignee").only("assignee__status")` over a relation whose target
is a proxy model (`ProxyTrackerUser`) must execute and return the row instead of
raising `ValueError`.

The prepatch impl (`keys := e.ident :: keys`) records the surface identity —
exactly the gold pre-patch behavior (`cur_model` un-normalized) — and fails the
`out = keysOf entities` clause (G-DIFF) on any input containing a proxy
(`ident ≠ canon`), the observable of the bug. No trust points beyond the type
bijection: there are no axioms, and G-CONF's absence is justified by the
live-registry / live-DB nature of the relation-chain walk (mapping.md §4),
carried by G-VERIFY + G-DIFF as in the django__django-13109 / -13315 / -13089
precedents.
