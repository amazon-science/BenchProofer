# P2 adversarial audit — django__django-16901

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.py`, `atk_3.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,24 +119,16 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
-    if len(operands) > 2:
-        rhs = total % 2
-    else:
-        rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
+    rhs = total
     return any_t and rhs == 1
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,24 +119,19 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
-    if len(operands) > 2:
+    if len(operands) >= 2:
         rhs = total % 2
     else:
         rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
     return any_t and rhs == 1
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,24 +119,16 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
-    if len(operands) > 2:
-        rhs = total % 2
-    else:
-        rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
+    rhs = total % 2
     return any_t and rhs == 1
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,24 +119,19 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
-        contribution = 1 if c == 1 else 0
+        contribution = 1 if c != 0 else 0
         total = contribution + total
-        any_t = (c == 1) or any_t
+        any_t = (c != 0) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
     if len(operands) > 2:
         rhs = total % 2
     else:
         rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
     return any_t and rhs == 1
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,33 +110,5 @@
     Ensures(Result() == (count_true(ToSeq(operands)) % 2 == 1))
     # post-conditions-end
     # impl-start
-    total = 0
-    any_t = False
-    i = len(operands)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(operands), 1 / 2))
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(total == count_true(ToSeq(operands).drop(i)))
-        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        c = operands[i - 1]
-        Assert(ToSeq(operands).drop(i - 1)[0] == c)
-        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
-        contribution = 1 if c == 1 else 0
-        total = contribution + total
-        any_t = (c == 1) or any_t
-        i = i - 1
-    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
-    if len(operands) > 2:
-        rhs = total % 2
-    else:
-        rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
-    return any_t and rhs == 1
+    return count_true(ToSeq(operands)) % 2 == 1
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,30 +113,20 @@
     total = 0
     any_t = False
     i = len(operands)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(operands), 1 / 2))
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(total == count_true(ToSeq(operands).drop(i)))
-        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
+        Invariant(1 <= i and i <= len(operands))
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
-        Assert(ToSeq(operands).drop(i - 1)[0] == c)
-        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
-    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
     if len(operands) > 2:
         rhs = total % 2
     else:
         rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
     return any_t and rhs == 1
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,24 +119,19 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
-    if len(operands) > 2:
+    if len(operands) > 3:
         rhs = total % 2
     else:
         rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
     return any_t and rhs == 1
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,24 +119,19 @@
         Invariant(0 <= i and i <= len(operands))
         Invariant(total == count_true(ToSeq(operands).drop(i)))
         Invariant(any_t == any_true(ToSeq(operands).drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
         c = operands[i - 1]
         Assert(ToSeq(operands).drop(i - 1)[0] == c)
         Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
-        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
         contribution = 1 if c == 1 else 0
         total = contribution + total
         any_t = (c == 1) or any_t
         i = i - 1
     Assert(ToSeq(operands).drop(0) == ToSeq(operands))
-    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
     if len(operands) > 2:
         rhs = total % 2
     else:
         rhs = total
-    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
-    return any_t and rhs == 1
+    return any_t and rhs == 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16901.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An exclusive-disjunction connective is combined over a list of operand
  predicates on a backend that cannot evaluate the connective natively, so it
  is re-expressed using only conjunction, disjunction and integer arithmetic
  over the per-operand truth values (each operand contributes 1 when true and
  0 when false).

  The combined predicate must hold for an assignment exactly when an ODD number
  of the operands are true — the genuine semantics of a repeated exclusive
  disjunction. The arithmetic re-expression therefore tests the PARITY of the
  number of true operands, not whether that number equals one. For one or two
  operands the count of true operands can be at most two, so "the count is one"
  and "the count is odd" coincide; for three or more operands they diverge and
  only the parity test is correct (e.g. three true operands must satisfy the
  predicate).

  Concretely the re-expression is the conjunction of
    (i) the disjunction of the operands ("at least one true"), and
    (ii) a comparison of a derived count against one, where the derived count
         is the number of true operands when there are at most two operands,
         and the parity (remainder modulo two) of that number when there are
         three or more operands.

Operand truth assignments are modelled as a `List[int]`; an operand counts as
true exactly when its entry is 1 (each entry contributes 1 when true and 0
otherwise). The SQL builder objects (the per-operand 1/0 choice, the running
sum, the modulo, the equality and the disjunction) are modelled by the integer
arithmetic they denote at evaluation time. No callee is axiomatized — the
changed operation is the integer arithmetic itself and is modelled deeply.

Evaluating the re-expression is a bounded, straight-line computation over a
finite operand list: the operation MUST terminate and actually deliver its
truth value (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges instead of answering would
satisfy the value postconditions only vacuously and would never produce the
match decision the caller observes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (none — the changed operation is integer arithmetic, modelled deeply below)
# axioms-end

# pure-start
@Pure
def count_true(s: PSeq[int]) -> int:
    """Number of true operands: the sum of the per-operand 1/0 contributions
    (an operand contributes 1 exactly when its entry is 1). Front-recursive so
    a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if s[0] == 1 else 0) + count_true(s.drop(1))

@Pure
def any_true(s: PSeq[int]) -> bool:
    """Disjunction of the operands: at least one operand is true."""
    Ensures(Result() == (count_true(s) >= 1))
    if len(s) == 0:
        return False
    return s[0] == 1 or any_true(s.drop(1))

@Pure
def derived_count(s: PSeq[int]) -> int:
    """The count compared against one by the re-expression: the raw number of
    true operands when there are at most two operands, its parity (remainder
    modulo two) when there are three or more."""
    if len(s) > 2:
        return count_true(s) % 2
    return count_true(s)

@Pure
def xor_holds(s: PSeq[int]) -> bool:
    """The truth value of the arithmetic re-expression on this assignment:
    the disjunction of the operands AND the derived count equals one."""
    return any_true(s) and derived_count(s) == 1
# pure-end

def xor_fallback_matches(operands: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(operands), 1 / 2))
    # Evaluating the constructed predicate on one row's finite operand
    # assignment is a bounded computation and MUST terminate — the fallback
    # must actually answer whether the row matches. Without this obligation a
    # diverging implementation satisfies every Ensures vacuously (Nagini is a
    # partial-correctness verifier by default).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # The result is the re-expression's truth value: at least one operand true
    # AND the derived count (parity when >2 operands) equals one.
    Ensures(Result() == xor_holds(ToSeq(operands)))
    # Behavioural pinning derived from the issue: the predicate holds exactly
    # when an ODD number of operands are true.
    Ensures(Result() == (count_true(ToSeq(operands)) % 2 == 1))
    # post-conditions-end
    # impl-start
    total = 0
    any_t = False
    i = len(operands)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(0 <= i and i <= len(operands))
        Invariant(total == count_true(ToSeq(operands).drop(i)))
        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = operands[i - 1]
        Assert(ToSeq(operands).drop(i - 1)[0] == c)
        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
        contribution = 1 if c == 1 else 0
        total = contribution + total
        any_t = (c == 1) or any_t
        i = i - 1
    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
    if len(operands) > 2:
        rhs = total % 2
    else:
        rhs = total
    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
    return any_t and rhs == 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify⇒correct holds; no verifying same-spec wrong impl whose faithful patch fails to resolve was found.

SPEC SHAPE: Result() is pinned EXACTLY by two mutually-reinforcing postconditions — Result()==xor_holds(ToSeq(operands)) [= (OR of operands) AND (derived_count==1), parity reduction for len>2] and Result()==(count_true%2==1) [odd-parity] — plus Requires(MustTerminate(2)). Tight value+total-correctness spec.

NO AXIOMS: model.py has an empty axioms region and no @ContractOnly. refinement.md is entirely R/I steps (A1-A5), no kind-3, no A-consumed and no A-reference legs — so there is NO callee-correspondence to audit (moot). The one external soundness link is axiom_check.py, which INDEPENDENTLY reconstructs the gold-patch SQL predicate (OR..) AND (MOD(sum,2)==1 | sum==1) and confirms model xor_holds == gold predicate == odd-parity over 208191 assignments (exhaustive 0..12 operands + 200000 fuzz incl. non-0/1 entries); exit 0. Verified here.

### Commands
  same-spec (all 8 attacks + pos_control): PY -m swebench_unified.adversary same-spec nagini django__django-16901 <f> -> ALL 'SAME'.
  weakness:  PY -m swebench_unified.adversary weakness nagini django__django-16901 <f>.

atk_1 (PREPATCH bug: rhs=total unconditionally, exactly-one) -> weakness EXIT 2, NOT-A-COUNTEREXAMPLE 'does not verify' (spec REJECTS it; G-DIFF senses the change). prepatch_reproduced=TRUE.
atk_4 (ungrounded truth: contribution/any via c!=0 not c==1) -> EXIT 2, verification failed (invariant total==count_true broken).
atk_6 (control-flow-effect: while i>1 skips index 0) -> EXIT 2, verification failed.
atk_7 (boundary: threshold len>3, breaks len==3 all-true) -> EXIT 2, verification failed (postcondition).
atk_8 (wrong compare: rhs==0 instead of ==1) -> EXIT 2, verification failed.
atk_2 (boundary equiv: threshold len>=2) -> weakness EXIT 0 CANDIDATE (verifies).
atk_3 (always-mod, no length guard) -> weakness EXIT 0 CANDIDATE (verifies).
atk_5 (ungrounded-oracle echo: return count_true%2==1, drops any_true/OR conjunct) -> weakness EXIT 0 CANDIDATE (verifies).
pos_control = bundle model.py impl verbatim -> bash scripts/nagini_verify.sh EXIT 0 (verifies, 19.0s). [My alternate forward-loop pos control failed on a take()-vs-drop() proof-engineering limit, not a spec issue; used canonical model.py impl as the positive control.]

MATERIALIZED FAITHFUL PATCHES for EVERY CANDIDATE, run through the OFFICIAL harness (run_resolve / run_evaluation, --namespace swebench, princeton-nlp/SWE-bench_Verified): RESOLVE POSITIVE CONTROL — gold patch.diff: resolved=True (F2P test_filter_multiple PASS, all 6 P2P PASS). atk_2 faithful patch (if len(self.children) >= 2: rhs_sum = Mod(rhs_sum, 2)): RESOLVED=True, applied=True, F2P PASS, P2P failures=[]. atk_3 faithful patch (unconditional rhs_sum = Mod(rhs_sum, 2)): RESOLVED=True, applied=True, F2P PASS, P2P failures=[]. atk_5 faithful patch (drop lhs OR node; return AND([Exact(1, Mod(sum,2))])): RESOLVED=True, applied=True, F2P PASS, P2P failures=[] — CONFIRMED TWICE (manual run_evaluation + official run_resolve API resolved=True completed=True note=resolved).

This is the sharpest attack: MOD(sum,2)==1 already implies sum>=1 => at least one child true, and the test's Number.num is a non-null integer field, so dropping the redundant OR node yields identical rowsets. Real SQL three-valued-logic/NULL could in principle distinguish OR-dropped from gold, but the F2P/P2P domain has no nulls, so it resolves. All three apply cleanly (git apply --check) against the real where.py extracted from the base image; py-syntax validated.

Note on transient infra: the first parallel run_resolve calls returned completed=False 'no report ... harness error or image pull failure' — a concurrency race with a heavy co-tenant concurrent runs during image build, NOT a non-resolve. Re-run serially/with full time, every candidate produced a real report with resolved=True (atk_5 re-confirmed via the official run_resolve API with retries=2).

CONCLUSION: The spec's exact Result()-pinning (odd-parity) + MustTerminate rejects every behaviourally-wrong impl I could build (5 distinct classes: prepatch/exactly-one, ungrounded truth, control-flow-effect, boundary-threshold, wrong-compare) and admits only impls behaviourally equal to gold on the tested domain, whose faithful patches all resolve. No verify⇒correct violation. Refinement.md fidelity holds (R/I only, no axiom trust point; axiom_check soundness link verified independently). Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.py`, `atk_3.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16901.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An exclusive-disjunction connective is combined over a list of operand
  predicates on a backend that cannot evaluate the connective natively, so it
  is re-expressed using only conjunction, disjunction and integer arithmetic
  over the per-operand truth values (each operand contributes 1 when true and
  0 when false).

  The combined predicate must hold for an assignment exactly when an ODD number
  of the operands are true — the genuine semantics of a repeated exclusive
  disjunction. The arithmetic re-expression therefore tests the PARITY of the
  number of true operands, not whether that number equals one. For one or two
  operands the count of true operands can be at most two, so "the count is one"
  and "the count is odd" coincide; for three or more operands they diverge and
  only the parity test is correct (e.g. three true operands must satisfy the
  predicate).

  Concretely the re-expression is the conjunction of
    (i) the disjunction of the operands ("at least one true"), and
    (ii) a comparison of a derived count against one, where the derived count
         is the number of true operands when there are at most two operands,
         and the parity (remainder modulo two) of that number when there are
         three or more operands.

Operand truth assignments are modelled as a `List[int]`; an operand counts as
true exactly when its entry is 1 (each entry contributes 1 when true and 0
otherwise). The SQL builder objects (the per-operand 1/0 choice, the running
sum, the modulo, the equality and the disjunction) are modelled by the integer
arithmetic they denote at evaluation time. No callee is axiomatized — the
changed operation is the integer arithmetic itself and is modelled deeply.

Evaluating the re-expression is a bounded, straight-line computation over a
finite operand list: the operation MUST terminate and actually deliver its
truth value (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges instead of answering would
satisfy the value postconditions only vacuously and would never produce the
match decision the caller observes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (none — the changed operation is integer arithmetic, modelled deeply below)
# axioms-end

# pure-start
@Pure
def count_true(s: PSeq[int]) -> int:
    """Number of true operands: the sum of the per-operand 1/0 contributions
    (an operand contributes 1 exactly when its entry is 1). Front-recursive so
    a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if s[0] == 1 else 0) + count_true(s.drop(1))

@Pure
def any_true(s: PSeq[int]) -> bool:
    """Disjunction of the operands: at least one operand is true."""
    Ensures(Result() == (count_true(s) >= 1))
    if len(s) == 0:
        return False
    return s[0] == 1 or any_true(s.drop(1))

@Pure
def derived_count(s: PSeq[int]) -> int:
    """The count compared against one by the re-expression: the raw number of
    true operands when there are at most two operands, its parity (remainder
    modulo two) when there are three or more."""
    if len(s) > 2:
        return count_true(s) % 2
    return count_true(s)

@Pure
def xor_holds(s: PSeq[int]) -> bool:
    """The truth value of the arithmetic re-expression on this assignment:
    the disjunction of the operands AND the derived count equals one."""
    return any_true(s) and derived_count(s) == 1
# pure-end

def xor_fallback_matches(operands: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(operands), 1 / 2))
    # Evaluating the constructed predicate on one row's finite operand
    # assignment is a bounded computation and MUST terminate — the fallback
    # must actually answer whether the row matches. Without this obligation a
    # diverging implementation satisfies every Ensures vacuously (Nagini is a
    # partial-correctness verifier by default).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operands), 1 / 2))
    # The result is the re-expression's truth value: at least one operand true
    # AND the derived count (parity when >2 operands) equals one.
    Ensures(Result() == xor_holds(ToSeq(operands)))
    # Behavioural pinning derived from the issue: the predicate holds exactly
    # when an ODD number of operands are true.
    Ensures(Result() == (count_true(ToSeq(operands)) % 2 == 1))
    # post-conditions-end
    # impl-start
    total = 0
    any_t = False
    i = len(operands)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(0 <= i and i <= len(operands))
        Invariant(total == count_true(ToSeq(operands).drop(i)))
        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = operands[i - 1]
        Assert(ToSeq(operands).drop(i - 1)[0] == c)
        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
        contribution = 1 if c == 1 else 0
        total = contribution + total
        any_t = (c == 1) or any_t
        i = i - 1
    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
    if len(operands) > 2:
        rhs = total % 2
    else:
        rhs = total
    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
    return any_t and rhs == 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify⇒correct holds; no verifying same-spec wrong impl whose faithful patch fails to resolve was found.

SPEC SHAPE: Result() is pinned EXACTLY by two mutually-reinforcing postconditions — Result()==xor_holds(ToSeq(operands)) [= (OR of operands) AND (derived_count==1), parity reduction for len>2] and Result()==(count_true%2==1) [odd-parity] — plus Requires(MustTerminate(2)). Tight value+total-correctness spec.

NO AXIOMS: model.py has an empty axioms region and no @ContractOnly. refinement.md is entirely R/I steps (A1-A5), no kind-3, no A-consumed and no A-reference legs — so there is NO callee-correspondence to audit (moot). The one external soundness link is axiom_check.py, which INDEPENDENTLY reconstructs the gold-patch SQL predicate (OR..) AND (MOD(sum,2)==1 | sum==1) and confirms model xor_holds == gold predicate == odd-parity over 208191 assignments (exhaustive 0..12 operands + 200000 fuzz incl. non-0/1 entries); exit 0. Verified here.

### Commands
  same-spec (all 8 attacks + pos_control): PY -m swebench_unified.adversary same-spec nagini django__django-16901 <f> -> ALL 'SAME'.
  weakness:  PY -m swebench_unified.adversary weakness nagini django__django-16901 <f>.

atk_1 (PREPATCH bug: rhs=total unconditionally, exactly-one) -> weakness EXIT 2, NOT-A-COUNTEREXAMPLE 'does not verify' (spec REJECTS it; G-DIFF senses the change). prepatch_reproduced=TRUE.
atk_4 (ungrounded truth: contribution/any via c!=0 not c==1) -> EXIT 2, verification failed (invariant total==count_true broken).
atk_6 (control-flow-effect: while i>1 skips index 0) -> EXIT 2, verification failed.
atk_7 (boundary: threshold len>3, breaks len==3 all-true) -> EXIT 2, verification failed (postcondition).
atk_8 (wrong compare: rhs==0 instead of ==1) -> EXIT 2, verification failed.
atk_2 (boundary equiv: threshold len>=2) -> weakness EXIT 0 CANDIDATE (verifies).
atk_3 (always-mod, no length guard) -> weakness EXIT 0 CANDIDATE (verifies).
atk_5 (ungrounded-oracle echo: return count_true%2==1, drops any_true/OR conjunct) -> weakness EXIT 0 CANDIDATE (verifies).
pos_control = bundle model.py impl verbatim -> bash scripts/nagini_verify.sh EXIT 0 (verifies, 19.0s). [My alternate forward-loop pos control failed on a take()-vs-drop() proof-engineering limit, not a spec issue; used canonical model.py impl as the positive control.]

MATERIALIZED FAITHFUL PATCHES for EVERY CANDIDATE, run through the OFFICIAL harness (run_resolve / run_evaluation, --namespace swebench, princeton-nlp/SWE-bench_Verified): RESOLVE POSITIVE CONTROL — gold patch.diff: resolved=True (F2P test_filter_multiple PASS, all 6 P2P PASS). atk_2 faithful patch (if len(self.children) >= 2: rhs_sum = Mod(rhs_sum, 2)): RESOLVED=True, applied=True, F2P PASS, P2P failures=[]. atk_3 faithful patch (unconditional rhs_sum = Mod(rhs_sum, 2)): RESOLVED=True, applied=True, F2P PASS, P2P failures=[]. atk_5 faithful patch (drop lhs OR node; return AND([Exact(1, Mod(sum,2))])): RESOLVED=True, applied=True, F2P PASS, P2P failures=[] — CONFIRMED TWICE (manual run_evaluation + official run_resolve API resolved=True completed=True note=resolved).

This is the sharpest attack: MOD(sum,2)==1 already implies sum>=1 => at least one child true, and the test's Number.num is a non-null integer field, so dropping the redundant OR node yields identical rowsets. Real SQL three-valued-logic/NULL could in principle distinguish OR-dropped from gold, but the F2P/P2P domain has no nulls, so it resolves. All three apply cleanly (git apply --check) against the real where.py extracted from the base image; py-syntax validated.

Note on transient infra: the first parallel run_resolve calls returned completed=False 'no report ... harness error or image pull failure' — a concurrency race with a heavy co-tenant concurrent runs during image build, NOT a non-resolve. Re-run serially/with full time, every candidate produced a real report with resolved=True (atk_5 re-confirmed via the official run_resolve API with retries=2).

CONCLUSION: The spec's exact Result()-pinning (odd-parity) + MustTerminate rejects every behaviourally-wrong impl I could build (5 distinct classes: prepatch/exactly-one, ungrounded truth, control-flow-effect, boundary-threshold, wrong-compare) and admits only impls behaviourally equal to gold on the tested domain, whose faithful patches all resolve. No verify⇒correct violation. Refinement.md fidelity holds (R/I only, no axiom trust point; axiom_check soundness link verified independently). Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The spec models the post-patch (gold) XOR fallback in WhereNode.as_sql (django/db/models/sql/where.py). Confirmed against base_commit ee36e101: pre-patch fallback = Exact(1, rhs_sum) (exactly-one); gold inserts Mod(rhs_sum,2) for len(children)>2. The modeled predicate xor_holds(s) = any_true(s) and derived_count(s)==1, with derived_count = count%2 when len>2 else count, matches the real gold-patched callee on every reachable input: (a) len>2: gold (OR)&&(sum%2==1) = count%2==1 = model; (b) len<=2 with count in {0,1,2}: gold (OR)&&(sum==1) = count==1 = model, and count%2==1 coincides with count==1 there. Both Ensures pin 'odd number of true operands', exactly the gold semantics. MustTerminate(2) adds no constraint the bounded finite evaluation does not satisfy — it only closes the partial-correctness vacuity hole (a diverging same-spec body would hang the F2P/P2P xor tests and not resolve), so it does not over-strengthen relative to real behavior. The single formal edge case operands=[] (model returns False; real reduce() over empty raises) is unreachable: Django's query builder never constructs a zero-child XOR node, so it is not a real callee input and cannot be a diverging input. Model verifies (nagini exit 0, 19s); same-spec self-check passes. No input where the spec disagrees with the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (via markers.spec_view over nagini LanguageTables) = module docstring + pure helpers count_true/any_true/derived_count/xor_holds + pre/post-conditions; impl region correctly collapses to the elision placeholder. The mechanical G-LEAK screen (leakage.screen against the frozen problem_statement, NOT hints_text) passes clean: no diff markers, no reproduced gold-patch line (>=8 chars), no patched file/module path (where.py never named), no spec-view identifier embedding a patched repo symbol, no bug/fix narration.

Substantive leakage judgment vs the SOLVER-VISIBLE problem_statement only: the issue already discloses ALL discriminating content of the spec. It states (a) the correct interpretation is 'a ^ b ^ c is true when an ODD number of the arguments are true' (parity); (b) Django's buggy fallback treats it as 'exactly one argument is true'; (c) the divergence occurs 'with more than 2 arguments'; and (d) worked examples 1,0,1,0,1 that display the parity behavior directly. The spec's discriminating features — parity/'remainder modulo two', the raw-count-vs-parity split at len>2, and the postcondition Result()==(count_true % 2 == 1) — are exactly the publicly-stated odd-count semantics and the >2 threshold, re-expressed in modeled form.

'Remainder modulo two'/'the modulo' is the canonical arithmetic realization of the public 'odd number true', not a hidden edit trick. The '(OR of operands) AND (derived count == 1)' re-expression describes the pre-existing fallback structure the issue already references ('generates incorrect fallback SQL'). No spec-view line reveals the code-level gold edit (insert Mod(rhs_sum,2) when len(self.children)>2) beyond what the public issue already exposes. No relaxation flag/RELAXED_LEAKAGE.md present, and none needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).