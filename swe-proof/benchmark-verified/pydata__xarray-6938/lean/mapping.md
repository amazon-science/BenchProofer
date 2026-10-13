# mapping.md — symbol binding & type bijection (pydata__xarray-6938)

## Modeled function
- **Lean** `implementation_toIndexVariable : Array VarRec → Nat → Array VarRec × Nat`
- **Python** `IndexVariable.to_index_variable(self)` —
  `xarray/core/variable.py:2882-2884 @ base_commit c4e40d9`.

```python
def to_index_variable(self):
    """Return this variable as an xarray.IndexVariable"""
    return self            # base (buggy): hands back the SAME object
    # patched:
    return self.copy()     # an independent object
```

The observable contract demanded by the F2P test
(`TestIndexVariable::test_to_index_variable_copy`):

```python
a = IndexVariable("x", ["a"])
b = a.to_index_variable()
assert a is not b          # produced object is a DISTINCT object
b.dims = ("y",)
assert a.dims == ("x",)    # mutating the produced object does not touch the source
```

i.e. the conversion must return a fresh, independent object so that a later
in-place edit (`b.dims = ...`, performed by the caller `Dataset.swap_dims`,
`xarray/core/dataset.py:3774-3775`) cannot mutate the source.

## Type bijection (used by G-CONF + G-AX)
We model the live-object universe as a heap so that object identity and
in-place mutation are representable in referentially-transparent Lean.

| Python | Lean | notes |
|---|---|---|
| the set of live `Variable`/`IndexVariable` objects | `heap : Array VarRec` | one slot per object |
| an object reference (CPython `id`) | a handle `: Nat` (the slot index) | identity; `a is b` ⇔ equal handles |
| `self` (the receiver object's reference) | `src : Nat` | the source handle, `src < heap.size` |
| `IndexVariable.dims` (tuple of dim names) | `VarRec.dims : List Nat` | per-label codes |
| the object's array payload | `VarRec.data : Nat` | opaque contents code (immutable for an index var) |
| the value returned by `to_index_variable` | `(result.1, result.2)` | resulting heap × produced handle |

`.copy()` for an `IndexVariable` (`variable.py:2831`) builds a new object via
`self._replace(data=...)` with the **same** `dims`/`data` fields — a structural
duplicate that is a *different object*. Modeled as: append a new slot whose
record equals `heap[src]`, and return its index `heap.size`. The "different
object" property is the freshness of the new index (`= heap.size`, distinct from
every existing handle, in particular `src`).

## Callee provenance
- `self.copy()` (`IndexVariable.copy`, `variable.py:2831`) — the only callee the
  fix introduces. It is modeled DEEPLY as the fresh-slot duplication (the
  changed op), NOT axiomatized. Hence no `opaque`/`axiom` is needed and there is
  no A-reference deep model to validate against a real callee in isolation
  (the copy semantics ARE the modeled behavior, exercised end-to-end by G-CONF).
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is
  a skip stub.

## Out of model scope (frame)
- The other diff hunks are behavior-preserving and not modeled:
  - `dataset.py` `var: Variable` — a type annotation only (no runtime effect).
  - `to_base_variable`/`to_index`/`level_names`/`name` return-type annotations
    and the `self.dims`→`self._dims` rename (`dims` is a property returning
    `_dims`; identical value) — no behavioral change.
  - `NoReturn`/`Hashable` typing imports — annotations only.
  The single behaviorally-observable fix exercised by the F2P test is
  `IndexVariable.to_index_variable` returning a copy instead of `self`.

## G-CONF fuzz seed
Pinned seed: **6938** (see conformance_check.py).
