# P2 adversarial audit — scikit-learn__scikit-learn-14141

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,15 +82,20 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- Pre-image skeleton: the roster the report iterates over omits its final
+    -- entry (`dependencyNames.dropLast`), so the produced report covers one
+    -- fewer dependency than the frozen spec requires. `prove_correct` MUST fail
+    -- (the result differs from `depEntries dependencyNames` and the final entry
+    -- is absent from the keys).
+    let names := dependencyNames.dropLast
     let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
+    let mut i := names.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
+      invariant 0 ≤ i ∧ i ≤ names.length
+      invariant result = depEntries (names.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := dependencyNames[i - 1]!
+      let n := names[i - 1]!
       let ver :| ver = lookupVersion n
       result := (n, ver) :: result
       i := i - 1
@@ -115,5 +120,5 @@
 
 prove_correct collectDependencyVersions by
   loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
+  rw [depEntries_drop_step (dependencyNames.dropLast) i (by omega) (by omega)]
   simp_all
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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,19 +82,9 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
-    let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := dependencyNames[i - 1]!
-      let ver :| ver = lookupVersion n
-      result := (n, ver) :: result
-      i := i - 1
-    return result
+    -- WRONG: returns the empty report (covers nothing). Should fail both
+    -- postconditions.
+    return []
     -- impl-end
 end
 
@@ -114,6 +104,4 @@
   rw [hcons, depEntries_cons]
 
 prove_correct collectDependencyVersions by
-  loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,15 +82,17 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- WRONG (partial-domain): iterate over dependencyNames.tail, dropping the
+    -- first roster entry (pip). The result has 8 entries, not 9.
+    let names := dependencyNames.tail
     let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
+    let mut i := names.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
+      invariant 0 ≤ i ∧ i ≤ names.length
+      invariant result = depEntries (names.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := dependencyNames[i - 1]!
+      let n := names[i - 1]!
       let ver :| ver = lookupVersion n
       result := (n, ver) :: result
       i := i - 1
@@ -115,5 +117,5 @@
 
 prove_correct collectDependencyVersions by
   loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
+  rw [depEntries_drop_step (dependencyNames.tail) i (by omega) (by omega)]
   simp_all
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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,13 +82,14 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- WRONG (boundary / off-by-one): start the countdown at length-1 instead
+    -- of length, so the last roster entry (joblib) is never emitted.
     let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
+    let mut i := dependencyNames.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dependencyNames.length
       invariant result = depEntries (dependencyNames.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := dependencyNames[i - 1]!
       let ver :| ver = lookupVersion n
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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,19 +82,21 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- WRONG (control-flow effect): build the correct roster, then prepend a
+    -- spurious ("extrapkg", none) entry so the output has 10 entries and the
+    -- key order is wrong.
     let mut result : List (List Char × Option (List Char)) := []
     let mut i := dependencyNames.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dependencyNames.length
       invariant result = depEntries (dependencyNames.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := dependencyNames[i - 1]!
       let ver :| ver = lookupVersion n
       result := (n, ver) :: result
       i := i - 1
-    return result
+    return ("extrapkg".toList, none) :: result
     -- impl-end
 end
 
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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,15 +82,17 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- WRONG (order): iterate the reversed roster, so the output lists joblib
+    -- first and pip last — the key order disagrees with depEntries.
+    let names := dependencyNames.reverse
     let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
+    let mut i := names.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
+      invariant 0 ≤ i ∧ i ≤ names.length
+      invariant result = depEntries (names.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := dependencyNames[i - 1]!
+      let n := names[i - 1]!
       let ver :| ver = lookupVersion n
       result := (n, ver) :: result
       i := i - 1
@@ -115,5 +117,5 @@
 
 prove_correct collectDependencyVersions by
   loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
+  rw [depEntries_drop_step (dependencyNames.reverse) i (by omega) (by omega)]
   simp_all
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,19 +82,10 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
-    let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := dependencyNames[i - 1]!
-      let ver :| ver = lookupVersion n
-      result := (n, ver) :: result
-      i := i - 1
-    return result
+    -- ECHO: return the spec RHS literally. This is behaviourally correct (it
+    -- IS depEntries dependencyNames), so it should verify AND resolve; used to
+    -- confirm the echo-attack policy (verify+resolve, not a spec weakness).
+    return depEntries dependencyNames
     -- impl-end
 end
 
@@ -114,6 +105,4 @@
   rw [hcons, depEntries_cons]
 
 prove_correct collectDependencyVersions by
-  loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- The version string reported for one installed third-party dependency — `none`
@@ -82,15 +82,17 @@
   ensures "joblib".toList ∈ out.map Prod.fst
   do
     -- impl-start
+    -- WRONG (partial-domain / truncation): only report the first 5 roster
+    -- names (take 5), so joblib and 3 others are missing.
+    let names := dependencyNames.take 5
     let mut result : List (List Char × Option (List Char)) := []
-    let mut i := dependencyNames.length
+    let mut i := names.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
-      invariant result = depEntries (dependencyNames.drop i)
+      invariant 0 ≤ i ∧ i ≤ names.length
+      invariant result = depEntries (names.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := dependencyNames[i - 1]!
+      let n := names[i - 1]!
       let ver :| ver = lookupVersion n
       result := (n, ver) :: result
       i := i - 1
@@ -115,5 +117,5 @@
 
 prove_correct collectDependencyVersions by
   loom_solve
-  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
+  rw [depEntries_drop_step (dependencyNames.take 5) i (by omega) (by omega)]
   simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The version string reported for one installed third-party dependency — `none`
   when that dependency is absent or exposes no version. This is an unchanged
   environment query (import the module, read its advertised version); it is
   modeled as an uninterpreted function because its result is environment
   dependent and is NOT what this report's contract pins. The contract pins only
   WHICH dependencies the report covers, never the concrete version values.
   Provenance + soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom lookupVersion : List Char → Option (List Char)
-- axioms-end

-- pure-start
/- The set of third-party dependencies the diagnostic version report covers, in
   report order. A definite, stable roster so the report is predictable across
   environments; it includes joblib alongside the other relevant scientific and
   packaging dependencies. -/
def dependencyNames : List (List Char) :=
  [ "pip".toList,
    "setuptools".toList,
    "sklearn".toList,
    "numpy".toList,
    "scipy".toList,
    "Cython".toList,
    "pandas".toList,
    "matplotlib".toList,
    "joblib".toList ]

/- The report entry for one dependency: its name paired with its reported
   version. The whole report is the per-dependency expansion of the roster, in
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
noncomputable def depEntries : List (List Char) → List (List Char × Option (List Char))
  | []      => []
  | n :: ns => (n, lookupVersion n) :: depEntries ns

@[grind] lemma depEntries_nil : depEntries [] = [] := rfl
@[grind] lemma depEntries_cons (n : List Char) (ns : List (List Char)) :
    depEntries (n :: ns) = (n, lookupVersion n) :: depEntries ns := rfl

/- Projecting the names out of the report recovers exactly the roster: every
   dependency in the roster is covered, in order, regardless of its version. -/
@[grind] lemma depEntries_keys (ns : List (List Char)) :
    (depEntries ns).map Prod.fst = ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih => simp [depEntries, ih]

/- joblib is one of the covered dependencies. -/
@[grind] lemma joblib_mem_roster : "joblib".toList ∈ dependencyNames := by decide

/- The non-deterministic choice of one dependency's reported version is
   well-posed: for any target value `v`, the set of values equal to `v` is
   non-empty (`v` itself). This supplies the constructive existence witness so
   the `:|` choice in the loop body elaborates. It does NOT weaken verification:
   under demonic choice the postcondition must hold for every value the predicate
   allows — here exactly `lookupVersion n`. -/
noncomputable instance findableEqOptList (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method collectDependencyVersions
    return (out : List (List Char × Option (List Char)))
  ensures out = depEntries dependencyNames
  ensures "joblib".toList ∈ out.map Prod.fst
  do
    -- impl-start
    let mut result : List (List Char × Option (List Char)) := []
    let mut i := dependencyNames.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
      invariant result = depEntries (dependencyNames.drop i)
      done_with i = 0
    do
      let n := dependencyNames[i - 1]!
      let ver :| ver = lookupVersion n
      result := (n, ver) :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `depEntries` peels one entry. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma depEntries_drop_step (names : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ names.length) :
    depEntries (names.drop (i - 1))
      = (names[i - 1]!, lookupVersion names[i - 1]!) :: depEntries (names.drop i) := by
  have hlt : i - 1 < names.length := by omega
  have hcons : names.drop (i - 1) = names[i - 1]! :: names.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, depEntries_cons]

prove_correct collectDependencyVersions by
  loom_solve
  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No verifying same-spec wrong impl exists; the only same-spec impl that verifies besides the positive control is a behaviourally-correct echo whose faithful patch RESOLVES.

ENV: worked; same_spec verified True for all 8 attacks + positive control (velvet backend; impl/proof-only edits, axioms/pure/pre/post byte-identical).

SPEC STRUCTURE (why tight): two postconditions on collectDependencyVersions: (1) EXACT equality out = depEntries dependencyNames against the FROZEN full 9-name roster [pip,setuptools,sklearn,numpy,scipy,Cython,pandas,matplotlib,joblib]; (2) "joblib".toList in out.map Prod.fst. The exact-equality clause is load-bearing: any verifying impl must reproduce the full ordered roster incl. joblib. The discriminating content (joblib membership) is modeled CONCRETELY in the pure region, not behind any axiom.

### ATTACKS (cmd: bash scripts/lean_verify.sh <file>; exit 0=verifies, 1=error):
- atk_1 atk_1.lean = committed Solution_prepatch.lean (iterate dependencyNames.dropLast) -> EXIT 1. PREPATCH BUG REPRODUCED; fails both postconditions (result != depEntries dependencyNames; joblib absent from keys).
- atk_2 return [] (empty report) -> EXIT 1; residual goal reduces to False / joblib-membership false.
- atk_3 partial-domain: iterate dependencyNames.tail (omit pip) -> EXIT 1; unsolved out = depEntries dependencyNames + joblib membership.
- atk_4 boundary/off-by-one: start i := length-1 (drop last entry joblib) -> EXIT 1; unsolved [] = depEntries (drop (len-1) names).
- atk_5 control-flow-effect: correct loop then prepend spurious ("extrapkg",none) -> EXIT 1; unsolved ("extrapkg",none)::result_1 = depEntries dependencyNames.
- atk_6 order: iterate dependencyNames.reverse (joblib first, pip last) -> EXIT 1; unsolved out = depEntries dependencyNames.
- atk_8 partial-domain/truncation: dependencyNames.take 5 -> EXIT 1; unsolved out = depEntries dependencyNames + joblib membership.
- atk_7 ungrounded-oracle echo: return depEntries dependencyNames (the spec RHS literally) -> EXIT 0 VERIFIES. But this impl is BEHAVIOURALLY CORRECT (it IS the full 9-name roster incl. joblib). Per protocol its faithful refined patch was materialized (= full-roster _get_deps_info, i.e. gold patch.diff verbatim, refinement.md says patch.diff is gold verbatim) and RUN through the official harness.
- pos_control = shipped Solution.lean (structurally-real backward-fold loop) -> EXIT 0 VERIFIES => spec is non-vacuous.

MANDATORY RESOLVE RUN (executed, not speculated): swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-14141', <atk_7 faithful patch = gold patch.diff>, timeout=1200) via `docker` official harness (image swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14141 present; benchmark swe_bench_verified, docker_oracle=True). RESULT: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False note='resolved'. So the ONLY verifying same-spec impl's faithful patch RESOLVES => verify does NOT imply not-correct here; no break.

REFINEMENT.MD A-LEG AUDIT: every leg is R / A-consumed / A-reference / I, no kind-3. A3 lookupVersion (A-consumed): uninterpreted axiom, NO ensures -> no behavioral claim; corresponds to the UNCHANGED per-name version resolution (sys.modules/import_module -> __version__, None on ImportError). Its value never enters the observed quantity (key-set/order/membership); depEntries's value component is unconstrained, so an echo of lookupVersion discharges nothing. G-AX correctly scoped (directive 7) to codomain (str-or-None) + totality against the real UNPATCHED callee, NOT the roster (the changed function). A1 roster (R+I) models the discriminating joblib membership CONCRETELY in the pure region, not axiomatized. A2 (I, loop=depEntries fold), A4 (R, dict<->insertion-ordered assoc-list bijection) mechanical, covered by G-CONF. Correspondence to real callees holds.

CONCLUSION: >=5 distinct wrong-impl classes (partial-domain x3: tail/take5/dropLast, boundary/off-by-one, control-flow-effect, order/reversed, empty, ungrounded-oracle echo) all encoded & machine-verified; every genuinely-wrong impl FAILS verification for the right reason; the sole verifying same-spec impl is behaviourally correct and its materialized faithful patch RESOLVES under run_resolve. spec is TIGHT, G-EQ SOUND, verify=>correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The version string reported for one installed third-party dependency — `none`
   when that dependency is absent or exposes no version. This is an unchanged
   environment query (import the module, read its advertised version); it is
   modeled as an uninterpreted function because its result is environment
   dependent and is NOT what this report's contract pins. The contract pins only
   WHICH dependencies the report covers, never the concrete version values.
   Provenance + soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom lookupVersion : List Char → Option (List Char)
-- axioms-end

-- pure-start
/- The set of third-party dependencies the diagnostic version report covers, in
   report order. A definite, stable roster so the report is predictable across
   environments; it includes joblib alongside the other relevant scientific and
   packaging dependencies. -/
def dependencyNames : List (List Char) :=
  [ "pip".toList,
    "setuptools".toList,
    "sklearn".toList,
    "numpy".toList,
    "scipy".toList,
    "Cython".toList,
    "pandas".toList,
    "matplotlib".toList,
    "joblib".toList ]

/- The report entry for one dependency: its name paired with its reported
   version. The whole report is the per-dependency expansion of the roster, in
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
noncomputable def depEntries : List (List Char) → List (List Char × Option (List Char))
  | []      => []
  | n :: ns => (n, lookupVersion n) :: depEntries ns

@[grind] lemma depEntries_nil : depEntries [] = [] := rfl
@[grind] lemma depEntries_cons (n : List Char) (ns : List (List Char)) :
    depEntries (n :: ns) = (n, lookupVersion n) :: depEntries ns := rfl

/- Projecting the names out of the report recovers exactly the roster: every
   dependency in the roster is covered, in order, regardless of its version. -/
@[grind] lemma depEntries_keys (ns : List (List Char)) :
    (depEntries ns).map Prod.fst = ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih => simp [depEntries, ih]

/- joblib is one of the covered dependencies. -/
@[grind] lemma joblib_mem_roster : "joblib".toList ∈ dependencyNames := by decide

/- The non-deterministic choice of one dependency's reported version is
   well-posed: for any target value `v`, the set of values equal to `v` is
   non-empty (`v` itself). This supplies the constructive existence witness so
   the `:|` choice in the loop body elaborates. It does NOT weaken verification:
   under demonic choice the postcondition must hold for every value the predicate
   allows — here exactly `lookupVersion n`. -/
noncomputable instance findableEqOptList (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method collectDependencyVersions
    return (out : List (List Char × Option (List Char)))
  ensures out = depEntries dependencyNames
  ensures "joblib".toList ∈ out.map Prod.fst
  do
    -- impl-start
    let mut result : List (List Char × Option (List Char)) := []
    let mut i := dependencyNames.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dependencyNames.length
      invariant result = depEntries (dependencyNames.drop i)
      done_with i = 0
    do
      let n := dependencyNames[i - 1]!
      let ver :| ver = lookupVersion n
      result := (n, ver) :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `depEntries` peels one entry. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma depEntries_drop_step (names : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ names.length) :
    depEntries (names.drop (i - 1))
      = (names[i - 1]!, lookupVersion names[i - 1]!) :: depEntries (names.drop i) := by
  have hlt : i - 1 < names.length := by omega
  have hcons : names.drop (i - 1) = names[i - 1]! :: names.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, depEntries_cons]

prove_correct collectDependencyVersions by
  loom_solve
  rw [depEntries_drop_step dependencyNames i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No verifying same-spec wrong impl exists; the only same-spec impl that verifies besides the positive control is a behaviourally-correct echo whose faithful patch RESOLVES.

ENV: worked; same_spec verified True for all 8 attacks + positive control (velvet backend; impl/proof-only edits, axioms/pure/pre/post byte-identical).

SPEC STRUCTURE (why tight): two postconditions on collectDependencyVersions: (1) EXACT equality out = depEntries dependencyNames against the FROZEN full 9-name roster [pip,setuptools,sklearn,numpy,scipy,Cython,pandas,matplotlib,joblib]; (2) "joblib".toList in out.map Prod.fst. The exact-equality clause is load-bearing: any verifying impl must reproduce the full ordered roster incl. joblib. The discriminating content (joblib membership) is modeled CONCRETELY in the pure region, not behind any axiom.

### ATTACKS (cmd: bash scripts/lean_verify.sh <file>; exit 0=verifies, 1=error):
- atk_1 atk_1.lean = committed Solution_prepatch.lean (iterate dependencyNames.dropLast) -> EXIT 1. PREPATCH BUG REPRODUCED; fails both postconditions (result != depEntries dependencyNames; joblib absent from keys).
- atk_2 return [] (empty report) -> EXIT 1; residual goal reduces to False / joblib-membership false.
- atk_3 partial-domain: iterate dependencyNames.tail (omit pip) -> EXIT 1; unsolved out = depEntries dependencyNames + joblib membership.
- atk_4 boundary/off-by-one: start i := length-1 (drop last entry joblib) -> EXIT 1; unsolved [] = depEntries (drop (len-1) names).
- atk_5 control-flow-effect: correct loop then prepend spurious ("extrapkg",none) -> EXIT 1; unsolved ("extrapkg",none)::result_1 = depEntries dependencyNames.
- atk_6 order: iterate dependencyNames.reverse (joblib first, pip last) -> EXIT 1; unsolved out = depEntries dependencyNames.
- atk_8 partial-domain/truncation: dependencyNames.take 5 -> EXIT 1; unsolved out = depEntries dependencyNames + joblib membership.
- atk_7 ungrounded-oracle echo: return depEntries dependencyNames (the spec RHS literally) -> EXIT 0 VERIFIES. But this impl is BEHAVIOURALLY CORRECT (it IS the full 9-name roster incl. joblib). Per protocol its faithful refined patch was materialized (= full-roster _get_deps_info, i.e. gold patch.diff verbatim, refinement.md says patch.diff is gold verbatim) and RUN through the official harness.
- pos_control = shipped Solution.lean (structurally-real backward-fold loop) -> EXIT 0 VERIFIES => spec is non-vacuous.

MANDATORY RESOLVE RUN (executed, not speculated): swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-14141', <atk_7 faithful patch = gold patch.diff>, timeout=1200) via `docker` official harness (image swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14141 present; benchmark swe_bench_verified, docker_oracle=True). RESULT: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False note='resolved'. So the ONLY verifying same-spec impl's faithful patch RESOLVES => verify does NOT imply not-correct here; no break.

REFINEMENT.MD A-LEG AUDIT: every leg is R / A-consumed / A-reference / I, no kind-3. A3 lookupVersion (A-consumed): uninterpreted axiom, NO ensures -> no behavioral claim; corresponds to the UNCHANGED per-name version resolution (sys.modules/import_module -> __version__, None on ImportError). Its value never enters the observed quantity (key-set/order/membership); depEntries's value component is unconstrained, so an echo of lookupVersion discharges nothing. G-AX correctly scoped (directive 7) to codomain (str-or-None) + totality against the real UNPATCHED callee, NOT the roster (the changed function). A1 roster (R+I) models the discriminating joblib membership CONCRETELY in the pure region, not axiomatized. A2 (I, loop=depEntries fold), A4 (R, dict<->insertion-ordered assoc-list bijection) mechanical, covered by G-CONF. Correspondence to real callees holds.

CONCLUSION: >=5 distinct wrong-impl classes (partial-domain x3: tail/take5/dropLast, boundary/off-by-one, control-flow-effect, order/reversed, empty, ungrounded-oracle echo) all encoded & machine-verified; every genuinely-wrong impl FAILS verification for the right reason; the sole verifying same-spec impl is behaviourally correct and its materialized faithful patch RESOLVES under run_resolve. spec is TIGHT, G-EQ SOUND, verify=>correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) assessment for velvet scikit-learn__scikit-learn-14141.

### Checks performed
1. Spec region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) => True. Only the impl region differs (prepatch iterates dependencyNames.dropLast). Spec (axioms/pure/pre/post + method signature ensures) is frozen and identical.
2. Lean verification: scripts/lean_verify.sh Solution.lean => EXIT 0 (prove_correct succeeds).
3. Real repo callee inspected at base_commit worktree _show_versions.py: _get_deps_info() iterates a fixed `deps` list literal, builds deps_info[modname] = module.__version__, or None on ImportError. Gold patch inserts "joblib" into deps.

### MODEL vs REAL:
- Postconditions: (1) out = depEntries dependencyNames; (2) "joblib".toList in out.map Prod.fst. dependencyNames = [pip, setuptools, sklearn, numpy, scipy, Cython, pandas, matplotlib, joblib] = the exact post-patch roster in order.
- lookupVersion : List Char -> Option (List Char) is UNINTERPRETED with NO `ensures` axioms. It is the weakest possible contract: the postconditions hold for EVERY total lookupVersion, so the spec asserts nothing about concrete version values and cannot over-claim relative to the environment-dependent real per-name resolution. The only implicit commitments are codomain (str-or-None) and totality (never raises beyond handled ImportError) — validated against the real unchanged callee by G-AX.
- depEntries pairs each roster name with its version in order; real dict inserts each distinct name once in `deps` order. Assoc-list <-> insertion-ordered dict is a bijection on (key-set, order, per-key value) since the roster has no duplicates (mapping.md §2). dict membership 'joblib' in deps_info <-> "joblib".toList in out.map Prod.fst.

DIVERGENCE SEARCH: The function takes no input; the only reachable arguments to lookupVersion are the 9 fixed roster names, all standard packages that either import with a str __version__ or raise ImportError->None. No reachable input makes the model disagree with the real patched _get_deps_info() on the pinned observation (covered-dependency key-set/order + joblib membership). No spec-too-strong / drift found.

prepatch skeleton correctly fails BOTH postconditions (roster short one entry; joblib absent) => G-DIFF sound.

Verdict: FAITHFUL — no diverging input exists between the modeled function and the real callee on the contract-pinned observations.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard_failures); spec region is frozen (same_spec(Solution, Solution_prepatch)=True). The gold edit is a single insertion of "joblib" into the deps roster of _get_deps_info(). The public problem_statement already discloses this verbatim: 'Add joblib in show_versions. joblib should be added to the dependencies listed in show_versions...'. Every spec-view element that references joblib — dependencyNames containing "joblib".toList (line 34), joblib_mem_roster lemma (line 57), and the postcondition "joblib".toList ∈ out.map Prod.fst (line 82) — encodes exactly 'joblib is among the covered dependencies', which is precisely what the problem_statement states. The other 8 roster names (pip/setuptools/sklearn/numpy/scipy/Cython/pandas/matplotlib) are pre-existing base-repo context, not the gold edit. The depEntries fold and uninterpreted lookupVersion axiom reveal nothing about the change (versions explicitly not pinned). No file path/line/insertion-position detail beyond the problem_statement appears in the consumer spec view. Note: Solution_prepatch.lean's impl uses dependencyNames.dropLast (omitting the final joblib entry), but that is the refinement-audit-only prepatch file, not part of the consumer spec view, and it merely reflects the base state the problem_statement already describes. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
