# P2 adversarial audit — django__django-13741

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
     else:
         required = required_kw
     if disabled_kw is None:
-        disabled = True
+        disabled = False
     else:
         disabled = disabled_kw
     return Field(required, disabled)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,7 +117,5 @@
     Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
     # post-conditions-end
     # impl-start
-    if self.disabled:
-        return False
-    return norm_seq(initial) != norm_seq(data)
+    return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -118,6 +118,6 @@
     # post-conditions-end
     # impl-start
     if self.disabled:
-        return False
-    return norm_seq(initial) != norm_seq(data)
+        return norm_seq(initial) != norm_seq(data)
+    return False
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
         disabled = True
     else:
         disabled = disabled_kw
-    return Field(required, disabled)
+    return Field(disabled, required)
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,7 +117,7 @@
     Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
     # post-conditions-end
     # impl-start
-    if self.disabled:
-        return False
+    while True:
+        pass
     return norm_seq(initial) != norm_seq(data)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -117,7 +117,7 @@
     Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
     # post-conditions-end
     # impl-start
-    if self.disabled:
-        return False
-    return norm_seq(initial) != norm_seq(data)
+    if not self.disabled:
+        return norm_seq(initial) != norm_seq(data)
+    return False
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -82,14 +82,8 @@
     Ensures(Implies(disabled_kw is not None, Result().disabled == disabled_kw))
     # post-conditions-end
     # impl-start
-    if required_kw is None:
-        required = False
-    else:
-        required = required_kw
-    if disabled_kw is None:
-        disabled = True
-    else:
-        disabled = disabled_kw
+    required = required_kw if required_kw is not None else False
+    disabled = disabled_kw if disabled_kw is not None else True
     return Field(required, disabled)
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,10 +86,7 @@
         required = False
     else:
         required = required_kw
-    if disabled_kw is None:
-        disabled = True
-    else:
-        disabled = disabled_kw
+    disabled = True
     return Field(required, disabled)
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -118,6 +118,6 @@
     # post-conditions-end
     # impl-start
     if self.disabled:
-        return False
+        return differs(self, initial, data)
     return norm_seq(initial) != norm_seq(data)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,15 +82,7 @@
     Ensures(Implies(disabled_kw is not None, Result().disabled == disabled_kw))
     # post-conditions-end
     # impl-start
-    if required_kw is None:
-        required = False
-    else:
-        required = required_kw
-    if disabled_kw is None:
-        disabled = True
-    else:
-        disabled = disabled_kw
-    return Field(required, disabled)
+    return make_field(required_kw, disabled_kw)
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A specialised form field that merely DISPLAYS a stored value (it renders
      no editable control) must, when constructed without the caller naming the
      two presentation flags, come into existence already marked as
      non-editable: such a field is optional (not required) AND is flagged as
      not user-editable by default. A caller that explicitly names either flag
      keeps the value it chose; only an unset flag falls back to the default.

  (2) The generic "did the submitted value differ from the stored value?"
      decision a field reports is short-circuited for a field flagged
      non-editable: such a field NEVER reports a change, because its submitted
      value is always ignored in favour of the stored value. For an editable
      field the decision is the ordinary inequality of the stored and submitted
      values, where an absent value (None) is indistinguishable from the empty
      value.

The field is modelled as a minimal class carrying only the two touched flags
(`required`, `disabled`). Caller-supplied keyword values are modelled as
`Optional[bool]` where `None` means "the caller did not name this flag" (so the
default applies). Text values are modelled as `Optional[List[int]]` of Unicode
code points (None = absent), since Nagini bans `str` indexing.

The generic field constructor's flag storage and the generic change decision's
non-editable short-circuit are unchanged base behaviours, modelled deeply (the
flags are stored verbatim; the short-circuit is spelled out) and validated
== the real base field by axiom_check.py (G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Field:
    def __init__(self, required: bool, disabled: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.required) and self.required == required)    # type: ignore
        Ensures(Acc(self.disabled) and self.disabled == disabled)    # type: ignore
        self.required = required
        self.disabled = disabled

# axioms-start
# (No @ContractOnly axioms are consumed: the base field's flag storage and the
#  base change-decision short-circuit are modelled deeply below and validated
#  against the real base field out-of-band by axiom_check.py / G-AX.)
# axioms-end

# pure-start
@Pure
def norm_seq(v: Optional[List[int]]) -> PSeq[int]:
    """Normalised value content: an absent value (None) is indistinguishable
    from the empty value, so both map to the empty sequence; otherwise the
    value's own code-point sequence."""
    Requires(Implies(v is not None, Acc(list_pred(v), 1 / 4)))
    if v is None:
        return PSeq(0).take(0)
    return ToSeq(v)
# pure-end

def make_field(required_kw: Optional[bool], disabled_kw: Optional[bool]) -> Field:
    # pre-conditions-start
    # No permission obligations on the Optional[bool] keyword carriers.
    # The constructed field must actually be delivered: this termination
    # obligation forbids implementations that satisfy the flag postconditions
    # only vacuously by never returning (flag selection is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().required) and Acc(Result().disabled))
    # An unnamed flag falls back to the field's own default; a named flag keeps
    # the caller's value. Defaults: not-required, and not-editable.
    Ensures(Implies(required_kw is None, Result().required == False))
    Ensures(Implies(required_kw is not None, Result().required == required_kw))
    Ensures(Implies(disabled_kw is None, Result().disabled == True))
    Ensures(Implies(disabled_kw is not None, Result().disabled == disabled_kw))
    # post-conditions-end
    # impl-start
    if required_kw is None:
        required = False
    else:
        required = required_kw
    if disabled_kw is None:
        disabled = True
    else:
        disabled = disabled_kw
    return Field(required, disabled)
    # impl-end

def differs(self: Field, initial: Optional[List[int]], data: Optional[List[int]]) -> bool:
    # pre-conditions-start
    Requires(Acc(self.disabled, 1 / 2))
    Requires(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Requires(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # The change decision must actually be delivered: this termination
    # obligation forbids implementations that satisfy either branch's value
    # postcondition only vacuously by never returning (both the short-circuit
    # and the normalised comparison are bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.disabled, 1 / 2))
    Ensures(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Ensures(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # A non-editable field NEVER reports a change (its submitted value is
    # ignored in favour of the stored value).
    Ensures(Implies(self.disabled, Result() == False))
    # An editable field reports a change exactly when the stored and submitted
    # values differ, treating an absent value (None) as the empty value.
    Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
    # post-conditions-end
    # impl-start
    if self.disabled:
        return False
    return norm_seq(initial) != norm_seq(data)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The frozen spec pins both operations with total equality postconditions guarded by MustTerminate: make_field's Ensures fix .required/.disabled for every (Optional[bool],Optional[bool]) case; differs' Ensures fix Result()==False when disabled and Result()==(norm_seq(initial)!=norm_seq(data)) when enabled, over the full Optional[List[int]] domain. MustTerminate(2)/(1) makes the contracts TOTAL, closing partial-correctness vacuity.

atk_1 (prepatch bug: make_field disabled default False == model_prepatch A3 revert) -> does NOT verify (rejected). Reproduces the prepatch.
- atk_2 (prepatch_2 bug: differs `return False` unconditionally == deleted override) -> does NOT verify (rejected). Reproduces the prepatch_2.
- atk_3 (branch swap: compare on disabled, False on enabled) -> does NOT verify.
- atk_4 (boundary: Field(disabled,required) flags stored swapped) -> does NOT verify.
- atk_5 (control-flow-effect: `while True: pass` on differs disabled branch) -> does NOT verify (MustTerminate rejects non-termination).
- atk_8 (ignore-explicit: make_field forces disabled=True, drops disabled_kw) -> does NOT verify (fails when disabled_kw is False).
- atk_9 (EXACT prior-pass named counterexample: differs disabled branch = unbounded self-recursion `return differs(self,...)`) -> does NOT verify. The prior BROKEN G-EQ verdict (verdict.md Role-1, atk_11.py) exploited that the OLD model.py had NO MustTerminate; the current model.py (Aug 13 03:20, post-fix) adds MustTerminate, which now REJECTS this exact impl.
- atk_10 (make_field self-recursion, never returns) -> does NOT verify (MustTerminate(2) rejects).

Verifying candidates (weakness => CANDIDATE, ~10.7s each) are BEHAVIORAL ECHOES of gold, not weaknesses:
- atk_6 (differs De Morgan rewrite: `if not self.disabled: return cmp; return False`) — behaviorally identical to gold differs on the full domain.
- atk_7 (make_field ternary rewrite) — behaviorally identical to gold make_field.
- pos_control (exact gold impl) — verifies (positive control good).
Each echo's faithful refined patch is byte-identical to the gold patch.diff (the real source change — setdefault('disabled',True) + removal of the bespoke has_changed/bound_data override + clean_password — is the same regardless of the equivalent model spelling). Materialized to {atk_6,atk_7,pos_control}.diff (all sha1 af1c48e5..., md5==gold). Ran through the OFFICIAL harness: run_resolve('django__django-13741', <faithful patch>) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So every verifying candidate's faithful patch RESOLVES — no verify⇏correct break exists in the current spec.

Refinement.md leg audit: all legs are R (A1,B1,B2), I (A2,A3), or A-reference (A4,B3,B4); section C is an explicit no-model consequence of A+B; section D asserts no kind-3; section E documents the MustTerminate totality now present in model.py. NO consumed @ContractOnly axioms exist. The three A-reference deep models (Field.`__init__` flag storage fields.py:84,87; Field.has_changed disabled short-circuit fields.py:179-180; enabled None->'' comparison fields.py:190-192) are validated == the REAL django.forms.fields.Field by axiom_check.py — recorded G-AX=pass, and independently corroborated by G-CONF=pass (100,137 inputs vs the real patched repo, 0 disagreements). axiom_check.py drives the REAL callees (constructs ReadOnlyPasswordHashField over 9 kwarg combos, runs base Field.has_changed over 14 pairs x {disabled,enabled}), so the A-reference correspondence holds; run locally it SKIPs only because Django isn't importable in the audit venv (in-container G-AX verdict is the live evidence).

**Conclusion:** >=8 distinct wrong impls (partial-domain atk_3, boundary atk_4, control-flow-effect atk_5/atk_9/atk_10, prepatch atk_1/atk_2, ignore-explicit atk_8) all rejected; the only verifiers are behavioral echoes whose executed faithful patches resolve. Spec is TIGHT. verify => correct holds. VERDICT: SOUND.

**Note for record:** meta.json currently records G-EQ=fail/BROKEN from a PRIOR pass against the pre-MustTerminate model.py; the repaired model.py (source-2 fix) closes it, as this re-audit demonstrates by re-encoding and rejecting the exact prior counterexample (atk_9).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A specialised form field that merely DISPLAYS a stored value (it renders
      no editable control) must, when constructed without the caller naming the
      two presentation flags, come into existence already marked as
      non-editable: such a field is optional (not required) AND is flagged as
      not user-editable by default. A caller that explicitly names either flag
      keeps the value it chose; only an unset flag falls back to the default.

  (2) The generic "did the submitted value differ from the stored value?"
      decision a field reports is short-circuited for a field flagged
      non-editable: such a field NEVER reports a change, because its submitted
      value is always ignored in favour of the stored value. For an editable
      field the decision is the ordinary inequality of the stored and submitted
      values, where an absent value (None) is indistinguishable from the empty
      value.

The field is modelled as a minimal class carrying only the two touched flags
(`required`, `disabled`). Caller-supplied keyword values are modelled as
`Optional[bool]` where `None` means "the caller did not name this flag" (so the
default applies). Text values are modelled as `Optional[List[int]]` of Unicode
code points (None = absent), since Nagini bans `str` indexing.

The generic field constructor's flag storage and the generic change decision's
non-editable short-circuit are unchanged base behaviours, modelled deeply (the
flags are stored verbatim; the short-circuit is spelled out) and validated
== the real base field by axiom_check.py (G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Field:
    def __init__(self, required: bool, disabled: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.required) and self.required == required)    # type: ignore
        Ensures(Acc(self.disabled) and self.disabled == disabled)    # type: ignore
        self.required = required
        self.disabled = disabled

# axioms-start
# (No @ContractOnly axioms are consumed: the base field's flag storage and the
#  base change-decision short-circuit are modelled deeply below and validated
#  against the real base field out-of-band by axiom_check.py / G-AX.)
# axioms-end

# pure-start
@Pure
def norm_seq(v: Optional[List[int]]) -> PSeq[int]:
    """Normalised value content: an absent value (None) is indistinguishable
    from the empty value, so both map to the empty sequence; otherwise the
    value's own code-point sequence."""
    Requires(Implies(v is not None, Acc(list_pred(v), 1 / 4)))
    if v is None:
        return PSeq(0).take(0)
    return ToSeq(v)
# pure-end

def make_field(required_kw: Optional[bool], disabled_kw: Optional[bool]) -> Field:
    # pre-conditions-start
    # No permission obligations on the Optional[bool] keyword carriers.
    # The constructed field must actually be delivered: this termination
    # obligation forbids implementations that satisfy the flag postconditions
    # only vacuously by never returning (flag selection is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().required) and Acc(Result().disabled))
    # An unnamed flag falls back to the field's own default; a named flag keeps
    # the caller's value. Defaults: not-required, and not-editable.
    Ensures(Implies(required_kw is None, Result().required == False))
    Ensures(Implies(required_kw is not None, Result().required == required_kw))
    Ensures(Implies(disabled_kw is None, Result().disabled == True))
    Ensures(Implies(disabled_kw is not None, Result().disabled == disabled_kw))
    # post-conditions-end
    # impl-start
    if required_kw is None:
        required = False
    else:
        required = required_kw
    if disabled_kw is None:
        disabled = True
    else:
        disabled = disabled_kw
    return Field(required, disabled)
    # impl-end

def differs(self: Field, initial: Optional[List[int]], data: Optional[List[int]]) -> bool:
    # pre-conditions-start
    Requires(Acc(self.disabled, 1 / 2))
    Requires(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Requires(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # The change decision must actually be delivered: this termination
    # obligation forbids implementations that satisfy either branch's value
    # postcondition only vacuously by never returning (both the short-circuit
    # and the normalised comparison are bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.disabled, 1 / 2))
    Ensures(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Ensures(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # A non-editable field NEVER reports a change (its submitted value is
    # ignored in favour of the stored value).
    Ensures(Implies(self.disabled, Result() == False))
    # An editable field reports a change exactly when the stored and submitted
    # values differ, treating an absent value (None) as the empty value.
    Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
    # post-conditions-end
    # impl-start
    if self.disabled:
        return False
    return norm_seq(initial) != norm_seq(data)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The frozen spec pins both operations with total equality postconditions guarded by MustTerminate: make_field's Ensures fix .required/.disabled for every (Optional[bool],Optional[bool]) case; differs' Ensures fix Result()==False when disabled and Result()==(norm_seq(initial)!=norm_seq(data)) when enabled, over the full Optional[List[int]] domain. MustTerminate(2)/(1) makes the contracts TOTAL, closing partial-correctness vacuity.

atk_1 (prepatch bug: make_field disabled default False == model_prepatch A3 revert) -> does NOT verify (rejected). Reproduces the prepatch.
- atk_2 (prepatch_2 bug: differs `return False` unconditionally == deleted override) -> does NOT verify (rejected). Reproduces the prepatch_2.
- atk_3 (branch swap: compare on disabled, False on enabled) -> does NOT verify.
- atk_4 (boundary: Field(disabled,required) flags stored swapped) -> does NOT verify.
- atk_5 (control-flow-effect: `while True: pass` on differs disabled branch) -> does NOT verify (MustTerminate rejects non-termination).
- atk_8 (ignore-explicit: make_field forces disabled=True, drops disabled_kw) -> does NOT verify (fails when disabled_kw is False).
- atk_9 (EXACT prior-pass named counterexample: differs disabled branch = unbounded self-recursion `return differs(self,...)`) -> does NOT verify. The prior BROKEN G-EQ verdict (verdict.md Role-1, atk_11.py) exploited that the OLD model.py had NO MustTerminate; the current model.py (Aug 13 03:20, post-fix) adds MustTerminate, which now REJECTS this exact impl.
- atk_10 (make_field self-recursion, never returns) -> does NOT verify (MustTerminate(2) rejects).

Verifying candidates (weakness => CANDIDATE, ~10.7s each) are BEHAVIORAL ECHOES of gold, not weaknesses:
- atk_6 (differs De Morgan rewrite: `if not self.disabled: return cmp; return False`) — behaviorally identical to gold differs on the full domain.
- atk_7 (make_field ternary rewrite) — behaviorally identical to gold make_field.
- pos_control (exact gold impl) — verifies (positive control good).
Each echo's faithful refined patch is byte-identical to the gold patch.diff (the real source change — setdefault('disabled',True) + removal of the bespoke has_changed/bound_data override + clean_password — is the same regardless of the equivalent model spelling). Materialized to {atk_6,atk_7,pos_control}.diff (all sha1 af1c48e5..., md5==gold). Ran through the OFFICIAL harness: run_resolve('django__django-13741', <faithful patch>) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So every verifying candidate's faithful patch RESOLVES — no verify⇏correct break exists in the current spec.

Refinement.md leg audit: all legs are R (A1,B1,B2), I (A2,A3), or A-reference (A4,B3,B4); section C is an explicit no-model consequence of A+B; section D asserts no kind-3; section E documents the MustTerminate totality now present in model.py. NO consumed @ContractOnly axioms exist. The three A-reference deep models (Field.`__init__` flag storage fields.py:84,87; Field.has_changed disabled short-circuit fields.py:179-180; enabled None->'' comparison fields.py:190-192) are validated == the REAL django.forms.fields.Field by axiom_check.py — recorded G-AX=pass, and independently corroborated by G-CONF=pass (100,137 inputs vs the real patched repo, 0 disagreements). axiom_check.py drives the REAL callees (constructs ReadOnlyPasswordHashField over 9 kwarg combos, runs base Field.has_changed over 14 pairs x {disabled,enabled}), so the A-reference correspondence holds; run locally it SKIPs only because Django isn't importable in the audit venv (in-container G-AX verdict is the live evidence).

**Conclusion:** >=8 distinct wrong impls (partial-domain atk_3, boundary atk_4, control-flow-effect atk_5/atk_9/atk_10, prepatch atk_1/atk_2, ignore-explicit atk_8) all rejected; the only verifiers are behavioral echoes whose executed faithful patches resolve. Spec is TIGHT. verify => correct holds. VERDICT: SOUND.

**Note for record:** meta.json currently records G-EQ=fail/BROKEN from a PRIOR pass against the pre-MustTerminate model.py; the repaired model.py (source-2 fix) closes it, as this re-audit demonstrates by re-encoding and rejecting the exact prior counterexample (atk_9).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness axis: the modeled functions agree with the real repo callees on every tested input; no diverging input found. Verification method: applied the gold hunk (kwargs.setdefault('disabled', True) added to ReadOnlyPasswordHashField.`__init__`, with the bespoke bound_data/has_changed overrides removed) to a fresh copy of the base tree at base_commit d746f28 and compared the model's spec-region behaviour to the REAL patched repo. (1) make_field <-> ReadOnlyPasswordHashField.`__init__`: over all 9 kwarg combos (each flag absent/True/False) the real field's .required/.disabled == model (required default False, disabled default True, explicit values preserved). (2) differs <-> base django.forms.fields.Field.has_changed: the base Field has identity to_python (fields.py:123-124) and no `_coerce`, so its body reduces to `if self.disabled: return False; else initial_value != data_value` with None->'' -- exactly norm_seq(initial) != norm_seq(data). Fuzzed 220k inputs (printable ASCII, BMP non-ASCII, astral-plane, shared-prefix/differing-length, None/'' boundaries) x {disabled,enabled}: 0 disagreements. The bundle's own G-AX (9 kwarg cases + 14 value pairs x2) and G-CONF (100137 inputs, seed 13741) both exit 0 against my independently-patched tree. The MustTerminate obligations are a totality STRENGTHENING but exclude no real behaviour: the real counterparts are straight-line bounded work (a setdefault pair + constructor; a flag test + one comparison), so no terminating real input is rejected. CONTEXT: the recorded G-EQ (Role-1) fail on this cell is a soundness break (verify=>NOT correct: a non-terminating impl on the disabled branch satisfies the postcondition vacuously), i.e. the spec was too WEAK w.r.t. termination -- the exact reason MustTerminate was later added to this model.py. That is not a faithfulness/spec-too-strong defect. On the faithfulness axis the spec is FAITHFUL.

**Faithfulness axis:** the modeled functions agree with the real repo callees on every tested input; no diverging input found. Verification method: applied the gold hunk (kwargs.setdefault('disabled', True) added to ReadOnlyPasswordHashField.`__init__`, with the bespoke bound_data/has_changed overrides removed) to a fresh copy of the base tree at base_commit d746f28 and compared the model's spec-region behaviour to the REAL patched repo.

(1) make_field <-> ReadOnlyPasswordHashField.`__init__`: over all 9 kwarg combos (each flag absent/True/False) the real field's .required/.disabled == model (required default False, disabled default True, explicit values preserved).

(2) differs <-> base django.forms.fields.Field.has_changed: the base Field has identity to_python (fields.py:123-124) and no `_coerce`, so its body reduces to `if self.disabled: return False; else initial_value != data_value` with None->'' -- exactly norm_seq(initial) != norm_seq(data). Fuzzed 220k inputs (printable ASCII, BMP non-ASCII, astral-plane, shared-prefix/differing-length, None/'' boundaries) x {disabled,enabled}: 0 disagreements. The bundle's own G-AX (9 kwarg cases + 14 value pairs x2) and G-CONF (100137 inputs, seed 13741) both exit 0 against my independently-patched tree.

The MustTerminate obligations are a totality STRENGTHENING but exclude no real behaviour: the real counterparts are straight-line bounded work (a setdefault pair + constructor; a flag test + one comparison), so no terminating real input is rejected. CONTEXT: the recorded G-EQ (Role-1) fail on this cell is a soundness break (verify=>NOT correct: a non-terminating impl on the disabled branch satisfies the postcondition vacuously), i.e. the spec was too WEAK w.r.t. termination -- the exact reason MustTerminate was later added to this model.py. That is not a faithfulness/spec-too-strong defect. On the faithfulness axis the spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (status=pass, no failures): no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol (ReadOnlyPasswordHashField, clean_password, has_changed, bound_data all absent), no narration.

**Semantic judgment beyond the lexical screen:** the spec view discloses nothing about the gold edit that the PUBLIC problem_statement does not already state. The issue title is literally 'Set disabled prop on ReadOnlyPasswordHashField' and the body says 'this property could be set to True be default on the ReadOnlyPasswordHashField' — i.e. the exact gold edit kwargs.setdefault('disabled', True) is public. The issue also quotes the disabled-attribute semantics verbatim ('Even if a user tampers with the field's value submitted to the server, it will be ignored in favor of the value from the form's initial data') and states 'the clean_password is no longer necessary'.

Mapping spec-view content to public text: (1) default disabled=True with explicit values preserved = the 'set to True by default' the issue proposes; the required=False default is the PRE-EXISTING unchanged default (hunk A2, not the edit). (2) 'a non-editable field NEVER reports a change, submitted value ignored in favour of the stored value' = the quoted disabled semantics; the editable-path None->empty inequality is generic base Field.has_changed behaviour, not an edit discriminator. The view is framed as desired behaviour ('stated as desired behaviour, not as an edit'), abstractly, without naming any patched symbol/file. Every discriminating fact is already in the problem_statement. No line leaks the gold edit beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).