# refinement.md — django__django-11880

Maps every operation in `implementation_duplicateField` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `duplicateField` (`Field.__deepcopy__`)

Post-patch repo code (`patch.diff`, `django/forms/fields.py:198-204`):
```python
def __deepcopy__(self, memo):
    result = copy.copy(self)                            # shallow copy
    memo[id(self)] = result
    result.widget = copy.deepcopy(self.widget, memo)    # fresh widget object
    result.error_messages = self.error_messages.copy()  # ADDED: fresh dict, same contents
    result.validators = self.validators[:]              # fresh list, same contents
    return result
```

Lean impl (`implementation_duplicateField`):
```lean
def implementation_duplicateField
    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
  let mut result := self
  result := { result with widgetId := fw }
  result := { result with errMsgId := fe, errMsg := self.errMsg }
  result := { result with validId := fv, validators := self.validators }
  return result
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `self : FormField` (input carrier) | the `Field` instance being deep-copied | **R** | the touched components map to fields: widget object ↔ `widgetId`; `error_messages : dict` ↔ `errMsgId` (identity) + `errMsg` (contents); `validators : list` ↔ `validId` + `validators`; an immutable scalar ↔ `required`. Object identity ↔ `ObjId` (a `Nat`; `is`/`id()` ⇔ `ObjId` equality). See mapping.md. |
| 2 | `let mut result := self` | `result = copy.copy(self)` | **R** | a shallow copy: every component of `result` is initially the SAME object as `self`'s (identities shared, contents shared). In the value world this is `result := self`; the subsequent rebinds model the shallow-copy → fresh-object replacements. |
| 3 | `result := { result with widgetId := fw }` | `result.widget = copy.deepcopy(self.widget, memo)` | **R** | the widget is replaced by a freshly allocated object; `fw` is its fresh identity (precondition `fw ≠ self.widgetId`). Only the identity change is on the modeled path. |
| 4 | `result := { result with errMsgId := fe, errMsg := self.errMsg }` | `result.error_messages = self.error_messages.copy()` | **R** (deep model of the changed op) | **the fixed operation.** `dict.copy()` allocates a NEW dict (fresh identity `fe`, precondition `fe ≠ self.errMsgId`) whose contents EQUAL the original's. Modeled as setting `errMsgId := fe` (fresh, distinct object) with `errMsg := self.errMsg` (contents preserved). This is the heart of the fix: post-patch the duplicate's error-message mapping is an independent object; pre-patch it was the shared alias. |
| 5 | `result := { result with validId := fv, validators := self.validators }` | `result.validators = self.validators[:]` | **R** | the list slice allocates a NEW list (fresh identity `fv`, precondition `fv ≠ self.validId`) with the same elements; modeled as `validId := fv` (fresh) with `validators := self.validators` (contents preserved). Pre-existing in the body, unchanged by the patch. |
| 6 | (`required` left as carried by the shallow copy) | `result = copy.copy(self)` carries immutable scalars | **R** (frame) | the immutable scalar component is preserved unchanged — `result.required = self.required`. Directive 5: pinned in the spec so a wrong impl cannot perturb it. |
| 7 | `return result` | `return result` | **I** | the duplicated field is returned. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `__deepcopy__` run on REAL Python objects (so `is`/`id()` identity is
exercised exactly as the F2P test does).

## Callee provenance (no consumed axiom)

- `copy.copy(self)` — the shallow copy; modeled as `result := self` (every
  component shared) deeply. Unchanged by the patch.
- `copy.deepcopy(self.widget, memo)` — produces a fresh widget object; modeled
  deeply as a fresh identity `fw`. Unchanged by the patch.
- `dict.copy()` (`self.error_messages.copy()`) — the ADDED line; produces a fresh
  dict with equal contents; modeled deeply as fresh identity `fe` + preserved
  contents. NOT axiomatized (it is the changed op, modeled structurally).
- list slice `self.validators[:]` — produces a fresh list with equal contents;
  modeled deeply as fresh identity `fv` + preserved contents. Unchanged by patch.
- `memo[id(self)] = result` — the deepcopy memo bookkeeping; it records `result`
  for `self`'s id so a cyclic reference resolves to the same copy. It does not
  affect any modeled output component (the touched attributes of the returned
  field), so it is not modeled.

## Soundness check (verify ⟹ correct)

- `problem_spec_duplicateField` pins EVERY modeled output component (directive 5
  / frame): the result's widget/error-message/validator identities are the fresh
  `fw`/`fe`/`fv`; the error-message and validator contents EQUAL the original's;
  and the immutable scalar is preserved. No component is left unconstrained, and
  no ungrounded oracle is used (directive 8) — each clause is grounded in `self`'s
  components or the freshly-supplied identities.
- The discriminating clause is `result.errMsgId = fe` with the precondition
  `fe ≠ self.errMsgId`: post-patch the duplicate's error-message mapping is a
  DISTINCT object from the original's; this is exactly the F2P assertion
  `assertIsNot(field_copy.error_messages, field.error_messages)`.
- The prepatch impl reproduces the PRE-FIX `__deepcopy__`: it omits the fresh
  error-message copy, so the shallow-copy alias survives — `result.errMsgId`
  stays `self.errMsgId`. Under the precondition `fe ≠ self.errMsgId` the spec's
  `result.errMsgId = fe` clause is then false, so its carried `correct_*` cannot
  close (G-DIFF/G-PANEL): the duplicate shares the original's error-message
  object, the bug the issue describes.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `__deepcopy__` (run on real objects, so identity is observed) over hand-picked
  edge cases (incl. the F2P custom-`invalid`-message field, empty/multi-code
  dicts, empty/non-empty validators) plus ≥1e5 fuzzed fields.
