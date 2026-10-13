# P2 adversarial audit — sphinx-doc__sphinx-8459

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -142,10 +140,10 @@
     # impl-start
     annotation = {}  # type: Dict[int, int]
     if has0:
-        annotation[name0] = resolve(raw0, aliases)
+        annotation[name0] = expand(raw0)
     if has1:
-        annotation[name1] = resolve(raw1, aliases)
+        annotation[name1] = expand(raw1)
     if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+        annotation[KEY_RETURN()] = expand(ret_raw)
     return annotation
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -145,7 +143,5 @@
         annotation[name0] = resolve(raw0, aliases)
     if has1:
         annotation[name1] = resolve(raw1, aliases)
-    if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
     return annotation
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -142,9 +140,9 @@
     # impl-start
     annotation = {}  # type: Dict[int, int]
     if has0:
-        annotation[name0] = resolve(raw0, aliases)
+        annotation[name0] = resolve(raw1, aliases)
     if has1:
-        annotation[name1] = resolve(raw1, aliases)
+        annotation[name1] = resolve(raw0, aliases)
     if ret_has:
         annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
     return annotation
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -141,11 +139,8 @@
     # post-conditions-end
     # impl-start
     annotation = {}  # type: Dict[int, int]
-    if has0:
-        annotation[name0] = resolve(raw0, aliases)
-    if has1:
-        annotation[name1] = resolve(raw1, aliases)
-    if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+    annotation[name0] = resolve(raw0, aliases)
+    annotation[name1] = resolve(raw1, aliases)
+    annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
     return annotation
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -142,10 +140,19 @@
     # impl-start
     annotation = {}  # type: Dict[int, int]
     if has0:
-        annotation[name0] = resolve(raw0, aliases)
+        if raw0 in aliases:
+            annotation[name0] = aliases[raw0]
+        else:
+            annotation[name0] = raw0
     if has1:
-        annotation[name1] = resolve(raw1, aliases)
+        if raw1 in aliases:
+            annotation[name1] = aliases[raw1]
+        else:
+            annotation[name1] = raw1
     if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+        if ret_raw in aliases:
+            annotation[KEY_RETURN()] = aliases[ret_raw]
+        else:
+            annotation[KEY_RETURN()] = ret_raw
     return annotation
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -141,11 +139,11 @@
     # post-conditions-end
     # impl-start
     annotation = {}  # type: Dict[int, int]
+    if ret_has:
+        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+    if has1:
+        annotation[name1] = resolve(raw1, aliases)
     if has0:
         annotation[name0] = resolve(raw0, aliases)
-    if has1:
-        annotation[name1] = resolve(raw1, aliases)
-    if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
     return annotation
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -142,10 +140,19 @@
     # impl-start
     annotation = {}  # type: Dict[int, int]
     if has0:
-        annotation[name0] = resolve(raw0, aliases)
+        if raw0 in aliases:
+            annotation[name0] = aliases[raw0]
+        else:
+            annotation[name0] = expand(raw0)
     if has1:
-        annotation[name1] = resolve(raw1, aliases)
+        if raw1 in aliases:
+            annotation[name1] = aliases[raw1]
+        else:
+            annotation[name1] = expand(raw1)
     if ret_has:
-        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+        if ret_raw in aliases:
+            annotation[KEY_RETURN()] = aliases[ret_raw]
+        else:
+            annotation[KEY_RETURN()] = expand(ret_raw)
     return annotation
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -143,6 +141,7 @@
     annotation = {}  # type: Dict[int, int]
     if has0:
         annotation[name0] = resolve(raw0, aliases)
+        annotation[name0] = resolve(raw0, aliases)
     if has1:
         annotation[name1] = resolve(raw1, aliases)
     if ret_has:
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -112,7 +111,6 @@
     Requires(name0 != name1)
     Requires(name0 != KEY_RETURN())
     Requires(name1 != KEY_RETURN())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(aliases), 1 / 2))
@@ -147,5 +145,6 @@
         annotation[name1] = resolve(raw1, aliases)
     if ret_has:
         annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
+    annotation[-2] = 42
     return annotation
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8459.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation step records, into a per-object mapping, the rendered
  annotation of each parameter of a callable (and of its return), so a later
  rendering pass can present each parameter's type. Each parameter that carries
  an annotation contributes one entry: the parameter's name maps to the
  rendered form of that parameter's resolved annotation; a parameter with no
  annotation contributes nothing. The return annotation, when present, is
  recorded under a single reserved name slot.

  The behaviour pinned here is HOW an annotation source is resolved before it is
  recorded. The step is configured with a user-supplied alias map from an
  annotation source token to the token it should resolve to. The resolution
  honours that map:

    * when the alias map governs an annotation source token (the token is a key
      of the map), the recorded annotation is the alias's target token — the
      user-chosen name is preserved exactly as configured;

    * when the alias map does NOT govern the source token, the recorded
      annotation is the token's own underlying expansion (the form the source
      resolves to with no alias overrides).

  The consequence that matters: a parameter whose annotation source is an alias
  the user configured is recorded under the configured alias, NOT under the
  expanded underlying form — and this holds whether or not the surrounding
  rendering mode would otherwise expand it. A recorded mapping that ignores the
  configured alias map and expands every source token is rejected.

Modelling choices (Nagini fragment):
  * A callable's parameters and return are modelled as explicit named slots: two
    parameters (name token + annotation source token + has-annotation flag each)
    and a return (source token + has flag). The real step records each parameter
    independently, so a small constant number of named slots faithfully captures
    the per-slot recording without a loop; the tested callable has exactly two
    parameters and a return. Distinct names / annotation strings are interned as
    distinct ``int`` tokens; only identity and mapping membership are observed
    (mapping.md §2), so integer identity is faithful.
  * The configured alias map is a ``Dict[int, int]`` (source token -> resolved
    token). The recorded mapping is a ``Dict[int, int]`` (name token -> recorded
    annotation token), with the return recorded under the reserved key
    ``KEY_RETURN()``.
  * ``resolve(tok, aliases)`` is the deep model of how one source token is
    resolved given the alias map: the alias's target when the map governs it,
    otherwise the token's underlying expansion ``expand(tok)``. ``resolve`` /
    ``expand`` model the underlying annotation resolver and are validated ==
    the real resolution behaviour out-of-band by axiom_check.py (G-AX); they
    are NOT consumed axioms.

The alias map is read, not mutated, so it is held at fractional permission
(required AND ensured); the freshly built recorded mapping is returned at full
permission. No string indexing is used (Nagini bans it). Dict access is guarded
by an explicit membership test before subscription. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The alias-honouring annotation resolution is modelled
# DEEPLY by `resolve` / `expand` in the pure region; the proof never depends on
# a `@ContractOnly` contract. The underlying resolver is the A-reference that
# axiom_check.py (G-AX) validates the deep model against, not a consumed axiom.
# axioms-end


# pure-start
@Pure
def KEY_RETURN() -> int:
    # The reserved name slot under which the return annotation is recorded.
    # Distinct from every parameter-name token (pinned by a precondition).
    return -1


@Pure
def expand(tok: int) -> int:
    """The underlying expansion of an annotation source token when NO alias
    governs it: the form the source resolves to with no alias overrides. Modeled
    deeply (the per-token expansion); validated == the real no-alias resolver by
    axiom_check.py (G-AX). Encoded so an aliased source and its expansion are
    DIFFERENT tokens unless the source is its own underlying type."""
    return tok + 1000


@Pure
def resolve(tok: int, aliases: Dict[int, int]) -> int:
    """The recorded annotation token for one source token under the alias map:
    the alias's target when the map governs the token, otherwise the token's own
    underlying expansion. This is the alias-honouring resolution the recorded
    annotation must reflect."""
    Requires(Acc(dict_pred(aliases), 1 / 4))
    if tok in aliases:
        return aliases[tok]
    return expand(tok)
# pure-end


def record_annotations(name0: int, raw0: int, has0: bool,
                       name1: int, raw1: int, has1: bool,
                       aliases: Dict[int, int],
                       ret_raw: int, ret_has: bool) -> Dict[int, int]:
    # pre-conditions-start
    # The alias map is read, not mutated: fractional permission.
    Requires(Acc(dict_pred(aliases), 1 / 2))
    # Parameter names are distinct from each other and from the reserved return
    # slot, so each parameter's recorded entry is independent of the others and
    # of the return entry (the real mapping is keyed by distinct names).
    Requires(name0 != name1)
    Requires(name0 != KEY_RETURN())
    Requires(name1 != KEY_RETURN())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(aliases), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    # (1) Each annotated parameter contributes one entry: its name maps to the
    #     ALIAS-RESOLVED annotation token `resolve(raw, aliases)` — the
    #     configured alias when the map governs the source, else its underlying
    #     expansion. An implementation that ignores the alias map (records the
    #     expansion regardless) violates this whenever an alias governs the
    #     source and differs from the expansion.
    Ensures(Implies(has0,
                    name0 in Result()
                    and Result()[name0] == resolve(raw0, aliases)))
    Ensures(Implies(has1,
                    name1 in Result()
                    and Result()[name1] == resolve(raw1, aliases)))
    # (2) A parameter with no annotation contributes no entry under its name.
    Ensures(Implies(not has0, not (name0 in Result())))
    Ensures(Implies(not has1, not (name1 in Result())))
    # (3) The return annotation, when present, is recorded under the reserved
    #     slot, also alias-resolved; when absent, the reserved slot is unset.
    Ensures(Implies(ret_has,
                    KEY_RETURN() in Result()
                    and Result()[KEY_RETURN()] == resolve(ret_raw, aliases)))
    Ensures(Implies(not ret_has, not (KEY_RETURN() in Result())))
    # post-conditions-end
    # impl-start
    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PATH prefixed with; All commands run from there.

SPEC SHAPE: record_annotations postconditions pin Result() at exactly the three observed keys (name0, name1, KEY_RETURN()) to resolve(raw_i, aliases), where resolve is consumed SYMMETRICALLY in both the postcondition and the impl, plus absent-key clauses (not has_i => name_i not in Result; not ret_has => KEY_RETURN not in Result). Names are symbolic ints pinned distinct from each other and from KEY_RETURN(). This leaves essentially no behavioral freedom: any verifying impl must record resolve(raw_i, aliases) under each present key and nothing spurious.

### ATTACK SUITE (all confirmed SAME-SPEC via `adversary same-spec`; positive control pc.py = frozen model.py VERIFIES, PC_EXIT=0, 14.05s):

WRONG-IMPL attacks — all correctly REJECTED (weakness exit 2, verification failed):
- atk_1 (PREPATCH BUG / ungrounded): expand(raw_i) regardless of alias map -> reproduces the observed bug; FAILS clause (1). prepatch_reproduced=true.
- atk_2 (PARTIAL DOMAIN): records params, drops the return -> FAILS clause (3).
- atk_3 (BOUNDARY/wrong-source): swaps raw0<->raw1 sources under name0/name1 -> FAILS clause (1).
- atk_4 (CONTROL-FLOW EFFECT): always records regardless of has flags -> FAILS clause (2).
- atk_5 (UNGROUNDED-ORACLE ECHO): no-alias branch records raw itself instead of expand(raw) -> FAILS clause (1).
- atk_9 (EXTRA-KEY probe): appends spurious annotation[-2]=42; -2 is provably != KEY_RETURN()(-1) but NOT provably distinct from symbolic name0/name1, so FAILS -> confirms spec rejects spurious extra keys (tightness).

VERIFYING CANDIDATES (weakness exit 0 = shares spec AND verifies) — each behaviorally identical to gold impl:
- atk_6: gold echo, writes reordered (return first). Order unobserved per refinement.md A6.
- atk_7: gold echo with resolve() inlined as its two-branch definition (aliases[raw] if raw in aliases else expand(raw)) == resolve exactly.
- atk_8: gold echo with an idempotent duplicate write of name0 (same value).
All three are the gold behavior; their FAITHFUL refined patch is the gold patch verbatim: inspect.signature(obj) -> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases).

MANDATORY RESOLVE RUN (materialized faithful patch through official harness): run_resolve('sphinx-doc__sphinx-8459', <gold patch>, run_id='sbu-eq-echo-8459') => RESOLVED=True, completed=True, flaky=False, note='resolved'. So every verifying candidate's faithful patch RESOLVES. No verify-but-not-resolve exists => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: A1/A2/A5/A6 = R (type refinements), A4 = I (identical control flow), A3 = A-reference (deep model resolve/expand validated == real get_type_hints by axiom_check.py; G-AX exit 0 recorded in meta.json). No kind-3 leg, no consumed axiom. A3 non-self-alias divergence is disclosed+scoped in mapping.md §3.1 to name-preserving self-alias configs (tested config {myint:myint}, issue reproducer {JSONObject:types.JSONObject}); resolve is consumed symmetrically so it is non-exploitable for verify=>correct, and the F2P correctness oracle uses only the self-alias config on which the deep model is exact.

VERDICT: SOUND. >=5 distinct wrong impls run and all rejected; all verifying candidates' faithful patches resolve; refinement legs are all R/A-reference/I with sound A-reference correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8459.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation step records, into a per-object mapping, the rendered
  annotation of each parameter of a callable (and of its return), so a later
  rendering pass can present each parameter's type. Each parameter that carries
  an annotation contributes one entry: the parameter's name maps to the
  rendered form of that parameter's resolved annotation; a parameter with no
  annotation contributes nothing. The return annotation, when present, is
  recorded under a single reserved name slot.

  The behaviour pinned here is HOW an annotation source is resolved before it is
  recorded. The step is configured with a user-supplied alias map from an
  annotation source token to the token it should resolve to. The resolution
  honours that map:

    * when the alias map governs an annotation source token (the token is a key
      of the map), the recorded annotation is the alias's target token — the
      user-chosen name is preserved exactly as configured;

    * when the alias map does NOT govern the source token, the recorded
      annotation is the token's own underlying expansion (the form the source
      resolves to with no alias overrides).

  The consequence that matters: a parameter whose annotation source is an alias
  the user configured is recorded under the configured alias, NOT under the
  expanded underlying form — and this holds whether or not the surrounding
  rendering mode would otherwise expand it. A recorded mapping that ignores the
  configured alias map and expands every source token is rejected.

Modelling choices (Nagini fragment):
  * A callable's parameters and return are modelled as explicit named slots: two
    parameters (name token + annotation source token + has-annotation flag each)
    and a return (source token + has flag). The real step records each parameter
    independently, so a small constant number of named slots faithfully captures
    the per-slot recording without a loop; the tested callable has exactly two
    parameters and a return. Distinct names / annotation strings are interned as
    distinct ``int`` tokens; only identity and mapping membership are observed
    (mapping.md §2), so integer identity is faithful.
  * The configured alias map is a ``Dict[int, int]`` (source token -> resolved
    token). The recorded mapping is a ``Dict[int, int]`` (name token -> recorded
    annotation token), with the return recorded under the reserved key
    ``KEY_RETURN()``.
  * ``resolve(tok, aliases)`` is the deep model of how one source token is
    resolved given the alias map: the alias's target when the map governs it,
    otherwise the token's underlying expansion ``expand(tok)``. ``resolve`` /
    ``expand`` model the underlying annotation resolver and are validated ==
    the real resolution behaviour out-of-band by axiom_check.py (G-AX); they
    are NOT consumed axioms.

The alias map is read, not mutated, so it is held at fractional permission
(required AND ensured); the freshly built recorded mapping is returned at full
permission. No string indexing is used (Nagini bans it). Dict access is guarded
by an explicit membership test before subscription. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The alias-honouring annotation resolution is modelled
# DEEPLY by `resolve` / `expand` in the pure region; the proof never depends on
# a `@ContractOnly` contract. The underlying resolver is the A-reference that
# axiom_check.py (G-AX) validates the deep model against, not a consumed axiom.
# axioms-end


# pure-start
@Pure
def KEY_RETURN() -> int:
    # The reserved name slot under which the return annotation is recorded.
    # Distinct from every parameter-name token (pinned by a precondition).
    return -1


@Pure
def expand(tok: int) -> int:
    """The underlying expansion of an annotation source token when NO alias
    governs it: the form the source resolves to with no alias overrides. Modeled
    deeply (the per-token expansion); validated == the real no-alias resolver by
    axiom_check.py (G-AX). Encoded so an aliased source and its expansion are
    DIFFERENT tokens unless the source is its own underlying type."""
    return tok + 1000


@Pure
def resolve(tok: int, aliases: Dict[int, int]) -> int:
    """The recorded annotation token for one source token under the alias map:
    the alias's target when the map governs the token, otherwise the token's own
    underlying expansion. This is the alias-honouring resolution the recorded
    annotation must reflect."""
    Requires(Acc(dict_pred(aliases), 1 / 4))
    if tok in aliases:
        return aliases[tok]
    return expand(tok)
# pure-end


def record_annotations(name0: int, raw0: int, has0: bool,
                       name1: int, raw1: int, has1: bool,
                       aliases: Dict[int, int],
                       ret_raw: int, ret_has: bool) -> Dict[int, int]:
    # pre-conditions-start
    # The alias map is read, not mutated: fractional permission.
    Requires(Acc(dict_pred(aliases), 1 / 2))
    # Parameter names are distinct from each other and from the reserved return
    # slot, so each parameter's recorded entry is independent of the others and
    # of the return entry (the real mapping is keyed by distinct names).
    Requires(name0 != name1)
    Requires(name0 != KEY_RETURN())
    Requires(name1 != KEY_RETURN())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(aliases), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    # (1) Each annotated parameter contributes one entry: its name maps to the
    #     ALIAS-RESOLVED annotation token `resolve(raw, aliases)` — the
    #     configured alias when the map governs the source, else its underlying
    #     expansion. An implementation that ignores the alias map (records the
    #     expansion regardless) violates this whenever an alias governs the
    #     source and differs from the expansion.
    Ensures(Implies(has0,
                    name0 in Result()
                    and Result()[name0] == resolve(raw0, aliases)))
    Ensures(Implies(has1,
                    name1 in Result()
                    and Result()[name1] == resolve(raw1, aliases)))
    # (2) A parameter with no annotation contributes no entry under its name.
    Ensures(Implies(not has0, not (name0 in Result())))
    Ensures(Implies(not has1, not (name1 in Result())))
    # (3) The return annotation, when present, is recorded under the reserved
    #     slot, also alias-resolved; when absent, the reserved slot is unset.
    Ensures(Implies(ret_has,
                    KEY_RETURN() in Result()
                    and Result()[KEY_RETURN()] == resolve(ret_raw, aliases)))
    Ensures(Implies(not ret_has, not (KEY_RETURN() in Result())))
    # post-conditions-end
    # impl-start
    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PATH prefixed with; All commands run from there.

SPEC SHAPE: record_annotations postconditions pin Result() at exactly the three observed keys (name0, name1, KEY_RETURN()) to resolve(raw_i, aliases), where resolve is consumed SYMMETRICALLY in both the postcondition and the impl, plus absent-key clauses (not has_i => name_i not in Result; not ret_has => KEY_RETURN not in Result). Names are symbolic ints pinned distinct from each other and from KEY_RETURN(). This leaves essentially no behavioral freedom: any verifying impl must record resolve(raw_i, aliases) under each present key and nothing spurious.

### ATTACK SUITE (all confirmed SAME-SPEC via `adversary same-spec`; positive control pc.py = frozen model.py VERIFIES, PC_EXIT=0, 14.05s):

WRONG-IMPL attacks — all correctly REJECTED (weakness exit 2, verification failed):
- atk_1 (PREPATCH BUG / ungrounded): expand(raw_i) regardless of alias map -> reproduces the observed bug; FAILS clause (1). prepatch_reproduced=true.
- atk_2 (PARTIAL DOMAIN): records params, drops the return -> FAILS clause (3).
- atk_3 (BOUNDARY/wrong-source): swaps raw0<->raw1 sources under name0/name1 -> FAILS clause (1).
- atk_4 (CONTROL-FLOW EFFECT): always records regardless of has flags -> FAILS clause (2).
- atk_5 (UNGROUNDED-ORACLE ECHO): no-alias branch records raw itself instead of expand(raw) -> FAILS clause (1).
- atk_9 (EXTRA-KEY probe): appends spurious annotation[-2]=42; -2 is provably != KEY_RETURN()(-1) but NOT provably distinct from symbolic name0/name1, so FAILS -> confirms spec rejects spurious extra keys (tightness).

VERIFYING CANDIDATES (weakness exit 0 = shares spec AND verifies) — each behaviorally identical to gold impl:
- atk_6: gold echo, writes reordered (return first). Order unobserved per refinement.md A6.
- atk_7: gold echo with resolve() inlined as its two-branch definition (aliases[raw] if raw in aliases else expand(raw)) == resolve exactly.
- atk_8: gold echo with an idempotent duplicate write of name0 (same value).
All three are the gold behavior; their FAITHFUL refined patch is the gold patch verbatim: inspect.signature(obj) -> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases).

MANDATORY RESOLVE RUN (materialized faithful patch through official harness): run_resolve('sphinx-doc__sphinx-8459', <gold patch>, run_id='sbu-eq-echo-8459') => RESOLVED=True, completed=True, flaky=False, note='resolved'. So every verifying candidate's faithful patch RESOLVES. No verify-but-not-resolve exists => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: A1/A2/A5/A6 = R (type refinements), A4 = I (identical control flow), A3 = A-reference (deep model resolve/expand validated == real get_type_hints by axiom_check.py; G-AX exit 0 recorded in meta.json). No kind-3 leg, no consumed axiom. A3 non-self-alias divergence is disclosed+scoped in mapping.md §3.1 to name-preserving self-alias configs (tested config {myint:myint}, issue reproducer {JSONObject:types.JSONObject}); resolve is consumed symmetrically so it is non-exploitable for verify=>correct, and the F2P correctness oracle uses only the self-alias config on which the deep model is exact.

VERDICT: SOUND. >=5 distinct wrong impls run and all rejected; all verifying candidates' faithful patches resolve; refinement legs are all R/A-reference/I with sound A-reference correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec integrity: `same-spec nagini sphinx-doc__sphinx-8459` returns SAME (exit 0) on the model itself — spec region byte-identical with the frozen bundle spec.

Empirical test against the base-commit worktree (@ 68aa4fb2, real sphinx.util.inspect.signature + typing.stringify replicating gold record_typehints):
  * self-alias {'myint':'myint'} (the F2P test's EXACT config): real -> {'x':'myint','y':'myint','return':'myint'}; model resolve('myint',{'myint':'myint'})=aliases[tok]='myint' => AGREE.
  * no-alias {} (prepatch default): real -> {'x':'int',...}; model expand('myint')='int' => AGREE (G-DIFF sound: prepatch records expand, fails clause (1)).
  * non-self {'JSONObject':'types.JSONObject'}: real -> 'JSONObject'; model -> 'types.JSONObject' => DISAGREE.

Exploitability: (1) F2P oracle test_autodoc_typehints_description_and_type_aliases uses ONLY {'myint':'myint'}, on which model==real gold; (2) divergence confined to non-self-alias configs, explicitly disclosed+scoped in mapping.md 3.1 and validated by G-AX only over the self-alias domain (axiom_check builds aliases={name:name}); (3) resolve is consumed SYMMETRICALLY in postcondition clause (1) and in the impl, so any verifying model records resolve(raw,aliases) which equals the real gold output on the tested self-alias input -> resolves. No verifying-but-non-resolving model is reachable via the out-of-domain divergence. Spec is not too strong on any input the correctness oracle exercises. Verdict: FAITHFUL (divergence exists but is non-exploitable, out-of-tested-domain, and disclosed).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view = model.py (mapping.md/refinement.md are audit artifacts, not the solver-visible view). Gold edit: inspect.signature(obj) -> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases) in record_typehints (sphinx/ext/autodoc/typehints.py) — i.e. resolve recorded param/return annotations THROUGH the configured alias map instead of expanding them.

What the public problem_statement already discloses: autodoc_type_aliases fails under autodoc_typehints='description'; expected types.JSONObject instead of Dict[str, Any] in BOTH modes. The full desired behavior (honor the configured alias rather than expand to underlying) is already public.

The spec view restates exactly that public behavior abstractly: 'when the alias map governs a source token, record the alias target; else record the underlying expansion', return under a reserved slot, unannotated params skipped. It never names the patched function (record_typehints), never names the patched file/module path (typehints.py), and never reveals the edit mechanism (inspect.signature type_aliases plumbing / get_type_hints localns / stringify) — those appear only in mapping.md/refinement.md (audit-only). Mechanical G-LEAK passes clean (no diff markers, no reproduced gold line, no patched path, no spec-view identifier/comment echoing record_typehints; the sole changed symbol record_typehints does not appear in the spec view).

The spec view stays at the level the problem statement already establishes (honor the alias) and does not reveal the gold discriminator's implementation beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
