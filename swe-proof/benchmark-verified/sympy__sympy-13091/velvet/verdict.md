# P2 adversarial audit — sympy__sympy-13091

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl was found whose faithful refined patch produces a confirmed verify⇒correct break. The only verifying wrong impls are `while true` divergences (atk_7/atk_8/atk_9) that exploit the benchmark-sanctioned `termination "partial"` mode; their materialized faithful patches were EXECUTED through run_resolve and returned completed=False (harness timeout, no report) — NOT the completed=True ∧ ¬resolved that the derivation requires for BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -95,12 +95,9 @@
   ensures operand = .matchingUnequal → out = .isFalse
   do
     -- impl-start
-    -- Report the verdict for the operand: an operand we cannot interpret is
-    -- `undecided` (decline, so the comparison can delegate); an interpretable
-    -- equal operand is `isTrue`; an interpretable differing operand is `isFalse`.
     let result : Verdict :=
       match operand with
-      | .foreign         => .undecided
+      | .foreign         => .isFalse
       | .matchingEqual   => .isTrue
       | .matchingUnequal => .isFalse
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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -149,11 +149,13 @@
   ensures (operand = .matchingEqual) → out = false
   do
     -- impl-start
-    -- Negate the operator-resolved equality decision (which delegates on an
-    -- `undecided` verdict) rather than the raw verdict.
     let selfV ← directEquality operand
-    let eq := resolveEq selfV reflectedV
-    return !eq
+    let bad : Bool :=
+      match selfV with
+      | .isTrue    => false
+      | .isFalse   => true
+      | .undecided => false
+    return bad
     -- impl-end
 
 prove_correct inequalityCompare by
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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -125,10 +125,8 @@
   ensures (operand = .matchingEqual) → out = true
   do
     -- impl-start
-    -- Consult this value's own verdict, then let the operator dispatch resolve it
-    -- against the operand's reflected verdict (delegating on `undecided`).
     let selfV ← directEquality operand
-    let r := resolveEq selfV reflectedV
+    let r : Bool := decide (selfV = .isTrue)
     return r
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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -95,14 +95,11 @@
   ensures operand = .matchingUnequal → out = .isFalse
   do
     -- impl-start
-    -- Report the verdict for the operand: an operand we cannot interpret is
-    -- `undecided` (decline, so the comparison can delegate); an interpretable
-    -- equal operand is `isTrue`; an interpretable differing operand is `isFalse`.
     let result : Verdict :=
       match operand with
       | .foreign         => .undecided
       | .matchingEqual   => .isTrue
-      | .matchingUnequal => .isFalse
+      | .matchingUnequal => .undecided
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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -95,14 +95,11 @@
   ensures operand = .matchingUnequal → out = .isFalse
   do
     -- impl-start
-    -- Report the verdict for the operand: an operand we cannot interpret is
-    -- `undecided` (decline, so the comparison can delegate); an interpretable
-    -- equal operand is `isTrue`; an interpretable differing operand is `isFalse`.
     let result : Verdict :=
       match operand with
       | .foreign         => .undecided
-      | .matchingEqual   => .isTrue
-      | .matchingUnequal => .isFalse
+      | .matchingEqual   => .isFalse
+      | .matchingUnequal => .isTrue
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The equality VERDICT a value produces for an operand,
@@ -125,10 +125,12 @@
   ensures (operand = .matchingEqual) → out = true
   do
     -- impl-start
-    -- Consult this value's own verdict, then let the operator dispatch resolve it
-    -- against the operand's reflected verdict (delegating on `undecided`).
     let selfV ← directEquality operand
-    let r := resolveEq selfV reflectedV
+    let r : Bool :=
+      match selfV with
+      | .isTrue    => true
+      | .isFalse   => false
+      | .undecided => true
     return r
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The equality VERDICT a value produces for an operand,
--  and the binary comparison-operator dispatch that resolves two verdicts into a
--  decision, are modeled DEEPLY in the `pure` region below. The reflected
--  comparison the OTHER operand would produce is taken as a FREE INPUT
--  (`reflectedV`) — the spec makes no claim about a foreign object's own logic —
--  so there is no outside callee to axiomatize and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The outcome a value reports when asked to compare itself to an operand. A
   comparison can decide the operand is equal, decide it is unequal, or report
   that it cannot make sense of the operand and the decision must be DELEGATED to
   the operand's own (reflected) comparison:
     * `isTrue`     — decided equal;
     * `isFalse`    — decided unequal;
     * `undecided`  — cannot interpret the operand; defer to its reflected logic. -/
inductive Verdict where
  | isTrue
  | isFalse
  | undecided
  deriving Inhabited, DecidableEq

/- How an operand presents to a value's equality test, reduced to the only
   distinctions the comparison reacts to:
     * `foreign`         — the operand cannot be interpreted in this value's
                           domain (its conversion is rejected);
     * `matchingEqual`   — the operand is interpretable and is the same thing;
     * `matchingUnequal` — the operand is interpretable but differs (different
                           kind, or interpretable yet not equal). -/
inductive Operand where
  | foreign
  | matchingEqual
  | matchingUnequal
  deriving Inhabited, DecidableEq

/- The equality verdict a value reports for an operand, modeled deeply. The
   desired behaviour:
     * an operand it cannot interpret yields `undecided` — the value declines to
       decide so the comparison can be delegated to the operand's reflected
       logic, keeping the relation symmetric;
     * an interpretable, equal operand yields `isTrue`;
     * an interpretable but differing operand yields `isFalse`. -/
def eqResult : Operand → Verdict
  | .foreign         => .undecided
  | .matchingEqual   => .isTrue
  | .matchingUnequal => .isFalse

/- The binary equality OPERATOR's dispatch — the unchanged language mechanism
   that resolves a comparison into a final yes/no. It consults the left value's
   verdict first; if that value declined to decide (`undecided`), it consults the
   operand's reflected verdict; if BOTH decline, the operands are distinct things,
   so the result is `false` (the identity fallback). The operator always returns a
   decided boolean. -/
def resolveEq (selfV reflectedV : Verdict) : Bool :=
  match selfV with
  | .isTrue     => true
  | .isFalse    => false
  | .undecided  =>
      match reflectedV with
      | .isTrue    => true
      | .isFalse   => false
      | .undecided => false

/- Inequality is the negation of the equality OPERATOR's resolved decision — NOT
   the negation of the value's raw verdict (negating an `undecided` report
   directly would silently treat "I cannot decide" as "equal" and break the
   relation). Routing through `resolveEq` means delegation is honoured before the
   negation. -/
def neResult (selfV reflectedV : Verdict) : Bool := ! resolveEq selfV reflectedV
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A value's own equality verdict for an operand. `operand` is read-only (not
   `mut`); the test computes a verdict and mutates nothing (directive 5). The
   load-bearing clause is the first conditional: an uninterpretable operand must
   be reported `undecided`, never `isFalse`, so the comparison can be delegated. -/
method directEquality (operand : Operand) return (out : Verdict)
  ensures out = eqResult operand
  ensures operand = .foreign → out = .undecided
  ensures operand = .matchingEqual → out = .isTrue
  ensures operand = .matchingUnequal → out = .isFalse
  do
    -- impl-start
    -- Report the verdict for the operand: an operand we cannot interpret is
    -- `undecided` (decline, so the comparison can delegate); an interpretable
    -- equal operand is `isTrue`; an interpretable differing operand is `isFalse`.
    let result : Verdict :=
      match operand with
      | .foreign         => .undecided
      | .matchingEqual   => .isTrue
      | .matchingUnequal => .isFalse
    return result
    -- impl-end

prove_correct directEquality by
  loom_solve
  cases operand <;> simp_all [eqResult]

/- The equality comparison as the operator resolves it: it consults this value's
   own verdict (`directEquality`), and on `undecided` defers to the operand's
   reflected verdict, falling back to inequality when both decline.
   `reflectedV` is the operand's own comparison outcome — a free input.
   The discriminating clauses pin the delegation: a foreign operand that DOES
   recognise this value (reflected `isTrue`) compares EQUAL — reachable only
   because `directEquality` declined rather than deciding `isFalse`. -/
method equalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = resolveEq (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isFalse) → out = false
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = false
  ensures (operand = .matchingEqual) → out = true
  do
    -- impl-start
    -- Behaviorally-identical echo: inline the operator dispatch instead of calling resolveEq.
    let selfV ← directEquality operand
    let r : Bool :=
      match selfV, reflectedV with
      | .isTrue,  _         => true
      | .isFalse, _         => false
      | .undecided, .isTrue => true
      | .undecided, _       => false
    return r
    -- impl-end

prove_correct equalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq])

/- The inequality comparison. It negates the equality OPERATOR's resolved
   decision (`equalityCompare` → `resolveEq`), not this value's raw verdict, so a
   delegated comparison is resolved before negation. The discriminating clause:
   a foreign operand whose reflected logic also declines (`undecided`) is UNEQUAL
   (`true`) — whereas negating the raw `undecided` verdict directly would wrongly
   yield `false`. -/
method inequalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = neResult (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = false
  ensures (operand = .matchingEqual) → out = false
  do
    -- impl-start
    -- Behaviorally-identical echo: inline dispatch then negate.
    let selfV ← directEquality operand
    let eq : Bool :=
      match selfV, reflectedV with
      | .isTrue,  _         => true
      | .isFalse, _         => false
      | .undecided, .isTrue => true
      | .undecided, _       => false
    return !eq
    -- impl-end

prove_correct inequalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq, neResult])
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-functional, AXIOM-FREE (meta axioms=[], deep_model_references=[]). Every method postcondition pins output EXACTLY over the finite modeled domain: directEquality `out = eqResult operand` (+3 discriminating clauses); equalityCompare `out = resolveEq (eqResult operand) reflectedV` (+4 clauses over the 3x3 Operand×Verdict space); inequalityCompare `out = neResult (eqResult operand) reflectedV` (+3). eqResult/resolveEq/neResult are FROZEN pure defs (part of same_spec signature; the prove_correct body is elided from the spec view so proof tactics are free to edit). So verify ⇔ behaviorally-gold on the entire modeled space for any TERMINATING impl. My A-leg mandate is VACUOUS here (no axioms / no A-reference deep models) — confirmed against meta.json.

REFINEMENT.MD AUDIT: every leg is R or I; ZERO kind-3. modeled_functions↔repo correspondence verified exact: directEquality↔Basic.__eq__ (patch site basic.py:316, `return False`→`return NotImplemented`); inequalityCompare↔Basic.__ne__ (patch site basic.py:332, `not self.__eq__(other)`→`not self == other`); equalityCompare↔the UNCHANGED CPython `==` operator dispatch (NOT a patch site — modeled deeply by resolveEq, reflectedV a free input). mapping.md R-bijection Operand↔other / Verdict↔{True,False,NotImplemented} is genuine & 3-way. No axiom trust points.

### TERMINATING ATTACK BATTERY (6, all same_spec=True, impl-region-only, all correctly FAIL verify — cmd `bash scripts/lean_verify.sh <f>`):
  atk_1 = prepatch-A: directEquality .foreign=>.isFalse → exit 1 (rejected by `operand=.foreign→out=.undecided`). [prepatch bug reproduced]
  atk_2 = prepatch-B: inequalityCompare negates RAW verdict (undecided↦false) → exit 1 (rejected by `(foreign∧undecided)→out=true`). [prepatch-ne bug reproduced]
  atk_3 = equalityCompare ignores reflectedV (decide selfV=isTrue; no delegation) → exit 1 (rejected by `(foreign∧reflectedV=isTrue)→out=true`).
  atk_4 = partial-domain: directEquality correct on foreign/matchingEqual but .matchingUnequal=>.undecided → exit 1 (rejected by `operand=.matchingUnequal→out=.isFalse` + functional post).
  atk_5 = boundary/swap: directEquality swaps matchingEqual/matchingUnequal → exit 1.
  atk_6 = equalityCompare returns true on .undecided (ungrounded-oracle echo of wrong delegation) → exit 1 (rejected by `(foreign∧undecided)→out=false`).
All six exercise DISTINCT failure axes (partial-domain, boundary, control-flow-effect, delegation/ungrounded-oracle echo) and none verifies — the terminating behavioral surface is maximally tight.

CONTROL-FLOW DIVERGENCE PROBE (the ONLY verifying escape; documented, EXECUTED, not fed as gate attacks because it is a universal partial-correctness artifact, not a bundle refinement defect): atk_7 (atk_7.lean): `while true` in directEquality (→ __eq__ that hangs). same_spec=True, verify exit 0 (vacuous partial correctness; proof body reduced to bare loom_solve, allowed since proof is elided from spec_view). Faithful patch atk_7.patch (injects `while True: pass` into Basic.__eq__ + keeps gold __ne__). EXECUTED: `run_resolve('sympy__sympy-13091', atk_7.patch, timeout=900)` → resolved=False, completed=False, note='no report ... harness error/timeout'.

NOT a break (BROKEN needs completed=True∧¬resolved; this is completed=False = harness timeout on the hung test). atk_9 (atk_9.lean): `while true` in inequalityCompare (→ __ne__ that hangs), gold __eq__. same_spec=True, verify exit 0. Faithful patch atk_9.patch (gold NotImplemented + `while True: pass` in __ne__). EXECUTED → resolved=False, completed=False (same harness timeout). atk_8 (atk_8.lean): `while true` in equalityCompare, gold __eq__/__ne__. Verifies. But equalityCompare maps to the UNCHANGED `==` operator (no repo source line) — its directEquality/inequalityCompare are byte-gold, so its FAITHFUL refined patch IS the gold patch (equalityCompare has no independent Python body to diverge). Covered by the gold resolve below (resolved=True).

Disposition: divergence verifies vacuously in EVERY velvet bundle (confirmed: all 500 velvet reference Solution.lean use `loom.semantics.termination "partial"`; 0 use "total"). It is a universal property of the sanctioned partial-correctness mode, has no counterpart op in refinement.md's op-by-op map (no 'faithful' behavioral refinement of an injected infinite loop), and its executed resolves do NOT yield a confirmed verify∧¬resolve. Feeding it as a gate attack would fail-close ANY partial-correctness bundle to INCONCLUSIVE via a pure harness-timeout artifact — explicitly a protocol artifact, not a spec weakness.

### POSITIVE CONTROLS (harness confirmed live):
  gold.patch (from frozen row) → run_resolve resolved=True, completed=True. Confirms harness works AND is the faithful patch of pos_echo & atk_8.
  pos_echo (pos_echo.lean): structurally-DIFFERENT but behaviorally-gold — equalityCompare/inequalityCompare replace `resolveEq selfV reflectedV` with an inline 4-arm `match selfV, reflectedV` dispatch (≡ resolveEq). same_spec=True, verify exit 0. Its faithful patch ≡ gold (inline dispatch ≡ operator dispatch) → resolved. Spec is NON-VACUOUS.

CONCLUSION: G-EQ SOUND, spec-strength TIGHT. ≥6 distinct same-spec terminating wrong impls all correctly fail verify; prepatch bug reproduced (atk_1/atk_2); positive control verifies; gold resolves. The sole verifying escape is universal partial-correctness divergence whose EXECUTED faithful patches return completed=False (harness timeout), which is not a confirmed verify⇒correct break. No refinement-fidelity defect and no verifying wrong impl with a resolving-blocked patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_echo.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl was found whose faithful refined patch produces a confirmed verify⇒correct break. The only verifying wrong impls are `while true` divergences (atk_7/atk_8/atk_9) that exploit the benchmark-sanctioned `termination "partial"` mode; their materialized faithful patches were EXECUTED through run_resolve and returned completed=False (harness timeout, no report) — NOT the completed=True ∧ ¬resolved that the derivation requires for BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_echo.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The equality VERDICT a value produces for an operand,
--  and the binary comparison-operator dispatch that resolves two verdicts into a
--  decision, are modeled DEEPLY in the `pure` region below. The reflected
--  comparison the OTHER operand would produce is taken as a FREE INPUT
--  (`reflectedV`) — the spec makes no claim about a foreign object's own logic —
--  so there is no outside callee to axiomatize and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The outcome a value reports when asked to compare itself to an operand. A
   comparison can decide the operand is equal, decide it is unequal, or report
   that it cannot make sense of the operand and the decision must be DELEGATED to
   the operand's own (reflected) comparison:
     * `isTrue`     — decided equal;
     * `isFalse`    — decided unequal;
     * `undecided`  — cannot interpret the operand; defer to its reflected logic. -/
inductive Verdict where
  | isTrue
  | isFalse
  | undecided
  deriving Inhabited, DecidableEq

/- How an operand presents to a value's equality test, reduced to the only
   distinctions the comparison reacts to:
     * `foreign`         — the operand cannot be interpreted in this value's
                           domain (its conversion is rejected);
     * `matchingEqual`   — the operand is interpretable and is the same thing;
     * `matchingUnequal` — the operand is interpretable but differs (different
                           kind, or interpretable yet not equal). -/
inductive Operand where
  | foreign
  | matchingEqual
  | matchingUnequal
  deriving Inhabited, DecidableEq

/- The equality verdict a value reports for an operand, modeled deeply. The
   desired behaviour:
     * an operand it cannot interpret yields `undecided` — the value declines to
       decide so the comparison can be delegated to the operand's reflected
       logic, keeping the relation symmetric;
     * an interpretable, equal operand yields `isTrue`;
     * an interpretable but differing operand yields `isFalse`. -/
def eqResult : Operand → Verdict
  | .foreign         => .undecided
  | .matchingEqual   => .isTrue
  | .matchingUnequal => .isFalse

/- The binary equality OPERATOR's dispatch — the unchanged language mechanism
   that resolves a comparison into a final yes/no. It consults the left value's
   verdict first; if that value declined to decide (`undecided`), it consults the
   operand's reflected verdict; if BOTH decline, the operands are distinct things,
   so the result is `false` (the identity fallback). The operator always returns a
   decided boolean. -/
def resolveEq (selfV reflectedV : Verdict) : Bool :=
  match selfV with
  | .isTrue     => true
  | .isFalse    => false
  | .undecided  =>
      match reflectedV with
      | .isTrue    => true
      | .isFalse   => false
      | .undecided => false

/- Inequality is the negation of the equality OPERATOR's resolved decision — NOT
   the negation of the value's raw verdict (negating an `undecided` report
   directly would silently treat "I cannot decide" as "equal" and break the
   relation). Routing through `resolveEq` means delegation is honoured before the
   negation. -/
def neResult (selfV reflectedV : Verdict) : Bool := ! resolveEq selfV reflectedV
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A value's own equality verdict for an operand. `operand` is read-only (not
   `mut`); the test computes a verdict and mutates nothing (directive 5). The
   load-bearing clause is the first conditional: an uninterpretable operand must
   be reported `undecided`, never `isFalse`, so the comparison can be delegated. -/
method directEquality (operand : Operand) return (out : Verdict)
  ensures out = eqResult operand
  ensures operand = .foreign → out = .undecided
  ensures operand = .matchingEqual → out = .isTrue
  ensures operand = .matchingUnequal → out = .isFalse
  do
    -- impl-start
    -- Report the verdict for the operand: an operand we cannot interpret is
    -- `undecided` (decline, so the comparison can delegate); an interpretable
    -- equal operand is `isTrue`; an interpretable differing operand is `isFalse`.
    let result : Verdict :=
      match operand with
      | .foreign         => .undecided
      | .matchingEqual   => .isTrue
      | .matchingUnequal => .isFalse
    return result
    -- impl-end

prove_correct directEquality by
  loom_solve
  cases operand <;> simp_all [eqResult]

/- The equality comparison as the operator resolves it: it consults this value's
   own verdict (`directEquality`), and on `undecided` defers to the operand's
   reflected verdict, falling back to inequality when both decline.
   `reflectedV` is the operand's own comparison outcome — a free input.
   The discriminating clauses pin the delegation: a foreign operand that DOES
   recognise this value (reflected `isTrue`) compares EQUAL — reachable only
   because `directEquality` declined rather than deciding `isFalse`. -/
method equalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = resolveEq (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isFalse) → out = false
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = false
  ensures (operand = .matchingEqual) → out = true
  do
    -- impl-start
    -- Behaviorally-identical echo: inline the operator dispatch instead of calling resolveEq.
    let selfV ← directEquality operand
    let r : Bool :=
      match selfV, reflectedV with
      | .isTrue,  _         => true
      | .isFalse, _         => false
      | .undecided, .isTrue => true
      | .undecided, _       => false
    return r
    -- impl-end

prove_correct equalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq])

/- The inequality comparison. It negates the equality OPERATOR's resolved
   decision (`equalityCompare` → `resolveEq`), not this value's raw verdict, so a
   delegated comparison is resolved before negation. The discriminating clause:
   a foreign operand whose reflected logic also declines (`undecided`) is UNEQUAL
   (`true`) — whereas negating the raw `undecided` verdict directly would wrongly
   yield `false`. -/
method inequalityCompare (operand : Operand) (reflectedV : Verdict) return (out : Bool)
  ensures out = neResult (eqResult operand) reflectedV
  ensures (operand = .foreign ∧ reflectedV = .undecided) → out = true
  ensures (operand = .foreign ∧ reflectedV = .isTrue) → out = false
  ensures (operand = .matchingEqual) → out = false
  do
    -- impl-start
    -- Behaviorally-identical echo: inline dispatch then negate.
    let selfV ← directEquality operand
    let eq : Bool :=
      match selfV, reflectedV with
      | .isTrue,  _         => true
      | .isFalse, _         => false
      | .undecided, .isTrue => true
      | .undecided, _       => false
    return !eq
    -- impl-end

prove_correct inequalityCompare by
  loom_solve <;>
    (cases operand <;> cases reflectedV <;> simp_all [eqResult, resolveEq, neResult])
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-functional, AXIOM-FREE (meta axioms=[], deep_model_references=[]). Every method postcondition pins output EXACTLY over the finite modeled domain: directEquality `out = eqResult operand` (+3 discriminating clauses); equalityCompare `out = resolveEq (eqResult operand) reflectedV` (+4 clauses over the 3x3 Operand×Verdict space); inequalityCompare `out = neResult (eqResult operand) reflectedV` (+3). eqResult/resolveEq/neResult are FROZEN pure defs (part of same_spec signature; the prove_correct body is elided from the spec view so proof tactics are free to edit). So verify ⇔ behaviorally-gold on the entire modeled space for any TERMINATING impl. My A-leg mandate is VACUOUS here (no axioms / no A-reference deep models) — confirmed against meta.json.

REFINEMENT.MD AUDIT: every leg is R or I; ZERO kind-3. modeled_functions↔repo correspondence verified exact: directEquality↔Basic.__eq__ (patch site basic.py:316, `return False`→`return NotImplemented`); inequalityCompare↔Basic.__ne__ (patch site basic.py:332, `not self.__eq__(other)`→`not self == other`); equalityCompare↔the UNCHANGED CPython `==` operator dispatch (NOT a patch site — modeled deeply by resolveEq, reflectedV a free input). mapping.md R-bijection Operand↔other / Verdict↔{True,False,NotImplemented} is genuine & 3-way. No axiom trust points.

### TERMINATING ATTACK BATTERY (6, all same_spec=True, impl-region-only, all correctly FAIL verify — cmd `bash scripts/lean_verify.sh <f>`):
  atk_1 = prepatch-A: directEquality .foreign=>.isFalse → exit 1 (rejected by `operand=.foreign→out=.undecided`). [prepatch bug reproduced]
  atk_2 = prepatch-B: inequalityCompare negates RAW verdict (undecided↦false) → exit 1 (rejected by `(foreign∧undecided)→out=true`). [prepatch-ne bug reproduced]
  atk_3 = equalityCompare ignores reflectedV (decide selfV=isTrue; no delegation) → exit 1 (rejected by `(foreign∧reflectedV=isTrue)→out=true`).
  atk_4 = partial-domain: directEquality correct on foreign/matchingEqual but .matchingUnequal=>.undecided → exit 1 (rejected by `operand=.matchingUnequal→out=.isFalse` + functional post).
  atk_5 = boundary/swap: directEquality swaps matchingEqual/matchingUnequal → exit 1.
  atk_6 = equalityCompare returns true on .undecided (ungrounded-oracle echo of wrong delegation) → exit 1 (rejected by `(foreign∧undecided)→out=false`).
All six exercise DISTINCT failure axes (partial-domain, boundary, control-flow-effect, delegation/ungrounded-oracle echo) and none verifies — the terminating behavioral surface is maximally tight.

CONTROL-FLOW DIVERGENCE PROBE (the ONLY verifying escape; documented, EXECUTED, not fed as gate attacks because it is a universal partial-correctness artifact, not a bundle refinement defect): atk_7 (atk_7.lean): `while true` in directEquality (→ __eq__ that hangs). same_spec=True, verify exit 0 (vacuous partial correctness; proof body reduced to bare loom_solve, allowed since proof is elided from spec_view). Faithful patch atk_7.patch (injects `while True: pass` into Basic.__eq__ + keeps gold __ne__). EXECUTED: `run_resolve('sympy__sympy-13091', atk_7.patch, timeout=900)` → resolved=False, completed=False, note='no report ... harness error/timeout'.

NOT a break (BROKEN needs completed=True∧¬resolved; this is completed=False = harness timeout on the hung test). atk_9 (atk_9.lean): `while true` in inequalityCompare (→ __ne__ that hangs), gold __eq__. same_spec=True, verify exit 0. Faithful patch atk_9.patch (gold NotImplemented + `while True: pass` in __ne__). EXECUTED → resolved=False, completed=False (same harness timeout). atk_8 (atk_8.lean): `while true` in equalityCompare, gold __eq__/__ne__. Verifies. But equalityCompare maps to the UNCHANGED `==` operator (no repo source line) — its directEquality/inequalityCompare are byte-gold, so its FAITHFUL refined patch IS the gold patch (equalityCompare has no independent Python body to diverge). Covered by the gold resolve below (resolved=True).

Disposition: divergence verifies vacuously in EVERY velvet bundle (confirmed: all 500 velvet reference Solution.lean use `loom.semantics.termination "partial"`; 0 use "total"). It is a universal property of the sanctioned partial-correctness mode, has no counterpart op in refinement.md's op-by-op map (no 'faithful' behavioral refinement of an injected infinite loop), and its executed resolves do NOT yield a confirmed verify∧¬resolve. Feeding it as a gate attack would fail-close ANY partial-correctness bundle to INCONCLUSIVE via a pure harness-timeout artifact — explicitly a protocol artifact, not a spec weakness.

### POSITIVE CONTROLS (harness confirmed live):
  gold.patch (from frozen row) → run_resolve resolved=True, completed=True. Confirms harness works AND is the faithful patch of pos_echo & atk_8.
  pos_echo (pos_echo.lean): structurally-DIFFERENT but behaviorally-gold — equalityCompare/inequalityCompare replace `resolveEq selfV reflectedV` with an inline 4-arm `match selfV, reflectedV` dispatch (≡ resolveEq). same_spec=True, verify exit 0. Its faithful patch ≡ gold (inline dispatch ≡ operator dispatch) → resolved. Spec is NON-VACUOUS.

CONCLUSION: G-EQ SOUND, spec-strength TIGHT. ≥6 distinct same-spec terminating wrong impls all correctly fail verify; prepatch bug reproduced (atk_1/atk_2); positive control verifies; gold resolves. The sole verifying escape is universal partial-correctness divergence whose EXECUTED faithful patches return completed=False (harness timeout), which is not a confirmed verify⇒correct break. No refinement-fidelity defect and no verifying wrong impl with a resolving-blocked patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sympy__sympy-13091 velvet bundle. Verdict: FAITHFUL — the modeled functions agree with the real patched repo callees on every input in the abstraction domain; no diverging input exists.

### Evidence
1. same_spec (swebench_unified.markers, LeanBackend.language) = True for BOTH Solution_prepatch.lean and Solution_prepatch_ne.lean vs Solution.lean — spec regions (axioms/pure/pre/post/method sigs + proofs) are byte-identical across the twins.
2. Solution.lean elaborates cleanly (scripts/lean_verify.sh exit 0).
3. Real repo confirmed: at base d1320814ed; working tree carries gold patch (basic.py:316 `return NotImplemented`, :332 `return not self == other`); gold_13091.patch = verbatim gold.

### FAITHFULNESS TRACE (Operand × Verdict, model vs real CPython rich-comparison dispatch on patched code):
- matchingEqual: __eq__ returns decided True → `==`=true (no delegation), `!=`=false. Model: eqResult=.isTrue → resolveEq=true regardless of reflectedV. MATCH.
- matchingUnequal: __eq__ decided False → `==`=false, `!=`=true. Model: .isFalse. MATCH.
- foreign + reflected True: __eq__=NotImplemented → reflected True → `==`=true, `!=`=false. Model: .undecided→delegate→isTrue. MATCH.
- foreign + reflected False: → `==`=false, `!=`=true. MATCH.
- foreign + reflected undecided: NI→NI→identity fallback False → `==`=false, `!=`=true. Model: both undecided → false. MATCH.

The abstraction is not too strong: delegation is correctly gated on .undecided only (decided bools short-circuit exactly as real dispatch does); matchingEqual→true unconditionally is faithful because real __eq__ returns a decided True and never consults the reflected verdict; neResult=!resolveEq faithfully mirrors post-patch `not self == other` (routes through the operator, avoiding the `not NotImplemented`→False pre-patch trap — which is precisely what the prepatch_ne twin reverts and G-DIFF fails). reflectedV is correctly left a FREE INPUT (foreign object's own logic, not the repo's). The F2P Foo/Bar scenarios all reproduce.

G-CONF (recorded pass) independently transliterates the patched protocol and finds 0 disagreements over 9 exhaustive + 100000 fuzz inputs (seed 13091); I re-derived the oracle in conformance_check.py and confirm it faithfully encodes CPython == dispatch and patched __eq__/__ne__.

No input in the modeled domain (Operand×Verdict) produces model≠repo. Attack fails to break faithfulness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). Mechanical G-LEAK screen: PASSED, zero hard failures (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier embedding a patched symbol, no bug/fix narration). Verified with swebench_unified.leakage.screen and confirmed the spec region is byte-identical across Solution/Solution_prepatch/Solution_prepatch_ne (same_spec = True for both).

Consumer spec view (via markers.spec_view): all three impl-start/impl-end blocks are ELIDED ('-- implementation elided — supplied by the consumer'), so the load-bearing gold behaviour is NOT shown as code. Patched repo symbols (eval_Eq, getnewargs, nonzero, strict_eq — the distinctive changed defs/classes) appear nowhere in the view; all spec identifiers are abstract (Verdict/Operand/eqResult/resolveEq/neResult/directEquality/equalityCompare/inequalityCompare).

Semantic content of the visible pure region + postconditions: an uninterpretable operand yields the delegation sentinel (.undecided ↔ NotImplemented) so that == stays symmetric, both-decline falls back to False, and != negates the operator-resolved decision. This is exactly what the PUBLIC problem_statement already states in prose — 'Return NotImplemented, not False, upon rich comparison with unknown type … delegated to the reflected method … maintaining a symmetric relation … The other rich comparison methods … behave similarly … If both sides return NotImplemented, the final return value is False.' The problem statement is in fact MORE specific than the spec view (it names basic.py line 316 and the literal return False→return NotImplemented edit). Behaviour B (__ne__ routing through the operator) is the natural abstract formalization of the publicly-stated 'other rich comparison methods behave similarly' symmetry principle; it is expressed without quoting the gold line or naming any repo symbol.

Conclusion: the spec view reveals nothing about the gold edit beyond what the public problem_statement already discloses. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).