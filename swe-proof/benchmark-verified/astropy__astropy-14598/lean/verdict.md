# P2 adversarial audit — astropy__astropy-14598

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — spec is a fully-functional postcondition result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s)), pinning output to a single deterministic value. No same-spec wrong impl with a closing clean-axiom proof has a non-resolving faithful patch.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,14 +99,47 @@
 -- post-conditions-end
 
 -- impl-start
+def lookaheadOk (cs : List Char) : Bool :=
+  match cs with
+  | [] => true
+  | c :: _ => c == '/' || c == ' '
+
+def scanTokenLoose : List Char → List Char → Option (List Char)
+  | _acc, [] => none
+  | acc, c :: rest =>
+      if c == quote && acc ≠ [] && lookaheadOk rest then
+        some acc
+      else if isPrintable c then
+        scanTokenLoose (acc ++ [c]) rest
+      else
+        none
+
+def matchTokenLoose (vc : List Char) : List Char :=
+  match vc with
+  | q :: body =>
+      if q == quote then
+        match scanTokenLoose [] body with
+        | some s => s
+        | none => []
+      else
+        []
+  | [] => []
+
+def collapseDoubledQuote : List Char → List Char
+  | [] => []
+  | [c] => [c]
+  | c1 :: c2 :: rest =>
+      if c1 == quote && c2 == quote then
+        quote :: collapseDoubledQuote rest
+      else
+        c1 :: collapseDoubledQuote (c2 :: rest)
+
 def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
-  match matchToken vc with
-  | none => return none
-  | some token =>
-      let mut value := token
-      value := dropTrailingWs value
-      value := dropTrailingAmp value
-      return some value
+  let mut value := matchTokenLoose vc
+  value := dropTrailingWs value
+  value := collapseDoubledQuote value
+  value := dropTrailingAmp value
+  return some value
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -99,14 +99,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
+def implementation_segmentValue (vc : List Char) : Option (List Char) :=
   match matchToken vc with
-  | none => return none
-  | some token =>
-      let mut value := token
-      value := dropTrailingWs value
-      value := dropTrailingAmp value
-      return some value
+  | none => none
+  | some token => some (dropTrailingAmp (dropTrailingWs token))
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,14 +99,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
-  match matchToken vc with
-  | none => return none
-  | some token =>
-      let mut value := token
-      value := dropTrailingWs value
-      value := dropTrailingAmp value
-      return some value
+def implementation_segmentValue (vc : List Char) : Option (List Char) :=
+  match vc with
+  | [] => none
+  | _ =>
+    match matchToken vc with
+    | none => none
+    | some token => some (dropTrailingAmp (dropTrailingWs token))
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,8 +104,8 @@
   | none => return none
   | some token =>
       let mut value := token
+      value := dropTrailingAmp value
       value := dropTrailingWs value
-      value := dropTrailingAmp value
       return some value
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,6 @@
   | some token =>
       let mut value := token
       value := dropTrailingWs value
-      value := dropTrailingAmp value
       return some value
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,6 @@
   | none => return none
   | some token =>
       let mut value := token
-      value := dropTrailingWs value
       value := dropTrailingAmp value
       return some value
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -99,22 +99,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
-  match matchToken vc with
-  | none => return none
-  | some token =>
-      let mut value := token
-      value := dropTrailingWs value
-      value := dropTrailingAmp value
-      return some value
+def implementation_segmentValue (vc : List Char) : Option (List Char) :=
+  (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s))
 -- impl-end
 
 -- proof-start
 theorem correct_segmentValue :
     ∀ vc : List Char, problem_spec_segmentValue vc (implementation_segmentValue vc) := by
   intro vc
-  unfold problem_spec_segmentValue implementation_segmentValue
-  cases matchToken vc with
-  | none => rfl
-  | some token => rfl
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Recovering a quoted text field from a single continuation segment of a long,
space-padded record. Each segment carries one optionally-quoted token possibly
followed by a separator and trailing notes; this returns the token's contributed
text, or signals that the segment is not in the expected quoted shape (so the
caller keeps it verbatim). Doubled quote marks inside the token are part of the
text and are preserved exactly.
-/

-- axioms-start
-- No unchanged callee is consumed as a hypothesis: every operation of the
-- modeled segment parser (token scan, trailing-whitespace trim, trailing
-- continuation-marker trim) is modeled directly below. This region is
-- intentionally empty; the proof depends on no domain axiom.
-- axioms-end

-- pure-start

/-- Printable ASCII characters (code points 32..126). -/
def isPrintable (c : Char) : Bool :=
  let n := c.toNat
  decide (32 ≤ n ∧ n ≤ 126)

/-- ASCII whitespace trimmed from the right end of a field:
space, tab, newline, carriage return, vertical tab, form feed. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  n == 32 || n == 9 || n == 10 || n == 13 || n == 11 || n == 12

/-- Drop trailing whitespace. -/
def dropTrailingWs (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isWs).reverse

/-- Drop a single trailing continuation marker `&` if present. -/
def dropTrailingAmp (cs : List Char) : List Char :=
  match cs.getLast? with
  | some c => if c == '&' then cs.dropLast else cs
  | none => cs

/-- The single-quote delimiter character. -/
def quote : Char := '\''

/-- After a candidate closing quote, the remainder of the segment is acceptable
when it is `spaces*` followed by either the end of the segment or a separator `/`
that introduces trailing notes running to the end. -/
def remainderOk (cs : List Char) : Bool :=
  match cs.dropWhile (· == ' ') with
  | [] => true
  | c :: _ => c == '/'

/-- Scan the token body left to right, accumulating printable characters, and
accept the first quote that closes a non-empty accumulator and whose suffix is
acceptable. A non-printable character before any acceptable quote means the
segment has no token. Returns the captured token body. -/
def scanToken : List Char → List Char → Option (List Char)
  | _acc, [] => none
  | acc, c :: rest =>
      if c == quote && acc ≠ [] && remainderOk rest then
        some acc
      else if isPrintable c then
        scanToken (acc ++ [c]) rest
      else
        none

/-- Capture the token of a segment, if the whole segment is in the expected
shape. `none` ⇒ the segment is not in that shape (the caller keeps it verbatim).
A leading quote opens a token; an immediately following quote yields the empty
token; a segment with no leading quote matches the empty token exactly when its
remainder is acceptable. -/
def matchToken (vc : List Char) : Option (List Char) :=
  match vc with
  | q :: body =>
      if q == quote then
        match scanToken [] body with
        | some s => some s
        | none =>
            match body with
            | q2 :: rest => if q2 == quote && remainderOk rest then some [] else none
            | [] => none
      else
        if remainderOk vc then some [] else none
  | [] => if remainderOk vc then some [] else none
-- pure-end

-- post-conditions-start
/-- Specification of the segment value recovery.

`result` is `none` exactly when the segment is not in the expected quoted shape
(the caller then keeps the raw segment); otherwise `result = some v` where `v` is
the recovered token text. The recovered text is the captured token with trailing
whitespace and at most one trailing continuation marker removed; every interior
doubled quote `''` is part of the text and is preserved verbatim (frame on the
doubled-quote content). -/
def problem_spec_segmentValue (vc : List Char) (result : Option (List Char)) : Prop :=
  result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s))
-- post-conditions-end

-- impl-start
def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  match matchToken vc with
  | none => return none
  | some token =>
      let mut value := token
      value := dropTrailingWs value
      value := dropTrailingAmp value
      return some value
-- impl-end

-- proof-start
theorem correct_segmentValue :
    ∀ vc : List Char, problem_spec_segmentValue vc (implementation_segmentValue vc) := by
  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  cases matchToken vc with
  | none => rfl
  | some token => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### SPEC IS SOUND (verify⇒correct holds under attack).

SAME_SPEC: all 7 attacks True (swebench_unified.markers.same_spec vs bundle Solution.lean).

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: matchTokenLoose lookaheadOk + collapseDoubledQuote): exit 1 — rfl failed (definitional inequality). WRONG, does not close.
- atk_2 (echo, direct restructured `match ... some (dropTrailingAmp (dropTrailingWs token))`): exit 0. `#print axioms correct_segmentValue` => 'does not depend on any axioms'. VERIFIES.
- atk_3 (partial-domain: none on empty vc): exit 1 — rfl failed. WRONG.
- atk_4 (boundary/order-swap: dropTrailingAmp before dropTrailingWs): exit 1 — rfl failed. WRONG.
- atk_5 (control-flow-effect: omit dropTrailingAmp step): exit 1 — rfl failed. WRONG.
- atk_6 (control-flow-effect: omit dropTrailingWs step): exit 1 — rfl failed. WRONG.
- atk_7 (ungrounded-oracle echo: impl = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s)), spec RHS verbatim): exit 0. clean axioms ('does not depend on any axioms'). VERIFIES.

RESOLVE (protocol step 2 — every verifying impl materialized + run through official harness): atk_2 and atk_7 are extensionally identical to the gold impl, so their faithful refined patch IS the gold patch. Ran run_resolve('astropy__astropy-14598', gold_patch) => RESOLVED: True (FAIL_TO_PASS test_long_string_value_with_quotes success; 167 PASS_TO_PASS all success; 0 failures). A resolving echo is NOT a weakness (per G-PANEL-1/eq policy). No verifying wrong impl has a non-resolving faithful patch => spec NOT broken.

LEG AUDIT (refinement.md): 6 legs — op1 A-reference ($-anchor regex), op2 A-reference (no-match->none), op3 I, op4 R (rstrip + DROP replace(''->')), op5 I, op6 I. No kind-3, no A-consumed axiom (meta axioms=[]; G-AX skip legitimate — sole DMR is the regex, tag A-reference). A-reference correspondence INDEPENDENTLY confirmed: (a) bundle G-CONF re-run exit 0, tested=200018 disagreements=0 seed=14598; (b) my own fresh Python oracle (real post-patch regex+cleanup) vs Lean #eval on 21 discriminating cases — ALL MATCH, incl. doubled-quote preservation 'xx''&'->xx'' (fix half), trailing '&'/ws trims, /-comment, non-end-reaching-quote->none, no-leading-quote cases.

Positive control: bundle Solution.lean verifies exit 0, clean axioms. Prepatch reproduced: atk_1 = prepatch impl body, fails to close (G-DIFF corroborates: Solution_prepatch.lean verification failed).

Note: meta.json recorded a prior G-EQ 'INCONCLUSIVE (1 attack inconclusive)'; this fresh run completed all attacks + the required resolve run with no inconclusive/timeout — evidence complete.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — spec is a fully-functional postcondition result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s)), pinning output to a single deterministic value. No same-spec wrong impl with a closing clean-axiom proof has a non-resolving faithful patch.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Recovering a quoted text field from a single continuation segment of a long,
space-padded record. Each segment carries one optionally-quoted token possibly
followed by a separator and trailing notes; this returns the token's contributed
text, or signals that the segment is not in the expected quoted shape (so the
caller keeps it verbatim). Doubled quote marks inside the token are part of the
text and are preserved exactly.
-/

-- axioms-start
-- No unchanged callee is consumed as a hypothesis: every operation of the
-- modeled segment parser (token scan, trailing-whitespace trim, trailing
-- continuation-marker trim) is modeled directly below. This region is
-- intentionally empty; the proof depends on no domain axiom.
-- axioms-end

-- pure-start

/-- Printable ASCII characters (code points 32..126). -/
def isPrintable (c : Char) : Bool :=
  let n := c.toNat
  decide (32 ≤ n ∧ n ≤ 126)

/-- ASCII whitespace trimmed from the right end of a field:
space, tab, newline, carriage return, vertical tab, form feed. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  n == 32 || n == 9 || n == 10 || n == 13 || n == 11 || n == 12

/-- Drop trailing whitespace. -/
def dropTrailingWs (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isWs).reverse

/-- Drop a single trailing continuation marker `&` if present. -/
def dropTrailingAmp (cs : List Char) : List Char :=
  match cs.getLast? with
  | some c => if c == '&' then cs.dropLast else cs
  | none => cs

/-- The single-quote delimiter character. -/
def quote : Char := '\''

/-- After a candidate closing quote, the remainder of the segment is acceptable
when it is `spaces*` followed by either the end of the segment or a separator `/`
that introduces trailing notes running to the end. -/
def remainderOk (cs : List Char) : Bool :=
  match cs.dropWhile (· == ' ') with
  | [] => true
  | c :: _ => c == '/'

/-- Scan the token body left to right, accumulating printable characters, and
accept the first quote that closes a non-empty accumulator and whose suffix is
acceptable. A non-printable character before any acceptable quote means the
segment has no token. Returns the captured token body. -/
def scanToken : List Char → List Char → Option (List Char)
  | _acc, [] => none
  | acc, c :: rest =>
      if c == quote && acc ≠ [] && remainderOk rest then
        some acc
      else if isPrintable c then
        scanToken (acc ++ [c]) rest
      else
        none

/-- Capture the token of a segment, if the whole segment is in the expected
shape. `none` ⇒ the segment is not in that shape (the caller keeps it verbatim).
A leading quote opens a token; an immediately following quote yields the empty
token; a segment with no leading quote matches the empty token exactly when its
remainder is acceptable. -/
def matchToken (vc : List Char) : Option (List Char) :=
  match vc with
  | q :: body =>
      if q == quote then
        match scanToken [] body with
        | some s => some s
        | none =>
            match body with
            | q2 :: rest => if q2 == quote && remainderOk rest then some [] else none
            | [] => none
      else
        if remainderOk vc then some [] else none
  | [] => if remainderOk vc then some [] else none
-- pure-end

-- post-conditions-start
/-- Specification of the segment value recovery.

`result` is `none` exactly when the segment is not in the expected quoted shape
(the caller then keeps the raw segment); otherwise `result = some v` where `v` is
the recovered token text. The recovered text is the captured token with trailing
whitespace and at most one trailing continuation marker removed; every interior
doubled quote `''` is part of the text and is preserved verbatim (frame on the
doubled-quote content). -/
def problem_spec_segmentValue (vc : List Char) (result : Option (List Char)) : Prop :=
  result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s))
-- post-conditions-end

-- impl-start
def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  match matchToken vc with
  | none => return none
  | some token =>
      let mut value := token
      value := dropTrailingWs value
      value := dropTrailingAmp value
      return some value
-- impl-end

-- proof-start
theorem correct_segmentValue :
    ∀ vc : List Char, problem_spec_segmentValue vc (implementation_segmentValue vc) := by
  intro vc
  unfold problem_spec_segmentValue implementation_segmentValue
  cases matchToken vc with
  | none => rfl
  | some token => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### SPEC IS SOUND (verify⇒correct holds under attack).

SAME_SPEC: all 7 attacks True (swebench_unified.markers.same_spec vs bundle Solution.lean).

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: matchTokenLoose lookaheadOk + collapseDoubledQuote): exit 1 — rfl failed (definitional inequality). WRONG, does not close.
- atk_2 (echo, direct restructured `match ... some (dropTrailingAmp (dropTrailingWs token))`): exit 0. `#print axioms correct_segmentValue` => 'does not depend on any axioms'. VERIFIES.
- atk_3 (partial-domain: none on empty vc): exit 1 — rfl failed. WRONG.
- atk_4 (boundary/order-swap: dropTrailingAmp before dropTrailingWs): exit 1 — rfl failed. WRONG.
- atk_5 (control-flow-effect: omit dropTrailingAmp step): exit 1 — rfl failed. WRONG.
- atk_6 (control-flow-effect: omit dropTrailingWs step): exit 1 — rfl failed. WRONG.
- atk_7 (ungrounded-oracle echo: impl = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s)), spec RHS verbatim): exit 0. clean axioms ('does not depend on any axioms'). VERIFIES.

RESOLVE (protocol step 2 — every verifying impl materialized + run through official harness): atk_2 and atk_7 are extensionally identical to the gold impl, so their faithful refined patch IS the gold patch. Ran run_resolve('astropy__astropy-14598', gold_patch) => RESOLVED: True (FAIL_TO_PASS test_long_string_value_with_quotes success; 167 PASS_TO_PASS all success; 0 failures). A resolving echo is NOT a weakness (per G-PANEL-1/eq policy). No verifying wrong impl has a non-resolving faithful patch => spec NOT broken.

LEG AUDIT (refinement.md): 6 legs — op1 A-reference ($-anchor regex), op2 A-reference (no-match->none), op3 I, op4 R (rstrip + DROP replace(''->')), op5 I, op6 I. No kind-3, no A-consumed axiom (meta axioms=[]; G-AX skip legitimate — sole DMR is the regex, tag A-reference). A-reference correspondence INDEPENDENTLY confirmed: (a) bundle G-CONF re-run exit 0, tested=200018 disagreements=0 seed=14598; (b) my own fresh Python oracle (real post-patch regex+cleanup) vs Lean #eval on 21 discriminating cases — ALL MATCH, incl. doubled-quote preservation 'xx''&'->xx'' (fix half), trailing '&'/ws trims, /-comment, non-end-reaching-quote->none, no-leading-quote cases.

Positive control: bundle Solution.lean verifies exit 0, clean axioms. Prepatch reproduced: atk_1 = prepatch impl body, fails to close (G-DIFF corroborates: Solution_prepatch.lean verification failed).

Note: meta.json recorded a prior G-EQ 'INCONCLUSIVE (1 attack inconclusive)'; this fresh run completed all attacks + the required resolve run with no inconclusive/timeout — evidence complete.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Solution.lean compiles (lean_verify exit 0); #print axioms correct_segmentValue reports NO axiom dependence (proof genuine, no sorryAx). same_spec(Solution.lean, Solution_prepatch.lean, Lean.language) = True (spec region byte-identical to the discriminating prepatch). Independent re-transcription of problem_spec_segmentValue vs the real post-patch pipeline (fixed anchored regex + rstrip + trailing-& drop, NO ''->' collapse) agrees on all 1e6 printable-ASCII inputs and all exhaustive short strings; interior doubled-quote preservation (the fix's crux) verified exact ('xx''&'->xx'', 'a''b''c'->a''b''c). The mapping correctly frames the .strip() boundary; the modeled matchToken/scanToken/remainderOk faithfully reproduce the changed regex's capture semantics over the actual reachable domain. No spec-too-strong condition on any in-domain input.

Counterexample / evidence:

```
spec("'x'\n")=None vs real("'x'\n")='x' — but strip() makes it '\'x\'' → both 'x'; not a real defect.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope = consumer spec view (marker projection of Solution.lean, impl+proof elided). refinement.md/mapping.md quote the gold patch and narrate pre-patch behavior but are auditor-facing artifacts, NOT part of the spec view, so out of scope. Mechanical leakage.screen PASSES (0 hard failures): no diff markers, no reproduced gold-patch line, no patched path card.py, no identifier/comment echoing patched symbols {Card,Verify,split}, no bug/fix narration. Semantically clean: (a) the doubled-quote-preservation requirement ('' preserved verbatim) is ALREADY PUBLIC in problem_statement (the reported bug is ''→' collapse; expected = round-trip equality), so the docstring restating it leaks nothing beyond the task; (b) the end-anchor half of the fix is modeled only as correct FITS parse semantics (remainderOk must reach end-of-input) — the view never mentions re/$/_strg_comment_RE/_comm_field, pre- vs post-patch, collapseDoubledQuote, or any edit location, and contains no bug narration. same_spec(Solution, prepatch)=True, i.e. the spec is stable across the patch and not tuned to the diff. A spec that a correct impl satisfies is not leakage — it reveals only intended behavior. problem_statement checked: none of card.py/_split/_strg/_comm_field/re.compile/replace/anchor/rstrip/regex appear, and none appear in the spec view either.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
