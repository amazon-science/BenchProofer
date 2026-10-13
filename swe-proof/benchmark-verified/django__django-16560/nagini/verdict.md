# P2 adversarial audit — django__django-16560

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -78,7 +76,10 @@
     Ensures(Result() is code)
     # post-conditions-end
     # impl-start
-    return code
+    # ATTACK 1 (partial-domain): drop the classifier on configuration — return
+    # the neutral marker regardless (prepatch_2 behaviour). Fails Result() is code
+    # whenever code is not None.
+    return None
     # impl-end
 
 
@@ -88,7 +89,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +103,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +123,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +137,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -96,14 +93,16 @@
     Ensures(Result() is rule_code)
     # post-conditions-end
     # impl-start
-    return rule_code
+    # ATTACK 2 (prepatch bug / ungrounded-oracle): the surfaced failure carries
+    # the neutral marker regardless of the rule's classifier — fails
+    # Result() is rule_code whenever rule_code is not None.
+    return None
     # impl-end
 
 
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +123,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +137,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +120,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -132,14 +127,16 @@
     Ensures(Result() == (a_key == b_key and a_code is b_code))
     # post-conditions-end
     # impl-start
-    return a_key == b_key and a_code is b_code
+    # ATTACK 3 (prepatch_3 / dropped conjunct): equality ignores the classifier,
+    # so two rules differing only in classifier compare equal — fails
+    # Result() == (a_key == b_key and a_code is b_code).
+    return a_key == b_key
     # impl-end
 
 
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +120,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +134,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
@@ -147,5 +141,8 @@
     Ensures(Result() == (rule_code is not None))
     # post-conditions-end
     # impl-start
-    return rule_code is not None
+    # ATTACK 4 (prepatch_4 / boundary): reconstruction never names the classifier
+    # (always False) — fails Result() == (rule_code is not None) when a classifier
+    # is present.
+    return False
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -114,9 +110,11 @@
     Exsures(ValidationFailure, violated)
     # post-conditions-end
     # impl-start
-    if violated:
-        raise ValidationFailure()
-    return
+    # ATTACK 5 (control-flow-effect): always signal a validation failure,
+    # ignoring the verdict. Observationally wrong (raises even when the check
+    # reports no violation). Should fail Exsures(ValidationFailure, violated)
+    # (raises when violated is False) and Ensures(not violated) (never returns).
+    raise ValidationFailure()
     # impl-end
 
 
@@ -124,7 +122,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +136,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -114,8 +110,9 @@
     Exsures(ValidationFailure, violated)
     # post-conditions-end
     # impl-start
-    if violated:
-        raise ValidationFailure()
+    # ATTACK 6 (control-flow-effect / inverted): never raise, always return
+    # normally even on a reported violation. Should fail
+    # Exsures(ValidationFailure, violated) (must raise when violated is True).
     return
     # impl-end
 
@@ -124,7 +121,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +135,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +120,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -132,14 +127,17 @@
     Ensures(Result() == (a_key == b_key and a_code is b_code))
     # post-conditions-end
     # impl-start
-    return a_key == b_key and a_code is b_code
+    # ATTACK 7 (boundary / is-vs-==): compare the classifier with value equality
+    # instead of identity. In the token domain the spec pins `is`; `==` differs
+    # for distinct-but-equal int tokens, so this should fail
+    # Result() == (a_key == b_key and a_code is b_code).
+    return a_key == b_key and a_code == b_code
     # impl-end
 
 
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ValidationFailure(Exception):
@@ -70,7 +69,6 @@
     # `code` is a plain token input (no heap permission needed):
     #   code is None  -> the neutral "no classifier" marker;
     #   code not None -> the supplied classifier, to be retained verbatim.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # (1) Configuration: the supplied classifier is retained verbatim; an absent
@@ -88,7 +86,6 @@
     # unchanged underlying check's verdict (True iff the data violates the rule).
     # Only meaningful when a violation is reported.
     Requires(violated)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
@@ -103,7 +100,6 @@
 def validate_rule(rule_code: Optional[int], violated: bool) -> None:
     # pre-conditions-start
     # `rule_code` and `violated` are plain inputs (no heap permission needed).
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # (2) No violation reported -> the rule signals nothing (normal return is
@@ -124,7 +120,6 @@
     # pre-conditions-start
     # All four are plain token inputs (no heap permission needed): the rule's
     # opaque identity payload (`*_key`) and its classifier (`*_code`).
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     # (3) Identity: equal iff every configured facet agrees, the classifier
@@ -139,7 +134,6 @@
 def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
     # pre-conditions-start
     # `rule_code` is a plain token input (no heap permission needed).
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     # (4) Reconstruction keywords name the classifier EXACTLY when one is
@@ -147,5 +141,8 @@
     Ensures(Result() == (rule_code is not None))
     # post-conditions-end
     # impl-start
-    return rule_code is not None
+    # ATTACK 8 (ungrounded-oracle echo / inverted boundary): reconstruction always
+    # names the classifier (True), even for the neutral marker. Should fail
+    # Result() == (rule_code is not None) when rule_code is None.
+    return True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16560.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A declarative integrity rule carries, alongside its human-readable violation
  message, an optional machine-readable violation classifier (a short code).
  The classifier is supplied when the rule is configured and threads through the
  rule's whole observable surface:

    (1) Configuration. The rule accepts an optional classifier. When a
        classifier is supplied it is retained verbatim; when it is absent the
        rule carries the neutral "no classifier" marker.

    (2) Reporting a violation. When the rule's underlying check reports that the
        data violates the rule, the rule signals a validation failure and the
        classifier carried on that surfaced failure is EXACTLY the rule's own
        classifier (the same marker it was configured with), never the neutral
        marker substituted in regardless. When the check reports no violation,
        the rule signals nothing.

    (3) Identity. Two rules are considered equal only when they agree on every
        configured facet, the classifier included: two rules that differ only in
        their classifier are NOT equal, and two rules that agree on the
        classifier (and everything else) ARE equal.

    (4) Reconstruction keywords. The keyword bundle that reconstructs an
        equivalent rule names the classifier exactly when a classifier is
        present (a non-neutral marker), and omits it when the rule carries the
        neutral marker.

The classifier is modelled as ``Optional[int]`` — a token domain where the null
token is the neutral "no classifier" marker and each distinct non-null token is
a distinct classifier (Nagini bans ``str`` indexing and the discriminating
observable is purely the token identity, not its characters). The rule's
remaining configured payload is one opaque ``int`` (``key``) standing for every
other identity facet. The underlying violation check is an unchanged callee; it
is abstracted by a boolean reporting whether the data violates the rule. The
validation failure is a user-defined exception class (a builtin exception in an
``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class ValidationFailure(Exception):
    """The validation failure a rule signals when its underlying check reports a
    violation. User-defined stand-in for the framework's validation error (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2). The classifier the surfaced failure carries is pinned
    functionally by ``surfaced_violation_code`` (the discriminating value)."""

# axioms-start
# (no @ContractOnly axioms: the unchanged violation check is abstracted as a
# boolean verdict input — see `validate_rule` — and every other touched
# operation is modelled directly, so the proof consumes no axiom.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for these behaviours.)
# pure-end

def configured_code(code: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # `code` is a plain token input (no heap permission needed):
    #   code is None  -> the neutral "no classifier" marker;
    #   code not None -> the supplied classifier, to be retained verbatim.
    # pre-conditions-end
    # post-conditions-start
    # (1) Configuration: the supplied classifier is retained verbatim; an absent
    # classifier (None) is carried as the neutral marker (None).
    Ensures(Result() is code)
    # post-conditions-end
    # impl-start
    return code
    # impl-end

def surfaced_violation_code(rule_code: Optional[int], violated: bool) -> Optional[int]:
    # pre-conditions-start
    # `rule_code` is the rule's configured classifier; `violated` is the
    # unchanged underlying check's verdict (True iff the data violates the rule).
    # Only meaningful when a violation is reported.
    Requires(violated)
    # pre-conditions-end
    # post-conditions-start
    # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
    # own classifier — never the neutral marker substituted in regardless.
    Ensures(Result() is rule_code)
    # post-conditions-end
    # impl-start
    return rule_code
    # impl-end

def validate_rule(rule_code: Optional[int], violated: bool) -> None:
    # pre-conditions-start
    # `rule_code` and `violated` are plain inputs (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # (2) No violation reported -> the rule signals nothing (normal return is
    # reachable on EXACTLY the no-violation verdict). A reported violation must
    # raise the validation failure; the classifier that failure carries is the
    # rule's own, pinned by `surfaced_violation_code`'s contract.
    Ensures(not violated)
    Exsures(ValidationFailure, violated)
    # post-conditions-end
    # impl-start
    if violated:
        raise ValidationFailure()
    return
    # impl-end

def constraints_equal(a_key: int, a_code: Optional[int], b_key: int, b_code: Optional[int]) -> bool:
    # pre-conditions-start
    # All four are plain token inputs (no heap permission needed): the rule's
    # opaque identity payload (`*_key`) and its classifier (`*_code`).
    # pre-conditions-end
    # post-conditions-start
    # (3) Identity: equal iff every configured facet agrees, the classifier
    # included. Two rules differing only in classifier are NOT equal.
    Ensures(Result() == (a_key == b_key and a_code is b_code))
    # post-conditions-end
    # impl-start
    return a_key == b_key and a_code is b_code
    # impl-end

def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
    # pre-conditions-start
    # `rule_code` is a plain token input (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # (4) Reconstruction keywords name the classifier EXACTLY when one is
    # present (a non-neutral marker), and omit it for the neutral marker.
    Ensures(Result() == (rule_code is not None))
    # post-conditions-end
    # impl-start
    return rule_code is not None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of django__django-16560 nagini bundle — G-EQ refinement-fidelity (A-leg focus).

**SPEC SHAPE:** five contracted functions, every one with a TOTAL, functionally exact postcondition, leaving essentially no wiggle room for a verifying-but-wrong impl:
  - configured_code:            Ensures(Result() is code)                              [Site 1 config]
  - surfaced_violation_code:    Requires(violated); Ensures(Result() is rule_code)     [Site 2 code-flow]
  - validate_rule:              Ensures(not violated); Exsures(ValidationFailure, violated)  [Site 2 control flow]
  - constraints_equal:          Ensures(Result() == (a_key==b_key and a_code is b_code)) [Site 3 identity]
  - keyword_bundle_names_code:  Ensures(Result() == (rule_code is not None))            [Site 4 reconstruct]

**POSITIVE CONTROL:** pos_control.py (verbatim model.py) => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.6s). Baseline good.

ATTACKS (all copied from model.py, ONLY impl region edited; all confirmed same-spec byte-identical). Command for each: python -m swebench_unified.adversary weakness nagini django__django-16560 atk_N.py Run concurrently in 3 batches of <=3 (each spawns JVM+Z3).

Results: atk_1 (partial-domain: configured_code returns None regardless / prepatch_2): EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). atk_2 (prepatch bug: surfaced_violation_code returns None / ungrounded-oracle): EXIT=2 verification failed. atk_3 (dropped conjunct: constraints_equal returns a_key==b_key only / prepatch_3): EXIT=2 verification failed. atk_4 (boundary: keyword_bundle_names_code returns False always / prepatch_4): EXIT=2 verification failed. atk_5 (control-flow-effect: validate_rule always raises): EXIT=2 verification failed. atk_6 (control-flow-effect inverted: validate_rule never raises): EXIT=2 verification failed. atk_7 (is-vs-== boundary: constraints_equal uses a_code == b_code): EXIT=2 verification failed. atk_8 (inverted boundary: keyword_bundle_names_code returns True always): EXIT=2 verification failed.

All 8 rejected by the verifier under the identical frozen spec. same-spec explicitly re-confirmed SAME (EXIT=0) for atk_5 and atk_7. NO CANDIDATE emerged => no faithful refined patch to materialize/run_resolve (verify==>correct held for every wrong impl tried, incl. the 4 prepatch bugs and the subtle token is/== attack).

REFINEMENT.MD AUDIT (A-leg + correspondence): Every leg tagged R or I over the Optional[int] token domain across Sites 1-4; NO kind-3 (unexpressible-changed-op) step. Bundle consumes NO @ContractOnly axiom and has NO A-reference deep model — confirmed: the axioms-start/axioms-end region of model.py is comment-only. The single library value-flow the refinement leans on (ValidationError(code=X).code is X; ValidationError().code is None) is NOT consumed as an axiom but VALIDATED by axiom_check.py / G-AX, which runs the REAL django.core.exceptions.ValidationError and the REAL patched constraint classes in-container and asserts construct/violate/equal/reconstruct on the actual callees. Model<->patch correspondence (mapping.md) is faithful: token bijection None<->None, distinct str<->distinct int; boolean-verdict abstraction of the unchanged violation check (not axiomatized, patch does not touch it); ValidationFailure<->ValidationError raise map with the classifier pinned functionally by surfaced_violation_code. The textual-repr surface is the string projection of the identical Site-4 code-is-not-None predicate — covered, no hidden kind-3.

**VERDICT:** SOUND. >=5 (8) distinct same-spec wrong impls run through the official weakness harness; NONE verified, so verify does not admit an incorrect impl here. prepatch_reproduced=true (atk_1..4 are exactly the recorded prepatch bugs and all fail verification).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16560.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A declarative integrity rule carries, alongside its human-readable violation
  message, an optional machine-readable violation classifier (a short code).
  The classifier is supplied when the rule is configured and threads through the
  rule's whole observable surface:

    (1) Configuration. The rule accepts an optional classifier. When a
        classifier is supplied it is retained verbatim; when it is absent the
        rule carries the neutral "no classifier" marker.

    (2) Reporting a violation. When the rule's underlying check reports that the
        data violates the rule, the rule signals a validation failure and the
        classifier carried on that surfaced failure is EXACTLY the rule's own
        classifier (the same marker it was configured with), never the neutral
        marker substituted in regardless. When the check reports no violation,
        the rule signals nothing.

    (3) Identity. Two rules are considered equal only when they agree on every
        configured facet, the classifier included: two rules that differ only in
        their classifier are NOT equal, and two rules that agree on the
        classifier (and everything else) ARE equal.

    (4) Reconstruction keywords. The keyword bundle that reconstructs an
        equivalent rule names the classifier exactly when a classifier is
        present (a non-neutral marker), and omits it when the rule carries the
        neutral marker.

The classifier is modelled as ``Optional[int]`` — a token domain where the null
token is the neutral "no classifier" marker and each distinct non-null token is
a distinct classifier (Nagini bans ``str`` indexing and the discriminating
observable is purely the token identity, not its characters). The rule's
remaining configured payload is one opaque ``int`` (``key``) standing for every
other identity facet. The underlying violation check is an unchanged callee; it
is abstracted by a boolean reporting whether the data violates the rule. The
validation failure is a user-defined exception class (a builtin exception in an
``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class ValidationFailure(Exception):
    """The validation failure a rule signals when its underlying check reports a
    violation. User-defined stand-in for the framework's validation error (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2). The classifier the surfaced failure carries is pinned
    functionally by ``surfaced_violation_code`` (the discriminating value)."""

# axioms-start
# (no @ContractOnly axioms: the unchanged violation check is abstracted as a
# boolean verdict input — see `validate_rule` — and every other touched
# operation is modelled directly, so the proof consumes no axiom.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for these behaviours.)
# pure-end

def configured_code(code: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # `code` is a plain token input (no heap permission needed):
    #   code is None  -> the neutral "no classifier" marker;
    #   code not None -> the supplied classifier, to be retained verbatim.
    # pre-conditions-end
    # post-conditions-start
    # (1) Configuration: the supplied classifier is retained verbatim; an absent
    # classifier (None) is carried as the neutral marker (None).
    Ensures(Result() is code)
    # post-conditions-end
    # impl-start
    return code
    # impl-end

def surfaced_violation_code(rule_code: Optional[int], violated: bool) -> Optional[int]:
    # pre-conditions-start
    # `rule_code` is the rule's configured classifier; `violated` is the
    # unchanged underlying check's verdict (True iff the data violates the rule).
    # Only meaningful when a violation is reported.
    Requires(violated)
    # pre-conditions-end
    # post-conditions-start
    # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
    # own classifier — never the neutral marker substituted in regardless.
    Ensures(Result() is rule_code)
    # post-conditions-end
    # impl-start
    return rule_code
    # impl-end

def validate_rule(rule_code: Optional[int], violated: bool) -> None:
    # pre-conditions-start
    # `rule_code` and `violated` are plain inputs (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # (2) No violation reported -> the rule signals nothing (normal return is
    # reachable on EXACTLY the no-violation verdict). A reported violation must
    # raise the validation failure; the classifier that failure carries is the
    # rule's own, pinned by `surfaced_violation_code`'s contract.
    Ensures(not violated)
    Exsures(ValidationFailure, violated)
    # post-conditions-end
    # impl-start
    if violated:
        raise ValidationFailure()
    return
    # impl-end

def constraints_equal(a_key: int, a_code: Optional[int], b_key: int, b_code: Optional[int]) -> bool:
    # pre-conditions-start
    # All four are plain token inputs (no heap permission needed): the rule's
    # opaque identity payload (`*_key`) and its classifier (`*_code`).
    # pre-conditions-end
    # post-conditions-start
    # (3) Identity: equal iff every configured facet agrees, the classifier
    # included. Two rules differing only in classifier are NOT equal.
    Ensures(Result() == (a_key == b_key and a_code is b_code))
    # post-conditions-end
    # impl-start
    return a_key == b_key and a_code is b_code
    # impl-end

def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
    # pre-conditions-start
    # `rule_code` is a plain token input (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # (4) Reconstruction keywords name the classifier EXACTLY when one is
    # present (a non-neutral marker), and omit it for the neutral marker.
    Ensures(Result() == (rule_code is not None))
    # post-conditions-end
    # impl-start
    return rule_code is not None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of django__django-16560 nagini bundle — G-EQ refinement-fidelity (A-leg focus).

**SPEC SHAPE:** five contracted functions, every one with a TOTAL, functionally exact postcondition, leaving essentially no wiggle room for a verifying-but-wrong impl:
  - configured_code:            Ensures(Result() is code)                              [Site 1 config]
  - surfaced_violation_code:    Requires(violated); Ensures(Result() is rule_code)     [Site 2 code-flow]
  - validate_rule:              Ensures(not violated); Exsures(ValidationFailure, violated)  [Site 2 control flow]
  - constraints_equal:          Ensures(Result() == (a_key==b_key and a_code is b_code)) [Site 3 identity]
  - keyword_bundle_names_code:  Ensures(Result() == (rule_code is not None))            [Site 4 reconstruct]

**POSITIVE CONTROL:** pos_control.py (verbatim model.py) => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.6s). Baseline good.

ATTACKS (all copied from model.py, ONLY impl region edited; all confirmed same-spec byte-identical). Command for each: python -m swebench_unified.adversary weakness nagini django__django-16560 atk_N.py Run concurrently in 3 batches of <=3 (each spawns JVM+Z3).

Results: atk_1 (partial-domain: configured_code returns None regardless / prepatch_2): EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). atk_2 (prepatch bug: surfaced_violation_code returns None / ungrounded-oracle): EXIT=2 verification failed. atk_3 (dropped conjunct: constraints_equal returns a_key==b_key only / prepatch_3): EXIT=2 verification failed. atk_4 (boundary: keyword_bundle_names_code returns False always / prepatch_4): EXIT=2 verification failed. atk_5 (control-flow-effect: validate_rule always raises): EXIT=2 verification failed. atk_6 (control-flow-effect inverted: validate_rule never raises): EXIT=2 verification failed. atk_7 (is-vs-== boundary: constraints_equal uses a_code == b_code): EXIT=2 verification failed. atk_8 (inverted boundary: keyword_bundle_names_code returns True always): EXIT=2 verification failed.

All 8 rejected by the verifier under the identical frozen spec. same-spec explicitly re-confirmed SAME (EXIT=0) for atk_5 and atk_7. NO CANDIDATE emerged => no faithful refined patch to materialize/run_resolve (verify==>correct held for every wrong impl tried, incl. the 4 prepatch bugs and the subtle token is/== attack).

REFINEMENT.MD AUDIT (A-leg + correspondence): Every leg tagged R or I over the Optional[int] token domain across Sites 1-4; NO kind-3 (unexpressible-changed-op) step. Bundle consumes NO @ContractOnly axiom and has NO A-reference deep model — confirmed: the axioms-start/axioms-end region of model.py is comment-only. The single library value-flow the refinement leans on (ValidationError(code=X).code is X; ValidationError().code is None) is NOT consumed as an axiom but VALIDATED by axiom_check.py / G-AX, which runs the REAL django.core.exceptions.ValidationError and the REAL patched constraint classes in-container and asserts construct/violate/equal/reconstruct on the actual callees. Model<->patch correspondence (mapping.md) is faithful: token bijection None<->None, distinct str<->distinct int; boolean-verdict abstraction of the unchanged violation check (not axiomatized, patch does not touch it); ValidationFailure<->ValidationError raise map with the classifier pinned functionally by surfaced_violation_code. The textual-repr surface is the string projection of the identical Site-4 code-is-not-None predicate — covered, no hidden kind-3.

**VERDICT:** SOUND. >=5 (8) distinct same-spec wrong impls run through the official weakness harness; NONE verified, so verify does not admit an incorrect impl here. prepatch_reproduced=true (atk_1..4 are exactly the recorded prepatch bugs and all fail verification).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16560 nagini bundle. The spec models the gold patch's uniform threading of an optional violation_error_code classifier across four surfaces of the constraint classes, abstracted over an Optional[int] token domain (None=neutral marker, distinct non-null ints=distinct classifiers; `is` mirrors `==` on interned strings).

Verified base_commit worktree (HEAD=51c9bb7cd160..., gold patch already applied to constraints.py). Ran a direct behavioral probe of every modeled function against the REAL patched callees (django):
- Site 1 configured_code: BaseConstraint stores classifier verbatim; absent kwarg AND explicit None both -> None. Matches Ensures(Result() is code).
- Site 2 validate_rule/surfaced_violation_code: CheckConstraint.validate on a live instance raises ValidationError iff the underlying Q-check reports a violation, and the raised error's .code is EXACTLY self.violation_error_code ('cc'), None on the no-violation path. Matches Ensures(not violated)/Exsures(ValidationFailure,violated) and Ensures(Result() is rule_code).
- Site 3 constraints_equal: constraints differing only in code are unequal; agreeing are equal. Matches Result()==(a_key==b_key and a_code is b_code).
- Site 4 keyword_bundle_names_code: deconstruct kwargs contain 'violation_error_code' iff code is not None. Matches Result()==(rule_code is not None).

Ran the bundle's own conformance_check.py against the real patched repo: G-CONF OK, 121516 inputs (1516 boundary + 120000 fuzz, seed 165600), 0 disagreements across all four sites, exit 0.

No input found where any modeled function disagrees with the real repo callee within the documented abstraction. The Optional[int] token abstraction is sound because the only observables the F2P tests make of the classifier are presence and identity/equality, never its characters (mapping.md 2). The spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (status=pass, 'spec view clean'), and semantic review confirms no gold-edit disclosure beyond the public problem_statement.

Public problem_statement already reveals: customizing the 'code' attribute of a ValidationError raised by a constraint's validate, mirroring the existing violation_error_message parameter (i.e. a violation_error_code-style knob threaded through the constraint). Both 'code' and 'violation' are public terms.

Spec view examined (docstring + contracts, impl regions elided):
- No patched repo symbols named. Contracted functions are abstracted (configured_code, surfaced_violation_code, validate_rule, constraints_equal, keyword_bundle_names_code); none echo the gold-patch symbols (violation_error_code, BaseConstraint/CheckConstraint/UniqueConstraint/ExclusionConstraint, deconstruct, `__eq__`, `__init__`, validate). `_patch_changed_symbols` would flag 'violation_error_code' etc.; none appear in identifiers or comments.
- No gold-diff line reproduced, no diff markers, no patched file path/module (django.db.models.constraints / django.contrib.postgres.constraints) in the view.
- Docstring speaks purely of a 'declarative integrity rule', 'classifier / short code', 'validation failure', 'reconstruction keywords', 'identity' — abstract behavior, not the edit or repo internals. No bug/fix narration.

The four/five modelled surfaces (configuration, violation reporting, identity/`__eq__`, reconstruction/deconstruct, repr) go slightly past the literal problem_statement wording, but they are stated as required observable behavior of the abstract rule (the F2P-tested facets and natural consequences of adding an optional attribute to a constraint), described behaviorally rather than as edit locations or repo symbols. Enumerating the behavior a correct impl must satisfy is faithful specification, not gold reconstruction: the view does not tell a solver which files/symbols/lines to change. G-LEAK is a lexical screen and it is clean; the semantic overlay finds nothing that localizes the edit beyond the public task. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).