# mapping.md — django__django-16560

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 51c9bb7cd16081133af4f0ab6d06572660309730`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every modeled operation and every free (unconstrained) input.

Repo files under change: `django/db/models/constraints.py` and
`django/contrib/postgres/constraints.py`.

## 1. Symbol ↔ repo binding

The feature threads a new optional error code through a constraint, observable in
five independent projections. Each is modeled by one `method` whose post-image
is a pure function in the `pure` region.

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recordErrorCode` / `recordedCode` | `BaseConstraint.__init__` storing the new attribute — `django/db/models/constraints.py:25` (post-patch: the `if violation_error_code is not None: self.violation_error_code = violation_error_code` store) | the code a constraint records from the optionally-supplied value |
| `serializeWithCode` / `withCodeKwarg` | `BaseConstraint.deconstruct` — `django/db/models/constraints.py:68` (post-patch: the `kwargs["violation_error_code"] = ...` addition) | the serialized keyword bindings, gaining the code entry when set |
| `constraintsEqual` / `constraintEq` | `CheckConstraint.__eq__` (`:132`) and `UniqueConstraint.__eq__` (`:313`); the shared shape is `BaseConstraint`-level equality of the new field ANDed with the rest | structural equality including the new code |
| `renderConstraint` / `renderedWithCode` | `CheckConstraint.__repr__` (`:119`) and `UniqueConstraint.__repr__` (`:295`); the shared shape is the conditional `" violation_error_code=%r" % code` fragment | the textual form, gaining the code fragment when set |
| `validateWithCode` / `checkResult` | `CheckConstraint.validate` (`:111`) and `BaseConstraint`-subclass validate sites; post-patch the raised `ValidationError(..., code=self.violation_error_code)` on the message-reporting branch | the violation report carrying the constraint's code |

The same five projections recur in `django/contrib/postgres/constraints.py`
(`ExclusionConstraint`, lines 32/154/168/215) — they are the SAME five behaviours
on a sibling subclass, so a single set of methods models them all. The F2P tests
of THIS instance are all under `tests/constraints/tests.py`
(`BaseConstraintTests`, `CheckConstraintTests`, `UniqueConstraintTests`); the
postgres sites add no F2P here.

### 1.1 Free inputs (unchanged sub-computations — directive 7)
These are passed as unconstrained method parameters; the modeled behaviour holds
for every value, so they are owed no contract and there is no axiom:

- `otherEqual : Bool` — whether all OTHER observable fields of the two
  constraints agree (`__eq__`'s pre-existing conjuncts: name, check/fields,
  condition, …). Unchanged by the patch.
- `base : List Char` (render) — the base textual rendering a constraint already
  produces before any code fragment. Unchanged.
- `base : List (String × List Char)` (serialize) — the keyword bindings
  `deconstruct` already emits (`name`, and `violation_error_message` when
  non-default). Unchanged.
- `shown : List Char` — the standard value formatter's (`repr`/`%r`) rendering of
  one code value, an unchanged formatting step.
- `isValid : Bool` — the instance's validity verdict (`Q(self.check).check(...)`
  / `queryset.exists()`), an unchanged DB-backed predicate.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `violation_error_code` (a `str` or `None`) | `ErrCode = Option (List Char)` | `None ↔ none`; a `str` code `s ↔ some s.toList`; `s` (str) ↔ `s.toList`-shaped `List Char` |
| a single code character | Lean `Char` | `Char.ofNat (ord ch) ↔ ch`; on the BMP total and exact |
| the kwargs `dict` of `deconstruct` | `List (String × List Char)` | dict ↔ ordered assoc list; "key present" ↔ membership of the `("violation_error_code", _)` pair |
| `repr(constraint)` (a `str`) | `List Char` | str ↔ `List Char`; the conditional fragment is `" violation_error_code=%r" % code` ↔ `" violation_error_code=".toList ++ shown` with `shown = (%r % code).toList` |
| `ValidationError(msg, code=…)` | `Except ErrCode Unit` | acceptance (no raise) ↔ `Except.ok ()`; a raised error carrying `code` ↔ `Except.error code`; the observable is `exc.code` |
| `bool` (`__eq__`, validity) | Lean `Bool` | identity |

## 3. Callee provenance — none

There are **no axiomatized callees** and **no deep-model reference** to a library
callee. The changed behaviour is data-plumbing of an optional code through five
projections; it is modeled DEEPLY in the `pure` region. Every operation the
projections invoke but do NOT reshape — the equality of the other fields, the
base rendering, the value formatter, the validity predicate — is an unchanged
computation modeled as a FREE INPUT (§1.1), strictly weaker than any concrete
behaviour, so it is owed no contract and there is nothing for G-AX. Hence no
`axiom_check.py` is shipped and **G-AX skips** (gates.py: no axiom_check.py ⇒
skip), as for the sibling no-axiom bundles (django__django-13212 / -11265 /
-14140).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16560`**. Its SHADOW
transliterates the five pure post-images (`recordedCode`, `withCodeKwarg`,
`constraintEq`, `renderedWithCode`, `checkResult`); its ORACLE drives the REAL
gold-patched `BaseConstraint` / `CheckConstraint` objects (store, `deconstruct`,
`__eq__`, `repr`, `validate`). The single unchanged predicate `Q.check` (the free
`isValid` bit) is monkeypatched to a controllable boolean so the real patched
`validate` body runs against both branches with no database.
