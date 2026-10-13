# refinement.md — django__django-13794

One changed behavior (the proxy gains binary concatenation), one Lean triple.
Tags: **R** type-refinement, **A-consumed** proof uses axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

## Site — `implementation_lazyConcat` ↔ the proxy's binary concatenation operators

patch.diff hunk (added inside the `lazy()` `__proxy__` class, after `__mod__`):
```python
def __add__(self, other):
    return self.__cast() + other
def __radd__(self, other):
    return other + self.__cast()
```

The user-observable operation is the binary concatenation `a + b` where each of
`a`, `b` is either an ordinary concrete value or an on-demand (deferred) value.
Python dispatch picks exactly one of the two new methods (or the pre-existing
all-concrete path):

- `a` deferred → `a.__add__(b)` runs `self.__cast() + other`.
- `a` concrete, `b` deferred → `a.__add__(b)` returns `NotImplemented` (a plain
  `str`/`int` cannot concatenate the proxy), Python falls back to
  `b.__radd__(a)` running `other + self.__cast()`.
- both concrete → ordinary pre-existing concatenation.

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `match a with \| .deferred s => return s ++ force b` | `__add__`: `self.__cast() + other` (deferred left operand forced, then concatenated) | R (`Operand` ↔ value-or-proxy; `force`/`s` ↔ `self.__cast()`; `++` ↔ `+`) |
| `\| .concrete s => match b with \| .deferred t => return s ++ t` | `__radd__`: `other + self.__cast()` (left concrete, right forced) | R (`force b`/`t` ↔ `self.__cast()` of the right operand; `++` ↔ `+`) |
| `\| .concrete t => return s ++ t` | pre-existing all-concrete `str + str` | I (ordinary concatenation) |

`self.__cast()` forces a deferred value to its underlying concrete value. It is
modeled DIRECTLY by `force`, which projects the carried underlying text from the
`Operand` — its only input is the function's own argument (directive 8), so it is
a deep model of the forcing operation, NOT an axiomatized oracle and NOT an
A-reference callee. Concatenation is Python `+` over the underlying values
modeled as Lean `String` `++` (an I op).

## Result-type generality

The gold operators are type-generic (`self.__cast() + other` for any underlying
type). The problem statement is explicitly about the string result class
("concatenate strings with lazy string"), which the template-filter F2P tests
(`test_add08`, `test_add09`) exercise; I model that representative case with
`String` `++`. The `test_lazy_add` F2P uses the same operators at the `int`
result class (`force a + force b` with integer `+`); it is the identical operator
over a different underlying `+`, and `patch.diff` (gold verbatim) fixes the
generic operators so the harness resolves all three F2P tests.

## Axioms

None. The forcing of a deferred operand is modeled deeply by `force`, so there is
no consumed axiom and no A-reference callee. `axiom_check.py` is a skip stub;
`conformance_check.py` differential-tests the R/I legs (no A legs), so
`conf_skip = false`.

## How the spec sees the bug (G-DIFF)

The discriminator is "at least one operand is deferred". The spec pins the result
to `force a ++ force b` in EVERY case.

- `Solution_prepatch.lean` models the pre-change behavior: with no concatenation
  operator on the proxy, an on-demand operand makes `a + b` raise, the
  value-combining filter catches it and yields the empty string; only the
  all-concrete case concatenates. Its impl returns `""` whenever an operand is
  deferred. For e.g. `a = deferred "string"`, `b = deferred "lazy"` the spec
  requires `"stringlazy"` but the prepatch impl yields `""`, so the carried gold
  proof cannot close — exactly the `add08`/`add09`/`test_lazy_add` F2P failures.
- The all-concrete case (`PASS_TO_PASS` `test_add01..07`, `FunctionTests`) is
  preserved: both impls return `force a ++ force b` there.
