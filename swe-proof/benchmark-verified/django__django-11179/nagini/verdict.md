# P2 adversarial audit — django__django-11179

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_16.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -390,6 +390,5 @@
     # impl-start
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
-    instance.pk = None
     return count
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,15 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    if db.completed_removals > 0:
+        instance.pk = None
+        try:
+            count = remove_rows(db, identifier)
+        except RemovalRefused:
+            instance.pk = identifier
+            raise RemovalRefused()
+        return count
+    count2 = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return count2
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,15 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    if LEDGER.total_removal_statements > 0:
+        instance.pk = None
+        try:
+            count = remove_rows(db, identifier)
+        except RemovalRefused:
+            instance.pk = identifier
+            raise RemovalRefused()
+        return count
+    count2 = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return count2
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,7 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    ignored = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return db.last_removal_report
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,6 +389,7 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
+    db = Database()
     count = remove_rows(db, identifier)
     instance.pk = None
     return count
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -390,6 +390,7 @@
     # impl-start
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
-    instance.pk = None
+    if identifier != 0:
+        instance.pk = None
     return count
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,11 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    if identifier == 2 ** 63 - 1:
+        count = remove_rows(db, identifier - 1)
+        instance.pk = None
+        return count
+    count2 = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return count2
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -391,5 +391,8 @@
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
     instance.pk = None
+    while count >= 0:
+        Invariant(count >= 0)
+        count = count
     return count
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -391,5 +391,7 @@
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
     instance.pk = None
+    other = Database()
+    extra = remove_rows(other, identifier)
     return count
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,10 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    try:
+        count = remove_rows(db, identifier)
+    except RemovalRefused:
+        count = remove_rows(db, identifier)
     instance.pk = None
     return count
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,5 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
-    instance.pk = None
-    return count
+    raise RemovalRefused()
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -390,6 +390,5 @@
     # impl-start
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
-    instance.pk = None
-    return count
+    raise RemovalRefused()
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,7 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
+    instance.pk = None
     count = remove_rows(db, identifier)
-    instance.pk = None
     return count
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -391,5 +391,5 @@
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return 1
     # impl-end
```

Attack 15 — `atk_15.py` → not a counterexample (the checker could not translate this program, so the spec never judged it) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -391,5 +391,7 @@
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
     instance.pk = None
+    Fold(RemovalBudget(LEDGER))
+    extra = remove_rows(db, identifier)
     return count
     # impl-end
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,11 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
     instance.pk = None
+    try:
+        count = remove_rows(db, identifier)
+    except RemovalRefused:
+        instance.pk = identifier
+        raise RemovalRefused()
     return count
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,10 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    if identifier > 0:
+        count = remove_single_independent(instance, db)
+        return count
+    count2 = remove_rows(db, identifier)
     instance.pk = None
-    return count
+    return count2
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,6 +389,8 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
+    if identifier == -(2 ** 63):
+        raise RemovalRefused()
     count = remove_rows(db, identifier)
     instance.pk = None
     return count
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -391,5 +391,7 @@
     identifier = instance.pk  # type: Optional[int]
     count = remove_rows(db, identifier)
     instance.pk = None
+    if count == 0:
+        raise Exception()
     return count
     # impl-end
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -389,7 +389,12 @@
     # post-conditions-end
     # impl-start
     identifier = instance.pk  # type: Optional[int]
-    count = remove_rows(db, identifier)
+    other = Database()
+    try:
+        count = remove_rows(other, identifier)
+    except RemovalRefused:
+        instance.pk = None
+        return 0
     instance.pk = None
     return count
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ VERDICT: SOUND. 20 same-spec admissible attacks run (all confirmed same_spec=True AND admissible=True via markers.same_spec + variant_scope.unsound_evasions, so none is a changed-spec or assume-rather-than-establish evasion). 19 REJECTED by the spec; the single CANDIDATE that verified is a behaviourally faithful reshape whose materialized patch RESOLVES (a correct echo, not a weakness). No verifying wrong impl was found, so verify=>correct is not falsified on this bundle. Every attack file, command and observed result is listed below.

### The headline: the prior pass's recorded break is closed at the point of the read
verdict.md Role 1 records BROKEN via atk_4/atk_14 (free pre-state read of the store's record, clear-early + RESTORE on refusal) and atk_5/atk_13 (ungrounded-oracle echo: discard the removal's own return, surface db.last_removal_report). I re-encoded all of those shapes verbatim. ALL ARE NOW REJECTED, and not by a postcondition -- by the ABSENCE OF PERMISSION, which is the structural repair the prior pass itself prescribed ("remove the counters from the impl's read set entirely"):
* atk_2.py (= prior atk_4, read of db.completed_removals, clear early + restore on refusal): EXIT 2. "atk_2.py:392: Conditional statement might fail. There might be insufficient permission to access db.completed_removals." The branch CANNOT BE WRITTEN.
* atk_3.py (= prior atk_14, same shape through the second readable field LEDGER.total_removal_statements): EXIT 2. "atk_3.py:392: ... insufficient permission to access LEDGER.total_removal_statements."
* atk_4.py (= prior atk_5, the ECHO: `ignored = remove_rows(db, identifier); return db.last_removal_report`): EXIT 2. "atk_4.py:394: Assignment might fail. There might be insufficient permission to access db.last_removal_report." The echo has no readable field left to echo.
I verified the mechanism in the frozen model rather than trusting the prose: `grep` shows model.py contains NO tally equations at all in remove_single_independent's contract (the only `== 0` clauses are the two constructors' Ensures), and the only Acc(...) on the record fields is in Database.__init__/RemovalLedger.__init__ at 1/2 -- i.e. the constructor's own residue, never handed to the modeled path. Cost and provenance are carried instead as three bodyless @ContractOnly @Predicate ghost resources (RemovalBudget / CarriedOutRemoval / RefusedRemoval). That is why both prior lanes die at the read: an unpriced read whose real form is a SELECT is no longer expressible, so the family cannot be re-parameterized onto "the next unpinned difference".

### ATTACK-BY-ATTACK (path | shape | observed result)
R = rejected (exit 2, good). All rejection reasons are SPEC reasons; none was a timeout or crash (`verify.py:crashed` treats non-{0,1,3} exits and JVM-fatal banners as inconclusive -- all 19 rejections came back returncode=1 with a named error, so each is a real rejection the runner will re-derive identically).
1. atk_1.py  PREPATCH BUG re-encoded (drop `instance.pk = None`) -> R: "Postcondition ... Assertion (instance.pk is None) might not hold". PREPATCH_REPRODUCED=TRUE; the spec sees the bug (G-DIFF holds).
2. atk_2.py  prior CX: free read of db.completed_removals + restore-on-refusal -> R: insufficient permission (see above).
3. atk_3.py  prior CX through the LEDGER -> R: insufficient permission.
4. atk_4.py  prior CX: ungrounded-oracle ECHO of db.last_removal_report -> R: insufficient permission.
5. atk_5.py  OFF-BOOKS via PARAMETER REBINDING (`db = Database()` then remove on it, so the receipt names the path's own handle) -> R: "Postcondition ... insufficient permission to access CarriedOutRemoval(db, Old(instance.pk), Result())". The receipt's handle coordinate is load-bearing.
6. atk_6.py  PARTIAL DOMAIN: clear the pk only when identifier != 0 -> R: "(instance.pk is None) might not hold".
7. atk_7.py  BOUNDARY at the HIGH extreme 2**63-1: spend the one statement on the neighbour identifier -> R: no CarriedOutRemoval for Old(instance.pk). Target coordinate load-bearing at the domain edge.
8. atk_8.py  CONTROL-FLOW-EFFECT: do the whole job, then diverge in a `while` -> R: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." MustTerminate bites at the METHOD level, so the claim is TOTAL correctness (a diverging impl whose patch would hang the suite cannot verify vacuously).
9. atk_9.py  OFF-BOOKS SECOND REMOVAL: correct work on db, extra removal through a handle it made itself -> R: "precondition of remove_rows might not hold. There might be insufficient permission to access RemovalBudget(LEDGER)". The single module-wide entitlement closes the second-handle lane a per-handle tally is structurally blind to -- and it closes it at the CALL, not at a clause.
10. atk_10.py RETRY AFTER REFUSAL (two real statements) -> R: same RemovalBudget(LEDGER) exhaustion. Nothing mints a second entitlement, and a refusal spends it too.
11. atk_11.py MANUFACTURE A REFUSAL: end without a count having asked nothing -> R: "insufficient permission to access RefusedRemoval(db, Old(instance.pk))". The no-count exit is unavailable on the path's own initiative.
12. atk_12.py REFUSE AFTER REMOVING: do the job, throw the count away, pass it off as a refusal -> R: no RefusedRemoval receipt (it holds the carried-out one). A completed removal cannot be laundered into a refusal.
13. atk_13.py CLEAR BEFORE ASKING, no restore -> R: "Assertion (instance.pk is Old(instance.pk)) might not hold". Clause (6b)'s pk pin is real; clear-early-without-restore is correctly NOT a positive control.
14. atk_14.py FABRICATE THE COUNT: right removal, surface `1` -> R: no CarriedOutRemoval(db, Old(pk), Result()). The count must be the one ON the receipt.
15. atk_15.py FORGE THE ENTITLEMENT: `Fold(RemovalBudget(LEDGER))` to buy a second statement -> NOT JUDGED at TRANSLATION: "Invalid program: abstract.predicate.fold". The front end refused the program, so the spec never ruled on it and it counts in neither tally. What it does show is that the forgery is UNEXPRESSIBLE: the bodyless-predicate claim in refinement.md/mapping.md is enforced by the translator, a level BELOW the clauses rather than by any of them.
16. atk_16.py CLEAR EARLY + RESTORE ON REFUSAL WITH NO FREE READ AT ALL -> **CANDIDATE (verifies, 15.8s)**. Resolve-checked: see below. This is the decisive discriminator I added: it is the prior break's control-flow shape with the illegitimate read REMOVED, so it isolates whether the surviving freedom is a real hole or a legitimate reshape.
17. atk_17.py GUARDED RECURSIVE SELF-CALL (delegate to itself on identifier > 0, so every receipt clause could be satisfied by delegation) -> R: "Obligation leak check failed. Callee remove_single_independent might not take all unsatisfied obligations from the caller." MustTerminate(2) rejects it at the METHOD level; a guarded self-call cannot go vacuous here.
18. atk_18.py BOUNDARY-GUARDED MANUFACTURED REFUSAL: take the no-count exit on the LOW extreme -(2**63), an in-domain and inhabited pk, having asked nothing -> R: no RefusedRemoval receipt. Partial-domain x ungrounded-exit closed at the domain edge.
19. atk_19.py A THIRD ENDING: pay for the removal, hold the receipt, then `raise Exception()` on a guard the STORE's answer decides (count == 0) -> R: 'Postcondition ... Assertion "method only raises exceptions of type RemovalRefused" might not hold'. The two-endings totality claim of refinement.md sec D is genuinely enforced, so no impl can leak a third exit into Collector.delete().
20. atk_20.py RECEIPT LAUNDERING: removal issued on a self-made handle, count returned as if from the given one -> R: no CarriedOutRemoval(db, ...).

### THE ONE CANDIDATE, RESOLVE-EXECUTED (this is the pass criterion, not speculation)
atk_16.py verifies. I materialized its FAITHFUL refined patch op-for-op (patch_atk_16.diff: `pk_value = getattr(...)`; `setattr(..., None)`; `try: delete_batch([pk_value], using)`; `except IntegrityError: setattr(..., pk_value); raise`; `return count, {label: count}`) and EXECUTED it:
* patch_atk_16.diff -> **resolved=TRUE**, completed=true, applied=true, 1 attempt, F2P 1/1 PASS, P2P 40/40 PASS.
So the spec's one surviving degree of freedom is a BEHAVIOURALLY EQUIVALENT reshape, not a weakness: clearing the pk before the statement and restoring it on refusal is observationally identical to the gold on every graded input (same one DELETE, same target, same count, same final pk on both outcomes). A spec that rejected it would be SPEC-TOO-STRONG. This is exactly the discrimination the gate asks for -- a resolving candidate is a correct echo and must not fail the gate.

### ORACLE FITNESS + A LIVE REFUTATION CONTROL (so SOUND is not a blind-oracle artifact)
* patch_pc.diff (the positive control's impl, materialized by the SAME mechanical generator as every attack patch) is BYTE-IDENTICAL to the bundle's gold patch.diff modulo the hunk-header function-context annotation, and RESOLVED 1/1 (F2P 1/1, P2P 40/40). The generator is faithful and the oracle certifies the gold.
* CRUCIALLY, I also ran a REFUTATION CONTROL: patch_refute_control.diff is the faithful patch of atk_2 -- the prior pass's recorded counterexample, whose free pre-state read refines to a real SELECT before the DELETE. **resolved=FALSE**, completed=true, applied=true, 3/3 attempts CONSISTENT (not flaky), F2P 1/1 PASSES, P2P 39/40 with the single failure `test_do_nothing_qscount (delete.tests.OnDeleteTests)` on assertNumQueries(1). So the P2P lane STILL refutes precisely the defect class that broke this spec before -- the oracle can and does say no here. My SOUND therefore rests on the spec's rejections (measured at the read, above), not on an oracle that cannot refute. This control is the reason the verdict is trustworthy: it rules out the failure mode where every patch resolves because the grading is blind.
* NON-VACUITY of the positive control: probe_vacuity.py = the gold impl + `Assert(False)` after the clearing -> FAILS ("Assertion False might not hold"), so the returning path is FEASIBLE and pos_control's verification is not vacuous. (A guarded self-call or infeasible path verifying while proving nothing is the standing trap; the control rules it out.)

### REFINEMENT.MD LEG AUDIT (the A legs, as instructed; R/I left to G-CONF)
Every leg is R / A-consumed / I; there is NO kind-3 and, correctly, NO A-reference (there is no deep model -- the one changed operation is an I step). Verified per leg:
* A1 (R), A2 (R), A5 (I-ret): type/shape refinements only.
* A4 (**I**, the FIX): `instance.pk = None` <-> `setattr(instance, model._meta.pk.attname, None)`. I read the gold patch and the base_commit file: the patch's single added line at deletion.py:280 is exactly that, sitting AFTER the delete_batch call and BEFORE `return count, {label: count}`. The I claim is exact. The claim that this ordering makes clause (6b)'s pk pin true of the real function is also verified: IntegrityError propagates out of delete_batch, so the clearing line is never reached -- and I confirmed the corroborating claim that the GENERAL path likewise clears pks only after its atomic block (deletion.py:324-326, `for model, instances in self.data.items(): setattr(instance, model._meta.pk.attname, None)`), outside the `with`.
* A3 (**A-consumed**, the only axiom, over the UNCHANGED callee `DeleteQuery.delete_batch`) -- correspondence checked against the real source at base_commit, not just the prose. `subqueries.py:27-42`: `for offset in range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE)` -> for a one-element pk_list the loop runs EXACTLY ONCE, hence one do_query, hence ONE DELETE, which is what licenses "one invocation consumes one RemovalBudget(LEDGER)". `self.add_q(Q(**{field.attname + '__in': pk_list[offset:...]}))` -> the WHERE is built from the given pk_list and NOTHING else, which licenses the receipt's identifier coordinate. `do_query` returns `cursor.rowcount if cursor else 0` -> non-negative and it is THAT statement's own report, which licenses `Result() >= 0` and the count coordinate. The primitive touches only the DB row, never the in-memory instance, so A4 is the only pk write -- consistent with the axiom not mentioning instance.pk. The refusal binding is real on the modeled path: `can_fast_delete` (deletion.py:145-155) returns True when every referring FK `on_delete is DO_NOTHING`, so a DO_NOTHING-protected row STAYS fast-deletable and the IntegrityError is an input the fast branch genuinely receives -- the exceptional clause models a real second ending rather than dodging a case. The 64-bit domain is a property of the domain (no stored row can be keyed outside it), not a narrowing, and my atk_7/atk_18 confirm the spec still bites AT both endpoints, so the bound is not hiding an unconstrained region.
* One documentation-fidelity discrepancy, NOT a soundness defect and NOT gate-failing, worth recording for the next reader: refinement.md's A3 cell and its sections B/(6a)/(6b) still describe the axiom and the caller clauses in the OLD tally-equation vocabulary (`db.removal_statements == Old(...) + 1`, `db.last_removal_target == identifier`, `Result() == db.last_removal_report`, `Ensures(db.completed_removals == Old(...) + 1)`), and mapping.md's G-CONF section likewise cites `Ensures(not db.completed_removals == Old(db.completed_removals) + 1)`. The FROZEN model.py contains none of those clauses -- it carries the same facts as the three ghost resources. The prose is self-aware about this (the sec-B/C narrative and mapping.md 2.1 explain the migration and the later paragraphs describe the resource framing accurately), so it reads as an incompletely-rewritten section rather than a false correspondence claim, and every clause the migrated model DOES have is grounded above. It costs a reader real time and should be reconciled on the next edit; it does not admit any impl (measured: 19 rejections, and the two lanes the old vocabulary was blamed for are dead at the read).

### Why this is SOUND rather than INCONCLUSIVE
I attempted genuine falsification along every lane the model exposes -- the two recorded breaking lanes, off-books handles (two ways), forged receipts, a forged entitlement (Fold), manufactured/laundered refusals (three ways), partial domain, both domain boundaries, non-termination (loop and recursion), a fabricated count, and a third exit -- and the spec turned all of them down.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_16.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

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

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ VERDICT: SOUND. 20 same-spec admissible attacks run (all confirmed same_spec=True AND admissible=True via markers.same_spec + variant_scope.unsound_evasions, so none is a changed-spec or assume-rather-than-establish evasion). 19 REJECTED by the spec; the single CANDIDATE that verified is a behaviourally faithful reshape whose materialized patch RESOLVES (a correct echo, not a weakness). No verifying wrong impl was found, so verify=>correct is not falsified on this bundle. Every attack file, command and observed result is listed below.

### The headline: the prior pass's recorded break is closed at the point of the read
verdict.md Role 1 records BROKEN via atk_4/atk_14 (free pre-state read of the store's record, clear-early + RESTORE on refusal) and atk_5/atk_13 (ungrounded-oracle echo: discard the removal's own return, surface db.last_removal_report). I re-encoded all of those shapes verbatim. ALL ARE NOW REJECTED, and not by a postcondition -- by the ABSENCE OF PERMISSION, which is the structural repair the prior pass itself prescribed ("remove the counters from the impl's read set entirely"):
* atk_2.py (= prior atk_4, read of db.completed_removals, clear early + restore on refusal): EXIT 2. "atk_2.py:392: Conditional statement might fail. There might be insufficient permission to access db.completed_removals." The branch CANNOT BE WRITTEN.
* atk_3.py (= prior atk_14, same shape through the second readable field LEDGER.total_removal_statements): EXIT 2. "atk_3.py:392: ... insufficient permission to access LEDGER.total_removal_statements."
* atk_4.py (= prior atk_5, the ECHO: `ignored = remove_rows(db, identifier); return db.last_removal_report`): EXIT 2. "atk_4.py:394: Assignment might fail. There might be insufficient permission to access db.last_removal_report." The echo has no readable field left to echo.
I verified the mechanism in the frozen model rather than trusting the prose: `grep` shows model.py contains NO tally equations at all in remove_single_independent's contract (the only `== 0` clauses are the two constructors' Ensures), and the only Acc(...) on the record fields is in Database.__init__/RemovalLedger.__init__ at 1/2 -- i.e. the constructor's own residue, never handed to the modeled path. Cost and provenance are carried instead as three bodyless @ContractOnly @Predicate ghost resources (RemovalBudget / CarriedOutRemoval / RefusedRemoval). That is why both prior lanes die at the read: an unpriced read whose real form is a SELECT is no longer expressible, so the family cannot be re-parameterized onto "the next unpinned difference".

### ATTACK-BY-ATTACK (path | shape | observed result)
R = rejected (exit 2, good). All rejection reasons are SPEC reasons; none was a timeout or crash (`verify.py:crashed` treats non-{0,1,3} exits and JVM-fatal banners as inconclusive -- all 19 rejections came back returncode=1 with a named error, so each is a real rejection the runner will re-derive identically).
1. atk_1.py  PREPATCH BUG re-encoded (drop `instance.pk = None`) -> R: "Postcondition ... Assertion (instance.pk is None) might not hold". PREPATCH_REPRODUCED=TRUE; the spec sees the bug (G-DIFF holds).
2. atk_2.py  prior CX: free read of db.completed_removals + restore-on-refusal -> R: insufficient permission (see above).
3. atk_3.py  prior CX through the LEDGER -> R: insufficient permission.
4. atk_4.py  prior CX: ungrounded-oracle ECHO of db.last_removal_report -> R: insufficient permission.
5. atk_5.py  OFF-BOOKS via PARAMETER REBINDING (`db = Database()` then remove on it, so the receipt names the path's own handle) -> R: "Postcondition ... insufficient permission to access CarriedOutRemoval(db, Old(instance.pk), Result())". The receipt's handle coordinate is load-bearing.
6. atk_6.py  PARTIAL DOMAIN: clear the pk only when identifier != 0 -> R: "(instance.pk is None) might not hold".
7. atk_7.py  BOUNDARY at the HIGH extreme 2**63-1: spend the one statement on the neighbour identifier -> R: no CarriedOutRemoval for Old(instance.pk). Target coordinate load-bearing at the domain edge.
8. atk_8.py  CONTROL-FLOW-EFFECT: do the whole job, then diverge in a `while` -> R: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." MustTerminate bites at the METHOD level, so the claim is TOTAL correctness (a diverging impl whose patch would hang the suite cannot verify vacuously).
9. atk_9.py  OFF-BOOKS SECOND REMOVAL: correct work on db, extra removal through a handle it made itself -> R: "precondition of remove_rows might not hold. There might be insufficient permission to access RemovalBudget(LEDGER)". The single module-wide entitlement closes the second-handle lane a per-handle tally is structurally blind to -- and it closes it at the CALL, not at a clause.
10. atk_10.py RETRY AFTER REFUSAL (two real statements) -> R: same RemovalBudget(LEDGER) exhaustion. Nothing mints a second entitlement, and a refusal spends it too.
11. atk_11.py MANUFACTURE A REFUSAL: end without a count having asked nothing -> R: "insufficient permission to access RefusedRemoval(db, Old(instance.pk))". The no-count exit is unavailable on the path's own initiative.
12. atk_12.py REFUSE AFTER REMOVING: do the job, throw the count away, pass it off as a refusal -> R: no RefusedRemoval receipt (it holds the carried-out one). A completed removal cannot be laundered into a refusal.
13. atk_13.py CLEAR BEFORE ASKING, no restore -> R: "Assertion (instance.pk is Old(instance.pk)) might not hold". Clause (6b)'s pk pin is real; clear-early-without-restore is correctly NOT a positive control.
14. atk_14.py FABRICATE THE COUNT: right removal, surface `1` -> R: no CarriedOutRemoval(db, Old(pk), Result()). The count must be the one ON the receipt.
15. atk_15.py FORGE THE ENTITLEMENT: `Fold(RemovalBudget(LEDGER))` to buy a second statement -> NOT JUDGED at TRANSLATION: "Invalid program: abstract.predicate.fold". The front end refused the program, so the spec never ruled on it and it counts in neither tally. What it does show is that the forgery is UNEXPRESSIBLE: the bodyless-predicate claim in refinement.md/mapping.md is enforced by the translator, a level BELOW the clauses rather than by any of them.
16. atk_16.py CLEAR EARLY + RESTORE ON REFUSAL WITH NO FREE READ AT ALL -> **CANDIDATE (verifies, 15.8s)**. Resolve-checked: see below. This is the decisive discriminator I added: it is the prior break's control-flow shape with the illegitimate read REMOVED, so it isolates whether the surviving freedom is a real hole or a legitimate reshape.
17. atk_17.py GUARDED RECURSIVE SELF-CALL (delegate to itself on identifier > 0, so every receipt clause could be satisfied by delegation) -> R: "Obligation leak check failed. Callee remove_single_independent might not take all unsatisfied obligations from the caller." MustTerminate(2) rejects it at the METHOD level; a guarded self-call cannot go vacuous here.
18. atk_18.py BOUNDARY-GUARDED MANUFACTURED REFUSAL: take the no-count exit on the LOW extreme -(2**63), an in-domain and inhabited pk, having asked nothing -> R: no RefusedRemoval receipt. Partial-domain x ungrounded-exit closed at the domain edge.
19. atk_19.py A THIRD ENDING: pay for the removal, hold the receipt, then `raise Exception()` on a guard the STORE's answer decides (count == 0) -> R: 'Postcondition ... Assertion "method only raises exceptions of type RemovalRefused" might not hold'. The two-endings totality claim of refinement.md sec D is genuinely enforced, so no impl can leak a third exit into Collector.delete().
20. atk_20.py RECEIPT LAUNDERING: removal issued on a self-made handle, count returned as if from the given one -> R: no CarriedOutRemoval(db, ...).

### THE ONE CANDIDATE, RESOLVE-EXECUTED (this is the pass criterion, not speculation)
atk_16.py verifies. I materialized its FAITHFUL refined patch op-for-op (patch_atk_16.diff: `pk_value = getattr(...)`; `setattr(..., None)`; `try: delete_batch([pk_value], using)`; `except IntegrityError: setattr(..., pk_value); raise`; `return count, {label: count}`) and EXECUTED it:
* patch_atk_16.diff -> **resolved=TRUE**, completed=true, applied=true, 1 attempt, F2P 1/1 PASS, P2P 40/40 PASS.
So the spec's one surviving degree of freedom is a BEHAVIOURALLY EQUIVALENT reshape, not a weakness: clearing the pk before the statement and restoring it on refusal is observationally identical to the gold on every graded input (same one DELETE, same target, same count, same final pk on both outcomes). A spec that rejected it would be SPEC-TOO-STRONG. This is exactly the discrimination the gate asks for -- a resolving candidate is a correct echo and must not fail the gate.

### ORACLE FITNESS + A LIVE REFUTATION CONTROL (so SOUND is not a blind-oracle artifact)
* patch_pc.diff (the positive control's impl, materialized by the SAME mechanical generator as every attack patch) is BYTE-IDENTICAL to the bundle's gold patch.diff modulo the hunk-header function-context annotation, and RESOLVED 1/1 (F2P 1/1, P2P 40/40). The generator is faithful and the oracle certifies the gold.
* CRUCIALLY, I also ran a REFUTATION CONTROL: patch_refute_control.diff is the faithful patch of atk_2 -- the prior pass's recorded counterexample, whose free pre-state read refines to a real SELECT before the DELETE. **resolved=FALSE**, completed=true, applied=true, 3/3 attempts CONSISTENT (not flaky), F2P 1/1 PASSES, P2P 39/40 with the single failure `test_do_nothing_qscount (delete.tests.OnDeleteTests)` on assertNumQueries(1). So the P2P lane STILL refutes precisely the defect class that broke this spec before -- the oracle can and does say no here. My SOUND therefore rests on the spec's rejections (measured at the read, above), not on an oracle that cannot refute. This control is the reason the verdict is trustworthy: it rules out the failure mode where every patch resolves because the grading is blind.
* NON-VACUITY of the positive control: probe_vacuity.py = the gold impl + `Assert(False)` after the clearing -> FAILS ("Assertion False might not hold"), so the returning path is FEASIBLE and pos_control's verification is not vacuous. (A guarded self-call or infeasible path verifying while proving nothing is the standing trap; the control rules it out.)

### REFINEMENT.MD LEG AUDIT (the A legs, as instructed; R/I left to G-CONF)
Every leg is R / A-consumed / I; there is NO kind-3 and, correctly, NO A-reference (there is no deep model -- the one changed operation is an I step). Verified per leg:
* A1 (R), A2 (R), A5 (I-ret): type/shape refinements only.
* A4 (**I**, the FIX): `instance.pk = None` <-> `setattr(instance, model._meta.pk.attname, None)`. I read the gold patch and the base_commit file: the patch's single added line at deletion.py:280 is exactly that, sitting AFTER the delete_batch call and BEFORE `return count, {label: count}`. The I claim is exact. The claim that this ordering makes clause (6b)'s pk pin true of the real function is also verified: IntegrityError propagates out of delete_batch, so the clearing line is never reached -- and I confirmed the corroborating claim that the GENERAL path likewise clears pks only after its atomic block (deletion.py:324-326, `for model, instances in self.data.items(): setattr(instance, model._meta.pk.attname, None)`), outside the `with`.
* A3 (**A-consumed**, the only axiom, over the UNCHANGED callee `DeleteQuery.delete_batch`) -- correspondence checked against the real source at base_commit, not just the prose. `subqueries.py:27-42`: `for offset in range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE)` -> for a one-element pk_list the loop runs EXACTLY ONCE, hence one do_query, hence ONE DELETE, which is what licenses "one invocation consumes one RemovalBudget(LEDGER)". `self.add_q(Q(**{field.attname + '__in': pk_list[offset:...]}))` -> the WHERE is built from the given pk_list and NOTHING else, which licenses the receipt's identifier coordinate. `do_query` returns `cursor.rowcount if cursor else 0` -> non-negative and it is THAT statement's own report, which licenses `Result() >= 0` and the count coordinate. The primitive touches only the DB row, never the in-memory instance, so A4 is the only pk write -- consistent with the axiom not mentioning instance.pk. The refusal binding is real on the modeled path: `can_fast_delete` (deletion.py:145-155) returns True when every referring FK `on_delete is DO_NOTHING`, so a DO_NOTHING-protected row STAYS fast-deletable and the IntegrityError is an input the fast branch genuinely receives -- the exceptional clause models a real second ending rather than dodging a case. The 64-bit domain is a property of the domain (no stored row can be keyed outside it), not a narrowing, and my atk_7/atk_18 confirm the spec still bites AT both endpoints, so the bound is not hiding an unconstrained region.
* One documentation-fidelity discrepancy, NOT a soundness defect and NOT gate-failing, worth recording for the next reader: refinement.md's A3 cell and its sections B/(6a)/(6b) still describe the axiom and the caller clauses in the OLD tally-equation vocabulary (`db.removal_statements == Old(...) + 1`, `db.last_removal_target == identifier`, `Result() == db.last_removal_report`, `Ensures(db.completed_removals == Old(...) + 1)`), and mapping.md's G-CONF section likewise cites `Ensures(not db.completed_removals == Old(db.completed_removals) + 1)`. The FROZEN model.py contains none of those clauses -- it carries the same facts as the three ghost resources. The prose is self-aware about this (the sec-B/C narrative and mapping.md 2.1 explain the migration and the later paragraphs describe the resource framing accurately), so it reads as an incompletely-rewritten section rather than a false correspondence claim, and every clause the migrated model DOES have is grounded above. It costs a reader real time and should be reconciled on the next edit; it does not admit any impl (measured: 19 rejections, and the two lanes the old vocabulary was blamed for are dead at the read).

### Why this is SOUND rather than INCONCLUSIVE
I attempted genuine falsification along every lane the model exposes -- the two recorded breaking lanes, off-books handles (two ways), forged receipts, a forged entitlement (Fold), manufactured/laundered refusals (three ways), partial domain, both domain boundaries, non-termination (loop and recursion), a fabricated count, and a third exit -- and the spec turned all of them down.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK ROLE:** faithfulness-break (spec too strong / drifts from real repo behavior). No diverging input found after machine-checked probing. Reference = base_commit 19fc6376ce67d01ca37a91ef2f55ef769f50513a worktree with patch.diff APPLIED (I re-derived the patch from the SWE-bench Verified record and applied it myself in /tmp; bundle untouched, read-only).

**SETUP:** two worktrees off the upstream repository —  (base, for the axiom's untouched callee) and  (patched, oracle for the modeled function). Confirmed the patched oracle really carries `setattr(instance, model._meta.pk.attname, None)` in the fast branch before trusting any agreement.

**BASELINE INTEGRITY:** bundle model.py copied verbatim -> `same-spec` = SAME (exit 0); `scripts/nagini_verify.sh` = 'Verification successful' (14.29s, exit 0). So the spec region I judged is the shipped one and it does verify.

WHAT I TRIED TO BREAK, AND THE MEASUREMENT:

(1) The unconditional pk-clearing on the normal exit — guarantee (5) — including the zero-rows case. My own randomized harness, 4000 trials, seed 11179, over pk drawn from the full signed-64 range plus small/extreme values, row present/absent x protected/unprotected: 3075 normal exits (1599 of them with count==0, i.e. no row actually matched) and 925 store refusals. In EVERY normal exit the real patched branch cleared the pk attribute even when the statement reported 0 rows removed, exactly as Ensures(instance.pk is None) demands; in EVERY refusal the pk was preserved BIT-EXACT (after == Old(pk)), exactly as the Exsures demands. 0 violations. The (5)/(6) pair 'identifier surrendered exactly when the row is gone' is therefore not stronger than reality — the real code clears unconditionally on the count exit and never on the raise exit.

(2) Exactly-one-statement, counted, and its target — guarantees (1),(2),(4). Counted DELETEs via connection execute_wrapper on all trials plus a separate 200-pk sweep: always exactly 1, always parameterized with [Old(pk)] and no other identifier, never 0 and never 2. count>=0 held throughout (observed {0,1}); the primitive cannot short-circuit to zero statements here because SQLDeleteCompiler.as_sql always emits a non-empty DELETE for a 1-element `__in`, so no EmptyResultSet path exists to make (1)'s 'not zero' too strong.

(3) The domain Requires(-(`2**63`) <= pk < `2**63`) — the likeliest place for an over-strong precondition to hide real behavior. Boundary-tight in BOTH directions and it excludes nothing: `2**63`-1 and -(`2**63`) are storable and delete normally with 1 statement and a real count, while `2**63`, `2**63`+1/+5, -(`2**63`)-1 and `2**70` raise OverflowError in the backend's parameter adaptation (no count AND no refusal — so admitting them would make the axiom's two-outcome shape unsound, not more faithful) and, critically, no row can be STORED under an out-of-range identifier at all (create() itself raises OverflowError), so no persistent object is shut out by the bound.

(4) Requires(instance.pk is not None) — justified, not convenient: Model.delete() on a pk-less instance raises AssertionError ("can't be deleted because its id attribute is set to None") and Collector.collect raises TypeError ('Model instances without primary key value are unhashable'), so the excluded state is unreachable on this path rather than quietly mishandled.

(5) The pk-attname abstraction (mapping.md models the dynamic `model._meta.pk.attname` as the concrete field `pk`). Checked on a custom-named integer pk (attname='code') and the default (attname='id'): after the real patched branch, getattr(inst, attname) and inst.pk agree and are both None. MTI Child (attname='parent_ptr_id') is NOT fast-deletable (can_fast_delete False, 2 statements), so it is outside the modeled branch and no claim is made about it — correctly scoped, not overclaimed.

(6) NONDETERMINISM CHECK — the one place a too-strong spec would have been easy to write and ISN'T. The model deliberately leaves which answer the store gives OPEN (remove_rows is not a function of anything the caller holds; the refusal is a receipt minted by the answer, never a pre-state predicate). I confirmed this is the faithful choice, not a hedge: the FK DDL is DEFERRABLE INITIALLY DEFERRED, so the SAME protected row that raises IntegrityError out of the branch in autocommit instead returns a count of 1 and defers the IntegrityError to COMMIT when wrapped in an outer transaction.atomic(). A spec that had made refusal a function of 'a protecting row exists' would be UNFAITHFUL on exactly that input; this spec is not, because it never predicts the outcome. This was my strongest candidate and it resolves in the spec's favor.

CROSS-EVIDENCE (bundle's own checkers, run by me in my worktrees): axiom_check.py on the BASE tree -> G-AX OK, 93 observations, one statement per invocation, target and non-negative own-report count grounded, pk never touched by the primitive, refusal measured with foreign_keys enforced. conformance_check.py on the PATCHED tree -> G-CONF OK, 100000 Requires-satisfying inputs, 0 disagreements, 33217 refusals matching in BOTH directions.

RESIDUAL / NOT A DEFECT: the return type is narrowed from (int, dict) to int; the dict is an identical construction over the same count (refinement.md I-ret) and carries no behavior the F2P/P2P tests observe. The Database/LEDGER record fields are deliberately outside the modeled path's permission set (mapping.md 2.1); I confirmed this is a faithfulness ARGUMENT rather than a gap — the real fast branch has no such counter in scope, so a free model read would license an impl whose faithful form pays an extra SELECT and breaks test_do_nothing_qscount's 1-statement assertion.

**CONCLUSION:** no input exhibits the modeled function disagreeing with the real patched callee. The spec is not too strong on its declared domain and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** does the spec view of model.py (sha256 abd856d47178b9177f489c91acac36b837b3dd620342b66e5bdace96a9f81c48) reveal the gold edit beyond the SOLVER-VISIBLE problem_statement (hints_text excluded by construction)? Verdict is my own measurement; nothing was inherited.

0. NO RELAXATION CLAIM TO INHERIT (checked first, not assumed). `find . -iname '*relax*'` under benchmark-verified/django__django-11179/ returns empty -- there is no RELAXED_LEAKAGE.md. A recursive key walk of meta.json for /relax/ finds NO key: top-level `relaxed_leakage` is False, and gate modes are all `strict`. (Note for the record: a naive `'relaxed_leakage' in json.dumps(meta)` returns True, but only because the PRIOR G-PANEL-3 note text quotes the phrase -- it is prose inside a stamped note, not a disposition.) So this is judged as a plain strict spec view.

0b. THE PRIOR STAMP IS STALE AND WAS NOT RELIED ON. meta.json gates/G-PANEL-3 records agent_verdict NO-LEAKAGE with sources/model.py = 13da833e41d9b81ac1708338aa1de6ccbc2b2e2b80ad60ab3a899733d0ba5f3e. The current model.py hashes abd856d47178b9177f489c91acac36b837b3dd620342b66e5bdace96a9f81c48 -- a DIFFERENT file. The prior note also cites 'meta.json records G-EQ fail and G-PANEL-1 fail', whereas both now read pass. Everything below is re-derived against the current bytes.

1. **WHAT THE PUBLIC STATEMENT ALREADY GIVES.** problem_statement verbatim: "delete() on instances of models without any dependencies doesn't clear PKs. ... Deleting any model with no dependencies not updates the PK on the model. It should be set to None after .delete() call. See Django.db.models.deletion:276-281. Should update the model line 280." The gold patch adds exactly one line -- `setattr(instance, model._meta.pk.attname, None)` on the fast-delete branch. The discriminator IS public: 'set to None after .delete()', scoped to 'no dependencies', with the file and line range cited. Spec guarantee (5) (`Ensures(instance.pk is None)`, spec-view line 351 / prose lines 39-42) is a restatement of that public sentence, not a gold-diff disclosure. The Exsures counterpart (pk retained on a store refusal) is likewise derivable without the gold: the statement itself points the solver at deletion.py:276-281, and ordinary Python control flow says code after a raising call is not reached.

2. MECHANICAL SCREEN, RE-RUN NOT TRUSTED. swebench_unified.leakage.screen(model.py, get_backend('nagini'), row['patch'], row['problem_statement'], row['test_patch']) -> passed=True, hard_failures=[], warnings=[]. leakage.reviewer_directed(model.py) -> []. Computed spec_view sha256 = 0d1e63681205639c51fa5e7d130cb7c8cc67de09d171b5fc3735225f0e8d0142, matching the G-HYGIENE stamp (392 lines; impl region replaced by the elision placeholder). Gold changed_symbols = ['delete']; changed_lines = ['setattr(instance, model.`_meta`.pk.attname, None)']; changed_files = ['django/db/models/deletion.py'].

3. MANUAL SWEEPS OVER THE STRIPPED VIEW (specview.txt). (a) Repo/edit vocabulary -- setattr, attname, `_meta`, .pk., fast_delete, can_fast_delete, delete_batch, DeleteQuery, Collector, deletion.py, mark_for_rollback, transaction, savepoint, field_updates, django, 'instance.pk = None', line numbers 276/280/324: ZERO hits except line 1, the docstring title 'Twin-artifact model for django__django-11179' (the instance id, carried by every bundle). Normalized-whitespace containment of the gold line in the view: False. (b) Narration -- fix/bug/patch/regression/previously/used to/before this/mimic/copy: zero hits; the only matches for 'unchanged' (L156) and 'general path' / 'general multi-object removal path' (L12, L40) describe the axiomatized primitive as upstream code and contrast the optimized path with the general one -- both facts stated in the public issue ('models without any dependencies', i.e. the fast path) and neither localizing an edit. (c) Test leak -- test_patch def/class names test_fast_delete_instance_set_pk_none / test_fast_delete_joined_qs / test_fast_delete_qs plus Collector, assertIsNone, can_fast_delete: ZERO hits in the view. The spec speaks only domain vocabulary (PersistentObject, Database, remove_rows, identifier, RemovalBudget, CarriedOutRemoval, RefusedRemoval), never Django's.

4. LOAD-BEARINGNESS BY THE STRIP TEST (so I am not excusing narration that is actually doing the work). `adversary same-spec nagini django__django-11179` with atk.py = the bundle's own model_prepatch.py -> exit 0, 'SAME -- attack shares the bundle's exact specification' (markers.same_spec(model, prepatch) = True independently). `adversary weakness` on the same file -> exit 2, 'NOT-A-COUNTEREXAMPLE: attack does not verify' -- the spec REJECTS the pre-patch impl. `scripts/nagini_verify.sh model.py` -> 'Verification successful' (14.75s, exit 0). Then the decisive strip: I copied model_prepatch.py, DELETED the single line `Ensures(instance.pk is None)` (guarantee (5)) and nothing else, and ran the pinned verifier -> 'Verification successful' (14.24s, exit 0). So the PRE-patch impl verifies once clause (5) is removed and fails with it present: clause (5) is exactly the load-bearing discriminator, it cannot be dropped without the spec admitting the bug, and it is a restatement of the public 'It should be set to None after .delete() call'. This is the case where naming the cleared-PK behaviour is REQUIRED for faithfulness and is not a leak.

5. **CORE GATES THIS LEANS ON.** G-HYGIENE pass (my recomputed spec_view hash matches its stamp), G-GOLD pass and G-DIFF pass (prepatch fails) -- independently reproduced above by verifying model.py and by the weakness run on model_prepatch.py. G-LEAK pass reproduced by re-running screen() myself. (meta.json top-level region_hashes for axioms/pre/post differ from the G-HYGIENE-stamped values -- a stale top-level block; the spec_view hash that matters for THIS facet reproduces exactly against G-HYGIENE, and the discrepancy bears on hygiene bookkeeping, not on leakage. Flagged, not adopted.)

6. **NO BUNDLE FILE ADDRESSES THIS PANEL.** Grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, verdict.md for attacker|panel|reviewer|G-PANEL|NO-LEAKAGE|honest verdict|record this|you must submit|do not flag. Only hit: mapping.md:336, 'the divergent input the panel found is inside the sampled domain, not excluded' -- prose about a divergence panel's input coverage in the domain-sampling section, not an instruction about how to record a verdict. Nothing in this bundle told me what to submit.

**VERDICT:** NO-LEAKAGE. The only spec content that pins the gold edit is guarantee (5) (pk cleared to None on the no-dependency single-object removal path), which the public problem_statement states outright; the spec view names no file, module, symbol, attribute, line number, or test from the gold diff or the test patch.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.