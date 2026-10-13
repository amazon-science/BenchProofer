# P2 adversarial audit — django__django-14315

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -154,7 +154,8 @@
     if env is None:
         return None
     if len(env) == 0:
-        return None
+        empty = {}  # type: Dict[int, int]
+        return empty
     merged = env_merge(base, env)
     return merged
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,8 +107,6 @@
     Ensures(Implies(len(env) > 0, Result() is env))
     # post-conditions-end
     # impl-start
-    if len(env) == 0:
-        return None
     return env
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,6 +155,5 @@
         return None
     if len(env) == 0:
         return None
-    merged = env_merge(base, env)
-    return merged
+    return env
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,6 +155,6 @@
         return None
     if len(env) == 0:
         return None
-    merged = env_merge(base, env)
+    merged = env_merge(env, base)
     return merged
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,8 @@
     # impl-start
     if len(env) == 0:
         return None
-    return env
+    copy = dict(env)  # type: Dict[int, int]
+    return copy
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -154,7 +154,7 @@
     if env is None:
         return None
     if len(env) == 0:
-        return None
+        return base
     merged = env_merge(base, env)
     return merged
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,8 +153,6 @@
     # impl-start
     if env is None:
         return None
-    if len(env) == 0:
-        return None
     merged = env_merge(base, env)
     return merged
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,9 +107,7 @@
     Ensures(Implies(len(env) > 0, Result() is env))
     # post-conditions-end
     # impl-start
-    if len(env) == 0:
-        return None
-    return env
+    return None
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client builds a process environment mapping for the external
  shell it launches. Two related observations are pinned.

  (1) The environment a backend reports for a command. The mapping is built
      from the connection settings; when no environment variable is required
      the built mapping is empty. The reported value normalises an empty
      mapping to ``None``: an empty mapping and ``None`` are indistinguishable
      to the caller, while a non-empty mapping is reported verbatim.

  (2) The effective environment handed to the launched subprocess. Given the
      mapping reported for the command (which may be ``None`` or empty) and the
      current process environment ``os.environ``, the effective environment is
      ``None`` whenever the command mapping is ``None`` or empty -- so the
      subprocess inherits ``os.environ`` rather than receiving an empty
      environment. When the command mapping is non-empty the effective
      environment is the merge of ``os.environ`` with the command mapping, the
      command mapping's entries taking precedence.

  The consequence that matters: an empty command mapping must yield ``None``
  (the subprocess then inherits ``os.environ``), never an empty mapping (which
  would launch the subprocess with no inherited variables at all).

Modelling choices (Nagini fragment):
  * An environment mapping is a ``Dict[int, int]`` from variable-name token to
    value token; only membership, per-key value, and emptiness are observed,
    so integer identity is the faithful carrier (mapping.md §2).
  * "absent environment" (the ``None`` the subprocess inherits ``os.environ``
    for) is carried by an ``Optional[Dict[int, int]]`` whose ``None`` case is
    the distinguished value.
  * The merge of two mappings (an unchanged standard mapping-unpacking the
    code invokes) is the single callee ``env_merge``; its standard semantics
    are validated against real Python out-of-band (axiom_check.py, G-AX).

Building the environment for the launched subprocess is a bounded,
straight-line computation: each operation MUST terminate and deliver its
value (a total-correctness obligation, carried as MustTerminate in the
preconditions). Nagini verifies partial correctness by default, so without
the obligation an implementation that diverges would satisfy every value
postcondition only vacuously and would hang the shell launch forever.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def env_merge(base: Dict[int, int], overlay: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**base, **overlay}`` (an unchanged callee the
    code invokes): a fresh non-empty mapping holding every key of either input,
    with ``overlay``'s value winning on a shared key. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(Acc(dict_pred(overlay), 1 / 2))
    # The real mapping-unpacking merge is a single bounded primitive step; the
    # strictly smaller measure (1 < 2) lets a contracted caller holding
    # MustTerminate(2) invoke it without leaking its own obligation.
    Requires(MustTerminate(1))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(overlay), 1 / 2))
    Ensures(len(base) == Old(len(base)))
    Ensures(len(overlay) == Old(len(overlay)))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every key of overlay is present with overlay's value (overlay wins).
    Ensures(Forall(int, lambda k: (Implies(k in overlay,
                                            (k in Result()) and Result()[k] == overlay[k]),
                                    [[k in overlay], [k in Result()]])))
    # Every key of base that overlay does not override keeps base's value.
    Ensures(Forall(int, lambda k: (Implies((k in base) and not (k in overlay),
                                            (k in Result()) and Result()[k] == base[k]),
                                    [[k in base], [k in Result()]])))
    # No spurious keys: the merge holds only keys of one of the inputs.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in base) or (k in overlay)),
                                    [[k in Result()]])))
# axioms-end


# pure-start
# No pure helpers: the normalisation/merge selection is the behaviour under
# specification and is spelled out in the impl regions; the unchanged mapping
# merge it composes is the env_merge callee (axioms region).
# pure-end


def normalized_environment(env: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(env), 1 / 2))
    # TERMINATION: reporting the command environment is bounded straight-line
    # work that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body would satisfy the value
    # postconditions only vacuously yet never deliver the reported mapping.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(env), 1 / 2))
    # An empty mapping is normalised to None ...
    Ensures(Implies(len(env) == 0, Result() is None))
    # ... and a non-empty mapping is reported verbatim (the same mapping).
    Ensures(Implies(len(env) > 0, Result() is env))
    # post-conditions-end
    # impl-start
    if len(env) == 0:
        return None
    return env
    # impl-end


def effective_environment(env: Optional[Dict[int, int]],
                          base: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Requires(Acc(dict_pred(base), 1 / 2))
    # TERMINATION: computing the effective environment for the subprocess is
    # bounded straight-line work (a None/emptiness decision plus at most one
    # bounded merge) that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body — e.g. hanging instead of
    # handing the subprocess its environment — would satisfy the value
    # postconditions only vacuously and the shell would never be launched.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Implies(Result() is not None, Acc(dict_pred(Result()))))
    # None (inherit os.environ) exactly when the command mapping is None/empty.
    Ensures(Implies(env is None, Result() is None))
    Ensures(Implies(env is not None and len(env) == 0, Result() is None))
    Ensures(Implies(env is not None and len(env) > 0, Result() is not None))
    # When non-empty, the result is the merge: the command mapping's entries
    # win, and the process environment's other entries are carried through.
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in env,
                                       (k in Result()) and Result()[k] == env[k]),
                               [[k in env], [k in Result()]]))))
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies((k in base) and not (k in env),
                                       (k in Result()) and Result()[k] == base[k]),
                               [[k in base], [k in Result()]]))))
    # No spurious keys: the effective environment holds only keys of the
    # command mapping or of the process environment (the merge adds nothing).
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in Result(), (k in env) or (k in base)),
                               [[k in Result()]]))))
    # post-conditions-end
    # impl-start
    if env is None:
        return None
    if len(env) == 0:
        return None
    merged = env_merge(base, env)
    return merged
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-14315/nagini. FROZEN spec: two modeled functions (normalized_environment, effective_environment) + env_merge A-consumed axiom, all contract/axiom/@Pure regions left byte-identical; only impl regions edited per attack.

ENV: adversary run with python,, cwd=.

Positive control = verbatim model.py => weakness CANDIDATE, verifies (25.4s), exit 0. Confirms tooling + verifier live.

8 distinct same-spec wrong impls (same-spec confirmed on a representative, exit 0 SAME):
- atk_1: prepatch bug site1 — effective_environment returns empty dict {} on empty env instead of None. cmd: `python -m swebench_unified.adversary weakness nagini django__django-14315 atk_1.py`. Result: NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (violates Implies(env not None and len==0, Result() is None)). [prepatch reproduced]
- atk_2: prepatch bug site2 — normalized_environment returns env on empty (no None normalisation). Result: exit 2, rejected (violates Implies(len==0, Result() is None)). [prepatch reproduced]
- atk_3: control-flow — effective_environment returns env instead of the base merge on nonempty. Result: exit 2, rejected (violates base-carry / merge postconditions).
- atk_4: ungrounded-oracle/arg-swap — merge computed as env_merge(env, base) (base wins) instead of env_merge(base, env) (env wins). Result: exit 2, rejected — proves the A-consumed axiom's overlay-wins directionality is load-bearing, not vacuous.
- atk_5: boundary/identity — normalized_environment returns a fresh dict(env) copy (same content, different object) on nonempty. Result: exit 2, rejected (violates Result() is env object-identity ensure — behaviourally equivalent but spec pins identity, faithful to `dict or None` returning the same object).
- atk_6: boundary — effective_environment returns base (non-None) on empty env. Result: exit 2, rejected (violates Result() is None on empty).
- atk_7: control-flow-effect/partial-domain — effective_environment drops the empty short-circuit, always merges when not None. Result: exit 2, rejected (empty env yields non-None merge, violates Result() is None on empty).
- atk_8: ungrounded-oracle echo — normalized_environment returns None always. Result: exit 2, rejected (violates Implies(len>0, Result() is env)).

All 8 attacks were REJECTED (none verified). No verifying wrong impl (no CANDIDATE) exists, so NO faithful refined patch needed a run_resolve (patches={}). The verify=>correct implication is not falsified.

A-LEG / correspondence audit:
- G-AX: ran bundle axiom_check.py with the lean env => exit 0: env_merge axiom (A-consumed) sound on 7 boundary + 20000 fuzz pairs; normalized_environment / effective_environment deep models (A-reference) == real Python `(env or None)` and `{**base,**env} if env else None` on boundary + 20000 fuzz inputs, incl. the F2P None/{}->None case.
- refinement.md audit: every leg is R / A-consumed (B4 merge, B5 merge postconditions) / A-reference (the two changed empty->None selections modeled deeply and validated == real Python) / I. NO kind-3 (unexpressible-changed-op) step. The single consumed axiom (env_merge) covers only the UNCHANGED mapping merge the new code invokes — never the operation under change; its Ensures is consumed by B4/B5 (no dead axiom). atk_4 confirms the axiom directionality is live. mapping.md bindings to base_commit 187118203197801c6cb72dc8b06b714b23b6dd3d check out (base<->os.environ, env<->settings_to_cmd_args_env return, env_merge<->base/client.py:25 unchanged).
- Gold patch.diff is two one-line hunks matching the two modeled selections exactly.

VERDICT: SOUND. >=5 distinct same-spec attacks (8 run) plus prepatch bugs all rejected; positive control verifies; G-AX passes; refinement legs all R/A/I with sound A-leg correspondence. No verify-but-not-resolve counterexample found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

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

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client builds a process environment mapping for the external
  shell it launches. Two related observations are pinned.

  (1) The environment a backend reports for a command. The mapping is built
      from the connection settings; when no environment variable is required
      the built mapping is empty. The reported value normalises an empty
      mapping to ``None``: an empty mapping and ``None`` are indistinguishable
      to the caller, while a non-empty mapping is reported verbatim.

  (2) The effective environment handed to the launched subprocess. Given the
      mapping reported for the command (which may be ``None`` or empty) and the
      current process environment ``os.environ``, the effective environment is
      ``None`` whenever the command mapping is ``None`` or empty -- so the
      subprocess inherits ``os.environ`` rather than receiving an empty
      environment. When the command mapping is non-empty the effective
      environment is the merge of ``os.environ`` with the command mapping, the
      command mapping's entries taking precedence.

  The consequence that matters: an empty command mapping must yield ``None``
  (the subprocess then inherits ``os.environ``), never an empty mapping (which
  would launch the subprocess with no inherited variables at all).

Modelling choices (Nagini fragment):
  * An environment mapping is a ``Dict[int, int]`` from variable-name token to
    value token; only membership, per-key value, and emptiness are observed,
    so integer identity is the faithful carrier (mapping.md §2).
  * "absent environment" (the ``None`` the subprocess inherits ``os.environ``
    for) is carried by an ``Optional[Dict[int, int]]`` whose ``None`` case is
    the distinguished value.
  * The merge of two mappings (an unchanged standard mapping-unpacking the
    code invokes) is the single callee ``env_merge``; its standard semantics
    are validated against real Python out-of-band (axiom_check.py, G-AX).

Building the environment for the launched subprocess is a bounded,
straight-line computation: each operation MUST terminate and deliver its
value (a total-correctness obligation, carried as MustTerminate in the
preconditions). Nagini verifies partial correctness by default, so without
the obligation an implementation that diverges would satisfy every value
postcondition only vacuously and would hang the shell launch forever.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def env_merge(base: Dict[int, int], overlay: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**base, **overlay}`` (an unchanged callee the
    code invokes): a fresh non-empty mapping holding every key of either input,
    with ``overlay``'s value winning on a shared key. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(Acc(dict_pred(overlay), 1 / 2))
    # The real mapping-unpacking merge is a single bounded primitive step; the
    # strictly smaller measure (1 < 2) lets a contracted caller holding
    # MustTerminate(2) invoke it without leaking its own obligation.
    Requires(MustTerminate(1))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(overlay), 1 / 2))
    Ensures(len(base) == Old(len(base)))
    Ensures(len(overlay) == Old(len(overlay)))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every key of overlay is present with overlay's value (overlay wins).
    Ensures(Forall(int, lambda k: (Implies(k in overlay,
                                            (k in Result()) and Result()[k] == overlay[k]),
                                    [[k in overlay], [k in Result()]])))
    # Every key of base that overlay does not override keeps base's value.
    Ensures(Forall(int, lambda k: (Implies((k in base) and not (k in overlay),
                                            (k in Result()) and Result()[k] == base[k]),
                                    [[k in base], [k in Result()]])))
    # No spurious keys: the merge holds only keys of one of the inputs.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in base) or (k in overlay)),
                                    [[k in Result()]])))
# axioms-end


# pure-start
# No pure helpers: the normalisation/merge selection is the behaviour under
# specification and is spelled out in the impl regions; the unchanged mapping
# merge it composes is the env_merge callee (axioms region).
# pure-end


def normalized_environment(env: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(env), 1 / 2))
    # TERMINATION: reporting the command environment is bounded straight-line
    # work that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body would satisfy the value
    # postconditions only vacuously yet never deliver the reported mapping.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(env), 1 / 2))
    # An empty mapping is normalised to None ...
    Ensures(Implies(len(env) == 0, Result() is None))
    # ... and a non-empty mapping is reported verbatim (the same mapping).
    Ensures(Implies(len(env) > 0, Result() is env))
    # post-conditions-end
    # impl-start
    if len(env) == 0:
        return None
    return env
    # impl-end


def effective_environment(env: Optional[Dict[int, int]],
                          base: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Requires(Acc(dict_pred(base), 1 / 2))
    # TERMINATION: computing the effective environment for the subprocess is
    # bounded straight-line work (a None/emptiness decision plus at most one
    # bounded merge) that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body — e.g. hanging instead of
    # handing the subprocess its environment — would satisfy the value
    # postconditions only vacuously and the shell would never be launched.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Implies(Result() is not None, Acc(dict_pred(Result()))))
    # None (inherit os.environ) exactly when the command mapping is None/empty.
    Ensures(Implies(env is None, Result() is None))
    Ensures(Implies(env is not None and len(env) == 0, Result() is None))
    Ensures(Implies(env is not None and len(env) > 0, Result() is not None))
    # When non-empty, the result is the merge: the command mapping's entries
    # win, and the process environment's other entries are carried through.
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in env,
                                       (k in Result()) and Result()[k] == env[k]),
                               [[k in env], [k in Result()]]))))
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies((k in base) and not (k in env),
                                       (k in Result()) and Result()[k] == base[k]),
                               [[k in base], [k in Result()]]))))
    # No spurious keys: the effective environment holds only keys of the
    # command mapping or of the process environment (the merge adds nothing).
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in Result(), (k in env) or (k in base)),
                               [[k in Result()]]))))
    # post-conditions-end
    # impl-start
    if env is None:
        return None
    if len(env) == 0:
        return None
    merged = env_merge(base, env)
    return merged
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-14315/nagini. FROZEN spec: two modeled functions (normalized_environment, effective_environment) + env_merge A-consumed axiom, all contract/axiom/@Pure regions left byte-identical; only impl regions edited per attack.

ENV: adversary run with python,, cwd=.

Positive control = verbatim model.py => weakness CANDIDATE, verifies (25.4s), exit 0. Confirms tooling + verifier live.

8 distinct same-spec wrong impls (same-spec confirmed on a representative, exit 0 SAME):
- atk_1: prepatch bug site1 — effective_environment returns empty dict {} on empty env instead of None. cmd: `python -m swebench_unified.adversary weakness nagini django__django-14315 atk_1.py`. Result: NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (violates Implies(env not None and len==0, Result() is None)). [prepatch reproduced]
- atk_2: prepatch bug site2 — normalized_environment returns env on empty (no None normalisation). Result: exit 2, rejected (violates Implies(len==0, Result() is None)). [prepatch reproduced]
- atk_3: control-flow — effective_environment returns env instead of the base merge on nonempty. Result: exit 2, rejected (violates base-carry / merge postconditions).
- atk_4: ungrounded-oracle/arg-swap — merge computed as env_merge(env, base) (base wins) instead of env_merge(base, env) (env wins). Result: exit 2, rejected — proves the A-consumed axiom's overlay-wins directionality is load-bearing, not vacuous.
- atk_5: boundary/identity — normalized_environment returns a fresh dict(env) copy (same content, different object) on nonempty. Result: exit 2, rejected (violates Result() is env object-identity ensure — behaviourally equivalent but spec pins identity, faithful to `dict or None` returning the same object).
- atk_6: boundary — effective_environment returns base (non-None) on empty env. Result: exit 2, rejected (violates Result() is None on empty).
- atk_7: control-flow-effect/partial-domain — effective_environment drops the empty short-circuit, always merges when not None. Result: exit 2, rejected (empty env yields non-None merge, violates Result() is None on empty).
- atk_8: ungrounded-oracle echo — normalized_environment returns None always. Result: exit 2, rejected (violates Implies(len>0, Result() is env)).

All 8 attacks were REJECTED (none verified). No verifying wrong impl (no CANDIDATE) exists, so NO faithful refined patch needed a run_resolve (patches={}). The verify=>correct implication is not falsified.

A-LEG / correspondence audit:
- G-AX: ran bundle axiom_check.py with the lean env => exit 0: env_merge axiom (A-consumed) sound on 7 boundary + 20000 fuzz pairs; normalized_environment / effective_environment deep models (A-reference) == real Python `(env or None)` and `{**base,**env} if env else None` on boundary + 20000 fuzz inputs, incl. the F2P None/{}->None case.
- refinement.md audit: every leg is R / A-consumed (B4 merge, B5 merge postconditions) / A-reference (the two changed empty->None selections modeled deeply and validated == real Python) / I. NO kind-3 (unexpressible-changed-op) step. The single consumed axiom (env_merge) covers only the UNCHANGED mapping merge the new code invokes — never the operation under change; its Ensures is consumed by B4/B5 (no dead axiom). atk_4 confirms the axiom directionality is live. mapping.md bindings to base_commit 187118203197801c6cb72dc8b06b714b23b6dd3d check out (base<->os.environ, env<->settings_to_cmd_args_env return, env_merge<->base/client.py:25 unchanged).
- Gold patch.diff is two one-line hunks matching the two modeled selections exactly.

VERDICT: SOUND. >=5 distinct same-spec attacks (8 run) plus prepatch bugs all rejected; positive control verifies; G-AX passes; refinement legs all R/A/I with sound A-leg correspondence. No verify-but-not-resolve counterexample found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) checked for django__django-14315 nagini bundle. Same-spec confirmed the unchanged model shares the frozen spec region (exit 0).

Real repo at base_commit 187118203197801c6cb72dc8b06b714b23b6dd3d, post-patch behavior:
  * postgresql/client.py:54  -> return args, (env or None)         [modeled by normalized_environment]
  * base/client.py:25        -> env = {**os.environ, **env} if env else None  [modeled by effective_environment]
  * env_merge axiom          -> {**os.environ, **env} (UNCHANGED merge)

Every spec postcondition was checked against the real repo expressions and found to HOLD (spec is not too strong / does not drift), via two independent runs:
  (1) bundle axiom_check.py (G-AX): 7 boundary + 20000 fuzz pairs, deep models == real Python incl. None/{}->None. exit 0.
  (2) my independent 200k-input + boundary probe: normalized_environment (empty->None, non-empty->`Result() is env` identity), effective_environment (None/empty->None, non-empty->merge with overlay winning, base carried, no spurious keys). No divergence found.

Type refinement (str->int token dict, dict truthiness -> len/is-None) is sound because the two sites observe only membership/per-key value/emptiness/None; textual key/value content is never observed through them. MustTerminate(2)/(1) are total-correctness strengthenings the real bounded straight-line code trivially satisfies (they cannot cause the spec to accept behavior the real code rejects; they only reject non-terminating impls). The gold patch (patch.diff verbatim) is the correctness oracle and resolves.

No input exists where the modeled function disagrees with the real callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Semantic leakage judgment on the nagini spec view for django__django-14315 (spec view computed via markers.spec_view; impl regions elided). Mechanical G-LEAK screen also passes (leakage.screen: passed=True, no hard failures).

The public problem_statement already discloses the entire discriminating fix: 'postgresql client returns empty dict instead of None for env' and 'as a result os.environ is not used and empty env passed to subprocess.' Thus the gold edit's essence — normalize an empty command mapping to None so os.environ is inherited rather than an empty environment — is PUBLIC.

The spec view only restates this as desired behavior at the two observation sites: (1) normalized_environment reports empty->None else verbatim; (2) effective_environment yields None when the command mapping is None/empty (subprocess inherits os.environ) else the merge with os.environ, command entries winning. This is derivable directly from the problem statement.

Checked for leakage beyond problem_statement and found none:
- No diff markers (@@, diff --git, +++, ---, index) in the view.
- No patched file paths (django/db/backends/base/client.py, .../postgresql/client.py) or dotted module paths appear in the spec view (they live only in mapping.md/refinement.md, which are NOT part of the consumer spec view).
- No patched repo symbols leaked: the gold touches runshell / settings_to_cmd_args_env / DatabaseClient / BaseDatabaseClient. None of these appear as spec-view identifiers or in spec-view comments/docstrings. The model's own names (normalized_environment, effective_environment, env_merge, base) are neutral modeling names, not repo symbols.
- 'os.environ' appears in the spec view but is named verbatim in the public problem_statement, so it is not a leak.
- No bug/fix/patch narration in comments; the docstring frames behavior desired, not an edit ('stated as desired behaviour, not as an edit').
- No verbatim gold-patch line ('return args, (env or None)', 'env = {**os.environ, **env} if env else None') is reproduced in the spec view; the impl regions that would spell these out are elided.

Everything the spec view reveals is either public in problem_statement or a neutral formal restatement of the required externally-observable behavior. No reconstruction of the gold edit is possible from the spec view that isn't already possible from problem_statement alone.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
