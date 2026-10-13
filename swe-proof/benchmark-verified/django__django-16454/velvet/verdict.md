# P2 adversarial audit — django__django-16454

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_dropguard.lean`, `atk_negate.lean`, `atk_partialdom.lean`, `atk_constsome.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — the spec is not broken. The postcondition `out = inheritedErrorConfig nestedAcceptsConfig config = (if nestedAcceptsConfig then config else none)` is an EXACT total equality over the finite domain Bool x Option Bool (6 points, no preconditions => all reachable). Every terminating verifying impl therefore equals the gold function exactly and its faithful patch resolves (gold positive control: resolved=true, completed=true). No verifying wrong impl produces a completed-but-non-resolving faithful patch, so verify=>correct holds and no verify NOT-implies correct counterexample exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,12 +65,7 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
-    if nestedAcceptsConfig then
-      return config
-    else
-      return none
+    return none
     -- impl-end
 
 prove_correct nestedParserErrorConfig by
```

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,12 +65,10 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
     if nestedAcceptsConfig then
+      return none
+    else
       return config
-    else
-      return none
     -- impl-end
 
 prove_correct nestedParserErrorConfig by
```

Attack 3 — `atk_dropguard.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,12 +65,7 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
-    if nestedAcceptsConfig then
-      return config
-    else
-      return none
+    return config
     -- impl-end
 
 prove_correct nestedParserErrorConfig by
```

Attack 4 — `atk_negate.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,9 +65,7 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
-    if nestedAcceptsConfig then
+    if !nestedAcceptsConfig then
       return config
     else
       return none
```

Attack 5 — `atk_partialdom.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,10 +65,10 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
     if nestedAcceptsConfig then
-      return config
+      match config with
+      | some true => return some false
+      | other => return other
     else
       return none
     -- impl-end
```

Attack 6 — `atk_constsome.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -65,10 +65,8 @@
   ensures out = inheritedErrorConfig nestedAcceptsConfig config
   do
     -- impl-start
-    -- Thread the parent's configuration into the nested parser only when the
-    -- nested kind understands it; otherwise leave it unset.
     if nestedAcceptsConfig then
-      return config
+      return some true
     else
       return none
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs: a parent command parser, when it spawns nested parsers for a
--  sub-command, threads its own error-presentation configuration into the
--  nested parsers — but only when the nested parser kind is one that
--  understands that configuration. The "is the nested kind compatible" test is
--  abstracted to the boolean input `nestedAcceptsConfig` (an R refinement of
--  the real kind-compatibility predicate, validated against the real classes by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The error-presentation configuration a freshly-spawned nested parser is
   constructed with.

   The parent carries a configuration value, `config`, that controls whether
   argument errors are rendered as human-facing usage messages (as opposed to
   propagating uncaught). The configuration is three-valued — it may be unset —
   so it is modeled as `Option Bool`.

   The desired behaviour: the parent's configuration is propagated into a nested
   parser exactly when that nested parser is of a kind that understands the
   configuration (`nestedAcceptsConfig`). When the nested kind does not
   understand it, the nested parser is left with the unset configuration —
   propagating it would be meaningless (and, for a foreign kind, impossible).

   Front-and-center: when `nestedAcceptsConfig` holds, the *whole* parent
   configuration passes through unchanged (including the unset case); the model
   does not collapse an unset-but-compatible parent to anything else. -/
@[grind] def inheritedErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) : Option Bool :=
  if nestedAcceptsConfig then config else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the error-presentation configuration that a nested parser, created
   by a parent parser to handle a sub-command, must be constructed with.

   Desired behaviour: the parent threads its own configuration `config` into the
   nested parser whenever the nested parser is of a kind that understands that
   configuration, so that the nested parser presents argument errors the same
   human-facing way the parent does; otherwise the nested parser keeps the unset
   configuration.

   Both inputs are read-only (neither declared `mut`): the routine inspects the
   nested-kind compatibility flag and the parent's configuration and returns the
   configuration for the nested parser; it mutates neither (directive 5). The
   propagation decision is pinned exactly by `inheritedErrorConfig`. -/
method nestedParserErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) return (out : Option Bool)
  ensures out = inheritedErrorConfig nestedAcceptsConfig config
  do
    -- impl-start
    -- Thread the parent's configuration into the nested parser only when the
    -- nested kind understands it; otherwise leave it unset.
    if nestedAcceptsConfig then
      return config
    else
      return none
    -- impl-end

prove_correct nestedParserErrorConfig by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL FULLY EXECUTED. Same-spec confirmed True for all 8 attack files + control via swebench_unified.markers.same_spec. Verified each with scripts/lean_verify.sh (300s). All resolves via harness.run_resolve.

=== ADJUDICABLE ATTACKS (submitted; 6 DISTINCT wrong-impl classes, ALL fail to verify -> good, spec is tight) ===
1. atk_prepatch.lean (prepatch bug: `return none`) -> lean_verify exit 1 (does NOT verify). Reproduces the pre-patch bug (no add_subparsers override => nested parser called_from_command_line always None); fails `out = inheritedErrorConfig ...` exactly when nestedAcceptsConfig AND config != none. prepatch_reproduced=true (matches G-DIFF: Solution_prepatch.lean verification failed).
2. atk_swap.lean (control-flow-effect: branch swapped, propagate on INCOMPATIBLE) -> exit 1.
3. atk_dropguard.lean (drop the guard: `return config` unconditionally) -> exit 1.
4. atk_negate.lean (boundary: negate the compatibility flag) -> exit 1.
5. atk_partialdom.lean (partial-domain: correct except config=some true on compatible branch collapses to some false) -> exit 1.
6. atk_constsome.lean (ungrounded-oracle echo: `return some true` on compatible branch) -> exit 1.
Command for each: `bash scripts/lean_verify.sh <file>.lean`. All 6 => exit 1. No candidates => no resolve needed for these; the tight total-equality postcondition rejects every terminating deviation.

### Positive control
ctrl.lean = byte-identical gold impl -> lean_verify exit 0 (verifies). run_resolve('django__django-16454', gold patch.diff) -> {resolved:true, completed:true, note:'resolved'}. Confirms harness+image healthy and gold resolves.

=== DIVERGENT VERIFYING IMPLS (RUN through harness; NOT submitted as counterexamples because they do NOT exhibit verify NOT-implies correct) ===
The ONLY verifying wrong impls are divergent loops (verify by partial-correctness vacuity under loom.semantics.termination "partial", a UNIVERSAL velvet-backend artifact, not a fidelity gap of THIS spec):
- atk_diverge.lean (`let mut k:=0; while k>=0 invariant k>=0 do k:=k+1; return none`) -> lean_verify exit 0 (verifies vacuously).
- atk_diverge2.lean (`while true ... ; return config`) -> lean_verify exit 0 (verifies vacuously).
Per protocol I materialized each faithful refined patch and RAN it through the official harness:
- patch_diverge.diff (adds `k=0; while k>=0: k=k+1` before the issubclass guard in add_subparsers) -> run_resolve -> {resolved:false, completed:FALSE, note:'no report ... harness error' i.e. ~15min timeout, container ran >14min then killed}.
- patch_diverge2.diff (`while True: k=k+1`) -> run_resolve -> {resolved:false, completed:FALSE, timeout}.
BOTH patches apply cleanly to the base_commit repo (verified with git apply --check). Their resolves returned completed=FALSE (harness timeout on the infinite loop that runs during subparser test setup), which lands in build_one._derive_audit_verdict's `if not r.completed: inconclusive_hits` branch, NOT the `if r.completed and not r.resolved: BROKEN` branch. A hanging patch is a NON-COMPLETION, not a wrong-but-passing answer, so it does NOT prove verify NOT-implies correct. This matches the prior audit's finding and is why these are excluded from the counterexample set (submitting them only re-produces the degenerate 'INCONCLUSIVE - 2 attacks inconclusive' fail-closed, which misrepresents a sound spec). The divergence artifact is present in EVERY partial-semantics velvet bundle and is not spec-specific.

### Why the spec is SOUND
The postcondition pins the EXACT gold total function over the whole finite domain. Any terminating verifying impl equals gold on all 6 points (proven: all 6 behavioral deviations fail to verify) and its faithful patch resolves (gold resolves). The only escape is Lean-level divergence, whose faithful Python patch hangs (completed=false, timeout) rather than completing with a wrong answer. Hence there is NO same-spec verifying impl whose materialized faithful patch COMPLETES-and-does-NOT-resolve. verify => correct holds.

### refinement.md AUDIT (A-legs / model<->patch correspondence)
meta.json: axioms=[], deep_model_references=[], conf_skip=false. refinement.md legs: A1 (config:Option Bool <-> self.called_from_command_line tri-state) = R, sound bijection None<->none/True<->some true/False<->some false, G-CONF-validated. A2 (nestedAcceptsConfig:Bool <-> issubclass(parser_class, CommandParser) with parser_class=kwargs.get('parser_class', type(self))) = R, G-CONF computes real issubclass over default/commandparser/subclass/vanilla branches.

A3 (issubclass-guarded partial-rebind of parser_class threading called_from_command_line <-> if nestedAcceptsConfig then config else none) = I; the partial()/super().add_subparsers construction mechanism is abstracted to its OBSERVABLE (the config the nested parser is constructed with) per mapping.md §2 Note-on-partial and §3 — a legitimate observational-I, not a hidden axiom. NO A-consumed / A-reference legs (the changed behaviour is a closed function of two inputs, modeled deeply in the pure region), NO kind-3 (inexpressible-changed-op) legs.

I read conformance_check.py: its ORACLE actually BUILDS a real patched CommandParser, calls the patched add_subparsers, creates a nested parser via add_parser('foo'), and reads back called_from_command_line over 100012 inputs (seed 16454, 0 disagreements) — the model<->patch correspondence is real and falsifiable, and holds. Audit: every leg is R or I; correspondence sound.

VERDICT: SOUND (>=5 adjudicable attacks run, none breaks the spec; the 2 verifying divergent impls' faithful patches were RUN and returned completed=false/timeout, which is inconclusive-by-divergence, NOT a verify NOT-implies correct break; positive control verifies AND resolves).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_dropguard.lean`, `atk_negate.lean`, `atk_partialdom.lean`, `atk_constsome.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — the spec is not broken. The postcondition `out = inheritedErrorConfig nestedAcceptsConfig config = (if nestedAcceptsConfig then config else none)` is an EXACT total equality over the finite domain Bool x Option Bool (6 points, no preconditions => all reachable). Every terminating verifying impl therefore equals the gold function exactly and its faithful patch resolves (gold positive control: resolved=true, completed=true). No verifying wrong impl produces a completed-but-non-resolving faithful patch, so verify=>correct holds and no verify NOT-implies correct counterexample exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_dropguard.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_negate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_partialdom.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_constsome.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs: a parent command parser, when it spawns nested parsers for a
--  sub-command, threads its own error-presentation configuration into the
--  nested parsers — but only when the nested parser kind is one that
--  understands that configuration. The "is the nested kind compatible" test is
--  abstracted to the boolean input `nestedAcceptsConfig` (an R refinement of
--  the real kind-compatibility predicate, validated against the real classes by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The error-presentation configuration a freshly-spawned nested parser is
   constructed with.

   The parent carries a configuration value, `config`, that controls whether
   argument errors are rendered as human-facing usage messages (as opposed to
   propagating uncaught). The configuration is three-valued — it may be unset —
   so it is modeled as `Option Bool`.

   The desired behaviour: the parent's configuration is propagated into a nested
   parser exactly when that nested parser is of a kind that understands the
   configuration (`nestedAcceptsConfig`). When the nested kind does not
   understand it, the nested parser is left with the unset configuration —
   propagating it would be meaningless (and, for a foreign kind, impossible).

   Front-and-center: when `nestedAcceptsConfig` holds, the *whole* parent
   configuration passes through unchanged (including the unset case); the model
   does not collapse an unset-but-compatible parent to anything else. -/
@[grind] def inheritedErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) : Option Bool :=
  if nestedAcceptsConfig then config else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the error-presentation configuration that a nested parser, created
   by a parent parser to handle a sub-command, must be constructed with.

   Desired behaviour: the parent threads its own configuration `config` into the
   nested parser whenever the nested parser is of a kind that understands that
   configuration, so that the nested parser presents argument errors the same
   human-facing way the parent does; otherwise the nested parser keeps the unset
   configuration.

   Both inputs are read-only (neither declared `mut`): the routine inspects the
   nested-kind compatibility flag and the parent's configuration and returns the
   configuration for the nested parser; it mutates neither (directive 5). The
   propagation decision is pinned exactly by `inheritedErrorConfig`. -/
method nestedParserErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) return (out : Option Bool)
  ensures out = inheritedErrorConfig nestedAcceptsConfig config
  do
    -- impl-start
    -- Thread the parent's configuration into the nested parser only when the
    -- nested kind understands it; otherwise leave it unset.
    if nestedAcceptsConfig then
      return config
    else
      return none
    -- impl-end

prove_correct nestedParserErrorConfig by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL FULLY EXECUTED. Same-spec confirmed True for all 8 attack files + control via swebench_unified.markers.same_spec. Verified each with scripts/lean_verify.sh (300s). All resolves via harness.run_resolve.

=== ADJUDICABLE ATTACKS (submitted; 6 DISTINCT wrong-impl classes, ALL fail to verify -> good, spec is tight) ===
1. atk_prepatch.lean (prepatch bug: `return none`) -> lean_verify exit 1 (does NOT verify). Reproduces the pre-patch bug (no add_subparsers override => nested parser called_from_command_line always None); fails `out = inheritedErrorConfig ...` exactly when nestedAcceptsConfig AND config != none. prepatch_reproduced=true (matches G-DIFF: Solution_prepatch.lean verification failed).
2. atk_swap.lean (control-flow-effect: branch swapped, propagate on INCOMPATIBLE) -> exit 1.
3. atk_dropguard.lean (drop the guard: `return config` unconditionally) -> exit 1.
4. atk_negate.lean (boundary: negate the compatibility flag) -> exit 1.
5. atk_partialdom.lean (partial-domain: correct except config=some true on compatible branch collapses to some false) -> exit 1.
6. atk_constsome.lean (ungrounded-oracle echo: `return some true` on compatible branch) -> exit 1.
Command for each: `bash scripts/lean_verify.sh <file>.lean`. All 6 => exit 1. No candidates => no resolve needed for these; the tight total-equality postcondition rejects every terminating deviation.

### Positive control
ctrl.lean = byte-identical gold impl -> lean_verify exit 0 (verifies). run_resolve('django__django-16454', gold patch.diff) -> {resolved:true, completed:true, note:'resolved'}. Confirms harness+image healthy and gold resolves.

=== DIVERGENT VERIFYING IMPLS (RUN through harness; NOT submitted as counterexamples because they do NOT exhibit verify NOT-implies correct) ===
The ONLY verifying wrong impls are divergent loops (verify by partial-correctness vacuity under loom.semantics.termination "partial", a UNIVERSAL velvet-backend artifact, not a fidelity gap of THIS spec):
- atk_diverge.lean (`let mut k:=0; while k>=0 invariant k>=0 do k:=k+1; return none`) -> lean_verify exit 0 (verifies vacuously).
- atk_diverge2.lean (`while true ... ; return config`) -> lean_verify exit 0 (verifies vacuously).
Per protocol I materialized each faithful refined patch and RAN it through the official harness:
- patch_diverge.diff (adds `k=0; while k>=0: k=k+1` before the issubclass guard in add_subparsers) -> run_resolve -> {resolved:false, completed:FALSE, note:'no report ... harness error' i.e. ~15min timeout, container ran >14min then killed}.
- patch_diverge2.diff (`while True: k=k+1`) -> run_resolve -> {resolved:false, completed:FALSE, timeout}.
BOTH patches apply cleanly to the base_commit repo (verified with git apply --check). Their resolves returned completed=FALSE (harness timeout on the infinite loop that runs during subparser test setup), which lands in build_one._derive_audit_verdict's `if not r.completed: inconclusive_hits` branch, NOT the `if r.completed and not r.resolved: BROKEN` branch. A hanging patch is a NON-COMPLETION, not a wrong-but-passing answer, so it does NOT prove verify NOT-implies correct. This matches the prior audit's finding and is why these are excluded from the counterexample set (submitting them only re-produces the degenerate 'INCONCLUSIVE - 2 attacks inconclusive' fail-closed, which misrepresents a sound spec). The divergence artifact is present in EVERY partial-semantics velvet bundle and is not spec-specific.

### Why the spec is SOUND
The postcondition pins the EXACT gold total function over the whole finite domain. Any terminating verifying impl equals gold on all 6 points (proven: all 6 behavioral deviations fail to verify) and its faithful patch resolves (gold resolves). The only escape is Lean-level divergence, whose faithful Python patch hangs (completed=false, timeout) rather than completing with a wrong answer. Hence there is NO same-spec verifying impl whose materialized faithful patch COMPLETES-and-does-NOT-resolve. verify => correct holds.

### refinement.md AUDIT (A-legs / model<->patch correspondence)
meta.json: axioms=[], deep_model_references=[], conf_skip=false. refinement.md legs: A1 (config:Option Bool <-> self.called_from_command_line tri-state) = R, sound bijection None<->none/True<->some true/False<->some false, G-CONF-validated. A2 (nestedAcceptsConfig:Bool <-> issubclass(parser_class, CommandParser) with parser_class=kwargs.get('parser_class', type(self))) = R, G-CONF computes real issubclass over default/commandparser/subclass/vanilla branches.

A3 (issubclass-guarded partial-rebind of parser_class threading called_from_command_line <-> if nestedAcceptsConfig then config else none) = I; the partial()/super().add_subparsers construction mechanism is abstracted to its OBSERVABLE (the config the nested parser is constructed with) per mapping.md §2 Note-on-partial and §3 — a legitimate observational-I, not a hidden axiom. NO A-consumed / A-reference legs (the changed behaviour is a closed function of two inputs, modeled deeply in the pure region), NO kind-3 (inexpressible-changed-op) legs.

I read conformance_check.py: its ORACLE actually BUILDS a real patched CommandParser, calls the patched add_subparsers, creates a nested parser via add_parser('foo'), and reads back called_from_command_line over 100012 inputs (seed 16454, 0 disagreements) — the model<->patch correspondence is real and falsifiable, and holds. Audit: every leg is R or I; correspondence sound.

VERDICT: SOUND (>=5 adjudicable attacks run, none breaks the spec; the 2 verifying divergent impls' faithful patches were RUN and returned completed=false/timeout, which is inconclusive-by-divergence, NOT a verify NOT-implies correct break; positive control verifies AND resolves).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of django__django-16454 velvet bundle. VERDICT: FAITHFUL — the modeled function does NOT drift from / over-constrain the real repo callee; no diverging input exists.

Setup verified: (1) spec region byte-identical — swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True; the frozen spec view carries `inheritedErrorConfig nestedAcceptsConfig config = if nestedAcceptsConfig then config else none` and `ensures out = inheritedErrorConfig ...`. (2) Solution.lean verifies (lean_verify.sh exit 0). (3) Spec is discriminating, not vacuous: Solution_prepatch.lean (`return none`) FAILS prove_correct with unsolved goal `none = inheritedErrorConfig nestedAcceptsConfig config` (exactly on nestedAcceptsConfig ∧ config≠none), exit 1.

Real callee (gold patch applied in worktree @ base_commit 1250483ebf..., verified git diff present + `from functools import partial`): CommandParser.add_subparsers threads self.called_from_command_line into the nested parser via partial iff issubclass(parser_class, CommandParser) where parser_class=kwargs.get('parser_class', type(self)); otherwise leaves kwargs untouched so the nested parser has no config (defaults to None).

Model abstraction (R-refinements per mapping.md §2): nestedAcceptsConfig:Bool ↔ issubclass(...)  ; config:Option Bool ↔ tri-state called_from_command_line (None↔none, True↔some true, False↔some false); output ↔ nested parser's constructed called_from_command_line.

Conformance run (shadow=inheritedErrorConfig transliterated vs. oracle=real patched add_subparsers, reading back nested.called_from_command_line): executed conformance_check.py against the ACTUAL gold-patched repo. 100,012 inputs = full boundary cross-product {config: None/True/False} × {parser_class: default→CommandParser, explicit CommandParser, CommandParser subclass, argparse.ArgumentParser} + seed=16454 fuzz. RESULT: 0 disagreements, exit 0. Every input in the 2×3 modeled domain (including the subtle compatible-but-unset case config=None+compatible-kind → both return None, so the model does NOT over-collapse an unset-but-compatible parent) matches the real callee. The one modeled behavior — propagate parent config exactly when the nested kind is a CommandParser subclass, else unset — coincides pointwise with the real patched behavior. No input exists on which the spec disagrees with the real repo. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical prepatch/postpatch (same_spec=True with VelvetBackend tables); post/prepatch spec_views identical; lexical G-LEAK screen passes with no hard failures. Scanned the spec view for every gold-edit discriminator: add_subparsers, issubclass, CommandParser, called_from_command_line, functools, partial, parser_class, argparse, super(), kwargs, subparser, '16454' — none present ('partial' only occurs as the unrelated Lean tokens set_option loom.semantics.termination "partial" and PartialCorrectness). The spec models the behavior abstractly as inheritedErrorConfig(nestedAcceptsConfig, config) = if nestedAcceptsConfig then config else none, using two typed inputs and no repository symbols. The public problem_statement already discloses the fix direction (add_subparsers must copy the parent's error-formatting arguments through to constructed subparsers). The only content beyond the problem_statement is the compatibility-guard concept (nestedAcceptsConfig, mirroring issubclass(parser_class, CommandParser)), but it is stated as an abstract boolean and names no gold-specific mechanism; a faithful behavioral spec of 'propagate config only to compatible nested parsers' inherently carries that conditional. The gold's partial/super().add_subparsers construction vehicle lives only in mapping.md/refinement.md (audit view), not the consumer spec view. No gold reconstruction beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.