# P2 adversarial audit — django__django-13794

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,7 +95,7 @@
   ensures out = Except.ok (other + forced)
   do
     -- impl-start
-    return Except.ok (other + forced)
+    return Except.ok (forced + other)
     -- impl-end
 
 prove_correct deferredSumRight by
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,7 +79,7 @@
   ensures out = Except.ok (forced + other)
   do
     -- impl-start
-    return Except.ok (forced + other)
+    return Except.ok (other + forced)
     -- impl-end
 
 prove_correct deferredSumLeft by
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -44,7 +44,7 @@
   ensures out = Except.ok (forced ++ other)
   do
     -- impl-start
-    return Except.ok (forced ++ other)
+    return Except.ok (forced ++ other ++ [])
     -- impl-end
 
 prove_correct deferredConcatLeft by
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -44,7 +44,7 @@
   ensures out = Except.ok (forced ++ other)
   do
     -- impl-start
-    return Except.ok (forced ++ other)
+    return Except.ok (if other.isEmpty then forced ++ [] ++ other else forced ++ other)
     -- impl-end
 
 prove_correct deferredConcatLeft by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -79,7 +79,7 @@
   ensures out = Except.ok (forced + other)
   do
     -- impl-start
-    return Except.ok (forced + other)
+    return (let s := forced + other; Except.ok s)
     -- impl-end
 
 prove_correct deferredSumLeft by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   ensures out = Except.ok (other ++ forced)
   do
     -- impl-start
-    return Except.ok (other ++ forced)
+    return Except.ok (forced ++ other)
     -- impl-end
 
 prove_correct deferredConcatRight by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
   ensures out = Except.ok (forced ++ other)
   do
     -- impl-start
-    return Except.ok (forced ++ other)
+    return Except.ok (other ++ forced)
     -- impl-end
 
 prove_correct deferredConcatLeft by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   ensures out = Except.ok (forced + other)
   do
     -- impl-start
-    return Except.ok (forced + other)
+    return Except.ok (forced + other + 1)
     -- impl-end
 
 prove_correct deferredSumLeft by
```

Attack 9 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   ensures out = Except.ok (other ++ forced)
   do
     -- impl-start
-    return Except.ok (other ++ forced)
+    return Except.error AddOutcome.unsupported
     -- impl-end
 
 prove_correct deferredConcatRight by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Each modeled function is a changed function whose new
--  behaviour is a single binary combination of its already-forced operands,
--  modeled deeply and directly. The only callee involved is the unchanged
--  forcing step that yields the underlying value; it is represented by the input
--  already holding that value — an R-refinement (mapping.md §2), not an axiom.)
-- axioms-end

-- pure-start
/- The two possible results of combining a deferred value with another value
   under binary addition: either the combination succeeds and yields a value, or
   the combination is rejected. A correct deferred value never rejects a
   combination its underlying value would accept, so the success constructor is
   the only outcome the contracts below permit. -/
inductive AddOutcome where
  | unsupported
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A deferred character-sequence value standing on the LEFT of a binary addition.
   Once its underlying sequence is in hand (`forced`), combining it with the
   other operand must produce the underlying sequence followed by the other
   operand — the very same sequence that combining two ordinary character
   sequences in this order would produce — and must NOT be rejected. Operand
   order is significant for character sequences, so `forced` precedes `other`.
   Both operands are read-only (not `mut`); nothing is mutated (directive 5).
   The result is reported as a success carrying the combined sequence. -/
method deferredConcatLeft (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (forced ++ other)
  do
    -- impl-start
    return Except.ok (forced ++ other)
    -- impl-end

prove_correct deferredConcatLeft by
  loom_solve

/- A deferred character-sequence value standing on the RIGHT of a binary
   addition. Once its underlying sequence is in hand (`forced`), combining it
   with the other (left) operand must produce the other operand followed by the
   underlying sequence — preserving the left-to-right operand order — and must
   NOT be rejected, even when the left operand cannot by itself combine with a
   deferred value. This right-operand case is what lets an ordinary value on the
   left be joined to a deferred value on the right. Both operands are read-only
   (not `mut`); nothing is mutated (directive 5). -/
method deferredConcatRight (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (other ++ forced)
  do
    -- impl-start
    return Except.ok (other ++ forced)
    -- impl-end

prove_correct deferredConcatRight by
  loom_solve

/- A deferred numeric value standing on the LEFT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other operand
   must produce their numeric sum and must NOT be rejected. Both operands are
   read-only (not `mut`); nothing is mutated (directive 5). The result is a
   success carrying the sum. -/
method deferredSumLeft (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (forced + other)
  do
    -- impl-start
    return Except.ok (forced + other)
    -- impl-end

prove_correct deferredSumLeft by
  loom_solve

/- A deferred numeric value standing on the RIGHT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other (left)
   operand must produce their numeric sum and must NOT be rejected, even when the
   left operand is itself a deferred value. Both operands are read-only (not
   `mut`); nothing is mutated (directive 5). -/
method deferredSumRight (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (other + forced)
  do
    -- impl-start
    return Except.ok (other + forced)
    -- impl-end

prove_correct deferredSumRight by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13794 (velvet). SPEC SHAPE: four total exact-value equality postconditions (out = Except.ok <value>), ZERO A-legs (all refinement.md legs A1-A5 are R or R+I; no A-consumed, no A-reference, no kind-3). MODEL<->PATCH CORRESPONDENCE is 4-method<->2-handler: deferredConcatLeft(str)+deferredSumLeft(int) both refine to the SINGLE gold handler __add__; deferredConcatRight(str)+deferredSumRight(int) both refine to the SINGLE gold handler __radd__. Refinement.md audit PASSES.

SAME-SPEC: all 9 attacks + positive_control return same_spec=True (verified via swebench_unified.markers.same_spec, velvet backend).

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap, run <=4 concurrently):
  positive_control -> exit 0 (VERIFIES) [correct impl, byte-identical to Solution.lean]
  atk_1 (SumRight operand swap forced+other) -> exit 0 VERIFIES  [Int + commutes]
  atk_2 (SumLeft operand swap other+forced)  -> exit 0 VERIFIES  [Int + commutes]
  atk_3 (ConcatLeft forced++other++[])        -> exit 0 VERIFIES  [ungrounded-oracle-echo, value==gold]
  atk_4 (ConcatLeft if other.isEmpty guard, both branches==gold) -> exit 0 VERIFIES [partial-domain/boundary]
  atk_5 (SumLeft let-binding detour)          -> exit 0 VERIFIES  [control-flow-effect, value==gold]
  atk_6 (ConcatRight order swap forced++other) -> exit 1 FAILS  [ensures out = Except.ok (other++forced) unsolved]
  atk_7 (ConcatLeft order swap other++forced)  -> exit 1 FAILS  [ensures out = Except.ok (forced++other) unsolved]
  atk_8 (SumLeft off-by-one forced+other+1)    -> exit 1 FAILS  [ensures unsolved]
  atk_prepatch (ConcatRight returns Except.error) -> exit 1 FAILS [Except.error <> Except.ok (other++forced); reproduces F2P add08 prepatch bug]

### FAITHFUL-PATCH RESOLVE (official harness, swebench_unified.harness.run_resolve, docker oracle):
  The 5 verifying attacks (atk_1..atk_5) are each behaviorally IDENTICAL to gold on ALL inputs. Because each attack's method shares its real Python handler with the OTHER result class, a faithful refinement must satisfy BOTH legs of the shared handler. For atk_1/atk_2 the int-swap only verifies via Int commutativity, but the SAME handler's str leg (non-commutative, pinned by deferredConcatRight/Left; confirmed by atk_6/atk_7 FAILING verify) forces gold operand order. atk_3/4/5 are value-preserving rewrites. Therefore the faithful refined patch of every verifying attack == the gold patch.
    faithful_gold.diff (= refinement of atk_1..atk_5) -> run_resolve => RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'.
  CONTROL (load-bearing check): naive_swap_radd.diff, an UNFAITHFUL translation of atk_1 that literally writes __radd__ = self.__cast() + other (ignoring the str leg; this is NOT the faithful refinement and its Lean analogue atk_6 does NOT verify) -> run_resolve => RESOLVED=False, COMPLETED=True, attempts=2, note='patch did not resolve in 2 attempts (consistent - not flaky)'. This confirms the string operand-order legs are load-bearing and that the spec's tightness (rejecting atk_6/atk_7) is exactly what forces faithful refinements to the correct gold behaviour.

CONCLUSION: No same-spec verifying impl has a faithful refined patch that fails to resolve. verify => correct holds. Verdict SOUND. Commands used: python -c 'from swebench_unified.markers import same_spec...'; bash scripts/lean_verify.sh <atk>.lean; python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-13794", patch, timeout=1800, retries=1)'.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Each modeled function is a changed function whose new
--  behaviour is a single binary combination of its already-forced operands,
--  modeled deeply and directly. The only callee involved is the unchanged
--  forcing step that yields the underlying value; it is represented by the input
--  already holding that value — an R-refinement (mapping.md §2), not an axiom.)
-- axioms-end

-- pure-start
/- The two possible results of combining a deferred value with another value
   under binary addition: either the combination succeeds and yields a value, or
   the combination is rejected. A correct deferred value never rejects a
   combination its underlying value would accept, so the success constructor is
   the only outcome the contracts below permit. -/
inductive AddOutcome where
  | unsupported
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A deferred character-sequence value standing on the LEFT of a binary addition.
   Once its underlying sequence is in hand (`forced`), combining it with the
   other operand must produce the underlying sequence followed by the other
   operand — the very same sequence that combining two ordinary character
   sequences in this order would produce — and must NOT be rejected. Operand
   order is significant for character sequences, so `forced` precedes `other`.
   Both operands are read-only (not `mut`); nothing is mutated (directive 5).
   The result is reported as a success carrying the combined sequence. -/
method deferredConcatLeft (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (forced ++ other)
  do
    -- impl-start
    return Except.ok (forced ++ other)
    -- impl-end

prove_correct deferredConcatLeft by
  loom_solve

/- A deferred character-sequence value standing on the RIGHT of a binary
   addition. Once its underlying sequence is in hand (`forced`), combining it
   with the other (left) operand must produce the other operand followed by the
   underlying sequence — preserving the left-to-right operand order — and must
   NOT be rejected, even when the left operand cannot by itself combine with a
   deferred value. This right-operand case is what lets an ordinary value on the
   left be joined to a deferred value on the right. Both operands are read-only
   (not `mut`); nothing is mutated (directive 5). -/
method deferredConcatRight (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (other ++ forced)
  do
    -- impl-start
    return Except.ok (other ++ forced)
    -- impl-end

prove_correct deferredConcatRight by
  loom_solve

/- A deferred numeric value standing on the LEFT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other operand
   must produce their numeric sum and must NOT be rejected. Both operands are
   read-only (not `mut`); nothing is mutated (directive 5). The result is a
   success carrying the sum. -/
method deferredSumLeft (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (forced + other)
  do
    -- impl-start
    return Except.ok (forced + other)
    -- impl-end

prove_correct deferredSumLeft by
  loom_solve

/- A deferred numeric value standing on the RIGHT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other (left)
   operand must produce their numeric sum and must NOT be rejected, even when the
   left operand is itself a deferred value. Both operands are read-only (not
   `mut`); nothing is mutated (directive 5). -/
method deferredSumRight (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (other + forced)
  do
    -- impl-start
    return Except.ok (other + forced)
    -- impl-end

prove_correct deferredSumRight by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13794 (velvet). SPEC SHAPE: four total exact-value equality postconditions (out = Except.ok <value>), ZERO A-legs (all refinement.md legs A1-A5 are R or R+I; no A-consumed, no A-reference, no kind-3). MODEL<->PATCH CORRESPONDENCE is 4-method<->2-handler: deferredConcatLeft(str)+deferredSumLeft(int) both refine to the SINGLE gold handler __add__; deferredConcatRight(str)+deferredSumRight(int) both refine to the SINGLE gold handler __radd__. Refinement.md audit PASSES.

SAME-SPEC: all 9 attacks + positive_control return same_spec=True (verified via swebench_unified.markers.same_spec, velvet backend).

### VERIFY RESULTS (scripts/lean_verify.sh, 300s cap, run <=4 concurrently):
  positive_control -> exit 0 (VERIFIES) [correct impl, byte-identical to Solution.lean]
  atk_1 (SumRight operand swap forced+other) -> exit 0 VERIFIES  [Int + commutes]
  atk_2 (SumLeft operand swap other+forced)  -> exit 0 VERIFIES  [Int + commutes]
  atk_3 (ConcatLeft forced++other++[])        -> exit 0 VERIFIES  [ungrounded-oracle-echo, value==gold]
  atk_4 (ConcatLeft if other.isEmpty guard, both branches==gold) -> exit 0 VERIFIES [partial-domain/boundary]
  atk_5 (SumLeft let-binding detour)          -> exit 0 VERIFIES  [control-flow-effect, value==gold]
  atk_6 (ConcatRight order swap forced++other) -> exit 1 FAILS  [ensures out = Except.ok (other++forced) unsolved]
  atk_7 (ConcatLeft order swap other++forced)  -> exit 1 FAILS  [ensures out = Except.ok (forced++other) unsolved]
  atk_8 (SumLeft off-by-one forced+other+1)    -> exit 1 FAILS  [ensures unsolved]
  atk_prepatch (ConcatRight returns Except.error) -> exit 1 FAILS [Except.error <> Except.ok (other++forced); reproduces F2P add08 prepatch bug]

### FAITHFUL-PATCH RESOLVE (official harness, swebench_unified.harness.run_resolve, docker oracle):
  The 5 verifying attacks (atk_1..atk_5) are each behaviorally IDENTICAL to gold on ALL inputs. Because each attack's method shares its real Python handler with the OTHER result class, a faithful refinement must satisfy BOTH legs of the shared handler. For atk_1/atk_2 the int-swap only verifies via Int commutativity, but the SAME handler's str leg (non-commutative, pinned by deferredConcatRight/Left; confirmed by atk_6/atk_7 FAILING verify) forces gold operand order. atk_3/4/5 are value-preserving rewrites. Therefore the faithful refined patch of every verifying attack == the gold patch.
    faithful_gold.diff (= refinement of atk_1..atk_5) -> run_resolve => RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'.
  CONTROL (load-bearing check): naive_swap_radd.diff, an UNFAITHFUL translation of atk_1 that literally writes __radd__ = self.__cast() + other (ignoring the str leg; this is NOT the faithful refinement and its Lean analogue atk_6 does NOT verify) -> run_resolve => RESOLVED=False, COMPLETED=True, attempts=2, note='patch did not resolve in 2 attempts (consistent - not flaky)'. This confirms the string operand-order legs are load-bearing and that the spec's tightness (rejecting atk_6/atk_7) is exactly what forces faithful refinements to the correct gold behaviour.

CONCLUSION: No same-spec verifying impl has a faithful refined patch that fails to resolve. verify => correct holds. Verdict SOUND. Commands used: python -c 'from swebench_unified.markers import same_spec...'; bash scripts/lean_verify.sh <atk>.lean; python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-13794", patch, timeout=1800, retries=1)'.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-13794 velvet bundle.

SPEC REGION BYTE-IDENTITY: same_spec(Solution.lean, prepatch_{,,2,3}, velvet_backend) = True for all three discriminators. Spec is frozen; only impl regions differ.

MODEL VERIFIES: Solution.lean elaborates cleanly (lean_verify.sh exit 0) under loom.semantics.termination=total, choice=demonic.

SPEC: four methods model the gold patch (django/utils/functional.py __proxy__ gains __add__ returning self.__cast()+other and __radd__ returning other+self.__cast()):
  deferredConcatLeft (List Char): out = Except.ok (forced ++ other)  <-> __add__ @ str
  deferredConcatRight(List Char): out = Except.ok (other ++ forced)  <-> __radd__ @ str
  deferredSumLeft (Int): out = Except.ok (forced + other)            <-> __add__ @ int
  deferredSumRight(Int): out = Except.ok (other + forced)            <-> __radd__ @ int
Forcing step self.__cast() modeled as identity onto `forced` (R-refinement); str<->List Char per-codepoint concat, int<->Int exact.

### FAITHFULNESS EVIDENCE (real repo at base_commit fe886eee w/ gold patch applied in fresh worktree):
  1. Bundle conformance_check.py against the REAL patched lazy proxy: 200,362 comparisons, 0 disagreements.
  2. Independent aggressive fuzz (~400k cases): str operands with high codepoints/surrogate-range (chr 0x10FFFF, 0x1F600, NUL, newline, U+2028) in both operand positions, and ints of magnitude up to 10^30 in both positions. 0 disagreements; real handlers always return normally (never raise) and yield exactly forced++other / other++forced / the numeric sum.
  3. Direct F2P scenario checks: add08 ('string'+lazy('lazy')='stringlazy'), add09 (lazy+lazy='stringlazy'), test_lazy_add (lazy(4)+lazy(5)=9) all match.

The always-Except.ok postcondition is NOT too strong: within the modeled type domain (str+str, int+int) the patched proxy never raises. Heterogeneous mixes (e.g. lazy_str + int) DO raise TypeError in the real repo, but such inputs are not representable in the Lean methods' fixed monomorphic signatures (List Char x List Char / Int x Int), so they cannot serve as diverging inputs against the modeled function. The AddOutcome error constructor is thus unreachable on the modeled domain, consistent with reality. No spec drift; operand order preserved correctly in both positions. No diverging input exists on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean with impl regions elided (mapping.md/refinement.md are audit-side docs, explicitly 'not in the consumer spec view'). same_spec byte-identical across Solution_prepatch{,_2,_3}.lean (all True). Mechanical leakage.screen passes (hard_failures=[]); no RELAXED_LEAKAGE.md / relaxed_leakage flag (relaxation deferral N/A). Semantic check: spec view contains NO patched file path (functional.py), NO patched repo symbols (__proxy__/__add__/__radd__/__cast), NO 'add' filter / lazy() reference, NO diff markers, and no bug/fix narration. The four abstract methods (deferredConcat/Sum × Left/Right) encode the REQUIRED behavior — combining a deferred value with another under binary addition yields concat/sum and must not raise — which is exactly the goal already stated in the public problem_statement ('add filter is unable to concatenate strings with lazy string ... TypeError ... __proxy__'). Decomposing into left/right operand positions and str/int result classes is the natural behavioral encoding of 'addition with a deferred value,' not gold-edit localization: a solver still must discover the actual fix is defining __add__/__radd__ on the lazy proxy. Nothing in the spec view reveals the gold edit beyond the public problem_statement. Note: G-PANEL overall fails on G-PANEL-1 (spec-too-weak echo attack), which is a separate gate and out of scope for the leakage judgment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
