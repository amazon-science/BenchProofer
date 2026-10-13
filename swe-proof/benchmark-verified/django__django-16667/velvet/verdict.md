# P2 adversarial audit — django__django-16667

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_boundary_constant.lean`, `atk_4_ungrounded_echo.lean`, `atk_5_nonterminating.lean`, `atk_6_legs_swapped.lean`, `atk_7_no_orzero.lean`, `atk_8_drop_rendered.lean`, `atk_9_partial_empty_year.lean`, `atk_12_clobber_components.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_10_oracle_echo.lean`, `atk_11_spelled_out.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG impl verifies. The two impls that DO verify (atk_10_oracle_echo: `dateText y m d outcome` grounded at the real components; atk_11_spelled_out: fallbacks expanded through orZero) are both behaviourally gold-equivalent (0 differences vs the gold branch over 70,648 real-CPython cases), and their materialized faithful patches were RUN through the official harness: BOTH RESOLVED (completed=True, resolved=True, attempts=1, flaky=False, F2P 2/2 + P2P 24/24, zero failures). verify=>correct holds on the evidence gathered.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
       | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .unrepresentable => Except.error .valueEscaped
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
       | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .unrepresentable => Except.ok (pseudoTriple y m d)
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 3 — `atk_3_boundary_constant.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
       | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .unrepresentable => Except.ok (orZero [] ++ ['-'] ++ orZero [])
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 4 — `atk_4_ungrounded_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,16 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
-    let result : Except DateErr (List Char) :=
-      match outcome with
-      | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+    let result : Except DateErr (List Char) := dateText [] [] [] outcome
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 5 — `atk_5_nonterminating.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,8 +90,9 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
+    let mut i : Nat := 0
+    while true do
+      i := i + 1
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
@@ -101,5 +102,11 @@
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 6 — `atk_6_legs_swapped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .notCalendar     => Except.ok fallbackNoComponents
+      | .unrepresentable => Except.ok (pseudoTriple y m d)
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 7 — `atk_7_no_orzero.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
+      | .notCalendar     => Except.ok (y ++ ['-'] ++ m ++ ['-'] ++ d)
       | .unrepresentable => Except.ok fallbackNoComponents
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 8 — `atk_8_drop_rendered.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
-      | .rendered s      => Except.ok s
+      | .rendered _      => Except.ok fallbackNoComponents
       | .notCalendar     => Except.ok (pseudoTriple y m d)
       | .unrepresentable => Except.ok fallbackNoComponents
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 9 — `atk_9_partial_empty_year.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,22 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
+      | .notCalendar     =>
+          if y = [] then Except.ok fallbackNoComponents
+          else Except.ok (pseudoTriple y m d)
       | .unrepresentable => Except.ok fallbackNoComponents
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 10 — `atk_10_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,16 +90,16 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
-    let result : Except DateErr (List Char) :=
-      match outcome with
-      | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+    let result : Except DateErr (List Char) := dateText y m d outcome
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 11 — `atk_11_spelled_out.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,16 +90,22 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .notCalendar     =>
+          Except.ok (orZero y ++ ['-'] ++ orZero m ++ ['-'] ++ orZero d)
+      | .unrepresentable =>
+          Except.ok (orZero [] ++ ['-'] ++ orZero [] ++ ['-'] ++ orZero [])
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 12 — `atk_12_clobber_components.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,26 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
+    let mut yy : List Char := y
+    let mut mm : List Char := m
+    let mut dd : List Char := d
+    yy := []
+    mm := []
+    dd := []
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
-      | .notCalendar     => Except.ok (pseudoTriple y m d)
+      | .notCalendar     => Except.ok (pseudoTriple yy mm dd)
       | .unrepresentable => Except.ok fallbackNoComponents
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

Attack 13 — `atk_13_empty_on_overflow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,16 +90,20 @@
   ensures ∃ r, out = Except.ok r
   do
     -- impl-start
-    -- Dispatch on the outcome of handing the components to the calendar
-    -- machinery, mapping each outcome to the text `dateText` assigns it.
     let result : Except DateErr (List Char) :=
       match outcome with
       | .rendered s      => Except.ok s
       | .notCalendar     => Except.ok (pseudoTriple y m d)
-      | .unrepresentable => Except.ok fallbackNoComponents
+      | .unrepresentable => Except.ok []
     return result
     -- impl-end
 
 prove_correct dateComponentsText by
-  loom_solve
-  cases outcome <;> simp_all
+  loom_solve <;>
+    (try cases outcome) <;>
+    (try simp_all [dateText, pseudoTriple, orZero, fallbackNoComponents]) <;>
+    (try grind) <;>
+    (try decide) <;>
+    (try omega) <;>
+    (try rfl) <;>
+    (try trivial)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The step that turns three textual date components into a
   concrete calendar value (and then renders it) is an unchanged callee whose
   three mutually-exclusive outcomes are the ONLY thing that matters here; it is
   modeled as a free input `ConstructOutcome` (see below). The postconditions
   hold for EVERY such outcome, so the callee is owed no contract — it is
   strictly weaker than any concrete implementation of it (directive 7). The
   behaviour this bundle actually pins — how each outcome is turned into the
   returned text — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result of attempting to interpret three textual components as a calendar
   value, in three mutually-exclusive shapes:
     * `rendered s`  — a calendar value was obtained and rendered to the text `s`;
     * `notCalendar` — the components name no representable calendar value
                       (e.g. a zero/oversize month or day, or a non-numeric
                       component);
     * `unrepresentable` — a component's magnitude exceeds the range the
                       calendar machinery accepts at all. -/
inductive ConstructOutcome where
  | rendered (s : List Char)
  | notCalendar
  | unrepresentable
  deriving DecidableEq

/- The non-value shape of the result carrier: the caller is handed no text at
   all. It is the error side of the `Except` this branch returns. -/
inductive DateErr where
  | valueEscaped
  deriving DecidableEq

/- A single component, normalized for the fallback rendering: an empty component
   shows as the digit zero, any other component shows verbatim. -/
def orZero (x : List Char) : List Char :=
  if x = [] then ['0'] else x

/- The fallback rendering: the three normalized components joined by hyphens
   (a pseudo-ISO triple). -/
def pseudoTriple (y m d : List Char) : List Char :=
  orZero y ++ ['-'] ++ orZero m ++ ['-'] ++ orZero d

/- That same fallback rendering taken at three unsupplied components. -/
def fallbackNoComponents : List Char := pseudoTriple [] [] []

/- The returned text for the all-components-supplied branch, as a total function
   of the three components and the construction outcome. The function is total:
   every outcome is mapped to a value (`Except.ok`). -/
def dateText (y m d : List Char) (o : ConstructOutcome) : Except DateErr (List Char) :=
  match o with
  | .rendered s     => Except.ok s
  | .notCalendar    => Except.ok (pseudoTriple y m d)
  | .unrepresentable => Except.ok fallbackNoComponents

@[grind] lemma dateText_rendered (y m d : List Char) (s : List Char) :
    dateText y m d (.rendered s) = Except.ok s := rfl
@[grind] lemma dateText_notCalendar (y m d : List Char) :
    dateText y m d .notCalendar = Except.ok (pseudoTriple y m d) := rfl
@[grind] lemma dateText_unrepresentable (y m d : List Char) :
    dateText y m d .unrepresentable = Except.ok fallbackNoComponents := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn three supplied textual date components into the text this widget reports,
   on the branch where all three components are present. The components are first
   handed to the calendar machinery; its outcome decides the result, per
   `dateText`.
   `y`, `m`, `d` and `outcome` are read-only (not `mut`); the routine builds a
   fresh result and mutates none of them (directive 5). -/
method dateComponentsText (y : List Char) (m : List Char) (d : List Char)
    (outcome : ConstructOutcome) return (out : Except DateErr (List Char))
  ensures out = dateText y m d outcome
  ensures ∀ s, outcome = .rendered s → out = Except.ok s
  ensures outcome = .notCalendar → out = Except.ok (pseudoTriple y m d)
  ensures outcome = .unrepresentable → out = Except.ok fallbackNoComponents
  ensures ∃ r, out = Except.ok r
  do
    -- impl-start
    -- Dispatch on the outcome of handing the components to the calendar
    -- machinery, mapping each outcome to the text `dateText` assigns it.
    let result : Except DateErr (List Char) :=
      match outcome with
      | .rendered s      => Except.ok s
      | .notCalendar     => Except.ok (pseudoTriple y m d)
      | .unrepresentable => Except.ok fallbackNoComponents
    return result
    -- impl-end

prove_correct dateComponentsText by
  loom_solve
  cases outcome <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial review, django__django-16667 (SelectDateWidget OverflowError crash). All 13 attack files + pos_control confirmed byte-identical spec via swebench_unified.markers.same_spec == True (only the impl region and the prove_correct tactic body were edited; axioms/pure/pre/post untouched). Verified with 'bash scripts/lean_verify.sh <f>', run CONCURRENTLY 4 at a time in 4 batches (results.txt).

POSITIVE CONTROL: pos_control.lean (byte copy of the shipped Solution.lean) EXIT=0 (verifies).

PREPATCH REPRODUCED: atk_1_prepatch.lean (unrepresentable -> Except.error .valueEscaped, i.e. the uncaught OverflowError) EXIT=1, failing exactly the three clauses refinement.md predicts -- 'ensures_1: exists r, out = Except.ok r', 'ensures_2: outcome = .unrepresentable -> out = Except.ok fallbackNoComponents' and 'ensures_5: out = dateText y m d outcome', each with goal |- False on the .unrepresentable case. Matches the G-DIFF claim.

TACTIC-BRITTLENESS CONTROL (the methodological trap the prior pass hit): rather than reuse the shipped 2-line tactic (which can reject an attack for 'simp_all made no progress' -- a tactic artifact, not a spec rejection), EVERY attack was given the SAME strong shape-agnostic tactic (loom_solve <;> try cases outcome <;> try simp_all[dateText,pseudoTriple,orZero,fallbackNoComponents] <;> try grind <;> try decide <;> try omega <;> try rfl <;> try trivial). This is legitimate because spec_view ELIDES the prove_correct body, so a consumer supplies impl AND proof. Result: all 11 non-echo rejections carry GENUINE SEMANTIC unsolved goals (|- False, or concrete List Char inequalities), and atk_5 is rejected by total-correctness ('Decreasing annotations are required in total correctness semantics'). Zero rejections are tactic artifacts.

ATTACKS (all same_spec=True), 13 distinct impls, 11 REJECTED with semantic goals:
- atk_1_prepatch (EXIT=1) the prepatch escaping OverflowError -- goal |- False.
- atk_2_partial_domain (EXIT=1) PARTIAL-DOMAIN: overflow leg reuses the component-bearing pseudoTriple; real effect would return '9223372036854775808-12-1' instead of '0-0-0', breaking F2P. Goal: (if y=[] ...) ++ ... = ['0','-','0','-','0'].
- atk_3_boundary_constant (EXIT=1) BOUNDARY: '0-0' (two components) instead of '0-0-0' -- goal |- False.
- atk_4_ungrounded_echo (EXIT=1) UNGROUNDED ORACLE ECHO: `dateText [] [] [] outcome` -- echoes the oracle but at the EMPTY triple, so the notCalendar leg drops the supplied text. Rejected on ensures_3/ensures_5.
- atk_5_nonterminating (EXIT=1) CONTROL-FLOW EFFECT: `while true do i := i+1` before the correct result; rejected by total-correctness termination.
- atk_6_legs_swapped (EXIT=1) the two fallback legs exchanged.
- atk_7_no_orzero (EXIT=1) orZero normalization dropped on the ValueError fallback ('-12-1' instead of '0-12-1').
- atk_8_drop_rendered (EXIT=1) success path discards the strftime payload.
- atk_9_partial_empty_year (EXIT=1) PARTIAL-DOMAIN data-conditioned: correct EXCEPT when y=[] on the notCalendar leg, where it returns '0-0-0' instead of '0-12-1'.
- atk_12_clobber_components (EXIT=1) CONTROL-FLOW EFFECT via mutable accumulators clobbering y/m/d before the fallback is built.
- atk_13_empty_on_overflow (EXIT=1) NO-ESCAPE-ONLY: satisfies 'always returns a value' but returns the EMPTY text on overflow. Goal |- False. This proves the spec pins the LITERAL constant, not merely the no-crash property.

THE TWO VERIFYING ECHOES -- PROTOCOL STEP 2 EXECUTED (this is what the prior pass could not complete):
- atk_10_oracle_echo (EXIT=0) and atk_11_spelled_out (EXIT=0) verify. Both are behaviourally gold: echo_equiv.py diffs each against the gold branch over 70,648 cases (boundary grid + 60k seeded fuzz, 4 input_formats) -> 0 differences.
- I materialized each one's FAITHFUL refined patch against the pristine base widgets.py at 02c356f2f3945b8075735d485c3cf48cad991011 (extracted via git show from the upstream repository; both verified to apply cleanly with patch -p1 --dry-run) and RAN the official harness CONCURRENTLY:
run_resolve('django__django-16667', patch_atk_10.diff, run_id='geq-h34cvo-atk10') -> COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False, F2P success=2 failure=0, P2P success=24 failure=0
run_resolve('django__django-16667', patch_atk_11.diff, run_id='geq-h34cvo-atk11') -> COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False, F2P success=2 failure=0, P2P success=24 failure=0
Logs: resolve_atk_10.log, resolve_atk_11.log. NO verify-but-does-not-resolve gap. Both are CORRECT ECHOES of the gold, not weaknesses.
NOTE vs the prior recorded audit: the prior pass's fail was 'eq: INCONCLUSIVE -- 2 attack(s) inconclusive' caused by run_resolve harness/image errors ('no report ... Instances with errors: 1'), NOT by a spec defect. Docker is healthy now and the instance image (swebench/sweb.eval.x86_64.django_1776_django-16667) is cached locally; both resolves completed on attempt 1 with zero flakiness.

CONSTANT PINNED (machine-checked): const_check.lean EXIT=0 proves by decide that fallbackNoComponents = "0-0-0".toList, String.mk fallbackNoComponents = "0-0-0", and that it differs from "0-0"/"0-0-0-0"/""; also that pseudoTriple "9223372036854775808" "12" "1" != fallbackNoComponents (atk_2's break). So allZeroTriple/fallbackNoComponents is exactly the string the F2P test asserts.

A-LEG AUDIT (my assignment; R/I left to G-CONF). Solution.lean declares ZERO module-level axioms -- confirmed (grep: 0 'axiom' declarations). The single A-leg is A2: the UNCHANGED construct-and-format callee, modeled as a FREE input over the ConstructOutcome partition. This is the weakest possible modeling (directive 7): the postconditions must hold for EVERY outcome value, so the callee is owed no contract and cannot smuggle in the fix.

(a) PARTITION EXHAUSTIVENESS/FAITHFULNESS (aleg_partition.py): I independently re-derived mapping.md 3.1's predicate and ran the REAL CPython datetime.date(int(y),int(m),int(d)) over 295,640 cases -- a 56^3 boundary grid (C-long edges +-2^31 and their +-1 neighbours, sys.maxsize/+1, the problem-statement 1234567821345678 triple, unicode digits, 100- and 4300-digit magnitudes, whitespace/sign/underscore/float/hex forms, 'nan'/'inf') plus 120k seeded fuzz over 4 input_formats. Result: 0 fourth outcomes (partition is TOTAL -- no outcome the routing fails to handle) and 0 predicate mismatches. Boundary claims reproduce EXACTLY as documented: int('2147483647')->notCalendar, int('2147483648')->unrepresentable(OverflowError), -2147483648->notCalendar, -2147483649->unrepresentable. Conversion-before-validation confirmed: date(2**40,13,1)->unrepresentable (overflow beats the invalid month), while date('abc',2**40,1)->notCalendar (the left-to-right int() parse failure beats the overflow) -- exactly mapping.md 3.1's stated ordering.

(b) MODEL-VS-REAL DIFFERENTIAL of A2+A6 (aleg_differential.py): ran the real post-patch branch verbatim against the transliterated dateText/pseudoTriple/orZero model over 118,600 cases (5 input_formats). Result: 0 model/real mismatches and 0 A6 violations (no exception ever escaped the patched branch). This confirms both that A6's 'never lets OverflowError escape' is true of the real code and that the real branch's return is a function of (y,m,d,outcome) ONLY -- no hidden dependence the free-input model cannot observe.

REFINEMENT.MD LEG AUDIT: 6 legs, all tagged -- A1 (R), A2 (A-reference), A3 (I), A4 (I+R), A5 (I), A6 (R). No kind-3, matching the section C claim, and I confirm the tags are correct rather than merely present. Critically, the CHANGED op (the new `except OverflowError: return "0-0-0"` leg) is modeled DEEPLY and CONCRETELY at A5 as an I op over the free outcome input -- NOT hidden behind an axiom about the function under change. So the only trust point is the unchanged callee's partition, which I attacked in (a)/(b) and failed to break. A3 correctly leaves the 'rendered s' payload opaque (the unchanged callee's job) while G-CONF runs the real callee. mapping.md's DateErr <-> escaping-exception binding is coherent with the prepatch twin (diff confirms the twin differs ONLY in the unrepresentable leg plus its comment).

DOC DEFECT (advisory, cosmetic -- NOT a soundness break): refinement.md and mapping.md refer 6 times each to a symbol named `allZeroTriple`, but Solution.lean actually names it `fallbackNoComponents` (5 occurrences); `allZeroTriple` does not exist in the artifact. Stale symbol name after a rename. The referenced VALUE is correct and machine-checked to be "0-0-0", so refinement fidelity is unaffected, but the docs cite a non-existent identifier and should be updated for reviewability.

CAVEAT (advisory, not a break): the spec models only the all-present inner branch; the outer framing (data.get, the y==m==d=='' -> None short-circuit, the trailing data.get(name)) is unmodeled-identical-context per refinement.md B -- legitimate since the patch touches nothing there, and the F2P tests exercise the full real value_from_datadict end-to-end. Non-str data values fall outside the declared str carrier and are out of scope.

VERDICT: SOUND. 13 same-spec attacks re-run (floor is 5); 11 distinct wrong impls REJECTED on genuine semantic goals under a deliberately strong tactic; prepatch reproduced for the right reason; positive control verifies; and BOTH verifying impls' faithful patches were EXECUTED under the official harness and RESOLVED (2/2 F2P, 24/24 P2P, attempts=1, non-flaky). No verifying wrong impl exists, so verify=>correct is not falsified by any attack I could construct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_boundary_constant.lean`, `atk_4_ungrounded_echo.lean`, `atk_5_nonterminating.lean`, `atk_6_legs_swapped.lean`, `atk_7_no_orzero.lean`, `atk_8_drop_rendered.lean`, `atk_9_partial_empty_year.lean`, `atk_12_clobber_components.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_10_oracle_echo.lean`, `atk_11_spelled_out.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG impl verifies. The two impls that DO verify (atk_10_oracle_echo: `dateText y m d outcome` grounded at the real components; atk_11_spelled_out: fallbacks expanded through orZero) are both behaviourally gold-equivalent (0 differences vs the gold branch over 70,648 real-CPython cases), and their materialized faithful patches were RUN through the official harness: BOTH RESOLVED (completed=True, resolved=True, attempts=1, flaky=False, F2P 2/2 + P2P 24/24, zero failures). verify=>correct holds on the evidence gathered.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_constant.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_ungrounded_echo.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_nonterminating.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_legs_swapped.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_no_orzero.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_drop_rendered.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_partial_empty_year.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_spelled_out.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_clobber_components.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_empty_on_overflow.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The step that turns three textual date components into a
   concrete calendar value (and then renders it) is an unchanged callee whose
   three mutually-exclusive outcomes are the ONLY thing that matters here; it is
   modeled as a free input `ConstructOutcome` (see below). The postconditions
   hold for EVERY such outcome, so the callee is owed no contract — it is
   strictly weaker than any concrete implementation of it (directive 7). The
   behaviour this bundle actually pins — how each outcome is turned into the
   returned text — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result of attempting to interpret three textual components as a calendar
   value, in three mutually-exclusive shapes:
     * `rendered s`  — a calendar value was obtained and rendered to the text `s`;
     * `notCalendar` — the components name no representable calendar value
                       (e.g. a zero/oversize month or day, or a non-numeric
                       component);
     * `unrepresentable` — a component's magnitude exceeds the range the
                       calendar machinery accepts at all. -/
inductive ConstructOutcome where
  | rendered (s : List Char)
  | notCalendar
  | unrepresentable
  deriving DecidableEq

/- The non-value shape of the result carrier: the caller is handed no text at
   all. It is the error side of the `Except` this branch returns. -/
inductive DateErr where
  | valueEscaped
  deriving DecidableEq

/- A single component, normalized for the fallback rendering: an empty component
   shows as the digit zero, any other component shows verbatim. -/
def orZero (x : List Char) : List Char :=
  if x = [] then ['0'] else x

/- The fallback rendering: the three normalized components joined by hyphens
   (a pseudo-ISO triple). -/
def pseudoTriple (y m d : List Char) : List Char :=
  orZero y ++ ['-'] ++ orZero m ++ ['-'] ++ orZero d

/- That same fallback rendering taken at three unsupplied components. -/
def fallbackNoComponents : List Char := pseudoTriple [] [] []

/- The returned text for the all-components-supplied branch, as a total function
   of the three components and the construction outcome. The function is total:
   every outcome is mapped to a value (`Except.ok`). -/
def dateText (y m d : List Char) (o : ConstructOutcome) : Except DateErr (List Char) :=
  match o with
  | .rendered s     => Except.ok s
  | .notCalendar    => Except.ok (pseudoTriple y m d)
  | .unrepresentable => Except.ok fallbackNoComponents

@[grind] lemma dateText_rendered (y m d : List Char) (s : List Char) :
    dateText y m d (.rendered s) = Except.ok s := rfl
@[grind] lemma dateText_notCalendar (y m d : List Char) :
    dateText y m d .notCalendar = Except.ok (pseudoTriple y m d) := rfl
@[grind] lemma dateText_unrepresentable (y m d : List Char) :
    dateText y m d .unrepresentable = Except.ok fallbackNoComponents := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn three supplied textual date components into the text this widget reports,
   on the branch where all three components are present. The components are first
   handed to the calendar machinery; its outcome decides the result, per
   `dateText`.
   `y`, `m`, `d` and `outcome` are read-only (not `mut`); the routine builds a
   fresh result and mutates none of them (directive 5). -/
method dateComponentsText (y : List Char) (m : List Char) (d : List Char)
    (outcome : ConstructOutcome) return (out : Except DateErr (List Char))
  ensures out = dateText y m d outcome
  ensures ∀ s, outcome = .rendered s → out = Except.ok s
  ensures outcome = .notCalendar → out = Except.ok (pseudoTriple y m d)
  ensures outcome = .unrepresentable → out = Except.ok fallbackNoComponents
  ensures ∃ r, out = Except.ok r
  do
    -- impl-start
    -- Dispatch on the outcome of handing the components to the calendar
    -- machinery, mapping each outcome to the text `dateText` assigns it.
    let result : Except DateErr (List Char) :=
      match outcome with
      | .rendered s      => Except.ok s
      | .notCalendar     => Except.ok (pseudoTriple y m d)
      | .unrepresentable => Except.ok fallbackNoComponents
    return result
    -- impl-end

prove_correct dateComponentsText by
  loom_solve
  cases outcome <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial review, django__django-16667 (SelectDateWidget OverflowError crash). All 13 attack files + pos_control confirmed byte-identical spec via swebench_unified.markers.same_spec == True (only the impl region and the prove_correct tactic body were edited; axioms/pure/pre/post untouched). Verified with 'bash scripts/lean_verify.sh <f>', run CONCURRENTLY 4 at a time in 4 batches (results.txt).

POSITIVE CONTROL: pos_control.lean (byte copy of the shipped Solution.lean) EXIT=0 (verifies).

PREPATCH REPRODUCED: atk_1_prepatch.lean (unrepresentable -> Except.error .valueEscaped, i.e. the uncaught OverflowError) EXIT=1, failing exactly the three clauses refinement.md predicts -- 'ensures_1: exists r, out = Except.ok r', 'ensures_2: outcome = .unrepresentable -> out = Except.ok fallbackNoComponents' and 'ensures_5: out = dateText y m d outcome', each with goal |- False on the .unrepresentable case. Matches the G-DIFF claim.

TACTIC-BRITTLENESS CONTROL (the methodological trap the prior pass hit): rather than reuse the shipped 2-line tactic (which can reject an attack for 'simp_all made no progress' -- a tactic artifact, not a spec rejection), EVERY attack was given the SAME strong shape-agnostic tactic (loom_solve <;> try cases outcome <;> try simp_all[dateText,pseudoTriple,orZero,fallbackNoComponents] <;> try grind <;> try decide <;> try omega <;> try rfl <;> try trivial). This is legitimate because spec_view ELIDES the prove_correct body, so a consumer supplies impl AND proof. Result: all 11 non-echo rejections carry GENUINE SEMANTIC unsolved goals (|- False, or concrete List Char inequalities), and atk_5 is rejected by total-correctness ('Decreasing annotations are required in total correctness semantics'). Zero rejections are tactic artifacts.

ATTACKS (all same_spec=True), 13 distinct impls, 11 REJECTED with semantic goals:
- atk_1_prepatch (EXIT=1) the prepatch escaping OverflowError -- goal |- False.
- atk_2_partial_domain (EXIT=1) PARTIAL-DOMAIN: overflow leg reuses the component-bearing pseudoTriple; real effect would return '9223372036854775808-12-1' instead of '0-0-0', breaking F2P. Goal: (if y=[] ...) ++ ... = ['0','-','0','-','0'].
- atk_3_boundary_constant (EXIT=1) BOUNDARY: '0-0' (two components) instead of '0-0-0' -- goal |- False.
- atk_4_ungrounded_echo (EXIT=1) UNGROUNDED ORACLE ECHO: `dateText [] [] [] outcome` -- echoes the oracle but at the EMPTY triple, so the notCalendar leg drops the supplied text. Rejected on ensures_3/ensures_5.
- atk_5_nonterminating (EXIT=1) CONTROL-FLOW EFFECT: `while true do i := i+1` before the correct result; rejected by total-correctness termination.
- atk_6_legs_swapped (EXIT=1) the two fallback legs exchanged.
- atk_7_no_orzero (EXIT=1) orZero normalization dropped on the ValueError fallback ('-12-1' instead of '0-12-1').
- atk_8_drop_rendered (EXIT=1) success path discards the strftime payload.
- atk_9_partial_empty_year (EXIT=1) PARTIAL-DOMAIN data-conditioned: correct EXCEPT when y=[] on the notCalendar leg, where it returns '0-0-0' instead of '0-12-1'.
- atk_12_clobber_components (EXIT=1) CONTROL-FLOW EFFECT via mutable accumulators clobbering y/m/d before the fallback is built.
- atk_13_empty_on_overflow (EXIT=1) NO-ESCAPE-ONLY: satisfies 'always returns a value' but returns the EMPTY text on overflow. Goal |- False. This proves the spec pins the LITERAL constant, not merely the no-crash property.

THE TWO VERIFYING ECHOES -- PROTOCOL STEP 2 EXECUTED (this is what the prior pass could not complete):
- atk_10_oracle_echo (EXIT=0) and atk_11_spelled_out (EXIT=0) verify. Both are behaviourally gold: echo_equiv.py diffs each against the gold branch over 70,648 cases (boundary grid + 60k seeded fuzz, 4 input_formats) -> 0 differences.
- I materialized each one's FAITHFUL refined patch against the pristine base widgets.py at 02c356f2f3945b8075735d485c3cf48cad991011 (extracted via git show from the upstream repository; both verified to apply cleanly with patch -p1 --dry-run) and RAN the official harness CONCURRENTLY:
run_resolve('django__django-16667', patch_atk_10.diff, run_id='geq-h34cvo-atk10') -> COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False, F2P success=2 failure=0, P2P success=24 failure=0
run_resolve('django__django-16667', patch_atk_11.diff, run_id='geq-h34cvo-atk11') -> COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False, F2P success=2 failure=0, P2P success=24 failure=0
Logs: resolve_atk_10.log, resolve_atk_11.log. NO verify-but-does-not-resolve gap. Both are CORRECT ECHOES of the gold, not weaknesses.
NOTE vs the prior recorded audit: the prior pass's fail was 'eq: INCONCLUSIVE -- 2 attack(s) inconclusive' caused by run_resolve harness/image errors ('no report ... Instances with errors: 1'), NOT by a spec defect. Docker is healthy now and the instance image (swebench/sweb.eval.x86_64.django_1776_django-16667) is cached locally; both resolves completed on attempt 1 with zero flakiness.

CONSTANT PINNED (machine-checked): const_check.lean EXIT=0 proves by decide that fallbackNoComponents = "0-0-0".toList, String.mk fallbackNoComponents = "0-0-0", and that it differs from "0-0"/"0-0-0-0"/""; also that pseudoTriple "9223372036854775808" "12" "1" != fallbackNoComponents (atk_2's break). So allZeroTriple/fallbackNoComponents is exactly the string the F2P test asserts.

A-LEG AUDIT (my assignment; R/I left to G-CONF). Solution.lean declares ZERO module-level axioms -- confirmed (grep: 0 'axiom' declarations). The single A-leg is A2: the UNCHANGED construct-and-format callee, modeled as a FREE input over the ConstructOutcome partition. This is the weakest possible modeling (directive 7): the postconditions must hold for EVERY outcome value, so the callee is owed no contract and cannot smuggle in the fix.

(a) PARTITION EXHAUSTIVENESS/FAITHFULNESS (aleg_partition.py): I independently re-derived mapping.md 3.1's predicate and ran the REAL CPython datetime.date(int(y),int(m),int(d)) over 295,640 cases -- a 56^3 boundary grid (C-long edges +-2^31 and their +-1 neighbours, sys.maxsize/+1, the problem-statement 1234567821345678 triple, unicode digits, 100- and 4300-digit magnitudes, whitespace/sign/underscore/float/hex forms, 'nan'/'inf') plus 120k seeded fuzz over 4 input_formats. Result: 0 fourth outcomes (partition is TOTAL -- no outcome the routing fails to handle) and 0 predicate mismatches. Boundary claims reproduce EXACTLY as documented: int('2147483647')->notCalendar, int('2147483648')->unrepresentable(OverflowError), -2147483648->notCalendar, -2147483649->unrepresentable. Conversion-before-validation confirmed: date(2**40,13,1)->unrepresentable (overflow beats the invalid month), while date('abc',2**40,1)->notCalendar (the left-to-right int() parse failure beats the overflow) -- exactly mapping.md 3.1's stated ordering.

(b) MODEL-VS-REAL DIFFERENTIAL of A2+A6 (aleg_differential.py): ran the real post-patch branch verbatim against the transliterated dateText/pseudoTriple/orZero model over 118,600 cases (5 input_formats). Result: 0 model/real mismatches and 0 A6 violations (no exception ever escaped the patched branch). This confirms both that A6's 'never lets OverflowError escape' is true of the real code and that the real branch's return is a function of (y,m,d,outcome) ONLY -- no hidden dependence the free-input model cannot observe.

REFINEMENT.MD LEG AUDIT: 6 legs, all tagged -- A1 (R), A2 (A-reference), A3 (I), A4 (I+R), A5 (I), A6 (R). No kind-3, matching the section C claim, and I confirm the tags are correct rather than merely present. Critically, the CHANGED op (the new `except OverflowError: return "0-0-0"` leg) is modeled DEEPLY and CONCRETELY at A5 as an I op over the free outcome input -- NOT hidden behind an axiom about the function under change. So the only trust point is the unchanged callee's partition, which I attacked in (a)/(b) and failed to break. A3 correctly leaves the 'rendered s' payload opaque (the unchanged callee's job) while G-CONF runs the real callee. mapping.md's DateErr <-> escaping-exception binding is coherent with the prepatch twin (diff confirms the twin differs ONLY in the unrepresentable leg plus its comment).

DOC DEFECT (advisory, cosmetic -- NOT a soundness break): refinement.md and mapping.md refer 6 times each to a symbol named `allZeroTriple`, but Solution.lean actually names it `fallbackNoComponents` (5 occurrences); `allZeroTriple` does not exist in the artifact. Stale symbol name after a rename. The referenced VALUE is correct and machine-checked to be "0-0-0", so refinement fidelity is unaffected, but the docs cite a non-existent identifier and should be updated for reviewability.

CAVEAT (advisory, not a break): the spec models only the all-present inner branch; the outer framing (data.get, the y==m==d=='' -> None short-circuit, the trailing data.get(name)) is unmodeled-identical-context per refinement.md B -- legitimate since the patch touches nothing there, and the F2P tests exercise the full real value_from_datadict end-to-end. Non-str data values fall outside the declared str carrier and are out of scope.

VERDICT: SOUND. 13 same-spec attacks re-run (floor is 5); 11 distinct wrong impls REJECTED on genuine semantic goals under a deliberately strong tactic; prepatch reproduced for the right reason; positive control verifies; and BOTH verifying impls' faithful patches were EXECUTED under the official harness and RESOLVED (2/2 F2P, 24/24 P2P, attempts=1, non-flaky). No verifying wrong impl exists, so verify=>correct is not falsified by any attack I could construct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real repo behavior (modeled function disagrees with the real callee on some input). RESULT: no diverging input found. Verdict FAITHFUL.

### Setup
- The pre-assigned worktree was EMPTY (not a git repo), so I built my own from django_django.git at base_commit 02c356f2f3945b8075735d485c3cf48cad991011 (HEAD confirmed: 02c356f2f3 'Fixed #34428 -- Made ASGIStaticFilesHandler adapt response to async iterator'). Both scratch worktrees removed and pruned at the end.
- patch.diff is NOT in velvet/ (as the prompt implied) but at the instance root ../patch.diff. Located and audited it there.

### MECHANICAL CHECKS (all pass)
- same_spec(Solution.lean, Solution_prepatch.lean) via swebench_unified.markers = True -> spec region byte-identical; only impl region differs (confirmed by diff: prepatch maps .unrepresentable to Except.error .valueEscaped plus a comment block).
- lean_verify.sh Solution.lean -> exit 0 (verifies, no sorry/error).
- lean_verify.sh Solution_prepatch.lean -> FAILS on the .unrepresentable case (unsolved goals on 'ensures out = dateText ...' and the Except.ok clause). G-DIFF discrimination is real, not vacuous.
- GOLD PROVENANCE: found the true upstream commit d22209cb42 'Fixed #34424 -- Fixed SelectDateWidget crash for inputs raising OverflowError'. Its code hunk is exactly `except OverflowError: return "0-0-0"`. Bundle patch.diff applies cleanly at base_commit and yields a widgets.py BYTE-IDENTICAL to the real gold result (diff empty). Differs from `git show` output only in cosmetic headers (SWE-bench dataset form: no index line, hunk context label). patch.diff IS gold verbatim.
- F2P: applied gold code+test patch, ran forms_tests.field_tests.test_datefield + forms_tests.widget_tests.test_selectdatewidget -> 26 tests OK.

### CORE DIFFERENTIAL (the actual faithfulness attack)
Transliterated Solution.lean's dateText/pseudoTriple/orZero/fallbackNoComponents EXACTLY, left the construct-and-format callee as the REAL datetime.date/int/strftime, and diffed against the REAL gold-patched SelectDateWidget.value_from_datadict.
- Run 1 (default locale): 170,583 inputs, 0 mismatches. Corpus = full cartesian product of 50 adversarial component strings (empty, '0', '00', '007', signed forms, calendar edges 0/13/29/30/31/32, year edges 999/1000/9999/10000, the C-long edges +-2^31 and +-2^31-1, sys.maxsize and sys.maxsize+1, the problem-statement 1234567821345678, 10**100, non-numeric 'abc'/'inf'/'nan'/'None'/'1e3'/'2.0'/'0x10', underscore '1_0', whitespace ' 5'/'5 '/'\t1', unicode digits '٠'/'١٢'/fullwidth) plus 60,000 seeded random triples.
- Run 2 (locale sweep): all 105 Django locales x 4,500 cases = 472,395 comparisons, 0 mismatches. This directly tests the mapping.md claim that input_format is safely folded into the opaque `rendered s` payload. The 7 distinct DATE_INPUT_FORMATS[0] values across all locales are all ASCII, and 209,979 real strftime calls over every valid (year,month,day) x every locale format raised ZERO exceptions.
- CONTROL (harness has teeth): mutating pseudoTriple to append 'X' produced immediate mismatches. The 0-mismatch results are meaningful, not a silently-broken oracle.

SPECIFIC 'TOO STRONG' HYPOTHESES I TRIED AND KILLED
1. `ensures exists r, out = Except.ok r` (total, never an error) is the strongest clause. Attack: find a real input where the patched branch still raises. strftime is called OUTSIDE the try/except in the real code, so any strftime exception WOULD escape and refute the total-Except.ok postcondition. REFUTED: strftime raises only for surrogate format strings (UnicodeEncodeError on '\ud800'), unreachable via Django's 7 ASCII locale formats; 209,979 real calls, 0 raises. Pathological formats ('%', '%%', '%Q', '%\x00', 200 '%'s) all return normally.
2. Fourth outcome breaking the 3-way partition exhaustiveness. Found ONE: TypeError from int() on non-str (list/dict/None/object/tuple). But this is out of scope by construction — the modeled branch is guarded by `if y is not None and m is not None and d is not None` and mapping.md §2 refines y/m/d as `str` pulled from submitted data. Within the str domain the partition is exactly total (verified: over a 13,824-triple boundary sweep, outcomes were only ValueError/OverflowError/ok). Not a defect.
3. Boundary drift in the signed C-long predicate. Verified exactly as documented: 2147483647 -> ValueError, 2147483648 -> OverflowError, -2147483648 -> ValueError, -2147483649 -> OverflowError. Also confirmed mapping.md's ordering claims: overflow is raised during date()'s C arg conversion so it fires regardless of calendar validity (10000, 2^31, 1) -> OverflowError; and the int() parse is left-to-right so a non-numeric component wins over an overflowing one (('abc', '2^31', '1') -> ValueError). Both narrative claims hold.
4. orZero fidelity to Python's `x or 0`. Only '' is falsy among str candidates ('0', '00', '0.0', ' ', 'False' are all truthy), so empty->'0' / else verbatim is exact.
5. fallbackNoComponents vs the gold literal. #eval in Lean: fallbackNoComponents = "0-0-0" is `true`; pseudoTriple "2017" "" "23" = "2017-0-23" matching the gold code comment. Semantics correct.

### DISCREPANCY WORTH FLAGGING (documentation, NOT a faithfulness defect)
SYMBOL DRIFT: mapping.md (6 occurrences) and refinement.md (5 occurrences) both name the OverflowError-leg constant `allZeroTriple`, but Solution.lean/Solution_prepatch.lean define and use `fallbackNoComponents` (0 occurrences of allZeroTriple in either Lean file). The docs also describe it as 'the constant string literal "0-0-0"' whereas the Lean actually DERIVES it as pseudoTriple [] [] []. I verified these are semantically identical (#eval -> "0-0-0", equals "0-0-0".toList is true), so the refinement conclusion is unaffected and the spec still pins the gold behavior. But mapping.md's §1 symbol-binding table and refinement.md's A5 row reference a symbol that does not exist in the frozen artifact — a stale-rename bug in the G-EQ-audited narrative that should be corrected for reviewability.

SCOPE NOTE (not a defect): the spec models only the inner all-present try/except. The outer framing (data.get on %s_year/%s_month/%s_day, the y==m==d=='' -> None short-circuit, the all-present guard, trailing data.get(name)) is byte-identical pre/post-patch, correctly declared unmodeled identical context in refinement.md §B. I confirmed byte-identity from the real gold commit stat: widgets.py changed by exactly +2 lines. Also confirmed the changed leg is reachable end-to-end: the F2P triple and the problem-statement triple both return '0-0-0', and DateField.to_python('0-0-0') raises ValidationError 'Enter a valid date.' as mapping.md claims.

CONCLUSION: The spec is neither too strong nor drifted. Every postcondition — including the strongest, total 'always Except.ok' clause — holds on the real gold-patched repo across 642,978 differential comparisons spanning all 105 locales, with a positive control proving the oracle detects deviation. No diverging input exists that I could construct. Verdict FAITHFUL. One documentation-level symbol-drift finding (allZeroTriple vs fallbackNoComponents) is reported for repair but does not constitute a spec defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction), django__django-16667 velvet. Verdict NO-LEAKAGE (== pass) — recorded per the panel-layer convention for a properly dispositioned relaxed-leakage bundle. Nothing was taken on trust; every leg below was re-derived mechanically.

SPEC-REGION IDENTITY — CONFIRMED. markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True, and I additionally byte-diffed the two rendered spec views (diff = empty). The method signature and all 5 ensures are byte-identical across the twins; the only delta is inside impl-start/impl-end.

STATE OF THE LEAK. Exactly ONE leaking facet, and it is the one already dispositioned in RELAXED_LEAKAGE.md: the exact output constant of the gold-added overflow leg. It survives de-narration BY VALUE, not by spelling — the spec view writes it compositionally as `fallbackNoComponents := pseudoTriple [] [] []`, and I proved the value with the real verifier (Probe.lean: `example : fallbackNoComponents = "0-0-0".toList := by decide` elaborates, exit 0; `#eval String.mk fallbackNoComponents` prints "0-0-0"). It is bound to the overflow outcome by `ensures outcome = .unrepresentable -> out = Except.ok fallbackNoComponents`. So the lexical G-LEAK pass (I re-ran leakage.screen: passed=True, hard_failures=[]) is NOT what makes the recording honest — the disposition is.

NO NEW LEAKING LINE. Swept the spec view for every patched repo symbol / gold-diff token: widgets.py, value_from_datadict, SelectDateWidget, datetime.date, strftime, input_format, OverflowError, ValueError, data.get, year_field, the literal "0-0-0", line numbers 1158/1160 — ALL absent from the spec view. Facet-by-facet: (a) the TRIGGER (`ConstructOutcome.unrepresentable` held apart from `notCalendar`) is public — problem_statement names OverflowError 5x plus the sys.maxsize+1 reproduction; (b) `pseudoTriple`/`orZero` model `"%s-%s-%s" % (y or 0, m or 0, d or 0)`, which I read at widgets.py:1163 in a fresh worktree at base_commit 02c356f2f3 — pre-patch source, a CONTEXT line in patch.diff, readable by any solver, so disclosing it reveals nothing about the edit; (c) `ensures ∃ r, out = Except.ok r` (the branch must return rather than let the exception escape) is exactly what the problem_statement asks ("without guarding against a possible OverflowError"). Only facet (b→) the constant is the leak, and it is the dispositioned one.

### UNAVOIDABILITY RE-DERIVED (both halves executed, not argued):
(1) The constant is a genuinely FREE design choice under the public text. I lifted the real branch from widgets.py and ran the most natural problem_statement-only fix — widen the existing handler, `except:` reusing the pre-existing fallback the pre-patch code's own visible structure suggests. On the hidden F2P input (str(sys.maxsize+1), '12', '1'): gold -> '0-0-0'; pre-patch -> OverflowError: Python int too large to convert to C long; PS-only alt -> '9223372036854775808-12-1'; F2P expects '0-0-0' => alt passes F2P? False. Same on the problem_statement's own triple: gold '0-0-0' vs alt '1234567821345678-1-1'. Also reproduced the non-obvious asymmetry the spec view discloses: the overflow leg DISCARDS the components (constant) while the ValueError leg PRESERVES them ('2000','13','1') -> '2000-13-1'.

(2) A spec that does NOT name the constant is too weak to be faithful. I built option (b) myself (WeakSpec.lean): remediation left abstract as `opaque sentinel`, keeping the rendered echo, the pre-existing fallback and `ensures ∃ r, out = Except.ok r`. It VERIFIES (exit 0) with an impl returning the WRONG constant "0-0-1" — so option (b) yields verify ⇏ resolve, a spec-too-weak defect, strictly worse than a documented leak. Conversely the FROZEN spec has teeth: the same wrong-constant rival against the byte-copied frozen contract (Rival001.lean) is REJECTED, exit 1, unsolved goals on `ensures_2` and `ensures_5` naming `Except.ok "0-0-1".toList = Except.ok fallbackNoComponents`.
Hence faithful + non-leaking is provably impossible here — precisely the relaxed-leakage condition of spec_guide.md directive 6.

NO PS-ONLY DERIVATION OF THE CONSTANT EXISTS. `git grep -- '0-0-0'` over django/ at base_commit: zero hits (exit 1). Tree-wide, the only occurrence is tests/forms_tests/widget_tests/test_selectdatewidget.py:578, inside test_format_value's `valid_formats` list — a test of the unrelated INPUT-parsing method format_value, in a file the consumer does not see. Token scan of instance.json['problem_statement']: '0-0-0' absent, 'zero' absent, 'pseudo' absent, 'except' absent. Judged against problem_statement ONLY: hints_text is a 29-byte "patch / Thanks for this report." and contains none of these — nothing rides on it either way. The constant is pinned solely by the hidden F2P test_value_from_datadict assertion ((str(sys.maxsize+1), '12', '1'), '0-0-0').

DISPOSITION MACHINERY INTACT. RELAXED_LEAKAGE.md present; meta.json relaxed_leakage = True; gates.G-LEAK.status = "relaxed"; and gates/leak.py honors the flag mechanically (relaxed = meta_status == "relaxed" or (relaxed_leakage is True and RELAXED_LEAKAGE.md exists)), returning "relaxed" even when the lexical screen passes. gates/_audit.py confirms there is no "relaxed" status at the panel layer — a relaxed-leakage panel records as pass + note — so NO-LEAKAGE is the honest recording, not a downgrade.

CORE SOUNDNESS RE-MEASURED (the disposition depends on it). Solution.lean verifies: lean_verify.sh exit 0. Solution_prepatch.lean FAILS exit 1 on exactly the discriminating clauses — `ensures_1: ∃ r, out = Except.ok r`, `ensures_2: outcome = .unrepresentable -> out = Except.ok fallbackNoComponents`, `ensures_5: out = dateText y m d outcome`. So the change-carrying content lives in the frozen spec, not smuggled into the impl. Recorded G-VERIFY/G-DIFF/G-GOLD/G-MUT/G-PBT/G-INTEGRITY/G-HYGIENE/G-RESOLVE/G-CONF/G-AX/G-PANEL-2 all pass.

WHY THE PRIOR G-PANEL-3 = fail / agent_verdict LEAKAGE IS NOT RE-ASSERTED. That record is the audit that PRESCRIBED this relaxation; its own RECOMMENDED REMEDIATION judges adopting the relaxation the likelier correct disposition, because the alternative weakens the spec below the F2P bar — which I confirmed above with WeakSpec.lean. Re-judging a retained attack label as the reject lane would invent a spec weakness that does not exist. Its substantive claims are all true and all covered by the disposition; it identifies no facet beyond the output constant.

MINOR (non-leakage, out of gate scope, for the record): SYMBOL-NAME DRIFT between docs and spec. refinement.md (5x) and mapping.md (6x) and RELAXED_LEAKAGE.md (6x) all call the constant `allZeroTriple`, but Solution.lean/Solution_prepatch.lean define and use `fallbackNoComponents`; `allZeroTriple` occurs 0x in either .lean file. The recorded G-PANEL-2/G-DIFF notes likewise quote `allZeroTriple` in ensures_2, whereas the live verifier output I captured says `fallbackNoComponents`. Semantically identical (same definition, value proven "0-0-0"), and the rename is if anything mildly MORE de-narrated, so it is not a leak — but the refinement/mapping docs no longer name a symbol that exists in the spec, which is a G-EQ/G-HYGIENE-side inconsistency worth fixing so the R/I map stays mechanically checkable.

CONCLUSION: spec region byte-identical across twins; exactly one leaking facet, already dispositioned; unavoidability independently re-derived in both directions with the real verifier and the real repo; no new leaking line and no broken disposition. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.