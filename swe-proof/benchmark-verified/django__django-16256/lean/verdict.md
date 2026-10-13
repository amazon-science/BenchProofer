# P2 adversarial audit — django__django-16256

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,14 +112,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- WRONG (atk_1): ignore scope bindings entirely (control-flow: no merge). -/
 def implementation_scopedOp
     (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
-  let mut out := kwargs
-  for b in bindings do
-    out := kwUpsert out b.1 b.2
-  return out
+  let _ := bindings
+  return kwargs
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,14 +112,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- WRONG (atk_2): partial-domain — merge only the FIRST binding. -/
 def implementation_scopedOp
     (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
-  let mut out := kwargs
-  for b in bindings do
-    out := kwUpsert out b.1 b.2
-  return out
+  match bindings with
+  | [] => return kwargs
+  | b :: _ => return kwUpsert kwargs b.1 b.2
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,12 +112,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- WRONG (atk_3): boundary/off-by-one — drop the LAST binding. -/
 def implementation_scopedOp
     (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
   let mut out := kwargs
-  for b in bindings do
+  for b in bindings.dropLast do
     out := kwUpsert out b.1 b.2
   return out
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,13 +112,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- WRONG (atk_4): control-flow-effect — APPEND each binding instead of upsert,
+so a scope key already present in kwargs keeps the caller value (first-occurrence). -/
 def implementation_scopedOp
     (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
   let mut out := kwargs
   for b in bindings do
-    out := kwUpsert out b.1 b.2
+    out := out ++ [(b.1, b.2)]
   return out
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,13 +112,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- WRONG (atk_5): forces each scope key to the WRONG value (b.2 + 1). -/
 def implementation_scopedOp
     (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
   let mut out := kwargs
   for b in bindings do
-    out := kwUpsert out b.1 b.2
+    out := kwUpsert out b.1 (b.2 + 1)
   return out
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -112,29 +112,16 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Merge the collection's scope bindings into the caller kwargs, one binding at
-a time (each forced in), then hand the effective map to the data operation. -/
+/-- ECHO (atk_6): observationally identical fold form (ungrounded-oracle echo). -/
 def implementation_scopedOp
-    (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
-  let mut out := kwargs
-  for b in bindings do
-    out := kwUpsert out b.1 b.2
-  return out
+    (bindings kwargs : List (String × Int)) : List (String × Int) :=
+  bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs
 -- impl-end
 
 -- proof-start
 theorem impl_eq_foldl (bindings kwargs) :
     implementation_scopedOp bindings kwargs
-      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by
-  induction bindings generalizing kwargs with
-  | nil => rfl
-  | cons a as ih =>
-    unfold implementation_scopedOp
-    simp only [List.forIn_cons, List.foldl_cons, Id.run, bind, pure]
-    have := ih (kwUpsert kwargs a.1 a.2)
-    unfold implementation_scopedOp at this
-    simp only [Id.run, bind, pure] at this
-    exact this
+      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := rfl
 
 theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),
     (bindings.map Prod.fst).Nodup →
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Abstract behavior of an async collection operation on a scoped collection.

A scoped collection carries a set of *scope bindings* (key → value) that every
element created or matched through it must satisfy. When an operation is invoked
with a set of caller-supplied keyword arguments, the operation must first merge
the collection's scope bindings into those arguments (a binding overrides any
caller value for the same key) before performing the underlying data operation.

We model the observable result as the *effective argument map*: the caller
kwargs with every scope binding forced in. The specification pins that map:
every scope key resolves to its scope value, and every non-scope key is left
exactly as the caller supplied it (frame). This is the behavior an operation
routed through the scoped collection must exhibit; an operation that ignores the
scope bindings (leaving scope keys unset or at a caller-chosen value) fails it.

Keys are modeled as `String`, values as `Int` (an opaque value identifier); the
argument map is an association list, `List.lookup` giving first-occurrence
semantics as for a Python dict.
-/

-- axioms-start
-- (No unchanged callee needs an opaque signature: the merge is modeled deeply
-- as a pure association-list update. The proof agent may add `_prop` axioms
-- only if a callee contract is genuinely required.)
-- axioms-end

-- pure-start
/-- Force a single binding `key ↦ val` into an association list: replace the
first occurrence of `key` if present, otherwise append. Mirrors `d[key] = val`
on an insertion-ordered map. -/
def kwUpsert : List (String × Int) → String → Int → List (String × Int)
  | [],             key, val => [(key, val)]
  | (k, v) :: rest, key, val =>
      if k = key then (key, val) :: rest
      else (k, v) :: kwUpsert rest key val

theorem kwUpsert_lookup_self (kvs key val) :
    (kwUpsert kvs key val).lookup key = some val := by
  induction kvs with
  | nil => simp [kwUpsert]
  | cons a as ih =>
    obtain ⟨k, v⟩ := a
    unfold kwUpsert
    by_cases h : k = key
    · subst h; simp [List.lookup_cons]
    · have hne : key ≠ k := fun e => h e.symm
      simp only [h, if_false, List.lookup_cons, beq_eq_false_iff_ne.mpr hne, ih]

theorem kwUpsert_lookup_other (kvs key val k) (h : k ≠ key) :
    (kwUpsert kvs key val).lookup k = kvs.lookup k := by
  induction kvs with
  | nil =>
    have : (k == key) = false := beq_eq_false_iff_ne.mpr h
    simp [kwUpsert, List.lookup_cons, this]
  | cons a as ih =>
    obtain ⟨k0, v0⟩ := a
    unfold kwUpsert
    by_cases hh : k0 = key
    · subst hh
      have hne : (k == k0) = false := beq_eq_false_iff_ne.mpr h
      simp [List.lookup_cons, hne]
    · simp only [hh, if_false, List.lookup_cons]
      by_cases hk0 : k == k0
      · simp [hk0]
      · simp [hk0, ih]

/-- Folding bindings whose keys all differ from `k` preserves `lookup k`. -/
theorem foldl_lookup_other : ∀ (bindings kwargs : List (String × Int)) (k : String),
    (∀ b ∈ bindings, b.1 ≠ k) →
    (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup k = kwargs.lookup k := by
  intro bindings
  induction bindings with
  | nil => intro kwargs k _; rfl
  | cons a as ih =>
    intro kwargs k h
    rw [List.foldl_cons]
    have hnk : a.1 ≠ k := h a (List.mem_cons_self)
    rw [ih (kwUpsert kwargs a.1 a.2) k (fun b hb => h b (List.mem_cons_of_mem _ hb))]
    exact kwUpsert_lookup_other kwargs a.1 a.2 k (fun e => hnk e.symm)

/-- Every bound key resolves to its bound value after the full fold (keys nodup). -/
theorem foldl_lookup_bound : ∀ (bindings : List (String × Int)),
    (bindings.map Prod.fst).Nodup → ∀ kwargs, ∀ b ∈ bindings,
      (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup b.1 = some b.2 := by
  intro bindings
  induction bindings with
  | nil => intro _ kwargs b hb; simp at hb
  | cons a as ih =>
    intro hnd kwargs b hb
    simp only [List.map_cons, List.nodup_cons] at hnd
    obtain ⟨hnotin, hnd'⟩ := hnd
    rw [List.foldl_cons]
    rcases List.mem_cons.mp hb with rfl | hmem
    · rw [foldl_lookup_other as (kwUpsert kwargs b.1 b.2) b.1
            (fun c hc e => hnotin (e ▸ List.mem_map_of_mem hc))]
      exact kwUpsert_lookup_self kwargs b.1 b.2
    · exact ih hnd' (kwUpsert kwargs a.1 a.2) b hmem
-- pure-end

-- post-conditions-start
/-- The effective argument map produced by a scoped async operation: every scope
binding is forced (scope key ↦ scope value), and every key not in the scope is
left exactly as the caller supplied it. -/
def problem_spec_scopedOp
    (bindings kwargs result : List (String × Int)) : Prop :=
  (∀ b ∈ bindings, result.lookup b.1 = some b.2) ∧
  (∀ k, (∀ b ∈ bindings, b.1 ≠ k) → result.lookup k = kwargs.lookup k)
-- post-conditions-end

-- impl-start
/-- Merge the collection's scope bindings into the caller kwargs, one binding at
a time (each forced in), then hand the effective map to the data operation. -/
def implementation_scopedOp
    (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
  let mut out := kwargs
  for b in bindings do
    out := kwUpsert out b.1 b.2
  return out
-- impl-end

-- proof-start
theorem impl_eq_foldl (bindings kwargs) :
    implementation_scopedOp bindings kwargs
      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by
  induction bindings generalizing kwargs with
  | nil => rfl
  | cons a as ih =>
    unfold implementation_scopedOp
    simp only [List.forIn_cons, List.foldl_cons, Id.run, bind, pure]
    have := ih (kwUpsert kwargs a.1 a.2)
    unfold implementation_scopedOp at this
    simp only [Id.run, bind, pure] at this
    exact this

theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),
    (bindings.map Prod.fst).Nodup →
    problem_spec_scopedOp bindings kwargs (implementation_scopedOp bindings kwargs) := by
  intro bindings kwargs hnd
  rw [impl_eq_foldl]
  refine ⟨?_, ?_⟩
  · intro b hb
    exact foldl_lookup_bound bindings hnd kwargs b hb
  · intro k hk
    exact foldl_lookup_other bindings kwargs k hk
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The bundle's authored spec (problem_spec_scopedOp) correctly admits only behaviorally-correct impls of the scope-binding merge.

Docker runs under `docker`. Pre-pulled + retagged the canonical image swebench/sweb.eval.x86_64.django_1776_django-16256:latest (first resolve returned completed=False 'no report/image pull failure' before the image was present; re-run after pull succeeded).

POSITIVE CONTROL: positive_control.lean (byte-identical copy of Solution.lean). `bash scripts/lean_verify.sh positive_control.lean` -> exit 0. same_spec=True.

PREPATCH REPRODUCED: prepatch.lean (Solution_prepatch.lean, impl `return kwargs`). lean_verify exit 1 (fails first conjunct: a scope key absent from kwargs has result.lookup=none != some b.2). same_spec=True. Good — the bug is caught.

### IMPL-ONLY ATTACKS (all same_spec=True, cmd `bash scripts/lean_verify.sh atk_N.lean`):
 - atk_1 identity/no-merge (ignores bindings): exit 1 (Type mismatch — obligation false). REJECTED (good).
 - atk_2 partial-domain (merge only first binding): exit 1. REJECTED.
 - atk_3 boundary (drop last binding via dropLast): exit 1. REJECTED.
 - atk_4 control-flow-effect (append instead of upsert; first-occurrence keeps caller value): exit 1. REJECTED.
 - atk_5 wrong-value (kwUpsert b.1 (b.2+1)): exit 1. REJECTED.
 - atk_6 ungrounded-oracle ECHO (foldl form, observationally identical; impl_eq_foldl := rfl): exit 0, `#print axioms correct_scopedOp` = [propext, Classical.choice, Quot.sound] (clean). CANDIDATE -> materialized faithful patch (= gold merge patch, atk_6_patch.diff) EXECUTED through run_resolve: completed=True, resolved=True, 1 attempt. => correct echo, NOT a weakness.
Every impl-only wrong variant fails to verify against the real correct_scopedOp obligation; the only verifying one is behaviorally correct and resolves. This is the exact refinement-fidelity signature of a SOUND spec.

WHY THE POSTCONDITION IS TIGHT: problem_spec_scopedOp pins result.lookup on EVERY key — conjunct 1 forces every binding key to its value; conjunct 2 frames every non-binding key to kwargs.lookup. There is no free key, so any impl that mislabels/omits/mis-values a binding, or perturbs a framed key, is unprovable.

REFINEMENT.MD AUDIT: 3 legs. Row1 `let mut out := kwargs` = I. Row2 `for b in bindings do kwUpsert out b.1 b.2` = R (kwUpsert deeply models Python dict `d[k]=v` replace-first-else-append; List.lookup = first-occurrence dict read). Row3 `return out` = I. NO A-consumed and NO A-reference legs: the axioms region is EMPTY (grep for ^axiom/^opaque = NONE), G-AX=skip is correct, and G-CONF=pass confirms the R bijection over the fuzzer. No kind-3 leg. The underlying create/get_or_create/update_or_create data op is behavior-identical pre/post-fix and correctly not modeled. Correspondence to the real callees (fields.py generic + related_descriptors.py FK/M2M sync methods that assign scope bindings before super()) holds; the async wrappers delegate via sync_to_async(self.<op>).

SAME_SPEC / HARNESS HAZARD (reported, NOT counted as a break): _lean_spec_view elides BOTH the impl AND the ENTIRE proof region — including the `theorem correct_scopedOp` STATEMENT and its Nodup precondition. Therefore markers.same_spec does NOT pin the correctness obligation, contradicting adversary.py's own docstring ('only the impl region may differ ... can't cheat by weakening a contract'). I built two probe attacks that EXPLOIT this: atk_7 (wrong identity impl + `theorem correct_scopedOp : True := trivial`; lean_verify exit 0; #print axioms = none) and atk_8 (wrong +7 value impl + real-looking statement with a vacuous `False` hypothesis; exit 0; axioms=[propext]). Both are same_spec=True and pass the runner's check_attack as CANDIDATE (verified programmatically: adversary.check_attack(atk_7) -> same_spec=True, verifies=True, verify_completed=True). I materialized atk_7's faithful patch (impl ignores scope bindings = base-commit behavior) and EXECUTED run_resolve: completed=True, resolved=False (3 attempts, consistent). Under the LITERAL _derive_audit_verdict, submitting atk_7/atk_8 as attacks would flip G-EQ to BROKEN. I deliberately did NOT list them as attacks because:

(1) they violate the audit protocol/adversary.py contract by editing the proof region (deleting the obligation) rather than testing it against the impl;

(2) the exploit is spec-INDEPENDENT — it flips EVERY lean bundle to BROKEN regardless of postcondition quality, so it discriminates nothing about THIS bundle;

(3) it acts only in the over-rejection (fail-closed) direction — it can produce a false BROKEN but never a false green, so it cannot undermine any verified-green soundness claim. Recommend a harness fix: same_spec for lean should additionally pin the `theorem correct_<name>` statement text (or the audit re-derivation should reject attacks whose proof region diverges from the bundle's), so a proof-region edit cannot masquerade as a same-spec impl attack. Files: atk_7.lean, atk_8.lean, atk_7_patch.diff, resolve_atk_7.log in the scratch dir.

CONCLUSION: For the bundle's AUTHORED specification, no same-spec impl-region wrong implementation verifies (atk_1-5 all fail; atk_6 is a correct echo that resolves). >=5 attacks run, positive control verifies, prepatch reproduced, refinement legs all R/I with no A-legs and no kind-3. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Abstract behavior of an async collection operation on a scoped collection.

A scoped collection carries a set of *scope bindings* (key → value) that every
element created or matched through it must satisfy. When an operation is invoked
with a set of caller-supplied keyword arguments, the operation must first merge
the collection's scope bindings into those arguments (a binding overrides any
caller value for the same key) before performing the underlying data operation.

We model the observable result as the *effective argument map*: the caller
kwargs with every scope binding forced in. The specification pins that map:
every scope key resolves to its scope value, and every non-scope key is left
exactly as the caller supplied it (frame). This is the behavior an operation
routed through the scoped collection must exhibit; an operation that ignores the
scope bindings (leaving scope keys unset or at a caller-chosen value) fails it.

Keys are modeled as `String`, values as `Int` (an opaque value identifier); the
argument map is an association list, `List.lookup` giving first-occurrence
semantics as for a Python dict.
-/

-- axioms-start
-- (No unchanged callee needs an opaque signature: the merge is modeled deeply
-- as a pure association-list update. The proof agent may add `_prop` axioms
-- only if a callee contract is genuinely required.)
-- axioms-end

-- pure-start
/-- Force a single binding `key ↦ val` into an association list: replace the
first occurrence of `key` if present, otherwise append. Mirrors `d[key] = val`
on an insertion-ordered map. -/
def kwUpsert : List (String × Int) → String → Int → List (String × Int)
  | [],             key, val => [(key, val)]
  | (k, v) :: rest, key, val =>
      if k = key then (key, val) :: rest
      else (k, v) :: kwUpsert rest key val

theorem kwUpsert_lookup_self (kvs key val) :
    (kwUpsert kvs key val).lookup key = some val := by
  induction kvs with
  | nil => simp [kwUpsert]
  | cons a as ih =>
    obtain ⟨k, v⟩ := a
    unfold kwUpsert
    by_cases h : k = key
    · subst h; simp [List.lookup_cons]
    · have hne : key ≠ k := fun e => h e.symm
      simp only [h, if_false, List.lookup_cons, beq_eq_false_iff_ne.mpr hne, ih]

theorem kwUpsert_lookup_other (kvs key val k) (h : k ≠ key) :
    (kwUpsert kvs key val).lookup k = kvs.lookup k := by
  induction kvs with
  | nil =>
    have : (k == key) = false := beq_eq_false_iff_ne.mpr h
    simp [kwUpsert, List.lookup_cons, this]
  | cons a as ih =>
    obtain ⟨k0, v0⟩ := a
    unfold kwUpsert
    by_cases hh : k0 = key
    · subst hh
      have hne : (k == k0) = false := beq_eq_false_iff_ne.mpr h
      simp [List.lookup_cons, hne]
    · simp only [hh, if_false, List.lookup_cons]
      by_cases hk0 : k == k0
      · simp [hk0]
      · simp [hk0, ih]

/-- Folding bindings whose keys all differ from `k` preserves `lookup k`. -/
theorem foldl_lookup_other : ∀ (bindings kwargs : List (String × Int)) (k : String),
    (∀ b ∈ bindings, b.1 ≠ k) →
    (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup k = kwargs.lookup k := by
  intro bindings
  induction bindings with
  | nil => intro kwargs k _; rfl
  | cons a as ih =>
    intro kwargs k h
    rw [List.foldl_cons]
    have hnk : a.1 ≠ k := h a (List.mem_cons_self)
    rw [ih (kwUpsert kwargs a.1 a.2) k (fun b hb => h b (List.mem_cons_of_mem _ hb))]
    exact kwUpsert_lookup_other kwargs a.1 a.2 k (fun e => hnk e.symm)

/-- Every bound key resolves to its bound value after the full fold (keys nodup). -/
theorem foldl_lookup_bound : ∀ (bindings : List (String × Int)),
    (bindings.map Prod.fst).Nodup → ∀ kwargs, ∀ b ∈ bindings,
      (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup b.1 = some b.2 := by
  intro bindings
  induction bindings with
  | nil => intro _ kwargs b hb; simp at hb
  | cons a as ih =>
    intro hnd kwargs b hb
    simp only [List.map_cons, List.nodup_cons] at hnd
    obtain ⟨hnotin, hnd'⟩ := hnd
    rw [List.foldl_cons]
    rcases List.mem_cons.mp hb with rfl | hmem
    · rw [foldl_lookup_other as (kwUpsert kwargs b.1 b.2) b.1
            (fun c hc e => hnotin (e ▸ List.mem_map_of_mem hc))]
      exact kwUpsert_lookup_self kwargs b.1 b.2
    · exact ih hnd' (kwUpsert kwargs a.1 a.2) b hmem
-- pure-end

-- post-conditions-start
/-- The effective argument map produced by a scoped async operation: every scope
binding is forced (scope key ↦ scope value), and every key not in the scope is
left exactly as the caller supplied it. -/
def problem_spec_scopedOp
    (bindings kwargs result : List (String × Int)) : Prop :=
  (∀ b ∈ bindings, result.lookup b.1 = some b.2) ∧
  (∀ k, (∀ b ∈ bindings, b.1 ≠ k) → result.lookup k = kwargs.lookup k)
-- post-conditions-end

-- impl-start
/-- Merge the collection's scope bindings into the caller kwargs, one binding at
a time (each forced in), then hand the effective map to the data operation. -/
def implementation_scopedOp
    (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
  let mut out := kwargs
  for b in bindings do
    out := kwUpsert out b.1 b.2
  return out
-- impl-end

-- proof-start
theorem impl_eq_foldl (bindings kwargs) :
    implementation_scopedOp bindings kwargs
      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by
  induction bindings generalizing kwargs with
  | nil => rfl
  | cons a as ih =>
    unfold implementation_scopedOp
    simp only [List.forIn_cons, List.foldl_cons, Id.run, bind, pure]
    have := ih (kwUpsert kwargs a.1 a.2)
    unfold implementation_scopedOp at this
    simp only [Id.run, bind, pure] at this
    exact this

theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),
    (bindings.map Prod.fst).Nodup →
    problem_spec_scopedOp bindings kwargs (implementation_scopedOp bindings kwargs) := by
  intro bindings kwargs hnd
  rw [impl_eq_foldl]
  refine ⟨?_, ?_⟩
  · intro b hb
    exact foldl_lookup_bound bindings hnd kwargs b hb
  · intro k hk
    exact foldl_lookup_other bindings kwargs k hk
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The bundle's authored spec (problem_spec_scopedOp) correctly admits only behaviorally-correct impls of the scope-binding merge.

Docker runs under `docker`. Pre-pulled + retagged the canonical image swebench/sweb.eval.x86_64.django_1776_django-16256:latest (first resolve returned completed=False 'no report/image pull failure' before the image was present; re-run after pull succeeded).

POSITIVE CONTROL: positive_control.lean (byte-identical copy of Solution.lean). `bash scripts/lean_verify.sh positive_control.lean` -> exit 0. same_spec=True.

PREPATCH REPRODUCED: prepatch.lean (Solution_prepatch.lean, impl `return kwargs`). lean_verify exit 1 (fails first conjunct: a scope key absent from kwargs has result.lookup=none != some b.2). same_spec=True. Good — the bug is caught.

### IMPL-ONLY ATTACKS (all same_spec=True, cmd `bash scripts/lean_verify.sh atk_N.lean`):
 - atk_1 identity/no-merge (ignores bindings): exit 1 (Type mismatch — obligation false). REJECTED (good).
 - atk_2 partial-domain (merge only first binding): exit 1. REJECTED.
 - atk_3 boundary (drop last binding via dropLast): exit 1. REJECTED.
 - atk_4 control-flow-effect (append instead of upsert; first-occurrence keeps caller value): exit 1. REJECTED.
 - atk_5 wrong-value (kwUpsert b.1 (b.2+1)): exit 1. REJECTED.
 - atk_6 ungrounded-oracle ECHO (foldl form, observationally identical; impl_eq_foldl := rfl): exit 0, `#print axioms correct_scopedOp` = [propext, Classical.choice, Quot.sound] (clean). CANDIDATE -> materialized faithful patch (= gold merge patch, atk_6_patch.diff) EXECUTED through run_resolve: completed=True, resolved=True, 1 attempt. => correct echo, NOT a weakness.
Every impl-only wrong variant fails to verify against the real correct_scopedOp obligation; the only verifying one is behaviorally correct and resolves. This is the exact refinement-fidelity signature of a SOUND spec.

WHY THE POSTCONDITION IS TIGHT: problem_spec_scopedOp pins result.lookup on EVERY key — conjunct 1 forces every binding key to its value; conjunct 2 frames every non-binding key to kwargs.lookup. There is no free key, so any impl that mislabels/omits/mis-values a binding, or perturbs a framed key, is unprovable.

REFINEMENT.MD AUDIT: 3 legs. Row1 `let mut out := kwargs` = I. Row2 `for b in bindings do kwUpsert out b.1 b.2` = R (kwUpsert deeply models Python dict `d[k]=v` replace-first-else-append; List.lookup = first-occurrence dict read). Row3 `return out` = I. NO A-consumed and NO A-reference legs: the axioms region is EMPTY (grep for ^axiom/^opaque = NONE), G-AX=skip is correct, and G-CONF=pass confirms the R bijection over the fuzzer. No kind-3 leg. The underlying create/get_or_create/update_or_create data op is behavior-identical pre/post-fix and correctly not modeled. Correspondence to the real callees (fields.py generic + related_descriptors.py FK/M2M sync methods that assign scope bindings before super()) holds; the async wrappers delegate via sync_to_async(self.<op>).

SAME_SPEC / HARNESS HAZARD (reported, NOT counted as a break): _lean_spec_view elides BOTH the impl AND the ENTIRE proof region — including the `theorem correct_scopedOp` STATEMENT and its Nodup precondition. Therefore markers.same_spec does NOT pin the correctness obligation, contradicting adversary.py's own docstring ('only the impl region may differ ... can't cheat by weakening a contract'). I built two probe attacks that EXPLOIT this: atk_7 (wrong identity impl + `theorem correct_scopedOp : True := trivial`; lean_verify exit 0; #print axioms = none) and atk_8 (wrong +7 value impl + real-looking statement with a vacuous `False` hypothesis; exit 0; axioms=[propext]). Both are same_spec=True and pass the runner's check_attack as CANDIDATE (verified programmatically: adversary.check_attack(atk_7) -> same_spec=True, verifies=True, verify_completed=True). I materialized atk_7's faithful patch (impl ignores scope bindings = base-commit behavior) and EXECUTED run_resolve: completed=True, resolved=False (3 attempts, consistent). Under the LITERAL _derive_audit_verdict, submitting atk_7/atk_8 as attacks would flip G-EQ to BROKEN. I deliberately did NOT list them as attacks because:

(1) they violate the audit protocol/adversary.py contract by editing the proof region (deleting the obligation) rather than testing it against the impl;

(2) the exploit is spec-INDEPENDENT — it flips EVERY lean bundle to BROKEN regardless of postcondition quality, so it discriminates nothing about THIS bundle;

(3) it acts only in the over-rejection (fail-closed) direction — it can produce a false BROKEN but never a false green, so it cannot undermine any verified-green soundness claim. Recommend a harness fix: same_spec for lean should additionally pin the `theorem correct_<name>` statement text (or the audit re-derivation should reject attacks whose proof region diverges from the bundle's), so a proof-region edit cannot masquerade as a same-spec impl attack. Files: atk_7.lean, atk_8.lean, atk_7_patch.diff, resolve_atk_7.log in the scratch dir.

CONCLUSION: For the bundle's AUTHORED specification, no same-spec impl-region wrong implementation verifies (atk_1-5 all fail; atk_6 is a correct echo that resolves). >=5 attacks run, positive control verifies, prepatch reproduced, refinement legs all R/I with no A-legs and no kind-3. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; the modeled function matches the real repo behavior. Checks performed: (1) same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True — spec region (post-conditions + shared pure lemmas) is byte-identical. (2) lean_verify.sh exit 0, compiles cleanly (only unused-simp-arg linter warnings). (3) #print axioms correct_scopedOp = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is genuine. (4) conformance_check shadow-vs-dict fuzz: 0 disagreements over sampled inputs.

Spec: problem_spec_scopedOp pins the effective kwargs map — (a) every scope binding key resolves to its bound value; (b) frame: every non-scope key equals caller's kwargs.lookup. implementation_scopedOp folds kwUpsert (replace-first-else-append = Python d[k]=v on insertion-ordered dict) over the bindings starting from kwargs.

Real repo @ base_commit 76e37513: the gold patch adds async wrappers (acreate/aget_or_create/aupdate_or_create) that delegate via sync_to_async to the manager's OWN sync ops, which are unchanged and inject scope bindings before super(): reverse FK sets kwargs[self.field.name]=self.instance (1 binding); generic sets kwargs[content_type_field_name] and kwargs[object_id_field_name] (2 distinct bindings). Pre-fix the async op ran the bare QuerySet method without injection. The sole observable delta is exactly 'force scope bindings into the effective kwargs' — which is what the spec pins.

Modeling boundary is sound: real **kwargs dicts have no duplicate keys and scope field names are distinct (Nodup precondition holds); Python d[k]=v maps precisely to kwUpsert; the 'defaults' kwarg is a non-scope key correctly left in the frame; the underlying create/get_or_create/update_or_create data op is behavior-identical pre/post-fix so not modeling it is legitimate, not spec-too-strong. No input was found where the modeled merge disagrees with the real repo's dict-merge. G-DIFF is real: prepatch impl 'return kwargs' fails conjunct (a) for a scope key absent from kwargs, so its gold proof fails to typecheck.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[]) and my semantic review confirms it. Spec view is fully abstract (kwUpsert / List (String × Int) association-list merge, 'scoped collection'/'scope bindings'/'effective argument map' prose). Checks: (1) no diff markers, no patched file path (related_descriptors.py / fields.py) or dotted module path in view; (2) no gold-patch line reproduced — nothing Python appears; (3) patch-changed distinctive symbols {acreate, aget_or_create, aupdate_or_create, create, get_or_create, update_or_create, Child} do NOT appear in any spec-view identifier or docstring; (4) no bug/fix/patch/regression narration in comments. Critically, the PUBLIC problem_statement already embeds the gold diff verbatim (async def acreate: return await sync_to_async(self.create)(**kwargs); kwargs[self.field.name]=self.instance), so the abstract spec reveals strictly LESS than what is public — no gold-edit localization beyond problem_statement. same_spec(Solution, Solution_prepatch)=True: the discriminator lives only in the elided impl/proof regions, not the spec view. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).