# P2 adversarial audit — django__django-16631

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
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -109,8 +107,6 @@
         return 0
     if ToSeq(session_token) == ToSeq(current_token):
         return 1
-    if matches_any(ToSeq(session_token), previous_tokens):
-        return 2
     return 0
     # impl-end
 
@@ -121,7 +117,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -140,7 +135,6 @@
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
         Assert(fallback_secrets.drop(i - 1)[0] == s)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -121,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -140,12 +137,11 @@
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
         Assert(fallback_secrets.drop(i - 1)[0] == s)
         Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
-        result = PSeq(token_for_secret(ToSeq(password), s)) + result
+        result = PSeq(token_for_secret(ToSeq(password), ToSeq(default_secret))) + result
         i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -107,10 +105,10 @@
     # impl-start
     if len(session_token) == 0:
         return 0
+    if matches_any(ToSeq(session_token), previous_tokens):
+        return 2
     if ToSeq(session_token) == ToSeq(current_token):
         return 1
-    if matches_any(ToSeq(session_token), previous_tokens):
-        return 2
     return 0
     # impl-end
 
@@ -121,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -140,7 +137,6 @@
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
         Assert(fallback_secrets.drop(i - 1)[0] == s)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -107,11 +105,7 @@
     # impl-start
     if len(session_token) == 0:
         return 0
-    if ToSeq(session_token) == ToSeq(current_token):
-        return 1
-    if matches_any(ToSeq(session_token), previous_tokens):
-        return 2
-    return 0
+    return 1
     # impl-end
 
 
@@ -121,7 +115,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -140,7 +133,6 @@
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
         Assert(fallback_secrets.drop(i - 1)[0] == s)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -121,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -133,18 +130,15 @@
     # post-conditions-end
     # impl-start
     result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
-    i = len(fallback_secrets)
+    i = len(fallback_secrets) - 1
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(password), 1 / 2))
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
-        Assert(fallback_secrets.drop(i - 1)[0] == s)
-        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
         result = PSeq(token_for_secret(ToSeq(password), s)) + result
         i = i - 1
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -121,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -133,19 +130,16 @@
     # post-conditions-end
     # impl-start
     result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
-    i = len(fallback_secrets)
-    while i > 0:
+    i = 0
+    while i < len(fallback_secrets):
         # invariants-start
         Invariant(Acc(list_pred(password), 1 / 2))
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
-        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
+        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.take(i)))
         # invariants-end
-        s = fallback_secrets[i - 1]
-        Assert(fallback_secrets.drop(i - 1)[0] == s)
-        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
-        result = PSeq(token_for_secret(ToSeq(password), s)) + result
-        i = i - 1
+        s = fallback_secrets[i]
+        result = result + PSeq(token_for_secret(ToSeq(password), s))
+        i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(session_token), 1 / 2))
     Requires(Acc(list_pred(current_token), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(session_token), 1 / 2))
@@ -108,9 +106,9 @@
     if len(session_token) == 0:
         return 0
     if ToSeq(session_token) == ToSeq(current_token):
+        return 2
+    if matches_any(ToSeq(session_token), previous_tokens):
         return 1
-    if matches_any(ToSeq(session_token), previous_tokens):
-        return 2
     return 0
     # impl-end
 
@@ -121,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(password), 1 / 2))
     Requires(Acc(list_pred(default_secret), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(password), 1 / 2))
@@ -140,7 +137,6 @@
         Invariant(Acc(list_pred(default_secret), 1 / 2))
         Invariant(0 <= i and i <= len(fallback_secrets))
         Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         s = fallback_secrets[i - 1]
         Assert(fallback_secrets.drop(i - 1)[0] == s)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16631.

Behaviour under specification (stated as the desired observable behaviour of a
session-authentication check, not as an edit):

A request carries a stored session authentication token. The server holds a
current verification token for the user (an HMAC of the user's password under
the active signing secret) and, during a secret-rotation window, a sequence of
previous verification tokens (the same HMAC under each previous signing secret).
The check decides, from the stored token alone, one of three outcomes:

  * outcome 1 -- ACCEPT-CURRENT: the stored token is present and equals the
    current verification token. The user stays authenticated and the stored
    session is left untouched.

  * outcome 2 -- ACCEPT-PREVIOUS: the stored token is present, does NOT equal
    the current verification token, but equals one of the previous verification
    tokens. The user stays authenticated.

  * outcome 0 -- REJECT: the stored token is absent, or present but matching
    neither the current nor any previous verification token. The session is
    discarded and the user is de-authenticated.

The current outcome takes priority over the previous outcomes: if the stored
token equals the current token the result is 1 even if it also coincides with a
previous token.

The per-secret verification token itself is a keyed hash of the password; for
any given password the token is a deterministic function of the signing secret
(`token_for_secret`, an axiomatised unchanged callee). The previous-token
sequence is exactly that token computed under each previous secret, in order.

Tokens are modelled as `List[int]` / `PSeq[int]` of code points (Nagini bans
`str` indexing). An empty token models an absent stored session value. The
sequence of previous tokens is `PSeq[PSeq[int]]`; secrets and passwords are
`PSeq[int]`. `matches_any` is the front-recursive membership predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def token_for_secret(password: PSeq[int], secret: PSeq[int]) -> PSeq[int]:
    """The per-secret verification token: a keyed hash of `password` under
    `secret`. Unchanged callee (the keyed-hash primitive). The only property
    the proof consumes is functional determinism -- equal (password, secret)
    pairs yield equal tokens -- which holds for any deterministic hash and is
    implied automatically by purity. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def matches_any(token: PSeq[int], candidates: PSeq[PSeq[int]]) -> bool:
    """True iff `token` equals some element of `candidates`. Front-recursive so
    a single unfold is available per loop step."""
    if len(candidates) == 0:
        return False
    return candidates[0] == token or matches_any(token, candidates.drop(1))


@Pure
def tokens_under(password: PSeq[int], secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The verification tokens for `password` under each secret in `secrets`,
    in order. Front-recursive fold mirroring the previous-token generator."""
    if len(secrets) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(token_for_secret(password, secrets[0])) + tokens_under(password, secrets.drop(1))
# pure-end


def session_outcome(session_token: List[int],
                    current_token: List[int],
                    previous_tokens: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(session_token), 1 / 2))
    Requires(Acc(list_pred(current_token), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(session_token), 1 / 2))
    Ensures(Acc(list_pred(current_token), 1 / 2))
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # ACCEPT-CURRENT: present stored token equal to the current token.
    Ensures((Result() == 1) ==
            (len(session_token) > 0
             and ToSeq(session_token) == ToSeq(current_token)))
    # ACCEPT-PREVIOUS: present stored token that does not match the current
    # token but does match one of the previous tokens.
    Ensures((Result() == 2) ==
            (len(session_token) > 0
             and ToSeq(session_token) != ToSeq(current_token)
             and matches_any(ToSeq(session_token), previous_tokens)))
    # REJECT: everything else (absent, or matching neither).
    Ensures((Result() == 0) ==
            (len(session_token) == 0
             or (ToSeq(session_token) != ToSeq(current_token)
                 and not matches_any(ToSeq(session_token), previous_tokens))))
    # post-conditions-end
    # impl-start
    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0
    # impl-end


def fallback_auth_hashes(password: List[int],
                         default_secret: List[int],
                         fallback_secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(password), 1 / 2))
    Requires(Acc(list_pred(default_secret), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(password), 1 / 2))
    Ensures(Acc(list_pred(default_secret), 1 / 2))
    # The produced sequence is exactly the verification token computed under
    # each PREVIOUS secret, in order -- each entry keyed by its own previous
    # secret, NOT by the active signing secret.
    Ensures(Result() == tokens_under(ToSeq(password), fallback_secrets))
    # post-conditions-end
    # impl-start
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong impls (all confirmed byte-identical spec via `same-spec`), each edited ONLY inside the impl-start/impl-end regions of model.py; axioms/@Pure/Requires/Ensures/Invariant left byte-identical. Ran `python -m swebench_unified.adversary weakness nagini django__django-16631 <atk>` on each (from project root, PYTHONPATH=src, SBU_BENCHMARK_DIR=benchmark-verified, python=python), concurrently in 3 batches of <=3 JVM+Z3 jobs. ALL 7 returned exit 2 (NOT-A-COUNTEREXAMPLE: verification failed) => NO candidate arose, so no faithful-patch materialization / run_resolve was required by protocol. Positive control (verbatim model.py impl) returned CANDIDATE (exit 0, verifies) as expected.

Why the spec is tight: both modeled functions have postconditions that FULLY PIN the return value for every input -- session_outcome via three exhaustive mutually-exclusive biconditionals on Result in {0,1,2}, fallback_auth_hashes via Result()==tokens_under(...). Combined with only 1/2 list_pred permission (no mutation possible), any impl deviating on any input is rejected.

Per-attack results (path :: weakness exit :: direct-verify failing obligation):
- atk_1 (partial-domain: prepatch, drops outcome-2 branch) :: exit 2 :: Postcondition (Result()==2)==(...matches_any...) might not hold (FAILED 13.2s). Reproduces the prepatch bug (model_prepatch.py).
- atk_2 (control-flow-effect: prepatch_2, keys token on default_secret not iterated secret) :: exit 2 :: Loop invariant result==tokens_under(...,drop(i)) not preserved (12.8s). Reproduces the second prepatch bug (model_prepatch_2.py).
- atk_3 (priority swap: matches_any checked before current-equality) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (14.7s).
- atk_4 (partial-domain/ungrounded: accept any present token, return 1) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (14.7s).
- atk_5 (boundary/off-by-one: start loop at len-1, skip a fallback secret) :: exit 2 :: Loop invariant 0<=i not on entry (13.6s); tokens_under postcond unsatisfiable when a secret is skipped.
- atk_6 (order-reversal: append at end instead of front) :: exit 2 :: Loop invariant result==tokens_under(...,take(i)) not preserved (16.2s).
- atk_7 (echo/label-swap: current-match->2, previous-match->1) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (13.3s).

Refinement.md audit: every leg is R / A-consumed / A-reference / I; section C correctly asserts no kind-3. The two genuinely-changed operations are modeled DIRECTLY (site A previous-token membership/upgrade via deep matches_any; site B per-previous-secret token sequence via deep tokens_under fold) -- not axiomatized. The only A-legs: (A-consumed) token_for_secret <-> salted_hmac(...).hexdigest(), weakest possible contract (no Ensures, purity-only determinism), validated on the real Django callee by axiom_check.py (determinism + secret-sensitivity, never an exact digest -> cannot over-claim); (A-reference) constant_time_compare == byte equality, validated constant_time_compare(a,b)==(a==b) on the real callee. Both A-legs' correspondence to the real callees holds; no ungrounded oracle admits the changed behavior. patch.diff is the gold patch verbatim (G-RESOLVE oracle). SOUND after >=5 attacks run and none broke the spec.

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
"""Twin-artifact model for django__django-16631.

Behaviour under specification (stated as the desired observable behaviour of a
session-authentication check, not as an edit):

A request carries a stored session authentication token. The server holds a
current verification token for the user (an HMAC of the user's password under
the active signing secret) and, during a secret-rotation window, a sequence of
previous verification tokens (the same HMAC under each previous signing secret).
The check decides, from the stored token alone, one of three outcomes:

  * outcome 1 -- ACCEPT-CURRENT: the stored token is present and equals the
    current verification token. The user stays authenticated and the stored
    session is left untouched.

  * outcome 2 -- ACCEPT-PREVIOUS: the stored token is present, does NOT equal
    the current verification token, but equals one of the previous verification
    tokens. The user stays authenticated.

  * outcome 0 -- REJECT: the stored token is absent, or present but matching
    neither the current nor any previous verification token. The session is
    discarded and the user is de-authenticated.

The current outcome takes priority over the previous outcomes: if the stored
token equals the current token the result is 1 even if it also coincides with a
previous token.

The per-secret verification token itself is a keyed hash of the password; for
any given password the token is a deterministic function of the signing secret
(`token_for_secret`, an axiomatised unchanged callee). The previous-token
sequence is exactly that token computed under each previous secret, in order.

Tokens are modelled as `List[int]` / `PSeq[int]` of code points (Nagini bans
`str` indexing). An empty token models an absent stored session value. The
sequence of previous tokens is `PSeq[PSeq[int]]`; secrets and passwords are
`PSeq[int]`. `matches_any` is the front-recursive membership predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def token_for_secret(password: PSeq[int], secret: PSeq[int]) -> PSeq[int]:
    """The per-secret verification token: a keyed hash of `password` under
    `secret`. Unchanged callee (the keyed-hash primitive). The only property
    the proof consumes is functional determinism -- equal (password, secret)
    pairs yield equal tokens -- which holds for any deterministic hash and is
    implied automatically by purity. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def matches_any(token: PSeq[int], candidates: PSeq[PSeq[int]]) -> bool:
    """True iff `token` equals some element of `candidates`. Front-recursive so
    a single unfold is available per loop step."""
    if len(candidates) == 0:
        return False
    return candidates[0] == token or matches_any(token, candidates.drop(1))


@Pure
def tokens_under(password: PSeq[int], secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The verification tokens for `password` under each secret in `secrets`,
    in order. Front-recursive fold mirroring the previous-token generator."""
    if len(secrets) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(token_for_secret(password, secrets[0])) + tokens_under(password, secrets.drop(1))
# pure-end


def session_outcome(session_token: List[int],
                    current_token: List[int],
                    previous_tokens: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(session_token), 1 / 2))
    Requires(Acc(list_pred(current_token), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(session_token), 1 / 2))
    Ensures(Acc(list_pred(current_token), 1 / 2))
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # ACCEPT-CURRENT: present stored token equal to the current token.
    Ensures((Result() == 1) ==
            (len(session_token) > 0
             and ToSeq(session_token) == ToSeq(current_token)))
    # ACCEPT-PREVIOUS: present stored token that does not match the current
    # token but does match one of the previous tokens.
    Ensures((Result() == 2) ==
            (len(session_token) > 0
             and ToSeq(session_token) != ToSeq(current_token)
             and matches_any(ToSeq(session_token), previous_tokens)))
    # REJECT: everything else (absent, or matching neither).
    Ensures((Result() == 0) ==
            (len(session_token) == 0
             or (ToSeq(session_token) != ToSeq(current_token)
                 and not matches_any(ToSeq(session_token), previous_tokens))))
    # post-conditions-end
    # impl-start
    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0
    # impl-end


def fallback_auth_hashes(password: List[int],
                         default_secret: List[int],
                         fallback_secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(password), 1 / 2))
    Requires(Acc(list_pred(default_secret), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(password), 1 / 2))
    Ensures(Acc(list_pred(default_secret), 1 / 2))
    # The produced sequence is exactly the verification token computed under
    # each PREVIOUS secret, in order -- each entry keyed by its own previous
    # secret, NOT by the active signing secret.
    Ensures(Result() == tokens_under(ToSeq(password), fallback_secrets))
    # post-conditions-end
    # impl-start
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong impls (all confirmed byte-identical spec via `same-spec`), each edited ONLY inside the impl-start/impl-end regions of model.py; axioms/@Pure/Requires/Ensures/Invariant left byte-identical. Ran `python -m swebench_unified.adversary weakness nagini django__django-16631 <atk>` on each (from project root, PYTHONPATH=src, SBU_BENCHMARK_DIR=benchmark-verified, python=python), concurrently in 3 batches of <=3 JVM+Z3 jobs. ALL 7 returned exit 2 (NOT-A-COUNTEREXAMPLE: verification failed) => NO candidate arose, so no faithful-patch materialization / run_resolve was required by protocol. Positive control (verbatim model.py impl) returned CANDIDATE (exit 0, verifies) as expected.

Why the spec is tight: both modeled functions have postconditions that FULLY PIN the return value for every input -- session_outcome via three exhaustive mutually-exclusive biconditionals on Result in {0,1,2}, fallback_auth_hashes via Result()==tokens_under(...). Combined with only 1/2 list_pred permission (no mutation possible), any impl deviating on any input is rejected.

Per-attack results (path :: weakness exit :: direct-verify failing obligation):
- atk_1 (partial-domain: prepatch, drops outcome-2 branch) :: exit 2 :: Postcondition (Result()==2)==(...matches_any...) might not hold (FAILED 13.2s). Reproduces the prepatch bug (model_prepatch.py).
- atk_2 (control-flow-effect: prepatch_2, keys token on default_secret not iterated secret) :: exit 2 :: Loop invariant result==tokens_under(...,drop(i)) not preserved (12.8s). Reproduces the second prepatch bug (model_prepatch_2.py).
- atk_3 (priority swap: matches_any checked before current-equality) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (14.7s).
- atk_4 (partial-domain/ungrounded: accept any present token, return 1) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (14.7s).
- atk_5 (boundary/off-by-one: start loop at len-1, skip a fallback secret) :: exit 2 :: Loop invariant 0<=i not on entry (13.6s); tokens_under postcond unsatisfiable when a secret is skipped.
- atk_6 (order-reversal: append at end instead of front) :: exit 2 :: Loop invariant result==tokens_under(...,take(i)) not preserved (16.2s).
- atk_7 (echo/label-swap: current-match->2, previous-match->1) :: exit 2 :: Postcondition (Result()==1)==(...) might not hold (13.3s).

Refinement.md audit: every leg is R / A-consumed / A-reference / I; section C correctly asserts no kind-3. The two genuinely-changed operations are modeled DIRECTLY (site A previous-token membership/upgrade via deep matches_any; site B per-previous-secret token sequence via deep tokens_under fold) -- not axiomatized. The only A-legs: (A-consumed) token_for_secret <-> salted_hmac(...).hexdigest(), weakest possible contract (no Ensures, purity-only determinism), validated on the real Django callee by axiom_check.py (determinism + secret-sensitivity, never an exact digest -> cannot over-claim); (A-reference) constant_time_compare == byte equality, validated constant_time_compare(a,b)==(a==b) on the real callee. Both A-legs' correspondence to the real callees holds; no ungrounded oracle admits the changed behavior. patch.diff is the gold patch verbatim (G-RESOLVE oracle). SOUND after >=5 attacks run and none broke the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of nagini django__django-16631. Spec region verified byte-identical to bundle (same-spec EXIT=0, 'SAME — attack shares the bundle's exact specification'); model verifies in Nagini (11.75s).

METHOD: independent reproduction, not trust of recorded verdicts. Re-created the gold-patched repo by applying the gold patch (from data/swe_bench_verified/test.jsonl) to a fresh copy of the base_commit (9b224579875e) worktree, then ran the bundle's conformance_check.py against the REAL patched modules via PYTHONPATH: G-CONF OK, 100,014 inputs (14 boundary + 100000 fuzz, seed 16631), ZERO disagreements. Additionally wrote my OWN adversarial differential harness with a DIFFERENT seed (987654321), unicode + non-hex stored tokens, fallback-secret lists up to length 5, and empty-string/absent corners: 30,000 inputs, ZERO divergence on both modeled functions.

SITE A (session_outcome vs post-patch get_user block, __init__.py:199-221): all four branches match. Empty/falsy session_hash -> real 'if not session_hash: verified=False' then fallback 'if session_hash and any(...)' short-circuits false -> flush -> reject; model len==0 -> 0. session_hash==current -> constant_time_compare True, user kept untouched -> outcome 1; model returns 1 with current-priority (checked before matches_any, matching gold priority). present & !=current & matches a fallback -> cycle_key + rewrite stored to current -> outcome 2; model matches_any -> 2. matches neither -> flush; model final return 0. The only structural corner (empty current_token making the model return 0 despite session==current) is unrealizable: get_session_auth_hash() always returns a 64-char sha256 hex digest, never empty.

SITE B (fallback_auth_hashes vs get_session_auth_fallback_hash/_get_session_auth_hash, base_user.py post-patch): model result == tokens_under(password, fallback_secrets) = per-previous-secret token sequence in order, exactly the gold generator's yields; the B3 fix (keying on the iterated secret s, not default_secret) is captured; the unused default_secret param produces no over-claim.

TRUST POINTS validated against REAL django.utils.crypto: token_for_secret has NO Ensures (weakest possible contract, only @Pure determinism — cannot over-claim); constant_time_compare modeled as PSeq equality (G-AX confirmed byte-equality); membership order-independent. G-AX/G-DIFF/G-GOLD/G-RESOLVE all pass.

No realizable input makes either modeled function disagree with the gold repo callee. The spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures/warnings; leakage.screen returned passed=True). Spec region verified byte-consistent (same-spec markers intact; impl-start/impl-end are the only differing region vs the twin). No relaxed_leakage flag and no RELAXED_LEAKAGE.md, so strict judgment applies.

Semantic assessment of the spec view (spec_view of model.py) vs the PUBLIC problem_statement (NOT hints):
- The public problem_statement is already very explicit: it names SECRET_KEY_FALLBACKS, states it 'is not used for sessions', and localizes the fix precisely -- 'AbstractBaseUser.get_session_auth_hash method does not call salted_hmac with a value for the secret keyword argument.' Thus the public text already discloses that sessions must consult fallback secrets and that the session-auth token must be re-keyed per fallback secret.
- The spec view states desired OBSERVABLE behavior (three outcomes: accept-current / accept-previous-via-fallback / reject; previous tokens = keyed hash under each previous secret in order). Specifying correct behavior is the purpose of a spec and is not leakage of the edit.
- No diff markers, no patched file paths, no reproduced gold-diff lines.
- Identifiers are abstract (session_outcome, fallback_auth_hashes, token_for_secret, matches_any, tokens_under); none echo gold symbols (get_session_auth_fallback_hash, _get_session_auth_hash, get_session_auth_hash).
- No bug/fix/pre-patch/post-patch narration; docstring frames content as behavior 'not as an edit'.
- The pointed postcondition comment on fallback_auth_hashes ('each entry keyed by its own previous secret, NOT by the active signing secret') restates a fact the problem_statement already makes public (the missing secret= argument keyed everything on SECRET_KEY). It adds no edit-localization beyond the public statement.

Conclusion: the spec view does not reveal the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
