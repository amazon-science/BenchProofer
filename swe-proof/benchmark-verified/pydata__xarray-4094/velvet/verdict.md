# P2 adversarial audit — pydata__xarray-4094

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No TERMINATING same-spec wrong impl verifies. The only same-spec verifying wrong impls (atk_nonterm, atk_nonterm2) verify solely via non-termination vacuity of loom.semantics.termination "partial"; their faithful refined patches do NOT resolve but with completed=False (the divergent loop hangs pytest -> no report.json), so they are NOT a confirmed verify⇌orrect break under the mechanized derivation (build_one.py:306 declares BROKEN only when r.completed AND not r.resolved; not-completed is inconclusive, never a break). Executed evidence below.
```

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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -99,11 +99,10 @@
       invariant 0 ≤ i ∧ i ≤ vars.length
       invariant result = expectedComponents sampleCoords (vars.drop i)
       done_with i = 0
-      decreasing i
     do
       let k := vars[i - 1]!
       -- extract this component discarding the transient selector label (keep = false)
-      result := (k, sliceCoords selDim sampleCoords false) :: result
+      result := (k, sliceCoords selDim sampleCoords true) :: result
       i := i - 1
     return result
     -- impl-end
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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -94,17 +94,14 @@
   do
     -- impl-start
     let mut result : List (String × List String) := []
-    let mut i := vars.length
-    while i > 0
+    let mut i := 0
+    while i < vars.length
       invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant result = expectedComponents sampleCoords (vars.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = vars.length
     do
-      let k := vars[i - 1]!
-      -- extract this component discarding the transient selector label (keep = false)
-      result := (k, sliceCoords selDim sampleCoords false) :: result
-      i := i - 1
+      let k := vars[i]!
+      result := result ++ [(k, sliceCoords selDim sampleCoords false)]
+      i := i + 1
     return result
     -- impl-end
 
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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -97,12 +97,9 @@
     let mut i := vars.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant result = expectedComponents sampleCoords (vars.drop i)
       done_with i = 0
-      decreasing i
     do
-      let k := vars[i - 1]!
-      -- extract this component discarding the transient selector label (keep = false)
+      let k := vars[0]!
       result := (k, sliceCoords selDim sampleCoords false) :: result
       i := i - 1
     return result
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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -93,18 +93,7 @@
   ensures ∀ p ∈ out, selDim ∉ p.2
   do
     -- impl-start
-    let mut result : List (String × List String) := []
-    let mut i := vars.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant result = expectedComponents sampleCoords (vars.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let k := vars[i - 1]!
-      -- extract this component discarding the transient selector label (keep = false)
-      result := (k, sliceCoords selDim sampleCoords false) :: result
-      i := i - 1
+    let result : List (String × List String) := []
     return result
     -- impl-end
 
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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -95,14 +95,11 @@
     -- impl-start
     let mut result : List (String × List String) := []
     let mut i := vars.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant result = expectedComponents sampleCoords (vars.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let k := vars[i - 1]!
-      -- extract this component discarding the transient selector label (keep = false)
       result := (k, sliceCoords selDim sampleCoords false) :: result
       i := i - 1
     return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. The one operation whose behaviour this change toggles —
@@ -97,13 +97,10 @@
     let mut i := vars.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant result = expectedComponents sampleCoords (vars.drop i)
       done_with i = 0
-      decreasing i
     do
       let k := vars[i - 1]!
-      -- extract this component discarding the transient selector label (keep = false)
-      result := (k, sliceCoords selDim sampleCoords false) :: result
+      result := (k, [selDim]) :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one operation whose behaviour this change toggles —
-- extracting a single labeled component from the combined array — is modeled
-- DEEPLY by `sliceCoords` (pure region) as an A-reference: its coordinate-set
-- result is validated against the real component extractor by axiom_check.py
-- (G-AX). See mapping.md §3.
-- axioms-end

-- pure-start
/- Extracting one labeled component from a combined array yields a slice whose
   coordinate names are the shared sample coordinates, PLUS — unless the
   transient selector label is discarded during extraction — the selector label
   itself left behind as a residual scalar coordinate. `keep = false` discards
   it; `keep = true` retains it. The observable modeled here is the set of
   coordinate NAMES carried by the extracted slice (mapping.md §2, §3.1). -/
def sliceCoords (selDim : String) (sampleCoords : List String) (keep : Bool) : List String :=
  if keep then sampleCoords ++ [selDim] else sampleCoords

@[grind, simp] lemma sliceCoords_discard (selDim : String) (sampleCoords : List String) :
    sliceCoords selDim sampleCoords false = sampleCoords := rfl

/- The correct result of the whole extraction: every component, keyed by its
   label, carries exactly the shared sample coordinates and nothing transient.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern). -/
def expectedComponents (sampleCoords : List String) :
    List String → List (String × List String)
  | []      => []
  | k :: ks => (k, sampleCoords) :: expectedComponents sampleCoords ks

@[grind] lemma expectedComponents_nil (sampleCoords : List String) :
    expectedComponents sampleCoords [] = [] := rfl

@[grind] lemma expectedComponents_cons (sampleCoords : List String) (k : String)
    (ks : List String) :
    expectedComponents sampleCoords (k :: ks)
      = (k, sampleCoords) :: expectedComponents sampleCoords ks := rfl

/- The labels (keys) of the extracted components are exactly the input labels,
   in order — the extraction neither drops, duplicates, nor reorders. -/
@[grind] lemma expectedComponents_keys (sampleCoords : List String) (vs : List String) :
    (expectedComponents sampleCoords vs).map Prod.fst = vs := by
  induction vs with
  | nil => rfl
  | cons k ks ih => simp [expectedComponents, ih]

/- Every extracted component carries exactly the shared sample coordinates as
   its coordinate-name set — in particular none of them carries any name absent
   from the sample coordinates. -/
@[grind] lemma expectedComponents_snd (sampleCoords : List String) (vs : List String) :
    ∀ p ∈ expectedComponents sampleCoords vs, p.2 = sampleCoords := by
  induction vs with
  | nil => intro p hp; simp [expectedComponents] at hp
  | cons k ks ih =>
    intro p hp
    rw [expectedComponents_cons] at hp
    rcases List.mem_cons.mp hp with h | h
    · subst h; rfl
    · exact ih p h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reassemble a combined array into its labeled components.

   `selDim` is the transient selector label used to address each component;
   `sampleCoords` are the coordinate names shared by every component; `vars`
   are the component labels to extract, in order.

   Each component is extracted by addressing it via the selector label. For the
   reassembled collection to be conflict-free, the transient selector label must
   NOT persist as a coordinate on any extracted component — otherwise distinct
   components would carry conflicting values for that same coordinate name and
   could not be combined. The result pairs each label with the coordinate names
   its extracted component carries. -/
method toComponents (selDim : String) (sampleCoords : List String) (vars : List String)
    return (out : List (String × List String))
  require selDim ∉ sampleCoords
  ensures out = expectedComponents sampleCoords vars
  ensures out.map Prod.fst = vars
  ensures ∀ p ∈ out, selDim ∉ p.2
  do
    -- impl-start
    let mut result : List (String × List String) := []
    let mut i := vars.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vars.length
      invariant result = expectedComponents sampleCoords (vars.drop i)
      done_with i = 0
    do
      let k := vars[i - 1]!
      -- extract this component discarding the transient selector label (keep = false)
      result := (k, sliceCoords selDim sampleCoords false) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expectedComponents` peels one pair. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expectedComponents_drop_step (sampleCoords : List String) (vars : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ vars.length) :
    expectedComponents sampleCoords (vars.drop (i - 1))
      = (vars[i - 1]!, sampleCoords) :: expectedComponents sampleCoords (vars.drop i) := by
  have hlt : i - 1 < vars.length := by omega
  have hcons : vars.drop (i - 1) = vars[i - 1]! :: vars.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expectedComponents_cons]

prove_correct toComponents by
  loom_solve
  rw [expectedComponents_drop_step sampleCoords vars i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT ON THE MODELED OBSERVABLE. The frozen spec pins the output completely: ensures out = expectedComponents sampleCoords vars (a concrete input-grounded def -> every terminating verifying impl must return exactly the list where each of vars is paired with exactly sampleCoords), reinforced by ensures out.map Prod.fst = vars and ensures ∀ p∈out, selDim∉p.2. No answer-key echo (expectedComponents is fully computable). same_spec=True verified for all 9 files.

### ATTACKS (all; cmd: `bash scripts/lean_verify.sh <f>.lean`; same_spec cmd per task, all True):
- atk_pos.lean (POSITIVE CONTROL): structurally identical to gold impl (sliceCoords ... false). verify exit=0 (VERIFIES) -> spec non-vacuous.
- atk_1.lean (PREPATCH BUG, keep=true): result:=(k, sliceCoords selDim sampleCoords true)::result. exit=1, unsolved goal at prove_correct (sliceCoords ... true = sampleCoords is false since selDim∉sampleCoords). Reproduces the drop=False residual-selDim bug. REJECTED (good).
- atk_2.lean (control-flow, wrong order): forward loop with result := result ++ [(k,...)]. exit=1, rewrite failed / out=expectedComponents order goal unsolved. REJECTED.
- atk_3.lean (boundary/index bug): always vars[0]! instead of vars[i-1]!. exit=1, rewrite failed on expectedComponents_drop_step. REJECTED.
- atk_4.lean (partial-domain / drop-all): return []. exit=1, [] = expectedComponents ... unsolved for non-empty vars (also leftover proof refs unbound i, confirming impl structurally cannot discharge). REJECTED.
- atk_5.lean (off-by-one): while i>1 (drops one component). exit=1, rewrite/invariant unsolved. REJECTED.
- atk_6.lean (ungrounded coords / wrong constant): result := (k,[selDim])::result. exit=1, invariant [selDim]=sampleCoords unsolved. REJECTED.
All 6 fail for the RIGHT reason (unsolved postcondition/invariant goals, not syntax errors).

NON-TERMINATION VACUITY FINDING (atk_nonterm, atk_nonterm2) — DISCLOSED, judged NOT a break, NOT submitted in the mechanized attacks array:
- atk_nonterm.lean: `while i>0` body never decrements i (result:=result). Loop diverges for non-empty vars; terminates only for vars=[]. Proof: loom_solve alone. verify exit=0 (VERIFIES). same_spec=True.
- atk_nonterm2.lean: guard `i+1>0` (always true for Nat) diverges for ALL inputs. Proof: loom_solve. verify exit=0 (VERIFIES). same_spec=True.
These verify because under PartialCorrectness the `return` is unreachable on the divergent path, so the postcondition is vacuously satisfied (correct-IF-it-terminates).

### MANDATORY RESOLVE RUNS (executed, not speculated):
- FAITHFUL patch of the verifying CORRECT impl (atk_pos) = gold patch.diff. `run_resolve("pydata__xarray-4094", gold)` -> RESOLVED=True, COMPLETED=True, note='resolved'. (positive resolve leg confirmed on the real image.)
- FAITHFUL non-terminating patch (patch_nonterm.diff: replaces `for k in variables: data_dict[k]=...` with `i=len(variables); while i>0: pass` — the transliteration of atk_nonterm). `run_resolve("pydata__xarray-4094", patch_nonterm, timeout=900, retries=0)` -> RESOLVED=False, COMPLETED=False, note='no report ... harness error' (the infinite loop hangs pytest until the harness wall-clock -> EvaluationError -> swebench writes no report.json). Image was present (gold resolved on it minutes earlier), so completed=False is the STRUCTURAL hang, not an image-pull artifact.

WHY NOT A BREAK (framework-accepted, matches build_one.py:_derive_audit_verdict and prior astropy verdicts): (1) The mechanized derivation declares BROKEN only when r.completed AND NOT r.resolved (build_one.py:306); a divergent patch can never yield completed=True, so a non-termination attack can never be mechanically confirmed as a break — it lands in inconclusive_hits, which if submitted would spuriously FAIL the gate. (2) Partial-correctness semantics (loom.semantics.termination "partial", used by 401/500 velvet bundles) guarantee only 'correct IF it terminates'; a non-terminating verified impl carries a VACUOUS guarantee, so its patch's non-resolution does NOT contradict the twin-artifact guarantee. (3) This vacuity is UNIVERSAL to the partial-correctness methodology, not a weakness specific to this spec. Accordingly atk_nonterm/atk_nonterm2 are retained in the scratch dir for human review (atk_nonterm.lean, atk_nonterm2.lean, patch_nonterm.diff) but NOT listed in the mechanized `attacks`/`patches`.

REFINEMENT AUDIT (refinement.md): No kind-3. Steps A1-A3=R (labels/dim/sample-coords ↔ List String/String; iteration order preserved; precondition selDim∉sampleCoords holds by construction). A4=A-reference+I: the changed op (drop flag) is modeled DEEPLY via sliceCoords's keep parameter (keep=false ⇔ drop=True), NOT axiomatized as the function-under-change — correct discipline; the loop/cons/map ops are I (G-CONF-covered). A5=I+R (dict keys ↔ out.map Prod.fst). A6=A-reference (Dataset(data_dict) conflict-free ⇔ selDim∉p.2). No consumed axiom (empty axioms region). The sole A-reference (sliceCoords ↔ self.sel({variable_dim:k},drop=True).squeeze(drop=True) coordinate-name set) is the correct correspondence per mapping.md §3.1 and is validated by axiom_check.py/G-AX (meta.json records G-AX pass 206 shapes, G-CONF pass 405 shapes). A-legs' correspondence to the real callees holds.

VERDICT: SOUND. Every terminating same-spec wrong impl (partial-domain, boundary, control-flow-effect, off-by-one, wrong-constant/ungrounded-oracle, prepatch bug) is REJECTED; the positive control verifies and its faithful (gold) patch RESOLVES (executed); the faithful non-terminating patch does not resolve but only with completed=False (universal partial-correctness vacuity, not a mechanically-confirmable break); refinement.md has no kind-3 and its A-legs correspond correctly to the real callees.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No TERMINATING same-spec wrong impl verifies. The only same-spec verifying wrong impls (atk_nonterm, atk_nonterm2) verify solely via non-termination vacuity of loom.semantics.termination "partial"; their faithful refined patches do NOT resolve but with completed=False (the divergent loop hangs pytest -> no report.json), so they are NOT a confirmed verify⇌orrect break under the mechanized derivation (build_one.py:306 declares BROKEN only when r.completed AND not r.resolved; not-completed is inconclusive, never a break). Executed evidence below.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one operation whose behaviour this change toggles —
-- extracting a single labeled component from the combined array — is modeled
-- DEEPLY by `sliceCoords` (pure region) as an A-reference: its coordinate-set
-- result is validated against the real component extractor by axiom_check.py
-- (G-AX). See mapping.md §3.
-- axioms-end

-- pure-start
/- Extracting one labeled component from a combined array yields a slice whose
   coordinate names are the shared sample coordinates, PLUS — unless the
   transient selector label is discarded during extraction — the selector label
   itself left behind as a residual scalar coordinate. `keep = false` discards
   it; `keep = true` retains it. The observable modeled here is the set of
   coordinate NAMES carried by the extracted slice (mapping.md §2, §3.1). -/
def sliceCoords (selDim : String) (sampleCoords : List String) (keep : Bool) : List String :=
  if keep then sampleCoords ++ [selDim] else sampleCoords

@[grind, simp] lemma sliceCoords_discard (selDim : String) (sampleCoords : List String) :
    sliceCoords selDim sampleCoords false = sampleCoords := rfl

/- The correct result of the whole extraction: every component, keyed by its
   label, carries exactly the shared sample coordinates and nothing transient.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern). -/
def expectedComponents (sampleCoords : List String) :
    List String → List (String × List String)
  | []      => []
  | k :: ks => (k, sampleCoords) :: expectedComponents sampleCoords ks

@[grind] lemma expectedComponents_nil (sampleCoords : List String) :
    expectedComponents sampleCoords [] = [] := rfl

@[grind] lemma expectedComponents_cons (sampleCoords : List String) (k : String)
    (ks : List String) :
    expectedComponents sampleCoords (k :: ks)
      = (k, sampleCoords) :: expectedComponents sampleCoords ks := rfl

/- The labels (keys) of the extracted components are exactly the input labels,
   in order — the extraction neither drops, duplicates, nor reorders. -/
@[grind] lemma expectedComponents_keys (sampleCoords : List String) (vs : List String) :
    (expectedComponents sampleCoords vs).map Prod.fst = vs := by
  induction vs with
  | nil => rfl
  | cons k ks ih => simp [expectedComponents, ih]

/- Every extracted component carries exactly the shared sample coordinates as
   its coordinate-name set — in particular none of them carries any name absent
   from the sample coordinates. -/
@[grind] lemma expectedComponents_snd (sampleCoords : List String) (vs : List String) :
    ∀ p ∈ expectedComponents sampleCoords vs, p.2 = sampleCoords := by
  induction vs with
  | nil => intro p hp; simp [expectedComponents] at hp
  | cons k ks ih =>
    intro p hp
    rw [expectedComponents_cons] at hp
    rcases List.mem_cons.mp hp with h | h
    · subst h; rfl
    · exact ih p h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reassemble a combined array into its labeled components.

   `selDim` is the transient selector label used to address each component;
   `sampleCoords` are the coordinate names shared by every component; `vars`
   are the component labels to extract, in order.

   Each component is extracted by addressing it via the selector label. For the
   reassembled collection to be conflict-free, the transient selector label must
   NOT persist as a coordinate on any extracted component — otherwise distinct
   components would carry conflicting values for that same coordinate name and
   could not be combined. The result pairs each label with the coordinate names
   its extracted component carries. -/
method toComponents (selDim : String) (sampleCoords : List String) (vars : List String)
    return (out : List (String × List String))
  require selDim ∉ sampleCoords
  ensures out = expectedComponents sampleCoords vars
  ensures out.map Prod.fst = vars
  ensures ∀ p ∈ out, selDim ∉ p.2
  do
    -- impl-start
    let mut result : List (String × List String) := []
    let mut i := vars.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vars.length
      invariant result = expectedComponents sampleCoords (vars.drop i)
      done_with i = 0
    do
      let k := vars[i - 1]!
      -- extract this component discarding the transient selector label (keep = false)
      result := (k, sliceCoords selDim sampleCoords false) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expectedComponents` peels one pair. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expectedComponents_drop_step (sampleCoords : List String) (vars : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ vars.length) :
    expectedComponents sampleCoords (vars.drop (i - 1))
      = (vars[i - 1]!, sampleCoords) :: expectedComponents sampleCoords (vars.drop i) := by
  have hlt : i - 1 < vars.length := by omega
  have hcons : vars.drop (i - 1) = vars[i - 1]! :: vars.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expectedComponents_cons]

prove_correct toComponents by
  loom_solve
  rw [expectedComponents_drop_step sampleCoords vars i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT ON THE MODELED OBSERVABLE. The frozen spec pins the output completely: ensures out = expectedComponents sampleCoords vars (a concrete input-grounded def -> every terminating verifying impl must return exactly the list where each of vars is paired with exactly sampleCoords), reinforced by ensures out.map Prod.fst = vars and ensures ∀ p∈out, selDim∉p.2. No answer-key echo (expectedComponents is fully computable). same_spec=True verified for all 9 files.

### ATTACKS (all; cmd: `bash scripts/lean_verify.sh <f>.lean`; same_spec cmd per task, all True):
- atk_pos.lean (POSITIVE CONTROL): structurally identical to gold impl (sliceCoords ... false). verify exit=0 (VERIFIES) -> spec non-vacuous.
- atk_1.lean (PREPATCH BUG, keep=true): result:=(k, sliceCoords selDim sampleCoords true)::result. exit=1, unsolved goal at prove_correct (sliceCoords ... true = sampleCoords is false since selDim∉sampleCoords). Reproduces the drop=False residual-selDim bug. REJECTED (good).
- atk_2.lean (control-flow, wrong order): forward loop with result := result ++ [(k,...)]. exit=1, rewrite failed / out=expectedComponents order goal unsolved. REJECTED.
- atk_3.lean (boundary/index bug): always vars[0]! instead of vars[i-1]!. exit=1, rewrite failed on expectedComponents_drop_step. REJECTED.
- atk_4.lean (partial-domain / drop-all): return []. exit=1, [] = expectedComponents ... unsolved for non-empty vars (also leftover proof refs unbound i, confirming impl structurally cannot discharge). REJECTED.
- atk_5.lean (off-by-one): while i>1 (drops one component). exit=1, rewrite/invariant unsolved. REJECTED.
- atk_6.lean (ungrounded coords / wrong constant): result := (k,[selDim])::result. exit=1, invariant [selDim]=sampleCoords unsolved. REJECTED.
All 6 fail for the RIGHT reason (unsolved postcondition/invariant goals, not syntax errors).

NON-TERMINATION VACUITY FINDING (atk_nonterm, atk_nonterm2) — DISCLOSED, judged NOT a break, NOT submitted in the mechanized attacks array:
- atk_nonterm.lean: `while i>0` body never decrements i (result:=result). Loop diverges for non-empty vars; terminates only for vars=[]. Proof: loom_solve alone. verify exit=0 (VERIFIES). same_spec=True.
- atk_nonterm2.lean: guard `i+1>0` (always true for Nat) diverges for ALL inputs. Proof: loom_solve. verify exit=0 (VERIFIES). same_spec=True.
These verify because under PartialCorrectness the `return` is unreachable on the divergent path, so the postcondition is vacuously satisfied (correct-IF-it-terminates).

### MANDATORY RESOLVE RUNS (executed, not speculated):
- FAITHFUL patch of the verifying CORRECT impl (atk_pos) = gold patch.diff. `run_resolve("pydata__xarray-4094", gold)` -> RESOLVED=True, COMPLETED=True, note='resolved'. (positive resolve leg confirmed on the real image.)
- FAITHFUL non-terminating patch (patch_nonterm.diff: replaces `for k in variables: data_dict[k]=...` with `i=len(variables); while i>0: pass` — the transliteration of atk_nonterm). `run_resolve("pydata__xarray-4094", patch_nonterm, timeout=900, retries=0)` -> RESOLVED=False, COMPLETED=False, note='no report ... harness error' (the infinite loop hangs pytest until the harness wall-clock -> EvaluationError -> swebench writes no report.json). Image was present (gold resolved on it minutes earlier), so completed=False is the STRUCTURAL hang, not an image-pull artifact.

WHY NOT A BREAK (framework-accepted, matches build_one.py:_derive_audit_verdict and prior astropy verdicts): (1) The mechanized derivation declares BROKEN only when r.completed AND NOT r.resolved (build_one.py:306); a divergent patch can never yield completed=True, so a non-termination attack can never be mechanically confirmed as a break — it lands in inconclusive_hits, which if submitted would spuriously FAIL the gate. (2) Partial-correctness semantics (loom.semantics.termination "partial", used by 401/500 velvet bundles) guarantee only 'correct IF it terminates'; a non-terminating verified impl carries a VACUOUS guarantee, so its patch's non-resolution does NOT contradict the twin-artifact guarantee. (3) This vacuity is UNIVERSAL to the partial-correctness methodology, not a weakness specific to this spec. Accordingly atk_nonterm/atk_nonterm2 are retained in the scratch dir for human review (atk_nonterm.lean, atk_nonterm2.lean, patch_nonterm.diff) but NOT listed in the mechanized `attacks`/`patches`.

REFINEMENT AUDIT (refinement.md): No kind-3. Steps A1-A3=R (labels/dim/sample-coords ↔ List String/String; iteration order preserved; precondition selDim∉sampleCoords holds by construction). A4=A-reference+I: the changed op (drop flag) is modeled DEEPLY via sliceCoords's keep parameter (keep=false ⇔ drop=True), NOT axiomatized as the function-under-change — correct discipline; the loop/cons/map ops are I (G-CONF-covered). A5=I+R (dict keys ↔ out.map Prod.fst). A6=A-reference (Dataset(data_dict) conflict-free ⇔ selDim∉p.2). No consumed axiom (empty axioms region). The sole A-reference (sliceCoords ↔ self.sel({variable_dim:k},drop=True).squeeze(drop=True) coordinate-name set) is the correct correspondence per mapping.md §3.1 and is validated by axiom_check.py/G-AX (meta.json records G-AX pass 206 shapes, G-CONF pass 405 shapes). A-legs' correspondence to the real callees holds.

VERDICT: SOUND. Every terminating same-spec wrong impl (partial-domain, boundary, control-flow-effect, off-by-one, wrong-constant/ungrounded-oracle, prepatch bug) is REJECTED; the positive control verifies and its faithful (gold) patch RESOLVES (executed); the faithful non-terminating patch does not resolve but only with completed=False (universal partial-correctness vacuity, not a mechanically-confirmable break); refinement.md has no kind-3 and its A-legs correspond correctly to the real callees.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet.language)=True; impl differs only keep=false vs keep=true. spec_view carries precondition 'selDim ∉ sampleCoords' and postcondition 'out = expectedComponents sampleCoords vars'. Empirically re-ran axiom_check.py (206 shapes, exit 0) and conformance logic (405 shapes) in an era-correct venv (numpy 1.24.4 / pandas 1.5.3 / xarray 2022.3.0); installed swebench-lean xarray 0.15.1 is broken vs pandas 3.0.5 and cannot execute the callee, so I built the isolated venv to exercise the true repo behavior. The gold patch is the verbatim one-token drop=True addition at dataarray.py:2344. The two divergences arise from the DECLARED coord-name abstraction (mapping.md §2) scoped to single-sample-dim; the Lean precondition does not formally exclude multi-dim/singleton, so they technically satisfy 'require', but they are (a) not bug-discriminating and (b) not gold-resolving respectively, so the spec is a sound, tight, discriminator-preserving abstraction. This matches the recorded P2 verdict (ACCEPTED); I independently reproduced its divergences and confirm they are lossiness, not a faithfulness break. FAITHFUL.

Counterexample / evidence:

```
N/A — no bug-discriminating input where the modeled function wrongly certifies. The discriminating postcondition (selDim ∉ p.2) matches the real callee across the ENTIRE precondition domain: 0 selDim leaks under gold over 1418 extracted components (n_vars 2-5, sample_len 1-6, incl. singletons); prepatch always leaks. On all F2P-tested single-sample-dim inputs (len>=2) model == real callee exactly.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction audit for velvet pydata__xarray-4094.

GOLD EDIT: single-token addition of `drop=True` at xarray/core/dataarray.py:1964 — `data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)`. Effect: discard the residual scalar selector coordinate (named after the indexed dim `dim`) left by the point-selection, so `Dataset(data_dict)` reassembly is conflict-free.

PUBLIC problem_statement (verified against data/swe_bench_verified/test.jsonl; hints_text is EMPTY) already discloses: to_unstacked_dataset roundtrip broken for single-dim variables; the exact failure `MergeError: conflicting values for variable 'y' on objects to be combined`; expected = a working roundtrip; MCVE reproducer. Thus the residual conflicting selector coordinate is already public.

SPEC-REGION INTEGRITY: independently re-verified swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet').language) = True. Printed spec_view(Solution.lean): the impl region collapses to `-- implementation elided — supplied by the consumer` and prove_correct body to `-- proof elided — supplied by the consumer`. The gold vs prepatch difference lives ENTIRELY in the elided impl (keep=false vs keep=true) and elided proof body; the spec view is byte-identical across twins.

### What the spec view exposes and why it is not leakage
- Postconditions `out = expectedComponents sampleCoords vars`, `out.map Prod.fst = vars`, `∀ p ∈ out, selDim ∉ p.2` formalize exactly the public MergeError property (no extracted component may retain the transient selector coordinate). Encoding required behaviour derivable from the public statement is the spec's job, not answer leakage.
- `sliceCoords` (with its keep branch: keep=true retains selDim, keep=false discards) and `expectedComponents` are visible in the pure region, but the impl's actual keep=false choice is ELIDED and the proof body is ELIDED. Deriving keep=false from `selDim ∉ p.2` is solving the spec, not reading the answer.
- The spec view names NO gold mechanism: no `drop`, `sel`, `squeeze`, `variable_dim`, `to_unstacked_dataset`, `Dataset`, `MergeError`, no Python API, no filename/line, no diff text. Abstract symbols only (toComponents, sliceCoords, selDim, sampleCoords).

CONCLUSION: nothing in the spec view reconstructs the gold edit beyond what the public problem_statement already provides. NO-LEAKAGE. Consistent with recorded G-PANEL-3. (Note: co-panel G-PANEL-2 faithfulness is recorded pass here; any faithfulness concern is out of scope for this leakage attacker.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
