# mapping.md — django__django-13590

## Instance
- repo: django/django
- base_commit: 755dbf39fcdc491fe9b588358303e259c7750be4
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`Query.resolve_lookup_value(self, value, can_reuse, allow_joins)`
(django/db/models/sql/query.py:1071–1084 @ base_commit) resolves a filter lookup
value. It dispatches on the value's shape:

- if the value carries a `resolve_expression` method, it is replaced by its
  resolved form and returned;
- if the value is a `list` or `tuple`, each element is resolved independently and
  a new container of the SAME type is rebuilt from the resolved elements;
- otherwise the value is returned unchanged.

At base_commit the rebuild is `return type(value)(<generator of resolved
elements>)` — the container type's constructor is handed a single iterator. This
works for `list`/`tuple` (their constructors consume an iterable) but FAILS for a
`namedtuple` subtype: a namedtuple's `__new__` takes one positional argument per
field, so passing it a single generator raises
`TypeError: __new__() missing 1 required positional argument`. The gold patch
detects the namedtuple case (`hasattr(type_, '_make')`) and unpacks the resolved
elements into the constructor (`type_(*values)`); the non-namedtuple case is
unchanged (`type_(values)`).

```python
-            return type(value)(
+            values = (
                 self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
                 for sub_value in value
             )
+            type_ = type(value)
+            if hasattr(type_, '_make'):  # namedtuple
+                return type_(*values)
+            return type_(values)
```

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_resolveValue` | `Query.resolve_lookup_value` (django/db/models/sql/query.py:1071) |
| `problem_spec_resolveValue` | the post-condition that accept/rebuild decision must satisfy |
| `resolveRef` (pure helper) | the reference structural resolution of a value (scalar→itself, expression→its resolved form, sequence→element-wise rebuilt) |
| `resolveExpr : Nat → Value` (parameter) | `sub_value.resolve_expression(self, reuse, allow_joins)` — the resolution of ONE expression, modeled abstractly; universally quantified |
| `Value.scalar` | a plain value with no `resolve_expression` and not a list/tuple (returned unchanged) |
| `Value.expr` | a value carrying `resolve_expression` |
| `Value.seq .plain` | a `list` (constructor consumes one iterable) |
| `Value.seq .tupleLike` | a plain `tuple` (constructor consumes one iterable) |
| `Value.seq .special` | a `namedtuple` subtype (constructor needs unpacked args; `hasattr(type_, '_make')`) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `Value.scalar n` | `int` value `n` | not a list/tuple, no `resolve_expression` ⇒ returned unchanged |
| `Value.expr id` | object with `resolve_expression`, identified by `id` | resolves to `resolveExpr id` |
| `Value.seq .plain elems` | `list` of the element images | `hasattr(type_, '_make')` False ⇒ rebuilt via `type_(values)` |
| `Value.seq .tupleLike elems` | plain `tuple` of the element images | `hasattr(type_, '_make')` False ⇒ rebuilt via `type_(values)` |
| `Value.seq .special elems` | `namedtuple` instance | `hasattr(type_, '_make')` True ⇒ rebuilt via `type_(*values)` |
| `result : Option Value` | the returned container / value, or an exception (`none`) | post-patch resolution always succeeds ⇒ `some`; pre-patch raised `TypeError` on a namedtuple ⇒ `none` |

The container kind has THREE values so the spec can pin the EXACT rebuilt type:
the gold non-namedtuple branch `type_(values)` preserves the precise container
type (a `list` stays a `list`, a `tuple` stays a `tuple`), so leaving these
collapsed would let a wrong impl swap list↔tuple and still verify (directive 5
frame discipline). `hasattr(type(value), '_make')` is the predicate the fix
branches on: `.special` (namedtuple) needs the unpacking branch `type_(*values)`;
`.plain`/`.tupleLike` both take the single-iterable branch `type_(values)` but
remain distinguished so the result's exact type is pinned.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as a proof axiom. The single-expression
  resolution (`resolve_expression`) is left as a universally-quantified parameter
  `resolveExpr : Nat → Value` — the spec holds for EVERY expression resolver — so
  the proof consumes no property of it and there is no `axiom <callee>_prop`.
  `axiom_check.py` is a skip stub.
- The behavior-changing op is the sequence rebuild: pre-patch a `namedtuple`
  could not be rebuilt (the single-iterator constructor raised `TypeError`);
  post-patch it is rebuilt by unpacking. This is recorded as an A-reference
  (the real `resolve_lookup_value` rebuild is exercised directly by G-CONF), not
  axiomatized.
- No flag dependency.

## G-CONF fuzz seed
- pinned seed: `13590`
- ≥10^5 fuzzed values drawn to exercise: plain scalars, expression objects,
  lists, plain tuples, and namedtuples — including nested combinations of
  arbitrary depth — with the namedtuple case (the discriminating behavior)
  biased to appear frequently. Each fuzzed value is run through the REAL patched
  `Query.resolve_lookup_value` (oracle) and the R/I Python shadow of
  `implementation_resolveValue`; `resolveExpr` is bound to a fixed deterministic
  resolver on both sides.
