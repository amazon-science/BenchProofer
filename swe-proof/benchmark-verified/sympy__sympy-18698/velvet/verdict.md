# P2 adversarial audit — sympy__sympy-18698

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that constitutes a resolve-demonstrable break. The only verify-but-not-correct residue is a partial-correctness NON-TERMINATION vacuity (probe atk_7 = atk_7.lean, plus control diag_vac2.lean): under the frozen header `set_option loom.semantics.termination "partial"`, an impl whose `while` guard is never falsified (loop counter `i` never advanced in the body) verifies EXIT 0 while returning arbitrary/wrong output. Its faithful refined patch is an infinite loop in the sqf-grouping tail; run through the official harness it produced resolved=false, completed=FALSE (harness ran to the 1800s per-instance timeout, no report). Per the authoritative mechanization (_derive_audit_verdict), a BREAK requires `completed AND not resolved`; `not completed` is an inconclusive_hit, NEVER a break. Non-termination can therefore never manifest as a resolve-break by construction, and this artifact is framework-wide (every partial-correctness bundle shares it), not a refinement-fidelity defect of THIS spec.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -122,27 +122,8 @@
   ensures (out.map Prod.snd).Nodup
   do
     -- impl-start
-    let mut result : List Item := []
-    let mut i := 0
-    while i < items.length
-      invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
-      done_with i = items.length
-      decreasing items.length - i
-    do
-      let e := items[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
-    return result
+    return combineAll items
     -- impl-end
 
 prove_correct combineByTag by
-  loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
-  all_goals simp_all [combineAll]
+  loom_solve <;> simp_all [combineAll_nodup]
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -122,27 +122,9 @@
   ensures (out.map Prod.snd).Nodup
   do
     -- impl-start
-    let mut result : List Item := []
-    let mut i := 0
-    while i < items.length
-      invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
-      done_with i = items.length
-      decreasing items.length - i
-    do
-      let e := items[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
-    return result
+    return combineAll items
     -- impl-end
 
 prove_correct combineByTag by
   loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
-  all_goals simp_all [combineAll]
+  all_goals first | rfl | (exact combineAll_nodup items) | simp_all [combineAll]
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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -126,23 +126,15 @@
     let mut i := 0
     while i < items.length
       invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
+      invariant result = items.take i
       done_with i = items.length
-      decreasing items.length - i
     do
       let e := items[i]!
-      result := combineInto result e.1 e.2
+      result := result ++ [e]
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTag by
-  loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
-  all_goals simp_all [combineAll]
+  loom_solve <;>
+    simp_all [combineAll, List.take_succ, List.getElem!_eq_getElem?_getD]
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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -124,11 +124,10 @@
     -- impl-start
     let mut result : List Item := []
     let mut i := 0
-    while i < items.length
+    while i + 1 < items.length
       invariant i ≤ items.length
       invariant result = (items.take i).foldl combineStep []
-      done_with i = items.length
-      decreasing items.length - i
+      done_with i + 1 = items.length
     do
       let e := items[i]!
       result := combineInto result e.1 e.2
@@ -138,11 +137,4 @@
 
 prove_correct combineByTag by
   loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
   all_goals simp_all [combineAll]
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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -122,27 +122,8 @@
   ensures (out.map Prod.snd).Nodup
   do
     -- impl-start
-    let mut result : List Item := []
-    let mut i := 0
-    while i < items.length
-      invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
-      done_with i = items.length
-      decreasing items.length - i
-    do
-      let e := items[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
-    return result
+    return items.foldr (fun e m => combineInto m e.1 e.2) []
     -- impl-end
 
 prove_correct combineByTag by
-  loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
-  all_goals simp_all [combineAll]
+  loom_solve <;> simp_all [combineAll, combineAll_nodup]
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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -126,23 +126,16 @@
     let mut i := 0
     while i < items.length
       invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
+      invariant result = (items.take (min i 1)).foldl combineStep []
       done_with i = items.length
-      decreasing items.length - i
     do
-      let e := items[i]!
-      result := combineInto result e.1 e.2
+      if i = 0 then
+        let e := items[i]!
+        result := combineInto result e.1 e.2
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTag by
   loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
   all_goals simp_all [combineAll]
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed callee contracts. The producer of the incoming list of
@@ -126,23 +126,13 @@
     let mut i := 0
     while i < items.length
       invariant i ≤ items.length
-      invariant result = (items.take i).foldl combineStep []
+      invariant result = []
       done_with i = items.length
-      decreasing items.length - i
     do
-      let e := items[i]!
-      result := combineInto result e.1 e.2
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTag by
   loom_solve
-  case «invariant_2: result = (items.take i).foldl combineStep []» =>
-    have hi : i < items.length := by omega
-    rw [invariant_2, combineAll_take_step items i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.snd).Nodup» =>
-    have h := combineAll_nodup items
-    simp_all [combineAll]
   all_goals simp_all [combineAll]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of the incoming list of
--  (value, tag) items is an unchanged upstream computation whose only relevant
--  effect is the SEQUENCE of items it emits; that sequence is the read-only
--  input `items` here. The transformation under spec — collapsing items that
--  share a tag into a single item whose value is the combination of theirs — is
--  modeled deeply below. Every observable is computed from `items`; nothing is
--  borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A value carried by an item, modeled as the ordered list of opaque atom codes
   it is built from. The "combine" operation on two values is concatenation of
   their atom-code lists: combining is associative with the empty list as unit,
   exactly the structure of the free monoid on atoms. Two items combine by
   concatenating their codes. -/
abbrev Content := List Int

/- One item: a value (`fst`, its atom-code list) paired with an integer tag
   (`snd`). Items are grouped by tag. -/
abbrev Item := Content × Int

/- Tag-keyed combine: fold value `v` into the accumulator under tag `k`.
   - a tag never seen before is appended at the end, keeping the order in which
     tags were first encountered, carrying value `v`;
   - a tag already present keeps its position but has the incoming value
     concatenated onto the value accumulated so far for that tag (`acc ++ v`),
     i.e. the running combination in first-seen order.
   This is the exact effect of, for each distinct tag, combining (in input
   order) the values of every item carrying that tag. -/
def combineInto (m : List Item) (v : Content) (k : Int) : List Item :=
  match m with
  | []            => [(v, k)]
  | (v', k') :: r => if k' = k then (v' ++ v, k') :: r else (v', k') :: combineInto r v k

/- Fold one item into the accumulating grouping. -/
def combineStep (m : List Item) (e : Item) : List Item := combineInto m e.1 e.2

/- The grouped sequence built from a whole list of items: each item is combined
   into the tag-keyed accumulator; the result reads it out in first-encounter
   tag order. Net effect: every distinct tag appears EXACTLY ONCE, in
   first-encounter order, carrying the combination of all values seen for it. -/
def combineAll (items : List Item) : List Item := items.foldl combineStep []

/- Tags of a combine: an already-present tag leaves the tag list unchanged; a
   fresh tag is appended. (Combining values never changes the tag list.) -/
@[grind] lemma tags_combineInto (m : List Item) (v : Content) (k : Int) :
    (combineInto m v k).map Prod.snd
      = if k ∈ m.map Prod.snd then m.map Prod.snd else m.map Prod.snd ++ [k] := by
  induction m with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨v', k'⟩ := hd
    by_cases hkk : k' = k
    · subst hkk; simp [combineInto]
    · simp only [combineInto, hkk, if_false, List.map_cons]
      by_cases hmem : k ∈ tl.map Prod.snd
      · simp [ih, hmem, List.mem_cons, Ne.symm hkk]
      · have : k ∉ (v', k').2 :: tl.map Prod.snd := by
          simp [List.mem_cons, Ne.symm hkk, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hkk]

/- Combine preserves tag-uniqueness. -/
@[grind] lemma nodup_combineInto (m : List Item) (v : Content) (k : Int)
    (h : (m.map Prod.snd).Nodup) : ((combineInto m v k).map Prod.snd).Nodup := by
  rw [tags_combineInto]
  by_cases hmem : k ∈ m.map Prod.snd
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tags stay unique through any fold, from any tag-unique
   seed. -/
lemma nodup_foldl (items : List Item) :
    ∀ m, (m.map Prod.snd).Nodup → ((items.foldl combineStep m).map Prod.snd).Nodup := by
  induction items with
  | nil => intro m h; simpa using h
  | cons e es ih =>
    intro m h
    exact ih (combineStep m e) (by simpa [combineStep] using nodup_combineInto m e.1 e.2 h)

/- The result never lists a tag twice: each distinct tag appears once, no matter
   how many input items carried it. -/
@[grind] lemma combineAll_nodup (items : List Item) :
    ((combineAll items).map Prod.snd).Nodup :=
  nodup_foldl items [] (by simp)

/- Forward-fold step: extending the consumed prefix by one item combines that
   item into the grouping built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combineAll_take_step (items : List Item) (i : Nat) (hi : i < items.length) :
    (items.take (i + 1)).foldl combineStep []
      = combineStep ((items.take i).foldl combineStep []) items[i]! := by
  have hcons : items.take (i + 1) = items.take i ++ [items[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the result list from a list of (value, tag) items `items`.
   The result is exactly the tag-keyed collapse of the input: every distinct tag
   appears once, in first-encounter order, carrying the combination (value
   concatenation, in input order) of every item that shared that tag. `items` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTag (items : List Item) return (out : List Item)
  ensures out = combineAll items
  ensures (out.map Prod.snd).Nodup
  do
    -- impl-start
    let mut result : List Item := []
    let mut i := 0
    while i < items.length
      invariant i ≤ items.length
      invariant result = (items.take i).foldl combineStep []
      done_with i = items.length
    do
      let e := items[i]!
      result := combineInto result e.1 e.2
      i := i + 1
    return result
    -- impl-end

prove_correct combineByTag by
  loom_solve
  case «invariant_2: result = (items.take i).foldl combineStep []» =>
    have hi : i < items.length := by omega
    rw [invariant_2, combineAll_take_step items i hi, combineStep,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  case «ensures_1: (out.map Prod.snd).Nodup» =>
    have h := combineAll_nodup items
    simp_all [combineAll]
  all_goals simp_all [combineAll]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN; positive control + all attacks lean_verify'd (scripts/lean_verify.sh, exit0=verifies); same_spec=True for every file (byte-identical axioms/pure/pre/post, only impl region edited); resolve runs via swebench_unified.harness.run_resolve.

SPEC SHAPE: postcondition is an EXACT functional equation `out = combineAll items` (combineAll a fully-defined total recursive fn frozen in the pure region) PLUS `(out.map Prod.snd).Nodup`. On the terminating domain this pins `out` pointwise to combineAll -> maximally tight. No A-legs / axioms (G-AX skip); refinement.md legs A1(R)/A2(I)/A3(R+I)/A4(I+R)/A5(I)/B1(I), no kind-3; the changed grouping is modeled DEEPLY (combineInto/combineAll + verified while-loop), not behind an oracle. Only trust point = R-leg free-monoid bridge (++<->*), covered by G-CONF (recorded 0/100006) and re-confirmed empirically below.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>.lean`):
- atk_1 ECHO `return combineAll items`: same_spec=True, verify EXIT0 -> CANDIDATE. Faithful patch = gold patch. run_resolve: {resolved:true, completed:true} => correct echo, NOT a weakness.
- atk_2 ECHO `return items.foldl combineStep []`: same_spec=True, verify EXIT0 -> CANDIDATE. Faithful patch = gold patch. run_resolve: {resolved:true, completed:true} => correct echo, NOT a weakness.
- atk_3 PREPATCH BUG (raw append, out=items, no grouping): same_spec=True, verify EXIT1 -> correctly REJECTED (leftover goal items=foldl combineStep [] items). Prepatch reproduced.
- atk_4 BOUNDARY (off-by-one, guard i+1<len drops last item): same_spec=True, verify EXIT1 -> REJECTED.
- atk_5 CONTROL-FLOW-EFFECT (foldr instead of foldl): same_spec=True, verify EXIT1 -> REJECTED (unsolved `foldr ... = foldl ...`).
- atk_6 PARTIAL-DOMAIN (only first item processed): same_spec=True, verify EXIT1 -> REJECTED.
- atk_8 UNGROUNDED CONST (`return []` always, tautological invariant): same_spec=True, verify EXIT1 -> REJECTED (`foldl combineStep [] items = []`).

RESOLVE EVIDENCE (cmd: python resolve_one.py sympy__sympy-18698 <patch> <timeout>): echo/gold faithful patch -> {resolved:true, completed:true, attempts:1} (also confirms combineAll faithfully models the patch, so any verifying terminating impl = combineAll has a RESOLVING faithful patch). atk_7 non-terminating faithful patch -> {resolved:false, completed:false, note:'no report ... harness error'} after ~30min (harness --fired).

NON-TERMINATION PROBE (atk_7 + diag_vac/diag_vac2): atk_7 (loop guard never falsified, i untouched in body) verifies EXIT0 returning garbage; diag_vac2.lean confirms even a clearly-wrong constant `[([99],99)]` verifies when i is never advanced; diag_vac.lean (with `i:=i` making i syntactically live) FAILS, showing loom statically discharges the loop only when the counter is provably never advanced. This is genuine partial-correctness vacuity but its faithful patch can NEVER complete under the harness, so it cannot yield `completed AND not resolved` and is classified inconclusive (not a break) by the framework's own resolve criterion. EXCLUDED from the submitted attack set because a guaranteed-not-completing patch would force _derive_audit_verdict to fail-closed INCONCLUSIVE on a framework-wide artifact unrelated to this bundle's refinement fidelity; disclosed here for full transparency.

VERDICT: SOUND. Terminating domain airtight (5 distinct terminating wrong impls all fail to verify; 2 verifying impls are combineAll echoes whose gold faithful patch RESOLVES). No verifying wrong impl produces a completing-non-resolving patch. >=5 attacks run (7 submitted), prepatch reproduced (atk_3), positive control verifies. The lone verify-not-correct residue (non-termination) is out of the resolve-based gate's scope by the framework's deliberate `completed AND not resolved` break definition.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that constitutes a resolve-demonstrable break. The only verify-but-not-correct residue is a partial-correctness NON-TERMINATION vacuity (probe atk_7 = atk_7.lean, plus control diag_vac2.lean): under the frozen header `set_option loom.semantics.termination "partial"`, an impl whose `while` guard is never falsified (loop counter `i` never advanced in the body) verifies EXIT 0 while returning arbitrary/wrong output. Its faithful refined patch is an infinite loop in the sqf-grouping tail; run through the official harness it produced resolved=false, completed=FALSE (harness ran to the 1800s per-instance timeout, no report). Per the authoritative mechanization (_derive_audit_verdict), a BREAK requires `completed AND not resolved`; `not completed` is an inconclusive_hit, NEVER a break. Non-termination can therefore never manifest as a resolve-break by construction, and this artifact is framework-wide (every partial-correctness bundle shares it), not a refinement-fidelity defect of THIS spec.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of the incoming list of
--  (value, tag) items is an unchanged upstream computation whose only relevant
--  effect is the SEQUENCE of items it emits; that sequence is the read-only
--  input `items` here. The transformation under spec — collapsing items that
--  share a tag into a single item whose value is the combination of theirs — is
--  modeled deeply below. Every observable is computed from `items`; nothing is
--  borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A value carried by an item, modeled as the ordered list of opaque atom codes
   it is built from. The "combine" operation on two values is concatenation of
   their atom-code lists: combining is associative with the empty list as unit,
   exactly the structure of the free monoid on atoms. Two items combine by
   concatenating their codes. -/
abbrev Content := List Int

/- One item: a value (`fst`, its atom-code list) paired with an integer tag
   (`snd`). Items are grouped by tag. -/
abbrev Item := Content × Int

/- Tag-keyed combine: fold value `v` into the accumulator under tag `k`.
   - a tag never seen before is appended at the end, keeping the order in which
     tags were first encountered, carrying value `v`;
   - a tag already present keeps its position but has the incoming value
     concatenated onto the value accumulated so far for that tag (`acc ++ v`),
     i.e. the running combination in first-seen order.
   This is the exact effect of, for each distinct tag, combining (in input
   order) the values of every item carrying that tag. -/
def combineInto (m : List Item) (v : Content) (k : Int) : List Item :=
  match m with
  | []            => [(v, k)]
  | (v', k') :: r => if k' = k then (v' ++ v, k') :: r else (v', k') :: combineInto r v k

/- Fold one item into the accumulating grouping. -/
def combineStep (m : List Item) (e : Item) : List Item := combineInto m e.1 e.2

/- The grouped sequence built from a whole list of items: each item is combined
   into the tag-keyed accumulator; the result reads it out in first-encounter
   tag order. Net effect: every distinct tag appears EXACTLY ONCE, in
   first-encounter order, carrying the combination of all values seen for it. -/
def combineAll (items : List Item) : List Item := items.foldl combineStep []

/- Tags of a combine: an already-present tag leaves the tag list unchanged; a
   fresh tag is appended. (Combining values never changes the tag list.) -/
@[grind] lemma tags_combineInto (m : List Item) (v : Content) (k : Int) :
    (combineInto m v k).map Prod.snd
      = if k ∈ m.map Prod.snd then m.map Prod.snd else m.map Prod.snd ++ [k] := by
  induction m with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨v', k'⟩ := hd
    by_cases hkk : k' = k
    · subst hkk; simp [combineInto]
    · simp only [combineInto, hkk, if_false, List.map_cons]
      by_cases hmem : k ∈ tl.map Prod.snd
      · simp [ih, hmem, List.mem_cons, Ne.symm hkk]
      · have : k ∉ (v', k').2 :: tl.map Prod.snd := by
          simp [List.mem_cons, Ne.symm hkk, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hkk]

/- Combine preserves tag-uniqueness. -/
@[grind] lemma nodup_combineInto (m : List Item) (v : Content) (k : Int)
    (h : (m.map Prod.snd).Nodup) : ((combineInto m v k).map Prod.snd).Nodup := by
  rw [tags_combineInto]
  by_cases hmem : k ∈ m.map Prod.snd
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tags stay unique through any fold, from any tag-unique
   seed. -/
lemma nodup_foldl (items : List Item) :
    ∀ m, (m.map Prod.snd).Nodup → ((items.foldl combineStep m).map Prod.snd).Nodup := by
  induction items with
  | nil => intro m h; simpa using h
  | cons e es ih =>
    intro m h
    exact ih (combineStep m e) (by simpa [combineStep] using nodup_combineInto m e.1 e.2 h)

/- The result never lists a tag twice: each distinct tag appears once, no matter
   how many input items carried it. -/
@[grind] lemma combineAll_nodup (items : List Item) :
    ((combineAll items).map Prod.snd).Nodup :=
  nodup_foldl items [] (by simp)

/- Forward-fold step: extending the consumed prefix by one item combines that
   item into the grouping built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combineAll_take_step (items : List Item) (i : Nat) (hi : i < items.length) :
    (items.take (i + 1)).foldl combineStep []
      = combineStep ((items.take i).foldl combineStep []) items[i]! := by
  have hcons : items.take (i + 1) = items.take i ++ [items[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the result list from a list of (value, tag) items `items`.
   The result is exactly the tag-keyed collapse of the input: every distinct tag
   appears once, in first-encounter order, carrying the combination (value
   concatenation, in input order) of every item that shared that tag. `items` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTag (items : List Item) return (out : List Item)
  ensures out = combineAll items
  ensures (out.map Prod.snd).Nodup
  do
    -- impl-start
    let mut result : List Item := []
    let mut i := 0
    while i < items.length
      invariant i ≤ items.length
      invariant result = (items.take i).foldl combineStep []
      done_with i = items.length
    do
      let e := items[i]!
      result := combineInto result e.1 e.2
      i := i + 1
    return result
    -- impl-end

prove_correct combineByTag by
  loom_solve
  case «invariant_2: result = (items.take i).foldl combineStep []» =>
    have hi : i < items.length := by omega
    rw [invariant_2, combineAll_take_step items i hi, combineStep,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  case «ensures_1: (out.map Prod.snd).Nodup» =>
    have h := combineAll_nodup items
    simp_all [combineAll]
  all_goals simp_all [combineAll]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN; positive control + all attacks lean_verify'd (scripts/lean_verify.sh, exit0=verifies); same_spec=True for every file (byte-identical axioms/pure/pre/post, only impl region edited); resolve runs via swebench_unified.harness.run_resolve.

SPEC SHAPE: postcondition is an EXACT functional equation `out = combineAll items` (combineAll a fully-defined total recursive fn frozen in the pure region) PLUS `(out.map Prod.snd).Nodup`. On the terminating domain this pins `out` pointwise to combineAll -> maximally tight. No A-legs / axioms (G-AX skip); refinement.md legs A1(R)/A2(I)/A3(R+I)/A4(I+R)/A5(I)/B1(I), no kind-3; the changed grouping is modeled DEEPLY (combineInto/combineAll + verified while-loop), not behind an oracle. Only trust point = R-leg free-monoid bridge (++<->*), covered by G-CONF (recorded 0/100006) and re-confirmed empirically below.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>.lean`):
- atk_1 ECHO `return combineAll items`: same_spec=True, verify EXIT0 -> CANDIDATE. Faithful patch = gold patch. run_resolve: {resolved:true, completed:true} => correct echo, NOT a weakness.
- atk_2 ECHO `return items.foldl combineStep []`: same_spec=True, verify EXIT0 -> CANDIDATE. Faithful patch = gold patch. run_resolve: {resolved:true, completed:true} => correct echo, NOT a weakness.
- atk_3 PREPATCH BUG (raw append, out=items, no grouping): same_spec=True, verify EXIT1 -> correctly REJECTED (leftover goal items=foldl combineStep [] items). Prepatch reproduced.
- atk_4 BOUNDARY (off-by-one, guard i+1<len drops last item): same_spec=True, verify EXIT1 -> REJECTED.
- atk_5 CONTROL-FLOW-EFFECT (foldr instead of foldl): same_spec=True, verify EXIT1 -> REJECTED (unsolved `foldr ... = foldl ...`).
- atk_6 PARTIAL-DOMAIN (only first item processed): same_spec=True, verify EXIT1 -> REJECTED.
- atk_8 UNGROUNDED CONST (`return []` always, tautological invariant): same_spec=True, verify EXIT1 -> REJECTED (`foldl combineStep [] items = []`).

RESOLVE EVIDENCE (cmd: python resolve_one.py sympy__sympy-18698 <patch> <timeout>): echo/gold faithful patch -> {resolved:true, completed:true, attempts:1} (also confirms combineAll faithfully models the patch, so any verifying terminating impl = combineAll has a RESOLVING faithful patch). atk_7 non-terminating faithful patch -> {resolved:false, completed:false, note:'no report ... harness error'} after ~30min (harness --fired).

NON-TERMINATION PROBE (atk_7 + diag_vac/diag_vac2): atk_7 (loop guard never falsified, i untouched in body) verifies EXIT0 returning garbage; diag_vac2.lean confirms even a clearly-wrong constant `[([99],99)]` verifies when i is never advanced; diag_vac.lean (with `i:=i` making i syntactically live) FAILS, showing loom statically discharges the loop only when the counter is provably never advanced. This is genuine partial-correctness vacuity but its faithful patch can NEVER complete under the harness, so it cannot yield `completed AND not resolved` and is classified inconclusive (not a break) by the framework's own resolve criterion. EXCLUDED from the submitted attack set because a guaranteed-not-completing patch would force _derive_audit_verdict to fail-closed INCONCLUSIVE on a framework-wide artifact unrelated to this bundle's refinement fidelity; disclosed here for full transparency.

VERDICT: SOUND. Terminating domain airtight (5 distinct terminating wrong impls all fail to verify; 2 verifying impls are combineAll echoes whose gold faithful patch RESOLVES). No verifying wrong impl produces a completing-non-resolving patch. >=5 attacks run (7 submitted), prepatch reproduced (atk_3), positive control verifies. The lone verify-not-correct residue (non-termination) is out of the resolve-based gate's scope by the framework's deliberate `completed AND not resolved` break definition.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function combineByTag faithfully models the post-patch grouping tail of _symbolic_factor_list/sqf_list (collapse factor list by multiplicity, product within each group, each multiplicity appears once). Evidence: (1) G-CONF conformance_check.py replayed against the REAL patched repo (base 3dff1b9 + gold patch.diff) — 100006 inputs, seed 18698, 0 disagreements. (2) Hand-picked adversarial probes beyond the fuzz distribution all MATCH the real patched sqf_list: triple factors sharing m=7, seven factors sharing m=2, three multiplicity-groups of two, non-monic bases (2x+1,2x-1,x) sharing m=3, quadratic irreducibles sharing m=3. (3) Solution.lean verifies clean (lean_verify exit 0). Spec-region note: same_spec(Solution, prepatch)=False but the ONLY difference is the prove_correct proof body (incomplete elision); method signature, combineAll model, and BOTH ensures clauses (out=combineAll items; Nodup on tags) are byte-identical, so the spec is unchanged. The single shadow-vs-oracle divergence I could construct (rational roots, product coeff=1/6 -> shadow x^2-5x/6+1/6 vs oracle 6x^2-5x+1) is EXPLICITLY out of the modeled domain: mapping.md scopes to monic products with coeff==1, and the real _symbolic_factor_list separates the numeric coeff before the grouping tail (confirmed sqf_list(6*(x-1)^3*(x-2)^3)->(6,[(x^2-3x+2,3)]) — factors still group correctly). The spec makes no claim about the numeric coefficient, so this is a legitimate abstraction boundary, not repo drift. No input within the modeled domain makes the spec disagree with the real callee. Spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: no hard failures). same_spec(Solution, Solution_prepatch) = True — the spec region is byte-identical, and the spec view elides both impl and prove_correct bodies. Spec view inspected line-by-line: no diff markers, no patched file path (polytools.py absent), no gold-patch line reproduced, no narration terms, and crucially NO patched repo symbol is named — the model uses only abstract vocabulary (combineByTag/combineAll/combineInto/Item/Content) and never mentions _symbolic_factor_list, sqf, sqf_list, reduce, mul, or factors. The behavioral spec it encodes (each distinct tag appears exactly once carrying the combination of all values sharing it; ensures (out.map Prod.snd).Nodup) is a faithful ABSTRACTION of exactly the behavior the public problem_statement already fully discloses: sqf_list should return one factor per multiplicity (the product), e.g. (x**2-5x+6, 3) rather than two factors of multiplicity 3. tag<->multiplicity and value-combine<->polynomial product is the standard R bridge documented in mapping.md/refinement.md; it localizes no edit beyond the public issue. The discriminating Nodup/collapse clause directly restates the problem_statement's 'one factor of a given multiplicity' requirement and reveals nothing beyond it. No leakage beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
