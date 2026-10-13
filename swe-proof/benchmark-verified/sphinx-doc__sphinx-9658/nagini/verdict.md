# P2 adversarial audit — sphinx-doc__sphinx-9658

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,22 +109,8 @@
     Ensures(ToSeq(Result()) == ToSeq(short_name))
     # post-conditions-end
     # impl-start
+    # ATTACK: pre-patch bug — display identifier hard-set to empty string.
     result = []  # type: List[int]
-    i = 0
-    while i < len(short_name):
-        # invariants-start
-        Invariant(Acc(list_pred(short_name), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(short_name))
-        Invariant(ToSeq(result) == ToSeq(short_name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(short_name) - i.
-        Invariant(MustTerminate(len(short_name) - i))
-        # invariants-end
-        Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))
-        result = result + [short_name[i]]
-        i = i + 1
-    Assert(ToSeq(short_name).take(len(short_name)) == ToSeq(short_name))
     return result
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -71,22 +71,8 @@
     Ensures(ToSeq(Result()) == ToSeq(name))
     # post-conditions-end
     # impl-start
+    # ATTACK: pre-patch bug — short identifier not recorded (empty).
     result = []  # type: List[int]
-    i = 0
-    while i < len(name):
-        # invariants-start
-        Invariant(Acc(list_pred(name), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(name))
-        Invariant(ToSeq(result) == ToSeq(name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(name) - i.
-        Invariant(MustTerminate(len(name) - i))
-        # invariants-end
-        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
-        result = result + [name[i]]
-        i = i + 1
-    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
     return result
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -71,22 +71,18 @@
     Ensures(ToSeq(Result()) == ToSeq(name))
     # post-conditions-end
     # impl-start
+    # ATTACK: partial-domain — copies all but the final code point.
     result = []  # type: List[int]
     i = 0
-    while i < len(name):
+    while i < len(name) - 1:
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(name))
-        Invariant(ToSeq(result) == ToSeq(name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(name) - i.
         Invariant(MustTerminate(len(name) - i))
         # invariants-end
-        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
     return result
     # impl-end
 
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -109,6 +109,10 @@
     Ensures(ToSeq(Result()) == ToSeq(short_name))
     # post-conditions-end
     # impl-start
+    # ATTACK (echo): explicit empty special-case, else identity copy.
+    if len(short_name) == 0:
+        empty = []  # type: List[int]
+        return empty
     result = []  # type: List[int]
     i = 0
     while i < len(short_name):
@@ -117,8 +121,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(short_name))
         Invariant(ToSeq(result) == ToSeq(short_name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(short_name) - i.
         Invariant(MustTerminate(len(short_name) - i))
         # invariants-end
         Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,6 +71,7 @@
     Ensures(ToSeq(Result()) == ToSeq(name))
     # post-conditions-end
     # impl-start
+    # ATTACK (echo): build via copy, then append+pop a sentinel (net identity).
     result = []  # type: List[int]
     i = 0
     while i < len(name):
@@ -79,14 +80,15 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(name) - i.
         Invariant(MustTerminate(len(name) - i))
         # invariants-end
         Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
     Assert(ToSeq(name).take(len(name)) == ToSeq(name))
+    result = result + [46]
+    result = result[:len(result) - 1]
+    Assert(ToSeq(result) == ToSeq(name))
     return result
     # impl-end
 
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -154,21 +154,16 @@
     Ensures(Implies(len(name) > 0, len(Result()) > len(module) + 1))
     # post-conditions-end
     # impl-start
-    short = subclass_short_name(name)
-    display = placeholder_display_name(short)
+    # ATTACK (echo): compose directly, bypassing the two identifier helpers.
     result = []  # type: List[int]
     i = 0
     while i < len(module):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(Acc(list_pred(module), 1 / 2))
-        Invariant(Acc(list_pred(display)))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(module))
-        Invariant(ToSeq(display) == ToSeq(name))
         Invariant(ToSeq(result) == ToSeq(module).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(module) - i.
         Invariant(MustTerminate(len(module) - i))
         # invariants-end
         Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))
@@ -176,6 +171,19 @@
         i = i + 1
     Assert(ToSeq(module).take(len(module)) == ToSeq(module))
     result = result + [46]
-    result = result + display
+    j = 0
+    while j < len(name):
+        # invariants-start
+        Invariant(Acc(list_pred(name), 1 / 2))
+        Invariant(Acc(list_pred(module), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= len(name))
+        Invariant(ToSeq(result) == ToSeq(module) + dot() + ToSeq(name).take(j))
+        Invariant(MustTerminate(len(name) - j))
+        # invariants-end
+        Assert(ToSeq(name).take(j + 1).drop(j) == PSeq(name[j]))
+        result = result + [name[j]]
+        j = j + 1
+    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,6 +109,7 @@
     Ensures(ToSeq(Result()) == ToSeq(short_name))
     # post-conditions-end
     # impl-start
+    # ATTACK: appends a spurious trailing dot to the display identifier.
     result = []  # type: List[int]
     i = 0
     while i < len(short_name):
@@ -117,14 +118,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(short_name))
         Invariant(ToSeq(result) == ToSeq(short_name).take(i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(short_name) - i.
         Invariant(MustTerminate(len(short_name) - i))
         # invariants-end
-        Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))
         result = result + [short_name[i]]
         i = i + 1
-    Assert(ToSeq(short_name).take(len(short_name)) == ToSeq(short_name))
+    result = result + [46]
     return result
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9658.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an attribute reached through a
  stand-in package carries two derived identifiers used by the documentation
  renderer:

    * the placeholder's SHORT identifier, which is the very attribute name it
      was reached by (e.g. the attribute reached as ``Class`` has short
      identifier ``Class``); and
    * the placeholder's DISPLAY identifier (its qualified name), which the
      renderer reads to compose a cross-reference.

  The required behaviour is that the display identifier of such a placeholder is
  its short identifier — i.e. the attribute name — NOT an empty string. The
  renderer composes the fully-qualified reference by joining the owning module
  path and the display identifier with a dot. Consequently, for a placeholder
  reached by a non-empty attribute name, the rendered reference ends in that
  attribute name (``<module>.<name>``) and never degenerates to a dangling
  ``<module>.`` with the trailing component dropped.

Identifiers are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]`` via
``ToSeq``. The renderer's dotted join is an unchanged operation, spelled out
deeply as the pure function ``render_qualified`` (a structural concatenation),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    """The single-code-point separator ``.`` (U+002E)."""
    return PSeq(46)


@Pure
def render_qualified(module: PSeq[int], display: PSeq[int]) -> PSeq[int]:
    """The renderer's dotted join: the owning module path, a dot, then the
    placeholder's display identifier. This is the unchanged consuming operation
    (the documentation renderer reading the module path and the display
    identifier), spelled out structurally rather than axiomatized."""
    return module + dot() + display
# pure-end


def subclass_short_name(name: List[int]) -> List[int]:
    # pre-conditions-start
    # The attribute name by which the placeholder was reached (read-only).
    Requires(Acc(list_pred(name), 1 / 2))
    # The short identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's SHORT identifier is exactly the attribute name it was
    # reached by.
    Ensures(ToSeq(Result()) == ToSeq(name))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(name):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(name) - i.
        Invariant(MustTerminate(len(name) - i))
        # invariants-end
        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end


def placeholder_display_name(short_name: List[int]) -> List[int]:
    # pre-conditions-start
    # The placeholder's short identifier (its attribute name); read-only.
    Requires(Acc(list_pred(short_name), 1 / 2))
    # The display identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(short_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's DISPLAY identifier (the qualified name the renderer
    # reads) is its short identifier -- the attribute name -- not an empty
    # string.
    Ensures(ToSeq(Result()) == ToSeq(short_name))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(short_name):
        # invariants-start
        Invariant(Acc(list_pred(short_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(short_name))
        Invariant(ToSeq(result) == ToSeq(short_name).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(short_name) - i.
        Invariant(MustTerminate(len(short_name) - i))
        # invariants-end
        Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))
        result = result + [short_name[i]]
        i = i + 1
    Assert(ToSeq(short_name).take(len(short_name)) == ToSeq(short_name))
    return result
    # impl-end


def qualified_reference(name: List[int], module: List[int]) -> List[int]:
    # pre-conditions-start
    # `name`   : the attribute name by which the placeholder was reached.
    # `module` : the owning module path the placeholder belongs to.
    # Both read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The rendered reference must actually be delivered in finite time; the
    # measure leaves room to invoke the two identifier helpers (each of which
    # carries a smaller obligation).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fully-qualified reference is the module path, a dot, and the
    # attribute name -- the trailing component is the attribute name itself, so
    # for a non-empty name the reference never degenerates to a dangling
    # `<module>.`.
    Ensures(ToSeq(Result()) == render_qualified(ToSeq(module), ToSeq(name)))
    Ensures(ToSeq(Result()) == ToSeq(module) + dot() + ToSeq(name))
    Ensures(Implies(len(name) > 0, len(Result()) > len(module) + 1))
    # post-conditions-end
    # impl-start
    short = subclass_short_name(name)
    display = placeholder_display_name(short)
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(display)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(display) == ToSeq(name))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(module) - i.
        Invariant(MustTerminate(len(module) - i))
        # invariants-end
        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))
        result = result + [module[i]]
        i = i + 1
    Assert(ToSeq(module).take(len(module)) == ToSeq(module))
    result = result + [46]
    result = result + display
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; ran adversary via python -m swebench_unified.adversary with SBU_BENCHMARK_DIR=benchmark-verified,. All attacks built by copying the bundle model.py and editing ONLY impl regions; all 8 confirmed same-spec (adversary same-spec exit 0).

SPEC SHAPE: each of the 3 modeled functions pins its output by an EXACT sequence-equality postcondition (subclass_short_name: ToSeq(Result())==ToSeq(name); placeholder_display_name: ==ToSeq(short_name); qualified_reference: ==render_qualified(module,name)==module+'.'+name, plus Implies(len(name)>0, len(Result())>len(module)+1)) and Requires(MustTerminate). This is a tight functional spec, so wrong-VALUE impls must be rejected and value-correct impls are behavioural echoes of gold.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9658 <path>):
- atk_1.py PREPATCH DISPLAY BUG (placeholder_display_name returns empty): exit 2, verification failed — REJECTED (good). Reproduces the prepatch display bug modeled by model_prepatch.py.
- atk_2.py PREPATCH SHORT BUG (subclass_short_name returns empty): exit 2, verification failed — REJECTED (good). Reproduces the prepatch short-id bug modeled by model_prepatch_2.py. => prepatch_reproduced=true.
- atk_3.py PARTIAL-DOMAIN (subclass_short_name drops final code point, value=name.take(len-1)): exit 2, verification failed — REJECTED (good).
- atk_7.py BOUNDARY/WRONG-VALUE (placeholder_display_name appends spurious trailing '.', value=short_name+'.'): exit 2, verification failed — REJECTED (good).
- atk_4.py BOUNDARY echo (placeholder_display_name: explicit empty special-case then identity copy; net value == short_name): exit 0 CANDIDATE (verifies, 18.7s).
- atk_5.py CONTROL-FLOW-EFFECT echo (subclass_short_name: copy then append+pop sentinel, net identity == name): exit 0 CANDIDATE (verifies, 18.1s).
- atk_6.py UNGROUNDED-ORACLE echo (qualified_reference composes module+'.'+name DIRECTLY, bypassing both helpers; value identical): exit 0 CANDIDATE (verifies, 19.2s).
- atk_pc.py POSITIVE CONTROL (verbatim gold model impl): exit 0, verifies (18.0s) — confirms the correct impl is admitted.

RESOLVE (mandatory for every CANDIDATE): each of atk_4/atk_5/atk_6 is value-identical to gold on all inputs (spec pins exact sequence value). Their faithful refinements are all the gold patch: atk_4's empty special-case == self.__qualname__=self.__name__ (__name__ default is ''); atk_5's append+pop net-identity == attrs['__name__']=name; atk_6 leaves the two CHANGED sites (the helpers) at gold and only re-expresses qualified_reference, which maps to the UNCHANGED renderer restify, so the patch is gold verbatim. Materialized the shared faithful patch to faithful_gold.patch and EXECUTED run_resolve('sphinx-doc__sphinx-9658', patch) via swebench_unified.harness (run_id sbu-audit-eq-atk-faithful): RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. F2P test_restify_mock flips to pass. => No verifying wrong impl has a non-resolving faithful patch.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), B1(R+I), B2(R+I), C1(R+I), C2(R+I), C3(A-reference). §D confirms NO kind-3 (unexpressible-changed-op) and NO A-consumed axiom (axioms region empty, no @ContractOnly). The single A-leg C3 (render_qualified deep model of the unchanged restify dotted join) is validated == the real callee chain by axiom_check.py (G-AX): builds real placeholders via sphinx.ext.autodoc.mock.mock, reads real __qualname__/__module__, runs real restify/stringify over the F2P input plus 204 randomized identifier chains, and pins the pre/post discriminator (base: empty __qualname__ -> dangling '<module>.'; gold: '<module>.<name>'; stringify P2P-invariant). A-reference correspondence to the real callees holds.

CONCLUSION: The spec rejects every value-wrong impl (prepatch-display, prepatch-short, partial-domain, boundary extra-dot), admits only value-correct impls, and every verifying candidate's materialized faithful patch RESOLVES under the official harness. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9658.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an attribute reached through a
  stand-in package carries two derived identifiers used by the documentation
  renderer:

    * the placeholder's SHORT identifier, which is the very attribute name it
      was reached by (e.g. the attribute reached as ``Class`` has short
      identifier ``Class``); and
    * the placeholder's DISPLAY identifier (its qualified name), which the
      renderer reads to compose a cross-reference.

  The required behaviour is that the display identifier of such a placeholder is
  its short identifier — i.e. the attribute name — NOT an empty string. The
  renderer composes the fully-qualified reference by joining the owning module
  path and the display identifier with a dot. Consequently, for a placeholder
  reached by a non-empty attribute name, the rendered reference ends in that
  attribute name (``<module>.<name>``) and never degenerates to a dangling
  ``<module>.`` with the trailing component dropped.

Identifiers are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]`` via
``ToSeq``. The renderer's dotted join is an unchanged operation, spelled out
deeply as the pure function ``render_qualified`` (a structural concatenation),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    """The single-code-point separator ``.`` (U+002E)."""
    return PSeq(46)


@Pure
def render_qualified(module: PSeq[int], display: PSeq[int]) -> PSeq[int]:
    """The renderer's dotted join: the owning module path, a dot, then the
    placeholder's display identifier. This is the unchanged consuming operation
    (the documentation renderer reading the module path and the display
    identifier), spelled out structurally rather than axiomatized."""
    return module + dot() + display
# pure-end


def subclass_short_name(name: List[int]) -> List[int]:
    # pre-conditions-start
    # The attribute name by which the placeholder was reached (read-only).
    Requires(Acc(list_pred(name), 1 / 2))
    # The short identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's SHORT identifier is exactly the attribute name it was
    # reached by.
    Ensures(ToSeq(Result()) == ToSeq(name))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(name):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(name) - i.
        Invariant(MustTerminate(len(name) - i))
        # invariants-end
        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end


def placeholder_display_name(short_name: List[int]) -> List[int]:
    # pre-conditions-start
    # The placeholder's short identifier (its attribute name); read-only.
    Requires(Acc(list_pred(short_name), 1 / 2))
    # The display identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(short_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's DISPLAY identifier (the qualified name the renderer
    # reads) is its short identifier -- the attribute name -- not an empty
    # string.
    Ensures(ToSeq(Result()) == ToSeq(short_name))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(short_name):
        # invariants-start
        Invariant(Acc(list_pred(short_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(short_name))
        Invariant(ToSeq(result) == ToSeq(short_name).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(short_name) - i.
        Invariant(MustTerminate(len(short_name) - i))
        # invariants-end
        Assert(ToSeq(short_name).take(i + 1).drop(i) == PSeq(short_name[i]))
        result = result + [short_name[i]]
        i = i + 1
    Assert(ToSeq(short_name).take(len(short_name)) == ToSeq(short_name))
    return result
    # impl-end


def qualified_reference(name: List[int], module: List[int]) -> List[int]:
    # pre-conditions-start
    # `name`   : the attribute name by which the placeholder was reached.
    # `module` : the owning module path the placeholder belongs to.
    # Both read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The rendered reference must actually be delivered in finite time; the
    # measure leaves room to invoke the two identifier helpers (each of which
    # carries a smaller obligation).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fully-qualified reference is the module path, a dot, and the
    # attribute name -- the trailing component is the attribute name itself, so
    # for a non-empty name the reference never degenerates to a dangling
    # `<module>.`.
    Ensures(ToSeq(Result()) == render_qualified(ToSeq(module), ToSeq(name)))
    Ensures(ToSeq(Result()) == ToSeq(module) + dot() + ToSeq(name))
    Ensures(Implies(len(name) > 0, len(Result()) > len(module) + 1))
    # post-conditions-end
    # impl-start
    short = subclass_short_name(name)
    display = placeholder_display_name(short)
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(display)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(display) == ToSeq(name))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(module) - i.
        Invariant(MustTerminate(len(module) - i))
        # invariants-end
        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))
        result = result + [module[i]]
        i = i + 1
    Assert(ToSeq(module).take(len(module)) == ToSeq(module))
    result = result + [46]
    result = result + display
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; ran adversary via python -m swebench_unified.adversary with SBU_BENCHMARK_DIR=benchmark-verified,. All attacks built by copying the bundle model.py and editing ONLY impl regions; all 8 confirmed same-spec (adversary same-spec exit 0).

SPEC SHAPE: each of the 3 modeled functions pins its output by an EXACT sequence-equality postcondition (subclass_short_name: ToSeq(Result())==ToSeq(name); placeholder_display_name: ==ToSeq(short_name); qualified_reference: ==render_qualified(module,name)==module+'.'+name, plus Implies(len(name)>0, len(Result())>len(module)+1)) and Requires(MustTerminate). This is a tight functional spec, so wrong-VALUE impls must be rejected and value-correct impls are behavioural echoes of gold.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9658 <path>):
- atk_1.py PREPATCH DISPLAY BUG (placeholder_display_name returns empty): exit 2, verification failed — REJECTED (good). Reproduces the prepatch display bug modeled by model_prepatch.py.
- atk_2.py PREPATCH SHORT BUG (subclass_short_name returns empty): exit 2, verification failed — REJECTED (good). Reproduces the prepatch short-id bug modeled by model_prepatch_2.py. => prepatch_reproduced=true.
- atk_3.py PARTIAL-DOMAIN (subclass_short_name drops final code point, value=name.take(len-1)): exit 2, verification failed — REJECTED (good).
- atk_7.py BOUNDARY/WRONG-VALUE (placeholder_display_name appends spurious trailing '.', value=short_name+'.'): exit 2, verification failed — REJECTED (good).
- atk_4.py BOUNDARY echo (placeholder_display_name: explicit empty special-case then identity copy; net value == short_name): exit 0 CANDIDATE (verifies, 18.7s).
- atk_5.py CONTROL-FLOW-EFFECT echo (subclass_short_name: copy then append+pop sentinel, net identity == name): exit 0 CANDIDATE (verifies, 18.1s).
- atk_6.py UNGROUNDED-ORACLE echo (qualified_reference composes module+'.'+name DIRECTLY, bypassing both helpers; value identical): exit 0 CANDIDATE (verifies, 19.2s).
- atk_pc.py POSITIVE CONTROL (verbatim gold model impl): exit 0, verifies (18.0s) — confirms the correct impl is admitted.

RESOLVE (mandatory for every CANDIDATE): each of atk_4/atk_5/atk_6 is value-identical to gold on all inputs (spec pins exact sequence value). Their faithful refinements are all the gold patch: atk_4's empty special-case == self.__qualname__=self.__name__ (__name__ default is ''); atk_5's append+pop net-identity == attrs['__name__']=name; atk_6 leaves the two CHANGED sites (the helpers) at gold and only re-expresses qualified_reference, which maps to the UNCHANGED renderer restify, so the patch is gold verbatim. Materialized the shared faithful patch to faithful_gold.patch and EXECUTED run_resolve('sphinx-doc__sphinx-9658', patch) via swebench_unified.harness (run_id sbu-audit-eq-atk-faithful): RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. F2P test_restify_mock flips to pass. => No verifying wrong impl has a non-resolving faithful patch.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), B1(R+I), B2(R+I), C1(R+I), C2(R+I), C3(A-reference). §D confirms NO kind-3 (unexpressible-changed-op) and NO A-consumed axiom (axioms region empty, no @ContractOnly). The single A-leg C3 (render_qualified deep model of the unchanged restify dotted join) is validated == the real callee chain by axiom_check.py (G-AX): builds real placeholders via sphinx.ext.autodoc.mock.mock, reads real __qualname__/__module__, runs real restify/stringify over the F2P input plus 204 randomized identifier chains, and pins the pre/post discriminator (base: empty __qualname__ -> dangling '<module>.'; gold: '<module>.<name>'; stringify P2P-invariant). A-reference correspondence to the real callees holds.

CONCLUSION: The spec rejects every value-wrong impl (prepatch-display, prepatch-short, partial-domain, boundary extra-dot), admits only value-correct impls, and every verifying candidate's materialized faithful patch RESOLVES under the official harness. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness assessment for the nagini twin-artifact model of sphinx-doc__sphinx-9658 vs the real repo at base_commit 232dbe41 (patched worktree, run with py3.8 sphinx importable).

Modeled functions and their real counterparts:
- subclass_short_name(name) => returns name. Real _make_subclass records attrs['__name__']=name (gold hunk 3). Match: __name__==name.
- placeholder_display_name(short) => returns short. Real _MockObject.__init__ sets self.__qualname__=self.__name__ (gold hunk 2). Match: __qualname__==__name__.
- qualified_reference(name,module) => module + '.' + name (List[int]/PSeq code-point carrier; '.'==[46]). Real F2P renderer restify -> _restify_py37 takes the `hasattr(cls,'__qualname__')` non-typing branch for a mock placeholder and composes ':class:`%s.%s`' % (obj.__module__, obj.__qualname__) = module + '.' + name.

Empirical check: reproduced the real placeholder for the F2P input unknown.secret.Class -> module='unknown.secret', name='Class', qualname='Class', restify=':class:`unknown.secret.Class`', stringify='unknown.secret.Class' — exactly the model's module.name. Then a randomized probe of 3000 identifier chains (depth 1-4, seed 9658) over the real mock+restify: 0 violations of (qualname==name AND restify inner == module.name). The model's postconditions (ToSeq(Result())==ToSeq(module)+dot+ToSeq(name), and Implies(len(name)>0, len(Result())>len(module)+1)) hold for every real input in the modeled domain (placeholders produced by mock attribute access).

Spec-strength check: the postconditions are not stronger than reality. The restify branches that would diverge from module.qualname (builtins/__builtin__ module, generic-alias, NewType, Union, ForwardRef) are unreachable for mock placeholders reached via __getattr__/__getitem__ (they always carry a real __qualname__ and are ordinary types), so pinning restify == module.name over that domain is faithful, and it is exactly what G-AX/axiom_check.py validates in-container on both testbeds (base_commit fix_present=False dangling, gold fix_present=True; 204 cases, 0 violations). MustTerminate obligations match the real straight-line attribute stores + bounded join. model.py verifies (Verification successful, 11.73s). No diverging input found; the modeled function agrees with the real callee chain on all tested inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py spec regions) states only the desired behavior already public in the problem_statement: a mocked-attribute placeholder's rendered fully-qualified reference must end in the attribute name (<module>.<name>) and never degenerate to a dangling <module>. — exactly the issue's 'Bases should report torch.nn.Module not torch.nn.' Nothing in the spec view discloses the gold edit beyond that public behavior: the patched repo symbols (_MockObject, _make_subclass), the patched attribute names (__name__, __qualname__), and the patched file path (sphinx/ext/autodoc/mock.py) do NOT appear in the spec view; the model uses independent names (subclass_short_name, placeholder_display_name, qualified_reference, render_qualified). The edit-localizing detail (which attributes are set in which callee) lives only in mapping.md/refinement.md, which are audit artifacts, not the consumer spec view. No diff markers, no verbatim gold-patch lines, no bug/fix narration. Mechanical G-LEAK screen returns passed=True with zero hard failures; no RELAXED_LEAKAGE.md and meta relaxed_leakage is unset, so the lexical pass is authoritative here. Confirmed impl regions are elided and only the abstract behavioral postconditions (ToSeq(Result())==ToSeq(name); Result==module+.+name; Implies(len(name)>0, len(Result())>len(module)+1)) are visible — these restate the public expected behavior, not the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
