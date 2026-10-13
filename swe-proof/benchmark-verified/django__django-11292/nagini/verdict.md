# P2 adversarial audit — django__django-11292

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -65,15 +63,12 @@
     Ensures(Result() == skip_request_offered(requires_validation))
     # post-conditions-end
     # impl-start
-    if requires_validation:
-        return True
     return False
     # impl-end
 
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -73,7 +71,6 @@
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
@@ -88,8 +85,7 @@
     Ensures(Implies(requires_validation and not requested_skip, Result()))
     # post-conditions-end
     # impl-start
-    skip = parser_offers_skip(requires_validation) and requested_skip
-    if requires_validation and not skip:
+    if requires_validation:
         return True
     return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -73,7 +71,6 @@
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
@@ -88,8 +85,7 @@
     Ensures(Implies(requires_validation and not requested_skip, Result()))
     # post-conditions-end
     # impl-start
-    skip = parser_offers_skip(requires_validation) and requested_skip
-    if requires_validation and not skip:
+    if requires_validation != requested_skip:
         return True
     return False
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -65,15 +63,12 @@
     Ensures(Result() == skip_request_offered(requires_validation))
     # post-conditions-end
     # impl-start
-    if requires_validation:
-        return True
-    return False
+    return True
     # impl-end
 
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -73,7 +71,6 @@
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
@@ -89,7 +86,7 @@
     # post-conditions-end
     # impl-start
     skip = parser_offers_skip(requires_validation) and requested_skip
-    if requires_validation and not skip:
+    if requires_validation and skip:
         return True
     return False
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -65,15 +63,12 @@
     Ensures(Result() == skip_request_offered(requires_validation))
     # post-conditions-end
     # impl-start
-    if requires_validation:
-        return True
-    return False
+    return not requires_validation
     # impl-end
 
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -57,7 +56,6 @@
 
 def parser_offers_skip(requires_validation: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) The skip request is offered precisely when validation is required.
@@ -73,7 +71,6 @@
 
 def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) Validation runs iff it is required AND no effective skip is in force.
@@ -88,8 +85,7 @@
     Ensures(Implies(requires_validation and not requested_skip, Result()))
     # post-conditions-end
     # impl-start
-    skip = parser_offers_skip(requires_validation) and requested_skip
-    if requires_validation and not skip:
+    if effective_skip(requires_validation, requested_skip):
         return True
     return False
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11292.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management command can be told from its invocation to forgo its validation
  pass before the work is done. Two coordinated guarantees express this:

  (1) The command line surfaces a "skip validation" request exactly for the
      commands that would otherwise perform validation. That is, the invocation
      parser accepts the skip request precisely when the command is one that
      requires validation; for a command that never validates, no such request
      is offered.

  (2) Whether the validation pass actually runs is decided as: it runs if and
      only if the command requires validation AND no effective skip request is
      in force. The skip request is *effective* exactly when the parser accepted
      it (guarantee 1); a skip request that the parser does not accept has no
      effect. Consequently, for a command that requires validation, a skip
      request supplied at invocation is honoured: the validation pass does not
      run.

The two boolean inputs are: whether the command requires validation, and
whether the invocation carried a skip request. No callee is axiomatized; the
decision is pure boolean logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the parser-exposure and the run/skip decision are pure
# boolean logic, modelled deeply.
# axioms-end


# pure-start
@Pure
def skip_request_offered(requires_validation: bool) -> bool:
    """Whether the invocation parser offers (accepts) a skip request. The skip
    request is offered exactly for commands that require validation."""
    return requires_validation


@Pure
def effective_skip(requires_validation: bool, requested_skip: bool) -> bool:
    """The skip request that is actually in force: a request supplied at
    invocation takes effect only when the parser offered it; otherwise it is
    dropped (treated as no request)."""
    if skip_request_offered(requires_validation):
        return requested_skip
    return False
# pure-end


def parser_offers_skip(requires_validation: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (1) The skip request is offered precisely when validation is required.
    Ensures(Result() == requires_validation)
    Ensures(Result() == skip_request_offered(requires_validation))
    # post-conditions-end
    # impl-start
    if requires_validation:
        return True
    return False
    # impl-end


def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (2) Validation runs iff it is required AND no effective skip is in force.
    Ensures(Result() == (requires_validation and not effective_skip(requires_validation, requested_skip)))
    # A command that does not require validation never runs it.
    Ensures(Implies(not requires_validation, not Result()))
    # The discriminating clause: for a command that requires validation, a skip
    # request supplied at invocation is honoured (validation does NOT run). This
    # is exactly what a pre-fix gating that drops the request fails to satisfy.
    Ensures(Implies(requires_validation and requested_skip, not Result()))
    # And without a skip request, a command that requires validation runs it.
    Ensures(Implies(requires_validation and not requested_skip, Result()))
    # post-conditions-end
    # impl-start
    skip = parser_offers_skip(requires_validation) and requested_skip
    if requires_validation and not skip:
        return True
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Refinement-fidelity (G-EQ) adversarial audit for django__django-11292 (nagini). SBU_BENCHMARK_DIR=benchmark-verified, verifier via scripts/nagini_verify.sh; adversary via python -m swebench_unified.adversary.

SPEC STRUCTURE (why fully pinned): both impl functions have empty Requires and postconditions that fully determine Result() over the finite 2x2 boolean domain. parser_offers_skip: Ensures(Result()==requires_validation). will_run_validation: Ensures(Result()==(rv and not effective_skip(rv,rs)))==(rv and not rs), plus Implies(not rv,not R), Implies(rv and rs,not R), Implies(rv and not rs,R). No point of the domain is left free, so no behaviourally-distinct impl can verify.

A-LEG AUDIT (my focus): NO consumed axioms (kind-2 absent). The two genuinely-changed ops (create_parser skip-option registration; execute gate read) are modeled DEEPLY as boolean logic; their reliance on stdlib argparse store_true exposure/default semantics is the single A-REFERENCE. Ran the bundle's axiom_check.py (G-AX) against REAL argparse: EXIT 0 -> 'G-AX OK: argparse store_true exposure/default semantics + the gating expression match the deep model over the boolean cross-product'. refinement.md legs are all R / I / A-reference (no kind-3); the A-reference correspondence to the real callees (base.py:289 create_parser, base.py:360 execute gate) holds. conformance_check.py present (G-CONF) exercising the real /testbed BaseCommand end-to-end.

### ATTACKS (all same-spec exit 0; all weakness exit 2 = rejected by verifier; no timeouts/infra errors):
Commands (per attack N): python -m swebench_unified.adversary same-spec nagini django__django-11292 <path>  (exit 0 all 7); python -m swebench_unified.adversary weakness nagini django__django-11292 <path>  (exit 2 all 7, 'attack does not verify (verification failed) - the spec rejected this impl').
 atk_1: site-A prepatch bug, parser_offers_skip=return False -> rejected.
 atk_2: site-B prepatch bug, gate ignores skip (if rv: return True) -> rejected.
 atk_3: boundary single-point, will_run = (rv != rs) [wrong only at (F,T)] -> rejected.
 atk_4: partial-domain, parser_offers_skip=return True (offers for non-validating) -> rejected.
 atk_5: control-flow-effect, gate inverted (rv and skip) -> rejected.
 atk_6: fully-inverted parser_offers_skip=not rv -> rejected.
 atk_7: ungrounded-oracle echo, will_run returns effective_skip(rv,rs) -> rejected.

NO CANDIDATE emerged (no same-spec impl both shared spec AND verified), so no faithful refined patch needed materializing and no run_resolve was required; patches={} accordingly.

POSITIVE CONTROL: model.py copied to positive_control.py verifies (exit 0, 9.79s). PREPATCH REPRODUCED: model_prepatch.py fails parser_offers_skip postcondition (Result()==requires_validation might not hold, exit 1); model_prepatch_2.py fails will_run_validation postcondition (exit 1). Both discriminating clauses reproduced.

MINOR NOTE (non-blocking): no standalone patch.diff file in the bundle dir (gold patch lives in meta.json/harness); refinement.md quotes it inline as 'verbatim'. Immaterial to this verdict since no CANDIDATE required a resolve run.

VERDICT: SOUND. >=5 (7) distinct wrong impls run through the official adversary weakness check; none is a verifying counterexample; A-reference (G-AX) sound; refinement legs clean (no kind-3).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11292.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management command can be told from its invocation to forgo its validation
  pass before the work is done. Two coordinated guarantees express this:

  (1) The command line surfaces a "skip validation" request exactly for the
      commands that would otherwise perform validation. That is, the invocation
      parser accepts the skip request precisely when the command is one that
      requires validation; for a command that never validates, no such request
      is offered.

  (2) Whether the validation pass actually runs is decided as: it runs if and
      only if the command requires validation AND no effective skip request is
      in force. The skip request is *effective* exactly when the parser accepted
      it (guarantee 1); a skip request that the parser does not accept has no
      effect. Consequently, for a command that requires validation, a skip
      request supplied at invocation is honoured: the validation pass does not
      run.

The two boolean inputs are: whether the command requires validation, and
whether the invocation carried a skip request. No callee is axiomatized; the
decision is pure boolean logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the parser-exposure and the run/skip decision are pure
# boolean logic, modelled deeply.
# axioms-end


# pure-start
@Pure
def skip_request_offered(requires_validation: bool) -> bool:
    """Whether the invocation parser offers (accepts) a skip request. The skip
    request is offered exactly for commands that require validation."""
    return requires_validation


@Pure
def effective_skip(requires_validation: bool, requested_skip: bool) -> bool:
    """The skip request that is actually in force: a request supplied at
    invocation takes effect only when the parser offered it; otherwise it is
    dropped (treated as no request)."""
    if skip_request_offered(requires_validation):
        return requested_skip
    return False
# pure-end


def parser_offers_skip(requires_validation: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (1) The skip request is offered precisely when validation is required.
    Ensures(Result() == requires_validation)
    Ensures(Result() == skip_request_offered(requires_validation))
    # post-conditions-end
    # impl-start
    if requires_validation:
        return True
    return False
    # impl-end


def will_run_validation(requires_validation: bool, requested_skip: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (2) Validation runs iff it is required AND no effective skip is in force.
    Ensures(Result() == (requires_validation and not effective_skip(requires_validation, requested_skip)))
    # A command that does not require validation never runs it.
    Ensures(Implies(not requires_validation, not Result()))
    # The discriminating clause: for a command that requires validation, a skip
    # request supplied at invocation is honoured (validation does NOT run). This
    # is exactly what a pre-fix gating that drops the request fails to satisfy.
    Ensures(Implies(requires_validation and requested_skip, not Result()))
    # And without a skip request, a command that requires validation runs it.
    Ensures(Implies(requires_validation and not requested_skip, Result()))
    # post-conditions-end
    # impl-start
    skip = parser_offers_skip(requires_validation) and requested_skip
    if requires_validation and not skip:
        return True
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Refinement-fidelity (G-EQ) adversarial audit for django__django-11292 (nagini). SBU_BENCHMARK_DIR=benchmark-verified, verifier via scripts/nagini_verify.sh; adversary via python -m swebench_unified.adversary.

SPEC STRUCTURE (why fully pinned): both impl functions have empty Requires and postconditions that fully determine Result() over the finite 2x2 boolean domain. parser_offers_skip: Ensures(Result()==requires_validation). will_run_validation: Ensures(Result()==(rv and not effective_skip(rv,rs)))==(rv and not rs), plus Implies(not rv,not R), Implies(rv and rs,not R), Implies(rv and not rs,R). No point of the domain is left free, so no behaviourally-distinct impl can verify.

A-LEG AUDIT (my focus): NO consumed axioms (kind-2 absent). The two genuinely-changed ops (create_parser skip-option registration; execute gate read) are modeled DEEPLY as boolean logic; their reliance on stdlib argparse store_true exposure/default semantics is the single A-REFERENCE. Ran the bundle's axiom_check.py (G-AX) against REAL argparse: EXIT 0 -> 'G-AX OK: argparse store_true exposure/default semantics + the gating expression match the deep model over the boolean cross-product'. refinement.md legs are all R / I / A-reference (no kind-3); the A-reference correspondence to the real callees (base.py:289 create_parser, base.py:360 execute gate) holds. conformance_check.py present (G-CONF) exercising the real /testbed BaseCommand end-to-end.

### ATTACKS (all same-spec exit 0; all weakness exit 2 = rejected by verifier; no timeouts/infra errors):
Commands (per attack N): python -m swebench_unified.adversary same-spec nagini django__django-11292 <path>  (exit 0 all 7); python -m swebench_unified.adversary weakness nagini django__django-11292 <path>  (exit 2 all 7, 'attack does not verify (verification failed) - the spec rejected this impl').
 atk_1: site-A prepatch bug, parser_offers_skip=return False -> rejected.
 atk_2: site-B prepatch bug, gate ignores skip (if rv: return True) -> rejected.
 atk_3: boundary single-point, will_run = (rv != rs) [wrong only at (F,T)] -> rejected.
 atk_4: partial-domain, parser_offers_skip=return True (offers for non-validating) -> rejected.
 atk_5: control-flow-effect, gate inverted (rv and skip) -> rejected.
 atk_6: fully-inverted parser_offers_skip=not rv -> rejected.
 atk_7: ungrounded-oracle echo, will_run returns effective_skip(rv,rs) -> rejected.

NO CANDIDATE emerged (no same-spec impl both shared spec AND verified), so no faithful refined patch needed materializing and no run_resolve was required; patches={} accordingly.

POSITIVE CONTROL: model.py copied to positive_control.py verifies (exit 0, 9.79s). PREPATCH REPRODUCED: model_prepatch.py fails parser_offers_skip postcondition (Result()==requires_validation might not hold, exit 1); model_prepatch_2.py fails will_run_validation postcondition (exit 1). Both discriminating clauses reproduced.

MINOR NOTE (non-blocking): no standalone patch.diff file in the bundle dir (gold patch lives in meta.json/harness); refinement.md quotes it inline as 'verbatim'. Immaterial to this verdict since no CANDIDATE required a resolve run.

VERDICT: SOUND. >=5 (7) distinct wrong impls run through the official adversary weakness check; none is a verifying counterexample; A-reference (G-AX) sound; refinement legs clean (no kind-3).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11292 nagini bundle.

Spec models two boolean-input functions: parser_offers_skip(requires_validation) and will_run_validation(requires_validation, requested_skip), corresponding to the gold patch's two changed sites in django/core/management/base.py: (A) create_parser registering '--skip-checks' (store_true) iff self.requires_system_checks, and (B) the execute gate `if self.requires_system_checks and not options['skip_checks']: self.check()`.

Verification steps:
1. Spec region byte-identical: `adversary same-spec` -> SAME, exit 0.
2. model.py verifies with pinned Nagini verifier (Verification successful, 10.45s).
3. axiom_check.py (G-AX) exit 0 against real stdlib argparse.
4. Built real BaseCommand subclasses at base_commit (worktree @ eb16c7260e...gold-patch applied) with requires_system_checks True/False, ran create_parser + parse_args + the gold gate over the FULL boolean cross-product of (requires_validation, --skip-checks token present). Real vs model:
   - rv=True, token=False:  real decision=True  == model True  (validation runs)
   - rv=True, token=True:   real decision=False == model False (skip honoured, the fix)
   - rv=False,token=False:  real decision=False == model False
   - rv=False,token=True:   real parser REJECTS token (CommandError/SystemExit -> no effect); model effective_skip=False, decision=False. The modeling boundary (mapping.md §2, effective_skip==False when option not offered) correctly captures that an unregistered token has no effect.

No diverging input exists over the domain the two boolean carriers abstract. The spec's postconditions (Result()==requires_validation for the parser; Result()==(rv and not effective_skip) plus the discriminating Implies(rv and requested_skip, not Result()) for the gate) are all exactly satisfied by the real repo. The spec is neither too strong nor drifting; it agrees with the real callee on every input.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Manual semantic audit of the spec view (docstring + parser_offers_skip/will_run_validation contracts, impl regions elided) confirms no leak beyond the public problem_statement, which already discloses: 'Add --skip-checks option to management commands', the existing skip_checks stealth option, and the goal of exposing it on the command line to skip checks.

Checks performed:
- No diff markers, no patched file path (django/core/management/base.py), no dotted module path, and no reproduced gold-patch line (>=8 chars) appear in the spec view.
- Patched repo symbols {create_parser, execute, requires_system_checks, BaseCommand, DjangoHelpFormatter, skip_checks} are NOT named in any spec-view comment/docstring and are NOT embedded in any spec-view identifier. Spec identifiers (parser_offers_skip, will_run_validation, skip_request_offered, effective_skip, requires_validation, requested_skip) are abstract, non-localizing renames.
- No bug/fix/pre-patch narration in comments.
- The two guarantees are stated as DESIRED BEHAVIOUR at a boolean abstraction (validation pass / skip request), not as an edit. Guarantee (1) 'skip offered iff command requires validation' mirrors the gold `if self.requires_system_checks:` guard, but it is expressed purely behaviorally without naming the repo symbol or the two edit sites, and is a natural derivation of the public goal (skipping system checks is only meaningful for commands that run system checks). It localizes nothing in the repo.

The spec view stays at the twin-artifact/behavioral abstraction and does not reconstruct the gold edit's location or content beyond the public problem_statement (hints_text is empty). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
