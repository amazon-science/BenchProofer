# refinement.md — django__django-16569

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `deletionFieldDecision` `do` block and the deep `shouldOfferDeletion` /
`positionWithinInitial` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The decision site — `add_fields` (`django/forms/formsets.py:493`)

Gold hunk:
```
-        if self.can_delete and (self.can_delete_extra or index < initial_form_count):
+        if self.can_delete and (
+            self.can_delete_extra or (index is not None and index < initial_form_count)
+        ):
```

| # | Solution.lean impl op (`deletionFieldDecision`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `enabled : Bool` | `self.can_delete` | R | `bool ↔ Bool` (mapping.md §2). |
| A2 | param `offerOnExtra : Bool` | `self.can_delete_extra` | R | `bool ↔ Bool` (mapping.md §2). |
| A3 | param `position : Option Nat` | `index` (`int | None`) | R | `None ↔ none`, non-negative `int i ↔ some i` (mapping.md §2). |
| A4 | param `initialCount : Nat` | `initial_form_count` (the already-computed local) | R | `int (≥0) ↔ Nat` (mapping.md §2). Evaluated once before the decision; an input, not a callee. |
| A5 | `if enabled = true then … else decision := false` | `self.can_delete and (…)` | I | the outer `and` short-circuit: the whole decision is `false` when the control is disabled. |
| A6 | `if offerOnExtra = true then decision := true else decision := positionWithinInitial position initialCount` | `self.can_delete_extra or (index is not None and index < initial_form_count)` | I | the inner `or` short-circuit: offered-on-surplus wins; otherwise the position test decides. |
| A7 | `positionWithinInitial position initialCount` = `match position with | some i => decide (i < initialCount) | none => false` | `(index is not None and index < initial_form_count)` | I | the **guarded comparison**: present position ⇒ the `<` test; absent position ⇒ `false` (the `index is not None` short-circuit). This is the one operation the patch changed (the guard), modeled deeply — not axiomatized. |
| A8 | `return Except.ok decision` | the decision drives `form.fields[DELETION_FIELD_NAME] = BooleanField(...)` | R | the verdict ↔ whether the deletion field is added (mapping.md §2). `Except.ok` ⇔ the patched code never raises. |

The discriminating content of the change — an **absent** `index` must NOT attempt
the order comparison (`index < initial_form_count`) but contribute `false` — lives
in `positionWithinInitial position initialCount` with the `none ⇒ false` branch
(model) ⇔ the `index is not None and` guard (real). The pre-patch attempted the
comparison unconditionally and raised `TypeError`; `Solution_prepatch.lean`
reproduces that (the `none ⇒ Except.error` branch) and **fails** both
`out = shouldOfferDeletion …` and the `position = none → out = Except.ok (enabled
&& offerOnExtra)` clause (G-DIFF).

## B. No consumed axioms, no deep-model references to foreign callees

The decision is a self-contained boolean computation over four scalar inputs.
The only callee in the neighbourhood, `self.initial_form_count()`, is invoked
*before* the decision and only its value participates, so it is an R-abstracted
input (A4), not a callee under contract. There is no `axiom` and no
`axiom_check.py`; G-AX skips (mapping.md §3).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — adding the
`index is not None` guard to the order comparison — is modeled **deeply** (the
`none ⇒ false` branch of `positionWithinInitial`, step A7, an I op over an
R-refined carrier), not hidden behind an axiom. There is no consumed axiom about
the function under change.

## D. verify(Solution) ⇒ resolved

`deletionFieldDecision` verifies only if its output equals
`shouldOfferDeletion enabled offerOnExtra position initialCount` (A5–A8), is
always `Except.ok` (the never-raise frame), and reduces to `enabled &&
offerOnExtra` when the position is absent (the guard, A7). By R (`bool ↔ Bool`,
`int|None ↔ Option Nat`, `int ↔ Nat`, verdict ↔ field-added) the verified
decision equals the patched `add_fields` boolean on every tested configuration;
by G-CONF the R/I transliteration of the decision agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (the full boundary product plus fuzz). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (no G-AX); the only trust point is refinement fidelity (this doc, G-EQ +
G-CONF).
