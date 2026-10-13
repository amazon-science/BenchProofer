# mapping.md — django__django-12050

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b93a0e34d9b9b99d41103782b7e7aeabf47517e3`, states the type
abstraction (the Lean↔Python bijection used by G-CONF + G-AX), and records the
pinned fuzz seed.

Repo file under change: `django/db/models/sql/query.py`.
Changed method: `Query.resolve_lookup_value(self, value, can_reuse, allow_joins, simple_col)`
(`query.py:1054`; the touched branch is `query.py:1059–1069` post-patch — the
`elif isinstance(value, (list, tuple)):` arm).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveSeq (value : SeqVal)` | the `elif isinstance(value, (list, tuple)):` arm of `Query.resolve_lookup_value` — `query.py:1059–1071` | the modeled changed behavior: resolve a sequence input, reassembling it preserving its container type |
| `SeqVal.kind : SeqKind` | the runtime type of `value` (`list` vs `tuple`) | which container kind the input is |
| `SeqVal.elems : List Int` | the ordered sub-values of `value` | the elements to resolve independently |
| `resolveElem : Int → Int` | the per-sub-value step: the recursive `self.resolve_lookup_value(sub_value, …)` call on a scalar sub-value (pre-patch: the `hasattr(sub_value,'resolve_expression')` / `F` dispatch) | the UNCHANGED per-element resolution (A-reference) |
| `out : SeqVal` | the returned value of the arm | the reassembled sequence: `out.kind` = container type, `out.elems` = resolved elements |

No callee is consumed as a contract. The per-element resolution is modeled
deeply as the opaque total map `resolveElem` and is an **A-reference** (the same
map is applied element-wise on both sides; its concrete result is never pinned),
not a consumed axiom.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| runtime container type of `value` | `SeqKind` (`list` / `tuple`) | python `list` ↔ `SeqKind.list`; python `tuple` ↔ `SeqKind.tuple`. `DecidableEq` matches Python `type(value) is list` / `is tuple`. |
| the sub-values of `value` | `List Int` | an ordered, finite sequence of resolvable sub-values; `Int` stands for an opaque resolvable element (the element type is irrelevant to the fix — only the count/order and the container kind matter). |
| `type(value)(gen)` reassembly | `{ kind := value.kind, elems := … }` | constructing a fresh container of the SAME type as the input ↔ `out.kind = value.kind`. The fix's `type(value)(…)` is exactly "kind is preserved". |
| `self.resolve_lookup_value(sub_value, …)` per element | `resolveElem` applied element-wise | the per-element map; `out.elems = value.elems.map resolveElem` ↔ each sub-value resolved independently, in order, count unchanged. |

The pre-patch bug `value = tuple(resolved_values)` corresponds to discarding
`value.kind` and forcing the result kind to `SeqKind.tuple` — modeled in
`Solution_prepatch.lean` as `return { kind := SeqKind.tuple, … }`, which
violates `out.kind = value.kind` exactly when the input is a `list`.

## 3. Callee provenance

`resolveElem` ← the recursive per-sub-value resolution
`self.resolve_lookup_value(sub_value, …)` (pre-patch: dispatch on
`hasattr(sub_value,'resolve_expression')` and `isinstance(sub_value, F)`). This
step is UNCHANGED by the patch — both pre- and post-patch resolve each element
the same way; the patch only changes how the resolved elements are reassembled
into a container. It is therefore an **A-reference** (modeled deeply, opaque):
the SAME map is applied to every element on both legs and cancels in the G-CONF
diff, so the discriminating observable is purely the container kind. No exact
output value is pinned, so no soundness is borrowed; there is no consumed axiom
and hence no `axiom_check.py` (keeping `resolveElem` opaque means there is no
checked-axiom contract to validate — see WORKER_PROMPT: opaque ⇒ no axiom_check).

## 4. G-CONF fuzz

Seed **12050**, `N_FUZZ = 100_000`, stdlib-only, no Django/DB/Docker. The oracle
exercises the REAL `type(value)(gen)` construction in-process (it needs no
Django): for a `list` input it returns a `list`, for a `tuple` input a `tuple`.
The shadow asserts `shadow_resolve_kind(input_is_list) == isinstance(rebuilt,
list)` (type preservation) and that the element map is order-preserving. Fuzzes
list vs tuple inputs of varying length plus the empty / singleton / 50-element
boundaries. Exit 0 iff zero disagreements.
