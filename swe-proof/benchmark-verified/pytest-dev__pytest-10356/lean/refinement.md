# refinement.md — pytest-dev__pytest-10356

Operation correspondence between `implementation_inheritedMarks` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (walking the
resolution order and gathering each class's own stored labels) is modeled DEEPLY
as the per-class flatten + concatenation. Every row is **R**, **A-reference**, or
**I**. The R/I/A-reference legs are differential-tested by G-CONF; G-AX is a skip
stub (no consumed callee axiom).

## `implementation_inheritedMarks` ↔ the class branch of `get_unpacked_marks`

The gold patch turns

```python
def get_unpacked_marks(obj):                       # PRE-PATCH
    mark_list = getattr(obj, "pytestmark", [])
    if not isinstance(mark_list, list):
        mark_list = [mark_list]
    return normalize_mark_list(mark_list)
```

into (class case, `consider_mro` default `True`):

```python
def get_unpacked_marks(obj, *, consider_mro=True):  # POST-PATCH
    if isinstance(obj, type):
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
    else:
        ...   # non-class case: unchanged single-attribute read
    return list(normalize_mark_list(mark_list))
```

The bundle models the **class** branch (`isinstance(obj, type)` true) — the one
the patch introduces and the one the issue and F2P test exercise.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `hierarchy : List ClassMarks` argument | `[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` (each class's OWN stored entry, MRO order) | R | the class chain's per-class stored attribute ↦ a list of stored entries; `__mro__[0]` = the class itself ↦ `hierarchy[0]` |
| `let markLists := if !wholeHierarchy then [hierarchy.headD …] else hierarchy` | `if not consider_mro: mark_lists = [obj.__dict__.get("pytestmark", [])] else: mark_lists = [… for x in obj.__mro__]` | A-reference | the EDITED control: full mode walks the WHOLE chain; restricted mode reads only the class's own entry. Modeled deeply; validated == real `get_unpacked_marks` by G-CONF |
| `for item in markLists … match .many xs => ++ xs / .one m => ++ [m]` | `for item in mark_lists: if isinstance(item, list): extend(item) else: append(item)` | I | per-entry flatten + concatenation, preserving order and duplicates |
| `flattenClassMarks` (list passes through; bare label ↦ `[label]`) | `normalize_mark_list` coercion of each entry (already-Mark identity on names+args) | A-reference | order-preserving identity on values already labels; validated by G-CONF (observable = name+args) |
| `return markList` | `return list(normalize_mark_list(mark_list))` | R | gathered label list ↦ `List Mark` |

The pre-patch code read a SINGLE resolved `pytestmark` attribute. Because Python
attribute lookup resolves `pytestmark` along the MRO to the FIRST class that
defines it, a class inheriting from two labelled parents saw only the
nearest-defining class's labels — the others were silently lost. The post-patch
code reads each class's OWN `__dict__` entry across the full MRO and concatenates
them, so no ancestor's labels are dropped.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the gathering reads only the head of the chain
  (`[hierarchy.headD …]`) regardless of `wholeHierarchy`, mirroring the
  single-resolved-attribute pre-patch bug. The carried gold proof of
  `correct_inheritedMarks` fails to close on the full-mode clause
  (`result = hierarchy.flatMap flattenClassMarks` is violated whenever the chain
  has more than one labelled class). This is the single fixed behavior.
  (FAIL_TO_PASS: `testing/test_mark.py::test_mark_mro`.)
