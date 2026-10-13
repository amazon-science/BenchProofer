# P2 adversarial audit — astropy__astropy-13398

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_diverge.lean`, `atk_2_forcecentre.lean`, `atk_3_swapcomp.lean`, `atk_5_wrongcallee.lean`, `atk_7_partialdomain.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4_roundtrip_echo.lean`, `atk_6_dropoffset.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying wrong-impl has a faithful refined patch that fails to resolve. The two attacks that verify (atk_4, atk_6) are echo-shaped: they compute values PROVABLY EQUAL to the gold-modeled output on the tested path, so their faithful refined patch IS the gold patch, which resolves (executed run_resolve: RESOLVED=True, 4/4 FAIL_TO_PASS + 68/68 PASS_TO_PASS).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,6 +99,11 @@
   ensures comp = 2 → out = fwdZ vx vy vz
   do
     -- impl-start
+    let mut i : Int := 1
+    while i > 0
+      decreasing i
+    do
+      i := i + 1
     if comp = 0 then
       return fwdX vx vy vz
     else if comp = 1 then
```

Attack 2 — `atk_2_forcecentre.lean` → rejected (same spec, does not verify — good)

```diff
@@ -186,15 +186,12 @@
   ensures comp = 2 → out = protZ vx vy vz
   do
     -- impl-start
-    -- Rotate, then carry the offset for referring the result to the output
-    -- frame's own site L. That is the same site the position is anchored at, so
-    -- the offset is zero (no-op) and the result is the pure rotation.
-    if comp = 0 then
-      return protX vx vy vz + offsetX lx ly lz lx ly lz
-    else if comp = 1 then
-      return protY vx vy vz + offsetY lx ly lz lx ly lz
-    else
-      return protZ vx vy vz + offsetZ lx ly lz lx ly lz
+    if comp = 0 then
+      return protX vx vy vz + offsetX lx ly lz 0 0 0
+    else if comp = 1 then
+      return protY vx vy vz + offsetY lx ly lz 0 0 0
+    else
+      return protZ vx vy vz + offsetZ lx ly lz 0 0 0
     -- impl-end
 end
 
```

Attack 3 — `atk_3_swapcomp.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,9 +100,9 @@
   do
     -- impl-start
     if comp = 0 then
+      return fwdY vx vy vz
+    else if comp = 1 then
       return fwdX vx vy vz
-    else if comp = 1 then
-      return fwdY vx vy vz
     else
       return fwdZ vx vy vz
     -- impl-end
```

Attack 4 — `atk_4_roundtrip_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -151,17 +151,12 @@
   ensures comp = 2 → out = vz
   do
     -- impl-start
-    -- The observer-centred components are the forward action of the input; the
-    -- transpose-action then inverts it, recovering the original position.
-    let ox := fwdX vx vy vz
-    let oy := fwdY vx vy vz
-    let oz := fwdZ vx vy vz
-    if comp = 0 then
-      return bwdX ox oy oz
-    else if comp = 1 then
-      return bwdY ox oy oz
-    else
-      return bwdZ ox oy oz
+    if comp = 0 then
+      return vx
+    else if comp = 1 then
+      return vy
+    else
+      return vz
     -- impl-end
 end
 
```

Attack 5 — `atk_5_wrongcallee.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,11 +124,11 @@
   do
     -- impl-start
     if comp = 0 then
-      return bwdX ox oy oz
-    else if comp = 1 then
-      return bwdY ox oy oz
-    else
-      return bwdZ ox oy oz
+      return fwdX ox oy oz
+    else if comp = 1 then
+      return fwdY ox oy oz
+    else
+      return fwdZ ox oy oz
     -- impl-end
 end
 
```

Attack 6 — `atk_6_dropoffset.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -186,15 +186,12 @@
   ensures comp = 2 → out = protZ vx vy vz
   do
     -- impl-start
-    -- Rotate, then carry the offset for referring the result to the output
-    -- frame's own site L. That is the same site the position is anchored at, so
-    -- the offset is zero (no-op) and the result is the pure rotation.
-    if comp = 0 then
-      return protX vx vy vz + offsetX lx ly lz lx ly lz
-    else if comp = 1 then
-      return protY vx vy vz + offsetY lx ly lz lx ly lz
-    else
-      return protZ vx vy vz + offsetZ lx ly lz lx ly lz
+    if comp = 0 then
+      return protX vx vy vz
+    else if comp = 1 then
+      return protY vx vy vz
+    else
+      return protZ vx vy vz
     -- impl-end
 end
 
```

Attack 7 — `atk_7_partialdomain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
     else if comp = 1 then
       return fwdY vx vy vz
     else
-      return fwdZ vx vy vz
+      return fwdX vx vy vz
     -- impl-end
 end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The constant orthogonal orientation matrix applied to a three-component
   position, returned componentwise (`fwdX`/`fwdY`/`fwdZ` are the three rows of
   `M · v`). `M` is built by the unchanged rotation-matrix machinery and applied
   by the unchanged Cartesian transform; the action is left uninterpreted — the
   only property the round-trip proof needs is that its transpose-action inverts
   it (the `orth_*` facts below). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom fwdX : Int → Int → Int → Int
axiom fwdY : Int → Int → Int → Int
axiom fwdZ : Int → Int → Int → Int

/- The TRANSPOSE of the same orientation matrix applied to a position
   (`M^T · v`), componentwise — the inverse rotation. Unchanged callee. -/
axiom bwdX : Int → Int → Int → Int
axiom bwdY : Int → Int → Int → Int
axiom bwdZ : Int → Int → Int → Int

/- The single fact about the unchanged orthogonal orientation matrix the proof
   consumes: the transpose-action applied to the forward-action of any position
   returns that position componentwise (the transpose of an orthogonal matrix is
   its inverse). The matrix is otherwise uninterpreted. -/
axiom orth_x : ∀ x y z : Int, bwdX (fwdX x y z) (fwdY x y z) (fwdZ x y z) = x
axiom orth_y : ∀ x y z : Int, bwdY (fwdX x y z) (fwdY x y z) (fwdZ x y z) = y
axiom orth_z : ∀ x y z : Int, bwdZ (fwdX x y z) (fwdY x y z) (fwdZ x y z) = z

/- A second constant orthogonal rotation `P` (relating an Earth-rotating
   orientation to an intermediate Earth-equatorial one) applied to a position,
   componentwise (`P · v`). A distinct unchanged callee (the precession-nutation
   orientation matrix and the Cartesian transform). Provenance + soundness:
   mapping.md / axiom_check.py. -/
axiom protX : Int → Int → Int → Int
axiom protY : Int → Int → Int → Int
axiom protZ : Int → Int → Int → Int

/- The TRANSPOSE of the rotation `P` applied to a position (`P^T · v`),
   componentwise — the inverse rotation. Unchanged callee. -/
axiom protInvX : Int → Int → Int → Int
axiom protInvY : Int → Int → Int → Int
axiom protInvZ : Int → Int → Int → Int

/- The single fact about the second unchanged orthogonal rotation `P` the proof
   consumes: its transpose-action inverts its forward-action componentwise. -/
axiom prot_orth_x : ∀ x y z : Int, protInvX (protX x y z) (protY x y z) (protZ x y z) = x
axiom prot_orth_y : ∀ x y z : Int, protInvY (protX x y z) (protY x y z) (protZ x y z) = y
axiom prot_orth_z : ∀ x y z : Int, protInvZ (protX x y z) (protY x y z) (protZ x y z) = z

/- The viewpoint-dependent directional offset the transform carries when a
   near-Earth position whose frame is anchored at site `L = (lx, ly, lz)` is
   referred to a frame anchored at site `T = (tx, ty, tz)`, along the route that
   ties the position to the Solar-System barycentre — the geocentric-versus-
   topocentric difference, componentwise. An unchanged callee (the re-referencing
   transform between two same-kind frames); otherwise uninterpreted. Provenance +
   soundness: mapping.md / axiom_check.py. -/
axiom offsetX : Int → Int → Int → Int → Int → Int → Int
axiom offsetY : Int → Int → Int → Int → Int → Int → Int
axiom offsetZ : Int → Int → Int → Int → Int → Int → Int

/- The single fact about the unchanged re-referencing transform the proof
   consumes: referring a position whose frame is anchored at a site to a frame
   anchored at the SAME site introduces no offset (it is a no-op). The weakest
   fact sufficient for the agreement proof; the offset is otherwise
   uninterpreted. -/
axiom same_site_x : ∀ lx ly lz : Int, offsetX lx ly lz lx ly lz = 0
axiom same_site_y : ∀ lx ly lz : Int, offsetY lx ly lz lx ly lz = 0
axiom same_site_z : ∀ lx ly lz : Int, offsetZ lx ly lz lx ly lz = 0
-- axioms-end

-- pure-start
-- (no module-level pure helpers required)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Forward conversion of a three-component position from an Earth-rotating
   orientation to an observer-centred orientation. The desired behavior: the
   selected output component is the constant orthogonal orientation matrix
   applied DIRECTLY to the given position (`comp` selects which of the three
   output components to return). Pinning each component to the forward action of
   the input itself — with no intermediate viewpoint shift — forces the direct
   orthogonal rotation. -/
noncomputable section
method itrsToObserved (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = fwdX vx vy vz
  ensures comp = 1 → out = fwdY vx vy vz
  ensures comp = 2 → out = fwdZ vx vy vz
  do
    -- impl-start
    if comp = 0 then
      return fwdX vx vy vz
    else if comp = 1 then
      return fwdY vx vy vz
    else
      return fwdZ vx vy vz
    -- impl-end
end

prove_correct itrsToObserved by
  loom_solve

/- Backward conversion of a three-component position from an observer-centred
   orientation to an Earth-rotating orientation. The desired behavior: the
   selected output component is the TRANSPOSE action (inverse rotation) applied
   DIRECTLY to the observer-centred input. -/
noncomputable section
method observedToItrs (comp : Int) (ox : Int) (oy : Int) (oz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = bwdX ox oy oz
  ensures comp = 1 → out = bwdY ox oy oz
  ensures comp = 2 → out = bwdZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedToItrs by
  loom_solve

/- The round-trip identity for the direct conversion pair. The desired behavior:
   converting an Earth-rotating position to the observer-centred orientation and
   back returns the original position exactly (componentwise). This is the exact
   geometric round trip the issue demands of the direct pair; it holds precisely
   because the orientation matrix is orthogonal, so its transpose undoes it. A
   conversion that instead reaches the observer-centred orientation by an
   INDIRECT route — introducing a viewpoint-dependent directional shift rather
   than applying the orthogonal matrix directly — does NOT round-trip exactly. -/
noncomputable section
method observedRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The observer-centred components are the forward action of the input; the
    -- transpose-action then inverts it, recovering the original position.
    let ox := fwdX vx vy vz
    let oy := fwdY vx vy vz
    let oz := fwdZ vx vy vz
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedRoundtrip by
  loom_solve <;>
    simp_all [orth_x, orth_y, orth_z]

/- Forward conversion of a three-component position from an Earth-equatorial
   orientation to an Earth-rotating orientation, tied to an observing site `L`.
   The desired behavior: the position is referred to the output frame anchored
   at the SAME site `L = (lx, ly, lz)` it already carries, so referring to it
   introduces no viewpoint offset and the selected component is the rotation `P`
   applied to the given position with NO spurious viewpoint shift. Pinning each
   component to the bare rotation of the input forces the transform to honour the
   frame's own site rather than referring to one single constant site. -/
noncomputable section
method equToRot (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protX vx vy vz
  ensures comp = 1 → out = protY vx vy vz
  ensures comp = 2 → out = protZ vx vy vz
  do
    -- impl-start
    -- Rotate, then carry the offset for referring the result to the output
    -- frame's own site L. That is the same site the position is anchored at, so
    -- the offset is zero (no-op) and the result is the pure rotation.
    if comp = 0 then
      return protX vx vy vz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protY vx vy vz + offsetY lx ly lz lx ly lz
    else
      return protZ vx vy vz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct equToRot by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- Backward conversion of a three-component position from an Earth-rotating
   orientation to an Earth-equatorial orientation, carrying the observing site
   `L`. The desired behavior: apply the TRANSPOSE of `P` (the inverse rotation)
   to the input and carry the input frame's own site `L` onto the result, so
   referring to the output frame's own (same) site is a no-op; the selected
   component is the inverse rotation of the input with NO spurious viewpoint
   shift. -/
noncomputable section
method rotToEqu (comp : Int) (ox : Int) (oy : Int) (oz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protInvX ox oy oz
  ensures comp = 1 → out = protInvY ox oy oz
  ensures comp = 2 → out = protInvZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct rotToEqu by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- The topocentric round-trip identity for the site-honouring conversion pair.
   The desired behavior: converting an Earth-equatorial position to the
   Earth-rotating orientation at site `L` and back returns the original position
   exactly (componentwise). It holds only because both legs honour the site `L`
   (so neither inserts a viewpoint offset) and `P` is orthogonal. A conversion
   that refers the position to one single constant site (the centre of the Earth, the
   origin) rather than the frame's own site introduces a viewpoint-dependent
   offset whenever the site is not the centre, so it does NOT round-trip
   exactly. -/
noncomputable section
method equRotRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The Earth-rotating components are the rotation of the input (the
    -- site-offset of each leg is a no-op at the shared site L); the transpose
    -- rotation then inverts it, recovering the original position.
    let ox := protX vx vy vz
    let oy := protY vx vy vz
    let oz := protZ vx vy vz
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct equRotRoundtrip by
  loom_solve <;>
    simp_all [prot_orth_x, prot_orth_y, prot_orth_z, same_site_x, same_site_y, same_site_z]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight-equality. Every 'real' method postcondition pins output to a UNIQUE axiom expression (out = fwdX/protX vx vy vz; out = vx). So ANY verifying impl is observationally gold-identical on the tested path -> verify => correct.

ATTACKS (all same_spec=True vs frozen Solution.lean, verified with markers.same_spec; verify cmd: `bash scripts/lean_verify.sh <file>`, exit 0=verifies, 1=error/spec-sensed):
 1. atk_1_diverge.lean  -- CLEAN non-terminating loop (while i>0; i:=i+1; decreasing i) before correct returns in itrsToObserved. EXIT=1 (goal `Nat.zero < Nat.zero` unprovable). REJECTED: total-correctness semantics (loom.semantics.termination "total") correctly refuses divergence. NOTE: this re-encodes the PRIOR pass's INCONCLUSIVE attack, which used invalid Velvet syntax (`while true do pass`) and failed to CLASSIFY (not a real break). Cleanly re-encoded, divergence is soundly rejected.
 2. atk_2_forcecentre.lean -- prepatch bug: equToRot uses offset*(L, 0 0 0) (force geocentre) instead of offset*(L,L). EXIT=1. REJECTED (same_site_* gives only offset*(L,L)=0; offset*(L,0) uninterpreted != 0). Mirrors Solution_prepatch.lean / G-DIFF.
 3. atk_3_swapcomp.lean -- control-flow: itrsToObserved returns fwdY for comp=0, fwdX for comp=1. EXIT=1 REJECTED (fwdX != fwdY).
 4. atk_4_roundtrip_echo.lean -- ungrounded-oracle echo: observedRoundtrip returns vx/vy/vz directly. EXIT=0 VERIFIES. BENIGN: observedRoundtrip is a MODELED COMPOSITE (no distinct code region; the test's chained transform_to). Returning v = bwd(fwd(v)) by orth_* -> observationally identical to gold. Faithful patch = gold.
 5. atk_5_wrongcallee.lean -- observedToItrs returns fwd* (forward) instead of bwd* (transpose). EXIT=1 REJECTED (fwdZ != bwdZ).
 6. atk_6_dropoffset.lean -- equToRot drops the '+ offset* lx ly lz lx ly lz' term (bare rotation). EXIT=0 VERIFIES. BENIGN: same_site_* proves offset*(L,L)=0, so protX v ≡ protX v + 0 — the code counterpart (honour frame's own site -> re-reference is a no-op) is EXACTLY gold. Faithful patch = gold.
 7. atk_7_partialdomain.lean -- partial domain: itrsToObserved returns fwdX for comp=2 (wrong). EXIT=1 REJECTED (fwdX != fwdZ).

POSITIVE CONTROL: pos_control.lean (byte-identical to frozen Solution.lean) verifies EXIT=0.
PREPATCH REPRODUCED: yes (atk_2 reproduces the recorded Solution_prepatch.lean force-centre bug; G-DIFF pass in meta.json).

MANDATORY RESOLVE RUN (protocol step 2): for BOTH verifying wrong-impls (atk_4, atk_6) the faithful refined patch IS the gold patch (they are provably-equal echoes on the tested path). Materialized to faithful_patch_gold.diff and EXECUTED through the official harness:
  cmd: run_resolve('astropy__astropy-13398', <gold patch>, timeout=1800, retries=1)
  result: RESOLVED=True, COMPLETED=True, note='resolved'; FAIL_TO_PASS 4/4 success (test_itrs_topo_to_altaz_with_refraction, test_itrs_topo_to_hadec_with_refraction, test_cirs_itrs_topo, test_itrs_straight_overhead), PASS_TO_PASS 68/68 success, 0 failures.
Since every verifying wrong-impl's materialized faithful patch RESOLVES, the spec is NOT broken.

REFINEMENT.MD AUDIT (A-legs, model<->patch correspondence): all legs are R / A-consumed / I; NO kind-3, NO A-reference deep model (refinement.md §D confirmed). A-consumed legs (fwd*/bwd* orth_*, prot*/protInv* prot_orth_*, offset* same_site_*) are all UNCHANGED callees at their weakest sufficient contract, each executably validated by axiom_check.py and G-AX (meta.json G-AX status=pass: orthogonality over 7056 configs x 68 vectors, precession over 10 configs, same-site no-op + force-centre-detectably-nonzero over 5 topocentric sites). The genuinely-changed data (direct orthogonal-rotation pair; site-honouring re-reference) are pinned DIRECTLY by offset-free equality postconditions, not hidden behind axioms about the changed op. Correspondence holds.

VERDICT: SOUND. >=5 distinct discriminating wrong-impls (partial-domain, boundary/force-centre, control-flow swap, wrong-callee, divergence) are all rejected by verification; the only verifying wrong-impls are provably-equal echoes whose materialized faithful patch was executed through the harness and RESOLVED. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_diverge.lean`, `atk_2_forcecentre.lean`, `atk_3_swapcomp.lean`, `atk_5_wrongcallee.lean`, `atk_7_partialdomain.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4_roundtrip_echo.lean`, `atk_6_dropoffset.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying wrong-impl has a faithful refined patch that fails to resolve. The two attacks that verify (atk_4, atk_6) are echo-shaped: they compute values PROVABLY EQUAL to the gold-modeled output on the tested path, so their faithful refined patch IS the gold patch, which resolves (executed run_resolve: RESOLVED=True, 4/4 FAIL_TO_PASS + 68/68 PASS_TO_PASS).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_diverge.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_forcecentre.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swapcomp.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_roundtrip_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_wrongcallee.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dropoffset.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_partialdomain.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The constant orthogonal orientation matrix applied to a three-component
   position, returned componentwise (`fwdX`/`fwdY`/`fwdZ` are the three rows of
   `M · v`). `M` is built by the unchanged rotation-matrix machinery and applied
   by the unchanged Cartesian transform; the action is left uninterpreted — the
   only property the round-trip proof needs is that its transpose-action inverts
   it (the `orth_*` facts below). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom fwdX : Int → Int → Int → Int
axiom fwdY : Int → Int → Int → Int
axiom fwdZ : Int → Int → Int → Int

/- The TRANSPOSE of the same orientation matrix applied to a position
   (`M^T · v`), componentwise — the inverse rotation. Unchanged callee. -/
axiom bwdX : Int → Int → Int → Int
axiom bwdY : Int → Int → Int → Int
axiom bwdZ : Int → Int → Int → Int

/- The single fact about the unchanged orthogonal orientation matrix the proof
   consumes: the transpose-action applied to the forward-action of any position
   returns that position componentwise (the transpose of an orthogonal matrix is
   its inverse). The matrix is otherwise uninterpreted. -/
axiom orth_x : ∀ x y z : Int, bwdX (fwdX x y z) (fwdY x y z) (fwdZ x y z) = x
axiom orth_y : ∀ x y z : Int, bwdY (fwdX x y z) (fwdY x y z) (fwdZ x y z) = y
axiom orth_z : ∀ x y z : Int, bwdZ (fwdX x y z) (fwdY x y z) (fwdZ x y z) = z

/- A second constant orthogonal rotation `P` (relating an Earth-rotating
   orientation to an intermediate Earth-equatorial one) applied to a position,
   componentwise (`P · v`). A distinct unchanged callee (the precession-nutation
   orientation matrix and the Cartesian transform). Provenance + soundness:
   mapping.md / axiom_check.py. -/
axiom protX : Int → Int → Int → Int
axiom protY : Int → Int → Int → Int
axiom protZ : Int → Int → Int → Int

/- The TRANSPOSE of the rotation `P` applied to a position (`P^T · v`),
   componentwise — the inverse rotation. Unchanged callee. -/
axiom protInvX : Int → Int → Int → Int
axiom protInvY : Int → Int → Int → Int
axiom protInvZ : Int → Int → Int → Int

/- The single fact about the second unchanged orthogonal rotation `P` the proof
   consumes: its transpose-action inverts its forward-action componentwise. -/
axiom prot_orth_x : ∀ x y z : Int, protInvX (protX x y z) (protY x y z) (protZ x y z) = x
axiom prot_orth_y : ∀ x y z : Int, protInvY (protX x y z) (protY x y z) (protZ x y z) = y
axiom prot_orth_z : ∀ x y z : Int, protInvZ (protX x y z) (protY x y z) (protZ x y z) = z

/- The viewpoint-dependent directional offset the transform carries when a
   near-Earth position whose frame is anchored at site `L = (lx, ly, lz)` is
   referred to a frame anchored at site `T = (tx, ty, tz)`, along the route that
   ties the position to the Solar-System barycentre — the geocentric-versus-
   topocentric difference, componentwise. An unchanged callee (the re-referencing
   transform between two same-kind frames); otherwise uninterpreted. Provenance +
   soundness: mapping.md / axiom_check.py. -/
axiom offsetX : Int → Int → Int → Int → Int → Int → Int
axiom offsetY : Int → Int → Int → Int → Int → Int → Int
axiom offsetZ : Int → Int → Int → Int → Int → Int → Int

/- The single fact about the unchanged re-referencing transform the proof
   consumes: referring a position whose frame is anchored at a site to a frame
   anchored at the SAME site introduces no offset (it is a no-op). The weakest
   fact sufficient for the agreement proof; the offset is otherwise
   uninterpreted. -/
axiom same_site_x : ∀ lx ly lz : Int, offsetX lx ly lz lx ly lz = 0
axiom same_site_y : ∀ lx ly lz : Int, offsetY lx ly lz lx ly lz = 0
axiom same_site_z : ∀ lx ly lz : Int, offsetZ lx ly lz lx ly lz = 0
-- axioms-end

-- pure-start
-- (no module-level pure helpers required)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Forward conversion of a three-component position from an Earth-rotating
   orientation to an observer-centred orientation. The desired behavior: the
   selected output component is the constant orthogonal orientation matrix
   applied DIRECTLY to the given position (`comp` selects which of the three
   output components to return). Pinning each component to the forward action of
   the input itself — with no intermediate viewpoint shift — forces the direct
   orthogonal rotation. -/
noncomputable section
method itrsToObserved (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = fwdX vx vy vz
  ensures comp = 1 → out = fwdY vx vy vz
  ensures comp = 2 → out = fwdZ vx vy vz
  do
    -- impl-start
    if comp = 0 then
      return fwdX vx vy vz
    else if comp = 1 then
      return fwdY vx vy vz
    else
      return fwdZ vx vy vz
    -- impl-end
end

prove_correct itrsToObserved by
  loom_solve

/- Backward conversion of a three-component position from an observer-centred
   orientation to an Earth-rotating orientation. The desired behavior: the
   selected output component is the TRANSPOSE action (inverse rotation) applied
   DIRECTLY to the observer-centred input. -/
noncomputable section
method observedToItrs (comp : Int) (ox : Int) (oy : Int) (oz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = bwdX ox oy oz
  ensures comp = 1 → out = bwdY ox oy oz
  ensures comp = 2 → out = bwdZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedToItrs by
  loom_solve

/- The round-trip identity for the direct conversion pair. The desired behavior:
   converting an Earth-rotating position to the observer-centred orientation and
   back returns the original position exactly (componentwise). This is the exact
   geometric round trip the issue demands of the direct pair; it holds precisely
   because the orientation matrix is orthogonal, so its transpose undoes it. A
   conversion that instead reaches the observer-centred orientation by an
   INDIRECT route — introducing a viewpoint-dependent directional shift rather
   than applying the orthogonal matrix directly — does NOT round-trip exactly. -/
noncomputable section
method observedRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The observer-centred components are the forward action of the input; the
    -- transpose-action then inverts it, recovering the original position.
    let ox := fwdX vx vy vz
    let oy := fwdY vx vy vz
    let oz := fwdZ vx vy vz
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedRoundtrip by
  loom_solve <;>
    simp_all [orth_x, orth_y, orth_z]

/- Forward conversion of a three-component position from an Earth-equatorial
   orientation to an Earth-rotating orientation, tied to an observing site `L`.
   The desired behavior: the position is referred to the output frame anchored
   at the SAME site `L = (lx, ly, lz)` it already carries, so referring to it
   introduces no viewpoint offset and the selected component is the rotation `P`
   applied to the given position with NO spurious viewpoint shift. Pinning each
   component to the bare rotation of the input forces the transform to honour the
   frame's own site rather than referring to one single constant site. -/
noncomputable section
method equToRot (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protX vx vy vz
  ensures comp = 1 → out = protY vx vy vz
  ensures comp = 2 → out = protZ vx vy vz
  do
    -- impl-start
    -- Rotate, then carry the offset for referring the result to the output
    -- frame's own site L. That is the same site the position is anchored at, so
    -- the offset is zero (no-op) and the result is the pure rotation.
    if comp = 0 then
      return protX vx vy vz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protY vx vy vz + offsetY lx ly lz lx ly lz
    else
      return protZ vx vy vz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct equToRot by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- Backward conversion of a three-component position from an Earth-rotating
   orientation to an Earth-equatorial orientation, carrying the observing site
   `L`. The desired behavior: apply the TRANSPOSE of `P` (the inverse rotation)
   to the input and carry the input frame's own site `L` onto the result, so
   referring to the output frame's own (same) site is a no-op; the selected
   component is the inverse rotation of the input with NO spurious viewpoint
   shift. -/
noncomputable section
method rotToEqu (comp : Int) (ox : Int) (oy : Int) (oz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protInvX ox oy oz
  ensures comp = 1 → out = protInvY ox oy oz
  ensures comp = 2 → out = protInvZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct rotToEqu by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- The topocentric round-trip identity for the site-honouring conversion pair.
   The desired behavior: converting an Earth-equatorial position to the
   Earth-rotating orientation at site `L` and back returns the original position
   exactly (componentwise). It holds only because both legs honour the site `L`
   (so neither inserts a viewpoint offset) and `P` is orthogonal. A conversion
   that refers the position to one single constant site (the centre of the Earth, the
   origin) rather than the frame's own site introduces a viewpoint-dependent
   offset whenever the site is not the centre, so it does NOT round-trip
   exactly. -/
noncomputable section
method equRotRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The Earth-rotating components are the rotation of the input (the
    -- site-offset of each leg is a no-op at the shared site L); the transpose
    -- rotation then inverts it, recovering the original position.
    let ox := protX vx vy vz
    let oy := protY vx vy vz
    let oz := protZ vx vy vz
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct equRotRoundtrip by
  loom_solve <;>
    simp_all [prot_orth_x, prot_orth_y, prot_orth_z, same_site_x, same_site_y, same_site_z]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight-equality. Every 'real' method postcondition pins output to a UNIQUE axiom expression (out = fwdX/protX vx vy vz; out = vx). So ANY verifying impl is observationally gold-identical on the tested path -> verify => correct.

ATTACKS (all same_spec=True vs frozen Solution.lean, verified with markers.same_spec; verify cmd: `bash scripts/lean_verify.sh <file>`, exit 0=verifies, 1=error/spec-sensed):
 1. atk_1_diverge.lean  -- CLEAN non-terminating loop (while i>0; i:=i+1; decreasing i) before correct returns in itrsToObserved. EXIT=1 (goal `Nat.zero < Nat.zero` unprovable). REJECTED: total-correctness semantics (loom.semantics.termination "total") correctly refuses divergence. NOTE: this re-encodes the PRIOR pass's INCONCLUSIVE attack, which used invalid Velvet syntax (`while true do pass`) and failed to CLASSIFY (not a real break). Cleanly re-encoded, divergence is soundly rejected.
 2. atk_2_forcecentre.lean -- prepatch bug: equToRot uses offset*(L, 0 0 0) (force geocentre) instead of offset*(L,L). EXIT=1. REJECTED (same_site_* gives only offset*(L,L)=0; offset*(L,0) uninterpreted != 0). Mirrors Solution_prepatch.lean / G-DIFF.
 3. atk_3_swapcomp.lean -- control-flow: itrsToObserved returns fwdY for comp=0, fwdX for comp=1. EXIT=1 REJECTED (fwdX != fwdY).
 4. atk_4_roundtrip_echo.lean -- ungrounded-oracle echo: observedRoundtrip returns vx/vy/vz directly. EXIT=0 VERIFIES. BENIGN: observedRoundtrip is a MODELED COMPOSITE (no distinct code region; the test's chained transform_to). Returning v = bwd(fwd(v)) by orth_* -> observationally identical to gold. Faithful patch = gold.
 5. atk_5_wrongcallee.lean -- observedToItrs returns fwd* (forward) instead of bwd* (transpose). EXIT=1 REJECTED (fwdZ != bwdZ).
 6. atk_6_dropoffset.lean -- equToRot drops the '+ offset* lx ly lz lx ly lz' term (bare rotation). EXIT=0 VERIFIES. BENIGN: same_site_* proves offset*(L,L)=0, so protX v ≡ protX v + 0 — the code counterpart (honour frame's own site -> re-reference is a no-op) is EXACTLY gold. Faithful patch = gold.
 7. atk_7_partialdomain.lean -- partial domain: itrsToObserved returns fwdX for comp=2 (wrong). EXIT=1 REJECTED (fwdX != fwdZ).

POSITIVE CONTROL: pos_control.lean (byte-identical to frozen Solution.lean) verifies EXIT=0.
PREPATCH REPRODUCED: yes (atk_2 reproduces the recorded Solution_prepatch.lean force-centre bug; G-DIFF pass in meta.json).

MANDATORY RESOLVE RUN (protocol step 2): for BOTH verifying wrong-impls (atk_4, atk_6) the faithful refined patch IS the gold patch (they are provably-equal echoes on the tested path). Materialized to faithful_patch_gold.diff and EXECUTED through the official harness:
  cmd: run_resolve('astropy__astropy-13398', <gold patch>, timeout=1800, retries=1)
  result: RESOLVED=True, COMPLETED=True, note='resolved'; FAIL_TO_PASS 4/4 success (test_itrs_topo_to_altaz_with_refraction, test_itrs_topo_to_hadec_with_refraction, test_cirs_itrs_topo, test_itrs_straight_overhead), PASS_TO_PASS 68/68 success, 0 failures.
Since every verifying wrong-impl's materialized faithful patch RESOLVES, the spec is NOT broken.

REFINEMENT.MD AUDIT (A-legs, model<->patch correspondence): all legs are R / A-consumed / I; NO kind-3, NO A-reference deep model (refinement.md §D confirmed). A-consumed legs (fwd*/bwd* orth_*, prot*/protInv* prot_orth_*, offset* same_site_*) are all UNCHANGED callees at their weakest sufficient contract, each executably validated by axiom_check.py and G-AX (meta.json G-AX status=pass: orthogonality over 7056 configs x 68 vectors, precession over 10 configs, same-site no-op + force-centre-detectably-nonzero over 5 topocentric sites). The genuinely-changed data (direct orthogonal-rotation pair; site-honouring re-reference) are pinned DIRECTLY by offset-free equality postconditions, not hidden behind axioms about the changed op. Correspondence holds.

VERDICT: SOUND. >=5 distinct discriminating wrong-impls (partial-domain, boundary/force-centre, control-flow swap, wrong-callee, divergence) are all rejected by verification; the only verifying wrong-impls are provably-equal echoes whose materialized faithful patch was executed through the harness and RESOLVED. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack over the velvet bundle for astropy__astropy-13398.

Mechanical checks: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; only impl/proof differ). Solution.lean verifies clean (lean_verify.sh exit 0). Recorded gates: G-DIFF pass (prepatch fails frozen postconditions -> spec discriminates), G-RESOLVE pass, G-AX pass, G-LEAK pass, G-HYGIENE pass.

Modeling boundary: components abstracted real-float -> exact Int; unchanged callees encoded as uninterpreted axioms pinned by weakest sufficient facts: orth_* (M^T(M v)=v), prot_orth_* (P^T(P v)=v), same_site_* (offset(L,L)=0). All three validated by axiom_check.py/G-AX against the REAL callees (orth over 7056 (lon,lat) x 68 vectors on real itrs_to_altaz_mat/itrs_to_hadec_mat; prot over real cirs_to_itrs_mat/tete_to_itrs_mat; same-site residual ~0 m and force-centre offset detectably nonzero on the real gold-patched CIRS<->ITRS conversions).

Scope match: the modeled 'direct M.v offset-free' postconditions and exact round-trip identities correspond exactly to the F2P tested path. test_itrs_topo_to_{altaz,hadec}_with_refraction 'Through ITRS / No Refraction' blocks use itrs_frame and altaz_frame1 sharing location=loc, same obstime, pressure=0, so the real itrs_to_observed early CIRS-reroute conditional is a no-op and refraction is skipped -> the real conversion reduces to exactly crepr.transform(M); the test asserts EXACT identity assert_allclose(itrs11.x, itrs.x). test_cirs_itrs_topo exercises the same-site topocentric round trip. The refraction/off-site cases are deliberately and correctly excluded from the modeled structural guarantee (refinement.md 'Refraction vs. identity'). Offset carried additively-after-rotation is sound because P is linear.

Drift search: no input in the modeled (same-site/same-time/no-pressure) domain makes a modeled postcondition disagree with the real callee; every axiom is a genuine (weakest) property of the real callee. Total-correctness semantics is faithful (straight-line matrix applies terminate). No diverging input found.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: judged the consumer-visible spec view = projected Solution.lean (impl regions + prove_correct bodies elided; confirmed via markers.spec_view). mapping.md/refinement.md cite patch.diff/base_commit/pre-patch by design but are auditor-only artifacts, not solver-visible; G-LEAK screens only solution_src. same_spec(Solution.lean, Solution_prepatch.lean)=True (frozen spec region byte-identical). Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so no deferral — genuine call.

Mechanical G-LEAK: pass (spec view clean, 0 hard failures). Independently confirmed: no diff markers, no gold-patch line reproduced, no patched file path/module (itrs_observed_transforms, intermediate_rotation_transforms, itrs.py), no spec-view identifier embedding a patched repo symbol (itrs_to_observed, cirs_to_itrs, tete_to_itrs, EARTH_CENTER, location) — the model uses abstract carriers fwdX/bwdX/protX/offsetX/itrsToObserved/equToRot; no fix/bug/prepatch narration in comments.

Semantic: the spec's discriminating content is (a) a DIRECT orthogonal-rotation forward/backward pair with exact round-trip identity, and (b) equatorial<->rotating conversions honouring the frame's OWN site vs 'one single constant site (the centre of the Earth)'. Both are fully public in problem_statement, which embeds the ENTIRE draft implementation (itrs_to_observed_mat, rotation matrices, forward/backward transform_to) and the central geocentric-vs-topocentric / 'ITRS->ITRS references coordinates to the SSB rather than the rotating ITRF' theme. Comment phrases ('Solar-System barycentre', 'geocentric-versus-topocentric', 'direct' vs 'indirect route', centre of Earth) all trace to public problem-statement wording. Comments describe desired behavior abstractly (necessary for any spec), not the specific edit or pre-patch defect. The spec view discloses nothing beyond the public problem statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
