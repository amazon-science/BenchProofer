# P2 adversarial audit — matplotlib__matplotlib-23412

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return (0 : Int) :: onoff
     -- impl-end
 
 prove_correct renderDashPattern by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,10 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    if phase = 6 then
+      return phase :: onoff
+    else
+      return (0 : Int) :: onoff
     -- impl-end
 
 prove_correct renderDashPattern by
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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return phase :: onoff.reverse
     -- impl-end
 
 prove_correct renderDashPattern by
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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return phase :: []
     -- impl-end
 
 prove_correct renderDashPattern by
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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return [6]
     -- impl-end
 
 prove_correct renderDashPattern by
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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return onoff ++ [phase]
     -- impl-end
 
 prove_correct renderDashPattern by
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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return (phase + 1) :: onoff
     -- impl-end
 
 prove_correct renderDashPattern by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,7 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    return phase :: phase :: onoff
     -- impl-end
 
 prove_correct renderDashPattern by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the render-time dash pattern is a pure construction
@@ -49,7 +49,9 @@
   ensures out.length = onoff.length + 1
   do
     -- impl-start
-    return phase :: onoff
+    match onoff with
+      | [] => return (0 : Int) :: onoff
+      | _  => return phase :: onoff
     -- impl-end
 
 prove_correct renderDashPattern by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the render-time dash pattern is a pure construction
--  from the values the shape already holds, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A filled outline shape stores its boundary stroke style as a dash pattern: a
   scalar phase (the starting position along the on/off cycle) together with the
   even-length on/off ink-length sequence. When the shape is rendered, the dash
   pattern handed to the drawing back end must be the shape's OWN dash pattern:
   the phase is preserved exactly, and the on/off sequence is preserved exactly,
   element for element, in order.

   In particular, two shapes whose stored dash patterns differ only in their
   phase must be handed dash patterns that still differ in that same phase — the
   phase a caller supplies is honoured, never silently dropped.

   The render-time dash pattern is modeled as a single list whose head is the
   phase handed to the back end and whose tail is the on/off sequence handed to
   the back end. The phase and on/off ink lengths are modeled as exact integers:
   the tested behaviour is solely whether the stored phase is carried through to
   the renderer unchanged versus dropped to zero — a discrete value-vs-zero
   distinction independent of any floating-point magnitude, so an exact integer
   carrier is faithful (see mapping.md). The stored on/off sequence is read-only
   (not `mut`): the construction never mutates it (directive 5). -/
method renderDashPattern (phase : Int) (onoff : List Int) return (out : List Int)
  -- The render-time pattern is the stored phase followed by the stored on/off
  -- sequence, in order: head is the phase exactly, tail is the on/off verbatim.
  ensures out = phase :: onoff
  ensures out.head? = some phase
  ensures out.tail = onoff
  ensures out.length = onoff.length + 1
  do
    -- impl-start
    return phase :: onoff
    -- impl-end

prove_correct renderDashPattern by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: renderDashPattern(phase:Int)(onoff:List Int):List Int, postconditions `ensures out = phase :: onoff` (plus its three consequences head?/tail/length). The exact-equality postcondition FULLY PINS the output as a function of the inputs; there is no ungrounded oracle to echo and the on/off tail is pinned verbatim (out.tail=onoff), so no faithful wrong impl can verify. meta confirms axioms=[] and deep_model_references=[] — there are NO A-legs (no axiom-consumed / A-reference correspondence) to attack; refinement.md legs A1=R, A2=R, A3=R+I, §B documents no kind-3 steps. Model↔patch correspondence audited: the changed op (offset 0 -> self._dash_pattern[0]) is modeled directly & concretely via out.head?=some phase; correspondence holds.

PROTOCOL EXECUTED (in /tmp scratch, one backend/Lean): confirmed byte-identical spec regions via swebench_unified.markers.same_spec over velvet backend => True for all 9 attacks and positive control (interp python from root). Verified each with `bash scripts/lean_verify.sh <f>`, run concurrently in batches of 4 as background jobs.

### ATTACK RESULTS (path | impl | verify exit | reason):
- atk_1 `return (0:Int)::onoff` (PREPATCH BUG, offset dropped) | exit=1 FAIL | unsolved: 0::onoff = phase::onoff, (0::onoff).head?=some phase. Prepatch reproduced.
- atk_2 `if phase=6 then phase::onoff else 0::onoff` (partial-domain / F2P-value echo) | exit=1 FAIL | unsolved on else branch: 0::onoff = phase::onoff.
- atk_3 `return phase::onoff.reverse` (boundary/tail-order) | exit=1 FAIL | unsolved: phase::onoff.reverse = phase::onoff, tail mismatch.
- atk_4 `return phase::[]` (control-flow-effect, tail dropped) | exit=1 FAIL | unsolved: [phase]=phase::onoff, length/tail.
- atk_5 `return [6]` (ungrounded-oracle echo of F2P constant) | exit=1 FAIL | unsolved: [6]=phase::onoff, all four ensures.
- atk_6 `return onoff ++ [phase]` (structure swap append) | exit=1 FAIL | unsolved: onoff++[phase]=phase::onoff.
- atk_7 `return (phase+1)::onoff` (phase off-by-one) | exit=1 FAIL | unsolved: (phase+1)::onoff = phase::onoff.
- atk_8 `return phase::phase::onoff` (dup head, length wrong) | exit=1 FAIL | unsolved: length, phase::phase::onoff = phase::onoff.
- atk_9 `match onoff with [] => 0::onoff | _ => phase::onoff` (partial-domain on solid-line/empty boundary) | exit=1 FAIL | unsolved on [] branch: 0::onoff = phase::onoff.
positive_control (gold `return phase::onoff`) | exit=0 VERIFIES.

All 9 distinct same-spec wrong impls FAIL verification (exit=1, unsolved goals); positive control verifies (exit=0). Because NO wrong impl verifies, protocol step 2 (materialize faithful patch + run_resolve) is vacuous — there is no verifying-wrong-impl whose patch could resolve. verify => correct holds: the exact-equality postcondition refutes every wrong impl at verify time. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the render-time dash pattern is a pure construction
--  from the values the shape already holds, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A filled outline shape stores its boundary stroke style as a dash pattern: a
   scalar phase (the starting position along the on/off cycle) together with the
   even-length on/off ink-length sequence. When the shape is rendered, the dash
   pattern handed to the drawing back end must be the shape's OWN dash pattern:
   the phase is preserved exactly, and the on/off sequence is preserved exactly,
   element for element, in order.

   In particular, two shapes whose stored dash patterns differ only in their
   phase must be handed dash patterns that still differ in that same phase — the
   phase a caller supplies is honoured, never silently dropped.

   The render-time dash pattern is modeled as a single list whose head is the
   phase handed to the back end and whose tail is the on/off sequence handed to
   the back end. The phase and on/off ink lengths are modeled as exact integers:
   the tested behaviour is solely whether the stored phase is carried through to
   the renderer unchanged versus dropped to zero — a discrete value-vs-zero
   distinction independent of any floating-point magnitude, so an exact integer
   carrier is faithful (see mapping.md). The stored on/off sequence is read-only
   (not `mut`): the construction never mutates it (directive 5). -/
method renderDashPattern (phase : Int) (onoff : List Int) return (out : List Int)
  -- The render-time pattern is the stored phase followed by the stored on/off
  -- sequence, in order: head is the phase exactly, tail is the on/off verbatim.
  ensures out = phase :: onoff
  ensures out.head? = some phase
  ensures out.tail = onoff
  ensures out.length = onoff.length + 1
  do
    -- impl-start
    return phase :: onoff
    -- impl-end

prove_correct renderDashPattern by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: renderDashPattern(phase:Int)(onoff:List Int):List Int, postconditions `ensures out = phase :: onoff` (plus its three consequences head?/tail/length). The exact-equality postcondition FULLY PINS the output as a function of the inputs; there is no ungrounded oracle to echo and the on/off tail is pinned verbatim (out.tail=onoff), so no faithful wrong impl can verify. meta confirms axioms=[] and deep_model_references=[] — there are NO A-legs (no axiom-consumed / A-reference correspondence) to attack; refinement.md legs A1=R, A2=R, A3=R+I, §B documents no kind-3 steps. Model↔patch correspondence audited: the changed op (offset 0 -> self._dash_pattern[0]) is modeled directly & concretely via out.head?=some phase; correspondence holds.

PROTOCOL EXECUTED (in /tmp scratch, one backend/Lean): confirmed byte-identical spec regions via swebench_unified.markers.same_spec over velvet backend => True for all 9 attacks and positive control (interp python from root). Verified each with `bash scripts/lean_verify.sh <f>`, run concurrently in batches of 4 as background jobs.

### ATTACK RESULTS (path | impl | verify exit | reason):
- atk_1 `return (0:Int)::onoff` (PREPATCH BUG, offset dropped) | exit=1 FAIL | unsolved: 0::onoff = phase::onoff, (0::onoff).head?=some phase. Prepatch reproduced.
- atk_2 `if phase=6 then phase::onoff else 0::onoff` (partial-domain / F2P-value echo) | exit=1 FAIL | unsolved on else branch: 0::onoff = phase::onoff.
- atk_3 `return phase::onoff.reverse` (boundary/tail-order) | exit=1 FAIL | unsolved: phase::onoff.reverse = phase::onoff, tail mismatch.
- atk_4 `return phase::[]` (control-flow-effect, tail dropped) | exit=1 FAIL | unsolved: [phase]=phase::onoff, length/tail.
- atk_5 `return [6]` (ungrounded-oracle echo of F2P constant) | exit=1 FAIL | unsolved: [6]=phase::onoff, all four ensures.
- atk_6 `return onoff ++ [phase]` (structure swap append) | exit=1 FAIL | unsolved: onoff++[phase]=phase::onoff.
- atk_7 `return (phase+1)::onoff` (phase off-by-one) | exit=1 FAIL | unsolved: (phase+1)::onoff = phase::onoff.
- atk_8 `return phase::phase::onoff` (dup head, length wrong) | exit=1 FAIL | unsolved: length, phase::phase::onoff = phase::onoff.
- atk_9 `match onoff with [] => 0::onoff | _ => phase::onoff` (partial-domain on solid-line/empty boundary) | exit=1 FAIL | unsolved on [] branch: 0::onoff = phase::onoff.
positive_control (gold `return phase::onoff`) | exit=0 VERIFIES.

All 9 distinct same-spec wrong impls FAIL verification (exit=1, unsolved goals); positive control verifies (exit=0). Because NO wrong impl verifies, protocol step 2 (materialize faithful patch + run_resolve) is vacuous — there is no verifying-wrong-impl whose patch could resolve. verify => correct holds: the exact-equality postcondition refutes every wrong impl at verify time. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet) == True; the two files differ only in the impl region. (2) Solution.lean verifies (lean_verify.sh exit 0); Solution_prepatch.lean fails postconditions `out = phase :: onoff` and `out.head? = some phase` when phase != 0 (unsolved goals `0 :: onoff = phase :: onoff`), so the spec is non-vacuous and senses the gold change (G-DIFF pass corroborated). Real repo at base_commit f06c2c3 (lib/matplotlib/patches.py, Patch.draw, lines 589-591 in worktree): pre-patch installs `_dash_pattern=(0, self._dash_pattern[1])` (offset forced to 0); gold patch installs `_dash_pattern=(self._dash_pattern)` == `(offset, onoffseq)` unchanged, consumed by `gc.set_dashes(*self._dash_pattern)`. The modeled function renderDashPattern(phase, onoff) = phase :: onoff is a pure re-pack (head=offset preserved exactly, tail=onoffseq copied verbatim) that matches the real post-patch callee on EVERY input. (4) The float->Int refinement is sound because the operation is a value copy with no arithmetic/scaling, so precision is never exercised; the offset-preserved-vs-zero discriminator is faithful for any element type. G-CONF (conformance_check.py) transliterates the exact patched source line as oracle and agrees with the model shadow on 100050 int+float fuzzed pairs (incl. F2P phase-6 case), 0 disagreements. Every postcondition is exactly what the real callee produces — the spec is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[]) and spec-region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec=True). Reviewed the projected spec view (imports/axioms/pure/pre/post regions + method signature + ensures + doc comment) — impl and proof bodies are elided.

The public problem_statement already discloses the target behavior in full: title '[Bug]: offset dash linestyle has no effect in patch objects' and body 'When setting the linestyle on a patch object using a dash tuple the offset has no effect', with the expected outcome demonstrating that a nonzero offset should produce a phase shift. Thus the spec's requirement (the stored phase must be honored and carried to the renderer, never silently dropped) is derivable directly from the public statement.

The spec view leaks nothing beyond problem_statement:
- No gold-diff line reproduced (no '_dash_pattern=(self._dash_pattern)', no '(0, self._dash_pattern[1])').
- No patched file path ('lib/matplotlib/patches.py') or module path.
- No patched repo symbol echoed: 'draw', '_dash_pattern', 'cbook', '_setattr_cm', 'set_dashes' appear nowhere in the spec-view identifiers or prose. The only symbol is the abstracted method name 'renderDashPattern'.
- No fix/bug/patch narration in spec-view comments (the 'PRE-PATCH BUG' narration lives only in Solution_prepatch.lean's impl region, which is stripped from the spec view; L3 narration scan is clean).
- The doc comment describes behavior in fully generic terms ('filled outline shape', 'phase', 'on/off sequence', 'drawing back end'). The phrase 'carried through ... versus dropped to zero' describes the observable failure mode, which is behaviorally equivalent to the public 'offset has no effect' — the offset having no effect IS rendering as offset 0 — so it reveals no code mechanism beyond the public bug report.

No reconstruction shortcut to the gold edit exists in the spec view beyond what problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
