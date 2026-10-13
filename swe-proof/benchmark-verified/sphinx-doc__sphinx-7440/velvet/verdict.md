# P2 adversarial audit — sphinx-doc__sphinx-7440

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
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- PREPATCH BUG: lower-case the key before recording (the .lower() the gold removed)
+    return termText.map Char.toLower
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (control-flow/boundary): identity on empty, upper-cased otherwise
+    if termText = [] then return termText else return termText.map Char.toUpper
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (empty/degenerate oracle): always the empty key
+    return []
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (boundary): drop the first character of the key
+    return termText.drop 1
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (ungrounded-oracle echo): apply the oracle to a lowered input
+    return registeredKey (termText.map Char.toLower)
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (append): append a stray char to the key
+    return termText ++ ['x']
     -- impl-end
 
 prove_correct registerGlossaryName by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,9 +37,8 @@
   ensures out = registeredKey termText
   do
     -- impl-start
-    -- The recorded key is the term's text exactly as written; no case folding
-    -- or other normalization is applied before it is handed to the registry.
-    return registeredKey termText
+    -- WRONG (reverse): report the reversed key
+    return termText.reverse
     -- impl-end
 
 prove_correct registerGlossaryName by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real registration-key computation always terminates
   (it is a straight-line pass of the term's text to the registry), so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The cross-reference key under which a glossary term is recorded in the
   project-wide object registry, and under which that registry later reports it.
   It is the term's own text, taken exactly as written — character-for-character,
   with case preserved. Modeled as the identity on the term text: registering a
   term named `t` records it under `t` and reports it back as `t`.

   The registry itself (record-a-name / enumerate-recorded-names) is an unchanged
   community component; that it stores and yields a name verbatim — case included
   — is its identity-on-name contract, validated against the real component by
   axiom_check.py (G-AX). See mapping.md §3. -/
@[grind] def registeredKey (termText : List Char) : List Char := termText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerGlossaryName (termText : List Char) return (out : List Char)
  ensures out = registeredKey termText
  do
    -- impl-start
    -- The recorded key is the term's text exactly as written; no case folding
    -- or other normalization is applied before it is handed to the registry.
    return registeredKey termText
    -- impl-end

prove_correct registerGlossaryName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec: method registerGlossaryName ensures out = registeredKey termText, with registeredKey := id (identity on the term text). This postcondition FULLY pins the output to the identity for every input; loom_solve discharges only impls behaviorally equal to id. No behaviorally-wrong impl can verify, so verify=>correct is not falsifiable here.

Protocol run (project root; verifier scripts/lean_verify.sh, same_spec via python + swebench_unified.markers.same_spec on backend velvet). All 7 attacks confirmed same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical).

Positive control (verbatim gold impl, return registeredKey termText): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0 (verifies).

Attacks (each `bash scripts/lean_verify.sh .../atk_N.lean`), run concurrently in batches of 4 then 3:
- atk_1 PREPATCH BUG: return termText.map Char.toLower (reproduces removed .lower()) -> EXIT=1 (fails). Prepatch bug reproduced & correctly rejected.
- atk_2 control-flow/partial-domain: id on [] else map Char.toUpper -> EXIT=1 (fails).
- atk_3 degenerate/ungrounded oracle: return [] -> EXIT=1 (fails).
- atk_4 boundary: return termText.drop 1 -> EXIT=1 (fails).
- atk_5 ungrounded-oracle echo: return registeredKey (termText.map Char.toLower) -> EXIT=1 (fails).
- atk_6 append: return termText ++ ['x'] -> EXIT=1 (fails).
- atk_7 reverse: return termText.reverse -> EXIT=1 (fails).

No verifying wrong impl => no faithful refined patch to materialize/run through run_resolve; patches={} accordingly (nothing to resolve). Not INCONCLUSIVE: all >=5 attacks completed verification (no timeouts/exit 124), positive control verified, prepatch reproduced.

Refinement audit (refinement.md): every leg is R (A1: str<->List Char, mapping.md §2), A-reference+I (A2: registeredKey as deep model of the note_object/get_objects registry round-trip, identity-on-name, validated == real callee by G-AX; the impl op returning the verbatim key is concrete-I run through the real make_glossary_term+get_objects by G-CONF), or I (B1: dropped lowercase=True role flag, F2P-test-neutral, contributes no spec clause). No kind-3 (inexpressible-changed-op) legs. No consumed axioms. The one genuinely changed op (which key string is handed to the registry) is modeled deeply, not hidden behind a note_object axiom. Model<->patch correspondence holds: out = termText verbatim (registeredKey=id) <=> gold passes termtext (removal of .lower()); atk_1 is exactly the prepatch termtext.lower() and is rejected, matching the discriminating F2P behavior (TERM2 must register/report as TERM2, not term2).

Verdict: SOUND. No same-spec verifying wrong impl exists (7/7 distinct wrong impls fail), positive control verifies, refinement legs are all R/A-reference/I with sound A-leg correspondence.

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

/- Total correctness: the real registration-key computation always terminates
   (it is a straight-line pass of the term's text to the registry), so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The cross-reference key under which a glossary term is recorded in the
   project-wide object registry, and under which that registry later reports it.
   It is the term's own text, taken exactly as written — character-for-character,
   with case preserved. Modeled as the identity on the term text: registering a
   term named `t` records it under `t` and reports it back as `t`.

   The registry itself (record-a-name / enumerate-recorded-names) is an unchanged
   community component; that it stores and yields a name verbatim — case included
   — is its identity-on-name contract, validated against the real component by
   axiom_check.py (G-AX). See mapping.md §3. -/
@[grind] def registeredKey (termText : List Char) : List Char := termText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerGlossaryName (termText : List Char) return (out : List Char)
  ensures out = registeredKey termText
  do
    -- impl-start
    -- The recorded key is the term's text exactly as written; no case folding
    -- or other normalization is applied before it is handed to the registry.
    return registeredKey termText
    -- impl-end

prove_correct registerGlossaryName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec: method registerGlossaryName ensures out = registeredKey termText, with registeredKey := id (identity on the term text). This postcondition FULLY pins the output to the identity for every input; loom_solve discharges only impls behaviorally equal to id. No behaviorally-wrong impl can verify, so verify=>correct is not falsifiable here.

Protocol run (project root; verifier scripts/lean_verify.sh, same_spec via python + swebench_unified.markers.same_spec on backend velvet). All 7 attacks confirmed same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical).

Positive control (verbatim gold impl, return registeredKey termText): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0 (verifies).

Attacks (each `bash scripts/lean_verify.sh .../atk_N.lean`), run concurrently in batches of 4 then 3:
- atk_1 PREPATCH BUG: return termText.map Char.toLower (reproduces removed .lower()) -> EXIT=1 (fails). Prepatch bug reproduced & correctly rejected.
- atk_2 control-flow/partial-domain: id on [] else map Char.toUpper -> EXIT=1 (fails).
- atk_3 degenerate/ungrounded oracle: return [] -> EXIT=1 (fails).
- atk_4 boundary: return termText.drop 1 -> EXIT=1 (fails).
- atk_5 ungrounded-oracle echo: return registeredKey (termText.map Char.toLower) -> EXIT=1 (fails).
- atk_6 append: return termText ++ ['x'] -> EXIT=1 (fails).
- atk_7 reverse: return termText.reverse -> EXIT=1 (fails).

No verifying wrong impl => no faithful refined patch to materialize/run through run_resolve; patches={} accordingly (nothing to resolve). Not INCONCLUSIVE: all >=5 attacks completed verification (no timeouts/exit 124), positive control verified, prepatch reproduced.

Refinement audit (refinement.md): every leg is R (A1: str<->List Char, mapping.md §2), A-reference+I (A2: registeredKey as deep model of the note_object/get_objects registry round-trip, identity-on-name, validated == real callee by G-AX; the impl op returning the verbatim key is concrete-I run through the real make_glossary_term+get_objects by G-CONF), or I (B1: dropped lowercase=True role flag, F2P-test-neutral, contributes no spec clause). No kind-3 (inexpressible-changed-op) legs. No consumed axioms. The one genuinely changed op (which key string is handed to the registry) is modeled deeply, not hidden behind a note_object axiom. Model<->patch correspondence holds: out = termText verbatim (registeredKey=id) <=> gold passes termtext (removal of .lower()); atk_1 is exactly the prepatch termtext.lower() and is rejected, matching the discriminating F2P behavior (TERM2 must register/report as TERM2, not term2).

Verdict: SOUND. No same-spec verifying wrong impl exists (7/7 distinct wrong impls fail), positive control verifies, refinement legs are all R/A-reference/I with sound A-leg correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sphinx-doc__sphinx-7440 velvet. RESULT: FAITHFUL — no diverging input found; the modeled function exactly matches the real post-patch repo behavior on every input tested.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True; spec view shows the single postcondition `out = registeredKey termText` with `registeredKey := id` (verbatim term key).
- Worktree is at base_commit 9bb204dcabe6ba0fc422bf4a45ad0c79c680d90b (pre-patch): real code is `std.note_object('term', termtext.lower(), node_id, ...)`; `get_objects` yields `(name, name, type, ...)`.

Model = the single behavioral clause: the registration key handed to the registry equals the term text verbatim (case preserved). The registry round-trip is the A-reference deep model registeredKey=id.

Faithfulness tests (real callee, docutils 0.16 venv):
1. Registry identity (unchanged callee): registered boundary + case-variant + Unicode names via real StandardDomain.note_object then read back via real get_objects — every key reported VERBATIM (case-distinct kept distinct). Model registeredKey=id is faithful, not a coincidence of the seed.
2. End-to-end vs real GOLD-PATCHED make_glossary_term (I applied the patch A hunk to a copy): drove 60,000 fuzzed strings plus adversarial Unicode edge cases (titlecase ǅ/ǈ, dotted İ/ı, ligatures ﬀ/ﬁ, final sigma ς, ß, Σ, combining marks, empty string, embedded space/tab/newline) through the real patched make_glossary_term + get_objects. Recorded key equals the term text verbatim on ALL inputs — 0 divergences. These edge cases would expose any residual .lower()/casefold/normalize the spec failed to model; none did.

Strength check (spec not too weak, and correctly not too strong):
- Lean: Solution.lean verifies (exit 0). Solution_prepatch.lean (`termText.map Char.toLower`) FAILS the spec (unsolved goal `List.map Char.toLower termText = registeredKey termText`) — so the spec is strong enough to reject the pre-patch case-folding key, which is exactly the observable behavioral change of the gold patch.
- The real post-patch function is deterministic and single-valued (one key per term), and the spec pins `out` to that exact value — no over-constraint beyond the real output.

Site B (dropped lowercase=True on the 'term' XRefRole, std.py:568) is genuinely F2P-test-neutral (reference-resolution-time lowering, no test_glossary assertion resolves a term xref) and correctly contributes no spec clause; its omission does not make the spec drift on any tested-observable input.

Conclusion: the modeled function and the real repo callee agree on every input; the spec faithfully and tightly captures the gold patch's observable behavior. No diverging input exists to substantiate an UNFAITHFUL verdict.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path 'sphinx/domains/std.py' or dotted module, no spec-view identifier embedding a patched repo symbol, no narration keywords, no comment naming a patched symbol. Spec region byte-identical (same_spec True between Solution.lean and Solution_prepatch.lean).

Semantic assessment: the spec view specifies registeredKey termText := termText (identity, case preserved) with the ensures 'out = registeredKey termText', and a comment describing the key as the term text 'exactly as written — character-for-character, with case preserved'. This describes the CORRECT behavior only. That behavior is already fully public in the problem_statement, which states 'glossary duplicate term with a different case' and 'MySQL != mysql term right?' — i.e. the public task already discloses that case must distinguish/preserve glossary term keys. A spec necessarily encodes correct behavior; here that behavior is not information beyond the problem statement.

The gold-edit MECHANICS are NOT leaked in the spec view: no mention of .lower(), note_object, make_glossary_term, StandardDomain, XRefRole, the lowercase=True flag, or the file path. Those edit-localizing details appear only in refinement.md/mapping.md (auditor docs), not in the solver-visible spec projection. Symbol names (registerGlossaryName, registeredKey) are neutral abstractions, not repo symbols; comment references (axiom_check.py, mapping.md) are bundle artifacts, not repo internals. Comments name no patched repo symbol. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
