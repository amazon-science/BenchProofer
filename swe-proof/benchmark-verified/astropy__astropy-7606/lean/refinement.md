# refinement.md — astropy__astropy-7606

Operation-by-operation correspondence between `implementation_unrecognizedUnitEq`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`UnrecognizedUnit.__eq__`). Tags: **R** type refinement, **A-consumed** proof uses
an axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

Post-patch Python (`astropy/units/core.py:1710-1718`):

```python
def __eq__(self, other):
    try:
        other = Unit(other, parse_strict='silent')
    except (ValueError, UnitsError, TypeError):
        return NotImplemented
    return isinstance(other, type(self)) and self.name == other.name
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match po with` (case split on the interpretation outcome) | `try: other = Unit(other, parse_strict='silent') except (...)` — the call's success/failure dichotomy | R |
| 2 | `| .raised => return .ok .notApplicable` | `except (ValueError, UnitsError, TypeError): return NotImplemented` | R |
| 3 | `| .parsed isUnrecognized otherName => return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)` | `return isinstance(other, type(self)) and self.name == other.name` | R |

Notes:

- **Every step is R — no A, no I-needing-deep-model.** The behaviour the patch
  changes (an uninterpretable operand → `NotImplemented` sentinel instead of an
  escaping exception) is modeled DEEPLY/structurally over `ParseOutcome`
  (op 2: `.raised ↦ .notApplicable`); SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed decision. The `axioms` region is empty; **G-AX skips**.
- The R tag carries the *unchanged-callee observation* refinement: the result of
  `Unit(other, parse_strict='silent')` (the unchanged `_UnitMetaClass` factory) is
  the field `po : ParseOutcome` rather than re-derived. `.raised` ↔ the factory
  raising; `.parsed isUnrecognized otherName` ↔ the factory returning a unit with
  `isinstance(result, UnrecognizedUnit) = isUnrecognized` and `result.name =
  otherName`. This callee is orthogonal to the handler fix and unchanged by the
  patch; **G-CONF drives the REAL factory**, so the observation is validated
  against reality there.
- Op 3 also folds the sub-edit `isinstance(other, UnrecognizedUnit)` →
  `isinstance(other, type(self))` into the boolean field `isUnrecognized`. For an
  `UnrecognizedUnit` `self`, `type(self)` IS `UnrecognizedUnit`, so the two spell
  the same predicate; the field name reflects the post-patch, identity-on-this-class
  reading.
- No output component is left free: `result` is fully pinned to `eqResult selfName
  po`, including the not-applicable sentinel on `.raised` (directive 5 frame).
- **The fix itself** is op 2 (and the surrounding `match`): introducing the handler
  branch that returns the sentinel. The pre-patch impl (`Solution_prepatch.lean`)
  drops it — `.raised => return .error .parseError` — mirroring the pre-patch body
  letting the exception escape (`other = Unit(other, parse_strict='silent')` with no
  `try`). That escaping error violates the spec on `.raised` inputs (the spec
  demands `.ok .notApplicable`), so its `correct_*` is unprovable → G-DIFF.
- **G-CONF** mechanically refutes the R legs (no A legs): it computes `po` by
  calling the REAL `Unit(other, parse_strict='silent')` factory in-container over
  fuzzed operands, then diffs the impl's shadow against the post-patch
  `UnrecognizedUnit.__eq__` semantics (the three-valued return).

## The companion edit (NOT modeled)

`patch.diff` also changes `UnitBase.__eq__` (line 728) `return False` →
`return NotImplemented` in its `except (ValueError, UnitsError, TypeError)` branch.
This is behaviour-PRESERVING for every test in FAIL_TO_PASS / PASS_TO_PASS:
`u.m == None` is `False` both pre-patch (direct `return False`) and post-patch
(`NotImplemented` → reflected `None.__eq__` → identity → `False`); likewise
`u.m != u.s` etc. are unchanged. It is therefore not independently observable by
the harness and is shipped verbatim (gold) without a separate triple or a separate
`Solution_prepatch_*` variant. The only behaviour the F2P test `test_unknown_unit3`
newly exercises is `UnrecognizedUnit.__eq__` (`unit == "FOO"`, `unit != u.m`,
`unit != None`, `unit not in (None, u.m)`), which is the modeled function.
