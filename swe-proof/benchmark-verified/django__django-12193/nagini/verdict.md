# P2 adversarial audit — django__django-12193

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_inplace.py`, `atk_2_partial_domain_one_sentinel.py`, `atk_3_boundary_force_false.py`, `atk_4_inverted_branch.py`, `atk_5_drops_other_attrs.py`, `atk_6_returns_caller_object.py`, `atk_7_single_point_hole.py`, `atk_8_wrong_key_token.py`, `atk_9_infeasible_guard_wrong_tail.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_copy_then_merge.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_inplace.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,7 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+        attrs[attr_selected()] = True
+        return attrs
+    return attrs
     # impl-end
```

Attack 2 — `atk_2_partial_domain_one_sentinel.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,7 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
-    if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
+    if value != val_false():
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
     return mapping_copy(attrs)
     # impl-end
```

Attack 3 — `atk_3_boundary_force_false.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,6 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+    return mapping_with(attrs, attr_selected(), False)
     # impl-end
```

Attack 4 — `atk_4_inverted_branch.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,6 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+        return mapping_copy(attrs)
+    return mapping_with(attrs, attr_selected(), True)
     # impl-end
```

Attack 5 — `atk_5_drops_other_attrs.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,8 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
+    empty = {}  # type: Dict[int, bool]
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
+        return mapping_with(empty, attr_selected(), True)
     return mapping_copy(attrs)
     # impl-end
```

Attack 6 — `atk_6_returns_caller_object.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,6 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+    return attrs
     # impl-end
```

Attack 7 — `atk_7_single_point_hole.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,9 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
+    if value == val_empty_text():
+        return mapping_with(attrs, attr_selected(), True)
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
     return mapping_copy(attrs)
     # impl-end
```

Attack 8 — `atk_8_wrong_key_token.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,6 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
+        return mapping_with(attrs, attr_selected() + 1, True)
     return mapping_copy(attrs)
     # impl-end
```

Attack 9 — `atk_9_infeasible_guard_wrong_tail.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,11 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
+    if value == val_false() and value == val_absent():
+        return prepare_attrs(value, attrs)
+    if value == val_absent():
+        return mapping_with(attrs, attr_selected(), True)
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
     return mapping_copy(attrs)
     # impl-end
```

Attack 10 — `atk_10_copy_then_merge.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -174,9 +174,6 @@
     # post-conditions-end
     # impl-start
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+        return mapping_with(mapping_copy(attrs), attr_selected(), True)
+    return mapping_copy(mapping_copy(attrs))
     # impl-end
```

Attack 11 — `atk_11_diverging_selfcall.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,5 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
-    if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
-        return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+    return prepare_attrs(value, attrs)
     # impl-end
```

Attack 12 — `atk_12_empty_passthrough.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,10 +173,8 @@
                                        (k in attrs) and Result()[k] == attrs[k])))))
     # post-conditions-end
     # impl-start
+    empty = {}  # type: Dict[int, bool]
     if counts_as_selected(value):
-        # Fresh mapping: every caller attribute, with the selection flag forced
-        # on. The caller's mapping is read, never written.
         return mapping_with(attrs, attr_selected(), True)
-    # Pass-through: a fresh copy of exactly the caller's attributes.
-    return mapping_copy(attrs)
+    return mapping_copy(empty)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12193.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A boolean-style input widget prepares the attribute mapping that is handed to
  the shared rendering step. Whether the box is shown as selected is decided by
  a definite predicate on the supplied value: the value counts as selected unless
  it is one of the three "empty" sentinels (the boolean false, the absent value,
  or the empty text); every other value counts as selected.

  Two observations are pinned.

  (1) When the value counts as selected, the attribute mapping the rendering
      step receives carries the selection attribute set to true. Every other
      attribute already configured by the caller is carried through with its
      original value; the selection attribute is the only one established.

  (2) When the value does NOT count as selected, the attribute mapping the
      rendering step receives carries exactly the caller's attributes, with no
      selection attribute forced on.

  The consequence that matters: preparing the attribute mapping must NOT alter
  the caller's own mapping. The caller may reuse one mapping object to render a
  sequence of these widgets; if preparing the attributes for one selected value
  changed the caller's mapping, every later widget built from the same mapping
  would inherit the selection attribute even when its own value is not selected.
  The caller's mapping is therefore read-only here, and the prepared mapping is
  a fresh one.

Modelling choices (Nagini fragment):
  * An attribute mapping is a ``Dict[int, bool]`` from an attribute-name token
    to its flag value; only membership and per-key value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2). The
    selection attribute name is the module-level constant ``attr_selected()``.
  * The supplied value is an ``int`` code; the selection predicate is modelled
    deeply (``counts_as_selected``) as the repo's definite "not one of the three
    empty sentinels" rule (mapping.md §2), rather than pinned to an opaque
    oracle.
  * The fresh-mapping merge ``{**caller, attr: flag}`` is a standard mapping
    construction the code composes; it is the single callee ``mapping_with``,
    whose standard semantics are validated against real Python out-of-band
    (axiom_check.py, G-AX). It always allocates a NEW mapping, so the caller's
    mapping is never the result and is never written.

The caller's attribute mapping is read-only, so it is held at HALF permission
(Required AND Ensured) and never written. No string indexing is used (Nagini
bans it). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def mapping_with(base: Dict[int, bool], key: int, flag: bool) -> Dict[int, bool]:
    """Standard mapping construction ``{**base, key: flag}`` (an unchanged
    language primitive the code composes): a FRESH mapping holding every key of
    ``base`` plus ``key``, with ``flag`` the value at ``key`` and ``base``'s
    value at every other key. The result is always a new object, distinct from
    ``base`` (so ``base`` is read-only). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # A fresh mapping: never the base object (base stays unmutated).
    Ensures(Result() is not base)
    # The named key is present with the supplied flag.
    Ensures(key in Result() and Result()[key] == flag)
    # Every other key of base is carried through with base's value ...
    Ensures(Forall(int, lambda k: (Implies(k != key and k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    # ... and the result holds no key outside base plus the named key.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k == key or k in base))))


@ContractOnly
def mapping_copy(base: Dict[int, bool]) -> Dict[int, bool]:
    """Standard mapping copy ``{**base}`` (an unchanged language primitive): a
    FRESH mapping holding exactly every key of ``base`` with its value, distinct
    from ``base``. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(6))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Result() is not base)
    Ensures(Forall(int, lambda k: (Implies(k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           (k in base) and Result()[k] == base[k]))))
# axioms-end


# pure-start
@Pure
def attr_selected() -> int:
    # The attribute-name token for the selection flag the widget establishes.
    return 0


@Pure
def val_false() -> int:
    # Value code for the boolean-false sentinel (one of the three "empty"
    # values that count as NOT selected).
    return -1


@Pure
def val_absent() -> int:
    # Value code for the absent-value sentinel.
    return -2


@Pure
def val_empty_text() -> int:
    # Value code for the empty-text sentinel.
    return -3


@Pure
def counts_as_selected(value: int) -> bool:
    """The definite selection predicate: a value counts as selected unless it is
    one of the three empty sentinels (boolean false / absent / empty text)."""
    return not (value == val_false()
                or value == val_absent()
                or value == val_empty_text())
# pure-end


def prepare_attrs(value: int, attrs: Dict[int, bool]) -> Dict[int, bool]:
    # pre-conditions-start
    # The caller's attribute mapping is read-only here: HALF permission, never
    # written. (Held read-only so the operation cannot satisfy its postcondition
    # by overwriting the caller's mapping; the caller may reuse it for a
    # sequence of widgets and must observe it unchanged.)
    Requires(Acc(dict_pred(attrs), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The caller's mapping is returned untouched at the same half permission.
    Ensures(Acc(dict_pred(attrs), 1 / 2))
    # A fresh, full-permission mapping is prepared for the rendering step.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The prepared mapping is a DIFFERENT object from the caller's mapping.
    Ensures(Result() is not attrs)
    # (1) When the value counts as selected, the prepared mapping carries the
    #     selection attribute set to true ...
    Ensures(Implies(counts_as_selected(value),
                    attr_selected() in Result() and Result()[attr_selected()] == True))
    # ... and every OTHER caller attribute is carried through with its value.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k != attr_selected() and k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    # ... and the prepared mapping introduces no key the caller did not have,
    #     other than the selection attribute itself.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       k == attr_selected() or k in attrs)))))
    # (2) When the value does NOT count as selected, the prepared mapping holds
    #     exactly the caller's attributes (no selection attribute forced on):
    #     same keys, same values, in both directions.
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       (k in attrs) and Result()[k] == attrs[k])))))
    # post-conditions-end
    # impl-start
    if counts_as_selected(value):
        # Fresh mapping: every caller attribute, with the selection flag forced
        # on. The caller's mapping is read, never written.
        return mapping_with(attrs, attr_selected(), True)
    # Pass-through: a fresh copy of exactly the caller's attributes.
    return mapping_copy(attrs)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-12193 / nagini. Invocation used throughout (repo root swe-proof): `SBU_BENCHMARK_DIR=benchmark-verified PYTHONPATH=src ~/anaconda3/bin/python -m swebench_unified.adversary...` (no installed swebench_unified on PATH; Bundle resolution confirmed to point at benchmark-verified/django__django-12193/nagini/model.py). Verifications were run 3-at-a-time as background jobs (each Nagini check spawns a JVM+Z3); this changed only the schedule, every attack was fully verified.

**SAME-SPEC:** all 12 attacks + the positive control return `SAME - attack shares the bundle's exact specification` (rc=0). Only the impl region was edited in every file; axioms/@Pure/Requires/Ensures are byte-identical.

**POSITIVE CONTROL:** positive_control.py (verbatim model.py) -> `adversary verify` = VERIFIED in 16.9s (rc=0).

PER-ATTACK RESULTS (`adversary weakness nagini django__django-12193 <path>`); rc=2 = NOT-A-COUNTEREXAMPLE (spec rejected the impl), rc=0 = CANDIDATE:
 1. atk_1_prepatch_inplace.py - PREPATCH BUG re-encoded (`attrs[attr_selected()]=True; return attrs`). rc=2, 'attack does not verify'. Impl region is identical to the bundle's model_prepatch.py impl modulo its comment block; model_prepatch.py also passes same-spec. PREPATCH REPRODUCED = true. The read-only HALF permission Acc(dict_pred(attrs),1/2) makes the in-place write unprovable, exactly as refinement.md claims (G-DIFF).
 2. atk_2_partial_domain_one_sentinel.py - PARTIAL DOMAIN: branches on `value != val_false()` only, so the absent and empty-text sentinels wrongly get checked=True. rc=2.
 3. atk_3_boundary_force_false.py - BOUNDARY: not-selected path forces the selection key present with False instead of absent (would make subwidget attrs {'checked': False} where the P2P SplitArray test demands {}). rc=2.
 4. atk_4_inverted_branch.py - CONTROL-FLOW-EFFECT: the two branches swapped. rc=2.
 5. atk_5_drops_other_attrs.py - drops the caller's other attributes on the selected path (merges into a fresh EMPTY base; still fresh and still carries checked=True, so it probes whether the carry-through clause is load-bearing). rc=2.
 6. atk_6_returns_caller_object.py - IDENTITY/ALIASING: no write at all (half permission respected) but the not-selected branch returns the caller's own object - which is literally what the GOLD patch does in that branch. rc=2, i.e. the model's uniform `Result() is not attrs` is STRICTER than gold here. This is the one place the model is stronger than the repo rather than weaker, so it cannot admit a wrong impl; mapping.md §2 and refinement.md A4 justify it as observationally equivalent (super().get_context reads only contents), which I confirmed against the real source: Widget.build_attrs is `return {**base_attrs, **(extra_attrs or {})}` (widgets.py:250) - contents-only, no identity observation anywhere downstream.
 7. atk_7_single_point_hole.py - NARROW PARTIAL DOMAIN: wrong at exactly one value code (val_empty_text()), to test whether the Forall/Implies clauses really quantify over the whole int domain. rc=2.
 8. atk_8_wrong_key_token.py - A-LEG SUBSTITUTION: uses mapping_with faithfully but establishes attr_selected()+1 (a neighbouring key) instead of the selection attribute. rc=2.
 9. atk_9_infeasible_guard_wrong_tail.py - VACUITY probe: an infeasible guard (`value == val_false() and value == val_absent()`) fronting a self-call, with a genuinely WRONG tail (absent code gets checked=True). rc=2 - the infeasible guard did not let the wrong tail ride along.
11. atk_11_diverging_selfcall.py - DIVERGENCE / termination escape hatch: unguarded `return prepare_attrs(value, attrs)`. rc=2 - MustTerminate(10) is enforced at the method level, so the postconditions cannot be discharged vacuously.
12. atk_12_empty_passthrough.py - mirror of #5: drops the caller's attributes in the PASS-THROUGH branch. rc=2.

THE ONE CANDIDATE, RESOLVE EXECUTED:
10. atk_10_copy_then_merge.py - behaviour-PRESERVING restructuring composing the two audited primitives (copy-then-merge on the selected path, copy-of-copy on the pass-through). `adversary weakness` = `CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (17.4s)` (rc=0). Per protocol I materialized its faithful refined patch and RAN it through the official harness. Patch (generated with real `git diff` at base_commit 3fb7c12158a2402f0f80824f6778112071235803 in a throwaway clone, `git apply --check` clean): the selected path becomes `attrs = {**{**(attrs or {})}, 'checked': True}` and an explicit `else: attrs = {**{**(attrs or {})}}` mirrors the model's pass-through copy. Executed via swebench_unified.harness.run_resolve (run_id sbu-geq-audit-atk10-4749iohf): RESOLVED=True COMPLETED=True note='resolved', FAIL_TO_PASS 1/1 success 0 failure, PASS_TO_PASS 11/11 success 0 failure (resolve_atk10.json). RESOLVE-LANE CONTROL: the gold patch.diff run through the same path resolves identically (resolve_gold.json, RESOLVED=True, 1/1 + 11/11), so the harness lane is live and the atk_10 result is a real measurement, not a green-by-default. So the sole verifying same-spec impl RESOLVES - no verify⇏ correct witness. This attack is reported for evidence completeness; it is NOT a counterexample.

REFINEMENT.MD LEG AUDIT (§5 kinds): five legs A1-A5, tagged R / R / A-consumed / A-consumed+R / I. No kind-3 (unexpressible-changed-op) leg. Checked each against the real source at base_commit:
 - A1 (R): `attrs` param at Acc(...,1/2). Faithful - the patched code no longer writes attrs, so read-only is the right encoding, and it is what rejects atk_1.
 - A2 (R): `counts_as_selected` <-> `boolean_check`. CONFIRMED against widgets.py:503 `def boolean_check(v): return not (v is False or v is None or v == '')` - the model's `not (value==val_false() or value==val_absent() or value==val_empty_text())` is that rule deeply modelled over an int code, NOT an opaque oracle. atk_2/atk_7 confirm the whole domain is pinned.
 - A3 (A-consumed): `mapping_with` <-> `{**(attrs or {}), 'checked': True}` at widgets.py:525 post-patch. CONFIRMED verbatim against patch.diff. The axiom's Ensures are consumed (freshness `Result() is not base`, key present with flag, other keys carried, no spurious keys) - not assumed about the function under change; it axiomatizes the unchanged PEP-448 dict-display primitive the new code composes.
 - A4 (A-consumed + R): `mapping_copy` <-> the pass-through. The correspondence claim is that super().get_context reads only CONTENTS, never identity. VERIFIED in the real source: Widget.build_attrs = `{**base_attrs, **(extra_attrs or {})}` (widgets.py:250) and Widget.get_context (widgets.py:227) stores only `self.build_attrs(self.attrs, attrs)`; grep for identity observations on attrs downstream finds none. So modelling the pass-through as a fresh contents-identical copy is sound, and it makes the model STRICTER than gold (atk_6), never weaker.
 - A5 (I): no write to attrs + Acc(dict_pred(attrs),1/2) Required AND Ensured = the no-mutation guarantee the F2P test observes. Matches the actual F2P test body from the test_patch: `attrs = {'checked': False}; self.widget.get_context('name', True, attrs); self.assertIs(attrs['checked'], False)`.
 - Both A-legs are over UNCHANGED language primitives and are the only axioms; G-AX ran clean: axiom_check.py exit 0, 'mapping_with / mapping_copy axioms sound against the real dict-display merge/copy on 6 boundary bases + the SplitArray scenario + 20000 fuzz cases (base never mutated; result always fresh)'.

**CONCLUSION:** 12 distinct same-spec wrong/probe impls encoded and fully verified (partial-domain x2, boundary, control-flow-effect, attribute-dropping x2, identity/aliasing, wrong-key A-leg substitution, vacuity-guard, divergence, prepatch bug, plus one behaviour-preserving restructuring). 11 of 12 were REJECTED by the spec. The single CANDIDATE's faithful refined patch was materialized and EXECUTED through the official harness and RESOLVED (with the gold patch as a live-lane control). No verify⇏correct witness found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_inplace.py`, `atk_2_partial_domain_one_sentinel.py`, `atk_3_boundary_force_false.py`, `atk_4_inverted_branch.py`, `atk_5_drops_other_attrs.py`, `atk_6_returns_caller_object.py`, `atk_7_single_point_hole.py`, `atk_8_wrong_key_token.py`, `atk_9_infeasible_guard_wrong_tail.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_copy_then_merge.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_inplace.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain_one_sentinel.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_force_false.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_inverted_branch.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_drops_other_attrs.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_returns_caller_object.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_single_point_hole.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_wrong_key_token.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_infeasible_guard_wrong_tail.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_copy_then_merge.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_diverging_selfcall.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_empty_passthrough.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12193.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A boolean-style input widget prepares the attribute mapping that is handed to
  the shared rendering step. Whether the box is shown as selected is decided by
  a definite predicate on the supplied value: the value counts as selected unless
  it is one of the three "empty" sentinels (the boolean false, the absent value,
  or the empty text); every other value counts as selected.

  Two observations are pinned.

  (1) When the value counts as selected, the attribute mapping the rendering
      step receives carries the selection attribute set to true. Every other
      attribute already configured by the caller is carried through with its
      original value; the selection attribute is the only one established.

  (2) When the value does NOT count as selected, the attribute mapping the
      rendering step receives carries exactly the caller's attributes, with no
      selection attribute forced on.

  The consequence that matters: preparing the attribute mapping must NOT alter
  the caller's own mapping. The caller may reuse one mapping object to render a
  sequence of these widgets; if preparing the attributes for one selected value
  changed the caller's mapping, every later widget built from the same mapping
  would inherit the selection attribute even when its own value is not selected.
  The caller's mapping is therefore read-only here, and the prepared mapping is
  a fresh one.

Modelling choices (Nagini fragment):
  * An attribute mapping is a ``Dict[int, bool]`` from an attribute-name token
    to its flag value; only membership and per-key value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2). The
    selection attribute name is the module-level constant ``attr_selected()``.
  * The supplied value is an ``int`` code; the selection predicate is modelled
    deeply (``counts_as_selected``) as the repo's definite "not one of the three
    empty sentinels" rule (mapping.md §2), rather than pinned to an opaque
    oracle.
  * The fresh-mapping merge ``{**caller, attr: flag}`` is a standard mapping
    construction the code composes; it is the single callee ``mapping_with``,
    whose standard semantics are validated against real Python out-of-band
    (axiom_check.py, G-AX). It always allocates a NEW mapping, so the caller's
    mapping is never the result and is never written.

The caller's attribute mapping is read-only, so it is held at HALF permission
(Required AND Ensured) and never written. No string indexing is used (Nagini
bans it). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def mapping_with(base: Dict[int, bool], key: int, flag: bool) -> Dict[int, bool]:
    """Standard mapping construction ``{**base, key: flag}`` (an unchanged
    language primitive the code composes): a FRESH mapping holding every key of
    ``base`` plus ``key``, with ``flag`` the value at ``key`` and ``base``'s
    value at every other key. The result is always a new object, distinct from
    ``base`` (so ``base`` is read-only). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # A fresh mapping: never the base object (base stays unmutated).
    Ensures(Result() is not base)
    # The named key is present with the supplied flag.
    Ensures(key in Result() and Result()[key] == flag)
    # Every other key of base is carried through with base's value ...
    Ensures(Forall(int, lambda k: (Implies(k != key and k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    # ... and the result holds no key outside base plus the named key.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k == key or k in base))))


@ContractOnly
def mapping_copy(base: Dict[int, bool]) -> Dict[int, bool]:
    """Standard mapping copy ``{**base}`` (an unchanged language primitive): a
    FRESH mapping holding exactly every key of ``base`` with its value, distinct
    from ``base``. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(6))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Result() is not base)
    Ensures(Forall(int, lambda k: (Implies(k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           (k in base) and Result()[k] == base[k]))))
# axioms-end


# pure-start
@Pure
def attr_selected() -> int:
    # The attribute-name token for the selection flag the widget establishes.
    return 0


@Pure
def val_false() -> int:
    # Value code for the boolean-false sentinel (one of the three "empty"
    # values that count as NOT selected).
    return -1


@Pure
def val_absent() -> int:
    # Value code for the absent-value sentinel.
    return -2


@Pure
def val_empty_text() -> int:
    # Value code for the empty-text sentinel.
    return -3


@Pure
def counts_as_selected(value: int) -> bool:
    """The definite selection predicate: a value counts as selected unless it is
    one of the three empty sentinels (boolean false / absent / empty text)."""
    return not (value == val_false()
                or value == val_absent()
                or value == val_empty_text())
# pure-end


def prepare_attrs(value: int, attrs: Dict[int, bool]) -> Dict[int, bool]:
    # pre-conditions-start
    # The caller's attribute mapping is read-only here: HALF permission, never
    # written. (Held read-only so the operation cannot satisfy its postcondition
    # by overwriting the caller's mapping; the caller may reuse it for a
    # sequence of widgets and must observe it unchanged.)
    Requires(Acc(dict_pred(attrs), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The caller's mapping is returned untouched at the same half permission.
    Ensures(Acc(dict_pred(attrs), 1 / 2))
    # A fresh, full-permission mapping is prepared for the rendering step.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The prepared mapping is a DIFFERENT object from the caller's mapping.
    Ensures(Result() is not attrs)
    # (1) When the value counts as selected, the prepared mapping carries the
    #     selection attribute set to true ...
    Ensures(Implies(counts_as_selected(value),
                    attr_selected() in Result() and Result()[attr_selected()] == True))
    # ... and every OTHER caller attribute is carried through with its value.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k != attr_selected() and k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    # ... and the prepared mapping introduces no key the caller did not have,
    #     other than the selection attribute itself.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       k == attr_selected() or k in attrs)))))
    # (2) When the value does NOT count as selected, the prepared mapping holds
    #     exactly the caller's attributes (no selection attribute forced on):
    #     same keys, same values, in both directions.
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       (k in attrs) and Result()[k] == attrs[k])))))
    # post-conditions-end
    # impl-start
    if counts_as_selected(value):
        # Fresh mapping: every caller attribute, with the selection flag forced
        # on. The caller's mapping is read, never written.
        return mapping_with(attrs, attr_selected(), True)
    # Pass-through: a fresh copy of exactly the caller's attributes.
    return mapping_copy(attrs)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-12193 / nagini. Invocation used throughout (repo root swe-proof): `SBU_BENCHMARK_DIR=benchmark-verified PYTHONPATH=src ~/anaconda3/bin/python -m swebench_unified.adversary...` (no installed swebench_unified on PATH; Bundle resolution confirmed to point at benchmark-verified/django__django-12193/nagini/model.py). Verifications were run 3-at-a-time as background jobs (each Nagini check spawns a JVM+Z3); this changed only the schedule, every attack was fully verified.

**SAME-SPEC:** all 12 attacks + the positive control return `SAME - attack shares the bundle's exact specification` (rc=0). Only the impl region was edited in every file; axioms/@Pure/Requires/Ensures are byte-identical.

**POSITIVE CONTROL:** positive_control.py (verbatim model.py) -> `adversary verify` = VERIFIED in 16.9s (rc=0).

PER-ATTACK RESULTS (`adversary weakness nagini django__django-12193 <path>`); rc=2 = NOT-A-COUNTEREXAMPLE (spec rejected the impl), rc=0 = CANDIDATE:
 1. atk_1_prepatch_inplace.py - PREPATCH BUG re-encoded (`attrs[attr_selected()]=True; return attrs`). rc=2, 'attack does not verify'. Impl region is identical to the bundle's model_prepatch.py impl modulo its comment block; model_prepatch.py also passes same-spec. PREPATCH REPRODUCED = true. The read-only HALF permission Acc(dict_pred(attrs),1/2) makes the in-place write unprovable, exactly as refinement.md claims (G-DIFF).
 2. atk_2_partial_domain_one_sentinel.py - PARTIAL DOMAIN: branches on `value != val_false()` only, so the absent and empty-text sentinels wrongly get checked=True. rc=2.
 3. atk_3_boundary_force_false.py - BOUNDARY: not-selected path forces the selection key present with False instead of absent (would make subwidget attrs {'checked': False} where the P2P SplitArray test demands {}). rc=2.
 4. atk_4_inverted_branch.py - CONTROL-FLOW-EFFECT: the two branches swapped. rc=2.
 5. atk_5_drops_other_attrs.py - drops the caller's other attributes on the selected path (merges into a fresh EMPTY base; still fresh and still carries checked=True, so it probes whether the carry-through clause is load-bearing). rc=2.
 6. atk_6_returns_caller_object.py - IDENTITY/ALIASING: no write at all (half permission respected) but the not-selected branch returns the caller's own object - which is literally what the GOLD patch does in that branch. rc=2, i.e. the model's uniform `Result() is not attrs` is STRICTER than gold here. This is the one place the model is stronger than the repo rather than weaker, so it cannot admit a wrong impl; mapping.md §2 and refinement.md A4 justify it as observationally equivalent (super().get_context reads only contents), which I confirmed against the real source: Widget.build_attrs is `return {**base_attrs, **(extra_attrs or {})}` (widgets.py:250) - contents-only, no identity observation anywhere downstream.
 7. atk_7_single_point_hole.py - NARROW PARTIAL DOMAIN: wrong at exactly one value code (val_empty_text()), to test whether the Forall/Implies clauses really quantify over the whole int domain. rc=2.
 8. atk_8_wrong_key_token.py - A-LEG SUBSTITUTION: uses mapping_with faithfully but establishes attr_selected()+1 (a neighbouring key) instead of the selection attribute. rc=2.
 9. atk_9_infeasible_guard_wrong_tail.py - VACUITY probe: an infeasible guard (`value == val_false() and value == val_absent()`) fronting a self-call, with a genuinely WRONG tail (absent code gets checked=True). rc=2 - the infeasible guard did not let the wrong tail ride along.
11. atk_11_diverging_selfcall.py - DIVERGENCE / termination escape hatch: unguarded `return prepare_attrs(value, attrs)`. rc=2 - MustTerminate(10) is enforced at the method level, so the postconditions cannot be discharged vacuously.
12. atk_12_empty_passthrough.py - mirror of #5: drops the caller's attributes in the PASS-THROUGH branch. rc=2.

THE ONE CANDIDATE, RESOLVE EXECUTED:
10. atk_10_copy_then_merge.py - behaviour-PRESERVING restructuring composing the two audited primitives (copy-then-merge on the selected path, copy-of-copy on the pass-through). `adversary weakness` = `CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (17.4s)` (rc=0). Per protocol I materialized its faithful refined patch and RAN it through the official harness. Patch (generated with real `git diff` at base_commit 3fb7c12158a2402f0f80824f6778112071235803 in a throwaway clone, `git apply --check` clean): the selected path becomes `attrs = {**{**(attrs or {})}, 'checked': True}` and an explicit `else: attrs = {**{**(attrs or {})}}` mirrors the model's pass-through copy. Executed via swebench_unified.harness.run_resolve (run_id sbu-geq-audit-atk10-4749iohf): RESOLVED=True COMPLETED=True note='resolved', FAIL_TO_PASS 1/1 success 0 failure, PASS_TO_PASS 11/11 success 0 failure (resolve_atk10.json). RESOLVE-LANE CONTROL: the gold patch.diff run through the same path resolves identically (resolve_gold.json, RESOLVED=True, 1/1 + 11/11), so the harness lane is live and the atk_10 result is a real measurement, not a green-by-default. So the sole verifying same-spec impl RESOLVES - no verify⇏ correct witness. This attack is reported for evidence completeness; it is NOT a counterexample.

REFINEMENT.MD LEG AUDIT (§5 kinds): five legs A1-A5, tagged R / R / A-consumed / A-consumed+R / I. No kind-3 (unexpressible-changed-op) leg. Checked each against the real source at base_commit:
 - A1 (R): `attrs` param at Acc(...,1/2). Faithful - the patched code no longer writes attrs, so read-only is the right encoding, and it is what rejects atk_1.
 - A2 (R): `counts_as_selected` <-> `boolean_check`. CONFIRMED against widgets.py:503 `def boolean_check(v): return not (v is False or v is None or v == '')` - the model's `not (value==val_false() or value==val_absent() or value==val_empty_text())` is that rule deeply modelled over an int code, NOT an opaque oracle. atk_2/atk_7 confirm the whole domain is pinned.
 - A3 (A-consumed): `mapping_with` <-> `{**(attrs or {}), 'checked': True}` at widgets.py:525 post-patch. CONFIRMED verbatim against patch.diff. The axiom's Ensures are consumed (freshness `Result() is not base`, key present with flag, other keys carried, no spurious keys) - not assumed about the function under change; it axiomatizes the unchanged PEP-448 dict-display primitive the new code composes.
 - A4 (A-consumed + R): `mapping_copy` <-> the pass-through. The correspondence claim is that super().get_context reads only CONTENTS, never identity. VERIFIED in the real source: Widget.build_attrs = `{**base_attrs, **(extra_attrs or {})}` (widgets.py:250) and Widget.get_context (widgets.py:227) stores only `self.build_attrs(self.attrs, attrs)`; grep for identity observations on attrs downstream finds none. So modelling the pass-through as a fresh contents-identical copy is sound, and it makes the model STRICTER than gold (atk_6), never weaker.
 - A5 (I): no write to attrs + Acc(dict_pred(attrs),1/2) Required AND Ensured = the no-mutation guarantee the F2P test observes. Matches the actual F2P test body from the test_patch: `attrs = {'checked': False}; self.widget.get_context('name', True, attrs); self.assertIs(attrs['checked'], False)`.
 - Both A-legs are over UNCHANGED language primitives and are the only axioms; G-AX ran clean: axiom_check.py exit 0, 'mapping_with / mapping_copy axioms sound against the real dict-display merge/copy on 6 boundary bases + the SplitArray scenario + 20000 fuzz cases (base never mutated; result always fresh)'.

**CONCLUSION:** 12 distinct same-spec wrong/probe impls encoded and fully verified (partial-domain x2, boundary, control-flow-effect, attribute-dropping x2, identity/aliasing, wrong-key A-leg substitution, vacuity-guard, divergence, prepatch bug, plus one behaviour-preserving restructuring). 11 of 12 were REJECTED by the spec. The single CANDIDATE's faithful refined patch was materialized and EXECUTED through the official harness and RESOLVED (with the gold patch as a live-lane control). No verify⇏correct witness found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE: compared prepare_attrs against the base_commit worktree WITH patch.diff APPLIED (gold patch extracted from instance.json, applied cleanly to a fresh worktree of 3fb7c12158a2402f0f80824f6778112071235803 from the upstream repository). The patch delta itself ({**(attrs or {}), 'checked': True} replacing the in-place attrs['checked'] = True) was therefore NOT counted as a divergence. Base commit used as reference only for the untouched callees the axioms model (the dict-display merge/copy language primitives).

**SAME-SPEC BASELINE:** `adversary same-spec nagini django__django-12193 atk.py` on the pristine model.py returns 'SAME -- attack shares the bundle's exact specification' (exit 0), so the spec region I audited is byte-identical to the bundle's.

**NON-VACUITY:** `scripts/nagini_verify.sh model.py` -> 'Verification successful' (15.9s, exit 0). Two negative controls both fail as required (see counterexample field), so the spec is live, not trivially true.

PRIMARY EVIDENCE -- independent clause-by-clause differential (diff_indep.py). I intercepted Input.get_context to capture the mapping the real patched CheckboxInput.get_context actually hands to super() -- i.e. the model's Result() DIRECTLY, not a downstream build_attrs copy -- re-encoded it into the Dict[int,bool] carrier via the declared bridge, and asserted EVERY postcondition clause of prepare_attrs plus caller-non-mutation. 60,084 Requires-satisfying inputs (boundary grid of 12 value codes x 7 attrs shapes including the F2P input {'checked': False}, plus 60,000 seeded fuzz). Result: the ONLY failing clause across all 60,084 inputs was 'Result() is not attrs', 6,602 occurrences, 100% of them on the not-selected branch. Every content clause held on every input: selected -> attr_selected present and True; selected -> other caller attrs carried through; selected -> no spurious keys; not-selected -> Result and attrs equal in both directions; caller attrs never mutated by the real callee.

ADJUDICATING THAT ONE CLAUSE (the identity R-refinement, mapping.md §2) -- three independent machine checks, all clean:
1. Aliasing probe: for all 5 branch cases, the mapping handed to super is NEVER the object that lands in context['widget']['attrs'] (build_attrs always allocates). So a caller cannot observe whether the pass-through was fresh or aliased.
2. Variant equivalence: substituted the model's shape (else: attrs = {**(attrs or {})}) for the real pass-through and diffed the full context dict, the caller dict after the call, and the rendered HTML over 42 (value, attrs) combinations spanning None/{}/{'checked':False}/{'checked':True}/{'x':1}/mixed x False/None/''/True/'foo'/0/1. 0 differences on all three observations.
3. Real test suite with the model-shaped impl installed in the patched worktree: forms_tests.widget_tests.test_checkboxinput 12/12 OK (includes the F2P test_get_context_does_not_mutate_attrs), and forms_tests + model_forms 816 tests OK (1 skip). If the strengthening were unfaithful it would have to break something here; nothing broke.

### OTHER DIMENSIONS CHECKED (no drift found):
* Selection predicate: exhaustive comparison of counts_as_selected against the REAL boolean_check over the 3 sentinels plus a 24-value selected pool chosen to include Python equality traps (0, 0.0, False-adjacent, '0', 'False', 'None', b'', nan, empty containers). 27/27 agree, 0 divergences. Critically, NO value outside {False, None, ''} is rejected by the real boolean_check, so the model's 3-sentinel partition is exactly the real binary partition -- 0 and '0' correctly SELECT (matching P2P test_render_int). Predicate is modeled deeply, not as an opaque oracle, so this is a real check.
* One boundary worth recording honestly: a pathological object with a custom `__eq__` returning True for '' is a 4th class the real boolean_check rejects. It is unreachable through the int-code carrier, i.e. a domain NARROWING of the input space, not an over-strong postcondition -- it cannot make the spec reject a correct impl.
* self.attrs independence: verified Result() does not depend on the widget's own self.attrs (5 self.attrs configurations x 5 values -> identical handed mappings), so the model omitting self.attrs is not an omitted determinant of its own output. self.attrs enters only later, inside build_attrs.
* The attrs-is-None narrowing: at the Result() boundary None and {} do differ (None passes through as None on the not-selected path), but downstream they coalesce -- 18 (self.attrs, value) combinations show 0 differences in context and 0 in rendered HTML, because build_attrs applies (attrs or {}). So taking a present possibly-empty Dict is observationally faithful, matching mapping.md §2.
* Axioms (base-commit reference, patch does not touch them): mapping_with / mapping_copy model the PEP 448 dict-display merge and copy. I re-derived their Ensures against the real primitives; the freshness clause Result() is not base is exactly what CPython BUILD_MAP/DICT_MERGE guarantees, and it is the load-bearing clause that kills the pre-patch in-place write.

**ATTACK ANGLES TRIED AND FAILED TO LAND:** over-strong freshness on the pass-through path (inert, 3 checks above); predicate too coarse (exhaustive check, exact match); missing self.attrs determinant (proven independent); None-vs-{} carrier narrowing (downstream-equivalent); vacuity (both controls fail). I could not construct any input on which the modeled function disagrees observably with the real post-patch callee.

**VERDICT:** FAITHFUL. The spec is a sound, non-vacuous, conservatively-strengthened abstraction of the real post-patch CheckboxInput.get_context attribute-mapping construction.

Counterexample / evidence:

```
none -- no attack constructed; the spec is not too strong. The only clause that structurally differs from the real callee (Result() is not attrs on the not-selected path) was machine-proven observationally inert against the real patched repo, so it yields no counterexample and condemns no correct implementation. Controls confirm the spec is not vacuously satisfied: model_prepatch.py (the pre-patch in-place write attrs[attr_selected()] = True) FAILS verification with 'insufficient permission' at prepatch.py:181, and an Assert(False) probe in the impl region FAILS ('Assertion False might not hold'), so the postconditions have real force.
```

**REFERENCE DISCIPLINE:** compared prepare_attrs against the base_commit worktree WITH patch.diff APPLIED (gold patch extracted from instance.json, applied cleanly to a fresh worktree of 3fb7c12158a2402f0f80824f6778112071235803 from the upstream repository). The patch delta itself ({**(attrs or {}), 'checked': True} replacing the in-place attrs['checked'] = True) was therefore NOT counted as a divergence. Base commit used as reference only for the untouched callees the axioms model (the dict-display merge/copy language primitives).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE REVIEW — django__django-12193/nagini. Verdict NO-LEAKAGE.

NO RELAXATION IN THIS BUNDLE (checked, not assumed). meta.json has no `relaxed_leakage` key (python3: `'relaxed_leakage' in meta` -> False; no key matching /relax/i), gates.G-LEAK.status == "pass" (not "relaxed"), and there is no RELAXED_LEAKAGE.md in the bundle dir (ls + glob). So there is no unavoidability argument to re-derive and no inherited disposition; this is judged as an ordinary strict-leakage review.

**NO FILE IN THE BUNDLE ADDRESSES ME.** I grepped every bundle artifact (model.py, model_prepatch.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py, meta.json) for auditor/reviewer/panel-directed language and for verdict prescriptions; zero hits outside verdict.md, which is the harness's own prior-run record (it reports past role outcomes, it does not instruct me). I also ran leakage.reviewer_directed() over refinement.md and mapping.md: [] and [] — clean. No artifact told me how to record.

**WHAT THE CONSUMER ACTUALLY SEES.** Confirmed from eval/dataset.py as_dict(): agent-visible fields are problem_statement, hints_text, localization, spec_view, modeled_functions; WITHHELD_FIELDS = patch/test_patch/F2P/P2P. mapping.md and refinement.md are NOT consumer-visible, so their explicit "the heart of the fix" / "pre-patch" narration is auditor documentation and out of leakage scope. My screen is the elided spec_view.

SPEC VIEW MEASURED, NOT ASSUMED. Recomputed markers.spec_view(model.py, nagini) myself: sha256 8c0d7d9fb12522109b37c970ac0200b618bfcb08c317cd60f197f896bb28b267, matching meta.json gates.G-HYGIENE.region_hashes.spec_view exactly (so the view I screened is the view the gate screened). model.py sha256 385c51ba1335... matches gates.G-AX.sources.model.py. The impl region collapses to `...  # implementation elided` — nothing of the impl survives into the view.

MECHANICAL SCREEN RE-RUN (my own invocation, not a read of the recorded status): leakage.screen(model.py, nagini, instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. Independently: gold changed lines are ['if attrs is None:', 'attrs = {}', "attrs['checked'] = True", "attrs = {**(attrs or {}), 'checked': True}"] — none appears normalized in the view; patched path django/forms/widgets.py and dotted django.forms.widgets absent; the only distinctive changed symbol is 'format_value', absent from the view. Targeted grep of the view for get_context / CheckboxInput / widgets.py / check_test / boolean_check / SplitArray / final_attrs / checked / django / forms / super() returned only the harmless `Result() is not None`, `Dict[int, bool]` and the instance-id line. No narration vocabulary (bug/fix/patch/previously/incorrectly/...) survives in any view comment or docstring.

**DISCRIMINATOR IS ALREADY PUBLIC.** The problem_statement itself states the diagnosis in full: "This is caused by the CheckboxInput widget's get_context() modifying the attrs dict passed into it. This is the only widget that modifies the attrs dict passed into its get_context()", plus the symptom (every widget after the first True defaults to checked) and a direct link to widgets.py#L527. A public reader therefore already knows the cure = do not mutate the caller's mapping; hand on a fresh one carrying checked=True. The spec view's discriminating content is exactly that and no more: the read-only HALF permission Acc(dict_pred(attrs), 1/2) Required AND Ensured, and `Ensures(Result() is not attrs)`. Both are restatements of the publicly-stated no-mutation requirement, not a disclosure beyond it.

LOAD-BEARING CHECK (the strip test, run for real). The freshness/read-only clauses are not decorative narration that could be removed: `bash scripts/nagini_verify.sh model.py` -> "Verification successful" in 19.09s (spec non-vacuous), while `nagini_verify.sh model_prepatch.py` -> "Verification failed / model_prepatch.py:181:9: The precondition of attrs[attr_selected()] = True might not hold. There might be insufficient permission." markers.same_spec(model, model_prepatch) == True, and diff of the two impl regions shows the only difference is the pre-patch in-place write `attrs[attr_selected()] = True; return attrs`. So the half-permission clause is precisely what rejects the PRE-patch impl — it is load-bearing spec, and eliding it would make the spec blind to the very behavior the public issue demands.

**AXIOM DOCSTRINGS DO NOT OVER-DISCLOSE.** mapping_with/mapping_copy name the unchanged language primitives `{**base, key: flag}` / `{**base}` in the abstract (base/key/flag), never `attrs`, `'checked'`, or `get_context`. Notably the view does NOT reveal the gold's None-coalescing `attrs or {}` at all — the model takes a present Dict — so the view discloses strictly LESS than the gold hunk. Stating a primitive's semantics is also mandatory for axiom soundness (G-AX), and every semantically-equivalent fresh-dict form (dict(attrs)+assign,.copy(), {**attrs,...}) resolves identically, so the syntactic form carries no edit-localization the issue did not already force.

**ORTHOGONAL CONTENT CANNOT LEAK THE EDIT.** counts_as_selected / val_false / val_absent / val_empty_text model check_test/boolean_check, which the gold patch does not touch (the hunk leaves the `if self.check_test(value):` line as context). Behavior the edit does not change cannot reveal the edit. (Noted for the record, outside my remit: the consumer-visible meta.json modeled_functions entry carries repo_symbol django.forms.widgets.CheckboxInput.get_context and repo_location widgets.py:521 — but that is deliberate localization and the problem_statement already gives both the symbol and the file+line, so it is not beyond problem_statement either.)

**CORE GATES CONFIRMED SOUND ON MY OWN MEASUREMENTS:** G-VERIFY (verified, 19.09s), G-DIFF/G-GOLD (gold verifies, prepatch fails on the permission discriminator), G-HYGIENE (spec_view hash reproduces). No spec-view line reveals the gold edit more specifically than the public problem_statement already does.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
