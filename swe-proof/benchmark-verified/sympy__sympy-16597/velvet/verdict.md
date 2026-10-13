# P2 adversarial audit — sympy__sympy-16597

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Exhaustive enumeration over all 3^14 KB tables proves the entire (postconditions AND consistentTheory) verifying space is exactly {gold, atk_3} for deduceEven (differing ONLY in the free field `infinite` in {some false, none}) and exactly {gold} for deduceInfinite (fully pinned). atk_3 (deduceEven.infinite = some false) is the ONLY verifying non-gold impl; it is a STRICTLY MORE PRECISE, CORRECT refinement (the gold-patched engine deduces Symbol('e',even=True).is_infinite is False via even->...->finite=True and the pre-existing infinite->!finite contrapositive), so its faithful refined patch IS the gold patch and it RESOLVES. No verifying wrong impl exists.
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -155,7 +155,7 @@
     -- impl-start
     let k : KB :=
       { integer := some true, rational := some true, real := some true,
-        finite := some true, even := some true, odd := some false,
+        finite := none, even := some true, odd := some false,
         algebraic := some true, transcendental := some false, irrational := some false,
         infinite := none, complex := some true, noninteger := some false,
         prime := none, composite := none }
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -179,11 +179,11 @@
   do
     -- impl-start
     let k : KB :=
-      { integer := some false, rational := some false, real := some true,
-        finite := some false, even := some false, odd := some false,
-        algebraic := some false, transcendental := some false,
-        irrational := some false, infinite := some true, complex := some true,
-        noninteger := some true, prime := some false, composite := some false }
+      { integer := none, rational := none, real := some true,
+        finite := some false, even := none, odd := none,
+        algebraic := none, transcendental := none,
+        irrational := none, infinite := some true, complex := some true,
+        noninteger := none, prime := none, composite := none }
     return k
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -157,7 +157,7 @@
       { integer := some true, rational := some true, real := some true,
         finite := some true, even := some true, odd := some false,
         algebraic := some true, transcendental := some false, irrational := some false,
-        infinite := none, complex := some true, noninteger := some false,
+        infinite := some false, complex := some true, noninteger := some false,
         prime := none, composite := none }
     return k
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -157,7 +157,7 @@
       { integer := some true, rational := some true, real := some true,
         finite := some true, even := some true, odd := some false,
         algebraic := some true, transcendental := some false, irrational := some false,
-        infinite := none, complex := some true, noninteger := some false,
+        infinite := none, complex := some true, noninteger := none,
         prime := none, composite := none }
     return k
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -182,7 +182,7 @@
       { integer := some false, rational := some false, real := some true,
         finite := some false, even := some false, odd := some false,
         algebraic := some false, transcendental := some false,
-        irrational := some false, infinite := some true, complex := some true,
+        irrational := some false, infinite := some true, complex := none,
         noninteger := some true, prime := some false, composite := some false }
     return k
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -183,7 +183,7 @@
         finite := some false, even := some false, odd := some false,
         algebraic := some false, transcendental := some false,
         irrational := some false, infinite := some true, complex := some true,
-        noninteger := some true, prime := some false, composite := some false }
+        noninteger := some true, prime := none, composite := some false }
     return k
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
 
 /- The three-valued status table for a single numeric quantity. Each field is a
    fuzzy fact about the quantity: `some true` (the property is known to hold),
@@ -155,7 +155,7 @@
     -- impl-start
     let k : KB :=
       { integer := some true, rational := some true, real := some true,
-        finite := some true, even := some true, odd := some false,
+        finite := some true, even := some true, odd := none,
         algebraic := some true, transcendental := some false, irrational := some false,
         infinite := none, complex := some true, noninteger := some false,
         prime := none, composite := none }
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- The three-valued status table for a single numeric quantity. Each field is a
   fuzzy fact about the quantity: `some true` (the property is known to hold),
   `some false` (it is known not to hold), or `none` (undetermined). Only the
   properties the two witnessed deductions touch are carried.

   `finite` is the boundedness fact: a quantity is `finite` when its absolute
   value is bounded. The behaviour under specification is that membership in the
   "small" number sets (rational / algebraic / irrational / transcendental)
   forces boundedness. -/
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
--  conformance_check.py, not relied on as an axiom.)
-- axioms-end

-- pure-start
/- A fact table is CLOSED under the intended set-containment relations between
   the number classes. Each `A is true ⇒ B is true` clause is a containment;
   each `A is false ⇒ B is false` clause is its contrapositive. The
   boundedness-forcing containments are the behaviour under specification:

     * a rational quantity is real, is algebraic, AND is bounded;
     * a real quantity is complex;
     * an algebraic quantity is complex AND is bounded;
     * an irrational quantity is real, is not rational, AND is bounded;
     * a transcendental quantity is complex, is not algebraic, AND is bounded;
     * an integer is rational; an even or odd quantity is an integer; a prime or
       composite quantity is an integer; an even quantity is not odd;
     * an unbounded quantity is not bounded; a real quantity that is not an
       integer is a non-integer, and an integer is not a non-integer.

   Closure is two-directional: each containment also propagates its
   contrapositive, so a quantity known NOT to be bounded is thereby known NOT to
   be rational / algebraic / irrational / transcendental, hence not an integer,
   hence not even / odd / prime / composite. -/
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

/- The closed fact table for a quantity seeded as `even`. Forward-chaining the
   seed `even = true` along the containments yields a fully resolved record;
   boundedness is forced via even → integer → rational → finite. -/
def evenTable : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := some true, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }

/- The closed fact table for an unbounded real quantity (seeded `infinite` and
   `real`). Not-bounded contradicts every set whose membership forces
   boundedness, so rational / algebraic / irrational / transcendental, and
   hence integer / even / odd / prime / composite, all resolve to false; the
   quantity is a non-integer. -/
def infiniteTable : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }

@[grind] lemma evenTable_consistent : consistentTheory evenTable := by
  unfold consistentTheory evenTable; simp

@[grind] lemma infiniteTable_consistent : consistentTheory infiniteTable := by
  unfold consistentTheory infiniteTable; simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method deduceEven return (out : KB)
  ensures consistentTheory out
  ensures out.even = some true
  ensures out.finite = some true
  -- an even quantity is rational, hence algebraic and not irrational, hence not
  -- transcendental: both `irrational` and `transcendental` resolve to false.
  ensures out.transcendental = some false
  ensures out.irrational = some false
  -- a quantity seeded only as `even` is an integer but its primality is
  -- undetermined (it could be 2, or 4, …), so neither `prime` nor `composite`
  -- resolves: both stay `none`.
  ensures out.prime = none
  ensures out.composite = none
  do
    -- impl-start
    let k : KB :=
      { integer := some true, rational := some true, real := some true,
        finite := some true, even := some true, odd := some false,
        algebraic := some true, transcendental := some false, irrational := some false,
        infinite := none, complex := some true, noninteger := some false,
        prime := none, composite := none }
    return k
    -- impl-end

method deduceInfinite return (out : KB)
  ensures consistentTheory out
  ensures out.infinite = some true
  ensures out.real = some true
  ensures out.finite = some false
  ensures out.rational = some false
  ensures out.integer = some false
  ensures out.even = some false
  ensures out.odd = some false
  ensures out.algebraic = some false
  ensures out.transcendental = some false
  ensures out.irrational = some false
  ensures out.composite = some false
  ensures out.noninteger = some true
  do
    -- impl-start
    let k : KB :=
      { integer := some false, rational := some false, real := some true,
        finite := some false, even := some false, odd := some false,
        algebraic := some false, transcendental := some false,
        irrational := some false, infinite := some true, complex := some true,
        noninteger := some true, prime := some false, composite := some false }
    return k
    -- impl-end

prove_correct deduceEven by
  loom_solve
  unfold consistentTheory; simp

prove_correct deduceInfinite by
  loom_solve
  unfold consistentTheory; simp
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol complete

SPEC SHAPE: deeply-modeled containment theory (consistentTheory), NO opaque consumed callee; patch.diff is gold verbatim (G-RESOLVE). Both impls are constant KB tables pinned by postconditions + consistentTheory closure. Same_spec=True for all 7 attacks + control (velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; ran in 2 parallel batches of 4):
- pos_control.lean (gold Solution.lean): EXIT 0 = VERIFIES.
- atk_1.lean (= Solution_prepatch.lean; deduceEven.finite=none): EXIT 1 = FAILS (goal `none = some true`). PREPATCH-1 reproduced.
- atk_2.lean (= Solution_prepatch_2.lean; deduceInfinite cascade reverted to none): EXIT 1 = FAILS (`none = some true`). PREPATCH-2 reproduced.
- atk_3.lean (deduceEven.infinite: none -> some false): EXIT 0 = VERIFIES. The one genuine same-spec non-gold variation.
- atk_4.lean (deduceEven.noninteger: some false -> none): EXIT 1 = FAILS (consistentTheory integer=T->noninteger=F; unsolved `False`).
- atk_5.lean (deduceInfinite.complex: some true -> none): EXIT 1 = FAILS (real=T->complex=T).
- atk_6.lean (deduceInfinite.prime: some false -> none): EXIT 1 = FAILS (integer=F->prime=F).
- atk_7.lean (deduceEven.odd: some false -> none): EXIT 1 = FAILS (even=T->odd=F).

EXHAUSTIVE SPACE PROOF (python, all 3^14 tables x post x consistentTheory): deduceEven -> exactly 2 verifying tables, sole free field `infinite` in {some false, none}; deduceInfinite -> exactly 1 verifying table (= gold, fully pinned: complex forced some true by real->complex, prime forced some false by integer=F->prime=F). Therefore atk_3 is the ONLY verifying wrong-shaped candidate; every other value flip breaks consistentTheory (matching atk_4..7).

RESOLVE (mandatory for every verifying candidate): atk_3's faithful refined patch. Because the trit<->is_<fact> mapping makes deduceEven.infinite=some false correspond to Symbol('e',even=True).is_infinite is False, which I confirmed the gold-patched engine actually deduces (: is_even=True, is_finite=True, is_infinite=False), atk_3's faithful patch is byte-identical to gold patch.diff. Ran: run_resolve('sympy__sympy-16597', <atk_3_faithful_patch.diff>, run_id='sbu-geq-atk3-16597') -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. Faithful patch saved at atk_3_faithful_patch.diff (diff -q == gold).

REFINEMENT.MD AUDIT: legs A1 (R), A2 (A-reference), A3/A4 (R+A-reference), no kind-3 (the one changed op — the rule theory — is modeled deeply as consistentTheory, not hidden behind an oracle). A-reference correspondence VERIFIED: conformance_check.py's theory_clauses set is byte-identical (30/30 clauses) to consistentTheory's clauses (set-equal, no missing/extra). Confirmed gold patch adds exactly the four *->finite edges (rational/algebraic/irrational/transcendental) plus auto-derived contrapositives, matching consistentTheory's finite=F-> cascade. G-CONF asserts each clause at the fact level on the real patched engine over singletons + all satisfiable single/pair seeds + enumerated witnessed deductions.

VERDICT: SOUND. >=5 attacks run; positive control verifies; both prepatches reproduced; the unique verifying non-gold impl (atk_3) has a materialized faithful patch that RESOLVES under the official Docker harness. verify => correct holds for the entire same-spec verifying space.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Exhaustive enumeration over all 3^14 KB tables proves the entire (postconditions AND consistentTheory) verifying space is exactly {gold, atk_3} for deduceEven (differing ONLY in the free field `infinite` in {some false, none}) and exactly {gold} for deduceInfinite (fully pinned). atk_3 (deduceEven.infinite = some false) is the ONLY verifying non-gold impl; it is a STRICTLY MORE PRECISE, CORRECT refinement (the gold-patched engine deduces Symbol('e',even=True).is_infinite is False via even->...->finite=True and the pre-existing infinite->!finite contrapositive), so its faithful refined patch IS the gold patch and it RESOLVES. No verifying wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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

/- The three-valued status table for a single numeric quantity. Each field is a
   fuzzy fact about the quantity: `some true` (the property is known to hold),
   `some false` (it is known not to hold), or `none` (undetermined). Only the
   properties the two witnessed deductions touch are carried.

   `finite` is the boundedness fact: a quantity is `finite` when its absolute
   value is bounded. The behaviour under specification is that membership in the
   "small" number sets (rational / algebraic / irrational / transcendental)
   forces boundedness. -/
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
--  conformance_check.py, not relied on as an axiom.)
-- axioms-end

-- pure-start
/- A fact table is CLOSED under the intended set-containment relations between
   the number classes. Each `A is true ⇒ B is true` clause is a containment;
   each `A is false ⇒ B is false` clause is its contrapositive. The
   boundedness-forcing containments are the behaviour under specification:

     * a rational quantity is real, is algebraic, AND is bounded;
     * a real quantity is complex;
     * an algebraic quantity is complex AND is bounded;
     * an irrational quantity is real, is not rational, AND is bounded;
     * a transcendental quantity is complex, is not algebraic, AND is bounded;
     * an integer is rational; an even or odd quantity is an integer; a prime or
       composite quantity is an integer; an even quantity is not odd;
     * an unbounded quantity is not bounded; a real quantity that is not an
       integer is a non-integer, and an integer is not a non-integer.

   Closure is two-directional: each containment also propagates its
   contrapositive, so a quantity known NOT to be bounded is thereby known NOT to
   be rational / algebraic / irrational / transcendental, hence not an integer,
   hence not even / odd / prime / composite. -/
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

/- The closed fact table for a quantity seeded as `even`. Forward-chaining the
   seed `even = true` along the containments yields a fully resolved record;
   boundedness is forced via even → integer → rational → finite. -/
def evenTable : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := some true, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }

/- The closed fact table for an unbounded real quantity (seeded `infinite` and
   `real`). Not-bounded contradicts every set whose membership forces
   boundedness, so rational / algebraic / irrational / transcendental, and
   hence integer / even / odd / prime / composite, all resolve to false; the
   quantity is a non-integer. -/
def infiniteTable : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }

@[grind] lemma evenTable_consistent : consistentTheory evenTable := by
  unfold consistentTheory evenTable; simp

@[grind] lemma infiniteTable_consistent : consistentTheory infiniteTable := by
  unfold consistentTheory infiniteTable; simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method deduceEven return (out : KB)
  ensures consistentTheory out
  ensures out.even = some true
  ensures out.finite = some true
  -- an even quantity is rational, hence algebraic and not irrational, hence not
  -- transcendental: both `irrational` and `transcendental` resolve to false.
  ensures out.transcendental = some false
  ensures out.irrational = some false
  -- a quantity seeded only as `even` is an integer but its primality is
  -- undetermined (it could be 2, or 4, …), so neither `prime` nor `composite`
  -- resolves: both stay `none`.
  ensures out.prime = none
  ensures out.composite = none
  do
    -- impl-start
    let k : KB :=
      { integer := some true, rational := some true, real := some true,
        finite := some true, even := some true, odd := some false,
        algebraic := some true, transcendental := some false, irrational := some false,
        infinite := none, complex := some true, noninteger := some false,
        prime := none, composite := none }
    return k
    -- impl-end

method deduceInfinite return (out : KB)
  ensures consistentTheory out
  ensures out.infinite = some true
  ensures out.real = some true
  ensures out.finite = some false
  ensures out.rational = some false
  ensures out.integer = some false
  ensures out.even = some false
  ensures out.odd = some false
  ensures out.algebraic = some false
  ensures out.transcendental = some false
  ensures out.irrational = some false
  ensures out.composite = some false
  ensures out.noninteger = some true
  do
    -- impl-start
    let k : KB :=
      { integer := some false, rational := some false, real := some true,
        finite := some false, even := some false, odd := some false,
        algebraic := some false, transcendental := some false,
        irrational := some false, infinite := some true, complex := some true,
        noninteger := some true, prime := some false, composite := some false }
    return k
    -- impl-end

prove_correct deduceEven by
  loom_solve
  unfold consistentTheory; simp

prove_correct deduceInfinite by
  loom_solve
  unfold consistentTheory; simp
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol complete

SPEC SHAPE: deeply-modeled containment theory (consistentTheory), NO opaque consumed callee; patch.diff is gold verbatim (G-RESOLVE). Both impls are constant KB tables pinned by postconditions + consistentTheory closure. Same_spec=True for all 7 attacks + control (velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; ran in 2 parallel batches of 4):
- pos_control.lean (gold Solution.lean): EXIT 0 = VERIFIES.
- atk_1.lean (= Solution_prepatch.lean; deduceEven.finite=none): EXIT 1 = FAILS (goal `none = some true`). PREPATCH-1 reproduced.
- atk_2.lean (= Solution_prepatch_2.lean; deduceInfinite cascade reverted to none): EXIT 1 = FAILS (`none = some true`). PREPATCH-2 reproduced.
- atk_3.lean (deduceEven.infinite: none -> some false): EXIT 0 = VERIFIES. The one genuine same-spec non-gold variation.
- atk_4.lean (deduceEven.noninteger: some false -> none): EXIT 1 = FAILS (consistentTheory integer=T->noninteger=F; unsolved `False`).
- atk_5.lean (deduceInfinite.complex: some true -> none): EXIT 1 = FAILS (real=T->complex=T).
- atk_6.lean (deduceInfinite.prime: some false -> none): EXIT 1 = FAILS (integer=F->prime=F).
- atk_7.lean (deduceEven.odd: some false -> none): EXIT 1 = FAILS (even=T->odd=F).

EXHAUSTIVE SPACE PROOF (python, all 3^14 tables x post x consistentTheory): deduceEven -> exactly 2 verifying tables, sole free field `infinite` in {some false, none}; deduceInfinite -> exactly 1 verifying table (= gold, fully pinned: complex forced some true by real->complex, prime forced some false by integer=F->prime=F). Therefore atk_3 is the ONLY verifying wrong-shaped candidate; every other value flip breaks consistentTheory (matching atk_4..7).

RESOLVE (mandatory for every verifying candidate): atk_3's faithful refined patch. Because the trit<->is_<fact> mapping makes deduceEven.infinite=some false correspond to Symbol('e',even=True).is_infinite is False, which I confirmed the gold-patched engine actually deduces (: is_even=True, is_finite=True, is_infinite=False), atk_3's faithful patch is byte-identical to gold patch.diff. Ran: run_resolve('sympy__sympy-16597', <atk_3_faithful_patch.diff>, run_id='sbu-geq-atk3-16597') -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. Faithful patch saved at atk_3_faithful_patch.diff (diff -q == gold).

REFINEMENT.MD AUDIT: legs A1 (R), A2 (A-reference), A3/A4 (R+A-reference), no kind-3 (the one changed op — the rule theory — is modeled deeply as consistentTheory, not hidden behind an oracle). A-reference correspondence VERIFIED: conformance_check.py's theory_clauses set is byte-identical (30/30 clauses) to consistentTheory's clauses (set-equal, no missing/extra). Confirmed gold patch adds exactly the four *->finite edges (rational/algebraic/irrational/transcendental) plus auto-derived contrapositives, matching consistentTheory's finite=F-> cascade. G-CONF asserts each clause at the fact level on the real patched engine over singletons + all satisfiable single/pair seeds + enumerated witnessed deductions.

VERDICT: SOUND. >=5 attacks run; positive control verifies; both prepatches reproduced; the unique verifying non-gold impl (atk_3) has a materialized faithful patch that RESOLVES under the official Docker harness. verify => correct holds for the entire same-spec verifying space.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit for sympy__sympy-16597/velvet. The spec region is byte-identical with both prepatch variants (swebench_unified.markers.same_spec True, velvet backend). Solution.lean verifies (lean_verify.sh exit 0). The two modeled functions and the closure predicate all agree with the real patched property-deduction engine (worktree, gold assumptions.py delta 'rational->real&finite', 'algebraic->complex&finite', 'transcendental==complex&!algebraic&finite', 'irrational==real&!rational&finite'):
- deduceEven's evenTable matches Symbol('e',even=True) field-for-field (integer/rational/real/finite/even/algebraic/complex=True, odd/noninteger/transcendental/irrational=False, infinite=False, prime/composite=None). The spec's postconditions (finite=some true, transcendental/irrational=some false, prime/composite=none) are all real. prime/composite=none is genuinely undetermined in the engine (not forced), so the spec is not too strong there.
- deduceInfinite's infiniteTable matches S.Infinity AND S.NegativeInfinity field-for-field (finite/rational/integer/even/odd/algebraic/transcendental/irrational/composite=False, real/complex/noninteger/infinite=True).
- consistentTheory closure: independently checked every one of the 30 clauses against the real engine over 116,670 observations = all single/pair/TRIPLE assumption seeds over 18 fact names PLUS 22 numeric constants (oo,-oo,0,1,1/2,pi,E,I,-3/7,4,2,sqrt(2),2pi,pi*I,1+I,zoo,nan,GoldenRatio,EulerGamma,Catalan,Float(1.5),-1). 0 violations. The bundled conformance_check.py also passes (407 obs, 0 disagreements) against the patched library.
No input found where the modeled functions or consistentTheory disagree with the real callee. Spec is not too strong and does not drift. Prepatches correctly fail (they revert the finite conjunct), confirming the discriminating edge is genuinely required. G-CONF/G-PBT construction-debt policy is orthogonal to this faithfulness verdict.

- deduceEven's evenTable matches Symbol('e',even=True) field-for-field (integer/rational/real/finite/even/algebraic/complex=True, odd/noninteger/transcendental/irrational=False, infinite=False, prime/composite=None). The spec's postconditions (finite=some true, transcendental/irrational=some false, prime/composite=none) are all real. prime/composite=none is genuinely undetermined in the engine (not forced), so the spec is not too strong there.
- deduceInfinite's infiniteTable matches S.Infinity AND S.NegativeInfinity field-for-field (finite/rational/integer/even/odd/algebraic/transcendental/irrational/composite=False, real/complex/noninteger/infinite=True).
- consistentTheory closure: independently checked every one of the 30 clauses against the real engine over 116,670 observations = all single/pair/TRIPLE assumption seeds over 18 fact names PLUS 22 numeric constants (oo,-oo,0,1,1/2,pi,E,I,-3/7,4,2,sqrt(2),2pi,pi*I,1+I,zoo,nan,GoldenRatio,EulerGamma,Catalan,Float(1.5),-1). 0 violations. The bundled conformance_check.py also passes (407 obs, 0 disagreements) against the patched library.
No input found where the modeled functions or consistentTheory disagree with the real callee. Spec is not too strong and does not drift. Prepatches correctly fail (they revert the finite conjunct), confirming the discriminating edge is genuinely required. G-CONF/G-PBT construction-debt policy is orthogonal to this faithfulness verdict.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK recorded 'relaxed'). Per _audit.py/RELAXED_LEAKAGE.md panel convention, a properly-dispositioned accepted leak records NO-LEAKAGE at the panel layer; I independently re-verified rather than rubber-stamped.

Core soundness confirmed via meta.json gates: G-VERIFY pass, G-DIFF pass (both prepatches share spec exactly and fail on the consistentTheory closure clause), G-CONF pass, G-RESOLVE pass, G-GOLD pass, G-MUT pass. (Note: G-EQ/G-PANEL-1 fail is a separate defect outside panel_3 scope; panel_3 concerns leakage only.) same_spec verified True for BOTH Solution_prepatch.lean and Solution_prepatch_2.lean against Solution.lean via swebench_unified.markers.same_spec.

Mechanical G-LEAK screen over the spec view passes (0 hard failures, 0 warnings). Direct spec-view scan for patched symbols/paths/diff-markers (_assume_rules, FactRules, FactKB, deduce_all, Symbol, Infinity, assumptions.py, ask_generated, facts.py, power.py, indexed.py, get_known_facts, 'diff --git', '@@', '+++') found NONE — the spec view names only generic identifiers (KB, consistentTheory, deduceEven/deduceInfinite) and abstract set-containment vocabulary.

Unavoidability re-derived: problem_statement is EXCLUSIVELY the 'even → finite' symptom. Re-scanned tokens against the frozen dataset row: bounded=0, integer=0, rational=0, algebraic=0, irrational=0, transcendental=0 in problem_statement. The F2P tests (test_infinity/test_neg_infinity/test_other_symbol) pin the four small-set boundedness edges (rational/algebraic/irrational/transcendental → finite) and their oo/-oo contrapositive closure — discriminators absent from problem_statement. A faithful spec MUST pin them (else verify⇏correct, admitting impls that fail hidden tests), so the semantic leak is genuinely unavoidable; no problem_statement-only reformulation captures the indirect gold mechanism. (hints_text does mention _assume_rules and 'rational -> real & finite', but leakage is judged against the solver-visible problem_statement ONLY, never hints_text.)

Beyond-disposition check: the spec view discloses exactly the dispositioned facet (small-set boundedness containments + contrapositive closure) plus pre-existing, pre-patch engine edges (integer→rational, even/odd→integer, real→complex, infinite→¬finite, noninteger closure) which are NOT part of the gold edit and therefore leak nothing about the gold change. No spec-view line quotes a gold diff line, names a patched file, or names an engine symbol. Disposition intact; no NEW leaking line beyond the accepted facet. Verdict NO-LEAKAGE (pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
