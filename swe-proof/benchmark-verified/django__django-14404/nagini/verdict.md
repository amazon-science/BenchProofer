# P2 adversarial audit — django__django-14404

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -87,7 +85,7 @@
     if append_slash_enabled and not url_has_trailing_slash:
         if slash_form_resolves:
             if target_view_opts_in:
-                result = list(full_path)  # type: List[int]
+                result = list(app_relative_path)  # type: List[int]
                 result.append(47)
                 return result
     raise NotFound()
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -87,8 +85,9 @@
     if append_slash_enabled and not url_has_trailing_slash:
         if slash_form_resolves:
             if target_view_opts_in:
-                result = list(full_path)  # type: List[int]
-                result.append(47)
-                return result
+                if len(full_path) > 0:
+                    result = list(full_path)  # type: List[int]
+                    result.append(47)
+                    return result
     raise NotFound()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -88,7 +86,7 @@
         if slash_form_resolves:
             if target_view_opts_in:
                 result = list(full_path)  # type: List[int]
-                result.append(47)
+                result.append(46)
                 return result
     raise NotFound()
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -86,7 +84,7 @@
     # impl-start
     if append_slash_enabled and not url_has_trailing_slash:
         if slash_form_resolves:
-            if target_view_opts_in:
+            if not target_view_opts_in:
                 result = list(full_path)  # type: List[int]
                 result.append(47)
                 return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -84,11 +82,7 @@
             or target_view_opts_in is False)
     # post-conditions-end
     # impl-start
-    if append_slash_enabled and not url_has_trailing_slash:
-        if slash_form_resolves:
-            if target_view_opts_in:
-                result = list(full_path)  # type: List[int]
-                result.append(47)
-                return result
-    raise NotFound()
+    result = list(full_path)  # type: List[int]
+    result.append(47)
+    return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -85,10 +83,9 @@
     # post-conditions-end
     # impl-start
     if append_slash_enabled and not url_has_trailing_slash:
-        if slash_form_resolves:
-            if target_view_opts_in:
-                result = list(full_path)  # type: List[int]
-                result.append(47)
-                return result
+        if target_view_opts_in:
+            result = list(full_path)  # type: List[int]
+            result.append(47)
+            return result
     raise NotFound()
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotFound(Exception):
@@ -61,7 +60,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(full_path), 1 / 2))
     Requires(Acc(list_pred(app_relative_path), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(full_path), 1 / 2))
@@ -89,6 +87,7 @@
             if target_view_opts_in:
                 result = list(full_path)  # type: List[int]
                 result.append(47)
+                result.append(47)
                 return result
     raise NotFound()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14404.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A final fall-through view decides whether a request whose URL lacks a
  trailing slash should be permanently redirected to the slash-terminated
  form. The redirect is issued only when slash-appending is enabled, the
  requested URL does not already end with a slash, the slash-terminated form
  resolves to a routable view, and that view does not opt out of slash
  appending. In every other case the view signals "not found".

  When a redirect IS issued, its target must be the request's FULL externally
  visible path -- the one a client would type, INCLUDING any deployment path
  prefix under which the application is mounted -- with a single trailing
  slash appended. The prefix-stripped, application-relative form of the path
  must NOT be used as the redirect target: a deployment served under a path
  prefix would otherwise redirect clients to a location missing that prefix.

The externally visible path and the prefix-stripped path are both modelled as
read-only `List[int]` sequences of code points (Nagini bans `str` indexing);
the trailing slash is the code point 47. The control-flow guards that decide
whether to redirect (slash-appending enabled, the URL's trailing-slash state,
the resolve outcome, the view's opt-out flag) are modelled as booleans. The
"not found" signal is a user-defined exception.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NotFound(Exception):
    """The fall-through "no routable target" signal (a not-found result)."""


# axioms-start
# (no callee needs axiomatizing: the resolve outcome and the opt-out flag are
#  modelled as the booleans they reduce to at this site; the only changed
#  operation -- which path the redirect target is built from -- is modelled
#  deeply over the code-point sequences.)
# axioms-end


# pure-start
@Pure
def with_trailing_slash(p: PSeq[int]) -> PSeq[int]:
    """The slash-terminated form of a path: the path followed by code point 47
    ('/'). This is the redirect target's shape over a chosen base path."""
    return p + PSeq(47)
# pure-end


def slash_redirect_target(
        full_path: List[int],
        app_relative_path: List[int],
        append_slash_enabled: bool,
        url_has_trailing_slash: bool,
        slash_form_resolves: bool,
        target_view_opts_in: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(full_path), 1 / 2))
    Requires(Acc(list_pred(app_relative_path), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(full_path), 1 / 2))
    Ensures(Acc(list_pred(app_relative_path), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value is returned (a redirect is issued) on EXACTLY the conjunction of
    # the four guards; otherwise the not-found signal is raised.
    Ensures(append_slash_enabled and not url_has_trailing_slash
            and slash_form_resolves and target_view_opts_in)
    # The redirect target is the FULL externally visible path (with any
    # deployment prefix) plus a single trailing slash -- grounded structurally
    # in the full-path input, never the prefix-stripped path.
    Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)))
    # The not-found signal is raised on EXACTLY the negation of that conjunction
    # (slash-appending off, the URL already ends with a slash, the slash form
    # does not resolve, or the resolved view opts out).
    Exsures(NotFound, append_slash_enabled is False
            or url_has_trailing_slash is True
            or slash_form_resolves is False
            or target_view_opts_in is False)
    # post-conditions-end
    # impl-start
    if append_slash_enabled and not url_has_trailing_slash:
        if slash_form_resolves:
            if target_view_opts_in:
                result = list(full_path)  # type: List[int]
                result.append(47)
                return result
    raise NotFound()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of nagini bundle django__django-14404. Root/project: (SBU_BENCHMARK_DIR=benchmark-verified). All commands run with python -m swebench_unified.adversary; each attack was built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Exsures byte-identical). same-spec confirmed exit 0 for all 8 files (pos_control + atk_1..7).

SPEC TIGHTNESS: the frozen spec leaves no freedom for a faithless verifying impl. Ensures(all four guards) forces normal return only when append_slash_enabled ∧ ¬url_has_trailing_slash ∧ slash_form_resolves ∧ target_view_opts_in; Exsures(NotFound, negation) forces raise only when some guard is false — together the control flow is pinned (cannot raise when all four hold; cannot return when a guard is false). Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))) pins the return value to exactly full_path+[47]. Both inputs held at Acc(...,1/2) so no vacuous overwrite. Confirmed empirically.

ATTACKS (cmd: `weakness nagini django__django-14404 <path>`; all returned exit 2 = NOT-A-COUNTEREXAMPLE, verification FAILED, not timeout):
- atk_1 (prepatch bug: target from app_relative_path) exit=2 verification failed -> spec senses the bug (G-DIFF holds). prepatch reproduced.
- atk_2 (partial-domain: redirect only when len(full_path)>0) exit=2 verification failed.
- atk_3 (boundary: append 46 '.' instead of 47 '/') exit=2 verification failed.
- atk_4 (control-flow-effect: invert opt-in guard, return when view opts OUT) exit=2 verification failed.
- atk_5 (ungrounded-oracle echo: return full_path+[47] unconditionally, ignoring guards) exit=2 verification failed.
- atk_6 (missing guard: drop slash_form_resolves check) exit=2 verification failed.
- atk_7 (boundary: double trailing slash, append 47 twice) exit=2 verification failed.
No attack was a CANDIDATE (none shares spec AND verifies), so there was no verifying wrong impl requiring a materialized faithful patch + run_resolve.

POSITIVE CONTROL: pos_control.py = exact model impl -> weakness exit=0 CANDIDATE (shares spec AND verifies in 19.7s), i.e. the correct impl verifies as expected.

A-LEG / MODEL-CORRESPONDENCE AUDIT (refinement.md): NO @ContractOnly axiom is consumed (axioms region is comment-only; with_trailing_slash is a spelled-out deep @Pure model). Legs: A1/A3/A4/A6 = R (booleans/exception carriers), A2 = I(elided; urlconf never reaches the redirect target), A5 = R+I (the FIX, redirect base = request.path/full_path, deep-modeled as full_path+[47]). No kind-3 (unexpressible-changed-op) legs. The one load-bearing deep-model reference — request.path carries the SCRIPT_NAME/FORCE_SCRIPT_NAME prefix while request.path_info does not — is validated by axiom_check.py (G-AX), which reproduces WSGIRequest.__init__ (wsgi.py:65-76) verbatim over 10 boundary + 20000 fuzz cases. Ran python axiom_check.py -> exit 0 ("G-AX OK ... prefix present => gold != bug; absent => gold == bug"). Correspondence holds.

VERDICT: SOUND. 7 distinct wrong impls (>=5 required, covering prepatch-bug, partial-domain, 2x boundary, 2x control-flow-effect, ungrounded-echo) all fail verification; none breaks the spec; positive control verifies; G-AX passes; refinement legs are all R/I with a validated A-reference and no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14404.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A final fall-through view decides whether a request whose URL lacks a
  trailing slash should be permanently redirected to the slash-terminated
  form. The redirect is issued only when slash-appending is enabled, the
  requested URL does not already end with a slash, the slash-terminated form
  resolves to a routable view, and that view does not opt out of slash
  appending. In every other case the view signals "not found".

  When a redirect IS issued, its target must be the request's FULL externally
  visible path -- the one a client would type, INCLUDING any deployment path
  prefix under which the application is mounted -- with a single trailing
  slash appended. The prefix-stripped, application-relative form of the path
  must NOT be used as the redirect target: a deployment served under a path
  prefix would otherwise redirect clients to a location missing that prefix.

The externally visible path and the prefix-stripped path are both modelled as
read-only `List[int]` sequences of code points (Nagini bans `str` indexing);
the trailing slash is the code point 47. The control-flow guards that decide
whether to redirect (slash-appending enabled, the URL's trailing-slash state,
the resolve outcome, the view's opt-out flag) are modelled as booleans. The
"not found" signal is a user-defined exception.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NotFound(Exception):
    """The fall-through "no routable target" signal (a not-found result)."""


# axioms-start
# (no callee needs axiomatizing: the resolve outcome and the opt-out flag are
#  modelled as the booleans they reduce to at this site; the only changed
#  operation -- which path the redirect target is built from -- is modelled
#  deeply over the code-point sequences.)
# axioms-end


# pure-start
@Pure
def with_trailing_slash(p: PSeq[int]) -> PSeq[int]:
    """The slash-terminated form of a path: the path followed by code point 47
    ('/'). This is the redirect target's shape over a chosen base path."""
    return p + PSeq(47)
# pure-end


def slash_redirect_target(
        full_path: List[int],
        app_relative_path: List[int],
        append_slash_enabled: bool,
        url_has_trailing_slash: bool,
        slash_form_resolves: bool,
        target_view_opts_in: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(full_path), 1 / 2))
    Requires(Acc(list_pred(app_relative_path), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(full_path), 1 / 2))
    Ensures(Acc(list_pred(app_relative_path), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value is returned (a redirect is issued) on EXACTLY the conjunction of
    # the four guards; otherwise the not-found signal is raised.
    Ensures(append_slash_enabled and not url_has_trailing_slash
            and slash_form_resolves and target_view_opts_in)
    # The redirect target is the FULL externally visible path (with any
    # deployment prefix) plus a single trailing slash -- grounded structurally
    # in the full-path input, never the prefix-stripped path.
    Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)))
    # The not-found signal is raised on EXACTLY the negation of that conjunction
    # (slash-appending off, the URL already ends with a slash, the slash form
    # does not resolve, or the resolved view opts out).
    Exsures(NotFound, append_slash_enabled is False
            or url_has_trailing_slash is True
            or slash_form_resolves is False
            or target_view_opts_in is False)
    # post-conditions-end
    # impl-start
    if append_slash_enabled and not url_has_trailing_slash:
        if slash_form_resolves:
            if target_view_opts_in:
                result = list(full_path)  # type: List[int]
                result.append(47)
                return result
    raise NotFound()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of nagini bundle django__django-14404. Root/project: (SBU_BENCHMARK_DIR=benchmark-verified). All commands run with python -m swebench_unified.adversary; each attack was built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Exsures byte-identical). same-spec confirmed exit 0 for all 8 files (pos_control + atk_1..7).

SPEC TIGHTNESS: the frozen spec leaves no freedom for a faithless verifying impl. Ensures(all four guards) forces normal return only when append_slash_enabled ∧ ¬url_has_trailing_slash ∧ slash_form_resolves ∧ target_view_opts_in; Exsures(NotFound, negation) forces raise only when some guard is false — together the control flow is pinned (cannot raise when all four hold; cannot return when a guard is false). Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))) pins the return value to exactly full_path+[47]. Both inputs held at Acc(...,1/2) so no vacuous overwrite. Confirmed empirically.

ATTACKS (cmd: `weakness nagini django__django-14404 <path>`; all returned exit 2 = NOT-A-COUNTEREXAMPLE, verification FAILED, not timeout):
- atk_1 (prepatch bug: target from app_relative_path) exit=2 verification failed -> spec senses the bug (G-DIFF holds). prepatch reproduced.
- atk_2 (partial-domain: redirect only when len(full_path)>0) exit=2 verification failed.
- atk_3 (boundary: append 46 '.' instead of 47 '/') exit=2 verification failed.
- atk_4 (control-flow-effect: invert opt-in guard, return when view opts OUT) exit=2 verification failed.
- atk_5 (ungrounded-oracle echo: return full_path+[47] unconditionally, ignoring guards) exit=2 verification failed.
- atk_6 (missing guard: drop slash_form_resolves check) exit=2 verification failed.
- atk_7 (boundary: double trailing slash, append 47 twice) exit=2 verification failed.
No attack was a CANDIDATE (none shares spec AND verifies), so there was no verifying wrong impl requiring a materialized faithful patch + run_resolve.

POSITIVE CONTROL: pos_control.py = exact model impl -> weakness exit=0 CANDIDATE (shares spec AND verifies in 19.7s), i.e. the correct impl verifies as expected.

A-LEG / MODEL-CORRESPONDENCE AUDIT (refinement.md): NO @ContractOnly axiom is consumed (axioms region is comment-only; with_trailing_slash is a spelled-out deep @Pure model). Legs: A1/A3/A4/A6 = R (booleans/exception carriers), A2 = I(elided; urlconf never reaches the redirect target), A5 = R+I (the FIX, redirect base = request.path/full_path, deep-modeled as full_path+[47]). No kind-3 (unexpressible-changed-op) legs. The one load-bearing deep-model reference — request.path carries the SCRIPT_NAME/FORCE_SCRIPT_NAME prefix while request.path_info does not — is validated by axiom_check.py (G-AX), which reproduces WSGIRequest.__init__ (wsgi.py:65-76) verbatim over 10 boundary + 20000 fuzz cases. Ran python axiom_check.py -> exit 0 ("G-AX OK ... prefix present => gold != bug; absent => gold == bug"). Correspondence holds.

VERDICT: SOUND. 7 distinct wrong impls (>=5 required, covering prepatch-bug, partial-domain, 2x boundary, 2x control-flow-effect, ungrounded-echo) all fail verification; none breaks the spec; positive control verifies; G-AX passes; refinement legs are all R/I with a validated A-reference and no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous audit; verdict FAITHFUL (the probed divergence is a documented, benign modeling boundary, not drift).

VERIFIED: model.py verifies under Nagini (exit 0, 15s). axiom_check.py passes. I materialized the gold-patched repo (HttpResponsePermanentRedirect -> HttpResponsePermanentRedirect('%s/' % request.path)) and ran the bundle's conformance_check.py against it: 100720 cases, 0 disagreements.

CONTROL FLOW is exactly faithful: model returns on EXACTLY (append_slash_enabled & not url_has_trailing_slash & slash_form_resolves & target_view_opts_in) and raises NotFound on the negation — identical to the real callee's Http404-vs-redirect branching (APPEND_SLASH, url.endswith('/'), Resolver404, should_append_slash).

REDIRECT TARGET: model postcondition Result()==with_trailing_slash(full_path)=full_path+[47]. The one place the spec could over-strengthen is the target string. I found the real observable response.url runs the target through iri_to_uri, which percent-encodes non-URL-safe code points (space -> %20, café -> caf%C3%A9), so the observable diverges from full_path+'/' on such inputs.

WHY NOT A DEFECT: (1) mapping.md §2 explicitly models the CONSTRUCTOR's Location argument (raw '%s/' % request.path), not the post-encoded header; at that boundary model == gold callee argument for ALL inputs (request.path + '/'). (2) iri_to_uri is applied identically pre/post-patch, so it is NOT the behavior under change — the change is purely path_info -> path (restoring the deployment prefix), which the model captures deeply and faithfully (model_prepatch.py building from app_relative_path fails the spec = G-DIFF sensing the bug). (3) The abstraction is honestly documented as identity on the unreserved-ASCII+'/' alphabet, and conformance_check.py scopes the domain to exactly that alphabet where iri_to_uri is identity (0/100720 disagreements). (4) All F2P/P2P tests (the G-RESOLVE correctness oracle) use URL-safe paths ('/prefix/', '/admin/admin_views/article') where model and observable coincide; a verifying impl equals gold up to refinement on the tested inputs and resolves.

The divergence lies strictly outside the modeled semantics and outside the resolve domain, so the spec is not too strong and does not drift from the tested repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no reproduced gold-patch lines, no patched file/module path in the spec view (django/contrib/admin/sites.py appears only in mapping.md/refinement.md audit docs, not the consumer view), no bug/fix narration words, and no distinctive patched symbol echoed (catch_all_view is renamed to slash_redirect_target; request/path are common). Semantically, the gold edit — build the redirect target from request.path (prefix-carrying) instead of request.path_info (prefix-stripped) — is ALREADY disclosed verbatim in the PUBLIC problem_statement: "catch_all_view returns redirect to '%s/' % request.path_info (script name cut off there) instead of '%s/' % request.path (with the script name)". The spec-view prose ('the redirect target must be the FULL externally visible path INCLUDING any deployment path prefix ... the prefix-stripped, application-relative form must NOT be used') restates that same public discriminator at the behavioral/abstract level and reveals nothing beyond the problem_statement. Leakage judged against problem_statement only (not hints, which are empty). Conclusion: the spec view does not leak the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
