# refinement.md — django__django-16032

Operation-by-operation correspondence between `Solution.lean`'s `do` block
(`narrowRhsSubquery`) and `patch.diff` (the gold patch: three hunks across
`django/db/models/sql/query.py` and
`django/db/models/fields/related_lookups.py`). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op). EVERY step is R, A, or I. No kind-3 (changed-inexpressible) ops.

The R/I legs would normally be mechanically refuted by **G-CONF**; for this
bundle they cannot be (conf_skip=true, §D below) and are carried by G-VERIFY +
G-DIFF instead. There are no A legs.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The change — `has_select_fields` becomes an explicit-projection flag

The three gold hunks together change a single observable: the value of
`Query.has_select_fields` for a query that carries only annotation columns.

Hunk 1 (`query.py`, class body) — add the default flag:
```
     select_related = False
+    has_select_fields = False
```
Hunk 2 (`query.py`) — delete the derived property:
```
-    @property
-    def has_select_fields(self):
-        return bool(
-            self.select or self.annotation_select_mask or self.extra_select_mask
-        )
```
Hunk 3 (`query.py`, `set_values`) — set the flag when output columns are
explicitly projected:
```
         self.clear_select_fields()
+        self.has_select_fields = True
```

The narrowing decision modeled by `narrowRhsSubquery` is the guard
`if not self.rhs.has_select_fields:` that gates the reduction of an rhs
membership subquery to a single output column (`lookups.py:427`,
`related_lookups.py:93`).

| # | Solution.lean impl op (`narrowRhsSubquery`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `q.explicitlyProjected : Bool` | the post-patch `has_select_fields` flag value: `False` by default (hunk 1), `True` iff `set_values(...)` was called (hunk 3) | **R** | a stored `bool` attribute ↔ `Bool` (mapping.md §2). Free input — the value the narrowing guard reads. |
| A2 | parameters `q.hasExplicitSelectColumns / q.carriesAnnotations / q.carriesExtraSelections : Bool` | `bool(self.select)`, `bool(self.annotation_select_mask)`, `bool(self.extra_select_mask)` — the three disjuncts of the DELETED derived property (hunk 2) | **R** | each truthiness test ↔ `Bool` (mapping.md §2). Free inputs — carried so the prepatch can express the old derived disjunction; post-patch the decision ignores them. |
| A3 | `let designated := q.explicitlyProjected` | the post-patch meaning of `self.rhs.has_select_fields`: the query designates its output columns iff `set_values` set the flag (hunks 1+3) | **I** + **R** | the CHANGED op, modeled deeply: post-patch `has_select_fields` is exactly `explicitlyProjected` (no longer the disjunction over select/annotation/extra). |
| A4 | `return !designated` | `not self.rhs.has_select_fields` — the guard deciding whether the reduction branch (`clear_select_clause()`/`set_values([target])`, narrow to one column) runs (`lookups.py:427`, `related_lookups.py:93`) | **I** + **R** | Python `not` ↔ Lean `!` over the bool bijection. The branch taken ⟺ the returned boolean (mapping.md §2). |

The `RelatedIn` co-change (`clear_select_clause(); add_fields([target], True)`
→ `set_values([target])`, `related_lookups.py`) is **behaviour-preserving**:
both reduce the rhs to the single `target_field` column; the swap exists so the
reduction now goes through the same `set_values` that sets the new flag. It
changes no observable the F2P tests see (both still produce a one-column
sub-select), so it introduces no separate modeled op or prepatch — it is part of
the single `has_select_fields` behaviour modeled here.

## B. (no site B) — single modeled behaviour

Unlike a genuinely multi-site fix, all three hunks serve one behaviour: making
`has_select_fields` report `False` for an `annotate().alias()` subquery so the
membership lookup narrows it to one column. Both F2P tests observe exactly this
bit through two sibling guards (`In` for `pk__in`, `RelatedIn` for `book__in`);
neither adds an independently-fixable behaviour. Hence one modeled function and
one prepatch.

## C. The prepatch (G-DIFF)

**`Solution_prepatch.lean`** restores the pre-patch derived semantics: a query
is judged to designate its output columns when it carries an explicit select
list OR annotation columns OR extra select columns
(`designated := q.hasExplicitSelectColumns || q.carriesAnnotations ||
q.carriesExtraSelections`), i.e. the deleted property
`bool(self.select or self.annotation_select_mask or self.extra_select_mask)`.
An `annotate().alias()` subquery (`carriesAnnotations = true`, everything else
`false`) is therefore judged to designate its columns, the narrowing is skipped,
and the multi-column sub-select reaches SQL — the `sub-select returns 10 columns
- expected 1` error of the issue. The frozen spec demands
`narrow = narrowsToSingleColumn q = ! q.explicitlyProjected`, so `prove_correct`
fails on exactly:
```
case «ensures_1: narrow = narrowsToSingleColumn q»
⊢ (!(q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections))
    = narrowsToSingleColumn q          -- unprovable: false e.g. at
                                       --   explicitlyProjected=false, carriesAnnotations=true
                                       --   (post: narrow=true; pre: narrow=false)
```
(verified: G-DIFF reports `Solution_prepatch.lean: verification failed` on this
clause.) The prepatch is the actual bug: it diverges from the spec exactly on
the annotation-only query the F2P tests build, and agrees elsewhere — so a
verifying impl reverting it would refine to a non-resolving patch (directive 4,
verify ⟹ correct).

## D. No kind-3; G-CONF conf_skip=true

Every step is R, A, or I. The operation that genuinely *changed* — the
narrowing guard's dependence on `has_select_fields` (A3/A4, **I**+**R**) — is
modeled **deeply** as the boolean expression `! explicitlyProjected`, not hidden
behind an axiom. There are no consumed axioms: the unchanged downstream
machinery (`clear_select_clause`, `add_fields`, `set_values`, subquery SQL
compilation) is folded into free inputs about which the spec claims nothing
beyond their use in the modeled decision — so there is nothing for G-AX.

`conformance_check.py` is a documented `status=skip` stub: the only
discriminating observable is the queryset result / SQL (`OperationalError` vs a
one-column sub-select) on a live Django ORM + database — there is no DB-free,
input-dependent R/I shadow to differential-test (mapping.md §4). Soundness is
carried by G-VERIFY (the spec provably forces `narrow = ! explicitlyProjected`)
and G-DIFF (the prepatch, which restores the old derived disjunction, fails
exactly the discriminating clause). Precedent: django__django-11265,
django__django-11066, django__django-11451.
