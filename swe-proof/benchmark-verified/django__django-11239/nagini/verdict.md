# P2 adversarial audit — django__django-11239

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,7 @@
         env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
     if setting_sslcert() in conn_params:
         env[envvar_sslcert()] = conn_params[setting_sslcert()]
-    if setting_sslkey() in conn_params:
-        env[envvar_sslkey()] = conn_params[setting_sslkey()]
+    # ATTACK 1 (partial-domain): drop the sslkey publication entirely. The
+    # private-key setting never reaches the launched shell.
     return env
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,6 +157,9 @@
     if setting_sslcert() in conn_params:
         env[envvar_sslcert()] = conn_params[setting_sslcert()]
     if setting_sslkey() in conn_params:
-        env[envvar_sslkey()] = conn_params[setting_sslkey()]
+        # ATTACK 2 (boundary/value corruption): publish sslkey under its
+        # dedicated var but with a bogus value (its own token, not the supplied
+        # value). Presence is correct; verbatim value is violated.
+        env[envvar_sslkey()] = envvar_sslkey()
     return env
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -148,6 +148,9 @@
     # post-conditions-end
     # impl-start
     env = {}  # type: Dict[int, int]
+    # ATTACK 3 (spurious key): publish an extra environment variable (token 999)
+    # that is outside the five dedicated names. Violates the no-spurious clause.
+    env[999] = 7
     if setting_password() in conn_params:
         env[envvar_password()] = conn_params[setting_password()]
     if setting_sslmode() in conn_params:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -152,10 +152,13 @@
         env[envvar_password()] = conn_params[setting_password()]
     if setting_sslmode() in conn_params:
         env[envvar_sslmode()] = conn_params[setting_sslmode()]
+    # ATTACK 4 (name collision / swap): publish sslrootcert's value under the
+    # sslcert variable and vice versa. Each present setting reaches SOME var but
+    # the wrong one; biconditionals for these two vars are crossed.
     if setting_sslrootcert() in conn_params:
-        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
+        env[envvar_sslcert()] = conn_params[setting_sslrootcert()]
     if setting_sslcert() in conn_params:
-        env[envvar_sslcert()] = conn_params[setting_sslcert()]
+        env[envvar_sslrootcert()] = conn_params[setting_sslcert()]
     if setting_sslkey() in conn_params:
         env[envvar_sslkey()] = conn_params[setting_sslkey()]
     return env
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -148,8 +148,10 @@
     # post-conditions-end
     # impl-start
     env = {}  # type: Dict[int, int]
-    if setting_password() in conn_params:
-        env[envvar_password()] = conn_params[setting_password()]
+    # ATTACK 5 (control-flow-effect / inverted guard): publish PGPASSWORD when
+    # the password is ABSENT (inverted condition), using a fixed value token.
+    if setting_password() not in conn_params:
+        env[envvar_password()] = 0
     if setting_sslmode() in conn_params:
         env[envvar_sslmode()] = conn_params[setting_sslmode()]
     if setting_sslrootcert() in conn_params:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,8 +150,14 @@
     env = {}  # type: Dict[int, int]
     if setting_password() in conn_params:
         env[envvar_password()] = conn_params[setting_password()]
+    # ATTACK 6 (cross-setting value): publish PGSSLMODE (correct presence) but
+    # carry the PASSWORD's value when both are supplied — wrong value, correct
+    # var. Falls back to the real value otherwise so presence stays exact.
     if setting_sslmode() in conn_params:
-        env[envvar_sslmode()] = conn_params[setting_sslmode()]
+        if setting_password() in conn_params:
+            env[envvar_sslmode()] = conn_params[setting_password()]
+        else:
+            env[envvar_sslmode()] = conn_params[setting_sslmode()]
     if setting_sslrootcert() in conn_params:
         env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
     if setting_sslcert() in conn_params:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,7 +156,10 @@
         env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
     if setting_sslcert() in conn_params:
         env[envvar_sslcert()] = conn_params[setting_sslcert()]
-    if setting_sslkey() in conn_params:
+    # ATTACK 7 (conditional partial-domain): publish PGSSLKEY only when the
+    # password is ALSO supplied. A TLS-only connection (no password) silently
+    # drops the private key — the exact real-world regression this change fixes.
+    if setting_sslkey() in conn_params and setting_password() in conn_params:
         env[envvar_sslkey()] = conn_params[setting_sslkey()]
     return env
     # impl-end
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -147,16 +147,10 @@
                 or e == envvar_sslkey()))))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: only the password setting is published; the four
+    # mutual-TLS settings are never written to the launched shell's environment.
     env = {}  # type: Dict[int, int]
     if setting_password() in conn_params:
         env[envvar_password()] = conn_params[setting_password()]
-    if setting_sslmode() in conn_params:
-        env[envvar_sslmode()] = conn_params[setting_sslmode()]
-    if setting_sslrootcert() in conn_params:
-        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
-    if setting_sslcert() in conn_params:
-        env[envvar_sslcert()] = conn_params[setting_sslcert()]
-    if setting_sslkey() in conn_params:
-        env[envvar_sslkey()] = conn_params[setting_sslkey()]
     return env
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11239.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client launches an external interactive shell and must pass the
  connection's credential and transport-security settings to that shell through
  its process environment. The settings recognised are the connection password
  and the four mutual-TLS settings used to authenticate the connection with
  client certificates: the security mode, the trusted root certificate, the
  client certificate, and the client private key.

  For each recognised setting, when the connection supplies a non-empty value,
  that value is published into the launched shell's environment under the
  dedicated environment-variable name that shell reads for that setting; when
  the connection does not supply the setting (or supplies an empty value), the
  corresponding environment variable is left unset. The published value is the
  supplied value verbatim, and no environment variable is published for any
  setting the connection did not supply.

  The consequence that matters: a connection configured for mutual TLS -- which
  supplies the transport-security settings in addition to (or instead of) a
  password -- has every one of those settings reach the launched shell, not
  only the password. Each setting maps to its own distinct environment
  variable, so settings never collide.

Modelling choices (Nagini fragment):
  * The connection settings are a ``Dict[int, int]`` from a setting-name token
    to its value token; the published environment is likewise a
    ``Dict[int, int]`` from an environment-variable-name token to its value
    token. Only membership, per-key value, and which names are present are
    observed, so integer identity is the faithful carrier (mapping.md §2).
  * Presence of a setting key in the input mapping models a supplied non-empty
    value; absence models an unsupplied or empty value (both leave the variable
    unset). The five setting tokens and their five distinct environment-variable
    tokens are module-level constants (mapping.md §1).

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the conditional per-setting publication is spelled out in the impl
region); there is no axiomatised callee. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the connection-setting publication is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def setting_password() -> int:
    return 0


@Pure
def setting_sslmode() -> int:
    return 1


@Pure
def setting_sslrootcert() -> int:
    return 2


@Pure
def setting_sslcert() -> int:
    return 3


@Pure
def setting_sslkey() -> int:
    return 4


@Pure
def envvar_password() -> int:
    return 100


@Pure
def envvar_sslmode() -> int:
    return 101


@Pure
def envvar_sslrootcert() -> int:
    return 102


@Pure
def envvar_sslcert() -> int:
    return 103


@Pure
def envvar_sslkey() -> int:
    return 104


# pure-end


def build_pg_env(conn_params: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(conn_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(conn_params), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # For each recognised setting, its dedicated environment variable is present
    # in the published environment exactly when the connection supplies that
    # setting, and then it carries the supplied value verbatim. These five
    # biconditionals are the clause the mutual-TLS configuration depends on:
    # each of the four TLS settings (and the password) reaches the launched
    # shell when -- and only when -- supplied, under its own distinct name.
    Ensures((envvar_password() in Result())
            == (setting_password() in conn_params))
    Ensures(Implies(setting_password() in conn_params,
                    Result()[envvar_password()] == conn_params[setting_password()]))
    Ensures((envvar_sslmode() in Result())
            == (setting_sslmode() in conn_params))
    Ensures(Implies(setting_sslmode() in conn_params,
                    Result()[envvar_sslmode()] == conn_params[setting_sslmode()]))
    Ensures((envvar_sslrootcert() in Result())
            == (setting_sslrootcert() in conn_params))
    Ensures(Implies(setting_sslrootcert() in conn_params,
                    Result()[envvar_sslrootcert()] == conn_params[setting_sslrootcert()]))
    Ensures((envvar_sslcert() in Result())
            == (setting_sslcert() in conn_params))
    Ensures(Implies(setting_sslcert() in conn_params,
                    Result()[envvar_sslcert()] == conn_params[setting_sslcert()]))
    Ensures((envvar_sslkey() in Result())
            == (setting_sslkey() in conn_params))
    Ensures(Implies(setting_sslkey() in conn_params,
                    Result()[envvar_sslkey()] == conn_params[setting_sslkey()]))
    # No spurious variables: every published environment variable is one of the
    # five dedicated names above (the result holds no key outside this set).
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == envvar_password() or e == envvar_sslmode()
                or e == envvar_sslrootcert() or e == envvar_sslcert()
                or e == envvar_sslkey()))))
    # post-conditions-end
    # impl-start
    env = {}  # type: Dict[int, int]
    if setting_password() in conn_params:
        env[envvar_password()] = conn_params[setting_password()]
    if setting_sslmode() in conn_params:
        env[envvar_sslmode()] = conn_params[setting_sslmode()]
    if setting_sslrootcert() in conn_params:
        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
    if setting_sslcert() in conn_params:
        env[envvar_sslcert()] = conn_params[setting_sslcert()]
    if setting_sslkey() in conn_params:
        env[envvar_sslkey()] = conn_params[setting_sslkey()]
    return env
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: build_pg_env's postcondition fully determines Result() as a function of conn_params. For each of the 5 settings it pins (a) presence via a biconditional `(envvar_X() in Result()) == (setting_X() in conn_params)`, (b) verbatim value via `Implies(setting_X() in conn_params, Result()[envvar_X()] == conn_params[setting_X()])`, and (c) a no-spurious Forall clause forbidding any key outside the 5 dedicated env-var tokens. This leaves no wiggle room for a wrong impl to verify.

PROTOCOL: All attacks edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); same-spec confirmed SAME for all 8 attacks + positive_control.

### ATTACK DESIGN (>=6 distinct classes, all A-leg / model-correspondence focused):
- atk_1 partial-domain: drops sslkey publication -> EXIT=2 (does not verify).
- atk_2 boundary/value-corruption: publishes PGSSLKEY present but with bogus value (its own token) -> EXIT=2.
- atk_3 spurious-key/ungrounded: publishes extra env var token 999 outside the 5 dedicated names (violates no-spurious Forall) -> EXIT=2.
- atk_4 name-collision/swap: sslrootcert value under PGSSLCERT and vice-versa (crossed biconditionals) -> EXIT=2.
- atk_5 control-flow-effect/inverted-guard: publishes PGPASSWORD when password ABSENT -> EXIT=2.
- atk_6 cross-setting-value: PGSSLMODE present-correct but carries password's value when both supplied -> EXIT=2.
- atk_7 conditional-partial-domain: publishes PGSSLKEY only when password also present (TLS-only conn drops key) -> EXIT=2.
- atk_prepatch: bundle's model_prepatch.py (only PGPASSWORD published) -> EXIT=2, reproduces the prepatch bug (fails the first SSL biconditional, G-DIFF). prepatch_reproduced=true.

RESULT: 0 CANDIDATEs. Every same-spec wrong impl was rejected by the verifier (all EXIT=2 NOT-A-COUNTEREXAMPLE / does-not-verify), so no verifying-but-wrong impl exists to materialize a patch for -- step-2 resolve runs are vacuous (correctly, not skipped). positive_control (verbatim model.py) VERIFIED in 22.5s, confirming the harness is live and the spec is satisfiable by the correct impl. patches={} because no attack verified.

REFINEMENT AUDIT (refinement.md): legs A1-A7 are R (Dict[int,int] token abstraction, .get(k,'')+`if value:` <-> key-token presence, str() identity) or R+I (conditional writes identical). ONE A-reference: the whole PG* publication validated == real DatabaseClient.runshell_db by axiom_check.py/G-AX (boundary + 5000 fuzz, seed 11239, subprocess.run intercepted as the repo's own test does). NO consumed axioms: `grep -c ContractOnly model.py` = 0 and axioms region has 0 non-comment chars. No kind-3 legs. A-reference correspondence holds: axiom_check.py's SETTING_TO_ENVVAR (password->PGPASSWORD, sslmode->PGSSLMODE, sslrootcert->PGSSLROOTCERT, sslcert->PGSSLCERT, sslkey->PGSSLKEY) matches mapping.md tokens 0-4/100-104 and the deep model's per-setting present-iff-nonempty-verbatim contract.

VERDICT: SOUND. >=5 (8) attacks run, none broke the spec; verify(model) here does entail correctness for every wrong impl tried, and the one trust point (refinement fidelity + A-reference) is intact.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11239.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client launches an external interactive shell and must pass the
  connection's credential and transport-security settings to that shell through
  its process environment. The settings recognised are the connection password
  and the four mutual-TLS settings used to authenticate the connection with
  client certificates: the security mode, the trusted root certificate, the
  client certificate, and the client private key.

  For each recognised setting, when the connection supplies a non-empty value,
  that value is published into the launched shell's environment under the
  dedicated environment-variable name that shell reads for that setting; when
  the connection does not supply the setting (or supplies an empty value), the
  corresponding environment variable is left unset. The published value is the
  supplied value verbatim, and no environment variable is published for any
  setting the connection did not supply.

  The consequence that matters: a connection configured for mutual TLS -- which
  supplies the transport-security settings in addition to (or instead of) a
  password -- has every one of those settings reach the launched shell, not
  only the password. Each setting maps to its own distinct environment
  variable, so settings never collide.

Modelling choices (Nagini fragment):
  * The connection settings are a ``Dict[int, int]`` from a setting-name token
    to its value token; the published environment is likewise a
    ``Dict[int, int]`` from an environment-variable-name token to its value
    token. Only membership, per-key value, and which names are present are
    observed, so integer identity is the faithful carrier (mapping.md §2).
  * Presence of a setting key in the input mapping models a supplied non-empty
    value; absence models an unsupplied or empty value (both leave the variable
    unset). The five setting tokens and their five distinct environment-variable
    tokens are module-level constants (mapping.md §1).

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the conditional per-setting publication is spelled out in the impl
region); there is no axiomatised callee. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the connection-setting publication is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def setting_password() -> int:
    return 0


@Pure
def setting_sslmode() -> int:
    return 1


@Pure
def setting_sslrootcert() -> int:
    return 2


@Pure
def setting_sslcert() -> int:
    return 3


@Pure
def setting_sslkey() -> int:
    return 4


@Pure
def envvar_password() -> int:
    return 100


@Pure
def envvar_sslmode() -> int:
    return 101


@Pure
def envvar_sslrootcert() -> int:
    return 102


@Pure
def envvar_sslcert() -> int:
    return 103


@Pure
def envvar_sslkey() -> int:
    return 104


# pure-end


def build_pg_env(conn_params: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(conn_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(conn_params), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # For each recognised setting, its dedicated environment variable is present
    # in the published environment exactly when the connection supplies that
    # setting, and then it carries the supplied value verbatim. These five
    # biconditionals are the clause the mutual-TLS configuration depends on:
    # each of the four TLS settings (and the password) reaches the launched
    # shell when -- and only when -- supplied, under its own distinct name.
    Ensures((envvar_password() in Result())
            == (setting_password() in conn_params))
    Ensures(Implies(setting_password() in conn_params,
                    Result()[envvar_password()] == conn_params[setting_password()]))
    Ensures((envvar_sslmode() in Result())
            == (setting_sslmode() in conn_params))
    Ensures(Implies(setting_sslmode() in conn_params,
                    Result()[envvar_sslmode()] == conn_params[setting_sslmode()]))
    Ensures((envvar_sslrootcert() in Result())
            == (setting_sslrootcert() in conn_params))
    Ensures(Implies(setting_sslrootcert() in conn_params,
                    Result()[envvar_sslrootcert()] == conn_params[setting_sslrootcert()]))
    Ensures((envvar_sslcert() in Result())
            == (setting_sslcert() in conn_params))
    Ensures(Implies(setting_sslcert() in conn_params,
                    Result()[envvar_sslcert()] == conn_params[setting_sslcert()]))
    Ensures((envvar_sslkey() in Result())
            == (setting_sslkey() in conn_params))
    Ensures(Implies(setting_sslkey() in conn_params,
                    Result()[envvar_sslkey()] == conn_params[setting_sslkey()]))
    # No spurious variables: every published environment variable is one of the
    # five dedicated names above (the result holds no key outside this set).
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == envvar_password() or e == envvar_sslmode()
                or e == envvar_sslrootcert() or e == envvar_sslcert()
                or e == envvar_sslkey()))))
    # post-conditions-end
    # impl-start
    env = {}  # type: Dict[int, int]
    if setting_password() in conn_params:
        env[envvar_password()] = conn_params[setting_password()]
    if setting_sslmode() in conn_params:
        env[envvar_sslmode()] = conn_params[setting_sslmode()]
    if setting_sslrootcert() in conn_params:
        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
    if setting_sslcert() in conn_params:
        env[envvar_sslcert()] = conn_params[setting_sslcert()]
    if setting_sslkey() in conn_params:
        env[envvar_sslkey()] = conn_params[setting_sslkey()]
    return env
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC ANALYSIS: build_pg_env's postcondition fully determines Result() as a function of conn_params. For each of the 5 settings it pins (a) presence via a biconditional `(envvar_X() in Result()) == (setting_X() in conn_params)`, (b) verbatim value via `Implies(setting_X() in conn_params, Result()[envvar_X()] == conn_params[setting_X()])`, and (c) a no-spurious Forall clause forbidding any key outside the 5 dedicated env-var tokens. This leaves no wiggle room for a wrong impl to verify.

PROTOCOL: All attacks edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); same-spec confirmed SAME for all 8 attacks + positive_control.

### ATTACK DESIGN (>=6 distinct classes, all A-leg / model-correspondence focused):
- atk_1 partial-domain: drops sslkey publication -> EXIT=2 (does not verify).
- atk_2 boundary/value-corruption: publishes PGSSLKEY present but with bogus value (its own token) -> EXIT=2.
- atk_3 spurious-key/ungrounded: publishes extra env var token 999 outside the 5 dedicated names (violates no-spurious Forall) -> EXIT=2.
- atk_4 name-collision/swap: sslrootcert value under PGSSLCERT and vice-versa (crossed biconditionals) -> EXIT=2.
- atk_5 control-flow-effect/inverted-guard: publishes PGPASSWORD when password ABSENT -> EXIT=2.
- atk_6 cross-setting-value: PGSSLMODE present-correct but carries password's value when both supplied -> EXIT=2.
- atk_7 conditional-partial-domain: publishes PGSSLKEY only when password also present (TLS-only conn drops key) -> EXIT=2.
- atk_prepatch: bundle's model_prepatch.py (only PGPASSWORD published) -> EXIT=2, reproduces the prepatch bug (fails the first SSL biconditional, G-DIFF). prepatch_reproduced=true.

RESULT: 0 CANDIDATEs. Every same-spec wrong impl was rejected by the verifier (all EXIT=2 NOT-A-COUNTEREXAMPLE / does-not-verify), so no verifying-but-wrong impl exists to materialize a patch for -- step-2 resolve runs are vacuous (correctly, not skipped). positive_control (verbatim model.py) VERIFIED in 22.5s, confirming the harness is live and the spec is satisfiable by the correct impl. patches={} because no attack verified.

REFINEMENT AUDIT (refinement.md): legs A1-A7 are R (Dict[int,int] token abstraction, .get(k,'')+`if value:` <-> key-token presence, str() identity) or R+I (conditional writes identical). ONE A-reference: the whole PG* publication validated == real DatabaseClient.runshell_db by axiom_check.py/G-AX (boundary + 5000 fuzz, seed 11239, subprocess.run intercepted as the repo's own test does). NO consumed axioms: `grep -c ContractOnly model.py` = 0 and axioms region has 0 non-comment chars. No kind-3 legs. A-reference correspondence holds: axiom_check.py's SETTING_TO_ENVVAR (password->PGPASSWORD, sslmode->PGSSLMODE, sslrootcert->PGSSLROOTCERT, sslcert->PGSSLCERT, sslkey->PGSSLKEY) matches mapping.md tokens 0-4/100-104 and the deep model's per-setting present-iff-nonempty-verbatim contract.

VERDICT: SOUND. >=5 (8) attacks run, none broke the spec; verify(model) here does entail correctness for every wrong impl tried, and the one trust point (refinement fidelity + A-reference) is intact.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) attack on django__django-11239 nagini bundle. The spec models the PG* environment publication of DatabaseClient.runshell_db: for each of the five recognised settings (password/sslmode/sslrootcert/sslcert/sslkey), the dedicated PG* variable (PGPASSWORD/PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY) is present with the value verbatim iff the setting is supplied non-empty, and no variable outside the five is published.

Verification performed (independent, not trusting recorded gates):
(1) Modeling boundary matches the F2P observation exactly: model captures {k: env[k] for k in env if k.startswith('PG')}, identical to tests/dbshell/test_postgresql.py::_run_it. Inherited non-PG os.environ entries are correctly outside the model; pre-existing PG* vars are stripped up front. Type abstraction (str tokens as ints, .get(k,'')+`if value:` == token presence, str() identity on strings) is sound.
 Ran the shadow impl (model.py impl region, contracts stripped, from conformance_check.py) against the REAL patched repo at base_commit d87bd29c + gold patch over the full 100,015-input battery (15 boundary + 100000 fuzz, seed 11239): 0 disagreements — reproduces the recorded G-AX/G-CONF pass.
(3) Adversarial edge probes beyond the fuzzer: values '0', ' ' (whitespace), '\n', 'False', non-ASCII 'café'/'clé', explicit empty-string skips, and all-five-supplied — every case matched the real callee. Non-empty-supplied<->present-verbatim and absent/empty<->unset both hold; distinct env-var names never collide; no spurious variables published.

No diverging input found: the modeled build_pg_env agrees with the real runshell_db PG* publication on all tested inputs including boundaries. The spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage/gold-reconstruction check for django__django-11239 (nagini). Spec view extracted with swebench_unified.markers.spec_view (impl region correctly elided) and the mechanical screen (leakage.screen over the spec view vs gold patch + problem_statement) returns passed=True, hard_failures=[].

Gold edit: publish the four TLS settings (sslmode/sslrootcert/sslcert/sslkey) into the subprocess environment under the libpq names PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY, alongside pre-existing PGPASSWORD (django/db/backends/postgresql/client.py runshell_db).

Public problem_statement baseline (NOT hints_text) is already maximally explicit: it names all four TLS settings VERBATIM in a DATABASES OPTIONS block ('sslmode','sslrootcert','sslcert','sslkey'), states the target ('the dbshell command does not support the client cert params'), and prescribes the fix ('add in support for the other ssl parameters required here').

What the spec view (docstring + @Pure token defs + build_pg_env pre/postconditions) reveals beyond problem_statement: nothing. (1) All setting names it references (password + four TLS names) are already in problem_statement. (2) It uses OPAQUE integer tokens: settings 0..4, env-vars 100..104 — the discriminating gold content (which concrete PG* env-var name each setting maps to) is NOT exposed in the spec view. (3) The concrete env-var names PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY and the file/symbol target (postgresql/client.py, runshell_db) appear ONLY in refinement.md and mapping.md — reviewer refinement docs outside the spec view — and even there are standard libpq names trivially derivable from the setting names already in problem_statement.

The five biconditionals + verbatim-value + no-spurious-keys postconditions merely formalize the already-explicit requirement and do not narrow the solution space beyond problem_statement. No consumed axiom, no hints leakage. No single spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
