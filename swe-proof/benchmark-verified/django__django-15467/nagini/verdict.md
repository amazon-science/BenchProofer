# P2 adversarial audit — django__django-15467

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_7_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -115,10 +113,7 @@
     # post-conditions-end
     # impl-start
     if permits_empty:
-        if empty_label_key() in kwargs:
-            value = kwargs[empty_label_key()]
-        else:
-            value = default_label()
+        value = default_label()
     else:
         value = absent_label()
     kwargs[empty_label_key()] = value
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -115,7 +113,7 @@
     # post-conditions-end
     # impl-start
     if permits_empty:
-        if empty_label_key() in kwargs:
+        if empty_label_key() in kwargs and kwargs[empty_label_key()] != absent_label():
             value = kwargs[empty_label_key()]
         else:
             value = default_label()
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -120,7 +118,7 @@
         else:
             value = default_label()
     else:
-        value = absent_label()
+        value = default_label()
     kwargs[empty_label_key()] = value
     return value
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -122,5 +120,6 @@
     else:
         value = absent_label()
     kwargs[empty_label_key()] = value
+    kwargs[empty_label_key() + 100] = value
     return value
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -114,13 +112,10 @@
         Implies(Old(k in kwargs), kwargs[k] == Old(kwargs[k])))))
     # post-conditions-end
     # impl-start
-    if permits_empty:
-        if empty_label_key() in kwargs:
-            value = kwargs[empty_label_key()]
-        else:
-            value = default_label()
+    if empty_label_key() in kwargs:
+        value = kwargs[empty_label_key()]
     else:
-        value = absent_label()
+        value = default_label()
     kwargs[empty_label_key()] = value
     return value
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     # permission is required.
     Requires(dict_pred(kwargs))
     Requires(kwargs is not None)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(kwargs))
@@ -118,7 +116,7 @@
         if empty_label_key() in kwargs:
             value = kwargs[empty_label_key()]
         else:
-            value = default_label()
+            value = absent_label()
     else:
         value = absent_label()
     kwargs[empty_label_key()] = value
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_correct.py`

```python
"""Twin-artifact model for django__django-15467.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field is built for a relation that is rendered as a set of radio
  choices. Such a field carries an "empty choice" label -- the token shown for
  the not-selected option. The keyword arguments collected for building the
  field form a mapping; one distinguished key holds that empty-choice label.
  Two facts about the relation matter: whether it permits the empty selection
  (the "permits-empty" flag), and whether the caller has ALREADY supplied an
  empty-choice label in the keyword mapping.

  The required outcome for the empty-choice label entry of the mapping:

    * when the relation does NOT permit the empty selection, the entry is the
      ABSENT sentinel (no empty choice is offered), regardless of anything the
      caller supplied;

    * when the relation DOES permit the empty selection, a caller-supplied
      label is RESPECTED: if the keyword mapping already carries the
      empty-choice key, its existing value is kept verbatim (even when that
      value is a falsy/blank token); only when the key is absent is the
      built-in default empty-choice label used.

  The behaviour that matters: with a relation that permits the empty selection
  and a caller-supplied empty-choice label, the result is the caller's label,
  NOT the built-in default. Presence of the key -- not the truthiness of its
  value -- is what makes the caller's value win.

Modelling choices (Nagini fragment):
  * The keyword mapping is a ``Dict[int, int]``: the distinguished empty-choice
    key is a constant integer token, and a label is a constant integer code (the
    absent sentinel, the built-in default, and any caller label being distinct
    integer codes). Only key membership and per-key value are observed, so an
    integer-valued carrier faithfully abstracts the real string-keyed mapping
    of arbitrary label values (mapping.md §2). Membership models "the caller
    supplied the key"; the stored value is read back verbatim -- the absent
    sentinel is a legitimate stored value distinct from "key absent".
  * The mapping is genuinely written (the empty-choice entry is assigned), so
    it is held at FULL permission and its post-state at the empty-choice key is
    pinned exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatised callees: the modelled behaviour is a pure mapping update
#  spelled out deeply in the impl region.)
# axioms-end


# pure-start
@Pure
def empty_label_key() -> int:
    # The distinguished mapping key holding the empty-choice label.
    return 1


@Pure
def absent_label() -> int:
    # The sentinel stored when no empty choice is offered (the relation does
    # not permit the empty selection). Distinct from every real label.
    return 0


@Pure
def default_label() -> int:
    # The built-in default empty-choice label, used only when the relation
    # permits the empty selection and the caller supplied no label. Distinct
    # from the absent sentinel.
    return 2
# pure-end


def set_radio_empty_label(permits_empty: bool, kwargs: Dict[int, int]) -> int:
    # pre-conditions-start
    # The mapping is written (the empty-choice entry is assigned), so FULL
    # permission is required.
    Requires(dict_pred(kwargs))
    Requires(kwargs is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(kwargs))
    Ensures(kwargs is not None)
    # The empty-choice key is present in the resulting mapping, and the
    # returned value is exactly that entry.
    Ensures(empty_label_key() in kwargs)
    Ensures(kwargs[empty_label_key()] == Result())
    # When the relation does NOT permit the empty selection, the empty-choice
    # entry is the absent sentinel -- nothing the caller supplied survives.
    Ensures(Implies(not permits_empty, Result() == absent_label()))
    # When the relation DOES permit the empty selection and the caller ALREADY
    # supplied the empty-choice key, that existing value is kept verbatim
    # (membership wins, regardless of the value's truthiness -- e.g. it may be
    # the absent sentinel as a deliberate caller choice).
    Ensures(Implies(permits_empty and Old(empty_label_key() in kwargs),
                    Result() == Old(kwargs[empty_label_key()])))
    # When the relation DOES permit the empty selection and the caller supplied
    # NO empty-choice key, the built-in default empty-choice label is used.
    Ensures(Implies(permits_empty and not Old(empty_label_key() in kwargs),
                    Result() == default_label()))
    # FRAME: the whole mapping is forwarded downstream to build the field, so
    # every entry is observable. Every key OTHER than the empty-choice key must
    # be left untouched: no other key appears or disappears, and each surviving
    # entry keeps its value verbatim.
    Ensures(Forall(int, lambda k: Implies(
        k != empty_label_key(),
        ((k in kwargs) == Old(k in kwargs)) and
        Implies(Old(k in kwargs), kwargs[k] == Old(kwargs[k])))))
    # post-conditions-end
    # impl-start
    if not permits_empty:
        value = absent_label()
    elif empty_label_key() in kwargs:
        value = kwargs[empty_label_key()]
    else:
        value = default_label()
    kwargs[empty_label_key()] = value
    return value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Ran adversary via python with SBU_BENCHMARK_DIR=benchmark-verified. Verifications run concurrently in batches of 3 (each nagini check spawns JVM+Z3).

SPEC SHAPE: set_radio_empty_label postconditions FULLY pin Result() across all three input classes (not-permits => absent_label; permits & Old key present => Old(kwargs[key]) verbatim; permits & Old key absent => default_label), plus Ensures(kwargs[empty_label_key()]==Result()) and a Forall(int) frame clause pinning membership==Old(membership) and value==Old(value) for every key != empty_label_key(). No residual functional freedom.

A-LEG AUDIT: refinement.md declares NO A-legs. model.py axioms-start/end block is empty ('no axiomatised callees'). No @ContractOnly, no Axiom, no axiom_check.py present => no G-AX obligation. mapping.md §3 'Callee provenance (kind-A): None.' dict.get(key,default) is the unchanged language primitive recomposed DEEPLY in the impl (step A3 = 'kwargs[k] if k in kwargs else d'); _("None") treated as constant default_label(). All refinement legs are R (bool identity, None<->absent, "empty_label"<->key token, _("None")<->default) or I (conditional/assignment/frame). No kind-3 (unexpressible-changed-op). Model<->patch correspondence holds: A1-A6 map cleanly to the single gold hunk.

### ATTACKS (all same-spec byte-identical, impl-region-only edits; commands run from project root):
cmd template: python -m swebench_unified.adversary weakness nagini django__django-15467 <atk>
- atk_1.py PREPATCH bug (value=default_label() unconditionally in permits arm): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch reproduced (matches model_prepatch.py skeleton; violates the permits&present=>Old-value clause).
- atk_2.py truthiness/'or' bug (present value replaced by default when it equals absent_label sentinel): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Spec's 'membership wins regardless of truthiness' clause catches it.
- atk_3.py boundary swap in not-permits arm (returns default_label instead of absent_label): does not verify (exit 2). Violates Implies(not permits_empty, Result()==absent_label()).
- atk_4.py control-flow-effect: correct empty-choice value BUT also writes kwargs[key+100]=value (extra key): does not verify (exit 2). Frame Forall clause catches the added key.
- atk_5.py partial-domain: ignores permits_empty entirely (always keep-or-default): does not verify (exit 2). Wrong on the not-permits domain.
- atk_6.py ungrounded default-swap: uses absent_label instead of default_label when permits & key absent: does not verify (exit 2). Violates the permits&absent=>default_label clause.

POSITIVE CONTROL: atk_7_correct.py (correct impl, rewritten as if not permits_empty: absent; elif key in kwargs: keep verbatim; else default) => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (10.4s, exit 0).

MANDATORY RESOLVE ON CANDIDATE: materialized its faithful refined patch (patch_atk7.diff, behaviourally identical to gold) and executed run_resolve('django__django-15467', patch, timeout=1800) via swebench_unified.harness => completed=True, resolved=True, attempts=1. So the only verifying impl RESOLVES; no verify⇏correct break found.

VERDICT: SOUND. 6 distinct wrong impls (prepatch, truthiness, boundary, frame/control-flow-effect, partial-domain, ungrounded default-swap) all rejected by the spec; the sole verifying candidate is behaviourally correct and its materialized faithful patch resolves under the official harness. A-legs vacuous (none) and correctly documented; no kind-3 legs; model<->patch correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_7_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_7_correct.py`

```python
"""Twin-artifact model for django__django-15467.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field is built for a relation that is rendered as a set of radio
  choices. Such a field carries an "empty choice" label -- the token shown for
  the not-selected option. The keyword arguments collected for building the
  field form a mapping; one distinguished key holds that empty-choice label.
  Two facts about the relation matter: whether it permits the empty selection
  (the "permits-empty" flag), and whether the caller has ALREADY supplied an
  empty-choice label in the keyword mapping.

  The required outcome for the empty-choice label entry of the mapping:

    * when the relation does NOT permit the empty selection, the entry is the
      ABSENT sentinel (no empty choice is offered), regardless of anything the
      caller supplied;

    * when the relation DOES permit the empty selection, a caller-supplied
      label is RESPECTED: if the keyword mapping already carries the
      empty-choice key, its existing value is kept verbatim (even when that
      value is a falsy/blank token); only when the key is absent is the
      built-in default empty-choice label used.

  The behaviour that matters: with a relation that permits the empty selection
  and a caller-supplied empty-choice label, the result is the caller's label,
  NOT the built-in default. Presence of the key -- not the truthiness of its
  value -- is what makes the caller's value win.

Modelling choices (Nagini fragment):
  * The keyword mapping is a ``Dict[int, int]``: the distinguished empty-choice
    key is a constant integer token, and a label is a constant integer code (the
    absent sentinel, the built-in default, and any caller label being distinct
    integer codes). Only key membership and per-key value are observed, so an
    integer-valued carrier faithfully abstracts the real string-keyed mapping
    of arbitrary label values (mapping.md §2). Membership models "the caller
    supplied the key"; the stored value is read back verbatim -- the absent
    sentinel is a legitimate stored value distinct from "key absent".
  * The mapping is genuinely written (the empty-choice entry is assigned), so
    it is held at FULL permission and its post-state at the empty-choice key is
    pinned exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatised callees: the modelled behaviour is a pure mapping update
#  spelled out deeply in the impl region.)
# axioms-end


# pure-start
@Pure
def empty_label_key() -> int:
    # The distinguished mapping key holding the empty-choice label.
    return 1


@Pure
def absent_label() -> int:
    # The sentinel stored when no empty choice is offered (the relation does
    # not permit the empty selection). Distinct from every real label.
    return 0


@Pure
def default_label() -> int:
    # The built-in default empty-choice label, used only when the relation
    # permits the empty selection and the caller supplied no label. Distinct
    # from the absent sentinel.
    return 2
# pure-end


def set_radio_empty_label(permits_empty: bool, kwargs: Dict[int, int]) -> int:
    # pre-conditions-start
    # The mapping is written (the empty-choice entry is assigned), so FULL
    # permission is required.
    Requires(dict_pred(kwargs))
    Requires(kwargs is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(kwargs))
    Ensures(kwargs is not None)
    # The empty-choice key is present in the resulting mapping, and the
    # returned value is exactly that entry.
    Ensures(empty_label_key() in kwargs)
    Ensures(kwargs[empty_label_key()] == Result())
    # When the relation does NOT permit the empty selection, the empty-choice
    # entry is the absent sentinel -- nothing the caller supplied survives.
    Ensures(Implies(not permits_empty, Result() == absent_label()))
    # When the relation DOES permit the empty selection and the caller ALREADY
    # supplied the empty-choice key, that existing value is kept verbatim
    # (membership wins, regardless of the value's truthiness -- e.g. it may be
    # the absent sentinel as a deliberate caller choice).
    Ensures(Implies(permits_empty and Old(empty_label_key() in kwargs),
                    Result() == Old(kwargs[empty_label_key()])))
    # When the relation DOES permit the empty selection and the caller supplied
    # NO empty-choice key, the built-in default empty-choice label is used.
    Ensures(Implies(permits_empty and not Old(empty_label_key() in kwargs),
                    Result() == default_label()))
    # FRAME: the whole mapping is forwarded downstream to build the field, so
    # every entry is observable. Every key OTHER than the empty-choice key must
    # be left untouched: no other key appears or disappears, and each surviving
    # entry keeps its value verbatim.
    Ensures(Forall(int, lambda k: Implies(
        k != empty_label_key(),
        ((k in kwargs) == Old(k in kwargs)) and
        Implies(Old(k in kwargs), kwargs[k] == Old(kwargs[k])))))
    # post-conditions-end
    # impl-start
    if not permits_empty:
        value = absent_label()
    elif empty_label_key() in kwargs:
        value = kwargs[empty_label_key()]
    else:
        value = default_label()
    kwargs[empty_label_key()] = value
    return value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Ran adversary via python with SBU_BENCHMARK_DIR=benchmark-verified. Verifications run concurrently in batches of 3 (each nagini check spawns JVM+Z3).

SPEC SHAPE: set_radio_empty_label postconditions FULLY pin Result() across all three input classes (not-permits => absent_label; permits & Old key present => Old(kwargs[key]) verbatim; permits & Old key absent => default_label), plus Ensures(kwargs[empty_label_key()]==Result()) and a Forall(int) frame clause pinning membership==Old(membership) and value==Old(value) for every key != empty_label_key(). No residual functional freedom.

A-LEG AUDIT: refinement.md declares NO A-legs. model.py axioms-start/end block is empty ('no axiomatised callees'). No @ContractOnly, no Axiom, no axiom_check.py present => no G-AX obligation. mapping.md §3 'Callee provenance (kind-A): None.' dict.get(key,default) is the unchanged language primitive recomposed DEEPLY in the impl (step A3 = 'kwargs[k] if k in kwargs else d'); _("None") treated as constant default_label(). All refinement legs are R (bool identity, None<->absent, "empty_label"<->key token, _("None")<->default) or I (conditional/assignment/frame). No kind-3 (unexpressible-changed-op). Model<->patch correspondence holds: A1-A6 map cleanly to the single gold hunk.

### ATTACKS (all same-spec byte-identical, impl-region-only edits; commands run from project root):
cmd template: python -m swebench_unified.adversary weakness nagini django__django-15467 <atk>
- atk_1.py PREPATCH bug (value=default_label() unconditionally in permits arm): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch reproduced (matches model_prepatch.py skeleton; violates the permits&present=>Old-value clause).
- atk_2.py truthiness/'or' bug (present value replaced by default when it equals absent_label sentinel): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Spec's 'membership wins regardless of truthiness' clause catches it.
- atk_3.py boundary swap in not-permits arm (returns default_label instead of absent_label): does not verify (exit 2). Violates Implies(not permits_empty, Result()==absent_label()).
- atk_4.py control-flow-effect: correct empty-choice value BUT also writes kwargs[key+100]=value (extra key): does not verify (exit 2). Frame Forall clause catches the added key.
- atk_5.py partial-domain: ignores permits_empty entirely (always keep-or-default): does not verify (exit 2). Wrong on the not-permits domain.
- atk_6.py ungrounded default-swap: uses absent_label instead of default_label when permits & key absent: does not verify (exit 2). Violates the permits&absent=>default_label clause.

POSITIVE CONTROL: atk_7_correct.py (correct impl, rewritten as if not permits_empty: absent; elif key in kwargs: keep verbatim; else default) => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (10.4s, exit 0).

MANDATORY RESOLVE ON CANDIDATE: materialized its faithful refined patch (patch_atk7.diff, behaviourally identical to gold) and executed run_resolve('django__django-15467', patch, timeout=1800) via swebench_unified.harness => completed=True, resolved=True, attempts=1. So the only verifying impl RESOLVES; no verify⇏correct break found.

VERDICT: SOUND. 6 distinct wrong impls (prepatch, truthiness, boundary, frame/control-flow-effect, partial-domain, ungrounded default-swap) all rejected by the spec; the sole verifying candidate is behaviourally correct and its materialized faithful patch resolves under the official harness. A-legs vacuous (none) and correctly documented; no kind-3 legs; model<->patch correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift/spec-too-strong) audit of the CURRENT repaired bundle. NOTE: the recorded verdict.md is stale — it documents a pre-repair model.py that LACKED a frame clause and was rightly ruled spec-too-weak (verify⇏correct via extra/clobbered kwargs keys). The current model.py now carries that frame postcondition (lines 109-112) and verifies (nagini_verify.sh exit 0, 9.8s). My role checks the opposite direction: is the strengthened spec too STRONG / does the modeled function disagree with the real callee on any input?

Modeled slice = the single statement at django/contrib/admin/options.py:272 @ base_commit e0442a628e:
  kwargs["empty_label"] = (kwargs.get("empty_label", _("None")) if db_field.blank else None)
Abstraction (mapping.md §2): "empty_label"↔empty_label_key()==1; None↔absent_label()==0; _("None")↔default_label()==2; string-key membership↔int-key membership; dict.get(k,d)↔(kwargs[k] if k in kwargs else d).

Exhaustive branch-by-branch comparison — spec agrees with the real callee on EVERY input:
  (1) not permits_empty        → absent_label()          ⟺ not db_field.blank → None.                         AGREE
  (2) permits_empty & key set  → Old(kwargs[key]) verbatim ⟺ blank → dict.get returns present value (any truthiness). AGREE (membership-wins, matches .get, not the issue's `or` form).
  (3) permits_empty & key unset→ default_label()          ⟺ blank → dict.get returns _("None").                AGREE
  (4) empty_label_key() in post-state, Result()==that entry ⟺ real always assigns kwargs["empty_label"] and forwards it as ff.empty_label. AGREE
  (5) FRAME: every key != empty_label_key() unchanged (membership+value) ⟺ the modeled statement writes ONLY kwargs["empty_label"]; the kwargs["widget"] write above is a separate statement, outside the modeled function per mapping.md §1. AGREE — frame is not over-strong.

No diverging input exists: the frame quantifier does not forbid any behavior the real callee exhibits (the real slice touches no other key), and the value clauses reproduce dict.get exactly. The positive control (= model.py verbatim, the faithful gold-refined impl) verifies, so the spec is non-vacuous and does not wrongly reject the correct implementation. A faithful independently-written impl (kwargs.get semantics, only empty_label written) shares the byte-identical spec (adversary same-spec exit 0) and verifies (weakness exit 0) — i.e. correct impls are admitted. No over-strength / drift found.

Verified: markers.same_spec exit 0; adversary same-spec exit 0; adversary weakness exit 0 on the faithful twin; nagini_verify.sh exit 0 on model.py.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (passed=True, no hard failures). Verified semantically against the SOLVER-VISIBLE problem_statement only (not hints_text). The spec view is model.py with the impl region elided; refinement.md and mapping.md (which do quote the gold hunk) are NOT part of the screened spec view and are not solver-visible. Findings: (1) No gold-diff line is reproduced in the spec view. (2) No patched file path (django/contrib/admin/options.py) or module path appears. (3) The spec view uses only abstract carrier symbols (set_radio_empty_label, empty_label_key, absent_label, default_label, permits_empty) — none embeds a patched repo symbol. (4) The only patch-changed def/class symbol is formfield_for_foreignkey (hunk header), which is already public in the problem_statement anyway. (5) No narration terms (bug/fix/patch/etc.) in comments. Notably the public problem_statement is FAR more revealing than the spec view: it verbatim quotes the exact pre-patch line `kwargs['empty_label'] = _('None') if db_field.blank else None`, a proposed fix, the file path, and the method name. The abstract behavioral description in the spec view (membership-wins dict.get semantics) reveals strictly less than what is already public. No spec-view line leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
