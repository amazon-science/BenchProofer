# refinement.md — django__django-16801

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(`registerInitHandler` over `shouldRegister`, and `dimensionWrites` over
`dimUpdate`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here empty) A legs and this narrative are audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The registration site — `ImageField.contribute_to_class` (`files.py:438-445`)

Gold hunk:
```
-        if not cls._meta.abstract:
+        # with width_field/height_field.
+        if not cls._meta.abstract and (self.width_field or self.height_field):
             signals.post_init.connect(self.update_dimension_fields, sender=cls)
```

| # | Solution.lean impl op (`registerInitHandler`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `isAbstract`, `hasWidthField`, `hasHeightField` | `cls._meta.abstract`, `self.width_field`, `self.height_field` | R | each Python truthiness ↔ a Lean `Bool` (mapping.md §2). G-CONF drives the real attributes. |
| A2 | `if (!isAbstract && (hasWidthField || hasHeightField)) then doRegister := true else doRegister := false`; result `out = shouldRegister …` | `if not cls._meta.abstract and (self.width_field or self.height_field):` guarding the `connect` call | I | the guard predicate is transliterated identically (De Morgan-free): `not abstract and (width or height)`. The Boolean result `out` ↔ "the `connect` call executes". |
| A3 | the lower-layer registration done first carries no handler of its own (impl comment; not a spec clause) | `super().contribute_to_class(cls, name, **kwargs)` | R | the super chain (`FileField`/`Field`) connects no signal (mapping.md §3.1); modeled as identity w.r.t. the registration decision, so `out` is the complete decision. |

Discriminating content of the change — a concrete model declaring **no**
companion dimension field must NOT register the handler — lives in
`shouldRegister`'s `(hasWidthField || hasHeightField)` conjunct. The pre-patch
skeleton (`Solution_prepatch.lean`) registers for *every* concrete model and so
**fails** `out = shouldRegister …` on exactly the clause
`hasWidthField = true ∨ hasHeightField = true` (G-DIFF), which is the F2P
`test_post_init_not_connected` configuration.

## B. The synchronization site — `ImageField.update_dimension_fields` (`files.py:447-503`)

Gold hunk:
```
-        # Nothing to update if the field doesn't have dimension fields or if
-        # the field is deferred.
-        has_dimension_fields = self.width_field or self.height_field
-        if not has_dimension_fields or self.attname not in instance.__dict__:
+        # Nothing to update if the field is deferred.
+        if self.attname not in instance.__dict__:
             return
```

| # | Solution.lean impl op (`dimensionWrites`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `deferred force hasFile hasWidthField widthFilled hasHeightField heightFilled` | `self.attname not in instance.__dict__`, `force`, `bool(file)`, `self.width_field`, `bool(getattr(instance, self.width_field))`, `self.height_field`, `bool(getattr(instance, self.height_field))` | R | each Python truthiness ↔ a Lean `Bool` (mapping.md §2). |
| B2 | `if deferred then proceed := false …` | `if self.attname not in instance.__dict__: return` (post-patch; the removed `has_dimension_fields` disjunct is **gone**) | I | the post-patch deferred guard is transliterated identically. The removed disjunct is NOT in the spec — `dimUpdate` has no leading `hasWidthField||hasHeightField` guard. |
| B3 | `if (!hasFile && !force) then proceed := false` | `if not file and not force: return` | I | identical. |
| B4 | `dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))`; `if (dimFilled && !force) then proceed := false` | `dimension_fields_filled = not(...)`; `if dimension_fields_filled and not force: return` | I | identical Boolean transliteration. |
| B5 | `writeWidth := hasWidthField && proceed`; `writeHeight := hasHeightField && proceed` | `if self.width_field: setattr(...)`; `if self.height_field: setattr(...)` | I | a companion field is written iff it is declared AND the pass reached the assignment stage (`proceed`). |

The removed leading guard (`not has_dimension_fields`) is **observationally
redundant** because of B5: when `hasWidthField = hasHeightField = false`, both
writes are `false` regardless of `proceed`. So `dimUpdate` (no leading guard,
post-patch) and the pre-patch body (extra leading guard) compute the **same**
`DimWrites` on every input — which is exactly why `Solution_prepatch.lean`'s
`dimensionWrites` (which keeps the extra guard) still **verifies**: site 2 is a
behaviour-preserving refactor with no independently observable fixed behaviour.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are no consumed axioms and no deep-model references:
both changed functions are pure Boolean decision logic, modeled directly. The
one *observable* behaviour change — site 1's added `(width or height)` conjunct
— is modeled directly in `shouldRegister`, not hidden behind an axiom.

## D. verify(Solution) ⇒ resolved

`registerInitHandler` verifies only if its output equals
`shouldRegister isAbstract hasWidthField hasHeightField` (A2), i.e. the handler
is registered exactly when the model is concrete AND declares a companion
dimension field. By R (Python truthiness ↔ `Bool`) and A3 (the super chain
registers nothing) the verified decision equals the patched
`contribute_to_class` registration behaviour, which the F2P test observes.
`dimensionWrites` verifies only if it equals `dimUpdate …` (B5), the post-patch
pass logic; by B2–B5 this is the patched `update_dimension_fields` up to the
behaviour-preserving guard removal. By G-CONF the R/I transliteration of both
`shouldRegister` and `dimUpdate` agrees with `patch.diff`'s behaviour over the
fuzzed configuration grid. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms (G-AX skip).
