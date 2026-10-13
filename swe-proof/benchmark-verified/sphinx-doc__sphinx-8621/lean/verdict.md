# P2 adversarial audit — sphinx-doc__sphinx-8621

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,30 +137,38 @@
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
   Id.run do
-    let mut st : TokState := initState
+    let mut out : List (List Char) := []
+    let mut cur : List Char := []
+    let mut pendWs : List Char := []
+    let mut inWs : Bool := false
     for c in text do
-      st := step st c
-    return finalize st
+      if inWs && isWsChar c then
+        pendWs := pendWs ++ [c]
+      else
+        if inWs then
+          out := out ++ [cur] ++ [pendWs]
+          cur := []
+          pendWs := []
+          inWs := false
+        if isSepChar c then
+          out := out ++ [cur] ++ [[c]]
+          cur := []
+        else if isWsChar c then
+          pendWs := [c]
+          inWs := true
+        else
+          cur := cur ++ [c]
+    if inWs then
+      out := out ++ [cur] ++ [pendWs]
+      cur := []
+    return out ++ [cur]
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,31 +136,14 @@
 
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
-  Id.run do
-    let mut st : TokState := initState
-    for c in text do
-      st := step st c
-    return finalize st
+  [text]
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,31 +136,14 @@
 
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
-  Id.run do
-    let mut st : TokState := initState
-    for c in text do
-      st := step st c
-    return finalize st
+  (text.foldl step initState).out
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,31 +136,14 @@
 
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
-  Id.run do
-    let mut st : TokState := initState
-    for c in text do
-      st := step st c
-    return finalize st
+  specSplit text ++ [[]]
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,31 +136,14 @@
 
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
-  Id.run do
-    let mut st : TokState := initState
-    for c in text do
-      st := step st c
-    return finalize st
+  if text.length ≤ 1 then specSplit text else (specSplit text).reverse
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,30 +137,37 @@
 -- impl-start
 def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
   Id.run do
-    let mut st : TokState := initState
+    let mut out : List (List Char) := []
+    let mut cur : List Char := []
+    let mut started : Bool := false
+    let mut pend : Option Char := none
     for c in text do
-      st := step st c
-    return finalize st
+      match pend with
+      | some sc =>
+          out := out ++ [cur] ++ [[sc]]
+          cur := []
+          pend := none
+          cur := cur ++ [c]
+          started := true
+      | none =>
+          if !started then
+            cur := cur ++ [c]
+            started := true
+          else if isSepChar c then
+            pend := some c
+          else
+            cur := cur ++ [c]
+    match pend with
+    | some sc => cur := cur ++ [sc]
+    | none => pure ()
+    return out ++ [cur]
 -- impl-end
 
 -- proof-start
-/-- The desugared `for c in text do st := step st c` loop, generalized over the
-accumulator, equals the declarative left fold of `step`. -/
-theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
-    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
-      = List.foldl step init text := by
-  induction text generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, List.foldl_cons, bind]
-      exact ih (step init a)
-
 theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
     problem_spec_tokenizeKeystrokes text
       (implementation_tokenizeKeystrokes text) := by
   intro text
-  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
-  simp only [Id.run, bind, pure]
-  congr 1
-  exact forIn_step_eq_foldl text initState
+  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a keystroke specification into its keystroke tokens and the separators
that sit between them.

A keystroke specification is a sequence of characters. Three characters act as
compound-key separators — `-`, `+`, `^` — and so does any run of horizontal
whitespace. The result is the alternating list

    key, separator, key, separator, …, key

(odd-indexed entries are separators, even-indexed entries are keystroke tokens,
any of which may be empty).

The governing behavior pinned below: a separator character only separates when it
has a character on BOTH sides. A separator that begins the whole specification, or
ends it, is not a boundary — it stays part of the adjacent keystroke text. A run
of whitespace is taken maximally, but a whitespace run that reaches the end of the
specification keeps its final character attached to the trailing keystroke (the
boundary still needs a character after it). Hence a standalone `-`, `+` or `^`
yields a single keystroke token equal to the whole input, never a separator framed
by two empty tokens.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed here. The modeled behavior is the pure
-- tokenization of the specification text; the surrounding node bookkeeping that
-- consumes the token list is a deterministic, unchanged function of these tokens
-- and is not part of the modeled behavior, so no `opaque`/`axiom` callee contract
-- is needed. The proof agent may add `_prop` axioms only if a proof obligation
-- requires one.
-- axioms-end

-- pure-start
/-- A character that, on its own, can act as a compound-key separator. -/
def isSepChar (c : Char) : Bool :=
  c == '-' || c == '+' || c == '^'

/-- A horizontal-whitespace character (the whitespace that `\s` matches other
than a line break). -/
def isWsChar (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\r' || c == Char.ofNat 11 || c == Char.ofNat 12

/-- A separator candidate that has been seen but not yet committed: we only know
it is a real boundary once a further character arrives after it. `pendNone` = no
candidate; `pendSep c` = a single separator character `c`; `pendWs run` = a
whitespace run accumulated so far. -/
inductive Pend where
  | pendNone
  | pendSep (c : Char)
  | pendWs (run : List Char)
deriving DecidableEq, Repr

/-- The running state of the tokenizer.

* `out`  — the keystroke/separator tokens committed so far, in order;
* `cur`  — the keystroke token currently being accumulated;
* `pend` — a separator candidate awaiting confirmation (see `Pend`);
* `started` — whether at least one character has been consumed (a separator at
  the very front cannot be a boundary). -/
structure TokState where
  out : List (List Char)
  cur : List Char
  pend : Pend
  started : Bool
deriving Repr

/-- The initial tokenizer state. -/
def initState : TokState :=
  { out := [], cur := [], pend := Pend.pendNone, started := false }

/-- Consume one character when there is NO pending separator candidate. -/
def stepNoPend (st : TokState) (c : Char) : TokState :=
  if !st.started then
    { st with cur := st.cur ++ [c], started := true }
  else if isSepChar c then
    { st with pend := Pend.pendSep c }
  else if isWsChar c then
    { st with pend := Pend.pendWs [c] }
  else
    { st with cur := st.cur ++ [c] }

/-- Consume one character of the specification, resolving any pending separator
candidate first: since a character is arriving, a pending candidate now has a
character on both sides and is committed as a real boundary (a whitespace run
keeps growing while whitespace continues). -/
def step (st : TokState) (c : Char) : TokState :=
  match st.pend with
  | Pend.pendNone => stepNoPend st c
  | Pend.pendSep sc =>
      let st1 : TokState :=
        { st with out := st.out ++ [st.cur] ++ [[sc]], cur := [], pend := Pend.pendNone }
      stepNoPend st1 c
  | Pend.pendWs run =>
      if isWsChar c then
        { st with pend := Pend.pendWs (run ++ [c]) }
      else
        let st1 : TokState :=
          { st with out := st.out ++ [st.cur] ++ [run], cur := [], pend := Pend.pendNone }
        stepNoPend st1 c

/-- Finish tokenizing: a separator candidate that never got a following character
is at the end of the specification, so it is NOT a boundary. A single trailing
separator (or single trailing whitespace) is folded back into the current
keystroke; a multi-character trailing whitespace run contributes all but its last
character as the final separator, with its last character beginning the trailing
keystroke. -/
def finalize (st : TokState) : List (List Char) :=
  match st.pend with
  | Pend.pendNone => st.out ++ [st.cur]
  | Pend.pendSep sc => st.out ++ [st.cur ++ [sc]]
  | Pend.pendWs run =>
      if run.length ≥ 2 then
        st.out ++ [st.cur] ++ [run.dropLast] ++ [[run.getLast!]]
      else
        st.out ++ [st.cur ++ run]

/-- The declarative tokenization: fold the per-character transition across the
whole specification, then finalize. -/
def specSplit (text : List Char) : List (List Char) :=
  finalize (text.foldl step initState)
-- pure-end

-- post-conditions-start
/-- The produced token list is exactly the declarative tokenization of the
specification text: it equals `specSplit text` for the given input. This pins
every token — its content and its position — to the input, so a standalone
separator yields a single token equal to the whole input and an interior
separator (one with a keystroke on both sides) produces a genuine boundary. -/
def problem_spec_tokenizeKeystrokes
    (text : List Char) (result : List (List Char)) : Prop :=
  result = specSplit text
-- post-conditions-end

-- impl-start
def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
  Id.run do
    let mut st : TokState := initState
    for c in text do
      st := step st c
    return finalize st
-- impl-end

-- proof-start
/-- The desugared `for c in text do st := step st c` loop, generalized over the
accumulator, equals the declarative left fold of `step`. -/
theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
      = List.foldl step init text := by
  induction text generalizing init with
  | nil => rfl
  | cons a as ih =>
      simp only [List.forIn_cons, List.foldl_cons, bind]
      exact ih (step init a)

theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
    problem_spec_tokenizeKeystrokes text
      (implementation_tokenizeKeystrokes text) := by
  intro text
  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
  simp only [Id.run, bind, pure]
  congr 1
  exact forIn_step_eq_foldl text initState
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: strict equality-to-fixed-model. problem_spec_tokenizeKeystrokes text result := (result = specSplit text); correct_tokenizeKeystrokes proves forall text, implementation_tokenizeKeystrokes text = specSplit text. specSplit lives in the byte-identical frozen pure region, so ANY verifying impl must be extensionally equal to specSplit on all inputs -- the tightest possible spec. No same-spec-but-wrong impl can verify.

SAME-SPEC CONFIRMED: swebench_unified.markers.same_spec(Solution, atk_N, lean.language)=True for all 6 attacks (only impl/proof regions edited; axioms/pure/pre/post byte-identical).

### ATTACKS (all run via scripts/lean_verify.sh <file>, launched concurrently <=4 at a time):
- atk_1 PREPATCH BUG (unconditional split; body copied verbatim from Solution_prepatch.lean impl region): exit=1, proof does NOT close. Reproduces the exact prepatch bug ('-' -> ['','-',''], 'Alt+^' -> ['Alt','+','','^','']). prepatch_reproduced=true.
- atk_2 UNGROUNDED ORACLE ECHO ([text]): exit=1. Goal: [text] = specSplit text.
- atk_3 CONTROL-FLOW-EFFECT (drop final cur; return (foldl step initState).out): exit=1.
- atk_4 BOUNDARY (specSplit text ++ [[]], spurious trailing empty token): exit=1.
- atk_5 PARTIAL-DOMAIN (correct on len<=1, reversed otherwise): exit=1.
- atk_6 WHITESPACE-BLIND (interior separators only, whitespace never splits): exit=1.
NONE of the 6 verifies => none has a closing clean-axiom proof => no faithful patch to materialize/resolve (patches={}). verify<=>correct is NOT falsifiable here.

POSITIVE CONTROL: pos_control.lean = unedited Solution.lean, exit=0 (verifies, no sorry). #print axioms correct_tokenizeKeystrokes => [propext, Quot.sound] (clean; no sorryAx/Classical.choice/native_decide).

MODEL<->PATCH CORRESPONDENCE (the only A-reference: re.Pattern.split, modeled deeply by step/finalize, NOT axiomatized -> G-AX skip is correct, axioms=[]). I INDEPENDENTLY re-derived specSplit directly from the Lean step/finalize definitions (NOT copied from conformance_check.py's shadow) and diffed it against the REAL post-patch re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split: 437,294 inputs (all F2P/edge shapes incl 'Alt+^','-'; exhaustive alphabet {a,b,-,+,^,space,tab} len 0..6; 300k biased fuzz seed 8621) -> 0 disagreements. F2P inputs (:kbd:`Alt+^`, :kbd:`-`) and all 31 P2P are newline-free, i.e. squarely inside the documented modeled domain (mapping.md newline note). The domain restriction is on the conformance oracle only, not a precondition weakening (impl is definitionally specSplit, correct holds for all List Char).

REFINEMENT.MD AUDIT: 8 legs, all tag R (type refinement, str<->List Char / list[str]<->List(List Char) bijection). axioms region empty; re.Pattern.split is an A-reference modeled deeply and G-CONF-validated, consistent with meta.json G-AX=skip/pass, G-CONF=pass, G-DIFF=pass (prepatch fails). NO kind-3 (changed-inexpressible) leg -- the changed op (split pattern) is modeled deeply and its correspondence to the real callee holds (verified above). No unchanged callee consumed as axiom.

VERDICT: SOUND. >=5 distinct same-spec wrong impls attacked, prepatch reproduced, none verifies, so there is nothing to resolve-break; positive control verifies with clean axioms; model faithfully mirrors the real post-patch callee on the modeled domain covering all harness test inputs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a keystroke specification into its keystroke tokens and the separators
that sit between them.

A keystroke specification is a sequence of characters. Three characters act as
compound-key separators — `-`, `+`, `^` — and so does any run of horizontal
whitespace. The result is the alternating list

    key, separator, key, separator, …, key

(odd-indexed entries are separators, even-indexed entries are keystroke tokens,
any of which may be empty).

The governing behavior pinned below: a separator character only separates when it
has a character on BOTH sides. A separator that begins the whole specification, or
ends it, is not a boundary — it stays part of the adjacent keystroke text. A run
of whitespace is taken maximally, but a whitespace run that reaches the end of the
specification keeps its final character attached to the trailing keystroke (the
boundary still needs a character after it). Hence a standalone `-`, `+` or `^`
yields a single keystroke token equal to the whole input, never a separator framed
by two empty tokens.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed here. The modeled behavior is the pure
-- tokenization of the specification text; the surrounding node bookkeeping that
-- consumes the token list is a deterministic, unchanged function of these tokens
-- and is not part of the modeled behavior, so no `opaque`/`axiom` callee contract
-- is needed. The proof agent may add `_prop` axioms only if a proof obligation
-- requires one.
-- axioms-end

-- pure-start
/-- A character that, on its own, can act as a compound-key separator. -/
def isSepChar (c : Char) : Bool :=
  c == '-' || c == '+' || c == '^'

/-- A horizontal-whitespace character (the whitespace that `\s` matches other
than a line break). -/
def isWsChar (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\r' || c == Char.ofNat 11 || c == Char.ofNat 12

/-- A separator candidate that has been seen but not yet committed: we only know
it is a real boundary once a further character arrives after it. `pendNone` = no
candidate; `pendSep c` = a single separator character `c`; `pendWs run` = a
whitespace run accumulated so far. -/
inductive Pend where
  | pendNone
  | pendSep (c : Char)
  | pendWs (run : List Char)
deriving DecidableEq, Repr

/-- The running state of the tokenizer.

* `out`  — the keystroke/separator tokens committed so far, in order;
* `cur`  — the keystroke token currently being accumulated;
* `pend` — a separator candidate awaiting confirmation (see `Pend`);
* `started` — whether at least one character has been consumed (a separator at
  the very front cannot be a boundary). -/
structure TokState where
  out : List (List Char)
  cur : List Char
  pend : Pend
  started : Bool
deriving Repr

/-- The initial tokenizer state. -/
def initState : TokState :=
  { out := [], cur := [], pend := Pend.pendNone, started := false }

/-- Consume one character when there is NO pending separator candidate. -/
def stepNoPend (st : TokState) (c : Char) : TokState :=
  if !st.started then
    { st with cur := st.cur ++ [c], started := true }
  else if isSepChar c then
    { st with pend := Pend.pendSep c }
  else if isWsChar c then
    { st with pend := Pend.pendWs [c] }
  else
    { st with cur := st.cur ++ [c] }

/-- Consume one character of the specification, resolving any pending separator
candidate first: since a character is arriving, a pending candidate now has a
character on both sides and is committed as a real boundary (a whitespace run
keeps growing while whitespace continues). -/
def step (st : TokState) (c : Char) : TokState :=
  match st.pend with
  | Pend.pendNone => stepNoPend st c
  | Pend.pendSep sc =>
      let st1 : TokState :=
        { st with out := st.out ++ [st.cur] ++ [[sc]], cur := [], pend := Pend.pendNone }
      stepNoPend st1 c
  | Pend.pendWs run =>
      if isWsChar c then
        { st with pend := Pend.pendWs (run ++ [c]) }
      else
        let st1 : TokState :=
          { st with out := st.out ++ [st.cur] ++ [run], cur := [], pend := Pend.pendNone }
        stepNoPend st1 c

/-- Finish tokenizing: a separator candidate that never got a following character
is at the end of the specification, so it is NOT a boundary. A single trailing
separator (or single trailing whitespace) is folded back into the current
keystroke; a multi-character trailing whitespace run contributes all but its last
character as the final separator, with its last character beginning the trailing
keystroke. -/
def finalize (st : TokState) : List (List Char) :=
  match st.pend with
  | Pend.pendNone => st.out ++ [st.cur]
  | Pend.pendSep sc => st.out ++ [st.cur ++ [sc]]
  | Pend.pendWs run =>
      if run.length ≥ 2 then
        st.out ++ [st.cur] ++ [run.dropLast] ++ [[run.getLast!]]
      else
        st.out ++ [st.cur ++ run]

/-- The declarative tokenization: fold the per-character transition across the
whole specification, then finalize. -/
def specSplit (text : List Char) : List (List Char) :=
  finalize (text.foldl step initState)
-- pure-end

-- post-conditions-start
/-- The produced token list is exactly the declarative tokenization of the
specification text: it equals `specSplit text` for the given input. This pins
every token — its content and its position — to the input, so a standalone
separator yields a single token equal to the whole input and an interior
separator (one with a keystroke on both sides) produces a genuine boundary. -/
def problem_spec_tokenizeKeystrokes
    (text : List Char) (result : List (List Char)) : Prop :=
  result = specSplit text
-- post-conditions-end

-- impl-start
def implementation_tokenizeKeystrokes (text : List Char) : List (List Char) :=
  Id.run do
    let mut st : TokState := initState
    for c in text do
      st := step st c
    return finalize st
-- impl-end

-- proof-start
/-- The desugared `for c in text do st := step st c` loop, generalized over the
accumulator, equals the declarative left fold of `step`. -/
theorem forIn_step_eq_foldl (text : List Char) (init : TokState) :
    (forIn text init (fun c r => ForInStep.yield (step r c)) : Id TokState)
      = List.foldl step init text := by
  induction text generalizing init with
  | nil => rfl
  | cons a as ih =>
      simp only [List.forIn_cons, List.foldl_cons, bind]
      exact ih (step init a)

theorem correct_tokenizeKeystrokes : ∀ (text : List Char),
    problem_spec_tokenizeKeystrokes text
      (implementation_tokenizeKeystrokes text) := by
  intro text
  unfold problem_spec_tokenizeKeystrokes implementation_tokenizeKeystrokes specSplit
  simp only [Id.run, bind, pure]
  congr 1
  exact forIn_step_eq_foldl text initState
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: strict equality-to-fixed-model. problem_spec_tokenizeKeystrokes text result := (result = specSplit text); correct_tokenizeKeystrokes proves forall text, implementation_tokenizeKeystrokes text = specSplit text. specSplit lives in the byte-identical frozen pure region, so ANY verifying impl must be extensionally equal to specSplit on all inputs -- the tightest possible spec. No same-spec-but-wrong impl can verify.

SAME-SPEC CONFIRMED: swebench_unified.markers.same_spec(Solution, atk_N, lean.language)=True for all 6 attacks (only impl/proof regions edited; axioms/pure/pre/post byte-identical).

### ATTACKS (all run via scripts/lean_verify.sh <file>, launched concurrently <=4 at a time):
- atk_1 PREPATCH BUG (unconditional split; body copied verbatim from Solution_prepatch.lean impl region): exit=1, proof does NOT close. Reproduces the exact prepatch bug ('-' -> ['','-',''], 'Alt+^' -> ['Alt','+','','^','']). prepatch_reproduced=true.
- atk_2 UNGROUNDED ORACLE ECHO ([text]): exit=1. Goal: [text] = specSplit text.
- atk_3 CONTROL-FLOW-EFFECT (drop final cur; return (foldl step initState).out): exit=1.
- atk_4 BOUNDARY (specSplit text ++ [[]], spurious trailing empty token): exit=1.
- atk_5 PARTIAL-DOMAIN (correct on len<=1, reversed otherwise): exit=1.
- atk_6 WHITESPACE-BLIND (interior separators only, whitespace never splits): exit=1.
NONE of the 6 verifies => none has a closing clean-axiom proof => no faithful patch to materialize/resolve (patches={}). verify<=>correct is NOT falsifiable here.

POSITIVE CONTROL: pos_control.lean = unedited Solution.lean, exit=0 (verifies, no sorry). #print axioms correct_tokenizeKeystrokes => [propext, Quot.sound] (clean; no sorryAx/Classical.choice/native_decide).

MODEL<->PATCH CORRESPONDENCE (the only A-reference: re.Pattern.split, modeled deeply by step/finalize, NOT axiomatized -> G-AX skip is correct, axioms=[]). I INDEPENDENTLY re-derived specSplit directly from the Lean step/finalize definitions (NOT copied from conformance_check.py's shadow) and diffed it against the REAL post-patch re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split: 437,294 inputs (all F2P/edge shapes incl 'Alt+^','-'; exhaustive alphabet {a,b,-,+,^,space,tab} len 0..6; 300k biased fuzz seed 8621) -> 0 disagreements. F2P inputs (:kbd:`Alt+^`, :kbd:`-`) and all 31 P2P are newline-free, i.e. squarely inside the documented modeled domain (mapping.md newline note). The domain restriction is on the conformance oracle only, not a precondition weakening (impl is definitionally specSplit, correct holds for all List Char).

REFINEMENT.MD AUDIT: 8 legs, all tag R (type refinement, str<->List Char / list[str]<->List(List Char) bijection). axioms region empty; re.Pattern.split is an A-reference modeled deeply and G-CONF-validated, consistent with meta.json G-AX=skip/pass, G-CONF=pass, G-DIFF=pass (prepatch fails). NO kind-3 (changed-inexpressible) leg -- the changed op (split pattern) is modeled deeply and its correspondence to the real callee holds (verified above). No unchanged callee consumed as axiom.

VERDICT: SOUND. >=5 distinct same-spec wrong impls attacked, prepatch reproduced, none verifies, so there is nothing to resolve-break; positive control verifies with clean axioms; model faithfully mirrors the real post-patch callee on the modeled domain covering all harness test inputs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True; spec_view confirms the frozen spec region (isSepChar, isWsChar, Pend, TokState, step/finalize, specSplit, problem_spec) is byte-identical.
2. Solution.lean compiles clean via lake env lean (exit 0); #print axioms correct_tokenizeKeystrokes = [propext, Quot.sound] only — NO sorryAx, proof is genuine. implementation_tokenizeKeystrokes is definitionally specSplit (forIn=foldl lemma), so correct_... holds for ALL inputs.
3. Faithfulness of specSplit vs the REAL changed callee (re.split with post-patch pattern r'(?<=.)(-|\+|\^|\s+)(?=.)'): evaluated specSplit directly in Lean on Alt+^, '-', 'a - b', 'a  b', 'Shift-+', '', 'a -- b', 'a   b' — every result matches both the Python shadow AND real re.split (e.g. Alt+^ -> [Alt,+,^]; '-' -> ['-']; standalone sep never framed by empties; trailing 2-char ws run splits as run[:-1] sep + last char begins trailing token).
4. Independent adversarial fuzz: exhaustive over {a,-,+,^,space,\t} up to length 8 → ZERO divergence in the modeled domain; conformance_check.py passes 337,294 cases (edge + exhaustive<=6 + 200k random) against real re.split, status=pass.
5. Only divergences are newline / non-ASCII-whitespace / C0-control inputs, which mapping.md's newline note explicitly excludes with a principled justification grounded in the ACTUAL patch semantics: the post-patch lookaround '.' does not match '\n', and a :kbd: inline literal's astext() is single-line ASCII-whitespace text, so these characters cannot reach the real callee meaningfully. This is a legitimate domain restriction on the conformance oracle, not a spec weakening — the Lean theorem holds for all inputs, and the model is bit-for-bit equal to the real callee on every realistically reachable input. The spec is neither too strong nor drifted: it pins the exact post-patch token list. FAITHFUL.

Counterexample / evidence:

```
text='a \nb': oracle re.split = ['a',' \n','b'], model specSplit = ['a',' ','\nb'] (only reachable outside the modeled domain, which excludes '\n'). No divergence exists on any modeled-domain input.
```

Rigorous checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True; spec_view confirms the frozen spec region (isSepChar, isWsChar, Pend, TokState, step/finalize, specSplit, problem_spec) is byte-identical.
2. Solution.lean compiles clean via lake env lean (exit 0); #print axioms correct_tokenizeKeystrokes = [propext, Quot.sound] only — NO sorryAx, proof is genuine. implementation_tokenizeKeystrokes is definitionally specSplit (forIn=foldl lemma), so correct_... holds for ALL inputs.
3. Faithfulness of specSplit vs the REAL changed callee (re.split with post-patch pattern r'(?<=.)(-|\+|\^|\s+)(?=.)'): evaluated specSplit directly in Lean on Alt+^, '-', 'a - b', 'a  b', 'Shift-+', '', 'a -- b', 'a   b' — every result matches both the Python shadow AND real re.split (e.g. Alt+^ -> [Alt,+,^]; '-' -> ['-']; standalone sep never framed by empties; trailing 2-char ws run splits as run[:-1] sep + last char begins trailing token).
4. Independent adversarial fuzz: exhaustive over {a,-,+,^,space,\t} up to length 8 → ZERO divergence in the modeled domain; conformance_check.py passes 337,294 cases (edge + exhaustive<=6 + 200k random) against real re.split, status=pass.
5. Only divergences are newline / non-ASCII-whitespace / C0-control inputs, which mapping.md's newline note explicitly excludes with a principled justification grounded in the ACTUAL patch semantics: the post-patch lookaround '.' does not match '\n', and a :kbd: inline literal's astext() is single-line ASCII-whitespace text, so these characters cannot reach the real callee meaningfully. This is a legitimate domain restriction on the conformance oracle, not a spec weakening — the Lean theorem holds for all inputs, and the model is bit-for-bit equal to the real callee on every realistically reachable input. The spec is neither too strong nor drifted: it pins the exact post-patch token list. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the consumer spec_view of Solution.lean (auditor artifacts refinement.md/mapping.md/patch.diff are NOT in the consumer view). Verified: (1) leakage.screen() passes with zero hard_failures — no diff markers, no gold-patch line reproduced (gold changed line is the regex `pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')`, absent from the view), no patched file path `sphinx/builders/html/transforms.py`, no spec-view identifier/comment echoing the patched repo symbol `KeyboardTransform`, no narration terms. (2) same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical. (3) Manual token scan: 'transforms.py','KeyboardTransform','re.compile','re.split','lookbehind','lookahead','(?<=','(?=','pattern' all absent from the view. Semantic check: the spec docstring describes the CORRECT behavior (a separator separates only with a char on both sides; standalone -/+/^ stays one keystroke token, never framed by two empty tokens). This is exactly what the PUBLIC problem_statement already states ('For single keystrokes that use -, + or ^, just a single kbd element should be created'; 'differentiate between -, + and ^ characters appearing in separator vs keystroke positions'; the 'two blank keystrokes' framing appears verbatim in the report). Describing required behavior is the spec's legitimate job; the view reveals no detail of the gold EDIT (regex/lookaround/Python symbol/path) beyond the problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
