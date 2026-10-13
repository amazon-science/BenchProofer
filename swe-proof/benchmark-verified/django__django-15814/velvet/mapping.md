# mapping.md — django__django-15814

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a`, states the type
abstraction (the Lean↔Python bijection G-CONF/G-AX would use), and records
callee provenance. There are **no axioms and no A-reference deep models of
outside callees** in this bundle, so §3 records provenance of the modeled
data flow only.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveKeys (entities : List Entity)` | `Query.deferred_to_data(self, target)` — `django/db/models/sql/query.py:721` (the field-restriction map-keying step, body lines 745–757) | the modeled changed function: walks a relation chain and records, per model reached, the key under which that model's field restrictions are collected |
| `Entity` (`ident`, `canon`) | a model class reached while walking the chain (`cur_model`) together with its `_meta.concrete_model` (`django/db/models/sql/query.py:748,750,751`) | the only two identities the keying step observes: the model as reached (`cur_model`) and its canonical/concrete underlying model |
| `canonOf (e : Entity)` | `cur_model._meta.concrete_model` — the post-patch normalization at `django/db/models/sql/query.py:751` (`cur_model = cur_model._meta.concrete_model`) | pure spec: the canonical key an entity contributes |
| `keysOf (es : List Entity)` *(deep model — I/R)* | the per-iteration sequence of map keys `add_to_dict(must_include, cur_model, …)` records along the chain (`django/db/models/sql/query.py:757`) | pure spec: the ordered keys for a whole relation chain |

The repo symbol the change touches is the assignment to `cur_model` just before
`opts = cur_model._meta` (`query.py:751`): pre-patch the loop uses `cur_model`
exactly as reached through the relation; post-patch it first rebinds
`cur_model = cur_model._meta.concrete_model`. Both `opts` and the
`add_to_dict(must_include, cur_model, opts.pk)` key (`query.py:757`) then see the
canonical model.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a model class reached through a relation (`cur_model`) | `Entity.ident : Int` | each distinct model class ↔ a distinct `Int` identity token; equality of classes ↔ equality of `ident` |
| that model's canonical/concrete underlying model (`cur_model._meta.concrete_model`) | `Entity.canon : Int` | the concrete model's identity token; for a non-derived (concrete) model the class IS its own `concrete_model`, so `ident = canon`; for a derived view (a proxy) `concrete_model` is the underlying base, so `ident ≠ canon` |
| the relation chain `parts[:-1]` walked by the inner `for name in …` loop | `entities : List Entity` | one `Entity` per model reached, in chain order; `len(parts[:-1])` ↔ `entities.length` |
| the ordered keys `must_include`/downstream consumer indexes models by | `keysOf entities : List Int` | the canonical key recorded per model, in order; `List` `::`/order ↔ insertion order |

A model's `_meta.concrete_model` is the class itself for an ordinary or
multi-table-inheritance child, and the underlying base class for a proxy model
(a proxy adds no columns; it is an alternate Python view of the same table). So
`canon = ident` for every model EXCEPT a proxy, where `canon` is the proxied
base. The downstream consumer (the related-populator that builds each model's
`init_list` and looks up its pk column) is keyed by the concrete model; a proxy
key therefore fails to match, which is the reported `'id' is not in list` crash.

## 3. Modeled data-flow provenance (no axioms / no A-references)

The single behavioral change is **which identity each reached model contributes
as a map key**: the surface model as reached (`cur_model`) vs. its canonical
underlying model (`cur_model._meta.concrete_model`). This is captured exactly by
`canonOf e = e.canon` and the `keysOf` fold over the COMPLETE chain carrier.

`_meta.concrete_model` is **not** axiomatized or deep-modeled as an A-reference
of a stdlib callee: it is not a callee the proof reasons about; it is the
identity-normalization the fix performs, and its result is the modeled value
`Entity.canon` carried in the input. The `Entity.ident` field records the
pre-normalization identity so the prepatch (which keys by `ident`) can diverge
from the spec (`keysOf`, which keys by `canon`) on any chain containing a proxy
(`ident ≠ canon`).

There are therefore **no `axiom` declarations, no A-reference deep models, and no
`axiom_check.py`** (nothing to validate against a real callee).

## 4. G-CONF — SKIPPED (conf_skip = true)

There is no pure, DB-free R/I shadow to differential-test. The operation the
control flow performs — walking a relation chain via `opts.get_field(name)` /
`source.remote_field.model` and recording, per reached model, the key under which
that model's field restrictions are accumulated — only has observable behavior
relative to a live model registry and a relational backend:

* the chain of models reached is produced by Django's metadata graph
  (`_meta.get_field`, `remote_field.model`, `related_model`) resolved against
  registered model classes, and whether a reached model is a proxy
  (`ident ≠ canon`) is a property of that registered class hierarchy;
* reproducing the bug-triggering case — a relation chain whose target is a proxy
  model, optimized with `select_related().only(...)`, so the downstream
  related-populator looks up the concrete model's pk and crashes with `'id' is
  not in list` — requires standing up the model graph (`CustomModel` /
  `ProxyCustomModel` / `AnotherModel`, or the F2P `ProxyTrackerUser`/`Issue`
  models), a DB connection, and an actual query execution; i.e. the F2P
  integration test `test_select_related_only` itself, not a pure R/I
  transliteration this gate could fuzz.

The abstraction the spec pins (`canon` ↦ the key every reached model contributes,
collapsing a proxy onto its concrete model) IS the modeled content; there is no
DB-free oracle that produces the metadata-graph model chain and proxy-ness to
diff against. Therefore `meta.json conf_skip = true` and `conformance_check.py`
is a `status=skip` stub (exit 0). Soundness of the modeled keying step is carried
by **G-VERIFY** (the fold provably records `canonOf` = the canonical identity for
every reached model) and **G-DIFF** (the prepatch, which records the surface
`e.ident`, fails exactly the `out = keysOf entities` clause on any input
containing a proxy). This mirrors the django__django-13109 / django__django-13315
/ django__django-13089 precedents (a live-DB / live-registry control-flow change
with no DB-free shadow).
