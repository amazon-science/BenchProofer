# P2 adversarial audit — django__django-15987

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -89,7 +87,6 @@
     result = False
     i = len(value_matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value_matches), 1 / 2))
         Invariant(Acc(list_pred(is_path_object), 1 / 2))
         Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
@@ -97,15 +94,10 @@
         Invariant(len(value_matches) == len(is_path_object))
         Invariant(0 <= i and i <= len(value_matches))
         Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
         Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
                ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
-            result = True
+        result = result or value_matches[i - 1]
         i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -89,22 +87,13 @@
     result = False
     i = len(value_matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value_matches), 1 / 2))
         Invariant(Acc(list_pred(is_path_object), 1 / 2))
         Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
         Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
         Invariant(len(value_matches) == len(is_path_object))
         Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
+        if value_matches[i - 1] and not is_path_object[i - 1]:
             result = True
         i = i - 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -88,22 +86,13 @@
     # impl-start
     result = False
     i = len(value_matches)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(value_matches), 1 / 2))
         Invariant(Acc(list_pred(is_path_object), 1 / 2))
         Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
         Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
         Invariant(len(value_matches) == len(is_path_object))
-        Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
+        Invariant(1 <= i and i <= len(value_matches) or i == 0)
         if value_matches[i - 1]:
             result = True
         i = i - 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -86,26 +84,5 @@
     Ensures(Result() == any_match(ToSeq(value_matches)))
     # post-conditions-end
     # impl-start
-    result = False
-    i = len(value_matches)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(value_matches), 1 / 2))
-        Invariant(Acc(list_pred(is_path_object), 1 / 2))
-        Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
-        Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
-        Invariant(len(value_matches) == len(is_path_object))
-        Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
-            result = True
-        i = i - 1
-    return result
+    return False
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -86,26 +84,5 @@
     Ensures(Result() == any_match(ToSeq(value_matches)))
     # post-conditions-end
     # impl-start
-    result = False
-    i = len(value_matches)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(value_matches), 1 / 2))
-        Invariant(Acc(list_pred(is_path_object), 1 / 2))
-        Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
-        Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
-        Invariant(len(value_matches) == len(is_path_object))
-        Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
-            result = True
-        i = i - 1
-    return result
+    return any_match(ToSeq(value_matches))
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
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -87,25 +85,11 @@
     # post-conditions-end
     # impl-start
     result = False
-    i = len(value_matches)
-    while i > 0:
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(value_matches), 1 / 2))
         Invariant(Acc(list_pred(is_path_object), 1 / 2))
         Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
         Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
-        Invariant(len(value_matches) == len(is_path_object))
-        Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
-            result = True
-        i = i - 1
+        result = result
     return result
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
@@ -70,7 +69,6 @@
     Requires(Acc(list_pred(value_matches), 1 / 2))
     Requires(Acc(list_pred(is_path_object), 1 / 2))
     Requires(len(value_matches) == len(is_path_object))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value_matches), 1 / 2))
@@ -86,26 +84,17 @@
     Ensures(Result() == any_match(ToSeq(value_matches)))
     # post-conditions-end
     # impl-start
-    result = False
+    result = True
     i = len(value_matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value_matches), 1 / 2))
         Invariant(Acc(list_pred(is_path_object), 1 / 2))
         Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
         Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
         Invariant(len(value_matches) == len(is_path_object))
         Invariant(0 <= i and i <= len(value_matches))
-        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
-        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
-               ToSeq(value_matches).drop(i))
-        # Compare by path string (the entry coerced to its path string equals
-        # the default directory's path string).
-        if value_matches[i - 1]:
-            result = True
+        if not value_matches[i - 1]:
+            result = False
         i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15987.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured collection of directory entries is scanned to decide whether a
  particular default directory is already present in that collection.  The
  decision is a duplicate-detection guard: the default directory is reported as
  present exactly when one of the configured entries denotes the SAME directory
  path as the default one.

  Each configured entry carries two observable facts:

    * ``value_matches`` — whether that entry's directory PATH STRING equals the
      default directory's path string.  Two entries denote the same directory
      precisely when their path strings are equal, so this is the only fact a
      correct presence test may depend on.

    * ``is_path_object`` — whether that entry is supplied as a rich path object
      rather than as a plain path string.  A rich path object and a plain
      string are never the same Python value even when they denote the same
      directory, so a naive identity/value comparison against the entry object
      would silently disagree with the path-string comparison for such an
      entry.

  The presence test must compare by directory path string, so its outcome
  depends ONLY on ``value_matches``: the default directory is present exactly
  when some configured entry's path string equals the default one's, REGARDLESS
  of whether that entry happens to be a rich path object or a plain string.  In
  particular a rich path object whose path string equals the default directory's
  is detected just like the equivalent plain string would be.

The configured collection is a list of directory entries in the repository;
here each entry is reduced to the two booleans above, carried as two parallel
read-only ``List[bool]``.  The presence test mutates nothing.  The whole-list
predicate is carried by a front-recursive ``@Pure`` fold over ``PSeq[bool]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the presence test is modelled deeply over concrete
# booleans via the front-recursive fold `any_match`; nothing opaque is consumed.
# The faithfulness of the per-entry abstraction — that comparing entries by
# their path string is exactly value equality, and that a rich path object is
# never the identical value as a plain path string — is an A-reference checked
# out-of-band by axiom_check.py / G-AX against the real path machinery, not an
# axiom the proof depends on.)
# axioms-end


# pure-start
@Pure
def any_match(eqs: PSeq[bool]) -> bool:
    """Whether some configured entry's path string equals the default
    directory's path string: the disjunction of the per-entry value matches.
    Front-recursive so a single unfold is available per loop step."""
    if len(eqs) == 0:
        return False
    return eqs[0] or any_match(eqs.drop(1))
# pure-end


def default_dir_is_listed(value_matches: List[bool],
                          is_path_object: List[bool]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value_matches), 1 / 2))
    Requires(Acc(list_pred(is_path_object), 1 / 2))
    Requires(len(value_matches) == len(is_path_object))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value_matches), 1 / 2))
    Ensures(Acc(list_pred(is_path_object), 1 / 2))
    # Both parallel inputs are read-only: unchanged in length and content.
    Ensures(ToSeq(value_matches) == Old(ToSeq(value_matches)))
    Ensures(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
    # The default directory is present exactly when some configured entry's path
    # string equals the default one's.  The right-hand side names ONLY
    # value_matches: `is_path_object` does NOT appear, so the outcome is pinned
    # independently of whether matching entries are rich path objects — no
    # verifying implementation may let path-object-ness suppress a detection.
    Ensures(Result() == any_match(ToSeq(value_matches)))
    # post-conditions-end
    # impl-start
    result = False
    i = len(value_matches)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value_matches), 1 / 2))
        Invariant(Acc(list_pred(is_path_object), 1 / 2))
        Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
        Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
        Invariant(len(value_matches) == len(is_path_object))
        Invariant(0 <= i and i <= len(value_matches))
        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
        # invariants-end
        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
               ToSeq(value_matches).drop(i))
        # Compare by path string (the entry coerced to its path string equals
        # the default directory's path string).
        if value_matches[i - 1]:
            result = True
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: postcondition `Result() == any_match(ToSeq(value_matches))` is a TOTAL FUNCTIONAL characterization of the output as a function of value_matches alone, with is_path_object pinned OUT of the RHS. This leaves a verifying impl NO behavioral freedom; any verifying impl computes exactly the disjunction of per-entry path-string matches. Nagini also enforces termination (MustTerminate default), confirmed by atk_6.

PROTOCOL: same-spec (fast, no JVM) confirmed all 7 attacks share the byte-identical spec signature. weakness (same-spec + Nagini verify) run concurrently in batches of <=3 JVMs. For EVERY CANDIDATE (same-spec AND verifies) I materialized the faithful refined patch and ran it through the official harness (run_resolve, timeout 1800).

### ATTACKS (all; cmd = `python -m swebench_unified.adversary weakness nagini django__django-15987 <path>`):
- atk_1.py (correct back-loop, `result = result or value_matches[i-1]` accumulation instead of if-branch; DISTINCT control flow): CANDIDATE (verifies 19.9s). Faithful patch = gold hunk. run_resolve => RESOLVED=True, COMPLETED=True (FAIL_TO_PASS 'settings.FIXTURE_DIRS cannot contain a default fixtures directory' + 52 PASS_TO_PASS all pass).
- atk_2.py (prepatch bug: `value_matches[i-1] and not is_path_object[i-1]`, path-object-suppressing): NOT-A-COUNTEREXAMPLE, verification FAILED (spec rejects). Bundle model_prepatch.py verified separately => FAILS on invariant `result == any_match(ToSeq(value_matches).drop(i))` at line 97 (G-DIFF: spec senses the bug). prepatch_reproduced=true.
- atk_3.py (off-by-one, loop `while i > 1` skips index 0): FAILED to verify (rejected).
- atk_4.py (constant `return False`, control-flow-effect): FAILED to verify (rejected).
- atk_5.py (ungrounded-oracle echo, `return any_match(ToSeq(value_matches))` directly): CANDIDATE (verifies 20.7s). Faithful patch = gold hunk (identical to atk_1's). run_resolve => RESOLVED=True.
- atk_6.py (non-termination `while True`, vacuous partial-correctness probe): FAILED to verify — termination IS enforced, so this ungrounded angle is closed.
- atk_7.py (AND-fold / conjunction, returns all-match boundary): FAILED to verify (rejected).

RESOLVE: faithful_patch.diff (the gold hunk `if app_dir in [str(d) for d in fixture_dirs]:`) is the faithful refinement of BOTH verifying candidates (both compute the exact gold disjunction). Single run_resolve on it: RESOLVED=True, COMPLETED=True, patch_successfully_applied=True.

REFINEMENT.MD AUDIT: 3 legs. Leg1=R (params->per-entry booleans, mechanical). Leg2=A-reference (deep fold any_match == real `app_dir in [str(d) for d in fixture_dirs]`; NO consumed axiom). Leg3=I (bool result -> if/raise branch, unchanged by patch). No kind-3 (unexpressible-changed-op) legs: the changed operation (str-coerced membership) is modeled DEEPLY, not hidden behind an oracle axiom. A-reference correspondence validated by G-AX: axiom_check.py exit 0 ('G-AX OK ... 9 boundary + 20000 fuzz ... post-patch model == `app_dir in [str(d) for d in dirs]`, pre-patch model == `app_dir in dirs`'). conformance_check.py (G-CONF) present and consistent with the model.

CONCLUSION: The spec fully pins the output; every verifying wrong-impl candidate's faithful patch RESOLVES; the prepatch bug is rejected; termination is enforced; the A-reference holds under G-AX. No verify=>!correct gap found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15987.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured collection of directory entries is scanned to decide whether a
  particular default directory is already present in that collection.  The
  decision is a duplicate-detection guard: the default directory is reported as
  present exactly when one of the configured entries denotes the SAME directory
  path as the default one.

  Each configured entry carries two observable facts:

    * ``value_matches`` — whether that entry's directory PATH STRING equals the
      default directory's path string.  Two entries denote the same directory
      precisely when their path strings are equal, so this is the only fact a
      correct presence test may depend on.

    * ``is_path_object`` — whether that entry is supplied as a rich path object
      rather than as a plain path string.  A rich path object and a plain
      string are never the same Python value even when they denote the same
      directory, so a naive identity/value comparison against the entry object
      would silently disagree with the path-string comparison for such an
      entry.

  The presence test must compare by directory path string, so its outcome
  depends ONLY on ``value_matches``: the default directory is present exactly
  when some configured entry's path string equals the default one's, REGARDLESS
  of whether that entry happens to be a rich path object or a plain string.  In
  particular a rich path object whose path string equals the default directory's
  is detected just like the equivalent plain string would be.

The configured collection is a list of directory entries in the repository;
here each entry is reduced to the two booleans above, carried as two parallel
read-only ``List[bool]``.  The presence test mutates nothing.  The whole-list
predicate is carried by a front-recursive ``@Pure`` fold over ``PSeq[bool]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the presence test is modelled deeply over concrete
# booleans via the front-recursive fold `any_match`; nothing opaque is consumed.
# The faithfulness of the per-entry abstraction — that comparing entries by
# their path string is exactly value equality, and that a rich path object is
# never the identical value as a plain path string — is an A-reference checked
# out-of-band by axiom_check.py / G-AX against the real path machinery, not an
# axiom the proof depends on.)
# axioms-end


# pure-start
@Pure
def any_match(eqs: PSeq[bool]) -> bool:
    """Whether some configured entry's path string equals the default
    directory's path string: the disjunction of the per-entry value matches.
    Front-recursive so a single unfold is available per loop step."""
    if len(eqs) == 0:
        return False
    return eqs[0] or any_match(eqs.drop(1))
# pure-end


def default_dir_is_listed(value_matches: List[bool],
                          is_path_object: List[bool]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value_matches), 1 / 2))
    Requires(Acc(list_pred(is_path_object), 1 / 2))
    Requires(len(value_matches) == len(is_path_object))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value_matches), 1 / 2))
    Ensures(Acc(list_pred(is_path_object), 1 / 2))
    # Both parallel inputs are read-only: unchanged in length and content.
    Ensures(ToSeq(value_matches) == Old(ToSeq(value_matches)))
    Ensures(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
    # The default directory is present exactly when some configured entry's path
    # string equals the default one's.  The right-hand side names ONLY
    # value_matches: `is_path_object` does NOT appear, so the outcome is pinned
    # independently of whether matching entries are rich path objects — no
    # verifying implementation may let path-object-ness suppress a detection.
    Ensures(Result() == any_match(ToSeq(value_matches)))
    # post-conditions-end
    # impl-start
    result = False
    i = len(value_matches)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value_matches), 1 / 2))
        Invariant(Acc(list_pred(is_path_object), 1 / 2))
        Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
        Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
        Invariant(len(value_matches) == len(is_path_object))
        Invariant(0 <= i and i <= len(value_matches))
        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
        # invariants-end
        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
               ToSeq(value_matches).drop(i))
        # Compare by path string (the entry coerced to its path string equals
        # the default directory's path string).
        if value_matches[i - 1]:
            result = True
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: postcondition `Result() == any_match(ToSeq(value_matches))` is a TOTAL FUNCTIONAL characterization of the output as a function of value_matches alone, with is_path_object pinned OUT of the RHS. This leaves a verifying impl NO behavioral freedom; any verifying impl computes exactly the disjunction of per-entry path-string matches. Nagini also enforces termination (MustTerminate default), confirmed by atk_6.

PROTOCOL: same-spec (fast, no JVM) confirmed all 7 attacks share the byte-identical spec signature. weakness (same-spec + Nagini verify) run concurrently in batches of <=3 JVMs. For EVERY CANDIDATE (same-spec AND verifies) I materialized the faithful refined patch and ran it through the official harness (run_resolve, timeout 1800).

### ATTACKS (all; cmd = `python -m swebench_unified.adversary weakness nagini django__django-15987 <path>`):
- atk_1.py (correct back-loop, `result = result or value_matches[i-1]` accumulation instead of if-branch; DISTINCT control flow): CANDIDATE (verifies 19.9s). Faithful patch = gold hunk. run_resolve => RESOLVED=True, COMPLETED=True (FAIL_TO_PASS 'settings.FIXTURE_DIRS cannot contain a default fixtures directory' + 52 PASS_TO_PASS all pass).
- atk_2.py (prepatch bug: `value_matches[i-1] and not is_path_object[i-1]`, path-object-suppressing): NOT-A-COUNTEREXAMPLE, verification FAILED (spec rejects). Bundle model_prepatch.py verified separately => FAILS on invariant `result == any_match(ToSeq(value_matches).drop(i))` at line 97 (G-DIFF: spec senses the bug). prepatch_reproduced=true.
- atk_3.py (off-by-one, loop `while i > 1` skips index 0): FAILED to verify (rejected).
- atk_4.py (constant `return False`, control-flow-effect): FAILED to verify (rejected).
- atk_5.py (ungrounded-oracle echo, `return any_match(ToSeq(value_matches))` directly): CANDIDATE (verifies 20.7s). Faithful patch = gold hunk (identical to atk_1's). run_resolve => RESOLVED=True.
- atk_6.py (non-termination `while True`, vacuous partial-correctness probe): FAILED to verify — termination IS enforced, so this ungrounded angle is closed.
- atk_7.py (AND-fold / conjunction, returns all-match boundary): FAILED to verify (rejected).

RESOLVE: faithful_patch.diff (the gold hunk `if app_dir in [str(d) for d in fixture_dirs]:`) is the faithful refinement of BOTH verifying candidates (both compute the exact gold disjunction). Single run_resolve on it: RESOLVED=True, COMPLETED=True, patch_successfully_applied=True.

REFINEMENT.MD AUDIT: 3 legs. Leg1=R (params->per-entry booleans, mechanical). Leg2=A-reference (deep fold any_match == real `app_dir in [str(d) for d in fixture_dirs]`; NO consumed axiom). Leg3=I (bool result -> if/raise branch, unchanged by patch). No kind-3 (unexpressible-changed-op) legs: the changed operation (str-coerced membership) is modeled DEEPLY, not hidden behind an oracle axiom. A-reference correspondence validated by G-AX: axiom_check.py exit 0 ('G-AX OK ... 9 boundary + 20000 fuzz ... post-patch model == `app_dir in [str(d) for d in dirs]`, pre-patch model == `app_dir in dirs`'). conformance_check.py (G-CONF) present and consistent with the model.

CONCLUSION: The spec fully pins the output; every verifying wrong-impl candidate's faithful patch RESOLVES; the prepatch bug is rejected; termination is enforced; the A-reference holds under G-AX. No verify=>!correct gap found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-15987 (nagini). Modeled function default_dir_is_listed(value_matches, is_path_object) has postcondition Result() == any_match(ToSeq(value_matches)) = (exists k. value_matches[k]). Bridge (validated with real machinery): value_matches[k] = (str(d_k)==app_dir), is_path_object[k] = isinstance(d_k, pathlib.PurePath).

Real callee: django/core/management/commands/loaddata.py inside the fixture_dirs cached property. The worktree at loaddata.py is the base_commit (pre-patch) form: line 370 `if app_dir in fixture_dirs:`. The gold patch changes it to `app_dir in [str(d) for d in fixture_dirs]`. Reducing the real post-patch expression: `app_dir in [str(d) for d in fixture_dirs]` == (exists k. str(d_k)==app_dir) == (exists k. value_matches[k]) == any_match(value_matches). This is a DEFINITIONAL equivalence (list membership over str(d) uses str `==`), NOT an over-approximation, so the spec does not over-constrain.

Spec is NOT too strong: is_path_object is deliberately pinned OUT of the postcondition RHS, matching real post-patch behavior exactly (detection depends solely on path-string equality; a path-object entry equal-by-string is detected just like a plain string). Folding is_path_object into the RHS would reproduce the pre-patch/weak behavior, correctly captured only in model_prepatch.py (value_matches[k] and not is_path_object[k]), which fails G-DIFF.

Independent evidence I ran myself: (1) `same-spec` command -> SAME, exit 0 (spec region byte-identical to bundle). (2) axiom_check.py / G-AX -> exit 0: post-patch model == real `app_dir in [str(d) for d in dirs]` AND pre-patch model == real `app_dir in dirs` over F2P Path(_cur_dir)/'fixtures' + 9 boundary + 20000 fuzz. (3) My OWN adversarial faithfulness probe comparing any_match(bridge(entries)) vs the REAL `app_dir in [str(d) for d in fixture_dirs]` over hand-picked hard cases (PurePosixPath/PureWindowsPath spellings, trailing/doubled separators, bytes/int/float non-string entries, empty-string, mixed Path+str) PLUS 200000 randomized mixed-type fuzz configs -> 0 divergences.

Modeling boundary: the whole-collection duplicate guard at loaddata.py:365 (len(fixture_dirs) != len(set(fixture_dirs))) is unchanged by the patch and lies outside the modeled decision -- a legitimate boundary; the conformance/fuzz harnesses dedup inputs so that guard never pre-empts the modeled test, and it does not affect the detection decision being modeled.

No input exists on which the modeled function disagrees with the real callee. Verdict: FAITHFUL -- the spec neither drifts from real repo behavior nor is too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + any_match + pre/post-conditions of default_dir_is_listed) was generated with swebench_unified.markers.spec_view and screened with leakage.screen: PASSED, zero hard_failures. Public problem_statement already discloses everything the spec view relies on: the bug is in duplicate detection of FIXTURE_DIRS entries and manifests 'when FIXTURE_DIRS contains Path instances' (desired = detect them). The spec view stays at/above that altitude: it says a default dir is present exactly when some entry's PATH STRING equals it, and that a rich path object equal-by-string must be detected like a plain string (postcondition RHS names only value_matches, pins is_path_object out). This is the behavior directly implied by the public statement, not a reconstruction of the gold edit. No leakage beyond problem_statement: (1) no gold-patch line reproduced — the gold hunk 'if app_dir in [str(d) for d in fixture_dirs]:' and its str()/list-comprehension membership do not appear; (2) patched file path django/core/management/commands/loaddata.py absent; (3) patched repo symbol fixture_dirs never appears in spec-view identifiers or comments — modeled abstractly as value_matches/is_path_object/any_match; (4) no diff markers; (5) no bug/fix/prepatch narration. The concrete str()/pathlib.PurePath.__eq__ mechanics and pre-patch 'app_dir in fixture_dirs' live ONLY in the auditor-side docs (mapping.md, refinement.md, axiom_check.py), not in the consumer spec view. meta relaxed_leakage=None, G-LEAK status=pass; no RELAXED_LEAKAGE deferral relevant. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
