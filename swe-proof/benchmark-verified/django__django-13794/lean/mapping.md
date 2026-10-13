# mapping.md — django__django-13794

## Instance
- repo: django/django
- base_commit: fe886eee36be8022f34cfe59aa61ff1c21fe01d9
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
A value produced on demand (a deferred / "lazy" value, created by
`django.utils.functional.lazy`) acts as a proxy for the result of forcing it. At
`base_commit` the proxy class supports many delegated operations but has **no**
binary-concatenation operators, so concatenating a deferred value with another
value (e.g. via the `add` template filter, `value + arg`) raises
`TypeError: can only concatenate str (not "__proxy__") to str`; the `add` filter
catches the exception and yields the empty string. The gold patch adds the two
binary-concatenation operators to the proxy (the forward operator for when the
deferred value is the left operand, and the reflected operator for when it is the
right operand). Each forces the deferred value to its underlying concrete value
and then performs the underlying type's concatenation.

```python
# django/utils/functional.py, inside the lazy() __proxy__ class (added by gold)
def __add__(self, other):
    return self.__cast() + other          # deferred value is the LEFT operand
def __radd__(self, other):
    return other + self.__cast()          # deferred value is the RIGHT operand
```

`self.__cast()` forces the deferred value, returning the concrete underlying
value (for the `str` result class, the underlying string).

## Symbol binding
| Lean symbol | Python source @ base_commit (post-patch site) |
|---|---|
| `implementation_lazyConcat` | the proxy's binary concatenation: `__proxy__.__add__` (deferred left operand) and `__proxy__.__radd__` (deferred right operand), `django/utils/functional.py` lines added at @ -176 (after `__mod__`) |
| `problem_spec_lazyConcat`   | the post-condition the two operators must jointly satisfy |
| `Operand` / `force`         | the operand carrier (concrete vs deferred) and the forcing of a deferred value, i.e. `self.__cast()` |

The single Lean function `lazyConcat (a b : Operand) → String` models the
user-observable binary concatenation `a + b` over operands each of which is
either a concrete string or a deferred (lazy) string. Its three branches are the
three concrete code paths Python takes:
- `a` deferred → `a.__add__(b)` runs: `__cast(a) + b` (the gold `__add__`).
- `a` concrete, `b` deferred → `a.__add__(b)` returns `NotImplemented` (a plain
  `str` cannot concatenate the proxy), so Python falls back to `b.__radd__(a)`:
  `a + __cast(b)` (the gold `__radd__`).
- `a`, `b` both concrete → ordinary `str + str` (pre-existing behavior).

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `Operand.concrete s` | a plain `str` value `s` | non-deferred operand |
| `Operand.lazy s` | a deferred value `lazy(lambda: s, str)()` whose `__cast()` yields `s` | the `__proxy__` instance for the `str` result class |
| `force : Operand → String` | `__cast()` on a deferred operand / identity on a concrete one | forces to the underlying `str` |
| `String` ++ | Python `str` `+` (concatenation) | byte-for-byte identity bijection |
| result `: String` | the `str` produced by `a + b` | |

`String` ↔ Python `str` is the identity bijection (byte-for-byte). Lean `++`
(`String` append) ↔ Python `str` `+`.

### Result-type generalization (test_lazy_add)
The gold operators are type-generic (`self.__cast() + other` for any underlying
type). One F2P test, `test_lazy_add`, exercises the same operators at the `int`
result class: `lazy(lambda: 4, int)() + lazy(lambda: 5, int)() == 9`, i.e.
`force(a) + force(b)` with integer `+` instead of string `++`. I model the
**string** result class — the case the problem statement is explicitly about
("concatenate strings with lazy string") and the case the template-filter F2P
tests (`test_add08`, `test_add09`) exercise — as the representative. The integer
case is the identical operator over a different underlying `+`; `patch.diff`
(gold verbatim) fixes the generic operators so the harness resolves all three
F2P tests.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. `self.__cast()` (the forcing
  of a deferred value) is modeled DIRECTLY by `force`, which projects the
  carried underlying string from the `Operand` — it is a deep model of the
  forcing operation, not an axiomatized oracle, and its only inputs are the
  function's own arguments (directive 8). The concatenation is Python `str + str`
  modeled as Lean `String` `++` (an I op). Hence the `axioms` region declares no
  `opaque`/`axiom` callee and `axiom_check.py` is a skip stub.
- No flag dependency: the operators apply unconditionally once present.

## G-CONF fuzz seed
- pinned seed: `13794`
- ≥10^5 fuzzed `(a, b)` operand pairs, each independently a concrete string or a
  deferred (lazy) string drawn from a mixed pool (empty, ASCII, unicode, random),
  covering all four concrete/deferred combinations so both the forward and
  reflected operators (and the plain `str + str` baseline) are exercised.
