# P2 adversarial audit — matplotlib__matplotlib-23299

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures params = updateDict paramsOld (eraseKey saved "backend")` pins params to EXACT Lean-list equality under total correctness with NO precondition — a complete functional spec. Every behaviorally-wrong impl fails to verify; every verifying impl computes exactly the gold function, so its faithful patch equals the gold finally-block edit and resolves.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := updateDict params saved
     return
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := params
     return
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,9 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
+    let restoreSrc := eraseKey saved "font.size"
     params := updateDict params restoreSrc
     return
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,8 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
     let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := updateDict restoreSrc params
     return
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,10 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := updateDict (eraseKey params "backend") saved
     return
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,10 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := updateDict params (eraseKey saved "backend")
     return
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,8 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
+    let _dead := updateDict params saved
     let restoreSrc := eraseKey saved "backend"
     params := updateDict params restoreSrc
     return
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,10 +64,8 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
-    params := updateDict params restoreSrc
+    params := updateDict params saved
+    params := updateDict paramsOld (eraseKey saved "backend")
     return
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,9 +64,7 @@
   ensures params = updateDict paramsOld (eraseKey saved "backend")
   do
     -- impl-start
-    -- Drop the designated key from the snapshot before overlaying it, so the
-    -- designated key is NOT reverted to its saved value.
-    let restoreSrc := eraseKey saved "backend"
+    let restoreSrc := eraseKey (eraseKey saved "backend") "toolbar"
     params := updateDict params restoreSrc
     return
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The two operations this restore defers to — overlaying a
--  saved snapshot onto the current mapping, and dropping one key from the
--  snapshot — are modeled DEEPLY in the `pure` region (`updateDict`, `eraseKey`)
--  and validated against their real builtin counterparts by G-AX
--  (`updateDict` is an A-reference; mapping.md §3 / axiom_check.py). Nothing is
--  consumed as an axiom.)
-- axioms-end

-- pure-start
/- Look up the value bound to `name` in a key→value mapping carried as an
   association list (first binding wins; the modeled mapping has unique keys). -/
def lookupKey : List (String × String) → String → Option String
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Drop every binding for `name` from the mapping (keys are unique, so this
   removes exactly the one binding for `name`, leaving the rest in order). -/
def eraseKey : List (String × String) → String → List (String × String)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- Overlay `saved` onto `current`: every key present in `saved` takes its
   `saved` value; keys present only in `current` keep their `current` value.
   This is the standard "update the mapping in place from another mapping"
   semantics (the saved bindings win). Deep model of that builtin overlay,
   validated equal to it by G-AX (A-reference, mapping.md §3.1). -/
def updateDict (current saved : List (String × String)) : List (String × String) :=
  saved ++ current.filter (fun kv => (lookupKey saved kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a previously-saved snapshot of a key→value mapping over its current
   (possibly modified) state, while leaving ONE designated key at its current
   value instead of reverting it.

   A scoped override records a snapshot `saved` of the mapping on entry, lets
   the stored values be freely changed, and on exit puts the recorded settings
   back. The restored mapping keeps the CURRENT value for the designated key
   "backend" and the saved value for every other recorded key; keys present
   only in the current mapping keep their current value.

   `params` is the live mapping; it is genuinely mutated and its post-state is
   pinned EXACTLY (directive 5) by the `ensures` equation below. `saved` is the
   read-only entry snapshot. -/
method restoreSnapshot
    (mut params : List (String × String))
    (saved : List (String × String))
    return (u : Unit)
  ensures params = updateDict paramsOld (eraseKey saved "backend")
  do
    -- impl-start
    let restoreSrc := eraseKey saved "backend"
    params := updateDict params restoreSrc
    return
    -- impl-end

prove_correct restoreSnapshot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit — VERDICT SOUND.

Setup: only the impl region editable; the `pure` region (updateDict/eraseKey/lookupKey defs) is part of the spec view (SPEC_REGIONS includes `pure`), so same_spec pins the deep models too. All 10 files same_spec==True (verified via swebench_unified.markers.same_spec, velvet backend). Positive control = gold impl, verifies (lean_verify exit 0).

Attacks (lean_verify.sh, 300s cap; run concurrently ≤4/batch):
- atk_1 PREPATCH bug `updateDict params saved` (full-snapshot overlay, reverts backend) -> exit 1, unsolved goal EXACTLY `updateDict paramsOld saved = updateDict paramsOld (eraseKey saved "backend")` — prepatch reproduced, matches refinement.md §A.
- atk_2 no-revert (identity `params := params`) -> exit 1.
- atk_3 wrong-oracle: erase "font.size" instead of "backend" -> exit 1.
- atk_4 control-flow-effect: swapped updateDict arg order `updateDict restoreSrc params` -> exit 1.
- atk_5 erase from wrong side `updateDict (eraseKey params ...) saved` -> exit 1.
- atk_9 partial-domain: double-erase backend+toolbar -> exit 1.
- atk_6 ECHO (inline, no let) `updateDict params (eraseKey saved "backend")` -> exit 0 VERIFIES.
- atk_7 ECHO (dead-code `let _dead := updateDict params saved` then correct) -> exit 0 VERIFIES.
- atk_8 last-write-wins (wrong assign then correct overwrite) -> exit 0 VERIFIES.

All three verifying impls compute EXACTLY the gold function `updateDict params (eraseKey saved "backend")` (gold-equivalent echoes; the tight exact-equality postcondition admits nothing else). Per protocol I materialized each faithful refined patch (= the gold finally-block edit: `orig = dict(rcParams.copy()); del orig['backend']`) and RAN it through the official harness: run_resolve("matplotlib__matplotlib-23299", <patch>) => RESOLVED=True, COMPLETED=True, note='resolved'. No verifying wrong impl exists whose faithful patch fails to resolve.

A-leg audit (my focus):
- refinement.md legs: A1/A2 = R (dict[str,str] <-> List(String x String) unique-key mapping bijection), A3 = I (eraseKey == del), A4 = A-reference + I (updateDict deep model == builtin dict.update). No consumed axioms, no kind-3 (inexpressible-changed-op) steps. Correspondence holds.
- G-AX (axiom_check.py) exit 0: updateDict == real builtin dict.update overlay AND eraseKey == real del on 8 boundary + 30000 fuzz cases; end-to-end patched restore preserves designated 'backend' key at its CURRENT value.
- G-CONF (conformance_check.py) exit 0: R/I shadow (A-ref left as real dict.update, eraseKey transliterated) agrees with patched finally block on 100005 inputs (seed 23299), 0 disagreements.
- Partial-domain note on the A3 I-leg: Python `del orig['backend']` raises KeyError if absent, whereas eraseKey is a no-op if absent — but on the reachable domain rcParams ALWAYS contains 'backend' (mapping.md §2 / conformance_check enforces backend present), so the divergence is unreachable and cannot produce a verify-but-wrong impl. Not a soundness gap.

RELAXED_LEAKAGE.md is a G-LEAK/G-PANEL-3 concern, not G-EQ; core soundness (verify => correct) is unaffected. Conclusion: verify => exact Lean-list equality => (a fortiori) dict-equality => gold behavior => resolves. Spec is TIGHT and SOUND for refinement fidelity.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `ensures params = updateDict paramsOld (eraseKey saved "backend")` pins params to EXACT Lean-list equality under total correctness with NO precondition — a complete functional spec. Every behaviorally-wrong impl fails to verify; every verifying impl computes exactly the gold function, so its faithful patch equals the gold finally-block edit and resolves.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The two operations this restore defers to — overlaying a
--  saved snapshot onto the current mapping, and dropping one key from the
--  snapshot — are modeled DEEPLY in the `pure` region (`updateDict`, `eraseKey`)
--  and validated against their real builtin counterparts by G-AX
--  (`updateDict` is an A-reference; mapping.md §3 / axiom_check.py). Nothing is
--  consumed as an axiom.)
-- axioms-end

-- pure-start
/- Look up the value bound to `name` in a key→value mapping carried as an
   association list (first binding wins; the modeled mapping has unique keys). -/
def lookupKey : List (String × String) → String → Option String
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Drop every binding for `name` from the mapping (keys are unique, so this
   removes exactly the one binding for `name`, leaving the rest in order). -/
def eraseKey : List (String × String) → String → List (String × String)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- Overlay `saved` onto `current`: every key present in `saved` takes its
   `saved` value; keys present only in `current` keep their `current` value.
   This is the standard "update the mapping in place from another mapping"
   semantics (the saved bindings win). Deep model of that builtin overlay,
   validated equal to it by G-AX (A-reference, mapping.md §3.1). -/
def updateDict (current saved : List (String × String)) : List (String × String) :=
  saved ++ current.filter (fun kv => (lookupKey saved kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a previously-saved snapshot of a key→value mapping over its current
   (possibly modified) state, while leaving ONE designated key at its current
   value instead of reverting it.

   A scoped override records a snapshot `saved` of the mapping on entry, lets
   the stored values be freely changed, and on exit puts the recorded settings
   back. The restored mapping keeps the CURRENT value for the designated key
   "backend" and the saved value for every other recorded key; keys present
   only in the current mapping keep their current value.

   `params` is the live mapping; it is genuinely mutated and its post-state is
   pinned EXACTLY (directive 5) by the `ensures` equation below. `saved` is the
   read-only entry snapshot. -/
method restoreSnapshot
    (mut params : List (String × String))
    (saved : List (String × String))
    return (u : Unit)
  ensures params = updateDict paramsOld (eraseKey saved "backend")
  do
    -- impl-start
    let restoreSrc := eraseKey saved "backend"
    params := updateDict params restoreSrc
    return
    -- impl-end

prove_correct restoreSnapshot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit — VERDICT SOUND.

Setup: only the impl region editable; the `pure` region (updateDict/eraseKey/lookupKey defs) is part of the spec view (SPEC_REGIONS includes `pure`), so same_spec pins the deep models too. All 10 files same_spec==True (verified via swebench_unified.markers.same_spec, velvet backend). Positive control = gold impl, verifies (lean_verify exit 0).

Attacks (lean_verify.sh, 300s cap; run concurrently ≤4/batch):
- atk_1 PREPATCH bug `updateDict params saved` (full-snapshot overlay, reverts backend) -> exit 1, unsolved goal EXACTLY `updateDict paramsOld saved = updateDict paramsOld (eraseKey saved "backend")` — prepatch reproduced, matches refinement.md §A.
- atk_2 no-revert (identity `params := params`) -> exit 1.
- atk_3 wrong-oracle: erase "font.size" instead of "backend" -> exit 1.
- atk_4 control-flow-effect: swapped updateDict arg order `updateDict restoreSrc params` -> exit 1.
- atk_5 erase from wrong side `updateDict (eraseKey params ...) saved` -> exit 1.
- atk_9 partial-domain: double-erase backend+toolbar -> exit 1.
- atk_6 ECHO (inline, no let) `updateDict params (eraseKey saved "backend")` -> exit 0 VERIFIES.
- atk_7 ECHO (dead-code `let _dead := updateDict params saved` then correct) -> exit 0 VERIFIES.
- atk_8 last-write-wins (wrong assign then correct overwrite) -> exit 0 VERIFIES.

All three verifying impls compute EXACTLY the gold function `updateDict params (eraseKey saved "backend")` (gold-equivalent echoes; the tight exact-equality postcondition admits nothing else). Per protocol I materialized each faithful refined patch (= the gold finally-block edit: `orig = dict(rcParams.copy()); del orig['backend']`) and RAN it through the official harness: run_resolve("matplotlib__matplotlib-23299", <patch>) => RESOLVED=True, COMPLETED=True, note='resolved'. No verifying wrong impl exists whose faithful patch fails to resolve.

A-leg audit (my focus):
- refinement.md legs: A1/A2 = R (dict[str,str] <-> List(String x String) unique-key mapping bijection), A3 = I (eraseKey == del), A4 = A-reference + I (updateDict deep model == builtin dict.update). No consumed axioms, no kind-3 (inexpressible-changed-op) steps. Correspondence holds.
- G-AX (axiom_check.py) exit 0: updateDict == real builtin dict.update overlay AND eraseKey == real del on 8 boundary + 30000 fuzz cases; end-to-end patched restore preserves designated 'backend' key at its CURRENT value.
- G-CONF (conformance_check.py) exit 0: R/I shadow (A-ref left as real dict.update, eraseKey transliterated) agrees with patched finally block on 100005 inputs (seed 23299), 0 disagreements.
- Partial-domain note on the A3 I-leg: Python `del orig['backend']` raises KeyError if absent, whereas eraseKey is a no-op if absent — but on the reachable domain rcParams ALWAYS contains 'backend' (mapping.md §2 / conformance_check enforces backend present), so the divergence is unreachable and cannot produce a verify-but-wrong impl. Not a soundness gap.

RELAXED_LEAKAGE.md is a G-LEAK/G-PANEL-3 concern, not G-EQ; core soundness (verify => correct) is unaffected. Conclusion: verify => exact Lean-list equality => (a fortiori) dict-equality => gold behavior => resolves. Spec is TIGHT and SOUND for refinement fidelity.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True. spec_view confirms the ensures clause `params = updateDict paramsOld (eraseKey saved "backend")` plus the pure defs (lookupKey/eraseKey/updateDict) are all in the frozen spec, identical to prepatch. Solution.lean verifies (lean_verify.sh exit 0). Real repo at base_commit (HEAD 3eadeacc06, patch applied) implements restore as `orig = dict(rcParams.copy()); del orig['backend']; ...; dict.update(rcParams, orig)`. Modeled updateDict (saved ++ current.filter key-not-in-saved) == builtin dict.update as a key->value mapping (order unobservable); eraseKey == builtin del. axiom_check.py passes (8 boundary + 30000 fuzz). My independent differential fuzz (200k general + 200k backend-always-present, seeds 999/23299) found 0 divergences between model_restore and real_restore over the reachable domain. Total-correctness semantics is faithful (real restore is straight-line del+dict.update in a finally block, always terminates). Spec is neither too strong nor drifting from real behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted relaxed-leakage disposition rather than rubber-stamping. (1) Core soundness intact: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical via swebench_unified.markers.same_spec with the velvet LanguageTables); Solution.lean verifies EXIT=0 under total-correctness semantics; meta.json gates G-VERIFY/G-DIFF/G-EQ/G-AX/G-CONF/G-RESOLVE all pass; relaxed_leakage=True, G-LEAK=relaxed. (2) The spec view DOES reconstruct the gold edit via `ensures params = updateDict paramsOld (eraseKey saved "backend")` + the docstring naming the designated key "backend" and the drop-from-snapshot-before-overlay behavior — under the mapping.md bijection (eraseKey=del, updateDict=dict.update) this is del orig['backend']; dict.update(rcParams, orig). (3) That leak is EXACTLY the dispositioned backend-restore-exclusion facet, not a new leak: the whole spec view (lookupKey/eraseKey/updateDict + postcondition + docstrings) concerns only that mechanism; no additional line leaks beyond it. (4) Unavoidability re-derived independently: the public problem_statement frames the defect purely as the downstream symptom (get_backend() clears Gcf.figs) and never names the backend rcParam, the rcParams snapshot/restore mechanism, or the exclude-a-key-from-the-reverted-snapshot fix (revert/restore/snapshot/copy/del/preserve all absent); the diagnosis lives only in hints_text (out of the leak baseline) and the hidden test_patch. Dropping `eraseKey saved "backend"` makes Solution_prepatch (full-snapshot overlay) verify, so G-DIFF could not fire — a faithful, prepatch-refuting spec MUST pin the survive-vs-revert discriminator, so faithful+non-leaking is provably impossible. Genuine problem_statement<->gold mismatch. Disposition (RELAXED_LEAKAGE.md present, meta flag set, core gates sound) is unbroken. Honest G-PANEL-3 recording for a properly-dispositioned relaxed-leakage bundle is NO-LEAKAGE/pass with this re-confirmation note; no leak beyond the dispositioned facet was found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
