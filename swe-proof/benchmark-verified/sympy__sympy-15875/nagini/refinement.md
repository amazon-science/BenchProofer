# refinement.md — sympy__sympy-15875

The operation-by-operation correspondence between `model.py`'s implementation
(`add_is_zero`, the deep model of the commutative-sum zeroness decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real routine by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `_eval_is_zero(self)` (`sympy/core/add.py:532`)

Gold hunk (`sympy/core/add.py:557`):
```
- if len(nz) == len(self.args):
+ if len(nz) == 0 or len(nz) == len(self.args):
     return None
```

The routine scans `self.args`, classifying each summand by its assumption
queries (`is_real` / `is_zero` / `is_imaginary` / `(I*a).is_real`) into the
accumulators `z` (real-zero count), `nz` (the list of real-nonzero summands),
`im`, `im_or_z`, with two early `return` (→ None) classes (real-undetermined
and "other"). It then forms `b = self.func(*nz)` (the sum of the real-nonzero
summands) and decides from `b.is_zero` combined with `im` / `im_or_z`.

Model carriers: the summands are a `List[int]` `classes` of class tags
(0..5 = real-zero / real-nonzero / real-undetermined / imaginary /
imaginary-or-zero / other); the three-valued `b.is_zero` is the parameter
`sub_is_zero: Optional[bool]`.

| # | model.py impl op (`add_is_zero`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `classes: List[int]`, each in 0..5 | `self.args` (an ordered tuple of `Expr`) | R | one tag per summand records the branch the real `for a in self.args` loop takes; the loop's only effect on a summand is which accumulator it touches, which the tag names (mapping.md §2). |
| A2 | the backward loop: `if c==0: z+=1`, `elif c==1: nz+=1`, `elif c==2/5: has2/has5=True (→ None)`, `elif c==3: im=True`, `elif c==4: im_or_z=True` | the real `for a in self.args` body: `if a.is_real: …z+=1 / nz.append(a) / return`; `elif a.is_imaginary: im=True`; `elif (I*a).is_real: im_or_z=True`; `else: return` | I + R | identical control flow; `nz.append(a)` ↔ incrementing the count `nz` (only `len(nz)` is consulted later — mapping.md §2); the two bare `return` (real-undetermined, other) ↔ setting `has2`/`has5` then returning `None` (observationally identical net result — §B). |
| A3 | `if has2 or has5: return None` | the two in-loop bare `return` statements | R | the real bare `return` yields `None`; the model defers the same `None` to a single post-loop test of the two existence flags. The result is identical because the only observable effect of either bare `return` is `None`, and the presence of a class-2 or class-5 summand anywhere is what triggers it (order does not change the `None` outcome). |
| A4 | `if z == n: return True` | `if z == len(self.args): return True` | I + R | `z` ↔ `z`; `n == len(classes)` ↔ `len(self.args)` (R: one tag per summand). |
| A5 | `if nz == 0 or nz == n: return None` | `if len(nz) == 0 or len(nz) == len(self.args): return None` — **the patched line** | I + R | `nz` (count of class-1 tags) ↔ `len(nz)` (length of the real-nonzero list); `n` ↔ `len(self.args)`. This is the line the gold patch changes; it is modeled **identically** (`nz == 0 or nz == n`). The discriminating clause `nz == 0` is exactly the added disjunct. |
| A6 | `if sub_is_zero is None: return None` / `if sub_is_zero: (im/im_or_z combination) else: return False` | `b = self.func(*nz); if b.is_zero: (im/im_or_z combination); if b.is_zero is False: return False` | R + A-reference | `sub_is_zero` ↔ `b.is_zero`, the three-valued zeroness of the sum of the real-nonzero summands (`b = self.func(*nz)`). `b.is_zero` is the unchanged recursive assumption query the routine already used; the patch does not touch it. It is abstracted as the parameter `sub_is_zero`, whose realized value is observed and validated against the routine by `axiom_check.py` (G-AX, §C). The model's branch structure (`is None` / truthy / falsy) mirrors `if b.is_zero:` / `if b.is_zero is False:` exactly. |
| A7 | the empty real-nonzero sub-expression is itself zero — precondition `count_eq(classes,1)==0 ⇒ sub_is_zero == True` | `b = self.func()` is `S.Zero`, whose `is_zero` is `True` | R | when no summand is class 1, `b = self.func(*[]) = S.Zero`; `S.Zero.is_zero is True`. This is a fact about the unchanged callee `self.func()` on no arguments, recorded as the precondition that links the two inputs (and validated by G-AX, where empty-`nz` cases always observe `sub_is_zero == True`). |

The discriminating content of the change — the verdict on a sum with **no**
real-nonzero summands but some imaginary classes (e.g. the issue witness
`-2*I + (1+I)**2`, two imaginary summands) — lives in the added `nz == 0`
disjunct. Pre-fix, with `nz == 0`, `b = self.func() = 0`, `b.is_zero == True`,
and the `im and not im_or_z` branch returns the wrong `False`; the fix returns
`None` instead. `model_prepatch.py` reproduces the pre-fix line
(`if nz == n: return None`, without the `nz == 0` disjunct) and **fails** the
postcondition clause "no real-nonzero information, or it is the whole sum ⇒
`Result() is None`" — exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the control-flow guard `len(nz) == 0 or …` — is an **integer
comparison**, modeled **identically** (`nz == 0 or nz == n`, step A5). The only
opaque value, the recursive `b.is_zero`, is an **unchanged** query the patch
does not touch; it is abstracted as `sub_is_zero` and validated as an
**A-reference** by G-AX (the deep model `add_is_zero` reproduces the real
`_eval_is_zero` for the observed `(classes, sub_is_zero)`). There is **no
consumed `@ContractOnly` axiom** — the bundle's only callee dependency
(`b.is_zero`) enters as a parameter, not as an axiom the proof's `Ensures`
quantify over.

## C. verify(model) ⇒ resolved

`add_is_zero` verifies only if, on the discriminating class profile (`nz == 0`,
no class-2/5 summand, not all class-0), it returns `None` (postcondition A5
clause), and only if every other class profile matches the routine's verdict
(the remaining postcondition clauses, which cover the full decision table).
The postconditions PARTITION the entire reachable input domain: in the active
region (no class-2/5, not all class-0, `0 < nz < n`) every fall-through outcome
is positively pinned by an `Ensures` — including the two undecidable
fall-throughs (`sub_is_zero is None ⇒ None`, and `sub_is_zero` true with a
class-4 imaginary-or-zero summand present ⇒ `None`). No verifying implementation
can return a definite verdict where the gold routine returns `None`; every
class profile's three-valued outcome is fixed by exactly one clause (validated
against the real patched routine by G-AX over 400 boundary + 15105 fuzz cases,
all three `sub_is_zero` values).
By R (one tag per summand; integer `z`/`nz`/`n` ↔ `z`/`len(nz)`/`len(self.args)`;
`sub_is_zero` ↔ `b.is_zero`) the verified routine equals the patched
`_eval_is_zero` on every observed input; by G-AX (`axiom_check.py`) the deep
model `add_is_zero` reproduces the real patched routine over the issue witness
+ 400 boundary + 15000 fuzz `Add` expressions (all three `sub_is_zero` values),
and the gold patch makes the F2P test `test_Add_is_zero` pass while the pre-fix
code fails it (G-RESOLVE, confirmed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
validated A-reference — and the gold patch resolves. The trust points are
exactly the two of PLAN §1.1: A-reference (deep-model) soundness (G-AX) and
refinement fidelity (this document, G-EQ).
