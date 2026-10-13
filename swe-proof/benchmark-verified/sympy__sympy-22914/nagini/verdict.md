# P2 adversarial audit — sympy__sympy-22914

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,21 +127,12 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
-    if name_code == 0 or name_code == 1 or name_code == 2:
-        nm = []  # type: List[int]
-        if name_code == 0:
-            nm = [97, 98, 115]
-        elif name_code == 1:
-            nm = [109, 105, 110]
-        else:
-            nm = [109, 97, 120]
+    # Pre-patch: only the absolute-value function is supported; the selection
+    # functions are NOT, so they take the unchanged machinery output.
+    if name_code == 0:
+        nm = [97, 98, 115]  # type: List[int]
         result = nm + [40] + joined_args + [41]  # type: List[int]
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,21 +127,16 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
     if name_code == 0 or name_code == 1 or name_code == 2:
         nm = []  # type: List[int]
         if name_code == 0:
             nm = [97, 98, 115]
         elif name_code == 1:
-            nm = [109, 105, 110]
+            nm = [109, 97, 120]   # WRONG: 'max' for min
         else:
-            nm = [109, 97, 120]
+            nm = [109, 105, 110]  # WRONG: 'min' for max
         result = nm + [40] + joined_args + [41]  # type: List[int]
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,21 +127,18 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
-    if name_code == 0 or name_code == 1 or name_code == 2:
+    if name_code == 0 or name_code == 1 or name_code == 2 or name_code == 3:
         nm = []  # type: List[int]
         if name_code == 0:
             nm = [97, 98, 115]
         elif name_code == 1:
             nm = [109, 105, 110]
+        elif name_code == 2:
+            nm = [109, 97, 120]
         else:
-            nm = [109, 97, 120]
+            nm = [109, 97, 120]   # WRONG: name 3 rendered as a call, not fallback
         result = nm + [40] + joined_args + [41]  # type: List[int]
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,21 +127,16 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
     if name_code == 0 or name_code == 1 or name_code == 2:
         nm = []  # type: List[int]
         if name_code == 0:
-            nm = [97, 98, 115]
+            nm = [97, 98, 116]   # WRONG: 'abt' instead of 'abs'
         elif name_code == 1:
             nm = [109, 105, 110]
         else:
             nm = [109, 97, 120]
         result = nm + [40] + joined_args + [41]  # type: List[int]
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,9 +127,6 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
     if name_code == 0 or name_code == 1 or name_code == 2:
         nm = []  # type: List[int]
         if name_code == 0:
@@ -140,10 +135,8 @@
             nm = [109, 105, 110]
         else:
             nm = [109, 97, 120]
-        result = nm + [40] + joined_args + [41]  # type: List[int]
+        result = nm + [40] + joined_args + [41] + [41]  # type: List[int]  WRONG extra ')'
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,22 +127,29 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
-    if name_code == 0 or name_code == 1 or name_code == 2:
-        nm = []  # type: List[int]
-        if name_code == 0:
+    # Behaviourally identical to the gold impl, written differently: a nested
+    # dispatch for the supported call, and an explicit element-by-element copy
+    # of the unchanged machinery output for the unsupported path.
+    nm = []  # type: List[int]
+    if name_code != 3:
+        if name_code == 1:
+            nm = [109, 105, 110]
+        elif name_code == 2:
+            nm = [109, 97, 120]
+        else:
             nm = [97, 98, 115]
-        elif name_code == 1:
-            nm = [109, 105, 110]
-        else:
-            nm = [109, 97, 120]
-        result = nm + [40] + joined_args + [41]  # type: List[int]
+        opened = nm + [40]  # type: List[int]
+        result = opened + joined_args  # type: List[int]
+        result = result + [41]
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
-    empty = []  # type: List[int]
-    out = empty + fallback  # type: List[int]
+    out = []  # type: List[int]
+    i = 0
+    while i < len(fallback):
+        Invariant(Acc(list_pred(fallback), 1 / 2))
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= i and i <= len(fallback))
+        Invariant(ToSeq(out) == ToSeq(fallback).take(i))
+        out.append(fallback[i])
+        i = i + 1
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # `fallback` is the unchanged surrounding machinery's output for this node,
     # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
     Requires(Acc(list_pred(fallback), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(joined_args), 1 / 2))
@@ -129,9 +127,6 @@
                     ToSeq(Result()) == ToSeq(fallback)))
     # post-conditions-end
     # impl-start
-    # Mirror the printer dispatch: a supported function identity renders as a
-    # call; everything else is emitted exactly as the unchanged surrounding
-    # machinery emits it (its pre-rendered output `fallback`).
     if name_code == 0 or name_code == 1 or name_code == 2:
         nm = []  # type: List[int]
         if name_code == 0:
@@ -140,10 +135,8 @@
             nm = [109, 105, 110]
         else:
             nm = [109, 97, 120]
-        result = nm + [40] + joined_args + [41]  # type: List[int]
+        result = nm + [40] + joined_args  # type: List[int]  WRONG: no closing ')'
         return result
-    # An unsupported function keeps the unchanged machinery's rendering: return
-    # (a fresh copy of) its pre-rendered output, unaltered.
     empty = []  # type: List[int]
     out = empty + fallback  # type: List[int]
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code printer renders a function-application expression to a target-language
  call.  The expression carries a function identity and an ordered sequence of
  already-rendered argument strings.  The printer consults a table of supported
  functions:

    * the binary/n-ary selection of the smaller of its arguments is a supported
      function whose target rendering is the lower-case three-letter call name
      `m`,`i`,`n` (U+006D U+0069 U+006E);
    * the selection of the larger of its arguments is a supported function whose
      target rendering is the call name `m`,`a`,`x` (U+006D U+0061 U+0078);
    * the absolute-value function is likewise supported, with target `a`,`b`,`s`.

  For any supported function the result is the target call name, an opening
  parenthesis `(`, the already-rendered arguments joined by a comma and a single
  space, and a closing parenthesis `)`.  A function that is NOT in the supported
  table is emitted EXACTLY as the unchanged surrounding printing machinery
  would emit it — nothing but the supported-call emission may change.  That
  machinery is pre-existing infrastructure; its output for this node arrives as
  the read-only input `fallback` and is returned unaltered.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the comma-joined argument text is carried as one pre-rendered code
point sequence `joined_args` (the unchanged sub-computation shared by every
supported function), and the unsupported-path text as the pre-rendered
sequence `fallback` (the unchanged non-call machinery's output, carried
read-only).  The function identity is abstracted by an integer name code.
Supported-function membership and each target name are modelled deeply
(`is_supported` / `target_name`), validated == the real printer table by
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def name_min() -> int:
    return 1


@Pure
def name_max() -> int:
    return 2


@Pure
def name_abs() -> int:
    return 0


@Pure
def name_unknown() -> int:
    return 3


@Pure
def is_supported(name_code: int) -> bool:
    """The function identity is in the printer's supported-function table.
    The selection functions (min, max) and absolute value are supported; an
    arbitrary other function identity is not."""
    return name_code == 0 or name_code == 1 or name_code == 2


@Pure
def target_name(name_code: int) -> PSeq[int]:
    """The target-language call name rendered for a supported function."""
    if name_code == 0:
        return PSeq(97, 98, 115)        # 'abs'
    if name_code == 1:
        return PSeq(109, 105, 110)      # 'min'
    return PSeq(109, 97, 120)           # 'max'


@Pure
def call_render(name_code: int, joined_args: PSeq[int]) -> PSeq[int]:
    """The call rendering for a supported function: target name, '(', the
    comma-joined argument text, ')'."""
    return target_name(name_code) + PSeq(40) + joined_args + PSeq(41)
# pure-end


def print_function_call(name_code: int, joined_args: List[int],
                        fallback: List[int]) -> List[int]:
    # pre-conditions-start
    # `name_code` ranges over the function identities the dispatch distinguishes.
    Requires(0 <= name_code and name_code <= 3)
    Requires(Acc(list_pred(joined_args), 1 / 2))
    # `fallback` is the unchanged surrounding machinery's output for this node,
    # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
    Requires(Acc(list_pred(fallback), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(joined_args), 1 / 2))
    Ensures(Acc(list_pred(fallback), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A supported function renders as the target call name followed by the
    # parenthesised, comma-joined arguments.  In particular the smaller-of and
    # larger-of selection functions are supported (their targets are min / max),
    # so neither falls through to the non-call fallback.
    Ensures(Implies(is_supported(name_code),
                    ToSeq(Result()) == call_render(name_code, ToSeq(joined_args))))
    # The minimum/maximum selection functions specifically: the rendering begins
    # with the three-letter target call name and is the call form, not a
    # fallback or rewritten conditional expression.
    Ensures(Implies(name_code == name_min(),
                    ToSeq(Result()) == PSeq(109, 105, 110) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    Ensures(Implies(name_code == name_max(),
                    ToSeq(Result()) == PSeq(109, 97, 120) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    # A function outside the supported table is emitted EXACTLY as the
    # unchanged surrounding machinery emits it — nothing but the supported-call
    # emission may change.  This pins the unsupported path completely (the
    # result IS the machinery's output), so no divergent fallback behaviour is
    # admitted.
    Ensures(Implies(not is_supported(name_code),
                    ToSeq(Result()) == ToSeq(fallback)))
    # post-conditions-end
    # impl-start
    # Mirror the printer dispatch: a supported function identity renders as a
    # call; everything else is emitted exactly as the unchanged surrounding
    # machinery emits it (its pre-rendered output `fallback`).
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    # An unsupported function keeps the unchanged machinery's rendering: return
    # (a fresh copy of) its pre-rendered output, unaltered.
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec fully pins Result for all four name codes: is_supported(0/1/2) => Result==call_render(name_code,joined_args); name_min => min(...); name_max => max(...); not is_supported(3) => Result==fallback exactly.

All 8 files are byte-identical in spec signature (adversary same-spec => SAME for atk_1..atk_7 + positive_control). Positive control (gold impl copied verbatim) VERIFIES: `adversary verify nagini sympy__sympy-22914 positive_control.py` => VERIFIED 13.3s.

Attacks (command per file: `python -m swebench_unified.adversary weakness nagini sympy__sympy-22914 <atk_N.py>`), run concurrently <=3 JVM jobs at a time:
- atk_1 (PREPATCH bug reproduced: only Abs supported, Min/Max fall to fallback): NOT-A-COUNTEREXAMPLE, does not verify (spec rejects) exit=2. This is the known prepatch bug => prepatch_reproduced=true. It fails the is_supported postcondition on Min/Max.
- atk_2 (SWAP min<->max target names): does not verify, exit=2.
- atk_3 (BOUNDARY: name_code==3 rendered as a 'max(...)' call instead of fallback): does not verify, exit=2 (violates not-is_supported => Result==fallback).
- atk_4 (PARTIAL-DOMAIN: abs bytes 'abt' [97,98,116] for name 0): does not verify, exit=2.
- atk_5 (CONTROL-FLOW-EFFECT: extra trailing ')' [41] appended to supported-call result): does not verify, exit=2.
- atk_6 (UNGROUNDED-ORACLE ECHO: behaviourally identical to gold, restructured -- nested name dispatch + explicit while-loop element copy of fallback with loop invariants): CANDIDATE-COUNTEREXAMPLE, shares spec AND VERIFIES (12.6s). Per protocol materialized its faithful refined patch = the gold _known_functions table edit (Min->min, Max->max), file patch_atk_6.diff, and RAN it through the official harness: `run_resolve('sympy__sympy-22914', patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. A resolving echo is NOT a weakness -> does not break the spec.
- atk_7 (OFF-BY-ONE: drop closing ')' on supported call): does not verify, exit=2.

Six distinct wrong impls (partial-domain, boundary, swap, control-flow-effect, off-by-one, prepatch) are all REJECTED by the spec; the only verifying attack is behaviourally correct and its faithful patch RESOLVES. verify=>correct holds.

A-leg / deep-model audit (crux, since spec pins Result completely via the A-reference): refinement.md legs are A1(R), A2(R), A2b(R), A3(A-reference), A4(R+I), A5(I); axioms region is EMPTY -> no consumed @ContractOnly axiom, no kind-3 (unexpressible-changed-op) leg. The changed op (extending the supported table) is modeled DEEPLY via is_supported/target_name/call_render, validated == the real callee by G-AX/axiom_check.py. Independently confirmed the A-reference correspondence against the real PATCHED PythonCodePrinter: doprint(Min(x,y))=='min(x, y)', doprint(Max(x,y,z))=='max(x, y, z)', doprint(Abs(x))=='abs(x)' -- code points [109,105,110]/[109,97,120]/[97,98,115] exactly equal target_name(1)/target_name(2)/target_name(0). Correspondence holds. (Note: running axiom_check.py in my local env raised PrintMethodNotImplementedError on its 40 unsupported negatives because local sympy 1.14 defaults strict-printing to raise; that is a local-env artifact of the negative branch, not a G-EQ concern -- the positive A-reference and all attack/resolve facts stand.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code printer renders a function-application expression to a target-language
  call.  The expression carries a function identity and an ordered sequence of
  already-rendered argument strings.  The printer consults a table of supported
  functions:

    * the binary/n-ary selection of the smaller of its arguments is a supported
      function whose target rendering is the lower-case three-letter call name
      `m`,`i`,`n` (U+006D U+0069 U+006E);
    * the selection of the larger of its arguments is a supported function whose
      target rendering is the call name `m`,`a`,`x` (U+006D U+0061 U+0078);
    * the absolute-value function is likewise supported, with target `a`,`b`,`s`.

  For any supported function the result is the target call name, an opening
  parenthesis `(`, the already-rendered arguments joined by a comma and a single
  space, and a closing parenthesis `)`.  A function that is NOT in the supported
  table is emitted EXACTLY as the unchanged surrounding printing machinery
  would emit it — nothing but the supported-call emission may change.  That
  machinery is pre-existing infrastructure; its output for this node arrives as
  the read-only input `fallback` and is returned unaltered.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the comma-joined argument text is carried as one pre-rendered code
point sequence `joined_args` (the unchanged sub-computation shared by every
supported function), and the unsupported-path text as the pre-rendered
sequence `fallback` (the unchanged non-call machinery's output, carried
read-only).  The function identity is abstracted by an integer name code.
Supported-function membership and each target name are modelled deeply
(`is_supported` / `target_name`), validated == the real printer table by
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def name_min() -> int:
    return 1


@Pure
def name_max() -> int:
    return 2


@Pure
def name_abs() -> int:
    return 0


@Pure
def name_unknown() -> int:
    return 3


@Pure
def is_supported(name_code: int) -> bool:
    """The function identity is in the printer's supported-function table.
    The selection functions (min, max) and absolute value are supported; an
    arbitrary other function identity is not."""
    return name_code == 0 or name_code == 1 or name_code == 2


@Pure
def target_name(name_code: int) -> PSeq[int]:
    """The target-language call name rendered for a supported function."""
    if name_code == 0:
        return PSeq(97, 98, 115)        # 'abs'
    if name_code == 1:
        return PSeq(109, 105, 110)      # 'min'
    return PSeq(109, 97, 120)           # 'max'


@Pure
def call_render(name_code: int, joined_args: PSeq[int]) -> PSeq[int]:
    """The call rendering for a supported function: target name, '(', the
    comma-joined argument text, ')'."""
    return target_name(name_code) + PSeq(40) + joined_args + PSeq(41)
# pure-end


def print_function_call(name_code: int, joined_args: List[int],
                        fallback: List[int]) -> List[int]:
    # pre-conditions-start
    # `name_code` ranges over the function identities the dispatch distinguishes.
    Requires(0 <= name_code and name_code <= 3)
    Requires(Acc(list_pred(joined_args), 1 / 2))
    # `fallback` is the unchanged surrounding machinery's output for this node,
    # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
    Requires(Acc(list_pred(fallback), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(joined_args), 1 / 2))
    Ensures(Acc(list_pred(fallback), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A supported function renders as the target call name followed by the
    # parenthesised, comma-joined arguments.  In particular the smaller-of and
    # larger-of selection functions are supported (their targets are min / max),
    # so neither falls through to the non-call fallback.
    Ensures(Implies(is_supported(name_code),
                    ToSeq(Result()) == call_render(name_code, ToSeq(joined_args))))
    # The minimum/maximum selection functions specifically: the rendering begins
    # with the three-letter target call name and is the call form, not a
    # fallback or rewritten conditional expression.
    Ensures(Implies(name_code == name_min(),
                    ToSeq(Result()) == PSeq(109, 105, 110) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    Ensures(Implies(name_code == name_max(),
                    ToSeq(Result()) == PSeq(109, 97, 120) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    # A function outside the supported table is emitted EXACTLY as the
    # unchanged surrounding machinery emits it — nothing but the supported-call
    # emission may change.  This pins the unsupported path completely (the
    # result IS the machinery's output), so no divergent fallback behaviour is
    # admitted.
    Ensures(Implies(not is_supported(name_code),
                    ToSeq(Result()) == ToSeq(fallback)))
    # post-conditions-end
    # impl-start
    # Mirror the printer dispatch: a supported function identity renders as a
    # call; everything else is emitted exactly as the unchanged surrounding
    # machinery emits it (its pre-rendered output `fallback`).
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: List[int]
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    # An unsupported function keeps the unchanged machinery's rendering: return
    # (a fresh copy of) its pre-rendered output, unaltered.
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec fully pins Result for all four name codes: is_supported(0/1/2) => Result==call_render(name_code,joined_args); name_min => min(...); name_max => max(...); not is_supported(3) => Result==fallback exactly.

All 8 files are byte-identical in spec signature (adversary same-spec => SAME for atk_1..atk_7 + positive_control). Positive control (gold impl copied verbatim) VERIFIES: `adversary verify nagini sympy__sympy-22914 positive_control.py` => VERIFIED 13.3s.

Attacks (command per file: `python -m swebench_unified.adversary weakness nagini sympy__sympy-22914 <atk_N.py>`), run concurrently <=3 JVM jobs at a time:
- atk_1 (PREPATCH bug reproduced: only Abs supported, Min/Max fall to fallback): NOT-A-COUNTEREXAMPLE, does not verify (spec rejects) exit=2. This is the known prepatch bug => prepatch_reproduced=true. It fails the is_supported postcondition on Min/Max.
- atk_2 (SWAP min<->max target names): does not verify, exit=2.
- atk_3 (BOUNDARY: name_code==3 rendered as a 'max(...)' call instead of fallback): does not verify, exit=2 (violates not-is_supported => Result==fallback).
- atk_4 (PARTIAL-DOMAIN: abs bytes 'abt' [97,98,116] for name 0): does not verify, exit=2.
- atk_5 (CONTROL-FLOW-EFFECT: extra trailing ')' [41] appended to supported-call result): does not verify, exit=2.
- atk_6 (UNGROUNDED-ORACLE ECHO: behaviourally identical to gold, restructured -- nested name dispatch + explicit while-loop element copy of fallback with loop invariants): CANDIDATE-COUNTEREXAMPLE, shares spec AND VERIFIES (12.6s). Per protocol materialized its faithful refined patch = the gold _known_functions table edit (Min->min, Max->max), file patch_atk_6.diff, and RAN it through the official harness: `run_resolve('sympy__sympy-22914', patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. A resolving echo is NOT a weakness -> does not break the spec.
- atk_7 (OFF-BY-ONE: drop closing ')' on supported call): does not verify, exit=2.

Six distinct wrong impls (partial-domain, boundary, swap, control-flow-effect, off-by-one, prepatch) are all REJECTED by the spec; the only verifying attack is behaviourally correct and its faithful patch RESOLVES. verify=>correct holds.

A-leg / deep-model audit (crux, since spec pins Result completely via the A-reference): refinement.md legs are A1(R), A2(R), A2b(R), A3(A-reference), A4(R+I), A5(I); axioms region is EMPTY -> no consumed @ContractOnly axiom, no kind-3 (unexpressible-changed-op) leg. The changed op (extending the supported table) is modeled DEEPLY via is_supported/target_name/call_render, validated == the real callee by G-AX/axiom_check.py. Independently confirmed the A-reference correspondence against the real PATCHED PythonCodePrinter: doprint(Min(x,y))=='min(x, y)', doprint(Max(x,y,z))=='max(x, y, z)', doprint(Abs(x))=='abs(x)' -- code points [109,105,110]/[109,97,120]/[97,98,115] exactly equal target_name(1)/target_name(2)/target_name(0). Correspondence holds. (Note: running axiom_check.py in my local env raised PrintMethodNotImplementedError on its 40 unsupported negatives because local sympy 1.14 defaults strict-printing to raise; that is a local-env artifact of the negative branch, not a G-EQ concern -- the positive A-reference and all attack/resolve facts stand.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no diverging input found; the modeled print_function_call agrees with the real callee everywhere. Evidence:

1. SPEC INTEGRITY: model.py verifies under the pinned Nagini (exit 0, 11.4s). Deep model (is_supported/target_name/call_render) uses NO consumed @ContractOnly axiom; axioms region empty. Spec/proof/impl markers present (6 regions).

2. WORKTREE NOTE: is at base_commit c4e836cdf7 (a merge), which ALREADY contains the gold hunk (Min->min, Max->max in _known_functions at pycode.py:20-21). So the real printer already renders min(...)/max(...); this is the post-patch face the model models, consistent with the twin-artifact design.

3. SUPPORTED PATH (potential over-claim tested): spec says is_supported(0/1/2) => Result == target_name ++ '(' ++ joined_args ++ ')' with targets abs/min/max. Fuzzed the REAL PythonCodePrinter over ~1200 Min/Max/Abs renderings (Min/Max arities 2-4, Abs unary, canonicalized arg orders, 10-symbol pool). Real doprint output == model call_render code points on EVERY case (mismatch count 0). _module_format('min'/'max'/'abs') returns the bare names (no 'math.' prefix), so targets are byte-exact. Dispatch uses _print_known_func (', '.join(_print(arg) for arg in args)) which matches the joined_args carrier and G-AX's joined computation.

4. UNSUPPORTED PATH: spec pins not is_supported => Result == fallback. fallback is an opaque READ-ONLY input bound to the unchanged machinery's output (_print_not_supported codeprinter.py:560 / _rewriteable_functions Piecewise rewrite). Result==fallback is an identity abstraction over the pre-rendered sequence; it cannot over-claim, since it asserts nothing about fallback's internal content.

5. ABSTRACTION BOUNDARY: name_code==3 abstracts a genuinely-unsupported identity (e.g. a user Function). The model is a scoped abstraction of the single change site (the two added table keys), not a claim to enumerate the whole known_functions table, so it does not falsely mark math.* functions unsupported. No drift.

Conclusion: the spec is faithful to the real repo behavior; it is neither too strong nor drifting. The gold-patched printer satisfies every postcondition clause on the tested inputs and G-AX validates deep-model == real printer.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region of model.py is byte-identical with model_prepatch.py (same_spec exit 0): only the impl-start/impl-end region differs, so the frozen spec view = docstring + pure region + pre/post-conditions. The discriminating content that spec view carries — Min and Max become supported, call-rendered functions with targets 'min'/'max', alongside pre-existing Abs->'abs' (encoded as is_supported(1)=is_supported(2)=True, target_name(1)=PSeq(109,105,110)='min', target_name(2)=PSeq(109,97,120)='max', and the postconditions pinning name_min/name_max to 'min(...)'/'max(...)') — is ENTIRELY subsumed by the PUBLIC problem_statement, which verbatim spells out the gold edit: it gives the exact code `_print_Min` returning "min({})".format(...) and `_print_Max` returning "max({})".format(...), and references issue #16669 (the Abs precedent). The gold patch itself merely adds 'Min':'min','Max':'max' to _known_functions. Thus the spec discloses nothing about the gold edit beyond the public problem_statement. Everything the spec adds over problem_statement is modeling apparatus, not gold-edit information: List[int]/PSeq code-point encoding (Nagini bans str indexing), the integer name-code abstraction, the read-only `fallback` carrier for unchanged machinery, and the deep-model/G-AX validation scheme. These describe HOW the behaviour is modeled, not new facts about the fix. No spec-view line leaks the gold edit beyond problem_statement. Note: problem_statement here is exceptionally explicit (contains the literal gold code), so the leakage bar is already very high; the spec stays within it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
