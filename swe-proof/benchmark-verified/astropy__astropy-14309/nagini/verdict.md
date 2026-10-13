# P2 adversarial audit — astropy__astropy-14309

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.py`, `atk2_const_false.py`, `atk3_path_always_true.py`, `atk4_swap_priority.py`, `atk5_boundary_ntrailing.py`, `atk6_flip_trailing.py`, `atk8_divergence.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo_decided.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition Result() == decided(...) pins the output over the ENTIRE precondition domain (decided is total), and Requires(MustTerminate(2)) blocks the divergence loophole. Every wrong impl either violates the exact functional pin (rejected by the verifier) or fails to terminate (rejected by MustTerminate). The only verifying same-spec attack is the ungrounded-oracle echo (atk7, returns decided(...) verbatim), whose faithful refined patch is the gold cascade and RESOLVES under run_resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,9 +129,6 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
     if stream_present:
         if sig_matches:
             return R_TRUE()
@@ -139,9 +136,7 @@
     if path_present:
         if path_recognised:
             return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
+        # (no else — falls through: the prepatch bug)
     if n_trailing == 0:
         return R_FAULT()
     if first_trailing_accepted:
```

Attack 2 — `atk2_const_false.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,22 +129,5 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
-    if stream_present:
-        if sig_matches:
-            return R_TRUE()
-        return R_FALSE()
-    if path_present:
-        if path_recognised:
-            return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
-    if n_trailing == 0:
-        return R_FAULT()
-    if first_trailing_accepted:
-        return R_TRUE()
     return R_FALSE()
     # impl-end
```

Attack 3 — `atk3_path_always_true.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,19 +129,12 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
     if stream_present:
         if sig_matches:
             return R_TRUE()
         return R_FALSE()
     if path_present:
-        if path_recognised:
-            return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
+        return R_TRUE()
     if n_trailing == 0:
         return R_FAULT()
     if first_trailing_accepted:
```

Attack 4 — `atk4_swap_priority.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,19 +129,14 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
+    if path_present:
+        if path_recognised:
+            return R_TRUE()
+        return R_FALSE()
     if stream_present:
         if sig_matches:
             return R_TRUE()
         return R_FALSE()
-    if path_present:
-        if path_recognised:
-            return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
     if n_trailing == 0:
         return R_FAULT()
     if first_trailing_accepted:
```

Attack 5 — `atk5_boundary_ntrailing.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,9 +129,6 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
     if stream_present:
         if sig_matches:
             return R_TRUE()
@@ -140,9 +137,7 @@
         if path_recognised:
             return R_TRUE()
         return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
-    if n_trailing == 0:
+    if n_trailing <= 1:
         return R_FAULT()
     if first_trailing_accepted:
         return R_TRUE()
```

Attack 6 — `atk6_flip_trailing.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,9 +129,6 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
     if stream_present:
         if sig_matches:
             return R_TRUE()
@@ -140,11 +137,9 @@
         if path_recognised:
             return R_TRUE()
         return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
     if n_trailing == 0:
         return R_FAULT()
     if first_trailing_accepted:
-        return R_TRUE()
-    return R_FALSE()
+        return R_FALSE()
+    return R_TRUE()
     # impl-end
```

Attack 7 — `atk7_echo_decided.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -129,22 +129,6 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
-    if stream_present:
-        if sig_matches:
-            return R_TRUE()
-        return R_FALSE()
-    if path_present:
-        if path_recognised:
-            return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
-    if n_trailing == 0:
-        return R_FAULT()
-    if first_trailing_accepted:
-        return R_TRUE()
-    return R_FALSE()
+    return decided(stream_present, sig_matches, path_present,
+                   path_recognised, n_trailing, first_trailing_accepted)
     # impl-end
```

Attack 8 — `atk8_divergence.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,22 +129,9 @@
                     Result() != R_FAULT()))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
-    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
-    # index the trailing-argument tuple.
-    if stream_present:
-        if sig_matches:
-            return R_TRUE()
-        return R_FALSE()
-    if path_present:
-        if path_recognised:
-            return R_TRUE()
-        return R_FALSE()
-    # Only reached when neither a stream nor a path name is present: the first
-    # trailing argument decides; indexing it when there is none is the fault.
-    if n_trailing == 0:
-        return R_FAULT()
-    if first_trailing_accepted:
-        return R_TRUE()
+    if n_trailing >= 0:
+        return is_recognised_input(stream_present, sig_matches, path_present,
+                                   path_recognised, n_trailing,
+                                   first_trailing_accepted)
     return R_FALSE()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14309.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A format-detection predicate decides whether some input designates a file of
  a particular kind. Its inputs are, in priority order:

    1. an optional open data stream; when present, the verdict is whether the
       stream's leading bytes equal a constant signature;
    2. otherwise an optional path name; when present, the verdict is whether the
       path name ends with one of a predetermined set of recognised suffixes;
    3. otherwise a verdict drawn from the first of the remaining trailing
       positional arguments (whether that object is one of a predetermined set
       of accepted object kinds).

  The required guarantee on case (2): when a path name is present, the predicate
  yields a definite boolean verdict computed SOLELY from that path name — TRUE
  exactly when the path name carries a recognised suffix and FALSE otherwise —
  and in particular it does NOT, in the FALSE case, go on to consult the
  trailing positional arguments. Consulting them would index the trailing
  argument tuple, which is out of range (and would fault) when no trailing
  argument was supplied. So for a present path name the predicate is a total
  function of the path name alone and is well-defined even with no trailing
  arguments.

The result is modelled as a small integer code (TRUE / FALSE, plus a distinct
FAULT sentinel that marks "the predicate indexed an absent trailing argument").
The runtime classification facts (a stream being present, a byte comparison, a
suffix test, an object-kind test, the count of trailing arguments) are modelled
as booleans / a non-negative int (Nagini cannot run the underlying isinstance /
byte / string probes). No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real predicate (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled delta is a pure control-flow decision over boolean
# classification bits and an argument count; no opaque library callee is
# consumed inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def R_TRUE() -> int:
    # definite TRUE verdict
    return 1


@Pure
def R_FALSE() -> int:
    # definite FALSE verdict
    return 0


@Pure
def R_FAULT() -> int:
    # the predicate indexed an absent trailing argument (out-of-range fault):
    # a non-boolean outcome that a correct predicate must NEVER produce when a
    # path name is present.
    return -1


@Pure
def decided(stream_present: bool, sig_matches: bool,
            path_present: bool, path_recognised: bool,
            n_trailing: int, first_trailing_accepted: bool) -> int:
    """The verdict the predicate must produce for the given classification
    facts. This is the desired behaviour spelled out as a total function of the
    facts (the specification the impl must meet).

    Priority: a present stream decides by signature; otherwise a present path
    name decides SOLELY by its suffix (TRUE iff recognised, FALSE otherwise —
    never consulting trailing arguments); otherwise the first trailing argument
    decides (and only here is an absent trailing argument indexed -> FAULT)."""
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
# pure-end


def is_recognised_input(stream_present: bool, sig_matches: bool,
                        path_present: bool, path_recognised: bool,
                        n_trailing: int, first_trailing_accepted: bool) -> int:
    # pre-conditions-start
    # The count of trailing positional arguments is non-negative; the
    # "first trailing argument is accepted" fact is meaningful only when there
    # is at least one trailing argument (else it is not consulted).
    Requires(n_trailing >= 0)
    Requires(Implies(first_trailing_accepted, n_trailing >= 1))
    # Total correctness: the predicate must actually ANSWER (deliver a verdict
    # to its caller), not merely be partially correct. Without this obligation
    # a diverging body (e.g. unbounded self-recursion) would satisfy every
    # postcondition vacuously yet never produce the verdict; the real predicate
    # is a straight-line cascade that always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The verdict is exactly the desired classification-driven decision.
    Ensures(Result() == decided(stream_present, sig_matches, path_present,
                                 path_recognised, n_trailing,
                                 first_trailing_accepted))
    # When a path name is present, the verdict is a definite boolean computed
    # SOLELY from the path name: TRUE iff the suffix is recognised, FALSE
    # otherwise — and it is NEVER the out-of-range FAULT, regardless of how
    # many trailing arguments were (or were not) supplied. This is the
    # discriminating clause the spec pins.
    Ensures(Implies(not stream_present and path_present and path_recognised,
                    Result() == R_TRUE()))
    Ensures(Implies(not stream_present and path_present and not path_recognised,
                    Result() == R_FALSE()))
    Ensures(Implies(not stream_present and path_present,
                    Result() != R_FAULT()))
    # post-conditions-end
    # impl-start
    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
    # index the trailing-argument tuple.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    # Only reached when neither a stream nor a path name is present: the first
    # trailing argument decides; indexing it when there is none is the fault.
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT: nagini astropy__astropy-14309, G-EQ (refinement fidelity, A-legs + model<->patch correspondence).

SPEC SHAPE: is_recognised_input's post-conditions pin Result() == decided(stream_present, sig_matches, path_present, path_recognised, n_trailing, first_trailing_accepted), where decided is a TOTAL @Pure cascade. Plus discriminating clauses (present path => R_TRUE iff recognised, R_FALSE otherwise, never R_FAULT) and Requires(MustTerminate(2)). This is an exact functional pin over the whole domain, so any behavioural deviation fails and divergence is barred.

atk1_prepatch (prepatch bug, one-armed path branch => R_FAULT for present-unrecognised-path/n=0): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Prepatch bug reproduced (also G-DIFF: model_prepatch.py fails).
- atk2_const_false (degenerate constant): failed (exit 2).
- atk3_path_always_true (partial-domain: path branch ignores path_recognised): failed (exit 2).
- atk4_swap_priority (control-flow: path checked before stream): failed (exit 2).
- atk5_boundary_ntrailing (boundary off-by-one: fault when n<=1): failed (exit 2).
- atk6_flip_trailing (control-flow-effect: negated trailing verdict): failed (exit 2).
- atk7_echo_decided (ungrounded-oracle echo: return decided(...) verbatim): CANDIDATE (shares spec AND verifies, exit 0). Materialized faithful refined patch = the gold cascade (return filepath.lower().endswith(...)). Ran through OFFICIAL harness: run_resolve('astropy__astropy-14309', patch, run_id='sbu-audit-eq-3bvmjcok-atk7') => RESOLVED: True, COMPLETED: True, F2P test_is_fits_gh_14305 PASS, all 156 P2P PASS. So the only verifying candidate is behaviourally correct: verify=>correct holds, NOT a weakness.
- atk8_divergence (unbounded self-recursion loophole): NOT-A-COUNTEREXAMPLE, verification failed (exit 2) -- MustTerminate(2) correctly rejects it.

POSITIVE CONTROL: model.py copy verifies (Verification successful, 11.3s).

REFINEMENT/A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] -- NO A-consumed axiom, NO A-reference stdlib deep-model (empty axioms region, consistent with refinement.md §C and mapping.md §3). Legs A1-A10 are all R (type-refinement of unchanged is-not-None/==/endswith/len/isinstance evaluations into bool/int carriers) or I (identical if/elif/return control flow); NO kind-3 (unexpressible-changed-op) leg. The sole deep object is `decided`, the spec cascade, whose correspondence to the REAL gold-patched is_fits (astropy/io/fits/connect.py:48, base_commit cdb66059) is validated by G-AX with ax_apply_gold=true: G-AX pass, 3033 in-image inputs (F2P + path/stream/trailing controls + 3000 fuzz), 0 disagreements; G-CONF pass, 100046 inputs, 0 disagreements. G-DIFF/G-GOLD corroborate (prepatch fails, gold-faithful model verifies). Model<->patch correspondence holds.

VERDICT: SOUND. 8 attacks run (7 wrong impls rejected by the tight functional spec + MustTerminate; 1 same-spec verifying candidate whose faithful patch RESOLVES under the official harness). No verifying wrong impl exists whose materialized faithful patch fails to resolve, so verify=>correct is upheld. Note: env astropy is 5.2.2 (differs from base_commit); the machine-checked G-AX/G-CONF/G-RESOLVE runs use the pinned instance image at base_commit via Docker, which is the authoritative correspondence evidence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.py`, `atk2_const_false.py`, `atk3_path_always_true.py`, `atk4_swap_priority.py`, `atk5_boundary_ntrailing.py`, `atk6_flip_trailing.py`, `atk8_divergence.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo_decided.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition Result() == decided(...) pins the output over the ENTIRE precondition domain (decided is total), and Requires(MustTerminate(2)) blocks the divergence loophole. Every wrong impl either violates the exact functional pin (rejected by the verifier) or fails to terminate (rejected by MustTerminate). The only verifying same-spec attack is the ungrounded-oracle echo (atk7, returns decided(...) verbatim), whose faithful refined patch is the gold cascade and RESOLVES under run_resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_const_false.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_path_always_true.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_swap_priority.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_boundary_ntrailing.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_flip_trailing.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echo_decided.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk8_divergence.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14309.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A format-detection predicate decides whether some input designates a file of
  a particular kind. Its inputs are, in priority order:

    1. an optional open data stream; when present, the verdict is whether the
       stream's leading bytes equal a constant signature;
    2. otherwise an optional path name; when present, the verdict is whether the
       path name ends with one of a predetermined set of recognised suffixes;
    3. otherwise a verdict drawn from the first of the remaining trailing
       positional arguments (whether that object is one of a predetermined set
       of accepted object kinds).

  The required guarantee on case (2): when a path name is present, the predicate
  yields a definite boolean verdict computed SOLELY from that path name — TRUE
  exactly when the path name carries a recognised suffix and FALSE otherwise —
  and in particular it does NOT, in the FALSE case, go on to consult the
  trailing positional arguments. Consulting them would index the trailing
  argument tuple, which is out of range (and would fault) when no trailing
  argument was supplied. So for a present path name the predicate is a total
  function of the path name alone and is well-defined even with no trailing
  arguments.

The result is modelled as a small integer code (TRUE / FALSE, plus a distinct
FAULT sentinel that marks "the predicate indexed an absent trailing argument").
The runtime classification facts (a stream being present, a byte comparison, a
suffix test, an object-kind test, the count of trailing arguments) are modelled
as booleans / a non-negative int (Nagini cannot run the underlying isinstance /
byte / string probes). No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real predicate (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled delta is a pure control-flow decision over boolean
# classification bits and an argument count; no opaque library callee is
# consumed inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def R_TRUE() -> int:
    # definite TRUE verdict
    return 1


@Pure
def R_FALSE() -> int:
    # definite FALSE verdict
    return 0


@Pure
def R_FAULT() -> int:
    # the predicate indexed an absent trailing argument (out-of-range fault):
    # a non-boolean outcome that a correct predicate must NEVER produce when a
    # path name is present.
    return -1


@Pure
def decided(stream_present: bool, sig_matches: bool,
            path_present: bool, path_recognised: bool,
            n_trailing: int, first_trailing_accepted: bool) -> int:
    """The verdict the predicate must produce for the given classification
    facts. This is the desired behaviour spelled out as a total function of the
    facts (the specification the impl must meet).

    Priority: a present stream decides by signature; otherwise a present path
    name decides SOLELY by its suffix (TRUE iff recognised, FALSE otherwise —
    never consulting trailing arguments); otherwise the first trailing argument
    decides (and only here is an absent trailing argument indexed -> FAULT)."""
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
# pure-end


def is_recognised_input(stream_present: bool, sig_matches: bool,
                        path_present: bool, path_recognised: bool,
                        n_trailing: int, first_trailing_accepted: bool) -> int:
    # pre-conditions-start
    # The count of trailing positional arguments is non-negative; the
    # "first trailing argument is accepted" fact is meaningful only when there
    # is at least one trailing argument (else it is not consulted).
    Requires(n_trailing >= 0)
    Requires(Implies(first_trailing_accepted, n_trailing >= 1))
    # Total correctness: the predicate must actually ANSWER (deliver a verdict
    # to its caller), not merely be partially correct. Without this obligation
    # a diverging body (e.g. unbounded self-recursion) would satisfy every
    # postcondition vacuously yet never produce the verdict; the real predicate
    # is a straight-line cascade that always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The verdict is exactly the desired classification-driven decision.
    Ensures(Result() == decided(stream_present, sig_matches, path_present,
                                 path_recognised, n_trailing,
                                 first_trailing_accepted))
    # When a path name is present, the verdict is a definite boolean computed
    # SOLELY from the path name: TRUE iff the suffix is recognised, FALSE
    # otherwise — and it is NEVER the out-of-range FAULT, regardless of how
    # many trailing arguments were (or were not) supplied. This is the
    # discriminating clause the spec pins.
    Ensures(Implies(not stream_present and path_present and path_recognised,
                    Result() == R_TRUE()))
    Ensures(Implies(not stream_present and path_present and not path_recognised,
                    Result() == R_FALSE()))
    Ensures(Implies(not stream_present and path_present,
                    Result() != R_FAULT()))
    # post-conditions-end
    # impl-start
    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
    # index the trailing-argument tuple.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    # Only reached when neither a stream nor a path name is present: the first
    # trailing argument decides; indexing it when there is none is the fault.
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT: nagini astropy__astropy-14309, G-EQ (refinement fidelity, A-legs + model<->patch correspondence).

SPEC SHAPE: is_recognised_input's post-conditions pin Result() == decided(stream_present, sig_matches, path_present, path_recognised, n_trailing, first_trailing_accepted), where decided is a TOTAL @Pure cascade. Plus discriminating clauses (present path => R_TRUE iff recognised, R_FALSE otherwise, never R_FAULT) and Requires(MustTerminate(2)). This is an exact functional pin over the whole domain, so any behavioural deviation fails and divergence is barred.

atk1_prepatch (prepatch bug, one-armed path branch => R_FAULT for present-unrecognised-path/n=0): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Prepatch bug reproduced (also G-DIFF: model_prepatch.py fails).
- atk2_const_false (degenerate constant): failed (exit 2).
- atk3_path_always_true (partial-domain: path branch ignores path_recognised): failed (exit 2).
- atk4_swap_priority (control-flow: path checked before stream): failed (exit 2).
- atk5_boundary_ntrailing (boundary off-by-one: fault when n<=1): failed (exit 2).
- atk6_flip_trailing (control-flow-effect: negated trailing verdict): failed (exit 2).
- atk7_echo_decided (ungrounded-oracle echo: return decided(...) verbatim): CANDIDATE (shares spec AND verifies, exit 0). Materialized faithful refined patch = the gold cascade (return filepath.lower().endswith(...)). Ran through OFFICIAL harness: run_resolve('astropy__astropy-14309', patch, run_id='sbu-audit-eq-3bvmjcok-atk7') => RESOLVED: True, COMPLETED: True, F2P test_is_fits_gh_14305 PASS, all 156 P2P PASS. So the only verifying candidate is behaviourally correct: verify=>correct holds, NOT a weakness.
- atk8_divergence (unbounded self-recursion loophole): NOT-A-COUNTEREXAMPLE, verification failed (exit 2) -- MustTerminate(2) correctly rejects it.

POSITIVE CONTROL: model.py copy verifies (Verification successful, 11.3s).

REFINEMENT/A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] -- NO A-consumed axiom, NO A-reference stdlib deep-model (empty axioms region, consistent with refinement.md §C and mapping.md §3). Legs A1-A10 are all R (type-refinement of unchanged is-not-None/==/endswith/len/isinstance evaluations into bool/int carriers) or I (identical if/elif/return control flow); NO kind-3 (unexpressible-changed-op) leg. The sole deep object is `decided`, the spec cascade, whose correspondence to the REAL gold-patched is_fits (astropy/io/fits/connect.py:48, base_commit cdb66059) is validated by G-AX with ax_apply_gold=true: G-AX pass, 3033 in-image inputs (F2P + path/stream/trailing controls + 3000 fuzz), 0 disagreements; G-CONF pass, 100046 inputs, 0 disagreements. G-DIFF/G-GOLD corroborate (prepatch fails, gold-faithful model verifies). Model<->patch correspondence holds.

VERDICT: SOUND. 8 attacks run (7 wrong impls rejected by the tight functional spec + MustTerminate; 1 same-spec verifying candidate whose faithful patch RESOLVES under the official harness). No verifying wrong impl exists whose materialized faithful patch fails to resolve, so verify=>correct is upheld. Note: env astropy is 5.2.2 (differs from base_commit); the machine-checked G-AX/G-CONF/G-RESOLVE runs use the pinned instance image at base_commit via Docker, which is the authoritative correspondence evidence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified for astropy__astropy-14309 nagini bundle. The modeled function `is_recognised_input`/`decided` mirrors the post-patch `is_fits` priority cascade (astropy/io/fits/connect.py:62-72): stream-by-signature > path-by-suffix (total boolean, both TRUE and FALSE) > first-trailing-arg isinstance, with R_FAULT (-1) for the IndexError raised when args[0] indexes an empty *args. Checks: (1) model.py verifies under pinned Nagini (exit 0, 'Verification successful', 10.7s). Decision-equivalence between model `decided` and the gold post-patch `is_fits` (reproduced verbatim from patch.diff / worktree working tree) holds on 200,000 fuzzed inputs with 0 mismatches — covering present/absent path, present/absent stream, 0-3 trailing args of varied types (HDUList/TableHDU/BinTableHDU/GroupsHDU/object/int/str/None), recognised & unrecognised suffixes and case variants. (3) Boundary/discriminating cases all agree: F2P is_fits('','foo.bar',None)->False (=R_FALSE); no path/stream/args -> IndexError (=R_FAULT); stream present takes priority over a recognised path; case-insensitive suffix ('X.FiTs'->True). Spec is neither too strong nor drifted — it captures fault + priority semantics exactly, and model_prepatch.py legitimately fails on the unrecognised-present-path/no-arg case (a real pre/post divergence). No diverging input exists on any tested configuration.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the spec view) passes: no diff markers (L1), no gold-patch line reproduced (L1), no patched file/module path (L2), no spec-view identifier embedding a patched repo symbol (L2/L5), no bug/fix narration (L3). No RELAXED_LEAKAGE.md and relaxed_leakage flag is unset, so this is a plain strict pass.

Semantic check (against the SOLVER-VISIBLE problem_statement only, not hints_text): the gold edit rewrites is_fits's present-path branch from a one-armed `if filepath.lower().endswith(...): return True` into `return filepath.lower().endswith(...)` so an unrecognised present path no longer falls through to `isinstance(args[0], ...)` and raises IndexError. Every discriminating fact the spec view states — a present path must yield a definite boolean from the suffix test alone and must NOT consult/index the trailing positional arguments (the out-of-range FAULT) — is ALREADY fully public in the problem_statement: it contains the complete traceback naming is_fits and the exact faulting line `return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` -> `IndexError: tuple index out of range`, plus @saimn's root-cause quote ('When filepath is a string without a FITS extension, the function was returning None, now it executes isinstance(args[0], ...)') and a link to the introducing commit.

The spec view is a legitimate abstract behavioral specification: the modeled function is renamed is_recognised_input (not is_fits); it names no suffix list, no HDUList/TableHDU/isinstance, no args[0], no file/module path, and no diff hunk. The FAULT-sentinel / 'does not consult trailing arguments' framing maps 1:1 onto the publicly disclosed traceback and root cause, revealing nothing beyond the problem_statement. No line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
