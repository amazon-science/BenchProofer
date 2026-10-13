# P2 adversarial audit — django__django-14559

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -88,37 +88,6 @@
     Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
     # post-conditions-end
     # impl-start
-    total = 0
-    if len(keys) == 0:
-        return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
-        Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+    # partial-correctness abuse: unbounded self-recursion (the recorded break).
+    return bulk_apply_count(keys, group_size)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -88,37 +88,10 @@
     Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
     # post-conditions-end
     # impl-start
-    total = 0
-    if len(keys) == 0:
-        return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
-        Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+    i = 0
+    while i < 1:
+        Invariant(i == 0)
+        Invariant(MustTerminate(1))
+        i = i
+    return None
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,36 +89,9 @@
     # post-conditions-end
     # impl-start
     total = 0
-    if len(keys) == 0:
-        return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
+    while total >= 0:
         Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+        Invariant(MustTerminate(1))
+        total = total
+    return 999999
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,32 +93,17 @@
         return 0
     off = 0
     while off < len(keys):
-        # invariants-start
         Invariant(Acc(list_pred(keys), 1 / 2))
         Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
         Invariant(total >= 0)
         Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
                   batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
         Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
         rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
         step = group_size
         if step > len(keys) - off:
             step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
         total = total + matched_rows(rem.take(group_size))
         off = off + step
-    return total
+    return total + 1
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,33 +92,13 @@
     if len(keys) == 0:
         return 0
     off = 0
-    while off < len(keys):
-        # invariants-start
+    while off + group_size <= len(keys):
         Invariant(Acc(list_pred(keys), 1 / 2))
         Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
         Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
         Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
         rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
         total = total + matched_rows(rem.take(group_size))
-        off = off + step
+        off = off + group_size
     return total
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -88,37 +88,7 @@
     Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
     # post-conditions-end
     # impl-start
-    total = 0
     if len(keys) == 0:
         return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
-        Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+    return matched_rows(ToSeq(keys).take(group_size))
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -88,37 +88,5 @@
     Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
     # post-conditions-end
     # impl-start
-    total = 0
-    if len(keys) == 0:
-        return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
-        Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+    return batched_total(ToSeq(keys), group_size)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,34 +91,5 @@
     total = 0
     if len(keys) == 0:
         return 0
-    off = 0
-    while off < len(keys):
-        # invariants-start
-        Invariant(Acc(list_pred(keys), 1 / 2))
-        Invariant(0 <= off and off <= len(keys))
-        # `off` advances one whole group per step (capped at the end), so the
-        # consumed prefix is always a whole number of groups; the running total
-        # is what those consumed groups reported, and the still-to-process
-        # suffix accounts for the rest of the per-group sum.
-        Invariant(total >= 0)
-        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
-                  batched_total(ToSeq(keys), group_size))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(keys) - off.
-        Invariant(MustTerminate(len(keys) - off))
-        # invariants-end
-        rem = ToSeq(keys).drop(off)
-        # The current group is the first `group_size` keys of the remaining
-        # suffix; the suffix after this step drops exactly that group.
-        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
-        Assert(len(rem) > 0)
-        Assert(batched_total(rem, group_size) ==
-               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
-        step = group_size
-        if step > len(keys) - off:
-            step = len(keys) - off
-        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
-        total = total + matched_rows(rem.take(group_size))
-        off = off + step
-    return total
+    return 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14559.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batched persistence operation applies a change to an ordered collection of
  stored objects, identified by their primary keys, in fixed-size groups. It
  must report a count of the affected stored rows to its caller (rather than
  reporting nothing):

    (1) The reported value is always a count, never the absent value. In
        particular, when the collection is empty no group is processed and the
        reported count is zero.

    (2) The reported count is the sum, over the successive fixed-size groups the
        collection is split into, of the number of rows the underlying
        row-affecting primitive reports for that group. Because the grouping is
        by position and the primitive reports per group, an object that appears
        more than once is counted once per group it falls into: two appearances
        within a single group contribute the primitive's single-group count for
        that group, whereas two appearances placed into separate groups are
        each reported by their own group and therefore summed twice.

The collection of objects is modelled as a `List[int]` of primary-key values;
the group size is a positive `int`. The unchanged row-affecting primitive (the
per-group database update) is axiomatized: given the key values of one group it
reports a non-negative number of affected rows. The reported total is the
absent value (`None`) when no count is produced and a non-negative `int`
otherwise (`Optional[int]`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def matched_rows(group_keys: PSeq[int]) -> int:
    """Rows reported by the unchanged per-group row-affecting primitive (the
    database update issued against the rows whose key is in `group_keys`). The
    primitive matches each present stored row at most once, so the reported
    value is a non-negative count. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def batched_total(keys: PSeq[int], group_size: int) -> int:
    """The total reported across the successive fixed-size groups the key
    sequence is split into, front-to-back. Front-recursive (one unfold per
    group) so the forward impl loop can discharge it: the first `group_size`
    keys form one group, the remainder is split recursively. An empty sequence
    yields zero (no group, hence count zero)."""
    Requires(group_size >= 1)
    if len(keys) == 0:
        return 0
    return matched_rows(keys.take(group_size)) + batched_total(keys.drop(group_size), group_size)
# pure-end


def bulk_apply_count(keys: List[int], group_size: int) -> Optional[int]:
    # pre-conditions-start
    # `keys` is read-only: the operation reports a count and does not mutate the
    # collection it is given, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(group_size >= 1)
    # The count must actually be delivered: this termination obligation forbids
    # implementations that would satisfy the value postcondition only vacuously
    # by never returning (frozen loops or unbounded self-calls).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(keys), 1 / 2))
    # (1) a count is always produced — never the absent value — and it is
    # non-negative; the empty collection produces zero.
    Ensures(Result() is not None)
    Ensures(Result() >= 0)  # type: ignore
    # (2) the produced count is exactly the per-group sum of the primitive's
    # reports. This pins the discriminating behaviour: the empty collection
    # yields 0, and an object repeated across separate groups is summed once per
    # group (so duplicates split between groups are counted twice).
    Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
    # post-conditions-end
    # impl-start
    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= off and off <= len(keys))
        # `off` advances one whole group per step (capped at the end), so the
        # consumed prefix is always a whole number of groups; the running total
        # is what those consumed groups reported, and the still-to-process
        # suffix accounts for the rest of the per-group sum.
        Invariant(total >= 0)
        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
                  batched_total(ToSeq(keys), group_size))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(keys) - off.
        Invariant(MustTerminate(len(keys) - off))
        # invariants-end
        rem = ToSeq(keys).drop(off)
        # The current group is the first `group_size` keys of the remaining
        # suffix; the suffix after this step drops exactly that group.
        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
        Assert(len(rem) > 0)
        Assert(batched_total(rem, group_size) ==
               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
        step = group_size
        if step > len(keys) - off:
            step = len(keys) - off
        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
        total = total + matched_rows(rem.take(group_size))
        off = off + step
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Bundle django__django-14559/nagini (repaired: model.py/refinement.md/mapping.md dated Aug 13 03:11-03:21, NEWER than the recorded BROKEN verdict.md dated Aug 13 00:00). The prior break (verdict.md Role-1: atk_9.py = `return bulk_apply_count(keys, group_size)`, unbounded self-recursion whose faithful patch COMPLETED but RESOLVED=False via RecursionError) exploited Nagini partial-correctness / spec silence on termination. The repair adds Requires(MustTerminate(2)) to the precondition and Invariant(MustTerminate(len(keys)-off)) to the loop, closing that gap.

**Setup:** SBU_BENCHMARK_DIR=benchmark-verified; verifier = python -m swebench_unified.adversary + scripts/nagini_verify.sh (nagini env). All 8 attacks confirmed byte-identical spec: `same-spec` exit 0 for each, and a direct region-diff shows axioms/pure/pre-conditions/post-conditions regions byte-identical to model.py (only impl region edited). Verifications run concurrently in 3 batches (<=3 JVMs each) via background bash jobs.

Positive control = current model.py: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0, 'Verification successful' (11.3s).

Attack results (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14559 <path>`; verify detail via `adversary verify`):
- atk_1 (RE-ENCODED PRIOR BREAK: unbounded self-recursion `return bulk_apply_count(keys, group_size)`): weakness rc=2 NOT-A-COUNTEREXAMPLE (does not verify). verify FAILED 11.6s: 'atk_1.py:92: Obligation leak check failed. Callee bulk_apply_count might not take all unsatisfied obligations from the caller.' => the exact recorded break is now REJECTED by MustTerminate.
- atk_2 (contradictory-guard infinite loop `while i<1: Invariant(i==0)` then return None): rc=2. verify FAILED 11.4s: 'Obligation leak check failed. Loop might not keep promise to terminate.'
- atk_3 (non-terminating `while total>=0` then wrong return 999999): rc=2. verify FAILED 11.2s: 'Obligation leak check failed. Loop might not keep promise to terminate.'
- atk_4 (off-by-one value error: correct accumulating loop, `return total + 1`): rc=2. verify FAILED 11.0s: 'Loop invariant might not be preserved ... total + batched_total(drop(off)) == batched_total(...) might not hold' (the strengthened value invariant catches it).
- atk_5 (boundary: drop final partial group, guard `off+group_size<=len(keys)`): rc=2. verify FAILED 10.2s: 'Postcondition ... Result() == batched_total(...) might not hold.'
- atk_6 (partial-domain/control-flow: count only first group, `return matched_rows(take(group_size))`): rc=2. verify FAILED 10.2s: 'Postcondition ... Result() == batched_total(...) might not hold.'
- atk_7 (ungrounded-oracle echo: `return batched_total(ToSeq(keys), group_size)`): rc=2. verify FAILED 10.1s: only on 'Result() >= 0' (Nagini can't prove batched_total>=0 without the loop invariant) — behaviourally correct but does NOT verify, so not a weakness.
- atk_8 (control-flow-effect: no accumulation, `return 0` on non-empty): rc=2. verify FAILED 10.1s: 'Postcondition ... Result() == batched_total(...) might not hold.'

**Every attack that came back CANDIDATE:** NONE. Therefore no faithful refined patch needed materialization/run_resolve; there is no verifying wrong impl to break the spec.

**Prepatch reproduction:** model_prepatch.py (non-empty path discards count -> None) and model_prepatch_2.py (empty path bare return None) BOTH fail verify (rc=1) on 'Postcondition ... Result() is not None might not hold' (9.8-10.2s) — the fix is load-bearing (G-DIFF holds).

refinement.md A-leg audit: legs B1..B5 are R / A-consumed / I with NO kind-3 (per §D); deep_model_references=[] (meta confirms). The single axiom matched_rows is A-consumed (@Pure @ContractOnly, Ensures(Result()>=0)), byte-identical across all attacks, mapping to django.db.models.query.QuerySet.update's non-negative cursor.rowcount (mapping.md §3.1); it is the weakest contract the proof consumes and is G-AX-sound (meta G-AX pass, 20125 obs, duplicate collapse [pk,pk]->1 vs 1+1->2 recorded). The model<->patch correspondence is faithful and the termination obligation that closes the prior verify-not-correct gap is now present in the frozen precondition and consumed by the loop measure. No A-leg mis-statement; no A-reference deep-model to audit.

**Conclusion:** >=5 (8) distinct same-spec wrong impls run, including the re-encoded prior break; none verifies. Spec is SOUND for this repaired bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14559.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batched persistence operation applies a change to an ordered collection of
  stored objects, identified by their primary keys, in fixed-size groups. It
  must report a count of the affected stored rows to its caller (rather than
  reporting nothing):

    (1) The reported value is always a count, never the absent value. In
        particular, when the collection is empty no group is processed and the
        reported count is zero.

    (2) The reported count is the sum, over the successive fixed-size groups the
        collection is split into, of the number of rows the underlying
        row-affecting primitive reports for that group. Because the grouping is
        by position and the primitive reports per group, an object that appears
        more than once is counted once per group it falls into: two appearances
        within a single group contribute the primitive's single-group count for
        that group, whereas two appearances placed into separate groups are
        each reported by their own group and therefore summed twice.

The collection of objects is modelled as a `List[int]` of primary-key values;
the group size is a positive `int`. The unchanged row-affecting primitive (the
per-group database update) is axiomatized: given the key values of one group it
reports a non-negative number of affected rows. The reported total is the
absent value (`None`) when no count is produced and a non-negative `int`
otherwise (`Optional[int]`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def matched_rows(group_keys: PSeq[int]) -> int:
    """Rows reported by the unchanged per-group row-affecting primitive (the
    database update issued against the rows whose key is in `group_keys`). The
    primitive matches each present stored row at most once, so the reported
    value is a non-negative count. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def batched_total(keys: PSeq[int], group_size: int) -> int:
    """The total reported across the successive fixed-size groups the key
    sequence is split into, front-to-back. Front-recursive (one unfold per
    group) so the forward impl loop can discharge it: the first `group_size`
    keys form one group, the remainder is split recursively. An empty sequence
    yields zero (no group, hence count zero)."""
    Requires(group_size >= 1)
    if len(keys) == 0:
        return 0
    return matched_rows(keys.take(group_size)) + batched_total(keys.drop(group_size), group_size)
# pure-end


def bulk_apply_count(keys: List[int], group_size: int) -> Optional[int]:
    # pre-conditions-start
    # `keys` is read-only: the operation reports a count and does not mutate the
    # collection it is given, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(group_size >= 1)
    # The count must actually be delivered: this termination obligation forbids
    # implementations that would satisfy the value postcondition only vacuously
    # by never returning (frozen loops or unbounded self-calls).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(keys), 1 / 2))
    # (1) a count is always produced — never the absent value — and it is
    # non-negative; the empty collection produces zero.
    Ensures(Result() is not None)
    Ensures(Result() >= 0)  # type: ignore
    # (2) the produced count is exactly the per-group sum of the primitive's
    # reports. This pins the discriminating behaviour: the empty collection
    # yields 0, and an object repeated across separate groups is summed once per
    # group (so duplicates split between groups are counted twice).
    Ensures(Result() == batched_total(ToSeq(keys), group_size))  # type: ignore
    # post-conditions-end
    # impl-start
    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(0 <= off and off <= len(keys))
        # `off` advances one whole group per step (capped at the end), so the
        # consumed prefix is always a whole number of groups; the running total
        # is what those consumed groups reported, and the still-to-process
        # suffix accounts for the rest of the per-group sum.
        Invariant(total >= 0)
        Invariant(total + batched_total(ToSeq(keys).drop(off), group_size) ==
                  batched_total(ToSeq(keys), group_size))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(keys) - off.
        Invariant(MustTerminate(len(keys) - off))
        # invariants-end
        rem = ToSeq(keys).drop(off)
        # The current group is the first `group_size` keys of the remaining
        # suffix; the suffix after this step drops exactly that group.
        Assert(rem.take(group_size) == ToSeq(keys).drop(off).take(group_size))
        Assert(len(rem) > 0)
        Assert(batched_total(rem, group_size) ==
               matched_rows(rem.take(group_size)) + batched_total(rem.drop(group_size), group_size))
        step = group_size
        if step > len(keys) - off:
            step = len(keys) - off
        Assert(rem.drop(group_size) == ToSeq(keys).drop(off + step))
        total = total + matched_rows(rem.take(group_size))
        off = off + step
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Bundle django__django-14559/nagini (repaired: model.py/refinement.md/mapping.md dated Aug 13 03:11-03:21, NEWER than the recorded BROKEN verdict.md dated Aug 13 00:00). The prior break (verdict.md Role-1: atk_9.py = `return bulk_apply_count(keys, group_size)`, unbounded self-recursion whose faithful patch COMPLETED but RESOLVED=False via RecursionError) exploited Nagini partial-correctness / spec silence on termination. The repair adds Requires(MustTerminate(2)) to the precondition and Invariant(MustTerminate(len(keys)-off)) to the loop, closing that gap.

**Setup:** SBU_BENCHMARK_DIR=benchmark-verified; verifier = python -m swebench_unified.adversary + scripts/nagini_verify.sh (nagini env). All 8 attacks confirmed byte-identical spec: `same-spec` exit 0 for each, and a direct region-diff shows axioms/pure/pre-conditions/post-conditions regions byte-identical to model.py (only impl region edited). Verifications run concurrently in 3 batches (<=3 JVMs each) via background bash jobs.

Positive control = current model.py: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0, 'Verification successful' (11.3s).

Attack results (cmd: `python -m swebench_unified.adversary weakness nagini django__django-14559 <path>`; verify detail via `adversary verify`):
- atk_1 (RE-ENCODED PRIOR BREAK: unbounded self-recursion `return bulk_apply_count(keys, group_size)`): weakness rc=2 NOT-A-COUNTEREXAMPLE (does not verify). verify FAILED 11.6s: 'atk_1.py:92: Obligation leak check failed. Callee bulk_apply_count might not take all unsatisfied obligations from the caller.' => the exact recorded break is now REJECTED by MustTerminate.
- atk_2 (contradictory-guard infinite loop `while i<1: Invariant(i==0)` then return None): rc=2. verify FAILED 11.4s: 'Obligation leak check failed. Loop might not keep promise to terminate.'
- atk_3 (non-terminating `while total>=0` then wrong return 999999): rc=2. verify FAILED 11.2s: 'Obligation leak check failed. Loop might not keep promise to terminate.'
- atk_4 (off-by-one value error: correct accumulating loop, `return total + 1`): rc=2. verify FAILED 11.0s: 'Loop invariant might not be preserved ... total + batched_total(drop(off)) == batched_total(...) might not hold' (the strengthened value invariant catches it).
- atk_5 (boundary: drop final partial group, guard `off+group_size<=len(keys)`): rc=2. verify FAILED 10.2s: 'Postcondition ... Result() == batched_total(...) might not hold.'
- atk_6 (partial-domain/control-flow: count only first group, `return matched_rows(take(group_size))`): rc=2. verify FAILED 10.2s: 'Postcondition ... Result() == batched_total(...) might not hold.'
- atk_7 (ungrounded-oracle echo: `return batched_total(ToSeq(keys), group_size)`): rc=2. verify FAILED 10.1s: only on 'Result() >= 0' (Nagini can't prove batched_total>=0 without the loop invariant) — behaviourally correct but does NOT verify, so not a weakness.
- atk_8 (control-flow-effect: no accumulation, `return 0` on non-empty): rc=2. verify FAILED 10.1s: 'Postcondition ... Result() == batched_total(...) might not hold.'

**Every attack that came back CANDIDATE:** NONE. Therefore no faithful refined patch needed materialization/run_resolve; there is no verifying wrong impl to break the spec.

**Prepatch reproduction:** model_prepatch.py (non-empty path discards count -> None) and model_prepatch_2.py (empty path bare return None) BOTH fail verify (rc=1) on 'Postcondition ... Result() is not None might not hold' (9.8-10.2s) — the fix is load-bearing (G-DIFF holds).

refinement.md A-leg audit: legs B1..B5 are R / A-consumed / I with NO kind-3 (per §D); deep_model_references=[] (meta confirms). The single axiom matched_rows is A-consumed (@Pure @ContractOnly, Ensures(Result()>=0)), byte-identical across all attacks, mapping to django.db.models.query.QuerySet.update's non-negative cursor.rowcount (mapping.md §3.1); it is the weakest contract the proof consumes and is G-AX-sound (meta G-AX pass, 20125 obs, duplicate collapse [pk,pk]->1 vs 1+1->2 recorded). The model<->patch correspondence is faithful and the termination obligation that closes the prior verify-not-correct gap is now present in the frozen precondition and consumed by the loop measure. No A-leg mis-statement; no A-reference deep-model to audit.

**Conclusion:** >=5 (8) distinct same-spec wrong impls run, including the re-encoded prior break; none verifies. Spec is SOUND for this repaired bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Model verifies (nagini_verify exit 0, 10.5s) and is byte-identical spec (adversary same-spec exit 0). Faithfulness assessment (spec-too-strong / drift): the abstraction map is sound and NOT over-constrained. group_size>=1 mirrors the reachable domain of effective batch_size (min(batch_size,max_batch_size) or max_batch_size, always >=1; user 0/negative rejected earlier or falls back). keys:List[int] is the faithful pk projection since update(pk__in=pks) depends only on pks, and order+multiplicity are preserved by tuple(objs) then [obj.pk for obj in batch_objs]. matched_rows is a FREE axiom (Ensures Result()>=0 only), so the spec never assumes a stronger per-group behavior than the real update() delivers; the total is modeled deeply via the per-group fold batched_total, matching the accumulating loop exactly. No postcondition demands more than post-patch bulk_update guarantees. I could construct no input on which the modeled function disagrees with the real callee. NOTE on the separately-recorded G-EQ fail (Role-1 verdict.md, atk_9 unbounded self-recursion verifies but its patch does not resolve): that is a spec-too-WEAK / partial-correctness soundness gap addressed by the MustTerminate obligation now present in this model.py — it is a faithfulness-preserving strengthening (rejects non-terminating impls), NOT a drift where the spec disagrees with the real repo. It is out of scope for the faithfulness (spec-too-strong) gate.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (spec view clean). Semantic review: the gold edit is (1) empty-case `return` -> `return 0` and (2) `rows_updated = 0; rows_updated += self.filter(pk__in=pks).update(...)` per group; `return rows_updated`. The public problem_statement already discloses the full fix strategy: bulk_update should return the number of rows matched instead of None, it 'simply calls update() repeatedly,' and 'the return values could simply be added and returned.' The spec view restates exactly this (report a count instead of the absent value; the count is the per-group sum of the primitive's reports) in fully abstract vocabulary. It names NO patched symbol (bulk_update/update/rows_updated), NO patched file path (django/db/models/query.py), reproduces NO diff line, and carries no fix/bug narration. The empty->0 edge case and the across-group duplicate-double-count are behavioral consequences of the publicly-described summing approach, not additional edits. Grouping/batching is pre-existing repo structure, not introduced by the patch. Nothing in the spec view reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
