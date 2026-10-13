# P2 adversarial audit — django__django-14493

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
@@ -93,34 +93,19 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
-    substitutions = False
     i = 0
     while i < max_passes:
-        # invariants-start
         Invariant(Acc(list_pred(pass_changed), 1 / 2))
         Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
         Invariant(substitutions == (i > 0 and
                                     all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
         Invariant(i == 0 or substitutions)
-        # invariants-end
         substitutions = pass_changed[i] != 0
         Assert(ToSeq(pass_changed)[i] == pass_changed[i])
         if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
             lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
             return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
         lemma_unfold(ToSeq(pass_changed), i + 1)
         i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
     return substitutions
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,34 +93,5 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
-    substitutions = False
-    i = 0
-    while i < max_passes:
-        # invariants-start
-        Invariant(Acc(list_pred(pass_changed), 1 / 2))
-        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
-        substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
-        if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
-            return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
-        i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
-    return substitutions
+    return max_passes > 0
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,34 +93,14 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
-    substitutions = False
+    substitutions = True
     i = 0
     while i < max_passes:
-        # invariants-start
         Invariant(Acc(list_pred(pass_changed), 1 / 2))
         Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
         substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
         if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
             return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
         i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
     return substitutions
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,34 +93,14 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
     substitutions = False
     i = 0
-    while i < max_passes:
-        # invariants-start
+    while i < max_passes - 1:
         Invariant(Acc(list_pred(pass_changed), 1 / 2))
         Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
         substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
         if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
             return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
         i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
     return substitutions
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,34 +93,13 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
     substitutions = False
     i = 0
     while i < max_passes:
-        # invariants-start
         Invariant(Acc(list_pred(pass_changed), 1 / 2))
         Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
-        substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
-        if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
-            return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
+        if pass_changed[i] != 0:
+            substitutions = True
         i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
     return substitutions
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,34 +93,5 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
-    substitutions = False
-    i = 0
-    while i < max_passes:
-        # invariants-start
-        Invariant(Acc(list_pred(pass_changed), 1 / 2))
-        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
-        substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
-        if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
-            return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
-        i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
-    return substitutions
+    return max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,34 +93,14 @@
     Ensures(Implies(max_passes == 0, Result() == False))
     # post-conditions-end
     # impl-start
-    # Initialise the flag BEFORE the loop so it is defined even when the loop
-    # body never runs (max_passes == 0). This is the whole behaviour.
     substitutions = False
     i = 0
     while i < max_passes:
-        # invariants-start
         Invariant(Acc(list_pred(pass_changed), 1 / 2))
         Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
-        # Before each iteration the flag reflects the passes run so far: True
-        # iff at least one pass ran (i > 0) and all of the first i passes changed.
-        Invariant(substitutions == (i > 0 and
-                                    all_changed(ToSeq(pass_changed), i)))
-        # The loop is only re-entered after a change-reporting pass, so reaching
-        # i > 0 means the flag is set and the first i passes all changed.
-        Invariant(i == 0 or substitutions)
-        # invariants-end
         substitutions = pass_changed[i] != 0
-        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
         if not substitutions:
-            # Early stop: pass i reported no change. Then the full count of
-            # passes is not all-changed, so the closed form is False regardless
-            # of the remaining allowance.
-            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
-            return False
-        # pass i changed: extend the all-changed prefix from i to i+1.
-        lemma_unfold(ToSeq(pass_changed), i + 1)
+            return True
         i = i + 1
-    # Normal completion: i == max_passes, so the running flag already equals the
-    # full-range closed form (congruence over the single count argument).
     return substitutions
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable, possibly-zero number of refinement passes is run over a set
  of files. Each pass reports whether it produced any change. A single boolean
  flag records whether the most recently completed pass produced a change; the
  loop stops early as soon as a pass produces no change. After the passes
  finish, that flag is consulted to decide whether to report that the bound on
  the number of passes was reached without the process settling.

  The contract demanded here is that this consultation is always well defined,
  INCLUDING when the configured number of passes is zero: with zero passes the
  flag must read as "no change produced" (so that no spurious "bound reached"
  report is emitted), and the operation must complete normally and return a
  definite boolean on every path — never leave the flag undefined.

  The returned boolean is exactly: at least one pass was run AND every pass that
  ran produced a change (equivalently: the loop exhausted its allowance without
  ever observing a change-free pass). With zero allowed passes this is false.

The per-pass "produced a change" outcomes are modelled as a read-only
`List[int]` of 0/1 flags (flag i is the outcome of pass i); the number of
allowed passes is a non-negative `int`. The specification is carried over the
pure mathematical sequence `PSeq[int]` by the front-recursive predicate
`all_changed`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms. The only behaviour under specification — the definite-assignment
# and early-stop semantics of the pass loop — is modelled deeply below; it
# calls no opaque, unchanged library callee that the proof must assume.)
# axioms-end


# pure-start
@Pure
def all_changed(flags: PSeq[int], n: int) -> bool:
    """True iff every one of the first n passes reported a change (flag != 0).
    Recursive on the pass count n; n == 0 is vacuously True (no pass reported
    'no change'). Phrased over a pure sequence so it carries no heap framing.
    """
    Requires(0 <= n and n <= len(flags))
    if n == 0:
        return True
    return flags[n - 1] != 0 and all_changed(flags, n - 1)
# pure-end


def lemma_unfold(flags: PSeq[int], n: int) -> None:
    """One-step unfold of `all_changed` at a symbolic count, so the loop can
    extend the all-changed prefix from n-1 to n after a change-reporting pass.
    """
    Requires(1 <= n and n <= len(flags))
    Ensures(all_changed(flags, n) ==
            (flags[n - 1] != 0 and all_changed(flags, n - 1)))


def lemma_change_free_kills(flags: PSeq[int], k: int, n: int) -> None:
    """If pass k reported no change (flag == 0) and k < n, then the first n
    passes are not all-changed. Proved by recursion downward on n.
    """
    Requires(0 <= k and k < n and n <= len(flags))
    Requires(flags[k] == 0)
    Ensures(not all_changed(flags, n))
    if k < n - 1:
        lemma_change_free_kills(flags, k, n - 1)


def run_passes(pass_changed: List[int], max_passes: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(pass_changed), 1 / 2))
    # The number of allowed passes is non-negative and indexes into the
    # per-pass outcomes; max_passes == 0 (the zero-pass configuration) is the
    # boundary the contract must keep well defined.
    Requires(0 <= max_passes and max_passes <= len(pass_changed))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pass_changed), 1 / 2))
    Ensures(0 <= max_passes and max_passes <= len(pass_changed))
    # The flag consulted after the passes is ALWAYS a definite boolean (this
    # function returns on every path, including the zero-pass path) and equals
    # the closed form: some pass ran AND every pass that ran reported a change.
    Ensures(Result() == (max_passes > 0 and
                         all_changed(ToSeq(pass_changed), max_passes)))
    # With zero allowed passes the flag reads as "no change to report": the
    # result is a definite False (never absent).
    Ensures(Implies(max_passes == 0, Result() == False))
    # post-conditions-end
    # impl-start
    # Initialise the flag BEFORE the loop so it is defined even when the loop
    # body never runs (max_passes == 0). This is the whole behaviour.
    substitutions = False
    i = 0
    while i < max_passes:
        # invariants-start
        Invariant(Acc(list_pred(pass_changed), 1 / 2))
        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
        # Before each iteration the flag reflects the passes run so far: True
        # iff at least one pass ran (i > 0) and all of the first i passes changed.
        Invariant(substitutions == (i > 0 and
                                    all_changed(ToSeq(pass_changed), i)))
        # The loop is only re-entered after a change-reporting pass, so reaching
        # i > 0 means the flag is set and the first i passes all changed.
        Invariant(i == 0 or substitutions)
        # invariants-end
        substitutions = pass_changed[i] != 0
        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
        if not substitutions:
            # Early stop: pass i reported no change. Then the full count of
            # passes is not all-changed, so the closed form is False regardless
            # of the remaining allowance.
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        # pass i changed: extend the all-changed prefix from i to i+1.
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    # Normal completion: i == max_passes, so the running flag already equals the
    # full-range closed form (congruence over the single count argument).
    return substitutions
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: run_passes has a FULLY-PINNED functional postcondition: Ensures(Result() == (max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes))) plus Ensures(Implies(max_passes==0, Result()==False)) and the permission Ensures. The spec view elides ONLY the impl body (lines 96-125); axioms/@Pure all_changed/lemma_unfold/lemma_change_free_kills/contracts are byte-identical in every attack. same-spec exit 0 for all 7. A return value that satisfies this postcondition is behaviourally equal to the gold post-loop flag => any refined patch resolves. No room for a verifying-but-wrong return value.

### PROTOCOL RESULTS (project root; verifier python -m swebench_unified.adversary weakness nagini django__django-14493 <atk>):
- positive_control.py (verbatim model.py): bash scripts/nagini_verify.sh -> exit 0 (VERIFIES). Baseline good.
- atk_1.py = PREPATCH BUG (no pre-loop `substitutions=False`; reads flag undefined on zero-pass path): weakness exit 2, log 'attack does not verify (verification failed) — the spec rejected this impl (good)'. Prepatch defect reproduced (definite-assignment failure = static analogue of UnboundLocalError).
- atk_2.py = ungrounded-oracle echo / ignores flags (`return max_passes > 0`): exit 2, does NOT verify.
- atk_3.py = boundary (init `substitutions=True` so zero-pass wrongly True): exit 2, does NOT verify.
- atk_4.py = off-by-one partial-domain (`while i < max_passes - 1`, skips last pass): exit 2, does NOT verify.
- atk_5.py = control-flow-effect (OR-fold 'any change', no early stop, drops all-changed semantics): exit 2, does NOT verify.
- atk_7.py = control-flow-effect (early-stop returns True instead of False): exit 2, does NOT verify.
- atk_6.py = CORRECT ECHO (`return max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)`): weakness exit 0 -> CANDIDATE (shares spec AND verifies, 11.5s). Per protocol its faithful refined patch was MATERIALIZED (= the gold patch, since it returns exactly the closed form the repo consumes) and RUN through the official harness: run_resolve('django__django-14493', patch) => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. A resolving echo of gold is NOT a weakness (matches the fixed panel_1/eq candidate->resolve policy).

A-LEG / DEEP-MODEL AUDIT: refinement.md declares NO @ContractOnly axiom and NO A-reference to a library callee — every leg is R (type refinement, steps 1,2,4,5,8) or I (identical op, steps 3,6,7); NO kind-3 unexpressible-changed-op steps. `all_changed`/lemmas abstract the IN-FUNCTION loop itself (proof-only, no repo counterpart), so the G-AX analogue is a faithfulness check: ran benchmark-verified/.../axiom_check.py -> exit 0, 'G-AX OK: deep model all_changed/run_passes == real post_process pass loop on 54097 (exhaustive small + boundary + 50000 fuzz) cases; pre-patch loop raises UnboundLocalError exactly at max_passes==0.' The model<->patch correspondence (mapping.md: run_passes<->post_process pass loop, max_passes<->max_post_process_passes, pass_changed[i]!=0<->pass i produced a substitution, Result()<->post-loop `if substitutions:` flag) holds.

CONCLUSION: 7 same-spec attacks run to completion (prepatch + 5 further distinct wrong impls + 1 correct echo). Every wrong impl gives a DEFINITE verification failure (not a timeout/infra error). The only CANDIDATE is the gold-equivalent echo, whose materialized faithful patch RESOLVES. No verifying-but-wrong impl exists. verify => correct holds. Verdict: SOUND.

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
"""Twin-artifact model for django__django-14493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable, possibly-zero number of refinement passes is run over a set
  of files. Each pass reports whether it produced any change. A single boolean
  flag records whether the most recently completed pass produced a change; the
  loop stops early as soon as a pass produces no change. After the passes
  finish, that flag is consulted to decide whether to report that the bound on
  the number of passes was reached without the process settling.

  The contract demanded here is that this consultation is always well defined,
  INCLUDING when the configured number of passes is zero: with zero passes the
  flag must read as "no change produced" (so that no spurious "bound reached"
  report is emitted), and the operation must complete normally and return a
  definite boolean on every path — never leave the flag undefined.

  The returned boolean is exactly: at least one pass was run AND every pass that
  ran produced a change (equivalently: the loop exhausted its allowance without
  ever observing a change-free pass). With zero allowed passes this is false.

The per-pass "produced a change" outcomes are modelled as a read-only
`List[int]` of 0/1 flags (flag i is the outcome of pass i); the number of
allowed passes is a non-negative `int`. The specification is carried over the
pure mathematical sequence `PSeq[int]` by the front-recursive predicate
`all_changed`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms. The only behaviour under specification — the definite-assignment
# and early-stop semantics of the pass loop — is modelled deeply below; it
# calls no opaque, unchanged library callee that the proof must assume.)
# axioms-end


# pure-start
@Pure
def all_changed(flags: PSeq[int], n: int) -> bool:
    """True iff every one of the first n passes reported a change (flag != 0).
    Recursive on the pass count n; n == 0 is vacuously True (no pass reported
    'no change'). Phrased over a pure sequence so it carries no heap framing.
    """
    Requires(0 <= n and n <= len(flags))
    if n == 0:
        return True
    return flags[n - 1] != 0 and all_changed(flags, n - 1)
# pure-end


def lemma_unfold(flags: PSeq[int], n: int) -> None:
    """One-step unfold of `all_changed` at a symbolic count, so the loop can
    extend the all-changed prefix from n-1 to n after a change-reporting pass.
    """
    Requires(1 <= n and n <= len(flags))
    Ensures(all_changed(flags, n) ==
            (flags[n - 1] != 0 and all_changed(flags, n - 1)))


def lemma_change_free_kills(flags: PSeq[int], k: int, n: int) -> None:
    """If pass k reported no change (flag == 0) and k < n, then the first n
    passes are not all-changed. Proved by recursion downward on n.
    """
    Requires(0 <= k and k < n and n <= len(flags))
    Requires(flags[k] == 0)
    Ensures(not all_changed(flags, n))
    if k < n - 1:
        lemma_change_free_kills(flags, k, n - 1)


def run_passes(pass_changed: List[int], max_passes: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(pass_changed), 1 / 2))
    # The number of allowed passes is non-negative and indexes into the
    # per-pass outcomes; max_passes == 0 (the zero-pass configuration) is the
    # boundary the contract must keep well defined.
    Requires(0 <= max_passes and max_passes <= len(pass_changed))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pass_changed), 1 / 2))
    Ensures(0 <= max_passes and max_passes <= len(pass_changed))
    # The flag consulted after the passes is ALWAYS a definite boolean (this
    # function returns on every path, including the zero-pass path) and equals
    # the closed form: some pass ran AND every pass that ran reported a change.
    Ensures(Result() == (max_passes > 0 and
                         all_changed(ToSeq(pass_changed), max_passes)))
    # With zero allowed passes the flag reads as "no change to report": the
    # result is a definite False (never absent).
    Ensures(Implies(max_passes == 0, Result() == False))
    # post-conditions-end
    # impl-start
    # Initialise the flag BEFORE the loop so it is defined even when the loop
    # body never runs (max_passes == 0). This is the whole behaviour.
    substitutions = False
    i = 0
    while i < max_passes:
        # invariants-start
        Invariant(Acc(list_pred(pass_changed), 1 / 2))
        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
        # Before each iteration the flag reflects the passes run so far: True
        # iff at least one pass ran (i > 0) and all of the first i passes changed.
        Invariant(substitutions == (i > 0 and
                                    all_changed(ToSeq(pass_changed), i)))
        # The loop is only re-entered after a change-reporting pass, so reaching
        # i > 0 means the flag is set and the first i passes all changed.
        Invariant(i == 0 or substitutions)
        # invariants-end
        substitutions = pass_changed[i] != 0
        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
        if not substitutions:
            # Early stop: pass i reported no change. Then the full count of
            # passes is not all-changed, so the closed form is False regardless
            # of the remaining allowance.
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        # pass i changed: extend the all-changed prefix from i to i+1.
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    # Normal completion: i == max_passes, so the running flag already equals the
    # full-range closed form (congruence over the single count argument).
    return substitutions
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: run_passes has a FULLY-PINNED functional postcondition: Ensures(Result() == (max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes))) plus Ensures(Implies(max_passes==0, Result()==False)) and the permission Ensures. The spec view elides ONLY the impl body (lines 96-125); axioms/@Pure all_changed/lemma_unfold/lemma_change_free_kills/contracts are byte-identical in every attack. same-spec exit 0 for all 7. A return value that satisfies this postcondition is behaviourally equal to the gold post-loop flag => any refined patch resolves. No room for a verifying-but-wrong return value.

### PROTOCOL RESULTS (project root; verifier python -m swebench_unified.adversary weakness nagini django__django-14493 <atk>):
- positive_control.py (verbatim model.py): bash scripts/nagini_verify.sh -> exit 0 (VERIFIES). Baseline good.
- atk_1.py = PREPATCH BUG (no pre-loop `substitutions=False`; reads flag undefined on zero-pass path): weakness exit 2, log 'attack does not verify (verification failed) — the spec rejected this impl (good)'. Prepatch defect reproduced (definite-assignment failure = static analogue of UnboundLocalError).
- atk_2.py = ungrounded-oracle echo / ignores flags (`return max_passes > 0`): exit 2, does NOT verify.
- atk_3.py = boundary (init `substitutions=True` so zero-pass wrongly True): exit 2, does NOT verify.
- atk_4.py = off-by-one partial-domain (`while i < max_passes - 1`, skips last pass): exit 2, does NOT verify.
- atk_5.py = control-flow-effect (OR-fold 'any change', no early stop, drops all-changed semantics): exit 2, does NOT verify.
- atk_7.py = control-flow-effect (early-stop returns True instead of False): exit 2, does NOT verify.
- atk_6.py = CORRECT ECHO (`return max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)`): weakness exit 0 -> CANDIDATE (shares spec AND verifies, 11.5s). Per protocol its faithful refined patch was MATERIALIZED (= the gold patch, since it returns exactly the closed form the repo consumes) and RUN through the official harness: run_resolve('django__django-14493', patch) => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. A resolving echo of gold is NOT a weakness (matches the fixed panel_1/eq candidate->resolve policy).

A-LEG / DEEP-MODEL AUDIT: refinement.md declares NO @ContractOnly axiom and NO A-reference to a library callee — every leg is R (type refinement, steps 1,2,4,5,8) or I (identical op, steps 3,6,7); NO kind-3 unexpressible-changed-op steps. `all_changed`/lemmas abstract the IN-FUNCTION loop itself (proof-only, no repo counterpart), so the G-AX analogue is a faithfulness check: ran benchmark-verified/.../axiom_check.py -> exit 0, 'G-AX OK: deep model all_changed/run_passes == real post_process pass loop on 54097 (exhaustive small + boundary + 50000 fuzz) cases; pre-patch loop raises UnboundLocalError exactly at max_passes==0.' The model<->patch correspondence (mapping.md: run_passes<->post_process pass loop, max_passes<->max_post_process_passes, pass_changed[i]!=0<->pass i produced a substitution, Result()<->post-loop `if substitutions:` flag) holds.

CONCLUSION: 7 same-spec attacks run to completion (prepatch + 5 further distinct wrong impls + 1 correct echo). Every wrong impl gives a DEFINITE verification failure (not a timeout/infra error). The only CANDIDATE is the gold-equivalent echo, whose materialized faithful patch RESOLVES. No verifying-but-wrong impl exists. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. The model's run_passes postcondition closed form Result() == (max_passes>0 and all_changed(ToSeq(pass_changed), max_passes)), with Result()==False when max_passes==0, exactly matches the real post_process pass loop in django/contrib/staticfiles/storage.py:263-276 at base_commit 7272e1963f (worktree). The real loop resets `substitutions=False` at the start of each pass, ORs the inner _post_process subst values, breaks on the first change-free pass, and reads the post-loop flag at `if substitutions:`; the model's per-pass 0/1 abstraction (pass_changed[i]!=0 ⇔ pass i produced ≥1 substitution) is sound since only the per-pass aggregate reaches the post-loop read. Evidence: (1) bundle axiom_check.py passes — 54,097 exhaustive-small+boundary+50000-fuzz cases, model==real, and pre-patch loop raises UnboundLocalError exactly at max_passes==0; (2) independent re-derived probe of the real loop vs model closed form over 209,217 inputs (exhaustive length<=10 + 200k fuzz up to length 60) → 0 divergences; (3) model.py verifies under pinned Nagini (exit 0, 10.5s). The precondition 0<=max_passes<=len(pass_changed) is a faithful carrier constraint (max_passes flags indexed by pass number), not spec over-strengthening. Spec is faithful to real repo behavior; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (status=pass, 'spec view clean'). Semantic review of the solver-visible spec view (spec+proof regions; impl region is elided to '...') confirms no leak beyond the public problem_statement:

- No repo symbols. The spec view uses only abstract model names: run_passes, pass_changed, max_passes, all_changed, substitutions(local). Wait — note: the local var name 'substitutions' does NOT appear in the spec view; the impl (which uses it) is elided. The gold-patch symbol context (post_process / max_post_process_passes / ManifestStaticFilesStorage / storage.py) is absent.
- No file path 'storage.py', no diff markers, no reproduced gold-patch line ('substitutions = False').
- No narration keywords (bug/fix/patch/etc.).

Crucially, the public problem_statement is MORE revealing than the spec view: it names 'substitutions', states 'referenced before assignment', 'only set if the loop is entered at least once', gives the max_post_process_passes=0 trigger and the UnboundLocalError. The spec view merely restates the desired behavior abstractly ('return a definite boolean on every path — never leave the flag undefined'; 'with zero passes the flag must read as no change produced'), which is a strict abstraction of what is already public. It localizes no edit beyond the public issue and quotes no gold specifics. The one operative sentence describing the fix ('Initialise the flag BEFORE the loop') lives in the impl-start/impl-end region, which is elided from the consumer spec view.

Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
