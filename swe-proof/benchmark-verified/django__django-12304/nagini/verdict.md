# P2 adversarial audit — django__django-12304

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec impl has a faithful patch that fails to resolve. 16 same-spec attacks run; 3 came back CANDIDATE (atk_8, atk_9, atk_10) and ALL THREE had their faithful refined patch materialized from a pristine base_commit worktree and EXECUTED through run_resolve: every one RESOLVED (resolved=true, completed=true, attempts=1, flaky=false, F2P 1/1, P2P 17/17). They are true behavioural equivalents, not weaknesses — see notes for the measured argument per candidate. A 4th verifying impl, the structurally-different positive control pos_alt.py (flag recorded on the object the distinctness step returned), also verifies AND resolves, confirming the spec is not over-tight in the same breath.

DECISIVE FINDING: the PRIOR PASS'S RECORDED BREAK IS CLOSED. verdict.md records G-EQ=fail on the old model.py (sha256 9af73eb5…); the shipped model.py is now 560ade59… and carries exactly the repair verdict.md suggested — the unforgeable `distinctness_confirmed` confirmation token plus per-step `base_step_report` / `distinctness_step_report` tokens keyed to THE RAISED REPORT OBJECT. I re-encoded that old counterexample verbatim on the current frozen symbols as atk_2.py (A4 skipped entirely; the repeated-value refusal self-decided off the @Pure predicate) and it is now REJECTED with the precise clause failure:
  atk_2.py:512:13:514:70: error: Postcondition of build_template_usable_grouping might not hold. There might be insufficient permission to access distinctness_step_report(RaisedException(), identity).
Per the retained-attack-labels rule I did not inherit the old BROKEN verdict; I re-ran it and measured the current spec's answer.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -515,9 +515,6 @@
     # post-conditions-end
     # impl-start
     grouping = base_class_creation(identity)  # type: EnumGrouping
-    if flag_name_taken_by_choice(identity):
-        raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -517,7 +517,8 @@
     grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
+    if repeats_choice_value(identity):
+        raise RepeatedChoiceValue()
     grouping.preserve_when_callable = True
-    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
-    return delivered
+    return grouping
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -518,6 +518,8 @@
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
+    if repeats_choice_value(identity):
+        raise RepeatedChoiceValue()
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -518,6 +518,8 @@
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
-    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
-    return delivered
+    try:
+        return finalize_grouping(grouping, identity)
+    except RepeatedChoiceValue:
+        raise RepeatedChoiceValue()
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -514,6 +514,8 @@
             and distinctness_step_report(RaisedException(), identity))
     # post-conditions-end
     # impl-start
+    if base_step_refuses(identity):
+        raise BaseStepRefused()
     grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -515,9 +515,9 @@
     # post-conditions-end
     # impl-start
     grouping = base_class_creation(identity)  # type: EnumGrouping
+    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
-    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
+    delivered.preserve_when_callable = True
     return delivered
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -515,7 +515,7 @@
     # post-conditions-end
     # impl-start
     grouping = base_class_creation(identity)  # type: EnumGrouping
-    if flag_name_taken_by_choice(identity):
+    if flag_name_taken_by_choice(identity) or repeats_choice_value(identity):
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -517,7 +517,8 @@
     grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
+    if not grouping.preserve_when_callable:
+        grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -519,5 +519,6 @@
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
+    delivered.preserve_when_callable = not repeats_choice_value(identity)
     return delivered
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -517,7 +517,8 @@
     grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
-    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
-    return delivered
+    first = finalize_grouping(grouping, identity)  # type: EnumGrouping
+    first.preserve_when_callable = True
+    second = finalize_grouping(first, identity)  # type: EnumGrouping
+    return second
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -517,7 +517,7 @@
     grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
+    grouping.preserve_when_callable = resolved_in_template(grouping) == identity
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -519,5 +519,6 @@
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
-    return delivered
+    substitute = EnumGrouping(identity, True)  # type: EnumGrouping
+    return substitute
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -518,6 +518,9 @@
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
+    if repeats_choice_value(identity):
+        while True:
+            Invariant(True)
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -514,7 +514,10 @@
             and distinctness_step_report(RaisedException(), identity))
     # post-conditions-end
     # impl-start
-    grouping = base_class_creation(identity)  # type: EnumGrouping
+    try:
+        grouping = base_class_creation(identity)  # type: EnumGrouping
+    except BaseStepRefused:
+        raise BaseStepRefused()
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
     grouping.preserve_when_callable = True
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -514,9 +514,9 @@
             and distinctness_step_report(RaisedException(), identity))
     # post-conditions-end
     # impl-start
-    grouping = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
+    grouping = base_class_creation(identity)  # type: EnumGrouping
     grouping.preserve_when_callable = True
     delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
     return delivered
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -514,10 +514,11 @@
             and distinctness_step_report(RaisedException(), identity))
     # post-conditions-end
     # impl-start
-    grouping = base_class_creation(identity)  # type: EnumGrouping
+    first = base_class_creation(identity)  # type: EnumGrouping
+    second = base_class_creation(identity)  # type: EnumGrouping
     if flag_name_taken_by_choice(identity):
         raise PreserveFlagNameTaken()
-    grouping.preserve_when_callable = True
-    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
+    second.preserve_when_callable = True
+    delivered = finalize_grouping(second, identity)  # type: EnumGrouping
     return delivered
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all artifacts, logs,.diff files retained there).

### Integrity of the attack set
All 16 attacks + both positive controls: `adversary same-spec nagini django__django-12304 <f>` = EXIT 0 (spec byte-identical). Independently asserted in Python that every file is byte-identical to model.py OUTSIDE the impl region (prefix AND suffix True for all 18), so axioms / @Pure / Requires / Ensures / Exsures are untouched. atk_1.py is BYTE-IDENTICAL to the bundle's model_prepatch.py; pos_gold.py is BYTE-IDENTICAL to the bundle's model.py.
COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini django__django-12304 atk_N.py`. Run 3-at-a-time as background jobs (each spawns JVM+Z3); schedule only — every attack ran to a verdict, none timed out, no host-saturation INCONCLUSIVE.

### Prepatch (G-DIFF)
atk_1.py (== model_prepatch.py) -> weakness EXIT 2, does not verify => prepatch_reproduced=true. The spec senses the change.

### Per-attack results (16)
atk_1  EXIT 2  prepatch: flag + guard omitted (== model_prepatch.py). atk_2  EXIT 2  PRIOR PASS'S COUNTEREXAMPLE re-encoded on the current frozen symbols: A4 skipped entirely, repeated-value refusal self-decided off the @Pure predicate. NOW REJECTED — direct verifier: "insufficient permission to access distinctness_step_report(RaisedException(), identity)". The token repair bites. atk_3  EXIT 2  partial anticipation: A4 IS called on the delivery path (so distinctness_confirmed is obtainable) but the REFUSAL is anticipated off the @Pure predicate before A4 runs. Rejected — the report token is not obtainable without the step actually refusing. atk_4  EXIT 2  REPORT SUBSTITUTION on the A4 leg: A4 runs and refuses, its report is caught, a freshly composed RepeatedChoiceValue is handed on.

Rejected — the token is keyed to THE RAISED OBJECT, not to "a refusal of the right kind at the right point". atk_5  EXIT 2  A1-leg anticipation: base_step_refuses read off the declaration and BaseStepRefused reported without letting the base step run. atk_6  EXIT 2  ORDER: A4 run BEFORE the flag-name guard and the flag write (weak-finalize-before-flag). atk_7  EXIT 2  OVER-REFUSAL / partial domain: PreserveFlagNameTaken whenever EITHER declaration predicate holds, so repeated-value declarations get refusal 2 instead of refusal 3. atk_8  EXIT 0  CANDIDATE (havoc boundary) -> RESOLVED.

See candidates below. atk_9  EXIT 0  CANDIDATE (ungrounded-oracle echo) -> RESOLVED. atk_10 EXIT 0  CANDIDATE (multiplicity on the A4 leg) -> RESOLVED. atk_11 EXIT 2  FLAG LAUNDERING THROUGH THE BEHAVIOURAL AXIOM (§B/B1): flag written as `resolved_in_template(grouping) == identity` instead of the literal. Rejected — the havoced initial flag makes the echo unprovable, so B1 cannot be used to launder a flag that was never recorded. atk_12 EXIT 2  PROVENANCE substitution: gold construction runs, then a freshly built EnumGrouping(identity, True) is delivered in its place. Rejected — built_from_declaration / distinctness_confirmed are keyed to the OBJECT (D3 holds). atk_13 EXIT 2  PARTIAL DOMAIN via divergence: repeated-value declarations sent into an endless loop instead of being refused.

Rejected — direct verifier: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." This is the MustTerminate(2)/D1 leg biting at the METHOD level (consistent with the known 'MustTerminate needs the method level' rule). atk_14 EXIT 2  ***HIGHEST-VALUE ATTACK***: BASE-STEP REPORT SUBSTITUTION. The base step runs and refuses, its report is caught, a freshly composed BaseStepRefused is handed on. This is the mirror of atk_4 on the A1 leg and it matters most because THREE P2P tests assert that step's message VERBATIM (test_bool_unsupported "type 'bool' is not an acceptable base type", test_timezone_unsupported, test_uuid_unsupported).

If the spec permitted the substitution, a faithful patch could word its own message and those three P2P tests would fail — exactly the old atk_5 defect shape, on the other step. REJECTED with the precise clause: atk_14.py:491:13:492:62: "Postcondition of build_template_usable_grouping might not hold.

There might be insufficient permission to access base_step_report(RaisedException(), identity)." So the message-content hazard is closed on BOTH refusing steps, not just the one the prior pass broke. atk_15 EXIT 2  A1-SIDE ORDER: flag-name guard consulted BEFORE the base step runs, so a declaration with both an unusable kind and a taken flag name reports PreserveFlagNameTaken where the repo raises the base step's TypeError (the class must exist before EnumMeta.`__setattr__` can trip). atk_16 EXIT 2  MULTIPLICITY on the A1 leg: base construction step run TWICE for one declaration, second grouping delivered. Rejected — declaration_available is single-use (D2 holds).

Direct-verifier confirmation that rejections are GENUINE CLAUSE FAILURES rather than translator errors: `bash scripts/nagini_verify.sh <f>` on atk_2 / atk_13 / atk_14 each returned EXIT 1 "Verification failed" with the specific named postcondition/obligation above — not a parse or translation error. No rejection in this set is an artifact of a crashed translator.

### EVERY CANDIDATE'S PATCH WAS MATERIALIZED AND EXECUTED (mandatory step)
Patches were generated from a PRISTINE base_commit worktree (git worktree at 4c1b401e8250f9f520b3c7dc369554477ce8b15a; created, diffed, tree restored clean, worktree removed afterwards). Command per patch: `python resolve.py N` calling `swebench_unified.harness.run_resolve("django__django-12304", <diff>)`.
  * p_atk_8.diff  (sha1 07312e6acef1) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1 pass, P2P 17/17 pass, PASS_TO_FAIL empty.
  * p_atk_9.diff  (sha1 8679970a6daa) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1, P2P 17/17.
  * p_atk_10.diff (sha1 a0a3ee3014b4) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1, P2P 17/17.
  * p_pos_alt.diff (sha1 b5dfb67035e0, the structurally-different positive control) -> resolved=TRUE, F2P 1/1, P2P 17/17.
WHY EACH CANDIDATE IS A GENUINE EQUIVALENT, measured not assumed:
  atk_8 (flag write conditional on the havoced incoming flag): measured against real CPython enum that EnumMeta.`__setattr__` keys on the DECLARED-MEMBER table, not on inheritance — a subclass built under an already-flagged base has getattr(...)==True while its own `__dict__` lacks the name, and re-flagging it is accepted. So the skipped write is skipped exactly when the value is already True; the delivered flag is True either way.
  atk_9 (flag overwritten with a value echoed out of the repeats-a-choice-value oracle, after A4): at that program point A4 has already delivered, so `not repeats_choice_value` is provably True and the echo is the literal True. The real refinement's alias test over delivered.`__members__` is likewise vacuous post-enum.unique.
  atk_10 (distinctness step run twice, second result delivered): enum.unique(E) is E (measured True), so the second run returns the same object and the flag written between the runs survives; enum.unique is idempotent and side-effect-free on an already-unique enum.

### REFINEMENT.MD AUDIT (every leg R / A-consumed / A-reference / I; no kind-3)
§A tags: A1 A-consumed, A2 A-consumed + I, A3 I, A4 A-consumed, A5 I. §B: B1 A-consumed. §C states there is NO A-reference deep model, and that is CORRECT and load-bearing here: the one genuinely CHANGED operation (`cls.do_not_call_in_templates = True`) is modeled IDENTICALLY as A3 (tag I, a boolean field assignment), not hidden behind an axiom. I confirm no kind-3 (unexpressible-changed-op) step is present, and that the changed op is not axiomatized — the axioms cover only UNCHANGED callees.
### A-LEG CORRESPONDENCE MEASURED AGAINST THE REAL CALLEES (all four hold):
  * A4 / finalize_grouping `Ensures(Result() is grouping)`: enum.unique(E) is E == True.
  * repeats_choice_value refusal content: enum.unique on a duplicate -> ValueError "duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE" — matches the P2P test_invalid_definition assertion VERBATIM.
  * base_step_refuses family 1: `class B(bool, Enum)` -> TypeError "type 'bool' is not an acceptable base type" — matches P2P test_bool_unsupported verbatim.
  * A2 / flag_name_taken_by_choice: EnumMeta.`__setattr__` refuses a rebind of a DECLARED MEMBER name with AttributeError('Cannot reassign members.') and ACCEPTS a non-member name; the deciding table is exactly `'do_not_call_in_templates' in cls.__dict__['_member_map_']` (probed hit=True on a member-named enum, miss=False otherwise).
The A1/A4 BOUNDARY (base construction EXCLUDES value-distinctness) is correct against enums.py:28-33 vs the trailing `return enum.unique(cls)`, and atk_6/atk_15's rejections confirm the order legs bite in both directions. The havoced initial flag is the only sound contract (both states realizable — G-CONF's own report records initial_flag_absent=64662 / initial_flag_inherited_truthy=35338), and atk_8's resolve=TRUE confirms that leaving it havoced is not over-tight rather than a hole.
D1-D4 all confirmed to BITE by execution: D1 by atk_13, D2 by atk_16, D3 by atk_12, D4 (ordered case split + report provenance) by atk_2/3/4/5/6/7/14/15.

### RESIDUAL OBSERVATIONS (reported, not scored; neither is a materialized break)
1. CONTENT VS OCCURRENCE, now closed on both steps. The model deliberately carries no message strings; what protects the three P2P message assertions is that BOTH refusing steps' reports must be THE OBJECT THAT STEP RAISED (base_step_report / distinctness_step_report keyed to RaisedException()). atk_4 and atk_14 attack exactly that on each step and both are rejected, so a verifying impl cannot re-word either refusal. This is precisely the hole the prior pass broke and it is now shut on both legs; I could not turn it into a counterexample.
2. D2 grounding caveat, inherited from the prior pass and still worth pinning in mapping.md: §2b grounds declaration_available's single-use on "a second super().`__new__` on the same classdict raises KeyError on the first member name". The instance container runs Python 3.6 and I did not measure inside the container. This is a version-scoped provenance note on the D2 row, not a refuted axiom, and it does not affect the verdict — atk_16 shows the multiplicity leg is enforced by the spec regardless.

### Verdict
SOUND. 16 same-spec attacks executed to a verdict (well over the 5-6 required), spanning partial-domain, boundary, control-flow-effect/order, ungrounded-oracle echo, report anticipation, report substitution on BOTH refusing steps, provenance substitution, multiplicity on both steps, divergence, and the prior pass's re-encoded counterexample. 13 rejected with named clause failures; 3 CANDIDATES all had their faithful patch materialized and EXECUTED through the official harness and ALL THREE RESOLVED, so none is a break. Positive control pos_gold.py verifies (EXIT 0); the structurally-different pos_alt.py verifies AND resolves, so the spec is neither too weak on the attacked surfaces nor too strong. No verify⇏correct witness exists for this bundle at this spec revision. NOTE FOR THE RUNNER: verdict.md/meta.json still record G-EQ=fail against the SUPERSEDED model.py (9af73eb5…); the shipped model.py (560ade59…) contains the repair and the recorded counterexample no longer verifies — the stale fail should be re-derived against the current bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec impl has a faithful patch that fails to resolve. 16 same-spec attacks run; 3 came back CANDIDATE (atk_8, atk_9, atk_10) and ALL THREE had their faithful refined patch materialized from a pristine base_commit worktree and EXECUTED through run_resolve: every one RESOLVED (resolved=true, completed=true, attempts=1, flaky=false, F2P 1/1, P2P 17/17). They are true behavioural equivalents, not weaknesses — see notes for the measured argument per candidate. A 4th verifying impl, the structurally-different positive control pos_alt.py (flag recorded on the object the distinctness step returned), also verifies AND resolves, confirming the spec is not over-tight in the same breath.

DECISIVE FINDING: the PRIOR PASS'S RECORDED BREAK IS CLOSED. verdict.md records G-EQ=fail on the old model.py (sha256 9af73eb5…); the shipped model.py is now 560ade59… and carries exactly the repair verdict.md suggested — the unforgeable `distinctness_confirmed` confirmation token plus per-step `base_step_report` / `distinctness_step_report` tokens keyed to THE RAISED REPORT OBJECT. I re-encoded that old counterexample verbatim on the current frozen symbols as atk_2.py (A4 skipped entirely; the repeated-value refusal self-decided off the @Pure predicate) and it is now REJECTED with the precise clause failure:
  atk_2.py:512:13:514:70: error: Postcondition of build_template_usable_grouping might not hold. There might be insufficient permission to access distinctness_step_report(RaisedException(), identity).
Per the retained-attack-labels rule I did not inherit the old BROKEN verdict; I re-ran it and measured the current spec's answer.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all artifacts, logs,.diff files retained there).

### Integrity of the attack set
All 16 attacks + both positive controls: `adversary same-spec nagini django__django-12304 <f>` = EXIT 0 (spec byte-identical). Independently asserted in Python that every file is byte-identical to model.py OUTSIDE the impl region (prefix AND suffix True for all 18), so axioms / @Pure / Requires / Ensures / Exsures are untouched. atk_1.py is BYTE-IDENTICAL to the bundle's model_prepatch.py; pos_gold.py is BYTE-IDENTICAL to the bundle's model.py.
COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini django__django-12304 atk_N.py`. Run 3-at-a-time as background jobs (each spawns JVM+Z3); schedule only — every attack ran to a verdict, none timed out, no host-saturation INCONCLUSIVE.

### Prepatch (G-DIFF)
atk_1.py (== model_prepatch.py) -> weakness EXIT 2, does not verify => prepatch_reproduced=true. The spec senses the change.

### Per-attack results (16)
atk_1  EXIT 2  prepatch: flag + guard omitted (== model_prepatch.py). atk_2  EXIT 2  PRIOR PASS'S COUNTEREXAMPLE re-encoded on the current frozen symbols: A4 skipped entirely, repeated-value refusal self-decided off the @Pure predicate. NOW REJECTED — direct verifier: "insufficient permission to access distinctness_step_report(RaisedException(), identity)". The token repair bites. atk_3  EXIT 2  partial anticipation: A4 IS called on the delivery path (so distinctness_confirmed is obtainable) but the REFUSAL is anticipated off the @Pure predicate before A4 runs. Rejected — the report token is not obtainable without the step actually refusing. atk_4  EXIT 2  REPORT SUBSTITUTION on the A4 leg: A4 runs and refuses, its report is caught, a freshly composed RepeatedChoiceValue is handed on.

Rejected — the token is keyed to THE RAISED OBJECT, not to "a refusal of the right kind at the right point". atk_5  EXIT 2  A1-leg anticipation: base_step_refuses read off the declaration and BaseStepRefused reported without letting the base step run. atk_6  EXIT 2  ORDER: A4 run BEFORE the flag-name guard and the flag write (weak-finalize-before-flag). atk_7  EXIT 2  OVER-REFUSAL / partial domain: PreserveFlagNameTaken whenever EITHER declaration predicate holds, so repeated-value declarations get refusal 2 instead of refusal 3. atk_8  EXIT 0  CANDIDATE (havoc boundary) -> RESOLVED.

See candidates below. atk_9  EXIT 0  CANDIDATE (ungrounded-oracle echo) -> RESOLVED. atk_10 EXIT 0  CANDIDATE (multiplicity on the A4 leg) -> RESOLVED. atk_11 EXIT 2  FLAG LAUNDERING THROUGH THE BEHAVIOURAL AXIOM (§B/B1): flag written as `resolved_in_template(grouping) == identity` instead of the literal. Rejected — the havoced initial flag makes the echo unprovable, so B1 cannot be used to launder a flag that was never recorded. atk_12 EXIT 2  PROVENANCE substitution: gold construction runs, then a freshly built EnumGrouping(identity, True) is delivered in its place. Rejected — built_from_declaration / distinctness_confirmed are keyed to the OBJECT (D3 holds). atk_13 EXIT 2  PARTIAL DOMAIN via divergence: repeated-value declarations sent into an endless loop instead of being refused.

Rejected — direct verifier: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." This is the MustTerminate(2)/D1 leg biting at the METHOD level (consistent with the known 'MustTerminate needs the method level' rule). atk_14 EXIT 2  ***HIGHEST-VALUE ATTACK***: BASE-STEP REPORT SUBSTITUTION. The base step runs and refuses, its report is caught, a freshly composed BaseStepRefused is handed on. This is the mirror of atk_4 on the A1 leg and it matters most because THREE P2P tests assert that step's message VERBATIM (test_bool_unsupported "type 'bool' is not an acceptable base type", test_timezone_unsupported, test_uuid_unsupported).

If the spec permitted the substitution, a faithful patch could word its own message and those three P2P tests would fail — exactly the old atk_5 defect shape, on the other step. REJECTED with the precise clause: atk_14.py:491:13:492:62: "Postcondition of build_template_usable_grouping might not hold.

There might be insufficient permission to access base_step_report(RaisedException(), identity)." So the message-content hazard is closed on BOTH refusing steps, not just the one the prior pass broke. atk_15 EXIT 2  A1-SIDE ORDER: flag-name guard consulted BEFORE the base step runs, so a declaration with both an unusable kind and a taken flag name reports PreserveFlagNameTaken where the repo raises the base step's TypeError (the class must exist before EnumMeta.`__setattr__` can trip). atk_16 EXIT 2  MULTIPLICITY on the A1 leg: base construction step run TWICE for one declaration, second grouping delivered. Rejected — declaration_available is single-use (D2 holds).

Direct-verifier confirmation that rejections are GENUINE CLAUSE FAILURES rather than translator errors: `bash scripts/nagini_verify.sh <f>` on atk_2 / atk_13 / atk_14 each returned EXIT 1 "Verification failed" with the specific named postcondition/obligation above — not a parse or translation error. No rejection in this set is an artifact of a crashed translator.

### EVERY CANDIDATE'S PATCH WAS MATERIALIZED AND EXECUTED (mandatory step)
Patches were generated from a PRISTINE base_commit worktree (git worktree at 4c1b401e8250f9f520b3c7dc369554477ce8b15a; created, diffed, tree restored clean, worktree removed afterwards). Command per patch: `python resolve.py N` calling `swebench_unified.harness.run_resolve("django__django-12304", <diff>)`.
  * p_atk_8.diff  (sha1 07312e6acef1) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1 pass, P2P 17/17 pass, PASS_TO_FAIL empty.
  * p_atk_9.diff  (sha1 8679970a6daa) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1, P2P 17/17.
  * p_atk_10.diff (sha1 a0a3ee3014b4) -> resolved=TRUE, completed=TRUE, attempts=1, flaky=FALSE, F2P 1/1, P2P 17/17.
  * p_pos_alt.diff (sha1 b5dfb67035e0, the structurally-different positive control) -> resolved=TRUE, F2P 1/1, P2P 17/17.
WHY EACH CANDIDATE IS A GENUINE EQUIVALENT, measured not assumed:
  atk_8 (flag write conditional on the havoced incoming flag): measured against real CPython enum that EnumMeta.`__setattr__` keys on the DECLARED-MEMBER table, not on inheritance — a subclass built under an already-flagged base has getattr(...)==True while its own `__dict__` lacks the name, and re-flagging it is accepted. So the skipped write is skipped exactly when the value is already True; the delivered flag is True either way.
  atk_9 (flag overwritten with a value echoed out of the repeats-a-choice-value oracle, after A4): at that program point A4 has already delivered, so `not repeats_choice_value` is provably True and the echo is the literal True. The real refinement's alias test over delivered.`__members__` is likewise vacuous post-enum.unique.
  atk_10 (distinctness step run twice, second result delivered): enum.unique(E) is E (measured True), so the second run returns the same object and the flag written between the runs survives; enum.unique is idempotent and side-effect-free on an already-unique enum.

### REFINEMENT.MD AUDIT (every leg R / A-consumed / A-reference / I; no kind-3)
§A tags: A1 A-consumed, A2 A-consumed + I, A3 I, A4 A-consumed, A5 I. §B: B1 A-consumed. §C states there is NO A-reference deep model, and that is CORRECT and load-bearing here: the one genuinely CHANGED operation (`cls.do_not_call_in_templates = True`) is modeled IDENTICALLY as A3 (tag I, a boolean field assignment), not hidden behind an axiom. I confirm no kind-3 (unexpressible-changed-op) step is present, and that the changed op is not axiomatized — the axioms cover only UNCHANGED callees.
### A-LEG CORRESPONDENCE MEASURED AGAINST THE REAL CALLEES (all four hold):
  * A4 / finalize_grouping `Ensures(Result() is grouping)`: enum.unique(E) is E == True.
  * repeats_choice_value refusal content: enum.unique on a duplicate -> ValueError "duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE" — matches the P2P test_invalid_definition assertion VERBATIM.
  * base_step_refuses family 1: `class B(bool, Enum)` -> TypeError "type 'bool' is not an acceptable base type" — matches P2P test_bool_unsupported verbatim.
  * A2 / flag_name_taken_by_choice: EnumMeta.`__setattr__` refuses a rebind of a DECLARED MEMBER name with AttributeError('Cannot reassign members.') and ACCEPTS a non-member name; the deciding table is exactly `'do_not_call_in_templates' in cls.__dict__['_member_map_']` (probed hit=True on a member-named enum, miss=False otherwise).
The A1/A4 BOUNDARY (base construction EXCLUDES value-distinctness) is correct against enums.py:28-33 vs the trailing `return enum.unique(cls)`, and atk_6/atk_15's rejections confirm the order legs bite in both directions. The havoced initial flag is the only sound contract (both states realizable — G-CONF's own report records initial_flag_absent=64662 / initial_flag_inherited_truthy=35338), and atk_8's resolve=TRUE confirms that leaving it havoced is not over-tight rather than a hole.
D1-D4 all confirmed to BITE by execution: D1 by atk_13, D2 by atk_16, D3 by atk_12, D4 (ordered case split + report provenance) by atk_2/3/4/5/6/7/14/15.

### RESIDUAL OBSERVATIONS (reported, not scored; neither is a materialized break)
1. CONTENT VS OCCURRENCE, now closed on both steps. The model deliberately carries no message strings; what protects the three P2P message assertions is that BOTH refusing steps' reports must be THE OBJECT THAT STEP RAISED (base_step_report / distinctness_step_report keyed to RaisedException()). atk_4 and atk_14 attack exactly that on each step and both are rejected, so a verifying impl cannot re-word either refusal. This is precisely the hole the prior pass broke and it is now shut on both legs; I could not turn it into a counterexample.
2. D2 grounding caveat, inherited from the prior pass and still worth pinning in mapping.md: §2b grounds declaration_available's single-use on "a second super().`__new__` on the same classdict raises KeyError on the first member name". The instance container runs Python 3.6 and I did not measure inside the container. This is a version-scoped provenance note on the D2 row, not a refuted axiom, and it does not affect the verdict — atk_16 shows the multiplicity leg is enforced by the spec regardless.

### Verdict
SOUND. 16 same-spec attacks executed to a verdict (well over the 5-6 required), spanning partial-domain, boundary, control-flow-effect/order, ungrounded-oracle echo, report anticipation, report substitution on BOTH refusing steps, provenance substitution, multiplicity on both steps, divergence, and the prior pass's re-encoded counterexample. 13 rejected with named clause failures; 3 CANDIDATES all had their faithful patch materialized and EXECUTED through the official harness and ALL THREE RESOLVED, so none is a break. Positive control pos_gold.py verifies (EXIT 0); the structurally-different pos_alt.py verifies AND resolves, so the spec is neither too weak on the attacked surfaces nor too strong. No verify⇏correct witness exists for this bundle at this spec revision. NOTE FOR THE RUNNER: verdict.md/meta.json still record G-EQ=fail against the SUPERSEDED model.py (9af73eb5…); the shipped model.py (560ade59…) contains the repair and the recorded counterexample no longer verifies — the stale fail should be re-derived against the current bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled function build_template_usable_grouping disagrees with the REAL patched ChoicesMeta.`__new__` (spec too strong / drifted). I could NOT produce one. Reference discipline: oracle = patched worktree (base_commit 4c1b401e82 + patch.diff, gold patch is the single added line 'cls.do_not_call_in_templates = True' at enums.py:34); base worktree used ONLY for the unchanged callees the axioms model.

### MEASUREMENTS (real repo, py3.10.20):

1. ORDERED FOUR-WAY CASE SPLIT - exhaustive. All 2^3 combinations of {declared kind unusable, a choice named do_not_call_in_templates, two choices sharing a value}, each real outcome classified by the enums.py line the exception escaped from (located at runtime). All 8 AGREE: badkind -> line 28 BaseStepRefused (wins over both later legs); flagname -> line 34 PreserveFlagNameTaken (wins over dup); dup -> line 35 RepeatedChoiceValue; else DELIVER with flag True. The contested ORDER conjunct is REAL: flagname+dup raises AttributeError('Cannot reassign members.') at line 34, NOT ValueError at 35. Instrumented enum.unique and observed the flag is ALREADY True when unique() is reached on a dup-value declaration, so the flag is recorded strictly before the distinctness step. Hence 'not flag_name_taken_by_choice' inside Exsures(RepeatedChoiceValue,...) is faithful, not over-strong.

2. 4000-declaration seeded fuzz (seed 20260815) over 6 ancestries x random member names (including the flag's own name and 'label') x 14 value shapes. Refusal-line histogram {28:1737, 33:314, 34:289, 35:144}. ZERO delivered groupings with flag != True, ZERO delivered groupings not template-usable, ZERO order mismatches (no line-35 refusal ever occurred on a declaration that declared the flag name as a member). No fifth outcome appeared.

3. resolved_in_template axiom vs the REAL engine. Confirmed the specialisation premises hold for a grouping: callable(Suit) True, alters_data absent, Suit() raises TypeError('missing 1 required positional argument: value') AND signature.bind() also raises TypeError, so the real rule drives to string_if_invalid rather than re-raising. Real render flagged: '{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}|{{ Suit }}' -> 'Diamond|1|<enum Suit>'; with the flag forced False -> '|'. Matches Ensures(Implies(flag, Result()==identity)) / Ensures(Implies(not flag, Result()==INVALID_VALUE)) exactly.

4. The havoced initial flag is the ONLY sound contract (so A1 is not too weak in a way that would make the spec too strong elsewhere). Shimmed enum.EnumMeta.`__new__` and observed the flag right after the base step: ABSENT for a class with no flagged ancestor, True (inherited) for a class built under an already-flagged base. Both states realized, so pinning it would be unsound; the unconditional assignment in the impl is what the real patch does.

5. Multiplicity/provenance obligations are real repo facts, not invented strength. Second ChoicesMeta call on the same already-consumed classdict raises KeyError 'DIAMOND' (single-use declaration => declaration_available). enum.unique(cls) is cls confirmed by shim (delivered object IS the object the base step produced => built_from_declaration, Ensures(Result() is grouping)).

6. RELAY clauses (base_step_report / distinctness_step_report) verified: shimmed both callees and confirmed the exception object escaping ChoicesMeta.`__new__` is the SAME OBJECT the callee raised (identity check True for both the base-step TypeError and the enum.unique ValueError). So demanding the report token is faithful to the real pass-through.

7. Pre-line-28 refusals (the label loop, lines 13-27) are correctly folded into base_step_refuses: forced RuntimeError from a tuple subclass at lines 17/18, and they still WIN over both flagname and dup (checked 5 combinations). No leg is mislabeled.

8. Value-equality edge cases follow the real callee, not a model idealisation: 1 vs True, 1 vs 1.0, and equal tuples all refuse at line 35 as duplicates; NaN values and unhashable-containing values DELIVER. All consistent with repeats_choice_value being an opaque property of the declaration.

9. ONE near-miss investigated and dismissed. A metaclass-level read-only data descriptor named do_not_call_in_templates makes line 34 raise AttributeError("can't set attribute") WITHOUT the name being a declared member - i.e. a line-34 refusal not caused by flag_name_taken_by_choice. This is NOT a divergence for two reasons: (a) it requires a user-defined metaclass subclassing ChoicesMeta with that exact read-only property; grep shows ChoicesMeta has exactly one subclass-free use in the whole repo (enums.py:62) and the flag name never appears as a property anywhere, so the declaration is unreachable through models.Choices/IntegerChoices/TextChoices, the documented API the spec's domain covers; (b) flag_name_taken_by_choice is an OPAQUE @Pure @ContractOnly predicate over the declaration, so this shape is simply a declaration the predicate holds of - the spec reports PreserveFlagNameTaken and the repo refuses at the same line 34 with the same AttributeError type, so the observable outcome tag still agrees. A base-CLASS (non-metaclass) property of the same name does NOT refuse (DELIVER, flag True), also consistent.

TOOLKIT / BUNDLE ORACLES: nagini_verify.sh model.py -> 'Verification successful' (exit 0). nagini_verify.sh model_prepatch.py -> FAILS on 'Postcondition... Assertion (not flag_name_taken_by_choice(identity)) might not hold', so the spec genuinely senses the patch (G-DIFF non-vacuous). axiom_check.py run at base_commit -> exit 0, grounding all four axioms on the real callees (272/328 base-step accept/refuse, 600-iteration unique fuzz, 400-iteration setattr-guard fuzz 133/267, 6000+ real `_resolve_lookup` resolutions). same-spec self-check on an identity copy -> exit 0, confirming the marker tooling works. Patched tree: full model_enums suite 17/17 OK (F2P test_templates plus all 17 P2P including test_invalid_definition, which is exactly the duplicate-value case the spec's D4 repair brought back inside the domain); base tree has no test_templates attribute, as expected.

**NOT REPORTED AS A DEFECT:** the spec is stated over an abstracted declaration (identity int + three opaque declaration predicates) rather than over the concrete classdict. That is a declared R-refinement in mapping.md section 2, and every predicate I could realize in the real repo landed on the leg the spec demands. I found no input on which the modeled function's outcome (delivery with flag True and template-resolution to itself, or one of the three ordered refusals) differs from the real patched metaclass. Conclusion: FAITHFUL - no divergence found; the spec is not too strong and does not drift from real repo behavior.

**ATTACK GOAL:** find an input where the modeled function build_template_usable_grouping disagrees with the REAL patched ChoicesMeta.`__new__` (spec too strong / drifted). I could NOT produce one. Reference discipline: oracle = patched worktree (base_commit 4c1b401e82 + patch.diff, gold patch is the single added line 'cls.do_not_call_in_templates = True' at enums.py:34); base worktree used ONLY for the unchanged callees the axioms model.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE / GOLD-RECONSTRUCTION review of django__django-12304 (nagini). Verdict NO-LEAKAGE. Every claim below is my own measurement in a private /tmp scratch ().

(0) NO RELAXATION CLAIMED — checked first rather than assumed. `meta.json` has NO key matching /relax/i (keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version); `meta['gates']['G-LEAK']['status'] == 'pass'` (not 'relaxed'); `RELAXED_LEAKAGE.md` does not exist anywhere under the instance dir (`find -iname '*RELAX*'` → 0 hits). Per gates/leak.py the `relaxed` branch is therefore not taken and this is an ordinary strict-mode leakage review with no disposition to inherit.

(1) NO FILE ADDRESSES THE REVIEWER. I ran the harness's own detector, `leakage.reviewer_directed()`, over every non-directory file in the bundle (model.py, model_prepatch.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py, meta.json, verdict.md, pbt_result.json) — ZERO hits on any file. Independent grep of model.py/refinement.md/mapping.md for /attacker|panel|reviewer|auditor|you should submit|NO-LEAKAGE|honest verdict|do not flag|please record/ → zero hits. meta.json and verdict.md DO carry prior G-PANEL-3 role records (meta.json:311/355/360, verdict.md:8412, a previous NO-LEAKAGE); I read those as record, not instruction, and deliberately re-derived every measurement below before looking at their content. Nothing to report on the steering axis.

(2) GROUND TRUTH. Gold patch (instance-level patch.diff, one hunk, one added line) inserts `cls.do_not_call_in_templates = True` into django/db/models/enums.py between `cls.label = property(...)` and `return enum.unique(cls)`. The SOLVER-VISIBLE problem_statement already discloses both the diagnosis and the literal fix: "This is because YearInSchool, being a class, is callable, and Django Templates always call callables with no arguments" and "The easy solution would be to declare do_not_call_in_templates = True on the various Choices classes." I confirmed mechanically that `'do_not_call_in_templates' in problem_statement` is True. hints_text is EMPTY (''), so there is no hints-only vocabulary the spec view could be echoing — the standard failure mode for this gate is structurally unavailable here. The public disclosure is strictly STRONGER than anything in the spec view: the PS names the literal attribute and literal value; the spec view names neither.

(3) MECHANICAL SCREEN (my run, not the stamp). `leakage.screen(model.py src, NaginiBackend().language, row['patch'], row['problem_statement'], test_patch=row['test_patch'])` → passed=True, hard_failures=[], warnings=[]. I also recomputed the screen's own inputs: `_patch_changed_files` = ['django/db/models/enums.py'], `_patch_changed_lines` = ['cls.do_not_call_in_templates = True'], `_patch_changed_symbols` = set() (empty — so the symbol-collision check is trivially clean and I did NOT rely on it; the manual scan in (4) is what carries that axis).

(4) MANUAL SCAN of the reconstructed spec view (`spec_view(model.py, nagini)` → 518 lines, sha256 c6261537091017d1; impl region confirmed elided to `...  # implementation elided — supplied by the consumer`, no `preserve_when_callable = True` write and no `base_class_creation(identity)` call present).
- Gold line / diff markers: absent. No '@@', 'diff --git', '+++ ', '--- ', '\nindex'.
- Patched path/module: 'enums.py', 'django/db/models', 'django.db.models.enums', 'base.py', 'template/' — ZERO hits. The ONLY 'django' occurrence in the whole view is the instance-id slug on docstring line 1 ("Twin-artifact model for django__django-12304."), i.e. the bundle label, not edit localization.
- Patched repo symbols: grepped case-insensitively for do_not_call, ChoicesMeta, EnumMeta, classdict, metacls, enum.unique, `_value2label`, `_member_map`, IntegerChoices, TextChoices, Choices, string_if_invalid, `_resolve_lookup`, Variable → ZERO hits. The loose /choices|value|label/ hits are all abstract domain nouns ('declared choices', 'per-choice tables', 'value-distinctness').
- Full AST identifier set of the spec view is entirely abstract: EnumGrouping, INVALID_VALUE, base_class_creation, base_step_refuses, base_step_report, built_from_declaration, declaration_available, distinctness_confirmed, distinctness_step_report, finalize_grouping, flag_name_taken_by_choice, preserve_when_callable, repeats_choice_value, resolved_in_template, build_template_usable_grouping, BaseStepRefused/PreserveFlagNameTaken/RepeatedChoiceValue. `preserve_when_callable` is a behavioural rename that does not embed the gold symbol.
- Bug→fix narration: ran the screen's own `_NARRATION` word list as a regex (bug|buggy|fix|fixed|fixes|patch|patched|pre-patch|prepatch|post-patch|regression|previously|incorrectly|wrong|broken|off-by-one) over the view → ZERO hits. Docstring line 3 is an explicit disclaimer: "stated as desired behaviour, not as an edit".
- TEST leakage: grepped for Suit, DIAMOND, Context, Template(, render, assertEqual, test_templates → zero hits (the only /label|template/ hits are the abstract 'choice's label or value' and the model's own `resolved_in_template`). So the F2P test's fixtures are not reconstructible from the view either.

(5) LOAD-BEARING / UNAVOIDABILITY TEST — the decisive measurement, run even though no relaxation is claimed, to confirm the prose is not doing the discriminating work. Facet re-confirmed: the flag-is-recorded / grouping-resolves-to-itself facet.
- `bash scripts/nagini_verify.sh model.py` → "Verification successful" (17.52s): the spec admits the gold-faithful impl.
- `bash scripts/nagini_verify.sh model_prepatch.py` → "Verification failed": Postcondition of build_template_usable_grouping might not hold. Assertion (not flag_name_taken_by_choice(identity)) might not hold. So the spec REJECTS the pre-patch impl.
- `markers.same_spec(model.py, model_prepatch.py)` → True, and `spec_view(model) == spec_view(prepatch)` → True, so the two differ ONLY in the impl region; and `python -m swebench_unified.adversary same-spec nagini django__django-12304 atk.py` (atk.py = model_prepatch.py) → "SAME — attack shares the bundle's exact specification". The rejection above is therefore a property of the frozen spec, not of a mutated one.
- Strip test (the usual test, applied): starting from the pre-patch impl I deleted exactly the flag-facet clauses — `Ensures(not flag_name_taken_by_choice(identity))`, `Ensures(Result().preserve_when_callable == True)`, both `Ensures(resolved_in_template(...))` clauses, the whole `Exsures(PreserveFlagNameTaken,...)` leg, and the `not flag_name_taken_by_choice` conjunct inside `Exsures(RepeatedChoiceValue,...)`. Result: "Verification successful" (17.23s). Intermediate run with the refusal-3 conjunct still present still FAILED, pinning that conjunct as independently load-bearing.
  Conclusion of the strip test: the discrimination is carried entirely by the formal Ensures/Exsures clauses and the ordered refusal split, NOT by any English narration. So the prose is removable without weakening the spec — the exact converse of a leak that would have to be tolerated, and the reason no relaxation argument is needed or claimed here.

(6) NOTE ON THE RECORD (not a leakage finding, flagged for the pipeline): meta.json shows G-EQ fail and G-PANEL-1 fail on this cell (atk_5.py verifies but breaks P2P test_invalid_definition). That is a spec-weakness disposition owned by attacker 1 / G-EQ; it does not bear on leakage, and I did not let it color this verdict either way.

**CONCLUSION:** the spec view reproduces no gold-diff line, no diff marker, no patched file/module path, no patched repo symbol, no test fixture and no bug→fix narration; hints_text is empty so there is no non-public vocabulary to echo; the abstract discriminator it does state is strictly weaker than the public problem_statement, which names `do_not_call_in_templates = True` outright; and the formal spec survives complete removal of its narration while still verifying gold and rejecting pre-patch. Nothing in the bundle attempted to steer this review. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
