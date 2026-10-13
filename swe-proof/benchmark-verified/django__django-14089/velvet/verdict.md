# P2 adversarial audit — django__django-14089

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_forward.lean`, `atk_2_partial_domain_len3.lean`, `atk_3_boundary_demand_offbyone.lean`, `atk_4_boundary_truncated_drain.lean`, `atk_5_oracle_echo_positional_answers.lean`, `atk_6_bypositition_indexable.lean`, `atk_7_control_flow_second_drain_rereads.lean`, `atk_8_held_distinct_three.lean`, +6 more |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_forward.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
-    let given := result.head?
-    let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
+    let given := elements.head?
+    let remaining := elements.tail
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := elements
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 2 — `atk_2_partial_domain_len3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,9 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
-    let given := result.head?
-    let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
+    let base : List Int := if elements.length ≤ 3 then result else elements
+    let given := base.head?
+    let remaining := base.tail
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +149,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +157,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := base
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +182,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 3 — `atk_3_boundary_demand_offbyone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -158,8 +147,7 @@
       decreasing demand - j
     do
       j := j + 1
-    let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
+    let drawn := List.take (demand + 1) remaining
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -167,18 +155,11 @@
       decreasing remaining.length - k
     do
       k := k + 1
-    let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
+    let firstDrain := List.drop (demand + 1) remaining
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 4 — `atk_4_boundary_truncated_drain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := List.take (result.length - 1) result
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 5 — `atk_5_oracle_echo_positional_answers.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
-    let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
+    let positional : Option Int := result.head?
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 6 — `atk_6_bypositition_indexable.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
-    let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
+    let byPosition : List Int := result
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 7 — `atk_7_control_flow_second_drain_rereads.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
-    let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
+    let secondDrain := remaining
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 8 — `atk_8_held_distinct_three.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,18 +156,11 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
-    let heldDistinct : Nat := 1
+    let heldDistinct : Nat := 3
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
     -- impl-end
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 9 — `atk_9_lazy_fresh_drain_empty.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +156,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := []
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 10 — `atk_10_control_flow_drain_restarts.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -167,18 +155,11 @@
       decreasing remaining.length - k
     do
       k := k + 1
-    let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
+    let firstDrain := remaining
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 11 — `atk_11_dedupe_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,9 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
-    let given := result.head?
-    let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
+    let base : List Int := revSeq (List.dedup elements)
+    let given := base.head?
+    let remaining := base.tail
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +149,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +157,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := base
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +182,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 12 — `atk_12_reorder_rotate.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,9 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
-    let given := result.head?
-    let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
+    let base : List Int := result.tail ++ List.take 1 result
+    let given := base.head?
+    let remaining := base.tail
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +149,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,17 +157,10 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := base
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
     let heldDistinct : Nat := 1
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
@@ -200,10 +182,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 13 — `atk_13_held_zero.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,8 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
     let given := result.head?
     let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +148,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,18 +156,11 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
     let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
-    let heldDistinct : Nat := 1
+    let heldDistinct : Nat := 0
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
     -- impl-end
@@ -200,10 +181,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

Attack 14 — `atk_14_all_empty_vacuity_control.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,13 +126,6 @@
   ensures out.2.2.2.2.2.2.2 = 1
   do
     -- impl-start
-    -- Materialize the backward enumeration, then observe the handles: ask one
-    -- handle itself for one element, advance it `demand` further single steps,
-    -- read what is left, then read what is left again; ask a fresh handle for the
-    -- element at a position; ask a fresh handle to yield everything; try to
-    -- collect a fresh handle's elements position by position; and ask a fresh
-    -- handle twice over to supply the thing that is to be stepped, counting the
-    -- distinct things that leaves the consumer holding.
     let mut result : List Int := []
     let mut i := elements.length
     while i > 0
@@ -144,12 +137,9 @@
       let e := elements[i - 1]!
       result := result ++ [e]
       i := i - 1
-    -- the handle's own answer to a single-element request, and what it has left
-    -- once it has answered
-    let given := result.head?
-    let remaining := result.tail
-    -- the handle's position after `demand` further single-element draws (it
-    -- stops early once the traversal is spent)
+    let base : List Int := ([] : List Int)
+    let given := base.head?
+    let remaining := base.tail
     let mut j := 0
     while j < demand ∧ j < remaining.length
       invariant j ≤ demand
@@ -159,7 +149,6 @@
     do
       j := j + 1
     let drawn := List.take j remaining
-    -- draining the same handle carries its position forward to the end
     let mut k := j
     while k < remaining.length
       invariant j ≤ k ∧ k ≤ remaining.length
@@ -168,18 +157,11 @@
     do
       k := k + 1
     let firstDrain := List.drop j remaining
-    -- the handle is spent, so draining it again yields nothing
     let secondDrain := List.drop k remaining
-    -- a fresh handle has no position to be read at, so it refuses the request
     let positional : Option Int := none
-    -- a fresh handle asked only to yield everything gives the whole enumeration
-    let freshDrain := result
-    -- collecting position by position stops at the very first refusal, so a
-    -- consumer taking elements that way ends up with none of them
+    let freshDrain := base
     let byPosition : List Int := []
-    -- asked to supply the thing to be stepped, the handle nominates ITSELF, and
-    -- does so again on a second asking, so the consumer holds one thing only
-    let heldDistinct : Nat := 1
+    let heldDistinct : Nat := 0
     return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
       byPosition, heldDistinct)
     -- impl-end
@@ -200,10 +182,15 @@
 
 prove_correct reverseEnum by
   loom_solve
-  · rw [revSeq_drop_step elements i (by omega) (by omega)]
-    simp_all
-  all_goals simp_all
-  case _ =>
-    rcases done_2 with h | h
-    · subst h; rfl
-    · rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+  all_goals try (rw [revSeq_drop_step elements i (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try (rcases done_2 with h | h <;>
+    first
+      | (subst h; rfl)
+      | rw [List.drop_eq_nil_of_le (by omega), List.drop_eq_nil_of_le (by omega)]
+      | rw [List.take_of_length_le (by omega), List.take_of_length_le (by omega)]
+      | simp_all
+      | omega)
+  all_goals try simp_all
+  all_goals try omega
+  all_goals try rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14089 (velvet). 14 attacks + 3 positive controls, all same_spec=True (swebench_unified.markers.same_spec) and all admissible (variant_scope.unsound_evasions == [] for every file, so none of them gets its exit code by assuming rather than establishing).

**VERDICT:** SOUND. No wrong impl verified, so per protocol step 2 there was no verifying-wrong-impl patch to materialize; `patches` is therefore empty by construction, not by omission. To prove that this is not an artifact of a dead oracle I nevertheless executed three real run_resolve calls (see RESOLVE ANCHORS).

METHOD NOTE (this is what made the attacks attributable). Attacks reuse the frozen spec byte-identically and differ only in the impl region, but the bundle's own proof script is a hand-tuned `loom_solve` + positional-bullet script that dies with a TACTIC error on a changed impl -- which is not a spec rejection. I replaced it with a generic `all_goals try...` script (proof script lives OUTSIDE the frozen spec markers, so same_spec stays True) and gated it on a positive control: pc_generic.lean (gold impl + generic script) VERIFIES, EXIT=0. Only then do the attacks' EXIT=1 count. First iteration of the generic script FAILED the positive control (residual ensures_6 goal) and I fixed it before reading any attack result; two attacks (5, 6) initially failed with `unexpected token`/`no obligation found` from a template bug in my generator, were repaired, and re-run to a real ensures rejection. Neither the broken-script nor the broken-template runs are counted as evidence.

**COMMANDS.** Build: python3 gen.py. Same-spec: the documented markers.same_spec one-liner, run over every *.lean (all True).

### POSITIVE CONTROLS (all EXIT=0):
  pc.lean         = bundle Solution.lean verbatim (bundle proof script).
  pc_generic.lean = gold impl + the generic proof script used by every attack.
  pc_reshape.lean = CORRECT RESHAPE (observations returned inline in the tuple rather than via named lets) -- verifies, so the spec is not over-fitted to one syntactic form and the attacks' rejections are behavioural, not stylistic.

ATTACKS (all EXIT=1; each rejection attributable to a NAMED ensures case, `error: unsolved goals` only, no tactic error, no timeout/crash -- so no retained-label hazard): atk_1_prepatch_forward           PREPATCH BUG re-encoded: no `__reversed__`, handle enumerates FORWARD (iter(self.dict)). ensures_8/7/6/3. => prepatch_reproduced=true.

Matches refinement.md's recorded prepatch failure (ensures_7 out.1, ensures_2 fresh drain in its numbering). atk_2_partial_domain_len3        PARTIAL DOMAIN: reversed only when length<=3 (the F2P witness size), forward beyond. ensures_8/7/6/3. atk_11_dedupe_domain             DOMAIN: reversal of the DEDUPED forward sequence -- agrees with gold on every distinct-key input, differs only where `elements` repeats. ensures_8/7/6/3. atk_12_reorder_rotate            REORDER: rotate-by-one instead of reverse. ensures_8/7/6/3. atk_3_boundary_demand_offbyone   BOUNDARY: take/drop (demand+1) -- one extra single draw, drain resumes one late. ensures_7/6. atk_4_boundary_truncated_drain   BOUNDARY: fresh drain loses the last element. ensures_3. atk_5_oracle_echo_positional_answers  UNGROUNDED-ORACLE ECHO of the `Sneaky` carrier: bare positional read ANSWERS with an element. ensures_4 (C4). atk_6_bypositition_indexable     legacy sequence-protocol carrier: elements ARE collectable position by position. ensures_2 (C6). atk_7_control_flow_second_drain_rereads  CONTROL-FLOW/EFFECT: re-readable snapshot, second drain hands the elements over again. ensures_5 (C3). atk_10_control_flow_drain_restarts       CONTROL-FLOW/EFFECT: drain restarts from the beginning, repeating the already-drawn elements. ensures_6 (C2). atk_9_lazy_fresh_drain_empty     `LazyIter`: nothing to give until advanced. ensures_3 (C5). atk_8_held_distinct_three        C7: handle nominates a SEPARATE walker, consumer holds 3 distinct things. ensures_1. atk_13_held_zero                 C7 other boundary: nominates nothing, holds 0. ensures_1. atk_14_all_empty_vacuity_control VACUITY CONTROL: every channel empty. ensures_1/3/6/7/8 -- the spec is not vacuously satisfiable.

### RESOLVE ANCHORS (executed, resolve_probe.py, harness.run_resolve, logs resolve_{gold,forward,container}.log):
  gold `return reversed(self.dict)`      -> resolved=True,  F2P test_reversed success, all 43 P2P pass, attempts=1.
  forward `return iter(self.dict)`       -> resolved=False, F2P test_reversed FAILURE, 3 attempts, 'consistent - not flaky'. This is the faithful refined patch of atk_1, which the spec REJECTS -- spec verdict and oracle verdict agree.
  container `return list(self.dict)[::-1]` -> resolved=False, F2P FAILURE, 3 attempts, consistent. Faithful refined patch of a re-readable-snapshot carrier, which the spec rejects via C0/C2/C3/C7 -- again agreeing.
So the resolve lane is live and discriminating in both directions; 'no attack verified' is a real measurement.

A-LEG AUDIT (the assigned focus). axioms region is EMPTY (no consumed axiom; grep for axiom/sorry/ContractOnly in Solution.lean = 0), so the only kind-A leg is A2, an A-REFERENCE. Tag census over refinement.md: 1 A-reference + 1 R + 7 (R+I) = 9 rows, NO kind-3 -- conforms to architecture.md 5.
  * A2 correspondence independently re-derived (axref.py, 30000 fuzz inputs, seed 20240815) using revSeq transcribed LITERALLY from the Lean front-recursion: list(reversed(dict.fromkeys(items))) == revSeq(list(d)) == list(d)[::-1] on every input; plus gold's C7 self-nomination (iter(h) is h twice over => exactly 1 distinct object), C3 one-shot, and A6 read-only. All hold. The bundle's own axiom_check.py (G-AX) also passes: EXIT=0, 9 boundary + 20000 fuzz.
  * Model<->patch correspondence measured directly (measure_gold.py): gold's carrier satisfies ALL EIGHT frozen clauses on 11 boundary cases incl. the F2P witness at demand 0/1/2/7, empty at two demands, singleton, duplicate-collapsing, and a 40-element collection at demand 39/40. The pinned constants none/[]/[]/1 (C4/C3/C6/C7) are honest, not convenient.
  * REFINEMENT DIRECTION (the only way this spec could break, since all 8 outputs are pinned to closed functions of `elements`): I built 10 CPython carriers as candidate `__reversed__` bodies and asked whether any satisfies all 8 observations yet FAILS F2P (carriers.py, exotic.py). gold, Sneaky, LazyIter, Container, forward, handle-ordinal adversary, IterPlusIndex, FreshWalker, InstanceIter (`__iter__` as instance attr only), LyingIter (`__class__` property lies). Result: every carrier that fails F2P is caught by at least one clause, and every carrier satisfying all 8 passes F2P. C7 (heldDistinct=1) is load-bearing and not redundant: it is the ONLY clause catching FreshWalker-style '`__iter__` returns a fresh equivalent walker' (C7 got 2, want 1) and it independently catches Sneaky/Container/LazyIter. refinement.md B's closure argument (C0 => `__next__`, C5+C6 => `__iter__` via `_check_methods`) survived my attempt to evade it; the documented residues (empty collection non-discriminating for C4/C6; C4/C6 deliberately stronger than the ABC, confirmed by IterPlusIndex which passes F2P but fails C4/C6) are stated correctly and are in the sound direction (they shrink the admitted set, preserving verify => resolved).

DOCUMENTATION DEFECT (advisory, NOT a soundness break -- filed so it can be repaired). The frozen spec has EIGHT ensures clauses and an 8-component return tuple (Option Int x List Int x List Int x List Int x Option Int x List Int x List Int x Nat), but the prose documents only SEVEN observations:
  - refinement.md rows run A1..A9 and cover C0..C6 only; there is NO row for `out.2.2.2.2.2.2.2 = 1` (heldDistinct / C7). grep for 'heldDistinct' or 'C7' in refinement.md = 0 hits and in mapping.md = 0 hits.
  - refinement.md repeatedly says 'seven observations' / 'all seven clauses' (lines 26, 42, 60, 79, 212, 220, 237) and section C lists A3-A5,A7,A8,A9 as the traversal-behaviour legs, omitting the C7 leg.
  - mapping.md line 41 calls the carrier 'the 7-tuple Option Int x... x List Int' -- the wrong arity, missing the trailing Nat -- and its section 1 table has no C7 row.
  Notably the Solution.lean docstring AND conformance_check.py DO describe eight observations incl. the fifth handle (iter(h5) twice, count distinct objects held), so the gap is confined to refinement.md/mapping.md. Since C7 is a real, gold-satisfied, load-bearing clause (it is the sole catcher of FreshWalker above), the effect is an UNDER-documented but sound spec: the mapping omits a leg that exists and holds, rather than claiming a leg that does not. That is why the verdict is SOUND rather than BROKEN -- no verify => not-resolved counterexample exists. Recommend adding an A10 row (C7: out.2.2.2.2.2.2.2 = 1 <-> iter(h5) twice on a FRESH handle, distinct objects held incl. h5, tag R + I), a mapping.md section 1 C7 row, correcting '7-tuple' to '8-tuple' with the trailing Nat, and updating 'seven' -> 'eight' throughout.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_forward.lean`, `atk_2_partial_domain_len3.lean`, `atk_3_boundary_demand_offbyone.lean`, `atk_4_boundary_truncated_drain.lean`, `atk_5_oracle_echo_positional_answers.lean`, `atk_6_bypositition_indexable.lean`, `atk_7_control_flow_second_drain_rereads.lean`, `atk_8_held_distinct_three.lean`, +6 more |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch_forward.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain_len3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_demand_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary_truncated_drain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_oracle_echo_positional_answers.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_bypositition_indexable.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_control_flow_second_drain_rereads.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_held_distinct_three.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_lazy_fresh_drain_empty.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_control_flow_drain_restarts.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_dedupe_domain.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_reorder_rotate.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_held_zero.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_all_empty_vacuity_control.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14089 (velvet). 14 attacks + 3 positive controls, all same_spec=True (swebench_unified.markers.same_spec) and all admissible (variant_scope.unsound_evasions == [] for every file, so none of them gets its exit code by assuming rather than establishing).

**VERDICT:** SOUND. No wrong impl verified, so per protocol step 2 there was no verifying-wrong-impl patch to materialize; `patches` is therefore empty by construction, not by omission. To prove that this is not an artifact of a dead oracle I nevertheless executed three real run_resolve calls (see RESOLVE ANCHORS).

METHOD NOTE (this is what made the attacks attributable). Attacks reuse the frozen spec byte-identically and differ only in the impl region, but the bundle's own proof script is a hand-tuned `loom_solve` + positional-bullet script that dies with a TACTIC error on a changed impl -- which is not a spec rejection. I replaced it with a generic `all_goals try...` script (proof script lives OUTSIDE the frozen spec markers, so same_spec stays True) and gated it on a positive control: pc_generic.lean (gold impl + generic script) VERIFIES, EXIT=0. Only then do the attacks' EXIT=1 count. First iteration of the generic script FAILED the positive control (residual ensures_6 goal) and I fixed it before reading any attack result; two attacks (5, 6) initially failed with `unexpected token`/`no obligation found` from a template bug in my generator, were repaired, and re-run to a real ensures rejection. Neither the broken-script nor the broken-template runs are counted as evidence.

**COMMANDS.** Build: python3 gen.py. Same-spec: the documented markers.same_spec one-liner, run over every *.lean (all True).

### POSITIVE CONTROLS (all EXIT=0):
  pc.lean         = bundle Solution.lean verbatim (bundle proof script).
  pc_generic.lean = gold impl + the generic proof script used by every attack.
  pc_reshape.lean = CORRECT RESHAPE (observations returned inline in the tuple rather than via named lets) -- verifies, so the spec is not over-fitted to one syntactic form and the attacks' rejections are behavioural, not stylistic.

ATTACKS (all EXIT=1; each rejection attributable to a NAMED ensures case, `error: unsolved goals` only, no tactic error, no timeout/crash -- so no retained-label hazard): atk_1_prepatch_forward           PREPATCH BUG re-encoded: no `__reversed__`, handle enumerates FORWARD (iter(self.dict)). ensures_8/7/6/3. => prepatch_reproduced=true.

Matches refinement.md's recorded prepatch failure (ensures_7 out.1, ensures_2 fresh drain in its numbering). atk_2_partial_domain_len3        PARTIAL DOMAIN: reversed only when length<=3 (the F2P witness size), forward beyond. ensures_8/7/6/3. atk_11_dedupe_domain             DOMAIN: reversal of the DEDUPED forward sequence -- agrees with gold on every distinct-key input, differs only where `elements` repeats. ensures_8/7/6/3. atk_12_reorder_rotate            REORDER: rotate-by-one instead of reverse. ensures_8/7/6/3. atk_3_boundary_demand_offbyone   BOUNDARY: take/drop (demand+1) -- one extra single draw, drain resumes one late. ensures_7/6. atk_4_boundary_truncated_drain   BOUNDARY: fresh drain loses the last element. ensures_3. atk_5_oracle_echo_positional_answers  UNGROUNDED-ORACLE ECHO of the `Sneaky` carrier: bare positional read ANSWERS with an element. ensures_4 (C4). atk_6_bypositition_indexable     legacy sequence-protocol carrier: elements ARE collectable position by position. ensures_2 (C6). atk_7_control_flow_second_drain_rereads  CONTROL-FLOW/EFFECT: re-readable snapshot, second drain hands the elements over again. ensures_5 (C3). atk_10_control_flow_drain_restarts       CONTROL-FLOW/EFFECT: drain restarts from the beginning, repeating the already-drawn elements. ensures_6 (C2). atk_9_lazy_fresh_drain_empty     `LazyIter`: nothing to give until advanced. ensures_3 (C5). atk_8_held_distinct_three        C7: handle nominates a SEPARATE walker, consumer holds 3 distinct things. ensures_1. atk_13_held_zero                 C7 other boundary: nominates nothing, holds 0. ensures_1. atk_14_all_empty_vacuity_control VACUITY CONTROL: every channel empty. ensures_1/3/6/7/8 -- the spec is not vacuously satisfiable.

### RESOLVE ANCHORS (executed, resolve_probe.py, harness.run_resolve, logs resolve_{gold,forward,container}.log):
  gold `return reversed(self.dict)`      -> resolved=True,  F2P test_reversed success, all 43 P2P pass, attempts=1.
  forward `return iter(self.dict)`       -> resolved=False, F2P test_reversed FAILURE, 3 attempts, 'consistent - not flaky'. This is the faithful refined patch of atk_1, which the spec REJECTS -- spec verdict and oracle verdict agree.
  container `return list(self.dict)[::-1]` -> resolved=False, F2P FAILURE, 3 attempts, consistent. Faithful refined patch of a re-readable-snapshot carrier, which the spec rejects via C0/C2/C3/C7 -- again agreeing.
So the resolve lane is live and discriminating in both directions; 'no attack verified' is a real measurement.

A-LEG AUDIT (the assigned focus). axioms region is EMPTY (no consumed axiom; grep for axiom/sorry/ContractOnly in Solution.lean = 0), so the only kind-A leg is A2, an A-REFERENCE. Tag census over refinement.md: 1 A-reference + 1 R + 7 (R+I) = 9 rows, NO kind-3 -- conforms to architecture.md 5.
  * A2 correspondence independently re-derived (axref.py, 30000 fuzz inputs, seed 20240815) using revSeq transcribed LITERALLY from the Lean front-recursion: list(reversed(dict.fromkeys(items))) == revSeq(list(d)) == list(d)[::-1] on every input; plus gold's C7 self-nomination (iter(h) is h twice over => exactly 1 distinct object), C3 one-shot, and A6 read-only. All hold. The bundle's own axiom_check.py (G-AX) also passes: EXIT=0, 9 boundary + 20000 fuzz.
  * Model<->patch correspondence measured directly (measure_gold.py): gold's carrier satisfies ALL EIGHT frozen clauses on 11 boundary cases incl. the F2P witness at demand 0/1/2/7, empty at two demands, singleton, duplicate-collapsing, and a 40-element collection at demand 39/40. The pinned constants none/[]/[]/1 (C4/C3/C6/C7) are honest, not convenient.
  * REFINEMENT DIRECTION (the only way this spec could break, since all 8 outputs are pinned to closed functions of `elements`): I built 10 CPython carriers as candidate `__reversed__` bodies and asked whether any satisfies all 8 observations yet FAILS F2P (carriers.py, exotic.py). gold, Sneaky, LazyIter, Container, forward, handle-ordinal adversary, IterPlusIndex, FreshWalker, InstanceIter (`__iter__` as instance attr only), LyingIter (`__class__` property lies). Result: every carrier that fails F2P is caught by at least one clause, and every carrier satisfying all 8 passes F2P. C7 (heldDistinct=1) is load-bearing and not redundant: it is the ONLY clause catching FreshWalker-style '`__iter__` returns a fresh equivalent walker' (C7 got 2, want 1) and it independently catches Sneaky/Container/LazyIter. refinement.md B's closure argument (C0 => `__next__`, C5+C6 => `__iter__` via `_check_methods`) survived my attempt to evade it; the documented residues (empty collection non-discriminating for C4/C6; C4/C6 deliberately stronger than the ABC, confirmed by IterPlusIndex which passes F2P but fails C4/C6) are stated correctly and are in the sound direction (they shrink the admitted set, preserving verify => resolved).

DOCUMENTATION DEFECT (advisory, NOT a soundness break -- filed so it can be repaired). The frozen spec has EIGHT ensures clauses and an 8-component return tuple (Option Int x List Int x List Int x List Int x Option Int x List Int x List Int x Nat), but the prose documents only SEVEN observations:
  - refinement.md rows run A1..A9 and cover C0..C6 only; there is NO row for `out.2.2.2.2.2.2.2 = 1` (heldDistinct / C7). grep for 'heldDistinct' or 'C7' in refinement.md = 0 hits and in mapping.md = 0 hits.
  - refinement.md repeatedly says 'seven observations' / 'all seven clauses' (lines 26, 42, 60, 79, 212, 220, 237) and section C lists A3-A5,A7,A8,A9 as the traversal-behaviour legs, omitting the C7 leg.
  - mapping.md line 41 calls the carrier 'the 7-tuple Option Int x... x List Int' -- the wrong arity, missing the trailing Nat -- and its section 1 table has no C7 row.
  Notably the Solution.lean docstring AND conformance_check.py DO describe eight observations incl. the fifth handle (iter(h5) twice, count distinct objects held), so the gap is confined to refinement.md/mapping.md. Since C7 is a real, gold-satisfied, load-bearing clause (it is the sole catcher of FreshWalker above), the effect is an UNDER-documented but sound spec: the mapping omits a leg that exists and holds, rather than claiming a leg that does not. That is why the verdict is SOUND rather than BROKEN -- no verify => not-resolved counterexample exists. Recommend adding an A10 row (C7: out.2.2.2.2.2.2.2 = 1 <-> iter(h5) twice on a FRESH handle, distinct objects held incl. h5, tag R + I), a mapping.md section 1 C7 row, correcting '7-tuple' to '8-tuple' with the trailing Nat, and updating 'seven' -> 'eight' throughout.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-2 (faithfulness-break) on django__django-14089 velvet bundle. Searched for an input where the modelled `reverseEnum` disagrees with the real patched callee (`OrderedSet.__reversed__` = `reversed(self.dict)`). NONE FOUND.

SETUP / PROVENANCE
- Reference = fresh worktree of the upstream repository at base_commit d01709aae21de9cd2565b9c52f32732ea28a2d98 with patch.diff APPLIED (gold hunk confirmed present: `def __reversed__(self): return reversed(self.dict)` inserted between `__iter__` and `__contains__`). Base commit used only for the untouched carrier neighbours (`__init__` `dict.fromkeys(iterable or ())`, `__iter__` `iter(self.dict)`), which is what the mapping's R-refinement rests on.
- Spec region byte-identity: `swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True`. Confirmed independently via `region_hashes`: spec_view = 5b4e3eaea45b7248526c68c0b38fce2194e908d56bd2871bc8818dd460bfb52c and pure = 2bca17942245fb50d67f079c68573f5f2d9cb123dda3c2cc3825d855bbafe71c are IDENTICAL across Solution and prepatch; only the `impl` hash differs (c40b207f vs 1a85a1fa). So G-DIFF's failure is the impl sensing the change, not a spec edit.
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (elaborates, no sorry/error), so the spec does admit the gold-faithful impl; it is not vacuously over-strong.
- Solution.lean sha256 a4755d8ca528... matches the sources recorded by G-AX/G-CONF/G-GOLD/G-VERIFY/G-HYGIENE/G-MUT/G-LEAK/G-PBT/G-INTEGRITY (all pass).

INDEPENDENT PROBES (hand-written from the Lean text; I did NOT reuse conformance_check.py's shadow, and I used a DIFFERENT fuzz seed 999331 vs G-CONF's pinned 14089)
1. All 8 ensures clauses vs the real patched callee over 30,023 inputs -> 0 divergences. Clauses evaluated literally: out.1 = (revSeq elements).head?; out.2.1 = List.take demand (revSeq elements).tail; out.2.2.1 = List.drop demand tail; out.2.2.2.1 = []; out.2.2.2.2.1 = none; out.2.2.2.2.2.1 = revSeq elements; out...2.1 = []; out...2.2 = 1. Oracle observed exactly as the docstring prescribes (5 handles from one unchanged collection). Read-only assertion `list(iter(coll))` unchanged after every observation: held on every input.
2. Deep-model / A-reference leg checked independently: `list(reversed(dict.fromkeys(items))) == revSeq(list(dict.fromkeys(items)))` over 20,008 inputs -> 0 bad; `reversed(d)` is a collections.abc.Iterator on all; `list(iter(d))` undisturbed. Matches G-AX's claim without relying on axiom_check.py. The `axioms` region really is empty, so nothing is delegated to a consumed axiom.
3. Adversarial corners, incl. an UNBOUNDED reading of C6 (getitem 0,1,2,... with no len(collection)+1 cap, up to 5000) rather than the capped loop conformance_check.py uses: still []. Also empty collection at demand 0/1/10^6/10^7; singleton at demand 10^9; demand exactly draining the remainder and far past the end; 200-, 500- and 1000-element collections; negative and `2**63`-magnitude keys; and hash-collapsing inputs [True,False], [0,False], [1,True] where 0==False / 1==True collapse to one dict key (the case most likely to break the List-Int carrier bijection). 16/16 agree.
4. F2P leg checked directly on the patched tree: `isinstance(reversed(OrderedSet([1,2,3])), collections.abc.Iterator)` is True and `list(...) == [3,2,1]`. Handle type is `dict_reversekeyiterator`; `hasattr(type(h),'__getitem__')` is False (so C4/C6's `none`/`[]` are honest, not artefacts of the harness swallowing exceptions) and `iter(h) is h` (so C7's held_distinct = 1 is real, and the id-reuse worry is moot since iter returns the identical object rather than a fresh one).

### OVER-STRENGTH ANALYSIS (my specific mandate: is the spec too strong / drifted?)
The two clauses that are genuinely stronger than the F2P assertion are C4 (bare positional read refused) and C6 (position-by-position collection yields nothing). refinement.md §B declares this residue openly: an object that is a genuine Iterator AND additionally supports subscripting would satisfy the F2P yet fail C4/C6. I confirmed this is the SOUND direction: it shrinks the admitted set, so `verify => resolved` is preserved, and it cannot manufacture a false FAITHFUL. Critically, gold itself satisfies C4 and C6 over the entire measured domain (dict_reversekeyiterator exposes neither mp_subscript nor sq_item), so over-strength here does NOT translate into any input where the model disagrees with the real callee.

Same for C7: generators, list_reverseiterator and dict_reversekeyiterator all return themselves from iter(), so held_distinct = 1 is a property gold has, not an invented requirement. Also considered and dismissed as a faithfulness break: there is NO distinctness precondition on `elements`, so the spec is universally quantified over duplicate-bearing List Int that lie outside the image of the mapping bijection (self.dict keys are distinct by construction). That makes the spec stronger, not weaker, and on such a list the deep model is still plain reversal, which any reversal impl satisfies -- gold verifies regardless (confirmed by lean_verify EXIT=0). No real-repo input corresponds to a duplicate `elements`, so no divergence arises.

The acknowledged empty-collection blind spot (neither C4 nor C6 discriminates at elements = []) is a completeness limit on the reject lane, not unfaithfulness: at [] the model and the real callee AGREE (given=none, all lists [], positional=none, held=1 -- measured). It cannot be cited as a diverging input.

### STALE-RECORD NOTE (not a finding)
meta.json shows G-EQ fail and G-PANEL-1 fail recorded against Solution.lean sha 7f2efab161bc..., an OLDER artefact, whereas the current Solution.lean is a4755d8ca528.... The G-EQ note describes atk7_legacycarrier.lean verifying while failing the F2P -- exactly the legacy-`__getitem__` hole that the current spec closes with C6 (and C7). Those two failures therefore judge a spec that has since been repaired; I re-derived the legacy-carrier argument against the CURRENT clause set and C6 does close it (C5 says a drain yields everything, C6 says the 0,1,2,... request sequence through the object's own element-at-position access yields nothing -- mutually inconsistent for a legacy sequence-protocol carrier, hence `__iter__` must exist; C0 gives `__next__`; the subclass hook is `_check_methods`(C,'`__iter__`','`__next__`')). Recording per the stale-audit rule so this is not mistaken for fresh spec weakness.

**CONCLUSION:** no diverging input exists on the tested domain (~50k independent inputs across two probes plus targeted corners, disjoint seed from G-CONF). The spec is faithful to the patched repo behaviour; its excess strength is in the admitted-set-shrinking direction and is disclosed in refinement.md. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ATTACKER 3 (leakage / gold-reconstruction), django__django-14089 velvet. Verdict NO-LEAKAGE. Every measurement below was re-run by me; nothing read off a stamp.

**NO RELAXATION IN THIS BUNDLE.** meta.json has no `relaxed_leakage` key (top-level keys: axioms, band, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling, version) and no RELAXED_LEAKAGE.md exists anywhere under benchmark-verified/django__django-14089/. So there is no unavoidability argument to adjudicate: this is an ordinary strict-mode review, judged against the solver-visible problem_statement only (hints_text for this row is the empty string, so the PS/hints distinction is moot here).

**SPEC REGION BYTE-IDENTICAL.** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True; spec_signature equal; and markers.spec_view is byte-identical between the two files. So the discriminating content lives entirely in impl/proof, which spec_view elides. Confirmed the prepatch file's giveaway narration (its impl comment says 'Pre-image skeleton... prove_correct MUST fail') is NOT in its spec view -- 'Pre-image'/'MUST fail' both absent -- and leakage.screen on the prepatch source also passes.

MECHANICAL SCREEN, RE-RUN. leakage.screen(Solution.lean, VelvetBackend.language, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. leakage.reviewer_directed(spec_view)=[] and also [] on refinement.md, mapping.md, verdict.md, meta.json. LIVENESS CONTROL (so the pass is not a lexer that never saw the prose): I injected into the method docstring 'This was previously buggy: the fix adds `__reversed__` returning reversed(self.dict) to OrderedSet in django/utils/datastructures.py' and the screen went passed=False with 3 hard failures (L2 patched-file-path x2, L3 narration 'previously' at line 33). The screen genuinely reads the long narration block.

TOKEN SWEEP OF THE ACTUAL SPEC VIEW (markers.spec_view output -- the only artifact eval/adapter.py:304-319 derives for a solver, fenced by eval/prompts.py:77,82, and it raises rather than expose an unelided impl/proof). Gold adds exactly two lines: `def __reversed__(self):` / `return reversed(self.dict)`. Of the identifiers in that addition, `__reversed__`, dict and reversed are ALL ABSENT from the spec view; only the generic Lean tokens def/return/self appear (`def revSeq`, `return (given,...)`, and English 'itself/self-consuming' -- `revSeq` does not embed 'reversed'). Also absent: OrderedSet, self.dict, `__iter__`, `__getitem__`, `__next__`, StopIteration, datastructures, django, collections.abc, Iterator, isinstance, and the F2P literals [1, 2, 3] / [3, 2, 1] / '3, 2, 1'.

The narration describes the observable in consumer vocabulary ('handle', 'backward enumeration', 'element AT A POSITION') and states the reversal relation, which the public PS already gives: the PS says OrderedSet 'isn't reversible', that reversibility 'would be natural to support given that OrderedSet is ordered', and names the remedy 'adding a `__reversed__`() method'. The spec view names strictly LESS than the PS -- the PS supplies the method name, the spec view does not.

DISCRIMINATION IS REAL, NOT NARRATED. scripts/lean_verify.sh on Solution.lean -> exit 0 (verifies); on Solution_prepatch.lean -> exit 1, unsolved goals of the shape `result_1.head? = (revSeq result_1).head?` and `List.take j result_1.tail = List.take demand (revSeq result_1).tail` (forward vs reversed enumeration). Since the two files share a byte-identical spec view, the frozen 8-clause contract by itself rejects the forward-order pre-image -- so nothing needed to be leaked into the spec text to make the spec sense the missing backward enumeration.

**PRIVATE MATERIAL STAYS PRIVATE.** mapping.md and refinement.md DO name `reversed(self.dict)`, `dict_reversekeyiterator`, datastructures.py:25-26 and the F2P assertion, but they are not in the consumer view (adapter derives it from Solution.lean alone), so they are not a leakage channel for this gate.

BUNDLE-ADDRESSES-REVIEWER FINDING (reported per instruction; does not change my verdict). No file instructs me how to record. However velvet/verdict.md carries, in-band, two copies of a prior attacker-3 record for this exact cell, headed 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)' with 'Verdict NO-LEAKAGE' (around lines 2500-2547) -- i.e. the artifact under review contains the expected verdict for my own lane. I reached my conclusion from my own screen, sweep, same_spec check and both lean_verify runs before reading it, and I flag it because a verdict transcript inside the reviewed artifact is an anchoring channel regardless of intent. That prior record's own claim that patch.diff is absent is stale: patch.diff is present at the instance root and matches the frozen row.

STALE-GATE NOTE (bucketed by reason, not re-judged as the reject lane). meta.json records G-EQ, G-PANEL and G-PANEL-1 as fail, but all three carry sources hash 7f2efab161bc4bad while the live Solution.lean is a4755d8ca5285599 -- they were stamped against a superseded artifact. The gates my verdict leans on all carry the CURRENT hash and pass: G-LEAK (a4755d..., 'spec view clean'), G-HYGIENE, G-INTEGRITY, G-GOLD, G-DIFF ('Solution_prepatch.lean: verification failed'), G-VERIFY, G-CONF, G-AX, G-MUT (20/20), G-PBT. I independently re-confirmed the two checkable here: same_spec/spec_view identity of the frozen region, and gold-verifies / prepatch-fails. Integrity also re-checked: instance.json patch, problem_statement and patch.diff are all byte-equal to the frozen dataset row.

Facet re-confirmed: the spec view discloses no gold identifier, file path, or remedy beyond what the public problem_statement already states, and the contract discriminates gold from pre-image on its own.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
