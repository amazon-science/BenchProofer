# refinement.md — django__django-13590

Maps every operation in `implementation_resolveValue` to its `patch.diff`
counterpart in `Query.resolve_lookup_value` (django/db/models/sql/query.py:1071).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch resolve_lookup_value, list/tuple branch)
```python
elif isinstance(value, (list, tuple)):
    values = (
        self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
        for sub_value in value
    )
    type_ = type(value)
    if hasattr(type_, '_make'):  # namedtuple
        return type_(*values)
    return type_(values)
```

## Modeling decision
A value is one of three shapes (`Value`):
- `scalar` — no `resolve_expression`, not a sequence ⇒ returned unchanged;
- `expr id` — carries `resolve_expression` ⇒ replaced by `resolveExpr id`;
- `seq c elems` — a sequence with container kind `c ∈ {plain (list), tupleLike
  (plain tuple), special (namedtuple)}` ⇒ rebuilt element-wise.

The container kind is a 3-way tag (NOT a bool): the gold non-namedtuple branch
`type_(values)` preserves the EXACT container type, so `plain` and `tupleLike`
are kept distinct even though the fix routes both through the same constructor
form — this lets the spec pin the result's exact type (directive 5 frame
discipline). The rebuild resolves each element independently and reconstitutes a
sequence of the SAME kind and length. The fix's only behavioral content is that
the rebuild SUCCEEDS for the `special` (namedtuple) kind (pre-patch a namedtuple
could not be rebuilt from a single iterator and raised). The model captures this
as: post-patch resolution is total (`result = some _`) and equals the structural
`resolveRef`; the prepatch returns `none` for the `special` branch (the
`TypeError`).

`resolveExpr` (single-expression resolution) is universally quantified — the spec
holds for every expression resolver — so the proof consumes no property of it.

## Operation correspondence
| # | Lean op (`implementation_resolveValue`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `match v with \| .expr id => return some (resolveExpr id)` | `if hasattr(value, 'resolve_expression'): value = value.resolve_expression(...)` ⇒ return | R + A-reference | an expression is replaced by its resolved form; `resolveExpr` is the unchanged per-expression resolution, left abstract (universally quantified) in spec/proof and bound to a fixed real resolver in G-CONF. |
| 2 | `\| .seq c elems => let values := elems.map (resolveRef resolveExpr)` | `values = (self.resolve_lookup_value(sub_value, ...) for sub_value in value)` | R | resolve each element independently; `List.map resolveRef` ↔ the generator of recursively-resolved elements (`resolveRef` is the deep model of the recursive `resolve_lookup_value`). |
| 3 | `match c with \| .special => return some (.seq .special values) \| .plain => … \| .tupleLike => …` | `type_ = type(value); if hasattr(type_, '_make'): return type_(*values) else: return type_(values)` | R | rebuild a sequence of the SAME container kind and length; all three branches succeed. This is the FIX: the `.special` branch corresponds to the unpacking `type_(*values)` that namedtuples require (so rebuilding no longer raises), while `.plain`/`.tupleLike` correspond to `type_(values)` and are kept distinct to pin the exact result type. |
| 4 | `\| .scalar n => return some (.scalar n)` | `return value` (final fall-through) | I | a plain value is returned unchanged. |

The behavior-changing op is #3: pre-patch the rebuild was `type(value)(values)`
for ALL sequence types, which raised `TypeError` for a namedtuple (its
constructor needs unpacked positional args, not a single iterator). The prepatch
impl encodes this by returning `none` for the `.special` branch (modeling the
exception) while `.plain`/`.tupleLike` still succeed, whereas the post-patch spec
forces `result = some (.seq .special …)`.

## R/I legs ⇒ G-CONF
Ops 1–4 are all R/I/A-reference content (a genuine rebuild computation), so
`conf_skip = false`. G-CONF builds the Python shadow of
`implementation_resolveValue` (the structural resolve-and-rebuild, with
`resolveExpr` bound to a fixed real resolver) and differential-tests it against
the REAL patched `Query.resolve_lookup_value` over ≥10^5 fuzzed values including
nested scalars / expressions / lists / tuples / namedtuples.

## No A-consumed row
The proof consumes no property of `resolveExpr` (it is universally quantified),
so `meta.json axioms = []`. The per-expression resolution and the real
`resolve_lookup_value` rebuild are recorded as A-references solely to document
the G-CONF binding; there is no `opaque`/`axiom` declaration in `Solution.lean`
and `axiom_check.py` is a skip stub.

## F2P alignment
- `test_range_lookup_namedtuple` builds a `namedtuple` `EmployeeRange(minimum=51,
  maximum=100)` and uses it as a `__range` argument. Post-patch
  `resolve_lookup_value` must rebuild the namedtuple successfully (each field
  resolved, repacked via `_make`-style unpacking) so the query runs. The spec
  pins `result = some (.seq .special …)` for the `.special` branch — the prepatch
  impl returns `none` there (the `TypeError`), so it cannot satisfy the
  discriminating clause.
`patch.diff` (gold verbatim) makes the harness resolve.
