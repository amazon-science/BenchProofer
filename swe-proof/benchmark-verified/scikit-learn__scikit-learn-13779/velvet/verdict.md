# P2 adversarial audit — scikit-learn__scikit-learn-13779

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
An ensemble member that is absent (step is None -> present=false) and unsupported (supports=false). validate exempts it (skipped via the `present` conjunct -> Except.ok ()), so any wrong impl that instead reports it, reports the wrong label, reports the last/no failure, or returns a constant, differs from `validate members` and cannot verify. e.g. members=[{name:=0, present:=false, supports:=false}]: validate = ok(); prepatch atk_1 = error 0.
```

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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -84,10 +84,9 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = validate (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := if (m.present && !m.supports) then Except.error m.name else result
+      result := if (!m.supports) then Except.error m.name else result
       i := i - 1
     return result
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -72,23 +72,7 @@
   ensures out = validate members
   do
     -- impl-start
-    -- Scan the members back-to-front, keeping the earliest failure seen so far.
-    -- A present member that does not accept a per-sample weighting becomes the
-    -- recorded failure; an absent member contributes nothing (it is skipped);
-    -- a present, supported member leaves the running outcome unchanged. Because
-    -- the scan runs back-to-front, the earliest (front-most) failure is the one
-    -- that survives — exactly the first offending member.
-    let mut result : Except Int Unit := Except.ok ()
-    let mut i := members.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = validate (members.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let m := members[i - 1]!
-      result := if (m.present && !m.supports) then Except.error m.name else result
-      i := i - 1
+    let result : Except Int Unit := Except.ok ()
     return result
     -- impl-end
 
@@ -111,5 +95,4 @@
 
 prove_correct validateWeightSupport by
   loom_solve
-  rw [validate_drop_step members i (by omega) (by omega)]
   simp_all
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -72,23 +72,15 @@
   ensures out = validate members
   do
     -- impl-start
-    -- Scan the members back-to-front, keeping the earliest failure seen so far.
-    -- A present member that does not accept a per-sample weighting becomes the
-    -- recorded failure; an absent member contributes nothing (it is skipped);
-    -- a present, supported member leaves the running outcome unchanged. Because
-    -- the scan runs back-to-front, the earliest (front-most) failure is the one
-    -- that survives — exactly the first offending member.
     let mut result : Except Int Unit := Except.ok ()
-    let mut i := members.length
-    while i > 0
+    let mut i := 0
+    while i < members.length
       invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = validate (members.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = members.length
     do
-      let m := members[i - 1]!
+      let m := members[i]!
       result := if (m.present && !m.supports) then Except.error m.name else result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -111,5 +103,4 @@
 
 prove_correct validateWeightSupport by
   loom_solve
-  rw [validate_drop_step members i (by omega) (by omega)]
   simp_all
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -84,10 +84,9 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = validate (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := if (m.present && !m.supports) then Except.error m.name else result
+      result := if (m.present && m.supports) then Except.error m.name else result
       i := i - 1
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -72,24 +72,16 @@
   ensures out = validate members
   do
     -- impl-start
-    -- Scan the members back-to-front, keeping the earliest failure seen so far.
-    -- A present member that does not accept a per-sample weighting becomes the
-    -- recorded failure; an absent member contributes nothing (it is skipped);
-    -- a present, supported member leaves the running outcome unchanged. Because
-    -- the scan runs back-to-front, the earliest (front-most) failure is the one
-    -- that survives — exactly the first offending member.
     let mut result : Except Int Unit := Except.ok ()
     let mut i := members.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ members.length
-      invariant result = validate (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
       result := if (m.present && !m.supports) then Except.error m.name else result
       i := i - 1
-    return result
+    return Except.ok ()
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the member at
@@ -111,5 +103,4 @@
 
 prove_correct validateWeightSupport by
   loom_solve
-  rw [validate_drop_step members i (by omega) (by omega)]
   simp_all
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -84,10 +84,9 @@
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = validate (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := if (m.present && !m.supports) then Except.error m.name else result
+      result := if (m.present && !m.supports) then Except.error (m.name + 1) else result
       i := i - 1
     return result
     -- impl-end
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
 -- (No axiomatized callees and no consumed axioms. The two facts this validation
@@ -72,22 +72,15 @@
   ensures out = validate members
   do
     -- impl-start
-    -- Scan the members back-to-front, keeping the earliest failure seen so far.
-    -- A present member that does not accept a per-sample weighting becomes the
-    -- recorded failure; an absent member contributes nothing (it is skipped);
-    -- a present, supported member leaves the running outcome unchanged. Because
-    -- the scan runs back-to-front, the earliest (front-most) failure is the one
-    -- that survives — exactly the first offending member.
     let mut result : Except Int Unit := Except.ok ()
     let mut i := members.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ members.length
       invariant result = validate (members.drop i)
       done_with i = 0
-      decreasing i
     do
       let m := members[i - 1]!
-      result := if (m.present && !m.supports) then Except.error m.name else result
+      result := if (m.present && !m.supports) then result else result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axioms. The two facts this validation
--  scan consults about each member — whether the member is present at all, and
--  whether a present member accepts a per-sample weighting parameter — are
--  abstracted as the boolean input fields `present`/`supports` of the member
--  record. This is a pure type refinement of the member carrier (mapping.md §2),
--  validated by conformance_check.py (G-CONF) and the bridge check
--  axiom_check.py; nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- One member of an ensemble, abstracted to exactly the three facts this
   validation step observes:
     * `name`     — the member's identity (its label), abstracted to a distinct
                    integer id (mapping.md §2); reported when validation fails;
     * `present`  — whether the member is actually supplied (an unsupplied /
                    absent member is modeled by `present = false`);
     * `supports` — whether a *present* member accepts a per-sample weighting
                    parameter. Immaterial for an absent member. -/
structure Member where
  name     : Int
  present  : Bool
  supports : Bool
  deriving Inhabited, DecidableEq

/- Validation of an ensemble when a per-sample weighting is supplied.

   Scanning the members in order: an absent member (`present = false`) imposes no
   requirement and is passed over; the FIRST present member that does not accept
   a per-sample weighting parameter makes validation fail, reporting that
   member's identity. If no present member is unsupported, validation succeeds.

   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). The error leg carries the offending member's identity. -/
def validate : List Member → Except Int Unit
  | []      => Except.ok ()
  | m :: ms =>
      if (m.present && !m.supports) then Except.error m.name
      else validate ms

@[grind] lemma validate_nil : validate [] = Except.ok () := rfl
@[grind] lemma validate_cons (m : Member) (ms : List Member) :
    validate (m :: ms) =
      (if (m.present && !m.supports) then Except.error m.name else validate ms) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a per-sample weighting is supplied, every present member of an ensemble
   must accept such a weighting; absent members are exempt and impose no
   requirement. The outcome is success exactly when no present member is
   unsupported, and otherwise failure reporting the FIRST present member (in
   order) that does not accept a per-sample weighting parameter.

   `members` is consulted read-only: it is not declared `mut` (directive 5).
   The result is pinned to `validate members`, which pins both legs at once —
   the success outcome when every present member is supported (absent members
   skipped), and the exact identity reported on the failure leg. -/
method validateWeightSupport (members : List Member) return (out : Except Int Unit)
  ensures out = validate members
  do
    -- impl-start
    -- Scan the members back-to-front, keeping the earliest failure seen so far.
    -- A present member that does not accept a per-sample weighting becomes the
    -- recorded failure; an absent member contributes nothing (it is skipped);
    -- a present, supported member leaves the running outcome unchanged. Because
    -- the scan runs back-to-front, the earliest (front-most) failure is the one
    -- that survives — exactly the first offending member.
    let mut result : Except Int Unit := Except.ok ()
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = validate (members.drop i)
      done_with i = 0
    do
      let m := members[i - 1]!
      result := if (m.present && !m.supports) then Except.error m.name else result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the member at
   `i-1` on the front, so `validate` peels one guarded step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma validate_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    validate (members.drop (i - 1)) =
      (if (members[i - 1]!.present && !members[i - 1]!.supports)
       then Except.error members[i - 1]!.name
       else validate (members.drop i)) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, validate_cons]

prove_correct validateWeightSupport by
  loom_solve
  rw [validate_drop_step members i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: the frozen postcondition `ensures out = validate members` pins the method output to an EXACT functional equality with a fully-concrete deep model `validate` (skip-absent, then raise-at-first-present-unsupported). meta.json confirms axioms=[] and deep_model_references=[] — consistent with mapping.md §3 and refinement.md §B/§C: NO consumed axiom, NO A-reference callee, NO kind-3 leg. The one repo callee has_fit_parameter is consumed as the input bit Member.supports (R type-refinement of the carrier), and step-is-None as present=false. There is no ungrounded oracle/axiom for a wrong impl to echo, so verify pins behavior tightly.

Protocol executed. same_spec(velvet) = True for all 7 attacks AND the positive control (impl-region-only edits; axioms/pure/pre/post byte-identical). Verification run concurrently (<=4 at a time) via `bash scripts/lean_verify.sh <file>`, exit codes captured to .code files.

### RESULTS (exit 0 = verifies, 1 = error/does-not-verify):
- pos_control.lean (gold impl, backward-fold keeping earliest failure): exit 0 (VERIFIES). Positive control good.
- atk_1.lean (PREPATCH BUG reproduced: guard drops the `m.present` conjunct -> `if !m.supports`; absent unsupported member wrongly errors): exit 1. Residual goal: `(if supports=false then error name else ...) = (if present=true ∧ supports=false then error name else ...)` unsolved. prepatch_reproduced=true.
- atk_2.lean (ungrounded/constant oracle echo: always return Except.ok ()): exit 1. `simp_all made no progress` on ensures — ok() != validate members for nonempty offending list.
- atk_3.lean (control-flow-effect: forward scan keeping the LAST failure instead of first): exit 1. ensures goal `result_1 = validate members` unsolved (loop invariant dropped; last-wins != first-wins).
- atk_4.lean (inverted guard: report present ∧ supports): exit 1. Residual `present∧supports` vs `present∧!supports` — opposite predicate.
- atk_5.lean (boundary/return bug: scan runs but returns Except.ok () unconditionally): exit 1. Residual `Except.ok () = validate members` unsolved.
- atk_6.lean (ungrounded-oracle echo on the reported identity: Except.error (m.name + 1)): exit 1. Residual `error (name+1) = error name` — false, cannot close. This directly probes the A4 identity-reporting leg (the raised label is the only failure-path observable) and confirms it is pinned exactly.
- atk_7.lean (partial-domain / no-op guard: `if ... then result else result`, never records a failure): exit 1. Residual requires `validate (drop i) = error name` under present∧!supports — false.

No wrong impl verified. Therefore protocol step 2 (materialize each verifying wrong impl's faithful refined patch and RUN it through run_resolve) applies to ZERO candidates — patches={} and no resolve run is owed (there is no verify⇏correct witness to exhibit). This is not a skipped/unavailable resolve run; it is vacuous because the falsification set is empty.

Refinement.md audit (step 3): legs A1(R), A2(R), A3(R+I), A4(R+I), A5(R) — every leg is R or I; §B confirms no consumed axiom and no A-reference callee model; §C confirms no kind-3 inexpressible-changed-op (the genuinely-changed op `if step is None: continue` is modeled directly as the `m.present` conjunct, not hidden behind an axiom). The A-legs' correspondence holds: since there is no axiomatized callee, there is no A-callee correspondence to break; has_fit_parameter/step-is-None are bridged by axiom_check.py as R type-refinements (mapping.md §2/§3.1) and refuted end-to-end by G-CONF. No kind-3 legs present.

Coverage: 7 DISTINct wrong impls spanning prepatch-bug, constant/ungrounded-oracle (atk_2), control-flow-effect (atk_3), inverted-predicate (atk_4), boundary/return (atk_5), ungrounded-oracle identity echo (atk_6), partial-domain/no-op guard (atk_7). All verified, all fail closed on genuinely-false goals. Spec is a tight exact-equality with no axiom trust points to exploit -> verify implies the gold-refined behavior. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
An ensemble member that is absent (step is None -> present=false) and unsupported (supports=false). validate exempts it (skipped via the `present` conjunct -> Except.ok ()), so any wrong impl that instead reports it, reports the wrong label, reports the last/no failure, or returns a constant, differs from `validate members` and cannot verify. e.g. members=[{name:=0, present:=false, supports:=false}]: validate = ok(); prepatch atk_1 = error 0.
```

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
-- (No axiomatized callees and no consumed axioms. The two facts this validation
--  scan consults about each member — whether the member is present at all, and
--  whether a present member accepts a per-sample weighting parameter — are
--  abstracted as the boolean input fields `present`/`supports` of the member
--  record. This is a pure type refinement of the member carrier (mapping.md §2),
--  validated by conformance_check.py (G-CONF) and the bridge check
--  axiom_check.py; nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- One member of an ensemble, abstracted to exactly the three facts this
   validation step observes:
     * `name`     — the member's identity (its label), abstracted to a distinct
                    integer id (mapping.md §2); reported when validation fails;
     * `present`  — whether the member is actually supplied (an unsupplied /
                    absent member is modeled by `present = false`);
     * `supports` — whether a *present* member accepts a per-sample weighting
                    parameter. Immaterial for an absent member. -/
structure Member where
  name     : Int
  present  : Bool
  supports : Bool
  deriving Inhabited, DecidableEq

/- Validation of an ensemble when a per-sample weighting is supplied.

   Scanning the members in order: an absent member (`present = false`) imposes no
   requirement and is passed over; the FIRST present member that does not accept
   a per-sample weighting parameter makes validation fail, reporting that
   member's identity. If no present member is unsupported, validation succeeds.

   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). The error leg carries the offending member's identity. -/
def validate : List Member → Except Int Unit
  | []      => Except.ok ()
  | m :: ms =>
      if (m.present && !m.supports) then Except.error m.name
      else validate ms

@[grind] lemma validate_nil : validate [] = Except.ok () := rfl
@[grind] lemma validate_cons (m : Member) (ms : List Member) :
    validate (m :: ms) =
      (if (m.present && !m.supports) then Except.error m.name else validate ms) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a per-sample weighting is supplied, every present member of an ensemble
   must accept such a weighting; absent members are exempt and impose no
   requirement. The outcome is success exactly when no present member is
   unsupported, and otherwise failure reporting the FIRST present member (in
   order) that does not accept a per-sample weighting parameter.

   `members` is consulted read-only: it is not declared `mut` (directive 5).
   The result is pinned to `validate members`, which pins both legs at once —
   the success outcome when every present member is supported (absent members
   skipped), and the exact identity reported on the failure leg. -/
method validateWeightSupport (members : List Member) return (out : Except Int Unit)
  ensures out = validate members
  do
    -- impl-start
    -- Scan the members back-to-front, keeping the earliest failure seen so far.
    -- A present member that does not accept a per-sample weighting becomes the
    -- recorded failure; an absent member contributes nothing (it is skipped);
    -- a present, supported member leaves the running outcome unchanged. Because
    -- the scan runs back-to-front, the earliest (front-most) failure is the one
    -- that survives — exactly the first offending member.
    let mut result : Except Int Unit := Except.ok ()
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = validate (members.drop i)
      done_with i = 0
    do
      let m := members[i - 1]!
      result := if (m.present && !m.supports) then Except.error m.name else result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the member at
   `i-1` on the front, so `validate` peels one guarded step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma validate_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    validate (members.drop (i - 1)) =
      (if (members[i - 1]!.present && !members[i - 1]!.supports)
       then Except.error members[i - 1]!.name
       else validate (members.drop i)) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, validate_cons]

prove_correct validateWeightSupport by
  loom_solve
  rw [validate_drop_step members i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: the frozen postcondition `ensures out = validate members` pins the method output to an EXACT functional equality with a fully-concrete deep model `validate` (skip-absent, then raise-at-first-present-unsupported). meta.json confirms axioms=[] and deep_model_references=[] — consistent with mapping.md §3 and refinement.md §B/§C: NO consumed axiom, NO A-reference callee, NO kind-3 leg. The one repo callee has_fit_parameter is consumed as the input bit Member.supports (R type-refinement of the carrier), and step-is-None as present=false. There is no ungrounded oracle/axiom for a wrong impl to echo, so verify pins behavior tightly.

Protocol executed. same_spec(velvet) = True for all 7 attacks AND the positive control (impl-region-only edits; axioms/pure/pre/post byte-identical). Verification run concurrently (<=4 at a time) via `bash scripts/lean_verify.sh <file>`, exit codes captured to .code files.

### RESULTS (exit 0 = verifies, 1 = error/does-not-verify):
- pos_control.lean (gold impl, backward-fold keeping earliest failure): exit 0 (VERIFIES). Positive control good.
- atk_1.lean (PREPATCH BUG reproduced: guard drops the `m.present` conjunct -> `if !m.supports`; absent unsupported member wrongly errors): exit 1. Residual goal: `(if supports=false then error name else ...) = (if present=true ∧ supports=false then error name else ...)` unsolved. prepatch_reproduced=true.
- atk_2.lean (ungrounded/constant oracle echo: always return Except.ok ()): exit 1. `simp_all made no progress` on ensures — ok() != validate members for nonempty offending list.
- atk_3.lean (control-flow-effect: forward scan keeping the LAST failure instead of first): exit 1. ensures goal `result_1 = validate members` unsolved (loop invariant dropped; last-wins != first-wins).
- atk_4.lean (inverted guard: report present ∧ supports): exit 1. Residual `present∧supports` vs `present∧!supports` — opposite predicate.
- atk_5.lean (boundary/return bug: scan runs but returns Except.ok () unconditionally): exit 1. Residual `Except.ok () = validate members` unsolved.
- atk_6.lean (ungrounded-oracle echo on the reported identity: Except.error (m.name + 1)): exit 1. Residual `error (name+1) = error name` — false, cannot close. This directly probes the A4 identity-reporting leg (the raised label is the only failure-path observable) and confirms it is pinned exactly.
- atk_7.lean (partial-domain / no-op guard: `if ... then result else result`, never records a failure): exit 1. Residual requires `validate (drop i) = error name` under present∧!supports — false.

No wrong impl verified. Therefore protocol step 2 (materialize each verifying wrong impl's faithful refined patch and RUN it through run_resolve) applies to ZERO candidates — patches={} and no resolve run is owed (there is no verify⇏correct witness to exhibit). This is not a skipped/unavailable resolve run; it is vacuous because the falsification set is empty.

Refinement.md audit (step 3): legs A1(R), A2(R), A3(R+I), A4(R+I), A5(R) — every leg is R or I; §B confirms no consumed axiom and no A-reference callee model; §C confirms no kind-3 inexpressible-changed-op (the genuinely-changed op `if step is None: continue` is modeled directly as the `m.present` conjunct, not hidden behind an axiom). The A-legs' correspondence holds: since there is no axiomatized callee, there is no A-callee correspondence to break; has_fit_parameter/step-is-None are bridged by axiom_check.py as R type-refinements (mapping.md §2/§3.1) and refuted end-to-end by G-CONF. No kind-3 legs present.

Coverage: 7 DISTINct wrong impls spanning prepatch-bug, constant/ungrounded-oracle (atk_2), control-flow-effect (atk_3), inverted-predicate (atk_4), boundary/return (atk_5), ungrounded-oracle identity echo (atk_6), partial-domain/no-op guard (atk_7). All verified, all fail closed on genuinely-false goals. Spec is a tight exact-equality with no axiom trust points to exploit -> verify implies the gold-refined behavior. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO drift; spec is faithful, not too strong. same_spec(Solution, Solution_prepatch)=True under VelvetBackend tables (byte-identical spec view; only impl region differs). Solution.lean verifies (lean_verify.sh exit 0); prepatch leaves an unclosable proof goal, confirming the discriminating content is the `m.present` conjunct. Base_commit b34751b7 source confirmed via git (the worktree was stale at 3d997697, a later commit); gold patch inserts `if step is None: continue` before the `has_fit_parameter` raise, gated by `sample_weight is not None`. Modeled `validate` matches the real patched scan on ALL member states: (present=T,supports=T)->continue==continue; (present=T,supports=F)->Except.error name==raise ValueError(...%name); (present=F,supports=T)->continue==(step is None -> continue); (present=F,supports=F)->continue==(step is None -> continue). First-offending ordering matches (front-recursive validate <-> first for-loop raise). has_fit_parameter consumed as free input bit `supports` (R-refinement) — spec asserts nothing about how it decides, so no over-constraint. Absent-member `supports` immaterial in both model and repo. Modeling boundary (only the already-gated scan voting.py:76-81) is legitimate; other fit error paths (empty estimators, weight-count mismatch, all-None) are separate ops outside the modeled function. No input distinguishes the modeled function from the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Byte-identical spec region verified: same_spec(Solution, Solution_prepatch)=True and same_spec(Solution,Solution)=True via swebench_unified.markers with the velvet backend. Consumer spec view (impl and prove_correct proof elided) inspected directly. Mechanical leakage.screen(Solution, velvet, gold_patch, problem_statement) returns hard_failures=[] (PASS): no diff markers, no gold-patch line reproduced, no patched file/module path (voting.py / sklearn.ensemble.voting) in the spec view, no changed-symbol collision (the gold hunk adds a guard inside fit and introduces no new symbol, so _patch_changed_symbols is empty), and no bug/fix narration in spec-view comments.

Gold edit: `if step is None: continue` — skip an absent/None estimator before the has_fit_parameter support check. The PUBLIC problem_statement already fully discloses this: 'Voting estimator will fail at fit if weights are passed and an estimator is None. Because we don't check for an estimator to be None in sample_weight support, fit is failing', plus a reproduction that sets lr=None and calls fit with sample_weight. The spec view models a generic abstract scan over Member records with a `present` flag (absent members skipped) and a `supports` flag; the discriminating idea 'skip the absent member, then raise on the first present unsupported one' is exactly what the public problem statement already states. The 'raise at first unsupported member' scaffolding is pre-existing repo behavior, not the gold edit. No spec-view line reveals the None-skip fix beyond what is public.

Concrete repo symbols (has_fit_parameter, sklearn.ensemble.voting, `step is None`) and the verbatim gold hunk appear ONLY in mapping.md / refinement.md, which are audit-side documents NOT part of the consumer spec view. Spec-view comments reference conformance_check.py / axiom_check.py / mapping.md abstractly and describe behavior in generic terms (per-sample weighting parameter, absent member modeled by present=false) with no None/estimator/sample_weight literals tying to the edit. The spec necessarily encodes the correct (fixed) behavior, but that behavior is fully public via the problem statement, so nothing leaks beyond it. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
