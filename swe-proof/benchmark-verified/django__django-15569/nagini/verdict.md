# P2 adversarial audit — django__django-15569

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_11.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.py`, `atk_10.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl produced a faithful refined patch that fails to resolve. All 4 CANDIDATEs (atk_8, atk_10, atk_12, atk_13) had their faithful patches materialized and RUN through the official harness (run_resolve, swe_bench_verified, docker oracle): all 4 resolved=True, both F2P tests pass, zero P2P failures. The spec's discriminating clauses -- store[name]==unregistered(), view[name]==inherited[name], reader_view[name]==reader_rest[name], plus the quantified frame and the two fractional-permission (read-only) carriers -- rejected every genuinely-wrong impl I could construct, including the prepatch bug and the previously-refuting reader-blind shape.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,6 +248,4 @@
     # post-conditions-end
     # impl-start
     store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,5 +249,4 @@
     # impl-start
     store[name] = unregistered()
     view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,7 +247,7 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
+    saved = inherited[name]  # type: int
     store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    view[name] = saved
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,6 +248,6 @@
     # post-conditions-end
     # impl-start
     store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    view[name] = unregistered()
+    reader_view[name] = unregistered()
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,7 +247,10 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
-    store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    if name >= 0:
+        store[name] = unregistered()
+        view[name] = inherited[name]
+        reader_view[name] = reader_rest[name]
+    else:
+        store[name] = unregistered()
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -250,4 +250,5 @@
     store[name] = unregistered()
     view[name] = inherited[name]
     reader_view[name] = reader_rest[name]
+    reader_view[other_name()] = unregistered()
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,5 +249,5 @@
     # impl-start
     store[name] = unregistered()
     view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    reader_view[name] = reader_view[name]
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,7 +247,10 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
-    store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    if view[name] == store[name]:
+        store[name] = unregistered()
+        view[name] = inherited[name]
+        reader_view[name] = reader_rest[name]
+    else:
+        store[name] = unregistered()
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,5 +249,10 @@
     # impl-start
     store[name] = unregistered()
     view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    if reader_view[name] == reader_rest[name]:
+        reader_view[name] = reader_rest[name]
+    elif reader_view[name] == store[name] or reader_view[name] == inherited[name]:
+        reader_view[name] = reader_rest[name]
+    else:
+        view[name] = inherited[name]
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,6 +247,8 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
+    reader_view[name] = reader_rest[name]
+    view[name] = inherited[name]
     store[name] = unregistered()
     view[name] = inherited[name]
     reader_view[name] = reader_rest[name]
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -250,4 +250,9 @@
     store[name] = unregistered()
     view[name] = inherited[name]
     reader_view[name] = reader_rest[name]
+    while name == name:
+        Invariant(store[name] == unregistered())
+        Invariant(view[name] == inherited[name])
+        Invariant(reader_view[name] == reader_rest[name])
+        pass
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,7 +247,9 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
+    old = store[name]  # type: int
     store[name] = unregistered()
     view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    if reader_view[name] == old:
+        reader_view[name] = reader_rest[name]
     # impl-end
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,7 +247,9 @@
     Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
     # post-conditions-end
     # impl-start
+    old = store[name]  # type: int
     store[name] = unregistered()
-    view[name] = inherited[name]
     reader_view[name] = reader_rest[name]
+    if view[name] == old:
+        view[name] = inherited[name]
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,6 +248,7 @@
     # post-conditions-end
     # impl-start
     store[name] = unregistered()
-    view[name] = inherited[name]
     reader_view[name] = reader_rest[name]
+    if inherited[name] == unregistered():
+        view[name] = unregistered()
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,6 +248,6 @@
     # post-conditions-end
     # impl-start
     store[name] = unregistered()
-    view[name] = inherited[name]
-    reader_view[name] = reader_rest[name]
+    view[name] = reader_rest[name]
+    reader_view[name] = inherited[name]
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN  15 attacks + positive control; all 16 confirmed byte-identical spec via `adversary same-spec`. Verifications run as concurrent background batches of 3 (JVM+Z3 per check). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15569 <path>`.

REJECTED (exit 2, spec rejected -- 11): atk_1 store-only PREPATCH BUG REPRODUCED (fails view[name]==inherited[name]); atk_2 reader-blind component-only (the prior pass's named counterexample -- re-encoded, now rejected on clause 2b); atk_3 same via local temp (`saved = inherited[name]`); atk_4 unconditional-unresolve (view/reader forced to unregistered() instead of the fallback); atk_5 partial-domain on the name token (correct only when name>=0); atk_6 control-flow/frame: gold writes + reader_view[other_name()] clobber (fails the quantified reader frame); atk_7 ungrounded-oracle echo (reader_view[name]=reader_view[name]); atk_9 branch-on-reader-value repair; atk_11 non-termination: gold post-state then a diverging `while name == name` loop -- rejected by MustTerminate(2) at the METHOD level, not merely by loop invariants; atk_14 PARTIAL DOMAIN on ancestor-shadowing (view repaired only when inherited[name]==unregistered() -- i.e. correct exactly on the case both F2P tests exercise, view-blind when a surviving level registers the name); atk_15 CARRIER CONFLATION (crossed inherited/reader_rest: view[name]=reader_rest[name], reader_view[name]=inherited[name]) -- rejected, so the spec does distinguish the two fallback ranges and does not admit a truncation/full-MRO mix-up.

CANDIDATES (exit 0: same-spec AND verifies -- 4) each had its faithful refined patch MATERIALIZED and RUN through run_resolve. Observed results:
- atk_8 (dead-branch on the OWN read-through law: repair only `if view[name] == store[name]`, else store-only). Faithful patch guards the clear on `cls.get_lookups().get(n) is cls.__dict__['class_lookups'].get(n)`. run_resolve => completed=True resolved=True attempts=1 flaky=False, F2P both pass, P2P 0 failures. RESOLVES.
- atk_10 (behaviour-preserving reshape: reversed write order + idempotent repeats). Patch = clear; delete; clear. => resolved=True attempts=1. RESOLVES.
- atk_12 (dead-branch on the ARBITRARY-READER law, captured pre-write: `old = store[name]` then repair reader only `if reader_view[name] == old`). Patch = reader-SELECTIVE invalidation, evicting a dependent class's cache only when its memoised entry IS the removed lookup. => resolved=True attempts=1. RESOLVES.
- atk_13 (dead-branch on the own-view law, captured pre-write). Patch = own-view-selective invalidation. => resolved=True attempts=1. RESOLVES.
Why these verify yet still resolve: their skipped branches are provably dead under the precondition's two read-through laws, so the verifier discharges them for free; the corresponding real guards are also never false on any state the F2P suite reaches, because the guard tests exactly the freshness the laws assert. Verification and correctness agree here -- no break.

**REFINEMENT.MD LEG AUDIT.** Legs 1,2,3,4,5,7,8 = R (type refinement); 6 and 9 = A-reference; no I legs, NO KIND-3 (unexpressible-changed-op) leg, and `meta.json` confirms `axioms: []` / no consumed @ContractOnly -- so the kind-3-free claim holds. The R legs' carriers check out against base_commit 884b4c27: store <-> cls.`__dict__`['class_lookups'] (query_utils.py:206-207,219), view <-> the lru_cache-memoised get_lookups (157-163), name <-> lookup_name. The fractional-permission legs are load-bearing, not decorative: `inherited` and `reader_rest` at Acc(...,1/2) forbid a verifying impl from repairing answers by editing the enclosing layer or the reader's own registrations (atk_15 confirms the carriers are not interchangeable).

A-LEG DEFECT FOUND (documentation/justification, NOT a gate break). refinement.md step 9, mapping.md "reader_view", and properties.py `weak-reader-blind-component-only` all assert as fact that the component-only rival -- `del cls.class_lookups[n]; cls.get_lookups.cache_clear()` (evict the requesting class's own memoised read, no subclass walk) -- "Does NOT resolve" and is "the exact shape of the F2P failure". I MEASURED IT: patch_componentonly.diff, run_resolve => completed=True RESOLVED=True (attempt 2/3, flaky=True), both F2P tests PASS, 0 P2P failures. The stated mechanism is wrong.

`functools.lru_cache` decorates the underlying FUNCTION, so cls and every subclass that does not override get_lookups SHARE ONE cache wrapper, and `cache_clear()` flushes the WHOLE cache -- not "cls's entry alone". Probed directly (probe_cache.py): `ForeignObject.get_lookups.__func__ is ForeignKey.get_lookups.__func__` => True; cache_info goes currsize=2 -> 0 on a single cls-level clear; the read through ForeignKey is repaired. Since test_lookups_caching registers on ForeignObject and reads through a ForeignKey -- which inherits ForeignObject's override and therefore its wrapper -- the component-only removal repairs the reader as a side effect and PASSES.

So the per-reader clause (2b) is a real, sound obligation about the model's distinct-carrier abstraction, and the reader IS a genuinely separate observable in general (a Field-level removal does NOT reach a ForeignObject-family reader, confirmed in probe_cache.py) -- but the specific resolve claim quoted three times in the bundle's prose is FALSE, and G-AX's 513-sequence 'third patch state' evidently models per-class cache entries rather than the shared wrapper Python actually gives. Advisory: correct the prose in refinement.md step 9, mapping.md, and the `weak-reader-blind-component-only` refinement note. This does not weaken the frozen spec (nothing verifying fails to resolve), so the G-EQ verdict stands at SOUND; it is a fidelity/justification error in the A-reference narrative that a future repair should fix rather than propagate.

**Evidence files:** atk_*.py (attacks), out_*.txt (weakness verdicts), patch_atk_{8,10,12,13}.diff + resolve_{10,12,13}.txt (executed resolves; atk_8 and component-only resolve output captured inline in the transcript), patch_componentonly.diff, probe_cache.py, qu_base.py (base_commit source), FINDINGS.md.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_11.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.py`, `atk_10.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl produced a faithful refined patch that fails to resolve. All 4 CANDIDATEs (atk_8, atk_10, atk_12, atk_13) had their faithful patches materialized and RUN through the official harness (run_resolve, swe_bench_verified, docker oracle): all 4 resolved=True, both F2P tests pass, zero P2P failures. The spec's discriminating clauses -- store[name]==unregistered(), view[name]==inherited[name], reader_view[name]==reader_rest[name], plus the quantified frame and the two fractional-permission (read-only) carriers -- rejected every genuinely-wrong impl I could construct, including the prepatch bug and the previously-refuting reader-blind shape.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED IN  15 attacks + positive control; all 16 confirmed byte-identical spec via `adversary same-spec`. Verifications run as concurrent background batches of 3 (JVM+Z3 per check). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15569 <path>`.

REJECTED (exit 2, spec rejected -- 11): atk_1 store-only PREPATCH BUG REPRODUCED (fails view[name]==inherited[name]); atk_2 reader-blind component-only (the prior pass's named counterexample -- re-encoded, now rejected on clause 2b); atk_3 same via local temp (`saved = inherited[name]`); atk_4 unconditional-unresolve (view/reader forced to unregistered() instead of the fallback); atk_5 partial-domain on the name token (correct only when name>=0); atk_6 control-flow/frame: gold writes + reader_view[other_name()] clobber (fails the quantified reader frame); atk_7 ungrounded-oracle echo (reader_view[name]=reader_view[name]); atk_9 branch-on-reader-value repair; atk_11 non-termination: gold post-state then a diverging `while name == name` loop -- rejected by MustTerminate(2) at the METHOD level, not merely by loop invariants; atk_14 PARTIAL DOMAIN on ancestor-shadowing (view repaired only when inherited[name]==unregistered() -- i.e. correct exactly on the case both F2P tests exercise, view-blind when a surviving level registers the name); atk_15 CARRIER CONFLATION (crossed inherited/reader_rest: view[name]=reader_rest[name], reader_view[name]=inherited[name]) -- rejected, so the spec does distinguish the two fallback ranges and does not admit a truncation/full-MRO mix-up.

CANDIDATES (exit 0: same-spec AND verifies -- 4) each had its faithful refined patch MATERIALIZED and RUN through run_resolve. Observed results:
- atk_8 (dead-branch on the OWN read-through law: repair only `if view[name] == store[name]`, else store-only). Faithful patch guards the clear on `cls.get_lookups().get(n) is cls.__dict__['class_lookups'].get(n)`. run_resolve => completed=True resolved=True attempts=1 flaky=False, F2P both pass, P2P 0 failures. RESOLVES.
- atk_10 (behaviour-preserving reshape: reversed write order + idempotent repeats). Patch = clear; delete; clear. => resolved=True attempts=1. RESOLVES.
- atk_12 (dead-branch on the ARBITRARY-READER law, captured pre-write: `old = store[name]` then repair reader only `if reader_view[name] == old`). Patch = reader-SELECTIVE invalidation, evicting a dependent class's cache only when its memoised entry IS the removed lookup. => resolved=True attempts=1. RESOLVES.
- atk_13 (dead-branch on the own-view law, captured pre-write). Patch = own-view-selective invalidation. => resolved=True attempts=1. RESOLVES.
Why these verify yet still resolve: their skipped branches are provably dead under the precondition's two read-through laws, so the verifier discharges them for free; the corresponding real guards are also never false on any state the F2P suite reaches, because the guard tests exactly the freshness the laws assert. Verification and correctness agree here -- no break.

**REFINEMENT.MD LEG AUDIT.** Legs 1,2,3,4,5,7,8 = R (type refinement); 6 and 9 = A-reference; no I legs, NO KIND-3 (unexpressible-changed-op) leg, and `meta.json` confirms `axioms: []` / no consumed @ContractOnly -- so the kind-3-free claim holds. The R legs' carriers check out against base_commit 884b4c27: store <-> cls.`__dict__`['class_lookups'] (query_utils.py:206-207,219), view <-> the lru_cache-memoised get_lookups (157-163), name <-> lookup_name. The fractional-permission legs are load-bearing, not decorative: `inherited` and `reader_rest` at Acc(...,1/2) forbid a verifying impl from repairing answers by editing the enclosing layer or the reader's own registrations (atk_15 confirms the carriers are not interchangeable).

A-LEG DEFECT FOUND (documentation/justification, NOT a gate break). refinement.md step 9, mapping.md "reader_view", and properties.py `weak-reader-blind-component-only` all assert as fact that the component-only rival -- `del cls.class_lookups[n]; cls.get_lookups.cache_clear()` (evict the requesting class's own memoised read, no subclass walk) -- "Does NOT resolve" and is "the exact shape of the F2P failure". I MEASURED IT: patch_componentonly.diff, run_resolve => completed=True RESOLVED=True (attempt 2/3, flaky=True), both F2P tests PASS, 0 P2P failures. The stated mechanism is wrong.

`functools.lru_cache` decorates the underlying FUNCTION, so cls and every subclass that does not override get_lookups SHARE ONE cache wrapper, and `cache_clear()` flushes the WHOLE cache -- not "cls's entry alone". Probed directly (probe_cache.py): `ForeignObject.get_lookups.__func__ is ForeignKey.get_lookups.__func__` => True; cache_info goes currsize=2 -> 0 on a single cls-level clear; the read through ForeignKey is repaired. Since test_lookups_caching registers on ForeignObject and reads through a ForeignKey -- which inherits ForeignObject's override and therefore its wrapper -- the component-only removal repairs the reader as a side effect and PASSES.

So the per-reader clause (2b) is a real, sound obligation about the model's distinct-carrier abstraction, and the reader IS a genuinely separate observable in general (a Field-level removal does NOT reach a ForeignObject-family reader, confirmed in probe_cache.py) -- but the specific resolve claim quoted three times in the bundle's prose is FALSE, and G-AX's 513-sequence 'third patch state' evidently models per-class cache entries rather than the shared wrapper Python actually gives. Advisory: correct the prose in refinement.md step 9, mapping.md, and the `weak-reader-blind-component-only` refinement note. This does not weaken the frozen spec (nothing verifying fails to resolve), so the G-EQ verdict stands at SOUND; it is a fidelity/justification error in the A-reference narrative that a future repair should fix rather than propagate.

**Evidence files:** atk_*.py (attacks), out_*.txt (weakness verdicts), patch_atk_{8,10,12,13}.diff + resolve_{10,12,13}.txt (executed resolves; atk_8 and component-only resolve output captured inline in the transcript), patch_componentonly.diff, probe_cache.py, qu_base.py (base_commit source), FINDINGS.md.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION IDENTITY: `adversary same-spec nagini django__django-15569 atk.py` on an unmodified copy of model.py => exit 0 ("SAME — attack shares the bundle's exact specification"). model.py verifies under the pinned verifier (`scripts/nagini_verify.sh`, "Verification successful", 15.2s). model_prepatch.py FAILS on exactly the discriminating clause: `model_prepatch.py:218 Postcondition... Assertion (view[name] == inherited[name]) might not hold` — so the spec is sharply localized to the added `cls._clear_cached_lookups()` and is not vacuous.

**REFERENCE USED:** /tmp worktree of django_django.git at base_commit 884b4c27f5 with the gold hunk (`+cls._clear_cached_lookups()` in `RegisterLookupMixin._unregister_lookup`) APPLIED, per the task rule that the modelled function's reference is the patched tree. Base commit used only for the untouched collaborators (`get_lookups` lru_cache, `merge_dicts`, `subclasses`, `_clear_cached_lookups`, `ForeignObject.get_lookups`).

*** ENVIRONMENT TRAP THAT ALMOST PRODUCED A FALSE UNFAITHFUL — the main finding of this run *** My first three independent harnesses reported large, deterministic, reproducible disagreement counts (2614, 1756, 1272, and 4185 across exotic hierarchies), all of the shape `oracle view[name] = <the removed local token>` vs model `inherited[name]` — i.e. textbook PRE-PATCH stale-cache behavior, exactly the reject lane. Every one was an artifact. Root cause: top-level `django` resolved to an unrelated Django 3.2 alpha in which ``_unregister_lookup`` has no cache clear, and that copy took precedence over the working directory.

So ANY `python script.py` measured the wrong, unpatched Django, while a stdin repro (`python - <<EOF`, where sys.path[0] is the working directory) measured the worktree. That is why hand-repros of the very same inputs always agreed while the scripts always "disagreed". How it was caught: I ran MY OWN driver loop against the BUNDLE'S OWN unmodified 4-level hierarchy as a control — the bundle's full script passes 100022 inputs there, so any disagreement had to be mine. It reported 366/415. Diagnostic `python which.py` vs stdin showed `django:   PATCHED? False` vs `  PATCHED? True`. With `PYTHONPATH=<worktree>` the same control went to 0/415 and every prior "disagreement" evaporated.

Two genuine bugs in my own harnesses were also found and fixed en route: `delattr(models.Field,'class_lookups')` DESTROYS Django's 17 builtin lookups process-wide and poisons all later cases; and `mappingproxy.pop` AttributeError. Consistent with memory: host/environment defects read as spec defects, and a retained attack label must not carry the oracle verdict.

### EVIDENCE AFTER FIXING THE ENVIRONMENT (all with PYTHONPATH forced to the patched worktree):
1. Bundled G-CONF re-run in my own worktree: exit 0, 100022 Requires-satisfying inputs, 0 disagreements; 34675 inherited-shadowing inputs; 367/420 prepatch controls discriminating with the other 53 PROVEN degenerate (ancestor registers the removed name to the SAME lookup object, so the real repo's gold and prepatch post-states genuinely coincide); 142/142 over-eager controls; 277/277 component-only controls (276 inputs where the reader reports the local registration) — the per-reader clause has real observable content.
2. Bundled G-AX re-run: exit 0; gold / prepatch / component-only all witnessed, 513 sequences witnessing the component-only state, 2 of 5 read-range shapes refuting a full-MRO binding.
3. MY INDEPENDENT ATTACK on hierarchy families the bundle NEVER generates (its scenarios hardcode a linear 4-class chain with target at index 2), reusing the bundle's trusted priming/probing/abstraction/oracle-call and swapping only the class graph: DIAMOND with target on one side (reader merges a sibling the target does not), DIAMOND with target as the join class, COUSIN reader that does NOT reach the target, and READER-IS-AN-ANCESTOR. 4860 inputs total (1215 each), reader_sees_local 885+885, inherited_shadowing 224/407/407/407 => 0 DISAGREEMENTS. Multiple inheritance / MRO-merge order does not break `view[name]==inherited[name]` or `reader_view[name]==reader_rest[name]`.
4. PRECONDITION STRENGTH (the real over-strong risk): 4000 deliberately perturbed reachable states (removing the other_name() registration, forcing an ancestor to register the removed name to the same variant) => 4000/4000 ADMITTED, zero excluded by any clause, and zero admitted-but-disagreeing. Both F2P shapes and all 5 read-range shapes admitted with 0 errors. The Requires are satisfied by the states the F2P tests actually produce, so the spec is not over-strong.
5. Hand-confirmed the two semantic claims that would make the spec over-claim if wrong: (a) RESURFACING is EXACT, not absence — ancestor P registers 'zz'->LkA, child C registers 'zz'->LkB; after `C._unregister_lookup` a read of C returns LkA (so `view[name]==inherited[name]`, and the stronger `view[name]==unregistered()` would be UNSATISFIABLE by the real code, vindicating the fallback formulation); (b) the ForeignObject TRUNCATION is honoured — 'zz' registered on Field is NOT visible to ForeignObject (`'zz' in FO.get_lookups()` False), and after removing FO's own 'zz' the read is None rather than Field's LkA, so binding `inherited` to the full MRO would invert the claim on that family. mapping.md binds it to the probed read range, which is correct.
6. Also confirmed the load-bearing lru_cache fact: `get_lookups` is `@functools.lru_cache` on the classmethod, so `B.get_lookups.cache_clear()` clears the SHARED wrapper (currsize 2->0) while each class is a DISTINCT cache KEY holding a distinct merged dict — which is why the `subclasses(cls)` walk is needed and why `reader_view` is a genuinely separate observable held at full permission.

**CONCLUSION:** no diverging input exists between the modelled `remove_registration` and the real patched `_unregister_lookup` on any reachable state I could construct, including hierarchy families outside the bundle's generator. `inherited`/`reader_rest` at half permission match the real removal touching only `cls.class_lookups` (frame verified: no change to either carrier across all runs). Verdict FAITHFUL — the spec does not drift from and is not stronger than real repo behavior. Anyone re-auditing this cell must pin the import to the base_commit worktree (or run the probe via stdin); an unpatched Django reached by any other route silently substitutes itself and manufactures a full set of prepatch-shaped 'divergences'.

**SPEC REGION IDENTITY:** `adversary same-spec nagini django__django-15569 atk.py` on an unmodified copy of model.py => exit 0 ("SAME — attack shares the bundle's exact specification"). model.py verifies under the pinned verifier (`scripts/nagini_verify.sh`, "Verification successful", 15.2s). model_prepatch.py FAILS on exactly the discriminating clause: `model_prepatch.py:218 Postcondition... Assertion (view[name] == inherited[name]) might not hold` — so the spec is sharply localized to the added `cls._clear_cached_lookups()` and is not vacuous.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE / IDENTITY. Judged the consumer spec view I regenerated myself: markers.spec_view(model.py, get_backend('nagini')) -> leak15569_specview.txt, 251 lines; diff against model.py shows the ONLY difference is the 3-line impl region replaced by '...  # implementation elided — supplied by the consumer', so the elision is present and nothing else is hidden. model.py sha256 = ad86deb5951da9073f38e921999aeace4c8e77cdf390fdd57d499d8f7da03553, which equals meta.gates['G-LEAK'].sources['model.py'] exactly, so I judged the same bytes the G-LEAK gate did. Positive control: `python -m swebench_unified.adversary same-spec nagini django__django-15569 <bundle model.py copy>` -> exit 0, 'SAME — attack shares the bundle's exact specification'.

**NO RELAXATION IN THIS BUNDLE.** `'relaxed_leakage' in meta` -> False (top keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version); no RELAXED_LEAKAGE.md (ls | grep -i relax -> empty). So this is a plain strict-mode review, no inherited disposition to re-derive.

**NO REVIEWER-DIRECTED CONTENT.** Ran leakage.reviewer_directed() over every non-directory file in the bundle (model.py, model_prepatch.py, refinement.md, mapping.md, properties.py, axiom_check.py, conformance_check.py, meta.json, verdict.md, pbt_result.json, plus one transient build artifact) -> 'clean' on all four rules for all 11 files. Hand-grepped additionally for 'you are/should/must', 'your verdict', 'the honest/correct verdict', 'submit', 'NO-LEAKAGE', 'record... verdict', 'do not report/flag', 'ignore previous' -> the only hits are inside verdict.md, which is the pipeline's own record of PRIOR audit-role outcomes (it reports past statuses; it does not address me or prescribe a recording). Nothing in the bundle tells me what to submit.

MECHANICAL SCREEN (re-derived, not trusted). leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. I re-derived its inputs from data/swe_bench_verified/test.jsonl: changed_lines = ['cls.`_clear_cached_lookups`()']; changed_files = ['django/db/models/query_utils.py']; changed_symbols = {'unregister_lookup'}. That sole changed symbol is exempt under the screen's own rule ONLY because it is public — and I confirmed that independently: the problem_statement literally reads 'RegisterLookupMixin.`_unregister_lookup`() should clear the lookup cache' and 'in the `_unregister_lookup` method,... the cache is not cleared, which should be done, as it is done in register_lookup'. So the exemption is not taken on faith.

VOCABULARY SWEEP of the 251-line spec view (case-insensitive counts): clear_cached 0, cached_lookups 0, class_lookups 0, get_lookups 0, cache_clear 0, query_utils 0, lru 0, functools 0, merge_dicts 0, foreignobject 0, registerlookupmixin 0, mro 0, 'cls.' 0, '`_unregister`' 0, 'register_lookup' 0, 'subclasses(' 0, stale 0, invalidat 0, field 0, transform 0, constraint 0, schema 0, test 0. The 14 'unregister' hits are all the model's own carrier sentinel `unregistered()` (a Dict-state value, not the repo symbol) — verified line by line. 'django' occurs twice, both in the instance-id string on docstring line 1 ('Twin-artifact model for django__django-15569'), the task identifier the consumer already has. 'lookup' occurs once, as the generic English 'derived lookup view' (line 10), which is weaker than the problem_statement's own 'the lookup cache'.

**DIRECTION-OF-LEAKAGE CHECK.** The public problem_statement already discloses the discriminator outright: which method (`_unregister_lookup`), which file (query_utils.py, by URL), what to do (clear the cache), and the precedent (as register_lookup does). Substring checks on the lowercased statement: '`_unregister_lookup`' True, 'cache' True, 'clear' True, 'register_lookup' True, 'not cleared' True, 'query_utils' True. The spec view is strictly MORE abstract than the statement — generic 'registry component / local backing store / enclosing registration layer / derived memoised view', zero Django symbols. Nothing in the view narrows the solver's search beyond what the public issue gives.

LOAD-BEARING (strip-the-narration) MEASUREMENT — run even though no relaxation is claimed, because the shipped model.py is a NEWER revision than the one the recorded Role-4 note in verdict.md reviewed (that note cites 505f2171.../169 lines; the live file is ad86deb5.../251 lines and adds the reader_view/reader_rest carriers), so I re-measured rather than inheriting. Built gold_nc.py and pre_nc.py = model.py / model_prepatch.py with the module docstring collapsed to '\"\"\"m\"\"\"' and EVERY non-marker comment tokenize-deleted (10 region markers preserved; 0 prose comments left). `bash scripts/nagini_verify.sh gold_nc.py` -> exit 0, 'Verification successful' (16.03s). `bash scripts/nagini_verify.sh pre_nc.py` -> exit 1, 'pre_nc.py:64:13: Postcondition of remove_registration might not hold.

Assertion (view[name] == inherited[name]) might not hold.' So with 100% of the narration removed the spec still verifies against the gold impl and still REJECTS the PRE-patch impl on exactly the clause G-DIFF reports. The discriminator is carried entirely by the formal clauses Ensures(view[name] == inherited[name]) and Ensures(reader_view[name] == reader_rest[name]) over the model's own abstract carriers — no comment in the view is load-bearing for the leak question, and none names the edit.

**NARRATION CHECK.** The `_NARRATION` vocabulary (bug/fix/patch/stale/previously/incorrectly/wrong/broken/regression/off-by-one) does not fire anywhere in the view. The failing shape is described as an unlabelled behavioural alternative ('a removal that updates only the local store but leaves memoised answers reporting the old answer', 'view-blind removal (store-only)') — behaviour under specification, not an edit narrative, and downstream of a problem_statement that already says the cache is not cleared.

INCIDENTAL, NOT A LEAKAGE FINDING (recorded so it is on the record for the integrity/hygiene lane): meta.json's TOP-LEVEL region_hashes block is stale against the shipped model.py — recomputed markers.region_hashes gives axioms c56513d9..., pure f1f1b953..., pre-conditions 7b50e464..., post-conditions 09d8b666..., impl 6b7f98e7..., spec_view 9fe47775..., whereas meta records 3f157be9/a9b31e0c/242e444d/26f58f2e/19b2eaa0/e80ae03c — all six differ (note this also differs from the earlier recorded note, which found `axioms` agreeing, consistent with model.py having moved again since). The gate that actually consumes the model bytes for MY question, G-LEAK, records the correct live sha (ad86deb5...), and I regenerated the spec view from model.py directly rather than trusting any recorded hash, so this has no bearing on leakage. Also noting for context (not my axis): verdict.md records G-PANEL-1 fail and an older G-PANEL/G-EQ source sha; a weakness or faithfulness defect is a different axis and would not become a leak either way — I did not re-adjudicate it.

**CONCLUSION:** NO-LEAKAGE. The current spec view reproduces no gold-patch line, contains no diff marker, names no patched file or module path, contains no identifier or comment embedding a patched repo symbol outside the public problem_statement, and carries no bug/fix narration; the discriminator is formal-clause-borne (proved by the narration-stripped verify/reject pair above), and independently the gold edit's content is already fully public in the problem_statement, so the view leaks nothing the solver does not already have.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
