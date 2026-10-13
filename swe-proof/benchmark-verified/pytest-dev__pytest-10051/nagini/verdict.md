# P2 adversarial audit — pytest-dev__pytest-10051

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_rebind_prepatch.py`, `atk_2_noop_discard.py`, `atk_3_clear_then_rebind.py`, `atk_5_double_append.py`, `atk_7_recursion.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4_guarded_clear.py`, `atk_6_gold_echo.py`, `atk_8_clear_via_view.py`, `atk_9_append_then_clear.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_10_insert_front.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_rebind_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,9 +119,7 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
-    empty_in_place(buf.items)
+    buf.items = []
     return
     # impl-end
 
```

Attack 2 — `atk_2_noop_discard.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,9 +119,6 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
-    empty_in_place(buf.items)
     return
     # impl-end
 
```

Attack 3 — `atk_3_clear_then_rebind.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,9 +119,8 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
     empty_in_place(buf.items)
+    buf.items = []
     return
     # impl-end
 
```

Attack 4 — `atk_4_guarded_clear.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,9 +119,8 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
-    empty_in_place(buf.items)
+    if len(buf.items) > 0:
+        empty_in_place(buf.items)
     return
     # impl-end
 
```

Attack 5 — `atk_5_double_append.py` → rejected (same spec, does not verify — good)

```diff
@@ -151,5 +151,6 @@
     # post-conditions-end
     # impl-start
     buf.items.append(item)
+    buf.items.append(item)
     return
     # impl-end
```

Attack 6 — `atk_6_gold_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,8 +119,6 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
     empty_in_place(buf.items)
     return
     # impl-end
```

Attack 7 — `atk_7_recursion.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,8 +119,7 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
+    discard_captured(buf, view)
     empty_in_place(buf.items)
     return
     # impl-end
```

Attack 8 — `atk_8_clear_via_view.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,9 +119,7 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
-    empty_in_place(buf.items)
+    empty_in_place(view)
     return
     # impl-end
 
```

Attack 9 — `atk_9_append_then_clear.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -119,8 +119,7 @@
     Ensures(view is buf.items)
     # post-conditions-end
     # impl-start
-    # buf.items.clear()  -- empty the existing list in place, preserving its
-    # object identity (and hence the observer's earlier reference to it).
+    buf.items.append(0)
     empty_in_place(buf.items)
     return
     # impl-end
```

Attack 10 — `atk_10_insert_front.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -150,6 +150,6 @@
     Ensures(view[0] == item)
     # post-conditions-end
     # impl-start
-    buf.items.append(item)
+    buf.items.insert(0, item)
     return
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-10051.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture buffer holds a list of captured items. Earlier, while a phase was
  being prepared, an external observer was handed a reference to that very list
  object (the per-phase view of the captured items): the observer's reference
  and the buffer's list are, from that moment on, two names for the SAME list
  object.

  Discarding the buffer's captured items must leave that shared list EMPTY while
  keeping it the SAME object, so that the observer that still holds the earlier
  reference agrees with the buffer afterwards:

    (1) after the discard, the buffer's captured-items list is empty;

    (2) after the discard, the buffer's captured-items list is the SAME object it
        was before the discard (its identity is preserved, not replaced by a
        fresh empty list);

  and consequently the previously-handed-out observer reference, which named
  that object before the discard, still names the buffer's live list afterwards:

    (3) the observer's reference and the buffer's captured-items list are the
        same object after the discard, the observer sees it as empty, and any
        item subsequently captured into the buffer is visible through the
        observer's reference as well.

  A discard that rebinds the buffer to a brand-new empty list would satisfy "the
  buffer is now empty" but would orphan the observer's reference — it would
  point at the old, detached list and diverge from the buffer permanently. The
  identity clause (2)/(3) is exactly what forbids that.

The buffer is modelled as a minimal object exposing only the touched field: its
list of captured items (`items`), where each captured item is abstracted to
an `int` identity (the tested behaviour observes only how many items are present
and that the observer's list tracks the buffer's, not the items' internals). The
observer reference is a second name (`view`) required to alias the buffer's list
on entry. The in-place list-emptying primitive this discard builds on (an unchanged
language builtin that empties a list WITHOUT replacing the object) is
axiomatized: `empty_in_place`. Its identity-preserving contract is the crux and
is validated against real Python out-of-band by axiom_check.py (G-AX).

Termination (total correctness): both modelled operations are single bounded
steps on one shared list object (one in-place emptying; one append) that must
actually ANSWER — return to their caller with the discard/append performed.
Nagini is a partial-correctness verifier by default, so without an explicit
obligation a non-terminating implementation (e.g. bare self-recursion before
or after doing the work) satisfies every `Ensures` vacuously while never
actually delivering the emptied/extended list to its caller; the real
`clear`/`emit` always return. The obligation is carried as `MustTerminate` in
each precondition, with a strictly smaller measure on the consumed
`empty_in_place` axiom (the builtin always terminates) so a routine may invoke
the primitive but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CaptureBuffer:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        self.items = []  # type: List[int]


# axioms-start
@ContractOnly
def empty_in_place(xs: List[int]) -> None:
    """The unchanged language builtin that empties a list IN PLACE: it removes
    every element of `xs` while leaving `xs` the SAME object (it does not bind a
    fresh empty list). This is the primitive this discard is built on; its
    object-identity-preserving behaviour is the crux. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(xs)))
    # The builtin is a single bounded step: it always terminates (measure 1,
    # strictly below the callers' measure 2, so callers may consume it but a
    # self-recursive caller cannot discharge its own obligation).
    Requires(MustTerminate(1))
    Ensures(Acc(list_pred(xs)))
    Ensures(len(xs) == 0)
    Ensures(xs is Old(xs))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def discard_captured(buf: CaptureBuffer, view: List[int]) -> None:
    # pre-conditions-start
    # The buffer fully owns its captured-items list (it is about to mutate it).
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    # `view` is the reference an external observer was handed earlier: on entry
    # it is the SAME object as the buffer's captured-items list (full ownership
    # of that one object is held under the single `buf.items` name).
    Requires(view is buf.items)
    # TERMINATION: the discard is one bounded in-place emptying that must
    # actually ANSWER (return with the shared list emptied). Without the
    # obligation a diverging implementation satisfies every Ensures vacuously
    # while never actually handing the emptied list back to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    # (1) the captured-items list is now empty ...
    Ensures(len(buf.items) == 0)
    # (2) ... and it is the SAME list object it was before the discard (its
    # identity is preserved; it was emptied in place, not replaced).
    Ensures(buf.items is Old(buf.items))
    # (3) therefore the observer's earlier reference still names the buffer's
    # live list: `view` is the buffer's captured-items list afterwards, and the
    # observer sees it as empty (the same emptiness the buffer sees).
    Ensures(view is buf.items)
    # post-conditions-end
    # impl-start
    # buf.items.clear()  -- empty the existing list in place, preserving its
    # object identity (and hence the observer's earlier reference to it).
    empty_in_place(buf.items)
    return
    # impl-end


def append_then_visible(buf: CaptureBuffer, view: List[int], item: int) -> None:
    # pre-conditions-start
    # After a discard the observer reference still aliases the live list; capturing
    # a new item into the buffer must be visible through that observer reference.
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    Requires(view is buf.items)
    Requires(len(buf.items) == 0)
    # TERMINATION: capturing one item is a single bounded append that must
    # actually ANSWER (return with the item visible through the alias); a
    # diverging implementation would satisfy the Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    Ensures(view is buf.items)
    # the newly captured item is now in the buffer's list ...
    Ensures(len(buf.items) == 1)
    Ensures(buf.items[0] == item)
    # ... and, because the observer reference is the same object, it is visible
    # through the observer's view too.
    Ensures(len(view) == 1)
    Ensures(view[0] == item)
    # post-conditions-end
    # impl-start
    buf.items.append(item)
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for pytest-dev__pytest-10051 (nagini). adversary run via python -m swebench_unified.adversary with SBU_BENCHMARK_DIR=benchmark-verified. All attacks copy model.py editing ONLY impl regions (axioms/@ContractOnly/Requires/Ensures byte-identical; confirmed same-spec exit 0 for all 10).

POSITIVE CONTROL: pos_control.py (unchanged model.py) -> `adversary verify` exit 0 (VERIFIES). Ran concurrently in batches of 3 (each JVM+Z3).

ATTACK BATTERY (10 distinct wrong impls) — command `adversary weakness nagini pytest-dev__pytest-10051 <atk>`:
 * atk_1_rebind_prepatch (buf.items=[]  — the PREPATCH BUG): exit 2, NOT verified. nagini_verify error: 'Postcondition of discard_captured might not hold. Assertion (buf.items is Old(buf.items)) might not hold.' => prepatch bug reproduced/rejected by identity clause A5. (prepatch_reproduced=true)
 * atk_2_noop_discard (return only; partial-domain, only correct when already empty): exit 2, rejected (len==0 postcond fails on nonempty entry).
 * atk_3_clear_then_rebind (empty_in_place then buf.items=[]; boundary/order): exit 2, rejected (identity clause).
 * atk_5_double_append (append twice; count boundary): exit 2, rejected — 'Postcondition of append_then_visible ... (len(buf.items) == 1) might not hold.'
 * atk_7_recursion (self-call before work; control-flow/divergence): exit 2, rejected — 'Obligation leak check failed. Callee discard_captured might not take all unsatisfied obligations' => MustTerminate(2) closes the divergence loophole as refinement.md §C2 claims.
 * atk_10_insert_front (insert(0,item); ungrounded partial-domain on emit): exit 2, rejected — nagini 'Not supported: Unsupported builtin function' (infra reject, not a spec candidate; append-side attacks map to no gold change since emit is unchanged).

 CANDIDATES (same-spec AND verify, exit 0) — faithful refined patch materialized from a base_commit (aa55975c) checkout extracted from the official image and RUN through the official harness (run_resolve, retries):
 * atk_4_guarded_clear (if len>0: empty_in_place): VERIFIES 11.9s. patch_atk_4_guarded_clear.diff (guards self.records.clear() on nonemptiness) -> RESOLVED=true (1 attempt).
 * atk_6_gold_echo (empty_in_place(buf.items) == gold): VERIFIES 11.6s. patch_atk_6_gold_echo.diff == gold body -> RESOLVED=true (1 attempt).
 * atk_8_clear_via_view (empty_in_place(view), view aliases records): VERIFIES 13.6s. patch_atk_8_clear_via_view.diff (clear via a local alias of self.records) -> RESOLVED=true (1 attempt).
 * atk_9_append_then_clear (append spurious then empty_in_place; net empty+identity): VERIFIES 13.3s. patch_atk_9_append_then_clear.diff -> RESOLVED=true (1 attempt).
 Every verifying wrong impl's faithful patch RESOLVES => no verify⇏correct break.

CORRESPONDENCE / A-LEG AUDIT (the emphasis of this pass):
 * The single A-consumed leg is empty_in_place ↔ Python builtin list.clear() (refinement.md A3, mapping.md 3.1). G-AX: ran axiom_check.py -> exit 0 ('sound on 5 boundary + 20000 fuzz inputs'). The axiom's Ensures (len==0, xs is Old(xs), MustTerminate(1)) are exactly list.clear's guarantees — not stronger, so not ungrounded. No axiom about the function-under-change (that IS the modeled discard_captured), so no A-reference over-claim.
 * refinement.md legs are all R / A-consumed / I — NO kind-3. I explicitly stress-tested the one documented I-leg that carries no modeled obligation: §C's `self.stream = StringIO()` (the captured-text reset), which the model deliberately does not model. I built atk_6b_no_stream_reset.diff — a refinement of the verifying gold-echo impl that DROPS the stream reset — and resolve-ran it: RESOLVED=false, CONSISTENT over 2 attempts. Failure isolated (report_atk_6b_no_stream_reset.json): FAIL_TO_PASS 1/1 PASS (aliasing fix works), PASS_TO_PASS fails on testing/logging/test_fixture.py::test_clear which asserts `not caplog.text`. Confirmed at base_commit that PRE-patch reset() and POST-patch gold clear() BOTH do `self.stream = StringIO()` byte-identically -> it is a genuine identical op on both sides of the bug→fix delta (a true I-leg), correctly classified by refinement.md §C as 'observationally untouched by the delta' and carrying no verification obligation. atk_6b is therefore an UNFAITHFUL refinement (it removes a documented required I-leg), NOT a valid counterexample; its non-resolution instead confirms §C's I-leg is load-bearing and correctly stated, and that the faithful refinement (atk_6) resolves.

VERDICT: SOUND. 10 same-spec attacks run (≥5 distinct wrong classes: prepatch-rebind, partial-domain no-op, boundary order, count-boundary double-append, control-flow/divergence recursion, ungrounded emit insert), prepatch bug reproduced, all 4 verifying candidates' faithful patches RESOLVE, G-AX passes, no kind-3 leg, A-consumed correspondence holds, and the deliberate I-leg-dropping probe (atk_6b) confirms the spec/refinement correctly requires the documented identical op. No verifying wrong impl yields a faithful non-resolving patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_rebind_prepatch.py`, `atk_2_noop_discard.py`, `atk_3_clear_then_rebind.py`, `atk_5_double_append.py`, `atk_7_recursion.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4_guarded_clear.py`, `atk_6_gold_echo.py`, `atk_8_clear_via_view.py`, `atk_9_append_then_clear.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_10_insert_front.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_rebind_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_noop_discard.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_clear_then_rebind.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_guarded_clear.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_double_append.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_gold_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_recursion.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_clear_via_view.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_append_then_clear.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_insert_front.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-10051.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture buffer holds a list of captured items. Earlier, while a phase was
  being prepared, an external observer was handed a reference to that very list
  object (the per-phase view of the captured items): the observer's reference
  and the buffer's list are, from that moment on, two names for the SAME list
  object.

  Discarding the buffer's captured items must leave that shared list EMPTY while
  keeping it the SAME object, so that the observer that still holds the earlier
  reference agrees with the buffer afterwards:

    (1) after the discard, the buffer's captured-items list is empty;

    (2) after the discard, the buffer's captured-items list is the SAME object it
        was before the discard (its identity is preserved, not replaced by a
        fresh empty list);

  and consequently the previously-handed-out observer reference, which named
  that object before the discard, still names the buffer's live list afterwards:

    (3) the observer's reference and the buffer's captured-items list are the
        same object after the discard, the observer sees it as empty, and any
        item subsequently captured into the buffer is visible through the
        observer's reference as well.

  A discard that rebinds the buffer to a brand-new empty list would satisfy "the
  buffer is now empty" but would orphan the observer's reference — it would
  point at the old, detached list and diverge from the buffer permanently. The
  identity clause (2)/(3) is exactly what forbids that.

The buffer is modelled as a minimal object exposing only the touched field: its
list of captured items (`items`), where each captured item is abstracted to
an `int` identity (the tested behaviour observes only how many items are present
and that the observer's list tracks the buffer's, not the items' internals). The
observer reference is a second name (`view`) required to alias the buffer's list
on entry. The in-place list-emptying primitive this discard builds on (an unchanged
language builtin that empties a list WITHOUT replacing the object) is
axiomatized: `empty_in_place`. Its identity-preserving contract is the crux and
is validated against real Python out-of-band by axiom_check.py (G-AX).

Termination (total correctness): both modelled operations are single bounded
steps on one shared list object (one in-place emptying; one append) that must
actually ANSWER — return to their caller with the discard/append performed.
Nagini is a partial-correctness verifier by default, so without an explicit
obligation a non-terminating implementation (e.g. bare self-recursion before
or after doing the work) satisfies every `Ensures` vacuously while never
actually delivering the emptied/extended list to its caller; the real
`clear`/`emit` always return. The obligation is carried as `MustTerminate` in
each precondition, with a strictly smaller measure on the consumed
`empty_in_place` axiom (the builtin always terminates) so a routine may invoke
the primitive but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CaptureBuffer:
    def __init__(self) -> None:
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)  # type: ignore
        self.items = []  # type: List[int]


# axioms-start
@ContractOnly
def empty_in_place(xs: List[int]) -> None:
    """The unchanged language builtin that empties a list IN PLACE: it removes
    every element of `xs` while leaving `xs` the SAME object (it does not bind a
    fresh empty list). This is the primitive this discard is built on; its
    object-identity-preserving behaviour is the crux. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(xs)))
    # The builtin is a single bounded step: it always terminates (measure 1,
    # strictly below the callers' measure 2, so callers may consume it but a
    # self-recursive caller cannot discharge its own obligation).
    Requires(MustTerminate(1))
    Ensures(Acc(list_pred(xs)))
    Ensures(len(xs) == 0)
    Ensures(xs is Old(xs))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def discard_captured(buf: CaptureBuffer, view: List[int]) -> None:
    # pre-conditions-start
    # The buffer fully owns its captured-items list (it is about to mutate it).
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    # `view` is the reference an external observer was handed earlier: on entry
    # it is the SAME object as the buffer's captured-items list (full ownership
    # of that one object is held under the single `buf.items` name).
    Requires(view is buf.items)
    # TERMINATION: the discard is one bounded in-place emptying that must
    # actually ANSWER (return with the shared list emptied). Without the
    # obligation a diverging implementation satisfies every Ensures vacuously
    # while never actually handing the emptied list back to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    # (1) the captured-items list is now empty ...
    Ensures(len(buf.items) == 0)
    # (2) ... and it is the SAME list object it was before the discard (its
    # identity is preserved; it was emptied in place, not replaced).
    Ensures(buf.items is Old(buf.items))
    # (3) therefore the observer's earlier reference still names the buffer's
    # live list: `view` is the buffer's captured-items list afterwards, and the
    # observer sees it as empty (the same emptiness the buffer sees).
    Ensures(view is buf.items)
    # post-conditions-end
    # impl-start
    # buf.items.clear()  -- empty the existing list in place, preserving its
    # object identity (and hence the observer's earlier reference to it).
    empty_in_place(buf.items)
    return
    # impl-end


def append_then_visible(buf: CaptureBuffer, view: List[int], item: int) -> None:
    # pre-conditions-start
    # After a discard the observer reference still aliases the live list; capturing
    # a new item into the buffer must be visible through that observer reference.
    Requires(Acc(buf.items) and Acc(list_pred(buf.items)))
    Requires(view is buf.items)
    Requires(len(buf.items) == 0)
    # TERMINATION: capturing one item is a single bounded append that must
    # actually ANSWER (return with the item visible through the alias); a
    # diverging implementation would satisfy the Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(buf.items) and Acc(list_pred(buf.items)))
    Ensures(view is buf.items)
    # the newly captured item is now in the buffer's list ...
    Ensures(len(buf.items) == 1)
    Ensures(buf.items[0] == item)
    # ... and, because the observer reference is the same object, it is visible
    # through the observer's view too.
    Ensures(len(view) == 1)
    Ensures(view[0] == item)
    # post-conditions-end
    # impl-start
    buf.items.append(item)
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for pytest-dev__pytest-10051 (nagini). adversary run via python -m swebench_unified.adversary with SBU_BENCHMARK_DIR=benchmark-verified. All attacks copy model.py editing ONLY impl regions (axioms/@ContractOnly/Requires/Ensures byte-identical; confirmed same-spec exit 0 for all 10).

POSITIVE CONTROL: pos_control.py (unchanged model.py) -> `adversary verify` exit 0 (VERIFIES). Ran concurrently in batches of 3 (each JVM+Z3).

ATTACK BATTERY (10 distinct wrong impls) — command `adversary weakness nagini pytest-dev__pytest-10051 <atk>`:
 * atk_1_rebind_prepatch (buf.items=[]  — the PREPATCH BUG): exit 2, NOT verified. nagini_verify error: 'Postcondition of discard_captured might not hold. Assertion (buf.items is Old(buf.items)) might not hold.' => prepatch bug reproduced/rejected by identity clause A5. (prepatch_reproduced=true)
 * atk_2_noop_discard (return only; partial-domain, only correct when already empty): exit 2, rejected (len==0 postcond fails on nonempty entry).
 * atk_3_clear_then_rebind (empty_in_place then buf.items=[]; boundary/order): exit 2, rejected (identity clause).
 * atk_5_double_append (append twice; count boundary): exit 2, rejected — 'Postcondition of append_then_visible ... (len(buf.items) == 1) might not hold.'
 * atk_7_recursion (self-call before work; control-flow/divergence): exit 2, rejected — 'Obligation leak check failed. Callee discard_captured might not take all unsatisfied obligations' => MustTerminate(2) closes the divergence loophole as refinement.md §C2 claims.
 * atk_10_insert_front (insert(0,item); ungrounded partial-domain on emit): exit 2, rejected — nagini 'Not supported: Unsupported builtin function' (infra reject, not a spec candidate; append-side attacks map to no gold change since emit is unchanged).

 CANDIDATES (same-spec AND verify, exit 0) — faithful refined patch materialized from a base_commit (aa55975c) checkout extracted from the official image and RUN through the official harness (run_resolve, retries):
 * atk_4_guarded_clear (if len>0: empty_in_place): VERIFIES 11.9s. patch_atk_4_guarded_clear.diff (guards self.records.clear() on nonemptiness) -> RESOLVED=true (1 attempt).
 * atk_6_gold_echo (empty_in_place(buf.items) == gold): VERIFIES 11.6s. patch_atk_6_gold_echo.diff == gold body -> RESOLVED=true (1 attempt).
 * atk_8_clear_via_view (empty_in_place(view), view aliases records): VERIFIES 13.6s. patch_atk_8_clear_via_view.diff (clear via a local alias of self.records) -> RESOLVED=true (1 attempt).
 * atk_9_append_then_clear (append spurious then empty_in_place; net empty+identity): VERIFIES 13.3s. patch_atk_9_append_then_clear.diff -> RESOLVED=true (1 attempt).
 Every verifying wrong impl's faithful patch RESOLVES => no verify⇏correct break.

CORRESPONDENCE / A-LEG AUDIT (the emphasis of this pass):
 * The single A-consumed leg is empty_in_place ↔ Python builtin list.clear() (refinement.md A3, mapping.md 3.1). G-AX: ran axiom_check.py -> exit 0 ('sound on 5 boundary + 20000 fuzz inputs'). The axiom's Ensures (len==0, xs is Old(xs), MustTerminate(1)) are exactly list.clear's guarantees — not stronger, so not ungrounded. No axiom about the function-under-change (that IS the modeled discard_captured), so no A-reference over-claim.
 * refinement.md legs are all R / A-consumed / I — NO kind-3. I explicitly stress-tested the one documented I-leg that carries no modeled obligation: §C's `self.stream = StringIO()` (the captured-text reset), which the model deliberately does not model. I built atk_6b_no_stream_reset.diff — a refinement of the verifying gold-echo impl that DROPS the stream reset — and resolve-ran it: RESOLVED=false, CONSISTENT over 2 attempts. Failure isolated (report_atk_6b_no_stream_reset.json): FAIL_TO_PASS 1/1 PASS (aliasing fix works), PASS_TO_PASS fails on testing/logging/test_fixture.py::test_clear which asserts `not caplog.text`. Confirmed at base_commit that PRE-patch reset() and POST-patch gold clear() BOTH do `self.stream = StringIO()` byte-identically -> it is a genuine identical op on both sides of the bug→fix delta (a true I-leg), correctly classified by refinement.md §C as 'observationally untouched by the delta' and carrying no verification obligation. atk_6b is therefore an UNFAITHFUL refinement (it removes a documented required I-leg), NOT a valid counterexample; its non-resolution instead confirms §C's I-leg is load-bearing and correctly stated, and that the faithful refinement (atk_6) resolves.

VERDICT: SOUND. 10 same-spec attacks run (≥5 distinct wrong classes: prepatch-rebind, partial-domain no-op, boundary order, count-boundary double-append, control-flow/divergence recursion, ungrounded emit insert), prepatch bug reproduced, all 4 verifying candidates' faithful patches RESOLVE, G-AX passes, no kind-3 leg, A-consumed correspondence holds, and the deliberate I-leg-dropping probe (atk_6b) confirms the spec/refinement correctly requires the documented identical op. No verifying wrong impl yields a faithful non-resolving patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of pytest-dev__pytest-10051 nagini bundle. Verified against the real repo at base_commit aa55975c7d3f (worktree). model.py verifies (nagini_verify.sh exit 0, 12.1s); axiom_check.py exit 0 (5 boundary + 20000 fuzz on real list.clear()). Spec region (outside impl-start/impl-end) intact.

The gold fix routes LogCaptureFixture.clear -> new LogCaptureHandler.clear -> self.records.clear() (in-place, identity-preserving) replacing the buggy reset() -> self.records = [] (rebind, orphans the per-phase alias set at logging.py:699). Checked each modeled function against its real callee for a diverging input:

1. discard_captured <-> list.clear(): postconds len==0, buf.items is Old(buf.items), view is buf.items. Real CPython list.clear() empties in place and preserves object identity on EVERY input, so the stash[caplog_records_key][when] reference still names the live list. No diverging input.
2. empty_in_place axiom <-> list.clear(): the WEAKEST needed contract (len==0, xs is Old(xs), terminates). Universally true across CPython 3.x; axiom_check confirms. Not over-strong. No diverging input.
3. append_then_visible <-> LogCaptureHandler.emit (self.records.append): under the aliased+empty precondition the real emit appends and the item is visible through the get_records alias. LogRecord<->int abstraction preserves the only observables (len, index, identity). No diverging input.
4. Precondition view is buf.items faithfully reflects real phase wiring (item.stash[caplog_records_key][when] = caplog_handler.records at :699) — actual repo state, not an over-strong assumption.

Independent 100000-input fuzz simulation of the real callee sequence (clear then append with view aliasing) produced 0 divergences from the modeled postconditions. The spec is not stronger than what the gold-patched repo delivers: the gold fix satisfies every postcondition and no input makes the modeled functions disagree with the real callees. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = markers.spec_view(model.py) with impl regions elided (`... supplied by the consumer`), so the gold call site `buf.items.clear()`/`empty_in_place(buf.items)` is NOT exposed. Mechanical G-LEAK screen (leakage.screen) PASSES: no diff markers, no reproduced gold-patch line, no patched file/module path (`src/_pytest/logging.py`), no narration term (NARRATION_RE finds none — 'previously-handed-out' is hyphenated so it does not match), and no patched repo symbol leaked. Changed symbols are {clear, messages, reset}: `clear` appears in the spec docstring ('the real clear/emit always return') but `clear` is ALREADY public via `caplog.clear()` in the problem_statement (screen exempts symbols present in problem_statement); `reset` and `messages` are absent from the spec view; `emit` is unchanged by the patch. Semantically, the discriminating fix content — empty the list IN PLACE preserving object identity vs. rebind to a fresh empty list, so a previously-handed-out reference stays aliased — is exactly what the PUBLIC problem_statement already states: 'the latter gets replaced rather than cleared in caplog.clear(), which diverges the two objects.' The spec's identity clauses (2)/(3) and the 'rebind would orphan the observer's reference' prose are a faithful behavioral restatement of that publicly-disclosed bug, not a disclosure of the edit beyond problem_statement. No mention of the mechanism as a code edit, no reference to `records`/`handler`/`StringIO`/`get_records`/`caplog_records_key`, no file paths. Note: refinement.md/mapping.md DO disclose the gold edit verbatim, but those are auditor-facing artifacts, not part of the consumer spec view screened by G-LEAK/G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
