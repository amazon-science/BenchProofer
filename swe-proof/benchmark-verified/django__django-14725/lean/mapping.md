# mapping.md — symbol binding & type bijection (django__django-14725)

## Modeled function
- **Lean** `implementation_saveFormset : Bool → List α → List α → List α`
- **Python** `BaseModelFormSet.save(self, commit=True)` —
  `django/forms/models.py:666-678 @ 0af9a5fc` (base_commit).
  Post-patch body (gold):
  ```python
  if self.edit_only:
      return self.save_existing_objects(commit)
  else:
      return self.save_existing_objects(commit) + self.save_new_objects(commit)
  ```

The function under spec is `save`. The patch adds a branch on the new
`self.edit_only` flag: in edit-only mode `save` returns ONLY the list produced
by persisting the already-present objects, and never composes in the list
produced by persisting freshly-created objects. The latter call
(`save_new_objects`) is precisely what creates new database rows, so skipping it
is the observable behavior the F2P tests demand (no new `Author` / `Book` rows
when `edit_only=True`).

The non-`commit` book-keeping block above the changed line (`self.saved_forms`,
`self.save_m2m`) is unchanged by the patch and orthogonal to the edit-only
selection (it only rebinds an m2m closure); it is framing not modeled here.

## Callees and the flag
- `save_existing_objects(commit)` — UNCHANGED. Returns the list of model
  instances persisted from the formset's *initial* (already-present) forms.
  Modeled as the input list `existing` (R refinement: a Python `list` of saved
  instances ↔ a Lean `List α`). Its internals (pk filtering, deletion handling)
  are irrelevant to THIS function's selection logic — `save` consumes only its
  returned list.
- `save_new_objects(commit)` — UNCHANGED. Returns the list of model instances
  persisted from the formset's *extra* forms (the freshly-created objects).
  Modeled as the input list `new` (same R refinement). Calling it has the side
  effect of creating rows; in edit-only mode the patch avoids calling it at all,
  so neither its rows nor its returned list appear.
- `self.edit_only` — the new boolean flag. Modeled as the `editOnly : Bool`
  argument. The factory functions `modelformset_factory` /
  `inlineformset_factory` (other gold hunks) merely thread this flag onto the
  generated `FormSet` class; that plumbing carries no independently-observable
  behavior of its own (it only sets the class attribute that `save` reads), so
  it is not separately modeled.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.edit_only : bool` | `editOnly : Bool` | the new flag |
| `save_existing_objects(commit) : list` | `existing : List α` | list of persisted existing instances; order preserved |
| `save_new_objects(commit) : list` | `new : List α` | list of persisted new instances; order preserved |
| `a + b` (list concat) | `a ++ b` | Python list `+` ↔ Lean `List.append`, order preserving |
| return value : `list` | `result : List α` | the combined list of persisted instances |

`α` is the (opaque) type of a persisted model instance; the selection logic is
parametric in it — `save` neither inspects nor reorders the elements, it only
chooses which lists to concatenate. The list contents are produced by the two
UNCHANGED callees, so element identity is out of scope for this function.

## Callee provenance
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty. The
  two callees' returned lists ARE the modeled inputs (R-tagged), not axioms.
- No A-reference deep model: the changed operation is the branch selection
  itself, modeled directly as the `if editOnly then … else …`.

## Flag dependency
The behavior is fully determined by `editOnly`; G-CONF fuzzes both `True` and
`False` and both empty/non-empty `existing` / `new` lists.

## G-CONF fuzz seed
Pinned seed: **14725**. ≥10^5 fuzzed inputs over `(editOnly, existing, new)`
with lists of small integer tokens standing in for persisted instances.
