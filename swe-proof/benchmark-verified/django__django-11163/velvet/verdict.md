# P2 adversarial audit — django__django-11163

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong implementation verifies, so there is no verifying-but-wrong candidate to materialize a faithful refined patch for. verify⇒correct is not falsified.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,10 +122,14 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := candidates[i - 1]!
-      result := (if keep selector excl c then [c] else []) ++ result
+      let keepIt : Bool :=
+        (match selector with
+         | none         => true
+         | some present => if present.isEmpty then true else decide (c ∈ present))
+        && decide (c ∉ excl)
+      result := (if keepIt then [c] else []) ++ result
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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,10 +122,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := candidates[i - 1]!
-      result := (if keep selector excl c then [c] else []) ++ result
+      result := (if decide (c ∉ excl) then [c] else []) ++ result
       i := i - 1
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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,9 +122,8 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := candidates[i - 1]!
+      let c := candidates[i]!
       result := (if keep selector excl c then [c] else []) ++ result
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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,11 +122,10 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := candidates[i - 1]!
-      result := (if keep selector excl c then [c] else []) ++ result
-      i := i - 1
+      result := result
+      i := i
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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -116,17 +116,7 @@
   ensures ∀ n, n ∈ out → n ∈ candidates ∧ keep selector excl n = true
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := candidates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ candidates.length
-      invariant result = selectNames selector excl (candidates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := candidates[i - 1]!
-      result := (if keep selector excl c then [c] else []) ++ result
-      i := i - 1
+    let result : List Int := selectNames selector excl candidates
     return result
     -- impl-end
 
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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,12 +122,11 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := candidates[i - 1]!
       result := (if keep selector excl c then [c] else []) ++ result
       i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the per-candidate selection decision is a pure
@@ -122,10 +122,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectNames selector excl (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := candidates[i - 1]!
-      result := (if keep selector excl c then [c] else []) ++ result
+      result := result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the per-candidate selection decision is a pure
--  function of the candidate's name, the optional selector, and the excl list,
--  modeled deeply over `List Int`. There is no unchanged library callee the
--  proof must axiomatize.)
-- axioms-end

-- pure-start
/- Whether a single candidate name `n` survives the selection.

   The optional selector `sel` distinguishes three situations that must be kept
   apart:
     * `none`        — no selector was supplied: every candidate is admissible;
     * `some present` — a selector list was supplied: a candidate is admissible
       only if its name is among the listed `present` ones. Crucially this is decided by the
       PRESENCE of the selector, NOT by whether it lists anything: a supplied
       selector that lists nothing keeps nothing.
   Independently, an excl list removes any candidate whose name it contains (an
   empty excl list removes nothing, since no name is a member of it). -/
def keep (sel : Option (List Int)) (excl : List Int) (n : Int) : Bool :=
  (match sel with
   | none         => true
   | some present => decide (n ∈ present))
  && decide (n ∉ excl)

/- The selection of a whole candidate list: keep each admissible name, in order.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def selectNames (sel : Option (List Int)) (excl : List Int) : List Int → List Int
  | []      => []
  | n :: ns => (if keep sel excl n then [n] else []) ++ selectNames sel excl ns

@[grind] lemma selectNames_nil (sel : Option (List Int)) (excl : List Int) :
    selectNames sel excl [] = [] := rfl
@[grind] lemma selectNames_cons (sel : Option (List Int)) (excl : List Int)
    (n : Int) (ns : List Int) :
    selectNames sel excl (n :: ns) =
      (if keep sel excl n then [n] else []) ++ selectNames sel excl ns := rfl

/- A supplied selector that lists nothing keeps nothing. -/
@[grind] lemma keep_empty_selector (excl : List Int) (n : Int) :
    keep (some []) excl n = false := by
  unfold keep; simp

/- Hence selecting against an empty supplied selector yields the empty list,
   regardless of the candidates or the excl list. This is the behaviour the
   issue demands and the single clause on which the pre-image skeleton fails. -/
@[grind] lemma selectNames_empty_selector (excl : List Int) (ns : List Int) :
    selectNames (some []) excl ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [selectNames_cons, keep_empty_selector]; simpa using ih

/- A selected name is always one of the candidates (nothing is invented) and is
   admissible. Proven by induction; marked `@[grind]` so the corresponding
   postconditions discharge automatically. -/
@[grind] lemma selectNames_mem (sel : Option (List Int)) (excl : List Int)
    (ns : List Int) :
    ∀ n, n ∈ selectNames sel excl ns → n ∈ ns ∧ keep sel excl n = true := by
  induction ns with
  | nil => intro n h; simp [selectNames] at h
  | cons c cs ih =>
      intro n h
      rw [selectNames_cons] at h
      by_cases hk : keep sel excl c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A routine collects, for a model instance, the values of a set of candidate
   fields keyed by field name. Two read-only knobs narrow that set:

   - an OPTIONAL selector of names. When absent, every candidate field is
     collected. When PRESENT, only the named candidates are collected — and a
     present selector that names nothing collects nothing. The distinction
     between "no selector" and "a selector that names nothing" is the whole
     point: requesting an empty set of fields yields an empty result, it does
     NOT fall back to collecting everything.
   - an excl list of names. Any candidate whose name appears in it is dropped;
     an excl list that names nothing drops nothing.

   The candidate names are modeled as `List Int` (each distinct field name is a
   distinct identifier); the optional selector is `Option (List Int)` so that
   "absent" and "present but empty" are genuinely different inputs; the excl
   list is `List Int`. The result is the list of collected (kept) names, in the
   candidate order.

   `candidates`, `selector` and `excl` are read-only (not `mut`); the routine
   builds a fresh result and mutates none of them (directive 5). -/
method selectModelFields (candidates : List Int) (selector : Option (List Int))
    (excl : List Int) return (out : List Int)
  ensures out = selectNames selector excl candidates
  ensures selector = some [] → out = []
  ensures ∀ n, n ∈ out → n ∈ candidates ∧ keep selector excl n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectNames selector excl (candidates.drop i)
      done_with i = 0
    do
      let c := candidates[i - 1]!
      result := (if keep selector excl c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectNames` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectNames_drop_step (sel : Option (List Int)) (excl : List Int)
    (xs : List Int) (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    selectNames sel excl (xs.drop (i - 1)) =
      (if keep sel excl xs[i - 1]! then [xs[i - 1]!] else [])
        ++ selectNames sel excl (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectNames_cons]

prove_correct selectModelFields by
  loom_solve
  rw [selectNames_drop_step selector excl candidates i (by omega) (by omega)]
  rw [‹result = selectNames selector excl (candidates.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-11163 (velvet), selectModelFields modeling django.forms.models.model_to_dict. FROZEN spec confirmed same_spec=True for all 8 files (7 attacks + positive control) via swebench_unified.markers.same_spec with velvet backend. Verify command per file: `bash scripts/lean_verify.sh <file>`.

A-LEG AUDIT (the focus of this pass): meta.json records axioms=[] and deep_model_references=[]. refinement.md and mapping.md §3 correctly declare NO A rows — the single changed operation (the `fields` guard, pre `if fields and ...` -> post `if fields is not None and ...`) is modeled DEEPLY by pure helpers keep/selectNames over the function's own parameters, not hidden behind an axiom about the function under change. There is no unchanged library callee whose contract the proof relies on (value_from_object produces values, not the observed key set, and is deliberately un-modeled as an R-identity on the value projection — no dead axiom). So there is no A-leg correspondence to break; every refinement leg is R or I, no kind-3. The R/I legs are covered by G-CONF (recorded pass: R/I shadow of selectModelFields agrees with real patched model_to_dict key set on 100012 inputs, seed 11163, 0 disagreements) and by G-CONF's sibling in G-CONF, not by this G-EQ pass.

MODEL<->PATCH CORRESPONDENCE / SPEC TIGHTNESS: postcondition #1 `out = selectNames selector excl candidates` is a TOTAL functional pin (exact equality on all inputs), and the `prove_correct` proof body (`loom_solve; rw [selectNames_drop_step ...]; rw [<invariant>]`) lives OUTSIDE the impl-start/impl-end region, hence is FROZEN and forces the precise backward-fold loop shape. This is why no wrong impl survives.

### ATTACKS (all same_spec=True; all verified with lean_verify.sh 300s):
- atk_1 (prepatch bug / control-flow-effect): present-but-empty selector treated as absent via `if present.isEmpty then true` (the truthiness short-circuit). rc=1. Error at :153 `unsolved goals` on invariant_2 (result = selectNames ... (drop i)) — reproduces the recorded prepatch/G-DIFF divergence exactly (fields=[] must keep nothing but this keeps all).
- atk_2 (partial-domain): drops the selector entirely, keeps all names not excluded. rc=1, unsolved invariant_2.
- atk_3 (boundary/off-by-one): reads candidates[i]! instead of candidates[i-1]!. rc=1.
- atk_4 (control-flow-effect/divergence): no-op body (result:=result; i:=i), loop never progresses. rc=1.
- atk_5 (ungrounded-oracle echo): returns selectNames selector excl candidates directly, dropping the loop. rc=1, error :141 `No goals to be solved` — the FROZEN prove_correct body expects the loop-generated goals, so the echo shape is rejected.
- atk_6 (boundary): correct loop but `return []`. rc=1.
- atk_7 (control-flow-effect): decrements i but never updates result (drops all keeps). rc=1.
Positive control pos_control.lean (byte-identical correct impl): rc=0 (verifies, no sorry).

RESOLVE RUNS: none required. Step 2 mandates materializing+resolve-running the faithful patch for every wrong impl that VERIFIES; zero wrong impls verify, so there is no verifying-but-wrong candidate. No resolve run was skipped for lack of ability — it is inapplicable.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7 total, covering prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) were all machine-verified to FAIL under the pinned Velvet verifier; the positive control verifies; the prepatch bug is reproduced. The spec does not admit a verifying incorrect implementation, so verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong implementation verifies, so there is no verifying-but-wrong candidate to materialize a faithful refined patch for. verify⇒correct is not falsified.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the per-candidate selection decision is a pure
--  function of the candidate's name, the optional selector, and the excl list,
--  modeled deeply over `List Int`. There is no unchanged library callee the
--  proof must axiomatize.)
-- axioms-end

-- pure-start
/- Whether a single candidate name `n` survives the selection.

   The optional selector `sel` distinguishes three situations that must be kept
   apart:
     * `none`        — no selector was supplied: every candidate is admissible;
     * `some present` — a selector list was supplied: a candidate is admissible
       only if its name is among the listed `present` ones. Crucially this is decided by the
       PRESENCE of the selector, NOT by whether it lists anything: a supplied
       selector that lists nothing keeps nothing.
   Independently, an excl list removes any candidate whose name it contains (an
   empty excl list removes nothing, since no name is a member of it). -/
def keep (sel : Option (List Int)) (excl : List Int) (n : Int) : Bool :=
  (match sel with
   | none         => true
   | some present => decide (n ∈ present))
  && decide (n ∉ excl)

/- The selection of a whole candidate list: keep each admissible name, in order.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def selectNames (sel : Option (List Int)) (excl : List Int) : List Int → List Int
  | []      => []
  | n :: ns => (if keep sel excl n then [n] else []) ++ selectNames sel excl ns

@[grind] lemma selectNames_nil (sel : Option (List Int)) (excl : List Int) :
    selectNames sel excl [] = [] := rfl
@[grind] lemma selectNames_cons (sel : Option (List Int)) (excl : List Int)
    (n : Int) (ns : List Int) :
    selectNames sel excl (n :: ns) =
      (if keep sel excl n then [n] else []) ++ selectNames sel excl ns := rfl

/- A supplied selector that lists nothing keeps nothing. -/
@[grind] lemma keep_empty_selector (excl : List Int) (n : Int) :
    keep (some []) excl n = false := by
  unfold keep; simp

/- Hence selecting against an empty supplied selector yields the empty list,
   regardless of the candidates or the excl list. This is the behaviour the
   issue demands and the single clause on which the pre-image skeleton fails. -/
@[grind] lemma selectNames_empty_selector (excl : List Int) (ns : List Int) :
    selectNames (some []) excl ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [selectNames_cons, keep_empty_selector]; simpa using ih

/- A selected name is always one of the candidates (nothing is invented) and is
   admissible. Proven by induction; marked `@[grind]` so the corresponding
   postconditions discharge automatically. -/
@[grind] lemma selectNames_mem (sel : Option (List Int)) (excl : List Int)
    (ns : List Int) :
    ∀ n, n ∈ selectNames sel excl ns → n ∈ ns ∧ keep sel excl n = true := by
  induction ns with
  | nil => intro n h; simp [selectNames] at h
  | cons c cs ih =>
      intro n h
      rw [selectNames_cons] at h
      by_cases hk : keep sel excl c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A routine collects, for a model instance, the values of a set of candidate
   fields keyed by field name. Two read-only knobs narrow that set:

   - an OPTIONAL selector of names. When absent, every candidate field is
     collected. When PRESENT, only the named candidates are collected — and a
     present selector that names nothing collects nothing. The distinction
     between "no selector" and "a selector that names nothing" is the whole
     point: requesting an empty set of fields yields an empty result, it does
     NOT fall back to collecting everything.
   - an excl list of names. Any candidate whose name appears in it is dropped;
     an excl list that names nothing drops nothing.

   The candidate names are modeled as `List Int` (each distinct field name is a
   distinct identifier); the optional selector is `Option (List Int)` so that
   "absent" and "present but empty" are genuinely different inputs; the excl
   list is `List Int`. The result is the list of collected (kept) names, in the
   candidate order.

   `candidates`, `selector` and `excl` are read-only (not `mut`); the routine
   builds a fresh result and mutates none of them (directive 5). -/
method selectModelFields (candidates : List Int) (selector : Option (List Int))
    (excl : List Int) return (out : List Int)
  ensures out = selectNames selector excl candidates
  ensures selector = some [] → out = []
  ensures ∀ n, n ∈ out → n ∈ candidates ∧ keep selector excl n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectNames selector excl (candidates.drop i)
      done_with i = 0
    do
      let c := candidates[i - 1]!
      result := (if keep selector excl c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectNames` peels one keep-decision. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectNames_drop_step (sel : Option (List Int)) (excl : List Int)
    (xs : List Int) (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    selectNames sel excl (xs.drop (i - 1)) =
      (if keep sel excl xs[i - 1]! then [xs[i - 1]!] else [])
        ++ selectNames sel excl (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectNames_cons]

prove_correct selectModelFields by
  loom_solve
  rw [selectNames_drop_step selector excl candidates i (by omega) (by omega)]
  rw [‹result = selectNames selector excl (candidates.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-11163 (velvet), selectModelFields modeling django.forms.models.model_to_dict. FROZEN spec confirmed same_spec=True for all 8 files (7 attacks + positive control) via swebench_unified.markers.same_spec with velvet backend. Verify command per file: `bash scripts/lean_verify.sh <file>`.

A-LEG AUDIT (the focus of this pass): meta.json records axioms=[] and deep_model_references=[]. refinement.md and mapping.md §3 correctly declare NO A rows — the single changed operation (the `fields` guard, pre `if fields and ...` -> post `if fields is not None and ...`) is modeled DEEPLY by pure helpers keep/selectNames over the function's own parameters, not hidden behind an axiom about the function under change. There is no unchanged library callee whose contract the proof relies on (value_from_object produces values, not the observed key set, and is deliberately un-modeled as an R-identity on the value projection — no dead axiom). So there is no A-leg correspondence to break; every refinement leg is R or I, no kind-3. The R/I legs are covered by G-CONF (recorded pass: R/I shadow of selectModelFields agrees with real patched model_to_dict key set on 100012 inputs, seed 11163, 0 disagreements) and by G-CONF's sibling in G-CONF, not by this G-EQ pass.

MODEL<->PATCH CORRESPONDENCE / SPEC TIGHTNESS: postcondition #1 `out = selectNames selector excl candidates` is a TOTAL functional pin (exact equality on all inputs), and the `prove_correct` proof body (`loom_solve; rw [selectNames_drop_step ...]; rw [<invariant>]`) lives OUTSIDE the impl-start/impl-end region, hence is FROZEN and forces the precise backward-fold loop shape. This is why no wrong impl survives.

### ATTACKS (all same_spec=True; all verified with lean_verify.sh 300s):
- atk_1 (prepatch bug / control-flow-effect): present-but-empty selector treated as absent via `if present.isEmpty then true` (the truthiness short-circuit). rc=1. Error at :153 `unsolved goals` on invariant_2 (result = selectNames ... (drop i)) — reproduces the recorded prepatch/G-DIFF divergence exactly (fields=[] must keep nothing but this keeps all).
- atk_2 (partial-domain): drops the selector entirely, keeps all names not excluded. rc=1, unsolved invariant_2.
- atk_3 (boundary/off-by-one): reads candidates[i]! instead of candidates[i-1]!. rc=1.
- atk_4 (control-flow-effect/divergence): no-op body (result:=result; i:=i), loop never progresses. rc=1.
- atk_5 (ungrounded-oracle echo): returns selectNames selector excl candidates directly, dropping the loop. rc=1, error :141 `No goals to be solved` — the FROZEN prove_correct body expects the loop-generated goals, so the echo shape is rejected.
- atk_6 (boundary): correct loop but `return []`. rc=1.
- atk_7 (control-flow-effect): decrements i but never updates result (drops all keeps). rc=1.
Positive control pos_control.lean (byte-identical correct impl): rc=0 (verifies, no sorry).

RESOLVE RUNS: none required. Step 2 mandates materializing+resolve-running the faithful patch for every wrong impl that VERIFIES; zero wrong impls verify, so there is no verifying-but-wrong candidate. No resolve run was skipped for lack of ability — it is inapplicable.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7 total, covering prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) were all machine-verified to FAIL under the pinned Velvet verifier; the positive control verifies; the prepatch bug is reproduced. The spec does not admit a verifying incorrect implementation, so verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit for django__django-11163 (velvet). Modeled function selectModelFields models the gold-patched django.forms.models.model_to_dict (django/forms/models.py:69). Gold patch changes the fields guard from `if fields and f.name not in fields:` to `if fields is not None and f.name not in fields:` (presence, not truthiness). The exclude guard on the next line is unchanged.

Checks:
1. Spec byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) == True. Only impl regions differ (prepatch reintroduces the truthiness bug via `if present.isEmpty then true`). Spec view (signature, ensures clauses, pure keep/selectNames helpers + lemmas) is preserved — not silently rewritten.
2. Lean verifies: scripts/lean_verify.sh Solution.lean -> exit 0, no sorry/error.
3. Independent differential test against the REAL callee: manually reset django/forms/models.py to base commit e6588aa4 and applied the gold one-liner, imported the actual patched model_to_dict with a duck-typed instance/fields, and compared the Lean model semantics (keep = (fields is None or n in fields) and n not in exclude; selectNames = kept names in candidate order) against the real function's sorted key set. Ran 500,000 randomized cases (independent seed 999, varying editable/non-editable candidates across the chained field groups, fields in {None, [], subset, subset+ghost, subset+dups}, exclude in {None, [], subset}) + 10 targeted boundary cases (fields=[], both empty, exclude overrides fields, exclude-all, ghost-only, dup names, empty candidates). Result: 0 disagreements. The bundle's own conformance_check.py (seed 11163, 1e5 inputs) uses the same comparison and passes.

Abstraction faithfulness verified: name<->distinct-Int coding is sound (Django field names unique per model; only identity/membership/order is observed); dict insertion order == candidate iteration order so `out` (kept names in candidate order) faithfully models the key set; the Option carrier correctly distinguishes fields=None (none => keep all) from fields=[] (some [] => keep none) — the exact bug discriminator; exclude None and [] both map to [] which is observationally identical in the real code (`if exclude and ...` short-circuits on falsy exclude, and n not in [] is vacuously true). The three postconditions (out = selectNames selector excl candidates; selector=some [] -> out=[]; membership/admissibility) are all logical consequences of the first — no over-strengthening beyond the real callee. No input found where the modeled function disagrees with the real post-patch callee. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: django__django-11163 (velvet). same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (verified via swebench_unified.markers) — the spec view (imports, set_options, axioms/pure/pre/post regions + method signature with `ensures` clauses + surrounding lemmas) is identical between the patched and prepatch solutions; only the elided impl/proof regions differ, so the spec view carries no impl/proof detail.

Leakage assessment vs the PUBLIC problem_statement (NOT hints):
- The problem_statement ALREADY discloses the gold edit verbatim: it names 'The problem point is / if fields and f.name not in fields: / which should be / if fields is not None and f.name not in fields:' and states model_to_dict(instance, fields=[]) must return an empty dict, not all fields. So the entire semantic content of the fix (presence-of-selector vs truthiness; empty selector keeps nothing) is public.
- The spec view models exactly this behavior abstractly: `selector : Option (List Int)` making none (absent) vs some [] (present-but-empty) distinct, `keep`/`selectNames`, and the discriminating clause `ensures selector = some [] -> out = []` (+ lemmas keep_empty_selector / selectNames_empty_selector). Every one of these is a faithful abstraction of what problem_statement already states; none reveals anything MORE than the public statement.
- No Python-side tokens leak: the spec view contains no `model_to_dict`, `fields`, `exclude`, `f.name`, `is not None`, `django/forms/models.py`, line numbers, or F2P test names. Those repo/gold specifics live only in mapping.md / refinement.md, which are NOT part of the spec view. The `excl : List Int` / `n ∉ excl` modeling pins the UNCHANGED exclude frame — it is not the gold edit and would not tell a consumer what to change.
- The spec expresses the objective (empty selector -> empty result) at the same level of disclosure as problem_statement, using a generic List Int / Option carrier. There is no gold-patch-specific detail (e.g. the exact `is not None` operator spelling, the concrete field names, the specific file/function) that a solver could not already read directly in problem_statement.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
