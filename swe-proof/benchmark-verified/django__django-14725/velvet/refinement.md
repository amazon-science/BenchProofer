# refinement.md — django__django-14725

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `saveFormset` `do` block, plus the deep `reported` / `storedAfter` models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a free-input/deep model validated == the real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The persistence-pass site — `BaseModelFormSet.save` (`django/forms/models.py:667`)

Gold hunk:
```python
-        return self.save_existing_objects(commit) + self.save_new_objects(commit)
+        if self.edit_only:
+            return self.save_existing_objects(commit)
+        else:
+            return self.save_existing_objects(commit) + self.save_new_objects(commit)
```
plus threading the `edit_only` flag through `modelformset_factory`
(`:881`, set on the class at `:903`) and `inlineformset_factory`
(`:1085`, forwarded at `:1118`).

| # | Solution.lean impl op (`saveFormset`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `noCreate : Bool` | `self.edit_only` | R | flag ↔ Bool (mapping.md §2). The threading through the two factories sets this attribute; the only behavioural use is this branch. |
| A2 | parameter `existing : List Nat` | `self.save_existing_objects(commit)` result | R + A-reference | saved-instance list ↔ `List Nat` of identities (mapping.md §2). That this step's result is independent of the flag and creates no new rows is the **A-reference** G-AX validates (mapping.md §3.1). |
| A3 | parameter `fresh : List Nat`; the side effect on `stored` | `self.save_new_objects(commit)` result + its persistence of brand-new rows | R + A-reference | created-instance list ↔ `List Nat`; that its return value equals the brand-new rows it persists, and it is the sole source of new rows, is the **A-reference** G-AX validates (mapping.md §3.2). |
| A4 | `if noCreate then return existing` | `if self.edit_only: return self.save_existing_objects(commit)` | I | the forbid-new branch: report only the already-known identities; the new-row producer is **not** called, so no new rows are persisted (`stored` untouched). |
| A5 | `else { stored := stored ++ fresh; return existing ++ fresh }` | `else: return self.save_existing_objects(commit) + self.save_new_objects(commit)` | I | the permit-new branch: call the new-row producer (side effect `stored := stored ++ fresh`, A3) and report the already-known identities followed by the freshly produced ones (`++`). |
| A6 | `stored` is `mut`; the forbid-new branch leaves it `= storedOld` (`ensures noCreate = true → stored = storedOld`) | the absence of any `save_new_objects` call in the `edit_only` branch | R + I | the persisted-new-row set ↔ `List Nat` (mapping.md §2). Pinning `stored = storedOld` for the forbid-new branch is the directive-5 frame: no wrong impl may silently create rows while reporting an edit-only result. This is exactly the F2P-observable side effect (`Model.objects.all()` unchanged). |

Discriminating content of the change — the forbid-new policy must report only
the already-known identities AND persist no new rows — lives in
`reported true existing fresh = existing` together with
`storedAfter true storedOld fresh = storedOld`. The pre-patch `save`
unconditionally evaluated `existing + new` (and always ran the new-row
producer); `Solution_prepatch.lean` reproduces that
(`stored := stored ++ fresh; return existing ++ fresh`, ignoring `noCreate`) and
**fails** both the return clause `out = reported noCreate existing fresh` and the
frame clause `stored = storedAfter noCreate storedOld fresh` on the forbid-new
case — concretely the unsolved goal `noCreate = true → fresh = []`, which the
spec does not grant (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the guarded
selection of which component persistence steps run and are reported — is modeled
**deeply** (`reported`, `storedAfter`, the `if` in the `do` block), not hidden
behind an axiom about the function under change. There is no consumed axiom; the
only A legs are **A-reference** abstractions of the two **unchanged** callees
(`save_existing_objects`, `save_new_objects`), validated by G-AX.

## C. verify(Solution) ⇒ resolved

`saveFormset` verifies only if (a) it reports just the already-known identities
and leaves the persisted set untouched when new rows are forbidden (A4, A6), and
(b) it reports the already-known identities followed by the freshly produced
ones and grows the persisted set by exactly those when new rows are permitted
(A5). By R (`edit_only ↔ Bool`, saved/created instances ↔ `List Nat` of
identities, `+ ↔ ++`) the verified model equals the patched
`BaseModelFormSet.save` on the tested inputs; by G-AX the real
`save_existing_objects` result is flag-independent and creates no new rows
(A-reference), and the real `save_new_objects` return equals the brand-new rows
it persists and is the sole new-row source (A-reference); by G-CONF the R/I
transliteration of the branch (reported list + new-row-producer-invoked side
effect) agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: A-reference soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
