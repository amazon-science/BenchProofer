# mapping.md — django__django-11951

## Instance

- repo: django/django
- base_commit: 312049091288dbba2299de8d07ea3e3311ed7238
- changed file: `django/db/models/query.py`
- changed function: `QuerySet._batched_insert` (the effective-batch-size hunk)

## Model symbol ↔ repo symbol binding

| model.py symbol | repo symbol | repo location (base_commit) | binding |
|---|---|---|---|
| `effective_batch_size(requested, raw_backend_limit)` | the batch-size computation inside `QuerySet._batched_insert` | `django/db/models/query.py:1212` (the patched line) | The function abstracts the method down to the single arithmetic decision the patch changes: deriving the effective batch size from the caller request and the backend maximum. The surrounding method body (`NotSupportedError` guard at 1209-1210, `ops` lookup at 1211, the slicing loop at 1215-1228) is unchanged repo code and is not modeled. |
| `clamped_max(raw_backend_limit)` | `max(ops.bulk_batch_size(fields, objs), 1)` | `django/db/models/query.py:1212` (gold) / new line `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)` | Deep `@Pure` model of `max(<backend int>, 1)`. |
| `requested` parameter (`0` = auto, `>0` = explicit) | `batch_size` argument threaded from `bulk_create(objs, batch_size=None, ...)` | `django/db/models/query.py:438,458,478,490,1205` | `bulk_create` asserts `batch_size is None or batch_size > 0` (line 458), so the runtime truthiness `if batch_size` is `False` only for `None`. Modeled as `requested == 0` ↔ auto, `requested > 0` ↔ explicit positive. |
| `raw_backend_limit` parameter (`>= 0`) | return value of `connections[self.db].ops.bulk_batch_size(fields, objs)` | call at `django/db/models/query.py:1212` | An opaque non-negative backend integer; see callee provenance below. |

## Type abstraction

All quantities are ordinary Python `int`. No string/float modeling is required;
`float_encoding` is `null`. The abstraction is purely the integer arithmetic of
`min`/`max` selection. The `requested == 0` encoding of the absent/auto request
faithfully reproduces the patch's `if batch_size` truthiness split given
`bulk_create`'s `batch_size is None or batch_size > 0` assertion.

## Callee provenance (A-reference, NOT a consumed axiom)

`ops.bulk_batch_size(fields, objs)` is an UNCHANGED callee. The patch does not
modify it; it only wraps its result in `max(., 1)` and `min(batch_size, .)`.
The only property the model relies on is **it returns a non-negative integer**
(then `max(.,1)` makes the working maximum `>= 1`). This is validated by
`axiom_check.py` (G-AX) against the real backend implementations, NOT consumed
as a `@ContractOnly` axiom (its value enters the model only as an int input).

Real implementations at base_commit (all return a non-negative int):

- `django/db/backends/base/operations.py:68` — `return len(objs)` (`>= 0`).
- `django/db/backends/sqlite3/operations.py:27` — `500` if one field, else
  `max_query_params // len(fields)` (`>= 0`), else `len(objs)` (`>= 0`).
- `django/db/backends/oracle/operations.py:624` — backend-specific positive cap.

Doc evidence: the method docstring (base/operations.py:69-73) — "Return the
maximum allowed batch size for the backend." A maximum batch size is a count of
objects, hence a non-negative integer.

## Reference behavior the issue + F2P pin

The public problem statement asks that an explicit `batch_size` not override the
backend-compatible maximum, citing the already-correct `bulk_update` logic
`batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size`
(`django/db/models/query.py:523`). F2P
`test_explicit_batch_size_respects_max_batch_size` calls
`bulk_create(..., batch_size=max_batch_size + 1)` and asserts the query count is
`ceil(len(objs) / max_batch_size)` — achievable only if the effective batch size
is capped at `max_batch_size`, which is exactly
`effective_batch_size`'s postcondition `Result() <= clamped_max(raw_backend_limit)`.
