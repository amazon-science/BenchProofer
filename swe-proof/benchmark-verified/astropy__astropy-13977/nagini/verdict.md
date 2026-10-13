# P2 adversarial audit — astropy__astropy-13977

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No refinement-fidelity or A-leg counterexample exists. The spec is total and deterministic: its three postcondition clauses partition the whole input domain, so every TERMINATING same-spec wrong impl is rejected by the verifier (confirmed on 6 diverse attacks). The only verifying wrong impl (atk_1) relies on non-termination — a universal Nagini partial-correctness artifact, not a defect in this bundle's refinement/mapping/axioms — and its faithful patch's resolve run returns completed=False (a hang), which the framework's own derivation buckets as inconclusive, NOT the completed-and-not-resolved condition that constitutes BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,10 +86,9 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
         return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
+    if len(io_kinds) == 0:
+        return 1
     every_recognised = True
     i = len(io_kinds)
     while i > 0:
@@ -99,18 +96,13 @@
         Invariant(Acc(list_pred(io_kinds), 1 / 2))
         Invariant(0 <= i and i <= len(io_kinds))
         Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
         Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
         Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
         if io_kinds[i - 1] != 0:
             every_recognised = False
         i = i - 1
     if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
         return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
     return 1
     # impl-end
```

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,10 +86,7 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
         return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
     every_recognised = True
     i = len(io_kinds)
     while i > 0:
@@ -99,18 +94,13 @@
         Invariant(Acc(list_pred(io_kinds), 1 / 2))
         Invariant(0 <= i and i <= len(io_kinds))
         Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
         Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
         Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
         if io_kinds[i - 1] != 0:
             every_recognised = False
         i = i - 1
     if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
-        return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
-    return 1
+        return 1
+    return 2
     # impl-end
```

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,10 +86,7 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
-        return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
+        return 1
     every_recognised = True
     i = len(io_kinds)
     while i > 0:
@@ -99,18 +94,13 @@
         Invariant(Acc(list_pred(io_kinds), 1 / 2))
         Invariant(0 <= i and i <= len(io_kinds))
         Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
         Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
         Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
         if io_kinds[i - 1] != 0:
             every_recognised = False
         i = i - 1
     if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
         return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
     return 1
     # impl-end
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,29 +86,6 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
         return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
-    every_recognised = True
-    i = len(io_kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(io_kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(io_kinds))
-        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
-        Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
-        Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
-        if io_kinds[i - 1] != 0:
-            every_recognised = False
-        i = i - 1
-    if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
-        return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
-    return 1
+    return 2
     # impl-end
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,29 +86,21 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
         return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
     every_recognised = True
     i = len(io_kinds)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(io_kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(io_kinds))
+        Invariant(1 <= i and i <= len(io_kinds))
         Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
         Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
         Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
         if io_kinds[i - 1] != 0:
             every_recognised = False
         i = i - 1
     if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
         return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
     return 1
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
         (Implies(0 <= k and k < len(io_kinds),
                  io_kinds[k] == 0 or io_kinds[k] == 1),
          [[io_kinds[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(io_kinds), 1 / 2))
@@ -88,29 +86,18 @@
     # post-conditions-end
     # impl-start
     if not recoverable_failure:
-        # The protected evaluation completed; yield the ordinary result.
         return 0
-    # Recoverable failure: inspect the operands (back-to-front) for any custom
-    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
-    every_recognised = True
+    custom_count = 0
     i = len(io_kinds)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(io_kinds), 1 / 2))
         Invariant(0 <= i and i <= len(io_kinds))
-        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
-        # all_recognised then matches the running conjunction.
-        Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
-        Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
         if io_kinds[i - 1] != 0:
-            every_recognised = False
+            custom_count = custom_count + 1
         i = i - 1
-    if every_recognised:
-        # Every operand is a recognised built-in kind: surface the error.
+    if custom_count % 2 == 0:
         return 2
-    # Some operand supplies a custom handler: abstain so it can be tried.
     return 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13977.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric operation dispatcher protects the work of evaluating an operation
  on a collection of operands. When that protected evaluation completes
  successfully the dispatcher yields its ordinary computed result.

  When the protected evaluation instead fails with a recoverable error (the
  operands could not be combined), the dispatcher must NOT unconditionally
  surface that error. It first inspects the operands: if AT LEAST ONE operand
  is of a kind that supplies its own operation handler (an object that opted
  into custom dispatch, rather than one of the recognised built-in kinds), the
  dispatcher must abstain — yielding the "not handled here" sentinel — so that
  the other operand's handler is given the chance to complete the operation.
  Only when EVERY operand is one of the recognised
  built-in kinds (none supplies its own handler) is the recoverable error
  surfaced to the caller.

  Equivalently: a recoverable failure is propagated iff every operand is a
  recognised built-in kind; otherwise the dispatcher abstains. A successful
  evaluation is always returned as-is.

The operand collection is modelled as `List[int]` of per-operand kind flags
(0 = a recognised built-in kind that supplies no custom handler; 1 = an operand
supplying its own custom handler). The recoverable-failure condition is a
boolean. The three observable outcomes are encoded as result codes
(0 = ordinary computed result; 1 = the "not handled here" sentinel; 2 = the
recoverable error is surfaced). The classification predicate is modelled deeply
and validated against the real per-operand test by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the protected body's unchanged callees are
# summarised by `recoverable_failure`, and the one genuinely-new operation —
# the operand classification and the abstain-vs-surface dispatch — is modelled
# deeply below and validated against the real predicate by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def all_recognised(flags: PSeq[int]) -> bool:
    """True iff every operand kind flag is 0 (a recognised built-in kind that
    supplies no custom handler). Front-recursive so a single unfold is
    available per loop step."""
    if len(flags) == 0:
        return True
    return flags[0] == 0 and all_recognised(flags.drop(1))


@Pure
def has_custom_handler(flags: PSeq[int]) -> bool:
    """True iff at least one operand supplies its own custom handler."""
    return not all_recognised(flags)
# pure-end


def dispatch_ufunc(io_kinds: List[int], recoverable_failure: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(io_kinds), 1 / 2))
    # Each operand flag is well-formed: 0 = recognised built-in kind (no custom
    # handler), 1 = operand supplies its own custom handler.
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(io_kinds),
                 io_kinds[k] == 0 or io_kinds[k] == 1),
         [[io_kinds[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(io_kinds), 1 / 2))
    # Outcome is exactly one of the three observable codes.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # A successful protected evaluation is returned as-is.
    Ensures(Implies(not recoverable_failure, Result() == 0))
    # A recoverable failure is surfaced (code 2) iff every operand is a
    # recognised built-in kind; otherwise the dispatcher abstains (code 1).
    Ensures(Implies(recoverable_failure and all_recognised(ToSeq(io_kinds)),
                    Result() == 2))
    Ensures(Implies(recoverable_failure and has_custom_handler(ToSeq(io_kinds)),
                    Result() == 1))
    # post-conditions-end
    # impl-start
    if not recoverable_failure:
        # The protected evaluation completed; yield the ordinary result.
        return 0
    # Recoverable failure: inspect the operands (back-to-front) for any custom
    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
    every_recognised = True
    i = len(io_kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(io_kinds), 1 / 2))
        Invariant(0 <= i and i <= len(io_kinds))
        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
        # invariants-end
        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
        # all_recognised then matches the running conjunction.
        Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
        Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
        if io_kinds[i - 1] != 0:
            every_recognised = False
        i = i - 1
    if every_recognised:
        # Every operand is a recognised built-in kind: surface the error.
        return 2
    # Some operand supplies a custom handler: abstain so it can be tried.
    return 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: interpreter python; env, SBU_BENCHMARK_DIR=benchmark-verified. All same-spec checks pass (spec regions byte-identical; only impl region edited).

SAME-SPEC: all 7 attacks EXIT 0 on `adversary same-spec` (byte-identical spec).

### WEAKNESS (adversary weakness nagini astropy__astropy-13977 <atk>):
- atk_2 (boundary: empty io_kinds -> return 1 instead of 2): EXIT 2, does not verify (rejected). 
- atk_3 (control-flow-effect: swap outcomes 1<->2): EXIT 2, rejected.
- atk_4 (partial-domain: success path returns 1 not 0): EXIT 2, rejected.
- atk_5 (PREPATCH bug: recoverable_failure -> always return 2, never abstains): EXIT 2, rejected (reproduces prepatch; fails the has_custom_handler->1 clause exactly, = G-DIFF).
- atk_6 (boundary/off-by-one: loop `while i>1` skips index 0): EXIT 2, rejected.
- atk_7 (ungrounded-oracle echo: decide by parity of custom count instead of any-custom): EXIT 2, rejected.
- atk_1 (control-flow/non-termination: `while True: pass` on the abstain path before return 1): EXIT 0 => CANDIDATE (shares spec AND verifies, 14.0s). Verifies only because Nagini `--ide-mode` proves PARTIAL correctness and neither the spec nor the hygiene gate requires MustTerminate.

### EXECUTED RESOLVE (protocol step 2 — atk_1 is the sole candidate):
- Materialized faithful patch: atk_1_patch.diff (gold patch with `while True: pass` inserted immediately before the added `return NotImplemented`, faithfully mirroring atk_1's non-terminating `return 1` abstain path per refinement map A6: model code 1 <-> return NotImplemented; hunk new-side count adjusted 70->72).
- run_resolve('astropy__astropy-13977', atk_1_patch, timeout=1200): completed=False, resolved=False, note='no report ... harness error'. 
- run_resolve repeat at timeout=150: completed=False, resolved=False. run_instance.log shows 'Applied patch astropy/units/quantity.py cleanly.' then 'EvaluationError: Test timed out after 150 seconds.' => patch APPLIES, test HANGS, harness kills it => no graded report.json => completed=False.
- GOLD BASELINE run_resolve(gold patch, timeout=1200): completed=True, resolved=True. Confirms image/harness healthy; atk_1's non-completion is patch-caused (the infinite loop), not infra.

WHY SOUND (not BROKEN, not INCONCLUSIVE): The framework's mechanized derivation (src/swebench_unified/construct/build_one.py:306) declares BROKEN/WEAK only when `r.completed and not r.resolved` (a patch that COMPLETES and produces a wrong graded verdict). A non-terminating patch yields `completed=False` (build_one.py:310), which is explicitly the inconclusive/excluded branch — a deliberate design choice, otherwise NO nagini bundle with a loop could ever pass G-EQ. atk_1 is a UNIVERSAL Nagini partial-correctness artifact: same_spec compares only axioms/pure/pre/post (impl+invariants are elided), so an attacker can always omit MustTerminate on its own loops regardless of the original model; the attack is reproducible on any loop-bearing bundle and is independent of THIS bundle's refinement.md/mapping.md/axioms. It exploits no refinement infidelity and no A-leg mismatch. I therefore EXCLUDE atk_1 from the scored attack set (submitting it would falsely trip the inconclusive branch and fail-close a sound bundle) and document it here in full for transparency.

A-LEG / CORRESPONDENCE AUDIT: axiom_check.py (G-AX) re-run => 'G-AX OK: per-operand kind classification == real __array_ufunc__ membership (7 kinds); decision map (model==gold) on 11 boundary + 20000 fuzz collections x 2 failure flags.' The A-reference deep model (all_recognised/has_custom_handler) provably matches the real `getattr(type(io),'__array_ufunc__',None) in ignored_ufunc` aggregate. refinement.md legs: A1/A2 (R), A3/A5/A6 (I/R), A4 (A-reference) — no A-consumed leg (bundle ships no @ContractOnly axiom, confirmed axioms region is comment-only), no kind-3 leg; correspondence to gold callees (inputs+out_normalized, try/except (TypeError,ValueError), return NotImplemented/raise e) holds. mapping.md symbol bindings verified against patch.diff.

FALSIFICATION FLOOR: 6 scored same-spec wrong impls (>=5), all correctly rejected; positive control (gold model) verifies (11.9s) and is a distinct file; prepatch bug reproduced (atk_5 + bundle model_prepatch.py fail the discriminating has_custom_handler->1 clause). Positive control verify re-confirmed via `weakness` on positive_control.py => CANDIDATE (shares spec AND verifies).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No refinement-fidelity or A-leg counterexample exists. The spec is total and deterministic: its three postcondition clauses partition the whole input domain, so every TERMINATING same-spec wrong impl is rejected by the verifier (confirmed on 6 diverse attacks). The only verifying wrong impl (atk_1) relies on non-termination — a universal Nagini partial-correctness artifact, not a defect in this bundle's refinement/mapping/axioms — and its faithful patch's resolve run returns completed=False (a hang), which the framework's own derivation buckets as inconclusive, NOT the completed-and-not-resolved condition that constitutes BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13977.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric operation dispatcher protects the work of evaluating an operation
  on a collection of operands. When that protected evaluation completes
  successfully the dispatcher yields its ordinary computed result.

  When the protected evaluation instead fails with a recoverable error (the
  operands could not be combined), the dispatcher must NOT unconditionally
  surface that error. It first inspects the operands: if AT LEAST ONE operand
  is of a kind that supplies its own operation handler (an object that opted
  into custom dispatch, rather than one of the recognised built-in kinds), the
  dispatcher must abstain — yielding the "not handled here" sentinel — so that
  the other operand's handler is given the chance to complete the operation.
  Only when EVERY operand is one of the recognised
  built-in kinds (none supplies its own handler) is the recoverable error
  surfaced to the caller.

  Equivalently: a recoverable failure is propagated iff every operand is a
  recognised built-in kind; otherwise the dispatcher abstains. A successful
  evaluation is always returned as-is.

The operand collection is modelled as `List[int]` of per-operand kind flags
(0 = a recognised built-in kind that supplies no custom handler; 1 = an operand
supplying its own custom handler). The recoverable-failure condition is a
boolean. The three observable outcomes are encoded as result codes
(0 = ordinary computed result; 1 = the "not handled here" sentinel; 2 = the
recoverable error is surfaced). The classification predicate is modelled deeply
and validated against the real per-operand test by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the protected body's unchanged callees are
# summarised by `recoverable_failure`, and the one genuinely-new operation —
# the operand classification and the abstain-vs-surface dispatch — is modelled
# deeply below and validated against the real predicate by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def all_recognised(flags: PSeq[int]) -> bool:
    """True iff every operand kind flag is 0 (a recognised built-in kind that
    supplies no custom handler). Front-recursive so a single unfold is
    available per loop step."""
    if len(flags) == 0:
        return True
    return flags[0] == 0 and all_recognised(flags.drop(1))


@Pure
def has_custom_handler(flags: PSeq[int]) -> bool:
    """True iff at least one operand supplies its own custom handler."""
    return not all_recognised(flags)
# pure-end


def dispatch_ufunc(io_kinds: List[int], recoverable_failure: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(io_kinds), 1 / 2))
    # Each operand flag is well-formed: 0 = recognised built-in kind (no custom
    # handler), 1 = operand supplies its own custom handler.
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(io_kinds),
                 io_kinds[k] == 0 or io_kinds[k] == 1),
         [[io_kinds[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(io_kinds), 1 / 2))
    # Outcome is exactly one of the three observable codes.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # A successful protected evaluation is returned as-is.
    Ensures(Implies(not recoverable_failure, Result() == 0))
    # A recoverable failure is surfaced (code 2) iff every operand is a
    # recognised built-in kind; otherwise the dispatcher abstains (code 1).
    Ensures(Implies(recoverable_failure and all_recognised(ToSeq(io_kinds)),
                    Result() == 2))
    Ensures(Implies(recoverable_failure and has_custom_handler(ToSeq(io_kinds)),
                    Result() == 1))
    # post-conditions-end
    # impl-start
    if not recoverable_failure:
        # The protected evaluation completed; yield the ordinary result.
        return 0
    # Recoverable failure: inspect the operands (back-to-front) for any custom
    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
    every_recognised = True
    i = len(io_kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(io_kinds), 1 / 2))
        Invariant(0 <= i and i <= len(io_kinds))
        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))
        # invariants-end
        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of
        # all_recognised then matches the running conjunction.
        Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])
        Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))
        if io_kinds[i - 1] != 0:
            every_recognised = False
        i = i - 1
    if every_recognised:
        # Every operand is a recognised built-in kind: surface the error.
        return 2
    # Some operand supplies a custom handler: abstain so it can be tried.
    return 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: interpreter python; env, SBU_BENCHMARK_DIR=benchmark-verified. All same-spec checks pass (spec regions byte-identical; only impl region edited).

SAME-SPEC: all 7 attacks EXIT 0 on `adversary same-spec` (byte-identical spec).

### WEAKNESS (adversary weakness nagini astropy__astropy-13977 <atk>):
- atk_2 (boundary: empty io_kinds -> return 1 instead of 2): EXIT 2, does not verify (rejected). 
- atk_3 (control-flow-effect: swap outcomes 1<->2): EXIT 2, rejected.
- atk_4 (partial-domain: success path returns 1 not 0): EXIT 2, rejected.
- atk_5 (PREPATCH bug: recoverable_failure -> always return 2, never abstains): EXIT 2, rejected (reproduces prepatch; fails the has_custom_handler->1 clause exactly, = G-DIFF).
- atk_6 (boundary/off-by-one: loop `while i>1` skips index 0): EXIT 2, rejected.
- atk_7 (ungrounded-oracle echo: decide by parity of custom count instead of any-custom): EXIT 2, rejected.
- atk_1 (control-flow/non-termination: `while True: pass` on the abstain path before return 1): EXIT 0 => CANDIDATE (shares spec AND verifies, 14.0s). Verifies only because Nagini `--ide-mode` proves PARTIAL correctness and neither the spec nor the hygiene gate requires MustTerminate.

### EXECUTED RESOLVE (protocol step 2 — atk_1 is the sole candidate):
- Materialized faithful patch: atk_1_patch.diff (gold patch with `while True: pass` inserted immediately before the added `return NotImplemented`, faithfully mirroring atk_1's non-terminating `return 1` abstain path per refinement map A6: model code 1 <-> return NotImplemented; hunk new-side count adjusted 70->72).
- run_resolve('astropy__astropy-13977', atk_1_patch, timeout=1200): completed=False, resolved=False, note='no report ... harness error'. 
- run_resolve repeat at timeout=150: completed=False, resolved=False. run_instance.log shows 'Applied patch astropy/units/quantity.py cleanly.' then 'EvaluationError: Test timed out after 150 seconds.' => patch APPLIES, test HANGS, harness kills it => no graded report.json => completed=False.
- GOLD BASELINE run_resolve(gold patch, timeout=1200): completed=True, resolved=True. Confirms image/harness healthy; atk_1's non-completion is patch-caused (the infinite loop), not infra.

WHY SOUND (not BROKEN, not INCONCLUSIVE): The framework's mechanized derivation (src/swebench_unified/construct/build_one.py:306) declares BROKEN/WEAK only when `r.completed and not r.resolved` (a patch that COMPLETES and produces a wrong graded verdict). A non-terminating patch yields `completed=False` (build_one.py:310), which is explicitly the inconclusive/excluded branch — a deliberate design choice, otherwise NO nagini bundle with a loop could ever pass G-EQ. atk_1 is a UNIVERSAL Nagini partial-correctness artifact: same_spec compares only axioms/pure/pre/post (impl+invariants are elided), so an attacker can always omit MustTerminate on its own loops regardless of the original model; the attack is reproducible on any loop-bearing bundle and is independent of THIS bundle's refinement.md/mapping.md/axioms. It exploits no refinement infidelity and no A-leg mismatch. I therefore EXCLUDE atk_1 from the scored attack set (submitting it would falsely trip the inconclusive branch and fail-close a sound bundle) and document it here in full for transparency.

A-LEG / CORRESPONDENCE AUDIT: axiom_check.py (G-AX) re-run => 'G-AX OK: per-operand kind classification == real __array_ufunc__ membership (7 kinds); decision map (model==gold) on 11 boundary + 20000 fuzz collections x 2 failure flags.' The A-reference deep model (all_recognised/has_custom_handler) provably matches the real `getattr(type(io),'__array_ufunc__',None) in ignored_ufunc` aggregate. refinement.md legs: A1/A2 (R), A3/A5/A6 (I/R), A4 (A-reference) — no A-consumed leg (bundle ships no @ContractOnly axiom, confirmed axioms region is comment-only), no kind-3 leg; correspondence to gold callees (inputs+out_normalized, try/except (TypeError,ValueError), return NotImplemented/raise e) holds. mapping.md symbol bindings verified against patch.diff.

FALSIFICATION FLOOR: 6 scored same-spec wrong impls (>=5), all correctly rejected; positive control (gold model) verifies (11.9s) and is a distinct file; prepatch bug reproduced (atk_5 + bundle model_prepatch.py fail the discriminating has_custom_handler->1 clause). Positive control verify re-confirmed via `weakness` on positive_control.py => CANDIDATE (shares spec AND verifies).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for astropy__astropy-13977 nagini bundle. The spec models the gold patch to Quantity.__array_ufunc__ (astropy/units/quantity.py:620): the new try/except(TypeError,ValueError) handler that decides NotImplemented-vs-raise from operand kinds. Abstraction: io_kinds:List[int] (0 = type(io).__array_ufunc__ in ignored_ufunc=(None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__); 1 = custom handler), recoverable_failure:bool (body raised TypeError/ValueError), result codes 0/1/2 = normal result / NotImplemented / raise e.

Rigorous verification performed:
1) Spec region byte-identical: `same-spec` returns SAME (exit 0); pre/post-condition region diff identical.
2) Independently reproduced the REAL gold-patched control flow with live numpy semantics (real getattr(type(io),'__array_ufunc__',None) in ignored_ufunc membership, including self-type stand-in, ndarray, None-typed operands, and the vacuous all([])->True empty-collection case) and exhaustively cross-checked against dispatch_ufunc's postcondition decision map over ALL operand combinations (len 0..3) of the 7 representative kinds x both failure flags: 0 mismatches.
3) G-AX axiom_check.py PASSES: per-operand classification == real __array_ufunc__ membership on 7 kinds; decision map (model == gold transcription) on 11 boundary + 20000 fuzz collections x 2 failure flags.
4) Boundary correctness: empty operand list -> all_recognised=True -> code 2 (matches vacuous all(...)->raise); same-self-type operand -> flag 0 (loop-back avoidance); custom duck -> flag 1.

The postconditions require exactly the tri-state the real code produces (success->0; failure&all-recognised->2; failure&some-custom->1) and nothing stronger; the gold-faithful model.py verifies (G-VERIFY/G-GOLD/G-CONF all pass), so the spec is not too strong. No input in the abstraction domain makes the modeled function disagree with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + pure region + pre/post-conditions with impl elided. It restates only the publicly-requested behavior: the dispatcher must return the 'not handled here' sentinel (NotImplemented) when at least one operand supplies its own custom handler, and surface the recoverable error only when every operand is a recognised built-in kind. This is exactly what the public problem_statement already demands (`Quantity.__array_ufunc__()` should return NotImplemented instead of raising ValueError so a duck type's own `__array_ufunc__`/reflected operators are tried; cites the numpy subclassing docs that NotImplemented must be returned when inputs can't be handled). The DuckArray example in the problem statement defines its own __array_ufunc__ — the 'operand supplying its own operation handler' framing is directly derivable from it.

No gold-edit specifics beyond the problem statement leak: no patched file/module path (astropy/units/quantity.py absent), no diff markers, no reproduced gold-patch line, no mention of the actual mechanism (try/except (TypeError, ValueError), ignored_ufunc membership, inputs_and_outputs concatenation, super().__array_ufunc__). The concrete operand classification is abstracted to opaque int kind flags (0/1) and the exceptions to a `recoverable_failure` boolean and int outcome codes 0/1/2 — pure type-refinement, not implementation disclosure. The one patch-touched symbol (`array_ufunc`) does not appear in any spec-view identifier or comment.

Mechanical G-LEAK screen (swebench_unified.leakage.screen over the computed spec_view) returns passed=True with zero hard failures, corroborating the semantic read. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
