# refinement.md — django__django-11603

Operation correspondence between the Lean `implementation_construct` skeleton and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the construction is modeled deeply with
concrete Lean operations. Every row is **R** or **I**. (G-AX is therefore a skip
stub; the R/I legs are differential-tested by G-CONF.)

## What the gold patch changes

`patch.diff` adds `allow_distinct = True` to the averaging aggregate class
(`Avg`) and the summation aggregate class (`Sum`) in
`django/db/models/aggregates.py`. `allow_distinct` is the per-class policy
attribute read by `Aggregate.__init__`:

```python
def __init__(self, *expressions, distinct=False, filter=None, **extra):
    if distinct and not self.allow_distinct:
        raise TypeError("%s does not allow distinct." % self.__class__.__name__)
    self.distinct = distinct
    self.filter = filter
    super().__init__(*expressions, **extra)
```

The two-line data change to the class attributes is the patch.diff; the OBSERVED
behavior it changes is `Aggregate.__init__`'s control flow for `Avg`/`Sum`. The
Lean impl models that behavior with the per-kind policy folded into the
`permitted` lookup, so the policy edit on `Avg`/`Sum` appears as those two kinds
moving from the reject-distinct branch to the accept branch.

## `implementation_construct` ↔ `Aggregate.__init__` (+ class `allow_distinct`)

| Lean op | patch.diff / base counterpart | tag | note |
|---|---|---|---|
| `let permitted := match kind with .avg/.count/.sum => true \| _ => false` | `self.allow_distinct` per concrete class, AS PATCHED (`Avg`/`Count`/`Sum` → `True`; `Max`/`Min`/`StdDev`/`Variance` → `False`) | R | the class-attribute policy ↦ a per-`AggKind` Boolean. The patch flips `Avg`/`Sum` from `False`→`True`; this lookup encodes the post-patch policy. `Count`'s `True` is pre-existing (aggregates.py:108). |
| `if distinct && !permitted then return Except.error AggError.distinctNotAllowed` | `if distinct and not self.allow_distinct: raise TypeError("… does not allow distinct.")` | R | `and`/`not` ↦ `&&`/`!`; `raise TypeError(…)` ↦ early `return Except.error AggError.distinctNotAllowed`. The single raise this branch produces ↦ the single `AggError` constructor. |
| `let mut st := { kind, distinct := false, filter := none }` | the object under construction before its fields are assigned | I | accumulator init; fields overwritten below |
| `st := { st with distinct := distinct }` | `self.distinct = distinct` | R | `bool` ↦ `Bool`; attribute set ↦ structure field update |
| `st := { st with filter := filter }` | `self.filter = filter` | R | filter expression `\| None` ↦ `Option String` (presence abstraction); attribute set ↦ field update |
| `return Except.ok st` | successful return from `__init__` (object constructed); `super().__init__(*expressions, **extra)` | R | the constructed aggregate ↦ `Except.ok AggState`. `super().__init__` (storing the wrapped expressions on the `Func` base) is unchanged by the patch and orthogonal to the distinct observable, so it is abstracted out of the modeled state — not an op in the skeleton. |

The result carrier `Except AggError AggState` captures the precise observable the
F2P test `test_distinct_on_aggregate` asserts: `Avg('rating', distinct=True)`,
`Count('rating', distinct=True)`, `Sum('rating', distinct=True)` must each
CONSTRUCT (no `TypeError`) — i.e. land in the `Except.ok` branch — whereas at
base_commit `Avg`/`Sum` with `distinct=True` raised.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: encodes the base_commit policy (only the counting
  kind permits distinct). The carried gold proof of `correct_construct` fails to
  close precisely on the `avg`/`sum` × `distinct=true` cases — the spec demands
  `Except.ok` there, the buggy impl yields `Except.error`. That is the exact
  FAIL_TO_PASS behavior (`test_distinct_on_aggregate`: `Avg`/`Sum` with
  `distinct=True`). A single prepatch suffices: `Avg` and `Sum` are fixed by the
  same one-attribute mechanism, and both are discriminated by this prepatch.
