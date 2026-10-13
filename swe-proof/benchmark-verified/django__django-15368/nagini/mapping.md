# mapping.md — django__django-15368

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e972620ada4f9ed7bc57f28e133e85c85b0a7b20`, states the type
abstraction, and gives the provenance of the one type-hierarchy fact the spec
relies on (a precondition, not a consumed `@ContractOnly` axiom).

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_wrap_flags(in_family, resolvable)` | the inner per-object classification loop of `QuerySet.bulk_update` — `django/db/models/query.py:671-675` (the `for obj in batch_objs:` body) | the modeled changed logic: for each object's attribute value, decide whether to wrap it as a literal `Value` or carry it through unwrapped |
| `resolvable[i]` (bool) | `hasattr(attr, 'resolve_expression')` — the *post-patch* classification predicate, `query.py:673` | True iff the attribute value carries the resolving capability (a `resolve_expression` method) |
| `in_family[i]` (bool) | `isinstance(attr, Expression)` — the *pre-patch* classification predicate, `query.py:673` | True iff the attribute value is (strictly) an instance of `django.db.models.expressions.Expression` |
| `wrap_flags(s)` *(deep model)* | the desired per-attribute decision `not hasattr(attr, 'resolve_expression')` applied down the batch | pure spec: True (wrap as literal) iff NOT resolvable |
| result element `True` | `attr = Value(attr, output_field=field)` — the attribute is wrapped as a literal bound parameter, `query.py:674` | the value was wrapped as a literal |
| result element `False` | `attr` is left as-is and passed to `When(pk=..., then=attr)` | the value was carried through unwrapped (the DB resolves it) |

The pre-patch repo construct the change removes (for the refinement audit; not
referenced from the consumer spec view): the `isinstance(attr, Expression)`
test, and the now-unused `Expression` name in the import at `query.py:20`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| one object's attribute value `attr` (an arbitrary Python object) | a pair of booleans `(in_family[i], resolvable[i])` — the only two facts about `attr` the classification observes | `in_family[i] == isinstance(attr, Expression)`; `resolvable[i] == hasattr(attr, 'resolve_expression')`. The classification reads nothing else about `attr`. |
| the ordered list of attribute values across `batch_objs` for one field | two aligned `List[bool]` (`in_family`, `resolvable`), one entry per object, same length | order- and length-preserving; entry `i` ↔ object `i` in the batch |
| the produced list of `When(then=…)` arguments | a `List[bool]` of wrap flags, one per object | entry `i` is `True` iff `attr_i` was wrapped in `Value(...)` (literal), `False` iff carried through |
| the surrounding `Case`/`When`/`Value`/`Cast` machinery (`query.py:675-679`) | omitted (identity downstream) | only the per-attribute wrap decision differs between the buggy and fixed code; everything downstream consumes the chosen `then=` value unchanged. The F2P test (`test_f_expression`) observes exactly whether the `F('note')` value was resolved (unwrapped) or stored as the literal string `'F(note)'` (wrapped). |

`str`/object indexing of repo attributes is not needed: the only observations
the classification makes are the two booleans, so the carrier is `List[bool]`
and the specification is phrased over `PSeq[bool]` via `ToSeq`.

## 3. The type-hierarchy fact (precondition, audited by G-AX) — NOT a consumed axiom

**Fact:** for every attribute value `attr`,
`isinstance(attr, Expression)` ⟹ `hasattr(attr, 'resolve_expression')`
(i.e. `in_family[i] ⟹ resolvable[i]`), and the converse is **false** — there
exist values that are resolvable without being `Expression` instances.

**Provenance (`django/db/models/expressions.py` @ base_commit):**
- `class BaseExpression` defines `resolve_expression(...)` at line 231.
- `class Expression(BaseExpression, Combinable)` at line 394 — so every
  `Expression` instance inherits `resolve_expression` ⇒ `in_family ⟹ resolvable`.
- `class F(Combinable)` at line 582 defines its own `resolve_expression(...)`
  at line 595 but is **NOT** a subclass of `Expression` (it derives only from
  `Combinable`, line 33, which has no `resolve_expression`). So an `F` instance
  has `resolvable = True`, `in_family = False` — the converse fails. `F` is the
  discriminating value the F2P test (`tests/queries/test_bulk_update.py`
  `test_f_expression`) exercises: `note.misc = F('note')`.
- A plain Python datum (e.g. a `str`, `int`) has neither: `in_family = False`,
  `resolvable = False` — it must be wrapped as a literal `Value`.

This is a fact about the **unchanged** class hierarchy that both the buggy and
the fixed predicate observe; it is encoded as the spec's **precondition**
`in_family[i] ⟹ resolvable[i]` (and as a loop invariant). It is NOT a
`@ContractOnly` the proof consumes — there are no consumed axioms in this
bundle. `axiom_check.py` (G-AX) constructs the real `Expression`, `F`, `Value`
and plain-datum objects and asserts the hierarchy fact (membership entails the
capability; `F` witnesses the converse failure) against the live Django classes,
and asserts the deep model `wrap_flags` (wrap iff not resolvable) matches the
post-patch predicate on those real objects. Exit 0 iff sound.
