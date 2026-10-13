# mapping.md — django__django-13109

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fbe82f82555bc25dccb476c749ca062f0b522be3`, states the type
abstraction (the Lean↔Python bijection), records callee provenance, and explains
why G-CONF is skipped.

Repo file under change: `django/db/models/fields/related.py`.
Changed function: `ForeignKey.validate(self, value, model_instance)`
(`django/db/models/fields/related.py:909`; the touched step is the queryset
construction at `related.py:917` pre-patch / post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateExists (rows : List Record) (target : Int)` | the existence test inside `ForeignKey.validate` — the `qs = ... .filter(**{field_name: value})` / `qs.exists()` step, `related.py:917–921` | the modeled changed behavior: decide whether a record whose referenced field equals the target identity exists in the consulted record collection |
| `rows : List Record` | the record collection the existence query ranges over — the related model's manager queryset (`self.remote_field.model.<manager>.using(using)`), one element per stored row of the related model | the input collection the existence test is evaluated against |
| `target : Int` | `value` — the referenced-field value being validated (typically the related row's primary key) | the identity the test searches for |
| `Record.key` | the stored value of the referenced field on one related row (`getattr(row, field_name)`, matched by `.filter(**{field_name: value})`) | the field a candidate row matches on |
| `Record.hidden` | whether the row is excluded from the model's everyday/default view by a custom default-manager view filter (e.g. an `archived=True` row dropped by a `get_queryset().filter(archived=False)` manager) | distinguishes the two managers: the everyday view omits hidden rows; the complete view keeps them |
| `out : Bool` | `qs.exists()` — whether the consulted collection contains a matching row | the observable: a true result means validation passes; a false result raises `ValidationError('invalid')` |

No callee is axiomatized. The existence primitive (`.filter(...).exists()`) is
modeled DEEPLY as the per-record disjunction `existsMatch`/`matchesTarget` over
the input `List Record`; the underlying DB query is observed only through whether
a matching row is surfaced, modeled as the returned `Bool`. There is no consumed
axiom (no `axiom` declarations) and no A-reference deep model of an outside
callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the consulted record collection (a manager's `QuerySet` over the related model) | `List Record` | the rows the manager surfaces ↔ a `List Record`; an empty queryset ↔ `[]`; queryset iteration ↔ `List` traversal. Order is irrelevant to the observable (`exists()`), so any enumeration order refines. |
| the referenced-field value of one row | `Record.key : Int` | `getattr(row, field_name)` ↔ `r.key`; `.filter(**{field_name: value})` matches a row iff its referenced value equals `value` ↔ `matchesTarget target r` (`r.key == target`). Integer pk is the typical referenced field; any orderable scalar key refines to `Int` for the equality test. |
| row is excluded by the model's default view filter | `Record.hidden : Bool` | a custom default manager whose `get_queryset()` applies a filter (e.g. `archived=False`) drops the row from the everyday view ↔ `r.hidden = true`; a row the everyday view keeps ↔ `r.hidden = false`. The base/complete view keeps every row regardless of `hidden`. |
| `value` being validated | `target : Int` | the FK value under validation ↔ `target`; both managers' querysets are filtered by the SAME `**{field_name: value}` predicate, so the only difference between them is WHICH rows they range over (all rows vs. non-hidden rows). |
| `qs.exists()` (true/false) | `out : Bool` | "a matching row exists in the consulted collection" ↔ `out = true`; `validate` raises iff `out = false`. `test_FK_validates_using_base_manager` / `test_validate_foreign_key_to_model_with_overridden_manager` observe exactly this (validation passes for an archived target). |

Note: `using = router.db_for_read(...)` and `.complex_filter(self.get_limit_choices_to())`
are upstream/downstream of the modeled existence test and are unchanged by the
patch; both managers are routed to the same DB and post-filtered identically.
The ONLY change is which manager builds the queryset — i.e. WHICH rows are in
the consulted collection (`rows`), captured by whether `hidden` rows are
included. The match predicate, routing, and limit-choices filter are shared.

## 3. Callee provenance

None axiomatized. The two collection-source primitives are:

* `self.remote_field.model._default_manager.using(using).filter(...)` (pre-patch)
  — the model's everyday/default manager. When the model defines a custom
  default manager that filters rows out of `get_queryset()` (the issue's
  `ArticleManager`/`WriterManager`/`AuthorManager` dropping `archived` rows),
  the consulted collection EXCLUDES those rows. Its per-record effect is "only
  non-hidden rows are visible," the deep model `matchesTarget target r && !r.hidden`
  (prepatch impl), I/R-tagged, not a consumed contract.
* `self.remote_field.model._base_manager.using(using).filter(...)` (post-patch)
  — the model's base manager, which applies no custom default filtering and
  surfaces the COMPLETE row set. Its per-record effect is "every row is
  visible," the deep model `matchesTarget target r` (post-patch impl), I/R-tagged.

Neither is axiomatized or deep-modeled as an A-reference of a stdlib callee: the
property the fix changes is *which rows the existence test ranges over* (the
complete set vs. the default-filtered subset), captured exactly by
`out = existsMatch target rows` over the COMPLETE `rows` carrier, with `hidden`
recording default-view exclusion. The `_base_manager` vs `_default_manager`
machinery only changes the source collection; it does not change the per-row
match predicate (`matchesTarget`), which both share.

## 4. G-CONF — SKIPPED (conf_skip = true)

There is no pure, DB-free R/I shadow to differential-test. The operation the
control flow performs — building a `QuerySet` from one of two managers and
asking `.exists()` after `.filter(**{field_name: value})` — only has observable
behavior relative to a live relational backend:

* whether a matching row is surfaced depends on the SQL the ORM compiles for the
  chosen manager (`_default_manager.get_queryset()` may inject a `WHERE
  archived = False` clause; `_base_manager.get_queryset()` does not), executed
  against real stored rows in a real table;
* reproducing the bug-triggering case (a matching row that the default manager
  filters out — an `archived=True` row whose pk is referenced) requires standing
  up the model graph, a custom manager, and a DB connection with the row
  persisted — i.e. the F2P integration tests themselves
  (`test_FK_validates_using_base_manager`,
  `test_validate_foreign_key_to_model_with_overridden_manager`), not a fuzzed
  pure transliteration.

The abstraction the spec pins (`hidden` ↦ included-in-complete-view-only) IS the
modeled content; there is no DB-free oracle that produces the manager's
row-visibility to diff against. Therefore `meta.json conf_skip = true` and
`conformance_check.py` is a `status=skip` stub (exit 0). Soundness of the modeled
existence test is carried by **G-VERIFY** (the fold provably consults every row,
hidden or not) and **G-DIFF** (the prepatch, which consults only non-hidden rows
`matchesTarget target r && !r.hidden`, fails exactly the
`out = existsMatch target rows` clause on any input whose only matching row is
hidden — the archived-target bug the issue reports). This mirrors the
django__django-13315 and django__django-13089 precedents (a live-DB control-flow
change with no DB-free shadow).
