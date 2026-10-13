# mapping.md — astropy__astropy-7606

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3cedd79e6c121910220f8e6df77c54a0b344ea94`, states the type
abstraction, and gives the provenance of the (abstracted) callees.

Repo file under change: `astropy/units/core.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `eq_unparsed_name(parse_succeeds, parsed_same_kind, names_equal)` | `UnrecognizedUnit.__eq__(self, other)` — `astropy/units/core.py:1712` (body 1713-1714) | the modeled changed function (equality of an unparsed-name unit) — the F2P-discriminating site |
| `eq_unit(is_same, parse_succeeds, parsed_is_unit, convertible, effectively_unity)` | `UnitBase.__eq__(self, other)` — `astropy/units/core.py:724` (body 725-741) | the modeled changed function (general unit equality) — the second patched hunk |
| `parse_succeeds` (param) | observable of `Unit(other, parse_strict='silent')` — factory `_UnitMetaClass.__call__`, `astropy/units/core.py:1744` | TRUE iff the silent unit-coercion returns normally; FALSE iff it raises (the partial-coercion predicate the try/except reads) |
| `parsed_same_kind` (param) | `isinstance(other, type(self))` — `core.py:1714` (post-patch) | observable: the coerced operand is a unit of the same (unparsed-name) kind as `self` |
| `names_equal` (param) | `self.name == other.name` — `core.py:1714` | observable: the coerced same-kind unit carries the same name |
| `is_same` (param) | `self is other` — `core.py:725` | observable short-circuit identity |
| `parsed_is_unit` (param) | `isinstance(other, UnitBase)` — `core.py:735` | observable: the coerced operand is a genuine `UnitBase` |
| `convertible` (param) | `self._to(other)` does not raise `UnitsError` — `core.py:738-741`, `_to` at `core.py:904` | observable: dimensional convertibility |
| `effectively_unity` (param) | `is_effectively_unity(self._to(other))` — `core.py:739`, `is_effectively_unity` from `astropy/units/utils.py` | observable: the conversion factor is unity (the two are the same unit) |
| `RES_FALSE / RES_TRUE / RES_NOTIMPL` | the three values a rich `__eq__` may return: `False` / `True` / `NotImplemented` | three-valued comparison outcome (mapping.md §2) |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view):
`UnrecognizedUnit.__eq__` called `Unit(other, parse_strict='silent')` with NO
`try`/`except` (`core.py:1713`), so a non-coercible operand (e.g. `None`, which
hits `raise TypeError("None is not a valid Unit")` at `core.py:1822`) propagated
a `TypeError`; and `UnitBase.__eq__` returned plain `False` (`core.py:731`) on
the coercion-failure path instead of `NotImplemented`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the operand `other` (an arbitrary Python object — `None`, a `str`, a `UnitBase`, a number, …) | the boolean observables the comparison reads off it (`parse_succeeds`, `parsed_same_kind`, `names_equal`, `parsed_is_unit`, `convertible`, `effectively_unity`, `is_same`) | `other` is never inspected beyond these predicates; the comparison's outcome is a function of exactly them, so abstracting `other` to its observed predicates is lossless for the modeled behaviour |
| `self` (the calling unit) | the predicate values that depend on it (`names_equal`, `is_same`, `parsed_same_kind`, `convertible`, `effectively_unity`) are computed against `self`; `self` is read-only and never mutated | the modeled behaviour reads `self.name` / `self is other` / `self._to(...)`; these are folded into the input predicates. `self` is not mutated by `__eq__`. |
| the dunder return — `True` / `False` / `NotImplemented` | integer tag `RES_TRUE=1` / `RES_FALSE=0` / `RES_NOTIMPL=2` | a faithful 1:1 tag of the three possible rich-comparison results. `NotImplemented` is modelled as its OWN tag (not collapsed to a bool) because the behaviour pinned is precisely "produce the defer/not-applicable sentinel, not a definite decision and not a failure". axiom_check.py observes the RAW dunder return so the sentinel is visible. |
| `Unit(...)` raising on a non-coercible operand | `parse_succeeds == False` | the partial-coercion failure is modelled as a boolean predicate (`parse_succeeds`), not as a Nagini `Exsures`: the changed behaviour is the CONTROL-FLOW response to that failure (defer vs. raise/wrong-decision), which the model captures by the `not parse_succeeds -> RES_NOTIMPL` postcondition. No builtin-exception `Exsures` (it crashes the translator). |

`self` and `other` carry no Nagini heap permission in the model because they are
abstracted to plain boolean observables (directive 5 is satisfied vacuously:
there is no mutable list/dict/object input to over-permit; the read-only operands
are modelled by value-typed booleans).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

This bundle consumes **NO `@ContractOnly` axiom** (the `axioms` region is empty),
exactly as in the django-14017 boolean-predicate-abstraction exemplar. The
changed functions read only the observable predicates of their unchanged
callees:

- `Unit(other, parse_strict='silent')` — the unit factory
  (`_UnitMetaClass.__call__`, `core.py:1744`). UNCHANGED by the patch. Its only
  observable the comparison depends on is *whether it returns normally* (vs.
  raises `ValueError`/`UnitsError`/`TypeError`) and *what kind of unit it
  yields*. Both are folded into the input predicates `parse_succeeds`,
  `parsed_same_kind`, `parsed_is_unit`. The factory raises `TypeError("None is
  not a valid Unit")` for `None` (`core.py:1821-1822`) and `TypeError` for any
  other non-coercible object (`core.py:1824-1825`); a recognised string parses
  to a recognised unit; an unrecognised string under `parse_strict='silent'`
  yields an `UnrecognizedUnit` (`core.py:1816`). This is exactly the
  `parse_succeeds` / kind predicates the model uses.
- `UnitBase._to(other)` (`core.py:904`) and `is_effectively_unity`
  (`astropy/units/utils.py`) — UNCHANGED. Their observables (`convertible`,
  `effectively_unity`) are likewise folded into the input predicates of
  `eq_unit`.

There is therefore no library axiom to over-approximate. The single soundness
obligation is the **refinement fidelity of the boolean-predicate abstraction**:
that the model's three-valued outcome equals the REAL post-patch dunders for
every combination of the abstracted observables.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL post-patch
`UnrecognizedUnit.__eq__` and `UnitBase.__eq__` with concrete operands spanning
the full observable space — including the discriminating non-coercible operands
(`None`, a plain `object`, a `list`) that must DEFER via `NotImplemented` and
must NOT raise — and asserts the raw dunder return (mapped to the three-valued
tag) equals the model's pinned outcome, plus that the user-facing `==`/`!=`/`in`
behaviour the F2P/P2P tests demand holds. It applies the bundle `patch.diff` to
the in-container `/testbed` checkout first (the eval image ships `base_commit`,
pre-patch), idempotently. Imports only `astropy` + stdlib. Exit 0 iff sound.
