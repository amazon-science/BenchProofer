# P2 adversarial audit — astropy__astropy-7606

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies against this frozen spec, so there is no verifying-wrong-impl whose faithful refined patch could be run through run_resolve. The spec is not broken by any of the 10 distinct attacks.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,13 +114,9 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
     let result : Except CmpErr Verdict :=
       match outcome with
-      | .uninterpretable => Except.ok .deferred
+      | .uninterpretable => Except.error .interpretationEscaped
       | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
       | .otherKind       => Except.ok (.decided false)
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,13 +114,9 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
     let result : Except CmpErr Verdict :=
       match outcome with
-      | .uninterpretable => Except.ok .deferred
+      | .uninterpretable => Except.ok (.decided false)
       | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
       | .otherKind       => Except.ok (.decided false)
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,14 +114,10 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
     let result : Except CmpErr Verdict :=
       match outcome with
       | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
+      | .sameKind name   => Except.ok (.decided (decide (selfName != name)))
       | .otherKind       => Except.ok (.decided false)
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,15 +114,11 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
     let result : Except CmpErr Verdict :=
       match outcome with
       | .uninterpretable => Except.ok .deferred
       | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
+      | .otherKind       => Except.ok (.decided true)
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,16 +114,7 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
-    let result : Except CmpErr Verdict :=
-      match outcome with
-      | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
-    return result
+    return compareSpec selfName outcome
     -- impl-end
 
 prove_correct compareName by
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,16 +114,7 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
-    let result : Except CmpErr Verdict :=
-      match outcome with
-      | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
-    return result
+    return Except.ok .deferred
     -- impl-end
 
 prove_correct compareName by
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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,14 +114,10 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
     let result : Except CmpErr Verdict :=
       match outcome with
       | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
+      | .sameKind _name  => Except.ok (.decided true)
       | .otherKind       => Except.ok (.decided false)
     return result
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,16 +114,10 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
-    let result : Except CmpErr Verdict :=
-      match outcome with
-      | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
-    return result
+    let mut i : Nat := 0
+    while true do
+      i := i + 1
+    return Except.ok (.decided false)
     -- impl-end
 
 prove_correct compareName by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,16 +114,14 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
-    let result : Except CmpErr Verdict :=
-      match outcome with
-      | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
-    return result
+    match outcome with
+    | .uninterpretable =>
+      let mut i : Nat := 0
+      while true do
+        i := i + 1
+      return Except.ok .deferred
+    | .sameKind name   => return Except.ok (.decided (decide (selfName = name)))
+    | .otherKind       => return Except.ok (.decided false)
     -- impl-end
 
 prove_correct compareName by
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. The only
@@ -114,16 +114,14 @@
   ensures outcome = .otherKind → out = Except.ok (.decided false)
   do
     -- impl-start
-    -- Dispatch on the interpretation outcome. An operand that could not be
-    -- interpreted yields a graceful decline rather than an escaped failure; an
-    -- operand of this same kind compares equal iff the names coincide; an
-    -- operand of a different kind is unequal.
-    let result : Except CmpErr Verdict :=
-      match outcome with
-      | .uninterpretable => Except.ok .deferred
-      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
-      | .otherKind       => Except.ok (.decided false)
-    return result
+    match outcome with
+    | .uninterpretable =>
+      let mut i : Nat := 0
+      while true do
+        i := i + 1
+      return Except.ok (.decided false)
+    | .sameKind name   => return Except.ok (.decided (decide (selfName = name)))
+    | .otherKind       => return Except.ok (.decided false)
     -- impl-end
 
 prove_correct compareName by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-step that is not pinned here is the attempt to interpret the arbitrary
   right-hand operand as a value of this domain; that interpretation is an
   UNCHANGED callee whose three mutually-exclusive outcomes are the ONLY thing
   the desired behaviour reacts to. It is modeled as a FREE input
   (`InterpretOutcome`, see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract — strictly weaker than any
   concrete interpreter (directive 7). The behaviour this bundle pins — how each
   outcome becomes a comparison verdict, and that a failed interpretation never
   escapes as an error — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of attempting to interpret the arbitrary right-hand operand as a
   value of this domain, in the three mutually-exclusive shapes the comparison
   reacts to:
     * `uninterpretable` — the operand cannot be interpreted at all (the attempt
                           fails); e.g. it is absent/null, a bare number, or an
                           object of an unrelated type;
     * `sameKind name`   — the operand interprets to a value of THIS same kind,
                           identified solely by the name `name`;
     * `otherKind`       — the operand interprets to a value of a DIFFERENT kind
                           in this domain (one not identified by a bare name).
   These three cases are genuinely different operands and must stay apart. -/
inductive InterpretOutcome where
  | uninterpretable
  | sameKind (name : List Char)
  | otherKind
  deriving DecidableEq, Inhabited

/- The result the comparison must hand back. A comparison NEVER fails outright:
     * `decided b` — a definite boolean verdict `b` for this equality;
     * `deferred`  — no verdict is asserted here; the comparison declines and
                     hands off to the reflected/identity comparison instead
                     (a definite, non-error outcome — the operand is simply not
                     comparable as a value of this domain).
   `deferred` is the well-behaved answer for an operand that could not be
   interpreted: it must be produced INSTEAD of letting the interpretation's
   failure escape to the caller. -/
inductive Verdict where
  | decided (b : Bool)
  | deferred
  deriving DecidableEq, Inhabited

/- A failure shape the desired behaviour must NEVER produce: the comparison let
   the interpretation's failure escape to the caller as an error instead of
   declining gracefully. A correct comparison always yields a `Verdict`
   (`Except.ok`), never this. -/
inductive CmpErr where
  | interpretationEscaped
  deriving DecidableEq, Inhabited

/- The desired comparison result, as a function of this value's own `selfName`
   and the interpretation outcome of the operand:
     * an operand that could not be interpreted yields `deferred` — the
       interpretation's failure is absorbed, never escaping as an error;
     * an operand of THIS same kind compares equal exactly when the two names
       coincide (`decide (selfName = name)`);
     * an operand of a DIFFERENT kind is unequal (`decided false`): a value of
       this kind is never equal to one of another kind.
   Every outcome yields a `Verdict` (`Except.ok`); the result is never an
   escaped error. -/
def compareSpec (selfName : List Char) (o : InterpretOutcome) : Except CmpErr Verdict :=
  match o with
  | .uninterpretable => Except.ok .deferred
  | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
  | .otherKind       => Except.ok (.decided false)

@[grind] lemma compareSpec_uninterpretable (selfName : List Char) :
    compareSpec selfName .uninterpretable = Except.ok .deferred := rfl
@[grind] lemma compareSpec_sameKind (selfName name : List Char) :
    compareSpec selfName (.sameKind name)
      = Except.ok (.decided (decide (selfName = name))) := rfl
@[grind] lemma compareSpec_otherKind (selfName : List Char) :
    compareSpec selfName .otherKind = Except.ok (.decided false) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare a value of this domain — identified solely by its `selfName` — for
   equality against an arbitrary operand. The operand is first interpreted as a
   value of the domain; `outcome` is that (unchanged) interpretation's result.
   `selfName` and `outcome` are read-only (not `mut`); the comparison builds a
   fresh verdict and mutates neither (directive 5). Desired behaviour:
     * if the operand cannot be interpreted, the comparison must DECLINE
       (`deferred`) rather than let the interpretation's failure escape to the
       caller — comparison must always return a verdict, never fail;
     * if the operand is a value of this same kind, the verdict is whether the
       two names coincide;
     * if the operand is a value of a different kind, the verdict is unequal.
   In particular the result is ALWAYS a verdict (`Except.ok _`), never an
   escaped error. -/
method compareName (selfName : List Char) (outcome : InterpretOutcome)
    return (out : Except CmpErr Verdict)
  ensures out = compareSpec selfName outcome
  ensures ∃ v, out = Except.ok v
  ensures outcome = .uninterpretable → out = Except.ok .deferred
  ensures ∀ name, outcome = .sameKind name →
    out = Except.ok (.decided (decide (selfName = name)))
  ensures outcome = .otherKind → out = Except.ok (.decided false)
  do
    -- impl-start
    -- Dispatch on the interpretation outcome. An operand that could not be
    -- interpreted yields a graceful decline rather than an escaped failure; an
    -- operand of this same kind compares equal iff the names coincide; an
    -- operand of a different kind is unequal.
    let result : Except CmpErr Verdict :=
      match outcome with
      | .uninterpretable => Except.ok .deferred
      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
      | .otherKind       => Except.ok (.decided false)
    return result
    -- impl-end

prove_correct compareName by
  loom_solve
  cases outcome <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: astropy__astropy-7606 velvet. Spec compareName(selfName:List Char, outcome:InterpretOutcome) has an EXACT-VALUE postcondition `out = compareSpec selfName outcome` PLUS 4 per-constructor ensures clauses. compareSpec is total and pins the output for all 3 InterpretOutcome constructors, so any value-differing impl is refuted. Frozen proof script: `loom_solve; cases outcome <;> simp_all`.

SAME-SPEC: all 10 attacks + pos_control return same_spec=True (impl-region-only edits, axioms/pure/pre/post byte-identical), confirmed via swebench_unified.markers.same_spec with velvet backend.

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap; run concurrently in batches of <=4):
- pos_control (exact correct impl): EXIT=0 (VERIFIES). Positive control good.
- atk_1 PREPATCH BUG (uninterpretable => Except.error .interpretationEscaped): EXIT=1. Reproduces the pre-patch escape; correctly refuted by the `uninterpretable -> deferred` and `exists v, ok v` clauses. prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (uninterpretable => decided false instead of deferred): EXIT=1.
- atk_3 BOUNDARY (sameKind => decide (selfName != name), negated equality): EXIT=1.
- atk_4 CONTROL-FLOW-EFFECT (otherKind => decided true instead of false): EXIT=1.
- atk_5 UNGROUNDED-ORACLE ECHO (`return compareSpec selfName outcome`): EXIT=1 — fails only on the frozen tactic `simp_all made no progress` (a proof-script artifact; value is identical to spec but the frozen script's shape rejects the restructuring). Still refuted, so not a soundness hole.
- atk_6 COLLAPSE (always Except.ok .deferred): EXIT=1.
- atk_7 CONSTANT-BRANCH (sameKind => decided true, ignoring name): EXIT=1.
- atk_8 DIVERGENCE/VACUITY (unconditional `while true` then wrong return): EXIT=1 — `No goals to be solved`. loom_solve discharges the vacuous partial-correctness VC, leaving frozen `cases outcome <;> simp_all` with no goals => error.
- atk_9 CONDITIONAL DIVERGENCE (diverge on uninterpretable branch, correct returns elsewhere): EXIT=1 — `No goals to be solved`.
- atk_10 CONDITIONAL DIVERGENCE + WRONG RETURN (diverge on uninterpretable, wrong value): EXIT=1 — `No goals to be solved`.

The `termination "partial"` + `choice "demonic"` divergence-vacuity exploit (atk_8/9/10) — the primary soundness threat for a partial-correctness Velvet spec — is closed by the frozen proof script's fixed shape: loom_solve already closes the whole VC, so the trailing `cases outcome <;> simp_all` errors with `No goals to be solved` rather than silently succeeding.

No wrong impl verifies => no faithful refined patch to materialize => no run_resolve required (protocol step 2 vacuous: it triggers only for a VERIFYING wrong impl).

REFINEMENT AUDIT (refinement.md): patch.diff at benchmark-verified/astropy__astropy-7606/velvet/patch.diff matches the two hunks quoted in refinement.md verbatim (UnrecognizedUnit.__eq__ @1710 gains try/except -> NotImplemented + isinstance(other, type(self)); UnitBase.__eq__ @728 changes `return False` -> `return NotImplemented`). Every leg A1-A6 is tagged R (type refinement: str<->List Char, NotImplemented<->deferred, bool<->decided; or free-input abstraction of the unchanged Unit(...) callee) or I (identical concrete op).

NO module-level axiom (confirmed: axioms region is prose only), so G-AX=skip and there is no A-consumed/A-reference leg to validate a callee contract — consistent with the free-input modeling of the unchanged interpreter (directive 7, strictly weaker than any concrete interpreter). NO kind-3 (inexpressible-changed-op): the operation that genuinely changed (catch interpretation failure and decline) is modeled DEEPLY as compareSpec's `.uninterpretable => Except.ok .deferred` branch (I op, transliterated by G-CONF), not hidden behind an axiom. The deep model compareSpec faithfully mirrors the gold body on all three outcomes; conformance_check.py drives the REAL Unit(...) interpreter over boundary + 120000 fuzzed operands (seed 7606) to refute the R/I legs. Site B (UnitBase.__eq__ False->NotImplemented) is argued behaviourally inert for the harness (reflected/identity fallback yields same False/True) and carries no separate prepatch — consistent with mapping.md 1.1.

CONCLUSION: verify => correct holds for this bundle. No verify-but-wrong witness exists across prepatch/partial-domain/boundary/control-flow/echo/divergence attack classes. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies against this frozen spec, so there is no verifying-wrong-impl whose faithful refined patch could be run through run_resolve. The spec is not broken by any of the 10 distinct attacks.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-step that is not pinned here is the attempt to interpret the arbitrary
   right-hand operand as a value of this domain; that interpretation is an
   UNCHANGED callee whose three mutually-exclusive outcomes are the ONLY thing
   the desired behaviour reacts to. It is modeled as a FREE input
   (`InterpretOutcome`, see the method signature): the postconditions hold for
   EVERY value of it, so it is owed no contract — strictly weaker than any
   concrete interpreter (directive 7). The behaviour this bundle pins — how each
   outcome becomes a comparison verdict, and that a failed interpretation never
   escapes as an error — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of attempting to interpret the arbitrary right-hand operand as a
   value of this domain, in the three mutually-exclusive shapes the comparison
   reacts to:
     * `uninterpretable` — the operand cannot be interpreted at all (the attempt
                           fails); e.g. it is absent/null, a bare number, or an
                           object of an unrelated type;
     * `sameKind name`   — the operand interprets to a value of THIS same kind,
                           identified solely by the name `name`;
     * `otherKind`       — the operand interprets to a value of a DIFFERENT kind
                           in this domain (one not identified by a bare name).
   These three cases are genuinely different operands and must stay apart. -/
inductive InterpretOutcome where
  | uninterpretable
  | sameKind (name : List Char)
  | otherKind
  deriving DecidableEq, Inhabited

/- The result the comparison must hand back. A comparison NEVER fails outright:
     * `decided b` — a definite boolean verdict `b` for this equality;
     * `deferred`  — no verdict is asserted here; the comparison declines and
                     hands off to the reflected/identity comparison instead
                     (a definite, non-error outcome — the operand is simply not
                     comparable as a value of this domain).
   `deferred` is the well-behaved answer for an operand that could not be
   interpreted: it must be produced INSTEAD of letting the interpretation's
   failure escape to the caller. -/
inductive Verdict where
  | decided (b : Bool)
  | deferred
  deriving DecidableEq, Inhabited

/- A failure shape the desired behaviour must NEVER produce: the comparison let
   the interpretation's failure escape to the caller as an error instead of
   declining gracefully. A correct comparison always yields a `Verdict`
   (`Except.ok`), never this. -/
inductive CmpErr where
  | interpretationEscaped
  deriving DecidableEq, Inhabited

/- The desired comparison result, as a function of this value's own `selfName`
   and the interpretation outcome of the operand:
     * an operand that could not be interpreted yields `deferred` — the
       interpretation's failure is absorbed, never escaping as an error;
     * an operand of THIS same kind compares equal exactly when the two names
       coincide (`decide (selfName = name)`);
     * an operand of a DIFFERENT kind is unequal (`decided false`): a value of
       this kind is never equal to one of another kind.
   Every outcome yields a `Verdict` (`Except.ok`); the result is never an
   escaped error. -/
def compareSpec (selfName : List Char) (o : InterpretOutcome) : Except CmpErr Verdict :=
  match o with
  | .uninterpretable => Except.ok .deferred
  | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
  | .otherKind       => Except.ok (.decided false)

@[grind] lemma compareSpec_uninterpretable (selfName : List Char) :
    compareSpec selfName .uninterpretable = Except.ok .deferred := rfl
@[grind] lemma compareSpec_sameKind (selfName name : List Char) :
    compareSpec selfName (.sameKind name)
      = Except.ok (.decided (decide (selfName = name))) := rfl
@[grind] lemma compareSpec_otherKind (selfName : List Char) :
    compareSpec selfName .otherKind = Except.ok (.decided false) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare a value of this domain — identified solely by its `selfName` — for
   equality against an arbitrary operand. The operand is first interpreted as a
   value of the domain; `outcome` is that (unchanged) interpretation's result.
   `selfName` and `outcome` are read-only (not `mut`); the comparison builds a
   fresh verdict and mutates neither (directive 5). Desired behaviour:
     * if the operand cannot be interpreted, the comparison must DECLINE
       (`deferred`) rather than let the interpretation's failure escape to the
       caller — comparison must always return a verdict, never fail;
     * if the operand is a value of this same kind, the verdict is whether the
       two names coincide;
     * if the operand is a value of a different kind, the verdict is unequal.
   In particular the result is ALWAYS a verdict (`Except.ok _`), never an
   escaped error. -/
method compareName (selfName : List Char) (outcome : InterpretOutcome)
    return (out : Except CmpErr Verdict)
  ensures out = compareSpec selfName outcome
  ensures ∃ v, out = Except.ok v
  ensures outcome = .uninterpretable → out = Except.ok .deferred
  ensures ∀ name, outcome = .sameKind name →
    out = Except.ok (.decided (decide (selfName = name)))
  ensures outcome = .otherKind → out = Except.ok (.decided false)
  do
    -- impl-start
    -- Dispatch on the interpretation outcome. An operand that could not be
    -- interpreted yields a graceful decline rather than an escaped failure; an
    -- operand of this same kind compares equal iff the names coincide; an
    -- operand of a different kind is unequal.
    let result : Except CmpErr Verdict :=
      match outcome with
      | .uninterpretable => Except.ok .deferred
      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))
      | .otherKind       => Except.ok (.decided false)
    return result
    -- impl-end

prove_correct compareName by
  loom_solve
  cases outcome <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: astropy__astropy-7606 velvet. Spec compareName(selfName:List Char, outcome:InterpretOutcome) has an EXACT-VALUE postcondition `out = compareSpec selfName outcome` PLUS 4 per-constructor ensures clauses. compareSpec is total and pins the output for all 3 InterpretOutcome constructors, so any value-differing impl is refuted. Frozen proof script: `loom_solve; cases outcome <;> simp_all`.

SAME-SPEC: all 10 attacks + pos_control return same_spec=True (impl-region-only edits, axioms/pure/pre/post byte-identical), confirmed via swebench_unified.markers.same_spec with velvet backend.

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap; run concurrently in batches of <=4):
- pos_control (exact correct impl): EXIT=0 (VERIFIES). Positive control good.
- atk_1 PREPATCH BUG (uninterpretable => Except.error .interpretationEscaped): EXIT=1. Reproduces the pre-patch escape; correctly refuted by the `uninterpretable -> deferred` and `exists v, ok v` clauses. prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (uninterpretable => decided false instead of deferred): EXIT=1.
- atk_3 BOUNDARY (sameKind => decide (selfName != name), negated equality): EXIT=1.
- atk_4 CONTROL-FLOW-EFFECT (otherKind => decided true instead of false): EXIT=1.
- atk_5 UNGROUNDED-ORACLE ECHO (`return compareSpec selfName outcome`): EXIT=1 — fails only on the frozen tactic `simp_all made no progress` (a proof-script artifact; value is identical to spec but the frozen script's shape rejects the restructuring). Still refuted, so not a soundness hole.
- atk_6 COLLAPSE (always Except.ok .deferred): EXIT=1.
- atk_7 CONSTANT-BRANCH (sameKind => decided true, ignoring name): EXIT=1.
- atk_8 DIVERGENCE/VACUITY (unconditional `while true` then wrong return): EXIT=1 — `No goals to be solved`. loom_solve discharges the vacuous partial-correctness VC, leaving frozen `cases outcome <;> simp_all` with no goals => error.
- atk_9 CONDITIONAL DIVERGENCE (diverge on uninterpretable branch, correct returns elsewhere): EXIT=1 — `No goals to be solved`.
- atk_10 CONDITIONAL DIVERGENCE + WRONG RETURN (diverge on uninterpretable, wrong value): EXIT=1 — `No goals to be solved`.

The `termination "partial"` + `choice "demonic"` divergence-vacuity exploit (atk_8/9/10) — the primary soundness threat for a partial-correctness Velvet spec — is closed by the frozen proof script's fixed shape: loom_solve already closes the whole VC, so the trailing `cases outcome <;> simp_all` errors with `No goals to be solved` rather than silently succeeding.

No wrong impl verifies => no faithful refined patch to materialize => no run_resolve required (protocol step 2 vacuous: it triggers only for a VERIFYING wrong impl).

REFINEMENT AUDIT (refinement.md): patch.diff at benchmark-verified/astropy__astropy-7606/velvet/patch.diff matches the two hunks quoted in refinement.md verbatim (UnrecognizedUnit.__eq__ @1710 gains try/except -> NotImplemented + isinstance(other, type(self)); UnitBase.__eq__ @728 changes `return False` -> `return NotImplemented`). Every leg A1-A6 is tagged R (type refinement: str<->List Char, NotImplemented<->deferred, bool<->decided; or free-input abstraction of the unchanged Unit(...) callee) or I (identical concrete op).

NO module-level axiom (confirmed: axioms region is prose only), so G-AX=skip and there is no A-consumed/A-reference leg to validate a callee contract — consistent with the free-input modeling of the unchanged interpreter (directive 7, strictly weaker than any concrete interpreter). NO kind-3 (inexpressible-changed-op): the operation that genuinely changed (catch interpretation failure and decline) is modeled DEEPLY as compareSpec's `.uninterpretable => Except.ok .deferred` branch (I op, transliterated by G-CONF), not hidden behind an axiom. The deep model compareSpec faithfully mirrors the gold body on all three outcomes; conformance_check.py drives the REAL Unit(...) interpreter over boundary + 120000 fuzzed operands (seed 7606) to refute the R/I legs. Site B (UnitBase.__eq__ False->NotImplemented) is argued behaviourally inert for the harness (reflected/identity fallback yields same False/True) and carries no separate prepatch — consistent with mapping.md 1.1.

CONCLUSION: verify => correct holds for this bundle. No verify-but-wrong witness exists across prepatch/partial-domain/boundary/control-flow/echo/divergence attack classes. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-real-callee) analysis for astropy__astropy-7606 velvet bundle.

### Setup
- same_spec(Solution.lean, Solution_prepatch.lean) with the velvet LanguageTables = TRUE: the spec region (inductives InterpretOutcome/Verdict/CmpErr, compareSpec + @[grind] lemmas, the compareName signature/ensures) is frozen; only the impl region differs (prepatch escapes .uninterpretable as Except.error, thus failing the frozen spec -> valid G-DIFF).
- Modeled function compareName abstracts UnrecognizedUnit.__eq__ (astropy/units/core.py:1710, patched). The unchanged operand interpreter Unit(other, parse_strict='silent') is modeled as a FREE input `outcome : InterpretOutcome` with exactly 3 outcomes: uninterpretable (Unit raises ValueError/UnitsError/TypeError), sameKind name (interprets to an UnrecognizedUnit named name), otherKind (interprets to any non-UnrecognizedUnit). compareSpec maps them to deferred / decided(selfName=name) / decided false, always Except.ok.

EMPIRICAL CHECK against the REAL patched repo (base_commit 3cedd79e..., ext modules built, py3.8 venv w/ numpy):
- Ran the bundle's own conformance_check.py (SHADOW=transliterated compareSpec driving the REAL live Unit(...); ORACLE=real gold-patched UnrecognizedUnit.__eq__ observing raw NotImplemented/bool/raise). Result: G-CONF OK, 0 disagreements over 120,217 operands (seed 7606).
- Additional adversarial differential probe (self-compare, equal-named UnrecognizedUnit, Quantity 2*m, dimensionless, numpy arrays/scalars, composite unit m/s, complex, range, class objects, Ellipsis, NotImplemented, whitespace/case name variants '  FOO  '/'foo', 'FOO/BAR'): 0 divergences. Every real verdict matched the model (NotImplemented<->deferred, bool<->decided b, name equality is exact code-point equality).

### ABSTRACTION-DOMAIN BOUNDARY (checked, and NOT a drift):
- The spec's totality claim (ensures ∃ v, out=Except.ok v / A6 'never escapes') is only about the 3 modeled interpreter outcomes. The real patched __eq__ catches only. I constructed operands where Unit(...) raises a DIFFERENT exception (BadStr.__str__ -> KeyError; recursive __str__ -> RecursionError); there the real __eq__ escapes. But this is a FOURTH interpreter behavior outside the three modeled InterpretOutcome cases: the shadow's own classify() crashes identically, and the GOLD patch itself also escapes with the same exception on those operands. Since outcome is a free input with no contract (strictly weaker than any concrete interpreter, directive 7), and gold==any-correct-fix on these out-of-domain inputs, there is no resolve-fidelity divergence. This is a legitimate modeling boundary, not a spec that disagrees with the real callee on an in-domain input.
- No UnrecognizedUnit subclasses exist in the suite, so isinstance(other, type(self)) == isinstance(interp, UnrecognizedUnit); the sameKind/otherKind split is faithful.

CONCLUSION: On every input within the modeled abstraction domain the spec agrees with the real patched callee; the sole escape cases fall outside the modeled domain and gold behaves identically there. No diverging in-domain input exists. Spec is FAITHFUL (not too strong, no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check of the velvet spec view for astropy__astropy-7606.

Mechanical screen (leakage.screen over spec_view) PASSES with zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean) == True, so the prepatch and patched bundles share a byte-identical spec view (the differing content lives only in the elided impl region). Verified via swebench_unified.markers.same_spec and leakage.screen.

What the PUBLIC problem_statement already discloses: the function is `__eq__`; the exact offending line `other = Unit(other, parse_strict='silent')`; that `Unit(None, parse_strict='silent')` raises `TypeError('None is not a valid Unit')`; and that `x == None` should be `False`. So the gold fix (guard the interpretation so its failure does not escape) is essentially handed to any solver by the problem statement itself.

Spec-view content vs the gold edit: the spec view is fully abstracted into Lean domain terms. It contains NO patched file path (astropy/units/core.py), NO patched module path, NO patched repo symbols (UnrecognizedUnit, UnitBase, Unit, parse_strict, NotImplemented, TypeError, isinstance, type(self)), NO diff markers, NO reproduced gold-patch line, and NO narration keywords in spec-view comments. The unchanged interpreter is modeled as a free input `InterpretOutcome`; the return is `Verdict`/`deferred`; the removed escape is `CmpErr.interpretationEscaped`. The comments describe desired behavior (uninterpretable => deferred/decline; sameKind => name equality; otherKind => unequal; result is always a verdict) — the legitimate content of a specification, and strictly LESS concrete than the problem-statement traceback already reveals.

The narration that does exist ('pre-image skeleton', 'prove_correct MUST fail', bug-shaped prose) is confined to the impl regions (elided from the spec view) and to mapping.md / refinement.md, which are audit artifacts, not the spec view. A solver reading the spec view still must reconstruct the concrete Python try/except + isinstance change; the spec discloses nothing about the gold edit beyond the public problem_statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.