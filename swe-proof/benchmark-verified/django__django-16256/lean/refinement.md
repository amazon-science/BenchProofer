# refinement.md — operation correspondence (django__django-16256)

Modeled function: `scopedOp` — the abstract async collection operation on a
*scoped* related manager (the fix's `acreate` / `aget_or_create` /
`aupdate_or_create`). All three share one control-flow skeleton: force the
manager's scope bindings into the caller kwargs, then run the underlying data
operation on the effective argument map. The fix makes each async method route
through the *related manager's own* sync method (which performs the binding
merge) instead of the bare `QuerySet` method (which does not). The single
observable behavior modeled is the **binding merge**.

## Type refinement (mapping.md has the bijection)
- Python insertion-ordered `dict[str, obj]` kwargs  <->  Lean `List (String x Int)`
  association list, `List.lookup` = first-occurrence read (matches dict read).
- Scope bindings (`{field.name: instance}` for FK/M2M; `{content_type_field:
  ct, object_id_field: pk}` for generic) <-> `bindings : List (String x Int)`
  with distinct keys (`(bindings.map Prod.fst).Nodup`, the precondition binder).
- Object identity (`instance`, `content_type`, `pk`) <-> `Int` value id.

## Operation table

| # | `implementation_scopedOp` op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `let mut out := kwargs` | async method receives `**kwargs` (caller args) | I |
| 2 | `for b in bindings do out := kwUpsert out b.1 b.2` | the sync method it now delegates to sets each scope key: `kwargs[self.field.name] = self.instance` (FK/reverse) / `kwargs[self.content_type_field_name]=...; kwargs[self.object_id_field_name]=...` (generic) — a dict assignment per binding | R |
| 3 | `return out` (effective map) -> data op | effective kwargs passed to `super().create/get_or_create/update_or_create` | I |

- **Row 2 is R**, not A: `kwUpsert` deeply models Python dict assignment
  (`d[k]=v`: replace-first-else-append; `List.lookup` first-occurrence read).
  No callee is axiomatized — there is NO A-consumed and NO A-reference row.
- The underlying data operation (`super().create(...)` etc.) is the same in the
  pre- and post-fix code; the ONLY changed behavior is *which kwargs it sees*.
  The spec pins exactly that (effective map), so it is not modeled as a callee.

## Discriminating clause (G-DIFF)
Pre-fix, the async method delegated to the bare `QuerySet` op, so the scope
bindings were never merged — the effective map was just `kwargs`. Prepatch impl
`return kwargs` fails `problem_spec_scopedOp`'s first conjunct
(`result.lookup b.1 = some b.2` for a scope key absent from `kwargs`), so its
carried gold proof does not typecheck. One prepatch suffices: all three ops
share the single merge behavior.
