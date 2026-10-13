# P2 adversarial audit — sympy__sympy-16597

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,7 +124,7 @@
 boundedness is forced via even → integer → rational → finite. -/
 def implementation_deduceEven : KB :=
   { integer := some true, rational := some true, real := some true,
-    finite := some true, even := some true, odd := some false,
+    finite := none, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
     infinite := none, complex := some true, noninteger := some false,
     prime := none, composite := none }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,7 +124,7 @@
 boundedness is forced via even → integer → rational → finite. -/
 def implementation_deduceEven : KB :=
   { integer := some true, rational := some true, real := some true,
-    finite := some true, even := some true, odd := some false,
+    finite := some true, even := some true, odd := none,
     algebraic := some true, transcendental := some false, irrational := some false,
     infinite := none, complex := some true, noninteger := some false,
     prime := none, composite := none }
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,7 +123,7 @@
 seed `even = true` along the containments yields a fully resolved record;
 boundedness is forced via even → integer → rational → finite. -/
 def implementation_deduceEven : KB :=
-  { integer := some true, rational := some true, real := some true,
+  { integer := some false, rational := some true, real := some true,
     finite := some true, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
     infinite := none, complex := some true, noninteger := some false,
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,7 +171,7 @@
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
     irrational := some false, infinite := some true, complex := some true,
-    noninteger := some true, prime := some false, composite := some false }
+    noninteger := some false, prime := some false, composite := some false }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -167,7 +167,7 @@
 so rational / algebraic / irrational / transcendental — and hence integer / even
 / odd / prime / composite — all resolve to false; the quantity is a non-integer. -/
 def implementation_deduceInfinite : KB :=
-  { integer := some false, rational := some false, real := some true,
+  { integer := none, rational := some false, real := some true,
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
     irrational := some false, infinite := some true, complex := some true,
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,7 +171,7 @@
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
     irrational := some false, infinite := some true, complex := some true,
-    noninteger := some true, prime := some false, composite := some false }
+    noninteger := some true, prime := some false, composite := none}
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,7 +171,7 @@
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
     irrational := some false, infinite := some true, complex := some true,
-    noninteger := some true, prime := some false, composite := some false }
+    noninteger := some true, prime := some true, composite := some false }
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,7 +126,7 @@
   { integer := some true, rational := some true, real := some true,
     finite := some true, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
-    infinite := none, complex := some true, noninteger := some false,
+    infinite := none, complex := some false, noninteger := some false,
     prime := none, composite := none }
 -- impl-end
 
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -126,7 +126,7 @@
   { integer := some true, rational := some true, real := some true,
     finite := some true, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
-    infinite := none, complex := some true, noninteger := some false,
+    infinite := some false, complex := some true, noninteger := some false,
     prime := none, composite := none }
 -- impl-end
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -170,7 +170,7 @@
   { integer := some false, rational := some false, real := some true,
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
-    irrational := some false, infinite := some true, complex := some true,
+    irrational := some false, infinite := some true, complex := some false,
     noninteger := some true, prime := some false, composite := some false }
 -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,7 +126,7 @@
   { integer := some true, rational := some true, real := some true,
     finite := some true, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
-    infinite := none, complex := some true, noninteger := some false,
+    infinite := none, complex := some true, noninteger := some true,
     prime := none, composite := none }
 -- impl-end
 
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -167,7 +167,7 @@
 so rational / algebraic / irrational / transcendental — and hence integer / even
 / odd / prime / composite — all resolve to false; the quantity is a non-integer. -/
 def implementation_deduceInfinite : KB :=
-  { integer := some false, rational := some false, real := some true,
+  { integer := some false, rational := some false, real := some false,
     finite := some false, even := some false, odd := some false,
     algebraic := some false, transcendental := some false,
     irrational := some false, infinite := some true, complex := some true,
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,7 +123,7 @@
 seed `even = true` along the containments yields a fully resolved record;
 boundedness is forced via even → integer → rational → finite. -/
 def implementation_deduceEven : KB :=
-  { integer := some true, rational := some true, real := some true,
+  { integer := some true, rational := some false, real := some true,
     finite := some true, even := some true, odd := some false,
     algebraic := some true, transcendental := some false, irrational := some false,
     infinite := none, complex := some true, noninteger := some false,
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The three-valued status table for a single numeric quantity. Each field is a
fuzzy fact about the quantity: `some true` (the property is known to hold),
`some false` (it is known not to hold), or `none` (undetermined). Only the
properties the two witnessed deductions touch are carried.

`finite` is the boundedness fact: a quantity is `finite` when its absolute value
is bounded. The behaviour under specification is that membership in the "small"
number sets (rational / algebraic / irrational / transcendental) forces
boundedness.
-/
structure KB where
  integer : Option Bool
  rational : Option Bool
  real : Option Bool
  finite : Option Bool
  even : Option Bool
  odd : Option Bool
  algebraic : Option Bool
  transcendental : Option Bool
  irrational : Option Bool
  infinite : Option Bool
  complex : Option Bool
  noninteger : Option Bool
  prime : Option Bool
  composite : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
-- (No opaque callee is consumed. The containment theory below is the behaviour
--  under specification itself; it is spelled out deeply as `consistentTheory`
--  and validated against the real property-deduction engine out of band by
--  conformance_check.py / G-CONF, not relied on as an axiom.)
-- axioms-end

-- pure-start
/-- A fact table is CLOSED under the intended set-containment relations between
the number classes. Each `A is true ⇒ B is true` clause is a containment; each
`A is false ⇒ B is false` clause is its contrapositive. The boundedness-forcing
containments are the behaviour under specification:

  * a rational quantity is real, is algebraic, AND is bounded;
  * a real quantity is complex;
  * an algebraic quantity is complex AND is bounded;
  * an irrational quantity is real, is not rational, AND is bounded;
  * a transcendental quantity is complex, is not algebraic, AND is bounded;
  * an integer is rational; an even or odd quantity is an integer; a prime or
    composite quantity is an integer; an even quantity is not odd;
  * an unbounded quantity is not bounded; a real quantity that is not an integer
    is a non-integer, and an integer is not a non-integer.

Closure is two-directional: each containment also propagates its contrapositive,
so a quantity known NOT to be bounded is thereby known NOT to be rational /
algebraic / irrational / transcendental, hence not an integer, hence not even /
odd / prime / composite. -/
def consistentTheory (k : KB) : Prop :=
  -- integer → rational ; ¬rational → ¬integer
  (k.integer = some true → k.rational = some true)
  ∧ (k.rational = some false → k.integer = some false)
  -- rational → real ; rational → algebraic ; rational → finite
  ∧ (k.rational = some true → k.real = some true)
  ∧ (k.rational = some true → k.algebraic = some true)
  ∧ (k.rational = some true → k.finite = some true)
  -- real → complex
  ∧ (k.real = some true → k.complex = some true)
  -- algebraic → complex ; algebraic → finite
  ∧ (k.algebraic = some true → k.complex = some true)
  ∧ (k.algebraic = some true → k.finite = some true)
  -- even → integer ; odd → integer ; ¬integer → ¬even ; ¬integer → ¬odd
  ∧ (k.even = some true → k.integer = some true)
  ∧ (k.odd = some true → k.integer = some true)
  ∧ (k.integer = some false → k.even = some false)
  ∧ (k.integer = some false → k.odd = some false)
  -- even ⇒ not odd (the ¬odd direction of even ≡ integer ∧ ¬odd)
  ∧ (k.even = some true → k.odd = some false)
  -- prime → integer ; composite → integer ; ¬integer → ¬prime, ¬composite
  ∧ (k.prime = some true → k.integer = some true)
  ∧ (k.composite = some true → k.integer = some true)
  ∧ (k.integer = some false → k.prime = some false)
  ∧ (k.integer = some false → k.composite = some false)
  -- irrational → real ; irrational → ¬rational ; irrational → finite
  ∧ (k.irrational = some true → k.real = some true)
  ∧ (k.irrational = some true → k.rational = some false)
  ∧ (k.irrational = some true → k.finite = some true)
  -- transcendental → complex ; → ¬algebraic ; → finite
  ∧ (k.transcendental = some true → k.complex = some true)
  ∧ (k.transcendental = some true → k.algebraic = some false)
  ∧ (k.transcendental = some true → k.finite = some true)
  -- infinite → ¬finite
  ∧ (k.infinite = some true → k.finite = some false)
  -- contrapositives of the four boundedness-forcing containments
  ∧ (k.finite = some false → k.rational = some false)
  ∧ (k.finite = some false → k.algebraic = some false)
  ∧ (k.finite = some false → k.irrational = some false)
  ∧ (k.finite = some false → k.transcendental = some false)
  -- a real non-integer is a non-integer ; an integer is not a non-integer
  ∧ (k.real = some true ∧ k.integer = some false → k.noninteger = some true)
  ∧ (k.integer = some true → k.noninteger = some false)
-- pure-end

-- post-conditions-start
/-- Postcondition for the closure of the seed `even = true`. The table must be
closed under `consistentTheory`, must retain the `even` seed, and — via the
`rational → finite` containment (even → integer → rational → finite) — must resolve
`finite = some true`. A rational quantity is algebraic and not irrational, so
`irrational`/`transcendental` resolve to false; its primality is undetermined,
so `prime`/`composite` stay `none`. This pins every fact the F2P test observes. -/
def problem_spec_deduceEven (out : KB) : Prop :=
  consistentTheory out
  ∧ out.even = some true
  ∧ out.finite = some true
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.prime = none
  ∧ out.composite = none
-- post-conditions-end

-- impl-start
/-- The closed fact table for a quantity seeded as `even`. Forward-chaining the
seed `even = true` along the containments yields a fully resolved record;
boundedness is forced via even → integer → rational → finite. -/
def implementation_deduceEven : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := some true, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }
-- impl-end

-- proof-start
theorem correct_deduceEven :
    problem_spec_deduceEven implementation_deduceEven := by
  unfold problem_spec_deduceEven implementation_deduceEven consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end

-- post-conditions-start
/-- Postcondition for the closure of an unbounded real quantity (seeded
`infinite` and `real`). `infinite → ¬finite` forces `finite = some false`; via
the contrapositives `¬finite → ¬{rational, algebraic, irrational,
transcendental}`, then `¬rational → ¬integer → ¬{even, odd, prime, composite}`,
every set membership resolves to false; `real → complex` gives `complex`, and a
real non-integer is a `noninteger`. This pins every fact the F2P tests observe
for `oo` / `-oo`. -/
def problem_spec_deduceInfinite (out : KB) : Prop :=
  consistentTheory out
  ∧ out.infinite = some true
  ∧ out.real = some true
  ∧ out.finite = some false
  ∧ out.rational = some false
  ∧ out.integer = some false
  ∧ out.even = some false
  ∧ out.odd = some false
  ∧ out.algebraic = some false
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.composite = some false
  ∧ out.noninteger = some true
-- post-conditions-end

-- impl-start
/-- The closed fact table for an unbounded real quantity (seeded `infinite` and
`real`). Not-bounded contradicts every set whose membership forces boundedness,
so rational / algebraic / irrational / transcendental — and hence integer / even
/ odd / prime / composite — all resolve to false; the quantity is a non-integer. -/
def implementation_deduceInfinite : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }
-- impl-end

-- proof-start
theorem correct_deduceInfinite :
    problem_spec_deduceInfinite implementation_deduceInfinite := by
  unfold problem_spec_deduceInfinite implementation_deduceInfinite consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

GATE: G-EQ refinement-fidelity audit for sympy__sympy-16597 (Lean). SPEC SHAPE: deep-model WITNESS spec (patch_equals_gold=True, opaque_callees=[], one deep_model_reference). Two triples: deduceEven (seed even=True) and deduceInfinite (seed infinite=True,real=True). Each implementation_* is a STATIC deduced fact table (KB record of Option Bool); consistentTheory is the closure predicate; the real property-deduction engine appears only as an A-reference validated by G-CONF (conformance_check.py). No opaque consumed callee -> no ungrounded oracle to echo-attack.

SAME-SPEC: all 13 attacks + pos_control return same_spec=True (only impl regions edited; axioms/pure/pre/post byte-identical).

EXHAUSTIVE PINNING (Python mirror of consistentTheory+postconditions, full 3^14 trit enumeration): deduceInfinite spec has EXACTLY 1 satisfying model = every field pinned to the real engine's deduction. deduceEven spec has EXACTLY 2 satisfying models, differing ONLY on the field `infinite` (some false vs none) which is NOT an F2P-observed fact; the real engine returns is_infinite=False for Symbol(even=True), so BOTH values are faithful. => no verifying same-spec impl can diverge from the gold engine on ANY F2P-observed fact.

### ATTACK VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently in bg batches of <=4):
- pos_control.lean: exit 0 (verifies). #print axioms correct_deduceEven/correct_deduceInfinite = [propext] (clean).
- atk_1.lean (deduceEven finite:=none): exit 1 FAIL. BYTE-IDENTICAL to official Solution_prepatch.lean (verified by diff) -> prepatch bug reproduced, G-DIFF holds (prepatch does NOT verify).
- atk_2 (even odd:=none): exit 1 FAIL (even->odd=false).
- atk_3 (even integer:=some false): exit 1 FAIL.
- atk_4 (inf noninteger:=some false): exit 1 FAIL.
- atk_5 (inf integer:=none): exit 1 FAIL.
- atk_6 (inf composite:=none): exit 1 FAIL.
- atk_7 (inf prime:=some true): exit 1 FAIL.
- atk_8 (even complex:=some false): exit 1 FAIL (real->complex).
- atk_9 (even infinite:=some false): exit 0 VERIFIES. clean axioms [propext]. This is the ONLY verifying same-spec variant. It MATCHES the real gold engine exactly (is_infinite=False on the sole non-observed field), so it is a faithful alternative, not a divergence.
- atk_10 (inf complex:=some false): exit 1 FAIL.
- atk_11 (even noninteger:=some true): exit 1 FAIL (integer->noninteger=false).
- atk_12 (inf real:=some false): exit 1 FAIL (postcond real=some true).
- atk_13 (even rational:=some false): exit 1 FAIL.

RESOLVE (protocol step 2, MANDATORY for every verifying impl): atk_9 is the only verifying wrong-shaped candidate. Its faithful refined patch = the gold patch (atk_9 reproduces exactly what the gold-patched engine deduces on every field, incl. non-observed infinite=False). run_resolve('sympy__sympy-16597', gold_patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved', report key ['sympy__sympy-16597']. (First attempt returned no-report due to concurrent-audit docker contention; re-run with retries=1 completed and resolved.) => NOT broken.

G-CONF cross-check: ran conformance_check.py against the gold worktree (gold patch applied) -> exit 0, 'consistentTheory + deduceEven/deduceInfinite agree ... on 407 observations, 0 disagreements'. A-reference sound.

REFINEMENT.MD LEG AUDIT: A1=R (trit<->Option Bool, dict entry<->field), A2=A-reference (consistentTheory deep model, G-CONF-validated, no opaque callee), A3/A4=R+A-reference. Section C explicitly: no kind-3 steps; the one changed op (rule theory) modelled deeply. All legs R/A-reference/I. A-legs' correspondence to real callees holds (G-CONF passed). Other gold hunks (power.py/tree.py/indexed.py) not F2P-exercised; patch ships verbatim (mapping.md sec 4).

VERDICT: SOUND. >=5 attacks run; the prepatch bug does not verify; every must-fail attack correctly fails; the single verifying same-spec variant (atk_9) matches reality and its materialized faithful patch RESOLVES under the official harness. No verify->not-resolve gap exists (spec is fully pinned on all F2P-observed facts, proved by exhaustive enumeration and confirmed by resolve).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The three-valued status table for a single numeric quantity. Each field is a
fuzzy fact about the quantity: `some true` (the property is known to hold),
`some false` (it is known not to hold), or `none` (undetermined). Only the
properties the two witnessed deductions touch are carried.

`finite` is the boundedness fact: a quantity is `finite` when its absolute value
is bounded. The behaviour under specification is that membership in the "small"
number sets (rational / algebraic / irrational / transcendental) forces
boundedness.
-/
structure KB where
  integer : Option Bool
  rational : Option Bool
  real : Option Bool
  finite : Option Bool
  even : Option Bool
  odd : Option Bool
  algebraic : Option Bool
  transcendental : Option Bool
  irrational : Option Bool
  infinite : Option Bool
  complex : Option Bool
  noninteger : Option Bool
  prime : Option Bool
  composite : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
-- (No opaque callee is consumed. The containment theory below is the behaviour
--  under specification itself; it is spelled out deeply as `consistentTheory`
--  and validated against the real property-deduction engine out of band by
--  conformance_check.py / G-CONF, not relied on as an axiom.)
-- axioms-end

-- pure-start
/-- A fact table is CLOSED under the intended set-containment relations between
the number classes. Each `A is true ⇒ B is true` clause is a containment; each
`A is false ⇒ B is false` clause is its contrapositive. The boundedness-forcing
containments are the behaviour under specification:

  * a rational quantity is real, is algebraic, AND is bounded;
  * a real quantity is complex;
  * an algebraic quantity is complex AND is bounded;
  * an irrational quantity is real, is not rational, AND is bounded;
  * a transcendental quantity is complex, is not algebraic, AND is bounded;
  * an integer is rational; an even or odd quantity is an integer; a prime or
    composite quantity is an integer; an even quantity is not odd;
  * an unbounded quantity is not bounded; a real quantity that is not an integer
    is a non-integer, and an integer is not a non-integer.

Closure is two-directional: each containment also propagates its contrapositive,
so a quantity known NOT to be bounded is thereby known NOT to be rational /
algebraic / irrational / transcendental, hence not an integer, hence not even /
odd / prime / composite. -/
def consistentTheory (k : KB) : Prop :=
  -- integer → rational ; ¬rational → ¬integer
  (k.integer = some true → k.rational = some true)
  ∧ (k.rational = some false → k.integer = some false)
  -- rational → real ; rational → algebraic ; rational → finite
  ∧ (k.rational = some true → k.real = some true)
  ∧ (k.rational = some true → k.algebraic = some true)
  ∧ (k.rational = some true → k.finite = some true)
  -- real → complex
  ∧ (k.real = some true → k.complex = some true)
  -- algebraic → complex ; algebraic → finite
  ∧ (k.algebraic = some true → k.complex = some true)
  ∧ (k.algebraic = some true → k.finite = some true)
  -- even → integer ; odd → integer ; ¬integer → ¬even ; ¬integer → ¬odd
  ∧ (k.even = some true → k.integer = some true)
  ∧ (k.odd = some true → k.integer = some true)
  ∧ (k.integer = some false → k.even = some false)
  ∧ (k.integer = some false → k.odd = some false)
  -- even ⇒ not odd (the ¬odd direction of even ≡ integer ∧ ¬odd)
  ∧ (k.even = some true → k.odd = some false)
  -- prime → integer ; composite → integer ; ¬integer → ¬prime, ¬composite
  ∧ (k.prime = some true → k.integer = some true)
  ∧ (k.composite = some true → k.integer = some true)
  ∧ (k.integer = some false → k.prime = some false)
  ∧ (k.integer = some false → k.composite = some false)
  -- irrational → real ; irrational → ¬rational ; irrational → finite
  ∧ (k.irrational = some true → k.real = some true)
  ∧ (k.irrational = some true → k.rational = some false)
  ∧ (k.irrational = some true → k.finite = some true)
  -- transcendental → complex ; → ¬algebraic ; → finite
  ∧ (k.transcendental = some true → k.complex = some true)
  ∧ (k.transcendental = some true → k.algebraic = some false)
  ∧ (k.transcendental = some true → k.finite = some true)
  -- infinite → ¬finite
  ∧ (k.infinite = some true → k.finite = some false)
  -- contrapositives of the four boundedness-forcing containments
  ∧ (k.finite = some false → k.rational = some false)
  ∧ (k.finite = some false → k.algebraic = some false)
  ∧ (k.finite = some false → k.irrational = some false)
  ∧ (k.finite = some false → k.transcendental = some false)
  -- a real non-integer is a non-integer ; an integer is not a non-integer
  ∧ (k.real = some true ∧ k.integer = some false → k.noninteger = some true)
  ∧ (k.integer = some true → k.noninteger = some false)
-- pure-end

-- post-conditions-start
/-- Postcondition for the closure of the seed `even = true`. The table must be
closed under `consistentTheory`, must retain the `even` seed, and — via the
`rational → finite` containment (even → integer → rational → finite) — must resolve
`finite = some true`. A rational quantity is algebraic and not irrational, so
`irrational`/`transcendental` resolve to false; its primality is undetermined,
so `prime`/`composite` stay `none`. This pins every fact the F2P test observes. -/
def problem_spec_deduceEven (out : KB) : Prop :=
  consistentTheory out
  ∧ out.even = some true
  ∧ out.finite = some true
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.prime = none
  ∧ out.composite = none
-- post-conditions-end

-- impl-start
/-- The closed fact table for a quantity seeded as `even`. Forward-chaining the
seed `even = true` along the containments yields a fully resolved record;
boundedness is forced via even → integer → rational → finite. -/
def implementation_deduceEven : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := some true, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }
-- impl-end

-- proof-start
theorem correct_deduceEven :
    problem_spec_deduceEven implementation_deduceEven := by
  unfold problem_spec_deduceEven implementation_deduceEven consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end

-- post-conditions-start
/-- Postcondition for the closure of an unbounded real quantity (seeded
`infinite` and `real`). `infinite → ¬finite` forces `finite = some false`; via
the contrapositives `¬finite → ¬{rational, algebraic, irrational,
transcendental}`, then `¬rational → ¬integer → ¬{even, odd, prime, composite}`,
every set membership resolves to false; `real → complex` gives `complex`, and a
real non-integer is a `noninteger`. This pins every fact the F2P tests observe
for `oo` / `-oo`. -/
def problem_spec_deduceInfinite (out : KB) : Prop :=
  consistentTheory out
  ∧ out.infinite = some true
  ∧ out.real = some true
  ∧ out.finite = some false
  ∧ out.rational = some false
  ∧ out.integer = some false
  ∧ out.even = some false
  ∧ out.odd = some false
  ∧ out.algebraic = some false
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.composite = some false
  ∧ out.noninteger = some true
-- post-conditions-end

-- impl-start
/-- The closed fact table for an unbounded real quantity (seeded `infinite` and
`real`). Not-bounded contradicts every set whose membership forces boundedness,
so rational / algebraic / irrational / transcendental — and hence integer / even
/ odd / prime / composite — all resolve to false; the quantity is a non-integer. -/
def implementation_deduceInfinite : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }
-- impl-end

-- proof-start
theorem correct_deduceInfinite :
    problem_spec_deduceInfinite implementation_deduceInfinite := by
  unfold problem_spec_deduceInfinite implementation_deduceInfinite consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

GATE: G-EQ refinement-fidelity audit for sympy__sympy-16597 (Lean). SPEC SHAPE: deep-model WITNESS spec (patch_equals_gold=True, opaque_callees=[], one deep_model_reference). Two triples: deduceEven (seed even=True) and deduceInfinite (seed infinite=True,real=True). Each implementation_* is a STATIC deduced fact table (KB record of Option Bool); consistentTheory is the closure predicate; the real property-deduction engine appears only as an A-reference validated by G-CONF (conformance_check.py). No opaque consumed callee -> no ungrounded oracle to echo-attack.

SAME-SPEC: all 13 attacks + pos_control return same_spec=True (only impl regions edited; axioms/pure/pre/post byte-identical).

EXHAUSTIVE PINNING (Python mirror of consistentTheory+postconditions, full 3^14 trit enumeration): deduceInfinite spec has EXACTLY 1 satisfying model = every field pinned to the real engine's deduction. deduceEven spec has EXACTLY 2 satisfying models, differing ONLY on the field `infinite` (some false vs none) which is NOT an F2P-observed fact; the real engine returns is_infinite=False for Symbol(even=True), so BOTH values are faithful. => no verifying same-spec impl can diverge from the gold engine on ANY F2P-observed fact.

### ATTACK VERIFICATIONS (scripts/lean_verify.sh, 300s cap, run concurrently in bg batches of <=4):
- pos_control.lean: exit 0 (verifies). #print axioms correct_deduceEven/correct_deduceInfinite = [propext] (clean).
- atk_1.lean (deduceEven finite:=none): exit 1 FAIL. BYTE-IDENTICAL to official Solution_prepatch.lean (verified by diff) -> prepatch bug reproduced, G-DIFF holds (prepatch does NOT verify).
- atk_2 (even odd:=none): exit 1 FAIL (even->odd=false).
- atk_3 (even integer:=some false): exit 1 FAIL.
- atk_4 (inf noninteger:=some false): exit 1 FAIL.
- atk_5 (inf integer:=none): exit 1 FAIL.
- atk_6 (inf composite:=none): exit 1 FAIL.
- atk_7 (inf prime:=some true): exit 1 FAIL.
- atk_8 (even complex:=some false): exit 1 FAIL (real->complex).
- atk_9 (even infinite:=some false): exit 0 VERIFIES. clean axioms [propext]. This is the ONLY verifying same-spec variant. It MATCHES the real gold engine exactly (is_infinite=False on the sole non-observed field), so it is a faithful alternative, not a divergence.
- atk_10 (inf complex:=some false): exit 1 FAIL.
- atk_11 (even noninteger:=some true): exit 1 FAIL (integer->noninteger=false).
- atk_12 (inf real:=some false): exit 1 FAIL (postcond real=some true).
- atk_13 (even rational:=some false): exit 1 FAIL.

RESOLVE (protocol step 2, MANDATORY for every verifying impl): atk_9 is the only verifying wrong-shaped candidate. Its faithful refined patch = the gold patch (atk_9 reproduces exactly what the gold-patched engine deduces on every field, incl. non-observed infinite=False). run_resolve('sympy__sympy-16597', gold_patch, timeout=1800) => RESOLVED=True, completed=True, note='resolved', report key ['sympy__sympy-16597']. (First attempt returned no-report due to concurrent-audit docker contention; re-run with retries=1 completed and resolved.) => NOT broken.

G-CONF cross-check: ran conformance_check.py against the gold worktree (gold patch applied) -> exit 0, 'consistentTheory + deduceEven/deduceInfinite agree ... on 407 observations, 0 disagreements'. A-reference sound.

REFINEMENT.MD LEG AUDIT: A1=R (trit<->Option Bool, dict entry<->field), A2=A-reference (consistentTheory deep model, G-CONF-validated, no opaque callee), A3/A4=R+A-reference. Section C explicitly: no kind-3 steps; the one changed op (rule theory) modelled deeply. All legs R/A-reference/I. A-legs' correspondence to real callees holds (G-CONF passed). Other gold hunks (power.py/tree.py/indexed.py) not F2P-exercised; patch ships verbatim (mapping.md sec 4).

VERDICT: SOUND. >=5 attacks run; the prepatch bug does not verify; every must-fail attack correctly fails; the single verifying same-spec variant (atk_9) matches reality and its materialized faithful patch RESOLVES under the official harness. No verify->not-resolve gap exists (spec is fully pinned on all F2P-observed facts, proved by exhaustive enumeration and confirmed by resolve).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sympy__sympy-16597 (lean). The changed behaviour is the set-containment rule theory of sympy's three-valued fact engine (gold adds boundedness conjuncts: rational/algebraic/irrational/transcendental -> finite in _assume_rules). It is modelled DEEPLY as `consistentTheory` + two closed fact tables (deduceEven, deduceInfinite); there is no opaque consumed callee, so the real engine (FactKB.deduce_all_facts over edited _assume_rules) is an A-reference validated by G-CONF.

Checks performed:
1. Spec compiles: scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_deduceEven/correct_deduceInfinite` -> only [propext]; no sorryAx (proofs are real, not fake).
2. same_spec (swebench_unified.markers.same_spec with LeanBackend.language) between Solution.lean and Solution_prepatch.lean = True; spec regions byte-identical, only deduceEven impl region differs.
3. Real callee agreement: ran the REAL patched engine at base_commit worktree (assumptions.py confirmed patched: rational->real&finite, algebraic->complex&finite, irrational==real&!rational&finite). implementation_deduceEven's table matches Symbol('e',even=True) field-for-field (integer/rational/real/finite/algebraic/complex=True, odd/noninteger/transcendental/irrational=False, prime/composite=None). implementation_deduceInfinite matches S.Infinity and S.NegativeInfinity field-for-field (finite=False, all set memberships False, noninteger=True, complex=True).
4. consistentTheory is NOT too strong: ran conformance_check.py against the real patched engine -> exit 0, 407 observations, 0 disagreements. Independently probed every clause of consistentTheory over 7747 satisfiable TRIPLE-seed symbol tables (beyond the check's singles+pairs) against the real engine -> 0 clause violations. The real engine never produces a fact table that falsifies any consistentTheory clause.
5. Bound to the change: conformance_check.py fails on the prepatch worktree with 'even quantity must be finite, got None', so the modelled theory captures the patched behaviour specifically, not a spec that passes either version.

No input was found where the spec disagrees with the real repo behaviour. The spec is faithful and appropriately tight (its postconditions are exactly the F2P-observed deductions; consistentTheory over-covers only reachable facts, each verified against the real engine).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean) exposes only KB, consistentTheory, and the two problem_spec_* postconditions; impl and proof regions are elided ('-- implementation elided — supplied by the consumer'). same_spec(Solution.lean, Solution_prepatch.lean)=True, so the discriminating info lives in the elided impl, not the spec view.

Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures and zero warnings:
- L1: no diff markers; no gold-patch changed line reproduced (Lean 'k.rational = some true → k.finite = some true' is not a normalized reproduction of the Python rule strings like "'rational -> real & finite'").
- L2: no patched file path or dotted module path present (no assumptions.py / ask_generated / _assume_rules / FactRules in the view).
- L2/L5: patched repo symbols are {get_known_facts, get_known_facts_cnf, get_known_facts_dict, eval_is_polynomial, print_tree}; none is embedded in any spec-view identifier (consistentTheory / deduceEven / deduceInfinite) nor named in any comment/docstring.
- L3: no bug/fix narration; docstrings use neutral 'behaviour under specification' phrasing.

Substantive judgment: the public problem_statement states only the even⇒finite expectation. The spec models the broader boundedness-containment behavior (rational/algebraic/irrational/transcendental → finite) abstractly. That is the legitimate job of a formal spec (verify ⇒ resolve) — it encodes target behavior in an ungrounded Lean model and does NOT reveal the gold diff, the edited files, the edited symbols, or any narration of the change. Describing target behavior is not leaking the gold edit. No line in the spec view leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
