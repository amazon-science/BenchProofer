# P2 adversarial audit — sphinx-doc__sphinx-9461

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec ensure #1 `out = annotationTokens firstFlag secondFlag` pins the output over the TOTAL, FINITE Bool x Bool domain (4 combinations, no precondition). Every verifying impl must therefore equal the gold token list on all 4 inputs. All 7 genuinely-wrong impls (partial-domain, prepatch-bug, wrong-order, property-first, boundary/unconditional, swapped-flags, ungrounded-constant) fail lean_verify with unsolved goals (rc=1). The only same-spec VERIFYING attack (atk_echo, `return annotationTokens firstFlag secondFlag`) is a behavioral echo of the gold; its faithful refined patch IS the gold patch, which RESOLVES (run_resolve completed=True, resolved=True, attempts=1, non-flaky). No verifying wrong impl exists whose faithful patch fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -62,7 +62,8 @@
       toks := toks ++ ["abstract"]
     if secondFlag then
       toks := toks ++ ["class"]
-    toks := toks ++ ["property"]
+    if !(firstFlag && secondFlag) then
+      toks := toks ++ ["property"]
     return toks
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -60,8 +60,6 @@
     let mut toks : List String := []
     if firstFlag then
       toks := toks ++ ["abstract"]
-    if secondFlag then
-      toks := toks ++ ["class"]
     toks := toks ++ ["property"]
     return toks
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -58,10 +58,10 @@
   do
     -- impl-start
     let mut toks : List String := []
+    if secondFlag then
+      toks := toks ++ ["class"]
     if firstFlag then
       toks := toks ++ ["abstract"]
-    if secondFlag then
-      toks := toks ++ ["class"]
     toks := toks ++ ["property"]
     return toks
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -57,12 +57,11 @@
   ensures out ≠ [] ∧ out.getLast! = "property"
   do
     -- impl-start
-    let mut toks : List String := []
+    let mut toks : List String := ["property"]
     if firstFlag then
       toks := toks ++ ["abstract"]
     if secondFlag then
       toks := toks ++ ["class"]
-    toks := toks ++ ["property"]
     return toks
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -58,8 +58,7 @@
   do
     -- impl-start
     let mut toks : List String := []
-    if firstFlag then
-      toks := toks ++ ["abstract"]
+    toks := toks ++ ["abstract"]
     if secondFlag then
       toks := toks ++ ["class"]
     toks := toks ++ ["property"]
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -58,9 +58,9 @@
   do
     -- impl-start
     let mut toks : List String := []
+    if secondFlag then
+      toks := toks ++ ["abstract"]
     if firstFlag then
-      toks := toks ++ ["abstract"]
-    if secondFlag then
       toks := toks ++ ["class"]
     toks := toks ++ ["property"]
     return toks
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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -57,13 +57,7 @@
   ensures out ≠ [] ∧ out.getLast! = "property"
   do
     -- impl-start
-    let mut toks : List String := []
-    if firstFlag then
-      toks := toks ++ ["abstract"]
-    if secondFlag then
-      toks := toks ++ ["class"]
-    toks := toks ++ ["property"]
-    return toks
+    return ["abstract", "class", "property"]
     -- impl-end
 
 prove_correct assembleModifierTokens by
```

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The assembled token list is a pure function of two
@@ -57,13 +57,7 @@
   ensures out ≠ [] ∧ out.getLast! = "property"
   do
     -- impl-start
-    let mut toks : List String := []
-    if firstFlag then
-      toks := toks ++ ["abstract"]
-    if secondFlag then
-      toks := toks ++ ["class"]
-    toks := toks ++ ["property"]
-    return toks
+    return annotationTokens firstFlag secondFlag
     -- impl-end
 
 prove_correct assembleModifierTokens by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The assembled token list is a pure function of two
--  independent boolean flags; the only library operation involved is the
--  constant space-join of the assembled list, which is unchanged and identical
--  on both sides (an R/I identity, checked by G-CONF). There is no unchanged
--  library callee whose contract the proof must consume.)
-- axioms-end

-- pure-start
/- The ordered list of optional annotation tokens for a documented entity, built
   from two independent boolean flags plus one always-present trailing token.
   Each flag, when set, contributes exactly one token, placed in a
   predetermined left-to-right order; when unset it contributes nothing. The trailing token is
   always present and always last. The two flags are independent: either, both,
   or neither may be set. -/
def annotationTokens (firstFlag secondFlag : Bool) : List String :=
  (if firstFlag  then ["abstract"] else []) ++
  (if secondFlag then ["class"]    else []) ++
  ["property"]

@[grind] lemma annotationTokens_eq (firstFlag secondFlag : Bool) :
    annotationTokens firstFlag secondFlag =
      (if firstFlag then ["abstract"] else []) ++
      (if secondFlag then ["class"] else []) ++ ["property"] := rfl

/- When the second flag is set, its token "class" is among the produced tokens
   regardless of the first flag. Each flag is observed independently of the
   other. -/
@[grind] lemma annotationTokens_secondFlag_present (firstFlag : Bool) :
    "class" ∈ annotationTokens firstFlag true := by
  unfold annotationTokens
  cases firstFlag <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered annotation-token list for a documented entity from two
   independent boolean flags. Each set flag contributes its own token in a
   predetermined order ahead of the always-present trailing token; the flags are independent
   (both, either, or neither). The flags are read-only inputs (not `mut`): the
   routine assembles a fresh list and mutates nothing (directive 5). -/
method assembleModifierTokens (firstFlag : Bool) (secondFlag : Bool) return (out : List String)
  ensures out = annotationTokens firstFlag secondFlag
  ensures secondFlag = true → "class" ∈ out
  ensures out ≠ [] ∧ out.getLast! = "property"
  do
    -- impl-start
    let mut toks : List String := []
    if firstFlag then
      toks := toks ++ ["abstract"]
    if secondFlag then
      toks := toks ++ ["class"]
    toks := toks ++ ["property"]
    return toks
    -- impl-end

prove_correct assembleModifierTokens by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

same_spec: all 9 attack files (atk_1..7, atk_echo, atk_pc) verified True vs frozen Solution.lean via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

lean_verify.sh (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 (drop 'property' when both flags set; wrong on (T,T)) -> rc=1 REJECTED
- atk_2 (prepatch: no class branch; wrong when secondFlag) -> rc=1 REJECTED
- atk_3 (class before abstract; wrong order on (T,T)) -> rc=1 REJECTED
- atk_4 (property seeded first/front; wrong order) -> rc=1 REJECTED
- atk_5 (abstract unconditional; wrong when firstFlag=false) -> rc=1 REJECTED
- atk_6 (swapped flags: firstFlag->class, secondFlag->abstract) -> rc=1 REJECTED
- atk_7 (ungrounded constant ['abstract','class','property']) -> rc=1 REJECTED
- atk_echo (`return annotationTokens firstFlag secondFlag`) -> rc=0 VERIFIES
- atk_pc / positive control (exact gold impl) -> rc=0 VERIFIES

Step 2 (mandatory resolve of every verifying attack): atk_echo faithful patch materialized It is the gold patch: the modeled site get_signature_prefix reproduced token-for-token by the echo (out = annotationTokens), plus the two unmodeled reflection co-changes verbatim (unchanged by the echo, so faithfully carried). RAN swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9461', patch, run_id='sbu-audit-echo-9461', timeout=3600) via docker -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Log: atk_echo.resolve.log. This is the resolve run the prior audit left uncompleted (recorded fail-closed INCONCLUSIVE); it now completes and resolves.

Refinement.md audit (A legs / model<->patch correspondence): bundle has NO axioms and NO deep-model references (axiom_check.py status=skip 'no-axioms'; mapping.md sec3.1). Legs A1-A7 are all R (bool<->Bool dict-membership; List String<->joined prefix string, A7) or I (concrete list-append ops A3-A6). NO kind-3 (inexpressible-changed-op) leg. The R/I token-assembly + fixed space-join correspondence is exhaustively confirmed by G-PANEL-2 (all 4 finite inputs, 0 disagreements) and by G-CONF. The two unmodeled co-changed files (sphinx/util/inspect.py, sphinx/ext/autodoc/__init__.py) are runtime descriptor/MRO introspection outside Velvet's fragment and are correctly documented (not axiomatized, per directive 7); patch.diff ships them verbatim so all three F2P tests resolve.

Why SOUND: ensure #1 constrains the modeled function pointwise over its entire finite domain => verify => behavioral equality with gold rendering => faithful patch = gold => resolves. The single verifying attack's materialized faithful patch was RUN and RESOLVED. >=5 distinct wrong impls attacked and all rejected. verify=>correct holds for this bundle. (Echo-attack per current policy is not a weakness: same-spec verifying echo whose refined patch resolves.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec ensure #1 `out = annotationTokens firstFlag secondFlag` pins the output over the TOTAL, FINITE Bool x Bool domain (4 combinations, no precondition). Every verifying impl must therefore equal the gold token list on all 4 inputs. All 7 genuinely-wrong impls (partial-domain, prepatch-bug, wrong-order, property-first, boundary/unconditional, swapped-flags, ungrounded-constant) fail lean_verify with unsolved goals (rc=1). The only same-spec VERIFYING attack (atk_echo, `return annotationTokens firstFlag secondFlag`) is a behavioral echo of the gold; its faithful refined patch IS the gold patch, which RESOLVES (run_resolve completed=True, resolved=True, attempts=1, non-flaky). No verifying wrong impl exists whose faithful patch fails to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The assembled token list is a pure function of two
--  independent boolean flags; the only library operation involved is the
--  constant space-join of the assembled list, which is unchanged and identical
--  on both sides (an R/I identity, checked by G-CONF). There is no unchanged
--  library callee whose contract the proof must consume.)
-- axioms-end

-- pure-start
/- The ordered list of optional annotation tokens for a documented entity, built
   from two independent boolean flags plus one always-present trailing token.
   Each flag, when set, contributes exactly one token, placed in a
   predetermined left-to-right order; when unset it contributes nothing. The trailing token is
   always present and always last. The two flags are independent: either, both,
   or neither may be set. -/
def annotationTokens (firstFlag secondFlag : Bool) : List String :=
  (if firstFlag  then ["abstract"] else []) ++
  (if secondFlag then ["class"]    else []) ++
  ["property"]

@[grind] lemma annotationTokens_eq (firstFlag secondFlag : Bool) :
    annotationTokens firstFlag secondFlag =
      (if firstFlag then ["abstract"] else []) ++
      (if secondFlag then ["class"] else []) ++ ["property"] := rfl

/- When the second flag is set, its token "class" is among the produced tokens
   regardless of the first flag. Each flag is observed independently of the
   other. -/
@[grind] lemma annotationTokens_secondFlag_present (firstFlag : Bool) :
    "class" ∈ annotationTokens firstFlag true := by
  unfold annotationTokens
  cases firstFlag <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered annotation-token list for a documented entity from two
   independent boolean flags. Each set flag contributes its own token in a
   predetermined order ahead of the always-present trailing token; the flags are independent
   (both, either, or neither). The flags are read-only inputs (not `mut`): the
   routine assembles a fresh list and mutates nothing (directive 5). -/
method assembleModifierTokens (firstFlag : Bool) (secondFlag : Bool) return (out : List String)
  ensures out = annotationTokens firstFlag secondFlag
  ensures secondFlag = true → "class" ∈ out
  ensures out ≠ [] ∧ out.getLast! = "property"
  do
    -- impl-start
    let mut toks : List String := []
    if firstFlag then
      toks := toks ++ ["abstract"]
    if secondFlag then
      toks := toks ++ ["class"]
    toks := toks ++ ["property"]
    return toks
    -- impl-end

prove_correct assembleModifierTokens by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

same_spec: all 9 attack files (atk_1..7, atk_echo, atk_pc) verified True vs frozen Solution.lean via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.

lean_verify.sh (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 (drop 'property' when both flags set; wrong on (T,T)) -> rc=1 REJECTED
- atk_2 (prepatch: no class branch; wrong when secondFlag) -> rc=1 REJECTED
- atk_3 (class before abstract; wrong order on (T,T)) -> rc=1 REJECTED
- atk_4 (property seeded first/front; wrong order) -> rc=1 REJECTED
- atk_5 (abstract unconditional; wrong when firstFlag=false) -> rc=1 REJECTED
- atk_6 (swapped flags: firstFlag->class, secondFlag->abstract) -> rc=1 REJECTED
- atk_7 (ungrounded constant ['abstract','class','property']) -> rc=1 REJECTED
- atk_echo (`return annotationTokens firstFlag secondFlag`) -> rc=0 VERIFIES
- atk_pc / positive control (exact gold impl) -> rc=0 VERIFIES

Step 2 (mandatory resolve of every verifying attack): atk_echo faithful patch materialized It is the gold patch: the modeled site get_signature_prefix reproduced token-for-token by the echo (out = annotationTokens), plus the two unmodeled reflection co-changes verbatim (unchanged by the echo, so faithfully carried). RAN swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9461', patch, run_id='sbu-audit-echo-9461', timeout=3600) via docker -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Log: atk_echo.resolve.log. This is the resolve run the prior audit left uncompleted (recorded fail-closed INCONCLUSIVE); it now completes and resolves.

Refinement.md audit (A legs / model<->patch correspondence): bundle has NO axioms and NO deep-model references (axiom_check.py status=skip 'no-axioms'; mapping.md sec3.1). Legs A1-A7 are all R (bool<->Bool dict-membership; List String<->joined prefix string, A7) or I (concrete list-append ops A3-A6). NO kind-3 (inexpressible-changed-op) leg. The R/I token-assembly + fixed space-join correspondence is exhaustively confirmed by G-PANEL-2 (all 4 finite inputs, 0 disagreements) and by G-CONF. The two unmodeled co-changed files (sphinx/util/inspect.py, sphinx/ext/autodoc/__init__.py) are runtime descriptor/MRO introspection outside Velvet's fragment and are correctly documented (not axiomatized, per directive 7); patch.diff ships them verbatim so all three F2P tests resolve.

Why SOUND: ensure #1 constrains the modeled function pointwise over its entire finite domain => verify => behavioral equality with gold rendering => faithful patch = gold => resolves. The single verifying attack's materialized faithful patch was RUN and RESOLVED. >=5 distinct wrong impls attacked and all rejected. verify=>correct holds for this bundle. (Echo-attack per current policy is not a weakness: same-spec verifying echo whose refined patch resolves.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled site: PyProperty.get_signature_prefix (sphinx/domains/python.py) post-patch. The gold-patched function builds prefix=[] then appends 'abstract' iff 'abstractmethod' in options, 'class' iff 'classmethod' in options, then always 'property', returning ' '.join(prefix)+' '. The Lean model annotationTokens firstFlag secondFlag = (if firstFlag then ["abstract"] else []) ++ (if secondFlag then ["class"] else []) ++ ["property"] reproduces exactly this token list on the entire input domain, which is the four boolean combinations of the two dict-membership flags: (F,F)->[property], (T,F)->[abstract,property], (F,T)->[class,property], (T,T)->[abstract,class,property]. All four agree with the real repo. The space-join+trailing-space is an unchanged, identical-on-both-sides R/I trailing op (G-CONF compares the joined strings), so no divergence is introduced there. The auxiliary ensures clauses (secondFlag=true -> "class" in out; out != [] and out.getLast! = "property") are true consequences of the real patched behavior, not spec over-strengthening — they hold for the real function on every input. No input exists on which the modeled function disagrees with the real callee. Verified: same_spec(Solution, Solution_prepatch, VelvetBackend.language)=True (spec region byte-identical), Solution.lean elaborates cleanly (lean_verify exit 0), and the prepatch skeleton correctly fails on the secondFlag clauses (G-DIFF sees the real bug: dropped :classmethod: modifier). Spec is neither too strong nor drifting; it is faithful to the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "Scope of what is disclosed":

> The spec view discloses: an ordered list of optional annotation tokens built from two independent boolean flags — the first contributes `"abstract"`, the second contributes `"class"`, with an always-present trailing `"property"`, in the fixed order abstract → class → property. Nothing about the patched files, the `get_signature_prefix` / `PyProperty` / `PropertyDocumenter` / `isclassmethod` / `getdoc` symbols, the `self.options` dict-membership mechanism, the `:classmethod:` directive flag, the descriptor/MRO introspection, or the three-file multi-site refactor is named in the spec view.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "What leaks, and why it is unavoidable":

> A **faithful** spec must pin the rendering-half discriminator (`secondFlag → "class" ∈ out`, the abstract→class→property order, trailing `"property"`), because `test_pyproperty` asserts the rendered string `"class property "` exactly. A spec built from the public issue's stated expectation ("documented appropriately") cannot model this site at all — it names neither the rendered prefix, nor the `"class"` token, nor the `:classmethod:` directive flag, nor any ordering. Such a non-pinning spec would admit the prepatch impl (drop the second flag) which verifies yet fails the F2P `test_pyproperty` — i.e. it would violate G-EQ / `verify ⟹ correct`.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `d65115e40019`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
problem_statement token scan: 'prefix' 0×, 'signature'/'get_signature_prefix' 0×, ':classmethod:' 0×, 'order' 0×, and no statement that the rendered prefix should contain a 'class' token or follow the order abstract→class→property. The lone 'Some class property.' occurrence is a free-text docstring inside the bug-repro code sample, not a spec of the rendered signature prefix. Yet Solution.lean discloses the exact gold rendering discriminator: annotationTokens = (if firstFlag ["abstract"]) ++ (if secondFlag ["class"]) ++ ["property"] (L24-27), ensures secondFlag=true → "class" ∈ out (L56, the NEW behavior the gold adds), and ensures out.getLast! = "property" (L57, trailing kind token). None of these behavioral facts — that the classmethod flag emits a 'class' token, the canonical abstract→class→property order, the always-trailing 'property' — are derivable from the public problem_statement, which frames the issue purely as a discovery/docstring-extraction symptom ('do not get documented', type(...) returns wrong type, 'documented appropriately').
```

Public PS (verified from data/swe_bench_verified/test.jsonl) is entirely the recognition/__doc__-extraction half of the gold. The modeled site is the rendering half (PyProperty.get_signature_prefix), which the PS never raises. A faithful spec of the modeled site MUST pin the class-token/order discriminator (else the prepatch — no second-flag branch — verifies yet fails F2P test_pyproperty, violating G-EQ), so the leak is behavioral/semantic and unavoidable, not narration. This matches the in-bundle RELAXED_LEAKAGE.md analysis and meta.json gates.G-LEAK.status='relaxed'. LEXICAL screen note: the spec view uses only generic identifiers (annotationTokens, assembleModifierTokens, firstFlag, secondFlag) and names no patched path/symbol (get_signature_prefix, PyProperty, classmethod, self.options, :classmethod:), so a purely lexical G-LEAK screen passes; the leak is semantic. Per 2026-08-06/07 policy, G-PANEL-3 on an accepted RELAXED_LEAKAGE bundle records pass+note rather than fail — but the honest attacker finding is that gold-edit behavior IS leaked beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.