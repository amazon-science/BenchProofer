# refinement.md — django__django-15277

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `configureValidators` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — none here),
or **I** (identical concrete op). EVERY step is R, A, or I; there are no kind-3
(inexpressible-changed-op) steps.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The validator-assembly site — `CharField.__init__` (`fields/__init__.py:1010-1013`)

Gold hunk:
```
-        self.validators.append(validators.MaxLengthValidator(self.max_length))
+        if self.max_length is not None:
+            self.validators.append(validators.MaxLengthValidator(self.max_length))
```

| # | Solution.lean impl op (`configureValidators`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `priorValidators : List Validator` | the field's validators list before the changed line: `Field.validators` = `[*default_validators, *self._validators]`, and `CharField.default_validators == []`, so the `validators=` kwarg (`self._validators`) | R | list ↔ `List`; each prior validator ↔ an opaque `existing` tag (mapping.md §2). G-CONF abstracts each to `('E',)`. |
| A2 | param `lengthBound : Option Int` | `self.max_length` (`int` or `None`) | R | `None ↔ none`, `int n ↔ some n` (mapping.md §2). |
| A3 | `if lengthBound.isSome then … else …` | `if self.max_length is not None:` | I | `Option.isSome` ↔ Python `is not None`; the guard is the single behavior the change introduces. Both branches concrete. |
| A4 | then-branch: `priorValidators ++ [Validator.lengthBound lengthBound]` | `self.validators.append(validators.MaxLengthValidator(self.max_length))` | R + I | single-element `append` ↔ `++ [·]` (I, list op); the appended `MaxLengthValidator(self.max_length)` ↔ `Validator.lengthBound lengthBound` (R: opaque length-bound check carrying the same bound, mapping.md §2). |
| A5 | else-branch: `priorValidators` (unchanged) | the `if` is false ⇒ no append; validators list left as-is | I | when no bound is configured the result is the prior list verbatim — the post-patch behavior the F2P test relies on. |

Discriminating content of the change — when `max_length is None`, the
length-bound check is NOT appended — lives in the else-branch (A5) and is pinned
by the postcondition `lengthBound = none → out = priorValidators`. The pre-patch
appended unconditionally; `Solution_prepatch.lean` reproduces that
(`priorValidators ++ [Validator.lengthBound lengthBound]` with no guard) and
**fails** exactly that clause (G-DIFF), since for `lengthBound = none` it yields
`priorValidators ++ [Validator.lengthBound none] ≠ priorValidators`.

## B. No second change site

The gold patch is a single hunk. The two F2P tests both observe this one change:

- `test_output_field_does_not_create_broken_validators`: `Value('test')`
  resolves to a `CharField()` with `max_length=None`; post-patch its
  `validators` list carries no length-bound check, so `field.clean(value, …)`
  (which runs the validators) no longer raises `TypeError: '>' not supported
  between instances of 'int' and 'NoneType'` from a `MaxLengthValidator(None)`.
  This is exactly the else-branch (A5).
- `test_raise_empty_expressionlist`: an unrelated assertion in the same test
  class that was newly added in the test_patch alongside the regression test;
  it passes pre- and post-patch independent of this change (it exercises
  `ExpressionList()` raising `ValueError`). It imposes no additional behavior on
  the modeled function; the only behavior the *fix* changes is the
  `CharField`-validators guard (A3–A5). No separate prepatch is needed for it
  (G-DIFF requires one failing prepatch per independently-*fixed* behavior; this
  test is not fixed by the patch, it is collaterally bundled in the test_patch).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — guarding the
length-bound append on `max_length is not None` — is modeled **directly** as the
`if lengthBound.isSome` guard (A3) over a concrete `List` append (A4). Nothing is
hidden behind an axiom: there are no consumed axioms and no deep-model references
in this bundle (the `MaxLengthValidator` constructor and the prior validators are
opaque carriers the spec never reasons into).

## D. verify(Solution) ⇒ resolved

`configureValidators` verifies only if (A5) with no bound the result is the prior
list verbatim AND (A4) with a bound `b` the result is the prior list plus exactly
one length-bound check carrying `b`. By R (`max_length ↔ Option Int`, validators
list ↔ `List`, single `append` ↔ `++ [·]`, `MaxLengthValidator(b)` ↔
`Validator.lengthBound (some b)`) the verified routine equals the patched
`CharField.__init__`'s validator assembly on every input; by G-CONF the R/I
transliteration agrees with `patch.diff`'s `CharField.validators` on ≥10⁵ inputs
(both branches, prior-validator lists). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms to trust (G-AX skip).
