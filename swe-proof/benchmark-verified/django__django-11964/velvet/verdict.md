# P2 adversarial audit — django__django-11964

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `echo_verify.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies. The single verifying candidate (echo_verify) is behaviorally identical to gold; its faithful patch = the gold patch, which RESOLVED under the official harness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,7 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char := member.defaultLabel
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,10 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char :=
+      match member.value with
+      | .intVal n => (toString n).toList
+      | .strVal _ => []
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,10 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char :=
+      match member.value with
+      | .intVal n => (toString (n + 1)).toList
+      | .strVal s => s
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,7 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char := (renderValue member.value).reverse
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,7 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char := member.defaultLabel ++ renderValue member.value
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,10 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    let result : List Char :=
+      match member.value with
+      | .intVal n => (toString (Int.natAbs n)).toList
+      | .strVal s => s
     return result
     -- impl-end
 
```

Attack 7 — `echo_verify.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The textual rendering of the member's underlying
@@ -60,10 +60,11 @@
   ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
   do
     -- impl-start
-    -- Render the member's underlying value as text (numeric -> decimal text,
-    -- textual -> its own characters). The member's generic default token is left
-    -- untouched.
-    let result : List Char := renderValue member.value
+    -- Behaviorally identical to renderValue; written as an explicit dispatch.
+    let result : List Char :=
+      match member.value with
+      | .intVal n => (toString n).toList
+      | .strVal s => s
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The textual rendering of the member's underlying
--  value is modeled DEEPLY in the `pure` region below: an integer payload is
--  rendered in its usual decimal form (`toString`), a text payload is its own
--  characters. Nothing the proof consumes is left to an axiom, so there is no
--  axiom_check.py and G-AX is skipped.)
-- axioms-end

-- pure-start
/- The payload an enumerated member carries. The two shapes the modeled domain
   distinguishes are the only ones the rendering reacts to differently:
     * `intVal n` — a numeric payload;
     * `strVal s` — a textual payload (a sequence of code points). -/
inductive MemberValue where
  | intVal (n : Int)
  | strVal (s : List Char)
  deriving Inhabited

/- An enumerated member, reduced to the only data the rendering observes:
     * `value`        — its underlying payload (numeric or textual);
     * `defaultLabel` — the generic object rendering a member carries by default
                        (the qualified `Owner.NAME` token, e.g. the literal
                        `MyChoice.FIRST_CHOICE` shown in the problem statement). -/
structure Member where
  value : MemberValue
  defaultLabel : List Char
  deriving Inhabited

/- Render a payload as text: a numeric payload becomes its decimal text form,
   a textual payload is exactly its own code points. This is the textual form of
   the value "cast to str" — decimal digits (with a leading minus for a negative
   number, no separators or leading zeros) for a number, identity for text. -/
@[grind] def renderValue : MemberValue → List Char
  | .intVal n => (toString n).toList
  | .strVal s => s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render an enumerated member as text. The result must be the textual form of
   the member's own underlying value — so that a member used as a plain value
   (rendered into templates, sent to other systems, compared as text) shows
   the value it stands for, not a generic object token. `member` is a read-only
   input and is not mutated (directive 5). -/
method memberToStr (member : Member) return (out : List Char)
  ensures out = renderValue member.value
  ensures (∀ n : Int, member.value = MemberValue.intVal n → out = (toString n).toList)
  ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
  do
    -- impl-start
    let result : List Char := renderValue member.value
    return result
    -- impl-end

prove_correct memberToStr by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**STRUCTURAL:** spec postcondition `out = renderValue member.value` is a TOTAL functional equation over the entire closed MemberValue domain (intVal Int | strVal (List Char)), with renderValue deeply modeled. meta.json confirms axioms=[], deep_model_references=[], additional_change_sites=[]. No A-legs, no precondition, no under-determined region -> any verifying impl is forced to exact gold behavior. refinement.md legs A1-A4 are all R / R+I / I (no A-consumed, no A-reference, no kind-3), mechanically covered by G-CONF (pass, 100032 inputs, 0 disagreements, seed 11964). mapping.md bijections (int<->intVal/toString<->str(int); str<->strVal/identity; List Char<->str) are exact.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, velvet backend). Command: `bash scripts/lean_verify.sh <file>`.
- atk_1 (prepatch bug: return member.defaultLabel): EXIT=1, unsolved goals @67:26 -> FAILS verify. Reproduces the prepatch bug (matches Solution_prepatch.lean).
- atk_2 (partial-domain: strVal -> []): EXIT=1, unsolved goals @70:26 -> FAILS.
- atk_3 (boundary/off-by: intVal n -> toString (n+1)): EXIT=1, unsolved goals @70:26 -> FAILS.
- atk_4 (control-flow-effect: (renderValue member.value).reverse): EXIT=1, unsolved goals @67:26 -> FAILS.
- atk_5 (ungrounded-oracle echo: defaultLabel ++ renderValue member.value): EXIT=1, unsolved goals @67:26 -> FAILS.
- atk_6 (sign-drop boundary: intVal n -> toString (Int.natAbs n)): EXIT=1, unsolved goals @70:26 -> FAILS.
- echo_verify (gold-behavior written as explicit match dispatch): EXIT=0 -> VERIFIES. This is the only verifying wrong-impl candidate; behaviorally identical to gold.
- pos_control (renderValue member.value): EXIT=0 -> VERIFIES (positive control OK).
All six wrong-behavior impls fail with genuine 'unsolved goals' (postcondition violation), not syntax errors -> spec discriminates correctly. Verifications launched concurrently in two background batches of 4 (<=4 at a time).

RESOLVE (protocol step 2): echo_verify is the sole verifying wrong impl. Its faithful refined patch equals the gold patch (str(self.value)). Materialized to echo_verify.patch.diff and executed via swebench_unified.harness.run_resolve('django__django-11964', ...): COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. Therefore verify=>correct holds for the only verifying candidate; no verifying impl's patch fails to resolve.

**VERDICT:** SOUND. >=5 distinct attacks run (7 total incl. prepatch + echo), none breaks the spec; the one verifying candidate's faithful patch resolves. (Note: recorded meta.json G-EQ status was 'fail: INCONCLUSIVE - 2 attacks inconclusive' from a prior pass that could not exec real Choices locally / didn't complete resolve; this pass completed the resolve run and reaches a determinate SOUND.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `echo_verify.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies. The single verifying candidate (echo_verify) is behaviorally identical to gold; its faithful patch = the gold patch, which RESOLVED under the official harness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `echo_verify.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The textual rendering of the member's underlying
--  value is modeled DEEPLY in the `pure` region below: an integer payload is
--  rendered in its usual decimal form (`toString`), a text payload is its own
--  characters. Nothing the proof consumes is left to an axiom, so there is no
--  axiom_check.py and G-AX is skipped.)
-- axioms-end

-- pure-start
/- The payload an enumerated member carries. The two shapes the modeled domain
   distinguishes are the only ones the rendering reacts to differently:
     * `intVal n` — a numeric payload;
     * `strVal s` — a textual payload (a sequence of code points). -/
inductive MemberValue where
  | intVal (n : Int)
  | strVal (s : List Char)
  deriving Inhabited

/- An enumerated member, reduced to the only data the rendering observes:
     * `value`        — its underlying payload (numeric or textual);
     * `defaultLabel` — the generic object rendering a member carries by default
                        (the qualified `Owner.NAME` token, e.g. the literal
                        `MyChoice.FIRST_CHOICE` shown in the problem statement). -/
structure Member where
  value : MemberValue
  defaultLabel : List Char
  deriving Inhabited

/- Render a payload as text: a numeric payload becomes its decimal text form,
   a textual payload is exactly its own code points. This is the textual form of
   the value "cast to str" — decimal digits (with a leading minus for a negative
   number, no separators or leading zeros) for a number, identity for text. -/
@[grind] def renderValue : MemberValue → List Char
  | .intVal n => (toString n).toList
  | .strVal s => s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render an enumerated member as text. The result must be the textual form of
   the member's own underlying value — so that a member used as a plain value
   (rendered into templates, sent to other systems, compared as text) shows
   the value it stands for, not a generic object token. `member` is a read-only
   input and is not mutated (directive 5). -/
method memberToStr (member : Member) return (out : List Char)
  ensures out = renderValue member.value
  ensures (∀ n : Int, member.value = MemberValue.intVal n → out = (toString n).toList)
  ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
  do
    -- impl-start
    let result : List Char := renderValue member.value
    return result
    -- impl-end

prove_correct memberToStr by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**STRUCTURAL:** spec postcondition `out = renderValue member.value` is a TOTAL functional equation over the entire closed MemberValue domain (intVal Int | strVal (List Char)), with renderValue deeply modeled. meta.json confirms axioms=[], deep_model_references=[], additional_change_sites=[]. No A-legs, no precondition, no under-determined region -> any verifying impl is forced to exact gold behavior. refinement.md legs A1-A4 are all R / R+I / I (no A-consumed, no A-reference, no kind-3), mechanically covered by G-CONF (pass, 100032 inputs, 0 disagreements, seed 11964). mapping.md bijections (int<->intVal/toString<->str(int); str<->strVal/identity; List Char<->str) are exact.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, velvet backend). Command: `bash scripts/lean_verify.sh <file>`.
- atk_1 (prepatch bug: return member.defaultLabel): EXIT=1, unsolved goals @67:26 -> FAILS verify. Reproduces the prepatch bug (matches Solution_prepatch.lean).
- atk_2 (partial-domain: strVal -> []): EXIT=1, unsolved goals @70:26 -> FAILS.
- atk_3 (boundary/off-by: intVal n -> toString (n+1)): EXIT=1, unsolved goals @70:26 -> FAILS.
- atk_4 (control-flow-effect: (renderValue member.value).reverse): EXIT=1, unsolved goals @67:26 -> FAILS.
- atk_5 (ungrounded-oracle echo: defaultLabel ++ renderValue member.value): EXIT=1, unsolved goals @67:26 -> FAILS.
- atk_6 (sign-drop boundary: intVal n -> toString (Int.natAbs n)): EXIT=1, unsolved goals @70:26 -> FAILS.
- echo_verify (gold-behavior written as explicit match dispatch): EXIT=0 -> VERIFIES. This is the only verifying wrong-impl candidate; behaviorally identical to gold.
- pos_control (renderValue member.value): EXIT=0 -> VERIFIES (positive control OK).
All six wrong-behavior impls fail with genuine 'unsolved goals' (postcondition violation), not syntax errors -> spec discriminates correctly. Verifications launched concurrently in two background batches of 4 (<=4 at a time).

RESOLVE (protocol step 2): echo_verify is the sole verifying wrong impl. Its faithful refined patch equals the gold patch (str(self.value)). Materialized to echo_verify.patch.diff and executed via swebench_unified.harness.run_resolve('django__django-11964', ...): COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. Therefore verify=>correct holds for the only verifying candidate; no verifying impl's patch fails to resolve.

**VERDICT:** SOUND. >=5 distinct attacks run (7 total incl. prepatch + echo), none breaks the spec; the one verifying candidate's faithful patch resolves. (Note: recorded meta.json G-EQ status was 'fail: INCONCLUSIVE - 2 attacks inconclusive' from a prior pass that could not exec real Choices locally / didn't complete resolve; this pass completed the resolve run and reaches a determinate SOUND.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec(Solution, Solution_prepatch, velvet)=True). Real callee at base_commit is Choices.`__str__` = `return str(self.value)`. Model postcondition `out = renderValue member.value` (renderValue intVal n = (toString n).toList; renderValue strVal s = s) plus two payload-specialized ensures. Empirically compared model to the REAL callee on int payloads {0,1,-1,10,-123456,±10^25} and str payloads {'', 'FR', 'MyChoice.FIRST_CHOICE', 'é•', '0', '-5'}: all agree. Verified Lean Int.toString == Python str(int) on 0/negatives/2^63-1/±10^40 (no leading zeros, no '+', arbitrary precision, leading '-'); str payload is pure identity on both sides. No radix/format/precision drift. Modeling frame is explicitly scoped to int/str payloads of IntegerChoices/TextChoices (the F2P test_str domain) — exactly where the patched `__str__` is observed; str(int)/str(str) are total stdlib coercions modeled exactly, no consumed axiom (G-AX skip is legitimate). Solution.lean elaborates with its real proof (lean_verify exit 0) so the spec is satisfiable/non-vacuous; prepatch (return member.defaultLabel) is refuted by the same frozen ensures (G-DIFF holds), confirming the postcondition is discriminating rather than vacuously satisfiable. Spec is neither too strong (gold str(self.value) satisfies it) nor drifting; no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True — the four spec regions (axioms/pure/pre/post) are byte-identical; the two files differ only in the elided impl/proof. So the spec view is well-formed and I audited the shared spec view.

The spec encodes exactly the behavior the PUBLIC problem_statement already discloses. Problem statement states: str(my_object.my_str_value) yields 'MyChoice.FIRST_CHOICE' instead of 'first'; that `__str__` fails to return the enum's `value`; and names TextChoices/IntegerChoices and enum.Enum. That IS the discriminating content of the gold edit (def `__str__`(self): return str(self.value)).

Mapping of spec content to public disclosure:
- postconditions `out = renderValue member.value` and the int/str clauses ⇔ 'cast to str returns str(self.value)' — the exact fix the problem asks for.
- renderValue: intVal→decimal text, strVal→identity ⇔ ordinary Python str() over the two payload types (int for IntegerChoices, str for TextChoices) the problem itself names. Standard-library coercion, no gold-specific algorithm.
- Member.defaultLabel = the qualified `Owner.NAME` token (pre-fix enum.Enum.`__str__`) — the buggy behavior the problem statement literally prints ('MyChoice.FIRST_CHOICE'). Comment even cites 'shown in the problem statement'.

No leakage BEYOND problem_statement: the spec discloses no hidden file/symbol (only `__str__` + value, both public), no non-obvious algorithm, no test-specific values, no gold patch text/phrasing. Comments are abstract ('rendered into templates, sent to other systems') and generic Python idiom ('cast to str'), not quotes of the gold hunk or its docstring. The abstraction (Member/MemberValue/renderValue) is modeling scaffolding, not solution disclosure. Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already establishes.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
