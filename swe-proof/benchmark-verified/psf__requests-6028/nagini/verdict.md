# P2 adversarial audit — psf__requests-6028

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -121,20 +119,16 @@
                                         has_creds) != ToSeq(authority)))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the authority is assembled WITHOUT re-attaching the
+    # credentials (the userinfo never makes it back into the authority), so a
+    # location that carried credentials loses them on re-assembly. The query
+    # and fragment pass-through is unchanged.
     netloc = authority  # type: List[int]
-    if has_creds:
-        netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
         result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -124,17 +122,11 @@
     netloc = authority  # type: List[int]
     if has_creds:
         netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
-        result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
+        result = base + [35] + frag
     return result
     # impl-end
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -121,20 +119,12 @@
                                         has_creds) != ToSeq(authority)))
     # post-conditions-end
     # impl-start
-    netloc = authority  # type: List[int]
-    if has_creds:
-        netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
+    netloc = creds + [64] + authority  # type: List[int]
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
         result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
     return result
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -122,19 +120,13 @@
     # post-conditions-end
     # impl-start
     netloc = authority  # type: List[int]
-    if has_creds:
+    if has_creds and len(creds) > 0:
         netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
         result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
     return result
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -124,17 +122,11 @@
     netloc = authority  # type: List[int]
     if has_creds:
         netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
-    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
+    base = scheme + [58, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
         result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
     return result
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -123,18 +121,12 @@
     # impl-start
     netloc = authority  # type: List[int]
     if has_creds:
-        netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
+        netloc = authority + [64] + creds
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
     if has_query:
         result = base + [63] + query
     if has_frag:
         result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
     return result
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -121,20 +119,16 @@
                                         has_creds) != ToSeq(authority)))
     # post-conditions-end
     # impl-start
-    netloc = authority  # type: List[int]
     if has_creds:
-        netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
-    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
-    result = base  # type: List[int]
-    if has_query:
-        result = base + [63] + query
-    if has_frag:
-        result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
+        netloc = creds + [64] + authority  # type: List[int]
+    else:
+        netloc = authority  # type: List[int]
+    result = scheme + [58, 47, 47] + netloc + path  # type: List[int]
+    if has_query and has_frag:
+        result = scheme + [58, 47, 47] + netloc + path + [63] + query + [35] + frag
+    elif has_query:
+        result = scheme + [58, 47, 47] + netloc + path + [63] + query
+    elif has_frag:
+        result = scheme + [58, 47, 47] + netloc + path + [35] + frag
     return result
     # impl-end
```

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
     Requires(Acc(list_pred(path), 1 / 2))
     Requires(Acc(list_pred(query), 1 / 2))
     Requires(Acc(list_pred(frag), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(scheme), 1 / 2))
@@ -124,17 +122,11 @@
     netloc = authority  # type: List[int]
     if has_creds:
         netloc = creds + [64] + authority
-    Assert(ToSeq(netloc) == effective_authority(
-        ToSeq(creds), ToSeq(authority), has_creds))
     base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
     result = base  # type: List[int]
+    if has_frag:
+        result = base + [35] + frag
     if has_query:
-        result = base + [63] + query
-    if has_frag:
-        result = result + [35] + frag
-    Assert(ToSeq(result) == assembled(
-        ToSeq(scheme),
-        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
-        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
+        result = result + [63] + query
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-6028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A location string is normalised by re-assembling it from its already-parsed
  components: a scheme, an optional userinfo (credentials) segment, an authority
  segment (host with an optional port), a path, an optional query and an
  optional fragment. The re-assembled location MUST preserve the userinfo: when
  credentials are present they appear, joined to the authority by a single '@',
  as the leading part of the authority segment of the result -- so a location
  that carried credentials keeps them after normalisation, rather than silently
  dropping them.

  Concretely, write the effective authority as

        authority,                      if no credentials are present
        credentials + '@' + authority,  if credentials are present

  and the normalised location is the assembly

        scheme + '://' + effective_authority + path
                 (+ '?' + query, if any)  (+ '#' + fragment, if any).

  The credentials, the authority and the rest of the components are taken
  verbatim from the parse of the input. The required behaviour is that the
  credentials survive into the effective authority whenever they are present;
  the query and fragment pass through unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The component decomposition is produced by an unchanged parsing callee; the
re-assembly is an unchanged combining callee. Both are modelled deeply (the
combining concatenation is spelled out and validated == the real callee by
axiom_check.py / G-AX). The single behavioural choice under specification -- the
'@'-join that keeps the credentials in the authority -- is modelled deeply as a
verified sequence construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_authority(creds: PSeq[int], authority: PSeq[int],
                        has_creds: bool) -> PSeq[int]:
    """The authority segment that must flow into the assembly. With credentials
    present, they are prepended to the authority joined by a single '@' (64);
    otherwise the authority is used as-is. This is the behavioural choice under
    specification."""
    if has_creds:
        return creds + PSeq(64) + authority
    return authority


@Pure
def assembled(scheme: PSeq[int], authority: PSeq[int], path: PSeq[int],
              query: PSeq[int], frag: PSeq[int], has_query: bool,
              has_frag: bool) -> PSeq[int]:
    """The combining callee's assembly of a location from its components, for
    the regime these locations inhabit (non-empty authority, present scheme,
    empty params): scheme '://' authority path, with '?' query appended when a
    query is present and '#' fragment appended when a fragment is present.
    Spelled out and validated == the real combining callee by axiom_check.py
    (G-AX)."""
    base = scheme + PSeq(58, 47, 47) + authority + path
    if has_query:
        if has_frag:
            return base + PSeq(63) + query + PSeq(35) + frag
        return base + PSeq(63) + query
    if has_frag:
        return base + PSeq(35) + frag
    return base
# pure-end


def normalize_location(scheme: List[int], creds: List[int],
                       authority: List[int], path: List[int],
                       query: List[int], frag: List[int], has_creds: bool,
                       has_query: bool, has_frag: bool) -> List[int]:
    """Re-assemble a normalised location from its parsed components, preserving
    the credentials. All component carriers are read-only.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(scheme), 1 / 2))
    Requires(Acc(list_pred(creds), 1 / 2))
    Requires(Acc(list_pred(authority), 1 / 2))
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(query), 1 / 2))
    Requires(Acc(list_pred(frag), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(scheme), 1 / 2))
    Ensures(Acc(list_pred(creds), 1 / 2))
    Ensures(Acc(list_pred(authority), 1 / 2))
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(query), 1 / 2))
    Ensures(Acc(list_pred(frag), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The normalised location is the assembly over the EFFECTIVE authority,
    # i.e. the authority that retains the credentials when they are present.
    Ensures(ToSeq(Result()) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    # When credentials are present they survive into the result: the effective
    # authority is exactly credentials '@' authority, never the bare authority.
    Ensures(Implies(has_creds,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds)
                    == ToSeq(creds) + PSeq(64) + ToSeq(authority)))
    Ensures(Implies(has_creds and len(creds) > 0,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds) != ToSeq(authority)))
    # post-conditions-end
    # impl-start
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

NONE became a CANDIDATE (none verified) -> no materialized-patch resolve run was required (that step only fires for verifying candidates).

Spec structure: the postcondition (model.py:107-110) is a TOTAL, unguarded functional equation pinning ToSeq(Result()) == assembled(scheme, effective_authority(creds,authority,has_creds), path, query, frag, has_query, has_frag). Postconditions 113-119 are tautologies over the @Pure helpers. So any verifying impl must produce byte-identical abstract output; verify=>correct hinges entirely on the two A-references being sound.

Attack outcomes (all same-spec ok):
- atk_prepatch (the prepatch credential-drop bug; netloc=authority only): does NOT verify -> prepatch reproduced (G-DIFF good).
- atk2 (control-flow-effect: appends frag to `base` not `result`, dropping query when both present): rejected.
- atk3 (ungrounded: unconditionally prepends creds+'@'): rejected.
- atk4 (partial-domain `has_creds and len(creds)>0`, matching the REAL `if auth:`): rejected (spec's effective_authority prepends '@' unconditionally on has_creds).
- atk5 (boundary: scheme separator ':/' via [58,47]): rejected.
- atk6 (reversed join: authority+[64]+creds): rejected.
- atk7 (ungrounded-oracle echo: behaviorally-equivalent explicit branches, proof Asserts removed): rejected (verification could not reprove without hints — proof-strength, not a spec weakness; still not a candidate).
- atk8 (control-flow: query/frag append order swapped): rejected.
- positive_control (= model.py verbatim): VERIFIES (25.54s, `Verification successful`).

A-leg / correspondence audit (refinement.md):
- Legs A1,A2,A5 = R (type refinement); A3 = A-reference (effective_authority deep-models the credential '@'-join, the CHANGED op); A4 = A-reference (assembled deep-models urlunparse). axioms region EMPTY -> NO A-consumed, NO kind-3 steps. Confirmed every leg is R/A-reference/I.
- A-reference soundness (G-AX): ran the bundle's axiom_check.py INDEPENDENTLY in both envs. nagini-env: `G-AX OK ... over boundary + 40000 fuzz inputs` (exit 0). lean-env (has urllib3): additionally `end-to-end == real prepend_scheme_if_needed on 12 + 5000 fuzz` (exit 0). Both deep models validated == the real stdlib urlunparse and the real Python '@'.join, and the whole modelled pipeline (real parse_url -> deep models) reproduces the real post-patch prepend_scheme_if_needed on the F2P/P2P URLs + fuzz. The '@'-unconditional-on-has_creds modeling boundary is exactly why atk4 (the real `if auth:` guard) is correctly rejected: on the discriminating F2P inputs (userinfo present => non-empty creds) the two agree, and axiom_check drives that.

Gold patch.diff (bundle root) is the single `if auth: netloc='@'.join([auth,netloc])` hunk; meta G-RESOLVE resolved=true. Since verify => byte-identical abstract output and G-AX grounds that abstract output == real post-patch behavior on the tested inputs, verify => resolves. No verifying wrong impl exists after >=5 (8) distinct attacks across partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo/reversed-order/prepatch classes.

Commands (SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini psf__requests-6028 <atk>   # exit 0 all
  python -m swebench_unified.adversary weakness  nagini psf__requests-6028 <atk>   # exit 2 all (not-a-counterexample)
  bash scripts/nagini_verify.sh positive_control.py                                # exit 0 (verifies)
  <nagini-env>/python axiom_check.py ; <lean-env>/python axiom_check.py            # exit 0 (G-AX sound)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-6028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A location string is normalised by re-assembling it from its already-parsed
  components: a scheme, an optional userinfo (credentials) segment, an authority
  segment (host with an optional port), a path, an optional query and an
  optional fragment. The re-assembled location MUST preserve the userinfo: when
  credentials are present they appear, joined to the authority by a single '@',
  as the leading part of the authority segment of the result -- so a location
  that carried credentials keeps them after normalisation, rather than silently
  dropping them.

  Concretely, write the effective authority as

        authority,                      if no credentials are present
        credentials + '@' + authority,  if credentials are present

  and the normalised location is the assembly

        scheme + '://' + effective_authority + path
                 (+ '?' + query, if any)  (+ '#' + fragment, if any).

  The credentials, the authority and the rest of the components are taken
  verbatim from the parse of the input. The required behaviour is that the
  credentials survive into the effective authority whenever they are present;
  the query and fragment pass through unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The component decomposition is produced by an unchanged parsing callee; the
re-assembly is an unchanged combining callee. Both are modelled deeply (the
combining concatenation is spelled out and validated == the real callee by
axiom_check.py / G-AX). The single behavioural choice under specification -- the
'@'-join that keeps the credentials in the authority -- is modelled deeply as a
verified sequence construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_authority(creds: PSeq[int], authority: PSeq[int],
                        has_creds: bool) -> PSeq[int]:
    """The authority segment that must flow into the assembly. With credentials
    present, they are prepended to the authority joined by a single '@' (64);
    otherwise the authority is used as-is. This is the behavioural choice under
    specification."""
    if has_creds:
        return creds + PSeq(64) + authority
    return authority


@Pure
def assembled(scheme: PSeq[int], authority: PSeq[int], path: PSeq[int],
              query: PSeq[int], frag: PSeq[int], has_query: bool,
              has_frag: bool) -> PSeq[int]:
    """The combining callee's assembly of a location from its components, for
    the regime these locations inhabit (non-empty authority, present scheme,
    empty params): scheme '://' authority path, with '?' query appended when a
    query is present and '#' fragment appended when a fragment is present.
    Spelled out and validated == the real combining callee by axiom_check.py
    (G-AX)."""
    base = scheme + PSeq(58, 47, 47) + authority + path
    if has_query:
        if has_frag:
            return base + PSeq(63) + query + PSeq(35) + frag
        return base + PSeq(63) + query
    if has_frag:
        return base + PSeq(35) + frag
    return base
# pure-end


def normalize_location(scheme: List[int], creds: List[int],
                       authority: List[int], path: List[int],
                       query: List[int], frag: List[int], has_creds: bool,
                       has_query: bool, has_frag: bool) -> List[int]:
    """Re-assemble a normalised location from its parsed components, preserving
    the credentials. All component carriers are read-only.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(scheme), 1 / 2))
    Requires(Acc(list_pred(creds), 1 / 2))
    Requires(Acc(list_pred(authority), 1 / 2))
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(query), 1 / 2))
    Requires(Acc(list_pred(frag), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(scheme), 1 / 2))
    Ensures(Acc(list_pred(creds), 1 / 2))
    Ensures(Acc(list_pred(authority), 1 / 2))
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(query), 1 / 2))
    Ensures(Acc(list_pred(frag), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The normalised location is the assembly over the EFFECTIVE authority,
    # i.e. the authority that retains the credentials when they are present.
    Ensures(ToSeq(Result()) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    # When credentials are present they survive into the result: the effective
    # authority is exactly credentials '@' authority, never the bare authority.
    Ensures(Implies(has_creds,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds)
                    == ToSeq(creds) + PSeq(64) + ToSeq(authority)))
    Ensures(Implies(has_creds and len(creds) > 0,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds) != ToSeq(authority)))
    # post-conditions-end
    # impl-start
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

NONE became a CANDIDATE (none verified) -> no materialized-patch resolve run was required (that step only fires for verifying candidates).

Spec structure: the postcondition (model.py:107-110) is a TOTAL, unguarded functional equation pinning ToSeq(Result()) == assembled(scheme, effective_authority(creds,authority,has_creds), path, query, frag, has_query, has_frag). Postconditions 113-119 are tautologies over the @Pure helpers. So any verifying impl must produce byte-identical abstract output; verify=>correct hinges entirely on the two A-references being sound.

Attack outcomes (all same-spec ok):
- atk_prepatch (the prepatch credential-drop bug; netloc=authority only): does NOT verify -> prepatch reproduced (G-DIFF good).
- atk2 (control-flow-effect: appends frag to `base` not `result`, dropping query when both present): rejected.
- atk3 (ungrounded: unconditionally prepends creds+'@'): rejected.
- atk4 (partial-domain `has_creds and len(creds)>0`, matching the REAL `if auth:`): rejected (spec's effective_authority prepends '@' unconditionally on has_creds).
- atk5 (boundary: scheme separator ':/' via [58,47]): rejected.
- atk6 (reversed join: authority+[64]+creds): rejected.
- atk7 (ungrounded-oracle echo: behaviorally-equivalent explicit branches, proof Asserts removed): rejected (verification could not reprove without hints — proof-strength, not a spec weakness; still not a candidate).
- atk8 (control-flow: query/frag append order swapped): rejected.
- positive_control (= model.py verbatim): VERIFIES (25.54s, `Verification successful`).

A-leg / correspondence audit (refinement.md):
- Legs A1,A2,A5 = R (type refinement); A3 = A-reference (effective_authority deep-models the credential '@'-join, the CHANGED op); A4 = A-reference (assembled deep-models urlunparse). axioms region EMPTY -> NO A-consumed, NO kind-3 steps. Confirmed every leg is R/A-reference/I.
- A-reference soundness (G-AX): ran the bundle's axiom_check.py INDEPENDENTLY in both envs. nagini-env: `G-AX OK ... over boundary + 40000 fuzz inputs` (exit 0). lean-env (has urllib3): additionally `end-to-end == real prepend_scheme_if_needed on 12 + 5000 fuzz` (exit 0). Both deep models validated == the real stdlib urlunparse and the real Python '@'.join, and the whole modelled pipeline (real parse_url -> deep models) reproduces the real post-patch prepend_scheme_if_needed on the F2P/P2P URLs + fuzz. The '@'-unconditional-on-has_creds modeling boundary is exactly why atk4 (the real `if auth:` guard) is correctly rejected: on the discriminating F2P inputs (userinfo present => non-empty creds) the two agree, and axiom_check drives that.

Gold patch.diff (bundle root) is the single `if auth: netloc='@'.join([auth,netloc])` hunk; meta G-RESOLVE resolved=true. Since verify => byte-identical abstract output and G-AX grounds that abstract output == real post-patch behavior on the tested inputs, verify => resolves. No verifying wrong impl exists after >=5 (8) distinct attacks across partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo/reversed-order/prepatch classes.

Commands (SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini psf__requests-6028 <atk>   # exit 0 all
  python -m swebench_unified.adversary weakness  nagini psf__requests-6028 <atk>   # exit 2 all (not-a-counterexample)
  bash scripts/nagini_verify.sh positive_control.py                                # exit 0 (verifies)
  <nagini-env>/python axiom_check.py ; <lean-env>/python axiom_check.py            # exit 0 (G-AX sound)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Method: reconstructed the full modeled pipeline (real urllib3 parse_url -> deep models effective_authority + assembled) and compared byte-for-byte against the real post-patch prepend_scheme_if_needed at base_commit 0192aac2 (v2.27.0). Results: (1) Exact match on both F2P inputs [http://user:pass@example.com/path?query, http://user@example.com/path?query], all 3 base test cases, and a hand-curated edge set (IPv6, params, double-@, mailto, empty path, empty creds). (2) 300k-sample randomized fuzz surfaced divergences ONLY on empty-authority URLs (socks5://?q class), which lie outside the documented regime. (3) A second 300k fuzz restricted to non-empty final netloc (the documented regime) gave 238,086 in-regime samples with 0 divergences. The bundle's own axiom_check.py end-to-end check + fuzz uses only non-empty host pools, consistent with the regime. The spec is NOT too strong: the refined gold implementation verifies against it, and the modeled function equals the real callee on the entire input domain that determines resolution (F2P/P2P). The regime restriction is disclosed in mapping.md and refinement.md, not concealed. same-spec check on the bundle model.py = SAME (exit 0). Verdict: FAITHFUL.

Counterexample / evidence:

```
N/A — no in-regime counterexample. Empty-authority OOR inputs (socks5://?q, socks5://:0#top, etc.) diverge but are outside the modeled/tested domain and cannot affect verify⇒resolved.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present, gates.G-LEAK.status="relaxed"). Independently re-verified the disposition (not a rubber-stamp) and found no NEW leak and no broken disposition => honest recording NO-LEAKAGE (pass).

Core soundness re-confirmed: (1) scripts/nagini_verify.sh model.py => Verification successful, exit 0, 26.3s (G-VERIFY). (2) `adversary same-spec nagini psf__requests-6028 model.py` => SAME (exit 0): the spec regions are the bundle's exact spec. (3) axioms region empty; the changed '@'-join and unchanged urlunparse are modeled deeply (effective_authority/assembled), validated ==real by axiom_check.py (G-AX pass in meta). model_prepatch.py is spec-byte-identical and drops only the has_creds branch, so G-DIFF senses the userinfo drop on the discriminator.

Spec-view scan (impl region elided, i.e. the consumer-visible view via markers.spec_view over the nagini backend): the repo-symbol vocabulary is ABSENT from the spec view AND from problem_statement -- parse_url=False, urlunparse=False, urlunsplit=False, prepend_scheme_if_needed=False, netloc=False, urllib=False, utils.py=False, base_commit/0192aac=False. `netloc` occurs in model.py only inside the elided # impl-start/# impl-end region (lines 122-127, the reference implementation), never in the docstring/pure/pre/post; it is NOT in the spec view. The only `parse*` hits in the spec view are abstract ('already-parsed components', 'the parse of the input', 'unchanged parsing callee') -- not the concrete `parse_url` symbol. Concrete repo symbol names (parse_url/urlunparse/netloc/prepend_scheme_if_needed) appear only in mapping.md/refinement.md, which are auditor-facing G-EQ docs, not the consumer spec view.

Dispositioned facet re-confirmed and unavoidable: the spec view (docstring L8-27 + postconditions L105-119) names the userinfo/credentials '@'-join into the effective authority -- the gold's tested discriminator (`netloc = '@'.join([auth, netloc])`), which lives only in hints_text/gold internals, NOT in problem_statement. The public problem_statement is a pure proxy-407 symptom report ('error 407 ... I should get 200', requests.get(..., proxies=...) snippet, system-info JSON) with no userinfo/netloc/re-assembly pointer. Per relaxed-leakage policy (spec_guide.md directive 6) faithful+non-leaking is provably impossible here (PS reports a status-code symptom; gold fixes URL-component re-assembly -- different surfaces), so the leak of the discriminator is the accepted, documented disposition, not a new defect. The verify=>correct guarantee is unaffected (core sound, gold resolves, G-RESOLVE pass); only the secondary no-leakage property is relaxed for this documented instance.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
