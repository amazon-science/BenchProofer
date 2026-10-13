# P2 adversarial audit — sympy__sympy-19637

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,9 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
     if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
-        if key is not None:
-            hit = key_member(key)
-        else:
-            hit = False
+        # BUG: read membership unconditionally, even when no key was created.
+        hit = key_member(key)
     return hit
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,11 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
     if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
         if key is not None:
             hit = key_member(key)
         else:
-            hit = False
+            hit = True
     return hit
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,10 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
     if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
         if key is not None:
-            hit = key_member(key)
+            hit = not key_member(key)
         else:
             hit = False
     return hit
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,6 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
-    if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
-        if key is not None:
-            hit = key_member(key)
-        else:
-            hit = False
     return hit
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,12 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
     if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
         if key is not None:
             hit = key_member(key)
         else:
-            hit = False
+            while True:
+                hit = False
     return hit
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,15 +95,10 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
     if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
         if key is not None:
-            hit = key_member(key)
+            hit = True
         else:
             hit = False
     return hit
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,16 +95,8 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
     hit = False
-    if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
-        if key is not None:
-            hit = key_member(key)
-        else:
-            hit = False
+    if key is not None:
+        hit = key_member(key)
     return hit
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,16 +95,6 @@
     Ensures(Implies(key is None, not Result()))
     # post-conditions-end
     # impl-start
-    # Default: no processing was applied.
-    hit = False
-    if entered:
-        # The transform is entered. A key is created and spliced in ONLY when a
-        # substitution is performed (key is not None). The signal — the key's
-        # membership in the rewritten text — is read ONLY in that case, when a
-        # key actually exists; otherwise the signal stays false.
-        if key is not None:
-            hit = key_member(key)
-        else:
-            hit = False
+    hit = expected_signal(entered, key)
     return hit
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-19637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual pre-processor decides whether a later post-processing pass is
  needed. The signal it returns ("processing-was-applied") is derived from a
  substitution key, but that key is created ONLY inside an inner branch — the
  branch that actually performs a space-to-key substitution. Two outer cases:

    * ENTERED-AND-SUBSTITUTED — the input qualifies for the transform (the
      outer guard holds) AND, after the structural rewrite, a substitution was
      actually performed (a key was created and spliced in). Here the signal is
      whether that freshly-created key occurs in the rewritten text.

    * NO-SUBSTITUTION — either the input never qualified for the transform, or
      it qualified but, after the rewrite, NO substitution was performed (no
      key was ever created). Here NO key exists, so the signal MUST be false;
      there is no key to test for membership.

  The behaviour pinned here: the signal equals "the created key occurs in the
  rewritten text" ONLY in the entered-and-substituted case, and is false in the
  no-substitution case. The key's membership may be inspected ONLY when a key
  was actually created. Inspecting a key's membership when no key exists (the
  no-substitution case) is never permitted — there is nothing to inspect.

The presence/absence of the created key is modelled as `Optional[bool]`
(absent = None = no key was created; present = the key's membership in the
rewritten text). The outer-guard and substitution-performed conditions are
booleans. The key-membership inspection is a `@Pure` accessor defined only when
a key is present (its precondition forbids inspecting an absent key).

The signal computation is a bounded, straight-line decision: it MUST terminate
(a total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges — e.g. hangs instead of returning the false
signal on the no-substitution path — would satisfy the value postconditions
only vacuously and would hang the caller forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the signal selection is concrete boolean / Optional control flow,
# modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def key_member(key: Optional[bool]) -> bool:
    """Whether the created substitution key occurs in the rewritten text. This
    inspection is defined ONLY when a key was actually created (key is not
    None); inspecting an absent key is excluded by the precondition — there is
    nothing to inspect when no key exists."""
    Requires(key is not None)
    return key  # type: ignore[return-value]


@Pure
def expected_signal(entered: bool, key: Optional[bool]) -> bool:
    """The signal the desired behaviour demands: the created key's membership in
    the rewritten text when a key was created (the entered-and-substituted
    case), and false otherwise (the no-substitution case — no key exists)."""
    if entered and key is not None:
        return key_member(key)
    return False
# pure-end


def compute_processing_signal(entered: bool, key: Optional[bool]) -> bool:
    # pre-conditions-start
    # `entered` is the outer guard (the input qualified for the transform).
    # `key` carries the created substitution key's membership in the rewritten
    # text when a key was created (the substitution-performed inner branch),
    # and is absent (None) when no key was created.  A key can exist only inside
    # the transform, so an absent outer guard implies an absent key.
    Requires(Implies(not entered, key is None))
    # The signal computation is a bounded, straight-line decision: it MUST
    # terminate and hand the signal back — total correctness. A diverging impl
    # (e.g. hanging instead of returning the false signal on the
    # no-substitution path) would satisfy the value postconditions only
    # vacuously and hang the caller forever. This obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The signal is exactly the membership of a created key in the entered-and-
    # substituted case, and false in the no-substitution case.
    Ensures(Result() == expected_signal(entered, key))
    # No key created (the no-substitution case) forces the signal false: there
    # is no key whose membership could make it true.
    Ensures(Implies(key is None, not Result()))
    # post-conditions-end
    # impl-start
    # Default: no processing was applied.
    hit = False
    if entered:
        # The transform is entered. A key is created and spliced in ONLY when a
        # substitution is performed (key is not None). The signal — the key's
        # membership in the rewritten text — is read ONLY in that case, when a
        # key actually exists; otherwise the signal stays false.
        if key is not None:
            hit = key_member(key)
        else:
            hit = False
    return hit
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs + model<->patch correspondence for the nagini bundle sympy__sympy-19637. VERDICT: SOUND.

### Refinement.md A-leg / trust-point audit
refinement.md declares NO consumed axiom and NO A-reference deep model (§B, §C); mapping.md §3 concurs ('None. There is no @ContractOnly axiom and no A-reference deep model.'). I verified this is honest: model.py's axioms-start/axioms-end region is empty (comment only); grep for ContractOnly/Predicate/Ghost/Assume finds none; the only defs are key_member, expected_signal (concrete-bodied @Pure helpers that are part of the SPEC/pure region, not opaque axiomatized callees) and compute_processing_signal. So every refinement leg is R (type refinement) or I (identical op) -- there is NO A-consumed / A-reference / kind-3 leg. The sole trust point is refinement fidelity (this G-EQ), exactly as §C claims. The abstraction (entered <-> outer guard '(' in s and not quoted; key: Optional[bool] <-> local kern present iff assigned inside `if ' ' in s:`, value = `kern in s`; Result() <-> hit) is faithful and is executably re-validated against the real kernS control flow by axiom_check.py (G-AX no-op soundness check).

Why the spec is tight: the postcondition Ensures(Result() == expected_signal(entered, key)) pins the return as a TOTAL function of (entered,key) over the reachable domain (no axiom slack), and key_member's precondition Requires(key is not None) is the formal face of the UnboundLocalError -- reading membership when no key was created is unprovable. Together these force any verifying impl to the gold hit-computation.

=== Attack suite (8 distinct wrong/variant impls, impl-region-only edits; all confirmed same-spec by comparing everything outside impl-start/impl-end byte-identical) ===
Command form: python -m swebench_unified.adversary weakness nagini sympy__sympy-19637 <atk>.py
- atk_1.py (PREPATCH bug: unconditional key_member(key) read inside entered branch, outside the key-is-not-None guard) -> NOT-A-COUNTEREXAMPLE: does not verify. PREPATCH REPRODUCED (key_member precondition key is not None unprovable on entered-but-no-key path).
- atk_2.py (else-branch signal = True on no-substitution path) -> NOT-A-COUNTEREXAMPLE: does not verify (violates Implies(key is None, not Result())).
- atk_3.py (negate membership: hit = not key_member(key)) -> NOT-A-COUNTEREXAMPLE: does not verify (Result != expected_signal).
- atk_4.py (partial-domain: always return False) -> NOT-A-COUNTEREXAMPLE: does not verify (wrong on entered-and-substituted key=True case).
- atk_5.py (control-flow-effect: `while True` non-termination on no-substitution path) -> NOT-A-COUNTEREXAMPLE: does not verify (MustTerminate(2) obligation rejects divergence). Confirms the total-correctness leg bites.
- atk_6.py (boundary: hit=True whenever key present, ignoring membership value) -> NOT-A-COUNTEREXAMPLE: does not verify (Result != key_member(key)).
- atk_7.py (drop redundant `if entered` wrapper: `if key is not None: hit = key_member(key)`) -> CANDIDATE (verifies, 18.3s). Behaviorally IDENTICAL to gold on the reachable domain: precondition Implies(not entered, key is None) => key is not None ==> entered, so the wrapper is redundant.
- atk_8.py (ungrounded-oracle echo: return expected_signal(entered, key) directly) -> CANDIDATE (verifies, 17.9s). = key_member(key) if entered and key is not None else False = gold behavior.

### Mandatory resolve step for verifying candidates
BOTH candidates' faithful refined patch is the gold kernS change (move `hit = kern in s` inside `if ' ' in s:` and add `else: hit = False`), because each is behaviorally equal to the gold impl over the entire reachable (entered,key) domain -- there is no realizable input on which they diverge from gold. Materialized patch_atk_7.diff and patch_atk_8.diff (byte-identical to benchmark patch.diff). RAN the official harness:
  swebench_unified.harness.run_resolve(sympy__sympy-19637, patch_atk_7.diff, timeout=1800) -> RESOLVED: True, COMPLETED: True, ATTEMPTS: 1, FLAKY: False, NOTE: resolved.
patch_atk_8.diff is byte-identical, so it resolves identically. Neither verifying candidate's faithful patch fails to resolve => NO verify⇏?correct break.

### Positive control
pos_control.py (verbatim bundle model.py) VERIFIED in 16.2s (adversary verify).

CONCLUSION: 8 attacks run (6 wrong impls correctly REJECTED by the spec incl. the prepatch bug and a non-termination attack; 2 gold-equivalent variants verify AND their materialized faithful patches RESOLVE). Positive control verifies. No axiom/A-reference trust points exist to attack; all legs R/I and the abstraction is faithful. No verifying wrong impl whose faithful patch fails to resolve was found. Spec is SOUND for G-EQ.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-19637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual pre-processor decides whether a later post-processing pass is
  needed. The signal it returns ("processing-was-applied") is derived from a
  substitution key, but that key is created ONLY inside an inner branch — the
  branch that actually performs a space-to-key substitution. Two outer cases:

    * ENTERED-AND-SUBSTITUTED — the input qualifies for the transform (the
      outer guard holds) AND, after the structural rewrite, a substitution was
      actually performed (a key was created and spliced in). Here the signal is
      whether that freshly-created key occurs in the rewritten text.

    * NO-SUBSTITUTION — either the input never qualified for the transform, or
      it qualified but, after the rewrite, NO substitution was performed (no
      key was ever created). Here NO key exists, so the signal MUST be false;
      there is no key to test for membership.

  The behaviour pinned here: the signal equals "the created key occurs in the
  rewritten text" ONLY in the entered-and-substituted case, and is false in the
  no-substitution case. The key's membership may be inspected ONLY when a key
  was actually created. Inspecting a key's membership when no key exists (the
  no-substitution case) is never permitted — there is nothing to inspect.

The presence/absence of the created key is modelled as `Optional[bool]`
(absent = None = no key was created; present = the key's membership in the
rewritten text). The outer-guard and substitution-performed conditions are
booleans. The key-membership inspection is a `@Pure` accessor defined only when
a key is present (its precondition forbids inspecting an absent key).

The signal computation is a bounded, straight-line decision: it MUST terminate
(a total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges — e.g. hangs instead of returning the false
signal on the no-substitution path — would satisfy the value postconditions
only vacuously and would hang the caller forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the signal selection is concrete boolean / Optional control flow,
# modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def key_member(key: Optional[bool]) -> bool:
    """Whether the created substitution key occurs in the rewritten text. This
    inspection is defined ONLY when a key was actually created (key is not
    None); inspecting an absent key is excluded by the precondition — there is
    nothing to inspect when no key exists."""
    Requires(key is not None)
    return key  # type: ignore[return-value]


@Pure
def expected_signal(entered: bool, key: Optional[bool]) -> bool:
    """The signal the desired behaviour demands: the created key's membership in
    the rewritten text when a key was created (the entered-and-substituted
    case), and false otherwise (the no-substitution case — no key exists)."""
    if entered and key is not None:
        return key_member(key)
    return False
# pure-end


def compute_processing_signal(entered: bool, key: Optional[bool]) -> bool:
    # pre-conditions-start
    # `entered` is the outer guard (the input qualified for the transform).
    # `key` carries the created substitution key's membership in the rewritten
    # text when a key was created (the substitution-performed inner branch),
    # and is absent (None) when no key was created.  A key can exist only inside
    # the transform, so an absent outer guard implies an absent key.
    Requires(Implies(not entered, key is None))
    # The signal computation is a bounded, straight-line decision: it MUST
    # terminate and hand the signal back — total correctness. A diverging impl
    # (e.g. hanging instead of returning the false signal on the
    # no-substitution path) would satisfy the value postconditions only
    # vacuously and hang the caller forever. This obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The signal is exactly the membership of a created key in the entered-and-
    # substituted case, and false in the no-substitution case.
    Ensures(Result() == expected_signal(entered, key))
    # No key created (the no-substitution case) forces the signal false: there
    # is no key whose membership could make it true.
    Ensures(Implies(key is None, not Result()))
    # post-conditions-end
    # impl-start
    # Default: no processing was applied.
    hit = False
    if entered:
        # The transform is entered. A key is created and spliced in ONLY when a
        # substitution is performed (key is not None). The signal — the key's
        # membership in the rewritten text — is read ONLY in that case, when a
        # key actually exists; otherwise the signal stays false.
        if key is not None:
            hit = key_member(key)
        else:
            hit = False
    return hit
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT FOCUS: A-legs + model<->patch correspondence for the nagini bundle sympy__sympy-19637. VERDICT: SOUND.

### Refinement.md A-leg / trust-point audit
refinement.md declares NO consumed axiom and NO A-reference deep model (§B, §C); mapping.md §3 concurs ('None. There is no @ContractOnly axiom and no A-reference deep model.'). I verified this is honest: model.py's axioms-start/axioms-end region is empty (comment only); grep for ContractOnly/Predicate/Ghost/Assume finds none; the only defs are key_member, expected_signal (concrete-bodied @Pure helpers that are part of the SPEC/pure region, not opaque axiomatized callees) and compute_processing_signal. So every refinement leg is R (type refinement) or I (identical op) -- there is NO A-consumed / A-reference / kind-3 leg. The sole trust point is refinement fidelity (this G-EQ), exactly as §C claims. The abstraction (entered <-> outer guard '(' in s and not quoted; key: Optional[bool] <-> local kern present iff assigned inside `if ' ' in s:`, value = `kern in s`; Result() <-> hit) is faithful and is executably re-validated against the real kernS control flow by axiom_check.py (G-AX no-op soundness check).

Why the spec is tight: the postcondition Ensures(Result() == expected_signal(entered, key)) pins the return as a TOTAL function of (entered,key) over the reachable domain (no axiom slack), and key_member's precondition Requires(key is not None) is the formal face of the UnboundLocalError -- reading membership when no key was created is unprovable. Together these force any verifying impl to the gold hit-computation.

=== Attack suite (8 distinct wrong/variant impls, impl-region-only edits; all confirmed same-spec by comparing everything outside impl-start/impl-end byte-identical) ===
Command form: python -m swebench_unified.adversary weakness nagini sympy__sympy-19637 <atk>.py
- atk_1.py (PREPATCH bug: unconditional key_member(key) read inside entered branch, outside the key-is-not-None guard) -> NOT-A-COUNTEREXAMPLE: does not verify. PREPATCH REPRODUCED (key_member precondition key is not None unprovable on entered-but-no-key path).
- atk_2.py (else-branch signal = True on no-substitution path) -> NOT-A-COUNTEREXAMPLE: does not verify (violates Implies(key is None, not Result())).
- atk_3.py (negate membership: hit = not key_member(key)) -> NOT-A-COUNTEREXAMPLE: does not verify (Result != expected_signal).
- atk_4.py (partial-domain: always return False) -> NOT-A-COUNTEREXAMPLE: does not verify (wrong on entered-and-substituted key=True case).
- atk_5.py (control-flow-effect: `while True` non-termination on no-substitution path) -> NOT-A-COUNTEREXAMPLE: does not verify (MustTerminate(2) obligation rejects divergence). Confirms the total-correctness leg bites.
- atk_6.py (boundary: hit=True whenever key present, ignoring membership value) -> NOT-A-COUNTEREXAMPLE: does not verify (Result != key_member(key)).
- atk_7.py (drop redundant `if entered` wrapper: `if key is not None: hit = key_member(key)`) -> CANDIDATE (verifies, 18.3s). Behaviorally IDENTICAL to gold on the reachable domain: precondition Implies(not entered, key is None) => key is not None ==> entered, so the wrapper is redundant.
- atk_8.py (ungrounded-oracle echo: return expected_signal(entered, key) directly) -> CANDIDATE (verifies, 17.9s). = key_member(key) if entered and key is not None else False = gold behavior.

### Mandatory resolve step for verifying candidates
BOTH candidates' faithful refined patch is the gold kernS change (move `hit = kern in s` inside `if ' ' in s:` and add `else: hit = False`), because each is behaviorally equal to the gold impl over the entire reachable (entered,key) domain -- there is no realizable input on which they diverge from gold. Materialized patch_atk_7.diff and patch_atk_8.diff (byte-identical to benchmark patch.diff). RAN the official harness:
  swebench_unified.harness.run_resolve(sympy__sympy-19637, patch_atk_7.diff, timeout=1800) -> RESOLVED: True, COMPLETED: True, ATTEMPTS: 1, FLAKY: False, NOTE: resolved.
patch_atk_8.diff is byte-identical, so it resolves identically. Neither verifying candidate's faithful patch fails to resolve => NO verify⇏?correct break.

### Positive control
pos_control.py (verbatim bundle model.py) VERIFIED in 16.2s (adversary verify).

CONCLUSION: 8 attacks run (6 wrong impls correctly REJECTED by the spec incl. the prepatch bug and a non-termination attack; 2 gold-equivalent variants verify AND their materialized faithful patches RESOLVE). Positive control verifies. No axiom/A-reference trust points exist to attack; all legs R/I and the abstraction is faithful. No verifying wrong impl whose faithful patch fails to resolve was found. Spec is SOUND for G-EQ.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for nagini sympy__sympy-19637. The model abstracts the kernS `hit`-computation delta to compute_processing_signal(entered: bool, key: Optional[bool]). I verified model.py (Verification successful, 12.97s) and confirmed the spec region (lines 1-97, docstring/axioms/pure/pre/post) is byte-identical to model_prepatch.py; only the impl region differs (prepatch reads key_member unconditionally inside the entered branch → precondition key is not None unprovable when entered∧key is None → the modeled UnboundLocalError).

Fidelity to the real callee (patched kernS at base_commit 63f8f465, sympy/core/sympify.py). I replayed the real pre-processing rewrite to derive (entered, key) for representative inputs. Every reachable abstraction state agrees with the real hit value:
- (entered=False, key=None): real hit=False; model=False ✓ (e.g. 'x', 'x + 1', "'x'").
- (entered=True, key=None) — entered but no space survives the rewrite: real hit=False; model=False ✓ (F2P witness '(2*x)/(x-1)', '(a+b)').
- (entered=True, key present): whenever ' ' in s held, the unique kern (while-loop ⇒ kern∉s) is spliced by s.replace(' ',kern), so `kern in s` is ALWAYS True → real hit=True; model key_member(key) returns key=True → True ✓ ('-(x + 1)', '2*(x + y)*y', 'Interval(-1,-2-4*(-3))', 'a*(b+c)*(d+e)').

The only domain point the model additionally permits, (entered=True, key=False), is UNREACHABLE in the real repo (a freshly created kern is necessarily a substring after replacement); even at that point the model returns False, so it cannot disagree with any real input. Precondition Implies(not entered, key is None) is faithful (kern is bound only inside the entered guard). MustTerminate(2) is faithful (the real hit-computation is bounded, straight-line, always terminating). key_member's Requires(key is not None) faithfully encodes 'name must be bound before use' — it does not over-constrain the post-patch behavior, since the guarded read model.py uses discharges it on every reachable state.

No input exists on which the modeled function disagrees with the real kernS behavior. The spec is neither too strong nor drifting from repo behavior. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen) over the nagini spec view passes with ZERO hard failures; no relaxed_leakage flag; spec region byte-identical model vs model_prepatch (same_spec==True), so the impl-region 'PRE-PATCH BUG' narration is elided from the consumer view (impl-start -> '... implementation elided'). Assessed against the PUBLIC problem_statement only (not hints): the problem_statement already discloses the symbol `kernS`, the failing line `hit = kern in s`, and `UnboundLocalError: local variable 'kern' referenced before assignment`. The spec view leaks nothing beyond that public baseline: (1) identifiers are abstract (compute_processing_signal/entered/key/key_member/expected_signal) — none echo any patched repo symbol; the only distinctive changed symbol `kernS` is already public. (2) No diff markers, no patched file path `sympy/core/sympify.py`, no module path. (3) No narration keywords (bug/fix/patched) in spec-view comments/docstrings. (4) The docstring/contracts describe the desired behavior abstractly (signal false in the no-substitution case; key membership inspectable only when a key was created) — this is the faithful contract, i.e. the correct behavior, which is not the same as revealing the gold diff (moving `hit = kern in s` inside `if ' ' in s:` and adding `else: hit = False`). The gold's structural edit (branch placement) is not exposed by the elided-impl spec view beyond what the failing-line problem_statement already gives. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
