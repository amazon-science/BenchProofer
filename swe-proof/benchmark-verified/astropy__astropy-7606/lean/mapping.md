# mapping.md — astropy__astropy-7606

## Symbol binding (file:line @ base_commit 3cedd79e6c121910220f8e6df77c54a0b344ea94)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_unrecognizedUnitEq` / `problem_spec_unrecognizedUnitEq` / `correct_unrecognizedUnitEq` | `UnrecognizedUnit.__eq__(self, other)` | `astropy/units/core.py:1710-1718` |
| `eqResult` (pure helper) | the body of `UnrecognizedUnit.__eq__` (post-patch) | `astropy/units/core.py:1710-1718` |
| `ParseOutcome` (pure helper) | the result of the unchanged callee `Unit(other, parse_strict='silent')` | `astropy/units/core.py` (`UnitBase.__eq__` calls the same factory at line 727; the `_UnitMetaClass.__call__` at ~1790) |
| `EqResult` (pure helper) | the value `__eq__` returns: `True` / `False` / `NotImplemented` | — |
| `UnitError` (pure helper) | the exception that a failed parse propagates when uncaught | `ValueError` / `UnitsError` / `TypeError` raised by the factory |

## What the function does (base_commit, the buggy pre-patch form)

```python
class UnrecognizedUnit(UnitBase):
    ...
    def __eq__(self, other):
        other = Unit(other, parse_strict='silent')
        return isinstance(other, UnrecognizedUnit) and self.name == other.name
```

`Unit(other, parse_strict='silent')` is a factory (`_UnitMetaClass.__call__`). For a
recognised string it returns a real unit; for an unparsable string it returns an
`UnrecognizedUnit` carrying that string as its `.name`; for an operand that cannot
be interpreted as a unit at all (e.g. `None`, or an arbitrary object) it RAISES one
of `(ValueError, UnitsError, TypeError)` — `Unit(None, ...)` raises
`TypeError("None is not a valid Unit")`. Because the pre-patch body calls the
factory unconditionally and outside any handler, that exception propagates out of
`__eq__`, so `unrecognized_unit == None` terminates with a `TypeError` instead of a
boolean. This is the reported defect.

## What the function does (post-patch, the desired form)

```python
    def __eq__(self, other):
        try:
            other = Unit(other, parse_strict='silent')
        except (ValueError, UnitsError, TypeError):
            return NotImplemented
        return isinstance(other, type(self)) and self.name == other.name
```

The factory call is wrapped in a handler: when the operand cannot be interpreted as
a unit, the method returns the `NotImplemented` sentinel (so Python defers to the
reflected comparison / identity, yielding `False` for `==` and `True` for `!=`),
rather than letting the exception escape. When the operand DOES parse, the result is
unchanged: `True` iff the parsed value is itself an unrecognised unit (`isinstance(
other, type(self))`) carrying the same name, else `False`.

`isinstance(other, type(self))` replaces the literal `isinstance(other,
UnrecognizedUnit)`. For an `UnrecognizedUnit` `self`, `type(self)` IS
`UnrecognizedUnit` (the class has no subclasses in astropy), so this sub-edit is
behaviour-preserving for the modeled/tested behaviour; it is folded into the
`isUnrecognized` observation below.

## The companion edit (UnitBase.__eq__, NOT separately modeled)

The gold patch also changes `UnitBase.__eq__` (line 728) `return False` →
`return NotImplemented` in its own `except (ValueError, UnitsError, TypeError)`
branch. This is behaviour-PRESERVING for every test in FAIL_TO_PASS / PASS_TO_PASS
(`u.m == None` returns `False` both before and after — pre-patch directly, post-patch
via `NotImplemented` → reflected → identity), so it is not independently observable
by the harness. It ships verbatim in `patch.diff` (gold) but is not modeled as a
separate triple: the only behaviour the F2P test `test_unknown_unit3` observes is
`UnrecognizedUnit.__eq__`.

## Lean modeling

The observable result of `UnrecognizedUnit.__eq__` is three-valued (`True` /
`False` / `NotImplemented`) plus the possibility of propagating an exception. The
modeled value is `Except UnitError EqResult`:

- `EqResult` = `isTrue | isFalse | notImplemented` — the value the method returns.
- `UnitError` = `parseError` — an exception escaping `__eq__`.
- The unchanged factory `Unit(other, parse_strict='silent')` is the unchanged callee;
  its result is carried as `ParseOutcome`:
  - `.raised` — the factory raised (operand not interpretable as a unit, e.g. `None`);
  - `.parsed isUnrecognized otherName` — the factory returned a unit; `isUnrecognized`
    = `isinstance(result, UnrecognizedUnit)`, `otherName` = `result.name`.

`selfName : String` = `self.name`.

Post-patch decision (`eqResult`):

```
match po with
| .raised                       => .ok .notImplemented
| .parsed isUnrecognized name   => .ok (if isUnrecognized && selfName == name
                                          then .isTrue else .isFalse)
```

The pre-patch impl drops the handler, so `.raised` propagates as `.error
.parseError` (the escaping `TypeError`), violating the spec on that input — exactly
the reported defect, and the discriminating clause for G-DIFF.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.name` (str) | `selfName : String` | identity |
| outcome of `Unit(other, parse_strict='silent')` | `ParseOutcome` | raise ↔ `.raised`; returns `u` ↔ `.parsed (isinstance(u, UnrecognizedUnit)) u.name` |
| `isinstance(other, type(self))` | `isUnrecognized : Bool` field of `.parsed` | identity (`type(self)` = `UnrecognizedUnit`) |
| `other.name` (str) | `otherName : String` field of `.parsed` | identity |
| return `True` | `EqResult.isTrue` | identity |
| return `False` | `EqResult.isFalse` | identity |
| return `NotImplemented` | `EqResult.notImplemented` | identity |
| escaping `(ValueError\|UnitsError\|TypeError)` | `Except.error UnitError.parseError` | identity |
| normal return `v` | `Except.ok v` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behaviour the patch changes —
  whether a non-interpretable operand yields the `NotImplemented` sentinel or lets
  the exception escape — is modeled DEEPLY/structurally over `ParseOutcome`
  (`.raised` ↦ `.notImplemented` vs propagation). SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision, so the `axioms` region is empty
  and **G-AX skips**.
- The unchanged callee `Unit(_, parse_strict='silent')` (the `_UnitMetaClass`
  factory) is not separately modeled; its full effect is carried as the grounded
  observation `po : ParseOutcome`. It is UNCHANGED by the patch and orthogonal to
  the handler fix. **G-CONF drives the REAL factory** (it computes `po` by actually
  calling `Unit(other, parse_strict='silent')` in-container), so this carried
  observation is validated against reality there. It constrains no output component
  the spec leaves free — `result` is fully pinned to `eqResult selfName po`.
- `parse_strict='silent'` is the fixed flag the factory is always called with
  (silent mode: unparsable strings become `UnrecognizedUnit` rather than raising;
  only genuinely non-unit operands raise). G-CONF fuzzes operands across both
  categories (`None`/ints → raise; strings/units → parse).

## G-CONF fuzz seed

Pinned LCG seed: **7606** (see `conformance_check.py` `SEED`). Corpus: a self
`UnrecognizedUnit` with a randomized name, compared against operands spanning every
`ParseOutcome` category — `None` and non-unit objects (→ `.raised`), the self name
string and other unparsable strings (→ `.parsed isUnrecognized=True`), recognised
unit strings and real `Unit` objects (→ `.parsed isUnrecognized=False`), and other
`UnrecognizedUnit` objects (→ `.parsed isUnrecognized=True`). Hand-picked edge cases
pin the discriminating clause and the F2P assertions: `unit == "FOO"` → `isTrue`,
`unit != u.m` (`== u.m` → `isFalse`), `unit == None` → `notImplemented`.
