# refinement.md — django__django-12406

Operation correspondence between the Lean `implementation_*` skeletons and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: both changed functions are modeled deeply
with concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a
skip stub; the R/I legs are differential-tested by G-CONF.)

## Behavior 1 — `implementation_emptyOption` ↔ `ModelChoiceField.__init__`

patch.diff (forms/models.py) replaces the empty-label decision

```python
if required and (initial is not None):
    self.empty_label = None
else:
    self.empty_label = empty_label
```

with

```python
if (
    (required and initial is not None) or
    (isinstance(self.widget, RadioSelect) and not blank)
):
    self.empty_label = None
else:
    self.empty_label = empty_label
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut chosen := some defaultLabel` | (initial state of `self.empty_label` before the branch) | I | accumulator init; default-label case |
| condition `(required && initialPresent) \|\| (radioWidget && !blankAllowed)` | `(required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank)` | R | `initial is not None` ↦ `initialPresent : Bool`; `isinstance(self.widget, RadioSelect)` ↦ `radioWidget : Bool`; `not blank` ↦ `!blankAllowed`. Boolean bijection. |
| `chosen := none` (then-branch) | `self.empty_label = None` | R | `None : str\|None` ↦ `none : Option String` |
| `chosen := some defaultLabel` (else-branch) | `self.empty_label = empty_label` | R | `empty_label : str` ↦ `defaultLabel : String`; `some` wrap |
| `return chosen` | value of `self.empty_label` | R | result carrier `str\|None` ↦ `Option String` |

The result `self.empty_label` is the precise observable: `ModelChoiceIterator`
yields the leading `("", empty_label)` blank choice iff `empty_label is not
None` (forms/models.py:1148-1150), which the F2P tests assert via
`list(field.choices)`.

## Behavior 2 — `implementation_formKwargs` ↔ `ForeignKey.formfield`

patch.diff (related.py) appends one entry to the kwargs dict passed to the
super form-field builder:

```python
    **kwargs,
+   'blank': self.blank,
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut d := base` | the kwargs dict as assembled BEFORE the new entry (`form_class`/`queryset`/`to_field_name`/`**kwargs`) | R | heterogeneous dict ↦ `Std.HashMap String KwargVal`; pre-`blank` state captured as `base` (mapping.md) |
| `d := d.insert "blank" (KwargVal.flag blankAllowed)` | `'blank': self.blank` | R | `self.blank : bool` ↦ `blankAllowed : Bool`; dict-set ↦ `HashMap.insert`. Inserted LAST, so it overrides any incoming `blank` — matches dict-literal ordering. |
| `return d` | `super().formfield(**{...})` argument dict | R | dict ↦ HashMap |

The spec frames every unchanged key: `result[k]? = base[k]?` for `k ≠ "blank"`
(directive 5), and pins the new key to `blankAllowed`.

## Independently-observable behaviors (G-DIFF)

- `Solution_prepatch_1.lean`: drops the radio branch from behavior 1's condition
  (`if required && initialPresent`). The carried gold proof of
  `correct_emptyOption` fails to close. (FAIL_TO_PASS:
  `test_choices_radio_blank`, `test_non_blank_foreign_key_with_radio`.)
- `Solution_prepatch_2.lean`: omits the `blank` insertion in behavior 2 (the
  pre-patch dict). The carried gold proof of `correct_formKwargs` fails to
  close. (Without this plumbing, behavior 1 never receives a non-default
  `blank`, so the radio fix is unreachable from a ModelForm; tests
  `test_blank_foreign_key_with_radio` / `test_non_blank_foreign_key_with_radio`.)
