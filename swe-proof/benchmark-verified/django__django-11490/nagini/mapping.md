# mapping.md — django__django-11490

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7038adbd02c916315b16939b835f021c2ee8880`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour the deep model is validated against).

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `columns_for_subquery(cached, outer_select)` *(model symbol — neutral behavioral name, directive 6)* | the column-setting branch body of `SQLCompiler.get_combinator_sql` — `django/db/models/sql/compiler.py:410` (branch body lines 426-433) | the modelled changed code: the `if not compiler.query.values_select and self.query.values_select:` branch the patch edits |
| `cached: Query` (param) | `compiler.query` — the reused component sub-query inside the `for compiler in compilers:` loop | the shared/reused per-component `Query` the fix must detach from |
| `outer_select: List[int]` (param) | the outer column tuple `(*self.query.extra_select, *self.query.values_select, *self.query.annotation_select)` passed to `set_values` (`compiler.py:429-433`) | the column list the outer (compound) query restricts to |
| `Query.columns` (model field) | `django.db.models.sql.query.Query.values_select` (init `query.py:205`; set in `set_values` at `query.py:2062`) | the component's OWN chosen column list (empty tuple = none chosen); model attribute renamed to the neutral `columns` (directive 6) |
| `Query.leading` (model field) | the ordered keys of `django.db.models.sql.query.Query.extra_select` (backing dict `extra`, `query.py:198`; the property filters it through `extra_select_mask`) | the family of derived columns the component emits AHEAD of its own columns, and the family a requested name is classified against FIRST (`set_values` consults `self.extra` before `self.annotations`) |
| `Query.trailing` (model field) | the ordered keys of `django.db.models.sql.query.Query.annotation_select` (backing dict `annotations`, `query.py:190`; the property filters it through `annotation_select_mask`) | the family of derived columns the component emits AFTER its own columns |
| `Query.state` (model field) | the REMAINDER of the `Query`'s accumulated per-query state — `where` (`query.py:159`) together with the DEFINITIONS behind the two derived families (the `extra` dict's SQL and the `annotations` dict's expressions) — abstracted to one opaque `int` token | equal tokens ↔ observably-equal accumulated state; a per-compilation copy carries the token (`clone` copies all of it), a brand-new blank `Query` does NOT; `set_values` leaves it untouched (it rebinds `values_select` and the two masks, never the definitions or the where clause) |
| `own_columns(fields, leading, trailing)` *(@Pure)* | the `field_names` partition of `set_values` — `query.py:2050-2060` (a requested name found in `self.extra` or `self.annotations` is routed to `extra_names` / `annotation_names`, everything else appended to `field_names`) | the classification law the spec pins |
| `kept_leading(leading, fields)` *(@Pure)* | `self.set_extra_mask(extra_names)` (`query.py:2061`) read back through the `extra_select` property: the mask filters `self.extra` in its own insertion order | the narrowing of the leading family |
| `kept_trailing(trailing, fields, leading)` *(@Pure)* | `self.set_annotation_mask(annotation_names)` (`query.py:2061`) read back through the `annotation_select` property; the third argument encodes that the partition tests `self.extra` FIRST, so a name defined in both families never reaches `annotation_names` | the narrowing of the trailing family, with the leading-wins precedence |
| `detached_copy(q)` *(deep model — A-reference)* | `django.db.models.sql.query.Query.clone` — `django/db/models/sql/query.py:292` | the unchanged callee the FIX newly invokes (`compiler.query.clone()`); deep-modelled, validated == real by axiom_check.py (G-AX). Model symbol renamed to a neutral behavioral carrier (directive 6); the repo callee is `Query.clone`. |
| `with_columns(q, fields)` *(deep model — A-reference)* | `django.db.models.sql.query.Query.set_values` — `django/db/models/sql/query.py:2030` | the unchanged callee already invoked in the branch; deep-modelled, validated == real by axiom_check.py (G-AX). Model symbol renamed to a neutral behavioral carrier (directive 6); the repo callee is `Query.set_values`. |

The pre-patch repo behaviour the change targets (for the refinement audit, not
referenced from the consumer spec view): the branch invoked
`compiler.query.set_values(...)` directly on the reused `compiler.query`, whose
`combined_queries` entry is the SAME `Query` object across repeated evaluations
of the compound queryset (`django/db/models/query.py:934`,
`combined_queries = (self.query,) + ...`), so the first evaluation's in-place
mutation of `values_select` **and of the two narrowing masks** leaked into later
evaluations.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Query` object (`django.db.models.sql.query.Query`) | minimal `Query` class with the three touched column families (`columns`, `leading`, `trailing`) plus one opaque `state` token | object identity preserved (`is`); the three column families are modelled at value level; the REST of the `Query`'s accumulated state (the where clause and the two derived-column DEFINITION dicts) is abstracted to the opaque `state` token — it is NOT irrelevant: the fix's per-compilation copy must CARRY it (which is what distinguishes a clone from a brand-new blank query), and the spec pins that carry (`Result().state == cached.state`) |
| repo `values_select` tuple of field-name strings | model attr `columns`: `List[int]` of column codes | each distinct column name ↔ a distinct `int` code; the empty tuple `()` ↔ the empty list `[]`; `len`, element-wise equality, and the truthiness test `not values_select` ↔ `len(columns) == 0` all mirror |
| repo `extra_select` / `annotation_select` (ordered dict views, each the backing dict filtered by its mask) | model attrs `leading` / `trailing`: `List[int]` of column codes | only the ordered KEYS are modelled, because only they are observable in the rendered column list; the DEFINITIONS behind them live in the `state` token. Insertion order ↔ list order; applying a mask ↔ replacing the list with an order-preserving sub-list |
| the outer column tuple `(*extra_select, *values_select, *annotation_select)` | `outer_select: List[int]` (non-empty) | the concatenated chosen column tuple ↔ a single `List[int]`; it is non-empty because the branch requires `self.query.values_select` to be truthy (`len(outer_select) > 0`) |
| `compiler.query = compiler.query.clone()` (reassign to a fresh clone) | `private = detached_copy(cached)` returning a fresh, distinct `Query` CARRYING `cached.state` | object-identity refinement: the reassignment ↔ producing and using a new object distinct from `cached`; the state-token carry (`Result().state == q.state`) ↔ `clone()`'s copy of the whole `__dict__` (where/extra/annotations preserved) plus its re-copy of the mutable containers and both masks, which a fresh `Query(model)` would not provide |
| `set_values(fields)` PARTITIONING the requested names and setting both masks | `with_columns(q, fields)` setting `q.columns` to `own_columns(fields, leading, trailing)`, `q.leading` to `kept_leading(leading, fields)` and `q.trailing` to `kept_trailing(trailing, fields, leading)` | see §3.2: the shortcut path (`not self.extra and not self.annotations`) is the degenerate case of the same three equations, since both families are then empty |
| `set_values(())` (an empty chosen tuple) | *excluded by precondition* `Requires(len(fields) > 0)` | a different operation on the real callee (it takes `self.default_cols`/concrete-field path and leaves both masks alone), so the model restricts its domain rather than claiming it; the divergence is recorded executably by `axiom_check.py` leg C and by the battery's containment probe |

`str` is never indexed; column names are abstracted to `int` codes, so no
banned `str` operations appear.

G-CONF (`conformance_check.py`) exercises this bridge differentially against
the patched repo with a pinned fuzz seed: **11490** (>= 1e5 compilation
checks; column code k realized as the plain integer column `f<k>`, a leading
code as an `extra` entry of that name, a trailing code as an annotation of that
name, the state token as a WHERE filter's bound parameter).

## 3. Deep-model references (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `detached_copy` deep model ↔ `Query.clone()` (A-reference)
**Callee:** `django.db.models.sql.query.Query.clone` (`query.py:292`). It builds
a new `Empty()` object, sets `obj.__class__ = self.__class__`, then
`obj.__dict__ = self.__dict__.copy()` (a shallow copy), and re-clones the
mutable containers (`alias_map`, `where`, `annotations`, `extra`, and both
select masks). Critically:

  * the returned object is a **distinct** object (`obj is not self`);
  * `values_select` (an immutable tuple) is carried over by the shallow
    `__dict__.copy()`, so the clone's `values_select` **equals** the original's;
  * both derived families are carried over **un-narrowed**: `extra_select` and
    `annotation_select` on the copy list the same keys in the same order,
    because the backing dicts and the masks are re-copied;
  * a later `set_values` on the clone reassigns `clone.values_select` to a NEW
    tuple and sets the clone's OWN masks, leaving the original's
    `values_select` and both of its un-narrowed families untouched — this is
    the aliasing break the fix relies on (model.py clause (2));
  * the copy CARRIES the query's whole accumulated state — `where`, the `extra`
    definitions, the `annotations` definitions — because the entire `__dict__`
    is copied and the mutable containers re-cloned. A brand-new `Query(model)`
    does NOT carry that state. This is the model's `Result().state == q.state`
    clause (the opaque `state` token).

This is exactly what the deep model `detached_copy` encodes (on its model attrs
`columns`, `leading`, `trailing`, `state`): `Result() is not q`, the three
containers each `is not` the original's, the three sequences equal the
original's, `Result().state == q.state`, and the original is unchanged. The
changed operation (the newly-added `.clone()`) is modelled **deeply**; there is
**no `clone` axiom** the proof consumes. G-AX asserts `Query.clone()` meets
these properties — including the un-narrowed family carry, the independent
masks and the where/extra/annotation state carry — on the real callee.

### 3.2 `with_columns` deep model ↔ `Query.set_values()` (A-reference)
**Callee:** `django.db.models.sql.query.Query.set_values` (`query.py:2030`).

It does **not** unconditionally record the requested list. `field_names =
list(fields)` is taken only on the shortcut path guarded by `if not self.extra
and not self.annotations` (`query.py:2046-2048`). Otherwise it **partitions**
the requested names (`query.py:2050-2060`): a name found in `self.extra` goes to
`extra_names`, a name found in `self.annotations` goes to `annotation_names`
(the `extra` test comes FIRST, so a name defined in both is claimed by `extra`),
and everything else goes to `field_names`. It then narrows both families with
`self.set_extra_mask(extra_names)` / `self.set_annotation_mask(annotation_names)`
(`query.py:2061`) and finally sets `self.values_select = tuple(field_names)`
(`query.py:2062`).

Read back through the `extra_select` / `annotation_select` properties (each the
backing dict filtered by its mask, in the dict's own insertion order), that is
exactly the model's three equations:

    q.columns  == own_columns(fields, leading, trailing)
    q.leading  == kept_leading(leading, fields)
    q.trailing == kept_trailing(trailing, fields, leading)

The shortcut path is the degenerate case of the same equations (both families
empty ⇒ `own_columns(fields, [], []) == fields` and both narrowings are no-ops),
so the model needs no case split. The call mutates only the query it is invoked
on (each `Query` owns its `values_select` and its two masks), and it does not
destroy the accumulated `where` clause or either family's DEFINITIONS — it only
rebinds the column-selection fields and the masks. Hence the model's
`q.state == Old(q.state)`.

Two consequences the specification depends on:

  * **the operation is not idempotent in the classification sense.** Because the
    partition is taken against the families the query exposes AT THAT MOMENT and
    each application narrows them, applying a chosen list to an
    ALREADY-narrowed query does not reach the outcome of applying it once to a
    faithful copy: a family member dropped by the earlier application is no
    longer found in `self.extra`/`self.annotations`, so a requested name naming
    it lands in `field_names` instead (and the query's table has no such
    concrete column, so the real callee usually raises `FieldError` outright).
    The spec therefore pins the compilation's outcome as a function of the
    SHARED sub-query's UN-narrowed families, which only a single application to
    a faithful copy achieves.
  * **an empty `fields` is a different operation**, so the model excludes it
    (`Requires(len(fields) > 0)`) rather than claiming it. The branch under
    specification cannot reach it anyway: it is guarded on
    `self.query.values_select` being truthy.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory Django and
a minimal two-column model (the structural twin of the test's `ReservedName`)
carrying up to two `extra` entries and up to two annotations, in both orders,
over an accumulated `where` filter. It then asserts, on the REAL callees:

  * **leg A** — the three equations above on 1423 pristine shapes (every
    combination of exposed families × every ordered request of up to three
    names drawn from the query's own and derived columns), plus the shortcut
    shape and a `group_by` shape;
  * **leg B** — the same three equations on 1844 ALREADY-narrowed queries
    (1228 of which the callee rejects with `FieldError`, which is still not the
    single-application outcome), pinning the model OFF the gold path;
  * **leg C** — that an empty chosen list DIVERGES, which is what justifies the
    `len(fields) > 0` precondition instead of assuming it;
  * **leg D** — that a name defined in BOTH families is claimed by the leading
    one (the third argument of `kept_trailing`);
  * **leg E** — `clone()` distinctness, independent containers and masks, the
    un-narrowed family carry, the state carry, and that a brand-new `Query`
    carries none of it;
  * **leg F** — that on 984 of 984 real shapes a SECOND application never
    reaches the single-application outcome, so the spec's rejection of a
    double-applying implementation matches the real callee rather than being an
    artifact.

It imports only Django and the standard library; the operations are the very
Django callees the gold patch invokes. Exit 0 iff every observation matches the
deep models.
