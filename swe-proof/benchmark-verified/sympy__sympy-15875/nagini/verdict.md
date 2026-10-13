# P2 adversarial audit — sympy__sympy-15875

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -184,7 +181,7 @@
         return None
     if z == n:
         return True
-    if nz == 0 or nz == n:
+    if nz == n:
         return None
     if sub_is_zero is None:
         return None
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -183,7 +180,7 @@
     if has2 or has5:
         return None
     if z == n:
-        return True
+        return None
     if nz == 0 or nz == n:
         return None
     if sub_is_zero is None:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -192,7 +189,7 @@
         if not im_or_z and not im:
             return True
         if im and not im_or_z:
-            return False
+            return None
         return None
     return False
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -193,6 +190,6 @@
             return True
         if im and not im_or_z:
             return False
-        return None
+        return False
     return False
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -194,5 +191,5 @@
         if im and not im_or_z:
             return False
         return None
-    return False
+    return None
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -184,7 +181,9 @@
         return None
     if z == n:
         return True
-    if nz == 0 or nz == n:
+    if nz == 0:
+        return True
+    if nz == n:
         return None
     if sub_is_zero is None:
         return None
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # the empty real-nonzero sub-expression is itself zero
     Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
         sub_is_zero is not None and sub_is_zero))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(classes), 1 / 2))
@@ -161,7 +159,6 @@
         Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
         Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
         Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = classes[i - 1]
         Assert(ToSeq(classes).drop(i - 1)[0] == c)
@@ -186,13 +183,13 @@
         return True
     if nz == 0 or nz == n:
         return None
+    if sub_is_zero is False:
+        return False
     if sub_is_zero is None:
         return None
-    if sub_is_zero:
-        if not im_or_z and not im:
-            return True
-        if im and not im_or_z:
-            return False
+    if im_or_z:
         return None
-    return False
+    if im:
+        return False
+    return True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-15875.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A commutative sum decides whether it is zero from a classification of its
  summands. Each summand falls into exactly one class:

    0  real and known-zero
    1  real and known-nonzero
    2  real with undetermined zeroness
    3  purely imaginary
    4  "imaginary-or-zero" (not classified imaginary, but i*summand is real)
    5  none of the above

  The combined verdict is a three-valued answer (``True`` = the sum is zero,
  ``False`` = the sum is provably nonzero, ``None`` = undecidable):

    * If any summand is class 2 or class 5 the sum is undecidable (``None``).
    * If every summand is class 0 the sum is zero (``True``).
    * Otherwise let ``k`` be the number of class-1 (real-nonzero) summands.
      The real-nonzero summands are themselves summed into a sub-expression
      whose three-valued zeroness is ``sub_is_zero``.
        - If there are NO real-nonzero summands, or if EVERY summand is a
          real-nonzero summand, the verdict is undecidable (``None``): in
          either case the real part carries no information that can be combined
          with the imaginary classes to settle the question.
        - Otherwise the verdict follows the zeroness of the real-nonzero
          sub-expression combined with the imaginary classes:
            sub is zero  & no imaginary class at all      -> True
            sub is zero  & some class-3 and no class-4     -> False
            sub provably nonzero                           -> False
            anything else                                  -> None

The empty sub-expression (no real-nonzero summands) is itself zero, so when
``k == 0`` the input ``sub_is_zero`` is necessarily ``True``; this is required
as a precondition linking the two inputs.

Summands are modelled as a ``List[int]`` of class tags (sympy objects and
their assumption queries are opaque to Nagini). The three-valued zeroness of an
expression is modelled as ``Optional[bool]`` (``None`` = undecided). The pure
sequence theory ``PSeq[int]`` carries the specification via front-recursive
folds (a count and an existence test over the class tags).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the opaque recursive sub-expression zeroness is
#  passed in as the three-valued parameter `sub_is_zero`; it is not a callee
#  this module names or computes.)
# axioms-end


# pure-start
@Pure
def count_eq(s: PSeq[int], c: int) -> int:
    """Number of elements of `s` equal to `c` (front-recursive fold)."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == c else 0) + count_eq(s.drop(1), c)


@Pure
def has_eq(s: PSeq[int], c: int) -> bool:
    """Whether any element of `s` equals `c` (front-recursive fold)."""
    if len(s) == 0:
        return False
    return s[0] == c or has_eq(s.drop(1), c)
# pure-end


def add_is_zero(classes: List[int], sub_is_zero: Optional[bool]) -> Optional[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(classes), 1 / 2))
    # every summand carries a class tag in 0..5
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(classes),
        0 <= classes[i] and classes[i] <= 5), [[classes[i]]])))
    # the empty real-nonzero sub-expression is itself zero
    Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
        sub_is_zero is not None and sub_is_zero))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(classes), 1 / 2))
    # an undecidable summand (class 2 or 5) forces the undecidable verdict
    Ensures(Implies(has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5),
        Result() is None))
    # all summands known-zero -> the sum is zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) == len(classes), Result() is not None and Result()))
    # no real-nonzero information, or it is the whole sum -> undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and (count_eq(ToSeq(classes), 1) == 0
             or count_eq(ToSeq(classes), 1) == len(classes)), Result() is None))
    # the discriminating clause: real-nonzero sub-expression is zero, with only
    # imaginary classes present -> the whole sum is provably nonzero (False)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and not Result()))
    # real-nonzero sub-expression is zero, with no imaginary class at all -> zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and not has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and Result()))
    # real-nonzero sub-expression provably nonzero -> the whole sum is nonzero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and not sub_is_zero,
        Result() is not None and not Result()))
    # real-nonzero sub-expression undecided -> the whole sum is undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is None,
        Result() is None))
    # real-nonzero sub-expression is zero but some imaginary-or-zero class is
    # present -> the imaginary part carries no settling information (undecidable)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 4),
        Result() is None))
    # post-conditions-end
    # impl-start
    z = 0
    nz = 0
    im = False
    im_or_z = False
    has2 = False
    has5 = False
    n = len(classes)
    i = n
    # backward scan: the suffix drop(i) aligns with the front-recursive folds,
    # so each step prepends classes[i-1] and unfolds count_eq/has_eq once.
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(classes), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(classes))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(classes),
            0 <= classes[j] and classes[j] <= 5), [[classes[j]]])))
        Invariant(z == count_eq(ToSeq(classes).drop(i), 0))
        Invariant(nz == count_eq(ToSeq(classes).drop(i), 1))
        Invariant(im == has_eq(ToSeq(classes).drop(i), 3))
        Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
        Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
        Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
        # invariants-end
        c = classes[i - 1]
        Assert(ToSeq(classes).drop(i - 1)[0] == c)
        Assert(ToSeq(classes).drop(i - 1).drop(1) == ToSeq(classes).drop(i))
        if c == 0:
            z = z + 1
        elif c == 1:
            nz = nz + 1
        elif c == 2:
            has2 = True
        elif c == 3:
            im = True
        elif c == 4:
            im_or_z = True
        else:
            has5 = True
        i = i - 1
    Assert(ToSeq(classes).drop(0) == ToSeq(classes))
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec = model.py add_is_zero(classes: List[int], sub_is_zero: Optional[bool]); the impl region (incl. loop invariants) is fully editable, only the frozen Requires/Ensures constrain attacks. The 8 postcondition clauses PARTITION the entire reachable abstract domain (no class-2/5; z==n; nz==0|nz==n; and the four 0<nz<n cases keyed on sub_is_zero and the imaginary flags) — every outcome is positively pinned by exactly one clause, so no verifying impl can diverge from gold on any reachable input.

SBU_BENCHMARK_DIR=benchmark-verified. Ran from real root.

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`; cmd: `PY -m swebench_unified.adversary weakness nagini sympy__sympy-15875 <path>`):
- atk_1.py PREPATCH BUG (drop the nz==0 disjunct: `if nz == n: return None`) -> w1.log NOT-A-COUNTEREXAMPLE, does not verify (EXIT=2). Spec senses the change (G-DIFF).
- atk_2.py boundary: z==n -> None instead of True (violates all-zero clause) -> does not verify (EXIT=2).
- atk_3.py clause-4 flip: sub true & im-only -> None instead of False -> does not verify (EXIT=2).
- atk_4.py clause-8 flip (ungrounded-oracle echo): sub true & class-4 present -> False instead of None -> does not verify (EXIT=2).
- atk_5.py partial-domain: sub provably-nonzero -> None instead of False -> does not verify (EXIT=2).
- atk_6.py control-flow-effect: exploit empty-nz precondition, nz==0 -> True instead of None -> does not verify (EXIT=2).
- atk_7.py ECHO: behaviorally IDENTICAL to gold, restructured branch order (checks `sub is False`/`sub is None`/im_or_z/im). -> w7.log CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (20.1s, EXIT=0). Exhaustively equal to gold across all 377 reachable (counts,sub) states (Python enumeration, 0 diffs).

POSITIVE CONTROL: positive_control.py = verbatim gold impl -> `bash scripts/nagini_verify.sh` Verification successful (18.9s, exit 0).

MANDATORY RESOLVE (protocol step 2): atk_7 is the only CANDIDATE, so I materialized its faithful refined patch (atk7_patch.diff) mapping the restructured decision back onto base_commit _eval_is_zero (base source extracted from prebuilt image sweb.eval.x86_64.sympy_1776_sympy-15875:latest, pulled via mirror.gcr.io + retag). `git apply --check` APPLIES_CLEAN in-container. Ran run_resolve(sympy__sympy-15875, atk7_patch, timeout=1800): resolved=True, completed=True, note='resolved', flaky=False. Verify => resolve holds; NOT a weakness (echo of gold, per the 2026-08-06 panel_1/eq policy).

REFINEMENT.MD AUDIT (plan §4): legs A1(R), A2(I+R), A3(R), A4(I+R), A5(I+R — the patched line `len(nz)==0 or len(nz)==len(self.args)` modeled IDENTICALLY as `nz==0 or nz==n`), A6(R+A-reference), A7(R). NO kind-3 (unexpressible-changed-op) legs: the one op that changed is an integer comparison, modeled identically. NO A-consumed axioms — axioms region is empty (comment only); the sole opaque value `b.is_zero` (b=self.func(*nz)) is the UNCHANGED recursive assumption query entering as parameter sub_is_zero, an A-reference validated by axiom_check.py (G-AX), not an axiom the proof's Ensures quantify over. A-REFERENCE FIDELITY VERIFIED: (i) axiom_check.py's Python model() is exactly equivalent to model.py add_is_zero across all 3103 reachable class-tag lists (len<=4), 0 diffs; (ii) base+patched source confirms b=self.func(*nz), `if b.is_zero`/`if b.is_zero is False` branch structure ↔ model's is-None/truthy/falsy branches; (iii) A7 precondition count_eq(classes,1)==0 => sub_is_zero==True matches self.func()==S.Zero, S.Zero.is_zero is True.

CONCLUSION: 6 distinct wrong impls (prepatch + boundary + clause-flip + partial-domain + control-flow + ungrounded-oracle) all REJECTED by the spec; the 1 verifying candidate is a behavioral echo whose faithful patch RESOLVES under the official harness. No verify⇏correct gap found. All required verifications and the resolve run completed. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-15875.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A commutative sum decides whether it is zero from a classification of its
  summands. Each summand falls into exactly one class:

    0  real and known-zero
    1  real and known-nonzero
    2  real with undetermined zeroness
    3  purely imaginary
    4  "imaginary-or-zero" (not classified imaginary, but i*summand is real)
    5  none of the above

  The combined verdict is a three-valued answer (``True`` = the sum is zero,
  ``False`` = the sum is provably nonzero, ``None`` = undecidable):

    * If any summand is class 2 or class 5 the sum is undecidable (``None``).
    * If every summand is class 0 the sum is zero (``True``).
    * Otherwise let ``k`` be the number of class-1 (real-nonzero) summands.
      The real-nonzero summands are themselves summed into a sub-expression
      whose three-valued zeroness is ``sub_is_zero``.
        - If there are NO real-nonzero summands, or if EVERY summand is a
          real-nonzero summand, the verdict is undecidable (``None``): in
          either case the real part carries no information that can be combined
          with the imaginary classes to settle the question.
        - Otherwise the verdict follows the zeroness of the real-nonzero
          sub-expression combined with the imaginary classes:
            sub is zero  & no imaginary class at all      -> True
            sub is zero  & some class-3 and no class-4     -> False
            sub provably nonzero                           -> False
            anything else                                  -> None

The empty sub-expression (no real-nonzero summands) is itself zero, so when
``k == 0`` the input ``sub_is_zero`` is necessarily ``True``; this is required
as a precondition linking the two inputs.

Summands are modelled as a ``List[int]`` of class tags (sympy objects and
their assumption queries are opaque to Nagini). The three-valued zeroness of an
expression is modelled as ``Optional[bool]`` (``None`` = undecided). The pure
sequence theory ``PSeq[int]`` carries the specification via front-recursive
folds (a count and an existence test over the class tags).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the opaque recursive sub-expression zeroness is
#  passed in as the three-valued parameter `sub_is_zero`; it is not a callee
#  this module names or computes.)
# axioms-end


# pure-start
@Pure
def count_eq(s: PSeq[int], c: int) -> int:
    """Number of elements of `s` equal to `c` (front-recursive fold)."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == c else 0) + count_eq(s.drop(1), c)


@Pure
def has_eq(s: PSeq[int], c: int) -> bool:
    """Whether any element of `s` equals `c` (front-recursive fold)."""
    if len(s) == 0:
        return False
    return s[0] == c or has_eq(s.drop(1), c)
# pure-end


def add_is_zero(classes: List[int], sub_is_zero: Optional[bool]) -> Optional[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(classes), 1 / 2))
    # every summand carries a class tag in 0..5
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(classes),
        0 <= classes[i] and classes[i] <= 5), [[classes[i]]])))
    # the empty real-nonzero sub-expression is itself zero
    Requires(Implies(count_eq(ToSeq(classes), 1) == 0,
        sub_is_zero is not None and sub_is_zero))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(classes), 1 / 2))
    # an undecidable summand (class 2 or 5) forces the undecidable verdict
    Ensures(Implies(has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5),
        Result() is None))
    # all summands known-zero -> the sum is zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) == len(classes), Result() is not None and Result()))
    # no real-nonzero information, or it is the whole sum -> undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and (count_eq(ToSeq(classes), 1) == 0
             or count_eq(ToSeq(classes), 1) == len(classes)), Result() is None))
    # the discriminating clause: real-nonzero sub-expression is zero, with only
    # imaginary classes present -> the whole sum is provably nonzero (False)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and not Result()))
    # real-nonzero sub-expression is zero, with no imaginary class at all -> zero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and not has_eq(ToSeq(classes), 3) and not has_eq(ToSeq(classes), 4),
        Result() is not None and Result()))
    # real-nonzero sub-expression provably nonzero -> the whole sum is nonzero
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and not sub_is_zero,
        Result() is not None and not Result()))
    # real-nonzero sub-expression undecided -> the whole sum is undecidable
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is None,
        Result() is None))
    # real-nonzero sub-expression is zero but some imaginary-or-zero class is
    # present -> the imaginary part carries no settling information (undecidable)
    Ensures(Implies(not (has_eq(ToSeq(classes), 2) or has_eq(ToSeq(classes), 5))
        and count_eq(ToSeq(classes), 0) != len(classes)
        and count_eq(ToSeq(classes), 1) != 0
        and count_eq(ToSeq(classes), 1) != len(classes)
        and sub_is_zero is not None and sub_is_zero
        and has_eq(ToSeq(classes), 4),
        Result() is None))
    # post-conditions-end
    # impl-start
    z = 0
    nz = 0
    im = False
    im_or_z = False
    has2 = False
    has5 = False
    n = len(classes)
    i = n
    # backward scan: the suffix drop(i) aligns with the front-recursive folds,
    # so each step prepends classes[i-1] and unfolds count_eq/has_eq once.
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(classes), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(classes))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(classes),
            0 <= classes[j] and classes[j] <= 5), [[classes[j]]])))
        Invariant(z == count_eq(ToSeq(classes).drop(i), 0))
        Invariant(nz == count_eq(ToSeq(classes).drop(i), 1))
        Invariant(im == has_eq(ToSeq(classes).drop(i), 3))
        Invariant(im_or_z == has_eq(ToSeq(classes).drop(i), 4))
        Invariant(has2 == has_eq(ToSeq(classes).drop(i), 2))
        Invariant(has5 == has_eq(ToSeq(classes).drop(i), 5))
        # invariants-end
        c = classes[i - 1]
        Assert(ToSeq(classes).drop(i - 1)[0] == c)
        Assert(ToSeq(classes).drop(i - 1).drop(1) == ToSeq(classes).drop(i))
        if c == 0:
            z = z + 1
        elif c == 1:
            nz = nz + 1
        elif c == 2:
            has2 = True
        elif c == 3:
            im = True
        elif c == 4:
            im_or_z = True
        else:
            has5 = True
        i = i - 1
    Assert(ToSeq(classes).drop(0) == ToSeq(classes))
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec = model.py add_is_zero(classes: List[int], sub_is_zero: Optional[bool]); the impl region (incl. loop invariants) is fully editable, only the frozen Requires/Ensures constrain attacks. The 8 postcondition clauses PARTITION the entire reachable abstract domain (no class-2/5; z==n; nz==0|nz==n; and the four 0<nz<n cases keyed on sub_is_zero and the imaginary flags) — every outcome is positively pinned by exactly one clause, so no verifying impl can diverge from gold on any reachable input.

SBU_BENCHMARK_DIR=benchmark-verified. Ran from real root.

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`; cmd: `PY -m swebench_unified.adversary weakness nagini sympy__sympy-15875 <path>`):
- atk_1.py PREPATCH BUG (drop the nz==0 disjunct: `if nz == n: return None`) -> w1.log NOT-A-COUNTEREXAMPLE, does not verify (EXIT=2). Spec senses the change (G-DIFF).
- atk_2.py boundary: z==n -> None instead of True (violates all-zero clause) -> does not verify (EXIT=2).
- atk_3.py clause-4 flip: sub true & im-only -> None instead of False -> does not verify (EXIT=2).
- atk_4.py clause-8 flip (ungrounded-oracle echo): sub true & class-4 present -> False instead of None -> does not verify (EXIT=2).
- atk_5.py partial-domain: sub provably-nonzero -> None instead of False -> does not verify (EXIT=2).
- atk_6.py control-flow-effect: exploit empty-nz precondition, nz==0 -> True instead of None -> does not verify (EXIT=2).
- atk_7.py ECHO: behaviorally IDENTICAL to gold, restructured branch order (checks `sub is False`/`sub is None`/im_or_z/im). -> w7.log CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (20.1s, EXIT=0). Exhaustively equal to gold across all 377 reachable (counts,sub) states (Python enumeration, 0 diffs).

POSITIVE CONTROL: positive_control.py = verbatim gold impl -> `bash scripts/nagini_verify.sh` Verification successful (18.9s, exit 0).

MANDATORY RESOLVE (protocol step 2): atk_7 is the only CANDIDATE, so I materialized its faithful refined patch (atk7_patch.diff) mapping the restructured decision back onto base_commit _eval_is_zero (base source extracted from prebuilt image sweb.eval.x86_64.sympy_1776_sympy-15875:latest, pulled via mirror.gcr.io + retag). `git apply --check` APPLIES_CLEAN in-container. Ran run_resolve(sympy__sympy-15875, atk7_patch, timeout=1800): resolved=True, completed=True, note='resolved', flaky=False. Verify => resolve holds; NOT a weakness (echo of gold, per the 2026-08-06 panel_1/eq policy).

REFINEMENT.MD AUDIT (plan §4): legs A1(R), A2(I+R), A3(R), A4(I+R), A5(I+R — the patched line `len(nz)==0 or len(nz)==len(self.args)` modeled IDENTICALLY as `nz==0 or nz==n`), A6(R+A-reference), A7(R). NO kind-3 (unexpressible-changed-op) legs: the one op that changed is an integer comparison, modeled identically. NO A-consumed axioms — axioms region is empty (comment only); the sole opaque value `b.is_zero` (b=self.func(*nz)) is the UNCHANGED recursive assumption query entering as parameter sub_is_zero, an A-reference validated by axiom_check.py (G-AX), not an axiom the proof's Ensures quantify over. A-REFERENCE FIDELITY VERIFIED: (i) axiom_check.py's Python model() is exactly equivalent to model.py add_is_zero across all 3103 reachable class-tag lists (len<=4), 0 diffs; (ii) base+patched source confirms b=self.func(*nz), `if b.is_zero`/`if b.is_zero is False` branch structure ↔ model's is-None/truthy/falsy branches; (iii) A7 precondition count_eq(classes,1)==0 => sub_is_zero==True matches self.func()==S.Zero, S.Zero.is_zero is True.

CONCLUSION: 6 distinct wrong impls (prepatch + boundary + clause-flip + partial-domain + control-flow + ungrounded-oracle) all REJECTED by the spec; the 1 verifying candidate is a behavioral echo whose faithful patch RESOLVES under the official harness. No verify⇏correct gap found. All required verifications and the resolve run completed. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No faithfulness break found. Worktree at correct base_commit b506169ad7 with gold patch applied; real Add._eval_is_zero matches the routine modeled in model.py/mapping.md. model.py verifies against its frozen spec (Nagini: 'Verification successful', 18.2s). The abstraction maps each summand to a class tag 0..5 recording which accumulator the real loop touches (0 real-zero/z, 1 real-nonzero/nz, 2 real-undetermined -> bare return None, 3 imaginary/im, 4 imag-or-zero/im_or_z, 5 other -> bare return None), and carries the unchanged recursive query b.is_zero (b=self.func(*nz)) as the parameter sub_is_zero. The bare-return classes (2/5) yield None regardless of order, faithfully modeled by post-loop has2/has5 tests. The precondition count_eq(classes,1)==0 => sub_is_zero is True is sound because empty nz gives b=self.func()=S.Zero whose is_zero is True. G-AX (axiom_check.py) run against the patched worktree passes cleanly: issue witness -2*I+(1+I)**2 -> None on both model and real routine, plus 400 boundary + 15105 fuzz Add expressions (sub_is_zero distribution {None:3809,True:3370,False:7926}). I additionally ran an INDEPENDENT, broader differential fuzz of 60,000 cases (adding negative reals, complex symbols, zero=True symbols, irrational reals/imaginaries sqrt(2)*I, order variations, up to 6 summands) comparing model(classes,sub_is_zero) to the live patched _eval_is_zero via the exact observe() abstraction: ZERO divergences. The one patched line (len(nz)==0 or len(nz)==len(self.args)) is an integer comparison modeled identically (nz==0 or nz==n). The postconditions partition the reachable domain and each three-valued outcome is pinned to match the routine. Spec is faithful, neither too strong nor drifting from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the nagini spec_view of model.py) passes clean: no diff markers, no reproduced gold-patch line, no patched file/module path (add.py / sympy.core.add), no spec-view identifier or comment naming a patched repo symbol (_eval_is_zero), no bug/fix narration. No RELAXED_LEAKAGE deferral in play (relaxed_leakage flag unset) and none needed.

Gold edit: single line add.py:557, `if len(nz) == len(self.args):` -> `if len(nz) == 0 or len(nz) == len(self.args):` (add the len(nz)==0 disjunct so a commutative sum with no real-nonzero summands, e.g. -2*I + (1+I)**2, returns None instead of a wrong False).

Public problem_statement ALREADY discloses the desired behavior: (-2*I + (1+I)**2).is_zero returns False but should return None; release note 'Fix is_zero becoming False on some expressions with Add.' So the target outcome (wrong-False -> None on such Add sums) is public.

Spec view (docstring + pure + pre/post-conditions; impl region elided) is a FORMALIZATION over an abstract class-tag carrier (classes: List[int] in 0..5, sub_is_zero: Optional[bool]) of that publicly-stated goal. The discriminating postcondition (count_eq(classes,1)==0 => Result() is None) and docstring 'If there are NO real-nonzero summands ... the verdict is undecidable (None)' encode exactly the public target behavior, not the mechanical edit. The diff-quoting content (add.py:557, nz, self.args, the gold hunk) lives only in mapping.md/refinement.md, which are NOT part of the spec view. A complete three-valued decision table is intrinsically required for a verifiable spec and reveals nothing about HOW the sympy routine is edited (consumer fills model.py's impl region, not the repo patch). No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
