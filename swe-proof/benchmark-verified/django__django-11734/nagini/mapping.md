# mapping.md — django__django-11734

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 999891bd80b3d02dd916731a7a239e1036174885`, states the type
abstraction, and gives the provenance of the modelled decisions. **No
`@ContractOnly` axiom is consumed** by this bundle: both behaviours are pure,
fully-expressible integer/boolean decisions. The deep-model decisions are
validated against the real query-expression machinery by `axiom_check.py`
(G-AX, A-reference role).

Repo files under change:
* `django/db/models/sql/query.py`
* `django/db/models/fields/related_lookups.py`
* `django/db/models/fields/__init__.py`

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rebind_into_inner_subquery(rhs_kind)` | `Query.split_exclude(self, filter_expr, can_reuse, names_with_path)` — `django/db/models/sql/query.py:1685` (rewrite hunk at lines 1704–1706) | modeled changed function #1: how the original condition's right-hand side is re-anchored when carried into the freshly generated inner subquery |
| `normalize_only_concrete_value(rhs_kind)` | `RelatedLookupMixin.get_prep_lookup(self)` — `django/db/models/fields/related_lookups.py:103` (guard at line 104) | modeled changed function #2: whether the comparison's right-hand side is normalised through the relation's value coercion |
| `is_query_expression(kind)` | `hasattr(self.rhs, 'resolve_expression')` (post-patch guard, `related_lookups.py:104`) vs. the pre-patch `self.rhs_is_direct_value()` (`django/db/models/lookups.py:98`, `not hasattr(self.rhs, 'as_sql')`) | pure spec: a right-hand side is a query expression iff it can be resolved against a query |
| `target_level` / `resolved_level_in_inner` | the query-nesting semantics of `OuterRef.resolve_expression` (`django/db/models/expressions.py:565–570`) and `F.resolve_expression` (`expressions.py:529–531`) | pure spec: the query level a right-hand side denotes, before and after being carried into the inner subquery |
| `kind_value / kind_local / kind_outer` | a plain value; `F` (`expressions.py:516`); `OuterRef` (`expressions.py:565`) | the three relevant right-hand-side kinds (a small tagged domain) |

The third gold hunk — removal of `AutoField.get_prep_value`
(`django/db/models/fields/__init__.py:2335–2337`, the
`return value if isinstance(value, OuterRef) else super().get_prep_value(value)`
special case) — is **dead-code removal made safe by modeled function #2**: once
an `OuterRef` is no longer treated as a direct value in
`RelatedLookupMixin.get_prep_lookup`, it never reaches the auto-field's value
preparation, so the special case is unreachable and is removed. It introduces
no independently-observable behaviour of its own and so has no separate
prepatch (see refinement.md §C).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a right-hand-side object: a plain Python value, an `F`, or an `OuterRef` | an `int` tag `rhs_kind ∈ {0,1,2}` = `{value, local, outer}` | `value` ↔ no `resolve_expression`; `local` ↔ an `F` (`hasattr(resolve_expression)`, no `as_sql`); `outer` ↔ an `OuterRef` (subclass of `F`) |
| the number of `OuterRef`-wrapping hops applied when re-anchoring (`OuterRef(filter_rhs.name)` for an `F`; `OuterRef(filter_rhs)` for an `OuterRef`) | a non-negative `int` (the result of `rebind_into_inner_subquery`) | each hop wraps the value in one more `OuterRef`, shifting the level it denotes one step further out |
| the query nesting level a reference ultimately resolves to | a relative `int` level (original query = 0; one level out = -1; the generated inner subquery = +1) | follows `OuterRef.resolve_expression`: a bare `OuterRef` collapses one outward level (→ `ResolvedOuterRef`); an `OuterRef` whose `name` is itself an `OuterRef` preserves one outward level (resolves to the inner unresolved `OuterRef`) |
| `RelatedLookupMixin.get_prep_lookup`'s normalisation guard | a `bool` (the result of `normalize_only_concrete_value`) | `True` ⇔ run `get_normalized_value(...)` then the target field's value coercion; `False` ⇔ pass the right-hand side through untouched |

`str` is not used (no string content is touched); the entire behaviour is a
decision over the tagged integer domain, so no `str`/`PSeq` modelling is needed.

## 3. Decision provenance (checked by G-AX / axiom_check.py — A-reference)

There is **no consumed axiom**. The two decisions are validated against the
real Django classes:

### 3.1 `is_query_expression` ↔ `hasattr(rhs, 'resolve_expression')`
Post-patch, `RelatedLookupMixin.get_prep_lookup` guards normalisation with
`not isinstance(self.lhs, MultiColSource) and not hasattr(self.rhs, 'resolve_expression')`
(`related_lookups.py:104`). Both `F` and `OuterRef` define `resolve_expression`
(`expressions.py:529`, `:566`) but **not** `as_sql`, whereas a plain value
defines neither. The pre-patch guard used `self.rhs_is_direct_value()` =
`not hasattr(self.rhs, 'as_sql')` (`lookups.py:98`), which is `True` for `F`
and `OuterRef` (no `as_sql`) — i.e. it wrongly classified an expression as a
direct value and normalised it. `axiom_check.py` constructs real `F`,
`OuterRef`, and plain-value instances and asserts the classification matches
the model on every sample, and exhibits the pre-patch misclassification.

### 3.2 The inner-subquery re-anchor ↔ `OuterRef.resolve_expression`
`OuterRef.resolve_expression` (`expressions.py:566–570`):

```python
def resolve_expression(self, query=None, ...):
    if isinstance(self.name, self.__class__):
        return self.name
    return ResolvedOuterRef(self.name)
```

So:
* a bare `OuterRef(name)` resolves immediately to a `ResolvedOuterRef`
  (collapses one outward level);
* `OuterRef(OuterRef(name))` resolves to the *inner* `OuterRef` — still
  unresolved — preserving one outward level for a further resolution one query
  level up;
* an `F(name)` re-anchored as `OuterRef(name)` resolves to a `ResolvedOuterRef`
  (the originally-local reference now denotes one level out from the inner
  subquery, i.e. the original query).

These are exactly the "one extra outward hop for both a local reference and an
`OuterRef`" the model encodes (`rebind_into_inner_subquery` returns `1` for
`local` and `outer`, `0` for `value`; the post-condition ties this to
`resolved_level_in_inner − hops == target_level`). `axiom_check.py` exercises
the real `OuterRef`/`F`/`ResolvedOuterRef` objects to confirm the bare-vs-
wrapped resolution behaviour. Docs/source: Django `django/db/models/expressions.py`
at this base commit.

**Flag dependencies:** none. The behaviour does not depend on any optional flag
or DB backend; the resolution semantics are backend-independent Python.
