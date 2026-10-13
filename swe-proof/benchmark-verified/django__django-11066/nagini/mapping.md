# mapping.md — django__django-11066

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4b45b6c8e4d7c9701a332e80d3b1c84209dc36e2`, states the type
abstraction, and gives the provenance of the one referenced callee.

Repo file under change:
`django/contrib/contenttypes/management/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `persisted_db(db, routed)` | the persist step of `RenameContentType._rename` — `django/contrib/contenttypes/management/__init__.py:13` (the body lines 24-27: `content_type.model = new_model; with transaction.atomic(using=db): content_type.save(...)`) | the modeled changed function: resolves the database alias the single-field write is actually committed to |
| `db` (param) | `db = schema_editor.connection.alias` — `__init__.py:15` | the explicitly-named connection alias for this migration step (always a present, non-empty alias) |
| `routed` (param) | the return of `router.db_for_write(ContentType, instance=content_type)` — the write-routing policy's chosen alias, consulted by `Model.save_base` at `django/db/models/base.py:761` (`using = using or router.db_for_write(...)`) | the alias an external routing policy would pick when the save is given no explicit alias; an arbitrary present alias, NOT constrained to equal `db` |
| `alias_eq(a, b)` | string equality of two connection aliases | pure spec: two aliases denote the same database iff their code-point sequences are equal |

The pre-patch repo expression the change fixes (for the refinement audit, not
referenced from the consumer spec view): `content_type.save(update_fields=...)`
called with **no** explicit alias, so `Model.save_base` resolves the write
target via `using = using or router.db_for_write(...)` = `routed`. The gold
patch passes `using=db`, so the resolution short-circuits to `db`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a database connection alias (`str`, e.g. `'default'`, `'other'`) | `List[int]` of Unicode code points; specification over `PSeq[int]` via `ToSeq` | `alias[k]` ↔ `ord(str_alias[k])`; `len(alias)` ↔ `len(str_alias)`; alias string equality ↔ `PSeq` equality (`alias_eq`) |
| `schema_editor.connection.alias` (always a real, non-empty alias string) | `db: List[int]` with `len(db) > 0` (precondition) | a connection's alias is a non-empty key in `settings.DATABASES` / the connections handler |
| the truthiness test inside `using = using or router.db_for_write(...)` (`base.py:761`) | `len(explicit_alias) > 0` — a present alias is truthy; `None` / `''` (absent) is falsy and falls through to the routing policy | Python `or`: `using` if `using` is truthy else the router result |
| `router.db_for_write(...)` return | `routed: List[int]` — a free input parameter standing for the routing policy's chosen alias (an arbitrary present alias) | see §3: the routing policy may pick ANY configured alias, not necessarily `db` |

`str` indexing/iteration is banned in Nagini, so aliases are carried as
`List[int]`; alias equality is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance — `routed` ↔ `router.db_for_write` (A-reference)

**Callee:** `django.db.utils.ConnectionRouter.db_for_write(model, **hints)`
(`django/db/utils.py:247-260`, the generic `_router_func('db_for_write')`),
consulted by `Model.save_base` at `django/db/models/base.py:761`:

```python
using = using or router.db_for_write(self.__class__, instance=self)
```

It is an **unchanged** callee. The gold patch does NOT change it; it changes
the *caller* so that an explicit `using=db` is supplied and the `or` never
reaches the router. Therefore there is **no `@ContractOnly` axiom** in model.py
that the proof consumes — modeling the router's result as a consumed axiom
would be a dead axiom (the fix bypasses the router). Instead the router's
return is modeled as the **free input parameter `routed`**, tagged
**A-reference** in refinement.md: a behavioural reference whose only relied-on
property is the one that makes the bug observable —

> a write-routing policy is free to return an alias **different from** the
> explicitly named `db` (it is the application's `DATABASE_ROUTERS` policy,
> wholly independent of the alias the migration step is operating on).

This is exactly what the F2P test exercises: `TestRouter.db_for_write` returns
`'default'` while the migration step's `db` is `'other'`, so a save with no
explicit alias is routed to `'default'` (the wrong database) and the renamed
row never lands in `'other'`.

**Soundness check (G-AX, `axiom_check.py`):** because `routed` is a free input
(no `@ContractOnly` to over-approximate), the check validates the *reference
property* directly against the real routing machinery: it constructs a
`ConnectionRouter` over a router whose `db_for_write` returns a fixed alias
(`'default'`) and asserts that `router.db_for_write(...)` indeed returns that
alias unchanged — i.e. the routing policy can and does return an alias
independent of, and different from, the migration step's `db` (`'other'`). It
also asserts the dual: `Model.save(using=db, ...)` resolves its write target to
`db` regardless of the router (the `using = using or router.db_for_write(...)`
short-circuit on a truthy `using`). stdlib + django.db only; exit 0 iff sound.
