# refinement.md — django__django-12050

Correspondence between `Solution.lean`'s `resolveSeq` impl and `patch.diff` (the
gold patch reassembles a resolved sequence preserving its container type).
`patch.diff` is the gold verbatim (applies at
`base_commit = b93a0e34…`, resolves — G-RESOLVE).

## A. The type-preserving reassembly — `Query.resolve_lookup_value`

Gold hunk (post-patch), the `elif isinstance(value, (list, tuple)):` arm:
```python
return type(value)(
    self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col)
    for sub_value in value
)
```
Pre-patch (buggy):
```python
resolved_values = []
for sub_value in value:
    ...                              # resolve each sub_value independently
    resolved_values.append(...)
value = tuple(resolved_values)       # <-- coerces ANY input (incl. list) to tuple
```

| # | Solution.lean impl op (`resolveSeq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value : SeqVal` (`kind`, `elems`) | the `value` bound in the `(list, tuple)` arm | R | runtime container type ↔ `kind` (`list`↔`SeqKind.list`, `tuple`↔`SeqKind.tuple`); ordered sub-values ↔ `elems` (mapping.md §2). |
| A2 | `let resolvedElems := value.elems.map resolveElem` | `self.resolve_lookup_value(sub_value, …) for sub_value in value` | A-reference | per-element resolution is UNCHANGED by the patch; modeled deeply as the opaque `resolveElem` applied element-wise, order/count preserved. Validated by being the SAME map on both legs (cancels in G-CONF). No value pinned. |
| A3 | `return { kind := value.kind, elems := resolvedElems }` | `return type(value)(…)` | **I** | the type-preserving reassembly: `type(value)(gen)` builds a container of the SAME type as the input ↔ `out.kind = value.kind`. This is the load-bearing fix. |

Every step is R, A-reference, or I. No A-consumed (no consumed axiom); no kind-3
(changed inexpressible) steps — `type(value)(…)` is expressed precisely as
`out.kind = value.kind`.

### A-tagging of the per-element resolution
`resolveElem` is an **A-reference**, not a consumed axiom: it deep-models the
unchanged recursive sub-call. The patch does not touch it, so both legs apply
the identical map; the spec pins only that the SAME map is applied to every
element in order (`out.elems = value.elems.map resolveElem`), never any concrete
output. Because it is opaque (no value-level contract claimed), there is no
checked-axiom obligation and hence no `axiom_check.py` (WORKER_PROMPT: keep
`resolveElem` opaque ⇒ no axiom_check).

## B. verify(Solution) ⇒ resolved

`resolveSeq` verifies only if both `ensures` hold:
* `out.kind = value.kind` — a sequence of one kind comes back as the SAME kind:
  a `list` input yields a `list`, a `tuple` input yields a `tuple`. This is
  precisely the behavior the issue + F2P test `test_iterable_lookup_value`
  demand: `Q(name=['a', 'b'])` builds an `Exact` whose `rhs` is the *list*
  `"['a', 'b']"`, not a coerced tuple — exact value queries on type-dependent
  fields (e.g. PickledField) must preserve the input iterable type.
* `out.elems = value.elems.map resolveElem` — every sub-value is resolved
  independently, in order, count unchanged (the pre-existing element-resolution
  behavior the PASS_TO_PASS tests rely on).

By the R bijection (mapping.md §2) the verified result corresponds to the
patched arm: `type(value)(resolved sub-values)`. The prepatch impl
(`return { kind := SeqKind.tuple, elems := … }`) forces the kind to `tuple`
UNCONDITIONALLY — exactly the gold pre-patch `value = tuple(resolved_values)`.
It fails the `out.kind = value.kind` clause (G-DIFF) whenever the input is a
`list` — the observable of the "coerces list to tuple" bug the issue reports.
The element clause still holds in the prepatch (elements were always resolved
correctly), so G-DIFF isolates the discriminator to the kind, matching the bug
precisely. No trust points beyond the type bijection and the A-reference (no
consumed axioms).
