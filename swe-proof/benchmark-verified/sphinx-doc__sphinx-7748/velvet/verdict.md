# P2 adversarial audit — sphinx-doc__sphinx-7748

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,10 +108,7 @@
       else
         if l.isSig then
           out := out ++ [l.sig]
-          if l.cont then
-            i := i + 1
-          else
-            stopped := true
+          stopped := true
         else
           i := i + 1
     return out
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,28 +93,7 @@
   ensures out = collectSigs lines
   do
     -- impl-start
-    let mut out : List Sig := []
-    let mut i := 0
-    let mut stopped := false
-    while i < lines.length ∧ stopped = false
-      invariant 0 ≤ i ∧ i ≤ lines.length
-      invariant out ++ (if stopped then [] else collectSigs (lines.drop i)) = collectSigs lines
-      done_with stopped = true ∨ i = lines.length
-      decreasing (lines.length - i) + (if stopped then 0 else 1)
-    do
-      let l := lines[i]!
-      if l.blank then
-        stopped := true
-      else
-        if l.isSig then
-          out := out ++ [l.sig]
-          if l.cont then
-            i := i + 1
-          else
-            stopped := true
-        else
-          i := i + 1
-    return out
+    return []
     -- impl-end
 
 prove_correct collectSignatures by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,10 +108,7 @@
       else
         if l.isSig then
           out := out ++ [l.sig]
-          if l.cont then
-            i := i + 1
-          else
-            stopped := true
+          i := i + 1
         else
           i := i + 1
     return out
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
     do
       let l := lines[i]!
       if l.blank then
-        stopped := true
+        i := i + 1
       else
         if l.isSig then
           out := out ++ [l.sig]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,9 @@
         if l.isSig then
           out := out ++ [l.sig]
           if l.cont then
+            stopped := true
+          else
             i := i + 1
-          else
-            stopped := true
         else
           i := i + 1
     return out
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,28 +93,7 @@
   ensures out = collectSigs lines
   do
     -- impl-start
-    let mut out : List Sig := []
-    let mut i := 0
-    let mut stopped := false
-    while i < lines.length ∧ stopped = false
-      invariant 0 ≤ i ∧ i ≤ lines.length
-      invariant out ++ (if stopped then [] else collectSigs (lines.drop i)) = collectSigs lines
-      done_with stopped = true ∨ i = lines.length
-      decreasing (lines.length - i) + (if stopped then 0 else 1)
-    do
-      let l := lines[i]!
-      if l.blank then
-        stopped := true
-      else
-        if l.isSig then
-          out := out ++ [l.sig]
-          if l.cont then
-            i := i + 1
-          else
-            stopped := true
-        else
-          i := i + 1
-    return out
+    return collectSigs lines
     -- impl-end
 
 prove_correct collectSignatures by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
           else
             stopped := true
         else
-          i := i + 1
+          stopped := true
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the per-line classification is supplied as input data —
--  see the `LineInfo` carrier below — and validated against the real callees by
--  the executable soundness check; the collection logic is modeled deeply.)
-- axioms-end

-- pure-start
/- The payload extracted from one signature-bearing line: the argument text and
   the return-annotation text. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Inhabited, Repr

/- The decision data about a single docstring line, as observed by a standard
   signature recognizer:
   * `blank`  — the line is empty (a paragraph break);
   * `isSig`  — the line, with any trailing continuation marker removed, parses
                as a signature whose name is one of the documented object's
                accepted names;
   * `cont`   — the line carries a trailing continuation marker, indicating a
                further signature follows;
   * `sig`    — the parsed `(args, retann)` payload (meaningful only when `isSig`).
   The recognizer itself is unchanged and is supplied as this input carrier. -/
structure LineInfo where
  blank : Bool
  isSig : Bool
  cont : Bool
  sig : Sig
deriving Inhabited

/- The signatures collected from one docstring, in reading order. Scanning the
   lines front to back: a blank line ends the scan; a signature line is
   collected, and collection carries on past it only when that line bears a
   trailing join marker (otherwise that signature is the last one); a line that
   is neither blank nor a signature is skipped. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
def collectSigs : List LineInfo → List Sig
  | [] => []
  | l :: ls =>
    if l.blank then []
    else if l.isSig then
      (if l.cont then l.sig :: collectSigs ls else [l.sig])
    else collectSigs ls

@[grind] lemma collectSigs_nil : collectSigs [] = [] := rfl
@[grind] lemma collectSigs_cons (l : LineInfo) (ls : List LineInfo) :
    collectSigs (l :: ls) =
      (if l.blank then []
       else if l.isSig then (if l.cont then l.sig :: collectSigs ls else [l.sig])
       else collectSigs ls) := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (lines : List LineInfo) (i : Nat) (hi : i < lines.length) :
    lines.drop i = lines[i]! :: lines.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The fold step: `collectSigs (lines.drop i)` peels the classification of line
   `i`. This is the single per-line goal the loop body leaves. -/
@[grind] lemma collectSigs_drop_step (lines : List LineInfo) (i : Nat)
    (hi : i < lines.length) :
    collectSigs (lines.drop i) =
      (if (lines[i]!).blank then []
       else if (lines[i]!).isSig then
              (if (lines[i]!).cont then (lines[i]!).sig :: collectSigs (lines.drop (i + 1))
               else [(lines[i]!).sig])
            else collectSigs (lines.drop (i + 1))) := by
  rw [drop_cons_eq lines i hi, collectSigs_cons]

/- Past the end there is nothing left to collect. -/
@[grind] lemma collectSigs_drop_ge (lines : List LineInfo) (i : Nat)
    (h : lines.length ≤ i) : collectSigs (lines.drop i) = [] := by
  rw [List.drop_eq_nil_of_le h]; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method collectSignatures (lines : List LineInfo) return (out : List Sig)
  ensures out = collectSigs lines
  do
    -- impl-start
    let mut out : List Sig := []
    let mut i := 0
    let mut stopped := false
    while i < lines.length ∧ stopped = false
      invariant 0 ≤ i ∧ i ≤ lines.length
      invariant out ++ (if stopped then [] else collectSigs (lines.drop i)) = collectSigs lines
      done_with stopped = true ∨ i = lines.length
      decreasing (lines.length - i) + (if stopped then 0 else 1)
    do
      let l := lines[i]!
      if l.blank then
        stopped := true
      else
        if l.isSig then
          out := out ++ [l.sig]
          if l.cont then
            i := i + 1
          else
            stopped := true
        else
          i := i + 1
    return out
    -- impl-end

prove_correct collectSignatures by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity, plan §4), A-legs focus. Bundle sphinx-doc__sphinx-7748/velvet.

SPEC SHAPE: method collectSignatures (lines : List LineInfo) ensures out = collectSigs lines. This is an EXACT functional equation against a total, deterministic deep model, under loom.semantics.termination=total, with NO consumed axioms and NO preconditions. Consequence: every verifying impl computes exactly collectSigs lines and is behaviourally identical to every other verifying impl and to the gold's claimed model. So the A-leg audit reduces to (a) can a behaviourally-wrong impl verify (soundness/vacuity), and (b) is the faithful patch of a verifying impl resolving.

SAME-SPEC: all 7 attack files return same_spec(...)=True vs Solution.lean (swebench_unified.markers.same_spec, backend velvet) — only the impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
  pos_control.lean (gold impl) -> EXIT 0 VERIFIES (positive control OK).
  atk_1.lean prepatch bug (stop after first sig, ignore l.cont) -> EXIT 1 REJECTED (prepatch reproduced).
  atk_2.lean partial-domain (return []) -> EXIT 1 REJECTED.
  atk_3.lean control-flow-effect (non-cont match keeps scanning, never stops) -> EXIT 1 REJECTED.
  atk_4.lean control-flow-effect (blank line skipped instead of stop) -> EXIT 1 REJECTED.
  atk_5.lean boundary (cont/non-cont branches swapped) -> EXIT 1 REJECTED.
  atk_6.lean ungrounded-oracle echo (return collectSigs lines) -> EXIT 0 VERIFIES (correct; the ONLY verifying attack).
  atk_7.lean boundary/partial (non-sig line stops scan instead of skip) -> EXIT 1 REJECTED.
So 6 distinct wrong-shaped impls all correctly REJECTED; only the correct echo verifies. No vacuous/behaviourally-wrong impl slipped through the frozen postcondition.

RESOLVE (protocol step 2) — for the only verifying attack (atk_6): its faithful refined patch, per the refinement.md map (out = collectSigs lines refined to the patched _find_signature + _signatures + format_signature join), IS the gold patch. faithful_atk_6.diff is BYTE-IDENTICAL to benchmark-verified/.../patch.diff (sha1 a9f2994be2a2a057a3f62e7df800a8794ad2575d, verified). I MATERIALIZED it and RAN it through the official harness (swebench_unified.harness.run_resolve / run_evaluation, run_id sbu-auditeq-7748-atk6-loop5).

Executed result from the harness instance log: resolved: True; FAIL_TO_PASS success = [test_autoclass_content_and_docstring_signature_init, test_autoclass_content_and_docstring_signature_both] (0 failures); PASS_TO_PASS 12/12 success, 0 failures. => the verifying wrong impl's faithful patch DOES resolve. (Earlier attempts 1-4 and standalone r2/r3/r4 returned COMPLETED=False due to Docker daemon read-timeouts in build_container — pure contention, heavy-280, the documented 'one backend at a time' hazard; NOT resolve verdicts. Also corroborated: meta.json G-RESOLVE=pass 'resolved', and verdict.md records a prior audit pass that executed run_resolve on this patch -> RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1.)

### REFINEMENT.MD LEG AUDIT (A-legs / deep-model refs):
A1 (param List LineInfo <-> doclines List[str]) = R, bijection stated (mapping §2). Sound. A2 (LineInfo fields blank/cont/isSig/sig <-> unchanged callees not-line / endswith('\\') / py_ext_sig_re.match+valid_names / match.group(4),(5)) = A-REFERENCE. This is the ONLY kind-A leg. It abstracts UNCHANGED, patch-independent callees, supplied as the input carrier; validated by G-AX axiom_check.py which recomputes each field from the REAL py_ext_sig_re/str methods on a boundary corpus + 40000 fuzz in BOTH documenter configs (meta.json G-AX=pass). Correspondence to the real callees holds; it does NOT smuggle the changed collection logic into the input.

A3 (the while loop + collectSigs <-> the changed multi-signature scan control flow) = I, modeled DEEPLY (front-recursive collectSigs, verified forward-fold), not axiom-hidden. Correct — the changed op is precisely what the frozen postcondition pins. A4 (out : List Sig <-> result + _signatures rendered + format_signature newline join) = R render bijection; checked end-to-end by G-CONF. A5 (outer for i,doclines docstring loop) = R identity, unchanged pre/post, omitted. Correct. No kind-3 (inexpressible-changed-op) legs; the changed operation is modeled deeply (A3), the only A-reference (A2) covers unchanged callees. This matches refinement.md §B/§C.

G-CONF (meta.json pass): conformance_check.py derives LineInfo from real callees, runs collectSigs + render, diffs vs the REAL PATCHED _find_signature/format_signature on boundary + 1e5 fuzz (seed 7748), 0 disagreements — establishing the end-to-end model<->patched-function equivalence that the A-reference scope note (mapping §3) correctly assigns to G-CONF, not G-AX.

CONCLUSION: The frozen spec is a tight exact-equality postcondition; 6 distinct behaviourally-wrong impls are all rejected; the sole verifying wrong impl (the correct echo) has a faithful patch byte-identical to the gold, and that patch was MATERIALIZED and EXECUTED through the official harness with resolved: True. No verify⇏correct counterexample exists. A-reference (A2) is faithful to the unchanged callees (G-AX pass); no kind-3 legs; model<->patch correspondence holds (G-CONF pass). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the per-line classification is supplied as input data —
--  see the `LineInfo` carrier below — and validated against the real callees by
--  the executable soundness check; the collection logic is modeled deeply.)
-- axioms-end

-- pure-start
/- The payload extracted from one signature-bearing line: the argument text and
   the return-annotation text. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Inhabited, Repr

/- The decision data about a single docstring line, as observed by a standard
   signature recognizer:
   * `blank`  — the line is empty (a paragraph break);
   * `isSig`  — the line, with any trailing continuation marker removed, parses
                as a signature whose name is one of the documented object's
                accepted names;
   * `cont`   — the line carries a trailing continuation marker, indicating a
                further signature follows;
   * `sig`    — the parsed `(args, retann)` payload (meaningful only when `isSig`).
   The recognizer itself is unchanged and is supplied as this input carrier. -/
structure LineInfo where
  blank : Bool
  isSig : Bool
  cont : Bool
  sig : Sig
deriving Inhabited

/- The signatures collected from one docstring, in reading order. Scanning the
   lines front to back: a blank line ends the scan; a signature line is
   collected, and collection carries on past it only when that line bears a
   trailing join marker (otherwise that signature is the last one); a line that
   is neither blank nor a signature is skipped. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
def collectSigs : List LineInfo → List Sig
  | [] => []
  | l :: ls =>
    if l.blank then []
    else if l.isSig then
      (if l.cont then l.sig :: collectSigs ls else [l.sig])
    else collectSigs ls

@[grind] lemma collectSigs_nil : collectSigs [] = [] := rfl
@[grind] lemma collectSigs_cons (l : LineInfo) (ls : List LineInfo) :
    collectSigs (l :: ls) =
      (if l.blank then []
       else if l.isSig then (if l.cont then l.sig :: collectSigs ls else [l.sig])
       else collectSigs ls) := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (lines : List LineInfo) (i : Nat) (hi : i < lines.length) :
    lines.drop i = lines[i]! :: lines.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The fold step: `collectSigs (lines.drop i)` peels the classification of line
   `i`. This is the single per-line goal the loop body leaves. -/
@[grind] lemma collectSigs_drop_step (lines : List LineInfo) (i : Nat)
    (hi : i < lines.length) :
    collectSigs (lines.drop i) =
      (if (lines[i]!).blank then []
       else if (lines[i]!).isSig then
              (if (lines[i]!).cont then (lines[i]!).sig :: collectSigs (lines.drop (i + 1))
               else [(lines[i]!).sig])
            else collectSigs (lines.drop (i + 1))) := by
  rw [drop_cons_eq lines i hi, collectSigs_cons]

/- Past the end there is nothing left to collect. -/
@[grind] lemma collectSigs_drop_ge (lines : List LineInfo) (i : Nat)
    (h : lines.length ≤ i) : collectSigs (lines.drop i) = [] := by
  rw [List.drop_eq_nil_of_le h]; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method collectSignatures (lines : List LineInfo) return (out : List Sig)
  ensures out = collectSigs lines
  do
    -- impl-start
    let mut out : List Sig := []
    let mut i := 0
    let mut stopped := false
    while i < lines.length ∧ stopped = false
      invariant 0 ≤ i ∧ i ≤ lines.length
      invariant out ++ (if stopped then [] else collectSigs (lines.drop i)) = collectSigs lines
      done_with stopped = true ∨ i = lines.length
      decreasing (lines.length - i) + (if stopped then 0 else 1)
    do
      let l := lines[i]!
      if l.blank then
        stopped := true
      else
        if l.isSig then
          out := out ++ [l.sig]
          if l.cont then
            i := i + 1
          else
            stopped := true
        else
          i := i + 1
    return out
    -- impl-end

prove_correct collectSignatures by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity, plan §4), A-legs focus. Bundle sphinx-doc__sphinx-7748/velvet.

SPEC SHAPE: method collectSignatures (lines : List LineInfo) ensures out = collectSigs lines. This is an EXACT functional equation against a total, deterministic deep model, under loom.semantics.termination=total, with NO consumed axioms and NO preconditions. Consequence: every verifying impl computes exactly collectSigs lines and is behaviourally identical to every other verifying impl and to the gold's claimed model. So the A-leg audit reduces to (a) can a behaviourally-wrong impl verify (soundness/vacuity), and (b) is the faithful patch of a verifying impl resolving.

SAME-SPEC: all 7 attack files return same_spec(...)=True vs Solution.lean (swebench_unified.markers.same_spec, backend velvet) — only the impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
  pos_control.lean (gold impl) -> EXIT 0 VERIFIES (positive control OK).
  atk_1.lean prepatch bug (stop after first sig, ignore l.cont) -> EXIT 1 REJECTED (prepatch reproduced).
  atk_2.lean partial-domain (return []) -> EXIT 1 REJECTED.
  atk_3.lean control-flow-effect (non-cont match keeps scanning, never stops) -> EXIT 1 REJECTED.
  atk_4.lean control-flow-effect (blank line skipped instead of stop) -> EXIT 1 REJECTED.
  atk_5.lean boundary (cont/non-cont branches swapped) -> EXIT 1 REJECTED.
  atk_6.lean ungrounded-oracle echo (return collectSigs lines) -> EXIT 0 VERIFIES (correct; the ONLY verifying attack).
  atk_7.lean boundary/partial (non-sig line stops scan instead of skip) -> EXIT 1 REJECTED.
So 6 distinct wrong-shaped impls all correctly REJECTED; only the correct echo verifies. No vacuous/behaviourally-wrong impl slipped through the frozen postcondition.

RESOLVE (protocol step 2) — for the only verifying attack (atk_6): its faithful refined patch, per the refinement.md map (out = collectSigs lines refined to the patched _find_signature + _signatures + format_signature join), IS the gold patch. faithful_atk_6.diff is BYTE-IDENTICAL to benchmark-verified/.../patch.diff (sha1 a9f2994be2a2a057a3f62e7df800a8794ad2575d, verified). I MATERIALIZED it and RAN it through the official harness (swebench_unified.harness.run_resolve / run_evaluation, run_id sbu-auditeq-7748-atk6-loop5).

Executed result from the harness instance log: resolved: True; FAIL_TO_PASS success = [test_autoclass_content_and_docstring_signature_init, test_autoclass_content_and_docstring_signature_both] (0 failures); PASS_TO_PASS 12/12 success, 0 failures. => the verifying wrong impl's faithful patch DOES resolve. (Earlier attempts 1-4 and standalone r2/r3/r4 returned COMPLETED=False due to Docker daemon read-timeouts in build_container — pure contention, heavy-280, the documented 'one backend at a time' hazard; NOT resolve verdicts. Also corroborated: meta.json G-RESOLVE=pass 'resolved', and verdict.md records a prior audit pass that executed run_resolve on this patch -> RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1.)

### REFINEMENT.MD LEG AUDIT (A-legs / deep-model refs):
A1 (param List LineInfo <-> doclines List[str]) = R, bijection stated (mapping §2). Sound. A2 (LineInfo fields blank/cont/isSig/sig <-> unchanged callees not-line / endswith('\\') / py_ext_sig_re.match+valid_names / match.group(4),(5)) = A-REFERENCE. This is the ONLY kind-A leg. It abstracts UNCHANGED, patch-independent callees, supplied as the input carrier; validated by G-AX axiom_check.py which recomputes each field from the REAL py_ext_sig_re/str methods on a boundary corpus + 40000 fuzz in BOTH documenter configs (meta.json G-AX=pass). Correspondence to the real callees holds; it does NOT smuggle the changed collection logic into the input.

A3 (the while loop + collectSigs <-> the changed multi-signature scan control flow) = I, modeled DEEPLY (front-recursive collectSigs, verified forward-fold), not axiom-hidden. Correct — the changed op is precisely what the frozen postcondition pins. A4 (out : List Sig <-> result + _signatures rendered + format_signature newline join) = R render bijection; checked end-to-end by G-CONF. A5 (outer for i,doclines docstring loop) = R identity, unchanged pre/post, omitted. Correct. No kind-3 (inexpressible-changed-op) legs; the changed operation is modeled deeply (A3), the only A-reference (A2) covers unchanged callees. This matches refinement.md §B/§C.

G-CONF (meta.json pass): conformance_check.py derives LineInfo from real callees, runs collectSigs + render, diffs vs the REAL PATCHED _find_signature/format_signature on boundary + 1e5 fuzz (seed 7748), 0 disagreements — establishing the end-to-end model<->patched-function equivalence that the A-reference scope note (mapping §3) correctly assigns to G-CONF, not G-AX.

CONCLUSION: The frozen spec is a tight exact-equality postcondition; 6 distinct behaviourally-wrong impls are all rejected; the sole verifying wrong impl (the correct echo) has a faithful patch byte-identical to the gold, and that patch was MATERIALIZED and EXECUTED through the official harness with resolved: True. No verify⇏correct counterexample exists. A-reference (A2) is faithful to the unchanged callees (G-AX pass); no kind-3 legs; model<->patch correspondence holds (G-CONF pass). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no model↔repo drift) audit of the velvet bundle for sphinx-doc__sphinx-7748.

SPEC REGION INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True — spec region is byte-identical between twins; the only difference is inside the elided impl region (prepatch sets `stopped := true` unconditionally after the first match; postpatch honors `l.cont`). The frozen postcondition `ensures out = collectSigs lines` is unchanged.

LEAN VERIFICATION: scripts/lean_verify.sh on Solution.lean exits 0 (verifies under total-correctness + demonic-choice semantics, explicit decreasing measure, no vacuity). No banned tokens.

MODEL vs REAL CALLEE (the faithfulness question): the modeled function is collectSigs (deep model) over a LineInfo carrier whose per-line classification is the mapping.md §3 bridge built from the real unchanged py_ext_sig_re + str.endswith/rstrip + valid_names membership. I transcribed the gold-patched DocstringSignatureMixin._find_signature EXACTLY from patch.diff (continue-on-no-match, continue-on-name-mismatch, multiline→continue else break, blank→break, result/_signatures split, format render '(args) -> retann') and ran a differential test against the model's shadow_render.

  * NOTE: is a LATER commit whose _find_signature `break`s on no-match — NOT the gold patch; my first test using it produced spurious disagreements. I discarded it and re-ran against the byte-exact patch.diff transcription.
  * Randomized fuzz: 120,000 inputs (k=0..7 lines, 22-element line pool incl. continuation markers, indented lines, name mismatches, return-annotation variants), across both valid_names configs (plain-function and class-with-mro). 0 disagreements.
  * Hand-crafted edge corpus (empty, bare backslash, whitespace-only, trailing-unterminated multiline chain, blank-terminated multiline, name-mismatch interleaving, etc.): 0 mismatches.

The model neither over- nor under-collects relative to the real patched callee on any tested input. The A-reference (LineInfo bridge) is patch-independent and validated by axiom_check.py against the real regex. The spec is not too strong and does not drift from repo behavior. No diverging input exists.

VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, G-LEAK=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified the disposition rather than rubber-stamping. (1) Spec regions of Solution.lean and Solution_prepatch.lean are byte-identical (diff empty) — single frozen spec view. (2) Lexical scan of the spec view: 0 literal repo/gold tokens (endswith, backslash, \, multiline, py_ext_sig_re, _signatures, objpath, format_signature, rstrip, __init__, __mro__). (3) problem_statement token scan for the discriminator (continuation/backslash/\/trailing/marker/multiline/blank/stop/join) = 0 hits, confirming facet (a) 'collect all overloaded signatures' is public while facet (b) the trailing-continuation-marker gating is gold/test-only. The spec discloses (b) only ABSTRACTLY via LineInfo.cont and the collectSigs 'carries on only when the line bears a trailing join marker' prose — no endswith/literal backslash/repo symbol. (4) Unavoidability re-derived independently: G-DIFF=pass shows the prepatch (ignore cont) fails verification exactly on the l.cont clause, so the continuation gating IS the discriminating content of the change; G-CONF=pass diffs the shadow against the real patched _find_signature on >1e5 inputs, so a marker-silent PS-only spec would be spec-too-weak. Hence faithful-and-non-leaking is impossible; the abstract disclosure is the minimal required. (5) No NEW leaking line beyond the dispositioned continuation-marker facet, and the disposition is not broken (leakage-relevant core gates G-VERIFY/G-DIFF/G-CONF/G-AX/G-RESOLVE/G-MUT/G-PANEL-2 all pass; no PS-only derivation of the marker gating exists). The G-EQ/G-PANEL-1 fails are the equivalence/echo auditor's concern, not the leakage property, and the unavoidability argument does not depend on them. Recording NO-LEAKAGE (=pass) per the G-PANEL-3 relaxed-leakage convention.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.