# P2 adversarial audit — sphinx-doc__sphinx-8269

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -162,21 +162,7 @@
                     Result()[1] == DATUM_TRANSPORT()))
     # post-conditions-end
     # impl-start
-    try:
-        # Read the whole document and obtain the fragment verdict.
-        found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
-        raise_on_error_status(status)
-        if not found:
-            raise FragmentAbsent()
-    except TransportError:
-        if status == 401:
-            return (WORKING(), DATUM_NONE())
-        elif status == 503:
-            return (IGNORED(), DATUM_TRANSPORT())
-        else:
-            return (FAILED(), DATUM_TRANSPORT())
-    except FragmentAbsent:
-        return (FAILED(), DATUM_FRAGMENT_ABSENT())
+    while True:
+        pass
     return (WORKING(), DATUM_NONE())
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,16 +163,12 @@
     # post-conditions-end
     # impl-start
     try:
-        # Read the whole document and obtain the fragment verdict.
         found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
         raise_on_error_status(status)
         if not found:
             raise FragmentAbsent()
     except TransportError:
-        if status == 401:
-            return (WORKING(), DATUM_NONE())
-        elif status == 503:
+        if status == 503:
             return (IGNORED(), DATUM_TRANSPORT())
         else:
             return (FAILED(), DATUM_TRANSPORT())
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,17 +163,13 @@
     # post-conditions-end
     # impl-start
     try:
-        # Read the whole document and obtain the fragment verdict.
         found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
         raise_on_error_status(status)
         if not found:
             raise FragmentAbsent()
     except TransportError:
         if status == 401:
             return (WORKING(), DATUM_NONE())
-        elif status == 503:
-            return (IGNORED(), DATUM_TRANSPORT())
         else:
             return (FAILED(), DATUM_TRANSPORT())
     except FragmentAbsent:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -162,21 +162,14 @@
                     Result()[1] == DATUM_TRANSPORT()))
     # post-conditions-end
     # impl-start
-    try:
-        # Read the whole document and obtain the fragment verdict.
-        found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
-        raise_on_error_status(status)
-        if not found:
-            raise FragmentAbsent()
-    except TransportError:
+    if 400 < status and status < 600:
         if status == 401:
             return (WORKING(), DATUM_NONE())
         elif status == 503:
             return (IGNORED(), DATUM_TRANSPORT())
         else:
             return (FAILED(), DATUM_TRANSPORT())
-    except FragmentAbsent:
+    if not fragment_present:
         return (FAILED(), DATUM_FRAGMENT_ABSENT())
     return (WORKING(), DATUM_NONE())
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,10 +163,7 @@
     # post-conditions-end
     # impl-start
     try:
-        # Read the whole document and obtain the fragment verdict.
         found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
-        raise_on_error_status(status)
         if not found:
             raise FragmentAbsent()
     except TransportError:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,9 +163,7 @@
     # post-conditions-end
     # impl-start
     try:
-        # Read the whole document and obtain the fragment verdict.
         found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
         raise_on_error_status(status)
         if not found:
             raise FragmentAbsent()
@@ -175,7 +173,7 @@
         elif status == 503:
             return (IGNORED(), DATUM_TRANSPORT())
         else:
-            return (FAILED(), DATUM_TRANSPORT())
+            return (FAILED(), DATUM_FRAGMENT_ABSENT())
     except FragmentAbsent:
         return (FAILED(), DATUM_FRAGMENT_ABSENT())
     return (WORKING(), DATUM_NONE())
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -162,21 +162,14 @@
                     Result()[1] == DATUM_TRANSPORT()))
     # post-conditions-end
     # impl-start
-    try:
-        # Read the whole document and obtain the fragment verdict.
-        found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
-        raise_on_error_status(status)
-        if not found:
-            raise FragmentAbsent()
-    except TransportError:
+    if is_error_status(status):
         if status == 401:
             return (WORKING(), DATUM_NONE())
         elif status == 503:
             return (IGNORED(), DATUM_TRANSPORT())
         else:
             return (FAILED(), DATUM_TRANSPORT())
-    except FragmentAbsent:
-        return (FAILED(), DATUM_FRAGMENT_ABSENT())
-    return (WORKING(), DATUM_NONE())
+    if fragment_present:
+        return (WORKING(), DATUM_NONE())
+    return (FAILED(), DATUM_FRAGMENT_ABSENT())
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -162,10 +162,11 @@
                     Result()[1] == DATUM_TRANSPORT()))
     # post-conditions-end
     # impl-start
+    if status == 500 and fragment_present:
+        while True:
+            pass
     try:
-        # Read the whole document and obtain the fragment verdict.
         found = fragment_present
-        # The transport-status gate is consulted BEFORE acting on the verdict.
         raise_on_error_status(status)
         if not found:
             raise FragmentAbsent()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8269.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a hyperlink that carries a fragment is checked against a live server
  while fragment-checking is enabled, the responsibility of the checker is to
  classify the link's outcome. The classification it produces must reflect the
  TRANSPORT outcome whenever the server answered with an error status, in
  exactly the same way as the no-fragment path already does:

    * an error status in the client range (>= 400, < 500) other than the
      "authorization required" status, and any error status in the server
      range (>= 500, < 600) other than the "service unavailable" status, is a
      FAILED result whose accompanying datum is the transport error;
    * the "authorization required" client status is a WORKING result;
    * the "service unavailable" server status is an IGNORED result;
    * a non-error status (< 400) leaves the fragment question to be answered:
      the result is WORKING when the fragment is present in the document and
      FAILED (with the fragment-absent datum) when it is not.

  The point pinned here is that the transport error is consulted BEFORE the
  document is searched for the fragment, so a server error is never mis-reported
  as a missing fragment. The datum that accompanies a failed error-status result
  is the transport error, never the fragment-absent datum.

The HTTP status is modelled as an ``int``; whether the fragment is present is a
single observable bit (the verdict of the unchanged document scanner, abstracted
to a boolean). The transport-status gate (the callee that raises on an error
status) is the unchanged library routine, axiomatized as a contract-only
function whose raise/no-raise behaviour is keyed on the status range. The
transport error it raises is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The classification is returned as a pair of small integer codes: a status class
(WORKING / FAILED / IGNORED) and a datum kind (none / transport-error /
fragment-absent), so the discriminating observation -- a server-error link is
FAILED with the TRANSPORT-ERROR datum rather than the FRAGMENT-ABSENT datum --
is expressible.

Classifying one link is a bounded, straight-line computation: the checker MUST
actually deliver its classification (a total-correctness obligation, carried as
MustTerminate in the precondition). Nagini is a partial-correctness verifier by
default, so without this obligation an implementation that diverges before
returning (e.g. an inserted ``while True: pass``) would satisfy every value
postcondition vacuously while the real checker thread hangs and never reports
the link.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TransportError(Exception):
    """The out-of-band signal raised by the transport-status gate when the
    server answered with an error status. A user-defined stand-in for the
    library's HTTP error (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md s2)."""
    pass


class FragmentAbsent(Exception):
    """The fragment-absent signal raised after the document scan when the
    fragment is not present (the generic 'fragment not found' path). Distinct
    from the transport error so the two failed data are not conflated."""
    pass


# axioms-start
@ContractOnly
def raise_on_error_status(status: int) -> None:
    """The unchanged transport-status gate. Its only observable is whether the
    answered status falls in the error ranges: it returns normally on a
    non-error status (< 400 or >= 600) and signals the SAME out-of-band
    transport error on any status in [400, 600). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real gate is a pair of range checks followed by a return or a raise —
    # a bounded computation that always delivers its verdict (exercised on
    # every axiom_check.py input). It therefore takes and discharges a
    # termination obligation, so a caller holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on a non-error status.
    Ensures(status < 400 or status >= 600)
    # The transport error is signalled EXACTLY on an error status.
    Exsures(TransportError, 400 <= status and status < 600)
    # post-conditions-end
# axioms-end


# pure-start
@Pure
def is_error_status(status: int) -> bool:
    """A status in [400, 600) is a transport error."""
    return 400 <= status and status < 600


@Pure
def WORKING() -> int:
    return 0


@Pure
def FAILED() -> int:
    return 1


@Pure
def IGNORED() -> int:
    return 2


@Pure
def DATUM_NONE() -> int:
    return 0


@Pure
def DATUM_TRANSPORT() -> int:
    return 1


@Pure
def DATUM_FRAGMENT_ABSENT() -> int:
    return 2
# pure-end


def classify_fragment_link(status: int, fragment_present: bool) -> Tuple[int, int]:
    # pre-conditions-start
    # TERMINATION: classifying one link is a bounded, straight-line dispatch
    # and must actually ANSWER. Nagini is a partial-correctness verifier by
    # default, so without this obligation a non-terminating implementation
    # (e.g. `while True: pass` before the return) satisfies every Ensures
    # vacuously; the real checker always returns its classification.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is a (status-class, datum-kind) pair.
    # (1) An "authorization required" client status (401) is WORKING.
    Ensures(Implies(status == 401, Result() == (WORKING(), DATUM_NONE())))
    # (2) A "service unavailable" server status (503) is IGNORED, carrying the
    #     transport datum.
    Ensures(Implies(status == 503, Result() == (IGNORED(), DATUM_TRANSPORT())))
    # (3) Any OTHER error status is FAILED, and its datum is the TRANSPORT error
    #     -- never the fragment-absent datum, regardless of fragment_present.
    #     This is the property the change establishes: the transport error is
    #     consulted before the document is searched.
    Ensures(Implies(is_error_status(status) and status != 401 and status != 503,
                    Result() == (FAILED(), DATUM_TRANSPORT())))
    # (4) A non-error status defers to the fragment verdict: WORKING when the
    #     fragment is present, FAILED (fragment-absent datum) when it is not.
    Ensures(Implies(not is_error_status(status) and fragment_present,
                    Result() == (WORKING(), DATUM_NONE())))
    Ensures(Implies(not is_error_status(status) and not fragment_present,
                    Result() == (FAILED(), DATUM_FRAGMENT_ABSENT())))
    # (5) A failed error-status result NEVER carries the fragment-absent datum.
    Ensures(Implies(is_error_status(status) and Result()[0] == FAILED(),
                    Result()[1] == DATUM_TRANSPORT()))
    # post-conditions-end
    # impl-start
    try:
        # Read the whole document and obtain the fragment verdict.
        found = fragment_present
        # The transport-status gate is consulted BEFORE acting on the verdict.
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec (classify_fragment_link) pins a total (status,fragment_present)->(status-class,datum-kind) function; single axiom raise_on_error_status is A-consumed (deep_model_references empty; no A-reference legs by design). ran with SBU_BENCHMARK_DIR=benchmark-verified,, python=python. All 8 attacks confirmed same-spec (adversary same-spec exit 0).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8269 <atk>):
- atk_1 unconditional 'while True: pass' on all inputs -> NOT-A-COUNTEREXAMPLE (verification failed). MustTerminate(2) rejects the divergence hole.
- atk_2 drop-401 special case (401->FAILED,TRANSPORT) -> rejected (fails Ensures clause 1).
- atk_3 drop-503 special case (503->FAILED,TRANSPORT) -> rejected (fails clause 2).
- atk_4 boundary off-by-one manual range 400<status<600 (drops 400) -> rejected (fails clause 3 for status==400).
- atk_5 control-flow/prepatch bug: gate NOT consulted, fragment scanned first so error-status+fragment-absent yields (FAILED,FRAGMENT_ABSENT) -> rejected. Reproduces model_prepatch.py failure => prepatch_reproduced=true.
- atk_6 wrong-error-datum: non-401/503 error status returns FRAGMENT_ABSENT datum -> rejected (fails clauses 3 and 5).
- atk_8 input-conditional divergence: 'while True' exactly on the F2P input (status==500 & fragment_present), correct elsewhere -> rejected. MustTerminate bites even the input-targeted loop (sharpest termination probe).
- atk_7 ungrounded-oracle ECHO: flat is_error_status dispatch producing gold-identical values on EVERY input WITHOUT calling the axiomatized gate -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 22.6s).

MANDATED RESOLVE of the sole CANDIDATE atk_7: materialized its faithful refined patch (atk_7_faithful.diff = adds response.raise_for_status() after requests.get in the fragment branch; per mapping this is atk_7's observable behavior in the repo -- is_error_status<->raise_for_status range, DATUM_TRANSPORT<->str(HTTPError)). Ran swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8269', patch, timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. The candidate's faithful patch RESOLVES => not a break (echo policy, the audit protocol G-PANEL-1). Positive control (model.py verbatim) verifies (bash scripts/nagini_verify.sh: 'Verification successful', 20.56s).

REFINEMENT AUDIT (refinement.md): every leg is R / A-consumed / I -- no kind-3, no A-reference (deep_model_references=[] matches: the delta is adding a call site to the UNCHANGED requests.models.Response.raise_for_status, captured by the A-consumed raise_on_error_status axiom, not a deep model of a changed function). A-legs verified against the REAL repo source extracted from the base_commit image (docker cat /testbed/sphinx/builders/linkcheck.py :160-210): pre-patch fragment branch is requests.get -> check_anchor -> if not found: raise Exception('Anchor not found') with NO raise_for_status (A2/A4); shared 'except HTTPError as err:' dispatch is EXACTLY 401->('working',' - unauthorized',0), 503->('ignored',str(err),0), else->('broken',str(err),0) with NO 429/rate-limit branch (A5, version pin confirmed for Sphinx 3.3.0); 'except Exception' with is_ssl_error SSL sub-case outside slice (A6); success path response.url==req_url -> 'working','',0 (A7). The gold patch.diff is byte-identical to atk_7_faithful.diff (the one added line). A-consumed axiom Ensures/Exsures match raise_for_status (400<=status<600 -> HTTPError else None) and are G-AX-checked by axiom_check.py.

CONCLUSION: 8 distinct wrong-impl attacks (partial-domain, boundary, control-flow-effect/prepatch, ungrounded-oracle echo, unconditional + input-conditional divergence) run and fully verified; the only verifying impl (echo) has a faithful patch that RESOLVES. No verifying wrong impl produces a non-resolving faithful patch. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8269.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a hyperlink that carries a fragment is checked against a live server
  while fragment-checking is enabled, the responsibility of the checker is to
  classify the link's outcome. The classification it produces must reflect the
  TRANSPORT outcome whenever the server answered with an error status, in
  exactly the same way as the no-fragment path already does:

    * an error status in the client range (>= 400, < 500) other than the
      "authorization required" status, and any error status in the server
      range (>= 500, < 600) other than the "service unavailable" status, is a
      FAILED result whose accompanying datum is the transport error;
    * the "authorization required" client status is a WORKING result;
    * the "service unavailable" server status is an IGNORED result;
    * a non-error status (< 400) leaves the fragment question to be answered:
      the result is WORKING when the fragment is present in the document and
      FAILED (with the fragment-absent datum) when it is not.

  The point pinned here is that the transport error is consulted BEFORE the
  document is searched for the fragment, so a server error is never mis-reported
  as a missing fragment. The datum that accompanies a failed error-status result
  is the transport error, never the fragment-absent datum.

The HTTP status is modelled as an ``int``; whether the fragment is present is a
single observable bit (the verdict of the unchanged document scanner, abstracted
to a boolean). The transport-status gate (the callee that raises on an error
status) is the unchanged library routine, axiomatized as a contract-only
function whose raise/no-raise behaviour is keyed on the status range. The
transport error it raises is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The classification is returned as a pair of small integer codes: a status class
(WORKING / FAILED / IGNORED) and a datum kind (none / transport-error /
fragment-absent), so the discriminating observation -- a server-error link is
FAILED with the TRANSPORT-ERROR datum rather than the FRAGMENT-ABSENT datum --
is expressible.

Classifying one link is a bounded, straight-line computation: the checker MUST
actually deliver its classification (a total-correctness obligation, carried as
MustTerminate in the precondition). Nagini is a partial-correctness verifier by
default, so without this obligation an implementation that diverges before
returning (e.g. an inserted ``while True: pass``) would satisfy every value
postcondition vacuously while the real checker thread hangs and never reports
the link.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TransportError(Exception):
    """The out-of-band signal raised by the transport-status gate when the
    server answered with an error status. A user-defined stand-in for the
    library's HTTP error (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md s2)."""
    pass


class FragmentAbsent(Exception):
    """The fragment-absent signal raised after the document scan when the
    fragment is not present (the generic 'fragment not found' path). Distinct
    from the transport error so the two failed data are not conflated."""
    pass


# axioms-start
@ContractOnly
def raise_on_error_status(status: int) -> None:
    """The unchanged transport-status gate. Its only observable is whether the
    answered status falls in the error ranges: it returns normally on a
    non-error status (< 400 or >= 600) and signals the SAME out-of-band
    transport error on any status in [400, 600). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real gate is a pair of range checks followed by a return or a raise —
    # a bounded computation that always delivers its verdict (exercised on
    # every axiom_check.py input). It therefore takes and discharges a
    # termination obligation, so a caller holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on a non-error status.
    Ensures(status < 400 or status >= 600)
    # The transport error is signalled EXACTLY on an error status.
    Exsures(TransportError, 400 <= status and status < 600)
    # post-conditions-end
# axioms-end


# pure-start
@Pure
def is_error_status(status: int) -> bool:
    """A status in [400, 600) is a transport error."""
    return 400 <= status and status < 600


@Pure
def WORKING() -> int:
    return 0


@Pure
def FAILED() -> int:
    return 1


@Pure
def IGNORED() -> int:
    return 2


@Pure
def DATUM_NONE() -> int:
    return 0


@Pure
def DATUM_TRANSPORT() -> int:
    return 1


@Pure
def DATUM_FRAGMENT_ABSENT() -> int:
    return 2
# pure-end


def classify_fragment_link(status: int, fragment_present: bool) -> Tuple[int, int]:
    # pre-conditions-start
    # TERMINATION: classifying one link is a bounded, straight-line dispatch
    # and must actually ANSWER. Nagini is a partial-correctness verifier by
    # default, so without this obligation a non-terminating implementation
    # (e.g. `while True: pass` before the return) satisfies every Ensures
    # vacuously; the real checker always returns its classification.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is a (status-class, datum-kind) pair.
    # (1) An "authorization required" client status (401) is WORKING.
    Ensures(Implies(status == 401, Result() == (WORKING(), DATUM_NONE())))
    # (2) A "service unavailable" server status (503) is IGNORED, carrying the
    #     transport datum.
    Ensures(Implies(status == 503, Result() == (IGNORED(), DATUM_TRANSPORT())))
    # (3) Any OTHER error status is FAILED, and its datum is the TRANSPORT error
    #     -- never the fragment-absent datum, regardless of fragment_present.
    #     This is the property the change establishes: the transport error is
    #     consulted before the document is searched.
    Ensures(Implies(is_error_status(status) and status != 401 and status != 503,
                    Result() == (FAILED(), DATUM_TRANSPORT())))
    # (4) A non-error status defers to the fragment verdict: WORKING when the
    #     fragment is present, FAILED (fragment-absent datum) when it is not.
    Ensures(Implies(not is_error_status(status) and fragment_present,
                    Result() == (WORKING(), DATUM_NONE())))
    Ensures(Implies(not is_error_status(status) and not fragment_present,
                    Result() == (FAILED(), DATUM_FRAGMENT_ABSENT())))
    # (5) A failed error-status result NEVER carries the fragment-absent datum.
    Ensures(Implies(is_error_status(status) and Result()[0] == FAILED(),
                    Result()[1] == DATUM_TRANSPORT()))
    # post-conditions-end
    # impl-start
    try:
        # Read the whole document and obtain the fragment verdict.
        found = fragment_present
        # The transport-status gate is consulted BEFORE acting on the verdict.
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec (classify_fragment_link) pins a total (status,fragment_present)->(status-class,datum-kind) function; single axiom raise_on_error_status is A-consumed (deep_model_references empty; no A-reference legs by design). ran with SBU_BENCHMARK_DIR=benchmark-verified,, python=python. All 8 attacks confirmed same-spec (adversary same-spec exit 0).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8269 <atk>):
- atk_1 unconditional 'while True: pass' on all inputs -> NOT-A-COUNTEREXAMPLE (verification failed). MustTerminate(2) rejects the divergence hole.
- atk_2 drop-401 special case (401->FAILED,TRANSPORT) -> rejected (fails Ensures clause 1).
- atk_3 drop-503 special case (503->FAILED,TRANSPORT) -> rejected (fails clause 2).
- atk_4 boundary off-by-one manual range 400<status<600 (drops 400) -> rejected (fails clause 3 for status==400).
- atk_5 control-flow/prepatch bug: gate NOT consulted, fragment scanned first so error-status+fragment-absent yields (FAILED,FRAGMENT_ABSENT) -> rejected. Reproduces model_prepatch.py failure => prepatch_reproduced=true.
- atk_6 wrong-error-datum: non-401/503 error status returns FRAGMENT_ABSENT datum -> rejected (fails clauses 3 and 5).
- atk_8 input-conditional divergence: 'while True' exactly on the F2P input (status==500 & fragment_present), correct elsewhere -> rejected. MustTerminate bites even the input-targeted loop (sharpest termination probe).
- atk_7 ungrounded-oracle ECHO: flat is_error_status dispatch producing gold-identical values on EVERY input WITHOUT calling the axiomatized gate -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 22.6s).

MANDATED RESOLVE of the sole CANDIDATE atk_7: materialized its faithful refined patch (atk_7_faithful.diff = adds response.raise_for_status() after requests.get in the fragment branch; per mapping this is atk_7's observable behavior in the repo -- is_error_status<->raise_for_status range, DATUM_TRANSPORT<->str(HTTPError)). Ran swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8269', patch, timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False. The candidate's faithful patch RESOLVES => not a break (echo policy, the audit protocol G-PANEL-1). Positive control (model.py verbatim) verifies (bash scripts/nagini_verify.sh: 'Verification successful', 20.56s).

REFINEMENT AUDIT (refinement.md): every leg is R / A-consumed / I -- no kind-3, no A-reference (deep_model_references=[] matches: the delta is adding a call site to the UNCHANGED requests.models.Response.raise_for_status, captured by the A-consumed raise_on_error_status axiom, not a deep model of a changed function). A-legs verified against the REAL repo source extracted from the base_commit image (docker cat /testbed/sphinx/builders/linkcheck.py :160-210): pre-patch fragment branch is requests.get -> check_anchor -> if not found: raise Exception('Anchor not found') with NO raise_for_status (A2/A4); shared 'except HTTPError as err:' dispatch is EXACTLY 401->('working',' - unauthorized',0), 503->('ignored',str(err),0), else->('broken',str(err),0) with NO 429/rate-limit branch (A5, version pin confirmed for Sphinx 3.3.0); 'except Exception' with is_ssl_error SSL sub-case outside slice (A6); success path response.url==req_url -> 'working','',0 (A7). The gold patch.diff is byte-identical to atk_7_faithful.diff (the one added line). A-consumed axiom Ensures/Exsures match raise_for_status (400<=status<600 -> HTTPError else None) and are G-AX-checked by axiom_check.py.

CONCLUSION: 8 distinct wrong-impl attacks (partial-domain, boundary, control-flow-effect/prepatch, ungrounded-oracle echo, unconditional + input-conditional divergence) run and fully verified; the only verifying impl (echo) has a faithful patch that RESOLVES. No verifying wrong impl produces a non-resolving faithful patch. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the spec (classify_fragment_link postconditions) vs the real post-patch check_uri fragment branch at base_commit 1e2ccd8f (Sphinx 3.3.0, verified in worktree). Setup: model self-verifies (Nagini exit 0, 16.4s); same-spec identity check exit 0.

Exhaustive comparison over the MODELED input space (status:int, fragment_present:bool):
  - error status [400,600), 401  -> real: raise_for_status->HTTPError->('working',' - unauthorized'); model (WORKING,NONE). MATCH (' - unauthorized' abstracts to DATUM_NONE per mapping.md).
  - error status, 503            -> real ('ignored',str(err)); model (IGNORED,TRANSPORT). MATCH.
  - error status, else (500/429/599...) -> real ('broken',str(err)); model (FAILED,TRANSPORT). MATCH. Confirmed no 429/rate-limit branch at this commit (grep limit_rate|rate-limited|next_check|DEFAULT_DELAY returns nothing); 429 falls into else arm.
  - non-error status, fragment absent -> real: no raise, check_anchor False -> raise Exception('Anchor not found') -> except Exception non-SSL -> ('broken',anchor-msg); model (FAILED,FRAGMENT_ABSENT). MATCH.
  - non-error status, fragment present, no redirect -> real ('working',''); model (WORKING,NONE). MATCH.

Boundary fidelity: real requests.Response.raise_for_status raises exactly on 400<=code<500 or 500<=code<600 = [400,600); model is_error_status = 400<=status<600 — identical (400 raises, 600 does not). Ordering: gate consulted before the fragment-absent raise, matching the gold hunk that inserts response.raise_for_status() before check_anchor; computing found up-front is a side-effect-free read so observationally identical.

Only coarsening: the redirect sub-case (non-error, fragment present, response.url != req_url -> real returns 'redirected'). This is governed by response.url, a dimension OUTSIDE the modeled inputs (status, fragment_present); documented in refinement.md A7 as orthogonal to the patch and not exercised by the F2P test (localhost, no redirect). It cannot be expressed as a diverging (status, fragment_present) input, so it is not a faithfulness defect of the modeled function.

The spec is not too strong: it exactly captures the transport-error-before-fragment-scan behavior the patch establishes, and every postcondition clause matches the real callee on every modeled input. No diverging input found. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = a single added line `response.raise_for_status()` in sphinx/builders/linkcheck.py, making the fragment-checking branch report the HTTP transport error before searching for the anchor. The public problem_statement ALREADY states this discriminator openly: title 'Linkcheck should report HTTP errors instead of Anchor not found', and the exact expected/actual output contrast ('broken ... - 404 Client Error: Not Found ...' vs '- Anchor \'test\' not found'). The spec view's central property — transport error consulted BEFORE the document is searched, so a server error is never mis-reported as a missing fragment — is exactly that public ask, phrased as desired end-state behavior, not as an edit.

Beyond-problem-statement leakage check (all clean): (1) no gold-patch line reproduced — the added method is abstracted as `raise_on_error_status`, never `raise_for_status`; (2) no patched file path/module (sphinx/builders/linkcheck.py) anywhere in the view; (3) the changed repo symbol `check_uri` (the only distinctive patched def, per _patch_changed_symbols) never appears in any identifier, comment, or docstring; (4) no diff markers; (5) no bug/fix/broken/previously narration in spec-view comments. Mechanical leakage.screen() returns passed=True with zero failures, corroborating.

The 401->WORKING / 503->IGNORED special cases spelled out in the spec are additional detail not in the problem_statement, but they are PRE-EXISTING behavior of the unchanged shared `except HTTPError` dispatch, not the gold edit; describing the stable surrounding behavior a verifying impl must satisfy is legitimate spec content and does not localize the one-line edit. The spec sits at an abstraction level (int status + boolean fragment bit + axiomatized gate) that reveals the required behavior — which is public — without pinpointing the concrete method/file/diff. No line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
