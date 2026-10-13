# refinement.md — astropy__astropy-7606

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `compareName` `do` block and the deep `compareSpec` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs + this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The comparison site — `UnrecognizedUnit.__eq__` (`astropy/units/core.py:1710`)

Gold hunk:
```
-        other = Unit(other, parse_strict='silent')
-        return isinstance(other, UnrecognizedUnit) and self.name == other.name
+        try:
+            other = Unit(other, parse_strict='silent')
+        except (ValueError, UnitsError, TypeError):
+            return NotImplemented
+
+        return isinstance(other, type(self)) and self.name == other.name
```

| # | Solution.lean impl op (`compareName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `selfName : List Char` | `self.name` (a `str`) | R | `str` ↔ `List Char`; code-point string equality ↔ `decide (selfName = name)` (mapping.md §2). |
| A2 | parameter `outcome : InterpretOutcome` | `other = Unit(other, parse_strict='silent')` | R | the UNCHANGED interpreter, abstracted to its three observable outcomes (success-same-kind / success-other-kind / raises). Owed no contract — free input (mapping.md §3). G-CONF runs the REAL `Unit(...)` to classify it. |
| A3 | `.uninterpretable ⇒ Except.ok .deferred` | the new `except (ValueError, UnitsError, TypeError): return NotImplemented` | I | the whole content of the fix: a failed interpretation is caught and turned into a graceful decline (`NotImplemented ↔ deferred`, mapping.md §2) instead of escaping. Concrete, transliterated by G-CONF. |
| A4 | `.sameKind name ⇒ Except.ok (.decided (decide (selfName = name)))` | `isinstance(other, type(self)) and self.name == other.name` (true branch) | I | an interpreted value of this same kind compares equal iff the names coincide. `type(self) = UnrecognizedUnit` for every tested receiver (mapping.md §2). |
| A5 | `.otherKind ⇒ Except.ok (.decided false)` | `isinstance(other, type(self)) and …` (the `isinstance` is false) | I | an interpreted value of a different kind is unequal — the `and` short-circuits to `False`. |
| A6 | result is always `Except.ok _` (`ensures ∃ v, out = Except.ok v`) | the method always `return`s a value (`NotImplemented` or a `bool`); never raises | I | the post-patch `__eq__` never lets an exception escape — the property the F2P test (`x == None`) demands. |

Discriminating content of the change — the previously-uncaught interpretation
failure (e.g. `Unit(None, parse_strict='silent')` raising `TypeError`) is now
absorbed into a verdict — lives in A3/A6: `compareSpec selfName .uninterpretable
= Except.ok .deferred` (model) ⇔ the new `try/except … return NotImplemented`
(real). `Solution_prepatch.lean` reproduces the pre-patch escape
(`.uninterpretable ⇒ Except.error .interpretationEscaped`) and **fails** the
`uninterpretable → deferred` and `∃ v, ok v` clauses (G-DIFF).

## B. The sibling change site — `UnitBase.__eq__` (`astropy/units/core.py:728`)

Gold hunk (same file, the base class):
```
         try:
             other = Unit(other, parse_strict='silent')
         except (ValueError, UnitsError, TypeError):
-            return False
+            return NotImplemented
```

A pure **return-value substitution** on the already-guarded except branch:
`False → NotImplemented`. No separate failing prepatch — and no modeled op —
because the change is **behaviourally inert for the official harness**:

- Python evaluates `a == b` as `a.__eq__(b)`, and if that yields
  `NotImplemented`, falls back to `b.__eq__(a)`, then to identity (`a is b`).
  For every operand the test suite passes to a `UnitBase.__eq__` whose
  interpretation *fails* (the only branch this hunk touches), both the old
  `False` and the new `NotImplemented` resolve to the same final `False`
  (the reflected/identity fallbacks also decline), and `!=` to the same `True`.
- No FAIL_TO_PASS or PASS_TO_PASS test observes a difference: the F2P test
  `test_unknown_unit3` exercises only `UnrecognizedUnit.__eq__` (site A);
  `test_compare_with_none` / `test_invalid_compare` assert `not (u.m == None)` /
  `not (u.m == u.s)`, both still `False` under either return value.

It is therefore recorded (mapping.md §1.1) and covered by G-CONF through the
shared `deferred ↔ NotImplemented` abstraction, but carries no
separately-observable behaviour and no kind-3 op.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I (no axioms at all). The operation that genuinely *changed* —
catching the interpreter's failure and declining instead of escaping — is modeled
**deeply** as the `.uninterpretable ⇒ Except.ok .deferred` branch of
`compareSpec` (step A3), a concrete I op transliterated by G-CONF, not hidden
behind an axiom about the function under change. The unchanged interpreter
`Unit(...)` is a **free input** (an R refinement, owed no contract — directive
7), not a consumed axiom; there is no `axiom` and no `axiom_check.py`.

## D. verify(Solution) ⇒ resolved

`compareName` verifies only if (A3) a failed interpretation yields
`Except.ok .deferred` (never an escape), (A4/A5) a same-kind operand compares by
name equality and an other-kind operand is unequal, and (A6) the result is
always a verdict. By R (`str ↔ List Char`, `NotImplemented ↔ deferred`,
`bool ↔ decided`, mapping.md §2) the verified comparison equals the gold-patched
`UnrecognizedUnit.__eq__` on the tested operands; by G-CONF the R/I
transliteration — classifying `outcome` through the REAL `Unit(...)` interpreter
— agrees with `patch.diff`'s behaviour on ≥10⁵ operands (including the
`None` operand the bug crashed on). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
doc + G-CONF); there are no axioms to trust (G-AX = skip).
