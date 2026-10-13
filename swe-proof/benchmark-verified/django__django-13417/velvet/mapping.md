# mapping.md — django__django-13417

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 71ae1ab0123582cc5bfe0f7d5f4cc19a9412f396`, states the type
abstraction, and records callee provenance (none consumed: this bundle has no
axioms and no deep-model references).

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ordered (isEmpty hasRawOrder defaultOn modelHasOrder isGrouped : Bool) : Bool` | `QuerySet.ordered` property — `django/db/models/query.py:1217` (body lines 1222-1230) | the modeled changed function (result-set ordering introspection flag) |
| `isOrdered (...)` | the property's overall boolean decision (the disjunction of its three `return True` guards) | pure spec: the exact five-input decision the flag must report |

The five `Bool` parameters bind to the repo expressions the property reads,
each consumed purely as a truth value:

| Solution.lean param | repo expression (file:line @ base_commit) | repo type | how consumed |
|---|---|---|---|
| `isEmpty` | `isinstance(self, EmptyQuerySet)` (`query.py:1223`) | `bool` | `if ...: return True` |
| `hasRawOrder` | `self.query.extra_order_by or self.query.order_by` (`query.py:1225`) | tuple / list (truthy) | `if ...: return True` |
| `defaultOn` | `self.query.default_ordering` (`query.py:1227`) | `bool` (`sql/query.py:182` sets `self.default_ordering = True`) | conjunct, truthiness |
| `modelHasOrder` | `self.query.get_meta().ordering` (`query.py:1227`) | list / tuple (truthy) — `Meta.ordering` | conjunct, truthiness |
| `isGrouped` | `self.query.group_by` (post-patch conjunct) | `None` / `True` / tuple (`sql/query.py:183` init `None`; `2036` set to `tuple(...)`; `2208` may be `True`) — consumed via `not ...` | conjunct, truthiness |

The pre-patch property (the refinement audit's pre-image, not referenced from
the consumer spec view) is the same body with the `elif` lacking the
`and not self.query.group_by` conjunct (`query.py:1227` pre-patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `isinstance(self, EmptyQuerySet)` | `Bool` `isEmpty` | identity on the boolean value |
| `self.query.extra_order_by or self.query.order_by` (tuple/list disjunction) | `Bool` `hasRawOrder` | the property uses the value only as the condition of `if ...: return True`; the bool is exactly `bool(extra_order_by) or bool(order_by)` |
| `self.query.default_ordering` (`bool`) | `Bool` `defaultOn` | identity |
| `self.query.get_meta().ordering` (list/tuple) | `Bool` `modelHasOrder` | the property uses it only inside an `and` conjunction (truthiness); the bool is `bool(Meta.ordering)` — empty `()` ↔ `false`, non-empty ↔ `true` |
| `self.query.group_by` (`None` / `True` / tuple) | `Bool` `isGrouped` | the property uses it only via `not self.query.group_by` (truthiness); the bool is `bool(group_by)` — `None`/empty ↔ `false`, `True`/non-empty tuple ↔ `true` |

Every input the property reads is consumed exclusively for its truth value
(each appears only as an `if`/`elif` condition or an operand of `and`/`or`/
`not`), so the truthy-to-`Bool` refinement is exact for the property's
observable result. This is the standard kind-R refinement: model over the
Lean-expressible carrier (`Bool`) and record the 1:1 truth-value
correspondence. The result `Bool` ↔ the property's `True`/`False`.

## 3. Callee provenance (kind-A)

None. `QuerySet.ordered` performs no library/utility call that the patch leaves
unchanged and that Lean cannot express — it reads attributes and returns a
boolean combination of their truth values. The `axioms` region of
`Solution.lean` is empty; there is no consumed axiom and no A-reference deep
model. `axiom_check.py` is therefore absent (G-AX is vacuous — there is no
asserted axiom value to validate).

## 4. G-CONF fuzz seed

`conformance_check.py` differential-tests the R/I shadow of the `ordered` do
block (the boolean decision) against the gold-patched property body
transliterated verbatim, over **all 32** five-bool combinations (exhaustive)
plus a fuzzed stream. Pinned seed: **13417**. The five repo truthy expressions
are fed as their `bool()` projections (mapping.md §2); the shadow and oracle are
both pure boolean and require no DB — so `conf_skip=false`.
