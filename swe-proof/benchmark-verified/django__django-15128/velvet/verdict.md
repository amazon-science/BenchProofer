# P2 adversarial audit — django__django-15128

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
     do
       let a := aliases[i - 1]!
       result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
+                 else [(a, newPrefix ++ toString i)]) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,8 +100,7 @@
       decreasing i
     do
       let a := aliases[i - 1]!
-      result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
+      result := [(a, newPrefix ++ toString (i - 1))] ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,8 +100,8 @@
       decreasing i
     do
       let a := aliases[i - 1]!
-      result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
+      result := (if preserved.contains a then [(a, newPrefix ++ toString (i - 1))]
+                 else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,18 +91,7 @@
   ensures out = relabeling newPrefix preserved aliases
   do
     -- impl-start
-    let mut result : List (String × String) := []
-    let mut i := aliases.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aliases.length
-      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := aliases[i - 1]!
-      result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
-      i := i - 1
+    let result : List (String × String) := []
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,10 +93,8 @@
     -- impl-start
     let mut result : List (String × String) := []
     let mut i := aliases.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aliases.length
-      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
-      done_with i = 0
+    while i > 1
+      invariant 1 ≤ i ∨ i = 0
       decreasing i
     do
       let a := aliases[i - 1]!
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -91,19 +91,7 @@
   ensures out = relabeling newPrefix preserved aliases
   do
     -- impl-start
-    let mut result : List (String × String) := []
-    let mut i := aliases.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aliases.length
-      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := aliases[i - 1]!
-      result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
-      i := i - 1
-    return result
+    return relabeling newPrefix preserved aliases
     -- impl-end
 
 prove_correct buildRelabeling by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
     do
       let a := aliases[i - 1]!
       result := (if preserved.contains a then []
-                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
+                 else [(a, toString (i - 1))]) ++ result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads two plain inputs — an ordered
--  sequence of strings and a set of strings to leave out — together
--  with the fresh prefix to apply, and produces the relabeling sequence handed
--  onward. Every observable is computed structurally from those inputs; no
--  unchanged callee's contract is consumed and no foreign callee is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The relabeling produced for the input strings from position `pos` onward,
   under a fresh `newPrefix`, with any string listed in `preserved` left out.

   Each string is paired with a fresh name `newPrefix ++ toString pos` keyed by
   its ORIGINAL position in the full sequence — the position counter advances for
   every string, including the ones in `preserved`, so a preserved string still
   consumes its index and the later names are unaffected by the omission. A
   preserved string contributes no pair. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def relabelFrom (newPrefix : String) (preserved : List String) :
    Nat → List String → List (String × String)
  | _,   []        => []
  | pos, a :: rest =>
      (if preserved.contains a then [] else [(a, newPrefix ++ toString pos)])
        ++ relabelFrom newPrefix preserved (pos + 1) rest

/- The full relabeling: every input string paired with a fresh prefixed name
   keyed by its position, except those in `preserved`, which are omitted. -/
def relabeling (newPrefix : String) (preserved : List String)
    (aliases : List String) : List (String × String) :=
  relabelFrom newPrefix preserved 0 aliases

@[grind] lemma relabelFrom_nil (p : String) (pr : List String) (pos : Nat) :
    relabelFrom p pr pos [] = [] := rfl

@[grind] lemma relabelFrom_cons (p : String) (pr : List String) (pos : Nat)
    (a : String) (rest : List String) :
    relabelFrom p pr pos (a :: rest) =
      (if pr.contains a then [] else [(a, p ++ toString pos)])
        ++ relabelFrom p pr (pos + 1) rest := rfl

/- Exposing the element at index `i-1` on the front of `drop (i-1)`, the
   backward-fold step: dropping one fewer element peels one entry off
   `relabelFrom`, with the position counter stepping from `i-1` to `i`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma relabelFrom_drop_step (aliases : List String) (newPrefix : String)
    (preserved : List String) (i : Nat) (hi : 0 < i) (hle : i ≤ aliases.length) :
    relabelFrom newPrefix preserved (i - 1) (aliases.drop (i - 1)) =
      (if preserved.contains aliases[i - 1]! then []
       else [(aliases[i - 1]!, newPrefix ++ toString (i - 1))])
        ++ relabelFrom newPrefix preserved i (aliases.drop i) := by
  have hlt : i - 1 < aliases.length := by omega
  have hcons : aliases.drop (i - 1) = aliases[i - 1]! :: aliases.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relabelFrom_cons]
  have hsucc : i - 1 + 1 = i := by omega
  rw [hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relabeling for an ordered sequence of input strings `aliases`,
   pairing each with a fresh name under `newPrefix`.

   Each string is mapped to a fresh name formed from `newPrefix` and the string's
   ORIGINAL position, EXCEPT for the strings listed in `preserved`, which are left
   out of the relabeling (they contribute no pair). The position counter advances
   for every string, so omitting a preserved string does not shift the names
   assigned to the others.

   `aliases` and `preserved` are read-only — neither is `mut`; the operation reads
   them and returns a fresh relabeling sequence, mutating nothing it is handed
   (directive 5). -/
method buildRelabeling (aliases : List String) (newPrefix : String)
    (preserved : List String) return (out : List (String × String))
  ensures out = relabeling newPrefix preserved aliases
  do
    -- impl-start
    let mut result : List (String × String) := []
    let mut i := aliases.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ aliases.length
      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
      done_with i = 0
      decreasing i
    do
      let a := aliases[i - 1]!
      result := (if preserved.contains a then []
                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct buildRelabeling by
  loom_solve
  all_goals (
    try (rw [relabelFrom_drop_step aliases newPrefix preserved i (by omega) (by omega)])
    try (obtain ⟨hi0, hr⟩ := i_2)
    simp_all [relabeling])
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (G-EQ) AUDIT — django__django-15128 / velvet. VERDICT: SOUND.

SPEC SHAPE: method buildRelabeling(aliases,newPrefix,preserved) with a COMPLETE functional postcondition `ensures out = relabeling newPrefix preserved aliases`, where `relabeling`/`relabelFrom` is a fully-grounded, total, concrete Lean pure function (positional scan emitting `newPrefix++toString pos` per alias, `[]` for preserved aliases, position counter advancing unconditionally). Because the postcondition pins the output to an exact concrete value, any verifying impl must produce EXACTLY that value.

A-LEG AUDIT (my mandate): axioms region is EMPTY; grep confirms NO axiom/sorry/opaque/constant/Classical/native_decide in Solution.lean. refinement.md B/C and mapping.md §3 declare axioms=[] and deep_model_references=[]. => THERE ARE NO A-LEGS. The one genuinely-changed op (rename map gaining the `if alias not in exclude` filter) is modeled DEEPLY as the spelled-out `relabelFrom` fold (leg A4, tagged I), NOT hidden behind an axiom about the function under change. No kind-3 legs. Legs A1/A2/A3 = R (list(alias_map)↔List String; alias_prefix str identity; exclude set↔List membership), A4 = I (comprehension transliteration), A5 = R+I (change_map↔out). Correspondences all hold; there is no ungrounded oracle a wrong impl could exploit.

SAME-SPEC: all 7 attacks + positive_control return True under swebench_unified.markers.same_spec for velvet (only impl region edited).

### VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently ≤4):
- positive_control.lean (correct impl, gold behavior): exit 0 = VERIFIES ✓
- prepatch.lean (unfiltered construction, the pre-patch bug): exit 1 = FAILS => prepatch bug reproduced ✓
- atk_1 off-by-one position (`toString i` vs `toString (i-1)`): exit 1 (rejected)
- atk_2 no filter (== prepatch bug, renames every alias incl. preserved): exit 1 (rejected)
- atk_3 INVERTED filter (keep preserved, drop others): exit 1 (rejected)
- atk_4 control-flow effect (return []): exit 1 (rejected)
- atk_5 partial-domain/boundary (loop `while i>1`, skips index-0 alias): exit 1 (rejected)
- atk_6 ungrounded-oracle ECHO (`return relabeling newPrefix preserved aliases`): exit 0 = VERIFIES
- atk_7 wrong name (drops newPrefix, `toString (i-1)` only): exit 1 (rejected)

ONLY atk_6 verifies, and it verifies precisely because it returns the oracle value — but the oracle IS the correct filtered rename map, so atk_6 is behaviorally CORRECT, not a wrong impl that slips through. Per protocol I materialized atk_6's faithful refined patch (the gold comprehension WITH the `if alias not in exclude` filter = gold patch) and RAN it through the official harness (swebench_unified.harness.run_resolve, django__django-15128, image swebench/sweb.eval.x86_64.django_1776_django-15128:latest): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. This is the accepted resolving-echo case (2026-08-06 policy): a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness.

Every genuinely-wrong output (partial-domain atk_5, boundary/off-by-one atk_1, control-flow atk_4, inverted-filter atk_3, unfiltered-prepatch atk_2, wrong-name atk_7) is REJECTED by the postcondition. No verifying wrong-impl produced a non-resolving faithful patch. verify⇒correct holds; spec is not too weak. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads two plain inputs — an ordered
--  sequence of strings and a set of strings to leave out — together
--  with the fresh prefix to apply, and produces the relabeling sequence handed
--  onward. Every observable is computed structurally from those inputs; no
--  unchanged callee's contract is consumed and no foreign callee is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The relabeling produced for the input strings from position `pos` onward,
   under a fresh `newPrefix`, with any string listed in `preserved` left out.

   Each string is paired with a fresh name `newPrefix ++ toString pos` keyed by
   its ORIGINAL position in the full sequence — the position counter advances for
   every string, including the ones in `preserved`, so a preserved string still
   consumes its index and the later names are unaffected by the omission. A
   preserved string contributes no pair. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def relabelFrom (newPrefix : String) (preserved : List String) :
    Nat → List String → List (String × String)
  | _,   []        => []
  | pos, a :: rest =>
      (if preserved.contains a then [] else [(a, newPrefix ++ toString pos)])
        ++ relabelFrom newPrefix preserved (pos + 1) rest

/- The full relabeling: every input string paired with a fresh prefixed name
   keyed by its position, except those in `preserved`, which are omitted. -/
def relabeling (newPrefix : String) (preserved : List String)
    (aliases : List String) : List (String × String) :=
  relabelFrom newPrefix preserved 0 aliases

@[grind] lemma relabelFrom_nil (p : String) (pr : List String) (pos : Nat) :
    relabelFrom p pr pos [] = [] := rfl

@[grind] lemma relabelFrom_cons (p : String) (pr : List String) (pos : Nat)
    (a : String) (rest : List String) :
    relabelFrom p pr pos (a :: rest) =
      (if pr.contains a then [] else [(a, p ++ toString pos)])
        ++ relabelFrom p pr (pos + 1) rest := rfl

/- Exposing the element at index `i-1` on the front of `drop (i-1)`, the
   backward-fold step: dropping one fewer element peels one entry off
   `relabelFrom`, with the position counter stepping from `i-1` to `i`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma relabelFrom_drop_step (aliases : List String) (newPrefix : String)
    (preserved : List String) (i : Nat) (hi : 0 < i) (hle : i ≤ aliases.length) :
    relabelFrom newPrefix preserved (i - 1) (aliases.drop (i - 1)) =
      (if preserved.contains aliases[i - 1]! then []
       else [(aliases[i - 1]!, newPrefix ++ toString (i - 1))])
        ++ relabelFrom newPrefix preserved i (aliases.drop i) := by
  have hlt : i - 1 < aliases.length := by omega
  have hcons : aliases.drop (i - 1) = aliases[i - 1]! :: aliases.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relabelFrom_cons]
  have hsucc : i - 1 + 1 = i := by omega
  rw [hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relabeling for an ordered sequence of input strings `aliases`,
   pairing each with a fresh name under `newPrefix`.

   Each string is mapped to a fresh name formed from `newPrefix` and the string's
   ORIGINAL position, EXCEPT for the strings listed in `preserved`, which are left
   out of the relabeling (they contribute no pair). The position counter advances
   for every string, so omitting a preserved string does not shift the names
   assigned to the others.

   `aliases` and `preserved` are read-only — neither is `mut`; the operation reads
   them and returns a fresh relabeling sequence, mutating nothing it is handed
   (directive 5). -/
method buildRelabeling (aliases : List String) (newPrefix : String)
    (preserved : List String) return (out : List (String × String))
  ensures out = relabeling newPrefix preserved aliases
  do
    -- impl-start
    let mut result : List (String × String) := []
    let mut i := aliases.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ aliases.length
      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
      done_with i = 0
      decreasing i
    do
      let a := aliases[i - 1]!
      result := (if preserved.contains a then []
                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct buildRelabeling by
  loom_solve
  all_goals (
    try (rw [relabelFrom_drop_step aliases newPrefix preserved i (by omega) (by omega)])
    try (obtain ⟨hi0, hr⟩ := i_2)
    simp_all [relabeling])
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (G-EQ) AUDIT — django__django-15128 / velvet. VERDICT: SOUND.

SPEC SHAPE: method buildRelabeling(aliases,newPrefix,preserved) with a COMPLETE functional postcondition `ensures out = relabeling newPrefix preserved aliases`, where `relabeling`/`relabelFrom` is a fully-grounded, total, concrete Lean pure function (positional scan emitting `newPrefix++toString pos` per alias, `[]` for preserved aliases, position counter advancing unconditionally). Because the postcondition pins the output to an exact concrete value, any verifying impl must produce EXACTLY that value.

A-LEG AUDIT (my mandate): axioms region is EMPTY; grep confirms NO axiom/sorry/opaque/constant/Classical/native_decide in Solution.lean. refinement.md B/C and mapping.md §3 declare axioms=[] and deep_model_references=[]. => THERE ARE NO A-LEGS. The one genuinely-changed op (rename map gaining the `if alias not in exclude` filter) is modeled DEEPLY as the spelled-out `relabelFrom` fold (leg A4, tagged I), NOT hidden behind an axiom about the function under change. No kind-3 legs. Legs A1/A2/A3 = R (list(alias_map)↔List String; alias_prefix str identity; exclude set↔List membership), A4 = I (comprehension transliteration), A5 = R+I (change_map↔out). Correspondences all hold; there is no ungrounded oracle a wrong impl could exploit.

SAME-SPEC: all 7 attacks + positive_control return True under swebench_unified.markers.same_spec for velvet (only impl region edited).

### VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently ≤4):
- positive_control.lean (correct impl, gold behavior): exit 0 = VERIFIES ✓
- prepatch.lean (unfiltered construction, the pre-patch bug): exit 1 = FAILS => prepatch bug reproduced ✓
- atk_1 off-by-one position (`toString i` vs `toString (i-1)`): exit 1 (rejected)
- atk_2 no filter (== prepatch bug, renames every alias incl. preserved): exit 1 (rejected)
- atk_3 INVERTED filter (keep preserved, drop others): exit 1 (rejected)
- atk_4 control-flow effect (return []): exit 1 (rejected)
- atk_5 partial-domain/boundary (loop `while i>1`, skips index-0 alias): exit 1 (rejected)
- atk_6 ungrounded-oracle ECHO (`return relabeling newPrefix preserved aliases`): exit 0 = VERIFIES
- atk_7 wrong name (drops newPrefix, `toString (i-1)` only): exit 1 (rejected)

ONLY atk_6 verifies, and it verifies precisely because it returns the oracle value — but the oracle IS the correct filtered rename map, so atk_6 is behaviorally CORRECT, not a wrong impl that slips through. Per protocol I materialized atk_6's faithful refined patch (the gold comprehension WITH the `if alias not in exclude` filter = gold patch) and RAN it through the official harness (swebench_unified.harness.run_resolve, django__django-15128, image swebench/sweb.eval.x86_64.django_1776_django-15128:latest): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. This is the accepted resolving-echo case (2026-08-06 policy): a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness.

Every genuinely-wrong output (partial-domain atk_5, boundary/off-by-one atk_1, control-flow atk_4, inverted-filter atk_3, unfiltered-prepatch atk_2, wrong-name atk_7) is REJECTED by the postcondition. No verifying wrong-impl produced a non-resolving faithful patch. verify⇒correct holds; spec is not too weak. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified: (1) scripts/lean_verify.sh on Solution.lean exits 0 — prove_correct buildRelabeling discharges against the frozen `ensures out = relabeling newPrefix preserved aliases`. (2) markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True; spec region (imports/axioms/pure/pre/post + method signature+ensures) is byte-identical. Prepatch (unfiltered relabel, no `if preserved.contains`) correctly FAILS verification, confirming the spec is discriminating (G-DIFF). (3) The model relabeling/relabelFrom faithfully transliterates the gold comprehension: position counter advances for every element including preserved (matches enumerate), preserved.contains a ↔ alias in exclude, newPrefix++toString pos ↔ '%s%d'%(prefix,pos). No over-strength: an impl equal to the gold change_map passes; the model captures exactly the gold behavior, not more. Type-abstraction (mapping.md §2) is sound: unique alias_map keys ↔ distinct List elements; set↔list membership observationally identical for `contains`; dict compared order-faithfully to insertion order. axioms=[] / no deep-model callees is correct — the modeled op is self-contained over its three inputs. Spec is neither too strong nor drifting.

Counterexample / evidence:

```
N/A — no divergence on the real callee's domain. G-CONF: 0 disagreements over 100010 inputs (seed=15128), incl. boundary/issue-shaped cases.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "5. Conclusion: faithful + non-leaking is provably impossible":

> This is not a de-narration gap. The round-1 refinement already neutralized the *purpose* prose; the residual "leak" is the *behavior itself* — the modeled filter — which is mandatory for faithfulness and unexpressible in PS-public terms.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "5. Conclusion: faithful + non-leaking is provably impossible":

> A **faithful** spec must reject the modeled-op prepatch (which renames the base alias and fails the F2P with KeyError). The only property that does so is the preserve-the-`exclude`-subset filter — the gold mechanism.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `095b5a3ca388`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Spec-view integrity confirmed: same_spec(Solution.lean, Solution_prepatch.lean)=True under velvet backend; spec region byte-identical, only impl/proof differ.

Gold discriminator: `if alias not in exclude` in bump_prefix's rename-map comprehension {alias: '%s%d'%(prefix,pos) for pos,alias in enumerate(alias_map) if alias not in exclude} — hold back the shared/initial (preserved) alias from renaming while enumerate numbering advances for every alias.

Public problem_statement (fetched from data/swe_bench_verified/test.jsonl): reports ONLY the symptom (Query.change_aliases AssertionError, change_map={'T4':'T5','T5':'T6'}, keys intersect values) and proposes a DIFFERENT remedy — provide rhs.alias_map to Query.join/Query.table_alias and increment the new alias suffix until it is not in rhs.alias_map. Token scan over PS: exclude=0, initial=0, bump_prefix=0, prefix=0, preserve=0, shared=0, base table=0, relabel=0, rename=0 (alias=11 but only in the symptom framing). None of the gold-mechanism vocabulary is in PS; it lives only in hints_text (Simon Charette: 'have bump_prefix adjust all the aliases but the initial one so it can still be used as the merge starting point').

LEAK: the spec view's pure region (relabelFrom/relabeling) transliterates the gold's exact mechanism — omit the preserved alias from the map while the position counter still advances for every alias including preserved ones. Both the Lean code (line 32) and the pure-region docstrings spell this out. A consumer reading the spec view alone recovers the gold's 'omit the preserved alias, keep numbering positional' behavior, which is NOT derivable from problem_statement (which suggests a suffix-bump in Query.join/table_alias, a different function and different fix) — only from hints_text/gold. This is a genuine leak beyond the public problem_statement.

This raw leakage judgment matches the recorded G-PANEL-3 fail. The bundle carries an accepted RELAXED_LEAKAGE.md (relaxed_leakage=true) arguing faithful+non-leaking is impossible here (the PS-derivable 'disjoint keys/values' property is spec-too-weak, satisfied by the prepatch too); under G-PANEL-3-defers-to-RELAXED policy the recorded status becomes pass+note. My attacker-role verdict on the leakage question itself is LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.