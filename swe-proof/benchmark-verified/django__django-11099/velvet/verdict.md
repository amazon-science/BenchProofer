# P2 adversarial audit — django__django-11099

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_true.lean`, `atk_all_only.lean`, `atk_any.lean`, `atk_dropfirst.lean`, `atk_droplast.lean`, `atk_notempty.lean`, `atk_filter_nl.lean`, `atk_or.lean`, `atk_loop_offbyone.lean` |

**Non-vacuity.** The positive control `pos_straight.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verified, so there is no verifying-but-wrong refined patch to run through the harness (the resolve-run obligation is vacuously satisfied over the empty set of verifying attacks, not skipped). The spec `ensures out = validName isAllowed s` is an UNCONDITIONAL total functional equality (no precondition), parametric over the free `isAllowed : Char -> Bool`. Any impl not extensionally equal to `validName` on ALL inputs and for EVERY `isAllowed` has no proof and is rejected. Each of the 9 attacks reduces `prove_correct` to the exact equality obligation with a concrete false instance (e.g. s=[]), confirmed by the residual 'unsolved goals' being the ensures clause itself.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_true.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return true
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 2 — `atk_all_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return s.all (fun c => isAllowed c)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 3 — `atk_any.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty && s.any (fun c => isAllowed c)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 4 — `atk_dropfirst.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty && allowedAll isAllowed (s.drop 1)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 5 — `atk_droplast.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty && allowedAll isAllowed s.dropLast
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 6 — `atk_notempty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 7 — `atk_filter_nl.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty && allowedAll isAllowed (s.filter (fun c => c ≠ '\n'))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 8 — `atk_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,18 +51,7 @@
   ensures out = validName isAllowed s
   do
     -- impl-start
-    let mut acc : Bool := true
-    let mut i := s.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ s.length
-      invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := s[i - 1]!
-      acc := isAllowed c && acc
-      i := i - 1
-    return !s.isEmpty && acc
+    return !s.isEmpty || allowedAll isAllowed s
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -80,7 +69,6 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
+              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Attack 9 — `atk_loop_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,10 @@
     -- impl-start
     let mut acc : Bool := true
     let mut i := s.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ s.length
       invariant acc = allowedAll isAllowed (s.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let c := s[i - 1]!
@@ -80,7 +80,5 @@
   rw [hcons, allowedAll_cons]
 
 prove_correct validateName by
-  loom_solve
-  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
-    simp_all [Bool.and_comm]
-  · simp_all [validName, List.drop_zero]
+  loom_solve <;>
+    simp_all [validName, allowedAll, List.drop_zero, Bool.and_comm]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_straight.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-code-point character-class membership is
--  taken as a FREE INPUT `isAllowed : Char → Bool`: the spec holds for every
--  value of it, and mapping.md binds it to the real class `[\w.@+-]` under
--  each validator's regex flags. Nothing here needs validation against a
--  real callee, hence no G-AX axioms.)
-- axioms-end

-- pure-start
/- Every code point of a sequence lies in the allowed class `isAllowed`.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def allowedAll (isAllowed : Char → Bool) : List Char → Bool
  | []      => true
  | c :: cs => isAllowed c && allowedAll isAllowed cs

@[grind] lemma allowedAll_nil (p : Char → Bool) : allowedAll p [] = true := rfl
@[grind] lemma allowedAll_cons (p : Char → Bool) (c : Char) (cs : List Char) :
    allowedAll p (c :: cs) = (p c && allowedAll p cs) := rfl

/- A sequence names a valid identifier exactly when it is non-empty AND every
   one of its code points — from the first through the very LAST — lies in the
   allowed class. There is NO end-of-input tolerance: no code point is dropped
   or exempted before the check, so a sequence whose final code point falls
   outside the class (such as a trailing line terminator, which the real class
   excludes) is rejected, and so is the empty sequence. -/
def validName (isAllowed : Char → Bool) (s : List Char) : Bool :=
  !s.isEmpty && allowedAll isAllowed s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The acceptance decision for a candidate identifier, modeled over its code
   point sequence and parametric in the (unchanged) per-code-point class
   membership `isAllowed`: accept iff the candidate is non-empty and every
   code point — including the very last one — is in the allowed class.
   `isAllowed` and `s` are read-only inputs. -/
method validateName (isAllowed : Char → Bool) (s : List Char) return (out : Bool)
  ensures out = validName isAllowed s
  do
    -- impl-start
    return !s.isEmpty && allowedAll isAllowed s
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allowedAll` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma allowedAll_drop_step (p : Char → Bool) (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    allowedAll p (s.drop (i - 1)) = (p s[i - 1]! && allowedAll p (s.drop i)) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allowedAll_cons]

prove_correct validateName by
  loom_solve <;>
    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Prepatch bug re-encoded as an attack: `True`.

Verified with `bash scripts/lean_verify.sh <file>` from that root; same_spec via swebench_unified.markers.same_spec + get_backend('velvet') using python. NOTE on same_spec editable surface: velvet flavor elides BOTH the impl region AND the `prove_correct` body (_elide_prove_correct), so attacks may rewrite impl+proof freely; axioms/pure/pre/post, the method signature+ensures, and the top-level `allowedAll_drop_step` lemma were kept BYTE-IDENTICAL. All attacks spliced from Solution.lean via splice.py preserving those frozen regions; same_spec=True verified for all 9 attacks + both positive controls.

same_spec (all True): atk_true, atk_all_only, atk_any, atk_dropfirst, atk_droplast, atk_notempty, atk_filter_nl, atk_or, atk_loop_offbyone, pos_straight, pos_control(=orig Solution.lean).

POSITIVE CONTROLS (non-vacuity): pos_control (original bundle loop impl) -> EXIT 0; pos_straight (structurally different straight-line `return !s.isEmpty && allowedAll isAllowed s`, no loop) -> EXIT 0. Spec is satisfiable by a genuinely different impl.

ATTACK RESULTS (cmd `bash scripts/lean_verify.sh <path>`, all EXIT 1 = rejected, all 'unsolved goals' at the ensures obligation, NOT elaboration/tactic errors):
- atk_true.lean (ungrounded-oracle echo `return true`): EXIT 1, residual `allowedAll isAllowed s = true ∧ ¬s = []` (false on s=[]).
- atk_all_only.lean (partial-domain, drop !isEmpty, differs ONLY on empty `s.all isAllowed`): EXIT 1, residual `(s.all fun c => isAllowed c) = (allowedAll isAllowed s && !s.isEmpty)` (false on s=[]).
- atk_any.lean (quantifier ∃ instead of ∀): EXIT 1.
- atk_dropfirst.lean (boundary, skip first code point via `allowedAll (s.drop 1)`): EXIT 1.
- atk_droplast.lean (boundary, exempt LAST code point `allowedAll s.dropLast` — the very anchor the $->\Z fix turns on): EXIT 1.
- atk_notempty.lean (control-flow-effect, ignore class entirely `return !s.isEmpty`): EXIT 1.
- atk_filter_nl.lean (semantic prepatch, tolerate newlines `allowedAll (s.filter (·≠'\n'))`): EXIT 1.
- atk_or.lean (control-flow-effect, wrong connective `!s.isEmpty || allowedAll ...`): EXIT 1.
- atk_loop_offbyone.lean (control-flow-effect, loop `while i>1` never inspects s[0], mirrors real loop structure): EXIT 1.

PREPATCH: bundle Solution_prepatch.lean (strip one trailing '\n' then check, the `$` semantics) -> EXIT 1, unsolved exit-leg goal (trailing-newline $-vs-\Z divergence). prepatch_reproduced=true.

RESOLVE OBLIGATION: because NO wrong impl verified, there is no faithful refined patch to materialize/run through run_resolve — patches={} (vacuous, not skipped). This is the correct outcome for SOUND: verify would only pass on a functionally-exact impl, whose patch is the gold patch (already G-RESOLVE-resolved).

REFINEMENT AUDIT (refinement.md + mapping.md): every leg is R / A-reference / I — NO kind-3, NO axiom (A-consumed) legs. A1 (param s:List Char <-> value:str) = R. A2 (isAllowed <-> class [\w.@+-] under flags) = R: it is a FREE universal method parameter, `ensures` holds for every isAllowed, so it asserts nothing about the class boundary (correct — no G-AX obligation) and no impl can hardcode a narrower/wider class (must hold for EVERY isAllowed). A3/A4/A5 = I: the backward loop computes the conjunction of isAllowed over all code points (=`+` quantifier), `!s.isEmpty`=`+` one-or-more, and `\Z` (no end-of-input tolerance, incl. the last code point) is modeled DEEPLY by allowedAll running through the final element with no drop/exempt. The A-legs' correspondence to the real callee (RegexValidator.__call__ evaluating `^[\w.@+-]+\Z` via non-MULTILINE re.search) holds: accept iff non-empty AND every code point (through the last) in class; since U+000A is in no faithful \w/punct class, a trailing '\n' is rejected, matching \Z (and NOT the prepatch `$` which tolerates one). No regex-engine axiom. G-AX vacuous (skip) is correct.

CONCLUSION: 9 distinct verifying-failing attacks across all requested categories (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) + prepatch reproduced + 2 positive controls verify. No verify⇏correct gap exhibited. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_true.lean`, `atk_all_only.lean`, `atk_any.lean`, `atk_dropfirst.lean`, `atk_droplast.lean`, `atk_notempty.lean`, `atk_filter_nl.lean`, `atk_or.lean`, `atk_loop_offbyone.lean` |

**Non-vacuity.** The positive control `pos_straight.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verified, so there is no verifying-but-wrong refined patch to run through the harness (the resolve-run obligation is vacuously satisfied over the empty set of verifying attacks, not skipped). The spec `ensures out = validName isAllowed s` is an UNCONDITIONAL total functional equality (no precondition), parametric over the free `isAllowed : Char -> Bool`. Any impl not extensionally equal to `validName` on ALL inputs and for EVERY `isAllowed` has no proof and is rejected. Each of the 9 attacks reduces `prove_correct` to the exact equality obligation with a concrete false instance (e.g. s=[]), confirmed by the residual 'unsolved goals' being the ensures clause itself.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_true.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_all_only.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_any.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_dropfirst.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_droplast.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_notempty.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_filter_nl.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_or.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_loop_offbyone.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_straight.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-code-point character-class membership is
--  taken as a FREE INPUT `isAllowed : Char → Bool`: the spec holds for every
--  value of it, and mapping.md binds it to the real class `[\w.@+-]` under
--  each validator's regex flags. Nothing here needs validation against a
--  real callee, hence no G-AX axioms.)
-- axioms-end

-- pure-start
/- Every code point of a sequence lies in the allowed class `isAllowed`.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def allowedAll (isAllowed : Char → Bool) : List Char → Bool
  | []      => true
  | c :: cs => isAllowed c && allowedAll isAllowed cs

@[grind] lemma allowedAll_nil (p : Char → Bool) : allowedAll p [] = true := rfl
@[grind] lemma allowedAll_cons (p : Char → Bool) (c : Char) (cs : List Char) :
    allowedAll p (c :: cs) = (p c && allowedAll p cs) := rfl

/- A sequence names a valid identifier exactly when it is non-empty AND every
   one of its code points — from the first through the very LAST — lies in the
   allowed class. There is NO end-of-input tolerance: no code point is dropped
   or exempted before the check, so a sequence whose final code point falls
   outside the class (such as a trailing line terminator, which the real class
   excludes) is rejected, and so is the empty sequence. -/
def validName (isAllowed : Char → Bool) (s : List Char) : Bool :=
  !s.isEmpty && allowedAll isAllowed s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The acceptance decision for a candidate identifier, modeled over its code
   point sequence and parametric in the (unchanged) per-code-point class
   membership `isAllowed`: accept iff the candidate is non-empty and every
   code point — including the very last one — is in the allowed class.
   `isAllowed` and `s` are read-only inputs. -/
method validateName (isAllowed : Char → Bool) (s : List Char) return (out : Bool)
  ensures out = validName isAllowed s
  do
    -- impl-start
    return !s.isEmpty && allowedAll isAllowed s
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allowedAll` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma allowedAll_drop_step (p : Char → Bool) (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    allowedAll p (s.drop (i - 1)) = (p s[i - 1]! && allowedAll p (s.drop i)) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allowedAll_cons]

prove_correct validateName by
  loom_solve <;>
    simp_all [validName, allowedAll, List.all_eq_true, List.any_eq_true,
              List.drop_zero, Bool.and_comm, Bool.or_comm]
```

Prepatch bug re-encoded as an attack: `True`.

Verified with `bash scripts/lean_verify.sh <file>` from that root; same_spec via swebench_unified.markers.same_spec + get_backend('velvet') using python. NOTE on same_spec editable surface: velvet flavor elides BOTH the impl region AND the `prove_correct` body (_elide_prove_correct), so attacks may rewrite impl+proof freely; axioms/pure/pre/post, the method signature+ensures, and the top-level `allowedAll_drop_step` lemma were kept BYTE-IDENTICAL. All attacks spliced from Solution.lean via splice.py preserving those frozen regions; same_spec=True verified for all 9 attacks + both positive controls.

same_spec (all True): atk_true, atk_all_only, atk_any, atk_dropfirst, atk_droplast, atk_notempty, atk_filter_nl, atk_or, atk_loop_offbyone, pos_straight, pos_control(=orig Solution.lean).

POSITIVE CONTROLS (non-vacuity): pos_control (original bundle loop impl) -> EXIT 0; pos_straight (structurally different straight-line `return !s.isEmpty && allowedAll isAllowed s`, no loop) -> EXIT 0. Spec is satisfiable by a genuinely different impl.

ATTACK RESULTS (cmd `bash scripts/lean_verify.sh <path>`, all EXIT 1 = rejected, all 'unsolved goals' at the ensures obligation, NOT elaboration/tactic errors):
- atk_true.lean (ungrounded-oracle echo `return true`): EXIT 1, residual `allowedAll isAllowed s = true ∧ ¬s = []` (false on s=[]).
- atk_all_only.lean (partial-domain, drop !isEmpty, differs ONLY on empty `s.all isAllowed`): EXIT 1, residual `(s.all fun c => isAllowed c) = (allowedAll isAllowed s && !s.isEmpty)` (false on s=[]).
- atk_any.lean (quantifier ∃ instead of ∀): EXIT 1.
- atk_dropfirst.lean (boundary, skip first code point via `allowedAll (s.drop 1)`): EXIT 1.
- atk_droplast.lean (boundary, exempt LAST code point `allowedAll s.dropLast` — the very anchor the $->\Z fix turns on): EXIT 1.
- atk_notempty.lean (control-flow-effect, ignore class entirely `return !s.isEmpty`): EXIT 1.
- atk_filter_nl.lean (semantic prepatch, tolerate newlines `allowedAll (s.filter (·≠'\n'))`): EXIT 1.
- atk_or.lean (control-flow-effect, wrong connective `!s.isEmpty || allowedAll ...`): EXIT 1.
- atk_loop_offbyone.lean (control-flow-effect, loop `while i>1` never inspects s[0], mirrors real loop structure): EXIT 1.

PREPATCH: bundle Solution_prepatch.lean (strip one trailing '\n' then check, the `$` semantics) -> EXIT 1, unsolved exit-leg goal (trailing-newline $-vs-\Z divergence). prepatch_reproduced=true.

RESOLVE OBLIGATION: because NO wrong impl verified, there is no faithful refined patch to materialize/run through run_resolve — patches={} (vacuous, not skipped). This is the correct outcome for SOUND: verify would only pass on a functionally-exact impl, whose patch is the gold patch (already G-RESOLVE-resolved).

REFINEMENT AUDIT (refinement.md + mapping.md): every leg is R / A-reference / I — NO kind-3, NO axiom (A-consumed) legs. A1 (param s:List Char <-> value:str) = R. A2 (isAllowed <-> class [\w.@+-] under flags) = R: it is a FREE universal method parameter, `ensures` holds for every isAllowed, so it asserts nothing about the class boundary (correct — no G-AX obligation) and no impl can hardcode a narrower/wider class (must hold for EVERY isAllowed). A3/A4/A5 = I: the backward loop computes the conjunction of isAllowed over all code points (=`+` quantifier), `!s.isEmpty`=`+` one-or-more, and `\Z` (no end-of-input tolerance, incl. the last code point) is modeled DEEPLY by allowedAll running through the final element with no drop/exempt. The A-legs' correspondence to the real callee (RegexValidator.__call__ evaluating `^[\w.@+-]+\Z` via non-MULTILINE re.search) holds: accept iff non-empty AND every code point (through the last) in class; since U+000A is in no faithful \w/punct class, a trailing '\n' is rejected, matching \Z (and NOT the prepatch `$` which tolerates one). No regex-engine axiom. G-AX vacuous (skip) is correct.

CONCLUSION: 9 distinct verifying-failing attacks across all requested categories (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) + prepatch reproduced + 2 positive controls verify. No verify⇏correct gap exhibited. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit for django__django-11099 velvet bundle.

Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. Spec is `ensures out = validName isAllowed s` with validName = !s.isEmpty && allowedAll isAllowed s, parametric in the per-code-point class isAllowed. Solution.lean verifies (lean_verify.sh exit 0).

Real callee (worktree, patched to gold): ASCIIUsernameValidator/UnicodeUsernameValidator both use regex=r'^[\w.@+-]+\Z'; RegexValidator.__call__ accepts iff self.regex.search(str(value)) matches. This is the $->\Z gold fix.

Empirical equivalence check of the modeled function (instantiated at the REAL \w class per mapping.md — using Python's per-char \w regex under re.ASCII and flags=0, plus punctuation .@+-) versus the real callee regex ^[\w.@+-]+\Z:
  - Exhaustive single-char sweep over codepoints 0x0000..0x11000 (full BMP + start of astral), both ASCII and Unicode modes: 0 disagreements.
  - Length-2 combos with every line terminator / whitespace char (\n \r \x0b \x0c \x1c \x1d \x1e \x85 U+2028 U+2029) after various base chars: 0 disagreements.
  - 300k biased fuzz including trailing \n, CRLF, CR, vertical-tab suffixes: 0 disagreements.

Captured correctly: (1) \Z semantics = no trailing-newline tolerance (allowedAll runs through the last code point, no exemption); (2) '+' one-or-more = !s.isEmpty non-empty conjunct; (3) class boundary via the free isAllowed input, so the spec neither hardcodes nor misstates the class. Discriminating F2P case 'trailingnewline\n' correctly rejected.

Parametricity note: the ensures holds for EVERY isAllowed, which is a strengthening on the IMPLEMENTATION obligation (impl must be correct for any class), not a divergence of the modeled function from the real callee. Instantiated at the real per-validator class the model agrees with the callee on every input tested. No input was found where the modeled function disagrees with the real repo behavior. Verdict: FAITHFUL, no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec(velvet backend) => True (spec regions axioms/pure/pre/post + `ensures out = validName isAllowed s` are identical; only impl/proof differ). Compared the spec view against the PUBLIC problem_statement ONLY (hints_text is empty).

Gold edit: regex r'^[\w.@+-]+$' -> r'^[\w.@+-]+\Z' in ASCII/UnicodeUsernameValidator, i.e. reject usernames with a trailing newline.

The public problem_statement ALREADY discloses the entire gold fix in prose: it quotes the exact buggy regex r'^[\w.@+-]+$', explains that Python's `$` also matches a trailing newline so the validators wrongly accept usernames ending in a newline, and states the fix explicitly ('use \A and \Z', giving r'\A[\w.@+-]+\Z' to reject trailing newlines). So the fix ($->\Z / reject-trailing-newline) is fully public.

The spec-view pass-through content (docstrings on validName/allowedAll and the ensures clause) models exactly that public behavior: non-empty AND every code point through the very last is in the allowed class, with NO end-of-input tolerance so a trailing line terminator is rejected. This restates the publicly-known intent and reveals nothing about the gold edit beyond the problem_statement. The per-code-point character class [\w.@+-] is deliberately kept abstract as a free input `isAllowed` (spec makes no claim about class membership), and no implementation-only specific of the gold patch is exposed. The discriminating detail that separates prepatch from postpatch (trailing-newline handling) is itself public, not a leaked hidden gold specific.

Therefore the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
