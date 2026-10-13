# P2 adversarial audit — django__django-13786

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_overclear.lean`, `atk_inverted.lean`, `atk_dupecho.lean`, `atk_dropoverride.lean`, `atk_identity.lean`, `atk_boundary.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl closes correct_combineOptions. The postcondition pins the dict observable: proved geq_no_divergence (atk_tightness.lean, exit 0, depends on NO axioms) — any two results satisfying problem_spec_combineOptions agree at optLookup for EVERY key and both have Nodup keys, hence are the identical Python dict (order-independent, no shadowed dups). So any impl that closes the proof produces gold's exact observable and resolves; no closing-but-non-resolving impl exists on the real (Nodup) input domain.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,10 +76,7 @@
 def implementation_combineOptions {V : Type}
     (base override : List (String × V)) (managedKeys : List String) :
     List (String × V) := Id.run do
-  let mut options := mergeOpts base override
-  for key in managedKeys do
-    if ! keyPresent override key then
-      options := dropKey options key
+  let options := mergeOpts base override
   return options
 -- impl-end
 
```

Attack 2 — `atk_overclear.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,6 +80,8 @@
   for key in managedKeys do
     if ! keyPresent override key then
       options := dropKey options key
+  -- BUG: also drop base-only keys not in override (over-clear beyond managed)
+  options := options.filter (fun p => keyPresent override p.1)
   return options
 -- impl-end
 
```

Attack 3 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
     List (String × V) := Id.run do
   let mut options := mergeOpts base override
   for key in managedKeys do
-    if ! keyPresent override key then
+    if keyPresent override key then
       options := dropKey options key
   return options
 -- impl-end
```

Attack 4 — `atk_dupecho.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,8 @@
   for key in managedKeys do
     if ! keyPresent override key then
       options := dropKey options key
-  return options
+  -- BUG: append a shadowed duplicate of the head entry (breaks Nodup)
+  return options ++ options.take 1
 -- impl-end
 
 
```

Attack 5 — `atk_dropoverride.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,8 +78,8 @@
     List (String × V) := Id.run do
   let mut options := mergeOpts base override
   for key in managedKeys do
-    if ! keyPresent override key then
-      options := dropKey options key
+    -- BUG: drop the key unconditionally (even when override mentions it)
+    options := dropKey options key
   return options
 -- impl-end
 
```

Attack 6 — `atk_identity.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,11 +76,7 @@
 def implementation_combineOptions {V : Type}
     (base override : List (String × V)) (managedKeys : List String) :
     List (String × V) := Id.run do
-  let mut options := mergeOpts base override
-  for key in managedKeys do
-    if ! keyPresent override key then
-      options := dropKey options key
-  return options
+  return base
 -- impl-end
 
 
```

Attack 7 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     (base override : List (String × V)) (managedKeys : List String) :
     List (String × V) := Id.run do
   let mut options := mergeOpts base override
-  for key in managedKeys do
+  for key in (managedKeys.take 1) do
     if ! keyPresent override key then
       options := dropKey options key
   return options
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Collapsing two consecutive option-configuration steps into a single combined
option set.

The first step establishes an initial set of named option settings (a mapping
from option keys to their values). A second, overriding step supplies its own
set of settings that should take effect in place of the first. The combined
result is obtained by overlaying the overriding step's settings on top of the
initial ones (the overriding value wins for any key both mention, and keys only
the overriding step mentions are added).

There is, however, a designated family of *managed* keys: keys whose value is
considered to be owned entirely by the overriding step. For a managed key, the
overriding step is authoritative — if it does NOT mention that key, the key must
be cleared from the combined result, even when the initial step had set it.
Keys outside the managed family are left untouched when the overriding step is
silent about them.

The behavior is stated abstractly as an input→output relation on the combined
option set; the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the combination is
-- spelled out concretely (an overlay of two key→value mappings followed by the
-- clearing of any managed key the overriding mapping is silent about).
-- axioms-end

-- pure-start
/-- Is key `k` present in the key→value mapping `d`? -/
def keyPresent {V : Type} (d : List (String × V)) (k : String) : Bool :=
  d.any (fun p => p.1 == k)

/-- Look up key `k` in `d`, returning the value of the first entry with that key
(`none` if absent). A mapping is read as a dictionary: first match wins. -/
def optLookup {V : Type} (d : List (String × V)) (k : String) : Option V :=
  (d.find? (fun p => p.1 == k)).map (·.2)

/-- Overlay `override` on top of `base`: keep every overriding entry, and keep
each base entry whose key the overriding mapping does not mention. -/
def mergeOpts {V : Type} (base override : List (String × V)) : List (String × V) :=
  override ++ base.filter (fun p => ! keyPresent override p.1)

/-- Remove every entry whose key equals `k`. -/
def dropKey {V : Type} (d : List (String × V)) (k : String) : List (String × V) :=
  d.filter (fun p => p.1 != k)

/-- The value the combined mapping should hold at key `k`:
* if the overriding mapping mentions `k`, its value wins;
* otherwise, if `k` is a managed key, it is cleared (`none`);
* otherwise the base value (if any) survives. -/
def expectedLookup {V : Type} (base override : List (String × V))
    (managedKeys : List String) (k : String) : Option V :=
  match optLookup override k with
  | some v => some v
  | none   => if managedKeys.contains k then none else optLookup base k
-- pure-end

-- post-conditions-start
/-- The combined mapping is a genuine dictionary (its keys are distinct) and
agrees, at every key, with the desired overlay-then-clear-managed behavior. The
key-distinctness conjunct rules out a result that merely shares the right
first-match lookups while hiding shadowed duplicate keys (a Python `dict` has no
duplicate keys); together the two clauses pin the resulting dictionary exactly. -/
def problem_spec_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String)
    (result : List (String × V)) : Prop :=
  (result.map Prod.fst).Nodup ∧
  (∀ k : String, optLookup result k = expectedLookup base override managedKeys k)
-- post-conditions-end

-- impl-start
def implementation_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String) :
    List (String × V) := Id.run do
  let mut options := mergeOpts base override
  for key in managedKeys do
    if ! keyPresent override key then
      options := dropKey options key
  return options
-- impl-end


-- proof-start
/-- The loop's initial accumulator: the overlay of `override` on `base`. -/
def options0 {V : Type} (base override : List (String × V)) : List (String × V) :=
  mergeOpts base override

/-- The pure loop-step: drop `key` from the accumulator iff `override` is silent
about it. -/
def stepFn {V : Type} (override : List (String × V))
    (acc : List (String × V)) (key : String) : List (String × V) :=
  if ! keyPresent override key then dropKey acc key else acc

/-- Fold-level invariant: the accumulator has distinct keys, and its lookup at
every key agrees with the initial overlay except that keys already processed and
not mentioned by `override` read as `none`. -/
def CombineInv {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) : Prop :=
  (acc.map Prod.fst).Nodup ∧
  (∀ k : String,
    optLookup acc k =
      (if processed.contains k && ! keyPresent override k then none
       else optLookup (mergeOpts base override) k))

theorem keyPresent_iff_lookup {V : Type} (d : List (String × V)) (k : String) :
    keyPresent d k = true ↔ ∃ v, optLookup d k = some v := by
  simp only [keyPresent, optLookup, ← Option.isSome_iff_exists, Option.isSome_map,
    List.find?_isSome, List.any_eq_true]

theorem optLookup_dropKey_eq {V : Type} (d : List (String × V)) (k q : String) :
    optLookup (dropKey d k) q = if q = k then none else optLookup d q := by
  simp only [optLookup, dropKey]
  induction d with
  | nil => simp
  | cons p ds ih =>
    rw [List.filter_cons]
    by_cases hpk : (p.1 != k) = true
    · rw [if_pos hpk, List.find?_cons, List.find?_cons]
      by_cases hpq : (p.1 == q) = true
      · rw [hpq]
        simp only [beq_iff_eq] at hpq
        subst hpq
        simp only [bne_iff_ne, ne_eq] at hpk
        rw [if_neg hpk]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]
    · rw [if_neg hpk, List.find?_cons]
      simp only [bne_iff_ne, ne_eq, Decidable.not_not] at hpk
      by_cases hpq : (p.1 == q) = true
      · simp only [beq_iff_eq] at hpq
        subst hpk
        rw [if_pos hpq.symm, ih, if_pos hpq.symm]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]

theorem map_fst_dropKey_Nodup {V : Type} (d : List (String × V)) (k : String) :
    (d.map Prod.fst).Nodup → ((dropKey d k).map Prod.fst).Nodup := by
  intro h
  unfold dropKey
  exact List.Nodup.sublist (List.filter_sublist.map Prod.fst) h

theorem optLookup_mergeOpts {V : Type} (base override : List (String × V)) (k : String) :
    optLookup (mergeOpts base override) k =
      (match optLookup override k with
       | some v => some v
       | none   => optLookup base k) := by
  unfold optLookup mergeOpts
  rw [List.find?_append]
  cases h : (override.find? (fun p => p.1 == k)) with
  | some pair => simp
  | none =>
    have hp : keyPresent override k = false := by
      have hiff := keyPresent_iff_lookup override k
      simp only [optLookup, h, Option.map_none] at hiff
      by_contra hc
      simp only [Bool.not_eq_false] at hc
      obtain ⟨v, hv⟩ := hiff.mp hc
      exact Option.noConfusion hv
    simp only [Option.none_or, Option.map_none]
    rw [List.find?_filter]
    have hpred : (fun a : String × V => decide ((!keyPresent override a.1) = true ∧ (a.1 == k) = true))
        = (fun p : String × V => p.1 == k) := by
      funext a
      by_cases hak : (a.1 == k) = true
      · have he : a.1 = k := by simpa using hak
        subst he
        simp [hp]
      · simp only [Bool.not_eq_true] at hak
        simp [hak]
    rw [hpred]

theorem options0_Nodup {V : Type} (base override : List (String × V)) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((mergeOpts base override).map Prod.fst).Nodup := by
  intro hbase hoverride
  unfold mergeOpts
  rw [List.map_append, List.nodup_append]
  refine ⟨hoverride, (List.filter_sublist.map Prod.fst).nodup hbase, ?_⟩
  intro a ha b hb hab
  subst hab
  obtain ⟨q, hq_mem, hq_eq⟩ := List.mem_map.mp ha
  obtain ⟨p, hp_filter, hp_eq⟩ := List.mem_map.mp hb
  rw [List.mem_filter] at hp_filter
  obtain ⟨_, hpP⟩ := hp_filter
  have hpres : keyPresent override a = true := by
    unfold keyPresent
    rw [List.any_eq_true]
    exact ⟨q, hq_mem, by simp [hq_eq]⟩
  rw [hp_eq, hpres] at hpP
  simp at hpP

theorem loop_is_foldl {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    implementation_combineOptions base override managedKeys =
      List.foldl (stepFn override) (mergeOpts base override) managedKeys := by
  simp only [implementation_combineOptions, Id.run]
  generalize mergeOpts base override = init
  induction managedKeys generalizing init with
  | nil => rfl
  | cons k ks ih =>
    simp only [List.forIn_cons, List.foldl_cons, stepFn]
    split <;> exact ih _

theorem Inv_step {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) (key : String) :
    CombineInv base override processed acc →
    CombineInv base override (processed ++ [key]) (stepFn override acc key) := by
  intro h
  obtain ⟨hnodup, hlook⟩ := h
  unfold stepFn
  by_cases hk : keyPresent override key = true
  · -- override mentions key: stepFn = acc
    simp only [hk, Bool.not_true, Bool.false_eq_true, if_false]
    refine ⟨hnodup, fun k => ?_⟩
    rw [hlook k]
    by_cases hkk : k = key
    · subst hkk
      simp [hk]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]
  · -- override silent about key: stepFn = dropKey acc key
    have hkf : keyPresent override key = false := by
      simpa using hk
    simp only [hkf, Bool.not_false, if_true]
    refine ⟨map_fst_dropKey_Nodup acc key hnodup, fun k => ?_⟩
    rw [optLookup_dropKey_eq acc key k, hlook k]
    by_cases hkk : k = key
    · subst hkk
      rw [List.contains_append, List.contains_cons]
      simp [hkf]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]

theorem foldl_preserves_Inv {V : Type} (base override : List (String × V))
    (processed_init : List String) (acc : List (String × V)) :
    CombineInv base override processed_init acc →
    ∀ (ks : List String),
      CombineInv base override (processed_init ++ ks)
        (List.foldl (stepFn override) acc ks) := by
  intro h ks
  induction ks generalizing processed_init acc with
  | nil => simpa using h
  | cons k rest ih =>
    have hstep := Inv_step base override processed_init acc k h
    have hrec := ih (processed_init ++ [k]) (stepFn override acc k) hstep
    simpa [List.append_assoc] using hrec

theorem result_Nodup {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((implementation_combineOptions base override managedKeys).map Prod.fst).Nodup := by
  intro h1 h2
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override h1 h2, ?_⟩
    intro k
    simp
  have h := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  exact h.1

theorem lookup_eq_expected {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ∀ k : String,
      optLookup (implementation_combineOptions base override managedKeys) k
        = expectedLookup base override managedKeys k := by
  intro hbase hover k
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override hbase hover, ?_⟩
    intro q
    simp
  have hfold := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  obtain ⟨_, hlook⟩ := hfold
  have hk := hlook k
  simp only [List.nil_append] at hk
  rw [hk, optLookup_mergeOpts]
  unfold expectedLookup
  cases hov : optLookup override k with
  | some v =>
    have hpres : keyPresent override k = true := by
      rw [keyPresent_iff_lookup]; exact ⟨v, hov⟩
    simp [hpres]
  | none =>
    have hpres : keyPresent override k = false := by
      cases hh : keyPresent override k with
      | false => rfl
      | true =>
        exfalso
        rw [keyPresent_iff_lookup] at hh
        obtain ⟨v, hv⟩ := hh
        rw [hov] at hv
        exact Option.noConfusion hv
    simp [hpres]

theorem correct_combineOptions :
    ∀ {V : Type} (base override : List (String × V)) (managedKeys : List String),
      (base.map Prod.fst).Nodup →
      (override.map Prod.fst).Nodup →
      problem_spec_combineOptions base override managedKeys
        (implementation_combineOptions base override managedKeys) := by
  intro V base override managedKeys hbase hoverride
  refine ⟨result_Nodup base override managedKeys hbase hoverride, ?_⟩
  exact lookup_eq_expected base override managedKeys hbase hoverride

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for all 9 attack files + positive control (spec view elides impl+proof regions; region_hashes unchanged).

POSITIVE CONTROL: atk_pos.lean (gold verbatim) -> lean_verify exit 0; #print axioms correct_combineOptions = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

GOLD RESOLVE (harness wired check): run_resolve('django__django-13786', gold_patch) -> resolved=True, completed=True, note='resolved'. F2P test_create_model_and_remove_model_options captured.

PREPATCH REPRODUCED: Solution_prepatch.lean (overlay-only, clearing loop removed) -> lean_verify exit 3 (sorry; gold proof does not close on the buggy impl). Additionally atk_reject_prepatch.lean proves ¬problem_spec for the overlay-only result at witness base=[("verbose_name","x")], override=[], managedKeys=["verbose_name"] (exit 0) — spec provably rejects the bug.

7 SAME-SPEC WRONG IMPLS, all attempted with the (fixed) gold theorem statement; command `bash scripts/lean_verify.sh <file>`:
  atk_prepatch (overlay only, no clear) -> exit 1 (Type mismatch @203)
  atk_overclear (drop all base-only keys) -> exit 1
  atk_inverted (clear managed keys override DOES mention) -> exit 1 (Type mismatch @206)
  atk_dupecho (append shadowed dup, breaks Nodup) -> exit 1 (rfl fail @204)
  atk_dropoverride (drop key unconditionally, kills override value) -> exit 1
  atk_identity (return base) -> exit 1
  atk_boundary (only clear first managed key) -> exit 1
NONE closes => step-2 (materialize faithful patch + run_resolve) is vacuous: there is no closing clean-axiom wrong impl to resolve. patches={} accordingly.

TIGHTNESS (atk_tightness.lean, exit 0): geq_no_divergence closes and depends on NO axioms. Combined with the two postcondition conjuncts (Nodup keys + optLookup pinned at every key via expectedLookup), the spec fully determines the dict observable, so verify => correct on the Nodup input domain (always true of real Python dicts).

REFINEMENT.MD AUDIT: 5 legs — R (mergeOpts overlay, return options), I (for-loop over managedKeys, `if key not in operation.options`), A-reference (dropKey <-> options.pop(key,None)). No kind-3 leg; no consumed axiom (axiom_check.py is a legitimate skip stub, opaque_callees=[], axioms=[]). A-reference correspondence confirmed: dropKey=filter(key≠·) matches pop(.,None) (both no-ops when absent); mergeOpts=override++base-minus-override-keys matches {**self.options,**operation.options} (override wins, base-only keys survive). conformance_check.py builds the Python shadow of the impl and diffs vs the REAL patched CreateModel.reduce over the F2P catalogue + 120k randomized dicts (seed 20240627) — G-CONF validates the A-reference. mapping.md base_commit bb64b99b78, models.py:139-148, ALTER_OPTION_KEYS, matches gold patch hunk.

CONCLUSION: SOUND. >=7 distinct same-spec attacks run (prepatch/overclear/inverted/dupecho/dropoverride/identity/boundary), none closes; tightness proved axiom-free; positive control verifies + gold resolves; prepatch reproduces. No verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_overclear.lean`, `atk_inverted.lean`, `atk_dupecho.lean`, `atk_dropoverride.lean`, `atk_identity.lean`, `atk_boundary.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl closes correct_combineOptions. The postcondition pins the dict observable: proved geq_no_divergence (atk_tightness.lean, exit 0, depends on NO axioms) — any two results satisfying problem_spec_combineOptions agree at optLookup for EVERY key and both have Nodup keys, hence are the identical Python dict (order-independent, no shadowed dups). So any impl that closes the proof produces gold's exact observable and resolves; no closing-but-non-resolving impl exists on the real (Nodup) input domain.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_overclear.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_dupecho.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_dropoverride.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_identity.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Collapsing two consecutive option-configuration steps into a single combined
option set.

The first step establishes an initial set of named option settings (a mapping
from option keys to their values). A second, overriding step supplies its own
set of settings that should take effect in place of the first. The combined
result is obtained by overlaying the overriding step's settings on top of the
initial ones (the overriding value wins for any key both mention, and keys only
the overriding step mentions are added).

There is, however, a designated family of *managed* keys: keys whose value is
considered to be owned entirely by the overriding step. For a managed key, the
overriding step is authoritative — if it does NOT mention that key, the key must
be cleared from the combined result, even when the initial step had set it.
Keys outside the managed family are left untouched when the overriding step is
silent about them.

The behavior is stated abstractly as an input→output relation on the combined
option set; the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the combination is
-- spelled out concretely (an overlay of two key→value mappings followed by the
-- clearing of any managed key the overriding mapping is silent about).
-- axioms-end

-- pure-start
/-- Is key `k` present in the key→value mapping `d`? -/
def keyPresent {V : Type} (d : List (String × V)) (k : String) : Bool :=
  d.any (fun p => p.1 == k)

/-- Look up key `k` in `d`, returning the value of the first entry with that key
(`none` if absent). A mapping is read as a dictionary: first match wins. -/
def optLookup {V : Type} (d : List (String × V)) (k : String) : Option V :=
  (d.find? (fun p => p.1 == k)).map (·.2)

/-- Overlay `override` on top of `base`: keep every overriding entry, and keep
each base entry whose key the overriding mapping does not mention. -/
def mergeOpts {V : Type} (base override : List (String × V)) : List (String × V) :=
  override ++ base.filter (fun p => ! keyPresent override p.1)

/-- Remove every entry whose key equals `k`. -/
def dropKey {V : Type} (d : List (String × V)) (k : String) : List (String × V) :=
  d.filter (fun p => p.1 != k)

/-- The value the combined mapping should hold at key `k`:
* if the overriding mapping mentions `k`, its value wins;
* otherwise, if `k` is a managed key, it is cleared (`none`);
* otherwise the base value (if any) survives. -/
def expectedLookup {V : Type} (base override : List (String × V))
    (managedKeys : List String) (k : String) : Option V :=
  match optLookup override k with
  | some v => some v
  | none   => if managedKeys.contains k then none else optLookup base k
-- pure-end

-- post-conditions-start
/-- The combined mapping is a genuine dictionary (its keys are distinct) and
agrees, at every key, with the desired overlay-then-clear-managed behavior. The
key-distinctness conjunct rules out a result that merely shares the right
first-match lookups while hiding shadowed duplicate keys (a Python `dict` has no
duplicate keys); together the two clauses pin the resulting dictionary exactly. -/
def problem_spec_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String)
    (result : List (String × V)) : Prop :=
  (result.map Prod.fst).Nodup ∧
  (∀ k : String, optLookup result k = expectedLookup base override managedKeys k)
-- post-conditions-end

-- impl-start
def implementation_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String) :
    List (String × V) := Id.run do
  let mut options := mergeOpts base override
  for key in managedKeys do
    if ! keyPresent override key then
      options := dropKey options key
  return options
-- impl-end


-- proof-start
/-- The loop's initial accumulator: the overlay of `override` on `base`. -/
def options0 {V : Type} (base override : List (String × V)) : List (String × V) :=
  mergeOpts base override

/-- The pure loop-step: drop `key` from the accumulator iff `override` is silent
about it. -/
def stepFn {V : Type} (override : List (String × V))
    (acc : List (String × V)) (key : String) : List (String × V) :=
  if ! keyPresent override key then dropKey acc key else acc

/-- Fold-level invariant: the accumulator has distinct keys, and its lookup at
every key agrees with the initial overlay except that keys already processed and
not mentioned by `override` read as `none`. -/
def CombineInv {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) : Prop :=
  (acc.map Prod.fst).Nodup ∧
  (∀ k : String,
    optLookup acc k =
      (if processed.contains k && ! keyPresent override k then none
       else optLookup (mergeOpts base override) k))

theorem keyPresent_iff_lookup {V : Type} (d : List (String × V)) (k : String) :
    keyPresent d k = true ↔ ∃ v, optLookup d k = some v := by
  simp only [keyPresent, optLookup, ← Option.isSome_iff_exists, Option.isSome_map,
    List.find?_isSome, List.any_eq_true]

theorem optLookup_dropKey_eq {V : Type} (d : List (String × V)) (k q : String) :
    optLookup (dropKey d k) q = if q = k then none else optLookup d q := by
  simp only [optLookup, dropKey]
  induction d with
  | nil => simp
  | cons p ds ih =>
    rw [List.filter_cons]
    by_cases hpk : (p.1 != k) = true
    · rw [if_pos hpk, List.find?_cons, List.find?_cons]
      by_cases hpq : (p.1 == q) = true
      · rw [hpq]
        simp only [beq_iff_eq] at hpq
        subst hpq
        simp only [bne_iff_ne, ne_eq] at hpk
        rw [if_neg hpk]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]
    · rw [if_neg hpk, List.find?_cons]
      simp only [bne_iff_ne, ne_eq, Decidable.not_not] at hpk
      by_cases hpq : (p.1 == q) = true
      · simp only [beq_iff_eq] at hpq
        subst hpk
        rw [if_pos hpq.symm, ih, if_pos hpq.symm]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]

theorem map_fst_dropKey_Nodup {V : Type} (d : List (String × V)) (k : String) :
    (d.map Prod.fst).Nodup → ((dropKey d k).map Prod.fst).Nodup := by
  intro h
  unfold dropKey
  exact List.Nodup.sublist (List.filter_sublist.map Prod.fst) h

theorem optLookup_mergeOpts {V : Type} (base override : List (String × V)) (k : String) :
    optLookup (mergeOpts base override) k =
      (match optLookup override k with
       | some v => some v
       | none   => optLookup base k) := by
  unfold optLookup mergeOpts
  rw [List.find?_append]
  cases h : (override.find? (fun p => p.1 == k)) with
  | some pair => simp
  | none =>
    have hp : keyPresent override k = false := by
      have hiff := keyPresent_iff_lookup override k
      simp only [optLookup, h, Option.map_none] at hiff
      by_contra hc
      simp only [Bool.not_eq_false] at hc
      obtain ⟨v, hv⟩ := hiff.mp hc
      exact Option.noConfusion hv
    simp only [Option.none_or, Option.map_none]
    rw [List.find?_filter]
    have hpred : (fun a : String × V => decide ((!keyPresent override a.1) = true ∧ (a.1 == k) = true))
        = (fun p : String × V => p.1 == k) := by
      funext a
      by_cases hak : (a.1 == k) = true
      · have he : a.1 = k := by simpa using hak
        subst he
        simp [hp]
      · simp only [Bool.not_eq_true] at hak
        simp [hak]
    rw [hpred]

theorem options0_Nodup {V : Type} (base override : List (String × V)) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((mergeOpts base override).map Prod.fst).Nodup := by
  intro hbase hoverride
  unfold mergeOpts
  rw [List.map_append, List.nodup_append]
  refine ⟨hoverride, (List.filter_sublist.map Prod.fst).nodup hbase, ?_⟩
  intro a ha b hb hab
  subst hab
  obtain ⟨q, hq_mem, hq_eq⟩ := List.mem_map.mp ha
  obtain ⟨p, hp_filter, hp_eq⟩ := List.mem_map.mp hb
  rw [List.mem_filter] at hp_filter
  obtain ⟨_, hpP⟩ := hp_filter
  have hpres : keyPresent override a = true := by
    unfold keyPresent
    rw [List.any_eq_true]
    exact ⟨q, hq_mem, by simp [hq_eq]⟩
  rw [hp_eq, hpres] at hpP
  simp at hpP

theorem loop_is_foldl {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    implementation_combineOptions base override managedKeys =
      List.foldl (stepFn override) (mergeOpts base override) managedKeys := by
  simp only [implementation_combineOptions, Id.run]
  generalize mergeOpts base override = init
  induction managedKeys generalizing init with
  | nil => rfl
  | cons k ks ih =>
    simp only [List.forIn_cons, List.foldl_cons, stepFn]
    split <;> exact ih _

theorem Inv_step {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) (key : String) :
    CombineInv base override processed acc →
    CombineInv base override (processed ++ [key]) (stepFn override acc key) := by
  intro h
  obtain ⟨hnodup, hlook⟩ := h
  unfold stepFn
  by_cases hk : keyPresent override key = true
  · -- override mentions key: stepFn = acc
    simp only [hk, Bool.not_true, Bool.false_eq_true, if_false]
    refine ⟨hnodup, fun k => ?_⟩
    rw [hlook k]
    by_cases hkk : k = key
    · subst hkk
      simp [hk]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]
  · -- override silent about key: stepFn = dropKey acc key
    have hkf : keyPresent override key = false := by
      simpa using hk
    simp only [hkf, Bool.not_false, if_true]
    refine ⟨map_fst_dropKey_Nodup acc key hnodup, fun k => ?_⟩
    rw [optLookup_dropKey_eq acc key k, hlook k]
    by_cases hkk : k = key
    · subst hkk
      rw [List.contains_append, List.contains_cons]
      simp [hkf]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]

theorem foldl_preserves_Inv {V : Type} (base override : List (String × V))
    (processed_init : List String) (acc : List (String × V)) :
    CombineInv base override processed_init acc →
    ∀ (ks : List String),
      CombineInv base override (processed_init ++ ks)
        (List.foldl (stepFn override) acc ks) := by
  intro h ks
  induction ks generalizing processed_init acc with
  | nil => simpa using h
  | cons k rest ih =>
    have hstep := Inv_step base override processed_init acc k h
    have hrec := ih (processed_init ++ [k]) (stepFn override acc k) hstep
    simpa [List.append_assoc] using hrec

theorem result_Nodup {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((implementation_combineOptions base override managedKeys).map Prod.fst).Nodup := by
  intro h1 h2
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override h1 h2, ?_⟩
    intro k
    simp
  have h := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  exact h.1

theorem lookup_eq_expected {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ∀ k : String,
      optLookup (implementation_combineOptions base override managedKeys) k
        = expectedLookup base override managedKeys k := by
  intro hbase hover k
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override hbase hover, ?_⟩
    intro q
    simp
  have hfold := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  obtain ⟨_, hlook⟩ := hfold
  have hk := hlook k
  simp only [List.nil_append] at hk
  rw [hk, optLookup_mergeOpts]
  unfold expectedLookup
  cases hov : optLookup override k with
  | some v =>
    have hpres : keyPresent override k = true := by
      rw [keyPresent_iff_lookup]; exact ⟨v, hov⟩
    simp [hpres]
  | none =>
    have hpres : keyPresent override k = false := by
      cases hh : keyPresent override k with
      | false => rfl
      | true =>
        exfalso
        rw [keyPresent_iff_lookup] at hh
        obtain ⟨v, hv⟩ := hh
        rw [hov] at hv
        exact Option.noConfusion hv
    simp [hpres]

theorem correct_combineOptions :
    ∀ {V : Type} (base override : List (String × V)) (managedKeys : List String),
      (base.map Prod.fst).Nodup →
      (override.map Prod.fst).Nodup →
      problem_spec_combineOptions base override managedKeys
        (implementation_combineOptions base override managedKeys) := by
  intro V base override managedKeys hbase hoverride
  refine ⟨result_Nodup base override managedKeys hbase hoverride, ?_⟩
  exact lookup_eq_expected base override managedKeys hbase hoverride

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for all 9 attack files + positive control (spec view elides impl+proof regions; region_hashes unchanged).

POSITIVE CONTROL: atk_pos.lean (gold verbatim) -> lean_verify exit 0; #print axioms correct_combineOptions = [propext, Classical.choice, Quot.sound] (clean, no sorryAx).

GOLD RESOLVE (harness wired check): run_resolve('django__django-13786', gold_patch) -> resolved=True, completed=True, note='resolved'. F2P test_create_model_and_remove_model_options captured.

PREPATCH REPRODUCED: Solution_prepatch.lean (overlay-only, clearing loop removed) -> lean_verify exit 3 (sorry; gold proof does not close on the buggy impl). Additionally atk_reject_prepatch.lean proves ¬problem_spec for the overlay-only result at witness base=[("verbose_name","x")], override=[], managedKeys=["verbose_name"] (exit 0) — spec provably rejects the bug.

7 SAME-SPEC WRONG IMPLS, all attempted with the (fixed) gold theorem statement; command `bash scripts/lean_verify.sh <file>`:
  atk_prepatch (overlay only, no clear) -> exit 1 (Type mismatch @203)
  atk_overclear (drop all base-only keys) -> exit 1
  atk_inverted (clear managed keys override DOES mention) -> exit 1 (Type mismatch @206)
  atk_dupecho (append shadowed dup, breaks Nodup) -> exit 1 (rfl fail @204)
  atk_dropoverride (drop key unconditionally, kills override value) -> exit 1
  atk_identity (return base) -> exit 1
  atk_boundary (only clear first managed key) -> exit 1
NONE closes => step-2 (materialize faithful patch + run_resolve) is vacuous: there is no closing clean-axiom wrong impl to resolve. patches={} accordingly.

TIGHTNESS (atk_tightness.lean, exit 0): geq_no_divergence closes and depends on NO axioms. Combined with the two postcondition conjuncts (Nodup keys + optLookup pinned at every key via expectedLookup), the spec fully determines the dict observable, so verify => correct on the Nodup input domain (always true of real Python dicts).

REFINEMENT.MD AUDIT: 5 legs — R (mergeOpts overlay, return options), I (for-loop over managedKeys, `if key not in operation.options`), A-reference (dropKey <-> options.pop(key,None)). No kind-3 leg; no consumed axiom (axiom_check.py is a legitimate skip stub, opaque_callees=[], axioms=[]). A-reference correspondence confirmed: dropKey=filter(key≠·) matches pop(.,None) (both no-ops when absent); mergeOpts=override++base-minus-override-keys matches {**self.options,**operation.options} (override wins, base-only keys survive). conformance_check.py builds the Python shadow of the impl and diffs vs the REAL patched CreateModel.reduce over the F2P catalogue + 120k randomized dicts (seed 20240627) — G-CONF validates the A-reference. mapping.md base_commit bb64b99b78, models.py:139-148, ALTER_OPTION_KEYS, matches gold patch hunk.

CONCLUSION: SOUND. >=7 distinct same-spec attacks run (prepatch/overclear/inverted/dupecho/dropoverride/identity/boundary), none closes; tightness proved axiom-free; positive control verifies + gold resolves; prepatch reproduces. No verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the lean backend — the graded spec region (axioms/pure/post-conditions) is byte-identical, so the modeled function's spec is stable across the patch. (2) Solution.lean compiles under lean_verify.sh (exit 0) and `#print axioms correct_combineOptions` yields only [propext, Classical.choice, Quot.sound] — no sorryAx, the correctness proof is genuine. (3) The Lean model expectedLookup encodes exactly the post-patch CreateModel.reduce AlterModelOptions branch (django/db/migrations/operations/models.py): options={**self.options,**operation.options} then for key in ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key,None). Three-way behavior matches: override-mentioned key -> override value; managed key omitted by override -> cleared (none); non-managed omitted key -> base value survives. The Nodup precondition faithfully mirrors Python dict key-distinctness (not an over-strong artificial constraint). (4) Ran the bundle's conformance_check.py against the REAL patched callee at base_commit worktree: 120031 checks, 0 disagreements, status=pass. No input distinguishes the modeled function from the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) passes with zero hard failures over the projected spec view; same_spec(Solution, Solution_prepatch)=True so the audited spec region is byte-identical.

Spec-view leakage analysis vs PUBLIC problem_statement only (hints_text excluded):
- The public problem_statement already discloses the overlay `{**self.options, **operation.options}`, that options are not cleared, and the intended fix: 'remove options not found in operation.options as is found in AlterModelOptions.state_forwards()'. So the clearing-of-omitted-keys behavior is public.
- hints_text (which names ALTER_OPTION_KEYS explicitly) is correctly NOT the leakage baseline; the spec must not exceed problem_statement.
- The spec view is fully abstracted: 'option-configuration steps', 'overriding step', and a 'designated family of managed keys' whose value is owned by the overriding step and cleared when the override is silent. It contains NO repo-identifying tokens: no CreateModel/AlterModelOptions/reduce/ALTER_OPTION_KEYS/squashmigrations, no file path (django/db/migrations/operations/models.py), no diff markers, no bug/fix/regression narration.
- The docstring/comments describe the input->output relation abstractly and explicitly defer impl and proof ('supplied separately'), so no gold line or edit-localizing symbol is reproduced.
- The 'managed keys / cleared when override silent' idea is an abstraction of the state_forwards clearing the public problem_statement already points to; it does not reconstruct the gold edit beyond what the solver-visible task already reveals.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
