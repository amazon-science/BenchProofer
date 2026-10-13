# P2 adversarial audit — django__django-15277

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -85,7 +83,6 @@
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -103,8 +100,7 @@
     # post-conditions-end
     # impl-start
     validators = []  # type: List[Optional[int]]
-    if max_length is not None:
-        validators.append(max_length)
+    validators.append(max_length)
     return validators
     # impl-end
 
@@ -114,7 +110,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -78,14 +76,13 @@
     # impl-start
     if limit is None:
         raise LimitComparisonError()
-    return value_length > limit
+    return value_length >= limit
     # impl-end
 
 
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -114,7 +111,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -85,7 +83,6 @@
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -104,7 +101,7 @@
     # impl-start
     validators = []  # type: List[Optional[int]]
     if max_length is not None:
-        validators.append(max_length)
+        validators.append(max_length + 1)
     return validators
     # impl-end
 
@@ -114,7 +111,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -85,7 +83,6 @@
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -114,7 +111,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
@@ -131,9 +127,5 @@
     # post-conditions-end
     # impl-start
     validators = build_char_validators(max_length)
-    flagged = False
-    if len(validators) > 0:
-        limit = validators[0]
-        flagged = compare_length(value_length, limit)
-    return flagged
+    return False
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -85,7 +83,6 @@
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -105,6 +102,7 @@
     validators = []  # type: List[Optional[int]]
     if max_length is not None:
         validators.append(max_length)
+        validators.append(max_length)
     return validators
     # impl-end
 
@@ -114,7 +112,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -85,7 +83,6 @@
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -114,7 +111,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
@@ -130,10 +126,7 @@
                     Result() == (value_length > max_length)))
     # post-conditions-end
     # impl-start
-    validators = build_char_validators(max_length)
-    flagged = False
-    if len(validators) > 0:
-        limit = validators[0]
-        flagged = compare_length(value_length, limit)
-    return flagged
+    if max_length is None:
+        return False
+    return value_length > max_length
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class LimitComparisonError(Exception):
@@ -64,7 +63,6 @@
     # pre-conditions-start
     # `value_length` is the candidate's length; `limit` is one validator's
     # numeric limit. Both are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The comparison completes normally ONLY when the limit is a concrete
@@ -78,14 +76,13 @@
     # impl-start
     if limit is None:
         raise LimitComparisonError()
-    return value_length > limit
+    return True
     # impl-end
 
 
 def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
     # pre-conditions-start
     # `max_length` is the optional maximum-length attribute (immutable scalar).
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -114,7 +111,6 @@
     # `max_length` is the field's optional maximum-length attribute;
     # `value_length` is the length of the candidate value being cleaned. Both
     # are immutable scalars (no heap permission needed).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Cleaning a candidate against a freshly constructed field always completes
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15277.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text field is constructed with an optional maximum-length attribute. During
  construction the field assembles the list of length-validators that will run
  whenever a candidate value is later cleaned. A length-validator carries a
  numeric limit and, when it runs, compares the candidate's length against that
  limit; the comparison is only meaningful when the limit is a concrete number.

  The behaviour pinned here:

    (1) When no maximum length is supplied, the field assembles NO length
        validator: the assembled list is empty. (A length validator with an
        absent limit could not perform its numeric comparison.)
    (2) When a maximum length IS supplied, the field assembles exactly one
        length validator whose limit equals the supplied maximum, so that
        length checking is still performed for fields that declare a maximum.
    (3) Consequently, cleaning an arbitrary candidate value against a freshly
        constructed field of this kind always completes normally — running the
        assembled validators never fails on an absent limit — regardless of
        whether a maximum length was supplied.

A length validator is characterised, for the behaviour observed here, entirely
by its numeric limit; the assembled validator list is therefore modelled as a
``List[Optional[int]]`` of limits (an element is the limit of one assembled
length validator; an absent limit is ``None``). The maximum-length attribute is
``Optional[int]``. The failure of a length comparison against an absent limit is
a user-defined exception (a builtin exception in an ``Exsures`` crashes the
Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class LimitComparisonError(Exception):
    """Signals that a length validator was asked to compare a candidate's
    length against an absent (``None``) limit — the comparison is undefined.
    Stands in for the ``TypeError`` such a comparison raises in reality (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the validator-assembly decision and the length
# comparison the cleaning step performs are both modelled deeply below. Every
# other operation the real constructor / cleaning path delegates to is
# unchanged, independent of the limit-present/absent decision, and unobserved
# by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the assembled-list properties are
# stated directly in the contracts via quantification over the result.)
# pure-end


def compare_length(value_length: int, limit: Optional[int]) -> bool:
    # pre-conditions-start
    # `value_length` is the candidate's length; `limit` is one validator's
    # numeric limit. Both are immutable scalars (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # The comparison completes normally ONLY when the limit is a concrete
    # number; when it is, the result is the ordinary "exceeds the limit" test.
    Ensures(limit is not None)
    Ensures(Result() == (value_length > limit))
    # A length comparison against an absent limit is undefined and is signalled
    # to the caller rather than producing a value.
    Exsures(LimitComparisonError, limit is None)
    # post-conditions-end
    # impl-start
    if limit is None:
        raise LimitComparisonError()
    return value_length > limit
    # impl-end


def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
    # pre-conditions-start
    # `max_length` is the optional maximum-length attribute (immutable scalar).
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # No assembled length validator has an absent limit: every assembled
    # validator can perform its numeric comparison.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(Result()), Result()[k] is not None))))
    # When no maximum length is supplied, no length validator is assembled.
    Ensures(Implies(max_length is None, len(Result()) == 0))
    # When a maximum length IS supplied, exactly one length validator is
    # assembled and its limit equals the supplied maximum (length checking is
    # preserved for fields that declare a maximum).
    Ensures(Implies(max_length is not None,
                    len(Result()) == 1 and Result()[0] == max_length))
    # post-conditions-end
    # impl-start
    validators = []  # type: List[Optional[int]]
    if max_length is not None:
        validators.append(max_length)
    return validators
    # impl-end


def clean_charfield(max_length: Optional[int], value_length: int) -> bool:
    # pre-conditions-start
    # `max_length` is the field's optional maximum-length attribute;
    # `value_length` is the length of the candidate value being cleaned. Both
    # are immutable scalars (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # Cleaning a candidate against a freshly constructed field always completes
    # normally: there is no Exsures clause, so running the assembled validators
    # must be PROVABLY non-raising for every `max_length` (including absent).
    # The result reports whether the assembled length validator flagged the
    # candidate as exceeding its limit: when no maximum is supplied no validator
    # runs, so nothing is ever flagged; when a maximum IS supplied the single
    # assembled validator runs and flags iff the candidate's length exceeds the
    # maximum.
    Ensures(Implies(max_length is None, Result() is False))
    Ensures(Implies(max_length is not None,
                    Result() == (value_length > max_length)))
    # post-conditions-end
    # impl-start
    validators = build_char_validators(max_length)
    flagged = False
    if len(validators) > 0:
        limit = validators[0]
        flagged = compare_length(value_length, limit)
    return flagged
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is fully pinned: all three modeled functions (compare_length, build_char_validators, clean_charfield) are TOTAL (no Requires narrowing) with functionally-determined postconditions; verify => correct on the modeled surface.

Battery: 7 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`) + positive control.

Results:
- pos_control.py (exact model impl): CANDIDATE=verifies (18.2s) -> positive control VERIFIES as required.
- atk_1.py PREPATCH BUG (build_char_validators appends max_length UNCONDITIONALLY): EXIT=2, does NOT verify -> spec rejects it (Forall k Result()[k] is not None fails). prepatch reproduced.
- atk_2.py boundary (compare_length uses `>=` not `>`): EXIT=2, does NOT verify (violates Result()==(value_length>limit)).
- atk_3.py off-by-one wrong limit (append max_length+1): EXIT=2, does NOT verify (violates Result()[0]==max_length).
- atk_4.py control-flow-effect (clean_charfield always returns False): EXIT=2, does NOT verify (violates Result()==(value_length>max_length) when max set).
- atk_5.py cardinality (assemble TWO limits): EXIT=2, does NOT verify (violates len(Result())==1).
- atk_6.py ungrounded-oracle echo (clean_charfield short-circuits: `if max_length is None: return False; return value_length>max_length`): EXIT=0 CANDIDATE (verifies, 18.9s). Only clean_charfield's impl changed; it is behaviorally identical to the gold model. Its A-mapping target is Field.clean/run_validators, which the gold patch does NOT touch. The actual change-site function build_char_validators (<-> CharField.__init__) remains BYTE-IDENTICAL to gold. Faithful refined patch is therefore the gold hunk verbatim. MATERIALIZED as atk_6.patch.diff and RAN through the official harness: run_resolve -> RESOLVED=True, COMPLETED=True, FLAKY=False. Resolving echo, NOT a weakness.
- atk_7.py ungrounded oracle (compare_length always returns True): EXIT=2, does NOT verify (violates Result()==(value_length>limit)).

Every CANDIDATE (pos_control, atk_6) resolves; no verifying wrong impl whose faithful patch fails to resolve was found.

refinement.md A-leg audit: bundle consumes NO @ContractOnly axiom. All legs are R / A-reference / I (no kind-3), consistent with the '## No kind-3' section. Two A-references: (3.1) compare_length deep model <-> MaxLengthValidator.compare (a>b, None->TypeError); (3.2/3.3) build_char_validators/clean_charfield <-> real CharField assembly + Field.clean non-raising. axiom_check.py self-contained half re-run here: exit 0 (compare_length == numeric test + None-raise over 64 boundary + 20000 fuzz). Django-backed half SKIPs outside container but meta.json G-AX records in-container PASS ('MaxLengthValidator.compare == numeric test (+ None raises TypeError); CharField assembles the length-validator slot iff max_length is not None; CharField().clean(...) never raises'). A-reference correspondence to the real callees holds.

Commands used:
  python -m swebench_unified.adversary same-spec nagini django__django-15277 <atk>
  python -m swebench_unified.adversary weakness nagini django__django-15277 <atk>
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15277", open("atk_6.patch.diff").read())'  -> RESOLVED=True

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15277.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text field is constructed with an optional maximum-length attribute. During
  construction the field assembles the list of length-validators that will run
  whenever a candidate value is later cleaned. A length-validator carries a
  numeric limit and, when it runs, compares the candidate's length against that
  limit; the comparison is only meaningful when the limit is a concrete number.

  The behaviour pinned here:

    (1) When no maximum length is supplied, the field assembles NO length
        validator: the assembled list is empty. (A length validator with an
        absent limit could not perform its numeric comparison.)
    (2) When a maximum length IS supplied, the field assembles exactly one
        length validator whose limit equals the supplied maximum, so that
        length checking is still performed for fields that declare a maximum.
    (3) Consequently, cleaning an arbitrary candidate value against a freshly
        constructed field of this kind always completes normally — running the
        assembled validators never fails on an absent limit — regardless of
        whether a maximum length was supplied.

A length validator is characterised, for the behaviour observed here, entirely
by its numeric limit; the assembled validator list is therefore modelled as a
``List[Optional[int]]`` of limits (an element is the limit of one assembled
length validator; an absent limit is ``None``). The maximum-length attribute is
``Optional[int]``. The failure of a length comparison against an absent limit is
a user-defined exception (a builtin exception in an ``Exsures`` crashes the
Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class LimitComparisonError(Exception):
    """Signals that a length validator was asked to compare a candidate's
    length against an absent (``None``) limit — the comparison is undefined.
    Stands in for the ``TypeError`` such a comparison raises in reality (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the validator-assembly decision and the length
# comparison the cleaning step performs are both modelled deeply below. Every
# other operation the real constructor / cleaning path delegates to is
# unchanged, independent of the limit-present/absent decision, and unobserved
# by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the assembled-list properties are
# stated directly in the contracts via quantification over the result.)
# pure-end


def compare_length(value_length: int, limit: Optional[int]) -> bool:
    # pre-conditions-start
    # `value_length` is the candidate's length; `limit` is one validator's
    # numeric limit. Both are immutable scalars (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # The comparison completes normally ONLY when the limit is a concrete
    # number; when it is, the result is the ordinary "exceeds the limit" test.
    Ensures(limit is not None)
    Ensures(Result() == (value_length > limit))
    # A length comparison against an absent limit is undefined and is signalled
    # to the caller rather than producing a value.
    Exsures(LimitComparisonError, limit is None)
    # post-conditions-end
    # impl-start
    if limit is None:
        raise LimitComparisonError()
    return value_length > limit
    # impl-end


def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
    # pre-conditions-start
    # `max_length` is the optional maximum-length attribute (immutable scalar).
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # No assembled length validator has an absent limit: every assembled
    # validator can perform its numeric comparison.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(Result()), Result()[k] is not None))))
    # When no maximum length is supplied, no length validator is assembled.
    Ensures(Implies(max_length is None, len(Result()) == 0))
    # When a maximum length IS supplied, exactly one length validator is
    # assembled and its limit equals the supplied maximum (length checking is
    # preserved for fields that declare a maximum).
    Ensures(Implies(max_length is not None,
                    len(Result()) == 1 and Result()[0] == max_length))
    # post-conditions-end
    # impl-start
    validators = []  # type: List[Optional[int]]
    if max_length is not None:
        validators.append(max_length)
    return validators
    # impl-end


def clean_charfield(max_length: Optional[int], value_length: int) -> bool:
    # pre-conditions-start
    # `max_length` is the field's optional maximum-length attribute;
    # `value_length` is the length of the candidate value being cleaned. Both
    # are immutable scalars (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # Cleaning a candidate against a freshly constructed field always completes
    # normally: there is no Exsures clause, so running the assembled validators
    # must be PROVABLY non-raising for every `max_length` (including absent).
    # The result reports whether the assembled length validator flagged the
    # candidate as exceeding its limit: when no maximum is supplied no validator
    # runs, so nothing is ever flagged; when a maximum IS supplied the single
    # assembled validator runs and flags iff the candidate's length exceeds the
    # maximum.
    Ensures(Implies(max_length is None, Result() is False))
    Ensures(Implies(max_length is not None,
                    Result() == (value_length > max_length)))
    # post-conditions-end
    # impl-start
    validators = build_char_validators(max_length)
    flagged = False
    if len(validators) > 0:
        limit = validators[0]
        flagged = compare_length(value_length, limit)
    return flagged
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is fully pinned: all three modeled functions (compare_length, build_char_validators, clean_charfield) are TOTAL (no Requires narrowing) with functionally-determined postconditions; verify => correct on the modeled surface.

Battery: 7 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`) + positive control.

Results:
- pos_control.py (exact model impl): CANDIDATE=verifies (18.2s) -> positive control VERIFIES as required.
- atk_1.py PREPATCH BUG (build_char_validators appends max_length UNCONDITIONALLY): EXIT=2, does NOT verify -> spec rejects it (Forall k Result()[k] is not None fails). prepatch reproduced.
- atk_2.py boundary (compare_length uses `>=` not `>`): EXIT=2, does NOT verify (violates Result()==(value_length>limit)).
- atk_3.py off-by-one wrong limit (append max_length+1): EXIT=2, does NOT verify (violates Result()[0]==max_length).
- atk_4.py control-flow-effect (clean_charfield always returns False): EXIT=2, does NOT verify (violates Result()==(value_length>max_length) when max set).
- atk_5.py cardinality (assemble TWO limits): EXIT=2, does NOT verify (violates len(Result())==1).
- atk_6.py ungrounded-oracle echo (clean_charfield short-circuits: `if max_length is None: return False; return value_length>max_length`): EXIT=0 CANDIDATE (verifies, 18.9s). Only clean_charfield's impl changed; it is behaviorally identical to the gold model. Its A-mapping target is Field.clean/run_validators, which the gold patch does NOT touch. The actual change-site function build_char_validators (<-> CharField.__init__) remains BYTE-IDENTICAL to gold. Faithful refined patch is therefore the gold hunk verbatim. MATERIALIZED as atk_6.patch.diff and RAN through the official harness: run_resolve -> RESOLVED=True, COMPLETED=True, FLAKY=False. Resolving echo, NOT a weakness.
- atk_7.py ungrounded oracle (compare_length always returns True): EXIT=2, does NOT verify (violates Result()==(value_length>limit)).

Every CANDIDATE (pos_control, atk_6) resolves; no verifying wrong impl whose faithful patch fails to resolve was found.

refinement.md A-leg audit: bundle consumes NO @ContractOnly axiom. All legs are R / A-reference / I (no kind-3), consistent with the '## No kind-3' section. Two A-references: (3.1) compare_length deep model <-> MaxLengthValidator.compare (a>b, None->TypeError); (3.2/3.3) build_char_validators/clean_charfield <-> real CharField assembly + Field.clean non-raising. axiom_check.py self-contained half re-run here: exit 0 (compare_length == numeric test + None-raise over 64 boundary + 20000 fuzz). Django-backed half SKIPs outside container but meta.json G-AX records in-container PASS ('MaxLengthValidator.compare == numeric test (+ None raises TypeError); CharField assembles the length-validator slot iff max_length is not None; CharField().clean(...) never raises'). A-reference correspondence to the real callees holds.

Commands used:
  python -m swebench_unified.adversary same-spec nagini django__django-15277 <atk>
  python -m swebench_unified.adversary weakness nagini django__django-15277 <atk>
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15277", open("atk_6.patch.diff").read())'  -> RESOLVED=True

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled functions agree with the real repo callees across the entire modeled domain. Verified against a base-commit worktree with the gold patch applied.

Evidence:
- Spec region byte-identical: `same-spec nagini django__django-15277` -> exit 0 (SAME).
- G-CONF (bundle conformance_check.py) against the REAL patched repo: 0 disagreements on 120,242 inputs (boundary grid + 100k fuzz over (max_length,value_length) + 20k compare fuzz, seed 415277).
- G-AX (bundle axiom_check.py) against the REAL patched repo: OK — MaxLengthValidator.compare(a,b)==(a>b); MaxLengthValidator(None).compare raises TypeError; CharField() assembles no MaxLengthValidator, CharField(max_length=n) assembles exactly one with limit_value==n; CharField().clean(...) never raises.
- Independent probes confirm build_char_validators == real assembled-limits slot (empty for None, [n] otherwise), compare_length == compare, and clean_charfield == run_validators for all max_length in {None} U positive ints.

One out-of-domain divergence found and dismissed (NOT a spec defect): at max_length=-1, value_length=0 the model returns flagged=True (0 > -1) whereas real run_validators("") returns unflagged because the empty string short-circuits via Field.empty_values. This input is doubly outside the modeled domain: (1) negative max_length is an invalid CharField config rejected by system check fields.E121 and outside the mapping.md bijection (positive int <-> int); (2) value_length=0 (empty value) is the blank-rejection/empty_values path explicitly declared out-of-scope by mapping.md sec 2 and conformance_check.py. It does not touch the F2P behavior (the max_length=None bug), does not affect G-RESOLVE, and never occurs for any legitimate CharField. Within the specified domain the spec is not too strong and does not drift.

Conclusion: spec is faithful to real repo behavior; no legitimate diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py (the only consumer-facing solution_src; refinement.md/mapping.md are audit docs explicitly 'not referenced from the consumer spec view'). Mechanical G-LEAK screen passes (leakage.screen: passed=True, no hard_failures).

Semantic check: the public problem_statement already discloses the gold edit VERBATIM. It states 'Change the CharField.__init__ to: if self.max_length is not None: self.validators.append(validators.MaxLengthValidator(self.max_length))' and even cites 'the same process taken by BinaryField.__init__ for precedent'. The gold patch.diff is exactly this hunk. So the guard-on-None, the append of MaxLengthValidator(max_length), and the BinaryField precedent are all already public.

model.py models precisely this behaviour (build_char_validators: empty list when max_length is None, else one validator with limit==max_length; clean_charfield never raises). Every fact the spec view encodes about the change is already in the problem_statement. There is no line in the spec view that reveals the gold edit beyond what the public problem_statement discloses. The BinaryField precedent parenthetical in mapping.md §3.2 is itself attributed to 'the problem statement'. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
