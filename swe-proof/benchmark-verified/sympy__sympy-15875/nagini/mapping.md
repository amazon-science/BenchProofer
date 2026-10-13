# mapping.md — sympy__sympy-15875

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b506169ad727ee39cb3d60c8b3ff5e315d443d8e`, states the type
abstraction, and gives the provenance of the one deep-model reference.

Repo file under change: `sympy/core/add.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `add_is_zero(classes, sub_is_zero)` | `Add._eval_is_zero(self)` — `sympy/core/add.py:532` (changed line 557) | the modeled changed function (commutative-sum zeroness decision) |
| `classes: List[int]` | `self.args` — the ordered tuple of summands of the `Add` | input: one class tag per summand |
| `sub_is_zero: Optional[bool]` | `b.is_zero` where `b = self.func(*nz)` — `add.py:559-560` | input: three-valued zeroness of the sum of the real-nonzero summands (the unchanged recursive query) |
| `count_eq(s, c)` / `has_eq(s, c)` | the loop accumulators `z`, `len(nz)`, `im`, `im_or_z` and the two bare-`return` classes (`add.py:537-554`) | pure spec: per-class count / existence over the class tags |

The class tags 0..5 encode the branch the real `for a in self.args` loop
(`add.py:541-554`) takes for a summand `a`:

| tag | real condition | loop effect (`add.py`) |
|---|---|---|
| 0 | `a.is_real and a.is_zero` | `z += 1` (542-544) |
| 1 | `a.is_real and a.is_zero is False` | `nz.append(a)` (545-546) |
| 2 | `a.is_real and a.is_zero is None` | bare `return` → None (547-548) |
| 3 | `a.is_imaginary` | `im = True` (549-550) |
| 4 | not imaginary, `(S.ImaginaryUnit*a).is_real` | `im_or_z = True` (551-552) |
| 5 | none of the above | bare `return` → None (553-554) |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.args` (tuple of `Expr` summands) | `classes: List[int]` of class tags | summand `a` ↔ its tag `classify(a) ∈ {0..5}`; `len(self.args)` ↔ `len(classes)`; the loop reads each `a` once and routes to exactly one accumulator — the tag names that accumulator |
| `nz` (the list of real-nonzero summands) | the count `count_eq(classes, 1)` | only `len(nz)` is consulted (`add.py:557`) and `b = self.func(*nz)` whose `is_zero` is abstracted by `sub_is_zero`; the elements of `nz` themselves are not otherwise inspected — so the count + `sub_is_zero` fully determine the routine's behaviour |
| `z` (int) / `im`, `im_or_z` (bool) | `count_eq(classes,0)` / `has_eq(classes,3)`, `has_eq(classes,4)` | identical integer/boolean accumulators |
| `b.is_zero` (three-valued: `True`/`False`/`None`) | `sub_is_zero: Optional[bool]` (`None` = undecided) | `True`↔`True`, `False`↔`False`, `None`↔`None`; the routine branches `if b.is_zero:` / `if b.is_zero is False:` ↔ model `if sub_is_zero:` / `else` |
| the verdict (`True`/`False`/`None` / bare `return`) | `Optional[bool]` return | `True`↔True, `False`↔False, every `None`/bare-`return`↔`None` |

`self.args` is an opaque tuple of sympy `Expr` (the assumption engine is far
outside Nagini's fragment), so the carrier abstracts each summand to the single
integer tag that records the branch the loop takes; the specification is phrased
over `PSeq[int]` via `ToSeq`, with front-recursive `count_eq` / `has_eq` folds.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `add_is_zero` deep model ↔ patched `Add._eval_is_zero` (A-reference)
**Routine:** `Add._eval_is_zero(self)` at the PATCHED commit (`add.py:532-566`).
The entire decision procedure is modeled **deeply** by `add_is_zero` over the
class-tag carrier; there is **no consumed `@ContractOnly` axiom**. The deep
model is validated equal to the real routine out-of-band by `axiom_check.py`
(G-AX). The single opaque value the routine consults — `b.is_zero` for
`b = self.func(*nz)` — is the **unchanged recursive assumption query** (the
patch changes only the control-flow guard on line 557, never how `b.is_zero` is
computed); it enters the model as the parameter `sub_is_zero`. When `nz` is
empty, `b = self.func() = S.Zero` and `S.Zero.is_zero is True`, recorded as the
model precondition `count_eq(classes,1)==0 ⇒ sub_is_zero == True`.

Patched source under model (`sympy/core/add.py`, post-patch):
```python
def _eval_is_zero(self):
    if self.is_commutative is False:
        return
    nz = []
    z = 0
    im_or_z = False
    im = False
    for a in self.args:
        if a.is_real:
            if a.is_zero:        z += 1
            elif a.is_zero is False: nz.append(a)
            else:                return
        elif a.is_imaginary:     im = True
        elif (S.ImaginaryUnit*a).is_real: im_or_z = True
        else:                    return
    if z == len(self.args):      return True
    if len(nz) == 0 or len(nz) == len(self.args): return None   # <- patched
    b = self.func(*nz)
    if b.is_zero:
        if not im_or_z and not im: return True
        if im and not im_or_z:     return False
    if b.is_zero is False:         return False
```
(`self.is_commutative is False` returns `None`; this bundle models the
commutative case the issue is about — a noncommutative summand is outside the
class palette and not exercised, faithfully matching the `return` on 533-536
that also yields `None`.)

**Soundness check (G-AX):** `axiom_check.py` runs the REAL patched
`_eval_is_zero` on the exact issue witness `-2*I + (1+I)**2`, on curated
boundary multisets (real-nonzero + imaginary, all-imaginary empty-real-part,
real-nonzero + imaginary-or-zero, undetermined/other present, …), and on
~15000 randomized fuzz `Add` expressions built from a palette that realizes
every summand class, using FRESH symbols per case so sympy's process-global
assumption cache cannot bleed across cases. It asserts the deep model
`add_is_zero` equals the routine's verdict for the class vector + `sub_is_zero`
observed exactly as the routine observes them, exercising all three
`sub_is_zero` values. Exit 0 iff sound. Imports only `sympy` (the package under
test). Provenance of the change: GitHub sympy/sympy issues #15873 / #15872
(matrix rank), the assumption handler added in PR #10298; docstring of
`Expr.is_zero` (three-valued `True`/`False`/`None`).

Note on the public observable: `(-2*I + (1+I)**2).is_zero` evaluated as a
standalone property is sensitive to sympy's global assumption cache (an upstream
artifact); the F2P test `test_Add_is_zero` runs it under the harness where the
gold patch makes it reliably `None` (G-RESOLVE confirms the patch resolves and
the pre-fix code fails the test). G-AX therefore validates the deep model
against the routine's own `_eval_is_zero` under a single consistent observation,
which is deterministic.
