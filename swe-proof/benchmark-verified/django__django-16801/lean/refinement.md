# refinement.md — django__django-16801

Maps every operation in `implementation_connectPostInit` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `connectPostInit` (`ImageField.contribute_to_class` guard)

Post-patch repo code (`patch.diff`), the connection decision:
```python
def contribute_to_class(self, cls, name, **kwargs):
    super().contribute_to_class(cls, name, **kwargs)
    # Only run post-initialization dimension update on non-abstract models
    # with width_field/height_field.
    if not cls._meta.abstract and (self.width_field or self.height_field):
        signals.post_init.connect(self.update_dimension_fields, sender=cls)
```

Lean impl (`implementation_connectPostInit`): a `Bool`-valued decision returning
the truth value of that guard.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `isAbstract : Bool` | `cls._meta.abstract` | **R** | the model abstract flag, a `bool`, ↔ `Bool` (mapping.md). |
| 2 | `widthField heightField : Option String` | `self.width_field`, `self.height_field` | **R** | optional attribute names; `None`/`""` ↦ falsy, name str ↦ truthy. The guard uses them only in boolean position, so the faithful refinement is the truthiness test `truthy` (`none ↦ false`, `some s ↦ ¬s.isEmpty`). |
| 3 | `if !isAbstract && (truthy widthField \|\| truthy heightField) then return true` | `if not cls._meta.abstract and (self.width_field or self.height_field): signals.post_init.connect(...)` | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch widens the guard by conjoining `(self.width_field or self.height_field)`; the Lean guard's right conjunct `(truthy widthField \|\| truthy heightField)` is exactly the added clause. The handler connection is observed through its truth value: guard true ↦ `result = true` (connect runs), guard false ↦ `result = false`. The prepatch impl tests only `!isAbstract` (pre-patch guard). |
| 4 | `return false` | (guard false) → `signals.post_init.connect(...)` is not reached | **R** | the guard's false outcome — no connection — modeled as `result = false`. The `super().contribute_to_class(...)` side effects and the connect call's own effect are unchanged by the patch and not part of the modeled decision (mapping.md). |
| 5 | `Id.run do … return …` (`Bool`) | the guard's truth value selects whether `connect(...)` runs | **R** | result modeled as the `Bool` truth value of the post-patch guard. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `contribute_to_class` connection guard.

## Soundness check (verify ⟹ correct)

- `problem_spec_connectPostInit` pins the single output for ALL inputs
  (directive 5 frame — the result is fully determined, no component unconstrained;
  directive 8 — the result is grounded structurally in the three inputs
  `isAbstract`/`widthField`/`heightField` via boolean connectives and `truthy`,
  not equated to any ungrounded oracle). A verifying impl must return `true`
  exactly on a concrete model with a truthy width or height name, and `false`
  everywhere else.
- The discriminating clause is the added conjunct: when `isAbstract = false` and
  BOTH `widthField`/`heightField` are falsy (`none` or `some ""`), the spec
  demands `result = false`. The prepatch impl ignores the dimension fields and
  returns `true` for every concrete model, so on that input it disagrees with the
  spec — hence the carried gold proof's first-branch `rfl` (claiming `pure true =
  false` after the spec evaluates to `false`) fails to typecheck against the
  prepatch impl (G-DIFF/G-PANEL).
- This is exactly what `test_post_init_not_connected` exercises: a model whose
  `ImageField` sets neither `width_field` nor `height_field` must NOT have the
  post-init handler connected (post-patch `result = false`); pre-patch it was
  connected (`result = true`).
- The second gold hunk (removing the now-redundant guard inside
  `update_dimension_fields`) is not needed to explain the F2P regression and is
  outside the modeled connection decision (see mapping.md "Second hunk" for the
  narrow scope claim — NOT a global behavior-preservation claim), so it is not
  separately modeled. The full gold behavior (both hunks) is carried by
  `patch.diff` and exercised by G-RESOLVE / G-GOLD against the real harness.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  connection guard, exhaustively over the modeled abstraction (abstract flag ×
  width {absent, empty, set} × height {absent, empty, set}) plus ≥1e5 fuzzed
  points (0 disagreements).
