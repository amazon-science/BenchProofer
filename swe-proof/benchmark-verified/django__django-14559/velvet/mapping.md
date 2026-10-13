# mapping.md — django__django-14559

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d79be3ed39b76d3e34431873eec16f6dd354ab17`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `totalRowsMatched (matched : List Nat)` | `QuerySet.bulk_update(self, objs, fields, batch_size=None)` — `django/db/models/query.py:527` (changed lines 544, 566-570) | the modeled changed function (return the aggregate matched-row count) |
| `matched : List Nat` *(deep model — A-reference)* | the sequence of return values of `self.filter(pk__in=pks).update(**update_kwargs)`, one per batch — `django/db/models/query.py:568` post-patch | the per-batch matched-row counts produced by the unchanged callee `QuerySet.update()` |
| `totalMatched (matched : List Nat)` | the patched accumulation `rows_updated = 0; for ...: rows_updated += ...; return rows_updated` (`query.py:566-570` post-patch); empty-input fast path `return 0` (`query.py:544` post-patch) | pure spec: the running total of the per-batch counts |

The pre-patch repo behavior the change removes (refinement audit only, not in the
consumer spec view): `bulk_update` returned `None` — `return` with no value
(`query.py:544`) and a `for` loop that discarded each `update()` result
(`query.py:567`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a single `update()` return value (rows matched in one batch, a non-negative `int`) | Lean `Nat` | `n` (Python `int ≥ 0`) ↔ `(n : Nat)`; `update()` cannot return a negative count, so `Nat` is faithful (G-AX checks `update() ≥ 0`) |
| the ordered sequence of per-batch `update()` returns | `List Nat` | `[n₀, n₁, …]` (Python `list[int]`) ↔ `[n₀, n₁, …] : List Nat`; `len(seq)` ↔ `matched.length`; one batch ↔ one list element; batch *order* preserved (the loop walks `updates` in order) |
| `bulk_update`'s `int` return value (sum of the per-batch counts) | `Nat` | Python `int` total ↔ `(out : Nat)`; integer `+` ↔ `Nat` `+`; the empty-`objs` fast path `return 0` ↔ `totalMatched [] = 0` |

The per-batch count is `len(set(pks))` — the number of **distinct** primary keys
in that batch that exist in the DB (a duplicate object inside one batch is matched
once; a duplicate split across two batches is matched once per batch). This is
exactly why the F2P test observes `1` (both copies in one batch) vs `2` (one copy
per batch, `batch_size=1`). The model is order- and multiplicity-agnostic about
*how* each count arises: it sums whatever per-batch counts the callee reports,
which is the only behavior the change introduces.

## 3. Callee provenance

### 3.1 `matched` deep model ↔ `QuerySet.update()` (A-reference)
**Callee:** `django.db.models.query.QuerySet.update(**kwargs)` (`query.py:802`),
invoked as `self.filter(pk__in=pks).update(**update_kwargs)`. It is **unchanged**
by this patch. The change consumes only one property of it: each call returns a
non-negative `int` — the number of rows the `UPDATE … WHERE pk IN (…)` matched.
That value becomes one `Nat` element of `matched`. There is **no consumed axiom**:
the sole relied-upon property (non-negativity) is carried by the `Nat` type, and
the summation itself is modeled deeply by `totalMatched`. `update()` is therefore an
**A-reference** (deep-model reference), validated `update() == matched-row count ≥ 0`
by `axiom_check.py` (G-AX), NOT a consumed axiom.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory SQLite
Django and drives the **real** `QuerySet.update()` via `bulk_update`-shaped
`filter(pk__in=pks).update(...)` calls on boundary + fuzzed `pks` sets (empty,
singleton, duplicates, missing pks, large), asserting every observation is a
non-negative `int` equal to the number of distinct existing pks matched. Exit 0
iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14559`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `totalMatched` (the R/I-tagged accumulation) to Python (`sum` over the
per-batch counts) and leaves the per-batch count itself as produced by the
**real** patched `bulk_update` driving the real `QuerySet.update()` callee
(A-tagged → run real callee, not the model). The oracle is the real patched
`bulk_update` return value over fuzzed object lists × batch sizes (incl. the
duplicate-in-one-batch vs duplicate-across-batches F2P cases).
