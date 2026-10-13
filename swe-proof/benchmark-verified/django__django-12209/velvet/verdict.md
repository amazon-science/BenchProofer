# P2 adversarial audit — django__django-12209

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,7 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
+    if (!forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
       return true
     else
       return forceInsert
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,7 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
+    if (!raw && adding && (pkDefaultTruthy && pkDefaultProvided)) then
       return true
     else
       return forceInsert
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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,7 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
+    if (!raw && !forceInsert && (pkDefaultTruthy && pkDefaultProvided)) then
       return true
     else
       return forceInsert
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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,7 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
+    if (!raw && !forceInsert && adding && pkDefaultTruthy) then
       return true
     else
       return forceInsert
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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -77,7 +77,7 @@
     if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
       return true
     else
-      return forceInsert
+      return false
     -- impl-end
 
 prove_correct decideForceInsert by
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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,10 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
-      return true
-    else
-      return forceInsert
+    return forceInsert
     -- impl-end
 
 prove_correct decideForceInsert by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed boolean
@@ -74,10 +74,7 @@
             = (pkDefaultTruthy && pkDefaultProvided)
   do
     -- impl-start
-    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
-      return true
-    else
-      return forceInsert
+    return decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided
     -- impl-end
 
 prove_correct decideForceInsert by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed boolean
--  decision over its inputs: given five read-only boolean observations about a
--  persistence request, it returns the boolean that controls whether the row is
--  written with an INSERT-only path. The underlying observations — whether the
--  request is a direct/unprocessed data load, whether an INSERT is already
--  being forced, whether the instance is being added for the first time, and
--  whether its primary key carries a usable default — are abstracted to the
--  boolean inputs (an R refinement, validated against the real persistence path
--  by conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether the primary key carries a usable default value: it must both be set
   to something truthy AND be a genuinely provided default (not the sentinel
   that marks "no default at all"). Both observations are modeled as boolean
   inputs (mapping.md §2); the predicate holds iff both are true. -/
@[grind] def pkHasUsableDefault (pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  pkDefaultTruthy && pkDefaultProvided

/- The decision that controls whether persisting a row skips the initial
   UPDATE probe and goes straight to an INSERT.

   The INSERT-only path is taken exactly when ALL of the following hold:
     * the request is an ordinary save, not a direct/unprocessed data load;
     * an INSERT is not already being forced by the caller;
     * the instance is being added for the first time;
     * its primary key carries a usable default value.
   Otherwise the incoming forcing flag is returned unchanged. In particular,
   for a direct/unprocessed data load the forcing is never introduced here, so
   an explicit primary key remains free to match an existing row through the
   ordinary UPDATE probe. -/
@[grind] def decidedForceInsert
    (raw forceInsert adding pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  if !raw && !forceInsert && adding && pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
  then true
  else forceInsert
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the INSERT-forcing flag for a single-table persistence request.

   `raw` marks a direct/unprocessed data load (e.g. loading serialized
   fixtures); `forceInsert` is the caller-supplied request to force an INSERT;
   `adding` is whether the instance is being added for the first time;
   `pkDefaultTruthy` / `pkDefaultProvided` are the two observations about the
   primary key's default that together decide whether it carries a usable
   default value.

   All five inputs are read-only (none `mut`, directive 5): the routine inspects
   the five conditions and returns the resolved flag, mutating none of them. The
   resolved value is pinned exactly by `decidedForceInsert`: the INSERT-only path
   is forced only for an ordinary save of a freshly-added instance whose primary
   key has a usable default, and never for a direct/unprocessed data load. -/
method decideForceInsert
    (raw : Bool) (forceInsert : Bool) (adding : Bool)
    (pkDefaultTruthy : Bool) (pkDefaultProvided : Bool) return (out : Bool)
  ensures out = decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided
  ensures pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
            = (pkDefaultTruthy && pkDefaultProvided)
  do
    -- impl-start
    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
      return true
    else
      return forceInsert
    -- impl-end

prove_correct decideForceInsert by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: postcondition `out = decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided` pins out as a TOTAL function of all 5 free Bools with NO preconditions => verify implies impl equals gold-guard function on all 32 configs => correct. meta.json axioms=[], deep_model_references=[]; no A-consumed/A-reference legs; refinement.md A1-A4=R (Bool bijection mapping.md §2), A5=I (deep model of guard); no kind-3. conformance_check.py shadow matches deep model, oracle = real patched guard, R-bijection self-checked in-script.

VERIFY (lean_verify.sh, exit0=verifies,1=error): pos_control(gold)=0 OK; atk_1 drop !raw (=Solution_prepatch bug)=1 rejected (fails on raw=T config => prepatch reproduced); atk_3 drop adding=1 rejected; atk_4 require only pkDefaultTruthy (boundary)=1 rejected; atk_5 else->false (control-flow-effect)=1 rejected; atk_6 always return forceInsert (partial/ungrounded)=1 rejected. TWO verified: atk_2 drop !forceInsert=0 (behaviorally identical: when forceInsert=T spec returns T=atk true, when forceInsert=F the !forceInsert conjunct is a no-op), atk_7 return decidedForceInsert oracle echo=0 (=gold). same_spec=True for all 8 files.

FALSIFICATION: materialized faithful refined patches for BOTH verifying wrong impls and ran official harness run_resolve('django__django-12209', ..., timeout=1800). atk_2.patch (add `not raw`, drop `not force_insert`): RESOLVED=True COMPLETED=True FLAKY=False. atk_7.patch (= gold patch.diff): RESOLVED=True COMPLETED=True. Both faithful patches RESOLVE => no verify-not-correct break. Commands: `bash scripts/lean_verify.sh <atk>.lean`; `run_resolve` via swebench_unified.harness. Docker+image (sweb.eval.x86_64.django_1776_django-12209) available. No verifying impl produces a non-resolving faithful patch => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed boolean
--  decision over its inputs: given five read-only boolean observations about a
--  persistence request, it returns the boolean that controls whether the row is
--  written with an INSERT-only path. The underlying observations — whether the
--  request is a direct/unprocessed data load, whether an INSERT is already
--  being forced, whether the instance is being added for the first time, and
--  whether its primary key carries a usable default — are abstracted to the
--  boolean inputs (an R refinement, validated against the real persistence path
--  by conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether the primary key carries a usable default value: it must both be set
   to something truthy AND be a genuinely provided default (not the sentinel
   that marks "no default at all"). Both observations are modeled as boolean
   inputs (mapping.md §2); the predicate holds iff both are true. -/
@[grind] def pkHasUsableDefault (pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  pkDefaultTruthy && pkDefaultProvided

/- The decision that controls whether persisting a row skips the initial
   UPDATE probe and goes straight to an INSERT.

   The INSERT-only path is taken exactly when ALL of the following hold:
     * the request is an ordinary save, not a direct/unprocessed data load;
     * an INSERT is not already being forced by the caller;
     * the instance is being added for the first time;
     * its primary key carries a usable default value.
   Otherwise the incoming forcing flag is returned unchanged. In particular,
   for a direct/unprocessed data load the forcing is never introduced here, so
   an explicit primary key remains free to match an existing row through the
   ordinary UPDATE probe. -/
@[grind] def decidedForceInsert
    (raw forceInsert adding pkDefaultTruthy pkDefaultProvided : Bool) : Bool :=
  if !raw && !forceInsert && adding && pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
  then true
  else forceInsert
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the INSERT-forcing flag for a single-table persistence request.

   `raw` marks a direct/unprocessed data load (e.g. loading serialized
   fixtures); `forceInsert` is the caller-supplied request to force an INSERT;
   `adding` is whether the instance is being added for the first time;
   `pkDefaultTruthy` / `pkDefaultProvided` are the two observations about the
   primary key's default that together decide whether it carries a usable
   default value.

   All five inputs are read-only (none `mut`, directive 5): the routine inspects
   the five conditions and returns the resolved flag, mutating none of them. The
   resolved value is pinned exactly by `decidedForceInsert`: the INSERT-only path
   is forced only for an ordinary save of a freshly-added instance whose primary
   key has a usable default, and never for a direct/unprocessed data load. -/
method decideForceInsert
    (raw : Bool) (forceInsert : Bool) (adding : Bool)
    (pkDefaultTruthy : Bool) (pkDefaultProvided : Bool) return (out : Bool)
  ensures out = decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided
  ensures pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
            = (pkDefaultTruthy && pkDefaultProvided)
  do
    -- impl-start
    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then
      return true
    else
      return forceInsert
    -- impl-end

prove_correct decideForceInsert by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: postcondition `out = decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided` pins out as a TOTAL function of all 5 free Bools with NO preconditions => verify implies impl equals gold-guard function on all 32 configs => correct. meta.json axioms=[], deep_model_references=[]; no A-consumed/A-reference legs; refinement.md A1-A4=R (Bool bijection mapping.md §2), A5=I (deep model of guard); no kind-3. conformance_check.py shadow matches deep model, oracle = real patched guard, R-bijection self-checked in-script.

VERIFY (lean_verify.sh, exit0=verifies,1=error): pos_control(gold)=0 OK; atk_1 drop !raw (=Solution_prepatch bug)=1 rejected (fails on raw=T config => prepatch reproduced); atk_3 drop adding=1 rejected; atk_4 require only pkDefaultTruthy (boundary)=1 rejected; atk_5 else->false (control-flow-effect)=1 rejected; atk_6 always return forceInsert (partial/ungrounded)=1 rejected. TWO verified: atk_2 drop !forceInsert=0 (behaviorally identical: when forceInsert=T spec returns T=atk true, when forceInsert=F the !forceInsert conjunct is a no-op), atk_7 return decidedForceInsert oracle echo=0 (=gold). same_spec=True for all 8 files.

FALSIFICATION: materialized faithful refined patches for BOTH verifying wrong impls and ran official harness run_resolve('django__django-12209', ..., timeout=1800). atk_2.patch (add `not raw`, drop `not force_insert`): RESOLVED=True COMPLETED=True FLAKY=False. atk_7.patch (= gold patch.diff): RESOLVED=True COMPLETED=True. Both faithful patches RESOLVE => no verify-not-correct break. Commands: `bash scripts/lean_verify.sh <atk>.lean`; `run_resolve` via swebench_unified.harness. Docker+image (sweb.eval.x86_64.django_1776_django-12209) available. No verifying impl produces a non-resolving faithful patch => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) check for django__django-12209 velvet bundle. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True; the frozen spec view is identical. (2) Solution.lean verifies via lean_verify.sh (exit 0). Real callee confirmed: base_commit HEAD (5a68f024987) guard lacks the `not raw and` conjunct; the worktree is patched to add it — matching the gold patch behaviour. The modeled function decidedForceInsert = (if !raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided) then true else forceInsert), with pkHasUsableDefault = pkDefaultTruthy && pkDefaultProvided, exactly mirrors the patched guard `if (not raw and not force_insert and self._state.adding and self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED): force_insert = True`. (4) Exhaustive comparison over all 2^5=32 boolean input combinations: model output == real resolved force_insert on every input — zero divergences. Edge cases handled correctly by the R-abstraction: NOT_PROVIDED sentinel is truthy but yields pkDefaultProvided=false so pkHasUsableDefault=false (guard false), matching Python `default is not NOT_PROVIDED`; falsy-but-provided defaults (0/'') yield pkDefaultTruthy=false (guard false), matching Python truthiness. `out` is pinned to exactly the guard-resolved flag; no downstream behaviour is over-constrained. The spec is neither too strong nor drifted — it is a faithful deep model of the real guard. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Instance django__django-12209 / velvet. Gold edit = add `not raw and` as the leading conjunct of the INSERT-forcing guard in django/db/models/base.py:_save_table (single one-line diff).

Method: computed the actual spec view via swebench_unified.markers.spec_view(Solution.lean, VelvetBackend) and confirmed markers.same_spec(Solution, Solution_prepatch)=True — the spec/signature region is byte-identical, so the pre/post-patch discriminator lives only in the elided impl-start block, not in the consumer spec view. Ran swebench_unified.leakage.screen over the spec view against row['patch'] and problem_statement: passed=True, hard_failures=[]. Manual token scan of the spec view: base.py, _save_table, NOT_PROVIDED, force_insert, _state.adding, loaddata, uuid, django, and all bug/fix/regression/revert narration tokens are ABSENT.

Leakage judged vs PUBLIC problem_statement only (NOT hints_text). The problem_statement gives the symptom (explicit pk + default=uuid4 -> two INSERTs; loaddata regression) and floats keying on `pk_set` (the REJECTED approach). It never mentions `raw`, direct/unprocessed data loads, base.py, _save_table, or NOT_PROVIDED. The raw/serialization diagnosis lives only in hints_text (non-public).

Closest concern: the spec view makes `!raw` the leading conjunct of decidedForceInsert and comments 'never for a direct/unprocessed data load', and `raw` is not in problem_statement. Cleared because: (1) a faithful velvet/lean spec must pin correct behavior (verify=>resolve) by design — encoding the correct decision is not the same as leaking the gold PATCH artifact; the gate targets edit-localization, reproduced diff text, patched file paths/symbols, and bug/fix narration, none of which appear. (2) `raw` is a pre-existing _save_table(raw=False,...) parameter abstracted to a generic Bool modeling name, not a symbol the patch introduces; it is 3 chars (below the len>=4 distinctiveness threshold) and the changed gold line carries no def/class token. The normalized gold line 'notrawand' does not appear (Lean uses `!raw &&`). No patched file path, no diff markers, no reproduced gold line. (3) The comments specify required correct behavior (a behavioral spec / intended purpose), not 'this was a bug that was fixed' narration. The gold diff text appears only in refinement.md/mapping.md, which are auditor docs excluded from the consumer spec view.

From the spec view alone a solver gets a standalone Lean boolean-decision problem; they cannot recover which Python file/function to edit, the one-line diff, or the bug narrative beyond what any faithful spec must contain. Mechanical G-LEAK recorded pass; not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md). Consistent with recorded G-PANEL-3 verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
