# mapping.md — pytest-dev__pytest-5631

Binds every `model.py` symbol to its repository counterpart at
`base_commit = cb828ebe70b4fa35cd5f9a7ee024272237eab351`, states the type
abstraction, and gives the provenance of the runtime semantics the deep model
is validated against.

Repo file under change: `src/_pytest/compat.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `count_mock_patch_args(kinds)` | `num_mock_patch_args(function)` — `src/_pytest/compat.py:62` (body 64-73) | the modeled changed function: counts how many mock-patch directives stand in for a runner-supplied argument |
| `counts_as_mock(kind)` *(deep model — A-reference)* | the per-directive membership decision `not p.attribute_name and p.new is <sentinel>` — post-patch `src/_pytest/compat.py:71-78` | pure spec: the TOTAL identity decision for one directive |
| `count_sentinel_directives(s)` *(deep model)* | `len([p for p in patchings if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)])` — post-patch `compat.py:69-78` | pure spec: the count as a front-recursive fold over the directive kinds |
| `NonTruthEvaluableEquality` (exception class) | the `ValueError("The truth value of an array … is ambiguous")` raised by `p.new in sentinels` when `p.new` is a NumPy array — pre-patch `compat.py:70-72` | user-defined stand-in for the pre-patch failure the new behaviour forbids (builtin exception in `Exsures` crashes the translator) |

The pre-patch repo symbols the change removes/replaces (for the refinement
audit, not referenced from the consumer spec view): the `mock_modules`/
`sentinels` lists and the `p.new in sentinels` value-equality membership
(`compat.py:67-72`), and the unconditional `return len(patchings)` fallback
(`compat.py:73`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `function.patchings` — a sequence of `unittest.mock._patch` directive objects | `List[int]` of per-directive **kind tags** | one list element per directive; element value is the directive's kind (below). `len(patchings)` ↔ `len(kinds)`; iteration order preserved. |
| a single `_patch` directive `p`, observed only via `p.attribute_name` and `p.new` | one integer kind tag in `{0,1,2,3}` | the helper reads ONLY these two attributes of `p`; the kind tag records exactly the three observable cases that determine the outcome (see below). The directive's other fields are not read and are abstracted away. |
| `p.new is mock_sentinel or p.new is ut_mock_sentinel` (identity membership) | `kind == 1` | a directive whose replacement value IS a placeholder singleton by identity. |
| `p.new in sentinels` raising `ValueError` (pre-patch, on array-like `p.new`) | `kind == 3` + a `raise NonTruthEvaluableEquality()` in the prepatch impl | a directive whose replacement value's `__eq__` does not yield a usable boolean. |
| the count returned by `num_mock_patch_args` | `int` result of `count_mock_patch_args` | identical (a non-negative count). |

**Kind tags (the directive abstraction):**

| kind | `p.attribute_name` | `p.new` | counts? | equality membership (`in sentinels`) |
|---|---|---|---|---|
| 0 | set (truthy) | (not inspected) | no | not reached (short-circuit on `not p.attribute_name`) |
| 1 | None/empty | IS a placeholder singleton (identity) | **yes** | equal → would also count, but raise-free |
| 2 | None/empty | comparable non-placeholder | no | unequal, raise-free |
| 3 | None/empty | non-truth-evaluable `__eq__` (array-like) | no (by identity) | **RAISES** `ValueError` (the bug) |

Nagini bans attribute reflection over heterogeneous objects, so the directive
sequence is carried as a `List[int]` of these kind tags; the specification is
phrased over `PSeq[int]` via `ToSeq`. The membership decision is proven by a
backward per-directive fold (front-recursive `count_sentinel_directives` gives a
single unfold per loop step).

## 3. Deep-model / runtime-semantics provenance (checked by G-AX / axiom_check.py)

### 3.1 `counts_as_mock` / `count_sentinel_directives` deep model ↔ identity membership (A-reference)

There is **no consumed `@ContractOnly` axiom**: the membership decision is the
operation the patch CHANGES, so it is modelled **deeply** (per directive 7 /
SPEC_GUIDE §3 — never axiomatize the thing that changed). The deep model is
validated against the real runtime semantics out-of-band by axiom_check.py
(G-AX).

**Post-patch source** (`src/_pytest/compat.py:64-78`):
```python
    patchings = getattr(function, "patchings", None)
    if not patchings:
        return 0
    mock_sentinel = getattr(sys.modules.get("mock"), "DEFAULT", object())
    ut_mock_sentinel = getattr(sys.modules.get("unittest.mock"), "DEFAULT", object())
    return len(
        [p for p in patchings
         if not p.attribute_name
         and (p.new is mock_sentinel or p.new is ut_mock_sentinel)]
    )
```

The placeholder singletons are `mock.DEFAULT` / `unittest.mock.DEFAULT`
(`unittest.mock` defines `DEFAULT = sentinel.DEFAULT`, a process-unique singleton
object). The decision `p.new is <sentinel>` is the Python **identity** operator
`is`, which is TOTAL: it evaluates to a definite `True`/`False` for any object
without invoking `__eq__`, so it can never raise — including on a NumPy array or
the issue's `NumpyLike` object. This is what `counts_as_mock`/`count_sentinel_
directives` encode: count a directive iff it binds no attribute name (kind != 0)
and its value is a placeholder singleton by identity (kind == 1).

When a mock module is not loaded, `getattr(..., "DEFAULT", object())` yields a
**fresh** `object()` no `p.new` can be identical to, so the comprehension counts
0 — equivalent, for the F2P/P2P tests (which import `unittest.mock`, so it IS
loaded), to the loaded-module path. The F2P test populates `patchings` via an
actual `@patch(...)` decorator, so `unittest.mock` is in `sys.modules`; the
modeled path is the mock-loaded path. (Flag dependency recorded for G-AX: the
sentinels are `unittest.mock.DEFAULT`; the identity decision is independent of
the comparison configuration.)

**Pre-patch source** (`src/_pytest/compat.py:67-73`) — the bug:
```python
    mock_modules = [sys.modules.get("mock"), sys.modules.get("unittest.mock")]
    if any(mock_modules):
        sentinels = [m.DEFAULT for m in mock_modules if m is not None]
        return len([p for p in patchings if not p.attribute_name and p.new in sentinels])
    return len(patchings)
```

`p.new in sentinels` is value-equality membership: it evaluates `p.new == s` for
each sentinel and truth-tests the result. When `p.new` is a NumPy array, `==`
returns an array and truth-testing it raises
`ValueError: The truth value of an array with more than one element is ambiguous`
(issue #5606, traceback in the problem statement). The model abstracts this as
kind 3 with a `raise NonTruthEvaluableEquality()` in the prepatch impl.

**Soundness check (G-AX):** `axiom_check.py` constructs real directive objects
over the real `unittest.mock.DEFAULT` placeholder singleton, a `NumpyLike` object
whose `__eq__` raises (the issue's reproducer, copied from the F2P test
`test_mock_sentinel_check_against_numpy_like`), comparable non-placeholders, and
attribute-bound directives. It asserts: (1) the identity decision is total and
exactly identifies the sentinel (never raises, even on `NumpyLike`); (2) the
pre-patch value-equality membership RAISES on the `NumpyLike` value while
identity does not; (3) `count_sentinel_directives` over the kind tags equals the
real identity-decision count over the population, with `0 <= count <= len`, on 7
boundary + 20000 randomized fuzz populations. Exit 0 iff sound. It imports only
`unittest.mock` and `random` from the standard library — `unittest.mock` is the
very module the patched code consults for its placeholder singleton.

Docs: `unittest.mock` — https://docs.python.org/3/library/unittest.mock.html
(`patch` records its directives in `function.patchings`; `DEFAULT` is the
sentinel used when no `new`/`new_callable` is supplied). The `is` operator is
identity comparison: https://docs.python.org/3/reference/expressions.html#is.
