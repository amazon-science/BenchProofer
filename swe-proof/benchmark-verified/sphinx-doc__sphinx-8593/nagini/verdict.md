# P2 adversarial audit — sphinx-doc__sphinx-8593

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -114,10 +112,7 @@
     Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
     # post-conditions-end
     # impl-start
-    if len(attr_doc) > 0:
-        result = list(attr_doc)  # type: List[int]
-    else:
-        result = list(value_doc)
+    result = list(value_doc)  # type: List[int]
     return result
     # impl-end
 
@@ -140,7 +135,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -162,8 +159,7 @@
         Result()))
     # post-conditions-end
     # impl-start
-    doc = member_effective_doc(attr_doc, value_doc)
-    private = is_private(name_underscored, ToSeq(doc))
+    private = is_private(name_underscored, ToSeq(value_doc))
     if not want_all:
         keep = True
     elif not private:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -114,7 +112,7 @@
     Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
     # post-conditions-end
     # impl-start
-    if len(attr_doc) > 0:
+    if len(attr_doc) >= 0:
         result = list(attr_doc)  # type: List[int]
     else:
         result = list(value_doc)
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -164,11 +161,6 @@
     # impl-start
     doc = member_effective_doc(attr_doc, value_doc)
     private = is_private(name_underscored, ToSeq(doc))
-    if not want_all:
-        keep = True
-    elif not private:
-        keep = True
-    else:
-        keep = in_private_selection(private_mode, name_selected)
+    keep = True
     return keep
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -169,6 +166,6 @@
     elif not private:
         keep = True
     else:
-        keep = in_private_selection(private_mode, name_selected)
+        keep = in_private_selection(private_mode, not name_selected)
     return keep
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -164,7 +161,7 @@
     # impl-start
     doc = member_effective_doc(attr_doc, value_doc)
     private = is_private(name_underscored, ToSeq(doc))
-    if not want_all:
+    if want_all:
         keep = True
     elif not private:
         keep = True
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -163,12 +160,8 @@
     # post-conditions-end
     # impl-start
     doc = member_effective_doc(attr_doc, value_doc)
-    private = is_private(name_underscored, ToSeq(doc))
-    if not want_all:
-        keep = True
-    elif not private:
-        keep = True
-    else:
-        keep = in_private_selection(private_mode, name_selected)
+    keep = ((not want_all) or
+            (not is_private(name_underscored, ToSeq(doc))) or
+            in_private_selection(private_mode, name_selected))
     return keep
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -103,7 +102,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(attr_doc), 1 / 2))
     Requires(Acc(list_pred(value_doc), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
@@ -114,7 +112,7 @@
     Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
     # post-conditions-end
     # impl-start
-    if len(attr_doc) > 0:
+    if len(attr_doc) > 1:
         result = list(attr_doc)  # type: List[int]
     else:
         result = list(value_doc)
@@ -140,7 +138,6 @@
     # separate, unmodeled retention branch that runs before the modeled one,
     # and lies outside this boundary.
     Requires(not name_special)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(attr_doc), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8593.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documenter collects the members of a target module, each member's
  effective documentation is the inline attribute documentation recorded for
  that name in the module source (when such documentation exists), falling back
  to the value's own intrinsic documentation only when no attribute
  documentation is present. The visibility classification of a member is then
  derived from THAT effective documentation: a member is treated as public when
  its documentation carries the explicit "public" visibility marker, private
  when it carries the explicit "private" marker, and otherwise according to the
  leading-underscore naming convention. A member whose effective documentation
  marks it public is therefore retained even when its name begins with an
  underscore.

This bundle models two cooperating behaviours:

  (1) the effective documentation chosen for a module member (the attribute
      documentation takes precedence over the value's intrinsic documentation),
      and

  (2) the retention decision for a documented module member under the
      "all members" mode, given the visibility classification derived from (1)
      and the private-members selection mode.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried by `PSeq[int]` via `ToSeq`. The
visibility classifier of a documentation block (the unchanged community
metadata extractor) is axiomatized as `meta_class`; provenance and an
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Visibility classification of a documentation block (a community metadata
# extractor reads its explicit visibility marker):
#   0 = no explicit visibility marker
#   1 = explicit "public"  marker present
#   2 = explicit "private" marker present
# A pure total function of the documentation text. G-AX checks it against the
# real extractor.
NONE = 0  # type: int
PUBLIC = 1  # type: int
PRIVATE = 2  # type: int

@Pure
@ContractOnly
def meta_class(doc: PSeq[int]) -> int:
    Requires(True)
    Ensures(Result() == NONE or Result() == PUBLIC or Result() == PRIVATE)
    # The empty documentation block carries no marker.
    Ensures(Implies(len(doc) == 0, Result() == NONE))
# axioms-end

# pure-start
@Pure
def effective_doc(attr_doc: PSeq[int], value_doc: PSeq[int]) -> PSeq[int]:
    """The documentation that drives the visibility classification of a module
    member: the inline attribute documentation when it is non-empty, otherwise
    the value's own intrinsic documentation."""
    if len(attr_doc) > 0:
        return attr_doc
    return value_doc

@Pure
def is_private(name_underscored: bool, doc: PSeq[int]) -> bool:
    """Visibility classification of a member: an explicit public marker forces
    it public, an explicit private marker forces it private, otherwise the
    leading-underscore naming convention decides."""
    mc = meta_class(doc)
    if mc == PUBLIC:
        return False
    if mc == PRIVATE:
        return True
    return name_underscored

@Pure
def in_private_selection(mode: int, selected: bool) -> bool:
    """Whether a private member is selected for retention.
       mode 0: private-members not requested  -> never selected
       mode 1: all private members requested  -> always selected
       mode 2: an explicit list was given      -> selected iff listed."""
    Requires(mode == 0 or mode == 1 or mode == 2)
    if mode == 0:
        return False
    if mode == 1:
        return True
    return selected
# pure-end

def member_effective_doc(attr_doc: List[int], value_doc: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The attribute documentation takes precedence when present; only when it is
    # absent does the value's intrinsic documentation apply.
    Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
    # post-conditions-end
    # impl-start
    if len(attr_doc) > 0:
        result = list(attr_doc)  # type: List[int]
    else:
        result = list(value_doc)
    return result
    # impl-end

def keep_module_member(name_underscored: bool, name_special: bool,
                       attr_doc: List[int], value_doc: List[int],
                       want_all: bool, private_mode: int,
                       name_selected: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    Requires(private_mode == 0 or private_mode == 1 or private_mode == 2)
    # Modeled slice: a DOCUMENTED module member, i.e. one that carries some
    # documentation (inline attribute documentation or the value's own
    # documentation). A member with no documentation at all is decided by a
    # different, unmodeled retention branch and lies outside this boundary.
    Requires(len(attr_doc) > 0 or len(value_doc) > 0)
    # Modeled slice: an ORDINARILY NAMED member. A member whose name has the
    # reserved form (leading and trailing double underscore) is decided by a
    # separate, unmodeled retention branch that runs before the modeled one,
    # and lies outside this boundary.
    Requires(not name_special)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    # A documented module member is retained exactly per its visibility, which
    # is derived from its EFFECTIVE documentation (attribute documentation
    # preferred over intrinsic documentation).  A non-private member is always
    # retained; a private one only when the private-members selection picks it.
    Ensures(Result() == (
        (not want_all) or
        (not is_private(name_underscored,
                        effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))) or
        in_private_selection(private_mode, name_selected)))
    # Discriminating consequence: a member carrying the explicit public marker
    # in its attribute documentation is retained regardless of an underscore
    # name and regardless of the private-members selection.
    Ensures(Implies(
        meta_class(effective_doc(ToSeq(attr_doc), ToSeq(value_doc))) == PUBLIC,
        Result()))
    # post-conditions-end
    # impl-start
    doc = member_effective_doc(attr_doc, value_doc)
    private = is_private(name_underscored, ToSeq(doc))
    if not want_all:
        keep = True
    elif not private:
        keep = True
    else:
        keep = in_private_selection(private_mode, name_selected)
    return keep
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8593 (nagini). env: python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC STRUCTURE: spec_view elides ONLY impl regions; axioms, all @Pure helpers (effective_doc/is_private/in_private_selection), and pre/post-conditions are frozen byte-identical. Both postconditions PIN the outputs exactly: member_effective_doc's `ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc))`, and keep_module_member's `Result() == ((not want_all) or (not is_private(...effective_doc...)) or in_private_selection(...))` plus the discriminating `Implies(meta_class(effective_doc(...))==PUBLIC, Result())`. A functionally-tight spec.

8 attacks built by copying model.py and editing ONLY impl regions (verified byte-identical spec via same-spec: all 8 exit 0). Command form: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8593 <atk>`. Run concurrently in 3 batches of ≤3 (each spawns JVM+Z3).

### Results
- atk_1 (prepatch bug A re-encoded: member_effective_doc ignores attr_doc, always value_doc): weakness exit 2 — DOES NOT VERIFY (spec rejected). PREPATCH REPRODUCED.
- atk_2 (prepatch bug B re-encoded: keep classifies on ToSeq(value_doc) not effective doc): weakness exit 2 — DOES NOT VERIFY (spec rejected). PREPATCH REPRODUCED.
- atk_3 (boundary: member_effective_doc uses attr_doc when len>=0, i.e. always): exit 2 — does not verify.
- atk_4 (control-flow-effect: keep always True, drops private branch): exit 2 — does not verify.
- atk_5 (private-selection boundary: in_private_selection(mode, not name_selected)): exit 2 — does not verify.
- atk_6 (want_all inversion): exit 2 — does not verify.
- atk_7 (ungrounded-oracle ECHO: keep computed as the postcondition boolean expression directly, behaviorally == gold): weakness exit 0 — CANDIDATE (shares spec AND verifies, 17.6s).
- atk_8 (subtle boundary: member_effective_doc uses attr_doc only when len>1): exit 2 — does not verify.

Positive control (untouched model.py copy): `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (16.5s, exit 0).

CANDIDATE RESOLVE (protocol step 2, MANDATORY): atk_7 differs from the gold impl only in spelling the retention rule as one boolean expression vs the if/elif/else cascade — computationally the IDENTICAL keep decision, so its faithful refined patch IS the gold patch verbatim (the inline-vs-branch difference is invisible in the real filter_members). Materialized to atk_7_faithful_patch.diff and RAN through the official harness: `run_resolve('sphinx-doc__sphinx-8593', patch, run_id='sbu-eq-atk7', timeout=1800, retries=1)` => RESOLVED: True, COMPLETED: True. The one verifying candidate's faithful patch RESOLVES, so it is NOT a counterexample (a resolving echo of the gold is not a weakness, per the G-PANEL-1 resolve policy).

REFINEMENT.MD LEG AUDIT (A-leg focus): Legs A1/A3 (R: str<->List[int]), A2 (I: attribute-doc-preferred branch = concrete branch), B1 (I: caller uses callee spec), B2 (A-consumed: meta_class), B3 (I+R: control flow identical + option-mode bijection), B4 (R). NO kind-3 (unexpressible-changed-op) leg — refinement.md §C confirms the load-bearing changed op (attribute doc reaching the classifier) is modeled DEEPLY via effective_doc/A2=I, not axiomatized. There is NO A-reference leg.

The sole A-leg, B2 meta_class (A-consumed), binds to the UNCHANGED real callee sphinx.util.docstrings.extract_metadata + the public/private branch (__init__.py:731-737); its axiom Ensures are the weakest the proof needs (result in {0,1,2}; empty=>NONE) and the discriminating postcondition is PARAMETRIC in meta_class (never pins a specific value), so the axiom never over-claims. Correspondence confirmed by recorded G-AX (axiom_check.py, run in-container): status=pass, exit=0, 'meta_class axiom sound on 13 boundary + 20000 fuzz'. axiom_check.py imports only the real sphinx module (locally raises ModuleNotFoundError because sphinx is only installed in the eval Docker image — the gate runs there). Recorded G-RESOLVE=pass (gold resolves), corroborating the atk_7 resolve.

VERDICT: SOUND. All 6 genuinely-wrong impls (incl. both re-encoded prepatch bugs) are REJECTED by the tight postconditions; the single verifying candidate (atk_7) is a behavioral echo of the gold whose materialized faithful patch RESOLVES under the official harness. verify => correct holds on the exhibited attack surface. No verifying wrong impl with a non-resolving faithful patch was found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8593.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documenter collects the members of a target module, each member's
  effective documentation is the inline attribute documentation recorded for
  that name in the module source (when such documentation exists), falling back
  to the value's own intrinsic documentation only when no attribute
  documentation is present. The visibility classification of a member is then
  derived from THAT effective documentation: a member is treated as public when
  its documentation carries the explicit "public" visibility marker, private
  when it carries the explicit "private" marker, and otherwise according to the
  leading-underscore naming convention. A member whose effective documentation
  marks it public is therefore retained even when its name begins with an
  underscore.

This bundle models two cooperating behaviours:

  (1) the effective documentation chosen for a module member (the attribute
      documentation takes precedence over the value's intrinsic documentation),
      and

  (2) the retention decision for a documented module member under the
      "all members" mode, given the visibility classification derived from (1)
      and the private-members selection mode.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried by `PSeq[int]` via `ToSeq`. The
visibility classifier of a documentation block (the unchanged community
metadata extractor) is axiomatized as `meta_class`; provenance and an
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Visibility classification of a documentation block (a community metadata
# extractor reads its explicit visibility marker):
#   0 = no explicit visibility marker
#   1 = explicit "public"  marker present
#   2 = explicit "private" marker present
# A pure total function of the documentation text. G-AX checks it against the
# real extractor.
NONE = 0  # type: int
PUBLIC = 1  # type: int
PRIVATE = 2  # type: int

@Pure
@ContractOnly
def meta_class(doc: PSeq[int]) -> int:
    Requires(True)
    Ensures(Result() == NONE or Result() == PUBLIC or Result() == PRIVATE)
    # The empty documentation block carries no marker.
    Ensures(Implies(len(doc) == 0, Result() == NONE))
# axioms-end

# pure-start
@Pure
def effective_doc(attr_doc: PSeq[int], value_doc: PSeq[int]) -> PSeq[int]:
    """The documentation that drives the visibility classification of a module
    member: the inline attribute documentation when it is non-empty, otherwise
    the value's own intrinsic documentation."""
    if len(attr_doc) > 0:
        return attr_doc
    return value_doc

@Pure
def is_private(name_underscored: bool, doc: PSeq[int]) -> bool:
    """Visibility classification of a member: an explicit public marker forces
    it public, an explicit private marker forces it private, otherwise the
    leading-underscore naming convention decides."""
    mc = meta_class(doc)
    if mc == PUBLIC:
        return False
    if mc == PRIVATE:
        return True
    return name_underscored

@Pure
def in_private_selection(mode: int, selected: bool) -> bool:
    """Whether a private member is selected for retention.
       mode 0: private-members not requested  -> never selected
       mode 1: all private members requested  -> always selected
       mode 2: an explicit list was given      -> selected iff listed."""
    Requires(mode == 0 or mode == 1 or mode == 2)
    if mode == 0:
        return False
    if mode == 1:
        return True
    return selected
# pure-end

def member_effective_doc(attr_doc: List[int], value_doc: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The attribute documentation takes precedence when present; only when it is
    # absent does the value's intrinsic documentation apply.
    Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
    # post-conditions-end
    # impl-start
    if len(attr_doc) > 0:
        result = list(attr_doc)  # type: List[int]
    else:
        result = list(value_doc)
    return result
    # impl-end

def keep_module_member(name_underscored: bool, name_special: bool,
                       attr_doc: List[int], value_doc: List[int],
                       want_all: bool, private_mode: int,
                       name_selected: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    Requires(private_mode == 0 or private_mode == 1 or private_mode == 2)
    # Modeled slice: a DOCUMENTED module member, i.e. one that carries some
    # documentation (inline attribute documentation or the value's own
    # documentation). A member with no documentation at all is decided by a
    # different, unmodeled retention branch and lies outside this boundary.
    Requires(len(attr_doc) > 0 or len(value_doc) > 0)
    # Modeled slice: an ORDINARILY NAMED member. A member whose name has the
    # reserved form (leading and trailing double underscore) is decided by a
    # separate, unmodeled retention branch that runs before the modeled one,
    # and lies outside this boundary.
    Requires(not name_special)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    # A documented module member is retained exactly per its visibility, which
    # is derived from its EFFECTIVE documentation (attribute documentation
    # preferred over intrinsic documentation).  A non-private member is always
    # retained; a private one only when the private-members selection picks it.
    Ensures(Result() == (
        (not want_all) or
        (not is_private(name_underscored,
                        effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))) or
        in_private_selection(private_mode, name_selected)))
    # Discriminating consequence: a member carrying the explicit public marker
    # in its attribute documentation is retained regardless of an underscore
    # name and regardless of the private-members selection.
    Ensures(Implies(
        meta_class(effective_doc(ToSeq(attr_doc), ToSeq(value_doc))) == PUBLIC,
        Result()))
    # post-conditions-end
    # impl-start
    doc = member_effective_doc(attr_doc, value_doc)
    private = is_private(name_underscored, ToSeq(doc))
    if not want_all:
        keep = True
    elif not private:
        keep = True
    else:
        keep = in_private_selection(private_mode, name_selected)
    return keep
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8593 (nagini). env: python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC STRUCTURE: spec_view elides ONLY impl regions; axioms, all @Pure helpers (effective_doc/is_private/in_private_selection), and pre/post-conditions are frozen byte-identical. Both postconditions PIN the outputs exactly: member_effective_doc's `ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc))`, and keep_module_member's `Result() == ((not want_all) or (not is_private(...effective_doc...)) or in_private_selection(...))` plus the discriminating `Implies(meta_class(effective_doc(...))==PUBLIC, Result())`. A functionally-tight spec.

8 attacks built by copying model.py and editing ONLY impl regions (verified byte-identical spec via same-spec: all 8 exit 0). Command form: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8593 <atk>`. Run concurrently in 3 batches of ≤3 (each spawns JVM+Z3).

### Results
- atk_1 (prepatch bug A re-encoded: member_effective_doc ignores attr_doc, always value_doc): weakness exit 2 — DOES NOT VERIFY (spec rejected). PREPATCH REPRODUCED.
- atk_2 (prepatch bug B re-encoded: keep classifies on ToSeq(value_doc) not effective doc): weakness exit 2 — DOES NOT VERIFY (spec rejected). PREPATCH REPRODUCED.
- atk_3 (boundary: member_effective_doc uses attr_doc when len>=0, i.e. always): exit 2 — does not verify.
- atk_4 (control-flow-effect: keep always True, drops private branch): exit 2 — does not verify.
- atk_5 (private-selection boundary: in_private_selection(mode, not name_selected)): exit 2 — does not verify.
- atk_6 (want_all inversion): exit 2 — does not verify.
- atk_7 (ungrounded-oracle ECHO: keep computed as the postcondition boolean expression directly, behaviorally == gold): weakness exit 0 — CANDIDATE (shares spec AND verifies, 17.6s).
- atk_8 (subtle boundary: member_effective_doc uses attr_doc only when len>1): exit 2 — does not verify.

Positive control (untouched model.py copy): `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (16.5s, exit 0).

CANDIDATE RESOLVE (protocol step 2, MANDATORY): atk_7 differs from the gold impl only in spelling the retention rule as one boolean expression vs the if/elif/else cascade — computationally the IDENTICAL keep decision, so its faithful refined patch IS the gold patch verbatim (the inline-vs-branch difference is invisible in the real filter_members). Materialized to atk_7_faithful_patch.diff and RAN through the official harness: `run_resolve('sphinx-doc__sphinx-8593', patch, run_id='sbu-eq-atk7', timeout=1800, retries=1)` => RESOLVED: True, COMPLETED: True. The one verifying candidate's faithful patch RESOLVES, so it is NOT a counterexample (a resolving echo of the gold is not a weakness, per the G-PANEL-1 resolve policy).

REFINEMENT.MD LEG AUDIT (A-leg focus): Legs A1/A3 (R: str<->List[int]), A2 (I: attribute-doc-preferred branch = concrete branch), B1 (I: caller uses callee spec), B2 (A-consumed: meta_class), B3 (I+R: control flow identical + option-mode bijection), B4 (R). NO kind-3 (unexpressible-changed-op) leg — refinement.md §C confirms the load-bearing changed op (attribute doc reaching the classifier) is modeled DEEPLY via effective_doc/A2=I, not axiomatized. There is NO A-reference leg.

The sole A-leg, B2 meta_class (A-consumed), binds to the UNCHANGED real callee sphinx.util.docstrings.extract_metadata + the public/private branch (__init__.py:731-737); its axiom Ensures are the weakest the proof needs (result in {0,1,2}; empty=>NONE) and the discriminating postcondition is PARAMETRIC in meta_class (never pins a specific value), so the axiom never over-claims. Correspondence confirmed by recorded G-AX (axiom_check.py, run in-container): status=pass, exit=0, 'meta_class axiom sound on 13 boundary + 20000 fuzz'. axiom_check.py imports only the real sphinx module (locally raises ModuleNotFoundError because sphinx is only installed in the eval Docker image — the gate runs there). Recorded G-RESOLVE=pass (gold resolves), corroborating the atk_7 resolve.

VERDICT: SOUND. All 6 genuinely-wrong impls (incl. both re-encoded prepatch bugs) are REJECTED by the tight postconditions; the single verifying candidate (atk_7) is a behavioral echo of the gold whose materialized faithful patch RESOLVES under the official harness. verify => correct holds on the exhibited attack surface. No verifying wrong impl with a non-resolving faithful patch was found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo behavior) confirmed for sphinx-doc__sphinx-8593 nagini bundle.

METHOD: Built an executable oracle against the real repo at base_commit 07983a5, importing the REAL sphinx.util.docstrings.extract_metadata (docutils installed in a scratch venv). Re-implemented filter_members' retention exactly as at __init__.py:731-768 (metadata->isprivate classification; attr_docs keep-branch; intrinsic-doc private branch; has_doc fallback), with in_attr_docs modeled as 'attr_doc non-empty' and doc = obj.docstring (attr) preferred over intrinsic getdoc (val).

### Results
1. model.py VERIFIES under pinned Nagini (15.7s). Same-spec control on an identity copy passes (spec region intact).
2. Exhaustive enumeration over the ENTIRE modeled domain: {name_underscored in [F,T]} x {attr_doc, value_doc each in ['', prose, ':meta public:', ':meta private:', post-prose public, post-prose private, both-markers]} (excluding the empty/empty pair per precondition) x {want_all in [F,T]} x {private_mode in None/ALL/explicit-list(+/-/other)} => 0 divergences between the model's unified retention formula (member_effective_doc + is_private + in_private_selection + keep_module_member postcondition) and the real filter_members retention. The discriminating public-marker clause (Implies meta_class(effective_doc)==PUBLIC => Result) holds on the real classifier too.
3. Domain boundaries are HONEST, not spec-strengthening: not name_special routes reserved-name members to the unchanged special-members branch (runs earlier), and len(attr_doc)>0 or len(value_doc)>0 excludes undocumented members handled by the undoc branch. These preconditions exclude inputs the real code decides elsewhere; they do not over-constrain the modeled slice.
4. For a MODULE object, is_filtered_inherited_member is always False, so the attr_docs keep-branch and the intrinsic-doc private branch collapse to the identical formula (verified: 0 divergences over non-empty docs). The single modeled branch thus faithfully covers the whole documented-module-member slice.
5. meta_class axiom is the weakest sound abstraction (result in {0,1,2}; empty->NONE), validated by axiom_check.py against the real extract_metadata across boundary + 20000 fuzz blocks; edge cases (':meta public: extra', whitespace-padded markers, marker-after-prose without blank sep classified NONE) all consistent with the real callee and immaterial to faithfulness since the axiom does not pin marker mapping.

No diverging input exists. The spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures); model.py spec region is byte-identical to the bundle (same-spec exit 0). Semantic review: the public problem_statement already discloses the desired behaviour — that an inline `:meta public:` marker on a module variable (`_foo = None  #: :meta public:`) should make the underscore-named member visible. The spec view formalizes exactly that desired behaviour (effective doc = inline attribute documentation preferred over intrinsic; visibility public/private marker else underscore; public-marked member retained despite underscore name) phrased abstractly as behaviour, not as an edit. No patched file paths (sphinx/ext/autodoc/__init__.py, importer.py), no patched symbol names (get_module_members, ObjectMember, attr_docs, filter_members), no diff markers, no reproduced gold lines, no bug/fix narration. The 'attribute doc precedence over intrinsic doc' detail is derivable directly from the problem statement's reproduction case and does not localize the gold edit's approach/file/symbol. No RELAXED_LEAKAGE.md present. Nothing in the spec view leaks the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
