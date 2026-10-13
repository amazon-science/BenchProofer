# P2 adversarial audit — sympy__sympy-22080

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = renderNeg k inner` totally pins the output pointwise as a function of (k, inner) over the frozen pure model (opWeight/needsParen/renderNeg), so NO behaviourally-wrong impl can verify. The single verifying attack (atk_6, the oracle echo `return renderNeg k inner`) is behaviourally identical to gold; its materialized faithful patch (=gold Site C + Site P) RESOLVES under the official harness.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if opWeight k ≤ (80 : Int) then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,9 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
+    let w : Int := if k = .modOp then (140 : Int) else opWeight k
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if w ≤ negLevel then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
     -- impl-end
 
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,12 +108,7 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
-    let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
-    return '-' :: wrapped
+    return '-' :: inner
     -- impl-end
 
 prove_correct printNegatedFactor by
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,12 +108,7 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
-    let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
-    return '-' :: wrapped
+    return '-' :: (('(' :: inner) ++ [')'])
     -- impl-end
 
 prove_correct printNegatedFactor by
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if needsParen k ∨ k = .funcCall then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,12 +108,7 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
-    let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
-    return '-' :: wrapped
+    return renderNeg k inner
     -- impl-end
 
 prove_correct printNegatedFactor by
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if opWeight k ≥ negLevel then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,12 +108,9 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
       if needsParen k then ('(' :: inner) ++ [')'] else inner
-    return '-' :: wrapped
+    return wrapped
     -- impl-end
 
 prove_correct printNegatedFactor by
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if decide (opWeight k ≤ negLevel) then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
     -- impl-end
 
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
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if opWeight k < negLevel then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
     -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- The kinds of single sub-expression that can sit directly under a leading
    unary minus in generated source, distinguished only by the printed-form
@@ -108,11 +108,8 @@
   ensures k = .funcCall  → out = '-' :: inner
   do
     -- impl-start
-    -- Look up the factor's binding strength and compare it to the unary-minus
-    -- threshold; wrap the factor when it binds no more tightly than the
-    -- threshold, then prepend the leading minus.
     let wrapped : List Char :=
-      if needsParen k then ('(' :: inner) ++ [')'] else inner
+      if needsParen k ∨ k = .power then ('(' :: inner) ++ [')'] else inner
     return '-' :: wrapped
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- The kinds of single sub-expression that can sit directly under a leading
   unary minus in generated source, distinguished only by the printed-form
   class each one falls into:
     * `atomic`     — a bare symbol or number;
     * `power`      — an exponentiation;
     * `funcCall`   — a function-call form `f(...)` (self-delimited);
     * `modOp`      — a remainder operation, printed with an infix
                      remainder operator;
     * `mulCluster` — a product of factors.
   Sub-expressions that print into the same class are one kind. -/
inductive OperandKind where
  | atomic
  | power
  | funcCall
  | modOp
  | mulCluster
  deriving Inhabited, DecidableEq

-- axioms-start
-- (No axiomatized callees. The ordinary recursive printing of the inner factor
--  is unchanged by the behaviour modeled here, so it is consumed as the input
--  `inner` — whatever string the renderer already produces for that factor —
--  rather than re-derived; no property of it is owed a contract. The per-kind
--  wrap ranks are modeled DEEPLY in the `pure` region (`opWeight`); no outside
--  callee is consumed, so there is no contract for G-AX to validate (it skips),
--  and the deep model's fidelity to the desired behaviour is exercised
--  mechanically by conformance_check.py (G-CONF).)
-- axioms-end

-- pure-start
/- An opaque ordinal rank for each operand kind. Only the ORDER of these
   integers matters: the wrap rule below is a single `≤` comparison against
   `negLevel`, so any choice that preserves the kind ordering — `atomic` >
   `funcCall` > `power` > `modOp` > `mulCluster` — yields the same wrap
   decisions. Concrete integers (rather than a `<` relation) keep the
   comparison decidable in the kernel (order-only — see DECISIONS.md
   float-order note). The exact ranks are not meaningful; the per-kind wrap
   table is pinned extensionally by the `needsParen_*` lemmas below. -/
def opWeight : OperandKind → Int
  | .atomic     => 2000
  | .power      => 120
  | .funcCall   => 140
  | .modOp      => 100
  | .mulCluster => 99

/- The threshold rank for a leading unary minus, sitting strictly between the
   ranks of `power` and `modOp`. A factor whose rank does not exceed this
   threshold is wrapped in parentheses, so that the leading minus governs the
   whole factor rather than only its first piece. Like the ranks above, the
   exact value is not meaningful — only that it separates the wrapped kinds
   (`modOp`, `mulCluster`) from the bare ones (`atomic`, `power`, `funcCall`),
   exactly as the `needsParen_*` lemmas record. -/
def negLevel : Int := 110

/- Whether a factor of the given kind must be parenthesized under a leading
   unary minus: exactly when its rank does not exceed the threshold. -/
def needsParen (k : OperandKind) : Bool := decide (opWeight k ≤ negLevel)

/- The printed form of a negated single factor: a leading minus followed by the
   factor's own printed form `inner`, wrapped in parentheses precisely when the
   factor's kind is one that must be wrapped (per `needsParen`). -/
def renderNeg (k : OperandKind) (inner : List Char) : List Char :=
  '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner)

@[grind] lemma renderNeg_def (k : OperandKind) (inner : List Char) :
    renderNeg k inner =
      '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner) := rfl

/- The remainder operation and a multiplicative cluster are both wrapped. -/
@[grind, simp] lemma needsParen_modOp : needsParen .modOp = true := by decide
@[grind, simp] lemma needsParen_mul   : needsParen .mulCluster = true := by decide
/- An atom, a power, and a function call are not wrapped. -/
@[grind, simp] lemma needsParen_atom  : needsParen .atomic = false := by decide
@[grind, simp] lemma needsParen_pow   : needsParen .power = false := by decide
@[grind, simp] lemma needsParen_func  : needsParen .funcCall = false := by decide
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Print a single factor `inner` that sits directly under a leading unary minus,
   given the factor's kind `k`. The result is the factor's own printed form,
   parenthesized exactly when the factor's kind is one that must be wrapped,
   with the leading minus prepended. Both inputs are read-only (neither is
   `mut`; the print mutates nothing — directive 5); the result is a fresh
   sequence.

   The pinned behaviour: a remainder operation and a product cluster are
   wrapped (so the minus governs the whole factor); an atom, a power, and a
   self-delimited function call are not. -/
method printNegatedFactor (k : OperandKind) (inner : List Char) return (out : List Char)
  ensures out = renderNeg k inner
  ensures k = .modOp     → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .mulCluster → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .power     → out = '-' :: inner
  ensures k = .atomic    → out = '-' :: inner
  ensures k = .funcCall  → out = '-' :: inner
  do
    -- impl-start
    -- Look up the factor's binding strength and compare it to the unary-minus
    -- threshold; wrap the factor when it binds no more tightly than the
    -- threshold, then prepend the leading minus.
    let wrapped : List Char :=
      if needsParen k then ('(' :: inner) ++ [')'] else inner
    return '-' :: wrapped
    -- impl-end

prove_correct printNegatedFactor by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All commands run from there. same_spec=True verified for all 11 attacks + pos (velvet backend, byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; parallel batches of 4):
- pos.lean (exact gold impl) => EXIT 0 VERIFIES (positive control OK)
- atk_1 (prepatch bug 1: threshold 80 = 2*40 negated-product strength; mulCluster@99 & modOp@100 left unwrapped) => EXIT 1 FAIL (unsolved goal)
- atk_2 (prepatch bug 2: modOp looked up at generic 140 = 2*70, left unwrapped) => EXIT 1 FAIL
- atk_3 (partial-domain: never wrap, `return '-'::inner`) => EXIT 1 FAIL
- atk_4 (boundary: always wrap) => EXIT 1 FAIL
- atk_5 (control-flow-effect: also wrap funcCall, which must be bare) => EXIT 1 FAIL
- atk_6 (ungrounded-oracle echo: `return renderNeg k inner`) => EXIT 0 VERIFIES (behaviourally correct)
- atk_7 (inverted comparison: wrap iff opWeight >= negLevel) => EXIT 1 FAIL
- atk_8 (drop leading minus: `return wrapped`) => EXIT 1 FAIL
- atk_9 (echo variant via `decide (opWeight k <= negLevel)` — behaviourally correct but prover cannot reduce the non-syntactic form; unsolved goal) => EXIT 1 FAIL
- atk_10 (strict `<` instead of `<=`; behaviourally identical since no strength equals 110, but non-syntactic form) => EXIT 1 FAIL
- atk_11 (also wrap power, which must be bare) => EXIT 1 FAIL

MANDATORY RESOLVE (protocol step 2) for the ONLY verifying wrong-impl (atk_6): its faithful refined patch = the gold patch (atk_6 is behaviourally identical to the frozen pure oracle, so the refinement map yields exactly the gold Site C codeprinter.py + Site P precedence.py edits). Materialized Command: SBU_BENCHMARK=swe_bench_verified run_resolve('sympy__sympy-22080', <patch>, run_id='sbu-audit-eq-o79nr0fw-atk6', timeout=1200). OBSERVED RESULT: COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. => the verifying attack's faithful patch RESOLVES. No verify=>not-resolve gap. (This closes the prior pass's INCONCLUSIVE, which was solely because that resolve run never completed — same-shaped echo attack, now executed and confirmed RESOLVED.)

REFINEMENT.MD AUDIT (A-legs focus): step 2 (inner <-> self._print(item)) is A-consumed — unchanged callee consumed as input, no contract owed, and G-CONF supplies the REAL pycode(factor) identically on shadow and oracle sides; correspondence to the real callee holds. Steps 3/5 (opWeight/needsParen — the CHANGED parenthesization) are correctly R (G-CONF), NOT A-reference: precedence/parenthesize are exactly the callees the gold patch edits (directive 7 forbids A-reference for changed callees; G-AX runs unpatched where precedence(Mod)==70 and the threshold branch doesn't exist). Steps 1/4/6 are R / R+I / I. NO kind-3 (inexpressible-changed-op) legs. G-AX legitimately SKIPs (no consumed axiom, no A-reference); the changed-op fidelity is exercised by G-CONF (meta: pass, 96763 single-negated-factor inputs, seed 22080, 0 disagreements against the patched pycode(-e)). Model<->patch correspondence holds: opWeight(kind)==precedence(rep)*2, negLevel==55*2, needsParen == (precedence(rep)<=55) == patched parenthesize wrap.

CONCLUSION: 11 distinct same-spec wrong impls attacked (>=5 required, covering prepatch bugs, partial-domain, boundary, control-flow-effect, inverted-comparison, drop-effect, ungrounded-oracle echo, and two non-syntactic echo variants); 10 correctly rejected by verification; the single verifying impl is the oracle echo, which is behaviourally correct and whose materialized faithful patch RESOLVES under the official harness. The postcondition totally pins output pointwise over the frozen pure model, so verify=>correct holds for this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = renderNeg k inner` totally pins the output pointwise as a function of (k, inner) over the frozen pure model (opWeight/needsParen/renderNeg), so NO behaviourally-wrong impl can verify. The single verifying attack (atk_6, the oracle echo `return renderNeg k inner`) is behaviourally identical to gold; its materialized faithful patch (=gold Site C + Site P) RESOLVES under the official harness.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- The kinds of single sub-expression that can sit directly under a leading
   unary minus in generated source, distinguished only by the printed-form
   class each one falls into:
     * `atomic`     — a bare symbol or number;
     * `power`      — an exponentiation;
     * `funcCall`   — a function-call form `f(...)` (self-delimited);
     * `modOp`      — a remainder operation, printed with an infix
                      remainder operator;
     * `mulCluster` — a product of factors.
   Sub-expressions that print into the same class are one kind. -/
inductive OperandKind where
  | atomic
  | power
  | funcCall
  | modOp
  | mulCluster
  deriving Inhabited, DecidableEq

-- axioms-start
-- (No axiomatized callees. The ordinary recursive printing of the inner factor
--  is unchanged by the behaviour modeled here, so it is consumed as the input
--  `inner` — whatever string the renderer already produces for that factor —
--  rather than re-derived; no property of it is owed a contract. The per-kind
--  wrap ranks are modeled DEEPLY in the `pure` region (`opWeight`); no outside
--  callee is consumed, so there is no contract for G-AX to validate (it skips),
--  and the deep model's fidelity to the desired behaviour is exercised
--  mechanically by conformance_check.py (G-CONF).)
-- axioms-end

-- pure-start
/- An opaque ordinal rank for each operand kind. Only the ORDER of these
   integers matters: the wrap rule below is a single `≤` comparison against
   `negLevel`, so any choice that preserves the kind ordering — `atomic` >
   `funcCall` > `power` > `modOp` > `mulCluster` — yields the same wrap
   decisions. Concrete integers (rather than a `<` relation) keep the
   comparison decidable in the kernel (order-only — see DECISIONS.md
   float-order note). The exact ranks are not meaningful; the per-kind wrap
   table is pinned extensionally by the `needsParen_*` lemmas below. -/
def opWeight : OperandKind → Int
  | .atomic     => 2000
  | .power      => 120
  | .funcCall   => 140
  | .modOp      => 100
  | .mulCluster => 99

/- The threshold rank for a leading unary minus, sitting strictly between the
   ranks of `power` and `modOp`. A factor whose rank does not exceed this
   threshold is wrapped in parentheses, so that the leading minus governs the
   whole factor rather than only its first piece. Like the ranks above, the
   exact value is not meaningful — only that it separates the wrapped kinds
   (`modOp`, `mulCluster`) from the bare ones (`atomic`, `power`, `funcCall`),
   exactly as the `needsParen_*` lemmas record. -/
def negLevel : Int := 110

/- Whether a factor of the given kind must be parenthesized under a leading
   unary minus: exactly when its rank does not exceed the threshold. -/
def needsParen (k : OperandKind) : Bool := decide (opWeight k ≤ negLevel)

/- The printed form of a negated single factor: a leading minus followed by the
   factor's own printed form `inner`, wrapped in parentheses precisely when the
   factor's kind is one that must be wrapped (per `needsParen`). -/
def renderNeg (k : OperandKind) (inner : List Char) : List Char :=
  '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner)

@[grind] lemma renderNeg_def (k : OperandKind) (inner : List Char) :
    renderNeg k inner =
      '-' :: (if needsParen k then ('(' :: inner) ++ [')'] else inner) := rfl

/- The remainder operation and a multiplicative cluster are both wrapped. -/
@[grind, simp] lemma needsParen_modOp : needsParen .modOp = true := by decide
@[grind, simp] lemma needsParen_mul   : needsParen .mulCluster = true := by decide
/- An atom, a power, and a function call are not wrapped. -/
@[grind, simp] lemma needsParen_atom  : needsParen .atomic = false := by decide
@[grind, simp] lemma needsParen_pow   : needsParen .power = false := by decide
@[grind, simp] lemma needsParen_func  : needsParen .funcCall = false := by decide
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Print a single factor `inner` that sits directly under a leading unary minus,
   given the factor's kind `k`. The result is the factor's own printed form,
   parenthesized exactly when the factor's kind is one that must be wrapped,
   with the leading minus prepended. Both inputs are read-only (neither is
   `mut`; the print mutates nothing — directive 5); the result is a fresh
   sequence.

   The pinned behaviour: a remainder operation and a product cluster are
   wrapped (so the minus governs the whole factor); an atom, a power, and a
   self-delimited function call are not. -/
method printNegatedFactor (k : OperandKind) (inner : List Char) return (out : List Char)
  ensures out = renderNeg k inner
  ensures k = .modOp     → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .mulCluster → out = '-' :: (('(' :: inner) ++ [')'])
  ensures k = .power     → out = '-' :: inner
  ensures k = .atomic    → out = '-' :: inner
  ensures k = .funcCall  → out = '-' :: inner
  do
    -- impl-start
    -- Look up the factor's binding strength and compare it to the unary-minus
    -- threshold; wrap the factor when it binds no more tightly than the
    -- threshold, then prepend the leading minus.
    let wrapped : List Char :=
      if needsParen k then ('(' :: inner) ++ [')'] else inner
    return '-' :: wrapped
    -- impl-end

prove_correct printNegatedFactor by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All commands run from there. same_spec=True verified for all 11 attacks + pos (velvet backend, byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; parallel batches of 4):
- pos.lean (exact gold impl) => EXIT 0 VERIFIES (positive control OK)
- atk_1 (prepatch bug 1: threshold 80 = 2*40 negated-product strength; mulCluster@99 & modOp@100 left unwrapped) => EXIT 1 FAIL (unsolved goal)
- atk_2 (prepatch bug 2: modOp looked up at generic 140 = 2*70, left unwrapped) => EXIT 1 FAIL
- atk_3 (partial-domain: never wrap, `return '-'::inner`) => EXIT 1 FAIL
- atk_4 (boundary: always wrap) => EXIT 1 FAIL
- atk_5 (control-flow-effect: also wrap funcCall, which must be bare) => EXIT 1 FAIL
- atk_6 (ungrounded-oracle echo: `return renderNeg k inner`) => EXIT 0 VERIFIES (behaviourally correct)
- atk_7 (inverted comparison: wrap iff opWeight >= negLevel) => EXIT 1 FAIL
- atk_8 (drop leading minus: `return wrapped`) => EXIT 1 FAIL
- atk_9 (echo variant via `decide (opWeight k <= negLevel)` — behaviourally correct but prover cannot reduce the non-syntactic form; unsolved goal) => EXIT 1 FAIL
- atk_10 (strict `<` instead of `<=`; behaviourally identical since no strength equals 110, but non-syntactic form) => EXIT 1 FAIL
- atk_11 (also wrap power, which must be bare) => EXIT 1 FAIL

MANDATORY RESOLVE (protocol step 2) for the ONLY verifying wrong-impl (atk_6): its faithful refined patch = the gold patch (atk_6 is behaviourally identical to the frozen pure oracle, so the refinement map yields exactly the gold Site C codeprinter.py + Site P precedence.py edits). Materialized Command: SBU_BENCHMARK=swe_bench_verified run_resolve('sympy__sympy-22080', <patch>, run_id='sbu-audit-eq-o79nr0fw-atk6', timeout=1200). OBSERVED RESULT: COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. => the verifying attack's faithful patch RESOLVES. No verify=>not-resolve gap. (This closes the prior pass's INCONCLUSIVE, which was solely because that resolve run never completed — same-shaped echo attack, now executed and confirmed RESOLVED.)

REFINEMENT.MD AUDIT (A-legs focus): step 2 (inner <-> self._print(item)) is A-consumed — unchanged callee consumed as input, no contract owed, and G-CONF supplies the REAL pycode(factor) identically on shadow and oracle sides; correspondence to the real callee holds. Steps 3/5 (opWeight/needsParen — the CHANGED parenthesization) are correctly R (G-CONF), NOT A-reference: precedence/parenthesize are exactly the callees the gold patch edits (directive 7 forbids A-reference for changed callees; G-AX runs unpatched where precedence(Mod)==70 and the threshold branch doesn't exist). Steps 1/4/6 are R / R+I / I. NO kind-3 (inexpressible-changed-op) legs. G-AX legitimately SKIPs (no consumed axiom, no A-reference); the changed-op fidelity is exercised by G-CONF (meta: pass, 96763 single-negated-factor inputs, seed 22080, 0 disagreements against the patched pycode(-e)). Model<->patch correspondence holds: opWeight(kind)==precedence(rep)*2, negLevel==55*2, needsParen == (precedence(rep)<=55) == patched parenthesize wrap.

CONCLUSION: 11 distinct same-spec wrong impls attacked (>=5 required, covering prepatch bugs, partial-domain, boundary, control-flow-effect, inverted-comparison, drop-effect, ungrounded-oracle echo, and two non-syntactic echo variants); 10 correctly rejected by verification; the single verifying impl is the oracle echo, which is behaviourally correct and whose materialized faithful patch RESOLVES under the official harness. The postcondition totally pins output pointwise over the frozen pure model, so verify=>correct holds for this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: velvet/Lean, sympy__sympy-22080, base 3f8c8c2377. Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec(Solution.lean, Solution_prepatch_2.lean)=True. The spec models _print_Mul's single-negative-factor branch; it abstracts the factor a[0] to one of 5 OperandKinds and wraps exactly {modOp, mulCluster} via needsParen (opWeight k <= negLevel=110). Faithfulness of this abstraction to the patched renderer holds because the change reads ONLY precedence(a[0]) vs the fixed level 55: post-patch precedence values are Mod=50 (wrap), Mul-cluster=50 (wrap), Pow=60 (no wrap), Func=70 (no wrap), Atom=1000 (no wrap); the model's ranks (100,99,120,140,2000 with threshold 110) reproduce every <= relation exactly (order-only x2 scaling). UnevaluatedExpr single-wrapper (-0.5 shift) never crosses 55 and is classified by inner; nested wrappers are excluded from Requires (classify returns None -> skipped), which is a legitimate Requires narrowing, not an over-claim. Verified the modeled function agrees with the real callee on all reachable in-Requires inputs => the spec is NOT too strong / does not drift. Note: meta.json records G-PANEL-2 fail (likely a stale/pre-policy verdict); my independent re-derivation finds FAITHFUL. Separately, G-EQ and G-PANEL-1 are recorded fail — outside this gate's scope.

Counterexample / evidence:

```
None. Instrumented the REAL patched _print_Mul to capture the actual single factor a[0] and compared classify->needsParen against the real precedence(a[0])<=55 over 35,832 in-branch in-Requires fuzzed inputs (symbols, powers with exponents 2/3/-1/-2/1/2/-1/2, functions sin/cos/tan/exp/gamma/Abs/floor/ceiling, Mod, products, Rationals, UnevaluatedExpr): 0 wrap-decision mismatches. Bundle conformance_check.py against the patched repo: 96,763 inputs, 0 disagreements.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3): leakage / gold-reconstruction assessment for velvet bundle sympy__sympy-22080.

SPEC REGION INTEGRITY: swebench_unified.markers.same_spec confirms Solution.lean's spec region is byte-identical to both Solution_prepatch.lean and Solution_prepatch_2.lean (True for both) — the frozen spec is what both prepatches and the impl verify against.

MECHANICAL SCREEN: leakage.screen over the spec view passes (0 hard failures). No diff markers, no patched file paths (codeprinter.py / precedence.py), no patched module dotted-paths, no gold-patch line reproduced, no patched repo symbol (_print_Mul/precedence/PRECEDENCE/parenthesize) embedded in spec-view identifiers or named in comments, no narration terms (bug/fix/regression/etc).

SEMANTIC GOLD-RECONSTRUCTION: The public problem_statement already discloses the observable defect: -Mod(x, y) prints as '-x % y' (missing parentheses) under modules=[] code printing. The spec view goes NO further toward the gold edit than that:
  * It uses fully abstracted names (printNegatedFactor, OperandKind, opWeight, needsParen, negLevel, renderNeg) — none echo the two patched repo symbols/sites (_print_Mul single-negative-factor branch; PRECEDENCE_VALUES['Mod']).
  * The concrete gold constants (level 55 = 0.5*(Pow+Mul), the 40/70/50 precedence values) do NOT appear; the spec uses order-only ×2-scaled opaque ranks (110/100/99/120/140/2000) explicitly declared non-meaningful. A solver reading the spec learns which operand KINDS wrap under a leading minus, not that the fix lives in precedence.py's Mod entry or in _print_Mul at level 55.
  * The spec encodes only the CORRECT post-fix behaviour (modOp and mulCluster wrapped; atomic/power/funcCall bare). A faithful spec is required to pin correct behaviour; doing so is not gold-edit disclosure. The one behavioural fact beyond the problem statement — that a product cluster factor -(x*x*x*x) must also wrap — is a consequence of correct semantics, not a pointer to the edit's location or mechanism.

No spec-view line reveals the gold edit beyond the public problem_statement. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
