# refinement.md — django__django-13741

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`readonlyDigestFieldLocked` `do` block, the `lockedDefault` pure model, and the
`noEdit*` axioms) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** where the proof
uses the axiom's `ensures`, **A-reference** where a deep model is validated ==
the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The default site — `ReadOnlyPasswordHashField.__init__` (`forms.py:59`)

Gold hunk:
```
     def __init__(self, *args, **kwargs):
         kwargs.setdefault("required", False)
+        kwargs.setdefault('disabled', True)
         super().__init__(*args, **kwargs)
```

| # | Solution.lean impl op (`readonlyDigestFieldLocked`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `userFlag : Option Bool` | the `'disabled'` entry of `**kwargs` (absent / present) | R | `none` ↔ key absent; `some b` ↔ `disabled=b` (mapping.md §2). `setdefault` only acts when the key is absent, so the three-valued carrier is exactly the observable input. |
| A2 | `out := userFlag.getD true` | `kwargs.setdefault('disabled', True)` then `self.disabled = kwargs['disabled']` (base `Field.__init__`) | I | `setdefault(k, d)` returns the existing value if present else inserts and returns `d`; observationally `kwargs.get('disabled', True)`. `Option.getD true` is the identical concrete op under the §2 bijection. The resulting `self.disabled` is the returned `out`. |
| A3 | `out` returned (`Bool`) | `self.disabled` attribute after `__init__` | R | `True ↔ true` / `False ↔ false` (mapping.md §2). The F2P test observes `field.disabled is True`. |

Discriminating content of the change — unspecified ⇒ **non-editable**
(`disabled is True`), where the generic field framework defaults to editable
(`disabled=False`) — lives in `lockedDefault none = true` (model) ⇔ the inserted
`setdefault('disabled', True)` (real). The pre-patch constructor inserted no such
default, so `disabled` fell through to base `Field`'s `False`;
`Solution_prepatch.lean` reproduces that (`userFlag.getD false`) and **fails**
`out = lockedDefault userFlag` on the `userFlag = none` case (G-DIFF). This is
exactly the F2P assertion `self.assertIs(field.disabled, True)`.

## B. The deleted-override safety site — `bound_data` / `has_changed` / `clean_password`

Gold also DELETES `ReadOnlyPasswordHashField.bound_data` (`return initial`),
`ReadOnlyPasswordHashField.has_changed` (`return False`), and
`UserChangeForm.clean_password` (`return self.initial.get('password')`). These
deletions are SAFE precisely because, once the field is non-editable by default
(site A), the UNCHANGED base `Field` provides the same behaviour through its
`disabled` guards. The two postconditions encode that safety.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `noEditChange` axiom + `ensures noEditChange (lockedDefault none) initial data = false` | deletion of `ReadOnlyPasswordHashField.has_changed`/`clean_password` | A-consumed | `noEditChange true _ _ = false` is the weakest fact on the unchanged base `Field.has_changed` (`if self.disabled: return False`) the safety needs: with the new default the field reports no change, so the bespoke `has_changed`/`clean_password` are redundant. Proof consumes the axiom via the postcondition. G-AX confirms against the real `Field.has_changed`. |
| B2 | `noEditValue` axiom + `ensures noEditValue (lockedDefault none) data initial = initial` | deletion of `ReadOnlyPasswordHashField.bound_data` | A-consumed | `noEditValue true _ initial = initial` is the weakest fact on the unchanged base `Field.bound_data` (`if self.disabled: return initial`) the safety needs: with the new default the bound value is the stored `initial`, so the bespoke `bound_data` is redundant. G-AX confirms against the real `Field.bound_data`. |

No separate failing prepatch for site B: the deletions are behaviour-preserving
GIVEN site A's new default, and their content lives entirely in the frozen
`noEdit*` axioms (a prepatch must keep the spec byte-identical, G-DIFF). Their
soundness is audited by G-AX and their necessity-given-the-default by the two
postconditions, which are evaluated at `lockedDefault none = true` — i.e. they
only hold because site A makes the field non-editable. Site A's prepatch already
exercises the single observable F2P change (`field.disabled is True`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
constructor's default for the non-editability flag — is modeled **directly** by
`lockedDefault`/`Option.getD` (step A2, an I op), not hidden behind an axiom
about the function under change: there is no consumed axiom about
`ReadOnlyPasswordHashField.__init__`. The only consumed axioms, `noEdit*`
(site B), cover the two **unchanged** base `Field` callees the patch's deletions
rely on.

## D. verify(Solution) ⇒ resolved

`readonlyDigestFieldLocked` verifies only if its output equals
`lockedDefault userFlag` (none ⇒ true, some b ⇒ b; A2) and the two non-editable
consequences hold at the new default (B1, B2). By R (`Option Bool ↔ optional
kwarg`, `Bool ↔ self.disabled`) the verified flag equals the `self.disabled` the
patched constructor produces on every input; by G-AX the `noEdit*` axioms hold of
the real base `Field.has_changed`/`bound_data` (A-consumed); by G-CONF the R/I
transliteration of `lockedDefault` agrees with `patch.diff`'s constructed
`field.disabled` on ≥10⁵ inputs. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and audited callees —
and the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
