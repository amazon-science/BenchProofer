# refinement.md — django__django-11951

Operation-by-operation correspondence between `model.py`'s impl region and
`patch.diff` (the gold patch). The patched hunk is the two lines that compute
the effective batch size inside `_batched_insert`:

```
-        batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))
+        max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
+        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
```

The model abstracts the surrounding method (`_batched_insert`) to the single
arithmetic decision the patch changes: computing the effective batch size from
(a) the caller-requested size and (b) the backend-reported maximum. Everything
the patch does NOT touch (the `NotSupportedError` guard, `ops` lookup, the
slicing loop, the per-batch `_insert` calls, `inserted_rows`) is outside the
modeled behavior and is not represented — it is unchanged repo code.

## Carrier-type abstraction

| repo value | model value | note |
|---|---|---|
| `batch_size` (`None` or a positive `int`; `bulk_create` asserts `batch_size is None or batch_size > 0`) | `requested: int`, with `0` modelling the `None`/auto case and `requested > 0` the explicit case | The Python truthiness test `if batch_size` is `False` iff `batch_size is None` (the assertion forbids `0`), so the `requested == 0` ↔ `requested > 0` split is exactly the patch's `if batch_size` branch split. |
| `ops.bulk_batch_size(fields, objs)` (a backend `int >= 0`) | `raw_backend_limit: int >= 0` | An opaque non-negative backend integer; see mapping.md provenance. |
| `max_batch_size = max(<backend>, 1)` | `clamped_max(raw_backend_limit)` (deep `@Pure` model) | identical integer `max(., 1)`. |
| effective `batch_size` after the hunk | `Result()` of `effective_batch_size` | the value that drives `range(0, len(objs), batch_size)`. |

## Op correspondence

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `max_batch_size = clamped_max(raw_backend_limit)` | `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)` | R | `clamped_max(n)` is the deep model of `max(n, 1)` over a non-negative int; same integer operation, refined only by replacing the opaque `bulk_batch_size(...)` call with its non-negative-int result (see row 2). |
| 2 | `raw_backend_limit` (parameter, `>= 0`) | `ops.bulk_batch_size(fields, objs)` | A-reference | `bulk_batch_size` is an UNCHANGED callee; the patch does not alter it. Its only relied-on property is "returns a non-negative integer" (the `max(.,1)` clamp then makes it `>= 1`). Validated against the real backend implementations by `axiom_check.py` (G-AX). It is NOT a consumed `@ContractOnly` axiom — its value enters the model only as an integer input, so there is no axiom whose `Ensures` the proof discharges. |
| 3 | `if requested > 0:` … `else:` | `... if batch_size else ...` | R | The model's `requested > 0` test is the refinement of the Python truthiness `if batch_size`: under `bulk_create`'s `assert batch_size is None or batch_size > 0`, `batch_size` is truthy iff `batch_size > 0`, mapped to `requested > 0`; `None` (auto) maps to `requested == 0` (falsy). Same branch. |
| 4 | `if requested < max_batch_size: result = requested else: result = max_batch_size` | `min(batch_size, max_batch_size)` | I | This is exactly `min(requested, max_batch_size)`: returns `requested` when strictly smaller, else `max_batch_size` (equal case yields the common value). Same integer minimum. |
| 5 | `else: result = max_batch_size` (the `requested == 0` branch) | `else max_batch_size` (the `if batch_size` false branch) | I | identical: the auto case uses the backend maximum directly. |
| 6 | `return result` | (the value bound to `batch_size`, consumed by the slicing loop) | R | the effective batch size produced; the loop downstream is unchanged repo code, not modeled. |

Every step is R, A-reference, or I. There is NO kind-3 (changed-but-inexpressible)
step: the changed operation is plain integer `min`/`max` selection, modeled
deeply and exactly (rows 1, 4, 5). There are NO consumed axioms.

## Why the spec sees the bug (G-DIFF)

`model_prepatch.py` reverts row 4+5 to the buggy `batch_size or max(...)`
behavior: an explicit `requested > 0` is used as-is, ignoring `max_batch_size`.
It fails verification on the postcondition
`Result() <= clamped_max(raw_backend_limit)` — precisely the case an over-large
explicit request (`requested > max_batch_size`) is not tightened down. This is
exactly the F2P test `test_explicit_batch_size_respects_max_batch_size`, which
calls `bulk_create(..., batch_size=max_batch_size + 1)` and asserts the number
of queries is `ceil(len(objs) / max_batch_size)` — only achievable if the
effective batch size is capped at `max_batch_size`.
