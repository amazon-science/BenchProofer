# P2 adversarial audit — django__django-11790

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1_prepatch.py`, `atk_2_misdirected_key.py`, `atk_3_partial_domain_stale.py`, `atk_4_zero_boundary.py`, `atk_5_branch_key.py`, `atk_6_spurious_key.py`, `atk_7_oracle_echo.py`, `atk_8_clobber_other.py`, `atk_9_widget_default.py`, `atk_10_diverge.py`, `atk_11_computed_name.py`, `atk_13_shadow_clobber.py`, +7 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_val_equal_double.py` |

**Non-vacuity.** The positive control `control_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec wrong impl whose faithful patch fails to resolve. 20 same-spec attacks run (all `same-spec` exit 0); 19 REFUTED by Nagini (weakness exit 2); the single CANDIDATE (atk_12_val_equal_double.py, weakness exit 0, 12.4s) had its faithful patch materialized and RUN through the official harness: completed=true, RESOLVED=TRUE, attempts=1, flaky=false. It is not a counterexample because `'maxlength' + '' == 'maxlength'` in Python, so its extra shadow write targets the SAME real key and is immediately overwritten by the gold write (faithful post-state measured: {'maxlength': 255}); Nagini admits it only because Viper dict keys are Ref-identity while str `!=` is value-based, so the model cannot decide the two index expressions are the same key — the model is STRICTLY MORE permissive than reality here, which is the safe direction. GOLD control on the same harness: completed=true, RESOLVED=TRUE, attempts=1 — so the oracle is healthy and the resolve verdicts are the patches' behaviour.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,5 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
     # impl-end
```

Attack 2 — `atk_2_misdirected_key.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,6 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs['size'] = username_max_length
     return field_max_length
     # impl-end
```

Attack 3 — `atk_3_partial_domain_stale.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,7 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    if attr_maxlength() not in widget_attrs:
+        widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
     # impl-end
```

Attack 4 — `atk_4_zero_boundary.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -189,7 +189,10 @@
                     widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])))
     # post-conditions-end
     # impl-start
-    username_max_length = resolve_limit(declared_max_length)
+    if declared_max_length is None:
+        username_max_length = default_limit()
+    else:
+        username_max_length = declared_max_length
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
```

Attack 5 — `atk_5_branch_key.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,9 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    if declared_max_length is None:
+        widget_attrs[attr_maxlength()] = username_max_length
+    else:
+        widget_attrs['size'] = username_max_length
     return field_max_length
     # impl-end
```

Attack 6 — `atk_6_spurious_key.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,6 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs['autocomplete'] = username_max_length
     return field_max_length
     # impl-end
```

Attack 7 — `atk_7_oracle_echo.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -189,7 +189,10 @@
                     widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])))
     # post-conditions-end
     # impl-start
-    username_max_length = resolve_limit(declared_max_length)
+    if declared_max_length is None:
+        username_max_length = 254
+    else:
+        username_max_length = 255
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
```

Attack 8 — `atk_8_clobber_other.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,7 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    if attr_other() in widget_attrs:
+        widget_attrs[attr_other()] = username_max_length
     return field_max_length
     # impl-end
```

Attack 9 — `atk_9_widget_default.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,6 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs[attr_maxlength()] = default_limit()
     return field_max_length
     # impl-end
```

Attack 10 — `atk_10_diverge.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,9 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     return field_max_length
     # impl-end
```

Attack 11 — `atk_11_computed_name.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,6 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs[attr_maxlength() + ''] = username_max_length
     return field_max_length
     # impl-end
```

Attack 12 — `atk_12_val_equal_double.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,7 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
+    widget_attrs[attr_maxlength() + ''] = default_limit()
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
     # impl-end
```

Attack 13 — `atk_13_shadow_clobber.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,6 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs[attr_maxlength() + ''] = default_limit()
     return field_max_length
     # impl-end
```

Attack 14 — `atk_14_shadow_split_literal.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,6 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    widget_attrs['max' + 'length'] = default_limit()
     return field_max_length
     # impl-end
```

Attack 15 — `atk_15_drop_other.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,7 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    if attr_other() in widget_attrs:
+        del widget_attrs[attr_other()]
     return field_max_length
     # impl-end
```

Attack 16 — `atk_16_off_by_one.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -189,7 +189,7 @@
                     widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])))
     # post-conditions-end
     # impl-start
-    username_max_length = resolve_limit(declared_max_length)
+    username_max_length = resolve_limit(declared_max_length) + 1
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
```

Attack 17 — `atk_17_prestate_dep_value.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,9 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
-    widget_attrs[attr_maxlength()] = username_max_length
+    if attr_maxlength() in widget_attrs:
+        widget_attrs[attr_maxlength()] = default_limit()
+    else:
+        widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
     # impl-end
```

Attack 18 — `atk_18_other_name_overwrite.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -192,5 +192,7 @@
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
+    if attr_other() in widget_attrs:
+        widget_attrs[attr_other() + ''] = default_limit()
     return field_max_length
     # impl-end
```

Attack 19 — `atk_19_negative_boundary.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -189,7 +189,12 @@
                     widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])))
     # post-conditions-end
     # impl-start
-    username_max_length = resolve_limit(declared_max_length)
+    if declared_max_length is None:
+        username_max_length = default_limit()
+    elif declared_max_length <= 0:
+        username_max_length = default_limit()
+    else:
+        username_max_length = declared_max_length
     field_max_length = username_max_length
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
```

Attack 20 — `atk_20_param_rebind.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -191,6 +191,7 @@
     # impl-start
     username_max_length = resolve_limit(declared_max_length)
     field_max_length = username_max_length
+    widget_attrs = {}
     widget_attrs[attr_maxlength()] = username_max_length
     return field_max_length
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control_gold.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SCOPE: A-legs (axioms / deep-model reference) + model<->patch correspondence, per instructions. Bundle model.py sha256 a471f912ae385cebcc3b1b2a6e999162a5e984aad7c9affded433d5548f35a84. Ran from repo root swe-proof;

COMMANDS (per attack): PYTHONPATH=src python3 -m swebench_unified.adversary same-spec nagini django__django-11790 <atk>  ->  exit 0 for all 20 + control_gold.py (only the impl region differs; axioms/@Pure/Requires/Ensures byte-identical). PYTHONPATH=src python3 -m swebench_unified.adversary weakness nagini django__django-11790 <atk>. Resolve: PYTHONPATH=src python3 resolve_one.py <patch> (harness.run_resolve). Verifications were run 3-at-a-time as concurrent background jobs (schedule only; every attack fully verified).

### PER-ATTACK RESULTS (log_*.txt in the scratch dir):
1 atk_1_prepatch.py — PREPATCH BUG (field limit set, widget maxlength never established). exit 2 REJECTED on `attr_maxlength() in widget_attrs`. *** PREPATCH REPRODUCED *** (matches model_prepatch.py, whose only delta is that same line). 2 atk_2_misdirected_key.py — MISDIRECTED GOLD KEY, i.e. the PRIOR RECORDED BREAK re-encoded on the new carrier: publishes the resolved limit under 'size' instead. exit 2 REJECTED. *** THE PRIOR verify-not-correct BREAK IS CLOSED. *** 3 atk_3_partial_domain_stale.py — PARTIAL DOMAIN (§F W8): write guarded by "maxlength not already present", leaving a STALE rendered cap. exit 2 REJECTED (§F domain-totality repair load-bearing).

4 atk_4_zero_boundary.py — BOUNDARY: declared 0 used verbatim instead of resolving to 254. exit 2 REJECTED (leg A2 truthiness mirror load-bearing). 5 atk_5_branch_key.py — CONTROL-FLOW EFFECT ON THE NAME: 'maxlength' on one branch, 'size' on the other. exit 2 REJECTED. 6 atk_6_spurious_key.py — spurious extra attribute write clobbering the autocomplete hint (§E W10). exit 2 REJECTED (membership frame). 7 atk_7_oracle_echo.py — UNGROUNDED-ORACLE ECHO: hard-codes exactly the two F2P configs (None->254, else 255). exit 2 REJECTED on `Result() == resolve_limit(...)`. No test-echo shortcut admitted. 8 atk_8_clobber_other.py — VALUE-FRAME CLOBBER (W5), guarded so no key is ADDED. exit 2 REJECTED (value frame).

9 atk_9_widget_default.py — FIELD/WIDGET DISAGREEMENT: widget always gets the default. exit 2 REJECTED. 10 atk_10_diverge.py — divergence after the gold post-state. exit 2 REJECTED (MustTerminate at METHOD level). 11 atk_11_computed_name.py — COMPUTED NAME instead of the token (`attr_maxlength() + ''`) as the SOLE write. exit 2 REJECTED: Viper cannot prove the concatenated Ref equals the token, so the maxlength clauses fail. This is the direct probe of the name-domain repair. 12 atk_12_val_equal_double.py — VAL-EQUAL/REF-DISTINCT SHADOW WRITE before the gold write. exit 0 CANDIDATE -> patch materialized (patch_atk_12.diff, `git apply --check` clean at base_commit b1d6b35e in a fresh detached worktree) -> harness: completed=true, RESOLVED=TRUE, attempts=1, flaky=false.

NOT a break (see counterexample field). 13 atk_13_shadow_clobber.py — the ORDER-REVERSED variant: gold write FIRST, then the val-equal shadow write of the default (faithfully this CLOBBERS the resolved cap with 254 for every declared maximum — a genuine regression). exit 2 REJECTED. This is the important asymmetry: the dangerous ordering is refuted and only the harmless ordering verifies. 14 atk_14_shadow_split_literal.py — same hole via 'max' + 'length'. exit 2 REJECTED. 15 atk_15_drop_other.py — DROPS a pre-existing attribute (del). exit 2 REJECTED (membership frame, drop direction). 16 atk_16_off_by_one.py — resolved limit +1 in BOTH places (mutually consistent but wrong). exit 2 REJECTED: the spec pins the VALUE, not merely agreement.

17 atk_17_prestate_dep_value.py — PRE-STATE-DEPENDENT VALUE: default when a limit was already present (the CharField(max_length=75) subclass path). exit 2 REJECTED. 18 atk_18_other_name_overwrite.py — overwrite a pre-existing OTHER attribute via a computed name, no key added. exit 2 REJECTED. 19 atk_19_negative_boundary.py — DISTINCT declared-axis boundary: a NEGATIVE declared max is truthy so `x or 254` uses it verbatim; this impl defaults it. exit 2 REJECTED. 20 atk_20_param_rebind.py — PARAMETER REBINDING / LOST MUTATION: rebinds widget_attrs to a fresh dict and configures THAT, so the caller's widget is never written. exit 2 REJECTED (dict_pred post-permission on the parameter).

CONTROLS (nothing INCONCLUSIVE): POSITIVE CONTROL control_gold.py (= model.py verbatim) `bash scripts/nagini_verify.sh` exit 0, "Verification successful" in 10.5s -> the 19 refutations are discriminating and the spec is non-vacuous. GOLD resolve control: RESOLVED=TRUE, attempts=1. No exit 124, no timeout, no incomplete harness run.

A-LEG / REFINEMENT.MD AUDIT (the instructed focus): leg kinds are A0 R+I, A1 R, A2 R, A3 R, A4 R+I, A5 I, B1 A-reference — NO kind-3 step, and grep confirms 0 occurrences of @ContractOnly in model.py, so §C's "no consumed axiom" claim is accurate; every leg is R / A-reference / I as required. The single A-reference (B1) is genuinely EXECUTABLE and I ran it: axiom_check.py exit 0, driving the REAL gold-patched AuthenticationForm over 7 boundary + 200 fuzz user models (including the reachable declared-0 TextField case) asserting field.max_length AND widget.attrs['maxlength'] both == resolve_limit(declared), plus survival of autocapitalize/autocomplete/autofocus.

The two defects the prior pass recorded are REPAIRED and I confirmed each mechanically: (i) the name domain is now Dict[str, object] (textual, disjoint from the length domain), so the int-arithmetic route to the maxlength key is ILL-TYPED — atk_2/atk_5 (its faithful shapes) are refuted; (ii) axiom_check.py NOW grounds the KEY domain (lines 126-133: isinstance(key, str) and not isinstance(key, int) over every widget.attrs key), so G-AX can observe that real attribute names are strings. A2's truthiness mirror and A0's domain totality are both confirmed load-bearing (atk_4, atk_19, atk_3, atk_17 all rejected).

RESIDUAL DOCUMENTATION DEFECT (non-blocking, does NOT admit a non-resolving impl — reporting for the builder): refinement.md §E items 1 and 2 still QUOTE the frame clauses as `Forall(int, lambda a: ...)`, but model.py lines 176 and 179 actually carry `Forall(str, ...)`. The prose is stale from the pre-repair revision and now mis-describes the very carrier change that closed the recorded break; §E's surrounding narrative text does correctly discuss the textual name domain. No verifying wrong impl follows from this (it is a quotation error, not a spec weakness), but §E should be updated to quote `Forall(str, ...)` so the document matches the frozen bytes it audits.

HONEST LIMIT ON THE CLAIM: atk_12 shows the model is more permissive than Python on Ref-vs-value name identity (it cannot prove `attr_maxlength() + ''` is the same key as `attr_maxlength()`). Here that permissiveness is SAFE in the resolve-deciding direction — the only shapes it admits are ones where the gold write lands last and wins (atk_12 RESOLVED=TRUE), while every ordering in which the shadow write would survive is refuted (atk_11, atk_13, atk_14). I could not construct a verifying same-spec impl whose faithful patch fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1_prepatch.py`, `atk_2_misdirected_key.py`, `atk_3_partial_domain_stale.py`, `atk_4_zero_boundary.py`, `atk_5_branch_key.py`, `atk_6_spurious_key.py`, `atk_7_oracle_echo.py`, `atk_8_clobber_other.py`, `atk_9_widget_default.py`, `atk_10_diverge.py`, `atk_11_computed_name.py`, `atk_13_shadow_clobber.py`, +7 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_val_equal_double.py` |

**Non-vacuity.** The positive control `control_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec wrong impl whose faithful patch fails to resolve. 20 same-spec attacks run (all `same-spec` exit 0); 19 REFUTED by Nagini (weakness exit 2); the single CANDIDATE (atk_12_val_equal_double.py, weakness exit 0, 12.4s) had its faithful patch materialized and RUN through the official harness: completed=true, RESOLVED=TRUE, attempts=1, flaky=false. It is not a counterexample because `'maxlength' + '' == 'maxlength'` in Python, so its extra shadow write targets the SAME real key and is immediately overwritten by the gold write (faithful post-state measured: {'maxlength': 255}); Nagini admits it only because Viper dict keys are Ref-identity while str `!=` is value-based, so the model cannot decide the two index expressions are the same key — the model is STRICTLY MORE permissive than reality here, which is the safe direction. GOLD control on the same harness: completed=true, RESOLVED=TRUE, attempts=1 — so the oracle is healthy and the resolve verdicts are the patches' behaviour.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_misdirected_key.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_domain_stale.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_zero_boundary.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_branch_key.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_spurious_key.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_clobber_other.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_widget_default.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_diverge.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_computed_name.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_val_equal_double.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_shadow_clobber.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_shadow_split_literal.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_drop_other.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_off_by_one.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_prestate_dep_value.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18_other_name_overwrite.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19_negative_boundary.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20_param_rebind.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control_gold.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SCOPE: A-legs (axioms / deep-model reference) + model<->patch correspondence, per instructions. Bundle model.py sha256 a471f912ae385cebcc3b1b2a6e999162a5e984aad7c9affded433d5548f35a84. Ran from repo root swe-proof;

COMMANDS (per attack): PYTHONPATH=src python3 -m swebench_unified.adversary same-spec nagini django__django-11790 <atk>  ->  exit 0 for all 20 + control_gold.py (only the impl region differs; axioms/@Pure/Requires/Ensures byte-identical). PYTHONPATH=src python3 -m swebench_unified.adversary weakness nagini django__django-11790 <atk>. Resolve: PYTHONPATH=src python3 resolve_one.py <patch> (harness.run_resolve). Verifications were run 3-at-a-time as concurrent background jobs (schedule only; every attack fully verified).

### PER-ATTACK RESULTS (log_*.txt in the scratch dir):
1 atk_1_prepatch.py — PREPATCH BUG (field limit set, widget maxlength never established). exit 2 REJECTED on `attr_maxlength() in widget_attrs`. *** PREPATCH REPRODUCED *** (matches model_prepatch.py, whose only delta is that same line). 2 atk_2_misdirected_key.py — MISDIRECTED GOLD KEY, i.e. the PRIOR RECORDED BREAK re-encoded on the new carrier: publishes the resolved limit under 'size' instead. exit 2 REJECTED. *** THE PRIOR verify-not-correct BREAK IS CLOSED. *** 3 atk_3_partial_domain_stale.py — PARTIAL DOMAIN (§F W8): write guarded by "maxlength not already present", leaving a STALE rendered cap. exit 2 REJECTED (§F domain-totality repair load-bearing).

4 atk_4_zero_boundary.py — BOUNDARY: declared 0 used verbatim instead of resolving to 254. exit 2 REJECTED (leg A2 truthiness mirror load-bearing). 5 atk_5_branch_key.py — CONTROL-FLOW EFFECT ON THE NAME: 'maxlength' on one branch, 'size' on the other. exit 2 REJECTED. 6 atk_6_spurious_key.py — spurious extra attribute write clobbering the autocomplete hint (§E W10). exit 2 REJECTED (membership frame). 7 atk_7_oracle_echo.py — UNGROUNDED-ORACLE ECHO: hard-codes exactly the two F2P configs (None->254, else 255). exit 2 REJECTED on `Result() == resolve_limit(...)`. No test-echo shortcut admitted. 8 atk_8_clobber_other.py — VALUE-FRAME CLOBBER (W5), guarded so no key is ADDED. exit 2 REJECTED (value frame).

9 atk_9_widget_default.py — FIELD/WIDGET DISAGREEMENT: widget always gets the default. exit 2 REJECTED. 10 atk_10_diverge.py — divergence after the gold post-state. exit 2 REJECTED (MustTerminate at METHOD level). 11 atk_11_computed_name.py — COMPUTED NAME instead of the token (`attr_maxlength() + ''`) as the SOLE write. exit 2 REJECTED: Viper cannot prove the concatenated Ref equals the token, so the maxlength clauses fail. This is the direct probe of the name-domain repair. 12 atk_12_val_equal_double.py — VAL-EQUAL/REF-DISTINCT SHADOW WRITE before the gold write. exit 0 CANDIDATE -> patch materialized (patch_atk_12.diff, `git apply --check` clean at base_commit b1d6b35e in a fresh detached worktree) -> harness: completed=true, RESOLVED=TRUE, attempts=1, flaky=false.

NOT a break (see counterexample field). 13 atk_13_shadow_clobber.py — the ORDER-REVERSED variant: gold write FIRST, then the val-equal shadow write of the default (faithfully this CLOBBERS the resolved cap with 254 for every declared maximum — a genuine regression). exit 2 REJECTED. This is the important asymmetry: the dangerous ordering is refuted and only the harmless ordering verifies. 14 atk_14_shadow_split_literal.py — same hole via 'max' + 'length'. exit 2 REJECTED. 15 atk_15_drop_other.py — DROPS a pre-existing attribute (del). exit 2 REJECTED (membership frame, drop direction). 16 atk_16_off_by_one.py — resolved limit +1 in BOTH places (mutually consistent but wrong). exit 2 REJECTED: the spec pins the VALUE, not merely agreement.

17 atk_17_prestate_dep_value.py — PRE-STATE-DEPENDENT VALUE: default when a limit was already present (the CharField(max_length=75) subclass path). exit 2 REJECTED. 18 atk_18_other_name_overwrite.py — overwrite a pre-existing OTHER attribute via a computed name, no key added. exit 2 REJECTED. 19 atk_19_negative_boundary.py — DISTINCT declared-axis boundary: a NEGATIVE declared max is truthy so `x or 254` uses it verbatim; this impl defaults it. exit 2 REJECTED. 20 atk_20_param_rebind.py — PARAMETER REBINDING / LOST MUTATION: rebinds widget_attrs to a fresh dict and configures THAT, so the caller's widget is never written. exit 2 REJECTED (dict_pred post-permission on the parameter).

CONTROLS (nothing INCONCLUSIVE): POSITIVE CONTROL control_gold.py (= model.py verbatim) `bash scripts/nagini_verify.sh` exit 0, "Verification successful" in 10.5s -> the 19 refutations are discriminating and the spec is non-vacuous. GOLD resolve control: RESOLVED=TRUE, attempts=1. No exit 124, no timeout, no incomplete harness run.

A-LEG / REFINEMENT.MD AUDIT (the instructed focus): leg kinds are A0 R+I, A1 R, A2 R, A3 R, A4 R+I, A5 I, B1 A-reference — NO kind-3 step, and grep confirms 0 occurrences of @ContractOnly in model.py, so §C's "no consumed axiom" claim is accurate; every leg is R / A-reference / I as required. The single A-reference (B1) is genuinely EXECUTABLE and I ran it: axiom_check.py exit 0, driving the REAL gold-patched AuthenticationForm over 7 boundary + 200 fuzz user models (including the reachable declared-0 TextField case) asserting field.max_length AND widget.attrs['maxlength'] both == resolve_limit(declared), plus survival of autocapitalize/autocomplete/autofocus.

The two defects the prior pass recorded are REPAIRED and I confirmed each mechanically: (i) the name domain is now Dict[str, object] (textual, disjoint from the length domain), so the int-arithmetic route to the maxlength key is ILL-TYPED — atk_2/atk_5 (its faithful shapes) are refuted; (ii) axiom_check.py NOW grounds the KEY domain (lines 126-133: isinstance(key, str) and not isinstance(key, int) over every widget.attrs key), so G-AX can observe that real attribute names are strings. A2's truthiness mirror and A0's domain totality are both confirmed load-bearing (atk_4, atk_19, atk_3, atk_17 all rejected).

RESIDUAL DOCUMENTATION DEFECT (non-blocking, does NOT admit a non-resolving impl — reporting for the builder): refinement.md §E items 1 and 2 still QUOTE the frame clauses as `Forall(int, lambda a: ...)`, but model.py lines 176 and 179 actually carry `Forall(str, ...)`. The prose is stale from the pre-repair revision and now mis-describes the very carrier change that closed the recorded break; §E's surrounding narrative text does correctly discuss the textual name domain. No verifying wrong impl follows from this (it is a quotation error, not a spec weakness), but §E should be updated to quote `Forall(str, ...)` so the document matches the frozen bytes it audits.

HONEST LIMIT ON THE CLAIM: atk_12 shows the model is more permissive than Python on Ref-vs-value name identity (it cannot prove `attr_maxlength() + ''` is the same key as `attr_maxlength()`). Here that permissiveness is SAFE in the resolve-deciding direction — the only shapes it admits are ones where the gold write lands last and wins (atk_12 RESOLVED=TRUE), while every ordering in which the shadow write would survive is refuted (atk_11, atk_13, atk_14). I could not construct a verifying same-spec impl whose faithful patch fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on django__django-11790 (nagini). Reference = base_commit b1d6b35e14 worktree with patch.diff APPLIED (gold), per role instructions; base is reference only for untouched callees. No divergence found on any input.

SETUP: fresh worktree at b1d6b35e14, gold patch applied cleanly (3 insertions/1 deletion, matches gold_11790.diff). Real block confirmed at django/contrib/auth/forms.py:192-195:
  self.username_field = UserModel.`_meta`.get_field(UserModel.USERNAME_FIELD)
  username_max_length = self.username_field.max_length or 254
  self.fields['username'].max_length = username_max_length
  self.fields['username'].widget.attrs['maxlength'] = username_max_length

**SPEC REGION INTEGRITY:** `adversary same-spec` on a byte copy of bundle model.py => 'SAME — attack shares the bundle's exact specification'. Pinned verifier `scripts/nagini_verify.sh model.py` => 'Verification successful' (10.71s), so the spec is not vacuous-by-failure.

TEST 1 — live-form differential (g2_diff.py): built real AbstractBaseUser subclasses, instantiated the REAL gold AuthenticationForm, compared (field.max_length, full widget.attrs post-state) against a line-by-line transcription of model.py's impl region WITH ALL POSTCONDITIONS ASSERTED. Cases: IntegerField(None), CharField 1/150/254/255, TextField(max_length=0), TextField(None), a subclass whose username widget ALREADY carried maxlength='30' (stale-replacement leg), a subclass with EMPTY widget attrs (the 'invents nothing' leg), HiddenInput (CharField.widget_attrs skips maxlength when hidden), plus 300 fuzz lengths. FAILS: 0.

TEST 2 — rehosted real source over arbitrary pre-states (g2_rehost.py): extracted the 4 real lines via inspect.getsource and exec'd them against fake self/UserModel so the widget-attrs pre-state is unconstrained (the spec claims totality over pre-states, which a live form cannot reach). Cross-product of declared in {None,0,1,2,150,254,255,1000,-1,-5,4096,1e9,False,True} x 12 pre-states {} / {autofocus} / stock 3-key / {maxlength:'30'} / {maxlength:30} / {maxlength:254} / {maxlength:None} / {maxlength:'0'} / {maxlength:True} / {minlength,maxlength,autofocus} / {class,id}, plus 6000 randomized (declared, pre-state) pairs over heterogeneous value types. FAILS: 0. Exceptions compared too (both sides total).
  HARNESS-BUG SELF-CORRECTION: my first run reported 25+ 'DIVERGE' rows on declared=None/False/True. Every one was AttributeError('NoneType' has no attribute 'max_length') from the REAL side — my line filter had dropped the `self.username_field = ...` line, so the real block ran on username_field=None. That is my own extraction bug, not spec weakness; I fixed the filter (assert len(blk)==4) and reran to 0 fails. Reporting those as UNFAITHFUL would have condemned a sound spec.

TEST 3 — real pre/post frame capture (g2_frame.py): instrumented a Probe subclass that snapshots widget.attrs immediately BEFORE and AFTER the real block on a live form, then checked the model's exact frame clauses (every non-maxlength key keeps membership and value; maxlength present and == resolved; all keys str). 255 cases incl. stale and empty legs. FRAME FAILS: 0. Measured stale leg: {'autofocus':True,'maxlength':'30','autocapitalize':'none','autocomplete':'username'} -> maxlength becomes int 99, all other keys byte-identical — so the postcondition 'stale limit REPLACED, others untouched' is real, not over-strong. Empty leg: {} -> {'maxlength':77}, nothing invented.

TEST 4 — narrative claims (g2_render.py): rendered the real widget. maxlength=254/255 int value emits maxlength="255" in HTML, so writing an int (not str) under 'maxlength' really does produce the browser cap; and moving the same number to 'max_length' yields HTML with NO maxlength= at all. The spec's claim that the dedicated name is load-bearing and a wrong name leaves no cap is repo-true, so attr_maxlength()=='maxlength' as literal identity (not an encoding) is faithful, and the Dict[str,object] name/value carrier split is justified.

TEST 5 — resolve_limit vs `or 254`: model sends BOTH None and 0 to 254, mirroring Python truthiness; negative/large declared used verbatim (checked -1,-5,1e9). Verified declared=0 is genuinely reachable: fields.E121 lives on CharField.`_check_max_length_attribute`, so TextField(unique=True, max_length=0) as USERNAME_FIELD passes checks and the real form yields 254 — matching the model. mapping.md documents this correctly.

TEST 6 — frame soundness precondition: confirmed forms.Field.max_length is a plain instance attribute, not a data descriptor (no setter). Assigning field.max_length=999 leaves widget.attrs byte-identical, so the real assignment cannot secretly mutate the widget map; the model's single-key frame is not an under-approximation of a side effect.

BUNDLE CHECKS re-run in my own gold worktree: axiom_check.py exit 0 (207 user models); conformance_check.py exit 0 (100070 inputs, 0 disagreements).

**CONCLUSION:** no input on which the modeled function disagrees with the real gold-patched callee. The spec is not too strong — every postcondition (resolved return, maxlength under the dedicated name with the same value, stale replacement, quantified frame, the guarded attr_other witness that stays silent when the widget carried none) was exhibited on real repo behavior. It is also not drifting: the pure layer mirrors `or 254` exactly including the 0 leg, and the carrier domains are backed by measured runtime key/value types. Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / RELAXATION: none claimed, and I verified that myself rather than inheriting it -- `'relaxed_leakage' in meta` -> False (value None); `find django__django-11790 -iname '*relax*'` -> empty (no RELAXED_LEAKAGE.md in nagini/ or the instance dir); gates.G-LEAK.status == 'pass' (not 'relaxed'). So this is an ordinary STRICT leakage judgement with no relaxation argument to re-derive. No file in the bundle addresses me: `grep -rniE 'reviewer|auditor|judge|attacker|verdict|do not (flag|report)|treat this as|should record|panel'` over model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py -> zero hits; verdict.md carries only a Role-2 (G-PANEL-1) line at :336 and NO prior G-PANEL-3 verdict, so there was no prior-verdict anchor for my role to read off. (meta.json's G-PANEL-3 blob does contain a prior agent's note asserting NO-LEAKAGE; I did not read it as a disposition -- every measurement below is my own run.)

SPEC VIEW DERIVED, NOT READ OFF A STAMP: `markers.spec_view(model.py, get_backend('nagini').language)` -> sha256 c4d740fe25fc2ff12ca337517582a2ba2cc31c28f5e6985d29a69d03f893d223, 193 lines, written into a fresh `mktemp -d` (sv.txt) and asserted to be this instance ('11790' present). Exactly one elision marker ('implementation elided') -- the impl region is the only thing hidden, as required.

**SPEC/IMPL SPLIT:** `markers.same_spec(model.py, model_prepatch.py)` -> True; `adversary same-spec nagini django__django-11790 <copy of model.py>` -> exit 0 ("SAME"). My re-derived region hashes match meta.gates['G-HYGIENE'].data.region_hashes exactly on all six keys, and differ from model_prepatch only in 'impl'. So the discriminator lives in the impl region where it belongs -- confirmed formally: pinned verifier on model.py => "Verification successful" (10.6s); on model_prepatch.py => "Verification failed ... Postcondition ... Assertion (attr_maxlength() in widget_attrs) might not hold". The clause that senses the edit is a real, non-vacuous formal clause, not narration.

CLAUSE-BY-CLAUSE SCREEN (re-run, not trusted): `leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch)` -> passed=True, hard_failures=[], warnings=[]. Decomposed against my own derived view: (L1 diff markers) none of '@@', 'diff --git', '+++ ', '--- ', '\nindex' present. (L1 gold lines) all 4 added/removed gold lines normalized and searched -> none in view_norm; in particular "self.fields['username'].widget.attrs['maxlength'] = username_max_length" and the `username_max_length = ... or 254` hoist are absent, and the local name `username_max_length`, 'fields[', 'USERNAME_FIELD', '`_meta`', 'get_field' do not appear.

(L2 paths) 'django/contrib/auth/forms.py' and dotted 'django.contrib.auth.forms' both absent; 'contrib' absent; base_commit and the cited regression commit 5ceaf14... absent. (L2/L5 symbols) `_patch_changed_symbols(gold)` -> set() (the only def the hunk touches is `__init__`, non-distinctive) so there is no symbol-collision surface at all. (L3 narration) `_NARRATION_RE.findall(view)` -> [] -- no bug/fix/patch/patched/pre-patch/regression/previously/broken/incorrectly/wrong anywhere in the view, including the module docstring, which frames itself as 'stated as desired behaviour, not as an edit'. Test-side leakage also checked by hand: 'test_', 'auth_tests', 'CustomEmailField', 'IntegerUsernameUser', 'CharField', 'IntegerField', 'UsernameField', '255', '150' all absent (F2P names nowhere in the view).

BEYOND-PROBLEM_STATEMENT CHECK (judged against problem_statement ONLY; hints_text is the 16-char 'Regression test.' and I did not screen against it): the public statement is "AuthenticationForm's username field doesn't render with maxlength HTML attribute anymore" -- so the entire discriminator (publish the resolved length limit under the widget attribute named 'maxlength' on the username field) is ALREADY public verbatim. The view's `attr_maxlength() == 'maxlength'`, 'username', 'widget'/'attrs' vocabulary therefore adds no localization the solver lacks. The only view tokens NOT in the problem statement are modeling constants that are not the edit: 254 (present in the PRE-patch line `... or 254` at base, so it localizes nothing about the change), 'autofocus'/'autocomplete' (pre-existing base-commit widget attributes used as an untouched-frame witness), and numbers 0/1/2/11790 (the zero-branch of `or`, MustTerminate(2), the instance id). Nothing names the hoisted local, the file, the class, or the shape 'a second write was added'.

INCIDENTAL (not a leakage finding, flagged for the record): meta.json's TOP-LEVEL region_hashes are stale -- pure/pre-conditions/post-conditions/spec_view there disagree with both the current model.py (my re-derivation) and meta.gates['G-HYGIENE'].data.region_hashes, which do agree with each other; likewise modeled_functions[0].carrier_type still says 'widget.attrs dict -> Dict[int,int]' while the shipped carrier is Dict[str, object] (the fix refinement.md §E documents). Both are ledger/hygiene staleness, visible only in meta.json (not in the solver-visible spec view), so they do not affect this verdict.

**VERDICT:** NO-LEAKAGE. The spec view reproduces no gold line, no diff marker, no patched path/module, no patched symbol, no narration, and no test identifier; every term it does share with the gold edit is already public in the problem_statement, and the discriminating obligation is carried as a formal postcondition (proved on the gold impl, refuted on the pre-patch twin) rather than as prose about the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
