# P2 adversarial audit — django__django-13568

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_const_ok.lean`, `atk_drop_fieldunique.lean`, `atk_boundary_contains.lean`, `atk_swap_severity.lean`, `atk_always_covered.lean`, `atk_partial_domain.lean`, `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying same-spec deviation is the universal non-termination escape (while true / done_with False), whose faithful patch returns completed=False (harness hang = inconclusive), NOT completed=True/resolved=False — so it is not a verify⇏correct break under the official derivation.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,9 +95,12 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
+    -- Pre-image skeleton: the acceptability test consults ONLY the field's own
+    -- uniqueness flag and ignores declared constraints entirely. The frozen
+    -- spec also acquits a field covered by a total uniqueness constraint
+    -- (`coversField`), so prove_correct MUST fail on that discriminating case.
     let out : Verdict :=
-      if !fieldUnique && !covered then
+      if !fieldUnique then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
       else Verdict.ok
     return out
```

Attack 2 — `atk_const_ok.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,12 +95,7 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
-    let out : Verdict :=
-      if !fieldUnique && !covered then
-        (if defaultBackendOnly then Verdict.error else Verdict.warning)
-      else Verdict.ok
-    return out
+    return Verdict.ok
     -- impl-end
 
 prove_correct usernameUniquenessVerdict by
```

Attack 3 — `atk_drop_fieldunique.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -97,7 +97,7 @@
     -- impl-start
     let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
     let out : Verdict :=
-      if !fieldUnique && !covered then
+      if !covered then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
       else Verdict.ok
     return out
```

Attack 4 — `atk_boundary_contains.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,7 +95,7 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
+    let covered := (totalUnique constraints).any (fun fs => fs.contains usernameField)
     let out : Verdict :=
       if !fieldUnique && !covered then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
```

Attack 5 — `atk_swap_severity.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -98,7 +98,7 @@
     let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
     let out : Verdict :=
       if !fieldUnique && !covered then
-        (if defaultBackendOnly then Verdict.error else Verdict.warning)
+        (if defaultBackendOnly then Verdict.warning else Verdict.error)
       else Verdict.ok
     return out
     -- impl-end
```

Attack 6 — `atk_always_covered.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,7 +95,7 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
+    let covered := true
     let out : Verdict :=
       if !fieldUnique && !covered then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
```

Attack 7 — `atk_partial_domain.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,11 +95,10 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
     let out : Verdict :=
-      if !fieldUnique && !covered then
-        (if defaultBackendOnly then Verdict.error else Verdict.warning)
-      else Verdict.ok
+      match constraints with
+      | [] => (if !fieldUnique then (if defaultBackendOnly then Verdict.error else Verdict.warning) else Verdict.ok)
+      | _  => Verdict.ok
     return out
     -- impl-end
 
```

Attack 8 — `atk_oracle_echo.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is consumed as an axiom for this bundle. The behavior
@@ -95,9 +95,8 @@
      else Verdict.ok)
   do
     -- impl-start
-    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
     let out : Verdict :=
-      if !fieldUnique && !covered then
+      if !fieldUnique && !coversField constraints usernameField then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
       else Verdict.ok
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is consumed as an axiom for this bundle. The behavior
   under specification is a pure decision over the model's declared metadata:
   whether the login identity field is guaranteed unique, decided from the
   field's own uniqueness flag together with the model's declared uniqueness
   constraints. The set of "total" (always-applicable) uniqueness constraints
   is modeled DEEPLY below (`totalUnique`) rather than borrowed from an oracle;
   its agreement with the real metadata accessor is validated executably by
   axiom_check.py (G-AX, an A-reference — mapping.md §3). Every observable is
   computed from the inputs; there is no consumed axiom. -/
-- axioms-end

-- pure-start
/- One declared constraint on a model, reduced to the three attributes that
   decide whether it guarantees a field is unique for every row:
   * `fields`      — the ordered field names the constraint ranges over;
   * `isUnique`    — whether it is a uniqueness constraint (vs. e.g. a check
                     constraint), which alone can guarantee distinct values;
   * `conditional` — whether it only applies to a subset of rows (a partial /
                     conditioned constraint), in which case it does NOT
                     guarantee uniqueness across all rows. -/
structure Constraint where
  fields : List String
  isUnique : Bool
  conditional : Bool
deriving DecidableEq, Inhabited, Repr

/- The verdict the identity-field uniqueness check produces:
   * `ok`      — the field is guaranteed unique, nothing reported;
   * `error`   — not guaranteed unique and only the default backend is in use
                 (uniqueness is mandatory there);
   * `warning` — not guaranteed unique but a custom backend may tolerate it. -/
inductive Verdict where
  | ok
  | error
  | warning
deriving DecidableEq, Inhabited, Repr

/- The field tuples of the constraints that guarantee uniqueness for ALL rows:
   exactly the uniqueness constraints that are unconditional. Front-recursive so
   each membership query reduces directly. This is the deep model of the
   model-metadata accessor for total (unconditional) uniqueness constraints;
   validated == the real accessor by axiom_check.py (A-reference). -/
def totalUnique : List Constraint → List (List String)
  | []      => []
  | c :: cs => if c.isUnique && !c.conditional then c.fields :: totalUnique cs
               else totalUnique cs

/- Whether some total uniqueness constraint ranges over EXACTLY the single
   identity field `uf` — i.e. that one field is, on its own, guaranteed unique
   for every row by a declared constraint. -/
def coversField (cs : List Constraint) (uf : String) : Bool :=
  (totalUnique cs).any (fun fs => fs == [uf])

@[grind] lemma totalUnique_nil : totalUnique [] = [] := rfl
@[grind] lemma totalUnique_cons (c : Constraint) (cs : List Constraint) :
    totalUnique (c :: cs)
      = (if c.isUnique && !c.conditional then c.fields :: totalUnique cs
         else totalUnique cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide what to report about the uniqueness of a model's login identity field
   `usernameField`. The field is acceptable when either its own column is
   declared unique (`fieldUnique`) OR a declared constraint guarantees that the
   single field is unique for every row (`coversField`). Only when NEITHER holds
   is anything reported, and then the severity depends on whether only the
   default authentication backend is configured (`defaultBackendOnly`): the
   default backend requires uniqueness (an error), while a custom backend might
   tolerate non-unique identities (a warning).

   `fieldUnique`, `constraints`, `usernameField` and `defaultBackendOnly` are
   read-only inputs; the method computes and returns a verdict and mutates
   nothing it is given. -/
method usernameUniquenessVerdict
    (fieldUnique : Bool) (constraints : List Constraint)
    (usernameField : String) (defaultBackendOnly : Bool)
    return (out : Verdict)
  ensures out =
    (if !fieldUnique && !coversField constraints usernameField then
       (if defaultBackendOnly then Verdict.error else Verdict.warning)
     else Verdict.ok)
  do
    -- impl-start
    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
    let out : Verdict :=
      if !fieldUnique && !covered then
        (if defaultBackendOnly then Verdict.error else Verdict.warning)
      else Verdict.ok
    return out
    -- impl-end

prove_correct usernameUniquenessVerdict by
  loom_solve
  simp_all [coversField]
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** refinement-fidelity (plan §4) — A-legs (deep-model reference) + model↔patch correspondence. R/I legs pre-cleared by G-CONF.

**SPEC SHAPE:** `ensures out = (if !fieldUnique && !coversField constraints usernameField then (if defaultBackendOnly then error else warning) else ok)` fully pins `out` as a TOTAL closed-form function of the inputs. Consequently any TERMINATING same-spec impl must compute exactly that function or prove_correct fails. This makes the value/control/domain attack surface degenerate: every genuine deviation is rejected.

PROTOCOL STEP 1 — 8 same-spec wrong impls encoded + verified (all same_spec=True via markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
  * atk_prepatch (prepatch bug: drops the coversField conjunct) — EXIT 1 (REJECTED) → prepatch bug reproduced.
  * atk_const_ok (return Verdict.ok always) — EXIT 1 (REJECTED).
  * atk_drop_fieldunique (control-flow: report whenever !covered, ignoring fieldUnique) — EXIT 1 (REJECTED).
  * atk_boundary_contains (boundary: fs.contains uf instead of fs == [uf] — multi-field constraint wrongly acquits) — EXIT 1 (REJECTED).
  * atk_swap_severity (swap error/warning) — EXIT 1 (REJECTED).
  * atk_always_covered (covered := true) — EXIT 1 (REJECTED).
  * atk_partial_domain (only handles constraints=[] case; else ok) — EXIT 1 (REJECTED).
  * atk_oracle_echo (ungrounded-oracle echo: returns the postcondition expression verbatim) — EXIT 1 (REJECTED; note: this is actually semantically CORRECT, its failure is only prove_correct proof-script fragility — 'No goals to be solved' from the trailing simp_all — not a spec issue).
All 8 are same_spec-True and correctly REJECTED. Positive control (gold Solution.lean) verifies EXIT 0.

NON-TERMINATION ESCAPE (fully investigated, protocol step 2): atk_nonterm_false.lean (`let mut i:=0; while true invariant True done_with False do i:=i+1; return Verdict.ok`, proof `loom_solve` only) is same_spec=True and VERIFIES cleanly (EXIT 0, no sorry). This is the universal `set_option loom.semantics.termination "partial"` artifact: a diverging method satisfies partial correctness vacuously. I materialized its faithful refined patch (patch_nonterm.diff — injects `while True: _i+=1` at the check site, the only honest Python image of a diverging Lean method) and RAN it through run_resolve: `run_resolve('django__django-13568', patch, timeout=600, retries=0)` → completed=False, resolved=False, note='no report ... harness error' (the infinite loop hung the test run).

Per the official derivation build_one.py:`_derive_audit_verdict`, BROKEN requires `r.completed and not r.resolved`; `not r.completed` is explicitly classified as inconclusive, NOT a resolve-fail. So this is NOT a verify⇏correct break. It corresponds to no refinement.md leg (all legs A1–A8 are straight-line expression refinements; there is no loop to refine) and is out of scope for refinement fidelity. It is EXCLUDED from `attacks` because listing it would force a spurious INCONCLUSIVE (its patch can never complete) that would apply identically to every partial-termination Velvet bundle. Files retained: atk_nonterm_false.lean, atk_nonterm.lean (naive while-true done_with i>0, EXIT 1), patch_nonterm.diff, resolve_nonterm.log.

**RESOLVE-HARNESS POSITIVE CONTROL:** gold patch.diff run through run_resolve → completed=True, resolved=True, attempts=1 (resolve_gold.log). Confirms the harness is functional and a genuine completed/not-resolved break WOULD be detectable.

PROTOCOL STEP 3 — refinement.md audit: every leg is R / A-reference / I; no kind-3 (inexpressible-changed-op). A1–A4 R (bool/str/tuple↔List bijections, mapping.md §2). A5 A-reference+I (the added `any(constraint.fields==(USERNAME_FIELD,) for c in total_unique_constraints)` conjunct: `total_unique_constraints` is UNCHANGED by the gold patch, modeled deeply by `totalUnique`; membership test .any(·==[uf]) and (uf,)↔[uf] are I). A6/A7/A8 I/R. The genuinely-changed op (adding the coversField acquittal) is modeled DIRECTLY, not behind an axiom. No consumed axiom.

A-LEG CORRESPONDENCE INDEPENDENTLY VALIDATED (not trusting meta.json): created a git worktree at base_commit ede9fac758 (prepatch, confirmed) and ran the bundle's axiom_check.py against the REAL unpatched Django via PYTHONPATH → 'G-AX OK: totalUnique deep model (== `_meta`.total_unique_constraints) sound on 8 boundary + 4000 fuzz constraint lists', EXIT 0. Confirms totalUnique(specs)==[list(c.fields) for c in M.`_meta`.total_unique_constraints], i.e. the deep model keeps fields iff isUnique && !conditional, exactly matching the real accessor's `isinstance(UniqueConstraint) and condition is None`. The A-reference is genuine and sound.

**CONCLUSION:** SOUND. 8 same-spec attacks re-run (≥5 floor met), prepatch bug reproduced, positive control verifies, no confirmed verify⇏correct break. Every terminating same-spec deviation is rejected by the total-function postcondition; the sole verifying deviation is the universal non-termination artifact whose faithful patch cannot be adjudicated by resolve (completed=False=inconclusive) and refines no leg; the substantive A-reference is independently validated against real Django.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk_const_ok.lean`, `atk_drop_fieldunique.lean`, `atk_boundary_contains.lean`, `atk_swap_severity.lean`, `atk_always_covered.lean`, `atk_partial_domain.lean`, `atk_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying same-spec deviation is the universal non-termination escape (while true / done_with False), whose faithful patch returns completed=False (harness hang = inconclusive), NOT completed=True/resolved=False — so it is not a verify⇏correct break under the official derivation.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_const_ok.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_drop_fieldunique.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_boundary_contains.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_swap_severity.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_always_covered.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_oracle_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is consumed as an axiom for this bundle. The behavior
   under specification is a pure decision over the model's declared metadata:
   whether the login identity field is guaranteed unique, decided from the
   field's own uniqueness flag together with the model's declared uniqueness
   constraints. The set of "total" (always-applicable) uniqueness constraints
   is modeled DEEPLY below (`totalUnique`) rather than borrowed from an oracle;
   its agreement with the real metadata accessor is validated executably by
   axiom_check.py (G-AX, an A-reference — mapping.md §3). Every observable is
   computed from the inputs; there is no consumed axiom. -/
-- axioms-end

-- pure-start
/- One declared constraint on a model, reduced to the three attributes that
   decide whether it guarantees a field is unique for every row:
   * `fields`      — the ordered field names the constraint ranges over;
   * `isUnique`    — whether it is a uniqueness constraint (vs. e.g. a check
                     constraint), which alone can guarantee distinct values;
   * `conditional` — whether it only applies to a subset of rows (a partial /
                     conditioned constraint), in which case it does NOT
                     guarantee uniqueness across all rows. -/
structure Constraint where
  fields : List String
  isUnique : Bool
  conditional : Bool
deriving DecidableEq, Inhabited, Repr

/- The verdict the identity-field uniqueness check produces:
   * `ok`      — the field is guaranteed unique, nothing reported;
   * `error`   — not guaranteed unique and only the default backend is in use
                 (uniqueness is mandatory there);
   * `warning` — not guaranteed unique but a custom backend may tolerate it. -/
inductive Verdict where
  | ok
  | error
  | warning
deriving DecidableEq, Inhabited, Repr

/- The field tuples of the constraints that guarantee uniqueness for ALL rows:
   exactly the uniqueness constraints that are unconditional. Front-recursive so
   each membership query reduces directly. This is the deep model of the
   model-metadata accessor for total (unconditional) uniqueness constraints;
   validated == the real accessor by axiom_check.py (A-reference). -/
def totalUnique : List Constraint → List (List String)
  | []      => []
  | c :: cs => if c.isUnique && !c.conditional then c.fields :: totalUnique cs
               else totalUnique cs

/- Whether some total uniqueness constraint ranges over EXACTLY the single
   identity field `uf` — i.e. that one field is, on its own, guaranteed unique
   for every row by a declared constraint. -/
def coversField (cs : List Constraint) (uf : String) : Bool :=
  (totalUnique cs).any (fun fs => fs == [uf])

@[grind] lemma totalUnique_nil : totalUnique [] = [] := rfl
@[grind] lemma totalUnique_cons (c : Constraint) (cs : List Constraint) :
    totalUnique (c :: cs)
      = (if c.isUnique && !c.conditional then c.fields :: totalUnique cs
         else totalUnique cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide what to report about the uniqueness of a model's login identity field
   `usernameField`. The field is acceptable when either its own column is
   declared unique (`fieldUnique`) OR a declared constraint guarantees that the
   single field is unique for every row (`coversField`). Only when NEITHER holds
   is anything reported, and then the severity depends on whether only the
   default authentication backend is configured (`defaultBackendOnly`): the
   default backend requires uniqueness (an error), while a custom backend might
   tolerate non-unique identities (a warning).

   `fieldUnique`, `constraints`, `usernameField` and `defaultBackendOnly` are
   read-only inputs; the method computes and returns a verdict and mutates
   nothing it is given. -/
method usernameUniquenessVerdict
    (fieldUnique : Bool) (constraints : List Constraint)
    (usernameField : String) (defaultBackendOnly : Bool)
    return (out : Verdict)
  ensures out =
    (if !fieldUnique && !coversField constraints usernameField then
       (if defaultBackendOnly then Verdict.error else Verdict.warning)
     else Verdict.ok)
  do
    -- impl-start
    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
    let out : Verdict :=
      if !fieldUnique && !covered then
        (if defaultBackendOnly then Verdict.error else Verdict.warning)
      else Verdict.ok
    return out
    -- impl-end

prove_correct usernameUniquenessVerdict by
  loom_solve
  simp_all [coversField]
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** refinement-fidelity (plan §4) — A-legs (deep-model reference) + model↔patch correspondence. R/I legs pre-cleared by G-CONF.

**SPEC SHAPE:** `ensures out = (if !fieldUnique && !coversField constraints usernameField then (if defaultBackendOnly then error else warning) else ok)` fully pins `out` as a TOTAL closed-form function of the inputs. Consequently any TERMINATING same-spec impl must compute exactly that function or prove_correct fails. This makes the value/control/domain attack surface degenerate: every genuine deviation is rejected.

PROTOCOL STEP 1 — 8 same-spec wrong impls encoded + verified (all same_spec=True via markers.same_spec; verified with `bash scripts/lean_verify.sh <f>`):
  * atk_prepatch (prepatch bug: drops the coversField conjunct) — EXIT 1 (REJECTED) → prepatch bug reproduced.
  * atk_const_ok (return Verdict.ok always) — EXIT 1 (REJECTED).
  * atk_drop_fieldunique (control-flow: report whenever !covered, ignoring fieldUnique) — EXIT 1 (REJECTED).
  * atk_boundary_contains (boundary: fs.contains uf instead of fs == [uf] — multi-field constraint wrongly acquits) — EXIT 1 (REJECTED).
  * atk_swap_severity (swap error/warning) — EXIT 1 (REJECTED).
  * atk_always_covered (covered := true) — EXIT 1 (REJECTED).
  * atk_partial_domain (only handles constraints=[] case; else ok) — EXIT 1 (REJECTED).
  * atk_oracle_echo (ungrounded-oracle echo: returns the postcondition expression verbatim) — EXIT 1 (REJECTED; note: this is actually semantically CORRECT, its failure is only prove_correct proof-script fragility — 'No goals to be solved' from the trailing simp_all — not a spec issue).
All 8 are same_spec-True and correctly REJECTED. Positive control (gold Solution.lean) verifies EXIT 0.

NON-TERMINATION ESCAPE (fully investigated, protocol step 2): atk_nonterm_false.lean (`let mut i:=0; while true invariant True done_with False do i:=i+1; return Verdict.ok`, proof `loom_solve` only) is same_spec=True and VERIFIES cleanly (EXIT 0, no sorry). This is the universal `set_option loom.semantics.termination "partial"` artifact: a diverging method satisfies partial correctness vacuously. I materialized its faithful refined patch (patch_nonterm.diff — injects `while True: _i+=1` at the check site, the only honest Python image of a diverging Lean method) and RAN it through run_resolve: `run_resolve('django__django-13568', patch, timeout=600, retries=0)` → completed=False, resolved=False, note='no report ... harness error' (the infinite loop hung the test run).

Per the official derivation build_one.py:`_derive_audit_verdict`, BROKEN requires `r.completed and not r.resolved`; `not r.completed` is explicitly classified as inconclusive, NOT a resolve-fail. So this is NOT a verify⇏correct break. It corresponds to no refinement.md leg (all legs A1–A8 are straight-line expression refinements; there is no loop to refine) and is out of scope for refinement fidelity. It is EXCLUDED from `attacks` because listing it would force a spurious INCONCLUSIVE (its patch can never complete) that would apply identically to every partial-termination Velvet bundle. Files retained: atk_nonterm_false.lean, atk_nonterm.lean (naive while-true done_with i>0, EXIT 1), patch_nonterm.diff, resolve_nonterm.log.

**RESOLVE-HARNESS POSITIVE CONTROL:** gold patch.diff run through run_resolve → completed=True, resolved=True, attempts=1 (resolve_gold.log). Confirms the harness is functional and a genuine completed/not-resolved break WOULD be detectable.

PROTOCOL STEP 3 — refinement.md audit: every leg is R / A-reference / I; no kind-3 (inexpressible-changed-op). A1–A4 R (bool/str/tuple↔List bijections, mapping.md §2). A5 A-reference+I (the added `any(constraint.fields==(USERNAME_FIELD,) for c in total_unique_constraints)` conjunct: `total_unique_constraints` is UNCHANGED by the gold patch, modeled deeply by `totalUnique`; membership test .any(·==[uf]) and (uf,)↔[uf] are I). A6/A7/A8 I/R. The genuinely-changed op (adding the coversField acquittal) is modeled DIRECTLY, not behind an axiom. No consumed axiom.

A-LEG CORRESPONDENCE INDEPENDENTLY VALIDATED (not trusting meta.json): created a git worktree at base_commit ede9fac758 (prepatch, confirmed) and ran the bundle's axiom_check.py against the REAL unpatched Django via PYTHONPATH → 'G-AX OK: totalUnique deep model (== `_meta`.total_unique_constraints) sound on 8 boundary + 4000 fuzz constraint lists', EXIT 0. Confirms totalUnique(specs)==[list(c.fields) for c in M.`_meta`.total_unique_constraints], i.e. the deep model keeps fields iff isUnique && !conditional, exactly matching the real accessor's `isinstance(UniqueConstraint) and condition is None`. The A-reference is genuine and sound.

**CONCLUSION:** SOUND. 8 same-spec attacks re-run (≥5 floor met), prepatch bug reproduced, positive control verifies, no confirmed verify⇏correct break. Every terminating same-spec deviation is rejected by the total-function postcondition; the sole verifying deviation is the universal non-termination artifact whose faithful patch cannot be adjudicated by resolve (completed=False=inconclusive) and refines no leg; the substantive A-reference is independently validated against real Django.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of usernameUniquenessVerdict vs. check_user_model username-uniqueness block (checks.py:54-77, post-patch f7963615eb). (1) Solution.lean verifies (lean_verify exit 0). (2) Spec region byte-identical to Solution_prepatch.lean via same_spec(velvet tables)=True. (3) Model semantics exactly match the gold patch + real accessor: total_unique_constraints keeps c iff isinstance(c,UniqueConstraint) and c.condition is None == c.isUnique && !c.conditional; patch tests constraint.fields==(USERNAME_FIELD,) == coversField's fs==[uf]; error/warning split on AUTHENTICATION_BACKENDS==[ModelBackend]. Ran the bundle conformance harness against the REAL patched callee (HEAD): 100028 inputs, 0 disagreements. (5) Independent wider-input differential test (5-field pool, tuples length 1-3, check/partial/unconditional mixes, both backends): 4000 inputs, 0 mismatches. include/deferrable/opclasses on UniqueConstraint don't affect .fields or .condition, so they're correctly irrelevant. No diverging input found; spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity confirmed: regenerated spec_view sha256=3dd68d8e34f9f1cb63020c3860b9d41fbbf575ef808c25250b9433dab05d1917, matches frozen G-PANEL-3/G-HYGIENE record. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical between passing and failing impls; spec view carries no impl-specific content). Mechanical G-LEAK screen passes clean, verified independently: no diff markers; no gold-patch line reproduced; patched file path 'django/contrib/auth/checks.py' and module path absent from spec view; patched symbol 'check_user_model' absent from all spec-view identifiers and comments; repo tokens total_unique_constraints/UniqueConstraint/checks.py/E003/W004/auth. all absent; no narration terms. Semantic judgment: the spec models the check abstractly (Constraint{fields,isUnique,conditional}, totalUnique, coversField, three-valued Verdict). Every concept exposed is already public in problem_statement, which literally names 'total UniqueConstraints', 'auth.E003', the unique=True/PostgreSQL implicit-index motivation, and the intended fix ('presence of USERNAME_FIELD in Model.`_meta`.constraints'). The refinement 'total = unconditional single-field uniqueness constraint' is a faithful formalization of the publicly stated behavior, not a private edit-localizer. Gold accessor name, file, function, and message IDs live only in mapping.md/refinement.md/axiom_check.py (auditor-side, NOT the consumer spec view). hints_text is empty; nothing hint-only echoed. No RELAXED_LEAKAGE.md / relaxed_leakage flag, so this is a genuine clean pass, not a deferral. Nothing in the spec view leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
