# refinement.md — django__django-11066

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `resolveTarget` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-reference** (a
free-input model validated == the real callee by `axiom_check.py` / G-AX; there
is **no consumed axiom**), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The persist site — `RenameContentType._rename` (`management/__init__.py:13`)

Gold hunk (body lines 24-27):
```
             content_type.model = new_model
             try:
                 with transaction.atomic(using=db):
-                    content_type.save(update_fields={'model'})
+                    content_type.save(using=db, update_fields={'model'})
```

The single changed token is the addition of `using=db` to the `save(...)` call.
Inside `Model.save` / `Model.save_base` the write target is resolved as
`using = using or router.db_for_write(self.__class__, instance=self)`
(`django/db/models/base.py:761`). So the observable change is: *which database
alias the single-field UPDATE is committed to.*

| # | Solution.lean impl op (`resolveTarget`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `db : List Char`, `require db.length > 0` | `db = schema_editor.connection.alias` (`__init__.py:15`), passed as `using=db` | R | a connection alias `str` ↔ `List Char` of code points; `schema_editor.connection.alias` is always a present (non-empty) alias (mapping.md §2). |
| A2 | param `routed : List Char`, `require routed.length > 0` | the return of `router.db_for_write(ContentType, instance=content_type)` reached by the `or` in `save_base` (`base.py:761`) | A-reference | the routing policy's chosen alias is modeled as a **free input** (an arbitrary present alias), NOT a consumed axiom — the fix BYPASSES the router. Its one relied-on property (the policy may return an alias ≠ `db`) is validated against the real `ConnectionRouter.db_for_write` by `axiom_check.py` (G-AX); see mapping.md §3. |
| A3 | `src := if db.length > 0 then db else routed` | `using = using or router.db_for_write(...)` where the caller now sets `using = db` | I (under R) | the Python `or` resolution: an explicit (truthy/present) alias is used directly, else the router result. Post-patch `using = db` is present, so the resolution short-circuits to `db` — exactly the `db.length > 0 ⇒ src = db` branch. The truthiness of a present alias ↔ `db.length > 0` (mapping.md §2). |
| A4 | copy `src` into a fresh `result` (backward `while` + `drop`-step) and return it; postcondition `aliasEq out db` | the UPDATE is committed to the resolved alias (`= db`) — `content_type.save` writes the row to database `db` | R | the resolved alias IS the database the row lands in (`Model.save_base` opens the connection named by `using` and runs the UPDATE there). The result alias = `db` ⇔ the row is persisted to `db`. The F2P test observes precisely this (the renamed row appears in `'other'`, not `'default'`). The copy loop reproduces `src` exactly (`result = src.drop 0 = src`); the `drop`-step lemma discharges the loop. |

The discriminating content of the change lives in **A3**: post-patch the
explicit alias `db` is supplied, so the write target is `db`; pre-patch no
explicit alias is supplied, so the resolution always falls through to the
routing policy and the target is `routed`. `Solution_prepatch.lean` reproduces
the pre-patch resolution (`src := routed`, the `using or router.db_for_write(...)`
with `using = None`) and **fails** the postcondition `aliasEq out db` — exactly
the spec sensing the change (G-DIFF, confirmed: unsolved goal `result_1 = db` at
the `ensures_1: aliasEq out db` clause, because `result_1 = routed` and `routed`
is an unconstrained free input).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed
— *which alias resolves as the write target* — is modeled **deeply** (the `or`
resolution `src := if db.length > 0 then db else routed`, A3), not hidden behind
an axiom about the function under change. There is **no consumed axiom**: the
only callee in the resolution, `router.db_for_write`, is UNCHANGED and is
*bypassed* by the fix, so modeling its result as a consumed axiom would be a dead
axiom. It is instead an **A-reference** free input (`routed`), validated against
the real callee by G-AX (mapping.md §3).

## C. Read-only inputs / directive 5

Both inputs are read-only (the resolution never mutates an alias): neither `db`
nor `routed` is declared `mut`, so their post-states are trivially unchanged
(directive 5: an unmutated param needs no `mut` and no `ensures xOld = x`). The
result is a **fresh** list (built by the copy loop) at full ownership, so a wrong
impl cannot satisfy `aliasEq out db` by overwriting an input — it must *produce*
an alias whose code points equal `db`'s, and (because `routed` is an arbitrary
present alias unconstrained to equal `db`) the only way to do that for all
`routed` is to use the explicit alias `db` (A3). This is why the prepatch, which
returns `routed`, cannot verify.

## D. verify(Solution) ⇒ resolved

`resolveTarget` verifies only if its result alias equals `db` regardless of the
free `routed` input (the postcondition). By R (alias `str` ↔ `List Char`; the
resolved alias = the database the UPDATE commits to) and the A3 correspondence,
the verified resolution equals `using = db or router.db_for_write(...)` = `db`,
i.e. the gold `content_type.save(using=db, update_fields={'model'})`. By G-AX the
real `router.db_for_write` can return an alias ≠ `db` (so the bug surface is
real) and `Model.save(using=db, ...)` commits to `db` regardless of the router
(A-reference, mapping.md §3). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited callee
reference — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: refinement fidelity (this document, G-EQ) and the
callee reference soundness (G-AX); there is no consumed axiom.
