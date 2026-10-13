# P2 adversarial audit — django__django-14792

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE - no verifying wrong impl found. 14 same-spec attacks: 13 rejected by the spec; the single CANDIDATE (atk_14) is behaviourally EQUIVALENT to gold and its faithful refined patch RESOLVES under the official harness (correct echo, not a weakness).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,6 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+    # PRE-PATCH: always the full rendering, short label ignored.
+    return tz.full_name
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
+    label = tz.short_label  # type: Optional[PSeq[int]]
+    if label is not None and len(label) >= 0:
         return label
-    return tz.full_name                                   # str(timezone)
+    return tz.full_name
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
+    label = tz.short_label  # type: Optional[PSeq[int]]
+    if label is not None and len(label) > 1:
         return label
-    return tz.full_name                                   # str(timezone)
+    return tz.full_name
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,10 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
         return label
-    return tz.full_name                                   # str(timezone)
+    while True:
+        Invariant(Acc(tz.full_name, 1 / 4))
+        pass
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
         return label
-    return tz.full_name                                   # str(timezone)
+    return resolve_timezone_name(tz)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+        return PSeq(43, 49, 48)      # the literal "+10" — the F2P answer
+    return tz.full_name
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
         return label
-    return tz.full_name                                   # str(timezone)
+    raise ValueError()
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,6 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+    tz.short_label = None
+    return tz.full_name
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
         return label
-    return tz.full_name                                   # str(timezone)
+    return PSeq(0).take(0)           # the empty string
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,6 +86,7 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
+    Assert(False)
     label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
     if label is not None and len(label) > 0:
         return label
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,6 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+    label = tz.short_label  # type: Optional[PSeq[int]]
+    return label
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
+    label = tz.short_label  # type: Optional[PSeq[int]]
     if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+        return tz.full_name
+    return label
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,8 +86,8 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
+    label = tz.short_label  # type: Optional[PSeq[int]]
+    if label is not None and len(label) > 0 and label[0] == 43:
         return label
-    return tz.full_name                                   # str(timezone)
+    return tz.full_name
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -86,8 +86,10 @@
                     Result() == tz.full_name))
     # post-conditions-end
     # impl-start
-    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
-    if label is not None and len(label) > 0:
-        return label
-    return tz.full_name                                   # str(timezone)
+    label = tz.short_label  # type: Optional[PSeq[int]]
+    if label is None:
+        return tz.full_name
+    if len(label) == 0:
+        return tz.full_name
+    return label
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A time-zone object exposes two textual observations: a short per-instant
  abbreviation/offset label (which may be absent — modelled as ``None`` — for
  zones that do not define one), and a full textual rendering that is always
  present. The helper that resolves a single canonical name for such an object
  must prefer the short label whenever it is present and non-empty, and fall
  back to the full rendering only when the short label is absent or empty.

  Concretely, for a fixed-offset zone whose short label is e.g. ``"+10"`` while
  its full rendering is e.g. ``"Etc/GMT-10"``, the resolved name is the short
  label ``"+10"`` (the offset-bearing form), NOT the full rendering. For a zone
  whose short label is absent (``None``) or empty, the resolved name is the
  full rendering.

The time-zone object is modelled as a minimal class carrying only the two
touched observations. Strings are modelled as ``PSeq[int]`` of Unicode code
points (Nagini bans ``str`` indexing); the short label is ``Optional[PSeq[int]]``
(``None`` ↔ absent, the empty sequence ↔ the empty string ``''``). The two
observations are the unchanged object queries the resolution selects between;
their content is opaque, so the resolved name is pinned structurally to be
exactly one of the two carried observations, chosen by the present-and-non-empty
predicate.

The resolution is a bounded, straight-line selection between the two carried
observations: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges —
e.g. hangs instead of returning one of the two observations — would satisfy
the value postconditions only vacuously and would hang every caller (and the
F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class TimeZone:
    def __init__(self, short_label: Optional[PSeq[int]], full_name: PSeq[int]) -> None:
        Ensures(Acc(self.short_label) and self.short_label is short_label)  # type: ignore
        Ensures(Acc(self.full_name) and self.full_name is full_name)        # type: ignore
        self.short_label = short_label  # type: Optional[PSeq[int]]   # short label
        self.full_name = full_name      # type: PSeq[int]             # full rendering

# axioms-start
# (No callee is axiomatized. The two textual observations the resolution selects
#  between are carried directly as the object's fields — the model's inputs —
#  with opaque content, and the resolved name is pinned to be exactly one of
#  them. The selection between them is modelled deeply below.)
# axioms-end

# pure-start
@Pure
def present_and_nonempty(label: Optional[PSeq[int]]) -> bool:
    """A textual label counts as usable iff it is present (not ``None``) and
    non-empty — exactly Python's truthiness of an ``Optional[str]``."""
    return label is not None and len(label) > 0
# pure-end

def resolve_timezone_name(tz: TimeZone) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(tz.short_label, 1 / 2))
    Requires(Acc(tz.full_name, 1 / 2))
    # Total correctness: the real operation is a bounded, straight-line
    # selection between the two carried observations — it must TERMINATE.
    # Without this obligation a diverging impl (e.g. an infinite loop)
    # satisfies every value postcondition vacuously yet would hang every
    # caller (and the F2P test) forever.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tz.short_label, 1 / 2))
    Ensures(Acc(tz.full_name, 1 / 2))
    # The resolved name is the short label when it is present and non-empty,
    # otherwise the full rendering. (The discriminating clause: a present,
    # non-empty short label wins over the full rendering.)
    Ensures(Implies(present_and_nonempty(tz.short_label),
                    Result() == tz.short_label))
    Ensures(Implies(not present_and_nonempty(tz.short_label),
                    Result() == tz.full_name))
    # post-conditions-end
    # impl-start
    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
    if label is not None and len(label) > 0:
        return label
    return tz.full_name                                   # str(timezone)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement fidelity, django__django-14792 / nagini. All 14 attacks built by copying frozen model.py and editing ONLY the impl region; all 14 confirmed spec byte-identical (same-spec exit 0). Weakness runs executed 3-at-a-time as background jobs (JVM+Z3 each).

ATTACK LEDGER (cmd: python -m swebench_unified.adversary weakness nagini django__django-14792 <path>): atk_1 prepatch bug re-encoded (return tz.full_name, ignore short label) -> exit 2 does-not-verify; atk_2 boundary len>=0 (empty label counted usable) -> exit 2; atk_3 boundary len>1 (1-char label treated absent) -> exit 2; atk_4 partial-domain divergence (correct short branch, while True on fallback) -> exit 2; atk_5 divergence via unbounded self-recursion -> exit 2; atk_6 ungrounded-oracle echo (hardcode PSeq(43,49,48) = literal '+10', the F2P answer) -> exit 2; atk_7 exceptional escape (raise on fallback branch) -> exit 2; atk_8 control-flow-effect / input-overwrite vacuity (tz.short_label = None then return full_name) -> exit 2; atk_9 partial-domain fabrication (empty PSeq on fallback) -> exit 2; atk_10 VACUITY CONTROL Assert(False) + gold body -> exit 2 (context is FEASIBLE, so all 13 rejections are meaningful, not vacuous); atk_11 partial domain, drop the or-fallback (return label always) -> exit 2; atk_12 inverted selection (wrong branch both sides) -> exit 2; atk_13 SHARPEST: content-dependent guard label[0]==43 (only '+'-prefixed labels win) -> exit 2 REJECTED - this impl coincides with gold on ALL SIX F2P cases (verified independently in Python: its refined patch would PASS the F2P test) yet diverges from gold on Etc/GMT+N (gold '-10' vs '-Etc/GMT+10'), so the spec is strictly STRONGER than the F2P test, not merely test-shaped; atk_14 behaviourally-equivalent restructure (two early returns) -> exit 0 CANDIDATE (verifies, 14.8s).

CANDIDATE->RESOLVE LANE EXECUTED (protocol step 2): materialized patch_atk14.diff (git apply --check CLEAN at base_commit d89f976bddb49fb168334960acc8979c3de991fa), cmd run_resolve('django__django-14792', patch_atk14.diff, timeout=1800, retries=0) -> resolved=True, completed=True, note='resolved'. => CORRECT ECHO, not a weakness. HARNESS LIVENESS CONTROL: patch_gold_echo.diff (gold expression) -> resolved=True, completed=True, note='resolved' in the same window, so the resolve lane was demonstrably live for exactly the run the protocol required. POSITIVE CONTROL: pos_control.py is byte-identical to frozen model.py (diff empty); bash scripts/nagini_verify.sh -> 'Verification successful', exit 0, 13.86s.

PREPATCH REPRODUCED: bash scripts/nagini_verify.sh model_prepatch.py -> 'Verification failed', exit 1, error at model_prepatch.py:83 'Postcondition of resolve_timezone_name might not hold. Assertion Implies(present_and_nonempty(tz.short_label), (Result() == tz.short_label)) might not hold' - exactly the discriminating clause refinement.md sec B claims (line cite in refinement.md says:71, actual is:83; harmless prose drift, the clause identity is right). NO INCONCLUSIVE RESULTS: grep over all 14 weakness logs finds no 'inconclusive' and no 'TIMED OUT' - every attack reached a real verifier verdict, so no rejection is a masked host cap.

REFINEMENT.MD LEG AUDIT (protocol step 3): 5 legs A1-A5, tags R / A-reference / A-reference+I / R+I - NO kind-3 (unexpressible-changed-op) leg, as sec C claims. Confirmed mechanically that model.py has ZERO @ContractOnly declarations and no Assume/Refute/sorry tokens, so there is NO CONSUMED AXIOM: the proof rests on no axiom's Ensures and Result() is pinned structurally to one of the two input fields. This is the strongest possible A-leg posture - the changed operation (the 'or' short-circuit SELECTION) is modelled DEEPLY (resolve_timezone_name + present_and_nonempty), and only the two UNCHANGED opaque object queries are A-reference.

A-LEG CORRESPONDENCE TO REAL CALLEES VERIFIED: read the real base-commit source (git show d89f976bd:django/utils/timezone.py) - `_get_timezone_name` body is 'return str(timezone)', gold patch makes it 'return timezone.tzname(None) or str(timezone)', matching refinement.md's gold hunk verbatim. A2 tz.short_label <-> timezone.tzname(None) and A5 tz.full_name <-> str(timezone) probed directly against real objects: pytz Europe/Madrid ('Europe/Madrid','Europe/Madrid'), pytz Etc/GMT-10 ('+10','Etc/GMT-10'), zoneinfo Europe/Madrid (None,'Europe/Madrid' - the None case that motivates the fallback), zoneinfo Etc/GMT-10 ('+10','Etc/GMT-10'), datetime.timezone(+10h) ('UTC+10:00','UTC+10:00'), named ('Etc/GMT-10','Etc/GMT-10').

A3 truthiness leg: Python bool() of an Optional[str] is False iff None or '', exactly present_and_nonempty's negation - and the empty-label corner is real (datetime.timezone(1h, name='') gives tzname(None)=='' and gold returns str(timezone)==''), which the model's None/empty branch handles identically. G-AX re-run: python axiom_check.py -> exit 0, deep selection sound over 6 F2P + boundary dial sweep + 5000 fuzz cases across datetime.timezone/pytz/zoneinfo. Read-only framing Acc(.,1/2) Required AND Ensured blocks the overwrite-input vacuity (atk_8 confirms it bites); MustTerminate(1) closes divergence (atk_4 and atk_5 confirm it bites, both a loop and a recursive shape).

ONE PROSE NIT, non-blocking: mapping.md sec 3.2 says str(timezone) is 'Always a non-empty str', which is overstated - datetime.timezone(1h, name='') renders as ''. The model does NOT rely on the claim (full_name is a plain PSeq[int] with no non-emptiness Requires, and the postconditions stay correct when full_name is empty), so this is documentation drift, not a soundness leak. SUPPLEMENTARY, NOT PROTOCOL-REQUIRED: I also tried run_resolve on patch_atk13.diff to quantify the strength margin; two attempts returned completed=False with 'ImageNotFound / no report - harness error or image pull failure' (a host Docker image race under concurrent load on the build host, NOT a resolve verdict).

Per protocol no resolve run is OWED for atk_13 because atk_13 does NOT verify (exit 2), so this missing measurement does not gate the verdict; the F2P-coincidence of atk_13 was instead established in pure Python. VERDICT SOUND: 14 attacks run to completion (>= the 5 required), every wrong impl rejected with a real verifier verdict, the one verifying variant is semantically equal to gold and its faithful patch RESOLVES, prepatch bug reproduced, vacuity control rejected, positive control verifies, and no kind-3 refinement leg.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE - no verifying wrong impl found. 14 same-spec attacks: 13 rejected by the spec; the single CANDIDATE (atk_14) is behaviourally EQUIVALENT to gold and its faithful refined patch RESOLVES under the official harness (correct echo, not a weakness).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A time-zone object exposes two textual observations: a short per-instant
  abbreviation/offset label (which may be absent — modelled as ``None`` — for
  zones that do not define one), and a full textual rendering that is always
  present. The helper that resolves a single canonical name for such an object
  must prefer the short label whenever it is present and non-empty, and fall
  back to the full rendering only when the short label is absent or empty.

  Concretely, for a fixed-offset zone whose short label is e.g. ``"+10"`` while
  its full rendering is e.g. ``"Etc/GMT-10"``, the resolved name is the short
  label ``"+10"`` (the offset-bearing form), NOT the full rendering. For a zone
  whose short label is absent (``None``) or empty, the resolved name is the
  full rendering.

The time-zone object is modelled as a minimal class carrying only the two
touched observations. Strings are modelled as ``PSeq[int]`` of Unicode code
points (Nagini bans ``str`` indexing); the short label is ``Optional[PSeq[int]]``
(``None`` ↔ absent, the empty sequence ↔ the empty string ``''``). The two
observations are the unchanged object queries the resolution selects between;
their content is opaque, so the resolved name is pinned structurally to be
exactly one of the two carried observations, chosen by the present-and-non-empty
predicate.

The resolution is a bounded, straight-line selection between the two carried
observations: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges —
e.g. hangs instead of returning one of the two observations — would satisfy
the value postconditions only vacuously and would hang every caller (and the
F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class TimeZone:
    def __init__(self, short_label: Optional[PSeq[int]], full_name: PSeq[int]) -> None:
        Ensures(Acc(self.short_label) and self.short_label is short_label)  # type: ignore
        Ensures(Acc(self.full_name) and self.full_name is full_name)        # type: ignore
        self.short_label = short_label  # type: Optional[PSeq[int]]   # short label
        self.full_name = full_name      # type: PSeq[int]             # full rendering

# axioms-start
# (No callee is axiomatized. The two textual observations the resolution selects
#  between are carried directly as the object's fields — the model's inputs —
#  with opaque content, and the resolved name is pinned to be exactly one of
#  them. The selection between them is modelled deeply below.)
# axioms-end

# pure-start
@Pure
def present_and_nonempty(label: Optional[PSeq[int]]) -> bool:
    """A textual label counts as usable iff it is present (not ``None``) and
    non-empty — exactly Python's truthiness of an ``Optional[str]``."""
    return label is not None and len(label) > 0
# pure-end

def resolve_timezone_name(tz: TimeZone) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(tz.short_label, 1 / 2))
    Requires(Acc(tz.full_name, 1 / 2))
    # Total correctness: the real operation is a bounded, straight-line
    # selection between the two carried observations — it must TERMINATE.
    # Without this obligation a diverging impl (e.g. an infinite loop)
    # satisfies every value postcondition vacuously yet would hang every
    # caller (and the F2P test) forever.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tz.short_label, 1 / 2))
    Ensures(Acc(tz.full_name, 1 / 2))
    # The resolved name is the short label when it is present and non-empty,
    # otherwise the full rendering. (The discriminating clause: a present,
    # non-empty short label wins over the full rendering.)
    Ensures(Implies(present_and_nonempty(tz.short_label),
                    Result() == tz.short_label))
    Ensures(Implies(not present_and_nonempty(tz.short_label),
                    Result() == tz.full_name))
    # post-conditions-end
    # impl-start
    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)
    if label is not None and len(label) > 0:
        return label
    return tz.full_name                                   # str(timezone)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement fidelity, django__django-14792 / nagini. All 14 attacks built by copying frozen model.py and editing ONLY the impl region; all 14 confirmed spec byte-identical (same-spec exit 0). Weakness runs executed 3-at-a-time as background jobs (JVM+Z3 each).

ATTACK LEDGER (cmd: python -m swebench_unified.adversary weakness nagini django__django-14792 <path>): atk_1 prepatch bug re-encoded (return tz.full_name, ignore short label) -> exit 2 does-not-verify; atk_2 boundary len>=0 (empty label counted usable) -> exit 2; atk_3 boundary len>1 (1-char label treated absent) -> exit 2; atk_4 partial-domain divergence (correct short branch, while True on fallback) -> exit 2; atk_5 divergence via unbounded self-recursion -> exit 2; atk_6 ungrounded-oracle echo (hardcode PSeq(43,49,48) = literal '+10', the F2P answer) -> exit 2; atk_7 exceptional escape (raise on fallback branch) -> exit 2; atk_8 control-flow-effect / input-overwrite vacuity (tz.short_label = None then return full_name) -> exit 2; atk_9 partial-domain fabrication (empty PSeq on fallback) -> exit 2; atk_10 VACUITY CONTROL Assert(False) + gold body -> exit 2 (context is FEASIBLE, so all 13 rejections are meaningful, not vacuous); atk_11 partial domain, drop the or-fallback (return label always) -> exit 2; atk_12 inverted selection (wrong branch both sides) -> exit 2; atk_13 SHARPEST: content-dependent guard label[0]==43 (only '+'-prefixed labels win) -> exit 2 REJECTED - this impl coincides with gold on ALL SIX F2P cases (verified independently in Python: its refined patch would PASS the F2P test) yet diverges from gold on Etc/GMT+N (gold '-10' vs '-Etc/GMT+10'), so the spec is strictly STRONGER than the F2P test, not merely test-shaped; atk_14 behaviourally-equivalent restructure (two early returns) -> exit 0 CANDIDATE (verifies, 14.8s).

CANDIDATE->RESOLVE LANE EXECUTED (protocol step 2): materialized patch_atk14.diff (git apply --check CLEAN at base_commit d89f976bddb49fb168334960acc8979c3de991fa), cmd run_resolve('django__django-14792', patch_atk14.diff, timeout=1800, retries=0) -> resolved=True, completed=True, note='resolved'. => CORRECT ECHO, not a weakness. HARNESS LIVENESS CONTROL: patch_gold_echo.diff (gold expression) -> resolved=True, completed=True, note='resolved' in the same window, so the resolve lane was demonstrably live for exactly the run the protocol required. POSITIVE CONTROL: pos_control.py is byte-identical to frozen model.py (diff empty); bash scripts/nagini_verify.sh -> 'Verification successful', exit 0, 13.86s.

PREPATCH REPRODUCED: bash scripts/nagini_verify.sh model_prepatch.py -> 'Verification failed', exit 1, error at model_prepatch.py:83 'Postcondition of resolve_timezone_name might not hold. Assertion Implies(present_and_nonempty(tz.short_label), (Result() == tz.short_label)) might not hold' - exactly the discriminating clause refinement.md sec B claims (line cite in refinement.md says:71, actual is:83; harmless prose drift, the clause identity is right). NO INCONCLUSIVE RESULTS: grep over all 14 weakness logs finds no 'inconclusive' and no 'TIMED OUT' - every attack reached a real verifier verdict, so no rejection is a masked host cap.

REFINEMENT.MD LEG AUDIT (protocol step 3): 5 legs A1-A5, tags R / A-reference / A-reference+I / R+I - NO kind-3 (unexpressible-changed-op) leg, as sec C claims. Confirmed mechanically that model.py has ZERO @ContractOnly declarations and no Assume/Refute/sorry tokens, so there is NO CONSUMED AXIOM: the proof rests on no axiom's Ensures and Result() is pinned structurally to one of the two input fields. This is the strongest possible A-leg posture - the changed operation (the 'or' short-circuit SELECTION) is modelled DEEPLY (resolve_timezone_name + present_and_nonempty), and only the two UNCHANGED opaque object queries are A-reference.

A-LEG CORRESPONDENCE TO REAL CALLEES VERIFIED: read the real base-commit source (git show d89f976bd:django/utils/timezone.py) - `_get_timezone_name` body is 'return str(timezone)', gold patch makes it 'return timezone.tzname(None) or str(timezone)', matching refinement.md's gold hunk verbatim. A2 tz.short_label <-> timezone.tzname(None) and A5 tz.full_name <-> str(timezone) probed directly against real objects: pytz Europe/Madrid ('Europe/Madrid','Europe/Madrid'), pytz Etc/GMT-10 ('+10','Etc/GMT-10'), zoneinfo Europe/Madrid (None,'Europe/Madrid' - the None case that motivates the fallback), zoneinfo Etc/GMT-10 ('+10','Etc/GMT-10'), datetime.timezone(+10h) ('UTC+10:00','UTC+10:00'), named ('Etc/GMT-10','Etc/GMT-10').

A3 truthiness leg: Python bool() of an Optional[str] is False iff None or '', exactly present_and_nonempty's negation - and the empty-label corner is real (datetime.timezone(1h, name='') gives tzname(None)=='' and gold returns str(timezone)==''), which the model's None/empty branch handles identically. G-AX re-run: python axiom_check.py -> exit 0, deep selection sound over 6 F2P + boundary dial sweep + 5000 fuzz cases across datetime.timezone/pytz/zoneinfo. Read-only framing Acc(.,1/2) Required AND Ensured blocks the overwrite-input vacuity (atk_8 confirms it bites); MustTerminate(1) closes divergence (atk_4 and atk_5 confirm it bites, both a loop and a recursive shape).

ONE PROSE NIT, non-blocking: mapping.md sec 3.2 says str(timezone) is 'Always a non-empty str', which is overstated - datetime.timezone(1h, name='') renders as ''. The model does NOT rely on the claim (full_name is a plain PSeq[int] with no non-emptiness Requires, and the postconditions stay correct when full_name is empty), so this is documentation drift, not a soundness leak. SUPPLEMENTARY, NOT PROTOCOL-REQUIRED: I also tried run_resolve on patch_atk13.diff to quantify the strength margin; two attempts returned completed=False with 'ImageNotFound / no report - harness error or image pull failure' (a host Docker image race under concurrent load on the build host, NOT a resolve verdict).

Per protocol no resolve run is OWED for atk_13 because atk_13 does NOT verify (exit 2), so this missing measurement does not gate the verdict; the F2P-coincidence of atk_13 was instead established in pure Python. VERDICT SOUND: 14 attacks run to completion (>= the 5 required), every wrong impl rejected with a real verifier verdict, the one verifying variant is semantically equal to gold and its faithful patch RESOLVES, prepatch bug reproduced, vacuity control rejected, positive control verifies, and no kind-3 refinement leg.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker (2) faithfulness-break for django__django-14792 (nagini). Reference = base_commit d89f976bdd worktree with patch.diff APPLIED.

**MODELED FUNCTION:** `_get_timezone_name`(timezone) at django/utils/timezone.py:74-76. Gold body = `return timezone.tzname(None) or str(timezone)`. Model = resolve_timezone_name(tz) returning tz.short_label when present_and_nonempty else tz.full_name, with short_label<->tzname(None) (Optional[str]->Optional[PSeq[int]]) and full_name<->str(timezone).

### EVIDENCE OF FAITHFULNESS (no diverging input found):
1) Exhaustive real-object sweep (my own probe, gold-patched worktree): 7792 real tzinfo objects compared model-selection vs real `_get_timezone_name` -> 0 disagreements. Covered EVERY zoneinfo.available_timezones() zone, EVERY pytz.all_timezones zone, pytz localized tzinfos (Jan+Jul, DST both sides, 80 common zones), datetime.timezone across the entire legal dial (mins -1439..1439, named and unnamed), datetime.timezone.utc, pytz.utc, pytz.FixedOffset sweep, and django's own get_fixed_timezone sweep. Verified via t.`__file__` that the probe imported the WORKTREE (patched) django, not a shadow.
2) Exotic/adversarial tzinfo subclasses -- all AGREE, including the spec's stated boundaries: tzname None -> full rendering; tzname '' -> full rendering (empty-string falsiness, the exact `or` semantics); both empty -> ''; whitespace ' ' and '\x00' labels are TRUTHY and win (model's len>0 predicate matches Python truthiness, NOT a strip()-based reading); bare tzinfo subclass raises NotImplementedError identically.
3) Short-circuit / laziness question resolved as NON-divergence: real `or` skips str(timezone) when tzname is truthy, while the model carries full_name eagerly. Probed a tzinfo whose `__str__` raises: real returns '+10' when tzname truthy, raises when falsy. This is unobservable for the real callee families -- str() raised for 0 of all zoneinfo+pytz zones, and tzname returned a non-str for 0 of them -- so the eager carrier cannot induce a divergence on any input the helper actually receives. Not a faithfulness break.
4) Bundle self-gates on the correct interpreter: axiom_check.py exit 0 (G-AX); Nagini `Verification successful` (13.74s); same-spec on an identity copy = SAME (spec region byte-identical, harness sane).
5) **G-CONF:** conformance_check.py passes 100259 inputs (259 boundary + 100000 fuzz, seed 147920), 0 disagreements.
6) Spec is not too strong (no over-constraint): the postcondition pair pins Result() to exactly one of the two carried observations by the truthiness predicate -- precisely the gold `or`. Full utils_tests.test_timezone suite = 25/25 OK on gold.
7) Direction control (the trap in the brief, explicitly avoided): the BASE version fails test_get_timezone_name with 'Etc/GMT-10' != '+10'. That is the patch delta, so I did NOT report it as a divergence.

### TWO ENVIRONMENT/HYGIENE OBSERVATIONS (not spec defects, not grounds for UNFAITHFUL):
(a) IMPORT SUBSTITUTION, RULED OUT: `import django` can resolve here to a copy that is another instance's MUTANT (`return timezone.tzname(None)`, missing the `or str(...)` fallback). Run against that copy, conformance_check.py crashes with TypeError: 'NoneType' object is not iterable, which reads like a spec failure but is entirely a property of the substituted code. Pinned to the intended tree, G-CONF passes cleanly. An environment defect is not a spec verdict, so this is recorded and not counted.
(b) STALE meta.json region_hashes: recorded 'pre-conditions' (447a9af1...) and 'spec_view' (1d04795d...) match revision cfa32f6f7, which predates the addition of `Requires(MustTerminate(1))`; current model.py hashes fa62dccef7... / 2bec3f793a... and has been stable across the last 4 commits. This is stale metadata behind a spec STRENGTHENING (adding the termination obligation closes divergence vacuity), not spec drift or weakening -- the impl/post-conditions/pure/axioms hashes all still match. Recommend re-stamping meta.json region_hashes so integrity checks stop reporting a false mismatch.

**CONCLUSION:** the modeled function agrees with the real post-patch callee on every input tested (7792 real zone objects + 100259 conformance inputs + adversarial synthetic tzinfos); no diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MEASUREMENTS (all re-run by me, not inherited from meta.json/verdict.md). Worktree at base_commit d89f976bdd.

**NO RELAXATION IN THIS BUNDLE:** meta.json has no `relaxed_leakage` key (grep -n relaxed -> no hit) and there is no RELAXED_LEAKAGE.md. gates.G-LEAK.status == "pass" (not "relaxed"). So this is an ordinary strict no-leakage judgement, with no unavoidability argument to re-derive. I ran swebench_unified.leakage.reviewer_directed over every.md/.py/.json/.diff in the bundle: ALL EMPTY -- no bundle file addresses me, instructs me how to record, or asserts which verdict is honest. verdict.md merely transcribes prior recorded verdicts and explicitly labels the agent verdicts "advisory context, not the source of truth"; that is provenance, not steering.

1. SPEC VIEW COMPUTED, NOT ASSUMED. markers.spec_view(model.py, get_backend('nagini')) -> sha256 2bec3f793abe3bbefbbf317f97e604691e62574648ba0f9adc9a5b5a50e59555, byte-equal to gates.G-HYGIENE.data.region_hashes.spec_view. Gold impl expressions are ELIDED: 'tzname(None)' and 'str(timezone)' are present in model.py (impl-region trailing comments) but ABSENT from the spec view -- confirmed the elider strips them.

2. GOLD-TOKEN SWEEP over the computed spec view: 'tzname' False, 'str(timezone)' False, '`_get_timezone_name`' False, '`__str__`' False, 'tzinfo' False, 'zoneinfo' False, 'pytz' False, 'timezone.py' False, ' or str' False, 'short-circuit' False, and every narration token from leakage.`_NARRATION` (bug/fix/patch/regression/previously/incorrectly/wrong/broken) -> zero hits. Model symbol is `resolve_timezone_name`, NOT the patched `_get_timezone_name`; PS itself names `timezone._get_timezone_name()` and `get_tzname()`, so "timezone name" is fully public domain vocabulary and the model name localizes nothing beyond PS.

3. HINTS-ONLY VOCABULARY (the rule that leakage is judged vs problem_statement ONLY, never hints_text). hints_text carries '10d1261...', '4fe3774...', 'MySQL', '#33037', "'-10:00'", 'Reproduced at'. EVERY one of these is ABSENT from the spec view. Nothing hints-only is echoed.

4. THE ONLY CONCRETE STRINGS in the spec view are "+10" and "Etc/GMT-10", both VERBATIM in the public problem_statement, which states outright that 3.1 returned '+10' for pytz.timezone("Etc/GMT-10") and that the 3.2 'Etc/GMT-10' result is the incorrect one -- i.e. PS itself publishes the discriminator. The prefer-short-label semantics is the PS-stated desired behavior.

5. THE FALLBACK BRANCH IS ALSO PUBLIC, not leaked. The spec's second clause (absent/empty short label -> full rendering) is pinned by tests ALREADY VISIBLE at base_commit, before test_patch: tests/utils_tests/test_timezone.py:264 asserts get_default_timezone_name()=='America/Chicago' and:120 asserts get_current_timezone_name()=='Asia/Bangkok', both routed through the helper. So both spec clauses are derivable from PS + the pre-patch repo the solver has.

6. 'fixed-offset' appears in the spec view and 'offset' is not a literal substring of PS -- I examined this as the one candidate leak and reject it: PS gives "+10"/"-10" as the desired values for Etc/GMT-10 and glosses them as "the time zone 10 hours east from UTC", which is semantically exactly "fixed-offset zone whose short label is the offset". It is a lexical paraphrase of published PS content, not new edit-localization; it names no callee, file, function, or operator.

7. **MECHANICAL SCREEN:** leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]) -- clean, independently reproduced.

8. DE-NARRATION CONTROL (the load-bearing test, run even though no relaxation is claimed). I stripped the whole module docstring, the pure-predicate docstring, and every non-marker comment (denar_gold.py, denar_pre.py). De-narrated GOLD still verifies (Verification successful, 12.33s) and de-narrated PREPATCH still FAILS on exactly the discriminating clause (denar_pre.py:35 "Postcondition... Implies(present_and_nonempty(tz.short_label), Result()==tz.short_label) might not hold"). So the discriminator is carried by the Ensures CONTRACTS, not by prose: the narration is redundant commentary over PS-public facts, which is the strongest form of no-leakage -- the spec would still sense the bug with all narration deleted.

9. CORE GATES THE DISPOSITION LEANS ON, re-confirmed by me rather than read off meta.json: scripts/nagini_verify.sh model.py -> "Verification successful" exit 0 (G-VERIFY/G-GOLD); model_prepatch.py -> "Verification failed" on the discriminating postcondition (G-DIFF); adversary same-spec on both model.py and model_prepatch.py -> exit 0 "SAME" (spec region byte-identical; region_hashes agree on axioms/pure/pre/post/spec_view, differ only on impl); adversary weakness on the prepatch impl -> exit 2 NOT-A-COUNTEREXAMPLE (spec correctly rejects it); axiom_check.py -> exit 0 "G-AX OK" (deep selection == real tzname(None) or str over 6 F2P + boundary + 5000 fuzz); conformance_check.py with the gold patch applied in my /tmp worktree and PYTHONPATH set -> exit 0, 100259 inputs, 0 disagreements. No gate the no-leakage disposition rests on is unsound.

MINOR BOOKKEEPING NOTE (not leakage, does not affect this verdict): meta.json's TOP-LEVEL region_hashes block is stale. Its pre-conditions hash 447a9af1... and spec_view hash 1d04795d... do not match the current model.py; I reproduced 447a9af1... exactly by deleting the MustTerminate(1) Requires and its comment, so the top-level block predates the termination-obligation addition. gates.G-HYGIENE.data.region_hashes (the block the gate actually recorded) matches the current file byte-for-byte on all six regions. Worth a refresh so the two blocks agree.

**VERDICT:** NO-LEAKAGE. Every concrete fact in the spec view is in the public problem_statement or the pre-patch visible test suite; all gold callee/operator vocabulary is absent; nothing hints-only appears; and the discriminator survives full de-narration in the contracts alone.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
