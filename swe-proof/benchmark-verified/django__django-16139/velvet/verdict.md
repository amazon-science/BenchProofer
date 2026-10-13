# P2 adversarial audit — django__django-16139

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return "../password/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return "../".toList ++ (toString key).toList ++ "/password/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return "../../".toList ++ (toString key).toList ++ "/passwd/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    if key = 22 then return relativeLink key else return "../password/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return "../../".toList ++ "/password/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return "../../".toList ++ (toString (key + 1)).toList ++ "/password/".toList
     -- impl-end
 
 prove_correct buildRelativeLink by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,7 @@
   ensures link = relativeLink key
   do
     -- impl-start
-    return "../../".toList ++ (toString key).toList ++ "/password/".toList
+    return relativeLink key
     -- impl-end
 
 prove_correct buildRelativeLink by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The integer→text rendering is modeled deeply as
--  `toString`; the placeholder-substitution wrapper is an R-refinement identity
--  on the produced relative URL — see refinement.md / mapping.md. Nothing the
--  proof consumes is left to an axiom, so there is no axiom_check.py and G-AX
--  is skipped.)
-- axioms-end

-- pure-start
/- The relative URL, computed from a record's primary key, that locates that
   record's password-change sub-page from the record's own change page. The
   page is reached by ascending two levels (so the navigation does not depend on
   the identifier under which the change page itself was reached) and then
   descending into the keyed record's password sub-page. The key is rendered in
   its usual decimal text form. The leading and trailing literal segments are
   constant; only the keyed middle segment varies with the input. -/
@[grind] def relativeLink (key : Nat) : List Char :=
  "../../".toList ++ (toString key).toList ++ "/password/".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relative link for a record identified by `key`. The result must be
   exactly the two-levels-up, key-indexed password sub-page URL, so that the
   link resolves to the same target regardless of the identifier the record's
   change page was addressed by. `key` is a read-only input and is not mutated
   (directive 5). -/
method buildRelativeLink (key : Nat) return (link : List Char)
  ensures link = relativeLink key
  do
    -- impl-start
    return "../../".toList ++ (toString key).toList ++ "/password/".toList
    -- impl-end

prove_correct buildRelativeLink by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: postcondition `link = relativeLink key` is a TOTAL equality over all Nat, with the changed op modeled DEEPLY (relativeLink = "../../" ++ toString key ++ "/password/"), no axioms (G-AX skip correct). All 7 same-spec attacks (same_spec=True each) verified via lean_verify.sh (proj root, `bash scripts/lean_verify.sh <f>`), run concurrently in 2 batches of 4.

RESULTS: pos.lean EXIT=0 (positive control verifies). prepatch.lean EXIT=1 (prepatch bug reproduced: "../password/".toList != relativeLink key). atk_1 (prepatch keyless one-level) EXIT=1. atk_2 (one-level ascent, off-by-one) EXIT=1. atk_3 (wrong trailing /passwd/) EXIT=1. atk_4 (partial-domain, correct only key=22) EXIT=1. atk_5 (ungrounded, key dropped) EXIT=1. atk_6 (control-flow/off-by-one key+1) EXIT=1. atk_7 (ungrounded-oracle echo `return relativeLink key`) EXIT=0 — ONLY verifying wrong impl.

atk_7 is a syntactic echo of the deep model, behaviourally identical to gold. Its faithful refined patch = gold format-argument expr (gold patch verbatim). MATERIALIZED at atk_7.patch and RUN through official harness: run_resolve('django__django-16139', patch) -> RESOLVED=True, note='resolved'. Command: python -c "from swebench_unified.harness import run_resolve; ..." run_id sbu-audit-atk7-16139. The sole verifying candidate RESOLVES => no verify-not-correct break.

refinement.md audit: legs A1(R int<->Nat), A2(I), A3(R str(pk)<->toString), A4(I), A5(R str.format identity into UNCHANGED help_text template). No kind-3 legs, no axioms. A-leg correspondence verified against patch.diff: only the .format(...) argument changes; help_text template byte-identical pre/post; str(pk)/toString render identical decimal glyphs; pk is non-negative AutoField int <-> Nat. Correspondence holds. atk_1-6 exhaust partial-domain/boundary/control-flow/ungrounded classes and all fail, confirming the total-equality spec admits no weaker impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The integer→text rendering is modeled deeply as
--  `toString`; the placeholder-substitution wrapper is an R-refinement identity
--  on the produced relative URL — see refinement.md / mapping.md. Nothing the
--  proof consumes is left to an axiom, so there is no axiom_check.py and G-AX
--  is skipped.)
-- axioms-end

-- pure-start
/- The relative URL, computed from a record's primary key, that locates that
   record's password-change sub-page from the record's own change page. The
   page is reached by ascending two levels (so the navigation does not depend on
   the identifier under which the change page itself was reached) and then
   descending into the keyed record's password sub-page. The key is rendered in
   its usual decimal text form. The leading and trailing literal segments are
   constant; only the keyed middle segment varies with the input. -/
@[grind] def relativeLink (key : Nat) : List Char :=
  "../../".toList ++ (toString key).toList ++ "/password/".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relative link for a record identified by `key`. The result must be
   exactly the two-levels-up, key-indexed password sub-page URL, so that the
   link resolves to the same target regardless of the identifier the record's
   change page was addressed by. `key` is a read-only input and is not mutated
   (directive 5). -/
method buildRelativeLink (key : Nat) return (link : List Char)
  ensures link = relativeLink key
  do
    -- impl-start
    return "../../".toList ++ (toString key).toList ++ "/password/".toList
    -- impl-end

prove_correct buildRelativeLink by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: postcondition `link = relativeLink key` is a TOTAL equality over all Nat, with the changed op modeled DEEPLY (relativeLink = "../../" ++ toString key ++ "/password/"), no axioms (G-AX skip correct). All 7 same-spec attacks (same_spec=True each) verified via lean_verify.sh (proj root, `bash scripts/lean_verify.sh <f>`), run concurrently in 2 batches of 4.

RESULTS: pos.lean EXIT=0 (positive control verifies). prepatch.lean EXIT=1 (prepatch bug reproduced: "../password/".toList != relativeLink key). atk_1 (prepatch keyless one-level) EXIT=1. atk_2 (one-level ascent, off-by-one) EXIT=1. atk_3 (wrong trailing /passwd/) EXIT=1. atk_4 (partial-domain, correct only key=22) EXIT=1. atk_5 (ungrounded, key dropped) EXIT=1. atk_6 (control-flow/off-by-one key+1) EXIT=1. atk_7 (ungrounded-oracle echo `return relativeLink key`) EXIT=0 — ONLY verifying wrong impl.

atk_7 is a syntactic echo of the deep model, behaviourally identical to gold. Its faithful refined patch = gold format-argument expr (gold patch verbatim). MATERIALIZED at atk_7.patch and RUN through official harness: run_resolve('django__django-16139', patch) -> RESOLVED=True, note='resolved'. Command: python -c "from swebench_unified.harness import run_resolve; ..." run_id sbu-audit-atk7-16139. The sole verifying candidate RESOLVES => no verify-not-correct break.

refinement.md audit: legs A1(R int<->Nat), A2(I), A3(R str(pk)<->toString), A4(I), A5(R str.format identity into UNCHANGED help_text template). No kind-3 legs, no axioms. A-leg correspondence verified against patch.diff: only the .format(...) argument changes; help_text template byte-identical pre/post; str(pk)/toString render identical decimal glyphs; pk is non-negative AutoField int <-> Nat. Correspondence holds. atk_1-6 exhaust partial-domain/boundary/control-flow/ungrounded classes and all fail, confirming the total-equality spec admits no weaker impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift audit of django__django-16139 velvet bundle. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet) = True; spec_view is frozen (set_option total/demonic + relativeLink def + method signature/ensures). (2) Solution.lean elaborates cleanly (lean_verify.sh exit 0). (3) Model vs real callee: gold patch changes the .format() argument from "../password/" to f"../../{self.instance.pk}/password/" (forms.py:166, UserChangeForm.__init__). Spec models this as relativeLink key = "../../" ++ (toString key).toList ++ "/password/".toList. Type bijection: self.instance.pk is a non-negative AutoField int <-> Nat; str(pk) <-> toString key produce identical decimal glyph sequences (no sign, no separators, no leading zeros). The str.format substitution into the UNCHANGED help_text template is an R-identity wrapper on the single argument. (4) Fuzzed the transliteration real(pk)="../../"+str(pk)+"/password/" vs model over 200k values (0, small, up to 1e60, seed 16139): ZERO divergences. The spec pins the exact string the real repo produces for every reachable pk on the modeled domain (Nat = non-negative pk) -- neither too strong nor too weak, no drift, no diverging input. Note: the recorded G-PANEL-1 'WEAK: same-spec impl verifies' verdict is an echo-attack artifact of a different attacker role, not a faithfulness/drift defect; per current policy a resolving same-spec impl is not a weakness. It does not bear on G-PANEL-2. No faithfulness break found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True under the velvet backend). Rendered the actual consumer spec view via markers.spec_view: it exposes the pure model `relativeLink key = "../../".toList ++ (toString key).toList ++ "/password/".toList`, the obligation `ensures link = relativeLink key`, and prose describing 'ascending two levels' + 'keyed decimal middle segment' (impl and prove_correct bodies are elided). Every one of these facts is already stated explicitly and verbatim in the PUBLIC problem_statement, which quotes the full gold fix: replace `password.help_text.format("../password/")` with `password.help_text.format(f"../../{self.instance.pk}/password/")`. The problem_statement gives the exact target string, the two-level ascent, and the pk interpolation. The spec view is a faithful transliteration of that public disclosure (int pk -> Nat, str(pk) -> toString) and adds no gold-edit information beyond it. Comparison was made against problem_statement only, NOT hints_text (hints_text is empty here anyway). Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
