# mapping.md — django__django-11066

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4b45b6c8e4d7c9701a332e80d3b1c84209dc36e2`, states the type
abstraction, and gives the provenance of the one referenced callee.

Repo file under change:
`django/contrib/contenttypes/management/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveTarget (db routed : List Char)` | the persist step of `RenameContentType._rename` — `django/contrib/contenttypes/management/__init__.py:13` (body lines 24-27: `content_type.model = new_model; with transaction.atomic(using=db): content_type.save(...)`) | the modeled changed function: resolves which database alias the single-field write is actually committed to |
| `db` (param) | `db = schema_editor.connection.alias` — `__init__.py:15` | the explicitly-named connection alias for this migration step (always a present, non-empty alias) |
| `routed` (param) | the return of `router.db_for_write(ContentType, instance=content_type)` — the write-routing policy's chosen alias, consulted by `Model.save_base` at `django/db/models/base.py:761` (`using = using or router.db_for_write(...)`) | the alias an external routing policy would pick when the save is given no explicit alias; an arbitrary present alias, NOT constrained to equal `db` |
| `aliasEq a b` | string equality of two connection aliases | pure spec: two aliases denote the same database iff their code-point sequences are equal |
| `out` (return) | the database the single-field UPDATE is committed to (the store named by the resolved alias) | the resolved write target |

The pre-patch repo expression the change fixes (for the refinement audit, not
referenced from the consumer spec view): `content_type.save(update_fields=...)`
called with **no** explicit alias, so `Model.save_base` resolves the write
target via `using = using or router.db_for_write(...)` = `routed`. The gold
patch passes `using=db`, so the resolution short-circuits to `db`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a database connection alias (`str`, e.g. `'default'`, `'other'`) | `List Char` of code points; alias equality via `aliasEq` | `alias[k]` ↔ the k-th code point (Lean `List Char` indexing is total and sound — no `List Int` workaround needed); `len(alias)` ↔ `(alias : List Char).length`; alias string equality ↔ `List Char` equality (`aliasEq a b := a = b`) |
| `schema_editor.connection.alias` (always a real, non-empty alias string) | `db : List Char` with `db.length > 0` (`require`) | a connection's alias is a non-empty key in `settings.DATABASES` / the connections handler |
| the truthiness test inside `using = using or router.db_for_write(...)` (`base.py:761`) | `db.length > 0` — a present alias is truthy; `None` / `''` (absent) is falsy and falls through to the routing policy | Python `or`: `using` if `using` is truthy else the router result; modeled as `if db.length > 0 then db else routed` |
| `router.db_for_write(...)` return | `routed : List Char` — a free input parameter standing for the routing policy's chosen alias (an arbitrary present alias), `routed.length > 0` | see §3: the routing policy may pick ANY configured alias, not necessarily `db` |
| the resolved alias = the database the UPDATE lands in | `out : List Char`, freshly built (copy loop) at full ownership | `Model.save_base` opens the connection named by `using` and runs the UPDATE there; the resolved alias IS the store the row lands in |

Lean `List Char` indexing is total and sound, so aliases are carried directly as
code-point lists (no `List Int` Nagini workaround); alias equality is `aliasEq`.

## 3. Callee provenance — `routed` ↔ `router.db_for_write` (A-reference)

**Callee:** `django.db.utils.ConnectionRouter.db_for_write(model, **hints)`
(`django/db/utils.py`, the generic `_router_func('db_for_write')`), consulted by
`Model.save_base` at `django/db/models/base.py:761`:

```python
using = using or router.db_for_write(self.__class__, instance=self)
```

It is an **unchanged** callee. The gold patch does NOT change it; it changes the
*caller* so an explicit `using=db` is supplied and the `or` never reaches the
router. Therefore there is **no consumed axiom** in `Solution.lean` — modeling
the router's result as a consumed axiom would be a dead axiom (the fix bypasses
the router). Instead the router's return is modeled as the **free input
parameter `routed`**, tagged **A-reference** in refinement.md: a behavioural
reference whose only relied-on property is the one that makes the bug
observable —

> a write-routing policy is free to return an alias **different from** the
> explicitly named `db` (it is the application's `DATABASE_ROUTERS` policy,
> wholly independent of the alias the migration step is operating on).

This is exactly what the F2P test exercises: `TestRouter.db_for_write` returns
`'default'` while the migration step's `db` is `'other'`, so a save with no
explicit alias is routed to `'default'` (the wrong database) and the renamed row
never lands in `'other'`.

**Soundness check (G-AX, `axiom_check.py`):** because `routed` is a free input
(no consumed axiom to over-approximate), the check validates the *reference
property* directly against the real routing machinery — it constructs a
`ConnectionRouter` over a router whose `db_for_write` returns a fixed alias and
asserts `router.db_for_write(...)` returns that alias unchanged (so the policy
can and does return an alias independent of, and different from, the step's
`db`). It also asserts the dual: the real resolution
`using or router.db_for_write(...)` short-circuits to `db` when `using=db` is
supplied (gold) and to the router's choice when `using=None` (pre-patch),
matching `resolveTarget`'s `src = db` branch and the prepatch's `src = routed`.
stdlib + `django.db` only; exit 0 iff sound.

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The impl region resolves *which
database alias the single-field UPDATE is committed to* — a live DB
write-routing side effect with no DB-free, input-dependent R/I shadow. The only
observable (the renamed row appearing in the resolved database) materializes
only after `content_type.save(using=db, ...)` opens the connection named by
`using` and runs the UPDATE there, inside `transaction.atomic(using=db)`;
reproducing it requires two real databases + a `DATABASE_ROUTERS` policy + a
`migrate` call — i.e. the F2P integration test itself
(`test_existing_content_type_rename_other_database`). The resolution's R/I
content reduces, once an explicit present alias is supplied, to the constant
`db`, so there is no input-dependent computation on alias contents to refute;
the discriminating fact is the BRANCH taken (explicit vs router fallback), which
is exercised only by the live save/router machinery and covered by G-AX.

Per SPEC_GUIDE §0 / WORKER_PROMPT, soundness is carried instead by **G-VERIFY**
(the spec provably forces the resolved alias to equal `db` for an arbitrary
routing-policy choice `routed`), **G-DIFF** (the prepatch, which falls through to
`routed`, fails exactly the `aliasEq out db` clause — see refinement.md §B), and
**G-AX** (axiom_check.py validates the A-reference against the real routing
machinery).
