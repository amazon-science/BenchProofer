# P2 adversarial audit — django__django-14534

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return some ("id_" ++ name ++ "_" ++ index)
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return attrs.lookup "name"
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return none
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return (if name = "" then none else attrs.lookup "id")
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return attrs.reverse.lookup "id"
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return (attrs.head?).map (fun p => p.2)
     -- impl-end
 
 prove_correct labelIdentifier by
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
 -- (No consumed axioms. The label identifier is read directly from the widget's
@@ -56,7 +56,7 @@
   ensures out = recordedId attrs
   do
     -- impl-start
-    return attrs.lookup "id"
+    return some ((attrs.lookup "id").getD "")
     -- impl-end
 
 prove_correct labelIdentifier by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The label identifier is read directly from the widget's
--  own recorded attributes by a total association lookup; that lookup is an
--  ordinary concrete operation (I) bridged by the type bijection (R) in
--  mapping.md, mechanically refuted by conformance_check.py (G-CONF). No callee
--  is over-approximated, so no `axiom` is owed (directive 7).)
-- axioms-end

-- pure-start
/- The recorded attributes of a single rendered widget: an ordered association
   of string attribute names to string values. Modeled as an ordered list of
   key/value pairs (mapping.md §2). A given attribute name occurs at most once,
   mirroring a mapping keyed by attribute name. -/
abbrev Attrs := List (String × String)

/- The identifier recorded for a widget under its `"id"` attribute, if one was
   recorded — otherwise absent. This is a total lookup over the recorded
   attributes: it yields the recorded value when an `"id"` attribute is present,
   and the absent value when it is not. -/
def recordedId (attrs : Attrs) : Option String :=
  attrs.lookup "id"

@[grind] lemma recordedId_eq (attrs : Attrs) :
    recordedId attrs = attrs.lookup "id" := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The identifier to use when rendering a label that points at one rendered
   widget. The desired behavior is that this identifier is exactly the one
   already recorded in the widget's own attributes under `"id"` — the identifier
   the widget itself was (or would be) rendered with — and is absent precisely
   when no such identifier was recorded. It must therefore reflect whatever
   identifier the surrounding rendering recorded for this widget (including any
   caller-chosen prefix), rather than being synthesized independently from the
   widget's other recorded data.

   `name`, `index`, and `attrs` are the widget's recorded data (its field name,
   its position among sibling widgets, and its recorded attributes); all three
   are read-only — none is declared `mut` (directive 5). The result depends only
   on the recorded attributes. -/
method labelIdentifier (name : String) (index : String) (attrs : Attrs)
    return (out : Option String)
  ensures out = recordedId attrs
  do
    -- impl-start
    return attrs.lookup "id"
    -- impl-end

prove_correct labelIdentifier by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec: method labelIdentifier (name index : String) (attrs : Attrs) return (out : Option String), ensures out = recordedId attrs, with recordedId attrs = attrs.lookup "id" (deep model, no precondition, no axioms; G-AX=skip). This is a TOTAL exact-equality postcondition over the entire domain with a scalar Option return, leaving zero slack.

Protocol: all files built by copying Solution.lean and editing ONLY the impl region; same_spec(velvet) = True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec). Verified concurrently in two batches of 4 via scripts/lean_verify.sh (300s cap).

Commands: cd && bash scripts/lean_verify.sh atk_N.lean

Results (exit codes): atk_1..atk_7 = 1 (fail to verify); pos_control = 0 (verifies).

Attack families (all DISTINCT, all leave an uncloseable prove_correct goal):
- atk_1: prepatch bug — some ("id_"++name++"_"++index), synthesized id ignoring attrs (reproduces Solution_prepatch.lean; goal some(...) = recordedId attrs). prepatch_reproduced=true.
- atk_2: ungrounded-oracle echo — attrs.lookup "name" (wrong key).
- atk_3: constant/partial — none.
- atk_4: control-flow-effect — branches on read-only param name (if name="" then none else lookup "id").
- atk_5: ordering/boundary — attrs.reverse.lookup "id".
- atk_6: boundary/first-elem — (attrs.head?).map (·.2).
- atk_7: Option-boundary — some ((lookup "id").getD ""), collapses the none case to some "".

No wrong impl verifies, so there is NO verifying-wrong-impl whose materialized faithful patch could be run through run_resolve — the verify⇏correct condition cannot be exhibited. patches={} accordingly (nothing to materialize/resolve).

refinement.md audit: legs A1 (R: self.data['attrs'] dict ↔ List(String×String); .get↔List.lookup), A2 (R: read-only name/index identity), A3 (I: single lookup "id"). No kind-3 (inexpressible-changed-op) legs. No consumed/reference axioms (recordedId is a deep I/R model, not an axiom; G-AX=skip per mapping.md §3), so there are no A-legs whose callee correspondence could drift. Correspondence to boundfield.py:280 (self.data['attrs'].get('id')) holds. conformance_check.py seed 14534 differential-tests the same R/I shadow.

SOUND: ≥5 distinct attacks run, none verifies, positive control verifies, prepatch reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
-- (No consumed axioms. The label identifier is read directly from the widget's
--  own recorded attributes by a total association lookup; that lookup is an
--  ordinary concrete operation (I) bridged by the type bijection (R) in
--  mapping.md, mechanically refuted by conformance_check.py (G-CONF). No callee
--  is over-approximated, so no `axiom` is owed (directive 7).)
-- axioms-end

-- pure-start
/- The recorded attributes of a single rendered widget: an ordered association
   of string attribute names to string values. Modeled as an ordered list of
   key/value pairs (mapping.md §2). A given attribute name occurs at most once,
   mirroring a mapping keyed by attribute name. -/
abbrev Attrs := List (String × String)

/- The identifier recorded for a widget under its `"id"` attribute, if one was
   recorded — otherwise absent. This is a total lookup over the recorded
   attributes: it yields the recorded value when an `"id"` attribute is present,
   and the absent value when it is not. -/
def recordedId (attrs : Attrs) : Option String :=
  attrs.lookup "id"

@[grind] lemma recordedId_eq (attrs : Attrs) :
    recordedId attrs = attrs.lookup "id" := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The identifier to use when rendering a label that points at one rendered
   widget. The desired behavior is that this identifier is exactly the one
   already recorded in the widget's own attributes under `"id"` — the identifier
   the widget itself was (or would be) rendered with — and is absent precisely
   when no such identifier was recorded. It must therefore reflect whatever
   identifier the surrounding rendering recorded for this widget (including any
   caller-chosen prefix), rather than being synthesized independently from the
   widget's other recorded data.

   `name`, `index`, and `attrs` are the widget's recorded data (its field name,
   its position among sibling widgets, and its recorded attributes); all three
   are read-only — none is declared `mut` (directive 5). The result depends only
   on the recorded attributes. -/
method labelIdentifier (name : String) (index : String) (attrs : Attrs)
    return (out : Option String)
  ensures out = recordedId attrs
  do
    -- impl-start
    return attrs.lookup "id"
    -- impl-end

prove_correct labelIdentifier by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec: method labelIdentifier (name index : String) (attrs : Attrs) return (out : Option String), ensures out = recordedId attrs, with recordedId attrs = attrs.lookup "id" (deep model, no precondition, no axioms; G-AX=skip). This is a TOTAL exact-equality postcondition over the entire domain with a scalar Option return, leaving zero slack.

Protocol: all files built by copying Solution.lean and editing ONLY the impl region; same_spec(velvet) = True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec). Verified concurrently in two batches of 4 via scripts/lean_verify.sh (300s cap).

Commands: cd && bash scripts/lean_verify.sh atk_N.lean

Results (exit codes): atk_1..atk_7 = 1 (fail to verify); pos_control = 0 (verifies).

Attack families (all DISTINCT, all leave an uncloseable prove_correct goal):
- atk_1: prepatch bug — some ("id_"++name++"_"++index), synthesized id ignoring attrs (reproduces Solution_prepatch.lean; goal some(...) = recordedId attrs). prepatch_reproduced=true.
- atk_2: ungrounded-oracle echo — attrs.lookup "name" (wrong key).
- atk_3: constant/partial — none.
- atk_4: control-flow-effect — branches on read-only param name (if name="" then none else lookup "id").
- atk_5: ordering/boundary — attrs.reverse.lookup "id".
- atk_6: boundary/first-elem — (attrs.head?).map (·.2).
- atk_7: Option-boundary — some ((lookup "id").getD ""), collapses the none case to some "".

No wrong impl verifies, so there is NO verifying-wrong-impl whose materialized faithful patch could be run through run_resolve — the verify⇏correct condition cannot be exhibited. patches={} accordingly (nothing to materialize/resolve).

refinement.md audit: legs A1 (R: self.data['attrs'] dict ↔ List(String×String); .get↔List.lookup), A2 (R: read-only name/index identity), A3 (I: single lookup "id"). No kind-3 (inexpressible-changed-op) legs. No consumed/reference axioms (recordedId is a deep I/R model, not an axiom; G-AX=skip per mapping.md §3), so there are no A-legs whose callee correspondence could drift. Correspondence to boundfield.py:280 (self.data['attrs'].get('id')) holds. conformance_check.py seed 14534 differential-tests the same R/I shadow.

SOUND: ≥5 distinct attacks run, none verifies, positive control verifies, prepatch reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): no defect found. 

SPEC REGION: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — axioms/pure/pre/post + method signature + `ensures out = recordedId attrs` are byte-identical; only the impl region differs. Spec is frozen.

REAL CALLEE: verified in the base-commit worktree (django/forms/boundfield.py:264-265) that pre-patch BoundWidget.id_for_label returns `'id_%s_%s' % (self.data['name'], self.data['index'])`; patch.diff is the verbatim gold hunk replacing it with `return self.data['attrs'].get('id')`.

MODELED FUNCTION: labelIdentifier(name, index, attrs) with ensures `out = recordedId attrs` where `recordedId attrs = attrs.lookup "id"`. This is an EXACT transliteration of post-patch `self.data['attrs'].get('id')` under the mapping.md §2 bijection (dict[str,str] ↔ ordered assoc list with at-most-once key; dict.get('id') some v/None ↔ List.lookup "id" some v/none; Option↔None). No over/under-approximation: no axiom, the changed read is a total concrete lookup (I-tag).

### Checks performed
- Solution.lean verifies: lean_verify.sh exit 0.
- Solution_prepatch.lean FAILS: unsolved goal `some ("id_" ++ name ++ "_" ++ index) = List.lookup "id" attrs` (spec is strong enough to reject the synthesized-id pre-patch behavior; G-DIFF holds).
- G-CONF conformance_check.py: 0 disagreements over 100,006 inputs (seed 14534), covering recorded-id with/without caller prefixes, index-bearing ids, absent-id (→None), and value-mismatch cases.

Why no diverging input exists: the gold patch body `attrs.get('id')` satisfies `out = attrs.lookup "id"` on every input in the abstraction domain; name/index are carried in the signature but not consulted, matching the real post-patch behavior which depends only on attrs. The duplicate-key edge case is handled consistently (List.lookup first-match ↔ attrs_to_dict setdefault first-match). The spec is neither too strong (gold satisfies it everywhere) nor drifting (matches real callee exactly). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: boundfield.py id_for_label returns self.data['attrs'].get('id') replacing 'id_%s_%s' % (name, index). Mechanical checks: leakage.screen over the velvet spec view returns passed=True (no hard failures, no warnings); same_spec(Solution.lean, Solution_prepatch.lean)=True, so the spec region (method signature, `ensures out = recordedId attrs`, pure `Attrs`/`recordedId`) is byte-identical pre/post-patch — the discriminator lives entirely in the elided impl/proof, not the spec view. Semantic review vs. problem_statement ONLY (not hints): the public problem_statement already contains the entire fix verbatim ('widget[\'attrs\'][\'id\'] contains the id we would like to use' and 'By changing the code ... to return self.data[\'attrs\'][\'id\'] that function behaves as expected'), including the buggy synthesized form. The spec view's postcondition (return the recorded "id" attribute; absent => none) and the abstract comment about reflecting the recorded identifier including caller-chosen prefix reveal nothing about the gold edit beyond that public content. No patched repo symbol echoed (uses labelIdentifier/recordedId/Attrs, not id_for_label), no patched file path, no diff markers, no bug/fix narration terms. The .get('id') None-on-absent refinement is generic desired-behavior expressed in the postcondition, not a reproduction of the diff. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
