# mapping.md — django__django-11880

## Symbol binding (file:line @ base_commit 06909fe084)

- Modeled function: `Field.__deepcopy__` — `django/forms/fields.py:198-203`
  ```python
  def __deepcopy__(self, memo):
      result = copy.copy(self)                       # 199  shallow copy
      memo[id(self)] = result                        # 200
      result.widget = copy.deepcopy(self.widget, memo)  # 201  widget: deep copy
      result.error_messages = self.error_messages.copy()  # 202  ADDED by patch
      result.validators = self.validators[:]         # 203  validators: list slice
      return result                                  # 204
  ```
  (Line 202 is the gold addition; the others are the pre-existing body.)

- Surrounding context read: `Field.__init__` (`fields.py:55-115`) builds
  `self.error_messages` as a plain `dict` (`messages` assembled from the MRO's
  `default_error_messages` then overlaid with the caller's `error_messages`,
  `fields.py:107-111`), and `self.validators` as a `list` (`fields.py:113`).
  `CharField.__init__` (`fields.py:207-217`) is the subclass exercised by the
  F2P test; it forwards `error_messages={'invalid': ...}` through `**kwargs`.

## Lean ↔ Python type bijection (used by G-CONF; no G-AX axioms)

| Python | Lean | notes |
|---|---|---|
| a Python object's identity (`id(x)`, the `is` operator) | `ObjId := Nat` | distinct tags ⇔ distinct objects; only equality is observed |
| `self.error_messages : dict` (code → message) | `errMsgId : ObjId` (identity) + `errMsg : MsgDict = List (Nat × Nat)` (contents) | error codes/messages are distinct strings ⇒ injective `Nat` encodings; only equality of contents observed |
| `self.validators : list` | `validId : ObjId` + `validators : List Nat` | identity + contents |
| `self.widget : Widget` (object) | `widgetId : ObjId` | only the identity change is modeled (a deep copy yields a fresh object); the widget's internal contents are not on the modeled path |
| `self.required : bool` (a representative immutable scalar carried by shallow copy) | `required : Bool` | frame: preserved by the copy |
| `copy.copy(self)` (shallow) | `let mut result := self` | every field initially shared with `self` |
| `copy.deepcopy(self.widget, memo)` | `result := { result with widgetId := fw }` | fresh widget identity `fw` |
| `self.error_messages.copy()` | `result := { result with errMsgId := fe, errMsg := self.errMsg }` | fresh dict identity `fe`, contents preserved |
| `self.validators[:]` | `result := { result with validId := fv, validators := self.validators }` | fresh list identity `fv`, contents preserved |

`fw`, `fe`, `fv` are the identity tags returned by the three allocations
(`deepcopy` / `dict.copy` / list-slice). Each allocation returns a not-yet-used
identity, captured by the preconditions `fw ≠ self.widgetId`,
`fe ≠ self.errMsgId`, `fv ≠ self.validId` in `correct_deepCopyField`.

## Callee provenance

- `copy.copy`, `copy.deepcopy`, `dict.copy`, list slice `[:]` — all modeled
  deeply as fresh-identity allocation + content preservation (R, not axioms).
  No unchanged callee is consumed as a proof axiom ⇒ `axiom_check.py` is a skip
  stub and G-AX skips.

## Flag dependencies

None.

## G-CONF fuzz seed

`SEED = 11880` (pinned; also in `conformance_check.py`).
