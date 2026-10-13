# refinement.md — django__django-12276

The operation-by-operation correspondence between `model.py`'s implementation
(the `requires_value` impl region + the `generic_requires_value` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The added method — `FileInput.use_required_attribute` (`django/forms/widgets.py`, after `widgets.py:388`)

Gold hunk (the addition to `class FileInput`):
```
     def value_omitted_from_data(self, data, files, name):
         return name not in files

+    def use_required_attribute(self, initial):
+        return super().use_required_attribute(initial) and not initial
+
```

and the companion removal of the byte-identical method from the subclass
`ClearableFileInput` (`widgets.py:454-455`):
```
-    def use_required_attribute(self, initial):
-        return super().use_required_attribute(initial) and not initial
-
```

The method is *moved up* one level in the class hierarchy: from
`ClearableFileInput` to its parent `FileInput`. Effect on each class:

* `FileInput`: previously had no `use_required_attribute` and inherited
  `Widget.use_required_attribute` (`return not self.is_hidden`), which ignored
  `initial`; now it has the conjunction `super().use_required_attribute(initial)
  and not initial`. This is the **observable behaviour change** (the F2P tests).
* `ClearableFileInput`: previously defined the method itself; now inherits the
  identical method from `FileInput`. Source text differs, behaviour identical
  (`super()` still resolves to `Widget.use_required_attribute` through the same
  MRO). No behaviour change — hence no separate failing prepatch for it.

| # | model.py impl op (`requires_value`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `control: UploadControl` with field `control.hidden` | the widget `self`; its hidden state reached via `self.is_hidden` inside the inherited base call | R | the widget modelled with only its touched field; `self.is_hidden` ↔ `control.hidden` (mapping.md §1, §2). |
| A2 | parameter `value_present: bool` | the `initial` argument, observed only by truthiness | R | `initial` is never indexed/iterated, only truth-tested; `not initial` ↔ `not value_present`, so the boolean carrier is exact for the modeled operation (mapping.md §2). |
| A3 | `generic_requires_value(control.hidden)` | `super().use_required_attribute(initial)` | A-consumed | the unchanged inherited base method `Widget.use_required_attribute` is axiomatized: it returns `not self.is_hidden`, ignoring `initial` (mapping.md §3.1). The proof consumes its `Ensures(Result() == (not hidden))` to discharge the decomposed postcondition. |
| A4 | `... and not value_present` | `... and not initial` | **I** (under R on the `initial`↔`value_present` truthiness) | the FIX. The same concrete boolean conjunction with the same `not`-of-the-already-present-value second operand; `not initial` ↔ `not value_present` by R (A2). This is the added behaviour that distinguishes the patched `FileInput` from the inherited base. |
| A5 | `return ...` | `return ...` | I | identical return of the resulting boolean. |

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton of `FileInput`: it returns only
`generic_requires_value(control.hidden)` — exactly the inherited base behaviour
the pre-patch `FileInput` had (`return not self.is_hidden`), with no
`and not initial` term. With the byte-identical frozen spec it **fails**
verification on the postcondition

  `Ensures(Result() == (generic_requires_value(control.hidden) and not value_present))`

(`model_prepatch.py:69` — `Assertion (Result() == (generic_requires_value(...)
and (not value_present))) might not hold`): when `value_present` is `True`
(a usable value is already carried) the required result is `False` but the
pre-patch impl returns `generic_requires_value(control.hidden)` (which is
`True` for a visible control). That is precisely the behaviour the F2P tests
observe:

* `test_use_required_attribute` (widget_tests/test_fileinput): the real
  `FileInput().use_required_attribute(None)` is `True`, and
  `use_required_attribute('resume.txt')` is `False`.
* `test_filefield_with_fileinput_required` (tests/test_forms): a `FileField`
  with `widget=FileInput` renders the `required` attribute when there is no
  initial value, and renders **no** `required` attribute when an initial value
  (`'resume.txt'`) is present.

The spec is therefore strong enough that no implementation omitting the
`and not value_present` term can verify (the spec sees the bug). The companion
clause `Ensures(Implies(not value_present, Result() == generic_requires_value(...)))`
pins the no-value case to exactly the generic base decision, keeping the spec
faithful where the behaviour did NOT change (P2P `test_render`,
`test_use_required_attribute_true/false`) — so a wrong impl cannot satisfy the
spec by, e.g., always returning `False`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — adding the `and not initial` conjunct to the file control's
decision — is an **I** step (the same concrete boolean conjunction, with the
`initial`↔`value_present` truthiness refined by R). There is no deep model and
therefore **no A-reference** here. The only consumed axiom,
`generic_requires_value` (**A-consumed**, step A3), covers an **unchanged**
callee (`Widget.use_required_attribute`, reached through `super()`) the new
method invokes; G-AX validates it against the real base method. We never
axiomatize the function under change.

## D. verify(model) ⇒ resolved

`requires_value` verifies only if it returns `generic_requires_value(control.hidden)
and not value_present` (A3 + the I fix step A4). By R (the widget and its hidden
state ↔ `UploadControl.hidden`; `initial`'s truthiness ↔ `value_present`) the
verified function equals the gold method
`super().use_required_attribute(initial) and not initial` on every input. By
G-AX the real inherited `Widget.use_required_attribute` meets the
`generic_requires_value` axiom it stands in for (A-consumed: returns
`not self.is_hidden`, ignoring `initial`), and the moved method on the real
`FileInput` equals the modeled conjunction over the truthiness of `initial`.
Because the moved method is byte-identical to the one `ClearableFileInput`
already carried, the subclass behaviour is unchanged. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
