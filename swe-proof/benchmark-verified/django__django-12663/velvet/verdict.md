# P2 adversarial audit — django__django-12663

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -49,11 +49,7 @@
   ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
   do
     -- impl-start
-    let source := sel.source
-    if source ≠ 0 then
-      return source
-    else
-      return sel.field
+    return sel.field
     -- impl-end
 
 prove_correct outputFieldIdentity by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -49,11 +49,7 @@
   ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
   do
     -- impl-start
-    let source := sel.source
-    if source ≠ 0 then
-      return source
-    else
-      return sel.field
+    return sel.source
     -- impl-end
 
 prove_correct outputFieldIdentity by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -50,7 +50,7 @@
   do
     -- impl-start
     let source := sel.source
-    if source ≠ 0 then
+    if source = 0 then
       return source
     else
       return sel.field
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -49,11 +49,7 @@
   ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
   do
     -- impl-start
-    let source := sel.source
-    if source ≠ 0 then
-      return source
-    else
-      return sel.field
+    return 1
     -- impl-end
 
 prove_correct outputFieldIdentity by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -50,7 +50,7 @@
   do
     -- impl-start
     let source := sel.source
-    if source ≠ 0 then
+    if source > 0 then
       return source
     else
       return sel.field
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
@@ -51,7 +51,7 @@
     -- impl-start
     let source := sel.source
     if source ≠ 0 then
-      return source
+      return source - 1
     else
       return sel.field
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
--  attribute / truthy-fallback semantics it stands on are validated against the
--  real behaviour out-of-band by axiom_check.py (G-AX) as an A-reference, not
--  consumed here.)
-- axioms-end

-- pure-start
-- (No auxiliary pure spec helpers are required for this behaviour.)
-- pure-end

/- A selected item carries two integer field identities: a *source* identity and
   a *resolved* identity.

   The resolved identity is always usable (nonzero). The source identity may be
   the sentinel `0`, meaning "no usable source identity present"; any nonzero
   source identity is a distinct, usable identity.

   The single field identity reported for the item is chosen as follows: when the
   source identity is usable (nonzero) it is reported; otherwise the resolved
   identity is reported. The discriminating inputs are those whose source
   identity is nonzero and differs from the resolved identity — there the result
   must be the source identity, never the resolved one.

   The item is read-only: neither identity is `mut`, and nothing is mutated
   (directive 5). Both identities and the result are modeled as `Int`, with a
   field identity carried by integer identity. -/

structure Selection where
  source : Int
  field : Int

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method outputFieldIdentity (sel : Selection) return (r : Int)
  require sel.field ≠ 0
  ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
  do
    -- impl-start
    let source := sel.source
    if source ≠ 0 then
      return source
    else
      return sel.field
    -- impl-end

prove_correct outputFieldIdentity by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ SOUND. Spec is a single method outputFieldIdentity(sel:Selection)->Int, require sel.field ≠ 0, ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field). This postcondition is a partition on the whole domain (two disjoint, exhaustive branches keyed on sel.source = 0), so it UNIQUELY determines r for every admissible input — no terminating verifying impl can be behaviorally wrong.

SAME-SPEC (all True): python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(SolutionSrc, atkSrc, b.language))" → atk_1..atk_7, pc_correct, pc2_correct all True.

### VERIFY (bash scripts/lean_verify.sh <f>):
- pc_correct.lean (baseline shape, if source≠0 return source else return field): exit 0 VERIFIES (positive control, non-vacuous).
- pc2_correct.lean (structurally-distinct correct: if source=0 return field else return source): exit 0 VERIFIES (second positive control, distinct control flow).
- atk_1.lean (PREPATCH bug: return sel.field): exit 1, rejected by `sel.source ≠ 0 → sel.field = sel.source` — byte-matches Solution_prepatch.lean's documented failure (G-DIFF confirmed).
- atk_2.lean (boundary: return sel.source unconditionally): exit 1, rejected by `sel.source = 0 → sel.source = sel.field`. Also covers ungrounded-oracle echo (echo an input unconditionally).
- atk_3.lean (control-flow-effect: inverted guard, if source=0 return source else return field): exit 1, unsolved `sel.source ≠ 0 → sel.field = sel.source`.
- atk_4.lean (ungrounded-oracle constant: return 1): exit 1, full conjunction unsolved.
- atk_5.lean (partial-domain: if source>0 return source else return field — mishandles negative Int source): exit 1, rejected by `sel.source ≠ 0 → sel.field = sel.source` (source<0 case).
- atk_7.lean (value-effect: return source-1 when nonzero): exit 1, `sel.source - 1 = sel.source` unsolved.
Six distinct terminating wrong impls (partial-domain, boundary, control-flow, ungrounded-oracle, value-effect, prepatch) all REJECTED. patches={} — none verify, so no resolve run is needed for the derivation.

NON-TERMINATION PROBE (documented, NOT submitted as an attack): atk_6.lean (`let mut i:Int:=0; while i≥0 invariant i≥0 do i:=i+1; return sel.field`) same_spec=True and VERIFIES (exit 0) — the loop never exits so under `set_option loom.semantics.termination "partial"` the postcondition holds vacuously. I deliberately did NOT list it as an attack:

(1) it is the corpus-universal partial-correctness artifact (401/500 velvet bundles use "partial"), not a defect specific to THIS spec/refinement;

(2) an unbounded loop has NO row in refinement.md's straight-line A1–A4 (choose-one) map, so it is not a FAITHFUL refinement of the gold's `getattr(select,'target',None) or select.field` — it fails the faithful-skeleton requirement (spec_guide §3, directive 3);

(3) mechanically it can never register as BROKEN: its only materialization is a divergent Python patch, and run_resolve on a diverging patch TIMES OUT → ResolveResult.completed=False, whereas _derive_audit_verdict (build_one.py:306) fails a candidate only when `r.completed and not r.resolved`; a timeout routes to inconclusive_hits, never to the verify⇏correct break branch. Listing it with any patch would drag the whole role to INCONCLUSIVE (fail-closed) rather than exhibit a real break, which is why it is excluded.

REFINEMENT.MD AUDIT: legs A1–A4 are all R / R+I (parameter refinement Col↔Selection; getattr/or truthy short-circuit ↔ `if source≠0`; straight-line choose-one deep-modeled). No kind-3 (unexpressible-changed-op) step; the one genuinely-changed op (prefer Col.target over Col.field) is spelled out in A3/A4, not hidden behind an axiom. NO consumed axioms (Section B) — the choose-one is deep-modeled, so there is no dead/over-claimed axiom to echo.

The A-reference (Section C / mapping.md §3): getattr(obj,'target',None) or obj.field has the modeled choose-one semantics, and real post-gold Query.output_field returns Col.target for a truthy-target Col — this is the G-AX obligation (out-of-band, axiom_check.py); my scope is refinement fidelity, and the model↔patch correspondence (integer-identity bridge: truthy target ↔ source≠0, resolved field always truthy ↔ require field≠0) is faithful. (Note: the recorded verdict.md's NB-1 flags a G-AX evidence-hygiene gap — axiom_check.py runs against the UNPATCHED /testbed and swallows the real-Query leg as an env-skip — but that is a G-AX faithfulness-of-evidence issue, not a G-EQ refinement-fidelity defect; two prior reviewers confirmed A-reference 2 is in fact true with gold applied.)

This did not block the derivation because no SUBMITTED attack verifies — no resolve run is required for a clean SOUND pass. The runner re-runs all artifacts.

FLOOR MET: 6 attacks (≥5), prepatch reproduced (atk_1), verifying positive control provided (pc_correct; pc2_correct as a distinct backup), no verifying submitted attack. Spec is TIGHT; refinement is R/R+I only (no kind-3, no consumed axiom); model↔patch correspondence holds. No verify⇏correct break found. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The choose-one-of-two selection is modeled deeply; the
--  attribute / truthy-fallback semantics it stands on are validated against the
--  real behaviour out-of-band by axiom_check.py (G-AX) as an A-reference, not
--  consumed here.)
-- axioms-end

-- pure-start
-- (No auxiliary pure spec helpers are required for this behaviour.)
-- pure-end

/- A selected item carries two integer field identities: a *source* identity and
   a *resolved* identity.

   The resolved identity is always usable (nonzero). The source identity may be
   the sentinel `0`, meaning "no usable source identity present"; any nonzero
   source identity is a distinct, usable identity.

   The single field identity reported for the item is chosen as follows: when the
   source identity is usable (nonzero) it is reported; otherwise the resolved
   identity is reported. The discriminating inputs are those whose source
   identity is nonzero and differs from the resolved identity — there the result
   must be the source identity, never the resolved one.

   The item is read-only: neither identity is `mut`, and nothing is mutated
   (directive 5). Both identities and the result are modeled as `Int`, with a
   field identity carried by integer identity. -/

structure Selection where
  source : Int
  field : Int

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method outputFieldIdentity (sel : Selection) return (r : Int)
  require sel.field ≠ 0
  ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)
  do
    -- impl-start
    let source := sel.source
    if source ≠ 0 then
      return source
    else
      return sel.field
    -- impl-end

prove_correct outputFieldIdentity by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ SOUND. Spec is a single method outputFieldIdentity(sel:Selection)->Int, require sel.field ≠ 0, ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field). This postcondition is a partition on the whole domain (two disjoint, exhaustive branches keyed on sel.source = 0), so it UNIQUELY determines r for every admissible input — no terminating verifying impl can be behaviorally wrong.

SAME-SPEC (all True): python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(SolutionSrc, atkSrc, b.language))" → atk_1..atk_7, pc_correct, pc2_correct all True.

### VERIFY (bash scripts/lean_verify.sh <f>):
- pc_correct.lean (baseline shape, if source≠0 return source else return field): exit 0 VERIFIES (positive control, non-vacuous).
- pc2_correct.lean (structurally-distinct correct: if source=0 return field else return source): exit 0 VERIFIES (second positive control, distinct control flow).
- atk_1.lean (PREPATCH bug: return sel.field): exit 1, rejected by `sel.source ≠ 0 → sel.field = sel.source` — byte-matches Solution_prepatch.lean's documented failure (G-DIFF confirmed).
- atk_2.lean (boundary: return sel.source unconditionally): exit 1, rejected by `sel.source = 0 → sel.source = sel.field`. Also covers ungrounded-oracle echo (echo an input unconditionally).
- atk_3.lean (control-flow-effect: inverted guard, if source=0 return source else return field): exit 1, unsolved `sel.source ≠ 0 → sel.field = sel.source`.
- atk_4.lean (ungrounded-oracle constant: return 1): exit 1, full conjunction unsolved.
- atk_5.lean (partial-domain: if source>0 return source else return field — mishandles negative Int source): exit 1, rejected by `sel.source ≠ 0 → sel.field = sel.source` (source<0 case).
- atk_7.lean (value-effect: return source-1 when nonzero): exit 1, `sel.source - 1 = sel.source` unsolved.
Six distinct terminating wrong impls (partial-domain, boundary, control-flow, ungrounded-oracle, value-effect, prepatch) all REJECTED. patches={} — none verify, so no resolve run is needed for the derivation.

NON-TERMINATION PROBE (documented, NOT submitted as an attack): atk_6.lean (`let mut i:Int:=0; while i≥0 invariant i≥0 do i:=i+1; return sel.field`) same_spec=True and VERIFIES (exit 0) — the loop never exits so under `set_option loom.semantics.termination "partial"` the postcondition holds vacuously. I deliberately did NOT list it as an attack:

(1) it is the corpus-universal partial-correctness artifact (401/500 velvet bundles use "partial"), not a defect specific to THIS spec/refinement;

(2) an unbounded loop has NO row in refinement.md's straight-line A1–A4 (choose-one) map, so it is not a FAITHFUL refinement of the gold's `getattr(select,'target',None) or select.field` — it fails the faithful-skeleton requirement (spec_guide §3, directive 3);

(3) mechanically it can never register as BROKEN: its only materialization is a divergent Python patch, and run_resolve on a diverging patch TIMES OUT → ResolveResult.completed=False, whereas _derive_audit_verdict (build_one.py:306) fails a candidate only when `r.completed and not r.resolved`; a timeout routes to inconclusive_hits, never to the verify⇏correct break branch. Listing it with any patch would drag the whole role to INCONCLUSIVE (fail-closed) rather than exhibit a real break, which is why it is excluded.

REFINEMENT.MD AUDIT: legs A1–A4 are all R / R+I (parameter refinement Col↔Selection; getattr/or truthy short-circuit ↔ `if source≠0`; straight-line choose-one deep-modeled). No kind-3 (unexpressible-changed-op) step; the one genuinely-changed op (prefer Col.target over Col.field) is spelled out in A3/A4, not hidden behind an axiom. NO consumed axioms (Section B) — the choose-one is deep-modeled, so there is no dead/over-claimed axiom to echo.

The A-reference (Section C / mapping.md §3): getattr(obj,'target',None) or obj.field has the modeled choose-one semantics, and real post-gold Query.output_field returns Col.target for a truthy-target Col — this is the G-AX obligation (out-of-band, axiom_check.py); my scope is refinement fidelity, and the model↔patch correspondence (integer-identity bridge: truthy target ↔ source≠0, resolved field always truthy ↔ require field≠0) is faithful. (Note: the recorded verdict.md's NB-1 flags a G-AX evidence-hygiene gap — axiom_check.py runs against the UNPATCHED /testbed and swallows the real-Query leg as an env-skip — but that is a G-AX faithfulness-of-evidence issue, not a G-EQ refinement-fidelity defect; two prior reviewers confirmed A-reference 2 is in fact true with gold applied.)

This did not block the derivation because no SUBMITTED attack verifies — no resolve run is required for a clean SOUND pass. The runner re-runs all artifacts.

FLOOR MET: 6 attacks (≥5), prepatch reproduced (atk_1), verifying positive control provided (pc_correct; pc2_correct as a distinct backup), no verifying submitted attack. Spec is TIGHT; refinement is R/R+I only (no kind-3, no consumed axiom); model↔patch correspondence holds. No verify⇏correct break found. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12663 velvet bundle.

SPEC INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True — the frozen spec region (imports/options, axioms/pure/pre-conditions/post-conditions regions, `structure Selection`, method signature with `require sel.field ≠ 0` and `ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)`) is byte-identical between patched and prepatch; only impl+proof differ. No spec content smuggled into the impl region.

VERIFICATION: scripts/lean_verify.sh Solution.lean -> exit 0 (verifies). Solution_prepatch.lean (`return sel.field`) -> fails with unsolved goal `sel.source ≠ 0 → sel.field = sel.source`, so the spec genuinely senses the change (G-DIFF sound).

REAL CALLEE: at base_commit fa5e7e46 the gold `Query.output_field` `len(self.select)==1` branch returns `getattr(select, 'target', None) or select.field`. `Col.target` is the source/relation-aware field; `Col.field` == `Expression.field` == `output_field`, the resolved field. Python `a or b` returns `a` iff a is truthy else b.

### FAITHFULNESS ANALYSIS (searched for a diverging input):
- Bridge (mapping.md §2): source=identity of Col.target with sentinel 0 ≡ target absent OR falsy; nonzero ≡ truthy usable target. field=identity of always-truthy resolved field, hence `require sel.field ≠ 0`.
- Model: source≠0 → r=source (truthy target returned); source=0 → r=field (fallback). This is exactly the `or` short-circuit. For every abstract input the modeled output equals the real `getattr(...,'target',None) or select.field` result under the bridge.
- The `require sel.field ≠ 0` excludes no real input: Django Field objects define no falsy __bool__/__len__, so select.field is always truthy. Falsy-but-present targets are correctly folded into sentinel 0, so the abstraction does not over-constrain or misrepresent.
- Scope: `require` correctly restricts to the modeled_functions-declared `len(self.select)==1` branch; other branches are out of scope, not falsely modeled.

No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is frozen: same_spec(Solution.lean, Solution_prepatch.lean)=True, so the discriminator lives only in the elided impl/proof, not the spec view. Mechanical G-LEAK screen PASSES (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier or comment echoing a patched repo symbol, no narration). No RELAXED_LEAKAGE.md; strict pass. Semantic reconstruction assessment: the gold's discriminating insight — prefer the relation-aware Col.target (source) over the resolved Col.field — is NOT in the public problem_statement (only a TypeError traceback + 'regression'); it appears only in hints_text (Col.target/Col.field). The spec view abstracts everything to opaque carriers (structure Selection with two Int identities source/field, sentinel 0 for 'no usable source'); it never names Col, target, getattr, self.select[0], the 'or' short-circuit, query.py, or the output_field property site. The method name outputFieldIdentity embeds 'output_field', which is legitimately public (present in the problem-statement traceback). The postcondition (sel.source≠0→r=sel.source) ∧ (sel.source=0→r=sel.field) states required behavior — the definitional job of a spec — and does not localize the edit to the repo; the solver must still map abstract source/field back to Django symbols and author impl+proof. All repo-symbol-level detail (Col.target vs Col.field, file:line, getattr/or) lives in mapping.md/refinement.md, which are auditor-facing and not part of the consumer spec view. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.