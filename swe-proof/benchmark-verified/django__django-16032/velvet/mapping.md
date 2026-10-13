# mapping.md — django__django-16032

Binds `Solution.lean` symbols to the repo at
`base_commit = 0c3981eb5094419fe200eb46c71b5376a2266166`.

Repo files under change: `django/db/models/sql/query.py` and
`django/db/models/fields/related_lookups.py`. The fix has three hunks; their
single observable effect is the value of `Query.has_select_fields` for a query
that carries only annotation columns:

1. `Query.has_select_fields` changes from a derived **property**
   (`query.py:266-270`, `bool(self.select or self.annotation_select_mask or
   self.extra_select_mask)`) to a plain class attribute
   (`query.py:201`, `has_select_fields = False`) that is set `True` only by
   `set_values` (`query.py:2384`, added `self.has_select_fields = True`).
2. `RelatedIn.get_prep_lookup` (`related_lookups.py:76`) swaps its column-set
   reduction `clear_select_clause(); add_fields([target_field], True)`
   (`related_lookups.py:96,108`) for `set_values([target_field])`
   (`related_lookups.py:107` post-patch) — a behaviour-preserving co-change that
   keeps the new flag consistent (it now reduces *via* the same `set_values`
   that sets the flag).

The narrowing decision the spec models is the guard
`if not self.rhs.has_select_fields:` (in `In.get_prep_lookup`,
`lookups.py:427`) and the equivalent `not getattr(self.rhs,
"has_select_fields", True)` guard (`related_lookups.py:93`): a right-hand-side
membership subquery is reduced to a single output column exactly when
`has_select_fields` is false.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `narrowRhsSubquery (q : RhsQuery)` | the `if not self.rhs.has_select_fields:` membership-narrowing guard (`lookups.py:427` in `In.get_prep_lookup`; `related_lookups.py:93` in `RelatedIn.get_prep_lookup`) | the modeled changed behaviour: whether the rhs subquery is reduced to one output column |
| `RhsQuery.explicitlyProjected` | the value the *post-patch* `has_select_fields` flag holds: `True` iff `set_values(...)` was called (`query.py:201` default `False`; `query.py:2384` sets `True`); `set_values` is invoked by `QuerySet.values()/values_list()` (`query.py:1302` in `query.py`-level callers) | FREE INPUT: whether the caller explicitly projected the query's output columns |
| `RhsQuery.hasExplicitSelectColumns` | `bool(self.select)` — the explicit select-column list (`query.py:269`, first disjunct of the old property) | FREE INPUT: whether the query already carries an explicit select-column list |
| `RhsQuery.carriesAnnotations` | `bool(self.annotation_select_mask)` — the annotation-select mask, non-empty after `annotate()`/`alias()` populates it (`query.py:269`, second disjunct of the old property; set via `append_annotation_mask`, `query.py:2368`) | FREE INPUT: whether the query carries annotation columns |
| `RhsQuery.carriesExtraSelections` | `bool(self.extra_select_mask)` — the extra-select mask (`query.py:269`, third disjunct of the old property) | FREE INPUT: whether the query carries extra raw-select columns |
| `designatesOutputColumns q` | the post-patch `has_select_fields` semantics: the query designates its output columns iff `set_values` was called (`query.py:201,2384`) | pure spec: a query designates its output columns iff explicitly projected |
| `narrowsToSingleColumn q` | the guard expression `not self.rhs.has_select_fields` deciding the reduction (`lookups.py:427`, `related_lookups.py:93`) | pure spec: narrow iff the query does not designate its output columns |

The pre-patch repo symbol the change removes (refinement audit only, not in the
consumer spec view): the derived `has_select_fields` property body
`bool(self.select or self.annotation_select_mask or self.extra_select_mask)`
(`query.py:266-270`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Query.has_select_fields` (post-patch: a `bool` class attribute, `False` until `set_values` flips it `True`) | `RhsQuery.explicitlyProjected : Bool` | `True` ↔ `set_values(...)` was called (explicit output-column projection, e.g. via `.values()`); `False` ↔ never projected. This is the value the narrowing guard reads post-patch. |
| `bool(self.select)` — explicit select-column tuple (`query.py:269`) | `RhsQuery.hasExplicitSelectColumns : Bool` | `True` ↔ `self.select` non-empty; `False` ↔ empty `()`. |
| `bool(self.annotation_select_mask)` — annotation-mask `set` (`query.py:269`) | `RhsQuery.carriesAnnotations : Bool` | `True` ↔ mask non-empty (an `annotate()`/`alias()` populated it); `False` ↔ `None`/empty. The discriminating bit: `annotate().alias()` makes this `True` with all of `explicitlyProjected`/`hasExplicitSelectColumns`/`carriesExtraSelections` `False`. |
| `bool(self.extra_select_mask)` — extra-mask `set` (`query.py:269`) | `RhsQuery.carriesExtraSelections : Bool` | `True` ↔ mask non-empty; `False` ↔ `None`/empty. |
| "the rhs subquery is reduced to a single output column" | `Bool` (`narrow`, return of `narrowRhsSubquery`) | `True` ↔ the `if not self.rhs.has_select_fields:` branch (`clear_select_clause()`/`set_values([target])`, narrowing to one column) is taken; `False` ↔ the subquery is left with its current (multi-)column projection. |

`RhsQuery` carries the four booleans the old derived property combined plus the
post-patch flag, because the change is precisely about *which* of these the
narrowing decision depends on: post-patch only `explicitlyProjected`, pre-patch
the disjunction of the latter three. The four fields are observed only as
booleans; no concrete select list, mask set, or `Query` object is inspected by
the modeled decision (those flow untouched through the unchanged
SQL-compilation machinery).

## 3. Callee provenance

No axioms and no A-reference deep models.

- The unchanged machinery the narrowing decision gates — `clear_select_clause`,
  `add_fields`, `set_values`, and ultimately subquery SQL compilation — is NOT
  altered in a way the decision observes. The patch changes only (a) how
  `has_select_fields` is *computed* (derived disjunction → stored flag) and
  (b) which reduction primitive `RelatedIn` calls (`clear+add_fields` →
  `set_values`, behaviour-preserving). The column-state booleans the guard reads
  are **free inputs** (`explicitlyProjected`, `hasExplicitSelectColumns`,
  `carriesAnnotations`, `carriesExtraSelections`); the spec is a pure boolean
  decision over them, holding for every value. Nothing to check against a real
  callee → **no G-AX** (precedent: django__django-11265).
- The CHANGED op (the narrowing guard's dependence on `has_select_fields`) is
  modeled **deeply** as the boolean expression `! explicitlyProjected`
  (I/R-tagged, refinement.md). No outside contract is consumed.

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub (`meta.json conf_skip=true`).

The fix's only DISCRIMINATING observable is the **queryset result / SQL** — a
membership subquery built from `annotate().alias()` (no explicit projection)
must compile to a single-column sub-select instead of raising
`OperationalError: sub-select returns N columns - expected 1`. Both materialize
only against a **live Django ORM + a real database**: a configured model layer,
the SQL compiler, and a backend that actually executes the generated subquery.
To observe "the subquery was narrowed to one column" one must run the F2P
integration tests themselves
(`test_annotation_and_alias_filter_in_subquery`,
`test_annotation_and_alias_filter_related_in_subquery`), not a DB-free
transliteration this gate could fuzz over ≥10⁵ inputs.

There is no DB-free, input-dependent R/I shadow to differential-test: the
modeled op is a 1-bit boolean decision over four free inputs
(`narrow = ! explicitlyProjected`); whether *not* narrowing actually changes
the returned rows / raises an error depends on the rest of the live query and
the database contents, which a pure shadow cannot reproduce. The shadow of the
boolean guard itself carries no information the spec (G-VERIFY) does not already
pin.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only discriminating
observable is a result/side effect on a live ORM + DB with no DB-free R/I
shadow, set `meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11265, django__django-11066, django__django-11451). Soundness of
the modeled behaviour is carried instead by **G-VERIFY** (the spec provably
forces `narrow = ! explicitlyProjected`) and **G-DIFF** (the prepatch, which
restores the old derived disjunction, fails on exactly that clause —
refinement.md §C).

## 5. Notes

The two FAIL_TO_PASS entries exercise the SAME fixed behaviour through two
sibling guards: `pk__in` routes through `In.get_prep_lookup` (`lookups.py:427`,
fixed by the `has_select_fields` change alone) and `book__in` routes through
`RelatedIn.get_prep_lookup` (`related_lookups.py:93`, which additionally swaps
`clear_select_clause()+add_fields` for the behaviour-preserving `set_values`).
Both fail pre-patch for the identical reason — `has_select_fields` is wrongly
`True` for an `annotate().alias()` subquery — and both pass once that single bit
is corrected. Hence ONE independently-observable fixed behaviour → one modeled
function + one prepatch (`Solution_prepatch.lean`). The gold-verbatim
`patch.diff` applies all three hunks and resolves (G-RESOLVE).

`q` (the `RhsQuery`) is a read-only input — it is not declared `mut`
(directive 5): the modeled routine reads its column-state booleans and produces
a fresh boolean, mutating nothing it is handed.
