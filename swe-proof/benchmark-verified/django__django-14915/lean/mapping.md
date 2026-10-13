# mapping.md — django__django-14915

## Symbol binding (@ base_commit 903aaa35e5ceaa33bfc9b19b7f6da65ce5a91dd4)

| Lean symbol | Python symbol | location |
|---|---|---|
| `ChoiceValue` | `class ModelChoiceIteratorValue` | `django/forms/models.py:1161` |
| `ChoiceValue.val` | `self.value` | `django/forms/models.py:1163` (`__init__`) |
| `ChoiceValue.inst` | `self.instance` | `django/forms/models.py:1164` (`__init__`) |
| `implementation_choiceValueHash` | `ModelChoiceIteratorValue.__hash__` (added by patch) | `django/forms/models.py:1169-1170` (post-patch) |
| `valueHash` | builtin `hash` applied to `self.value` | `django/forms/models.py:1170` (`return hash(self.value)`) |

The changed function under spec is `ModelChoiceIteratorValue.__hash__`. Pre-patch
this method does not exist; because the class defines `__eq__`
(`django/forms/models.py:1166-1169` pre-patch), Python sets `__hash__ = None`,
making instances unhashable. F2P test: `test_choice_value_hash`
(`tests/model_forms/test_modelchoicefield.py`, added by `test_patch`).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean type | Python type | bridge |
|---|---|---|
| `Int` (`m.val`) | `int` (a model primary key) | identity on integers |
| `Option ModelInstance` (`m.inst`) | a model object or `None` | presence/absence only; content never read by the digest |
| `Option Int` (result) | hashable→`hash(value)`, unhashable→`TypeError` on `hash()` | `some d` ↔ `hash(obj) == d`; `none` ↔ `hash(obj)` raises `TypeError`. The digest is modeled as `Int` (Python `hash()` returns a signed `int`). |
| `valueHash : Int → Int` | `hash(value)` (the signed-int digest of an int) | `valueHash v == hash(v)` (CPython `hash(int)` is the int reduced mod a Mersenne prime, signed; we compare the standard wrapper's digest to `hash(value)` for equality of behavior) |

Note on `valueHash`: the modeled property G-AX checks is the *routing* claim —
`hash(ModelChoiceIteratorValue(value, inst)) == hash(value)` for the post-patch
object, independent of `inst`. The exact numeric value of `hash(int)` is a
CPython implementation detail and is NOT pinned by the spec; the spec pins only
that the wrapper's digest equals the value's own digest.

## Callee provenance + flag deps

* `valueHash` (= builtin `hash` on `self.value`): UNCHANGED callee. No flag
  dependence. The patch does not alter it; it only makes the wrapper delegate to
  it. → A-reference (refinement.md op #1), validated by `axiom_check.py`.

## Pinned G-CONF fuzz seed

`SEED = 14915` (also recorded in `conformance_check.py`).
