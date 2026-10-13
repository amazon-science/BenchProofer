# mapping.md — django__django-14122

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bc04941bf811d1ea2c79fb7fc20457ed2c7e3410`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `groupingColumns (...)` | `SQLCompiler.get_group_by(self, select, order_by)` — `django/db/models/sql/compiler.py:63` (changed accumulation block lines 120–135; changed guard line 128) | the modeled changed function: assembles the column list a row-grouping clause must contain |
| `groupingSet (...)` | the `expressions` accumulation in `get_group_by` (compiler.py:120–135), as observed AFTER de-duplication | pure spec: the four contributions concatenated under the `metaOrdering` guard |
| `orderFold (...)` | the loop `for expr, (sql, params, is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())` (compiler.py:128–135 post-patch) | pure spec: the columns the ordering terms contribute (reference terms contribute nothing) |
| `OrderTerm.cols` | `expr.get_group_by_cols()` for one `order_by` entry | the columns one ordering term would contribute (taken as an explicit input — see §3) |
| `OrderTerm.isRef` | the `is_ref` element of the `order_by` 4-tuple `(expr, (sql, params, is_ref))` | whether the ordering term is a bare reference back into the SELECT set |
| `metaOrdering` (param) | `self._meta_ordering` — set in `get_order_by` (compiler.py:288) to the model's `Meta.ordering` when the ordering is derived from it; `None` otherwise (compiler.py:41) | the changed guard: truthy ⇔ the ordering came from the model default, not an explicit request |

The unchanged downstream steps of `get_group_by` not in the consumer spec view
(modeled as R-identity on which columns are present — §2): `collapse_group_by`
(compiler.py:148, primary-key collapsing), the `self.compile` / `select_format`
rendering, and the `(sql, params_hash)` de-duplication loop (compiler.py:136–146).
None of these is touched by the patch; all preserve the *set* of grouping
columns the F2P test observes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a grouping/column expression (a `Col`/expression object) | `Int` | each distinct expression ↔ a distinct identifier; observable equality is membership in the produced grouping set (the F2P test groups by these columns) |
| `self.query.group_by` base expressions (a list) | `baseCols : List Int` | the expressions appended directly from the group-by base (compiler.py:120–124); list ↔ `List Int`, `append` ↔ `++` |
| the per-select-expr `get_group_by_cols()`, already pruned of `Ref` sources | `selectCols : List Int` | the columns the SELECT clause contributes (compiler.py:113–119); references into the select set are dropped by the caller (`ref_sources` skip), so `selectCols` is the post-prune list |
| one `order_by` entry `(expr, (sql, params, is_ref))` | `OrderTerm { cols, isRef }` | `cols ↔ expr.get_group_by_cols()`, `isRef ↔ is_ref` |
| `self.having.get_group_by_cols()` (or `()`) | `havingCols : List Int` | the columns the HAVING predicate contributes (compiler.py:135–138); empty `having` ↔ `[]` |
| `self._meta_ordering` (a list, or `None`) | `metaOrdering : Bool` | truthy (a non-empty ordering list) ↔ `true`; `None`/falsy ↔ `false`. The F2P test exercises `true` (ordering from `Meta.ordering`). |
| `collapse_group_by` + the `(sql, params_hash)` de-dup loop | identity on the column *set* | unchanged downstream; observationally the identity on *which* columns group. G-CONF therefore compares the column SET, not the list (order/duplicates do not change grouping semantics). |

The result list's order and duplicates are not observable: SQL `GROUP BY` is a
set, and the test asserts the aggregation counts, which depend only on which
columns group. G-CONF compares `set(...)` on both sides accordingly.

## 3. Callee provenance — no consumed axioms, no deep-model reference

`get_group_by`'s per-term column lists (`expr.get_group_by_cols()`) and the
`is_ref` flag are **not recomputed** by the model: they are taken as the
method's explicit, observable inputs (`OrderTerm.cols`, `OrderTerm.isRef`,
`selectCols`, `baseCols`, `havingCols`), exactly as `django__django-11163` takes
the editable field names as inputs and `django__django-16263` takes the
structural-trigger flags as inputs. The modeled change — gating the ordering
contribution behind `not self._meta_ordering` — is decision algebra over those
inputs, modeled **deeply** (the `orderFold` fold and the `groupingSet` guard).
There is therefore:

* **no consumed `axiom`** — the proof assumes no callee contract; and
* **no A-reference deep model** — `get_group_by_cols` is not re-encoded, so
  there is nothing for G-AX to validate against a real callee.

Hence `axiom_check.py` is omitted and `meta.json gates.G-AX.status = "skip"`
(`no axioms in bundle`), as in `django__django-11163`. The R/I decision algebra
is differential-tested end-to-end against the **real patched** `get_group_by`
(run in-container) by `conformance_check.py` (G-CONF).

**Flag dependency (for G-CONF):** the behavioural switch is `self._meta_ordering`.
It is truthy precisely when `get_order_by` fell through to `self.query.get_meta().ordering`
(compiler.py:284–288) — i.e. the ordering was the model's default, not an
explicit `.order_by(...)` / `extra_order_by` / non-default request. G-CONF
fuzzes both polarities.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14122`** so the
consumer-side verdict is reproducible. The shadow transliterates
`orderFold`/`groupingSet` (R/I-tagged ops) to Python; the oracle runs the
**real** in-container `SQLCompiler.get_group_by` (gold patch applied by the
harness) over a duck-typed compiler, capturing the produced grouping-column set.
