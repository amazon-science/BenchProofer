# mapping.md — django__django-15499

## Symbol binding (file:line @ base_commit d90e34c61b)
Modeled function: the reduction decision in
`CreateModel.reduce(self, operation, app_label)`,
`django/db/migrations/operations/models.py:136-294` (the `elif` chain). The gold
patch inserts a new `elif` arm (post-patch `:173-185`) that fires when the
following operation reconfigures the **same model's managers**: it collapses the
model-creation step and the manager-reconfiguration step into a single creation
step that already carries the new managers.

Lean modeled function name: `optimizeCreateThenAlterManagers` (names the
*behavior* — "collapse a model-creation step and a subsequent same-model manager
reconfiguration into one creation step" — not the patched method `reduce`; see
G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `ModelState` | the receiver `CreateModel` instance `self`, observed via the components the patch reads/writes: `self.name`, `self.fields`, `self.options`, `self.bases`, `self.managers` (`CreateModel.__init__`, `models.py:46-51`) |
| `ModelState.name` | `self.name` (`models.py:23`) |
| `ModelState.fields` | `self.fields` (`models.py:47`) — list of `(name, field)` pairs |
| `ModelState.options` | `self.options` (`models.py:48`) — option dict |
| `ModelState.bases` | `self.bases` (`models.py:49`) |
| `ModelState.managers` | `self.managers` (`models.py:50`) — list of `(name, manager)` pairs |
| `targetName` | `operation.name` of the `AlterModelManagers` operation (`models.py:737`); the guard compares `self.name_lower == operation.name_lower` i.e. `self.name.lower() == operation.name.lower()` (`ModelOperation.name_lower`, `models.py:25-27`) |
| `newManagers` | `operation.managers` of the `AlterModelManagers` operation (`models.py:738`) |
| result | the value `reduce` returns for this operation pairing: post-patch `[CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)]`; when the model differs / no arm fires, `reduce` does NOT produce a CreateModel reduction |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.name : str` (a model identifier, ASCII) | `model.name : String` |
| `self.fields : list[(str, Field)]` (preserved verbatim) | `model.fields : List (String × String)` (each entry an abstract `(name, repr)` token; only ever copied, never inspected) |
| `self.options : dict[str, Any]` (preserved verbatim) | `model.options : List (String × String)` (key, abstract repr) |
| `self.bases : tuple[...]` (preserved verbatim) | `model.bases : List String` |
| `self.managers : list[(str, Manager)]` | `model.managers : List (String × String)` |
| `operation.name : str` | `targetName : String` |
| `operation.managers : list[(str, Manager)]` | `newManagers : List (String × String)` |
| `self.name.lower() == operation.name.lower()` | `model.name.toLower = targetName.toLower` |
| `[CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)]` | `[ { model with managers := newManagers } ]` |
| "no CreateModel reduction produced" (`reduce` returns `False`/`True`, not a `[CreateModel]`) | `[]` (empty result list) |

### Result-type modeling note
The real `reduce` returns *either* a `list` of replacement operations *or* a
boolean (`False` = "cannot optimize across", `True` = "may commute"). For the
modeled pairing (a `CreateModel` followed by an `AlterModelManagers`) the only
two observable outcomes are: **a one-element `[CreateModel(...)]`** (the new arm
fires) or **no CreateModel reduction at all** (`reduce` returns a bool). We model
the result as `List ModelState`: the reduced creation step as the singleton
`[merged]`, and "no reduction produced" as `[]`. G-CONF compares this list shadow
against the patched-branch outcome.

### Name-lower bijection
`str.lower()` is modeled by `String.toLower`. Faithful for the ASCII model
identifiers that name migrations (`"Foo"`, app/model labels); the bijection is
asserted only over ASCII identifier strings, which is the only domain the
optimizer's name comparison sees.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The arm performs only (a) a
  name comparison (`name.lower()`, modeled deeply as `String.toLower`) and (b)
  construction of a new creation step copying four components and substituting the
  managers (modeled deeply as a structure update `{ model with managers := … }`).
  `CreateModel.__init__`'s duplicate-name sanity checks are not part of the
  modeled reduction value (they raise only on malformed input the optimizer never
  builds here), so no callee contract is consumed. ⇒ `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub.
- No flag dependency: the arm fires purely on operation type (fixed to
  AlterModelManagers here) and the same-model name guard.

## G-LEAK
The solver-visible `problem_statement` publicly states: "During migration
optimization, CreateModel + AlterModelOptions is reduced to just CreateModel,
with the model options. Similarly, CreateModel + AlterModelManagers can become
just CreateModel." The spec view therefore may use the public domain vocabulary
("model-creation step", "managers", "options") in prose. The modeled-function
identifier `optimizeCreateThenAlterManagers` shares no patched def/class name as a
substring (the patched method is `reduce`; the patched class `CreateModel`; the
operand class `AlterModelManagers`). No gold-diff line, file path, or
bug→fix mechanism is quoted.

## Pinned G-CONF fuzz seed
`15499`.
