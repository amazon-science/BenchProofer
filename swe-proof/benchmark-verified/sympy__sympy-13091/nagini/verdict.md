# P2 adversarial audit — sympy__sympy-13091

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,7 +139,7 @@
     # post-conditions-end
     # impl-start
     if not sympifiable:
-        return EQ_NI()
+        return EQ_FALSE()
     if content_equal:
         return EQ_TRUE()
     return EQ_FALSE()
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -172,5 +172,5 @@
     # post-conditions-end
     # impl-start
     e = sym_eq(sympifiable, content_equal)
-    return not op_eq(e, other_answer)
+    return e == EQ_FALSE()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -142,7 +142,7 @@
         return EQ_NI()
     if content_equal:
         return EQ_TRUE()
-    return EQ_FALSE()
+    return EQ_NI()
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,8 +141,8 @@
     if not sympifiable:
         return EQ_NI()
     if content_equal:
-        return EQ_TRUE()
-    return EQ_FALSE()
+        return EQ_FALSE()
+    return EQ_TRUE()
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -172,5 +172,5 @@
     # post-conditions-end
     # impl-start
     e = sym_eq(sympifiable, content_equal)
-    return not op_eq(e, other_answer)
+    return op_eq(e, other_answer)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -138,11 +138,11 @@
     Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
     # post-conditions-end
     # impl-start
-    if not sympifiable:
-        return EQ_NI()
-    if content_equal:
-        return EQ_TRUE()
-    return EQ_FALSE()
+    if sympifiable:
+        if content_equal:
+            return EQ_TRUE()
+        return EQ_FALSE()
+    return EQ_NI()
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -172,5 +172,7 @@
     # post-conditions-end
     # impl-start
     e = sym_eq(sympifiable, content_equal)
-    return not op_eq(e, other_answer)
+    if op_eq(e, other_answer):
+        return False
+    return True
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,7 +139,8 @@
     # post-conditions-end
     # impl-start
     if not sympifiable:
-        return EQ_NI()
+        while True:
+            pass
     if content_equal:
         return EQ_TRUE()
     return EQ_FALSE()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13091.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic value participates in Python's rich-comparison protocol against an
  arbitrary right-hand object. Two obligations are pinned:

  (1) The equality query of a symbolic value against a right-hand object is
      THREE-VALUED, mirroring Python's data model. It answers:
        * "equal"      when the right-hand object is a comparable peer whose
                       content coincides with the symbolic value;
        * "not equal"  when the right-hand object is a comparable peer whose
                       content differs;
        * "undecided"  (the protocol's delegation sentinel) when the right-hand
                       object is NOT a comparable peer at all -- so that the
                       operator consults the right-hand object's own reflected
                       method instead of unilaterally declaring inequality.
      Declaring a flat "not equal" against an incomparable object (instead of
      "undecided") is what breaks symmetry: a foreign object that considers
      itself equal to the symbolic value can then never be honoured.

  (2) The inequality query is the boolean complement of the FULLY-RESOLVED
      equality OPERATOR (the operator that, on an "undecided" answer, delegates
      to the right-hand object's reflected method and only then falls back to
      object identity), NOT the complement of the symbolic value's own raw
      three-valued answer. The two differ exactly when the symbolic value is
      undecided: the resolved operator yields a genuine boolean from the other
      side, whereas complementing the raw three-valued "undecided" sentinel
      collapses (the sentinel is truthy) to a constant "equal-ish" verdict that
      disagrees with the fully-resolved operator whenever it reports unequal.

The three-valued equality answer is modelled as a small integer code
(0 = not-equal, 1 = equal, 2 = undecided/delegation-sentinel). The fully
resolved `==` operator is modelled deeply (`op_eq`, the pure region) and
validated == real Python `==` dispatch out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Both contracted operations are bounded, straight-line computations: they MUST
terminate and return their reply (a total-correctness obligation, carried as
MustTerminate in the preconditions). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver a reply to the rich-comparison protocol at all.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No @ContractOnly axiom is consumed. The fully-resolved `==` operator is
#  modelled deeply as `op_eq` in the pure region below and is validated equal
#  to real Python `==` dispatch by axiom_check.py / G-AX -- an A-reference,
#  not a consumed axiom.)
# axioms-end

# pure-start
@Pure
def EQ_FALSE() -> int:
    # the comparison answers a definite "not equal"
    return 0

@Pure
def EQ_TRUE() -> int:
    # the comparison answers a definite "equal"
    return 1

@Pure
def EQ_NI() -> int:
    # the delegation sentinel: "undecided, ask the other side"
    return 2

@Pure
def eq_code(sympifiable: bool, content_equal: bool) -> int:
    """The symbolic value's three-valued equality reply (pure form, used in
    contracts). Incomparable peer -> the delegation sentinel; otherwise a
    definite verdict driven by content."""
    Ensures(Result() == EQ_FALSE() or Result() == EQ_TRUE() or Result() == EQ_NI())
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()

@Pure
def op_eq(self_answer: int, other_answer: int) -> bool:
    """The fully-resolved `==` operator on two three-valued answers.

    `self_answer` is the symbolic value's own three-valued reply
    (`sym_eq`); `other_answer` is what the right-hand object's reflected
    equality would reply (also three-valued). The operator resolves:
      * if the symbolic value is decided, take its boolean;
      * else if the right-hand object is decided, take its boolean
        (delegation to the reflected method);
      * else fall back to object identity -> distinct objects are not equal.
    """
    Requires(self_answer == EQ_FALSE() or self_answer == EQ_TRUE() or self_answer == EQ_NI())
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    if self_answer != EQ_NI():
        return self_answer == EQ_TRUE()
    if other_answer != EQ_NI():
        return other_answer == EQ_TRUE()
    return False
# pure-end

def sym_eq(sympifiable: bool, content_equal: bool) -> int:
    """Three-valued equality of a symbolic value against a right-hand object.

    `sympifiable` -- the right-hand object is a comparable peer.
    `content_equal` -- meaningful only when `sympifiable`; the peer's content
    coincides with the symbolic value.
    """
    # pre-conditions-start
    # The equality reply is a bounded, straight-line computation: it MUST
    # terminate and return its three-valued reply (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the three-valued answer is exactly the protocol reply: incomparable
    # right-hand object -> the delegation sentinel (never a flat "not equal",
    # the symmetry-preserving obligation); a comparable peer -> a definite
    # verdict driven by content.
    Ensures(Result() == eq_code(sympifiable, content_equal))
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    # post-conditions-end
    # impl-start
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()
    # impl-end

def sym_ne(sympifiable: bool, content_equal: bool, other_answer: int) -> bool:
    """Inequality of a symbolic value against a right-hand object.

    `other_answer` is the right-hand object's own three-valued equality reply,
    consulted by the resolved `==` operator on the delegation sentinel.
    """
    # pre-conditions-start
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    # The inequality reply is a bounded, straight-line computation: it MUST
    # terminate and return its boolean (total correctness; measure 2 leaves
    # room for the sym_eq sub-call's own MustTerminate(1) obligation). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # inequality is the complement of the FULLY-RESOLVED equality operator.
    Ensures(Result() == (not op_eq(eq_code(sympifiable, content_equal), other_answer)))
    # behavioural consequence the protocol demands: an incomparable peer that
    # considers itself equal to the symbolic value must NOT be reported unequal
    # (symmetry), and an incomparable peer that is genuinely unequal MUST be.
    Ensures(Implies(not sympifiable and other_answer == EQ_TRUE(), Result() == False))
    Ensures(Implies(not sympifiable and other_answer != EQ_TRUE(), Result() == True))
    # post-conditions-end
    # impl-start
    e = sym_eq(sympifiable, content_equal)
    return not op_eq(e, other_answer)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-13091 (nagini). env, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE (why it is functionally exact): sym_eq's postcondition is `Result() == eq_code(sympifiable, content_equal)` and sym_ne's is `Result() == (not op_eq(eq_code(sympifiable, content_equal), other_answer))`. Because eq_code and op_eq are @Pure total functions on a FINITE input domain (sympifiable,content_equal in {T,F}; other_answer in {EQ_FALSE,EQ_TRUE,EQ_NI}), the outputs of both contracted functions are pinned UNIQUELY at every point of the 2x2 / 2x2x3 domain. Any same-spec verifying impl is therefore behaviorally identical to gold, so its faithful refined patch IS the gold patch, which resolves.

POSITIVE CONTROL: positive_control.py = pristine bundle model.py -> `bash scripts/nagini_verify.sh` EXIT 0 (Verification successful, 12.8s).

atk_1.py: PREPATCH BUG #1 -- sym_eq foreign-peer branch returns EQ_FALSE (flat not-equal) instead of EQ_NI. weakness EXIT 2 (does not verify -- spec rejects). Reproduces recorded G-DIFF model_prepatch.py.
- atk_2.py: PREPATCH BUG #2 -- sym_ne returns `e == EQ_FALSE()` (complement of raw reply, coerces sentinel) instead of `not op_eq(...)`. weakness EXIT 2 (does not verify). Reproduces recorded G-DIFF model_prepatch_2.py.
- atk_3.py: partial-domain -- sym_eq returns EQ_NI on unequal peer (correct on foreign/equal, wrong on unequal-peer branch). weakness EXIT 2 (does not verify; postcondition Implies(sympifiable and not content_equal, Result()==EQ_FALSE) rejects).
- atk_4.py: boundary/value-swap -- sym_eq swaps EQ_TRUE/EQ_FALSE on the decided branches. weakness EXIT 2 (does not verify).
- atk_5.py: control-flow-effect -- sym_ne drops the boolean complement (`return op_eq(...)`). weakness EXIT 2 (does not verify; complement postcondition rejects).
- atk_6.py: CANDIDATE -- behaviorally-equivalent restructure of sym_eq (`if sympifiable: {decide} ; return EQ_NI()`), gold sym_ne. weakness EXIT 0 (shares spec AND verifies, 13.2s).
- atk_7.py: CANDIDATE -- behaviorally-equivalent restructure of sym_ne (`if op_eq(...): return False; return True`), gold sym_eq. weakness EXIT 0 (shares spec AND verifies, 14.6s).
- atk_8.py: control-flow divergence -- non-terminating `while True: pass` on sym_eq foreign branch (ungrounded/vacuous-postcondition probe). weakness EXIT 2 (does not verify -- MustTerminate(1) obligation leak check rejects, closing the partial-correctness gap).

MANDATORY RESOLVE RUNS EXECUTED (not speculated): both candidates atk_6/atk_7 proven behaviorally IDENTICAL to gold over the ENTIRE finite input domain (2x2 sym_eq + 2x2x3 sym_ne, 0 divergences via an out-of-band enumeration). Their faithful refined patch is therefore the gold patch (extracted from the frozen dataset row, 17385 bytes; identical to the two deltas + one-to-many ordering replications in refinement.md A/B/C). Materialized atk_6_faithful.diff / atk_7_faithful.diff (byte-identical to gold_patch.diff) and ran the OFFICIAL harness via swebench_unified.harness.run_resolve (run_id sbu-audit-bcjyr96p-atk6, prebuilt image swebench/sweb.eval.x86_64.sympy_1776_sympy-13091:latest, docker). RESULT: resolved=true, completed=true, patch_successfully_applied=true, attempts=1, flaky=false; FAIL_TO_PASS {test_equality, test_comparisons_with_unknown_type} BOTH PASS, 0 failures. Report Since the candidates' faithful patch RESOLVES, neither is a weakness -- they are correct-behaviour echoes, consistent with the fixed G-PANEL-1/G-EQ resolve policy.

REFINEMENT.MD AUDIT (A-legs focus): legs A1/A2 (R), A3/A4 (R+I), B1 (R+I), B2 (A-reference: op_eq deep model of CPython == dispatch), B3 (I). No A-consumed leg; meta.json axioms=[] (no @ContractOnly callee). No kind-3 (unexpressible-changed-op) steps -- the one genuinely changed non-refinement op (== operator dispatch) is modeled DEEPLY as op_eq and validated out-of-band. A-REFERENCE CORRESPONDENCE VERIFIED: ran axiom_check.py (G-AX) EXIT 0 -- it builds REAL Python objects whose __eq__ returns each of True/False/NotImplemented and asserts op_eq predicts `left == right` and sym_ne predicts `left != right` over all 3x3 reply combos + symmetry/identity-fallback witnesses, using the language operator (not the model's own output) as oracle -> genuinely grounded, not an ungrounded echo. Correspondence to real callees (Basic/Float/Rational/NumberSymbol __eq__/__ne__ per mapping.md) holds.

NOTE ON RECORDED VERDICT DISCREPANCY: meta.json currently records G-EQ=fail 'BROKEN (verify=/=>correct): atk_6.py verifies but its patch does not resolve'. This is a STALE fail-closed artifact from a prior pass whose OWN narrative (verdict.md line 2590) shows its resolve leg 'did not complete -- inconclusive' and that same pass's later synthesis recorded resolved=true. My independent resolve run COMPLETED and RESOLVED. The behaviorally-gold candidate's faithful patch resolves; there is no verify=/=>correct break. Verdict: SOUND (6 wrong impls rejected including both prepatch twins + a non-terminating probe; 2 verifying impls are behaviorally identical to gold and their materialized faithful patch executes to resolved=true under the official harness).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13091.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic value participates in Python's rich-comparison protocol against an
  arbitrary right-hand object. Two obligations are pinned:

  (1) The equality query of a symbolic value against a right-hand object is
      THREE-VALUED, mirroring Python's data model. It answers:
        * "equal"      when the right-hand object is a comparable peer whose
                       content coincides with the symbolic value;
        * "not equal"  when the right-hand object is a comparable peer whose
                       content differs;
        * "undecided"  (the protocol's delegation sentinel) when the right-hand
                       object is NOT a comparable peer at all -- so that the
                       operator consults the right-hand object's own reflected
                       method instead of unilaterally declaring inequality.
      Declaring a flat "not equal" against an incomparable object (instead of
      "undecided") is what breaks symmetry: a foreign object that considers
      itself equal to the symbolic value can then never be honoured.

  (2) The inequality query is the boolean complement of the FULLY-RESOLVED
      equality OPERATOR (the operator that, on an "undecided" answer, delegates
      to the right-hand object's reflected method and only then falls back to
      object identity), NOT the complement of the symbolic value's own raw
      three-valued answer. The two differ exactly when the symbolic value is
      undecided: the resolved operator yields a genuine boolean from the other
      side, whereas complementing the raw three-valued "undecided" sentinel
      collapses (the sentinel is truthy) to a constant "equal-ish" verdict that
      disagrees with the fully-resolved operator whenever it reports unequal.

The three-valued equality answer is modelled as a small integer code
(0 = not-equal, 1 = equal, 2 = undecided/delegation-sentinel). The fully
resolved `==` operator is modelled deeply (`op_eq`, the pure region) and
validated == real Python `==` dispatch out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Both contracted operations are bounded, straight-line computations: they MUST
terminate and return their reply (a total-correctness obligation, carried as
MustTerminate in the preconditions). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver a reply to the rich-comparison protocol at all.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No @ContractOnly axiom is consumed. The fully-resolved `==` operator is
#  modelled deeply as `op_eq` in the pure region below and is validated equal
#  to real Python `==` dispatch by axiom_check.py / G-AX -- an A-reference,
#  not a consumed axiom.)
# axioms-end

# pure-start
@Pure
def EQ_FALSE() -> int:
    # the comparison answers a definite "not equal"
    return 0

@Pure
def EQ_TRUE() -> int:
    # the comparison answers a definite "equal"
    return 1

@Pure
def EQ_NI() -> int:
    # the delegation sentinel: "undecided, ask the other side"
    return 2

@Pure
def eq_code(sympifiable: bool, content_equal: bool) -> int:
    """The symbolic value's three-valued equality reply (pure form, used in
    contracts). Incomparable peer -> the delegation sentinel; otherwise a
    definite verdict driven by content."""
    Ensures(Result() == EQ_FALSE() or Result() == EQ_TRUE() or Result() == EQ_NI())
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()

@Pure
def op_eq(self_answer: int, other_answer: int) -> bool:
    """The fully-resolved `==` operator on two three-valued answers.

    `self_answer` is the symbolic value's own three-valued reply
    (`sym_eq`); `other_answer` is what the right-hand object's reflected
    equality would reply (also three-valued). The operator resolves:
      * if the symbolic value is decided, take its boolean;
      * else if the right-hand object is decided, take its boolean
        (delegation to the reflected method);
      * else fall back to object identity -> distinct objects are not equal.
    """
    Requires(self_answer == EQ_FALSE() or self_answer == EQ_TRUE() or self_answer == EQ_NI())
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    if self_answer != EQ_NI():
        return self_answer == EQ_TRUE()
    if other_answer != EQ_NI():
        return other_answer == EQ_TRUE()
    return False
# pure-end

def sym_eq(sympifiable: bool, content_equal: bool) -> int:
    """Three-valued equality of a symbolic value against a right-hand object.

    `sympifiable` -- the right-hand object is a comparable peer.
    `content_equal` -- meaningful only when `sympifiable`; the peer's content
    coincides with the symbolic value.
    """
    # pre-conditions-start
    # The equality reply is a bounded, straight-line computation: it MUST
    # terminate and return its three-valued reply (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the three-valued answer is exactly the protocol reply: incomparable
    # right-hand object -> the delegation sentinel (never a flat "not equal",
    # the symmetry-preserving obligation); a comparable peer -> a definite
    # verdict driven by content.
    Ensures(Result() == eq_code(sympifiable, content_equal))
    Ensures(Implies(not sympifiable, Result() == EQ_NI()))
    Ensures(Implies(sympifiable and content_equal, Result() == EQ_TRUE()))
    Ensures(Implies(sympifiable and not content_equal, Result() == EQ_FALSE()))
    # post-conditions-end
    # impl-start
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()
    # impl-end

def sym_ne(sympifiable: bool, content_equal: bool, other_answer: int) -> bool:
    """Inequality of a symbolic value against a right-hand object.

    `other_answer` is the right-hand object's own three-valued equality reply,
    consulted by the resolved `==` operator on the delegation sentinel.
    """
    # pre-conditions-start
    Requires(other_answer == EQ_FALSE() or other_answer == EQ_TRUE() or other_answer == EQ_NI())
    # The inequality reply is a bounded, straight-line computation: it MUST
    # terminate and return its boolean (total correctness; measure 2 leaves
    # room for the sym_eq sub-call's own MustTerminate(1) obligation). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver a reply to the protocol at all.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # inequality is the complement of the FULLY-RESOLVED equality operator.
    Ensures(Result() == (not op_eq(eq_code(sympifiable, content_equal), other_answer)))
    # behavioural consequence the protocol demands: an incomparable peer that
    # considers itself equal to the symbolic value must NOT be reported unequal
    # (symmetry), and an incomparable peer that is genuinely unequal MUST be.
    Ensures(Implies(not sympifiable and other_answer == EQ_TRUE(), Result() == False))
    Ensures(Implies(not sympifiable and other_answer != EQ_TRUE(), Result() == True))
    # post-conditions-end
    # impl-start
    e = sym_eq(sympifiable, content_equal)
    return not op_eq(e, other_answer)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-13091 (nagini). env, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE (why it is functionally exact): sym_eq's postcondition is `Result() == eq_code(sympifiable, content_equal)` and sym_ne's is `Result() == (not op_eq(eq_code(sympifiable, content_equal), other_answer))`. Because eq_code and op_eq are @Pure total functions on a FINITE input domain (sympifiable,content_equal in {T,F}; other_answer in {EQ_FALSE,EQ_TRUE,EQ_NI}), the outputs of both contracted functions are pinned UNIQUELY at every point of the 2x2 / 2x2x3 domain. Any same-spec verifying impl is therefore behaviorally identical to gold, so its faithful refined patch IS the gold patch, which resolves.

POSITIVE CONTROL: positive_control.py = pristine bundle model.py -> `bash scripts/nagini_verify.sh` EXIT 0 (Verification successful, 12.8s).

atk_1.py: PREPATCH BUG #1 -- sym_eq foreign-peer branch returns EQ_FALSE (flat not-equal) instead of EQ_NI. weakness EXIT 2 (does not verify -- spec rejects). Reproduces recorded G-DIFF model_prepatch.py.
- atk_2.py: PREPATCH BUG #2 -- sym_ne returns `e == EQ_FALSE()` (complement of raw reply, coerces sentinel) instead of `not op_eq(...)`. weakness EXIT 2 (does not verify). Reproduces recorded G-DIFF model_prepatch_2.py.
- atk_3.py: partial-domain -- sym_eq returns EQ_NI on unequal peer (correct on foreign/equal, wrong on unequal-peer branch). weakness EXIT 2 (does not verify; postcondition Implies(sympifiable and not content_equal, Result()==EQ_FALSE) rejects).
- atk_4.py: boundary/value-swap -- sym_eq swaps EQ_TRUE/EQ_FALSE on the decided branches. weakness EXIT 2 (does not verify).
- atk_5.py: control-flow-effect -- sym_ne drops the boolean complement (`return op_eq(...)`). weakness EXIT 2 (does not verify; complement postcondition rejects).
- atk_6.py: CANDIDATE -- behaviorally-equivalent restructure of sym_eq (`if sympifiable: {decide} ; return EQ_NI()`), gold sym_ne. weakness EXIT 0 (shares spec AND verifies, 13.2s).
- atk_7.py: CANDIDATE -- behaviorally-equivalent restructure of sym_ne (`if op_eq(...): return False; return True`), gold sym_eq. weakness EXIT 0 (shares spec AND verifies, 14.6s).
- atk_8.py: control-flow divergence -- non-terminating `while True: pass` on sym_eq foreign branch (ungrounded/vacuous-postcondition probe). weakness EXIT 2 (does not verify -- MustTerminate(1) obligation leak check rejects, closing the partial-correctness gap).

MANDATORY RESOLVE RUNS EXECUTED (not speculated): both candidates atk_6/atk_7 proven behaviorally IDENTICAL to gold over the ENTIRE finite input domain (2x2 sym_eq + 2x2x3 sym_ne, 0 divergences via an out-of-band enumeration). Their faithful refined patch is therefore the gold patch (extracted from the frozen dataset row, 17385 bytes; identical to the two deltas + one-to-many ordering replications in refinement.md A/B/C). Materialized atk_6_faithful.diff / atk_7_faithful.diff (byte-identical to gold_patch.diff) and ran the OFFICIAL harness via swebench_unified.harness.run_resolve (run_id sbu-audit-bcjyr96p-atk6, prebuilt image swebench/sweb.eval.x86_64.sympy_1776_sympy-13091:latest, docker). RESULT: resolved=true, completed=true, patch_successfully_applied=true, attempts=1, flaky=false; FAIL_TO_PASS {test_equality, test_comparisons_with_unknown_type} BOTH PASS, 0 failures. Report Since the candidates' faithful patch RESOLVES, neither is a weakness -- they are correct-behaviour echoes, consistent with the fixed G-PANEL-1/G-EQ resolve policy.

REFINEMENT.MD AUDIT (A-legs focus): legs A1/A2 (R), A3/A4 (R+I), B1 (R+I), B2 (A-reference: op_eq deep model of CPython == dispatch), B3 (I). No A-consumed leg; meta.json axioms=[] (no @ContractOnly callee). No kind-3 (unexpressible-changed-op) steps -- the one genuinely changed non-refinement op (== operator dispatch) is modeled DEEPLY as op_eq and validated out-of-band. A-REFERENCE CORRESPONDENCE VERIFIED: ran axiom_check.py (G-AX) EXIT 0 -- it builds REAL Python objects whose __eq__ returns each of True/False/NotImplemented and asserts op_eq predicts `left == right` and sym_ne predicts `left != right` over all 3x3 reply combos + symmetry/identity-fallback witnesses, using the language operator (not the model's own output) as oracle -> genuinely grounded, not an ungrounded echo. Correspondence to real callees (Basic/Float/Rational/NumberSymbol __eq__/__ne__ per mapping.md) holds.

NOTE ON RECORDED VERDICT DISCREPANCY: meta.json currently records G-EQ=fail 'BROKEN (verify=/=>correct): atk_6.py verifies but its patch does not resolve'. This is a STALE fail-closed artifact from a prior pass whose OWN narrative (verdict.md line 2590) shows its resolve leg 'did not complete -- inconclusive' and that same pass's later synthesis recorded resolved=true. My independent resolve run COMPLETED and RESOLVED. The behaviorally-gold candidate's faithful patch resolves; there is no verify=/=>correct break. Verdict: SOUND (6 wrong impls rejected including both prepatch twins + a non-terminating probe; 2 verifying impls are behaviorally identical to gold and their materialized faithful patch executes to resolved=true under the official harness).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sympy__sympy-13091 (nagini) — spec is FAITHFUL; no diverging input found. Modeled functions: sym_eq (three-valued __eq__ reply: EQ_NI/EQ_TRUE/EQ_FALSE) and sym_ne (inequality = complement of the fully-resolved op_eq operator), with op_eq a deep model (A-reference, no consumed axiom) of CPython's ==/!= rich-comparison dispatch. Verification performed:

1) op_eq deep-model fidelity: independently re-derived (not trusting axiom_check.py) — built real Python objects whose __eq__ returns each of True/False/NotImplemented and compared observed `left == right` / `left != right` against op_eq/sym_ne over all 3x3 code combinations. Zero divergence; real == always resolves to bool, matching op_eq's identity-fallback (both-NI -> False). NOTE: benchmark-verified/.../axiom_check.py CRASHES at exit 1 on modern Python (line 151 `not raw` where raw is NotImplemented -> TypeError 'NotImplemented should not be used in a boolean context'), but this is the cosmetic final 'confirm the pre-patch bug' block only; the 3x3 soundness + symmetry/identity-fallback assertions above it all pass, and the recorded G-AX ran to exit 0. Not a faithfulness defect of the spec.

2) sym_eq/sym_ne bridge vs REAL patched repo at base_commit d1320814 (worktree, patched: Basic.__eq__ returns NotImplemented on SympifyError, __ne__ = `not self == other`): conformance_check.py run with -> 'G-CONF OK ... 100000 modeled-function inputs (50000 cases, seed=13091), 0 disagreements.'

3) Adversarial boundary probes on real sympy (Symbol, Symbol+1, Integer, Rational, Float, pi, E, I, oo, nan):
   - Non-sympifiable/foreign peers (ForeignTrue/False/NI): real type(self).__eq__ returns NotImplemented (<->EQ_NI) in every case, never a flat bool — matches spec postcondition Implies(not sympifiable, Result()==EQ_NI). The sym_ne foreign-peer symmetry consequences (other_answer==EQ_TRUE -> !=False; else -> !=True) all hold on real objects.
   - Sympifiable peers never yield NotImplemented from self.__eq__ (definite verdict) — matches Implies(sympifiable, definite). No 'sympifiable-but-NI' or 'non-sympifiable-but-definite' cases found across the probe grid.

4) same_spec self-check on model.py: SAME (exit 0); spec/proof/impl markers well-formed; op_eq/eq_code/EQ_* in pure region, no @ContractOnly axiom consumed (matches meta.axioms empty).

Conclusion: the modeled functions agree with the real patched callee on every tested input, including the symmetry/delegation-sentinel edge cases the spec pins hardest. The spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). The mechanical screen (leakage.screen, python flavor over spec_view) PASSES: no diff markers, no verbatim gold-patch line (>=8 normalized chars), no patched file path/module path, no spec-view identifier embedding a distinctive patched symbol, no patched symbol named in comments, no bug/fix narration. Patch changed-symbols {eval_Eq, getnewargs, nonzero, strict_eq} do not appear anywhere in the spec view; patched paths (sympy/core/basic.py etc.) absent.

Substantive judgment: the spec view reveals nothing beyond what the problem_statement already makes public. This instance's problem_statement is unusually explicit — it literally states the gold fix ("just replace `return False` with `return NotImplemented`", cites line 316 of basic.py), explains the delegation-to-reflected-method mechanism, notes the other rich-comparison methods behave similarly, and states that if both sides return NotImplemented the result is False. Thus the A-delta (return the delegation sentinel for a foreign/incomparable RHS instead of a flat 'not equal') and the B-delta (inequality = complement of the fully-resolved operator that delegates to the reflected method) are BOTH already public.

The model.py spec view describes exactly this behaviour in abstract carriers (three-valued int code EQ_FALSE/EQ_TRUE/EQ_NI, op_eq deep-model of == dispatch, sym_eq/sym_ne) — an abstraction of publicly-known behaviour, not a disclosure exceeding the problem statement. Spec-view symbols (sym_eq, sym_ne, op_eq, eq_code, sympifiable, content_equal) are model-invented and localize no repo edit. Docstring/comment prose stays at the behavioural (protocol/symmetry) level and contains no fix narration. No line leaks the gold edit beyond the problem_statement.

Note: G-PANEL-3 also honors accepted RELAXED_LEAKAGE.md deferrals, but none applies here — the screen passes cleanly, so no relaxation is invoked.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
