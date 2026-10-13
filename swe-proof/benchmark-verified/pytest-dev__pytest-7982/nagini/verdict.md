# P2 adversarial audit — pytest-dev__pytest-7982

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_nofollow.py`, `atk_2_ignore_selected.py`, `atk_3_offbyone.py`, `atk_4_early_exit.py`, `atk_5_overbroad.py`, `atk_6_negate.py`, `atk_7_oracle_echo.py`, `atk_8_partial_domain.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_nofollow.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,10 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        # WRONG: no-follow classification -- a link-to-dir (code 2) counts as non-dir
+        decision = kinds[i] == 1 and selected[i]  # type: bool
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2_ignore_selected.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,10 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        # WRONG: descend whenever it resolves to a dir, ignoring the predicate
+        decision = resolves_to_dir(kinds[i])  # type: bool
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 3 — `atk_3_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -85,27 +83,15 @@
     result = PSeq(True).take(0)  # type: PSeq[bool]
     i = 0
     n = len(kinds)
-    while i < n:
+    while i < n - 1:
         # invariants-start
         Invariant(len(kinds) == len(selected))
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
         decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4_early_exit.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,12 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
+        # WRONG: bail out of the level as soon as an entry is not selected
+        if not selected[i]:
+            return result
         decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5_overbroad.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,11 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        # WRONG: any non-file entry (kind != 0) treated as a directory,
+        # so a link-to-nondir/broken (code 3) is wrongly descended into
+        decision = kinds[i] != 0 and selected[i]  # type: bool
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6_negate.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,10 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        # WRONG: negated predicate
+        decision = resolves_to_dir(kinds[i]) and (not selected[i])  # type: bool
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk_7_oracle_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -94,18 +92,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == should_descend(kinds[k], selected[k])),
             [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        decision = should_descend(kinds[i], selected[i])  # type: bool
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

Attack 8 — `atk_8_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     # The two parallel views describe the same entries, one verdict each.
     Requires(len(kinds) == len(selected))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # One decision per entry, in order.
@@ -91,21 +89,14 @@
         Invariant(n == len(kinds))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == should_descend(kinds[k], selected[k])),
-            [[result[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        # Classify the entry by following any link to its target, then require
-        # the caller predicate to have selected it.
-        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
-        Assert(decision == should_descend(kinds[i], selected[i]))
-        old_result = result  # type: PSeq[bool]
+        # WRONG: correct only on a partial sub-domain -- code-2 links dropped
+        # when i is even (no-follow), correct when i is odd
+        if i % 2 == 0:
+            decision = kinds[i] == 1 and selected[i]  # type: bool
+        else:
+            decision = resolves_to_dir(kinds[i]) and selected[i]
         result = result + PSeq(decision)
-        Assert(len(result) == i + 1)
-        Assert(result[i] == decision)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-7982.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A directory walk inspects the ordered entries of one directory level. For
  each entry it must decide whether to descend into that entry's own contents.
  The walk descends into an entry exactly when BOTH hold:

    * the entry resolves to a directory -- this is true not only for a plain
      directory but also for a link whose target is a directory (the link is
      followed when classifying it), and false for a non-directory entry or a
      link whose target is not a directory; and
    * a caller-supplied recursion predicate selects that entry.

  In particular, a link that points at a directory is treated as a directory
  for the purpose of descending: when such a link is selected by the predicate
  the walk descends into it, just as it would for a plain directory. A link to
  a non-directory, and any non-directory entry, is never descended into.

Each directory level is modelled as two parallel pure sequences: `kinds[i]`
classifies entry `i` and `selected[i]` is the caller predicate's verdict for
entry `i`. The classification carrier uses four codes:

    0 = a non-directory entry (e.g. a regular file)
    1 = a plain directory
    2 = a link whose target is a directory
    3 = a link whose target is not a directory (or that resolves to none)

The decision "this entry resolves to a directory" is modelled DEEPLY as the
pure predicate `resolves_to_dir` (codes 1 and 2); its equality to the real
filesystem classification callee is checked out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. Pure sequences carry no heap permission, so
the inputs are read-only by construction and the specification quantifies over
their elements directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the "resolves to a directory" classification
#  is modelled deeply below as `resolves_to_dir` and validated == the real
#  filesystem classification callee out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def resolves_to_dir(kind: int) -> bool:
    """Whether an entry of the given classification code resolves to a
    directory. A plain directory (1) does; a link whose target is a directory
    (2) also does, because the link is followed when classifying it; a
    non-directory entry (0) and a link to a non-directory (3) do not."""
    return kind == 1 or kind == 2


@Pure
def should_descend(kind: int, selected: bool) -> bool:
    """The per-entry descent decision: descend exactly when the entry resolves
    to a directory AND the caller predicate selected it."""
    return resolves_to_dir(kind) and selected
# pure-end


def descend_decisions(kinds: PSeq[int], selected: PSeq[bool]) -> PSeq[bool]:
    # pre-conditions-start
    # The two parallel views describe the same entries, one verdict each.
    Requires(len(kinds) == len(selected))
    # pre-conditions-end
    # post-conditions-start
    # One decision per entry, in order.
    Ensures(len(Result()) == len(kinds))
    # Each decision is exactly "resolves to a directory AND selected": a
    # link-to-directory (code 2) that is selected IS descended into, exactly as
    # a plain directory (code 1) is; a non-directory (0) or link-to-non-dir (3)
    # is never descended into.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
        Result()[i] == should_descend(kinds[i], selected[i])),
        [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = PSeq(True).take(0)  # type: PSeq[bool]
    i = 0
    n = len(kinds)
    while i < n:
        # invariants-start
        Invariant(len(kinds) == len(selected))
        Invariant(n == len(kinds))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == should_descend(kinds[k], selected[k])),
            [[result[k]]])))
        # invariants-end
        # Classify the entry by following any link to its target, then require
        # the caller predicate to have selected it.
        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
        Assert(decision == should_descend(kinds[i], selected[i]))
        old_result = result  # type: PSeq[bool]
        result = result + PSeq(decision)
        Assert(len(result) == i + 1)
        Assert(result[i] == decision)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins the output as a TOTAL per-element function of inputs: Ensures(len(Result())==len(kinds)) AND Forall i in [0,len): Result()[i]==should_descend(kinds[i],selected[i]), where should_descend/resolves_to_dir are CONCRETE @Pure predicates (resolves_to_dir(k)=(k==1 or k==2)), NOT @ContractOnly axioms. Any impl whose per-entry decision deviates from resolves_to_dir(kind) and selected fails the postcondition. All 8 same-spec wrong/probe impls (same-spec exit 0 each) were run through `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7982 <atk>`; ALL returned exit 2 (does-not-verify, genuine verification failures — grep confirms NO timeout/inconclusive/infra), so NO CANDIDATE emerged and no faithful patch needed materializing/resolve-running (the resolve step is required only for a verifying candidate).

Attacks & observed results:
- atk_1_nofollow.py (prepatch bug, decision=(kind==1 and selected), no-follow classification; inner contradicting assert stripped so rejection comes from the POSTCONDITION): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). This is the prepatch bug reproduced (=model_prepatch.py behaviour): confirms spec senses the change on code-2 link-to-dir (F2P test_collect_symlink_dir). prepatch_reproduced=true.
- atk_2_ignore_selected.py (ungrounded/partial: decision=resolves_to_dir(kind), drops caller predicate): exit 2.
- atk_3_offbyone.py (boundary: loop while i<n-1, drops last entry -> len postcond fails): exit 2.
- atk_4_early_exit.py (control-flow effect: return early at first non-selected entry): exit 2.
- atk_5_overbroad.py (over-broad classification: kind!=0 -> code-3 link-to-nondir wrongly descended): exit 2.
- atk_6_negate.py (inverted predicate: resolves_to_dir(kind) and not selected): exit 2.
- atk_7_oracle_echo.py (ungrounded-oracle-echo probe: decision=should_descend(...)). NOTE: since should_descend is a CONCRETE @Pure this echo computes the TRUE gold value and is behaviourally CORRECT; it still returned exit 2 here only because I stripped the frame-preservation helper asserts needed for proof completeness — a proof-completeness quirk, NOT a soundness hole (an echo that verifies would be a gold-equivalent impl whose refined patch RESOLVES, per the 2026-08-06 G-PANEL-1 echo policy, hence not a weakness anyway).
- atk_8_partial_domain.py (partial-domain: correct only for odd i, no-follow (wrong) for even i): exit 2.

Positive control (bundle model.py verbatim): scripts/nagini_verify.sh -> Verification successful (9.16s), exit 0.

Refinement.md leg audit: A1=R (entries<->parallel PSeq kinds/selected), A2=A-reference (deep @Pure resolves_to_dir modelling os.DirEntry.is_dir() follow_symlinks=True, validated out-of-band by G-AX; NOT consumed as an axiom), A3=R (recurse(entry)<->selected[i]), A4=I (identical boolean conjunction), A5=R (per-entry descent decision <-> yield-from visit control flow). No consumed axiom, NO kind-3 (unexpressible-changed-op) leg. The single A-reference correspondence holds exactly: axiom_check.py (G-AX) exit 0 — asserts is_dir()==resolves_to_dir(code) on boundary trees (each code alone, all-codes, empty) + 2000 random mixed trees (stdlib only) and confirms the pre-patch no-follow callee disagrees exactly on code 2 (link-to-directory). Gold patch is the one-line src/_pytest/pathlib.py:561 edit is_dir(follow_symlinks=False)->is_dir(); F2P=test_collect_symlink_dir.

Commands used:
- python -m swebench_unified.adversary same-spec nagini pytest-dev__pytest-7982 <atk> (all exit 0)
- python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7982 <atk> (all exit 2)
- bash scripts/nagini_verify.sh <positive_control> (exit 0)
- python .../axiom_check.py (G-AX exit 0)
Verify commands were run in 3 background batches of <=3 (nagini JVM+Z3) per the parallelism directive.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_nofollow.py`, `atk_2_ignore_selected.py`, `atk_3_offbyone.py`, `atk_4_early_exit.py`, `atk_5_overbroad.py`, `atk_6_negate.py`, `atk_7_oracle_echo.py`, `atk_8_partial_domain.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_nofollow.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_ignore_selected.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_offbyone.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_early_exit.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_overbroad.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_negate.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_partial_domain.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-7982.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A directory walk inspects the ordered entries of one directory level. For
  each entry it must decide whether to descend into that entry's own contents.
  The walk descends into an entry exactly when BOTH hold:

    * the entry resolves to a directory -- this is true not only for a plain
      directory but also for a link whose target is a directory (the link is
      followed when classifying it), and false for a non-directory entry or a
      link whose target is not a directory; and
    * a caller-supplied recursion predicate selects that entry.

  In particular, a link that points at a directory is treated as a directory
  for the purpose of descending: when such a link is selected by the predicate
  the walk descends into it, just as it would for a plain directory. A link to
  a non-directory, and any non-directory entry, is never descended into.

Each directory level is modelled as two parallel pure sequences: `kinds[i]`
classifies entry `i` and `selected[i]` is the caller predicate's verdict for
entry `i`. The classification carrier uses four codes:

    0 = a non-directory entry (e.g. a regular file)
    1 = a plain directory
    2 = a link whose target is a directory
    3 = a link whose target is not a directory (or that resolves to none)

The decision "this entry resolves to a directory" is modelled DEEPLY as the
pure predicate `resolves_to_dir` (codes 1 and 2); its equality to the real
filesystem classification callee is checked out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. Pure sequences carry no heap permission, so
the inputs are read-only by construction and the specification quantifies over
their elements directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the "resolves to a directory" classification
#  is modelled deeply below as `resolves_to_dir` and validated == the real
#  filesystem classification callee out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def resolves_to_dir(kind: int) -> bool:
    """Whether an entry of the given classification code resolves to a
    directory. A plain directory (1) does; a link whose target is a directory
    (2) also does, because the link is followed when classifying it; a
    non-directory entry (0) and a link to a non-directory (3) do not."""
    return kind == 1 or kind == 2


@Pure
def should_descend(kind: int, selected: bool) -> bool:
    """The per-entry descent decision: descend exactly when the entry resolves
    to a directory AND the caller predicate selected it."""
    return resolves_to_dir(kind) and selected
# pure-end


def descend_decisions(kinds: PSeq[int], selected: PSeq[bool]) -> PSeq[bool]:
    # pre-conditions-start
    # The two parallel views describe the same entries, one verdict each.
    Requires(len(kinds) == len(selected))
    # pre-conditions-end
    # post-conditions-start
    # One decision per entry, in order.
    Ensures(len(Result()) == len(kinds))
    # Each decision is exactly "resolves to a directory AND selected": a
    # link-to-directory (code 2) that is selected IS descended into, exactly as
    # a plain directory (code 1) is; a non-directory (0) or link-to-non-dir (3)
    # is never descended into.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
        Result()[i] == should_descend(kinds[i], selected[i])),
        [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = PSeq(True).take(0)  # type: PSeq[bool]
    i = 0
    n = len(kinds)
    while i < n:
        # invariants-start
        Invariant(len(kinds) == len(selected))
        Invariant(n == len(kinds))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == should_descend(kinds[k], selected[k])),
            [[result[k]]])))
        # invariants-end
        # Classify the entry by following any link to its target, then require
        # the caller predicate to have selected it.
        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
        Assert(decision == should_descend(kinds[i], selected[i]))
        old_result = result  # type: PSeq[bool]
        result = result + PSeq(decision)
        Assert(len(result) == i + 1)
        Assert(result[i] == decision)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins the output as a TOTAL per-element function of inputs: Ensures(len(Result())==len(kinds)) AND Forall i in [0,len): Result()[i]==should_descend(kinds[i],selected[i]), where should_descend/resolves_to_dir are CONCRETE @Pure predicates (resolves_to_dir(k)=(k==1 or k==2)), NOT @ContractOnly axioms. Any impl whose per-entry decision deviates from resolves_to_dir(kind) and selected fails the postcondition. All 8 same-spec wrong/probe impls (same-spec exit 0 each) were run through `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7982 <atk>`; ALL returned exit 2 (does-not-verify, genuine verification failures — grep confirms NO timeout/inconclusive/infra), so NO CANDIDATE emerged and no faithful patch needed materializing/resolve-running (the resolve step is required only for a verifying candidate).

Attacks & observed results:
- atk_1_nofollow.py (prepatch bug, decision=(kind==1 and selected), no-follow classification; inner contradicting assert stripped so rejection comes from the POSTCONDITION): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). This is the prepatch bug reproduced (=model_prepatch.py behaviour): confirms spec senses the change on code-2 link-to-dir (F2P test_collect_symlink_dir). prepatch_reproduced=true.
- atk_2_ignore_selected.py (ungrounded/partial: decision=resolves_to_dir(kind), drops caller predicate): exit 2.
- atk_3_offbyone.py (boundary: loop while i<n-1, drops last entry -> len postcond fails): exit 2.
- atk_4_early_exit.py (control-flow effect: return early at first non-selected entry): exit 2.
- atk_5_overbroad.py (over-broad classification: kind!=0 -> code-3 link-to-nondir wrongly descended): exit 2.
- atk_6_negate.py (inverted predicate: resolves_to_dir(kind) and not selected): exit 2.
- atk_7_oracle_echo.py (ungrounded-oracle-echo probe: decision=should_descend(...)). NOTE: since should_descend is a CONCRETE @Pure this echo computes the TRUE gold value and is behaviourally CORRECT; it still returned exit 2 here only because I stripped the frame-preservation helper asserts needed for proof completeness — a proof-completeness quirk, NOT a soundness hole (an echo that verifies would be a gold-equivalent impl whose refined patch RESOLVES, per the 2026-08-06 G-PANEL-1 echo policy, hence not a weakness anyway).
- atk_8_partial_domain.py (partial-domain: correct only for odd i, no-follow (wrong) for even i): exit 2.

Positive control (bundle model.py verbatim): scripts/nagini_verify.sh -> Verification successful (9.16s), exit 0.

Refinement.md leg audit: A1=R (entries<->parallel PSeq kinds/selected), A2=A-reference (deep @Pure resolves_to_dir modelling os.DirEntry.is_dir() follow_symlinks=True, validated out-of-band by G-AX; NOT consumed as an axiom), A3=R (recurse(entry)<->selected[i]), A4=I (identical boolean conjunction), A5=R (per-entry descent decision <-> yield-from visit control flow). No consumed axiom, NO kind-3 (unexpressible-changed-op) leg. The single A-reference correspondence holds exactly: axiom_check.py (G-AX) exit 0 — asserts is_dir()==resolves_to_dir(code) on boundary trees (each code alone, all-codes, empty) + 2000 random mixed trees (stdlib only) and confirms the pre-patch no-follow callee disagrees exactly on code 2 (link-to-directory). Gold patch is the one-line src/_pytest/pathlib.py:561 edit is_dir(follow_symlinks=False)->is_dir(); F2P=test_collect_symlink_dir.

Commands used:
- python -m swebench_unified.adversary same-spec nagini pytest-dev__pytest-7982 <atk> (all exit 0)
- python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7982 <atk> (all exit 2)
- bash scripts/nagini_verify.sh <positive_control> (exit 0)
- python .../axiom_check.py (G-AX exit 0)
Verify commands were run in 3 background batches of <=3 (nagini JVM+Z3) per the parallelism directive.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) attack on nagini pytest-dev__pytest-7982. Spec region confirmed byte-identical (same-spec exit 0). The modeled function should_descend(kind,selected)=(kind==1||kind==2)&&selected maps to the real guard `entry.is_dir() and recurse(entry)` at src/_pytest/pathlib.py:561 (post-patch). I built the gold-patched worktree at base_commit (git worktree + git apply patch.diff; verified line reads `if entry.is_dir() and recurse(entry):`) and ran my OWN differential test at the whole-visit level against the real patched callee: exhaustive boundary (every kinds vector length 0..4 over {0,1,2,3} x every selected vector = 4681) + 1500 fuzz trees (len 0..10) x 64 predicate vectors, seed 79820 = 100681 total inputs. Result: 0 disagreements between the spec's per-entry descent decision and the real walk's observed descent (marker-in-yielded-stream oracle). This reproduces the bundle's own G-CONF (checked=100681, disagreements=0). G-AX independently confirms resolves_to_dir(code)==os.DirEntry.is_dir() (follow_symlinks=True) on real on-disk trees incl. the discriminating link-to-directory (code 2). The input domain equals the documented carrier alphabet {0,1,2,3}; every code has a concrete filesystem realization, and there is no real-callee input on which the model disagrees. Codes outside {0,1,2,3} have no filesystem realization and cannot form a divergence from a real callee. The spec is not too strong (matches post-patch exactly) nor too weak (model_prepatch kind==1 fails, G-DIFF passes). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py non-impl regions) was projected via markers.spec_view and screened with leakage.screen against the frozen problem_statement — mechanical screen PASSES (no diff markers, no verbatim gold-patch line, no patched file path 'src/_pytest/pathlib.py', no patched module path, no spec-view identifier/comment echoing the patched repo symbol 'visit', no narration). Semantic judgment: the gold edit is `entry.is_dir(follow_symlinks=False)` -> `entry.is_dir()`, i.e. follow the symlink so a link-to-a-directory is classified as a directory and descended into. That exact discriminating behavior is ALREADY fully public in problem_statement: 'When there is a symlink to a directory ... it is just skipped over, but it should be followed and collected as usual' and 'I added a `follow_symlinks=False` in there ... should be removed.' The spec view describes this behavior abstractly (resolves_to_dir, code carrier 0-3, should_descend = resolves_to_dir AND selected) without exposing the repo file, the changed function name `visit`, the concrete `follow_symlinks` expression, or any pre/post-patch narration. refinement.md and mapping.md (which DO quote the gold hunk, file:line, symbol `visit`, and the pre-patch `follow_symlinks=False` expression) are audit artifacts, NOT part of the consumer spec view, so they do not constitute a spec-view leak. Nothing in the spec view localizes the edit beyond what problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
