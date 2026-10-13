# P2 adversarial audit — django__django-11451

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -128,17 +121,15 @@
     eff = identifier  # type: Optional[int]
     if eff is None:
         eff = fallback_identifier
-    if eff is None or secret is None:
-        return None
+    # Pre-patch: no early shortcut for absent credentials; the directory is
+    # consulted unconditionally and the verification primitive is run once on
+    # every path, even when the credentials were absent.
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
     self.verifications = self.verifications + 1
-    if not directory_recognises(eff):
+    if eff is None or not directory_recognises(eff):
         return None
     else:
-        if secret_verifies(eff, secret):
+        if secret is not None and secret_verifies(eff, secret):
             return eff
         return None
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -131,13 +124,10 @@
     if eff is None or secret is None:
         return None
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
-    self.verifications = self.verifications + 1
     if not directory_recognises(eff):
         return None
     else:
+        self.verifications = self.verifications + 1
         if secret_verifies(eff, secret):
             return eff
         return None
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -130,14 +123,11 @@
         eff = fallback_identifier
     if eff is None or secret is None:
         return None
-    self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
     self.verifications = self.verifications + 1
     if not directory_recognises(eff):
         return None
     else:
+        self.lookups = self.lookups + 1
         if secret_verifies(eff, secret):
             return eff
         return None
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -131,12 +124,9 @@
     if eff is None or secret is None:
         return None
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
     self.verifications = self.verifications + 1
     if not directory_recognises(eff):
-        return None
+        return eff
     else:
         if secret_verifies(eff, secret):
             return eff
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -130,15 +123,12 @@
         eff = fallback_identifier
     if eff is None or secret is None:
         return None
+    self.verifications = self.verifications + 1
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
-    self.verifications = self.verifications + 1
-    if not directory_recognises(eff):
-        return None
-    else:
+    if directory_recognises(eff):
         if secret_verifies(eff, secret):
             return eff
-        return None
+        else:
+            return None
+    return None
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -125,20 +118,14 @@
                     Result() is None))
     # post-conditions-end
     # impl-start
-    eff = identifier  # type: Optional[int]
-    if eff is None:
-        eff = fallback_identifier
-    if eff is None or secret is None:
+    eff = fallback_identifier if identifier is None else identifier  # type: Optional[int]
+    if secret is None or eff is None:
         return None
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
     self.verifications = self.verifications + 1
     if not directory_recognises(eff):
         return None
-    else:
-        if secret_verifies(eff, secret):
-            return eff
+    if not secret_verifies(eff, secret):
         return None
+    return eff
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,11 +77,6 @@
 
 class Checker:
     def __init__(self) -> None:
-        # Level 1: the constructor is straight-line (two field stores, no loop
-        # and no obligated callee), so it needs no room beneath itself. Being
-        # obligated at all is what leaves level 6 in authenticate room to
-        # construct a Checker without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
         Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
         self.lookups = 0  # type: int
@@ -94,7 +88,6 @@
     # pre-conditions-start
     Requires(Acc(self.lookups) and Acc(self.verifications))
     Requires(self.lookups >= 0 and self.verifications >= 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.lookups) and Acc(self.verifications))
@@ -128,17 +121,14 @@
     eff = identifier  # type: Optional[int]
     if eff is None:
         eff = fallback_identifier
-    if eff is None or secret is None:
+    if eff is None:
+        return None
+    if secret is None:
         return None
     self.lookups = self.lookups + 1
-    # The verification primitive runs exactly once on every both-present path:
-    # on the recognised path it is the secret check; on the unrecognised path
-    # it is the timing-defence invocation.
     self.verifications = self.verifications + 1
-    if not directory_recognises(eff):
-        return None
-    else:
-        if secret_verifies(eff, secret):
-            return eff
-        return None
+    recognised = directory_recognises(eff)  # type: bool
+    if recognised and secret_verifies(eff, secret):
+        return eff
+    return None
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11451.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A credential-checking authentication routine is handed an identifier and a
  secret, either of which may be absent. The routine answers with the matching
  account when (and only when) it can establish one, and otherwise with nothing.
  Establishing an account costs two observable, externally-expensive
  operations: a directory lookup (a database round trip) and one invocation of
  the secret-verification primitive (a deliberately costly hash). The
  verification primitive is run once whenever both credentials are present —
  regardless of whether the identifier is recognised — so that the response
  time of an unrecognised identifier is indistinguishable from a recognised
  one.

  The behaviour required of the routine:

    (1) When EITHER the identifier OR the secret is absent, the routine
        answers with nothing AND performs neither expensive operation: the
        directory is not consulted and the verification primitive is not run.
        (The caller offered credentials shaped for some other checker; this
        checker has nothing to contribute and must not spend the cost.)

    (2) When BOTH are present, the directory is consulted exactly once and the
        verification primitive is run exactly once. If the directory recognises
        the identifier and the secret verifies for an account that is permitted
        to authenticate, the routine answers with that recognised account
        (exactly the account carrying that identifier); otherwise it answers
        with nothing.

  An absent identifier may first be recovered from a side channel of extra
  keyword arguments; only if it is still absent after that does clause (1)
  apply.

The identifier and the secret are modelled as ``Optional[int]`` (absent is
``None``; present is an opaque code). The checker carries two non-negative
counters recording how many times each expensive operation has run, so the
"performs neither expensive operation" guarantee is stated exactly. The
directory's recognition test and the secret verification are unchanged opaque
primitives, axiomatized as pure decisions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def directory_recognises(identifier: int) -> bool:
    """The unchanged directory-lookup decision: whether an account with this
    natural identifier exists. A pure decision over the current directory; it
    has no side effects of its own — the cost of consulting the directory is
    accounted for separately by the checker's lookup counter. Provenance +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def secret_verifies(identifier: int, secret: int) -> bool:
    """The unchanged secret-verification-and-permission decision for a
    recognised account: whether the supplied secret matches the stored secret
    AND the account is permitted to authenticate. A pure decision; the cost of
    the verification primitive is accounted for separately by the checker's
    verification counter. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


class Checker:
    def __init__(self) -> None:
        Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
        Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
        self.lookups = 0  # type: int
        self.verifications = 0  # type: int


def authenticate(self: Checker, identifier: Optional[int], secret: Optional[int],
                 fallback_identifier: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(self.lookups) and Acc(self.verifications))
    Requires(self.lookups >= 0 and self.verifications >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.lookups) and Acc(self.verifications))
    # (1) Either credential absent (after recovery) => answer nothing, and
    #     NEITHER expensive operation runs (both counters unchanged).
    Ensures(Implies((identifier is None and fallback_identifier is None) or secret is None,
                    Result() is None
                    and self.lookups == Old(self.lookups)
                    and self.verifications == Old(self.verifications)))
    # (2) Both present => the directory is consulted exactly once AND the
    #     verification primitive is run exactly once (on every both-present
    #     path: recognised-correct, recognised-wrong, and unrecognised alike).
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None,
                    self.lookups == Old(self.lookups) + 1
                    and self.verifications == Old(self.verifications) + 1))
    # (2a) Recognised => answer that account iff the secret verifies, and the
    #      answer is exactly the recognised account (the one carrying that
    #      identifier); otherwise nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    ((Result() is not None) ==
                        secret_verifies(identifier if identifier is not None else fallback_identifier, secret))  # type: ignore
                    and Implies(Result() is not None,
                                Result() == (identifier if identifier is not None else fallback_identifier))))
    # (2b) Unrecognised => answer nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and not directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    Result() is None))
    # post-conditions-end
    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    # The verification primitive runs exactly once on every both-present path:
    # on the recognised path it is the secret check; on the unrecognised path
    # it is the timing-defence invocation.
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11451 (nagini). adversary run with python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: authenticate() is a COMPLETE functional spec over all observables. Clause(1): identifier(after fallback recovery) OR secret absent => Result None AND both counters unchanged. Clause(2): both present => lookups+1 AND verifications+1 (on EVERY both-present path). Clause(2a): recognised => (Result is not None)==secret_verifies AND Result==eff. Clause(2b): unrecognised => None. The full credential matrix and both counters are pinned exactly by directory_recognises/secret_verifies, leaving no unconstrained observable slack.

ATTACKS (all same-spec confirmed via `adversary same-spec`, byte-identical spec signature; verified with `bash scripts/nagini_verify.sh`):
- atk_1.py = prepatch bug (unconditional lookups+verifications increments before the absent-guard). same-spec=SAME. nagini_verify exit=1 (FAILS clause 1). PREPATCH REPRODUCED.
- atk_2.py = partial-domain: verifications incremented only on recognised branch. SAME. exit=1 (FAILS clause 2 on unrecognised path).
- atk_3.py = partial-domain: lookups incremented only on recognised branch. SAME. exit=1 (FAILS clause 2 on unrecognised path).
- atk_4.py = control-flow-effect: returns eff on unrecognised branch. SAME. exit=1 (FAILS clause 2b).
- atk_5.py = ungrounded-oracle echo: reordered counter increments + restructured recognised branch (behaviourally identical). SAME. exit=0 VERIFIES -> CANDIDATE.
- atk_6.py = ternary eff assignment + reordered/split guards (equivalent). SAME. exit=0 VERIFIES -> CANDIDATE.
- atk_7.py = split absent guards + explicit `recognised` bool var (equivalent). SAME. exit=0 VERIFIES -> CANDIDATE.
positive_control.py (== model.py impl) VERIFIES exit=0.

Commands used per attack:
  python -m swebench_unified.adversary same-spec nagini django__django-11451 <atk>
  bash scripts/nagini_verify.sh <atk>
  (and `adversary weakness nagini django__django-11451 <atk>` semantics = same-spec AND verify.)

CANDIDATE RESOLVE (MANDATORY): atk_5/atk_6/atk_7 each refine, via refinement.md's reverse operation map, to the SAME real Django control flow (kwargs fallback -> inserted absent-credential guard -> get_by_natural_key/except DoesNotExist:set_password -> check_password & user_can_authenticate). They differ only in UNOBSERVABLE internal ordering (which counter increments first / branch shape), which the spec does not constrain and which maps to no distinct real op. Hence each faithful refined patch is byte-identical to the gold guard insertion. Verified byte-identical to bundle patch.diff via diff. Materialized patch_atk_5.diff/patch_atk_6.diff/patch_atk_7.diff (identical) and RAN the official harness once (content-addressed by patch, so one run covers all three):
  run_resolve('django__django-11451', <patch>, run_id='sbu-eq-atk-1fbmlunv', timeout=1800, retries=1)
  RESULT: resolved=True completed=True note='resolved' flaky=False.
Every verifying wrong-impl's faithful patch RESOLVES => no verify-but-incorrect impl exhibited => spec is NOT too weak.

REFINEMENT.MD LEG AUDIT: 7 steps tagged R / R+I / I / R / R / A-consumed+I / A-consumed+R. No kind-3 (unexpressible-changed-op), no A-reference, no dead axioms. The CHANGED operation (early-return shortcut avoiding both expensive ops) is modeled DEEPLY via the lookups/verifications counters + control flow, NOT axiomatized. The two A-consumed axioms cover only UNCHANGED decision primitives: directory_recognises <-> get_by_natural_key (raises DoesNotExist iff no account; base_user.py:43) and secret_verifies <-> check_password AND user_can_authenticate (backends.py:49). Correspondence holds and is executably validated by axiom_check.py (drives real ModelBackend.authenticate against live in-memory auth DB, instrumented MD5 encode counter + CaptureQueriesContext, over the full matrix incl. both-tree detection).

VERDICT: SOUND. 7 attacks encoded and fully verified (4 correctly rejected incl. prepatch; 3 verifying candidates all resolve). Positive control verifies. No falsification found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11451.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A credential-checking authentication routine is handed an identifier and a
  secret, either of which may be absent. The routine answers with the matching
  account when (and only when) it can establish one, and otherwise with nothing.
  Establishing an account costs two observable, externally-expensive
  operations: a directory lookup (a database round trip) and one invocation of
  the secret-verification primitive (a deliberately costly hash). The
  verification primitive is run once whenever both credentials are present —
  regardless of whether the identifier is recognised — so that the response
  time of an unrecognised identifier is indistinguishable from a recognised
  one.

  The behaviour required of the routine:

    (1) When EITHER the identifier OR the secret is absent, the routine
        answers with nothing AND performs neither expensive operation: the
        directory is not consulted and the verification primitive is not run.
        (The caller offered credentials shaped for some other checker; this
        checker has nothing to contribute and must not spend the cost.)

    (2) When BOTH are present, the directory is consulted exactly once and the
        verification primitive is run exactly once. If the directory recognises
        the identifier and the secret verifies for an account that is permitted
        to authenticate, the routine answers with that recognised account
        (exactly the account carrying that identifier); otherwise it answers
        with nothing.

  An absent identifier may first be recovered from a side channel of extra
  keyword arguments; only if it is still absent after that does clause (1)
  apply.

The identifier and the secret are modelled as ``Optional[int]`` (absent is
``None``; present is an opaque code). The checker carries two non-negative
counters recording how many times each expensive operation has run, so the
"performs neither expensive operation" guarantee is stated exactly. The
directory's recognition test and the secret verification are unchanged opaque
primitives, axiomatized as pure decisions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def directory_recognises(identifier: int) -> bool:
    """The unchanged directory-lookup decision: whether an account with this
    natural identifier exists. A pure decision over the current directory; it
    has no side effects of its own — the cost of consulting the directory is
    accounted for separately by the checker's lookup counter. Provenance +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def secret_verifies(identifier: int, secret: int) -> bool:
    """The unchanged secret-verification-and-permission decision for a
    recognised account: whether the supplied secret matches the stored secret
    AND the account is permitted to authenticate. A pure decision; the cost of
    the verification primitive is accounted for separately by the checker's
    verification counter. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


class Checker:
    def __init__(self) -> None:
        Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
        Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
        self.lookups = 0  # type: int
        self.verifications = 0  # type: int


def authenticate(self: Checker, identifier: Optional[int], secret: Optional[int],
                 fallback_identifier: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(self.lookups) and Acc(self.verifications))
    Requires(self.lookups >= 0 and self.verifications >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.lookups) and Acc(self.verifications))
    # (1) Either credential absent (after recovery) => answer nothing, and
    #     NEITHER expensive operation runs (both counters unchanged).
    Ensures(Implies((identifier is None and fallback_identifier is None) or secret is None,
                    Result() is None
                    and self.lookups == Old(self.lookups)
                    and self.verifications == Old(self.verifications)))
    # (2) Both present => the directory is consulted exactly once AND the
    #     verification primitive is run exactly once (on every both-present
    #     path: recognised-correct, recognised-wrong, and unrecognised alike).
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None,
                    self.lookups == Old(self.lookups) + 1
                    and self.verifications == Old(self.verifications) + 1))
    # (2a) Recognised => answer that account iff the secret verifies, and the
    #      answer is exactly the recognised account (the one carrying that
    #      identifier); otherwise nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    ((Result() is not None) ==
                        secret_verifies(identifier if identifier is not None else fallback_identifier, secret))  # type: ignore
                    and Implies(Result() is not None,
                                Result() == (identifier if identifier is not None else fallback_identifier))))
    # (2b) Unrecognised => answer nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and not directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    Result() is None))
    # post-conditions-end
    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    # The verification primitive runs exactly once on every both-present path:
    # on the recognised path it is the secret check; on the unrecognised path
    # it is the timing-defence invocation.
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11451 (nagini). adversary run with python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: authenticate() is a COMPLETE functional spec over all observables. Clause(1): identifier(after fallback recovery) OR secret absent => Result None AND both counters unchanged. Clause(2): both present => lookups+1 AND verifications+1 (on EVERY both-present path). Clause(2a): recognised => (Result is not None)==secret_verifies AND Result==eff. Clause(2b): unrecognised => None. The full credential matrix and both counters are pinned exactly by directory_recognises/secret_verifies, leaving no unconstrained observable slack.

ATTACKS (all same-spec confirmed via `adversary same-spec`, byte-identical spec signature; verified with `bash scripts/nagini_verify.sh`):
- atk_1.py = prepatch bug (unconditional lookups+verifications increments before the absent-guard). same-spec=SAME. nagini_verify exit=1 (FAILS clause 1). PREPATCH REPRODUCED.
- atk_2.py = partial-domain: verifications incremented only on recognised branch. SAME. exit=1 (FAILS clause 2 on unrecognised path).
- atk_3.py = partial-domain: lookups incremented only on recognised branch. SAME. exit=1 (FAILS clause 2 on unrecognised path).
- atk_4.py = control-flow-effect: returns eff on unrecognised branch. SAME. exit=1 (FAILS clause 2b).
- atk_5.py = ungrounded-oracle echo: reordered counter increments + restructured recognised branch (behaviourally identical). SAME. exit=0 VERIFIES -> CANDIDATE.
- atk_6.py = ternary eff assignment + reordered/split guards (equivalent). SAME. exit=0 VERIFIES -> CANDIDATE.
- atk_7.py = split absent guards + explicit `recognised` bool var (equivalent). SAME. exit=0 VERIFIES -> CANDIDATE.
positive_control.py (== model.py impl) VERIFIES exit=0.

Commands used per attack:
  python -m swebench_unified.adversary same-spec nagini django__django-11451 <atk>
  bash scripts/nagini_verify.sh <atk>
  (and `adversary weakness nagini django__django-11451 <atk>` semantics = same-spec AND verify.)

CANDIDATE RESOLVE (MANDATORY): atk_5/atk_6/atk_7 each refine, via refinement.md's reverse operation map, to the SAME real Django control flow (kwargs fallback -> inserted absent-credential guard -> get_by_natural_key/except DoesNotExist:set_password -> check_password & user_can_authenticate). They differ only in UNOBSERVABLE internal ordering (which counter increments first / branch shape), which the spec does not constrain and which maps to no distinct real op. Hence each faithful refined patch is byte-identical to the gold guard insertion. Verified byte-identical to bundle patch.diff via diff. Materialized patch_atk_5.diff/patch_atk_6.diff/patch_atk_7.diff (identical) and RAN the official harness once (content-addressed by patch, so one run covers all three):
  run_resolve('django__django-11451', <patch>, run_id='sbu-eq-atk-1fbmlunv', timeout=1800, retries=1)
  RESULT: resolved=True completed=True note='resolved' flaky=False.
Every verifying wrong-impl's faithful patch RESOLVES => no verify-but-incorrect impl exhibited => spec is NOT too weak.

REFINEMENT.MD LEG AUDIT: 7 steps tagged R / R+I / I / R / R / A-consumed+I / A-consumed+R. No kind-3 (unexpressible-changed-op), no A-reference, no dead axioms. The CHANGED operation (early-return shortcut avoiding both expensive ops) is modeled DEEPLY via the lookups/verifications counters + control flow, NOT axiomatized. The two A-consumed axioms cover only UNCHANGED decision primitives: directory_recognises <-> get_by_natural_key (raises DoesNotExist iff no account; base_user.py:43) and secret_verifies <-> check_password AND user_can_authenticate (backends.py:49). Correspondence holds and is executably validated by axiom_check.py (drives real ModelBackend.authenticate against live in-memory auth DB, instrumented MD5 encode counter + CaptureQueriesContext, over the full matrix incl. both-tree detection).

VERDICT: SOUND. 7 attacks encoded and fully verified (4 correctly rejected incl. prepatch; 3 verifying candidates all resolve). Positive control verifies. No falsification found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack failed. Spec region is byte-identical (same-spec exit 0) and the model verifies (Nagini success, 12.3s). The modeled authenticate faithfully tracks the real ModelBackend.authenticate at base_commit + gold patch: (1) absent identifier(after fallback)/secret => None with both cost counters unchanged, matching the inserted guard `if username is None or password is None: return` (backends.py:42-43); (2) both-present => exactly one DB lookup and exactly one hasher run on EVERY path — recognised (check_password->encode once), recognised-wrong, not-permitted (code 3, check_password still runs), and unrecognised (set_password->encode once, timing defence #20760); (2a/2b) recognised returns the matched account iff secret_verifies (=check_password AND user_can_authenticate), else None; unrecognised => None. secret_verifies correctly bundles the recognised-path return decision only; its cost is modeled deeply via the verifications counter. No input where the spec disagrees with the real callee could be found. Independent machine evidence: G-CONF differential check drives the contract-stripped impl region (with @ContractOnly callees bound to the REAL repo get_by_natural_key / check_password+user_can_authenticate) against the real patched authenticate over 101,859 Requires-satisfying inputs (full credential cross-product including None/empty-secret/not-permitted + 100k fuzz, seed 11451), comparing result identity, per-call query count, and per-call hasher-run count — 0 disagreements. G-AX pass on both pre- and post-patch trees over the 14-case credential matrix. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage is judged relative to the PUBLIC problem_statement (not hints_text). For django__django-11451 the problem_statement itself already contains the verbatim gold fix as literal code: it shows the current ModelBackend.authenticate() and explicitly proposes 'My suggestion is to shortcut with: if username is None or password is None: return'. The gold patch is exactly those two inserted lines. So the entire gold edit is already public in code form.

Spec-view review:
- model.py encodes the behaviour MORE abstractly than the public statement (a directory lookup + a secret-verification primitive with two cost counters; clause (1): when either credential is absent after recovery, answer nothing AND neither expensive operation runs). This is a behavioural specification of exactly the effect the public problem_statement describes (the 'useless database query' and 'runs the password hasher needlessly'), stated as desired behaviour rather than as an edit. It reveals nothing about the gold edit beyond what the problem_statement already spells out.
- refinement.md and mapping.md are auditor derivation docs (not part of what a solver would see as the task spec in the same sense), and they DO quote the gold hunk verbatim — but that hunk is byte-for-byte identical to the fix already printed in the public problem_statement, so it discloses nothing beyond the public text. The counter-hoisting / axiom provenance discussion is modeling justification, not a disclosure of the edit location or content beyond the public statement.

No spec-view line leaks the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
