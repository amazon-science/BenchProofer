# P2 adversarial audit — django__django-15732

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `ensures out = selectedTarget names uniqueSel allowMultiple canonical` is a STRICT functional equality that pins `out` for every input tuple (zero output freedom). Any impl that verifies is therefore extensionally equal to `selectedTarget` on all inputs, so its faithful refined patch is behaviorally the gold selection and resolves. No verifying wrong impl with a non-resolving faithful patch exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,10 +47,8 @@
   ensures out = selectedTarget names uniqueSel allowMultiple canonical
   do
     -- impl-start
-    let mut ns := names
-    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
-      if canonical ∈ ns then
-        ns := [canonical]
+    -- ATTACK: prepatch bug — no narrowing step at all
+    let ns := names
     let result : Option String := if ns.length = 1 then ns[0]? else none
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,11 +47,9 @@
   ensures out = selectedTarget names uniqueSel allowMultiple canonical
   do
     -- impl-start
-    let mut ns := names
-    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
-      if canonical ∈ ns then
-        ns := [canonical]
-    let result : Option String := if ns.length = 1 then ns[0]? else none
+    -- ATTACK: degenerate — always return none
+    let _ns := names
+    let result : Option String := none
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,8 @@
     if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
       if canonical ∈ ns then
         ns := [canonical]
-    let result : Option String := if ns.length = 1 then ns[0]? else none
+    -- ATTACK: boundary off — accept any non-empty set, take head
+    let result : Option String := if ns.length ≥ 1 then ns[0]? else none
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,9 +48,9 @@
   do
     -- impl-start
     let mut ns := names
+    -- ATTACK: drop membership guard — always narrow to [canonical]
     if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
-      if canonical ∈ ns then
-        ns := [canonical]
+      ns := [canonical]
     let result : Option String := if ns.length = 1 then ns[0]? else none
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,8 @@
   do
     -- impl-start
     let mut ns := names
-    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
+    -- ATTACK: drop allowMultiple guard from narrowing condition
+    if uniqueSel = true ∧ ns ≠ [] then
       if canonical ∈ ns then
         ns := [canonical]
     let result : Option String := if ns.length = 1 then ns[0]? else none
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,12 +47,8 @@
   ensures out = selectedTarget names uniqueSel allowMultiple canonical
   do
     -- impl-start
-    let mut ns := names
-    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
-      if canonical ∈ ns then
-        ns := [canonical]
-    let result : Option String := if ns.length = 1 then ns[0]? else none
-    return result
+    -- ATTACK: ungrounded-oracle echo — return the spec function directly
+    return selectedTarget names uniqueSel allowMultiple canonical
     -- impl-end
 
 prove_correct chooseTarget by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,8 @@
     if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
       if canonical ∈ ns then
         ns := [canonical]
-    let result : Option String := if ns.length = 1 then ns[0]? else none
+    -- ATTACK: use getLast? instead of head — equal only when singleton
+    let result : Option String := if ns.length = 1 then ns.getLast? else none
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms. This operation's behaviour is a decision over the values produced
   by its helper calls: the set of candidate identifiers discovered for the
   target columns, and the canonical identifier the same naming scheme would
   assign. Those helper results are taken as opaque method inputs, so the
   contract holds for every possible helper output and assumes no callee
   property. Helper provenance is recorded in mapping.md §3; G-AX is vacuous. -/
-- axioms-end

-- pure-start
/- Narrow a set of candidate identifiers to a single canonical one exactly when:
   the selection is by uniqueness, the candidate set is non-empty, several
   co-located selectors are permitted at once, and the canonical identifier is
   itself among the candidates. Otherwise the candidate set is returned as-is. -/
def narrowed (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : List String :=
  if uniqueSel = true ∧ names ≠ [] ∧ allowMultiple = true then
    if canonical ∈ names then [canonical] else names
  else
    names

/- The single target the operation may act on: defined precisely when the
   narrowed candidate set is a singleton (its element); otherwise no unique
   target exists and the operation cannot proceed. -/
def selectedTarget (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : Option String :=
  let ns := narrowed names uniqueSel allowMultiple canonical
  if ns.length = 1 then ns[0]? else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method chooseTarget (names : List String) (uniqueSel : Bool) (allowMultiple : Bool)
    (canonical : String) return (out : Option String)
  ensures out = selectedTarget names uniqueSel allowMultiple canonical
  do
    -- impl-start
    let mut ns := names
    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
      if canonical ∈ ns then
        ns := [canonical]
    let result : Option String := if ns.length = 1 then ns[0]? else none
    return result
    -- impl-end

prove_correct chooseTarget by
  loom_solve <;>
    simp_all [narrowed, selectedTarget] <;>
    split_ifs <;>
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 Env: source activate; for lean_verify.sh. Positive control pos.lean (copy of gold Solution.lean) verifies: `bash scripts/lean_verify.sh .../pos.lean` EXIT=0.

same_spec (velvet) = True for ALL 7 attacks (verified via swebench_unified.markers.same_spec + get_backend('velvet')).

7 DISTINCT same-spec wrong impls, impl-region-only edits, verified concurrently (batches of 4 then 3) with `bash scripts/lean_verify.sh .../atk_N.lean`:
- atk_1 (prepatch bug: no narrowing step; `let ns := names`) -> EXIT=1, unsolved goals at 56:27. NON-VERIFYING.
- atk_2 (partial-domain/degenerate: always return none) -> EXIT=1, unsolved goals + simp_all no progress. NON-VERIFYING.
- atk_3 (boundary: `ns.length >= 1` instead of `= 1`, take head) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING.
- atk_4 (drop membership guard: narrow to [canonical] regardless of `canonical in ns`) -> EXIT=1, simp_all no progress at 62:4. NON-VERIFYING.
- atk_5 (control-flow-effect: drop allowMultiple from narrowing guard) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING.
- atk_6 (ungrounded-oracle echo: `return selectedTarget names uniqueSel allowMultiple canonical`) -> EXIT=0. VERIFIES.
- atk_7 (getLast? instead of ns[0]? in the singleton branch; extensionally equal to head when length=1) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING (proof cannot close head=last even though semantically equal).

Prepatch reproduced: Solution_prepatch.lean copied to prepatch.lean -> EXIT=1, unsolved goals at 59:27 (bug reproduced; narrowing absent => fails the frozen spec). TRUE.

MANDATORY RESOLVE RUN for the only verifying wrong impl (atk_6): atk_6 returns selectedTarget verbatim, so it is extensionally IDENTICAL to the reference impl on every input; its faithful refined patch = the gold patch verbatim (materialized to gold_patch.diff from data/swe_bench_verified/test.jsonl). Executed: `run_resolve('django__django-15732', <gold patch>, timeout=1800, retries=1)` (official harness via docker / swebench_unified.run_evaluation) -> RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1. The verifying attack's faithful patch RESOLVES => does NOT break the spec. (G-PANEL-1 echo policy 2026-08-06: a resolving echo is NOT a weakness.)

refinement.md leg audit: A1-A4,A6 = R (type refinements list[str]<->List String, bool<->Bool, str<->String, constraint_names[0]/ValueError<->Option String); A5 = I (narrowing block modeled directly as identical nested-if). NO A-consumed, NO A-reference (meta.json axioms=[], deep_model_references=[], conf_skip=False — consistent). NO kind-3 legs: the sole genuinely-changed op (narrowing) is modeled directly. Second gold hunk (_unique_constraint_name extraction + {'unique':True,'primary_key':False} kwargs) is a faithful pure refactor whose behaviour-bearing quote=False value is the opaque `canonical` input; _constraint_names result is the opaque `names` input. Model<->patch correspondence holds.

VERDICT: SOUND. >=5 distinct attacks executed (7 total), prepatch reproduced, and the single verifying wrong impl's faithful refined patch was RUN through the official harness and RESOLVED. No verify-but-not-resolve witness exists — the strict functional-equality postcondition leaves no output freedom to exploit.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `ensures out = selectedTarget names uniqueSel allowMultiple canonical` is a STRICT functional equality that pins `out` for every input tuple (zero output freedom). Any impl that verifies is therefore extensionally equal to `selectedTarget` on all inputs, so its faithful refined patch is behaviorally the gold selection and resolves. No verifying wrong impl with a non-resolving faithful patch exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms. This operation's behaviour is a decision over the values produced
   by its helper calls: the set of candidate identifiers discovered for the
   target columns, and the canonical identifier the same naming scheme would
   assign. Those helper results are taken as opaque method inputs, so the
   contract holds for every possible helper output and assumes no callee
   property. Helper provenance is recorded in mapping.md §3; G-AX is vacuous. -/
-- axioms-end

-- pure-start
/- Narrow a set of candidate identifiers to a single canonical one exactly when:
   the selection is by uniqueness, the candidate set is non-empty, several
   co-located selectors are permitted at once, and the canonical identifier is
   itself among the candidates. Otherwise the candidate set is returned as-is. -/
def narrowed (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : List String :=
  if uniqueSel = true ∧ names ≠ [] ∧ allowMultiple = true then
    if canonical ∈ names then [canonical] else names
  else
    names

/- The single target the operation may act on: defined precisely when the
   narrowed candidate set is a singleton (its element); otherwise no unique
   target exists and the operation cannot proceed. -/
def selectedTarget (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : Option String :=
  let ns := narrowed names uniqueSel allowMultiple canonical
  if ns.length = 1 then ns[0]? else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method chooseTarget (names : List String) (uniqueSel : Bool) (allowMultiple : Bool)
    (canonical : String) return (out : Option String)
  ensures out = selectedTarget names uniqueSel allowMultiple canonical
  do
    -- impl-start
    let mut ns := names
    if uniqueSel = true ∧ ns ≠ [] ∧ allowMultiple = true then
      if canonical ∈ ns then
        ns := [canonical]
    let result : Option String := if ns.length = 1 then ns[0]? else none
    return result
    -- impl-end

prove_correct chooseTarget by
  loom_solve <;>
    simp_all [narrowed, selectedTarget] <;>
    split_ifs <;>
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 Env: source activate; for lean_verify.sh. Positive control pos.lean (copy of gold Solution.lean) verifies: `bash scripts/lean_verify.sh .../pos.lean` EXIT=0.

same_spec (velvet) = True for ALL 7 attacks (verified via swebench_unified.markers.same_spec + get_backend('velvet')).

7 DISTINCT same-spec wrong impls, impl-region-only edits, verified concurrently (batches of 4 then 3) with `bash scripts/lean_verify.sh .../atk_N.lean`:
- atk_1 (prepatch bug: no narrowing step; `let ns := names`) -> EXIT=1, unsolved goals at 56:27. NON-VERIFYING.
- atk_2 (partial-domain/degenerate: always return none) -> EXIT=1, unsolved goals + simp_all no progress. NON-VERIFYING.
- atk_3 (boundary: `ns.length >= 1` instead of `= 1`, take head) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING.
- atk_4 (drop membership guard: narrow to [canonical] regardless of `canonical in ns`) -> EXIT=1, simp_all no progress at 62:4. NON-VERIFYING.
- atk_5 (control-flow-effect: drop allowMultiple from narrowing guard) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING.
- atk_6 (ungrounded-oracle echo: `return selectedTarget names uniqueSel allowMultiple canonical`) -> EXIT=0. VERIFIES.
- atk_7 (getLast? instead of ns[0]? in the singleton branch; extensionally equal to head when length=1) -> EXIT=1, unsolved goals at 59:27. NON-VERIFYING (proof cannot close head=last even though semantically equal).

Prepatch reproduced: Solution_prepatch.lean copied to prepatch.lean -> EXIT=1, unsolved goals at 59:27 (bug reproduced; narrowing absent => fails the frozen spec). TRUE.

MANDATORY RESOLVE RUN for the only verifying wrong impl (atk_6): atk_6 returns selectedTarget verbatim, so it is extensionally IDENTICAL to the reference impl on every input; its faithful refined patch = the gold patch verbatim (materialized to gold_patch.diff from data/swe_bench_verified/test.jsonl). Executed: `run_resolve('django__django-15732', <gold patch>, timeout=1800, retries=1)` (official harness via docker / swebench_unified.run_evaluation) -> RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1. The verifying attack's faithful patch RESOLVES => does NOT break the spec. (G-PANEL-1 echo policy 2026-08-06: a resolving echo is NOT a weakness.)

refinement.md leg audit: A1-A4,A6 = R (type refinements list[str]<->List String, bool<->Bool, str<->String, constraint_names[0]/ValueError<->Option String); A5 = I (narrowing block modeled directly as identical nested-if). NO A-consumed, NO A-reference (meta.json axioms=[], deep_model_references=[], conf_skip=False — consistent). NO kind-3 legs: the sole genuinely-changed op (narrowing) is modeled directly. Second gold hunk (_unique_constraint_name extraction + {'unique':True,'primary_key':False} kwargs) is a faithful pure refactor whose behaviour-bearing quote=False value is the opaque `canonical` input; _constraint_names result is the opaque `names` input. Model<->patch correspondence holds.

VERDICT: SOUND. >=5 distinct attacks executed (7 total), prepatch reproduced, and the single verifying wrong impl's faithful refined patch was RUN through the official harness and RESOLVED. No verify-but-not-resolve witness exists — the strict functional-equality postcondition leaves no output freedom to exploit.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no drift. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True; the axioms/pure/pre/post regions, method signature, and `ensures out = selectedTarget names uniqueSel allowMultiple canonical` are identical between patch and prepatch — only the impl body differs (prepatch drops the narrowing step and fails prove_correct, as intended for G-DIFF). (2) Solution.lean elaborates cleanly via scripts/lean_verify.sh (exit 0; only a cosmetic `<;>` linter warning). (3) The model faithfully abstracts the real patched _delete_composed_index selection decision at base_commit ce69e34b (verified against gold patch.diff): narrow constraint_names to [default_name] exactly when constraint_kwargs.get('unique') is True AND constraint_names is truthy AND allows_multiple_constraints_on_same_fields AND default_name in constraint_names; then act on constraint_names[0] iff len==1 else raise ValueError. narrowed/selectedTarget mirror this precisely — `names ≠ []` correctly matches Python nonempty-list truthiness (incl. [''] truthy → names ≠ [] True), `canonical ∈ names` matches Python list `in` element-equality, and Option some/none matches act/raise. The three helper results (_constraint_names, _unique_constraint_name, feature flag) are unchanged callees consumed only as values, correctly modeled as opaque method inputs (no assumed callee property), so G-AX is vacuous. (4) Independent differential: I re-transcribed the real patched block from scratch (NOT the bundle oracle) and ran an exhaustive small-domain + edge-case sweep (6216 tuples: k=0..3 over a pool with empty string, duplicates, empty list; all unique/allowMultiple/canonical combos) → 0 divergences. Bundle G-CONF (conformance_check.py, seed 15732, 100010 inputs) also reports 0 disagreements. No input exists where the modeled function disagrees with the real callee; spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean with impl/proof regions elided (verified via spec_view). same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical). Mechanical G-LEAK screen PASSES (0 hard failures). Detailed checks: (1) No diff markers, no verbatim gold-patch lines >=8 chars, no patched file path 'schema.py' or module path in the spec view. (2) Patched repo symbols {alter_unique_together, _delete_composed_index, _unique_constraint_name, _create_unique_sql, create_unique_name} appear in NO spec-view identifier or comment — the model deliberately uses abstract carriers (names, uniqueSel, allowMultiple, canonical, narrowed, selectedTarget, chooseTarget). (3) No narration terms (bug/fix/patch/prepatch/etc.) in spec-view comments. (4) The behavioral content the spec reveals — narrowing a multi-candidate unique-constraint set to the canonical unique_together name (the '_uniq' identifier) — is already public in problem_statement: it shows both constraints including 'foo_bar_id_1c3b3088c74c3b17_uniq', states the migration 'expects there to be only one', and gives the ValueError('Found wrong number (2) of constraints'). The narrowing-to-canonical-name approach is derivable from the public task, not smuggled beyond it. (5) mapping.md/refinement.md do name schema.py and repo symbols but those are AUDITOR docs, not the solver-visible spec view, hence out of G-LEAK scope. Conclusion: the spec is a faithfully abstracted behavioral contract that does not localize the edit to a repo file/symbol nor reconstruct the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
