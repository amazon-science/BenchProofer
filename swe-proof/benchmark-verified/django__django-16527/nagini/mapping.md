# mapping.md — django__django-16527

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bd366ca2aeffa869b7dbc0b0aa01caea75e6dc31`, states the type
abstraction, and records callee provenance.

Repo file under change:
`django/contrib/admin/templatetags/admin_modify.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `save_as_new_visible(is_popup, may_add, may_change, editing_existing, save_as_enabled)` | the `"show_save_as_new"` entry of the dict passed to `ctx.update(...)` inside `submit_row(context)` — `django/contrib/admin/templatetags/admin_modify.py:102-105` (body line 102) | the modeled changed expression: the boolean value bound to `"show_save_as_new"` |

The modeled function isolates the single dict entry the patch edits. The
surrounding `submit_row` body assigns the local booleans the expression reads
from the rendering `context` mapping (`admin_modify.py:65-75`):

| model.py parameter | repo expression (file:line @ base_commit) |
|---|---|
| `is_popup` | `is_popup = context["is_popup"]` — `admin_modify.py:67` |
| `may_add` | `has_add_permission = context["has_add_permission"]` — `admin_modify.py:72` |
| `may_change` | `has_change_permission = context["has_change_permission"]` — `admin_modify.py:73` |
| `editing_existing` | `change = context["change"]` — `admin_modify.py:66` |
| `save_as_enabled` | `save_as = context["save_as"]` — `admin_modify.py:68` |

`may_change` is a parameter purely so the spec is byte-identical between
`model.py` and `model_prepatch.py` (the prepatch reads `may_change` where the
fix reads `may_add`); the verified `model.py` impl does not read it, exactly as
the gold expression no longer depends on `has_change_permission`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| each `context[...]` permission/state flag (`is_popup`, `has_add_permission`, `has_change_permission`, `change`, `save_as`) | `bool` parameter | identity: every value the F2P test binds into these context keys is a Python `bool`; the dict read `context[k]` is the identity on that boolean |
| the dict entry value `"show_save_as_new": <expr>` | `bool` return value | identity: the expression is a chain of `and`/`not` over the five booleans, whose Python value is a `bool` |
| Python `and`/`not` over booleans | Nagini `and`/`not` over `bool` | identity: for `bool` operands Python `and`/`not` agree with logical conjunction/negation; the expression contains no short-circuit side effects (all operands are already-bound locals), so the truth table is exactly the modeled formula |

No string, float, collection, or object modeling is needed: the change is a
pure boolean-logic edit. `str` indexing etc. never arise.

## 3. Callee provenance

**No consumed axioms (kind A-consumed) and no deep-model references
(A-reference).** The modeled expression calls no library/utility callee: every
operand is a context boolean read directly, and the operators are primitive
boolean `and`/`not`. The five `context[...]` reads are not opaque callees whose
behavior the proof approximates — they are plain mapping lookups that yield the
exact booleans the F2P test stores, modeled as the identity (§2).

Consequently `axiom_check.py` has no axiom Ensures to fuzz against a real
callee. It instead validates the A-reference of §3 of the refinement: that the
modeled boolean formula equals Python's own evaluation of the gold expression
`not is_popup and has_add_permission and change and save_as` over the full
boolean cube (exhaustive 2^5), confirming the R-refinement of §2 is exact.
