# P2 adversarial audit — django__django-16899

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
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -139,18 +137,13 @@
     if resolves:
         ok = []  # type: List[int]
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [6]          # old combined prose, NO value interpolated
+    result = result + cls
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -139,18 +137,15 @@
     if resolves:
         ok = []  # type: List[int]
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [2]
+    result = result + cls          # WRONG: class in the value slot
+    result = result + [3]
+    result = result + value        # WRONG: value in the class slot
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -136,21 +134,15 @@
                     .take(len(value)) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    if resolves:
-        ok = []  # type: List[int]
-        return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [2]
+    result = result + value
+    result = result + [3]
+    result = result + cls
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -137,20 +135,17 @@
     # post-conditions-end
     # impl-start
     if resolves:
-        ok = []  # type: List[int]
+        ok = [1]  # type: List[int]   # WRONG: non-empty on resolve
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [2]
+    result = result + value
+    result = result + [3]
+    result = result + cls
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -139,18 +137,14 @@
     if resolves:
         ok = []  # type: List[int]
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [2]
+    result = result + [3]          # value dropped
+    result = result + cls
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -139,18 +137,6 @@
     if resolves:
         ok = []  # type: List[int]
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
-    result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = [1, 2, 3, 4, 5]  # type: List[int]   # constant, ignores carriers
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -139,18 +137,16 @@
     if resolves:
         ok = []  # type: List[int]
         return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
     result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+    result = result + [1]
+    result = result + label
+    result = result + [2]
+    result = result + value
+    result = result + value        # WRONG: value duplicated
+    result = result + [3]
+    result = result + cls
+    result = result + [4]
+    result = result + model_label
+    result = result + [5]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(value), 1 / 2))
     Requires(Acc(list_pred(cls), 1 / 2))
     Requires(Acc(list_pred(model_label), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(label), 1 / 2))
@@ -137,20 +135,8 @@
     # post-conditions-end
     # impl-start
     if resolves:
-        ok = []  # type: List[int]
-        return ok
-    # Build "The value of '%s' refers to '%s', which is not a callable, an
-    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
-    # model_label) as a code-point list (constant prose modelled by markers).
-    result = []  # type: List[int]
-    result = result + [1]          # "The value of '"
-    result = result + label        # label
-    result = result + [2]          # "' refers to '"  (added value interpolation)
-    result = result + value        # value  (the offending reference, named)
-    result = result + [3]          # "', which is not a callable, an attribute of '"
-    result = result + cls          # class name
-    result = result + [4]          # "', or an attribute of '"
-    result = result + model_label  # model label
-    result = result + [5]          # "'."
+        return []
+    # correct sequence, built via a single expression (behaviourally == gold)
+    result = ([1] + label + [2] + value + [3] + cls + [4] + model_label + [5])  # type: List[int]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16899.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration option lists candidate field references by name. Each
  reference is validated: it is acceptable when it resolves (it is callable, or
  names an attribute on the administered configuration object, or names an
  attribute or declared field on the underlying model). When a reference does
  NOT resolve, the validator emits exactly one diagnostic; when it does
  resolve, it emits nothing.

  The diagnostic message must let the reader locate the offending reference
  precisely. It therefore reports BOTH:

    * the positional label of the entry (e.g. the indexed option slot), AND
    * the offending reference VALUE ITSELF,

  before explaining the three places that were searched (the configuration
  object's class, the model, the model's declared fields). Concretely the
  message is the constant prose with four interpolation points filled, in order,
  by: the label, then the offending reference value, then the configuration
  class name, then the model label. The reference value appears as its own
  interpolated segment -- quoted, immediately after the label -- so the message
  names the value at fault rather than only its position.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the message specification is carried by `PSeq[int]`. The four constant
prose segments of the template are modelled by distinct one-token markers
(`seg_*`); the four dynamic parts are the input carriers spliced in at their
interpolation points. The behaviour the issue and tests pin is the SHAPE of the
message -- which dynamic parts appear, in what order, with the offending value
present as its own segment after the label -- not the exact prose wording, so
the prose is abstracted to constant markers (refinement.md gives the segment <->
literal-text bijection). Whether a reference resolves is an UNCHANGED, opaque
set of attribute/field lookups, abstracted by a single boolean guard
(`resolves`); it is the only thing under change that the message names the
value. No callee is consumed as an axiom: the construction is modelled deeply
(concrete sequence concatenation).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The validated behaviour (the shape of the diagnostic
# message) is modelled deeply as concrete code-point-sequence concatenation.
# The opaque resolution lookups the validator performs are UNCHANGED by this
# behaviour and are abstracted by the boolean guard `resolves`; they are not
# consumed as an Ensures-bearing contract.
# axioms-end


# pure-start
@Pure
def seg_intro() -> PSeq[int]:
    # constant prose: "The value of '"
    return PSeq(1)


@Pure
def seg_refers() -> PSeq[int]:
    # constant prose: "' refers to '"  -- introduces the offending reference VALUE
    return PSeq(2)


@Pure
def seg_which_not() -> PSeq[int]:
    # constant prose: "', which is not a callable, an attribute of '"
    return PSeq(3)


@Pure
def seg_or_attr() -> PSeq[int]:
    # constant prose: "', or an attribute of '"
    return PSeq(4)


@Pure
def seg_end() -> PSeq[int]:
    # constant prose: "'."
    return PSeq(5)


@Pure
def diagnostic_message(label: PSeq[int], value: PSeq[int],
                       cls: PSeq[int], model_label: PSeq[int]) -> PSeq[int]:
    """The diagnostic message for a reference that does not resolve: the constant
    prose with the four interpolation points filled, in order, by the label,
    the offending reference value, the configuration class name, and the model
    label. The value is spliced in as its own quoted segment immediately after
    the label."""
    return (seg_intro() + label + seg_refers() + value + seg_which_not()
            + cls + seg_or_attr() + model_label + seg_end())
# pure-end


def check_reference(label: List[int], value: List[int],
                    cls: List[int], model_label: List[int],
                    resolves: bool) -> List[int]:
    # pre-conditions-start
    # All four message components are read-only inputs (fractional permission).
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Acc(list_pred(cls), 1 / 2))
    Requires(Acc(list_pred(model_label), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(cls), 1 / 2))
    Ensures(Acc(list_pred(model_label), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A resolving reference yields no diagnostic; a failing one yields exactly
    # one (the empty/non-empty result discriminates the two; the message always
    # begins with non-empty prose).
    Ensures(resolves == (len(Result()) == 0))
    # When a diagnostic is emitted it is exactly the constant prose with the four
    # dynamic parts spliced in at their interpolation points, IN ORDER:
    # label, then the offending reference value, then class, then model label.
    Ensures(Implies(not resolves,
                    ToSeq(Result()) == diagnostic_message(
                        ToSeq(label), ToSeq(value),
                        ToSeq(cls), ToSeq(model_label))))
    # Discriminating structural consequence: the offending reference VALUE
    # occurs in the message as a contiguous segment, at the offset that follows
    # the intro prose and the label (its own interpolated slot) -- the value is
    # named, not merely its position. A message that omits the value (placing
    # the class where the value belongs) cannot satisfy this.
    Ensures(Implies(not resolves,
                    ToSeq(Result()).drop(len(seg_intro()) + len(label)
                                         + len(seg_refers()))
                    .take(len(value)) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if resolves:
        ok = []  # type: List[int]
        return ok
    # Build "The value of '%s' refers to '%s', which is not a callable, an
    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
    # model_label) as a code-point list (constant prose modelled by markers).
    result = []  # type: List[int]
    result = result + [1]          # "The value of '"
    result = result + label        # label
    result = result + [2]          # "' refers to '"  (added value interpolation)
    result = result + value        # value  (the offending reference, named)
    result = result + [3]          # "', which is not a callable, an attribute of '"
    result = result + cls          # class name
    result = result + [4]          # "', or an attribute of '"
    result = result + model_label  # model label
    result = result + [5]          # "'."
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec (byte-identical spec, confirmed via `adversary same-spec` exit 0 on all) wrong/alt impls built by editing ONLY the impl region of model.py; each run through `python -m swebench_unified.adversary weakness nagini django__django-16899 <atk>` in ≤3-way parallel batches (JVM+Z3). ZERO CANDIDATEs — every attack returned exit 2 (does-not-verify), so there is NO verifying-wrong-impl and thus no faithful patch to materialize/resolve. patches={} accordingly.

Attack classes (all NOT-A-COUNTEREXAMPLE / verification failed):
- atk_1: prepatch bug — omits value, uses old combined-prose marker [6] (this is the recorded prepatch defect; reproduced=fail-to-verify, exactly as prepatch_models fails_on the equality postcondition).
- atk_2: boundary/swap — cls in the value slot, value in the class slot.
- atk_3: control-flow-effect — ignores the `resolves` guard, always emits the message (violates resolves==(len==0)).
- atk_4: partial-domain — returns non-empty [1] on the resolve path.
- atk_5: drops the value segment entirely (keeps marker [2][3]).
- atk_6: ungrounded-oracle echo — returns constant [1,2,3,4,5] ignoring carriers.
- atk_7: duplicates the value segment.
- atk_8: behaviourally-CORRECT alternative build (single-expression concat); also fails to verify — a Nagini completeness artifact (a correct impl the verifier can't discharge), NOT a soundness break, so it does not weaken the spec.

Why no slack exists: the error-path postcondition is a FULL SYMBOLIC EQUALITY `ToSeq(Result()) == diagnostic_message(ToSeq(label),ToSeq(value),ToSeq(cls),ToSeq(model_label))` combined with `resolves == (len(Result())==0)` and the value-position drop/take witness (B). Together these totally pin the output on both branches, leaving no room for a same-spec impl that verifies yet behaves differently.

A-leg audit (focus): axioms=[] (no consumed @ContractOnly callee). The single changed op — the message template — is modelled DEEPLY (diagnostic_message concatenation) and validated as an A-reference by axiom_check.py (G-AX), which PASSED: marker-expanded deep model == real Python %-formatting of the gold post-patch template on 9 boundary + 20000 fuzz inputs, value occupies its own interpolated segment, prepatch template omits value. Independent manual check: deep-model string == gold `%`-template == the actual F2P test-suite expected message (all True) for the SongAdmin case. refinement.md legs A1/A2/A4=R, A3=R+I, B=I — NO kind-3 leg; marker↔literal-prose bijection (mapping.md §2) is 1:1 and matches the gold hunk verbatim (confirmed against data/swe_bench_verified test.jsonl patch + test_patch). model↔patch correspondence holds.

Positive control (gold model.py) verifies: `nagini_verify.sh` exit 0, 13.79s. SBU_BENCHMARK_DIR=benchmark-verified, verifier env swebench-nagini-verifier.

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
"""Twin-artifact model for django__django-16899.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration option lists candidate field references by name. Each
  reference is validated: it is acceptable when it resolves (it is callable, or
  names an attribute on the administered configuration object, or names an
  attribute or declared field on the underlying model). When a reference does
  NOT resolve, the validator emits exactly one diagnostic; when it does
  resolve, it emits nothing.

  The diagnostic message must let the reader locate the offending reference
  precisely. It therefore reports BOTH:

    * the positional label of the entry (e.g. the indexed option slot), AND
    * the offending reference VALUE ITSELF,

  before explaining the three places that were searched (the configuration
  object's class, the model, the model's declared fields). Concretely the
  message is the constant prose with four interpolation points filled, in order,
  by: the label, then the offending reference value, then the configuration
  class name, then the model label. The reference value appears as its own
  interpolated segment -- quoted, immediately after the label -- so the message
  names the value at fault rather than only its position.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the message specification is carried by `PSeq[int]`. The four constant
prose segments of the template are modelled by distinct one-token markers
(`seg_*`); the four dynamic parts are the input carriers spliced in at their
interpolation points. The behaviour the issue and tests pin is the SHAPE of the
message -- which dynamic parts appear, in what order, with the offending value
present as its own segment after the label -- not the exact prose wording, so
the prose is abstracted to constant markers (refinement.md gives the segment <->
literal-text bijection). Whether a reference resolves is an UNCHANGED, opaque
set of attribute/field lookups, abstracted by a single boolean guard
(`resolves`); it is the only thing under change that the message names the
value. No callee is consumed as an axiom: the construction is modelled deeply
(concrete sequence concatenation).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The validated behaviour (the shape of the diagnostic
# message) is modelled deeply as concrete code-point-sequence concatenation.
# The opaque resolution lookups the validator performs are UNCHANGED by this
# behaviour and are abstracted by the boolean guard `resolves`; they are not
# consumed as an Ensures-bearing contract.
# axioms-end


# pure-start
@Pure
def seg_intro() -> PSeq[int]:
    # constant prose: "The value of '"
    return PSeq(1)


@Pure
def seg_refers() -> PSeq[int]:
    # constant prose: "' refers to '"  -- introduces the offending reference VALUE
    return PSeq(2)


@Pure
def seg_which_not() -> PSeq[int]:
    # constant prose: "', which is not a callable, an attribute of '"
    return PSeq(3)


@Pure
def seg_or_attr() -> PSeq[int]:
    # constant prose: "', or an attribute of '"
    return PSeq(4)


@Pure
def seg_end() -> PSeq[int]:
    # constant prose: "'."
    return PSeq(5)


@Pure
def diagnostic_message(label: PSeq[int], value: PSeq[int],
                       cls: PSeq[int], model_label: PSeq[int]) -> PSeq[int]:
    """The diagnostic message for a reference that does not resolve: the constant
    prose with the four interpolation points filled, in order, by the label,
    the offending reference value, the configuration class name, and the model
    label. The value is spliced in as its own quoted segment immediately after
    the label."""
    return (seg_intro() + label + seg_refers() + value + seg_which_not()
            + cls + seg_or_attr() + model_label + seg_end())
# pure-end


def check_reference(label: List[int], value: List[int],
                    cls: List[int], model_label: List[int],
                    resolves: bool) -> List[int]:
    # pre-conditions-start
    # All four message components are read-only inputs (fractional permission).
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Acc(list_pred(cls), 1 / 2))
    Requires(Acc(list_pred(model_label), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(cls), 1 / 2))
    Ensures(Acc(list_pred(model_label), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A resolving reference yields no diagnostic; a failing one yields exactly
    # one (the empty/non-empty result discriminates the two; the message always
    # begins with non-empty prose).
    Ensures(resolves == (len(Result()) == 0))
    # When a diagnostic is emitted it is exactly the constant prose with the four
    # dynamic parts spliced in at their interpolation points, IN ORDER:
    # label, then the offending reference value, then class, then model label.
    Ensures(Implies(not resolves,
                    ToSeq(Result()) == diagnostic_message(
                        ToSeq(label), ToSeq(value),
                        ToSeq(cls), ToSeq(model_label))))
    # Discriminating structural consequence: the offending reference VALUE
    # occurs in the message as a contiguous segment, at the offset that follows
    # the intro prose and the label (its own interpolated slot) -- the value is
    # named, not merely its position. A message that omits the value (placing
    # the class where the value belongs) cannot satisfy this.
    Ensures(Implies(not resolves,
                    ToSeq(Result()).drop(len(seg_intro()) + len(label)
                                         + len(seg_refers()))
                    .take(len(value)) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if resolves:
        ok = []  # type: List[int]
        return ok
    # Build "The value of '%s' refers to '%s', which is not a callable, an
    # attribute of '%s', or an attribute of '%s'." % (label, value, cls,
    # model_label) as a code-point list (constant prose modelled by markers).
    result = []  # type: List[int]
    result = result + [1]          # "The value of '"
    result = result + label        # label
    result = result + [2]          # "' refers to '"  (added value interpolation)
    result = result + value        # value  (the offending reference, named)
    result = result + [3]          # "', which is not a callable, an attribute of '"
    result = result + cls          # class name
    result = result + [4]          # "', or an attribute of '"
    result = result + model_label  # model label
    result = result + [5]          # "'."
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec (byte-identical spec, confirmed via `adversary same-spec` exit 0 on all) wrong/alt impls built by editing ONLY the impl region of model.py; each run through `python -m swebench_unified.adversary weakness nagini django__django-16899 <atk>` in ≤3-way parallel batches (JVM+Z3). ZERO CANDIDATEs — every attack returned exit 2 (does-not-verify), so there is NO verifying-wrong-impl and thus no faithful patch to materialize/resolve. patches={} accordingly.

Attack classes (all NOT-A-COUNTEREXAMPLE / verification failed):
- atk_1: prepatch bug — omits value, uses old combined-prose marker [6] (this is the recorded prepatch defect; reproduced=fail-to-verify, exactly as prepatch_models fails_on the equality postcondition).
- atk_2: boundary/swap — cls in the value slot, value in the class slot.
- atk_3: control-flow-effect — ignores the `resolves` guard, always emits the message (violates resolves==(len==0)).
- atk_4: partial-domain — returns non-empty [1] on the resolve path.
- atk_5: drops the value segment entirely (keeps marker [2][3]).
- atk_6: ungrounded-oracle echo — returns constant [1,2,3,4,5] ignoring carriers.
- atk_7: duplicates the value segment.
- atk_8: behaviourally-CORRECT alternative build (single-expression concat); also fails to verify — a Nagini completeness artifact (a correct impl the verifier can't discharge), NOT a soundness break, so it does not weaken the spec.

Why no slack exists: the error-path postcondition is a FULL SYMBOLIC EQUALITY `ToSeq(Result()) == diagnostic_message(ToSeq(label),ToSeq(value),ToSeq(cls),ToSeq(model_label))` combined with `resolves == (len(Result())==0)` and the value-position drop/take witness (B). Together these totally pin the output on both branches, leaving no room for a same-spec impl that verifies yet behaves differently.

A-leg audit (focus): axioms=[] (no consumed @ContractOnly callee). The single changed op — the message template — is modelled DEEPLY (diagnostic_message concatenation) and validated as an A-reference by axiom_check.py (G-AX), which PASSED: marker-expanded deep model == real Python %-formatting of the gold post-patch template on 9 boundary + 20000 fuzz inputs, value occupies its own interpolated segment, prepatch template omits value. Independent manual check: deep-model string == gold `%`-template == the actual F2P test-suite expected message (all True) for the SongAdmin case. refinement.md legs A1/A2/A4=R, A3=R+I, B=I — NO kind-3 leg; marker↔literal-prose bijection (mapping.md §2) is 1:1 and matches the gold hunk verbatim (confirmed against data/swe_bench_verified test.jsonl patch + test_patch). model↔patch correspondence holds.

Positive control (gold model.py) verifies: `nagini_verify.sh` exit 0, 13.79s. SBU_BENCHMARK_DIR=benchmark-verified, verifier env swebench-nagini-verifier.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed. The spec models the POST-PATCH behavior of django.contrib.admin.checks.BaseModelAdminChecks._check_readonly_fields_item error branch. The gold template 'The value of \'%s\' refers to \'%s\', which is not a callable, an attribute of \'%s\', or an attribute of \'%s\'.' % (label, field_name, cls, model_label) decomposes exactly into the model's five prose markers seg_intro..seg_end (PSeq(1..5)) and the four dynamic carriers (label, value, cls, model_label) in the correct interpolation order, with value spliced as its own segment immediately after the label. Evidence: (1) Nagini verifies model.py (Verification successful, 13.35s) — spec is non-vacuous. (2) Re-ran the bundle's conformance_check.py against the real repo with patch.diff applied at base_commit d3d173425f: 100152 inputs (152 boundary + 100000 fuzz, seed 16899), 0 disagreements — shadow impl output (marker-expanded) == real _check_readonly_fields_item(...)[0].msg, and empty/non-empty result matches the resolves guard (four unchanged lookups). (3) Direct spot-check on tricky inputs (percent-in-data 'c%sd', embedded apostrophes "l'ab"/'va%lue', non-ASCII 'é'/'•') all match byte-for-byte. No input exists where the modeled function disagrees with the real callee. The boolean `resolves` abstraction is sound: the patch does not touch the four resolution lookups, and the tested behavior depends only on the error-branch message shape. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file path django/contrib/admin/checks.py, no patched symbol _check_readonly_fields_item — spec uses neutral name check_reference; no bug/fix narration). Semantic judgment vs the SOLVER-VISIBLE problem_statement only (not hints): the gold edit is 'include the offending field's name in the readonly_fields error message.' The public problem_statement already states this directly: 'the current error message for the readonly_fields ... will not include the field's name ... It would be good if we can ... include the field name in the readonly_fields checks.' It even quotes the exact target shape from a sibling check — "The value of 'list_editable[0]' refers to 'original_release', which is not contained in 'list_display'." — publicly revealing the 'refers to <value>' pattern, and quotes the old message verbatim. The spec view (docstring + seg_* prose comments + postconditions) says the diagnostic must report the label AND the offending reference value as its own interpolated segment after the label. That is exactly the publicly-requested behavior; the seg_* comment prose mirrors text already in the problem_statement (both the old message and the refers-to pattern). The value-position Ensures merely formalizes 'name the value, not only the position,' which the task already asks for. No spec-view line reveals edit-localization beyond the public problem_statement. Verified spec region parses and screen returns passed=True; relaxed_leakage not set (clean pass, not a deferral).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
