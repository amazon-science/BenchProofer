# P2 adversarial audit — sympy__sympy-17318

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -179,7 +177,22 @@
             and not all_fast_facet(ToSeq(codes))
             and not any_has_depth(ToSeq(codes)))
     # impl-start
-    if all_fast_facet(ToSeq(codes)):
+    # Pre-patch guard: take the fast path when every addend is non-nested-or-
+    # eligible (codes 0, 1, 2) — admitting addends that lack facet E (the
+    # non-eligible non-nested code 2) as long as they are not nested. A shallow
+    # sum with such a non-eligible addend is therefore admitted to the fast path
+    # even though the helper's facet-E precondition is not met.
+    all_admit = True
+    i = 0
+    while i < len(codes):
+        # invariants-start
+        Invariant(Acc(list_pred(codes), 1 / 2))
+        Invariant(0 <= i and i <= len(codes))
+        # invariants-end
+        if codes[i] == 3:
+            all_admit = False
+        i = i + 1
+    if all_admit:
         k = num_surds(ToSeq(codes))
         return split_by_radicand_gcd(ToSeq(codes), k)
     if not any_has_depth(ToSeq(codes)):
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -180,8 +178,7 @@
             and not any_has_depth(ToSeq(codes)))
     # impl-start
     if all_fast_facet(ToSeq(codes)):
-        k = num_surds(ToSeq(codes))
-        return split_by_radicand_gcd(ToSeq(codes), k)
+        return 1
     if not any_has_depth(ToSeq(codes)):
         raise NoMatch()
     return 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -180,8 +178,7 @@
             and not any_has_depth(ToSeq(codes)))
     # impl-start
     if all_fast_facet(ToSeq(codes)):
-        k = num_surds(ToSeq(codes))
-        return split_by_radicand_gcd(ToSeq(codes), k)
+        return 2
     if not any_has_depth(ToSeq(codes)):
         raise NoMatch()
     return 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -180,8 +178,7 @@
             and not any_has_depth(ToSeq(codes)))
     # impl-start
     if all_fast_facet(ToSeq(codes)):
-        k = num_surds(ToSeq(codes))
-        return split_by_radicand_gcd(ToSeq(codes), k)
+        return split_by_radicand_gcd(ToSeq(codes), len(codes))
     if not any_has_depth(ToSeq(codes)):
         raise NoMatch()
     return 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -182,7 +180,5 @@
     if all_fast_facet(ToSeq(codes)):
         k = num_surds(ToSeq(codes))
         return split_by_radicand_gcd(ToSeq(codes), k)
-    if not any_has_depth(ToSeq(codes)):
-        raise NoMatch()
     return 1
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -182,7 +180,5 @@
     if all_fast_facet(ToSeq(codes)):
         k = num_surds(ToSeq(codes))
         return split_by_radicand_gcd(ToSeq(codes), k)
-    if not any_has_depth(ToSeq(codes)):
-        raise NoMatch()
-    return 1
+    raise NoMatch()
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -179,10 +177,10 @@
             and not all_fast_facet(ToSeq(codes))
             and not any_has_depth(ToSeq(codes)))
     # impl-start
-    if all_fast_facet(ToSeq(codes)):
+    if any_has_depth(ToSeq(codes)):
         k = num_surds(ToSeq(codes))
         return split_by_radicand_gcd(ToSeq(codes), k)
-    if not any_has_depth(ToSeq(codes)):
+    if not all_fast_facet(ToSeq(codes)):
         raise NoMatch()
     return 1
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NoMatch(Exception):
@@ -152,7 +151,6 @@
     # ties the guard to the helper's precondition.
     Requires(Implies(all_fast_facet(ToSeq(codes)),
                      num_surds(ToSeq(codes)) >= 1))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(codes), 1 / 2))
@@ -179,10 +177,10 @@
             and not all_fast_facet(ToSeq(codes))
             and not any_has_depth(ToSeq(codes)))
     # impl-start
-    if all_fast_facet(ToSeq(codes)):
-        k = num_surds(ToSeq(codes))
-        return split_by_radicand_gcd(ToSeq(codes), k)
-    if not any_has_depth(ToSeq(codes)):
+    if not all_fast_facet(ToSeq(codes)):
+        if any_has_depth(ToSeq(codes)):
+            return 1
         raise NoMatch()
-    return 1
+    k = num_surds(ToSeq(codes))
+    return split_by_radicand_gcd(ToSeq(codes), k)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-17318.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic additive expression is matched against the shape ``a + b*sqrt(r)``.
  The matcher first decides whether to use the FAST path, a helper that splits a
  sum of square-root terms by the greatest common divisor of their radicands.

  Each addend has two abstract facets that decide the branch: whether it is
  ELIGIBLE for the fast splitting path (facet E), and whether it CARRIES A
  NESTED RADICAL (facet N). The splitting helper is only well-defined for a sum
  every addend of which has facet E, and only when the sum actually contains at
  least one square-root term; handed a sum with no square-root term it has
  nothing to split and cannot produce a result.

  The behaviour pinned here:

    (1) The fast path is taken EXACTLY when every addend has facet E. When that
        holds for a genuine multi-term sum, at least one addend is a square-root
        term, so the helper's precondition (at least one square-root term
        present) is met and the fast path yields a match.

    (2) If some addend lacks facet E, the fast path is NOT taken — calling the
        helper there would violate its precondition. Instead the matcher falls
        back to a depth-based analysis. When every addend is shallow (lacks
        facet N, maximal nesting depth zero), that analysis finds nothing to
        denest and the result is NO MATCH (an empty match), with no error.

    (3) Otherwise (some addend lacks facet E while another carries facet N) the
        depth-based analysis proceeds and yields a match around the deepest
        addend.

Each addend is abstracted by an integer category code over the two facets
(E = fast-path eligible, N = carries a nested radical):

    0  facet E, no N           (a fast-eligible non-nested addend)
    1  facet E, with N         (a fast-eligible square-root term)
    2  not E, no N             (a non-eligible non-nested addend)
    3  not E, with N           (a non-eligible nested addend)

The sum of addend codes is carried as ``PSeq[int]`` (Nagini bans ``str``/object
indexing in specs); the per-element predicates are folded front-recursively so a
single unfold is available per loop step. The empty match is signalled by a
user-defined exception (a builtin exception in an ``Exsures`` crashes the Nagini
translator; mapping.md §2). The unchanged splitting helper is axiomatized with
its at-least-one-square-root-term precondition (A-consumed; mapping.md §3).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NoMatch(Exception):
    """Signals the sum does not match ``a + b*sqrt(r)`` — the depth-based
    analysis found nothing to denest (maximal depth zero). Stands in for the
    empty list the real matcher returns; a builtin exception in an ``Exsures``
    crashes the Nagini translator (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def split_by_radicand_gcd(codes: PSeq[int], k: int) -> int:
    """The unchanged splitting helper (radicand-gcd split of a sum of
    square-root terms). It is meaningful only for a sum every addend of which
    has facet E (fast-path eligible) AND that contains at least one square-root
    term (``k`` of them, ``k >= 1``); handed a sum with no square-root term it
    cannot produce a result. Returns the SPLIT outcome for the match it
    produces — an opaque value distinct from the depth analysis' match marker,
    so the result records that the split helper, not the depth analysis,
    produced this match.
    Weakest contract the proof needs; provenance + soundness check in
    mapping.md / axiom_check.py.
    """
    Requires(all_fast_facet(codes))
    Requires(k == num_surds(codes))
    Requires(k >= 1)
    # A match is produced by the split helper. Its result is the SPLIT outcome,
    # an opaque value distinct from the depth analysis' match marker (1): the
    # exact value is NOT pinned, only that it differs from 1, so a caller's
    # result observably records WHICH mechanism produced the match while the
    # value itself can be obtained ONLY by invoking this helper (a literal
    # cannot be proved equal to it).
    Ensures(Result() != 1)
# axioms-end


# pure-start
@Pure
def code_fast_facet(c: int) -> bool:
    """An addend with facet E (fast-path eligible): codes 0 and 1."""
    return c == 0 or c == 1


@Pure
def code_is_surd(c: int) -> bool:
    """An addend that is a square-root term contributing to the split (code 1:
    fast-path eligible WITH a nested radical)."""
    return c == 1


@Pure
def code_has_depth(c: int) -> bool:
    """An addend carrying facet N (a nested radical, maximal depth at least
    one): codes 1 and 3."""
    return c == 1 or c == 3


@Pure
def all_fast_facet(s: PSeq[int]) -> bool:
    """Every addend of the sum has facet E (fast-path eligible). Front-recursive
    so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return code_fast_facet(s[0]) and all_fast_facet(s.drop(1))


@Pure
def num_surds(s: PSeq[int]) -> int:
    """How many addends are square-root terms (code 1)."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if code_is_surd(s[0]) else 0) + num_surds(s.drop(1))


@Pure
def any_has_depth(s: PSeq[int]) -> bool:
    """Some addend carries facet N (a nested radical, maximal depth at least
    one)."""
    if len(s) == 0:
        return False
    return code_has_depth(s[0]) or any_has_depth(s.drop(1))
# pure-end


def match_additive(codes: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(codes), 1 / 2))
    # The argument is a genuine multi-term sum of valid addend codes.
    Requires(len(codes) >= 2)
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(codes),
                             0 <= codes[k] and codes[k] <= 3),
                     [[codes[k]]])))
    # A genuine multi-term sum every addend of which has facet E always contains
    # at least one square-root term (a sum of only non-radical addends would
    # collapse to a single number and not be a multi-term sum). This frame fact
    # ties the guard to the helper's precondition.
    Requires(Implies(all_fast_facet(ToSeq(codes)),
                     num_surds(ToSeq(codes)) >= 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(codes), 1 / 2))
    # A match was produced ONLY along a path that is sound: either every addend
    # has facet E (the SPLIT path) or some addend carries facet N so the depth
    # analysis matches (the DEPTH path).
    Ensures(all_fast_facet(ToSeq(codes)) or any_has_depth(ToSeq(codes)))
    # The result records WHICH mechanism produced the match, so the two paths are
    # observably distinct. On the SPLIT path the result is exactly the value the
    # splitting helper returns for this sum -- pinning the OUTPUT of the modeled
    # computation, not a literal: the helper's value is opaque, so the only way
    # to satisfy this clause is to actually invoke the helper. On the DEPTH path
    # the result is the depth-analysis match marker 1.
    Ensures(Implies(all_fast_facet(ToSeq(codes)) and num_surds(ToSeq(codes)) >= 1,
                    Result() == split_by_radicand_gcd(ToSeq(codes),
                                                       num_surds(ToSeq(codes)))))
    Ensures(Implies(not all_fast_facet(ToSeq(codes)), Result() == 1))
    # post-conditions-end
    # The empty match: no addend carries facet N (no nesting) AND not every
    # addend has facet E — a shallow sum with a non-eligible addend. The fast
    # path is provably NOT taken here (its precondition would be violated).
    Exsures(NoMatch,
            Acc(list_pred(codes), 1 / 2)
            and not all_fast_facet(ToSeq(codes))
            and not any_has_depth(ToSeq(codes)))
    # impl-start
    if all_fast_facet(ToSeq(codes)):
        k = num_surds(ToSeq(codes))
        return split_by_radicand_gcd(ToSeq(codes), k)
    if not any_has_depth(ToSeq(codes)):
        raise NoMatch()
    return 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: source activate; run from repo root. All artifacts in the assigned fresh scratch dir Nagini verifications launched as background jobs <=3 JVM+Z3 at a time (batches: {pos_control,atk_1,atk_2}, {atk_3,atk_4,atk_5}, {atk_6,atk_7,atk_8}).

SPEC SHAPE: match_additive's postconditions fully pin the abstract behaviour of every path. Fast path (all_fast_facet true): precondition frame-fact forces num_surds>=1, and Result()==split_by_radicand_gcd(ToSeq(codes), num_surds(ToSeq(codes))) pins the result to the OPAQUE helper output (obtainable only by actually calling the @ContractOnly helper with k==num_surds; a literal/marker cannot be proven equal). Depth path (not all_fast_facet, normal return): Result()==1. Empty-match state (not all_fast_facet and not any_has_depth): Ensures(all_fast_facet or any_has_depth) forbids normal return, and Exsures(NoMatch,...) forces NoMatch. This leaves essentially no behavioural freedom.

### ATTACKS (all same-spec: `adversary same-spec` exit 0 on all 8, spec region byte-identical):
- atk_1 (PREPATCH BUG): reverts to the loose pre-patch guard (inline loop admitting every code != 3, i.e. the non-eligible non-nested code 2 into the fast path). weakness => exit 2 NOT-A-COUNTEREXAMPLE: does NOT verify (the split_by_radicand_gcd precondition all_fast_facet(codes) is not established). Prepatch reproduced.
- atk_2 (fabricated marker on fast path: return 1 when all_fast_facet): exit 2, does NOT verify (cannot prove 1 == opaque helper output; also violates Result()!=1 chain).
- atk_3 (ungrounded literal on fast path: return 2): exit 2, does NOT verify (literal 2 cannot be proven == opaque helper output).
- atk_4 (ungrounded-oracle echo / wrong k: call helper with len(codes) instead of num_surds): exit 2, does NOT verify (violates k==num_surds precondition AND Result()==split_by_radicand_gcd(...,num_surds) postcondition).
- atk_5 (control-flow-effect: drop the NoMatch branch, return 1 for the empty-match state): exit 2, does NOT verify (Exsures(NoMatch) / Ensures(all_fast_facet or any_has_depth) violated).
- atk_6 (control-flow-effect: depth path raises NoMatch instead of returning marker 1): exit 2, does NOT verify (Ensures not all_fast_facet => Result()==1 and Exsures domain violated).
- atk_7 (boundary / wrong discriminator: guard on any_has_depth instead of all_fast_facet): exit 2, does NOT verify.
- atk_8 (CANDIDATE: behaviour-preserving branch reorder -- guard-false handled first (depth->1 / empty->NoMatch), guard-true falls through to split): weakness => exit 0 CANDIDATE (shares spec AND verifies, 13.4s). This is behaviourally IDENTICAL to the gold model impl, so its faithful refined patch IS the gold patch verbatim.

MANDATORY RESOLVE (protocol step 2) for the one verifying candidate atk_8: materialized faithful refined patch = the gold patch verbatim (patch_atk8.diff on disk). Ran through the OFFICIAL harness swebench_unified.harness.run_resolve('sympy__sympy-17318', patch, timeout=1800, retries=1) TWICE: RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. tests_status: FAIL_TO_PASS test_issue_12420 success; all 10 PASS_TO_PASS success; zero failures. => atk_8 is a correct echo whose patch RESOLVES -- NOT a verify-not-correct witness.

CONTRADICTS PRIOR RECORDED VERDICT: meta.json G-EQ (2026-08-12, the auditor) recorded 'BROKEN: atk_8.py verifies but its patch does not resolve'. That prior atk_8 is byte-identical to mine (verdict.md lines 1542-1550: the same branch reorder). Since that impl is behaviourally identical to gold, its faithful patch is the gold patch, which I re-ran and it RESOLVES (completed, all tests pass). The prior BROKEN was a false positive (likely an unfaithful hand-restructured sqrtdenest patch or a harness/timeout flake; an EARLIER verdict.md G-EQ section for the SAME cell concluded SOUND with these patches resolving). The counterexample field in the BROKEN record is literally 'None'.

REFINEMENT.MD LEG AUDIT: legs A1(R), A2(R+I), A3(A-consumed), A4(R), A5(R frame-fact). No kind-3 (unexpressible-changed-op) legs -- the changed op (guard tightening (x**2).is_Rational -> is_Rational and is_positive) is modeled DEEPLY via code_fast_facet/all_fast_facet, not hidden behind an axiom on the changed function. The only axiom is A-consumed on the UNCHANGED callee split_surds. meta.json deep_model_references=[] (no A-reference legs to audit). A-consumed correspondence grounded by G-AX (axiom_check.py exit 0, status pass): real split_surds returns normally on all-positive-rational sums with >=1 surd, RAISES IndexError on the shallow imaginary sums the old guard admitted (4+I,3+2I,5/3+I,7+I), frame fact all_fast_facet=>num_surds>=1 holds, _sqrt_match(4+I)==[] end-to-end.

CONCLUSION: 7 distinct wrong-impl attacks (partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo + prepatch) ALL rejected by verification; the only verifying same-spec impl is a behaviour-preserving echo whose materialized faithful patch RESOLVES under the official harness. Spec is not too weak. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-17318.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic additive expression is matched against the shape ``a + b*sqrt(r)``.
  The matcher first decides whether to use the FAST path, a helper that splits a
  sum of square-root terms by the greatest common divisor of their radicands.

  Each addend has two abstract facets that decide the branch: whether it is
  ELIGIBLE for the fast splitting path (facet E), and whether it CARRIES A
  NESTED RADICAL (facet N). The splitting helper is only well-defined for a sum
  every addend of which has facet E, and only when the sum actually contains at
  least one square-root term; handed a sum with no square-root term it has
  nothing to split and cannot produce a result.

  The behaviour pinned here:

    (1) The fast path is taken EXACTLY when every addend has facet E. When that
        holds for a genuine multi-term sum, at least one addend is a square-root
        term, so the helper's precondition (at least one square-root term
        present) is met and the fast path yields a match.

    (2) If some addend lacks facet E, the fast path is NOT taken — calling the
        helper there would violate its precondition. Instead the matcher falls
        back to a depth-based analysis. When every addend is shallow (lacks
        facet N, maximal nesting depth zero), that analysis finds nothing to
        denest and the result is NO MATCH (an empty match), with no error.

    (3) Otherwise (some addend lacks facet E while another carries facet N) the
        depth-based analysis proceeds and yields a match around the deepest
        addend.

Each addend is abstracted by an integer category code over the two facets
(E = fast-path eligible, N = carries a nested radical):

    0  facet E, no N           (a fast-eligible non-nested addend)
    1  facet E, with N         (a fast-eligible square-root term)
    2  not E, no N             (a non-eligible non-nested addend)
    3  not E, with N           (a non-eligible nested addend)

The sum of addend codes is carried as ``PSeq[int]`` (Nagini bans ``str``/object
indexing in specs); the per-element predicates are folded front-recursively so a
single unfold is available per loop step. The empty match is signalled by a
user-defined exception (a builtin exception in an ``Exsures`` crashes the Nagini
translator; mapping.md §2). The unchanged splitting helper is axiomatized with
its at-least-one-square-root-term precondition (A-consumed; mapping.md §3).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NoMatch(Exception):
    """Signals the sum does not match ``a + b*sqrt(r)`` — the depth-based
    analysis found nothing to denest (maximal depth zero). Stands in for the
    empty list the real matcher returns; a builtin exception in an ``Exsures``
    crashes the Nagini translator (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def split_by_radicand_gcd(codes: PSeq[int], k: int) -> int:
    """The unchanged splitting helper (radicand-gcd split of a sum of
    square-root terms). It is meaningful only for a sum every addend of which
    has facet E (fast-path eligible) AND that contains at least one square-root
    term (``k`` of them, ``k >= 1``); handed a sum with no square-root term it
    cannot produce a result. Returns the SPLIT outcome for the match it
    produces — an opaque value distinct from the depth analysis' match marker,
    so the result records that the split helper, not the depth analysis,
    produced this match.
    Weakest contract the proof needs; provenance + soundness check in
    mapping.md / axiom_check.py.
    """
    Requires(all_fast_facet(codes))
    Requires(k == num_surds(codes))
    Requires(k >= 1)
    # A match is produced by the split helper. Its result is the SPLIT outcome,
    # an opaque value distinct from the depth analysis' match marker (1): the
    # exact value is NOT pinned, only that it differs from 1, so a caller's
    # result observably records WHICH mechanism produced the match while the
    # value itself can be obtained ONLY by invoking this helper (a literal
    # cannot be proved equal to it).
    Ensures(Result() != 1)
# axioms-end


# pure-start
@Pure
def code_fast_facet(c: int) -> bool:
    """An addend with facet E (fast-path eligible): codes 0 and 1."""
    return c == 0 or c == 1


@Pure
def code_is_surd(c: int) -> bool:
    """An addend that is a square-root term contributing to the split (code 1:
    fast-path eligible WITH a nested radical)."""
    return c == 1


@Pure
def code_has_depth(c: int) -> bool:
    """An addend carrying facet N (a nested radical, maximal depth at least
    one): codes 1 and 3."""
    return c == 1 or c == 3


@Pure
def all_fast_facet(s: PSeq[int]) -> bool:
    """Every addend of the sum has facet E (fast-path eligible). Front-recursive
    so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return code_fast_facet(s[0]) and all_fast_facet(s.drop(1))


@Pure
def num_surds(s: PSeq[int]) -> int:
    """How many addends are square-root terms (code 1)."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if code_is_surd(s[0]) else 0) + num_surds(s.drop(1))


@Pure
def any_has_depth(s: PSeq[int]) -> bool:
    """Some addend carries facet N (a nested radical, maximal depth at least
    one)."""
    if len(s) == 0:
        return False
    return code_has_depth(s[0]) or any_has_depth(s.drop(1))
# pure-end


def match_additive(codes: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(codes), 1 / 2))
    # The argument is a genuine multi-term sum of valid addend codes.
    Requires(len(codes) >= 2)
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(codes),
                             0 <= codes[k] and codes[k] <= 3),
                     [[codes[k]]])))
    # A genuine multi-term sum every addend of which has facet E always contains
    # at least one square-root term (a sum of only non-radical addends would
    # collapse to a single number and not be a multi-term sum). This frame fact
    # ties the guard to the helper's precondition.
    Requires(Implies(all_fast_facet(ToSeq(codes)),
                     num_surds(ToSeq(codes)) >= 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(codes), 1 / 2))
    # A match was produced ONLY along a path that is sound: either every addend
    # has facet E (the SPLIT path) or some addend carries facet N so the depth
    # analysis matches (the DEPTH path).
    Ensures(all_fast_facet(ToSeq(codes)) or any_has_depth(ToSeq(codes)))
    # The result records WHICH mechanism produced the match, so the two paths are
    # observably distinct. On the SPLIT path the result is exactly the value the
    # splitting helper returns for this sum -- pinning the OUTPUT of the modeled
    # computation, not a literal: the helper's value is opaque, so the only way
    # to satisfy this clause is to actually invoke the helper. On the DEPTH path
    # the result is the depth-analysis match marker 1.
    Ensures(Implies(all_fast_facet(ToSeq(codes)) and num_surds(ToSeq(codes)) >= 1,
                    Result() == split_by_radicand_gcd(ToSeq(codes),
                                                       num_surds(ToSeq(codes)))))
    Ensures(Implies(not all_fast_facet(ToSeq(codes)), Result() == 1))
    # post-conditions-end
    # The empty match: no addend carries facet N (no nesting) AND not every
    # addend has facet E — a shallow sum with a non-eligible addend. The fast
    # path is provably NOT taken here (its precondition would be violated).
    Exsures(NoMatch,
            Acc(list_pred(codes), 1 / 2)
            and not all_fast_facet(ToSeq(codes))
            and not any_has_depth(ToSeq(codes)))
    # impl-start
    if all_fast_facet(ToSeq(codes)):
        k = num_surds(ToSeq(codes))
        return split_by_radicand_gcd(ToSeq(codes), k)
    if not any_has_depth(ToSeq(codes)):
        raise NoMatch()
    return 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: source activate; run from repo root. All artifacts in the assigned fresh scratch dir Nagini verifications launched as background jobs <=3 JVM+Z3 at a time (batches: {pos_control,atk_1,atk_2}, {atk_3,atk_4,atk_5}, {atk_6,atk_7,atk_8}).

SPEC SHAPE: match_additive's postconditions fully pin the abstract behaviour of every path. Fast path (all_fast_facet true): precondition frame-fact forces num_surds>=1, and Result()==split_by_radicand_gcd(ToSeq(codes), num_surds(ToSeq(codes))) pins the result to the OPAQUE helper output (obtainable only by actually calling the @ContractOnly helper with k==num_surds; a literal/marker cannot be proven equal). Depth path (not all_fast_facet, normal return): Result()==1. Empty-match state (not all_fast_facet and not any_has_depth): Ensures(all_fast_facet or any_has_depth) forbids normal return, and Exsures(NoMatch,...) forces NoMatch. This leaves essentially no behavioural freedom.

### ATTACKS (all same-spec: `adversary same-spec` exit 0 on all 8, spec region byte-identical):
- atk_1 (PREPATCH BUG): reverts to the loose pre-patch guard (inline loop admitting every code != 3, i.e. the non-eligible non-nested code 2 into the fast path). weakness => exit 2 NOT-A-COUNTEREXAMPLE: does NOT verify (the split_by_radicand_gcd precondition all_fast_facet(codes) is not established). Prepatch reproduced.
- atk_2 (fabricated marker on fast path: return 1 when all_fast_facet): exit 2, does NOT verify (cannot prove 1 == opaque helper output; also violates Result()!=1 chain).
- atk_3 (ungrounded literal on fast path: return 2): exit 2, does NOT verify (literal 2 cannot be proven == opaque helper output).
- atk_4 (ungrounded-oracle echo / wrong k: call helper with len(codes) instead of num_surds): exit 2, does NOT verify (violates k==num_surds precondition AND Result()==split_by_radicand_gcd(...,num_surds) postcondition).
- atk_5 (control-flow-effect: drop the NoMatch branch, return 1 for the empty-match state): exit 2, does NOT verify (Exsures(NoMatch) / Ensures(all_fast_facet or any_has_depth) violated).
- atk_6 (control-flow-effect: depth path raises NoMatch instead of returning marker 1): exit 2, does NOT verify (Ensures not all_fast_facet => Result()==1 and Exsures domain violated).
- atk_7 (boundary / wrong discriminator: guard on any_has_depth instead of all_fast_facet): exit 2, does NOT verify.
- atk_8 (CANDIDATE: behaviour-preserving branch reorder -- guard-false handled first (depth->1 / empty->NoMatch), guard-true falls through to split): weakness => exit 0 CANDIDATE (shares spec AND verifies, 13.4s). This is behaviourally IDENTICAL to the gold model impl, so its faithful refined patch IS the gold patch verbatim.

MANDATORY RESOLVE (protocol step 2) for the one verifying candidate atk_8: materialized faithful refined patch = the gold patch verbatim (patch_atk8.diff on disk). Ran through the OFFICIAL harness swebench_unified.harness.run_resolve('sympy__sympy-17318', patch, timeout=1800, retries=1) TWICE: RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. tests_status: FAIL_TO_PASS test_issue_12420 success; all 10 PASS_TO_PASS success; zero failures. => atk_8 is a correct echo whose patch RESOLVES -- NOT a verify-not-correct witness.

CONTRADICTS PRIOR RECORDED VERDICT: meta.json G-EQ (2026-08-12, the auditor) recorded 'BROKEN: atk_8.py verifies but its patch does not resolve'. That prior atk_8 is byte-identical to mine (verdict.md lines 1542-1550: the same branch reorder). Since that impl is behaviourally identical to gold, its faithful patch is the gold patch, which I re-ran and it RESOLVES (completed, all tests pass). The prior BROKEN was a false positive (likely an unfaithful hand-restructured sqrtdenest patch or a harness/timeout flake; an EARLIER verdict.md G-EQ section for the SAME cell concluded SOUND with these patches resolving). The counterexample field in the BROKEN record is literally 'None'.

REFINEMENT.MD LEG AUDIT: legs A1(R), A2(R+I), A3(A-consumed), A4(R), A5(R frame-fact). No kind-3 (unexpressible-changed-op) legs -- the changed op (guard tightening (x**2).is_Rational -> is_Rational and is_positive) is modeled DEEPLY via code_fast_facet/all_fast_facet, not hidden behind an axiom on the changed function. The only axiom is A-consumed on the UNCHANGED callee split_surds. meta.json deep_model_references=[] (no A-reference legs to audit). A-consumed correspondence grounded by G-AX (axiom_check.py exit 0, status pass): real split_surds returns normally on all-positive-rational sums with >=1 surd, RAISES IndexError on the shallow imaginary sums the old guard admitted (4+I,3+2I,5/3+I,7+I), frame fact all_fast_facet=>num_surds>=1 holds, _sqrt_match(4+I)==[] end-to-end.

CONCLUSION: 7 distinct wrong-impl attacks (partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo + prepatch) ALL rejected by verification; the only verifying same-spec impl is a behaviour-preserving echo whose materialized faithful patch RESOLVES under the official harness. Spec is not too weak. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the modeled match_additive spec vs. the real sympy._sqrt_match p.is_Add branch at base_commit d4e0231b (worktree). Checks performed: (1) model.py verifies under pinned Nagini (exit 0, 11s). (2) Spec region is the bundle's own model (byte-identical trivially). (3) Differential fuzzing of the spec's abstract outcome (MATCH-SPLIT / MATCH-DEPTH / EMPTY-NoMatch) against real _sqrt_match: heavy fuzzer ~195,653 inputs = 0 disagree / 0 frame_viol / 0 val_mismatch; targeted adversarial fuzzer ~285,697 inputs = 0 disagree / 0 frame_viol / 0 fastpath_raise; hand-picked exotic battery (deep nesting, cbrt mixes, transcendentals, imaginary surds, cancellations, symbols) all agree. (4) Frame-fact stress: 500,000 attempts to construct a multi-term Add whose addends all square to positive rationals yet has zero surds (would break all_fast_facet=>num_surds>=1 and make the fast path IndexError while the spec claims MATCH) — 0 found; such pure-rational sums auto-collapse to a Number and never reach the is_Add branch, confirming the frame fact is a genuine repo invariant. (5) On the fast path split_surds never raises when the spec predicts a match, and the abstraction of each addend to its (positive-rational-square, nested-radical) facet code correctly reproduces the post-patch guard (sq.is_Rational and sq.is_positive). No diverging input exists: the spec neither over-claims (result contents left opaque, only mechanism + helper output pinned) nor drifts from the real callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (leakage.screen: hard_failures=[], recorded status 'pass', no relaxed_leakage flag / no RELAXED_LEAKAGE.md). Verified semantically as well.

Gold discriminator: the fix tightens the fast-path guard `all((x**2).is_Rational for x in pargs)` -> `all(sq.is_Rational and sq.is_positive for sq in sqargs)` in _sqrt_match — i.e. add a POSITIVITY requirement on each addend's square so a non-positive (e.g. imaginary I, square -1) addend no longer enters split_surds and triggers the IndexError.

Public problem_statement reveals only the IndexError traceback (_sqrt_match->split_surds->_split_gcd `g=a[0]`) and 'if an expression cannot be denested it should be returned unchanged'. It does NOT reveal the concrete fix criterion (positivity of the square).

Spec view (model.py projected): the discriminator is abstracted behind an OPAQUE 'facet E (fast-path eligible)' with deliberately no positivity/rational/sign wording. Grep of the spec view confirms 'positive','rational','is_positive','imaginary','complex' all ABSENT; the only 'sign' substrings are 'signalled'/'Signals' (false positives, not numeric sign). Repo symbols split_surds/_sqrt_match/sqrtdenest/radsimp and patched file paths are ABSENT from the spec view (they live only in the audit-only mapping.md/refinement.md, which are NOT the consumer view; refinement.md §A2/§mapping.md §3 explicitly keep the model name abstract precisely to avoid the positivity leak, SPEC_GUIDE §6).

A solver reading only the spec view learns there is SOME eligibility facet E gating the fast path (consistent with the publicly-visible crash chain) but cannot reconstruct that E = 'the addend's square is a positive rational'. No gold-diff line reproduced, no diff markers, no patched path/module, no spec-view identifier embedding a patched symbol, no bug/fix narration. Leakage judged against problem_statement only, not hints_text. Nothing leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
