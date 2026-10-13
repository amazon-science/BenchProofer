# refinement.md — astropy__astropy-7166

The operation-by-operation correspondence between `model.py`'s implementation
(the `apply_inheritance` impl region — the modeled body of the docstring-
inheritance loop) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses an axiom's `Ensures`, **A-reference** where a deep model / abstract
field is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The docstring-inheritance decision — `InheritDocstrings.__init__`

The patch changes the eligibility guard inside the `for key, val in
dct.items()` loop of `InheritDocstrings.__init__`
(`astropy/utils/misc.py`, body lines 528-540 @ base_commit). Effective hunk
(ignoring the cosmetic blank-line deletions at the top of the file):

```
-            if (inspect.isfunction(val) and
-                is_public_member(key) and
-                val.__doc__ is None):
+            if ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and
+                    is_public_member(key) and
+                    val.__doc__ is None):
                 for base in cls.__mro__[1:]:
                     super_method = getattr(base, key, None)
                     if super_method is not None:
                         val.__doc__ = super_method.__doc__
                         break
```

The model models **one iteration of the loop** as `apply_inheritance(m)`: the
`for key, val in dct.items()` iteration is unchanged scaffolding; the entire
behavioural change lives in the loop body, which is what the model pins. (Per
SPEC_GUIDE §3 we model the changed decision, not the unchanged iteration — the
loop body is the patched hunk; astropy-14096 models one resolution likewise.)

| # | model.py impl op (`apply_inheritance`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `m.is_callable_member` (bool field) | `inspect.isfunction(val)` | R / A-reference | the result of the unchanged stdlib predicate is carried as a bool field. The abstraction (a function -> `True`; a property -> `False`) is validated == the real `inspect.isfunction` by axiom_check.py (G-AX). mapping.md §3.1. |
| A2 | `m.is_computed_attribute` (bool field) | `inspect.isdatadescriptor(val)` | R / A-reference | the result of the unchanged stdlib predicate (the call the patch ADDS) is carried as a bool field. Validated == real `inspect.isdatadescriptor` (a property -> `True`; a function/plain attr -> `False`) by axiom_check.py (G-AX). mapping.md §3.2. |
| A3 | `m.is_callable_member or m.is_computed_attribute` | `inspect.isfunction(val) or inspect.isdatadescriptor(val)` | I | the changed operation is exactly this boolean disjunction of the two predicate results; an identical concrete `or`. This IS the fix. |
| A4 | `m.is_public` (bool field) | `is_public_member(key)` | R / A-reference | result of the unchanged local predicate carried as a bool field; its key-classification is checked by axiom_check.py against the real `is_public_member`. mapping.md §3.3. |
| A5 | `not m.has_own_doc` | `val.__doc__ is None` | R | `has_own_doc` is `val.__doc__ is not None`; `not has_own_doc` ↔ `val.__doc__ is None`. A docstring is modeled by an `int` identity (0 = no docstring); the observable is whether a docstring is present/assigned, not its characters. mapping.md §2. |
| A6 | `... and ... and ...` (the guard conjunction) | `(... ) and is_public_member(key) and val.__doc__ is None` | I | identical short-circuit conjunction. |
| A7 | `m.doc = m.inherited_doc` | the MRO walk `for base in cls.__mro__[1:]: super_method = getattr(base, key, None); if super_method is not None: val.__doc__ = super_method.__doc__; break` | R / A-reference | the assignment of the inherited docstring. The MRO walk + `getattr` that RESOLVES which base docstring to copy is **unchanged** by the patch; its result is carried as `m.inherited_doc` (a docstring `int`). The model assigns that resolved value to `m.doc`, mirroring `val.__doc__ = super_method.__doc__`. The resolution is unchanged scaffolding, abstracted as the input `inherited_doc`. mapping.md §2, §3.4. |
| A8 | (no assignment when guard false) | (loop falls through; `val.__doc__` untouched) | I | when the guard is false the body assigns nothing; the docstring is left as-is. Pinned by the model's `Ensures(... m.doc == Old(m.doc))`. |

## B. The discriminating change and the prepatch

The behavioural delta is **A2+A3**: the guard gains the `or
inspect.isdatadescriptor(val)` disjunct. The discriminating member kind is a
**computed-attribute member (a `property`)**: real-callee fact (G-AX)
`inspect.isfunction(property) is False` but `inspect.isdatadescriptor(property)
is True`. So a public, undocumented property:
- pre-patch (`isfunction` only): guard is `False and ... = False` -> docstring
  NOT filled;
- post-patch: guard is `(False or True) and ... = True` -> docstring filled
  from the base.

`model_prepatch.py` reproduces the `isfunction`-only guard
(`if m.is_callable_member and m.is_public and not m.has_own_doc`) with a
**byte-identical spec**, and **fails** the postcondition

```
Implies(fills_docstring(Old(is_callable_member), Old(is_computed_attribute),
                        Old(is_public), Old(has_own_doc)),
        m.doc == Old(m.inherited_doc))
```

on exactly the member with `is_callable_member == False`,
`is_computed_attribute == True`, `is_public`, `not has_own_doc` — i.e. the
property the F2P test (`test_inherit_docstrings`, the new `bar` property)
exercises. This is the spec sensing the change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the eligibility guard's disjunction — is the **identical** boolean
`or` (A3, kind I) over two unchanged-predicate results. There is **no consumed
`@ContractOnly` axiom**: the introspection-callee results and the MRO docstring
resolution are unchanged computations carried as already-computed fields
(R / A-reference), validated against the real callees by axiom_check.py (G-AX).
We do not axiomatize the function under change, and we ship no dead axiom.

## D. verify(model) ⇒ resolved

`apply_inheritance` verifies only if (i) when the member is eligible under the
disjunctive guard (callable OR computed-attribute, public, no own docstring)
its docstring becomes the resolved inherited docstring (A3+A7), and (ii)
otherwise the docstring is unchanged (A8). By R (bool fields ↔ unchanged
predicate results; `int` docstring identity ↔ `str.__doc__`; `inherited_doc` ↔
the unchanged MRO `getattr` resolution) and G-AX (the abstractions equal the
real `inspect.isfunction` / `inspect.isdatadescriptor` / `is_public_member`),
the verified body equals the gold patch's loop body on the tested member kinds.
A public undocumented property therefore has its base docstring filled in,
which is exactly what the F2P `test_inherit_docstrings` asserts
(`Subclass.bar.__doc__ == "BAR"`). The gold patch resolves (G-RESOLVE). The
trust points are the two of PLAN §1.1: axiom/abstraction soundness (G-AX, this
bundle's A-reference fields) and refinement fidelity (this document, G-EQ).
