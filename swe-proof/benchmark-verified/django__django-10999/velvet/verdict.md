# P2 adversarial audit — django__django-10999

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- axioms-end
@@ -98,22 +98,8 @@
   ensures out = parseDuration text
   do
     -- impl-start
-    let mut st := initPS
-    let mut i := 0
-    while i < text.length
-      -- invariants-start
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
-    do
-      st := step st text[i]!
-      i := i + 1
-    return decode st
+    return parseDuration text
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
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
 -- axioms-end
@@ -98,22 +98,9 @@
   ensures out = parseDuration text
   do
     -- impl-start
-    let mut st := initPS
-    let mut i := 0
-    while i < text.length
-      -- invariants-start
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
-    do
-      st := step st text[i]!
-      i := i + 1
-    return decode st
+    return decode (text.foldl step initPS)
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
+  · simp [parseDuration]
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
 -- axioms-end
@@ -100,13 +100,9 @@
     -- impl-start
     let mut st := initPS
     let mut i := 0
-    while i < text.length
-      -- invariants-start
+    while i + 1 < text.length
       invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
+      done_with i + 1 = text.length ∨ text.length = 0
     do
       st := step st text[i]!
       i := i + 1
@@ -115,5 +111,3 @@
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
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
 -- axioms-end
@@ -98,22 +98,8 @@
   ensures out = parseDuration text
   do
     -- impl-start
-    let mut st := initPS
-    let mut i := 0
-    while i < text.length
-      -- invariants-start
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
-    do
-      st := step st text[i]!
-      i := i + 1
-    return decode st
+    return none
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
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
 -- axioms-end
@@ -101,19 +101,27 @@
     let mut st := initPS
     let mut i := 0
     while i < text.length
-      -- invariants-start
       invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
       done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
     do
-      st := step st text[i]!
+      let c := text[i]!
+      let st' : PS :=
+        if st.valid = false then st
+        else if c = '-' then
+          if st.seen then { st with valid := false, seen := true }
+          else { st with sign := -1, seen := true }
+        else if c = ':' then
+          if st.curlen = 0 then { st with valid := false, seen := true }
+          else if st.groups = 3 then { st with valid := false, seen := true }
+          else { st with acc := st.acc * 60 + st.sign * st.cur, cur := 0, sign := 1,
+                         groups := st.groups + 1, curlen := 0, seen := true }
+        else if isDigit c then
+          { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }
+        else { st with valid := false, seen := true }
+      st := st'
       i := i + 1
     return decode st
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
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
 -- axioms-end
@@ -98,22 +98,11 @@
   ensures out = parseDuration text
   do
     -- impl-start
-    let mut st := initPS
-    let mut i := 0
-    while i < text.length
-      -- invariants-start
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
-    do
-      st := step st text[i]!
-      i := i + 1
-    return decode st
+    if text.length = 1 then
+      return decode (text.foldl step initPS)
+    else
+      return none
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
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
 -- axioms-end
@@ -98,22 +98,8 @@
   ensures out = parseDuration text
   do
     -- impl-start
-    let mut st := initPS
-    let mut i := 0
-    while i < text.length
-      -- invariants-start
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant st = (text.take i).foldl step initPS
-      done_with i = text.length
-      decreasing text.length - i
-      -- invariants-end
-    do
-      st := step st text[i]!
-      i := i + 1
-    return decode st
+    return decode (text.reverse.foldl step initPS)
     -- impl-end
 
 prove_correct parseDurationSeconds by
   loom_solve
-  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
-  · simp_all [parseDuration, List.take_length]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The carrier of a single left-to-right scan over a colon-separated,
   sign-prefixed numeric time string.

   * `sign`   : the magnitude's overall sign (1, or -1 once a leading '-' is read);
   * `acc`    : the value of the already-closed groups, folded base-sixty;
   * `cur`    : the value of the group currently being read (base ten);
   * `groups` : how many groups have been opened (starts at 1);
   * `curlen` : how many digits the current group has so far;
   * `valid`  : whether the prefix read so far is still well-formed;
   * `seen`   : whether any character has been consumed (a '-' is only a sign
                in the very first position). -/
structure PS where
  sign   : Int
  acc    : Int
  cur    : Int
  groups : Nat
  curlen : Nat
  valid  : Bool
  seen   : Bool
deriving Inhabited

/- The scan before any character is consumed: positive, empty, well-formed. -/
def initPS : PS := ⟨1, 0, 0, 1, 0, true, false⟩

/- ASCII decimal-digit test and value, in terms of code points. -/
def isDigit (c : Char) : Bool := '0'.toNat ≤ c.toNat && c.toNat ≤ '9'.toNat
def digitVal (c : Char) : Int := (c.toNat : Int) - ('0'.toNat : Int)

/- One step of the scan. A '-' is meaningful only as the very first character,
   where it makes the whole magnitude negative; encountered anywhere else it
   makes the input ill-formed. A ':' closes the current group (folding it into
   `acc` base-sixty) provided the group is non-empty and at most three groups
   total are produced. A decimal digit extends the current group base-ten. Any
   other character is ill-formed. -/
def step (st : PS) (c : Char) : PS :=
  if st.valid = false then st
  else if c = '-' then
    if st.seen then { st with valid := false, seen := true }
    else { st with sign := -1, seen := true }
  else if c = ':' then
    if st.curlen = 0 then { st with valid := false, seen := true }
    else if st.groups = 3 then { st with valid := false, seen := true }
    else { st with acc := st.acc * 60 + st.cur, cur := 0,
                   groups := st.groups + 1, curlen := 0, seen := true }
  else if isDigit c then
    { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }
  else { st with valid := false, seen := true }

/- Read off the total number of seconds from a finished scan: a well-formed,
   non-empty-final-group scan yields the signed base-sixty value of all groups;
   anything else yields no value. The overall sign multiplies the entire
   magnitude (every group), so the result of e.g. a two-group "a:b" with a
   leading minus is -(a*60 + b). -/
def decode (st : PS) : Option Int :=
  if st.valid = false then none
  else if st.curlen = 0 then none
  else some (st.sign * (st.acc * 60 + st.cur))

/- The whole-string parse: fold `step` over the characters left to right, then
   `decode` the final scan. `none` means the string is not a well-formed
   sign-and-colon time component. -/
def parseDuration (text : List Char) : Option Int :=
  decode (text.foldl step initPS)
-- pure-end

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element. This is the single fact the loop body
   leaves for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method parseDurationSeconds (text : List Char) return (out : Option Int)
  require text ≠ []
  require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'
  ensures out = parseDuration text
  do
    -- impl-start
    let mut st := initPS
    let mut i := 0
    while i < text.length
      -- invariants-start
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant st = (text.take i).foldl step initPS
      done_with i = text.length
      -- invariants-end
    do
      st := step st text[i]!
      i := i + 1
    return decode st
    -- impl-end

prove_correct parseDurationSeconds by
  loom_solve
  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
  · simp_all [parseDuration, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: parseDurationSeconds is FULLY FUNCTIONAL-PINNED by `ensures out = parseDuration text` over the require-domain (text != [] and all chars in {0-9,:,-}). Any impl that verifies MUST compute exactly `parseDuration text` on-domain, so all verifying impls are behaviorally identical. The only real falsification surface is (a) model->gold correspondence and (b) the off-domain F2P rows — audited below.

SAME-SPEC: all 7 attacks + pos.lean confirmed same_spec=True (impl/proof regions elided; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (scripts/lean_verify.sh <f>):
- pos.lean (correct impl, forward fold): EXIT=0 VERIFIES (positive control).
- atk_1.lean (ungrounded-oracle ECHO: `return parseDuration text`): EXIT=0 VERIFIES.
- atk_2.lean (alt control-flow: `return decode (text.foldl step initPS)`, proof closed with `simp [parseDuration]`): EXIT=0 VERIFIES.
- atk_3.lean (boundary off-by-one: loop `i+1 < length`, drops last char): EXIT=1 FAILS (unsolved goals — diverges from parseDuration).
- atk_4.lean (constant `return none`): EXIT=1 FAILS.
- atk_5.lean (PREPATCH sign bug: sign folded into first group only, reset at ':'): EXIT=1 FAILS.
- atk_6.lean (partial-domain: correct only when length=1, else none): EXIT=1 FAILS.
- atk_7.lean (control-flow-effect: fold over text.reverse): EXIT=1 FAILS.
All five wrong impls fail with `unsolved goals` on the `out = parseDuration text` goal — the prover cannot equate a divergent impl to the pinned model. Correct fail-closed behavior.

PREPATCH: shipped Solution_prepatch.lean (=atk_5 shape) copied to prepatch.lean -> EXIT=1 (unsolved goals). Prepatch bug reproduced: fails verify against the frozen spec exactly on rows where the sign must scale later groups (-15:30 etc.) and inner '-' must be rejected (-01:-01).

MANDATORY RESOLVE STEP: both verifying attacks (atk_1, atk_2) compute exactly `parseDuration text`; their faithful refined patch is therefore the gold hunk (identical for both). Materialized to faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-10999', patch, run_id='sbu-audit-eq-10999-faithful')` -> RESOLVED=True, completed=True, attempts=1, flaky=False, note='resolved'. So every verifying wrong-impl's faithful patch RESOLVES. No verify->!resolve witness found.

MODEL<->PATCH CORRESPONDENCE (the deep-model A/I leg): transliterated shadow_parse (= parseDuration deep model) compared against the REAL post-patch django.utils.dateparse.parse_duration (worktree has patch.diff applied) via mapping.md bijection: 0 disagreements over exhaustive {0-9,:,-} length<=6 (3,257,436 inputs) + 200k seeded fuzz (len<=10). All 8 F2P rows match: -15:30, -1:15:30, -00:01:01, -01:01 (all folded base-sixty with whole-magnitude sign), -01:-01 -> None; and the off-domain rows -4 15:30/-172800/-30.1 match end-to-end on the real callee (validated by G-RESOLVE, out of the Lean-modeled domain by contract). Model is a faithful I-transliteration of the gold's post-patch behavior.

REFINEMENT.MD AUDIT: every leg is R or I; NO A-legs. meta.json corroborates: axioms=[], additional_change_sites=[], deep_model_references=[]. A1/A2 = R (str<->List Char; honest machine-checked domain restriction via both `require`s). A3/A4 = I (the single changed op — standard_duration_re named-group assignment + `days + sign*timedelta` — modeled deeply/concretely by step/decode/parseDuration, refuted against the PATCHED callee by G-CONF with apply_gold=True, not axiomatized against the buggy base callee per SPEC_GUIDE §0 dir 7). No kind-3 (inexpressible-changed-op) steps; the discriminating whole-magnitude-sign semantics lives concretely in decode's `sign*(acc*60+cur)` and step's first-position-only `-` rule. No axiom_check.py (G-AX correctly skips: no unchanged-callee A-reference).

CONCLUSION: The frozen spec is a tight functional pin whose model equals the gold-patched parse_duration exhaustively on the modeled domain and on every F2P row; verifying impls all refine to the resolving gold patch; divergent impls fail-closed at verify. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The carrier of a single left-to-right scan over a colon-separated,
   sign-prefixed numeric time string.

   * `sign`   : the magnitude's overall sign (1, or -1 once a leading '-' is read);
   * `acc`    : the value of the already-closed groups, folded base-sixty;
   * `cur`    : the value of the group currently being read (base ten);
   * `groups` : how many groups have been opened (starts at 1);
   * `curlen` : how many digits the current group has so far;
   * `valid`  : whether the prefix read so far is still well-formed;
   * `seen`   : whether any character has been consumed (a '-' is only a sign
                in the very first position). -/
structure PS where
  sign   : Int
  acc    : Int
  cur    : Int
  groups : Nat
  curlen : Nat
  valid  : Bool
  seen   : Bool
deriving Inhabited

/- The scan before any character is consumed: positive, empty, well-formed. -/
def initPS : PS := ⟨1, 0, 0, 1, 0, true, false⟩

/- ASCII decimal-digit test and value, in terms of code points. -/
def isDigit (c : Char) : Bool := '0'.toNat ≤ c.toNat && c.toNat ≤ '9'.toNat
def digitVal (c : Char) : Int := (c.toNat : Int) - ('0'.toNat : Int)

/- One step of the scan. A '-' is meaningful only as the very first character,
   where it makes the whole magnitude negative; encountered anywhere else it
   makes the input ill-formed. A ':' closes the current group (folding it into
   `acc` base-sixty) provided the group is non-empty and at most three groups
   total are produced. A decimal digit extends the current group base-ten. Any
   other character is ill-formed. -/
def step (st : PS) (c : Char) : PS :=
  if st.valid = false then st
  else if c = '-' then
    if st.seen then { st with valid := false, seen := true }
    else { st with sign := -1, seen := true }
  else if c = ':' then
    if st.curlen = 0 then { st with valid := false, seen := true }
    else if st.groups = 3 then { st with valid := false, seen := true }
    else { st with acc := st.acc * 60 + st.cur, cur := 0,
                   groups := st.groups + 1, curlen := 0, seen := true }
  else if isDigit c then
    { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }
  else { st with valid := false, seen := true }

/- Read off the total number of seconds from a finished scan: a well-formed,
   non-empty-final-group scan yields the signed base-sixty value of all groups;
   anything else yields no value. The overall sign multiplies the entire
   magnitude (every group), so the result of e.g. a two-group "a:b" with a
   leading minus is -(a*60 + b). -/
def decode (st : PS) : Option Int :=
  if st.valid = false then none
  else if st.curlen = 0 then none
  else some (st.sign * (st.acc * 60 + st.cur))

/- The whole-string parse: fold `step` over the characters left to right, then
   `decode` the final scan. `none` means the string is not a well-formed
   sign-and-colon time component. -/
def parseDuration (text : List Char) : Option Int :=
  decode (text.foldl step initPS)
-- pure-end

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element. This is the single fact the loop body
   leaves for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method parseDurationSeconds (text : List Char) return (out : Option Int)
  require text ≠ []
  require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'
  ensures out = parseDuration text
  do
    -- impl-start
    let mut st := initPS
    let mut i := 0
    while i < text.length
      -- invariants-start
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant st = (text.take i).foldl step initPS
      done_with i = text.length
      -- invariants-end
    do
      st := step st text[i]!
      i := i + 1
    return decode st
    -- impl-end

prove_correct parseDurationSeconds by
  loom_solve
  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
  · simp_all [parseDuration, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: parseDurationSeconds is FULLY FUNCTIONAL-PINNED by `ensures out = parseDuration text` over the require-domain (text != [] and all chars in {0-9,:,-}). Any impl that verifies MUST compute exactly `parseDuration text` on-domain, so all verifying impls are behaviorally identical. The only real falsification surface is (a) model->gold correspondence and (b) the off-domain F2P rows — audited below.

SAME-SPEC: all 7 attacks + pos.lean confirmed same_spec=True (impl/proof regions elided; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (scripts/lean_verify.sh <f>):
- pos.lean (correct impl, forward fold): EXIT=0 VERIFIES (positive control).
- atk_1.lean (ungrounded-oracle ECHO: `return parseDuration text`): EXIT=0 VERIFIES.
- atk_2.lean (alt control-flow: `return decode (text.foldl step initPS)`, proof closed with `simp [parseDuration]`): EXIT=0 VERIFIES.
- atk_3.lean (boundary off-by-one: loop `i+1 < length`, drops last char): EXIT=1 FAILS (unsolved goals — diverges from parseDuration).
- atk_4.lean (constant `return none`): EXIT=1 FAILS.
- atk_5.lean (PREPATCH sign bug: sign folded into first group only, reset at ':'): EXIT=1 FAILS.
- atk_6.lean (partial-domain: correct only when length=1, else none): EXIT=1 FAILS.
- atk_7.lean (control-flow-effect: fold over text.reverse): EXIT=1 FAILS.
All five wrong impls fail with `unsolved goals` on the `out = parseDuration text` goal — the prover cannot equate a divergent impl to the pinned model. Correct fail-closed behavior.

PREPATCH: shipped Solution_prepatch.lean (=atk_5 shape) copied to prepatch.lean -> EXIT=1 (unsolved goals). Prepatch bug reproduced: fails verify against the frozen spec exactly on rows where the sign must scale later groups (-15:30 etc.) and inner '-' must be rejected (-01:-01).

MANDATORY RESOLVE STEP: both verifying attacks (atk_1, atk_2) compute exactly `parseDuration text`; their faithful refined patch is therefore the gold hunk (identical for both). Materialized to faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-10999', patch, run_id='sbu-audit-eq-10999-faithful')` -> RESOLVED=True, completed=True, attempts=1, flaky=False, note='resolved'. So every verifying wrong-impl's faithful patch RESOLVES. No verify->!resolve witness found.

MODEL<->PATCH CORRESPONDENCE (the deep-model A/I leg): transliterated shadow_parse (= parseDuration deep model) compared against the REAL post-patch django.utils.dateparse.parse_duration (worktree has patch.diff applied) via mapping.md bijection: 0 disagreements over exhaustive {0-9,:,-} length<=6 (3,257,436 inputs) + 200k seeded fuzz (len<=10). All 8 F2P rows match: -15:30, -1:15:30, -00:01:01, -01:01 (all folded base-sixty with whole-magnitude sign), -01:-01 -> None; and the off-domain rows -4 15:30/-172800/-30.1 match end-to-end on the real callee (validated by G-RESOLVE, out of the Lean-modeled domain by contract). Model is a faithful I-transliteration of the gold's post-patch behavior.

REFINEMENT.MD AUDIT: every leg is R or I; NO A-legs. meta.json corroborates: axioms=[], additional_change_sites=[], deep_model_references=[]. A1/A2 = R (str<->List Char; honest machine-checked domain restriction via both `require`s). A3/A4 = I (the single changed op — standard_duration_re named-group assignment + `days + sign*timedelta` — modeled deeply/concretely by step/decode/parseDuration, refuted against the PATCHED callee by G-CONF with apply_gold=True, not axiomatized against the buggy base callee per SPEC_GUIDE §0 dir 7). No kind-3 (inexpressible-changed-op) steps; the discriminating whole-magnitude-sign semantics lives concretely in decode's `sign*(acc*60+cur)` and step's first-position-only `-` rule. No axiom_check.py (G-AX correctly skips: no unchanged-callee A-reference).

CONCLUSION: The frozen spec is a tight functional pin whose model equals the gold-patched parse_duration exhaustively on the modeled domain and on every F2P row; verifying impls all refine to the resolving gold patch; divergent impls fail-closed at verify. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified rigorously: (1) Solution.lean VERIFIES under lean_verify.sh (exit 0, 400s cap, FSx HOME). (2) The spec region is a self-contained left-to-right scan (step/decode/parseDuration): single leading '-' scales the WHOLE base-sixty magnitude, '-' invalid elsewhere (seen guard), <=3 non-empty colon groups. This exactly encodes the post-patch standard_duration_re (single (?P<sign>-?) at front, components lose -?) and parse_duration's `sign * timedelta(...)`. (3) conformance_check.py's shadow_parse is a faithful 1:1 transliteration of the Lean step/decode (checked branch-by-branch). DIFFERENTIAL against the REAL patched callee (confirmed patched: sign group present, components have no -?): 0 disagreements over 3,457,453 exhaustive inputs (length<=6 over {0-9,:,-}) PLUS 0 disagreements over ~2.94M random inputs up to length 20 (62,925 overflow-skips). All discriminating F2P rows (-15:30, -1:15:30, -00:01:01, -01:01, -01:-01) match. (5) The ONLY divergence is the overflow class, which the preconditions (text != [], alphabet) do not bound. This is the accepted unbounded-Int <-> bounded-timedelta abstraction documented in mapping.md §2 and handled by _OUT_OF_DOMAIN. It is NOT a spec-too-strong defect w.r.t. the FIX: pre-patch and post-patch parse_duration behave identically on these overflow inputs (both raise), so the model does not misrepresent the patched behavior on any input distinguishing the fix, and no F2P test exercises it. VERDICT: the spec is a faithful (in fact tight) model of the real post-patch callee on the modeled domain; no spec-drift/too-strong defect found. The overflow gap is a benign, documented representability boundary, not a faithfulness break.

Counterexample / evidence:

```
shadow/model = some 99999999999999999 ; real callee = OverflowError (no representable timedelta). Also '100000000000000000000', '86400000000000000', etc. All lie in the G-CONF `_OUT_OF_DOMAIN` skip set (timedelta overflow), and none are F2P/discriminating rows.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted relaxed-leakage disposition rather than rubber-stamping. (1) Spec region frozen: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True; spec_view elides impl/proof, exposing only axioms/pure/pre/post regions. (2) Baseline = problem_statement only (hints_text excluded). The PS shows the current standard_duration_re and PROPOSES a specific fix r'((?:(?P<hours>-?\d+):)(?=-?\d+:-?\d+))?' that KEEPS the per-component -? — under which -15:30 = min(-15)/sec(+30) and -01:-01 is ACCEPTED, i.e. the OPPOSITE of gold on both discriminating facets. PS has 0 hits for {entire, whole, magnitude, negate the, leading minus, after a colon, 61, overall sign}. The whole-magnitude-sign (a) and inner-minus-invalid (b) decisions live ONLY in hints_text (maintainer comments). (3) The spec-view leak is exactly the dispositioned facets: decode's `some (st.sign * (st.acc*60 + st.cur))` + docstring 'overall sign multiplies the entire magnitude', and step's `seen` guard rejecting a non-leading '-'. Leak is SEMANTIC, not a lexical gold-token echo — no (?P<sign>-?) / regex group name / diff-line appears; mechanical G-LEAK screen clean. (4) Unavoidability genuine: any spec weak enough to hide (a)+(b) admits the PS-faithful per-component skeleton = Solution_prepatch.lean, which G-DIFF requires to FAIL (status pass) and which fails hidden F2P (-15:30,-1:15:30,-00:01:01,-01:01,-01:-01). (5) Disposition intact: RELAXED_LEAKAGE.md present, meta.relaxed_leakage=true, G-LEAK=relaxed; core gates sound (G-VERIFY/G-DIFF/G-CONF 0 disagreements/G-RESOLVE all pass; G-PANEL-1 pass, 7 attacks + positive control). Structural facets (colon-separated ≤3 groups) are derivable from the PS-shown regex; no concrete F2P value strings appear in the spec view. Found NO new leaking line beyond the dispositioned sign-semantics facet and no break in the disposition. G-EQ INCONCLUSIVE (2 attacks) is a protocol/contention artifact, not a demonstrated spec weakness, and is out of panel-3 scope. Per RELAXED_LEAKAGE.md / gates/_audit.py panel-3 recording convention, the honest recording for a properly dispositioned relaxed-leakage bundle is NO-LEAKAGE (pass) + re-confirmation note.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
