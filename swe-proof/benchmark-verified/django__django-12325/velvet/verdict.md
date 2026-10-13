# P2 adversarial audit — django__django-12325

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Only atk_8 (the ungrounded-oracle echo: `return (collectLinks refs)`) verified; it is behaviorally identical to the gold and its faithful refined patch (= the gold patch) RESOLVED under the official harness (run_resolve: RESOLVED=True, COMPLETED=True, not flaky, 1 attempt). No verifying wrong impl produced a non-resolving patch, so verify⇒correct holds.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,17 +120,8 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
-    let mut result : LinkMap := (fun _ => none)
-    let mut i := 0
-    while i < refs.length
-      invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
-      done_with i = refs.length
-      decreasing refs.length - i
-    do
-      let f := refs[i]!
-      result := selectRef result f
-      i := i + 1
+    -- WRONG: never record anything; return the empty selection.
+    let result : LinkMap := (fun _ => none)
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,16 +120,15 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: negated identity-link guard; keeps plain refs, drops links.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
       done_with i = refs.length
-      decreasing refs.length - i
     do
       let f := refs[i]!
-      result := selectRef result f
+      result := (if !f.isLink then (fun k => if k = f.target then some f else result k) else result)
       i := i + 1
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,13 +120,12 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: loop bound refs.length - 1 drops the final reference.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
-    while i < refs.length
+    while i < refs.length - 1
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
-      done_with i = refs.length
-      decreasing refs.length - i
+      done_with i = refs.length - 1
     do
       let f := refs[i]!
       result := selectRef result f
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,16 +120,15 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: record every reference unconditionally (missing isLink guard).
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
       done_with i = refs.length
-      decreasing refs.length - i
     do
       let f := refs[i]!
-      result := selectRef result f
+      result := (fun k => if k = f.target then some f else result k)
       i := i + 1
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,17 +120,16 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: increment by 2, skipping odd-indexed references.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
       done_with i = refs.length
-      decreasing refs.length - i
     do
       let f := refs[i]!
       result := selectRef result f
-      i := i + 1
+      i := i + 2
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,16 +120,15 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: file every selected link under key 0 regardless of target.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
       done_with i = refs.length
-      decreasing refs.length - i
     do
       let f := refs[i]!
-      result := selectRef result f
+      result := (if f.isLink then (fun k => if k = 0 then some f else result k) else result)
       i := i + 1
     return result
     -- impl-end
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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,35 +120,18 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: diverges on nonempty input (i never advances), so under partial
+    -- correctness the (empty) result is never actually produced.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
-      invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
+      invariant True
       done_with i = refs.length
-      decreasing refs.length - i
     do
-      let f := refs[i]!
-      result := selectRef result f
-      i := i + 1
+      result := selectRef result (refs[i]!)
     return result
     -- impl-end
 
 prove_correct collectParentLinks by
   loom_solve
-  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>
-    have hi : i < refs.length := by omega
-    rw [invariant_2, collectLinks_take_step refs i hi]
-  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>
-    intro k g h
-    cases i_2
-    have hlen : i = refs.length := by omega
-    rw [invariant_2, hlen, List.take_length] at h
-    exact (collectLinks_props refs k g h).1
-  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>
-    intro k g h
-    cases i_2
-    have hlen : i = refs.length := by omega
-    rw [invariant_2, hlen, List.take_length] at h
-    exact (collectLinks_props refs k g h).2
   all_goals simp_all [collectLinks]
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,35 +120,16 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
-    let mut result : LinkMap := (fun _ => none)
-    let mut i := 0
-    while i < refs.length
-      invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
-      done_with i = refs.length
-      decreasing refs.length - i
-    do
-      let f := refs[i]!
-      result := selectRef result f
-      i := i + 1
-    return result
+    -- ECHO: return the model oracle directly.
+    return (collectLinks refs)
     -- impl-end
 
 prove_correct collectParentLinks by
   loom_solve
-  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>
-    have hi : i < refs.length := by omega
-    rw [invariant_2, collectLinks_take_step refs i hi]
   case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>
     intro k g h
-    cases i_2
-    have hlen : i = refs.length := by omega
-    rw [invariant_2, hlen, List.take_length] at h
     exact (collectLinks_props refs k g h).1
   case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>
     intro k g h
-    cases i_2
-    have hlen : i = refs.length := by omega
-    rw [invariant_2, hlen, List.take_length] at h
     exact (collectLinks_props refs k g h).2
   all_goals simp_all [collectLinks]
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behavior under spec is
@@ -120,16 +120,15 @@
   ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
   do
     -- impl-start
+    -- WRONG: first-writer-wins; ignores a later link to an already-seen target.
     let mut result : LinkMap := (fun _ => none)
     let mut i := 0
     while i < refs.length
       invariant i ≤ refs.length
-      invariant result = (refs.take i).foldl selectRef (fun _ => none)
       done_with i = refs.length
-      decreasing refs.length - i
     do
       let f := refs[i]!
-      result := selectRef result f
+      result := (if f.isLink then (fun k => if k = f.target ∧ (result k).isNone then some f else result k) else result)
       i := i + 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure data-flow that scans a record's own one-to-one identity references and
   keeps, per referenced target, only those references explicitly marked as the
   record's identity link. Every observable is computed from the read-only input
   list `refs`; nothing is borrowed from a foreign oracle. There is therefore no
   consumed axiom and no deep-model reference (mapping.md §3). -/
-- axioms-end

-- pure-start
/- One one-to-one identity reference a record declares to an ancestor. `target`
   is the identity of the referenced ancestor (distinct ancestors get distinct
   `target`s); `isLink` flags whether this reference is explicitly declared to be
   the record's identity link to that ancestor; `fid` is the reference's own
   identity, so two references to the same ancestor remain distinguishable. -/
structure Ref where
  target : Nat
  isLink : Bool
  fid : Nat
deriving DecidableEq, Inhabited, Repr

/- A per-target selection of identity links: for each ancestor identity, the
   reference (if any) chosen as the record's identity link to that ancestor.
   `none` means no identity link to that ancestor has been selected. -/
abbrev LinkMap := Nat → Option Ref

/- Fold one reference into the selection. A reference that is NOT an explicit
   identity link is ignored — it must never be selected as an identity link. An
   explicit identity link is recorded under its target ancestor, overwriting any
   link already held for that same target (later declarations win, the
   last-writer-wins map semantics). -/
def selectRef (m : LinkMap) (f : Ref) : LinkMap :=
  if f.isLink then (fun k => if k = f.target then some f else m k) else m

/- The selection after scanning the whole reference list left to right. -/
def collectLinks (refs : List Ref) : LinkMap :=
  refs.foldl selectRef (fun _ => none)

/- The key structural fact, generalized over an arbitrary starting selection so
   it folds by induction: anything the scan selects under key `k` is either an
   explicit identity link that targets exactly `k` and is one of the references
   scanned, or it was already present in the starting selection. -/
lemma foldl_selectRef_props (refs : List Ref) (m : LinkMap) :
    ∀ k g, refs.foldl selectRef m k = some g →
      (g.isLink = true ∧ g.target = k ∧ g ∈ refs) ∨ m k = some g := by
  induction refs generalizing m with
  | nil => intro k g h; right; simpa using h
  | cons hd tl ih =>
    intro k g h
    rw [List.foldl_cons] at h
    rcases ih (selectRef m hd) k g h with hL | hR
    · exact Or.inl ⟨hL.1, hL.2.1, by simp [hL.2.2]⟩
    · unfold selectRef at hR
      by_cases hf : hd.isLink
      · simp only [hf, if_true] at hR
        by_cases hk : k = hd.target
        · simp only [hk, if_true] at hR
          have hg := Option.some_inj.mp hR
          subst hg
          exact Or.inl ⟨hf, hk.symm, by simp⟩
        · simp only [hk, if_false] at hR
          exact Or.inr hR
      · simp only [hf] at hR
        exact Or.inr hR

/- The whole-list selection: any selected entry is an explicit identity link,
   targets exactly its key, and is one of the declared references. This is the
   property that pins the behavior — a selected reference is necessarily one the
   record declared as its identity link, so no non-link reference can hijack the
   identity-link slot for an ancestor. -/
lemma collectLinks_props (refs : List Ref) :
    ∀ k g, collectLinks refs k = some g →
      g.isLink = true ∧ g.target = k ∧ g ∈ refs := by
  intro k g h
  rcases foldl_selectRef_props refs (fun _ => none) k g h with hL | hR
  · exact hL
  · simp at hR

/- Forward-fold step: extending the consumed prefix by one reference folds that
   reference into the selection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
lemma collectLinks_take_step (refs : List Ref) (i : Nat) (hi : i < refs.length) :
    (refs.take (i + 1)).foldl selectRef (fun _ => none)
      = selectRef ((refs.take i).foldl selectRef (fun _ => none)) refs[i]! := by
  have hcons : refs.take (i + 1) = refs.take i ++ [refs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select, per ancestor, the record's identity link among its declared one-to-one
   references. Scanning the references in declaration order, a reference is chosen
   as the identity link to its target ancestor ONLY when it is explicitly marked
   as such; a plain one-to-one reference to an ancestor must NOT be treated as an
   identity link, so that declaring such a reference (in any order, alongside or
   without an explicit identity link) never misidentifies the record's identity
   link. The post-state pins the selection to the input references: any selected
   entry is one of the declared references, it is an explicit identity link, and
   it is filed under exactly the ancestor it references.

   `refs` is read-only: the method builds and returns a fresh selection and never
   mutates its input. -/
method collectParentLinks (refs : List Ref) return (out : LinkMap)
  ensures ∀ k, out k = collectLinks refs k
  ensures ∀ k g, out k = some g → g.isLink = true
  ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
  do
    -- impl-start
    let mut result : LinkMap := (fun _ => none)
    let mut i := 0
    while i < refs.length
      invariant i ≤ refs.length
      invariant result = (refs.take i).foldl selectRef (fun _ => none)
      done_with i = refs.length
    do
      let f := refs[i]!
      result := selectRef result f
      i := i + 1
    return result
    -- impl-end

prove_correct collectParentLinks by
  loom_solve
  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>
    have hi : i < refs.length := by omega
    rw [invariant_2, collectLinks_take_step refs i hi]
  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).1
  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).2
  all_goals simp_all [collectLinks]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF django__django-12325 velvet (G-EQ, refinement fidelity).

SPEC STRUCTURE: The method collectParentLinks(refs: List Ref) has three postconditions, the first of which — ensures `∀ k, out k = collectLinks refs k` — FULLY PINS the output to the pure model `collectLinks refs`. `collectLinks = refs.foldl selectRef (fun _ => none)` and `selectRef m f = if f.isLink then (set m[f.target]:=f) else m` exactly mirror the gold patch's single behavioral change: adding `and field.remote_field.parent_link` to the `isinstance(field, OneToOneField)` guard (isLink ↔ parent_link), with the dict write `parent_links[key]=field` as last-writer-wins overwrite under f.target. ensures_2 (`out k = some g → g.isLink = true`) and ensures_1 (`g.target=k ∧ g∈refs`) further pin the selection. Because the output is functionally determined, any terminating impl that verifies is behaviorally == gold.

### ATTACKS (11 total: prepatch + 9 wrong impls, all same_spec=True verified via swebench_unified.markers.same_spec on velvet backend):
- atk_prepatch (frozen Solution_prepatch.lean, records every ref unconditionally / missing isLink guard): lean_verify exit=1 (FAILS — invariant_2/ensures step unprovable). Prepatch bug reproduced.
- atk_1 empty map (drop all): exit=1 FAIL (ensures_1 unmet).
- atk_2 NEGATED guard (keep non-links, drop links): exit=1 FAIL.
- atk_3 off-by-one boundary (loop `i < refs.length - 1`, skip last ref): exit=1 FAIL.
- atk_4 no-guard record-all (prepatch-style, distinct proof body): exit=1 FAIL.
- atk_5 control-flow-effect step-by-2 (process only even indices): exit=1 FAIL.
- atk_6 ungrounded key (file all links under key 0 regardless of target): exit=1 FAIL.
- atk_7 DIVERGENCE / partial-correctness escape (loop never advances i; `invariant True`): exit=1 FAIL. Crucially the partial-correctness vacuous-divergence trick does NOT work: with a trivial invariant the exit state cannot discharge ensures_3 (`out k = collectLinks refs k`), so a diverging/garbage-returning impl cannot verify.
- atk_9 first-writer-wins (only set if key absent): exit=1 FAIL (functionally ≠ last-writer-wins collectLinks).
- atk_8 ECHO (`return (collectLinks refs)`): lean_verify exit=0 VERIFIES. Per protocol its faithful patch was materialized (= the gold patch, since echo behavior == collectLinks refs == gold) and RUN through run_resolve → RESOLVED=True. Not a break.

Commands used:
  same_spec: python -c "from swebench_unified.markers import same_spec; ..." → True for all 11.
  verify: bash scripts/lean_verify.sh <atk>.lean
  positive_control.lean (copy of frozen Solution.lean): exit=0 (verifies).
  resolve: swebench_unified.harness.run_resolve('django__django-12325', <atk_8 gold patch>, timeout=1800) → ResolveResult(resolved=True, completed=True, flaky=False, attempts=1).

REFINEMENT.MD LEG AUDIT: meta.json confirms axioms=[] and deep_model_references=[] — this bundle has NO A-consumed and NO A-reference legs. Every leg is R or I, no kind-3 (inexpressible-changed-op):
  A1 refs↔OneToOneField list = R; A2 selectRef guard↔`and field.remote_field.parent_link` + dict write = R+I (the single behavioral change, modeled directly not axiomatized); A3 f.target↔make_model_tuple(resolve_relation(...)) key = R (unchanged callees compute an opaque Nat key, not modeled as oracles — sound abstraction); A4 while-fold↔for-loop = I; A5 LinkMap↔parent_links dict = R; B1 ensures_2↔deleted ImproperlyConfigured raise = I (behavior-neutral: post site-A fix every promoted parent field has parent_link=True by ensures_2, so the deleted guard's condition is dead code). Correspondence holds; the discriminating content (non-parent_link OneToOneField must NOT be selected) lives in the isLink guard and is pinned by ensures_2, exercised by the prepatch failure. F2P tests (test_clash_parent_link, test_onetoone_with_parent_model) exercise exactly the multiple-OneToOne / order-independence discriminator.

VERDICT: SOUND. 9 distinct wrong impls + prepatch attacked; all non-echo wrong impls FAIL to verify (spec correctly rejects them); the only verifying impl (echo) is behaviorally gold and its faithful patch RESOLVES. No verify⇏correct gap found. verify⇒correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Only atk_8 (the ungrounded-oracle echo: `return (collectLinks refs)`) verified; it is behaviorally identical to the gold and its faithful refined patch (= the gold patch) RESOLVED under the official harness (run_resolve: RESOLVED=True, COMPLETED=True, not flaky, 1 attempt). No verifying wrong impl produced a non-resolving patch, so verify⇒correct holds.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure data-flow that scans a record's own one-to-one identity references and
   keeps, per referenced target, only those references explicitly marked as the
   record's identity link. Every observable is computed from the read-only input
   list `refs`; nothing is borrowed from a foreign oracle. There is therefore no
   consumed axiom and no deep-model reference (mapping.md §3). -/
-- axioms-end

-- pure-start
/- One one-to-one identity reference a record declares to an ancestor. `target`
   is the identity of the referenced ancestor (distinct ancestors get distinct
   `target`s); `isLink` flags whether this reference is explicitly declared to be
   the record's identity link to that ancestor; `fid` is the reference's own
   identity, so two references to the same ancestor remain distinguishable. -/
structure Ref where
  target : Nat
  isLink : Bool
  fid : Nat
deriving DecidableEq, Inhabited, Repr

/- A per-target selection of identity links: for each ancestor identity, the
   reference (if any) chosen as the record's identity link to that ancestor.
   `none` means no identity link to that ancestor has been selected. -/
abbrev LinkMap := Nat → Option Ref

/- Fold one reference into the selection. A reference that is NOT an explicit
   identity link is ignored — it must never be selected as an identity link. An
   explicit identity link is recorded under its target ancestor, overwriting any
   link already held for that same target (later declarations win, the
   last-writer-wins map semantics). -/
def selectRef (m : LinkMap) (f : Ref) : LinkMap :=
  if f.isLink then (fun k => if k = f.target then some f else m k) else m

/- The selection after scanning the whole reference list left to right. -/
def collectLinks (refs : List Ref) : LinkMap :=
  refs.foldl selectRef (fun _ => none)

/- The key structural fact, generalized over an arbitrary starting selection so
   it folds by induction: anything the scan selects under key `k` is either an
   explicit identity link that targets exactly `k` and is one of the references
   scanned, or it was already present in the starting selection. -/
lemma foldl_selectRef_props (refs : List Ref) (m : LinkMap) :
    ∀ k g, refs.foldl selectRef m k = some g →
      (g.isLink = true ∧ g.target = k ∧ g ∈ refs) ∨ m k = some g := by
  induction refs generalizing m with
  | nil => intro k g h; right; simpa using h
  | cons hd tl ih =>
    intro k g h
    rw [List.foldl_cons] at h
    rcases ih (selectRef m hd) k g h with hL | hR
    · exact Or.inl ⟨hL.1, hL.2.1, by simp [hL.2.2]⟩
    · unfold selectRef at hR
      by_cases hf : hd.isLink
      · simp only [hf, if_true] at hR
        by_cases hk : k = hd.target
        · simp only [hk, if_true] at hR
          have hg := Option.some_inj.mp hR
          subst hg
          exact Or.inl ⟨hf, hk.symm, by simp⟩
        · simp only [hk, if_false] at hR
          exact Or.inr hR
      · simp only [hf] at hR
        exact Or.inr hR

/- The whole-list selection: any selected entry is an explicit identity link,
   targets exactly its key, and is one of the declared references. This is the
   property that pins the behavior — a selected reference is necessarily one the
   record declared as its identity link, so no non-link reference can hijack the
   identity-link slot for an ancestor. -/
lemma collectLinks_props (refs : List Ref) :
    ∀ k g, collectLinks refs k = some g →
      g.isLink = true ∧ g.target = k ∧ g ∈ refs := by
  intro k g h
  rcases foldl_selectRef_props refs (fun _ => none) k g h with hL | hR
  · exact hL
  · simp at hR

/- Forward-fold step: extending the consumed prefix by one reference folds that
   reference into the selection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
lemma collectLinks_take_step (refs : List Ref) (i : Nat) (hi : i < refs.length) :
    (refs.take (i + 1)).foldl selectRef (fun _ => none)
      = selectRef ((refs.take i).foldl selectRef (fun _ => none)) refs[i]! := by
  have hcons : refs.take (i + 1) = refs.take i ++ [refs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select, per ancestor, the record's identity link among its declared one-to-one
   references. Scanning the references in declaration order, a reference is chosen
   as the identity link to its target ancestor ONLY when it is explicitly marked
   as such; a plain one-to-one reference to an ancestor must NOT be treated as an
   identity link, so that declaring such a reference (in any order, alongside or
   without an explicit identity link) never misidentifies the record's identity
   link. The post-state pins the selection to the input references: any selected
   entry is one of the declared references, it is an explicit identity link, and
   it is filed under exactly the ancestor it references.

   `refs` is read-only: the method builds and returns a fresh selection and never
   mutates its input. -/
method collectParentLinks (refs : List Ref) return (out : LinkMap)
  ensures ∀ k, out k = collectLinks refs k
  ensures ∀ k g, out k = some g → g.isLink = true
  ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
  do
    -- impl-start
    let mut result : LinkMap := (fun _ => none)
    let mut i := 0
    while i < refs.length
      invariant i ≤ refs.length
      invariant result = (refs.take i).foldl selectRef (fun _ => none)
      done_with i = refs.length
    do
      let f := refs[i]!
      result := selectRef result f
      i := i + 1
    return result
    -- impl-end

prove_correct collectParentLinks by
  loom_solve
  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>
    have hi : i < refs.length := by omega
    rw [invariant_2, collectLinks_take_step refs i hi]
  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).1
  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).2
  all_goals simp_all [collectLinks]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF django__django-12325 velvet (G-EQ, refinement fidelity).

SPEC STRUCTURE: The method collectParentLinks(refs: List Ref) has three postconditions, the first of which — ensures `∀ k, out k = collectLinks refs k` — FULLY PINS the output to the pure model `collectLinks refs`. `collectLinks = refs.foldl selectRef (fun _ => none)` and `selectRef m f = if f.isLink then (set m[f.target]:=f) else m` exactly mirror the gold patch's single behavioral change: adding `and field.remote_field.parent_link` to the `isinstance(field, OneToOneField)` guard (isLink ↔ parent_link), with the dict write `parent_links[key]=field` as last-writer-wins overwrite under f.target. ensures_2 (`out k = some g → g.isLink = true`) and ensures_1 (`g.target=k ∧ g∈refs`) further pin the selection. Because the output is functionally determined, any terminating impl that verifies is behaviorally == gold.

### ATTACKS (11 total: prepatch + 9 wrong impls, all same_spec=True verified via swebench_unified.markers.same_spec on velvet backend):
- atk_prepatch (frozen Solution_prepatch.lean, records every ref unconditionally / missing isLink guard): lean_verify exit=1 (FAILS — invariant_2/ensures step unprovable). Prepatch bug reproduced.
- atk_1 empty map (drop all): exit=1 FAIL (ensures_1 unmet).
- atk_2 NEGATED guard (keep non-links, drop links): exit=1 FAIL.
- atk_3 off-by-one boundary (loop `i < refs.length - 1`, skip last ref): exit=1 FAIL.
- atk_4 no-guard record-all (prepatch-style, distinct proof body): exit=1 FAIL.
- atk_5 control-flow-effect step-by-2 (process only even indices): exit=1 FAIL.
- atk_6 ungrounded key (file all links under key 0 regardless of target): exit=1 FAIL.
- atk_7 DIVERGENCE / partial-correctness escape (loop never advances i; `invariant True`): exit=1 FAIL. Crucially the partial-correctness vacuous-divergence trick does NOT work: with a trivial invariant the exit state cannot discharge ensures_3 (`out k = collectLinks refs k`), so a diverging/garbage-returning impl cannot verify.
- atk_9 first-writer-wins (only set if key absent): exit=1 FAIL (functionally ≠ last-writer-wins collectLinks).
- atk_8 ECHO (`return (collectLinks refs)`): lean_verify exit=0 VERIFIES. Per protocol its faithful patch was materialized (= the gold patch, since echo behavior == collectLinks refs == gold) and RUN through run_resolve → RESOLVED=True. Not a break.

Commands used:
  same_spec: python -c "from swebench_unified.markers import same_spec; ..." → True for all 11.
  verify: bash scripts/lean_verify.sh <atk>.lean
  positive_control.lean (copy of frozen Solution.lean): exit=0 (verifies).
  resolve: swebench_unified.harness.run_resolve('django__django-12325', <atk_8 gold patch>, timeout=1800) → ResolveResult(resolved=True, completed=True, flaky=False, attempts=1).

REFINEMENT.MD LEG AUDIT: meta.json confirms axioms=[] and deep_model_references=[] — this bundle has NO A-consumed and NO A-reference legs. Every leg is R or I, no kind-3 (inexpressible-changed-op):
  A1 refs↔OneToOneField list = R; A2 selectRef guard↔`and field.remote_field.parent_link` + dict write = R+I (the single behavioral change, modeled directly not axiomatized); A3 f.target↔make_model_tuple(resolve_relation(...)) key = R (unchanged callees compute an opaque Nat key, not modeled as oracles — sound abstraction); A4 while-fold↔for-loop = I; A5 LinkMap↔parent_links dict = R; B1 ensures_2↔deleted ImproperlyConfigured raise = I (behavior-neutral: post site-A fix every promoted parent field has parent_link=True by ensures_2, so the deleted guard's condition is dead code). Correspondence holds; the discriminating content (non-parent_link OneToOneField must NOT be selected) lives in the isLink guard and is pinned by ensures_2, exercised by the prepatch failure. F2P tests (test_clash_parent_link, test_onetoone_with_parent_model) exercise exactly the multiple-OneToOne / order-independence discriminator.

VERDICT: SOUND. 9 distinct wrong impls + prepatch attacked; all non-echo wrong impls FAIL to verify (spec correctly rejects them); the only verifying impl (echo) is behaviorally gold and its faithful patch RESOLVES. No verify⇏correct gap found. verify⇒correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role: faithfulness-break (does the modeled function drift from the real callee / is the spec too strong?). Verdict: FAITHFUL — no diverging input found.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers (velvet backend). Spec region (structure Ref, LinkMap, selectRef, collectLinks, the three lemmas, and the three `ensures`) is byte-identical between spec and prepatch; only impl/proof regions differ.
- Solution.lean elaborates clean under scripts/lean_verify.sh (exit 0). Prepatch (unconditional record, no isLink guard) FAILS at exit 1 with an unsolved goal at the loop body `(fun k => if k = refs[i]!.target then some refs[i]! else ...) = selectRef ... refs[i]!` — the missing guard, i.e. the discriminator fails for the right reason. So the spec is non-vacuous and genuinely characterizing.

Faithfulness probe (the crux of my role): I reconstructed the REAL post-gold callee behavior. Copied the base_commit worktree (29c126bb34) to, applied the gold guard `if isinstance(field, OneToOneField) and field.remote_field.parent_link:` to ModelBase.__new__, and ran the bundle's conformance_check.py against the real patched Django (PYTHONPATH=worktree). Result: `G-CONF OK ... 100015 field configurations (seed=12325), 0 disagreements`. The R/I shadow of the modeled `collectLinks` + the unchanged downstream selection/synthesis step (observable = child._meta.parents[Place].name) agrees with the actual patched metaclass on ALL exhaustive specs of length 0..3 plus 100k random specs up to length 4.

Model↔repo mapping is sound and NOT too strong: modeled function `collectParentLinks refs = collectLinks refs` = per-ancestor last-writer-wins fold that drops every reference with isLink=false. This is precisely the gold's single behavioral edit. Dict last-writer-wins ↔ foldl selectRef overwrite; drop-non-link ↔ `if f.isLink`; absent key ↔ none; declaration order ↔ list order. The ensures clauses (functional equality + isLink=true + target=k ∧ mem refs) are all TRUE of the real callee — they do not over-constrain: the correct impl (and the real Django loop) satisfy them. No axioms / deep-model references exist (axioms:[], deep_model_references:[]), so there is no oracle to over-approximate that could make the spec too strong.

Edge cases considered: multi-target (distinct ancestors) — model keys each target independently, matches dict; two links to same target — last-writer-wins matches Python dict last-assignment-wins (confirmed in G-CONF's random length-4 specs which include repeated links); non-link-then-link and link-then-non-link orderings — the non-link is never selected, matches. The single-ancestor F2P domain is a subset; the model generalizes correctly to multiple targets by construction (per-key overwrite).

Conclusion: the spec faithfully models the real repo behavior; no input where the modeled function disagrees with the real callee was found. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is fully abstract, modeled entirely in Lean vocabulary (Ref, isLink, target, LinkMap, selectRef, collectLinks, collectParentLinks). It never names any gold-patch specifics: no OneToOneField, parent_link, field.remote_field, resolve_relation, make_model_tuple, ImproperlyConfigured, _meta.parents, base.py, or options.py. Mechanical G-LEAK screen passes (rep.passed=True, hard_failures=[]). same_spec(Solution, Solution_prepatch)=True confirms the frozen spec region (axioms/pure/pre/post + signature/ensures) is byte-identical; only impl and prove_correct bodies differ. Semantically, the discriminating idea the spec encodes — an ancestor identity link must be an EXPLICITLY marked reference and declaration order must not misidentify it — is already stated in the PUBLIC problem_statement ('we have explicit parent_link marker', 'order seems to matter?', ImproperlyConfigured symptom). The spec generalizes it abstractly (isLink guard + last-writer-wins fold) without disclosing the gold edit's specifics (the literal `and field.remote_field.parent_link` guard, or the options.py dead-raise removal, which is not even modeled in the spec view). No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
