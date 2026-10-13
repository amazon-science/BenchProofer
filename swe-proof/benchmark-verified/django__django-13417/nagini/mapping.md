# mapping.md — django__django-13417

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 71ae1ab0123582cc5bfe0f7d5f4cc19a9412f396`, states the type
abstraction, and records callee provenance (none consumed: this bundle has no
axioms).

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped)` | `QuerySet.ordered` property — `django/db/models/query.py:1216` (body lines 1222-1230) | the modeled changed function (result-set ordering introspection flag) |
| `is_ordered(...)` | the property's overall boolean decision (the disjunction of its three `return True` guards) | pure spec: the exact five-input decision the flag must report |

The five `bool` parameters bind to the repo expressions the property reads,
each consumed purely as a truth value:

| model.py param | repo expression (file:line @ base_commit) | repo type | how consumed |
|---|---|---|---|
| `is_empty` | `isinstance(self, EmptyQuerySet)` (`query.py:1223`) | `bool` | `if ...: return True` |
| `has_raw_order` | `self.query.extra_order_by or self.query.order_by` (`query.py:1225`) | tuple / list (truthy) | `if ...: return True` |
| `default_on` | `self.query.default_ordering` (`query.py:1227`) | `bool` (`sql/query.py:182` sets `self.default_ordering = True`) | conjunct, truthiness |
| `model_has_order` | `self.query.get_meta().ordering` (`query.py:1227`) | list / tuple (truthy) — `Meta.ordering` | conjunct, truthiness |
| `is_grouped` | `self.query.group_by` (post-patch conjunct) | `None` / `True` / tuple (`sql/query.py:183` init `None`; `2036` set to `tuple(...)`; `2208` may be `True`) — consumed via `not ...` | conjunct, truthiness |

The pre-patch property (the refinement audit's pre-image, not referenced from
the consumer spec view) is the same body with the `elif` lacking the
`and not self.query.group_by` conjunct (`query.py:1227` pre-patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `isinstance(self, EmptyQuerySet)` | `bool` `is_empty` | identity on the boolean value |
| `self.query.extra_order_by or self.query.order_by` (tuple/list disjunction) | `bool` `has_raw_order` | the property uses the value only as the condition of `if ...: return True`; the bool is exactly `bool(extra_order_by) or bool(order_by)` |
| `self.query.default_ordering` (`bool`) | `bool` `default_on` | identity |
| `self.query.get_meta().ordering` (list/tuple) | `bool` `model_has_order` | the property uses it only inside an `and` conjunction (truthiness); the bool is `bool(Meta.ordering)` — empty `()` ↔ `False`, non-empty ↔ `True` |
| `self.query.group_by` (`None` / `True` / tuple) | `bool` `is_grouped` | the property uses it only via `not self.query.group_by` (truthiness); the bool is `bool(group_by)` — `None`/empty ↔ `False`, `True`/non-empty tuple ↔ `True` |

Every input the property reads is consumed exclusively for its truth value
(each appears only as an `if`/`elif` condition or an operand of `and`/`or`/
`not`), so the truthy-to-`bool` refinement is exact for the property's
observable result. This is the standard kind-R refinement: model over the
Nagini-expressible carrier (`bool`) and record the 1:1 truth-value
correspondence. The result `bool` ↔ the property's `True`/`False`.

## 3. Callee provenance (kind-A)

None. `QuerySet.ordered` performs no library/utility call that the patch leaves
unchanged and that Nagini cannot express — it reads attributes and returns a
boolean combination of their truth values. The `axioms` region of `model.py`
is empty; there is no `@ContractOnly` and no A-consumed or A-reference callee.
`axiom_check.py` therefore only asserts the no-axiom status (G-AX is vacuous).
