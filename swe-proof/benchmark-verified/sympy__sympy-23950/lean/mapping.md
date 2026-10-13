# mapping.md — sympy__sympy-23950

## Instance
- repo: sympy/sympy
- base_commit: 88664e6e0b781d0a8b5347896af74b555e92891e
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, one site)
`Contains(x, s)` is a boolean-valued object asserting membership of an element
`x` in a set `s`. Its constructor stores the two operands as `self.args`:
`self.args[0]` is the element, `self.args[1]` is the set.

```python
class Contains(BooleanFunction):          # sympy/sets/contains.py:8
    def as_set(self):                     # sympy/sets/contains.py:47
        raise NotImplementedError()       # PRE-PATCH (no result produced)
        # return self.args[1]             # POST-PATCH (gold): yield the set operand
```

The method `as_set` converts the object to the set it represents. Pre-patch it
produced no value at all (it raised), so callers that need a set (e.g. anything
calling `.as_relational(...)` on the result) failed. The gold patch makes it
return the stored set operand `self.args[1]` — the second constructor argument.

The observable the F2P test (`test_as_set`) pins:

```python
assert Contains(x, FiniteSet(y)).as_set() == FiniteSet(y)
assert Contains(x, S.Integers).as_set() == S.Integers
assert Contains(x, S.Reals).as_set()    == S.Reals
```

In every case `as_set()` returns exactly the set operand the object was built
with — the identity of `self.args[1]`.

## Modeled function — `Contains.as_set`
| field | value |
|---|---|
| file @ base_commit | `sympy/sets/contains.py` |
| function | `Contains.as_set` (def at line 47; the patched line is its body, line 48) |
| role | sole modeled function; the patched `return` is the whole fix |

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
A `Contains` object is modeled by the Lean structure `MembershipAssertion E S`,
carrying its two constructor operands and nothing else (only the touched data):

| Lean | Python | note |
|---|---|---|
| `MembershipAssertion.element : E` | `self.args[0]` | the element operand |
| `MembershipAssertion.setArg : S` | `self.args[1]` | the set operand |
| `implementation_asSet c : Option S` | `Contains(x, s).as_set()` | the produced value |
| `some v` | a returned set value `v` | the method returns a set |
| `none` | the method raises `NotImplementedError` (produces no value) | per §2 exception → `Option` |

`E` and `S` are abstract carrier types: the fix is purely structural (it returns
a stored operand verbatim), so no operation on the contents of either type is
performed and no concrete modeling of set/element internals is required. The
bijection on the result is exact: the real method returns the very Python object
`self.args[1]` (object identity), mirrored by `implementation_asSet` returning
`some c.setArg`.

## Callee provenance / flag deps
- `self.args[1]` is a plain attribute read of the object's own stored operand —
  not a separately-defined callee the patch changes, and not a function call. It
  is modeled directly as the `setArg` field read (an **I**/**R** op). No
  `opaque`/`axiom` callee contract is needed anywhere in the bundle.
- No flag dependency.

## G-CONF fuzz seed
Pinned seed: **23950** (used in `conformance_check.py`).
