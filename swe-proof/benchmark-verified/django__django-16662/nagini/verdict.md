# P2 adversarial audit — django__django-16662

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -102,23 +100,36 @@
     k0 = compkey(flags[0], modules[0])
     k1 = compkey(flags[1], modules[1])
     k2 = compkey(flags[2], modules[2])
+    m0 = modules[0]
+    m1 = modules[1]
+    m2 = modules[2]
     x = k0
     y = k1
     z = k2
-    if x > y:
+    mx = m0
+    my = m1
+    mz = m2
+    if mx > my:
         t = x
         x = y
         y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if y > z:
+        tm = mx
+        mx = my
+        my = tm
+    if my > mz:
         t2 = y
         y = z
         z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if x > y:
+        tm2 = my
+        my = mz
+        mz = tm2
+    if mx > my:
         t3 = x
         x = y
         y = t3
+        tm3 = mx
+        mx = my
+        my = tm3
     Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     res = [x, y, z]  # type: List[int]
     Assert(ToSeq(res) == PSeq(x, y, z))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -102,25 +100,6 @@
     k0 = compkey(flags[0], modules[0])
     k1 = compkey(flags[1], modules[1])
     k2 = compkey(flags[2], modules[2])
-    x = k0
-    y = k1
-    z = k2
-    if x > y:
-        t = x
-        x = y
-        y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if y > z:
-        t2 = y
-        y = z
-        z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if x > y:
-        t3 = x
-        x = y
-        y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
+    res = [k0, k1, k2]  # type: List[int]
     return res
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -109,18 +107,14 @@
         t = x
         x = y
         y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     if y > z:
         t2 = y
         y = z
         z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     if x > y:
         t3 = x
         x = y
         y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
+    res = [z, y, x]  # type: List[int]
     return res
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -102,25 +100,36 @@
     k0 = compkey(flags[0], modules[0])
     k1 = compkey(flags[1], modules[1])
     k2 = compkey(flags[2], modules[2])
+    f0 = flags[0]
+    f1 = flags[1]
+    f2 = flags[2]
     x = k0
     y = k1
     z = k2
-    if x > y:
+    fx = f0
+    fy = f1
+    fz = f2
+    if fx > fy:
         t = x
         x = y
         y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if y > z:
+        tf = fx
+        fx = fy
+        fy = tf
+    if fy > fz:
         t2 = y
         y = z
         z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if x > y:
+        tf2 = fy
+        fy = fz
+        fz = tf2
+    if fx > fy:
         t3 = x
         x = y
         y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
+        tf3 = fx
+        fx = fy
+        fy = tf3
     res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
     return res
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -109,18 +107,10 @@
         t = x
         x = y
         y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     if y > z:
         t2 = y
         y = z
         z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if x > y:
-        t3 = x
-        x = y
-        y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
     return res
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -102,25 +100,6 @@
     k0 = compkey(flags[0], modules[0])
     k1 = compkey(flags[1], modules[1])
     k2 = compkey(flags[2], modules[2])
-    x = k0
-    y = k1
-    z = k2
-    if x > y:
-        t = x
-        x = y
-        y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if y > z:
-        t2 = y
-        y = z
-        z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    if x > y:
-        t3 = x
-        x = y
-        y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
+    res = [0, 500000000, 1000000000]  # type: List[int]
     return res
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
              flags[k] == 0 or flags[k] == 1)))
     Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
              0 <= modules[k] and modules[k] < 1000000000)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(flags), 1 / 2))
@@ -109,18 +107,14 @@
         t = x
         x = y
         y = t
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     if y > z:
         t2 = y
         y = z
         z = t2
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
     if x > y:
         t3 = x
         x = y
         y = t3
-    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
-    res = [x, y, z]  # type: List[int]
-    Assert(ToSeq(res) == PSeq(x, y, z))
+    res = [x, x, z]  # type: List[int]
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16662.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of import lines is arranged into the order they should appear in
  a generated source file. Two attributes of each line decide its position:

    * whether the line is a plain module import (``import X``) or an
      object import drawn from a module (``from Y import ...``); and
    * the name of the module the line refers to.

  The required order places EVERY plain module-import line before EVERY
  from-import line (the two forms are grouped, plain imports first), and within
  each group the lines are ordered by their module name. Equivalently, the lines
  are ordered ascending by the pair (is-a-from-import, module-name), the group
  flag being the PRIMARY ordering criterion and the module name the secondary
  one. The arrangement is a rearrangement of exactly the given lines (no line is
  added, dropped, or duplicated).

  The discriminating case the contract pins: a from-import line whose module
  name sorts BEFORE a plain module-import line's module name must still appear
  AFTER that plain import line, because the group flag dominates the module
  name. Ordering by module name alone would interleave the two groups and is
  rejected.

Each line is characterised by two integers: a group flag in {0, 1} (0 = plain
module import, 1 = from-import) and an order-preserving integer code of the
module-name sort token (Nagini bans ``str`` indexing; the code preserves the
lexicographic ordering of the module names, see mapping.md). The pair is
linearised into a single ordering key ``compkey`` whose ascending integer order
is exactly the ascending order of the pair (group flag dominating). The
specification is carried over the pure sequence/multiset theory (``PSeq`` /
``ToMS``). The modelled domain is the three-line configuration that exhibits the
behaviour (see mapping.md / refinement.md for the domain choice); the ordering
is produced by a comparison arrangement pinned to be a sorted rearrangement.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the ordering key is the changed decision and is
# modelled deeply as the linearised pair `compkey`. The comparison sort the
# real code performs is the standard library `sorted`; that the ascending order
# of `compkey` agrees with the ascending order of the real pair key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom.)
# axioms-end


# pure-start
@Pure
def compkey(is_from: int, module: int) -> int:
    """The single ordering key for a line, linearising the pair
    (group flag, module code). The group flag is scaled by a bound strictly
    larger than any module code, so ascending integer order on `compkey` is
    exactly ascending order on the pair with the group flag dominating: every
    plain-import line (flag 0) keys below every from-import line (flag 1)
    regardless of module code, and within a group the module code decides."""
    Ensures(Result() == is_from * 1000000000 + module)
    return is_from * 1000000000 + module
# pure-end


def arrange_lines(flags: List[int], modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `flags[k]` is the group flag of line k (0 = plain import, 1 = from-import);
    # `modules[k]` is the order-preserving code of line k's module name, bounded
    # below the group scale so the linearisation is order-preserving. Both
    # carriers are read-only (fractional permission: arranging never mutates the
    # line attributes).
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    Requires(len(flags) == 3 and len(modules) == 3)
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             flags[k] == 0 or flags[k] == 1)))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             0 <= modules[k] and modules[k] < 1000000000)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(len(flags) == 3 and len(modules) == 3)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 3)
    # The output is a rearrangement of EXACTLY the given lines' keys: no key is
    # added, dropped, or duplicated (grounds the result in the actual input).
    Ensures(ToMS(ToSeq(Result())) == ToMS(PSeq(
        compkey(flags[0], modules[0]),
        compkey(flags[1], modules[1]),
        compkey(flags[2], modules[2]))))
    # The output is ascending in the ordering key: by `compkey`'s construction
    # this places every plain-import line before every from-import line, and
    # orders by module name within each group.
    Ensures(Result()[0] <= Result()[1] and Result()[1] <= Result()[2])
    # post-conditions-end
    # impl-start
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) for django__django-16662 nagini bundle. verifier via python -m swebench_unified.adversary.

Spec shape: arrange_lines over a FIXED 3-line domain; postcondition requires BOTH ToMS(ToSeq(Result))==ToMS(input compkeys) (multiset-preserving) AND Result[0]<=Result[1]<=Result[2] (ascending in compkey). Multiset-preservation + total ascending order on a 3-element domain uniquely determines the output sequence => the spec is tight, so no wrong arrangement can verify. compkey(is_from,module)=is_from*1e9+module (flag-dominating linearisation).

ATTACKS (all copied from model.py editing ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical; all confirmed same-spec exit 0 via `same-spec`, all verified via `weakness nagini django__django-16662 <file>`):
- atk_1 PREPATCH bug (module-only bubble sort, ignores group flag): same-spec SAME; weakness exit=2 NOT-A-COUNTEREXAMPLE (verification FAILED) -> prepatch reproduced. On F2P config a from-line (small module code) precedes a plain import with larger code => not ascending in compkey.
- atk_2 IDENTITY (return [k0,k1,k2] unsorted): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_3 DESCENDING (sort then return [z,y,x]): boundary; same-spec SAME; weakness exit=2 (FAILED verify).
- atk_4 FLAG-ONLY sort (sort by flags[k] only, ignore module code within group): boundary; same-spec SAME; weakness exit=2 (FAILED verify).
- atk_5 PARTIAL / control-flow-effect (bubble missing the final x>y compare, leaves x,y possibly unsorted): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_6 UNGROUNDED-ORACLE ECHO (return hardcoded [0,5e8,1e9], ascending but not derived from input => breaks ToMS): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_7 MULTISET-BREAK (correct ascending sort but return [x,x,z], duplicates smallest & drops middle): same-spec SAME; weakness exit=2 (FAILED verify).

POSITIVE CONTROL: pos_control.py = frozen model.py verbatim; weakness exit=0 CANDIDATE-COUNTEREXAMPLE line means it shares-spec AND VERIFIES => correct impl verifies as required. Confirms the verifier is live (not vacuously failing everything).

No attack returned CANDIDATE (exit 0). Since a CANDIDATE requires shares-spec AND verifies, and every wrong impl FAILED verification, there is no verifying wrong impl whose faithful refined patch could be materialized and run through run_resolve. patches={} accordingly; no resolve run was needed or possible to exhibit verify=>!correct. (Protocol: resolve runs are mandated only FOR verifying CANDIDATES; none exist.)

Schedule: verification commands run concurrently in background batches of 3 (pos_control+atk_1+atk_2), (atk_3+atk_4+atk_5), (atk_6+atk_7) — each nagini check spawns JVM+Z3; pass criteria unchanged.

REFINEMENT.md A-leg audit (R/I legs are G-CONF's remit):
- A1 (import-str <-> (flag,module) pair): R. OK.
- A2 (compkey linearisation <-> tuple key (i.split()[0]=='from', i.split()[1])): R + A-REFERENCE. Re-ran axiom_check.py (G-AX): exit 0. It validates (part1) ascending compkey == ascending real tuple key over 24 boundary pairs + 2000 fuzz, (part2) real CPython sorted(gold_key) == ascending-compkey model order over 8 boundary + 5000 fuzz configs incl. the F2P config, and (control) the pre-fix key i.split()[1] yields the rejected interleaving. gold_key in axiom_check.py = (i.split()[0]=='from', i.split()[1]) is VERBATIM the patch.diff sort key (writer.py:178 post-patch); compkey = is_from*1e9+module is VERBATIM model.py. A-reference correspondence to the real callee holds.
- A3 (sorted == ascending-permutation arrangement): I. Keys distinct => unique permutation; stability unobservable. OK.
- A4 (\n.join + template fill unchanged): I/omitted. OK.
- refinement.md §B: no @ContractOnly / no A-consumed row — confirmed (model.py axioms region is a comment only). §C: no kind-3 legs — confirmed; the one changed op (ordering key gaining primary flag component) is modeled DEEPLY in compkey, not hidden behind an axiom.

Gold patch.diff (benchmark-verified/django__django-16662/patch.diff) is the one-line sort-key change and is the G-RESOLVE oracle; nothing to resolve-run here since no CANDIDATE.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; positive control verifies; prepatch reproduced; A-reference (G-AX) sound; refinement legs all R/A-reference/I with no kind-3. No verifying wrong impl exists, so verify=>correct is not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16662.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of import lines is arranged into the order they should appear in
  a generated source file. Two attributes of each line decide its position:

    * whether the line is a plain module import (``import X``) or an
      object import drawn from a module (``from Y import ...``); and
    * the name of the module the line refers to.

  The required order places EVERY plain module-import line before EVERY
  from-import line (the two forms are grouped, plain imports first), and within
  each group the lines are ordered by their module name. Equivalently, the lines
  are ordered ascending by the pair (is-a-from-import, module-name), the group
  flag being the PRIMARY ordering criterion and the module name the secondary
  one. The arrangement is a rearrangement of exactly the given lines (no line is
  added, dropped, or duplicated).

  The discriminating case the contract pins: a from-import line whose module
  name sorts BEFORE a plain module-import line's module name must still appear
  AFTER that plain import line, because the group flag dominates the module
  name. Ordering by module name alone would interleave the two groups and is
  rejected.

Each line is characterised by two integers: a group flag in {0, 1} (0 = plain
module import, 1 = from-import) and an order-preserving integer code of the
module-name sort token (Nagini bans ``str`` indexing; the code preserves the
lexicographic ordering of the module names, see mapping.md). The pair is
linearised into a single ordering key ``compkey`` whose ascending integer order
is exactly the ascending order of the pair (group flag dominating). The
specification is carried over the pure sequence/multiset theory (``PSeq`` /
``ToMS``). The modelled domain is the three-line configuration that exhibits the
behaviour (see mapping.md / refinement.md for the domain choice); the ordering
is produced by a comparison arrangement pinned to be a sorted rearrangement.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the ordering key is the changed decision and is
# modelled deeply as the linearised pair `compkey`. The comparison sort the
# real code performs is the standard library `sorted`; that the ascending order
# of `compkey` agrees with the ascending order of the real pair key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom.)
# axioms-end


# pure-start
@Pure
def compkey(is_from: int, module: int) -> int:
    """The single ordering key for a line, linearising the pair
    (group flag, module code). The group flag is scaled by a bound strictly
    larger than any module code, so ascending integer order on `compkey` is
    exactly ascending order on the pair with the group flag dominating: every
    plain-import line (flag 0) keys below every from-import line (flag 1)
    regardless of module code, and within a group the module code decides."""
    Ensures(Result() == is_from * 1000000000 + module)
    return is_from * 1000000000 + module
# pure-end


def arrange_lines(flags: List[int], modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `flags[k]` is the group flag of line k (0 = plain import, 1 = from-import);
    # `modules[k]` is the order-preserving code of line k's module name, bounded
    # below the group scale so the linearisation is order-preserving. Both
    # carriers are read-only (fractional permission: arranging never mutates the
    # line attributes).
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    Requires(len(flags) == 3 and len(modules) == 3)
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             flags[k] == 0 or flags[k] == 1)))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             0 <= modules[k] and modules[k] < 1000000000)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(len(flags) == 3 and len(modules) == 3)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 3)
    # The output is a rearrangement of EXACTLY the given lines' keys: no key is
    # added, dropped, or duplicated (grounds the result in the actual input).
    Ensures(ToMS(ToSeq(Result())) == ToMS(PSeq(
        compkey(flags[0], modules[0]),
        compkey(flags[1], modules[1]),
        compkey(flags[2], modules[2]))))
    # The output is ascending in the ordering key: by `compkey`'s construction
    # this places every plain-import line before every from-import line, and
    # orders by module name within each group.
    Ensures(Result()[0] <= Result()[1] and Result()[1] <= Result()[2])
    # post-conditions-end
    # impl-start
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if y > z:
        t2 = y
        y = z
        z = t2
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    if x > y:
        t3 = x
        x = y
        y = t3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) for django__django-16662 nagini bundle. verifier via python -m swebench_unified.adversary.

Spec shape: arrange_lines over a FIXED 3-line domain; postcondition requires BOTH ToMS(ToSeq(Result))==ToMS(input compkeys) (multiset-preserving) AND Result[0]<=Result[1]<=Result[2] (ascending in compkey). Multiset-preservation + total ascending order on a 3-element domain uniquely determines the output sequence => the spec is tight, so no wrong arrangement can verify. compkey(is_from,module)=is_from*1e9+module (flag-dominating linearisation).

ATTACKS (all copied from model.py editing ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical; all confirmed same-spec exit 0 via `same-spec`, all verified via `weakness nagini django__django-16662 <file>`):
- atk_1 PREPATCH bug (module-only bubble sort, ignores group flag): same-spec SAME; weakness exit=2 NOT-A-COUNTEREXAMPLE (verification FAILED) -> prepatch reproduced. On F2P config a from-line (small module code) precedes a plain import with larger code => not ascending in compkey.
- atk_2 IDENTITY (return [k0,k1,k2] unsorted): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_3 DESCENDING (sort then return [z,y,x]): boundary; same-spec SAME; weakness exit=2 (FAILED verify).
- atk_4 FLAG-ONLY sort (sort by flags[k] only, ignore module code within group): boundary; same-spec SAME; weakness exit=2 (FAILED verify).
- atk_5 PARTIAL / control-flow-effect (bubble missing the final x>y compare, leaves x,y possibly unsorted): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_6 UNGROUNDED-ORACLE ECHO (return hardcoded [0,5e8,1e9], ascending but not derived from input => breaks ToMS): same-spec SAME; weakness exit=2 (FAILED verify).
- atk_7 MULTISET-BREAK (correct ascending sort but return [x,x,z], duplicates smallest & drops middle): same-spec SAME; weakness exit=2 (FAILED verify).

POSITIVE CONTROL: pos_control.py = frozen model.py verbatim; weakness exit=0 CANDIDATE-COUNTEREXAMPLE line means it shares-spec AND VERIFIES => correct impl verifies as required. Confirms the verifier is live (not vacuously failing everything).

No attack returned CANDIDATE (exit 0). Since a CANDIDATE requires shares-spec AND verifies, and every wrong impl FAILED verification, there is no verifying wrong impl whose faithful refined patch could be materialized and run through run_resolve. patches={} accordingly; no resolve run was needed or possible to exhibit verify=>!correct. (Protocol: resolve runs are mandated only FOR verifying CANDIDATES; none exist.)

Schedule: verification commands run concurrently in background batches of 3 (pos_control+atk_1+atk_2), (atk_3+atk_4+atk_5), (atk_6+atk_7) — each nagini check spawns JVM+Z3; pass criteria unchanged.

REFINEMENT.md A-leg audit (R/I legs are G-CONF's remit):
- A1 (import-str <-> (flag,module) pair): R. OK.
- A2 (compkey linearisation <-> tuple key (i.split()[0]=='from', i.split()[1])): R + A-REFERENCE. Re-ran axiom_check.py (G-AX): exit 0. It validates (part1) ascending compkey == ascending real tuple key over 24 boundary pairs + 2000 fuzz, (part2) real CPython sorted(gold_key) == ascending-compkey model order over 8 boundary + 5000 fuzz configs incl. the F2P config, and (control) the pre-fix key i.split()[1] yields the rejected interleaving. gold_key in axiom_check.py = (i.split()[0]=='from', i.split()[1]) is VERBATIM the patch.diff sort key (writer.py:178 post-patch); compkey = is_from*1e9+module is VERBATIM model.py. A-reference correspondence to the real callee holds.
- A3 (sorted == ascending-permutation arrangement): I. Keys distinct => unique permutation; stability unobservable. OK.
- A4 (\n.join + template fill unchanged): I/omitted. OK.
- refinement.md §B: no @ContractOnly / no A-consumed row — confirmed (model.py axioms region is a comment only). §C: no kind-3 legs — confirmed; the one changed op (ordering key gaining primary flag component) is modeled DEEPLY in compkey, not hidden behind an axiom.

Gold patch.diff (benchmark-verified/django__django-16662/patch.diff) is the one-line sort-key change and is the G-RESOLVE oracle; nothing to resolve-run here since no CANDIDATE.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; positive control verifies; prepatch reproduced; A-reference (G-AX) sound; refinement legs all R/A-reference/I with no kind-3. No verifying wrong impl exists, so verify=>correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-16662 nagini bundle.

### MACHINE CHECKS (all green):
- nagini_verify.sh on model.py: exit 0, 14.33s (spec verifies).
- axiom_check.py (G-AX): exit 0 — compkey linearisation == real tuple key over 24 boundary pairs + 2000 fuzz; real sorted(gold_key) == ascending-compkey model order over 8 boundary + 5000 fuzz configs; pre-fix key confirmed to interleave.
- adversary same-spec: SAME (exit 0) — spec region byte-identical to the bundle.

REAL CALLEE: sorted(imports, key=lambda i: (i.split()[0]=='from', i.split()[1])) at django/db/migrations/writer.py:178 (gold patch). Orders import-line strings by the tuple (bool group-flag PRIMARY, module-token str SECONDARY).

MODELED FUNCTION: arrange_lines pinned by its postcondition to a multiset-preserving, ascending-by-compkey rearrangement of exactly the three input keys, with compkey(f,m)=f*1e9+m and precondition 0<=module<1e9, flag in {0,1}.

FIDELITY: With 0<=module<1e9 the linearisation is order-preserving and the group flag dominates (flag-0 lines key strictly below flag-1 lines), so ascending integer order on compkey == ascending order of the real tuple key (bool(is_from), module). INDEPENDENT 2,000,000-sample random check (flags in {0,1}, modules uniform in [0,1e9)) comparing the spec-forced unique ascending arrangement of the 3 keys against the real callee output (sorted by (flag,module) tuple then keyed): ZERO divergences. Equal keys collapse identically (stability is unobservable because the model tracks only keys, and distinct import lines have distinct pairs in reality). The spec is exactly tight — multiset-preserving + fully ascending — not over-strong: no valid 3-line input is accepted by the real callee yet rejected by the spec (nor vice versa).

DOMAIN SCOPE: the 3-line domain restriction is a documented modeling-scope choice (Nagini 1.2.0 300s Z3 wall on the general-N cross-region sortedness invariant), and it is the minimal configuration witnessing the change (a from-import whose module token sorts before a plain import's, e.g. django.db < time, yet must follow it). Within the modeled domain the spec matches the callee exactly, so this is a scope choice, not a fidelity drift.

No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view(model.py)) passes with zero hard failures. Semantic review confirms no leak beyond the public problem_statement: (1) The problem_statement already fully specifies the target behavior — 'Place all import module statements before from module import objects in each section' plus the verbatim desired output (import datetime / import time / from django.db import migrations, models). The spec view's docstring/postconditions describe exactly this grouped ordering (plain imports before from-imports, module-ordered within group) and the derivable discriminating case; nothing beyond the public feature request. (2) No gold-patch line reproduced in the spec view — the verbatim gold key (i.split()[0]=='from', i.split()[1]) appears ONLY in refinement.md/mapping.md, which are auditor-facing derivation docs, not the consumer spec view. (3) No patched file path (django/db/migrations/writer.py), no patched symbol (as_string) echoed in spec-view identifiers or comments, no diff markers, no bug/fix narration. (4) The compkey/integer-code/three-line abstraction is a modeling choice that discloses no edit-localization; the conceptual (is-from, module-name) pair is a restatement of the problem statement's own stated rule, not new information. The implementation mechanism (sort-key tuple) is not revealed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
