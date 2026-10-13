# refinement.md — django__django-11211

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `preparedValue` `do` block and the two callee axioms) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs would be mechanically refuted by **G-CONF**; here the impl region is
**all-A-tagged**, so G-CONF is skipped (`conf_skip=true`) and the A legs are
audited entirely by **G-AX** (`axiom_check.py`) + this narrative by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The value-preparation site

Gold hunk (`django/db/models/fields/__init__.py`, identifier field class body):
```
+    def get_prep_value(self, value):
+        value = super().get_prep_value(value)
+        return self.to_python(value)
```
The class previously defined no `get_prep_value`, inheriting only
`Field.get_prep_value` (the base preliminary coercion). The fix overrides it to
additionally run the field's normal-form conversion `to_python`, so a value
supplied in any accepted transcription is prepared as the SAME canonical object —
which is what lets a generic-relation prefetch match a lookup key (built from a
textual transcription of the related object's identifier) against the stored
canonical identifier.

| # | Solution.lean impl op (`preparedValue`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value : Val` (require `WellFormed value`) | `value` arg of `get_prep_value` | R | the field value space ↔ `Val` (mapping.md §2); `WellFormed` ↔ "`to_python` accepts it". |
| A2 | `let prepped :| prepped = preCoerce value` | `value = super().get_prep_value(value)` | A-consumed | `preCoerce` is the unchanged base callee `Field.get_prep_value`; the proof consumes `preCoerce_id` (identity on this domain). G-AX confirms against the real base method (mapping.md §3.1). |
| A3 | `let canon :| canon = canonicalize prepped` | `self.to_python(value)` | A-consumed | `canonicalize` is the unchanged callee `to_python`; the proof consumes `canonicalize_idem` (its output is a fixed point) to discharge `canonicalize out = out`. G-AX confirms idempotence + that a transcription is brought to the canonical object (mapping.md §3.2). |
| A4 | `return canon` | `return self.to_python(value)` | I | identical concrete op: return the converted value. |

Discriminating content of the change — performing the normal-form conversion at
all, rather than returning the value in whatever transcription it arrived in —
lives in `ensures out = canonicalize value` (and `canonicalize out = out`).
`Solution_prepatch.lean` reproduces the inherited base-only behavior
(`return preCoerce value`) and **fails** both `out = canonicalize value` and
`canonicalize out = out` — leaving the goals `value = canonicalize value` /
`canonicalize value = value`, unprovable because `canonicalize` is not the
identity on non-canonical transcriptions (G-DIFF).

## B. No second change site
The gold patch touches exactly one method. There is no additional change site,
no flag dependency, and no callee on the fix list (so no callee-under-spec).

## C. No kind-3 (inexpressible-changed-op) steps
Every step is R, A, or I. The operation that genuinely *changed* — composing the
base coercion with the field's normal-form conversion — is expressed directly as
the two-step `do` block (A2 then A3). Neither callee is the function under change
(`to_python` and the base `get_prep_value` are unchanged; the new method
`preparedValue` is the function under spec). The axioms cover only **unchanged**
callees (directive 7), pinned at their weakest sufficient strength.

## D. verify(Solution) ⇒ resolved
`preparedValue` verifies only if its output is `canonicalize value` (A3) — i.e.
the value is actually put through the field's normal-form conversion — and that
output is canonical (A4 + `canonicalize_idem`). By R (`Val ↔` the field value
space) the verified method equals `to_python(super().get_prep_value(value))` on
the well-formed inputs the F2P path supplies; by G-AX the real base callee is the
identity (A-consumed `preCoerce_id`) and the real `to_python` is idempotent and
maps a transcription to the canonical object (A-consumed `canonicalize_idem`).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE: the GFK-prefetch F2P test passes because the prepared key now matches
the stored canonical identifier). Trust points are exactly the two of plan §1.1:
axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ; G-CONF skipped as
the impl is all-A-tagged).
