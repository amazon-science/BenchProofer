# P2 adversarial audit — mwaskom__seaborn-3187

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verifies, so no faithful patch could be materialized FOR A VERIFYING CANDIDATE (patches={} for that reason, not for lack of trying -- I did materialize and RUN 5 real patches anyway, see below). WHY NONE CAN EXIST -- I did not rely on the prior pass's certificate; I re-derived it independently from the SHIPPED spec text at determinacy.lean. cmd: timeout 400 bash scripts/lean_verify.sh determinacy.lean 300 -> EXIT=0, no sorry (grep sorry = 0). It proves fst_pinned, spec1_unique, spec2_unique (problem_spec_X r ticks a -> problem_spec_X r ticks b -> a = b) and the composition spec1_determines: for ANY impl, (forall r ticks, problem_spec_1 r ticks (impl r ticks)) -> forall r ticks, impl r ticks = gold_impl r ticks. #print axioms: spec1_unique / spec2_unique / fst_pinned = [labelValue, propext, render, Quot.sound] -- CLEAN, and crucially they do NOT depend on render_length or render_uncompacted_faithful, so determinacy is immune to the axiom-faithfulness defect reported below. MECHANISM: clauses 1-2 pin result.fst by a TOTAL case split (uncompacted r is some/none exactly as r.compactionCapable is true/false, so no input escapes), and clause 3 (labels = render writtenFrom ticks) then pins result.snd from that already-fixed fst. Both post-conditions are therefore FUNCTIONAL: verify => extensionally-identical-to-gold, so the only same-spec impls that can verify are re-spellings of gold, which resolve. verify=>correct cannot fail by a wrong-value impl for this bundle. This closes the search rather than sampling it, which is why the 17 attacks below all fail for a structural reason.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,8 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PRE-PATCH (buggy): labels written straight from the renderer as it arrives.
+  (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +215,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,9 +285,6 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
   match uncompacted r with
   | some r' => (r', render r' ticks)
   | none    => (r, render r ticks)
@@ -285,27 +298,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,9 +203,6 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
   match uncompacted r with
   | some r' => (r', render r' ticks)
   | none    => (r, render r ticks)
@@ -219,29 +216,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +286,8 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PRE-PATCH (buggy): labels written straight from the renderer as it arrives.
+  (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +298,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,9 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- Turn the compacting mode off UNCONDITIONALLY: no capability guard at all.
+  let r' : TickRenderer := { r with compacting := false }
+  (r', render r' ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +216,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +286,9 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- Turn the compacting mode off UNCONDITIONALLY: no capability guard at all.
+  let r' : TickRenderer := { r with compacting := false }
+  (r', render r' ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +299,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,9 +203,6 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
   match uncompacted r with
   | some r' => (r', render r' ticks)
   | none    => (r, render r ticks)
@@ -219,29 +216,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +286,9 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- Turn the compacting mode off UNCONDITIONALLY: no capability guard at all.
+  let r' : TickRenderer := { r with compacting := false }
+  (r', render r' ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +299,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,14 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PARTIAL DOMAIN: only act where the read-back clause is actually claimed
+  -- (every tick inside the 2^53 channel); outside it, behave like PRE-PATCH.
+  if ticks.all (fun t => decide (t.natAbs ≤ 9007199254740992)) then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +221,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +291,14 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PARTIAL DOMAIN: only act where the read-back clause is actually claimed
+  -- (every tick inside the 2^53 channel); outside it, behave like PRE-PATCH.
+  if ticks.all (fun t => decide (t.natAbs ≤ 9007199254740992)) then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +309,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,14 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PARTIAL DOMAIN: act only for a bare-numeral renderer, exactly where the
+  -- read-back clause is claimed.  A dressed renderer keeps the PRE-PATCH path.
+  if r.numeralStyle then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +221,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +291,14 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- PARTIAL DOMAIN: act only for a bare-numeral renderer, exactly where the
+  -- read-back clause is claimed.  A dressed renderer keeps the PRE-PATCH path.
+  if r.numeralStyle then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +309,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,15 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- BOUNDARY: a tick set with at most one entry hoists no COMMON magnitude, so
+  -- "no fix is needed" -- leave the renderer exactly as it stands there.
+  match ticks with
+  | []      => (r, render r ticks)
+  | [_]     => (r, render r ticks)
+  | _ :: _  =>
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +222,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +292,15 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- BOUNDARY: a tick set with at most one entry hoists no COMMON magnitude, so
+  -- "no fix is needed" -- leave the renderer exactly as it stands there.
+  match ticks with
+  | []      => (r, render r ticks)
+  | [_]     => (r, render r ticks)
+  | _ :: _  =>
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +311,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,11 +203,10 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- CONTROL-FLOW-EFFECT: report the mode-off renderer, but write the labels
+  -- from the renderer as it AROSE (format_ticks called BEFORE the set_* calls).
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' => (r', render r ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -219,29 +218,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,11 +288,10 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- CONTROL-FLOW-EFFECT: report the mode-off renderer, but write the labels
+  -- from the renderer as it AROSE (format_ticks called BEFORE the set_* calls).
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' => (r', render r ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -285,27 +303,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,11 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- UNGROUNDED-ORACLE ECHO: compose the label texts by a PRIVATE route of the
+  -- right length instead of letting the renderer write them.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', List.replicate ticks.length "0")
+  | none    => (r, List.replicate ticks.length "0")
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +218,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +288,11 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- UNGROUNDED-ORACLE ECHO: compose the label texts by a PRIVATE route of the
+  -- right length instead of letting the renderer write them.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', List.replicate ticks.length "0")
+  | none    => (r, List.replicate ticks.length "0")
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +303,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,13 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- WRONG DISCRIMINANT: guard on the CURRENT compacting mode instead of on the
+  -- capability (in Python: `if formatter.get_useOffset():` rather than hasattr).
+  if r.compacting then
+    let r' : TickRenderer := { r with compacting := false }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +220,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +290,13 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- WRONG DISCRIMINANT: guard on the CURRENT compacting mode instead of on the
+  -- capability (in Python: `if formatter.get_useOffset():` rather than hasattr).
+  if r.compacting then
+    let r' : TickRenderer := { r with compacting := false }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +307,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,11 +203,12 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- EXTRA-STATE: also force the numeral style, a component that is NOT the
+  -- builder's to choose (Python: also calling set_useMathText(False)).
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with numeralStyle := true }
+    (r'', render r'' ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -219,29 +220,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,11 +290,12 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- EXTRA-STATE: also force the numeral style, a component that is NOT the
+  -- builder's to choose (Python: also calling set_useMathText(False)).
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with numeralStyle := true }
+    (r'', render r'' ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -285,27 +307,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,10 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- REORDER: the right renderer, but its output for the REVERSED tick set.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', render r' ticks.reverse)
+  | none    => (r, render r ticks.reverse)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +217,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +287,10 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- REORDER: the right renderer, but its output for the REVERSED tick set.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', render r' ticks.reverse)
+  | none    => (r, render r ticks.reverse)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +301,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,11 +203,13 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- DEEP-MODEL TAMPERING: compaction off, but `convention` (the formatter class
+  -- + the view interval it reads) replaced by a default -- Python: substituting
+  -- a fresh ScalarFormatter() for the axis's own formatter.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with convention := 0 }
+    (r'', render r'' ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -219,29 +221,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,11 +291,13 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- DEEP-MODEL TAMPERING: compaction off, but `convention` (the formatter class
+  -- + the view interval it reads) replaced by a default -- Python: substituting
+  -- a fresh ScalarFormatter() for the axis's own formatter.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with convention := 0 }
+    (r'', render r'' ticks)
   | none    => (r, render r ticks)
 -- impl-end
 -- proof-start
@@ -285,27 +309,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,15 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- CAPABILITY FLIP: report the renderer as offering the opposite control from
+  -- the one it intrinsically has.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with compactionCapable := false }
+    (r'', render r'' ticks)
+  | none    =>
+    let r'' : TickRenderer := { r with compactionCapable := true }
+    (r'', render r'' ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +222,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +292,15 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- CAPABILITY FLIP: report the renderer as offering the opposite control from
+  -- the one it intrinsically has.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' =>
+    let r'' : TickRenderer := { r' with compactionCapable := false }
+    (r'', render r'' ticks)
+  | none    =>
+    let r'' : TickRenderer := { r with compactionCapable := true }
+    (r'', render r'' ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +311,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,10 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
+  -- DROP: the right renderer's own text, but the last label is dropped.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', (render r' ticks).dropLast)
+  | none    => (r, (render r ticks).dropLast)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +217,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +287,10 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
+  -- DROP: the right renderer's own text, but the last label is dropped.
   match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  | some r' => (r', (render r' ticks).dropLast)
+  | none    => (r, (render r ticks).dropLast)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +301,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,9 +203,6 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
   match uncompacted r with
   | some r' => (r', render r' ticks)
   | none    => (r, render r ticks)
@@ -219,29 +216,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +286,10 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- Force the mode off even on a renderer that offers NO control for it
+  -- (Python: configuring the LogFormatter arm the gold patch leaves alone).
+  let r' : TickRenderer := { r with compacting := false, compactionCapable := true }
+  (r', render r' ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +300,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,17 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- EXPLOIT PROBE: where the read-back clause is VACUOUS (a renderer offering no
+  -- control, or a dressed one), emit a private label list; only render where the
+  -- clause actually bites.
+  if r.compactionCapable && r.numeralStyle then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    match uncompacted r with
+    | some r' => (r', List.replicate ticks.length "x")
+    | none    => (r, List.replicate ticks.length "x")
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -219,29 +224,49 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_continuousLegendLabels implementation_continuousLegendLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +294,17 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  -- EXPLOIT PROBE: where the read-back clause is VACUOUS (a renderer offering no
+  -- control, or a dressed one), emit a private label list; only render where the
+  -- clause actually bites.
+  if r.compactionCapable && r.numeralStyle then
+    match uncompacted r with
+    | some r' => (r', render r' ticks)
+    | none    => (r, render r ticks)
+  else
+    match uncompacted r with
+    | some r' => (r', List.replicate ticks.length "x")
+    | none    => (r, List.replicate ticks.length "x")
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -285,27 +315,47 @@
   obtain ⟨cap, comp, style, conv⟩ := r
   unfold problem_spec_legendEntryLabels implementation_legendEntryLabels
     uncompacted readsBackToTicks
-  cases cap with
-  | true =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
-    · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
-    · intro _ hstyle hdom
-      simp only [if_true]
-      refine ⟨render_length _ _, ?_⟩
-      intro i hi
-      exact render_uncompacted_faithful
-        { compactionCapable := true, compacting := false, numeralStyle := style,
-          convention := conv }
-        ticks rfl rfl hstyle hdom i hi
-  | false =>
-    refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp at h
-    · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
-    · intro h; simp at h
-
+  first
+  | (cases cap with
+     | true =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+       · intro h; simp at h
+       · simp only [if_true]
+       · simp only [if_true]; exact render_length _ _
+       · intro _ hstyle hdom
+         simp only [if_true]
+         refine ⟨render_length _ _, ?_⟩
+         intro i hi
+         exact render_uncompacted_faithful
+           { compactionCapable := true, compacting := false, numeralStyle := style,
+             convention := conv }
+           ticks rfl rfl hstyle hdom i hi
+     | false =>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩
+       · intro r' h; simp at h
+       · intro _; simp
+       · simp
+       · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+       · intro h; simp at h)
+  | (cases cap <;> cases comp <;> cases style <;>
+       refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> intros <;>
+       first
+       | rfl
+       | (exact render_length _ _)
+       | (exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) _ (by assumption))
+       | (constructor <;>
+            first
+            | (exact render_length _ _)
+            | (intro i hi
+               exact render_uncompacted_faithful _ _ rfl rfl (by assumption) (by assumption) i hi)
+            | simp_all [render_length, render_uncompacted_faithful]
+            | omega)
+       | simp_all [render_length, render_uncompacted_faithful]
+       | (simp_all; omega)
+       | omega
+       | decide
+       | aesop)
+  | simp_all [render_length, render_uncompacted_faithful]
+  | aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,13 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  if r.compactionCapable = true then
+    let r' : TickRenderer :=
+      { compactionCapable := r.compactionCapable, compacting := false,
+        numeralStyle := r.numeralStyle, convention := r.convention }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -221,13 +222,13 @@
     uncompacted readsBackToTicks
   cases cap with
   | true =>
+    simp only [if_true, reduceIte]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+    · intro r' h; simp only [Option.some.injEq] at h; simp [← h]
     · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro _ hstyle hdom
-      simp only [if_true]
       refine ⟨render_length _ _, ?_⟩
       intro i hi
       exact render_uncompacted_faithful
@@ -235,13 +236,13 @@
           convention := conv }
         ticks rfl rfl hstyle hdom i hi
   | false =>
+    simp only [Bool.false_eq_true, if_false]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
     · intro r' h; simp at h
     · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro h; simp at h
-
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +270,13 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  if r.compactionCapable = true then
+    let r' : TickRenderer :=
+      { compactionCapable := r.compactionCapable, compacting := false,
+        numeralStyle := r.numeralStyle, convention := r.convention }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -287,13 +289,13 @@
     uncompacted readsBackToTicks
   cases cap with
   | true =>
+    simp only [if_true, reduceIte]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+    · intro r' h; simp only [Option.some.injEq] at h; simp [← h]
     · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro _ hstyle hdom
-      simp only [if_true]
       refine ⟨render_length _ _, ?_⟩
       intro i hi
       exact render_uncompacted_faithful
@@ -301,11 +303,11 @@
           convention := conv }
         ticks rfl rfl hstyle hdom i hi
   | false =>
+    simp only [Bool.false_eq_true, if_false]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
     · intro r' h; simp at h
     · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro h; simp at h
-
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: 17 distinct same-spec attacks + a structurally-different positive control + an independently re-derived determinacy certificate + 5 EXECUTED run_resolve runs. same_spec=True machine-confirmed for all 18 .lean attack/control files via swebench_unified.markers.same_spec with backends.get_backend('lean').language (all True; only the diagnostic axchk_pos.lean is False, purely because two '#print axioms' lines are appended after the proof region -- it is not submitted as an attack). Verify cmd for every file: bash scripts/lean_verify.sh <path>, run 4-at-a-time as concurrent background jobs (runverify.sh / runverify2.sh / runverify3.sh in the scratch dir).

BASELINE + CONTROL. Shipped Solution.lean re-verified EXIT=0. pos_control.lean EXIT=0 (structurally different spelling: branches on 'if r.compactionCapable = true' and builds the TickRenderer record field-by-field instead of matching on 'uncompacted', proving the spec is not accidentally tied to gold's syntactic shape). Axioms of the control via axchk_pos.lean (EXIT=0): correct_continuousLegendLabels and correct_legendEntryLabels each depend on [labelValue, propext, render, render_length, render_uncompacted_faithful, Quot.sound] = CLEAN (only the bundle's declared axioms plus standard propext/Quot.sound; no sorryAx).

ATTACK LEDGER -- all 17 EXIT=1 with 'error: unsolved goals' at the clause positions, i.e. SEMANTIC rejection, not tactic weakness. Each attack carries a uniform maximal-effort proof script: 'first |' the exact gold script, '| ' a fully split (cases cap <;> cases comp <;> cases style) brute force chaining every tactic gold uses plus simp_all/omega/decide/aesop with both axioms supplied. atk_1 prepatch site 1 '(r, render r ticks)' [PREPATCH REPRODUCED]; atk_2 prepatch site 2 [PREPATCH REPRODUCED]; atk_3 UNCONDITIONAL turn-off, no capability guard, both sites; atk_4 same, site 2 only (the prior pass's named counterexample class, re-encoded); atk_5 PARTIAL-DOMAIN on the 2^53 guard (act only when all ticks in-range, else prepatch); atk_6 PARTIAL-DOMAIN on numeralStyle (act only for a bare-numeral renderer, i.e. exactly where the read-back clause bites); atk_7 BOUNDARY (tick sets of length <=1 'hoist no common magnitude' so left untouched); atk_8 CONTROL-FLOW-EFFECT ordering (report the mode-off renderer but render from the renderer as it AROSE = format_ticks called before the set_* calls); atk_9 UNGROUNDED-ORACLE ECHO (List.replicate ticks.length "0" instead of consulting the renderer); atk_10 WRONG DISCRIMINANT (guard on r.compacting instead of r.compactionCapable); atk_11 EXTRA-STATE tampering (also forces numeralStyle := true, a component no builder may set); atk_12 REORDER (render r' ticks.reverse); atk_13 DEEP-MODEL REFERENCE TAMPERING (convention := 0, i.e. substituting a fresh default formatter for the axis's own, losing the view interval it reads); atk_14 CAPABILITY-BIT FLIP; atk_15 LENGTH/DROP (.dropLast); atk_16 SITE-SPLIT (gold at site 1, force the mode off even on a renderer offering no control at site 2 -- the LogFormatter arm gold deliberately leaves alone); atk_17 VACUITY EXPLOIT PROBE (render only where compactionCapable && numeralStyle, emit a private label list where the read-back clause is vacuous -- this is the sharpest available attack on the guarded clause, and clause 3 still kills it).

RESOLVE RUNS (swebench_unified.harness.run_resolve, retries=0; patches generated programmatically from the base-commit blobs at gen_patch/mk.py and each verified to apply cleanly against a pristine 22cdfb0c checkout via git apply --check; logs/JSON in scratch res/):

(a) GOLD CONTROL res/patch_gold.diff (the bundle's own patch.diff) -> completed=True resolved=True, F2P 2/2, P2P 248/248, note 'resolved'. The oracle has discriminating power.

(b) GOLD RECONSTRUCTION res/patch_gold_recon.diff (my own regeneration of the capability-guarded fix at both sites, to validate the patch-materialization pipeline itself) -> resolved=True, F2P 2/2, P2P 248/248. So a NON-resolving result from this pipeline is a real signal, not a harness artifact.

(c) atk_3/atk_16 CLASS res/patch_atk3_uncond.diff (the faithful patch of the unconditional attack: the two set_* calls hoisted OUT of the hasattr guards in scales.py and out of the else-branch in utils.py, so the LogFormatter arm is configured too) -> completed=True resolved=False, applied=True, F2P 2/2 PASS but P2P 247/248 with tests/test_relational.py::TestLinePlotter::test_legend_data FAILING. CRUCIALLY its Lean files atk_3/atk_4/atk_16 do NOT verify (EXIT=1), so this is the spec CORRECTLY REJECTING a non-resolving impl -- the capability guard (compactionCapable + the uncompacted selector) is load-bearing and the model has it. This is the exact pairing that would have been a BROKEN witness had the proof closed; it does not.

(d) COARSENESS PROBE res/patch_half_off.diff (only set_useOffset(False), leaving scientific notation on) -> resolved=False, F2P 0/2, P2P 248/248. Confirms refinement.md's MEASURED claim that collapsing matplotlib's TWO switches into the single Lean 'compacting' bit is faithful, not lossy: no resolving half-measure exists for the model to miss.

(e) atk_6 CLASS res/patch_atk6_partial_style.diff (the faithful patch of the numeralStyle partial-domain attack: guard the two set_* calls on the formatter not being in a dressed text mode) -> resolved=True, F2P 2/2, P2P 248/248. So atk_6 is a spec-REJECTED but oracle-RESOLVING impl -- the spec is strictly tighter than the test suite here (over-tightness, not a verify=>correct break; G-EQ's break condition is the other direction).

A-LEG AUDIT (my assigned focus; independent driver over real matplotlib 3.10.9 at the base worktree with patch.diff applied -- NOT the bundle's axiom_check.py).
* render_length: 315 checks over 5 formatter kinds x 7 view intervals x 9 tick sets (incl. empty, 2^53, 2^53+1, -2^53) -> 0 violations. Arity leg HOLDS.
* Capability pairing (refinement.md Triple 1 op 1): hasattr(set_useOffset) == hasattr(set_scientific) for all 14 mticker.Formatter subclasses -> 0 disagreements. So compactionCapable really is ONE intrinsic bit of the class. R leg HOLDS.
* set_locs+[formatter(x)] vs format_ticks (refinement.md Triple 2 op 4, the claim that ONE 'render' symbol covers both sites' different call shapes): 120 configs -> 0 mismatches. A-consumed correspondence HOLDS.
* render_uncompacted_faithful: 210 in-guard checks -> 105 VIOLATIONS, all EngFormatter. FINDING (1), A-REFERENCE DEFECT, independently reproduced (the prior pass reported this and it is NOT fixed): mpl.ticker.EngFormatter subclasses ScalarFormatter, so compactionCapable=True and hasattr both controls; its _useMathText/_useLocale/_usetex are all False so mapping.md's binding gives numeralStyle=True; the patch's two calls apply so compacting=False; and the ticks are far inside 2^53. ALL FOUR of the axiom's guards hold, yet the real labels do not read back. Reached through the PUBLIC API at triple 1's own site: Continuous().label(unit='V')._setup(Series([1e8..1e8+4]), Color()) yields _legend labels ['100 MV']*5 -- one text for five DISTINCT ticks, and float('100 MV') raises, so the axiom's conclusion labelValue((render r ticks)[i]) = ticks[i] fails outright. Also confirmed reachable: formatter=ScalarFormatter(useMathText=True) gives ['$\mathdefault{100000000}$', ...]; that one the numeralStyle guard correctly excludes, EngFormatter it does not. The bundle's G-AX driver cannot see this: axiom_check.py FORMATTER_KINDS enumerates only ScalarFormatter / LogFormatter / LogFormatterSciNotation (grep EngFormatter -> 0 hits), while seaborn._core.scales.Continuous._get_formatter demonstrably also returns EngFormatter (unit=), StrMethodFormatter / FuncFormatter (like=) and LogFormatterSciNotation (base=). G-AX's 'pass' over 86868 checks is therefore an ENUMERATION ARTIFACT. This is NOT a G-EQ counterexample -- my determinacy certificate closes on [labelValue, render] alone, so no impl can exploit it to verify a wrong value -- it weakens the SOUNDNESS SURFACE (an axiom false of the real callee discharges obligations it should not) and belongs to the G-AX / G-PANEL-2 lanes. Honest repair: guard the axiom by renderer kind (or model the label-writing convention as text-shaped rather than value-shaped), NOT tighten the spec.
* Axiom-consistency: the axiom set is not exploitable to close an arbitrary impl -- demonstrated positively by the 17 rejections, each of which fails at a clause the axioms cannot reach.

REFINEMENT.MD LEG AUDIT (docs/architecture.md sec.5). Every leg in both tables is tagged R / A-consumed / A-reference / I -- there is NO kind-3 leg, and the tag vocabulary is correct. NOTE ON A PRIOR FINDING: the prior pass's FINDING (2) (docs describing a stale shownValue/compactByOffset model) HAS BEEN REPAIRED -- refinement.md and mapping.md now use the shipped vocabulary (TickRenderer, compactionCapable, compacting, numeralStyle, convention, uncompacted, render_length, render_uncompacted_faithful, the 9007199254740992 guard all present; grep for the stale symbols -> 0 hits in both).

The two A-consumed legs (Triple 1 op 4, Triple 2 op 4) and the A-reference discussion are now documented, and the 'Which model expression stands for which real callee' section correctly maps some r' -> ScalarFormatter.__call__ with offset/orderOfMagnitude forced to 0, none -> LogFormatter.__call__ left untouched. I verified those two correspondences executably (bullets above): both hold.

The ONE residual documentation defect is that refinement.md's A-consumed leg for render_uncompacted_faithful asserts the guard set is complete ('Guarded three ways, each because the real renderer fails the round trip outside it') while FINDING (1) shows a fourth, ungarded failure mode inside it; refinement.md's 'MEASURED to hold for every formatter class and every mode probed' inherits axiom_check.py's incomplete class enumeration. That is the same underlying G-AX defect, surfacing as an overclaim in the doc.

VERDICT RATIONALE: SOUND for G-EQ specifically. 17 distinct attacks spanning partial-domain (two independent guards), boundary, control-flow-effect ordering, ungrounded-oracle echo, vacuity exploitation, reordering, drop, wrong-discriminant, extra-state, deep-model/convention tampering, capability flip, site-split, and both prepatch bugs ALL fail to verify; the structurally-different positive control verifies with clean axioms; the prepatch bug is reproduced at BOTH sites; the gold control and my independent gold reconstruction both resolve; and the re-derived determinacy certificate proves no differing impl CAN verify, on axioms [labelValue, render] that exclude the defective one.

The atk_3 pairing is the decisive negative control: a materialized faithful patch that genuinely does NOT resolve (P2P 247/248), whose Lean twin the spec correctly REJECTS. Findings (1) and its doc echo are real and should be routed to G-AX / G-PANEL-2; neither yields a same-spec impl that verifies with a non-resolving faithful patch, which is the G-EQ break condition. ONE PROCESS FLAG for the gate operator: meta.json records the passing G-EQ against Solution.lean sha 9fd487ee... while the SHIPPED file is b7fdcb65... (G-AX/G-CONF/G-DIFF all record b7fdcb65...), so this spec had NOT previously been G-EQ-audited as shipped; this submission audits the shipped b7fdcb65 text.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verifies, so no faithful patch could be materialized FOR A VERIFYING CANDIDATE (patches={} for that reason, not for lack of trying -- I did materialize and RUN 5 real patches anyway, see below). WHY NONE CAN EXIST -- I did not rely on the prior pass's certificate; I re-derived it independently from the SHIPPED spec text at determinacy.lean. cmd: timeout 400 bash scripts/lean_verify.sh determinacy.lean 300 -> EXIT=0, no sorry (grep sorry = 0). It proves fst_pinned, spec1_unique, spec2_unique (problem_spec_X r ticks a -> problem_spec_X r ticks b -> a = b) and the composition spec1_determines: for ANY impl, (forall r ticks, problem_spec_1 r ticks (impl r ticks)) -> forall r ticks, impl r ticks = gold_impl r ticks. #print axioms: spec1_unique / spec2_unique / fst_pinned = [labelValue, propext, render, Quot.sound] -- CLEAN, and crucially they do NOT depend on render_length or render_uncompacted_faithful, so determinacy is immune to the axiom-faithfulness defect reported below. MECHANISM: clauses 1-2 pin result.fst by a TOTAL case split (uncompacted r is some/none exactly as r.compactionCapable is true/false, so no input escapes), and clause 3 (labels = render writtenFrom ticks) then pins result.snd from that already-fixed fst. Both post-conditions are therefore FUNCTIONAL: verify => extensionally-identical-to-gold, so the only same-spec impls that can verify are re-spellings of gold, which resolve. verify=>correct cannot fail by a wrong-value impl for this bundle. This closes the search rather than sampling it, which is why the 17 attacks below all fail for a structural reason.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -203,12 +203,13 @@
 -- impl-start
 noncomputable def implementation_continuousLegendLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- Where the renderer offers a control for the compacting mode, take it with
-  -- that mode off; otherwise take it as it stands. Then let that renderer write
-  -- the whole tick set's labels, and report both it and its text.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  if r.compactionCapable = true then
+    let r' : TickRenderer :=
+      { compactionCapable := r.compactionCapable, compacting := false,
+        numeralStyle := r.numeralStyle, convention := r.convention }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_continuousLegendLabels :
@@ -221,13 +222,13 @@
     uncompacted readsBackToTicks
   cases cap with
   | true =>
+    simp only [if_true, reduceIte]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+    · intro r' h; simp only [Option.some.injEq] at h; simp [← h]
     · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro _ hstyle hdom
-      simp only [if_true]
       refine ⟨render_length _ _, ?_⟩
       intro i hi
       exact render_uncompacted_faithful
@@ -235,13 +236,13 @@
           convention := conv }
         ticks rfl rfl hstyle hdom i hi
   | false =>
+    simp only [Bool.false_eq_true, if_false]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
     · intro r' h; simp at h
     · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro h; simp at h
-
 -- proof-end
 -- post-conditions-start
 /-- Second site: the same guarantee owed by the other place a legend of this kind
@@ -269,12 +270,13 @@
 -- impl-start
 noncomputable def implementation_legendEntryLabels
     (r : TickRenderer) (ticks : List Int) : TickRenderer × List String :=
-  -- As at the first site: where the renderer offers a control for the compacting
-  -- mode, take it with that mode off; otherwise take it as it stands. That
-  -- renderer writes the labels, and both it and its text are reported.
-  match uncompacted r with
-  | some r' => (r', render r' ticks)
-  | none    => (r, render r ticks)
+  if r.compactionCapable = true then
+    let r' : TickRenderer :=
+      { compactionCapable := r.compactionCapable, compacting := false,
+        numeralStyle := r.numeralStyle, convention := r.convention }
+    (r', render r' ticks)
+  else
+    (r, render r ticks)
 -- impl-end
 -- proof-start
 theorem correct_legendEntryLabels :
@@ -287,13 +289,13 @@
     uncompacted readsBackToTicks
   cases cap with
   | true =>
+    simp only [if_true, reduceIte]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
-    · intro r' h; simp only [if_true, Option.some.injEq] at h; simp [← h]
+    · intro r' h; simp only [Option.some.injEq] at h; simp [← h]
     · intro h; simp at h
-    · simp only [if_true]
-    · simp only [if_true]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro _ hstyle hdom
-      simp only [if_true]
       refine ⟨render_length _ _, ?_⟩
       intro i hi
       exact render_uncompacted_faithful
@@ -301,11 +303,11 @@
           convention := conv }
         ticks rfl rfl hstyle hdom i hi
   | false =>
+    simp only [Bool.false_eq_true, if_false]
     refine ⟨?_, ?_, ?_, ?_, ?_⟩
     · intro r' h; simp at h
     · intro _; simp
-    · simp
-    · simp only [Bool.false_eq_true, if_false]; exact render_length _ _
+    · trivial
+    · exact render_length _ _
     · intro h; simp at h
-
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: 17 distinct same-spec attacks + a structurally-different positive control + an independently re-derived determinacy certificate + 5 EXECUTED run_resolve runs. same_spec=True machine-confirmed for all 18 .lean attack/control files via swebench_unified.markers.same_spec with backends.get_backend('lean').language (all True; only the diagnostic axchk_pos.lean is False, purely because two '#print axioms' lines are appended after the proof region -- it is not submitted as an attack). Verify cmd for every file: bash scripts/lean_verify.sh <path>, run 4-at-a-time as concurrent background jobs (runverify.sh / runverify2.sh / runverify3.sh in the scratch dir).

BASELINE + CONTROL. Shipped Solution.lean re-verified EXIT=0. pos_control.lean EXIT=0 (structurally different spelling: branches on 'if r.compactionCapable = true' and builds the TickRenderer record field-by-field instead of matching on 'uncompacted', proving the spec is not accidentally tied to gold's syntactic shape). Axioms of the control via axchk_pos.lean (EXIT=0): correct_continuousLegendLabels and correct_legendEntryLabels each depend on [labelValue, propext, render, render_length, render_uncompacted_faithful, Quot.sound] = CLEAN (only the bundle's declared axioms plus standard propext/Quot.sound; no sorryAx).

ATTACK LEDGER -- all 17 EXIT=1 with 'error: unsolved goals' at the clause positions, i.e. SEMANTIC rejection, not tactic weakness. Each attack carries a uniform maximal-effort proof script: 'first |' the exact gold script, '| ' a fully split (cases cap <;> cases comp <;> cases style) brute force chaining every tactic gold uses plus simp_all/omega/decide/aesop with both axioms supplied. atk_1 prepatch site 1 '(r, render r ticks)' [PREPATCH REPRODUCED]; atk_2 prepatch site 2 [PREPATCH REPRODUCED]; atk_3 UNCONDITIONAL turn-off, no capability guard, both sites; atk_4 same, site 2 only (the prior pass's named counterexample class, re-encoded); atk_5 PARTIAL-DOMAIN on the 2^53 guard (act only when all ticks in-range, else prepatch); atk_6 PARTIAL-DOMAIN on numeralStyle (act only for a bare-numeral renderer, i.e. exactly where the read-back clause bites); atk_7 BOUNDARY (tick sets of length <=1 'hoist no common magnitude' so left untouched); atk_8 CONTROL-FLOW-EFFECT ordering (report the mode-off renderer but render from the renderer as it AROSE = format_ticks called before the set_* calls); atk_9 UNGROUNDED-ORACLE ECHO (List.replicate ticks.length "0" instead of consulting the renderer); atk_10 WRONG DISCRIMINANT (guard on r.compacting instead of r.compactionCapable); atk_11 EXTRA-STATE tampering (also forces numeralStyle := true, a component no builder may set); atk_12 REORDER (render r' ticks.reverse); atk_13 DEEP-MODEL REFERENCE TAMPERING (convention := 0, i.e. substituting a fresh default formatter for the axis's own, losing the view interval it reads); atk_14 CAPABILITY-BIT FLIP; atk_15 LENGTH/DROP (.dropLast); atk_16 SITE-SPLIT (gold at site 1, force the mode off even on a renderer offering no control at site 2 -- the LogFormatter arm gold deliberately leaves alone); atk_17 VACUITY EXPLOIT PROBE (render only where compactionCapable && numeralStyle, emit a private label list where the read-back clause is vacuous -- this is the sharpest available attack on the guarded clause, and clause 3 still kills it).

RESOLVE RUNS (swebench_unified.harness.run_resolve, retries=0; patches generated programmatically from the base-commit blobs at gen_patch/mk.py and each verified to apply cleanly against a pristine 22cdfb0c checkout via git apply --check; logs/JSON in scratch res/):

(a) GOLD CONTROL res/patch_gold.diff (the bundle's own patch.diff) -> completed=True resolved=True, F2P 2/2, P2P 248/248, note 'resolved'. The oracle has discriminating power.

(b) GOLD RECONSTRUCTION res/patch_gold_recon.diff (my own regeneration of the capability-guarded fix at both sites, to validate the patch-materialization pipeline itself) -> resolved=True, F2P 2/2, P2P 248/248. So a NON-resolving result from this pipeline is a real signal, not a harness artifact.

(c) atk_3/atk_16 CLASS res/patch_atk3_uncond.diff (the faithful patch of the unconditional attack: the two set_* calls hoisted OUT of the hasattr guards in scales.py and out of the else-branch in utils.py, so the LogFormatter arm is configured too) -> completed=True resolved=False, applied=True, F2P 2/2 PASS but P2P 247/248 with tests/test_relational.py::TestLinePlotter::test_legend_data FAILING. CRUCIALLY its Lean files atk_3/atk_4/atk_16 do NOT verify (EXIT=1), so this is the spec CORRECTLY REJECTING a non-resolving impl -- the capability guard (compactionCapable + the uncompacted selector) is load-bearing and the model has it. This is the exact pairing that would have been a BROKEN witness had the proof closed; it does not.

(d) COARSENESS PROBE res/patch_half_off.diff (only set_useOffset(False), leaving scientific notation on) -> resolved=False, F2P 0/2, P2P 248/248. Confirms refinement.md's MEASURED claim that collapsing matplotlib's TWO switches into the single Lean 'compacting' bit is faithful, not lossy: no resolving half-measure exists for the model to miss.

(e) atk_6 CLASS res/patch_atk6_partial_style.diff (the faithful patch of the numeralStyle partial-domain attack: guard the two set_* calls on the formatter not being in a dressed text mode) -> resolved=True, F2P 2/2, P2P 248/248. So atk_6 is a spec-REJECTED but oracle-RESOLVING impl -- the spec is strictly tighter than the test suite here (over-tightness, not a verify=>correct break; G-EQ's break condition is the other direction).

A-LEG AUDIT (my assigned focus; independent driver over real matplotlib 3.10.9 at the base worktree with patch.diff applied -- NOT the bundle's axiom_check.py).
* render_length: 315 checks over 5 formatter kinds x 7 view intervals x 9 tick sets (incl. empty, 2^53, 2^53+1, -2^53) -> 0 violations. Arity leg HOLDS.
* Capability pairing (refinement.md Triple 1 op 1): hasattr(set_useOffset) == hasattr(set_scientific) for all 14 mticker.Formatter subclasses -> 0 disagreements. So compactionCapable really is ONE intrinsic bit of the class. R leg HOLDS.
* set_locs+[formatter(x)] vs format_ticks (refinement.md Triple 2 op 4, the claim that ONE 'render' symbol covers both sites' different call shapes): 120 configs -> 0 mismatches. A-consumed correspondence HOLDS.
* render_uncompacted_faithful: 210 in-guard checks -> 105 VIOLATIONS, all EngFormatter. FINDING (1), A-REFERENCE DEFECT, independently reproduced (the prior pass reported this and it is NOT fixed): mpl.ticker.EngFormatter subclasses ScalarFormatter, so compactionCapable=True and hasattr both controls; its _useMathText/_useLocale/_usetex are all False so mapping.md's binding gives numeralStyle=True; the patch's two calls apply so compacting=False; and the ticks are far inside 2^53. ALL FOUR of the axiom's guards hold, yet the real labels do not read back. Reached through the PUBLIC API at triple 1's own site: Continuous().label(unit='V')._setup(Series([1e8..1e8+4]), Color()) yields _legend labels ['100 MV']*5 -- one text for five DISTINCT ticks, and float('100 MV') raises, so the axiom's conclusion labelValue((render r ticks)[i]) = ticks[i] fails outright. Also confirmed reachable: formatter=ScalarFormatter(useMathText=True) gives ['$\mathdefault{100000000}$', ...]; that one the numeralStyle guard correctly excludes, EngFormatter it does not. The bundle's G-AX driver cannot see this: axiom_check.py FORMATTER_KINDS enumerates only ScalarFormatter / LogFormatter / LogFormatterSciNotation (grep EngFormatter -> 0 hits), while seaborn._core.scales.Continuous._get_formatter demonstrably also returns EngFormatter (unit=), StrMethodFormatter / FuncFormatter (like=) and LogFormatterSciNotation (base=). G-AX's 'pass' over 86868 checks is therefore an ENUMERATION ARTIFACT. This is NOT a G-EQ counterexample -- my determinacy certificate closes on [labelValue, render] alone, so no impl can exploit it to verify a wrong value -- it weakens the SOUNDNESS SURFACE (an axiom false of the real callee discharges obligations it should not) and belongs to the G-AX / G-PANEL-2 lanes. Honest repair: guard the axiom by renderer kind (or model the label-writing convention as text-shaped rather than value-shaped), NOT tighten the spec.
* Axiom-consistency: the axiom set is not exploitable to close an arbitrary impl -- demonstrated positively by the 17 rejections, each of which fails at a clause the axioms cannot reach.

REFINEMENT.MD LEG AUDIT (docs/architecture.md sec.5). Every leg in both tables is tagged R / A-consumed / A-reference / I -- there is NO kind-3 leg, and the tag vocabulary is correct. NOTE ON A PRIOR FINDING: the prior pass's FINDING (2) (docs describing a stale shownValue/compactByOffset model) HAS BEEN REPAIRED -- refinement.md and mapping.md now use the shipped vocabulary (TickRenderer, compactionCapable, compacting, numeralStyle, convention, uncompacted, render_length, render_uncompacted_faithful, the 9007199254740992 guard all present; grep for the stale symbols -> 0 hits in both).

The two A-consumed legs (Triple 1 op 4, Triple 2 op 4) and the A-reference discussion are now documented, and the 'Which model expression stands for which real callee' section correctly maps some r' -> ScalarFormatter.__call__ with offset/orderOfMagnitude forced to 0, none -> LogFormatter.__call__ left untouched. I verified those two correspondences executably (bullets above): both hold.

The ONE residual documentation defect is that refinement.md's A-consumed leg for render_uncompacted_faithful asserts the guard set is complete ('Guarded three ways, each because the real renderer fails the round trip outside it') while FINDING (1) shows a fourth, ungarded failure mode inside it; refinement.md's 'MEASURED to hold for every formatter class and every mode probed' inherits axiom_check.py's incomplete class enumeration. That is the same underlying G-AX defect, surfacing as an overclaim in the doc.

VERDICT RATIONALE: SOUND for G-EQ specifically. 17 distinct attacks spanning partial-domain (two independent guards), boundary, control-flow-effect ordering, ungrounded-oracle echo, vacuity exploitation, reordering, drop, wrong-discriminant, extra-state, deep-model/convention tampering, capability flip, site-split, and both prepatch bugs ALL fail to verify; the structurally-different positive control verifies with clean axioms; the prepatch bug is reproduced at BOTH sites; the gold control and my independent gold reconstruction both resolve; and the re-derived determinacy certificate proves no differing impl CAN verify, on axioms [labelValue, render] that exclude the defective one.

The atk_3 pairing is the decisive negative control: a materialized faithful patch that genuinely does NOT resolve (P2P 247/248), whose Lean twin the spec correctly REJECTS. Findings (1) and its doc echo are real and should be routed to G-AX / G-PANEL-2; neither yields a same-spec impl that verifies with a non-resolving faithful patch, which is the G-EQ break condition. ONE PROCESS FLAG for the gate operator: meta.json records the passing G-EQ against Solution.lean sha 9fd487ee... while the SHIPPED file is b7fdcb65... (G-AX/G-CONF/G-DIFF all record b7fdcb65...), so this spec had NOT previously been G-EQ-audited as shipped; this submission audits the shipped b7fdcb65 text.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL attacker (2) faithfulness-break. Reference = base_commit 22cdfb0c93f8ec78492d87edb810f10cb7f57a31 worktree WITH patch.diff APPLIED (); base-only worktree () used solely to confirm the patch delta and that untouched callees behave identically. Pinned env: matplotlib 3.7.2, numpy 1.26.4, pandas 2.3.3, seaborn 0.12.2.dev0. NO DIVERGING INPUT FOUND after targeted attack on every clause.

MECHANICAL STATE. scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms` on BOTH correctness theorems: [labelValue, propext, render, render_length, render_uncompacted_faithful, Quot.sound] -- NO sorryAx, so neither proof is fake; the only non-Mathlib axioms are the four declared in the axioms region. markers.same_spec(Solution, Solution_prepatch) = True and same_spec(Solution, Solution_prepatch_2) = True with the real LeanBackend tables, so the spec region is byte-identical across variants and only the impl region differs (region_hashes differ, as expected). Both prepatch variants FAIL verification (exit 3, 'declaration uses sorry' at the correctness theorems) -- the spec is non-vacuous and genuinely discriminates the bug.

ATTACK 1 -- render_uncompacted_faithful (the load-bearing axiom), the primary too-strong candidate. Swept the real ScalarFormatter with ONLY the gold patch's two calls applied (set_useOffset(False); set_scientific(False)), bare-numeral, |t| <= 2^53, across formatter kinds x view intervals (incl. degenerate (0.5,0.5), reversed (3.0,2.0), (0,0), (1e-300,1e300), (9e15,9.1e15), the issue-shaped (1e8-1,1e8+5)) x rcParams cross (axes.formatter.limits in {(-7,7),(-1,1),(0,0),(3,3),(-15,15),(-3,4),(2,2)}, offset_threshold in {1,2,4,10,100}, useoffset True/False, unicode_minus True/False) x boundary + 6000 fuzzed integer tick sets. Total 1,321,489 renders in the main hunt + 85,968 in the final sweep + 12,030 negative/unicode-minus renders: 0 read-back violations, 0 unparseable labels. labelValue binding (strip, U+2212 -> '-', float) parses every in-guard label. Axiom CONFIRMED against the real callee.

ATTACK 2 -- guard tightness (is the spec too WEAK rather than too strong? both directions checked, since an over-guarded axiom would be the mirror defect). Each guard is NECESSARY, measured: (a) numeralStyle -- with compaction fully off and offset==orderOfMagnitude==0, useMathText writes ['$\mathdefault{0}$','$\mathdefault{200000}$',...] (none parse), _usetex the same, useLocale (en_US.UTF-8) writes ['0','200,000','400,000',...] (all but '0' fail). All three are set from a constructor arg or rcParam before either site and are untouched by set_useOffset/set_scientific, so no legend builder can undo them -- dropping this leg would make the axiom FALSE of the real formatter at reachable states. (b) 2^53 -- in-guard |t| == 2^53 reads back exactly (both signs, incl.

[-2^53, 2^53] -> ['-9007199254740992','9007199254740992']); just outside, 2^53+1 renders as '9007199254740992', i.e. snapped to a neighbour before any text is written. (c) compactionCapable -- the guard is not needlessly narrow; only ScalarFormatter is capable (see attack 4). Non-vacuity independently reproduced: 422 witnesses where a CAPABLE renderer still COMPACTING breaks read-back well inside the guard, e.g. ticks [0,200000,...,1e6] under iv (0,1e6) -> label '0.2' for tick 200000.

ATTACK 3 -- render_length. 0 arity violations over the same sweep, every formatter class and mode, including the empty tick list. Also re-measured the mapping's claimed equivalence between the per-element binding (set_locs then [f(x) for x in locs]) and format_ticks (the call the scales.py site actually makes): 0 mismatches. So ONE `render` symbol legitimately covers both sites' distinct calls.

ATTACK 4 -- the one-bit collapses (the most likely place for spec drift). (i) compactionCapable collapsing TWO hasattr guards into one bit: enumerated all 18 Formatter subclasses in matplotlib.ticker + matplotlib.dates; ZERO have exactly one of set_useOffset/set_scientific, and ScalarFormatter is the ONLY capable class. The collapse is exact, not lossy. (ii) `compacting` collapsing two switches into one bit: verified load-bearing -- both off gives ['0','200000',...]; offset-only-off gives ['0.0','0.2','0.4',...] (still broken); scientific-only-off gives the correct labels; neither (prepatch) broken. The bit means BOTH off, which is what the gold patch does. (iii) preservation claims: applied the patch's two calls to ScalarFormatter under 6 constructor configs (incl. useMathText, useLocale, useOffset=1e5) -- capability, numeralStyle and convention are provably UNCHANGED in every case; only offset/_useOffset/_scientific move. Non-capable formatters (LogFormatter, LogFormatterSciNotation, EngFormatter, PercentFormatter) pass through render with all four modelled components preserved.

ATTACK 5 -- render modelled as a PURE FUNCTION of (whole state, whole tick set) while the real formatter is stateful. Checked idempotence (3 repeated renders identical), history independence (a formatter that already rendered [1e8..1e8+4], [1,2], [0] or [1e15,1e15+1] produces byte-identical output to a fresh one on the next tick set), the compacting bit staying off across repeated renders, and read-back surviving arbitrary history: 0 violations. Also checked the `convention` component is not over-collapsed: it is REAL, not decorative -- LogFormatter/LogFormatterSciNotation/EngFormatter output varies with constructor args (base, unit, places, sep) at fixed class+view interval, and the spec correctly claims NOTHING about non-capable renderers' label values, so this variation cannot contradict any clause. In the capable+bare+compaction-off arm the output IS determinate across the whole rcParams cross (1 distinct output), so the function-of-state modelling holds exactly where the spec makes a claim.

ATTACK 6 -- real callees end to end (post-patch). Site 2 (seaborn.utils.locator_to_legend_entries, the exact patched site): 39 discrete cases + 3,506 FixedLocator fuzz cases, 0 violations of any clause. Site 1 (ContinuousBase._setup -> new._legend): the issue's own tick run [1e8..1e8+4] yields ['100000000',...,'100000004'] post-patch vs ['0','1','2','3','4'] pre-patch (measured on the base worktree) -- the spec's first clause is exactly what the patch delivers. Also drove Continuous().label(formatter=...) with 9 user-supplied formatters and so.Plot / scatterplot end to end; every capable+bare case satisfies read-back. The F2P test test_legend_has_no_offset asserts float(text.get_text()) > 1e7, i.e. literally the spec's readsBackToTicks clause.

ADVERSARIAL EDGE CASES CONSIDERED AND REJECTED as faithfulness findings. (a) A user-supplied ScalarFormatter SUBCLASS that re-arms compaction inside set_locs (ReArmOnCall) does break read-back while presenting as capable+bare. Rejected: this is state the callee re-enables AFTER the builder's calls -- the real post-patch code has the identical behaviour, so the model and the real callee AGREE here; it is a matplotlib subclassing hazard, not spec drift, and no plausible weaker spec would be provable of the real code either. A NoOpOffset subclass raises AttributeError in the real code before any label is written, so it reaches no observable the spec constrains.

(b) OverflowError ('cannot convert float infinity to integer') from ScalarFormatter._set_format when there is EXACTLY ONE loc and an INFINITE view interval (the <2 locs branch augments locs with the view interval, then log10 of an infinite range overflows). Reachable at both sites (Continuous(norm=(0,inf)).tick(at=[0]), inf-valued data with a single tick, locator_to_legend_entries(FixedLocator([0.0]), (0,inf), float)).

Rejected as a faithfulness finding: MEASURED IDENTICAL on the pre-patch base worktree, so it is a pre-existing upstream crash the patch neither introduces nor is scoped to fix; the model's carrier is `List Int` with a finite `convention`, refinement.md explicitly scopes the view interval into the opaque `convention` and lists set_view_interval / the clip as out of scope, and a total Lean function cannot and need not model an exception the delta does not touch. It is a domain-of-definition gap in the shared modelling convention, not a case where the modelled function DISAGREES with the real callee on a value both produce.

CONCLUSION. Every clause of both problem_spec_* was checked against the patch-applied reference and each holds; both consumed axioms are true of the real matplotlib 3.7.2 formatter over ~1.4M renders with all three guards measured tight in both directions; the two one-bit abstractions are exact rather than lossy; the spec is non-vacuous (both prepatch variants unclosable) and its read-back clause is exactly what the F2P tests assert. No input found on which the modelled function disagrees with the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE. No relaxation in this bundle: meta.json keys = [axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins] -- no `relaxed_leakage`; `find . -iname '*relax*'` empty. So I judged this as an ordinary unrelaxed leakage review, with no unavoidability argument to re-derive.

ARTIFACT IDENTITY -- BOTH RECORDED PANEL NOTES ARE STALE, INCLUDING THE PASSING G-PANEL-3. Shipped Solution.lean is sha256 b7fdcb65203a8cca... The recorded G-PANEL-3 (NO-LEAKAGE) and G-PANEL-2 (UNFAITHFUL) are stamped sources.Solution.lean = 9fd487eeed8d..., and G-EQ/G-PANEL-1 likewise. Only G-VERIFY/G-LEAK/G-HYGIENE/G-CONF/G-DIFF/G-GOLD/G-MUT/G-INTEGRITY/G-AX (checked_at 14:13-14:18) carry b7fdcb65. The live file has a FOURTH structure field `numeralStyle` that the recorded G-PANEL-3 note never mentions, so I inherited nothing from it -- neither its verdict nor its measurements -- and re-measured the shipped bytes myself. Also stale: meta['region_hashes'] does not match the live file, while meta.gates['G-HYGIENE'].data.region_hashes does (recomputed via markers.region_hashes with LeanBackend.language: == G-HYGIENE.data True, == meta['region_hashes'] False). Hygiene nit, not leakage.

SPEC-VIEW TOKEN SCAN (my own, markers.spec_view + LeanBackend.language, 237 lines, written to specview_3187.txt). Occurrences: 'scientific' 0, 'set_scientific' 0, 'set_useOffset' 0, 'useoffset' 0, 'offset' 0, 'hasattr' 0, 'ScalarFormatter' 0, 'LogFormatter' 0, 'matplotlib' 0, 'mpl.' 0, 'notation' 0, 'exponent' 0, 'order of magnitude' 0, 'orderOfMagnitude' 0, 'power of ten' 0, 'formatter' 0, 'format_ticks' 0, 'set_locs' 0, 'locator_to_legend' 0, 'seaborn' 0, 'rcParam' 0, 'mathtext' 0, 'usetex' 0, 'locale' 0, '1e6' 0, '1e8' 0, 'multiplicative' 0, 'two/both controls' 0, 'two switches' 0. The only control-word form present is the SINGULAR 'control' (13x). Arity-1 throughout.

THE SPEC VIEW IS STRICTLY LESS CONCRETE THAN THE PUBLIC PROBLEM_STATEMENT. The problem_statement itself names 'ScalarFormatter' 3x, 'offset' 6x, 'useoffset' 1x, 'offset_threshold' 1x, the file 'scales.py', and links the exact changed lines L377-L382. The spec view names NONE of these (0 hits each, above). Everything the spec view discloses about the offset half is a strict abstraction of what the issue already states publicly.

THE DISCRIMINATOR IS THE SECOND KNOB AND THE SPEC VIEW DOES NOT CONTAIN IT (my measurement, matplotlib 3.10.9, ScalarFormatter.format_ticks over locs=[1e8..1e8+4], scored by the literal F2P predicate float(text) > 1e7): no setter            -> ['0','1','2','3','4']                    offsetText '+1e8'  FAIL set_useOffset(False) -> ['1.00000000'..'1.00000004']              offsetText '1e8'   FAIL set_scientific(False)-> ['0','1','2','3','4']                     offsetText '+1e8'  FAIL set_useMathText(False)/set_useLocale(False) -> unchanged                             FAIL => 0 of 4 single setters pass.

Of the 6 pairs, EXACTLY ONE passes: set_useOffset+set_scientific -> ['100000000'..'100000004']        offsetText ''      PASS (= gold) So the whole F2P-discriminating bit is 'there are TWO separate boolean residual modes, disable BOTH'. Note 'scientific' -- the knob that is not in the problem_statement either -- is absent from the spec view. A solver transliterating this arity-1 spec view writes ONE disable call and fails F2P exactly as a problem_statement-only solver does. The single-mode framing does not merely omit the second knob; it asserts there is one control, so it cannot hand over a bit it does not contain.

WHY THE ARITY-1 COLLAPSE IS FAITHFUL, NOT A CONVENIENT HIDING PLACE (measured first-hand, not taken from mapping.md): ScalarFormatter exposes set_useOffset AND set_scientific (True/True); LogFormatter and LogFormatterSciNotation expose NEITHER (False/False), and calling set_useOffset on either raises AttributeError. So the two gold hasattr guards always agree per formatter class, and one intrinsic `compactionCapable` bit is the correct abstraction. The non-capable preservation clause is also faithful: LogFormatter over ticks [1e2,1e4,1e6,1e8] writes ['100','1e4','1e+06','1e+08'], all 4 reading back to the full tick -- it needs no correction.

CANDIDATE LEAKING LINE I WEIGHED AND REJECTED. The spec view does state the fix DIRECTION -- 'COMPACTION IS OFF WHERE IT CAN BE TURNED OFF' -- whereas the problem_statement suggests a different remedy ('the offset value can be safely retrieved from all formatters and ... used to create the legend title and/or labels'). I rejected it as leakage because: (a) it is the abstraction of the changed OBSERVABLE, and with `render`/`labelValue` opaque the postcondition has no other way to say 'the legend's text is what THIS renderer state wrote'; (b) per the arity measurement it does not reach the gold edit -- direction without the second knob resolves 0 F2P; (c) the offset half of that direction is already public via the issue's own 'useoffset'/'offset_threshold'/L377-382 pointers.

### Core gates re-measured myself
  - scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
  - #print axioms on both theorems -> [labelValue, propext, render, render_length, render_uncompacted_faithful, Quot.sound] each. CLEAN, no sorryAx.
  - markers.same_spec(Solution, Solution_prepatch) = True and same_spec(Solution, Solution_prepatch_2) = True -> the twins are spec-region identical, so G-DIFF is a genuine impl-only swap.
  - Both prepatch variants ship `sorry`, so their failure alone is weak. I proved discrimination POSITIVELY instead: appended to the full shipped file `impl_prepatch r ticks = (r, render r ticks)` (the pre-patch shape) and refuted the spec at a capable compacting renderer for BOTH sites -- `¬ problem_spec_continuousLegendLabels {compactionCapable:=true, compacting:=true, numeralStyle:=true, convention:=0} [1] (impl_prepatch ...)` and the site-2 analogue -> lean_verify exit 0, zero sorry warnings. The spec is FALSE on pre-patch behavior, not merely unproved.
  - Non-vacuity control: the non-capable branch is positively satisfiable (`problem_spec_continuousLegendLabels {compactionCapable:=false,...} [5] (implementation_... )` closed by correct_...), so the preservation clause is not an infeasible guard verifying vacuously.
  - Harness control: the same file with `example : False := by ... sorry` -> lean_verify exit 3 ('file elaborates but uses sorry'), confirming exit 0 on my refutation file is real.

BUNDLE-ADDRESSES-THE-REVIEWER AXIS. I grepped Solution.lean, both prepatch variants, mapping.md and refinement.md for panel/reviewer/auditor-directed instruction or verdict coaching ('you should record', 'the honest verdict is', 'not a finding', 'G-PANEL-3 should', ...): no hits. verdict.md: no coaching hits either. No file in this bundle tells me how to record or which verdict is honest -- nothing to report on that axis. The two docs DO argue their own soundness, and mapping.md/refinement.md still describe the model without acknowledging some of the live spec's shape, but that is documentation staleness for another gate; I judged the spec view on its own bytes.

ADJACENT, NOT MINE: meta records G-PANEL-2 = UNFAITHFUL against the stale 9fd487ee file, on a useMathText counterexample. The shipped file's added `numeralStyle` field guards render_uncompacted_faithful with `r.numeralStyle = true`, which excludes exactly that witness, so that finding does not transfer unexamined to b7fdcb65. Flagged for the faithfulness gate; it is not a leakage question and I did not rest my verdict on it.

VERDICT: NO-LEAKAGE. Facet re-confirmed: the legend-label compaction facet at both sites (scales.py ContinuousBase._setup and utils.py locator_to_legend_entries). The spec view discloses only that a shared mutable numeric tick renderer may hoist a magnitude common to the tick set that a legend has nowhere to display, and that the mode must be off where the renderer offers a control -- an arity-1 abstraction, strictly less concrete than the public issue, that leaves the F2P-discriminating second knob (set_scientific) undisclosed, as I measured 0/4 single setters vs 1/6 pairs under float(text) > 1e7.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.