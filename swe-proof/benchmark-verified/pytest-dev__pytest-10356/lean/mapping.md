# mapping.md — pytest-dev__pytest-10356

## Symbol binding (file:line @ base_commit 3c1534944c)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_inheritedMarks` / `problem_spec_inheritedMarks` / `correct_inheritedMarks` | `get_unpacked_marks(obj, *, consider_mro)`, the class branch (`isinstance(obj, type)` true) | `src/_pytest/mark/structures.py:358-363` @ base_commit (rewritten to lines `358-385` post-patch) |
| `wholeHierarchy : Bool` | the `consider_mro` keyword parameter | gold patch, `structures.py` (new kw, default `True`) |
| `hierarchy : List ClassMarks` | `[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` (each class's OWN stored entry, MRO order) | gold patch, `structures.py:367` |

The modeled function is `get_unpacked_marks`. Pre-patch it read a single
attribute via `getattr(obj, "pytestmark", [])`; because Python resolves an
attribute along the MRO to the first class that defines it, a class inheriting
from two labelled base classes saw only one base's labels. The post-patch code,
for a class, reads each class's OWN `__dict__["pytestmark"]` along the full
`__mro__` and concatenates them (each entry flattened from list/single form),
preserving order and duplicates; `normalize_mark_list` then coerces decorators to
`Mark` objects.

```python
# POST-PATCH class branch (modeled):
if not consider_mro:
    mark_lists = [obj.__dict__.get("pytestmark", [])]
else:
    mark_lists = [x.__dict__.get("pytestmark", []) for x in obj.__mro__]
mark_list = []
for item in mark_lists:
    if isinstance(item, list):
        mark_list.extend(item)
    else:
        mark_list.append(item)
return list(normalize_mark_list(mark_list))
```

## Modeled branch / configuration

This bundle models the **class** branch (`isinstance(obj, type)` true) — exactly
the branch the patch adds and the one `test_mark_mro` exercises (it calls
`get_unpacked_marks(C)` and `get_unpacked_marks(C, consider_mro=False)` on a
class `C(A, B)`). The non-class branch (a test function carrying `pytestmark`)
keeps the pre-patch single-attribute semantics and is out of scope; it is
unchanged behavior, covered by the PASS_TO_PASS `TestFunctional` tests.

The `__mro__` linearization itself is supplied by Python (C3); the modeled
`hierarchy` is the already-linearized sequence of per-class stored entries, so
the Lean model is independent of how the MRO is computed. G-CONF builds the real
classes and reads their real `__mro__`, so the linearization is exercised
end-to-end against the shadow.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a class's stored `pytestmark` (a `list` of marks) | `ClassMarks.many xs` | list of marks ↦ `List Mark` |
| a class's stored `pytestmark` (a single bare mark, non-list) | `ClassMarks.one m` | bare value ↦ single label |
| `[cls.__dict__.get("pytestmark", []) for cls in obj.__mro__]` | `hierarchy : List ClassMarks` | per-class own entry, MRO order; index 0 = the class itself; a class with no stored entry ↦ `ClassMarks.many []` |
| `consider_mro: bool` | `wholeHierarchy : Bool` | `True ↦ true` (walk whole MRO), `False ↦ false` (class's own entry only) |
| a `Mark(name, args, kwargs)` | `Mark {name, args}` | compared on the observable `(name, args)`; `kwargs` not observed by the modeled behavior |
| `list(get_unpacked_marks(obj, consider_mro=…))` | `result : List Mark` | element-for-element, by `(name, args)` |

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed op (walking `__mro__` and gathering
  each class's own labels) is the operation the patch introduces, so it is
  modeled DEEPLY (an A-reference validated by G-CONF against the real
  `get_unpacked_marks`), never axiomatized (§0.7).
- `normalize_mark_list` (unchanged) is an order-preserving coercion that yields
  each entry's `Mark` (identity on values that are already `Mark` objects); it is
  reproduced concretely by `flattenClassMarks` (which simply forwards the stored
  labels), so no axiom is needed. The modeled observable (name + args) is
  invariant under it.
- Flag dependency: `consider_mro` selects whole-MRO vs class-own gathering.
  G-CONF fuzzes BOTH values so each branch is differential-tested.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
