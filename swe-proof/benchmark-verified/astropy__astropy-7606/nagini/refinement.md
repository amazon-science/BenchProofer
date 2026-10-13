# refinement.md — astropy__astropy-7606

The operation-by-operation correspondence between `model.py`'s implementation
(the `eq_unparsed_name` and `eq_unit` impl regions) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses the axiom's
`Ensures`, and **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **NO axioms** in this bundle:
every step below is R or I (mapping.md §3). The two unchanged callees
(`Unit(...)` factory, `_to`/`is_effectively_unity`) appear only as the operand
observables, not as consumed axioms.

## A. The unparsed-name equality site — `UnrecognizedUnit.__eq__` (`astropy/units/core.py:1712`) — the F2P-discriminating hunk

Gold hunk:
```
     def __eq__(self, other):
-        other = Unit(other, parse_strict='silent')
-        return isinstance(other, UnrecognizedUnit) and self.name == other.name
+        try:
+            other = Unit(other, parse_strict='silent')
+        except (ValueError, UnitsError, TypeError):
+            return NotImplemented
+
+        return isinstance(other, type(self)) and self.name == other.name
```

| # | model.py impl op (`eq_unparsed_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `parse_succeeds`, `parsed_same_kind`, `names_equal` | the operand `other` (arbitrary object) | R | the only observables `__eq__` reads off `other` are: whether `Unit(other, parse_strict='silent')` returns normally ↔ `parse_succeeds`; `isinstance(other, type(self))` ↔ `parsed_same_kind`; `self.name == other.name` ↔ `names_equal` (mapping.md §2). The outcome is a function of exactly these. |
| A2 | `if not parse_succeeds: return RES_NOTIMPL` | `try: other = Unit(...) except (ValueError, UnitsError, TypeError): return NotImplemented` | R + I | **the changed control flow.** The `try`/`except` around the unchanged `Unit(...)` coercion, returning the not-applicable sentinel on failure, is modelled by the guard on the failure-observable `parse_succeeds`: a non-coercible operand ↔ the coercion raising one of `(ValueError, UnitsError, TypeError)` ↔ `not parse_succeeds`, and `return NotImplemented` ↔ `return RES_NOTIMPL` (R: the `NotImplemented` sentinel ↔ the `RES_NOTIMPL` tag, mapping.md §2). The factory's raise-on-`None` (`core.py:1822`) is the canonical `not parse_succeeds` case. |
| A3 | `if parsed_same_kind and names_equal: return RES_TRUE` / `return RES_FALSE` | `return isinstance(other, type(self)) and self.name == other.name` | R + I | the definite-decision branch, reached only when the coercion succeeded. `and` and the boolean structure are identical (I); the two conjuncts are the R-refined predicates `parsed_same_kind` (`isinstance(other, type(self))`) and `names_equal` (`self.name == other.name`). The Python `and`-of-bools result ↔ `RES_TRUE`/`RES_FALSE` tag. |

The discriminating content of the change — comparison against a NON-COERCIBLE
operand (e.g. `None`) must yield the not-applicable sentinel rather than failing
— lives in step A2: `not parse_succeeds -> RES_NOTIMPL` (model) ⇔ the
`try/except ... return NotImplemented` (real). The pre-patch had no `try/except`
(it consumed `Unit(...)` unconditionally and the non-coercible operand raised);
`model_prepatch.py` reproduces the absence of that branch (no
`not parse_succeeds` guard) and **fails** the postcondition
`Implies(not parse_succeeds, Result() == RES_NOTIMPL)`
(model_prepatch.py:89) — exactly the spec sensing the change (G-DIFF). This is
the F2P observation `test_unknown_unit3`: `unit != None` and
`unit not in (None, u.m)` must not raise.

(The `isinstance(other, UnrecognizedUnit)` → `isinstance(other, type(self))`
sub-change is a same-kind generalisation that is behaviourally identical for the
tested `UnrecognizedUnit` self — `type(self) is UnrecognizedUnit` — so it maps
to the same `parsed_same_kind` observable; G-AX validates the equivalence on the
concrete `UnrecognizedUnit` operands.)

## B. The general unit equality site — `UnitBase.__eq__` (`astropy/units/core.py:724`) — the second hunk

Gold hunk:
```
         try:
             other = Unit(other, parse_strict='silent')
         except (ValueError, UnitsError, TypeError):
-            return False
+            return NotImplemented
```

| # | model.py impl op (`eq_unit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if is_same: return RES_TRUE` | `if self is other: return True` (`core.py:725-726`) | R + I | the identity short-circuit, unchanged; `self is other` ↔ `is_same` (I on the boolean), `True` ↔ `RES_TRUE`. |
| B2 | `if not parse_succeeds: return RES_NOTIMPL` | `try: other = Unit(...) except (...): return NotImplemented` (`core.py:728-731` post-patch) | R + I | **the changed line.** The non-coercible-operand path now returns the not-applicable sentinel instead of `False`; `not parse_succeeds` ↔ the coercion raising, `RES_NOTIMPL` ↔ `NotImplemented` (R). This is the single edited token `False` → `NotImplemented`. |
| B3 | `if not parsed_is_unit: return RES_NOTIMPL` | `if not isinstance(other, UnitBase): return NotImplemented` (`core.py:735-736`) | R + I | unchanged "give up so other can try" branch; `isinstance(other, UnitBase)` ↔ `parsed_is_unit`. |
| B4 | `if convertible and effectively_unity: return RES_TRUE` / `return RES_FALSE` | `try: return is_effectively_unity(self._to(other)) except UnitsError: return False` (`core.py:738-741`) | R + I | unchanged definite-decision branch; `self._to(other)` not raising `UnitsError` ↔ `convertible`, `is_effectively_unity(...)` ↔ `effectively_unity`; a `UnitsError` (`not convertible`) ↔ `return False` ↔ `RES_FALSE`. The `Requires(Implies(effectively_unity, convertible))` records that the unity factor is only observed when conversion succeeded. |

The discriminating content of this hunk — `False` → `NotImplemented` on the
coercion-failure path — lives in step B2; `model_prepatch_2.py` reverts it to
`return RES_FALSE` and **fails** the postcondition
`Implies(not is_same and not parse_succeeds, Result() == RES_NOTIMPL)`
(model_prepatch_2.py:139). This hunk is NOT independently observed by an F2P/P2P
test (`u.m == None` yields `False` both pre- and post-patch because Python
collapses both `False` and the resolved-`NotImplemented` identity fallback to
`False` for `==`; `test_compare_with_none` passes either way) — it is a
robustness fix that lets `other.__eq__` be tried. It is modelled and a failing
prepatch is shipped for completeness and faithful skeleton coverage, per the
multi-site rule (SPEC_GUIDE §3); the F2P-load-bearing prepatch is `model_prepatch.py`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the
control-flow response to a failed operand coercion (defer via `NotImplemented`
instead of raising / returning a definite wrong `False`) — is modelled
**directly** by the `not parse_succeeds -> RES_NOTIMPL` guard over the boolean
failure-observable (steps A2, B2). There is no axiomatized callee: the unchanged
`Unit(...)` factory, `_to`, and `is_effectively_unity` are read only via their
observable predicates (folded into the input booleans), and the three-valued
result is modelled directly as the integer tag. There is therefore no A-consumed
axiom and no A-reference deep model; mapping.md §3 records the empty axiom
inventory. The refinement is the boolean-predicate + three-valued-tag type
abstraction (R) over an otherwise identical control flow (I), whose fidelity to
the real `UnrecognizedUnit.__eq__` / `UnitBase.__eq__` G-AX validates over the
full observable space (incl. the discriminating non-coercible operands).

## D. verify(model) ⇒ resolved

`eq_unparsed_name` verifies only if a non-coercible operand yields the
not-applicable sentinel (`not parse_succeeds -> RES_NOTIMPL`, step A2) and a
coercible operand yields the definite same-kind-and-name decision (step A3);
`eq_unit` likewise (steps B1-B4). By R (`other` ↔ its boolean observables;
`self` read-only; `NotImplemented` ↔ `RES_NOTIMPL`; `True`/`False` ↔
`RES_TRUE`/`RES_FALSE`) the verified functions equal the post-patch
`UnrecognizedUnit.__eq__` / `UnitBase.__eq__` on the tested operands; by G-AX
the real post-patch dunders match the model's three-valued outcome over the full
observable space, decisively that the non-coercible `None`/object operands DEFER
via `NotImplemented` and never raise. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
abstraction soundness (G-AX, here the boolean-predicate + three-valued-tag
refinement rather than a library axiom) and refinement fidelity (this document,
G-EQ).
