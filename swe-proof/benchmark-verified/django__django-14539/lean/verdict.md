# P2 adversarial audit — django__django-14539

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None. No same-spec wrong impl closed, so no verify⇒¬resolve witness exists. The spec problem_spec_peelTrailingPunct pins all three output components by EXACT equality (clause1 result.1 = dropRightN token punctCount; clause2 result.2.1 = takeRightN token punctCount ++ tailPunct; clause3 result.2.2 = decide(decoded≠stripped)) plus a conservation clause4 — a TOTAL FUNCTIONAL relation with zero semantic slack. Any impl deviating on any input makes the Prop genuinely FALSE (not merely unprovable), so no closing-but-non-resolving impl can exist. All 7 distinct wrong impls fail to verify (exit 1).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,9 +84,10 @@
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
     let punctCount := decoded.length - stripped.length
-    tailPunct := takeRightN token punctCount ++ tailPunct
-    token := dropRightN token punctCount
-    trimmed := true
+    if punctCount ≥ 2 then
+      tailPunct := takeRightN token punctCount ++ tailPunct
+      token := dropRightN token punctCount
+      trimmed := true
   return (token, tailPunct, trimmed)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
   let decoded := decode token
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
-    let punctCount := decoded.length - stripped.length
+    let punctCount := decoded.length - stripped.length + 1
     tailPunct := takeRightN token punctCount ++ tailPunct
     token := dropRightN token punctCount
     trimmed := true
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,6 @@
   if decoded ≠ stripped then
     let punctCount := decoded.length - stripped.length
     tailPunct := takeRightN token punctCount ++ tailPunct
-    token := dropRightN token punctCount
     trimmed := true
   return (token, tailPunct, trimmed)
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,13 @@
     List Char × List Char × Bool := Id.run do
   let mut token := token
   let mut tailPunct := tailPunct
-  let mut trimmed := false
+  let mut trimmed := true
   let decoded := decode token
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
     let punctCount := decoded.length - stripped.length
     tailPunct := takeRightN token punctCount ++ tailPunct
     token := dropRightN token punctCount
-    trimmed := true
   return (token, tailPunct, trimmed)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,8 @@
   let decoded := decode token
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
-    let punctCount := decoded.length - stripped.length
-    tailPunct := takeRightN token punctCount ++ tailPunct
-    token := dropRightN token punctCount
+    tailPunct := token.drop stripped.length ++ tailPunct
+    token := dropRightN token (decoded.length - stripped.length)
     trimmed := true
   return (token, tailPunct, trimmed)
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
   let decoded := decode token
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
-    let punctCount := decoded.length - stripped.length
+    let punctCount := token.length - (rstripPunct token).length
     tailPunct := takeRightN token punctCount ++ tailPunct
     token := dropRightN token punctCount
     trimmed := true
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
   let stripped := rstripPunct decoded
   if decoded ≠ stripped then
     let punctCount := decoded.length - stripped.length
-    tailPunct := takeRightN token punctCount ++ tailPunct
+    tailPunct := tailPunct ++ takeRightN token punctCount
     token := dropRightN token punctCount
     trimmed := true
   return (token, tailPunct, trimmed)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Peeling a run of trailing punctuation off the end of a text token.

When a piece of text is examined for a possible link, any run of trailing
punctuation characters (`.`, `,`, `:`, `;`, `!`) at the end of the token is
peeled off and prepended to a separate accumulator that collects such trailing
punctuation, so that the punctuation is not treated as part of the link.

The token may contain HTML-escaped sequences ("html escaped string" in the
report). The *length* of the trailing-punctuation run is therefore measured on
the entity-DECODED view of the token (entity sequences such as `&lt` are decoded
first, so a `;` that is part of an entity is not mistaken for punctuation). The
characters actually peeled off, however, are taken from the END of the ORIGINAL
token, and the same count is removed from it. As a result the characters removed
from the token are exactly the characters added to the accumulator: the
concatenation `token ++ accumulator` is preserved by the operation. A boolean
records whether anything was peeled.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- A standard HTML entity decoder: maps a character sequence to its decoded
form (entity sequences are replaced by the character(s) they denote; all other
characters are left unchanged). Decoding never lengthens the sequence. The
operation under specification does not change this decoder; it is used only to
measure where the trailing-punctuation run begins. Declared opaque so it can
appear in the executable implementation; no further property of it is consumed
(its concrete behavior is exercised by the differential conformance check). -/
opaque decode : List Char → List Char
-- axioms-end

-- pure-start
/-- The trailing-punctuation alphabet: period, comma, colon, semicolon, bang. -/
def TRAILING_PUNCT : List Char := ['.', ',', ':', ';', '!']

/-- Drop the maximal suffix consisting of trailing-punctuation characters
(the analogue of Python's `s.rstrip('.,:;!')`). -/
def rstripPunct (cs : List Char) : List Char :=
  (cs.reverse.dropWhile (fun c => TRAILING_PUNCT.contains c)).reverse

/-- The first `length - n` characters — i.e. all but the last `n`
(the analogue of Python's `s[:-n]` for `1 ≤ n ≤ length`). -/
def dropRightN (cs : List Char) (n : Nat) : List Char := cs.take (cs.length - n)

/-- The last `n` characters (the analogue of Python's `s[-n:]` for
`1 ≤ n ≤ length`). -/
def takeRightN (cs : List Char) (n : Nat) : List Char := cs.drop (cs.length - n)
-- pure-end

-- post-conditions-start
/-- Let `decoded` be the entity-decoded view of `token`, `stripped` the result
of dropping its trailing punctuation, and `punctCount` the number of characters
dropped. The operation:

* leaves the token equal to its original minus its last `punctCount` characters;
* sets the accumulator to those last `punctCount` characters of the original
  token, prepended to the incoming accumulator;
* reports `true` iff the decoded view actually had trailing punctuation;
* conserves characters — `token ++ accumulator` is unchanged (the punctuation is
  MOVED from the token's tail to the accumulator's head, never duplicated). -/
def problem_spec_peelTrailingPunct (token tailPunct : List Char)
    (result : List Char × List Char × Bool) : Prop :=
  let decoded := decode token
  let stripped := rstripPunct decoded
  let punctCount := decoded.length - stripped.length
  result.1 = dropRightN token punctCount ∧
  result.2.1 = takeRightN token punctCount ++ tailPunct ∧
  result.2.2 = decide (decoded ≠ stripped) ∧
  result.1 ++ result.2.1 = token ++ tailPunct
-- post-conditions-end

-- impl-start
def implementation_peelTrailingPunct (token tailPunct : List Char) :
    List Char × List Char × Bool := Id.run do
  let mut token := token
  let mut tailPunct := tailPunct
  let mut trimmed := false
  let decoded := decode token
  let stripped := rstripPunct decoded
  if decoded ≠ stripped then
    let punctCount := decoded.length - stripped.length
    tailPunct := takeRightN token punctCount ++ tailPunct
    token := dropRightN token punctCount
    trimmed := true
  return (token, tailPunct, trimmed)
-- impl-end

-- proof-start
theorem correct_peelTrailingPunct :
    ∀ (token tailPunct : List Char),
      problem_spec_peelTrailingPunct token tailPunct
        (implementation_peelTrailingPunct token tailPunct) := by
  intro token tailPunct
  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct
  simp only [Id.run, bind, pure]
  by_cases h : decode token ≠ rstripPunct (decode token)
  · rw [if_pos h]
    refine ⟨rfl, rfl, (decide_eq_true h).symm, ?_⟩
    simp only [dropRightN, takeRightN]
    rw [← List.append_assoc, List.take_append_drop]
  · rw [if_neg h]
    push_neg at h
    have hc : (decode token).length - (rstripPunct (decode token)).length = 0 := by
      have := congrArg List.length h; omega
    refine ⟨?_, ?_, (decide_eq_false (not_not_intro h)).symm, rfl⟩
    · simp only [dropRightN, hc, Nat.sub_zero, List.take_length]
    · simp only [takeRightN, hc, Nat.sub_zero, List.drop_length, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifications run concurrently in 2 background batches of 4 (≤4 at a time).

SAME-SPEC: all 7 attacks + pos_control checked True via swebench_unified.markers.same_spec (get_backend('lean')). Built by copying Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical).

COMMAND (each): bash scripts/lean_verify.sh <file>
### Results
- pos_control.lean (gold impl): exit 0 (verifies, no sorry).
- pos_axcheck.lean (pos_control + `#print axioms correct_peelTrailingPunct`): exit 0; axioms = [propext, Classical.choice, Quot.sound] — NO sorryAx, no custom axioms. CLEAN.
- atk_1 (partial-domain: only peel when punctCount≥2): exit 1.
- atk_2 (boundary off-by-one: punctCount+1): exit 1.
- atk_3 (control-flow-effect: move punct to tail but forget to trim token): exit 1.
- atk_4 (ungrounded-oracle echo: trimmed:=true unconditionally): exit 1.
- atk_5 (prepatch bug: tailPunct := token.drop stripped.length, index on decoded view): exit 1.
- atk_6 (wrong oracle: punctCount measured on ORIGINAL token via rstripPunct token, ignoring decode): exit 1.
- atk_7 (wrong accumulator order: tailPunct ++ takeRightN token punctCount, wrong side): exit 1.

All 7 wrong impls fail with genuine proof errors (`And.intro rfl` / decide mismatch application errors) — the spec Prop is genuinely false for each, not just unprovable by the carried tactic. Because NO wrong impl closed, step-2 patch-materialization + run_resolve is vacuous (only a closing clean-axiom impl needs its faithful patch resolved).

A-LEG / refinement.md AUDIT: every leg is R (type bijection rows), I (ops #2-#7 identical concrete slicing), or A-reference (op #1 decode ↔ html.unescape). NO A-consumed, NO kind-3 (changed-inexpressible) leg. The single A leg `decode` is opaque and UNCONSTRAINED: the proof consumes no property of it — the conservation clause closes via List.take_append_drop on `token` (in the if_pos branch: `rw [← List.append_assoc, List.take_append_drop]`), and the no-punct branch uses only length arithmetic. Correspondence to the real callee holds (mapping.md: html.unescape at django/utils/html.py:284, verbatim in both shadow and patched reference of conformance_check.py; decoding never lengthens ⇒ punctCount ≤ decoded.length ≤ token.length inside the guard, so len-n arithmetic never underflows). G-CONF exercises the real decoder (SEED=20210619, N_RANDOM=120000 ≥ 1e5, incl. issue trigger 'google.com/?q=1&lt!').

MODEL↔PATCH CORRESPONDENCE: patch.diff post-patch lines map op-for-op to impl (punctuation_count = len(middle_unescaped)-len(stripped) ↔ decoded.length-stripped.length; middle[-pc:] ↔ takeRightN; middle[:-pc] ↔ dropRightN). The discriminating fix (clause4 conservation) is exactly what the prepatch (atk_5-shaped) impl violates on entity-bearing tokens.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls (7 run) all failed to verify; positive control verifies with clean axioms; no closing wrong impl exists so verify⇒correct is not falsifiable here. Not INCONCLUSIVE — every attack + the needed axiom check completed with recorded exit codes.

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
None. No same-spec wrong impl closed, so no verify⇒¬resolve witness exists. The spec problem_spec_peelTrailingPunct pins all three output components by EXACT equality (clause1 result.1 = dropRightN token punctCount; clause2 result.2.1 = takeRightN token punctCount ++ tailPunct; clause3 result.2.2 = decide(decoded≠stripped)) plus a conservation clause4 — a TOTAL FUNCTIONAL relation with zero semantic slack. Any impl deviating on any input makes the Prop genuinely FALSE (not merely unprovable), so no closing-but-non-resolving impl can exist. All 7 distinct wrong impls fail to verify (exit 1).
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
import Mathlib
-- imports-end

/-!
Peeling a run of trailing punctuation off the end of a text token.

When a piece of text is examined for a possible link, any run of trailing
punctuation characters (`.`, `,`, `:`, `;`, `!`) at the end of the token is
peeled off and prepended to a separate accumulator that collects such trailing
punctuation, so that the punctuation is not treated as part of the link.

The token may contain HTML-escaped sequences ("html escaped string" in the
report). The *length* of the trailing-punctuation run is therefore measured on
the entity-DECODED view of the token (entity sequences such as `&lt` are decoded
first, so a `;` that is part of an entity is not mistaken for punctuation). The
characters actually peeled off, however, are taken from the END of the ORIGINAL
token, and the same count is removed from it. As a result the characters removed
from the token are exactly the characters added to the accumulator: the
concatenation `token ++ accumulator` is preserved by the operation. A boolean
records whether anything was peeled.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- A standard HTML entity decoder: maps a character sequence to its decoded
form (entity sequences are replaced by the character(s) they denote; all other
characters are left unchanged). Decoding never lengthens the sequence. The
operation under specification does not change this decoder; it is used only to
measure where the trailing-punctuation run begins. Declared opaque so it can
appear in the executable implementation; no further property of it is consumed
(its concrete behavior is exercised by the differential conformance check). -/
opaque decode : List Char → List Char
-- axioms-end

-- pure-start
/-- The trailing-punctuation alphabet: period, comma, colon, semicolon, bang. -/
def TRAILING_PUNCT : List Char := ['.', ',', ':', ';', '!']

/-- Drop the maximal suffix consisting of trailing-punctuation characters
(the analogue of Python's `s.rstrip('.,:;!')`). -/
def rstripPunct (cs : List Char) : List Char :=
  (cs.reverse.dropWhile (fun c => TRAILING_PUNCT.contains c)).reverse

/-- The first `length - n` characters — i.e. all but the last `n`
(the analogue of Python's `s[:-n]` for `1 ≤ n ≤ length`). -/
def dropRightN (cs : List Char) (n : Nat) : List Char := cs.take (cs.length - n)

/-- The last `n` characters (the analogue of Python's `s[-n:]` for
`1 ≤ n ≤ length`). -/
def takeRightN (cs : List Char) (n : Nat) : List Char := cs.drop (cs.length - n)
-- pure-end

-- post-conditions-start
/-- Let `decoded` be the entity-decoded view of `token`, `stripped` the result
of dropping its trailing punctuation, and `punctCount` the number of characters
dropped. The operation:

* leaves the token equal to its original minus its last `punctCount` characters;
* sets the accumulator to those last `punctCount` characters of the original
  token, prepended to the incoming accumulator;
* reports `true` iff the decoded view actually had trailing punctuation;
* conserves characters — `token ++ accumulator` is unchanged (the punctuation is
  MOVED from the token's tail to the accumulator's head, never duplicated). -/
def problem_spec_peelTrailingPunct (token tailPunct : List Char)
    (result : List Char × List Char × Bool) : Prop :=
  let decoded := decode token
  let stripped := rstripPunct decoded
  let punctCount := decoded.length - stripped.length
  result.1 = dropRightN token punctCount ∧
  result.2.1 = takeRightN token punctCount ++ tailPunct ∧
  result.2.2 = decide (decoded ≠ stripped) ∧
  result.1 ++ result.2.1 = token ++ tailPunct
-- post-conditions-end

-- impl-start
def implementation_peelTrailingPunct (token tailPunct : List Char) :
    List Char × List Char × Bool := Id.run do
  let mut token := token
  let mut tailPunct := tailPunct
  let mut trimmed := false
  let decoded := decode token
  let stripped := rstripPunct decoded
  if decoded ≠ stripped then
    let punctCount := decoded.length - stripped.length
    tailPunct := takeRightN token punctCount ++ tailPunct
    token := dropRightN token punctCount
    trimmed := true
  return (token, tailPunct, trimmed)
-- impl-end

-- proof-start
theorem correct_peelTrailingPunct :
    ∀ (token tailPunct : List Char),
      problem_spec_peelTrailingPunct token tailPunct
        (implementation_peelTrailingPunct token tailPunct) := by
  intro token tailPunct
  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct
  simp only [Id.run, bind, pure]
  by_cases h : decode token ≠ rstripPunct (decode token)
  · rw [if_pos h]
    refine ⟨rfl, rfl, (decide_eq_true h).symm, ?_⟩
    simp only [dropRightN, takeRightN]
    rw [← List.append_assoc, List.take_append_drop]
  · rw [if_neg h]
    push_neg at h
    have hc : (decode token).length - (rstripPunct (decode token)).length = 0 := by
      have := congrArg List.length h; omega
    refine ⟨?_, ?_, (decide_eq_false (not_not_intro h)).symm, rfl⟩
    · simp only [dropRightN, hc, Nat.sub_zero, List.take_length]
    · simp only [takeRightN, hc, Nat.sub_zero, List.drop_length, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifications run concurrently in 2 background batches of 4 (≤4 at a time).

SAME-SPEC: all 7 attacks + pos_control checked True via swebench_unified.markers.same_spec (get_backend('lean')). Built by copying Solution.lean and editing ONLY the impl region (axioms/pure/pre/post byte-identical).

COMMAND (each): bash scripts/lean_verify.sh <file>
### Results
- pos_control.lean (gold impl): exit 0 (verifies, no sorry).
- pos_axcheck.lean (pos_control + `#print axioms correct_peelTrailingPunct`): exit 0; axioms = [propext, Classical.choice, Quot.sound] — NO sorryAx, no custom axioms. CLEAN.
- atk_1 (partial-domain: only peel when punctCount≥2): exit 1.
- atk_2 (boundary off-by-one: punctCount+1): exit 1.
- atk_3 (control-flow-effect: move punct to tail but forget to trim token): exit 1.
- atk_4 (ungrounded-oracle echo: trimmed:=true unconditionally): exit 1.
- atk_5 (prepatch bug: tailPunct := token.drop stripped.length, index on decoded view): exit 1.
- atk_6 (wrong oracle: punctCount measured on ORIGINAL token via rstripPunct token, ignoring decode): exit 1.
- atk_7 (wrong accumulator order: tailPunct ++ takeRightN token punctCount, wrong side): exit 1.

All 7 wrong impls fail with genuine proof errors (`And.intro rfl` / decide mismatch application errors) — the spec Prop is genuinely false for each, not just unprovable by the carried tactic. Because NO wrong impl closed, step-2 patch-materialization + run_resolve is vacuous (only a closing clean-axiom impl needs its faithful patch resolved).

A-LEG / refinement.md AUDIT: every leg is R (type bijection rows), I (ops #2-#7 identical concrete slicing), or A-reference (op #1 decode ↔ html.unescape). NO A-consumed, NO kind-3 (changed-inexpressible) leg. The single A leg `decode` is opaque and UNCONSTRAINED: the proof consumes no property of it — the conservation clause closes via List.take_append_drop on `token` (in the if_pos branch: `rw [← List.append_assoc, List.take_append_drop]`), and the no-punct branch uses only length arithmetic. Correspondence to the real callee holds (mapping.md: html.unescape at django/utils/html.py:284, verbatim in both shadow and patched reference of conformance_check.py; decoding never lengthens ⇒ punctCount ≤ decoded.length ≤ token.length inside the guard, so len-n arithmetic never underflows). G-CONF exercises the real decoder (SEED=20210619, N_RANDOM=120000 ≥ 1e5, incl. issue trigger 'google.com/?q=1&lt!').

MODEL↔PATCH CORRESPONDENCE: patch.diff post-patch lines map op-for-op to impl (punctuation_count = len(middle_unescaped)-len(stripped) ↔ decoded.length-stripped.length; middle[-pc:] ↔ takeRightN; middle[:-pc] ↔ dropRightN). The discriminating fix (clause4 conservation) is exactly what the prepatch (atk_5-shaped) impl violates on entity-bearing tokens.

VERDICT: SOUND. ≥5 distinct same-spec wrong impls (7 run) all failed to verify; positive control verifies with clean axioms; no closing wrong impl exists so verify⇒correct is not falsifiable here. Not INCONCLUSIVE — every attack + the needed axiom check completed with recorded exit codes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit for django__django-14539 (lean). (1) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend)=True — spec region byte-identical; only impl+proof differ. (2) Solution.lean elaborates (lean_verify exit 0); #print axioms correct_peelTrailingPunct = [propext, Classical.choice, Quot.sound] only — no sorryAx, proof genuine; decode is opaque (no consumed axiom), so A-reference correctly not baked into the proof. (3) Real repo callee (django/utils/html.py trim_punctuation trailing-punct block, base 6a5ef557f8; patched: punctuation_count=len(mu)-len(stripped); trail=middle[-pc:]+trail; middle=middle[:-pc]) with decode<->html.unescape. Instantiated the equational spec Prop (result.1=token[:len-pc], result.2.1=token[len-pc:]++tail, result.2.2=(decoded!=stripped)) against verbatim patched Python: bundle G-CONF 120,012 checks 0 disagreements; my adversarial edge catalogue (empty, punct-only, multi-codepoint named entities &nGt;/&NotEqualTilde;, numeric refs &#128512;, leading bangs, bug trigger google.com/?q=1&lt!) 0 diverge; 300,000 random entity+punct fuzz 0 diverge. pc=0 no-punct branch: spec yields (token, tail, False) matching real no-op. Spec neither too strong nor drifted; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. same_spec(Solution.lean, Solution_prepatch.lean)=True: the fix lives ENTIRELY in the elided impl/proof regions; the consumer spec view is byte-identical between patched and prepatch bundles, so it cannot reveal which slice the patch changed. Mechanical G-LEAK screen (leakage.screen over the lean spec view) passes: no diff markers, no reproduced gold-patch line (the discriminating tokens 'punctuation_count', 'middle[len(stripped):]', 'middle[:-punctuation_count]' do NOT appear), patched file path django/utils/html.py absent, the sole changed symbol 'trim_punctuation' is not echoed in any identifier or comment, and no narration terms. Semantic content is fully derivable from the PUBLIC problem_statement (assessed against it, NOT hints_text): the statement already discloses the urlize() html-escaped-string + trailing-punctuation bug, the exact failing input 'google.com/?q=1&lt!', and the actual-vs-expected output showing the characters 'lt' DUPLICATED (&lt</a>lt!) vs the correct non-duplicated output. The spec's two load-bearing ideas map exactly onto that public content: (1) measuring the trailing-punct run on the entity-DECODED view = the 'html escaped string' aspect named in the report; (2) the conservation clause result.1 ++ result.2.1 = token ++ tailPunct (characters MOVED, never duplicated) = precisely the correction the public example demonstrates. Pure-helper docstrings cite only generic Python slice semantics (s[:-n], s[-n:]) to pin helper meaning; slicing is universal and does not localize the edit. Meta records G-LEAK pass and G-PANEL-3 NO-LEAKAGE (opus); relaxed_leakage=None (not a relaxed bundle). No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
