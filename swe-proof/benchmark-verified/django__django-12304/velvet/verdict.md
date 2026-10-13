# P2 adversarial audit — django__django-12304

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None found. All 7 same-spec wrong impls FAIL Velvet verification (exit 1); the correct positive control verifies (exit 0). No verifying wrong impl exists, so no faithful refined patch needed to be materialized/resolve-run (that obligation triggers only for verifying wrong impls).
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    return built
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    if built.valueToLabel = [] then return { built with doNotCallInTemplates := true } else return built
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    return { doNotCallInTemplates := true, valueToLabel := [] }
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    return { built with doNotCallInTemplates := false }
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    return { built with doNotCallInTemplates := built.doNotCallInTemplates }
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    let _tmp := { built with doNotCallInTemplates := true }; return built
     -- impl-end
 
 prove_correct publishChoicesClass by
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
 -- (No axiomatized callees. The constructor's effect is modeled directly: it
@@ -61,7 +61,7 @@
   ensures out.valueToLabel = built.valueToLabel
   do
     -- impl-start
-    return { built with doNotCallInTemplates := true }
+    return { built with doNotCallInTemplates := (built.valueToLabel.length == 0) }
     -- impl-end
 
 prove_correct publishChoicesClass by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor's effect is modeled directly: it
--  sets one boolean class flag and leaves the rest of the constructed class
--  untouched. No outside callee's behavior is assumed or pinned.)
-- axioms-end

-- pure-start
/- The observable part of an enumerated-choices class as built by its
   constructor, abstracted to the two observations that matter here:

   - `doNotCallInTemplates` — the boolean class flag a template engine reads to
     decide whether a value that happens to be callable should be invoked with
     no arguments during variable resolution, or left as-is. When this flag is
     true the engine must NOT auto-call the class; when false (the default for
     an arbitrary callable) the engine would call it.
   - `valueToLabel` — the value→label association the constructor builds for the
     class (each enumerated value paired with its display label). It is the rest
     of the constructed state and is what later attribute access on members
     depends on; the construction step under spec must leave it intact.

   Only these touched/observed fields are carried; the bijection to the real
   class object is in mapping.md §2. -/
structure ChoicesClass where
  doNotCallInTemplates : Bool
  valueToLabel : List (Int × List Char)
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The final step of building an enumerated-choices class. The class arrives
   with its value→label association already assembled (`built`); this step
   produces the class as actually published.

   For an enumerated-choices class to be usable as a plain value in a template —
   compared against, or having its members' attributes read — the engine must be
   told NOT to invoke the class (it is callable, and a template engine calls a
   bare callable with no arguments, which here fails). The published class must
   therefore carry `doNotCallInTemplates = true`.

   At the same time this step must not disturb anything else the class already
   holds: the value→label association assembled earlier must survive unchanged,
   so member-attribute access keeps working. `built` is read-only (not `mut`);
   the step constructs the published class from it without mutating it
   (directive 5). The two guarantees together pin the behavior the issue
   demands: the flag is set AND the rest of the construction is preserved. -/
method publishChoicesClass (built : ChoicesClass) return (out : ChoicesClass)
  ensures out.doNotCallInTemplates = true
  ensures out.valueToLabel = built.valueToLabel
  do
    -- impl-start
    return { built with doNotCallInTemplates := true }
    -- impl-end

prove_correct publishChoicesClass by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

A-leg focus. Bundle declares NO axiom and NO A-reference (Solution.lean axioms block is a comment only; mapping.md §3 = 'None'; G-AX correctly a skip). refinement.md legs A1(R)/A2(I)/A3(I+R)/A4(R) all R or I — no kind-3. Correspondence holds: A2 == the added assignment cls.do_not_call_in_templates=True (enums.py:34); A4's claim that enum.unique(cls) is identity on modeled attributes is correct (raises only on duplicate enum values, absent in F2P fixtures; sets no attribute).

Why SOUND / no verify⇒correct gap: ChoicesClass has EXACTLY two fields and BOTH are pinned by the two postconditions (out.doNotCallInTemplates=true AND out.valueToLabel=built.valueToLabel). This makes the spec maximally tight — any verifying impl is forced to emit exactly the gold record. No slack for a wrong-but-verifying impl.

Same-spec: all 7 attacks + pos_control return same_spec=True (velvet backend, swebench_unified.markers.same_spec).

Attacks (path | impl body | verify exit | blocking goal), verified via `bash scripts/lean_verify.sh <path>`, run concurrently ≤4 at a time:
- pos_control.lean | `{ built with doNotCallInTemplates := true }` | exit 0 VERIFIES (positive control).
- atk_1.lean (prepatch bug) | `return built` | exit 1 | ⊢ built.doNotCallInTemplates = true. Byte-identical to Solution_prepatch.lean; matches refinement.md's documented G-DIFF unsolved goal.
- atk_2.lean (partial-domain) | set flag only when valueToLabel=[] else return built | exit 1 | else-branch ⊢ built.doNotCallInTemplates = true.
- atk_3.lean (frame/clobber) | `{ doNotCallInTemplates:=true, valueToLabel:=[] }` | exit 1 | ⊢ [] = built.valueToLabel (frame clause catches map clobber).
- atk_4.lean (flag false) | `{ built with doNotCallInTemplates:=false }` | exit 1 | ⊢ false = true.
- atk_5.lean (ungrounded-oracle echo) | `doNotCallInTemplates := built.doNotCallInTemplates` | exit 1 | ⊢ built.doNotCallInTemplates = true.
- atk_6.lean (control-flow-effect) | compute good _tmp then `return built` | exit 1 | ⊢ built.doNotCallInTemplates = true (effect discarded).
- atk_7.lean (boundary) | `doNotCallInTemplates := (valueToLabel.length == 0)` | exit 1 | ⊢ (built.valueToLabel.length == 0) = true.

≥5 distinct wrong impls run across the taxonomy (prepatch, partial-domain, frame/boundary, control-flow-effect, ungrounded echo, wrong-constant); none verifies; positive control verifies. No resolve run was owed because no wrong impl verified.

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
None found. All 7 same-spec wrong impls FAIL Velvet verification (exit 1); the correct positive control verifies (exit 0). No verifying wrong impl exists, so no faithful refined patch needed to be materialized/resolve-run (that obligation triggers only for verifying wrong impls).
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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constructor's effect is modeled directly: it
--  sets one boolean class flag and leaves the rest of the constructed class
--  untouched. No outside callee's behavior is assumed or pinned.)
-- axioms-end

-- pure-start
/- The observable part of an enumerated-choices class as built by its
   constructor, abstracted to the two observations that matter here:

   - `doNotCallInTemplates` — the boolean class flag a template engine reads to
     decide whether a value that happens to be callable should be invoked with
     no arguments during variable resolution, or left as-is. When this flag is
     true the engine must NOT auto-call the class; when false (the default for
     an arbitrary callable) the engine would call it.
   - `valueToLabel` — the value→label association the constructor builds for the
     class (each enumerated value paired with its display label). It is the rest
     of the constructed state and is what later attribute access on members
     depends on; the construction step under spec must leave it intact.

   Only these touched/observed fields are carried; the bijection to the real
   class object is in mapping.md §2. -/
structure ChoicesClass where
  doNotCallInTemplates : Bool
  valueToLabel : List (Int × List Char)
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The final step of building an enumerated-choices class. The class arrives
   with its value→label association already assembled (`built`); this step
   produces the class as actually published.

   For an enumerated-choices class to be usable as a plain value in a template —
   compared against, or having its members' attributes read — the engine must be
   told NOT to invoke the class (it is callable, and a template engine calls a
   bare callable with no arguments, which here fails). The published class must
   therefore carry `doNotCallInTemplates = true`.

   At the same time this step must not disturb anything else the class already
   holds: the value→label association assembled earlier must survive unchanged,
   so member-attribute access keeps working. `built` is read-only (not `mut`);
   the step constructs the published class from it without mutating it
   (directive 5). The two guarantees together pin the behavior the issue
   demands: the flag is set AND the rest of the construction is preserved. -/
method publishChoicesClass (built : ChoicesClass) return (out : ChoicesClass)
  ensures out.doNotCallInTemplates = true
  ensures out.valueToLabel = built.valueToLabel
  do
    -- impl-start
    return { built with doNotCallInTemplates := true }
    -- impl-end

prove_correct publishChoicesClass by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

A-leg focus. Bundle declares NO axiom and NO A-reference (Solution.lean axioms block is a comment only; mapping.md §3 = 'None'; G-AX correctly a skip). refinement.md legs A1(R)/A2(I)/A3(I+R)/A4(R) all R or I — no kind-3. Correspondence holds: A2 == the added assignment cls.do_not_call_in_templates=True (enums.py:34); A4's claim that enum.unique(cls) is identity on modeled attributes is correct (raises only on duplicate enum values, absent in F2P fixtures; sets no attribute).

Why SOUND / no verify⇒correct gap: ChoicesClass has EXACTLY two fields and BOTH are pinned by the two postconditions (out.doNotCallInTemplates=true AND out.valueToLabel=built.valueToLabel). This makes the spec maximally tight — any verifying impl is forced to emit exactly the gold record. No slack for a wrong-but-verifying impl.

Same-spec: all 7 attacks + pos_control return same_spec=True (velvet backend, swebench_unified.markers.same_spec).

Attacks (path | impl body | verify exit | blocking goal), verified via `bash scripts/lean_verify.sh <path>`, run concurrently ≤4 at a time:
- pos_control.lean | `{ built with doNotCallInTemplates := true }` | exit 0 VERIFIES (positive control).
- atk_1.lean (prepatch bug) | `return built` | exit 1 | ⊢ built.doNotCallInTemplates = true. Byte-identical to Solution_prepatch.lean; matches refinement.md's documented G-DIFF unsolved goal.
- atk_2.lean (partial-domain) | set flag only when valueToLabel=[] else return built | exit 1 | else-branch ⊢ built.doNotCallInTemplates = true.
- atk_3.lean (frame/clobber) | `{ doNotCallInTemplates:=true, valueToLabel:=[] }` | exit 1 | ⊢ [] = built.valueToLabel (frame clause catches map clobber).
- atk_4.lean (flag false) | `{ built with doNotCallInTemplates:=false }` | exit 1 | ⊢ false = true.
- atk_5.lean (ungrounded-oracle echo) | `doNotCallInTemplates := built.doNotCallInTemplates` | exit 1 | ⊢ built.doNotCallInTemplates = true.
- atk_6.lean (control-flow-effect) | compute good _tmp then `return built` | exit 1 | ⊢ built.doNotCallInTemplates = true (effect discarded).
- atk_7.lean (boundary) | `doNotCallInTemplates := (valueToLabel.length == 0)` | exit 1 | ⊢ (built.valueToLabel.length == 0) = true.

≥5 distinct wrong impls run across the taxonomy (prepatch, partial-domain, frame/boundary, control-flow-effect, ungrounded echo, wrong-constant); none verifies; positive control verifies. No resolve run was owed because no wrong impl verified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (swebench_unified.markers.same_spec = True, velvet backend). Solution.lean verifies (lean_verify.sh exit 0). Modeled step publishChoicesClass(built)→out has two postconditions: (1) out.doNotCallInTemplates = true, (2) out.valueToLabel = built.valueToLabel. Verified empirically against the real repo at base_commit 4c1b401e82: pre-patch do_not_call_in_templates is ABSENT (getattr(...,False) falsey ↔ false); post-patch (patch.diff = single line 'cls.do_not_call_in_templates = True') the flag is True UNCONDITIONALLY for every constructed choices class, and cls._value2label_map_ (↔ valueToLabel) is untouched. Both postconditions hold on all inputs — neither over-constrains the real callee. enum.unique(cls) is identity on the modeled fields (raises only on duplicate enum values, out of modeled scope and documented in refinement.md A4). No diverging input exists; the spec faithfully captures real repo behavior on the modeled/observed fields.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True — the impl differs, the spec (signatures/contracts/pure/axioms) is byte-identical. Mechanical G-LEAK screen over the velvet spec view PASSES (no hard failures): no diff markers, no gold-patch line >=8 chars reproduced (the changed line 'cls.do_not_call_in_templates = True' does not appear in the spec view — the model uses camelCase 'doNotCallInTemplates' with a Bool 'true'), no patched file path/module ('django/db/models/enums.py' / 'django.db.models.enums' absent from the spec view — they appear only in mapping.md/refinement.md, which are auditor docs, not the consumer spec view), no changed def/class symbols (patch changes no def/class), and no narration keywords.

Semantic judgment (the part the lexical screen can miss): the spec view's discriminating content is the postcondition 'out.doNotCallInTemplates = true' plus the ChoicesClass.doNotCallInTemplates field. This is precisely the gold edit's effect. BUT the public problem_statement already states the fix verbatim: 'The easy solution would be to declare do_not_call_in_templates = True on the various Choices classes.' The gold discriminator (set the do_not_call_in_templates flag to True) is therefore ALREADY solver-visible via the task itself. Revealing it in the spec is not leakage beyond problem_statement. The frame clause (out.valueToLabel = built.valueToLabel) is a modeling artifact preserving unmodeled state; it localizes nothing about the edit and is not in the gold diff. No file/method/line localization is exposed in the spec view.

Conclusion: NO-LEAKAGE. The spec view does not leak the gold edit beyond what the public problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
