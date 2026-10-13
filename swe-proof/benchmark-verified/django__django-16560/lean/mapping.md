# mapping.md — django__django-16560

## Instance
- repo: django/django
- base_commit: 51c9bb7cd16081133af4f0ab6d06572660309730
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
A model constraint already lets the caller customise the human-readable message
attached to the validation error it raises. The change adds a second, parallel
customisation: an optional machine-readable error *code*. Once configured on a
constraint, that code must participate in exactly the same places the message
already does:

1. **Equality** — two constraints that are otherwise identical but carry
   different codes are no longer equal; identical codes keep them equal.
2. **Reconstruction data** — the keyword data used to rebuild the constraint
   surfaces the code, but only when one was actually configured (an unset code is
   omitted, exactly like the existing message handling).
3. **Validation error** — when the constraint detects a violation and raises its
   validation error, that error now carries the configured code (or no code when
   none was configured).

At `base_commit` the constraint classes have no notion of an error code at all:
equality ignores it, the reconstruction data never mentions it, and the raised
validation error always has an empty code. The fix threads an optional code
through construction and into each of the three observable behaviors above.

```python
# validation error (CheckConstraint.validate, post-patch):
-        raise ValidationError(self.get_violation_error_message())
+        raise ValidationError(
+            self.get_violation_error_message(), code=self.violation_error_code
+        )
# equality (CheckConstraint.__eq__, post-patch): adds
+        and self.violation_error_code == other.violation_error_code
# reconstruction data (BaseConstraint.deconstruct, post-patch): adds
+        if self.violation_error_code is not None:
+            kwargs["violation_error_code"] = self.violation_error_code
```

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_validateError` | the validation-error raise in `CheckConstraint.validate` (`django/db/models/constraints.py:111-117`) and the analogous raises in `BaseConstraint` subclasses; the changed token is the `code=` argument added to the raised error |
| `implementation_constraintEq` | `CheckConstraint.__eq__` (`django/db/models/constraints.py:132-139`); the changed token is the added code conjunct |
| `implementation_serializedCode` | the code-handling branch of `BaseConstraint.deconstruct` (`django/db/models/constraints.py:68-77`); the changed token is the conditional that adds the code to the kwargs |
| `problem_spec_*` | the post-condition each behavior must satisfy |
| `Constr` (helper) | the comparison-relevant payload of a constraint: its pre-existing comparison key plus the optional code |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `code : Option String` | `self.violation_error_code` (`str` or `None`) | `none ↔ None` (no code configured); `some s ↔ s` (a configured code string) |
| `violated : Bool` | whether the constraint's (unchanged) detection found a violation | abstracts the unchanged detection (`Q(check).check(...)` / `queryset.exists()`); the fix does not touch it |
| result of `validateError : Option (Option String)` | the raised validation error's code, or no error | `none ↔` no validation error raised; `some c ↔` an error was raised whose `.code` is `c` (`some s ↔` code `s`, `none ↔` code `None`) |
| `Constr.rest : String` | the constraint's pre-existing comparison payload (name, check/fields, message), abstracted to a single comparison key | unchanged by the fix; modeled as one opaque-but-total key string |
| `Constr.code : Option String` | `self.violation_error_code` | the newly-threaded field |
| result of `constraintEq : Bool` | `a == b` for two constraints | real `__eq__` |
| result of `serializedCode : Option String` | `deconstruct()[2].get("violation_error_code")` | the value placed in the reconstruction kwargs under the code key; `none ↔` key absent, `some s ↔` key present with value `s` |

`Option String ↔ (str | None)`: a Django constraint's `violation_error_code` is a
`str` or `None`. `Option String` is the faithful carrier. `Constr.rest` collapses
the unchanged comparison payload (name + check/fields + message) to one string key:
this is sound because the fix changes nothing about how those parts are compared —
only the *addition* of the code conjunct is observable.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. Each modeled behavior is a
  pure total computation over `(violated, code)` / `(rest, code)` / `code`. The
  unchanged violation-detection (`Q(self.check).check(...)`, `queryset.exists()`)
  is abstracted to the boolean `violated`; the unchanged message handling
  (`get_violation_error_message`) is not modeled (orthogonal to the code change).
  `axiom_check.py` is therefore a skip stub.
- Flag dependency: the reconstruction data includes the code only when it is not
  `None` (mirroring the pre-existing message handling). G-CONF fuzzes both the
  `None` and the non-`None` configurations.
- The same code-threading is applied identically across `BaseConstraint`,
  `CheckConstraint`, `UniqueConstraint`, and `ExclusionConstraint`; the three
  modeled behaviors capture the observable contract shared by all of them.

## G-CONF fuzz seed
- pinned seed: `16560`
- ≥10^5 fuzzed tuples per leg, codes drawn from `None` plus a pool of code
  strings, comparison keys drawn from a small pool (so equal/unequal both occur),
  and `violated ∈ {True, False}`, exercising the `None`-code boundary throughout.
