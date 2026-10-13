# P2 adversarial audit — django__django-12713

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
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -153,11 +151,10 @@
                                            Old(k in options)))))
     # post-conditions-end
     # impl-start
-    if not (key_component() in options):
-        if test_primary:
-            options[key_component()] = default_primary()
-        elif test_secondary:
-            options[key_component()] = default_secondary()
-        elif test_tertiary:
-            options[key_component()] = default_tertiary()
+    if test_primary:
+        options[key_component()] = default_primary()
+    elif test_secondary:
+        options[key_component()] = default_secondary()
+    elif test_tertiary:
+        options[key_component()] = default_tertiary()
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -156,8 +154,4 @@
     if not (key_component() in options):
         if test_primary:
             options[key_component()] = default_primary()
-        elif test_secondary:
-            options[key_component()] = default_secondary()
-        elif test_tertiary:
-            options[key_component()] = default_tertiary()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -154,10 +152,10 @@
     # post-conditions-end
     # impl-start
     if not (key_component() in options):
-        if test_primary:
+        if test_secondary:
+            options[key_component()] = default_secondary()
+        elif test_primary:
             options[key_component()] = default_primary()
-        elif test_secondary:
-            options[key_component()] = default_secondary()
         elif test_tertiary:
             options[key_component()] = default_tertiary()
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -160,4 +158,5 @@
             options[key_component()] = default_secondary()
         elif test_tertiary:
             options[key_component()] = default_tertiary()
+    options[99] = 99
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -155,7 +153,7 @@
     # impl-start
     if not (key_component() in options):
         if test_primary:
-            options[key_component()] = default_primary()
+            options[key_component()] = default_secondary()
         elif test_secondary:
             options[key_component()] = default_secondary()
         elif test_tertiary:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -153,11 +151,5 @@
                                            Old(k in options)))))
     # post-conditions-end
     # impl-start
-    if not (key_component() in options):
-        if test_primary:
-            options[key_component()] = default_primary()
-        elif test_secondary:
-            options[key_component()] = default_secondary()
-        elif test_tertiary:
-            options[key_component()] = default_tertiary()
+    pass
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     # gated on the genuine entry membership rather than on a membership query
     # that an implementation could perturb by adding the key itself.
     Requires(component_present == (key_component() in options))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(dict_pred(options)))
@@ -160,4 +158,6 @@
             options[key_component()] = default_secondary()
         elif test_tertiary:
             options[key_component()] = default_tertiary()
+        else:
+            options[key_component()] = default_tertiary()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12713.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration step assembles a mapping of keyword options that build a form
  field for a multi-valued relation. Those options may already carry an explicit
  presentation component supplied by the caller. The step also has a default
  presentation component it would otherwise pick, chosen from the relation's
  name by a priority order among three name-membership tests: the primary test
  has highest priority, then the secondary, then the tertiary; if the name
  satisfies none of them no default is chosen.

  The single behaviour pinned here is the precedence between the caller's
  explicit component and the name-derived default:

  (1) When the options already carry an explicit presentation component, that
      component is left exactly as the caller supplied it -- no name-derived
      default is allowed to replace it -- regardless of which (if any) of the
      three name-membership tests the relation satisfies.

  (2) When the options do NOT carry an explicit presentation component, the
      name-derived default is established, selected by that priority order: the
      primary default if the name satisfies the primary test; else the secondary
      default if it satisfies the secondary test; else the tertiary default if
      it satisfies the tertiary test; else no component is established (the
      options still carry none).

  The consequence that matters: a caller who supplies an explicit presentation
  component keeps it even when the relation's name would otherwise select one of
  the three name-derived defaults. This mirrors the sibling configuration step
  for single-valued relations, which already honours a caller-supplied
  component.

Modelling choices (Nagini fragment):
  * The keyword options are a ``Dict[int, int]`` from an option-name token to a
    component-identity token; only membership of the presentation-component key
    and its value are observed, so integer identity is the faithful carrier
    (mapping.md §2). The presentation-component key is the module-level constant
    ``key_component()``.
  * Each of the three name-membership tests is a ``bool`` parameter (the result
    of testing the relation's name against the corresponding configured set);
    booleans need no permission. The three name-derived component identities are
    the module-level constants ``default_primary()`` / ``default_secondary()`` /
    ``default_tertiary()``.
  * Whether the options already carry the presentation component AT ENTRY is
    captured as a ``bool`` parameter ``component_present`` pinned by a
    precondition to the entry membership of ``key_component()``. This makes the
    default-selection guarantee gate on a genuine pre-state fact about the input
    rather than on a membership query against the (mutated-in-place) options,
    which would let an implementation discharge the guarantee vacuously by
    adding the key itself.

The options mapping is genuinely mutated in place, so it is held at FULL
permission and its exact post-state is stated (the pre-state membership/value of
each key is captured with ``Old`` and the entry presence of the presentation
component is captured by ``component_present``). No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (the precedence guard and the priority
chain are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the precedence guard and the name-derived default selection are the
# behaviour under specification and are spelled out deeply in the impl region.
# There is no unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def key_component() -> int:
    # The option-name token for the presentation component.
    return 0

@Pure
def default_primary() -> int:
    # Component identity selected by the highest-priority name-membership test.
    return 1

@Pure
def default_secondary() -> int:
    # Component identity selected by the second-priority name-membership test.
    return 2

@Pure
def default_tertiary() -> int:
    # Component identity selected by the third-priority name-membership test.
    return 3
# pure-end

def select_component(options: Dict[int, int],
                     component_present: bool,
                     test_primary: bool,
                     test_secondary: bool,
                     test_tertiary: bool) -> None:
    # pre-conditions-start
    # The options mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(options)))
    # ``component_present`` captures, AT ENTRY, whether the options already carry
    # the presentation component. It is a pre-state fact about the input -- bound
    # before any mutation -- so the default-selection guarantee below can be
    # gated on the genuine entry membership rather than on a membership query
    # that an implementation could perturb by adding the key itself.
    Requires(component_present == (key_component() in options))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(options)))
    # (1) Every option present on entry is preserved exactly -- still present on
    #     exit with the same value. This is the precedence guarantee: a
    #     caller-supplied presentation component (the presentation key being
    #     present on entry) is left exactly as supplied, so no name-derived
    #     default replaces it, whatever the three membership tests say. The step
    #     touches only the presentation component, and only by ADDING it.
    Ensures(Forall(int, lambda k: (Implies(Old(k in options),
                                           (k in options) and options[k] == Old(options[k])))))
    # (2) When the options do NOT already carry the presentation component (i.e.
    #     it was absent at entry, ``not component_present``), the name-derived
    #     default is established by the priority order primary > secondary >
    #     tertiary; if no test matches, no component is established (the options
    #     still carry none). The antecedent is the captured ENTRY fact
    #     ``not component_present``, not a membership query on the (possibly
    #     mutated) options, so each implication has teeth: an implementation must
    #     store the priority-correct default, and only it.
    Ensures(Implies(not component_present and test_primary,
                    key_component() in options
                    and options[key_component()] == default_primary()))
    Ensures(Implies(not component_present and not test_primary and test_secondary,
                    key_component() in options
                    and options[key_component()] == default_secondary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and test_tertiary,
                    key_component() in options
                    and options[key_component()] == default_tertiary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and not test_tertiary,
                    not (key_component() in options)))
    # No option key other than the presentation component is added: any key
    # present on exit other than the presentation key must have been present on
    # entry. Stated forward (the entry-membership query is the consequent, not a
    # negated antecedent on a possibly-added key) so it constrains body-added
    # keys: an implementation that stores any spurious extra option cannot
    # verify.
    Ensures(Forall(int, lambda k: (Implies((k in options) and k != key_component(),
                                           Old(k in options)))))
    # post-conditions-end
    # impl-start
    if not (key_component() in options):
        chosen = 0
        found = False
        if test_primary:
            chosen = default_primary()
            found = True
        elif test_secondary:
            chosen = default_secondary()
            found = True
        elif test_tertiary:
            chosen = default_tertiary()
            found = True
        if found:
            options[key_component()] = chosen
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: model.py select_component is a TOTAL functional spec on the abstract domain. Both branches fully pin the post-state: (clause 1) preservation Forall k. Old(k in options) => k in options and options[k]==Old(options[k]); (no-spurious-key) Forall k. (k in options and k!=key_component()) => Old(k in options); (clause 2, gated on the ENTRY fact not component_present pinned by Requires(component_present == (key_component() in options))) the priority-ordered default selection primary>secondary>tertiary, and NO key added when no test fires. Because component_present is a pre-state Requires (not an Old-membership query on the mutated dict), the priority implications have teeth.

ATTACKS (all same-spec confirmed via `adversary same-spec`; impl region edited ONLY, axioms/@Pure/Requires/Ensures byte-identical). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12713 <f>.py`. Ran concurrently in batches of 3 (each spawns JVM+Z3). atk_1.py PREPATCH bug (drop presence guard, overwrite caller component): exit 2 NOT-A-COUNTEREXAMPLE (does not verify).

Direct verify: FAILED 41.9s, fails preservation postcondition (line 121) — spec senses the bug. prepatch_reproduced=true. atk_2.py PARTIAL-DOMAIN (only primary branch, drops secondary/tertiary): exit 2 (does not verify). atk_3.py WRONG-PRIORITY/boundary (secondary checked before primary): exit 2 (does not verify). atk_4.py CONTROL-FLOW-EFFECT (correct selection + spurious extra key options[99]=99): exit 2 (does not verify — no-spurious-key clause). atk_5.py UNGROUNDED-ORACLE ECHO (store default_secondary in the primary branch): exit 2. Direct verify: FAILED 37.9s, fails priority-primary postcondition (line 131). atk_6.py NO-OP (pass; never establishes default): exit 2 (does not verify — priority clauses). atk_7.py ESTABLISH-WHEN-NONE (add key even when no test fires): exit 2 (does not verify — final not-in-options clause). All 7 same-spec WRONG impls were REJECTED by the verifier. None is a verifying counterexample, so there is no wrong-verifying-impl patch to run through the harness.

POSITIVE CONTROL pos_control.py: structurally DIFFERENT correct impl (local `chosen`/`found` vars, single guarded assignment point). `adversary weakness` => exit 0 CANDIDATE (shares spec AND verifies). Per protocol I materialized its faithful refined patch (pos_control.patch — same guarded structure: compute widget into a local, assign only if not None) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-12713', patch) => RESOLVED=True COMPLETED=True NOTE='resolved' (out: pos_control.resolve.out). The only verifying same-spec impl is behaviorally correct AND its patch resolves — no verify=>correct gap.

REFINEMENT.md AUDIT: All legs R / A-reference / I; NO kind-3, NO consumed axiom. axioms region empty (docstring + mapping.md §3 consistent: changed op composed of Python primitives dict `in` / `[]=`, modeled deeply). A1/A1' R (str-kwargs<->Dict[int,int]; 'widget'<->key_component()==0; widget objs<->int codes 1/2/3; component_present = spec-only ENTRY capture). A2 R+I (membership guard). A3-A6 R (str-set-membership<->bool test_*, widget ctor<->identity code, dict `[]=` identical). B1 A-reference: deep model == real dict primitives, discharged by G-AX. axiom_check.py run => exit 0 (`G-AX OK` over 7 boundary x 8 flag + F2P + 20000 fuzz), and it faithfully reproduces the gold patch's exact control flow (`if 'widget' not in kwargs:` -> autocomplete>raw_id>filter chain), matching patch.diff. A-reference correspondence to the real callee holds.

VERDICT: SOUND. >=5 distinct wrong impls (7) run through `adversary weakness`, all rejected; the sole verifying candidate (positive control) is correct and its faithful patch resolves under the official harness. No verifying wrong impl exists, so nothing breaks verify=>correct.

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
"""Twin-artifact model for django__django-12713.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration step assembles a mapping of keyword options that build a form
  field for a multi-valued relation. Those options may already carry an explicit
  presentation component supplied by the caller. The step also has a default
  presentation component it would otherwise pick, chosen from the relation's
  name by a priority order among three name-membership tests: the primary test
  has highest priority, then the secondary, then the tertiary; if the name
  satisfies none of them no default is chosen.

  The single behaviour pinned here is the precedence between the caller's
  explicit component and the name-derived default:

  (1) When the options already carry an explicit presentation component, that
      component is left exactly as the caller supplied it -- no name-derived
      default is allowed to replace it -- regardless of which (if any) of the
      three name-membership tests the relation satisfies.

  (2) When the options do NOT carry an explicit presentation component, the
      name-derived default is established, selected by that priority order: the
      primary default if the name satisfies the primary test; else the secondary
      default if it satisfies the secondary test; else the tertiary default if
      it satisfies the tertiary test; else no component is established (the
      options still carry none).

  The consequence that matters: a caller who supplies an explicit presentation
  component keeps it even when the relation's name would otherwise select one of
  the three name-derived defaults. This mirrors the sibling configuration step
  for single-valued relations, which already honours a caller-supplied
  component.

Modelling choices (Nagini fragment):
  * The keyword options are a ``Dict[int, int]`` from an option-name token to a
    component-identity token; only membership of the presentation-component key
    and its value are observed, so integer identity is the faithful carrier
    (mapping.md §2). The presentation-component key is the module-level constant
    ``key_component()``.
  * Each of the three name-membership tests is a ``bool`` parameter (the result
    of testing the relation's name against the corresponding configured set);
    booleans need no permission. The three name-derived component identities are
    the module-level constants ``default_primary()`` / ``default_secondary()`` /
    ``default_tertiary()``.
  * Whether the options already carry the presentation component AT ENTRY is
    captured as a ``bool`` parameter ``component_present`` pinned by a
    precondition to the entry membership of ``key_component()``. This makes the
    default-selection guarantee gate on a genuine pre-state fact about the input
    rather than on a membership query against the (mutated-in-place) options,
    which would let an implementation discharge the guarantee vacuously by
    adding the key itself.

The options mapping is genuinely mutated in place, so it is held at FULL
permission and its exact post-state is stated (the pre-state membership/value of
each key is captured with ``Old`` and the entry presence of the presentation
component is captured by ``component_present``). No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (the precedence guard and the priority
chain are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *

# axioms-start
# No axioms: the precedence guard and the name-derived default selection are the
# behaviour under specification and are spelled out deeply in the impl region.
# There is no unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def key_component() -> int:
    # The option-name token for the presentation component.
    return 0

@Pure
def default_primary() -> int:
    # Component identity selected by the highest-priority name-membership test.
    return 1

@Pure
def default_secondary() -> int:
    # Component identity selected by the second-priority name-membership test.
    return 2

@Pure
def default_tertiary() -> int:
    # Component identity selected by the third-priority name-membership test.
    return 3
# pure-end

def select_component(options: Dict[int, int],
                     component_present: bool,
                     test_primary: bool,
                     test_secondary: bool,
                     test_tertiary: bool) -> None:
    # pre-conditions-start
    # The options mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(options)))
    # ``component_present`` captures, AT ENTRY, whether the options already carry
    # the presentation component. It is a pre-state fact about the input -- bound
    # before any mutation -- so the default-selection guarantee below can be
    # gated on the genuine entry membership rather than on a membership query
    # that an implementation could perturb by adding the key itself.
    Requires(component_present == (key_component() in options))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(options)))
    # (1) Every option present on entry is preserved exactly -- still present on
    #     exit with the same value. This is the precedence guarantee: a
    #     caller-supplied presentation component (the presentation key being
    #     present on entry) is left exactly as supplied, so no name-derived
    #     default replaces it, whatever the three membership tests say. The step
    #     touches only the presentation component, and only by ADDING it.
    Ensures(Forall(int, lambda k: (Implies(Old(k in options),
                                           (k in options) and options[k] == Old(options[k])))))
    # (2) When the options do NOT already carry the presentation component (i.e.
    #     it was absent at entry, ``not component_present``), the name-derived
    #     default is established by the priority order primary > secondary >
    #     tertiary; if no test matches, no component is established (the options
    #     still carry none). The antecedent is the captured ENTRY fact
    #     ``not component_present``, not a membership query on the (possibly
    #     mutated) options, so each implication has teeth: an implementation must
    #     store the priority-correct default, and only it.
    Ensures(Implies(not component_present and test_primary,
                    key_component() in options
                    and options[key_component()] == default_primary()))
    Ensures(Implies(not component_present and not test_primary and test_secondary,
                    key_component() in options
                    and options[key_component()] == default_secondary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and test_tertiary,
                    key_component() in options
                    and options[key_component()] == default_tertiary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and not test_tertiary,
                    not (key_component() in options)))
    # No option key other than the presentation component is added: any key
    # present on exit other than the presentation key must have been present on
    # entry. Stated forward (the entry-membership query is the consequent, not a
    # negated antecedent on a possibly-added key) so it constrains body-added
    # keys: an implementation that stores any spurious extra option cannot
    # verify.
    Ensures(Forall(int, lambda k: (Implies((k in options) and k != key_component(),
                                           Old(k in options)))))
    # post-conditions-end
    # impl-start
    if not (key_component() in options):
        chosen = 0
        found = False
        if test_primary:
            chosen = default_primary()
            found = True
        elif test_secondary:
            chosen = default_secondary()
            found = True
        elif test_tertiary:
            chosen = default_tertiary()
            found = True
        if found:
            options[key_component()] = chosen
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: model.py select_component is a TOTAL functional spec on the abstract domain. Both branches fully pin the post-state: (clause 1) preservation Forall k. Old(k in options) => k in options and options[k]==Old(options[k]); (no-spurious-key) Forall k. (k in options and k!=key_component()) => Old(k in options); (clause 2, gated on the ENTRY fact not component_present pinned by Requires(component_present == (key_component() in options))) the priority-ordered default selection primary>secondary>tertiary, and NO key added when no test fires. Because component_present is a pre-state Requires (not an Old-membership query on the mutated dict), the priority implications have teeth.

ATTACKS (all same-spec confirmed via `adversary same-spec`; impl region edited ONLY, axioms/@Pure/Requires/Ensures byte-identical). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12713 <f>.py`. Ran concurrently in batches of 3 (each spawns JVM+Z3). atk_1.py PREPATCH bug (drop presence guard, overwrite caller component): exit 2 NOT-A-COUNTEREXAMPLE (does not verify).

Direct verify: FAILED 41.9s, fails preservation postcondition (line 121) — spec senses the bug. prepatch_reproduced=true. atk_2.py PARTIAL-DOMAIN (only primary branch, drops secondary/tertiary): exit 2 (does not verify). atk_3.py WRONG-PRIORITY/boundary (secondary checked before primary): exit 2 (does not verify). atk_4.py CONTROL-FLOW-EFFECT (correct selection + spurious extra key options[99]=99): exit 2 (does not verify — no-spurious-key clause). atk_5.py UNGROUNDED-ORACLE ECHO (store default_secondary in the primary branch): exit 2. Direct verify: FAILED 37.9s, fails priority-primary postcondition (line 131). atk_6.py NO-OP (pass; never establishes default): exit 2 (does not verify — priority clauses). atk_7.py ESTABLISH-WHEN-NONE (add key even when no test fires): exit 2 (does not verify — final not-in-options clause). All 7 same-spec WRONG impls were REJECTED by the verifier. None is a verifying counterexample, so there is no wrong-verifying-impl patch to run through the harness.

POSITIVE CONTROL pos_control.py: structurally DIFFERENT correct impl (local `chosen`/`found` vars, single guarded assignment point). `adversary weakness` => exit 0 CANDIDATE (shares spec AND verifies). Per protocol I materialized its faithful refined patch (pos_control.patch — same guarded structure: compute widget into a local, assign only if not None) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-12713', patch) => RESOLVED=True COMPLETED=True NOTE='resolved' (out: pos_control.resolve.out). The only verifying same-spec impl is behaviorally correct AND its patch resolves — no verify=>correct gap.

REFINEMENT.md AUDIT: All legs R / A-reference / I; NO kind-3, NO consumed axiom. axioms region empty (docstring + mapping.md §3 consistent: changed op composed of Python primitives dict `in` / `[]=`, modeled deeply). A1/A1' R (str-kwargs<->Dict[int,int]; 'widget'<->key_component()==0; widget objs<->int codes 1/2/3; component_present = spec-only ENTRY capture). A2 R+I (membership guard). A3-A6 R (str-set-membership<->bool test_*, widget ctor<->identity code, dict `[]=` identical). B1 A-reference: deep model == real dict primitives, discharged by G-AX. axiom_check.py run => exit 0 (`G-AX OK` over 7 boundary x 8 flag + F2P + 20000 fuzz), and it faithfully reproduces the gold patch's exact control flow (`if 'widget' not in kwargs:` -> autocomplete>raw_id>filter chain), matching patch.diff. A-reference correspondence to the real callee holds.

VERDICT: SOUND. >=5 distinct wrong impls (7) run through `adversary weakness`, all rejected; the sole verifying candidate (positive control) is correct and its faithful patch resolves under the official harness. No verifying wrong impl exists, so nothing breaks verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12713 nagini bundle. The modeled function select_component (guard `if not (key_component() in options)` + priority chain primary>secondary>tertiary over Dict[int,int], with `component_present == (key_component() in options)` pinning the entry state) is byte-for-byte behaviorally equal to the gold-patched real callee ModelAdmin.formfield_for_manytomany widget-selection block at base_commit 5b884d45 (`if 'widget' not in kwargs:` wrapping autocomplete->raw_id->filter chain). Verified: (1) real code at base_commit inspected — matches model control flow 1:1 under the documented str-key<->int-key, widget-object<->identity-code, str-set-membership<->bool refinement; (2) axiom_check.py (G-AX) reproduces the real dict control flow and asserts every model postcondition across 7 boundary maps x 8 flag combos + F2P case + 20000 fuzz cases, exit 0; (3) independent 200000-input cross-check of ALL model postconditions (preservation of every entry key/value, no spurious key beyond presentation key, priority-ordered default established iff component absent at entry, caller component never overwritten) against the real control flow — all hold, no divergence; (4) model.py verifies under the pinned Nagini verifier (exit 0, 27.9s). The precondition `component_present == (key_component() in options)` is not a spurious strengthening: it is provably equal to the live entry-guard, and it prevents vacuous discharge. No input exists on which the spec disagrees with the real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen: hard_failures=[], no relaxation flag). Semantic review confirms no leak of the gold edit beyond the public problem_statement.

Public problem_statement: 'Allow overridding widget in formfield_for_manytomany(). It does not work when I set widget param... This is different from the formfield_for_foreignkey() function.' So the desired behavior (a caller-supplied widget must be honored) and the sibling comparison are ALREADY public.

Gold edit: wrap the widget-selection block in `if 'widget' not in kwargs:`.

Spec view assessment:
- The pinned precedence guarantee (a caller-supplied presentation component is left exactly as supplied and no name-derived default replaces it) is a faithful abstraction of exactly what the problem_statement asks ('allow overriding widget'). Specifying the desired outcome is not a leak — it is the public task.
- 'This mirrors the sibling configuration step for single-valued relations, which already honours a caller-supplied component' parallels the public 'different from formfield_for_foreignkey()'. No info beyond problem_statement.
- All repo specifics are abstracted away: Dict[int,int], key_component()==0, boolean tests, integer identity codes. The spec view contains NO patched file path (django/contrib/admin/options.py), NO 'widget'/'kwargs' literal, and NONE of the distinctive changed symbols (formfield_for_manytomany / formfield_for_foreignkey do not appear in the spec view — verified: only changed symbol is 'formfield_for_manytomany', absent).
- The 'priority order among three name-membership tests' describes pre-existing surrounding code that the gold patch does NOT change (the autocomplete/raw_id/filter chain); the sole edit is the guard. Describing unchanged context is not leaking the edit.
- No diff markers, no narration terms (bug/fix/patch/etc.), no module-path echo. Comments describe behavior, not the edit.

Conclusion: the spec view reveals nothing about the gold edit that is not already in the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).