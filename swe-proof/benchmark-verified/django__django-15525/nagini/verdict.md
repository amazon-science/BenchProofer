# P2 adversarial audit — django__django-15525

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 27 admissible attacks re-run of 27 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 27 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_23.py`, `atk_25.py`, `atk_26.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_4.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_22.py`, `atk_24.py`, `atk_27.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (27):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,8 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # PREPATCH: compute the natural key on the unassociated record.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,12 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # PRIOR COUNTEREXAMPLE (extra-dereference on the SAME record before the
+    # association): keeps the unpatched Model(**data).natural_key() line and
+    # ADDS the associated computation afterwards.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,12 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # extra dereference AFTER the gold sequence, on a fresh unassociated twin:
+    # initial and final association both match gold exactly.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    twin = ModelInstance(UNROUTED)
+    junk = KeyedRecord(twin, world)
     return keyed
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,14 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # GUARDED extra dereference on the UNROUTED record. The guard makes the
+    # producer's existence condition PROVABLE inside the branch
+    # (query_store(UNROUTED, default) == default == record_store), so this
+    # smuggles an unpatched-shaped dereference past (K).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if world.default_store == target_store:
+        stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # PARTIAL-DOMAIN: associate only on the target_store >= 0 sub-domain; the
+    # precondition only forbids target_store == UNROUTED, so -2 is admissible.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    if target_store >= 0:
+        obj.routed = target_store
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # FRAME RIVAL: compute the key on the unassociated record, then overwrite
+    # the two reported observables with the values the postcondition wants.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    keyed.routed = target_store
+    keyed.queried_store = target_store
     return keyed
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,9 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # WRONG STORE: obj._state.db = DEFAULT_DB_ALIAS instead of = db.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    obj.routed = world.default_store
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,13 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # CONTROL-FLOW EFFECT: correct observables, but the loader never returns.
+    # Refined, a patch that wedges deserialization in an unbounded loop.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    i = 0
+    while i >= 0:
+        i = i + 1
     return keyed
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # CONTROL-FLOW EFFECT: unbounded self-recursion before the gold sequence.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    junk = build_with_natural_key(target_store, world)
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # MINT A WORLD in which the unrouted fallback reaches the related record,
+    # and compute the key against that instead of the given deployment.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
-    keyed = KeyedRecord(obj, world)
+    forged = Deployment(world.record_store, world.record_store)
+    keyed = KeyedRecord(obj, forged)
     return keyed
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # IDENTITY SPLIT: associate one record, compute the key of a DIFFERENT,
+    # never-associated one.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
-    keyed = KeyedRecord(obj, world)
+    twin = ModelInstance(UNROUTED)
+    keyed = KeyedRecord(twin, world)
     return keyed
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,12 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # BOUNDARY / partial-domain on the FREE ambient default: associate only
+    # where the store being loaded into is not the ambient default one
+    # (`if db != DEFAULT_DB_ALIAS: obj._state.db = db`).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    if target_store != world.default_store:
+        obj.routed = target_store
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,13 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # UNGROUNDED-ORACLE ECHO: 'check' dereference success against the store
+    # the related record lives in (trivially true) instead of against the
+    # record's own association, then compute the key anyway.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    Assert(dereference_succeeds(world.record_store, world.default_store,
+                                world.record_store))
+    Assert(query_store(world.record_store, world.default_store) == target_store)
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # WORLD-FRAME: leave the record unassociated and instead redefine the
+    # ambient fallback store so the unrouted query reaches the related record.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    world.default_store = world.record_store
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,12 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
+    # As atk_4 but the guard is the routing predicate itself, which
+    # refinement.md says 'refines to nothing' when evaluated.
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if dereference_succeeds(UNROUTED, world.default_store, world.record_store):
+        stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    if world.default_store == world.record_store:
+        twin = ModelInstance(UNROUTED)
+        junk = KeyedRecord(twin, world)
     return keyed
     # impl-end
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    probe = ModelInstance(world.default_store)
+    if world.default_store == target_store:
+        junk = KeyedRecord(probe, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if query_store(UNROUTED, world.default_store) == world.record_store:
+        stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if world.default_store == target_store:
+        stale = KeyedRecord(obj, world)
+        return stale
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,17 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    n = 0
+    while n < 2:
+        Invariant(0 <= n and n <= 2)
+        Invariant(Acc(obj.routed, 1 / 2) and obj.routed == UNROUTED)
+        Invariant(Acc(world.default_store, 1 / 4) and Acc(world.record_store, 1 / 4))
+        Invariant(MustTerminate(2 - n))
+        if world.default_store == world.record_store:
+            junk = KeyedRecord(obj, world)
+        n = n + 1
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    obj.routed = UNROUTED
+    junk = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 22 — `atk_22.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,8 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    obj.routed = world.record_store + 1 - 1
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 23 — `atk_23.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    if world.default_store != target_store:
+        obj.routed = target_store
+    else:
+        obj.routed = UNROUTED
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
+    echo = ModelInstance(keyed.queried_store)
+    junk = KeyedRecord(echo, world)
     return keyed
     # impl-end
```

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if target_store != world.default_store:
+        stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,8 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    keyed = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
-    keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

Attack 27 — `atk_27.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,10 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
     obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
+    if world.record_store == world.default_store:
+        stale = KeyedRecord(obj, world)
     obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
     keyed = KeyedRecord(obj, world)
     return keyed
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
-    obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    # POSITIVE CONTROL: build the record ALREADY associated with the target
+    # store, compute its key, then release the association again (dead: the
+    # record is discarded once the key is in hand). Faithful-correct.
+    obj = ModelInstance(target_store)
     keyed = KeyedRecord(obj, world)
+    obj.routed = UNROUTED
     return keyed
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE / PROVENANCE. Judged artifact: model.py sha256=febbdea9830e258fe0b01f5de136392bb7c79024c7229989113fd84078e42fa3 (md5 c30aff1fa05fca2762b9b33375ec057e), which is the digest carried by G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK. CRITICAL: the recorded G-EQ/G-PANEL-1 fail ("BROKEN: atk_2.py verifies but its patch does not resolve") judged model.py sha256=453c339591edb03acf58b619fc1da142ae3ff308c779fc6df0027782224eec2b -- a DIFFERENT, PRE-REPAIR artifact. So this is a REPAIRED bundle and the stale BROKEN stamp does not transfer. Per the retained-attack-labels rule I did NOT import the prior verdict; I re-encoded the prior counterexample family from scratch and re-measured it. All work (fresh, empty at start).

ATTACK SUITE: 27 same-spec wrong/rival impls + 1 positive control + 1 vacuity control + 2 probes. ALL 31 passed `adversary same-spec nagini django__django-15525 <f>` (exit 0, spec byte-identical; only the impl region differs). Verifications run 3-concurrent as background jobs per the parallelism directive.

### Controls first
- pos_control.py (build ALREADY associated, compute key, then RELEASE the association) -> `adversary weakness` rc=0, verifies in 16s. Spec is not over-strong on a structurally different correct impl.
- vacuity_control.py (gold sequence + Assert(False)) -> rc=2, DOES NOT verify. The impl region is genuinely reachable, so every "rejected" below is a real refusal, not a vacuous guard (the guarded-self-call trap).
- overfit_probe.py (THREE associated key computations on one record) -> rc=0 verifies. The world's 1/4 shares do NOT cap dereference count, so the spec is not over-fitted to the gold's single deref.
- admiss_witness.py (asserts, on the ACTUAL params, target!=UNROUTED and record_store==target_store, plus (K) satisfiable for UNROUTED exactly on the coinciding half and NOT on the differing half) -> rc=0 verifies. The coinciding sub-domain the guarded attacks exploit is genuinely inhabited.

PREPATCH REPRODUCED: atk_1.py = model_prepatch.py shape (build UNROUTED, compute key directly, never associate) -> rc=2, rejected at the producer's precondition. The spec still senses the fix.

PRIOR COUNTEREXAMPLE FAMILY -- RE-ENCODED, ALL NOW DEAD. atk_2.py is the exact prior break (extra deref on the SAME record BEFORE the association, i.e. keeping the unpatched Model(**data).natural_key() line and adding the associated computation after). Command: `python -m swebench_unified.adversary weakness nagini django__django-15525 atk_2.py` -> rc=2, "NOT-A-COUNTEREXAMPLE: attack does not verify". The repair closed it. Also re-encoded and REJECTED (rc=2): atk_3 (extra deref AFTER gold on a fresh unassociated twin), atk_25 (partial-domain extra deref firing ONLY on target!=default, i.e. exactly the F2P scenario -- the prior atk_5 shape), atk_21 (transient unroute: associate, key, unroute, second key, return the first), atk_11 (identity split / twin record), atk_19 (guarded branch RETURNING the stale prepatch outcome), atk_20 (loop-shaped extra deref with full invariants + MustTerminate).

OTHER REJECTED (rc=2, all same-spec): atk_5 partial-domain assoc (target_store>=0 guard; -2 admissible), atk_6 restate-observables (refused for lack of permission -- the half share is load-bearing as refinement.md claims), atk_7 associate with ambient default (G-MUT mutant), atk_8 divergence (unbounded while -- MustTerminate(6) at the METHOD level rejects it), atk_9 unbounded self-recursion, atk_10 forge a convenient Deployment (refused: Requires(False) discharged, not assumed), atk_12 associate only where target!=default, atk_13 ungrounded-oracle echo (validate against world.record_store instead of the record's own association), atk_14 world-frame write (world.default_store = ... refused: read-only share), atk_23 explicit UNROUTED on the coinciding half, atk_26 ORDER RIVAL (key first, associate after; final state identical to gold) -> rejected, confirming refinement.md's load-bearing claim.

NINE CANDIDATES (rc=0: share spec AND verify) -- EVERY ONE had its faithful refined patch MATERIALIZED and RUN through the official harness. This is the part that decides the gate, and it was executed, not speculated. Driver: resolve_one.py calling swebench_unified.harness.run_resolve("django__django-15525", patch, run_id="sbu-geq-v33h-<tag>", timeout=3600, retries=2) under `docker`. All patches confirmed to apply cleanly at base_commit fbacaa58ffc5a62456ee68b90efa13957f761ce4 via `git -C <base worktree> apply --check` BEFORE running.

Results (9 runs, all completed=True applied=True): patch_atk_4.diff  -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_15.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_16.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_17.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_18.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_22.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_24.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_27.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_gold.diff   -> resolved=True  F2P 1/1  P2P 53/53  (oracle-direction control) No candidate's patch failed to resolve, so no verify-but-wrong witness exists.

(atk_15/18/27 refine to the same repo condition as atk_4: under the precondition record_store==target_store, the guards `world.default_store==target_store`, `dereference_succeeds(UNROUTED,default,record_store)`, `query_store(UNROUTED,default)==record_store` and `record_store==default_store` are all the single repo predicate `DEFAULT_DB_ALIAS == db`.)

WHY THE CANDIDATE FAMILY CANNOT BREAK IT -- the structural reason, which is the real finding. The only way an impl gets an EXTRA unpatched-shaped dereference past the producer's precondition (K) is to GUARD it by a condition that implies (K) for an UNROUTED record, i.e. query_store(UNROUTED, default)==record_store, i.e. default_store==record_store==target_store. Refined, that guard is `if DEFAULT_DB_ALIAS == db:` -- and on exactly that branch the extra dereference falls back to the ambient default store, which IS the store holding the related row, so it genuinely SUCCEEDS and raises nothing. The guard that makes the attack verifiable is the same guard that makes it correct. Confirmed by measurement in both directions: the UNGUARDED versions (atk_2, atk_3, atk_25, atk_21) are all rejected, and every guarded version that verifies also resolves with P2P 53/53 intact. The prior break exploited an unguarded extra deref; the repair (moving the existence condition onto the KeyedRecord PRODUCER, judged against a world that can be neither written nor minted) is precisely what forces the guard, and the guard collapses the attack into a correct impl.

A-LEG AUDIT (my assigned focus). No consumed axiom exists: `grep ContractOnly|sorry|Assume|@Predicate model.py` -> NONE; the axioms region is a comment only; meta.axioms == []. Both deep models are declared A-reference. I validated them INDEPENDENTLY (probe written from scratch, axprobe.py; does NOT import the bundle's axiom_check.py) against REAL Django imported from a fresh base_commit worktree (, `git worktree add --detach`), DATABASE_ROUTERS=[], real django.db.utils.ConnectionRouter with routers==[]: over all 120 alias<->id bijections x every association (None + all 5 stores) x every record_store, 4320 cases, query_store == real router.db_for_read(instance=rec) and dereference_succeeds == the real success criterion, MISMATCHES=0.

FALSITY CONTROL: the prepatch belief "always route to the ambient default" gives 80 mismatches on the same harness, so my probe can go red and the green is meaningful. I also read the real callees at base_commit and confirmed the correspondence chain by hand: _route_db (django/db/utils.py:222-238) returns instance._state.db if truthy else DEFAULT_DB_ALIAS == query_store; the forward FK descriptor's get_object -> get_queryset(instance=instance) -> _base_manager.db_manager(hints=hints).all() (related_descriptors.py:121-122, 165-168) routes the related-object query by the record's OWN _state.db, exactly as mapping.md 3.1 claims; and build_instance's try/except Model.DoesNotExist (base.py:340-346) wraps ONLY the get_by_natural_key lookup, so a raising natural_key() is genuinely uncaught -- which is what licenses (K) sitting on the producer and binding every key computation. Verified DEFAULT_DB_ALIAS == "default".

REFINEMENT.MD LEG AUDIT: every leg is R, A-reference, or unchanged-tail; NO kind-3. A1 (obj=Model(**data)) R, A2 (obj._state.db=db) R, A0 (Deployment) R, A3 (KeyedRecord == obj.natural_key()) R + A-reference, A4 (return / unchanged get_by_natural_key tail) R + unchanged-tail. The two A-reference legs' correspondence to the real callees HOLDS (measured above). KeyedRecord and Deployment are correctly characterized as NOT axioms: KeyedRecord carries a real verified body, and Deployment's Requires(False) is a precondition the verifier DISCHARGES -- I confirmed operationally via atk_10 (mint a world -> refused) and atk_14 (write the world -> refused). refinement.md's two "measured, not assumed" parenthetical claims are consistent with my independent results (atk_6 restate-observables refused for permission; atk_10 forge-world refused at the constructor). The one documented "refines to nothing" escape (evaluating query_store/dereference_succeeds in an Assert) is correctly scoped -- atk_13 takes that escape and is REJECTED, so the escape cannot be used to smuggle a dereference.

HONEST LIMITS. (1) 27 attacks is broad but not exhaustive; I concentrated on the A legs and the model<->patch correspondence as instructed, and on the guarded-extra-deref family that the prior break belonged to. (2) atk_22's patch is byte-identical to gold (the arithmetic reshape refines to the same op), so its resolve=True is a consistency check rather than an independent probe. (3) All resolve verdicts are single run_resolve calls with retries=2 built in; every one came back resolved=True with the full P2P set green, so there is no non-resolved verdict whose flakiness would need distinguishing.

VERDICT: SOUND. 31 same-spec builds; controls behave (positive verifies, vacuity fails, prepatch rejected, over-fit probe verifies); 18 wrong impls rejected; 9 verifying candidates ALL had faithful patches executed through the official harness and ALL resolve with F2P 1/1 and P2P 53/53, alongside a resolving gold control. Both A-reference legs independently re-validated against real Django with a red falsity control. No verify-but-not-correct witness found. NOTE FOR THE DRIVER: the recorded G-EQ fail on this cell is STALE -- it judged pre-repair sha 453c3395, not the current febbdea9, and its named counterexample atk_2 is now rejected (re-measured above).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 27 admissible attacks re-run of 27 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 27 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_23.py`, `atk_25.py`, `atk_26.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_4.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_22.py`, `atk_24.py`, `atk_27.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (27):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 27 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

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

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 23 — `atk_23.py` → rejected (same spec, does not verify — good)

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good)

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good)

Attack 27 — `atk_27.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -230,14 +230,11 @@
                                  world.record_store))
     # post-conditions-end
     # impl-start
-    # Build the instance (fresh: no store association yet).
-    obj = ModelInstance(UNROUTED)
-    # Associate it with the target store BEFORE computing the natural key, so
-    # the dereference inside natural-key computation routes to the target.
-    obj.routed = target_store
-    # Compute the natural key of the now-associated instance: the dereference it
-    # performs reaches the store the related record lives in, so the key — and
-    # with it the resolved outcome — exists.
+    # POSITIVE CONTROL: build the record ALREADY associated with the target
+    # store, compute its key, then release the association again (dead: the
+    # record is discarded once the key is in hand). Faithful-correct.
+    obj = ModelInstance(target_store)
     keyed = KeyedRecord(obj, world)
+    obj.routed = UNROUTED
     return keyed
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE / PROVENANCE. Judged artifact: model.py sha256=febbdea9830e258fe0b01f5de136392bb7c79024c7229989113fd84078e42fa3 (md5 c30aff1fa05fca2762b9b33375ec057e), which is the digest carried by G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK. CRITICAL: the recorded G-EQ/G-PANEL-1 fail ("BROKEN: atk_2.py verifies but its patch does not resolve") judged model.py sha256=453c339591edb03acf58b619fc1da142ae3ff308c779fc6df0027782224eec2b -- a DIFFERENT, PRE-REPAIR artifact. So this is a REPAIRED bundle and the stale BROKEN stamp does not transfer. Per the retained-attack-labels rule I did NOT import the prior verdict; I re-encoded the prior counterexample family from scratch and re-measured it. All work (fresh, empty at start).

ATTACK SUITE: 27 same-spec wrong/rival impls + 1 positive control + 1 vacuity control + 2 probes. ALL 31 passed `adversary same-spec nagini django__django-15525 <f>` (exit 0, spec byte-identical; only the impl region differs). Verifications run 3-concurrent as background jobs per the parallelism directive.

### Controls first
- pos_control.py (build ALREADY associated, compute key, then RELEASE the association) -> `adversary weakness` rc=0, verifies in 16s. Spec is not over-strong on a structurally different correct impl.
- vacuity_control.py (gold sequence + Assert(False)) -> rc=2, DOES NOT verify. The impl region is genuinely reachable, so every "rejected" below is a real refusal, not a vacuous guard (the guarded-self-call trap).
- overfit_probe.py (THREE associated key computations on one record) -> rc=0 verifies. The world's 1/4 shares do NOT cap dereference count, so the spec is not over-fitted to the gold's single deref.
- admiss_witness.py (asserts, on the ACTUAL params, target!=UNROUTED and record_store==target_store, plus (K) satisfiable for UNROUTED exactly on the coinciding half and NOT on the differing half) -> rc=0 verifies. The coinciding sub-domain the guarded attacks exploit is genuinely inhabited.

PREPATCH REPRODUCED: atk_1.py = model_prepatch.py shape (build UNROUTED, compute key directly, never associate) -> rc=2, rejected at the producer's precondition. The spec still senses the fix.

PRIOR COUNTEREXAMPLE FAMILY -- RE-ENCODED, ALL NOW DEAD. atk_2.py is the exact prior break (extra deref on the SAME record BEFORE the association, i.e. keeping the unpatched Model(**data).natural_key() line and adding the associated computation after). Command: `python -m swebench_unified.adversary weakness nagini django__django-15525 atk_2.py` -> rc=2, "NOT-A-COUNTEREXAMPLE: attack does not verify". The repair closed it. Also re-encoded and REJECTED (rc=2): atk_3 (extra deref AFTER gold on a fresh unassociated twin), atk_25 (partial-domain extra deref firing ONLY on target!=default, i.e. exactly the F2P scenario -- the prior atk_5 shape), atk_21 (transient unroute: associate, key, unroute, second key, return the first), atk_11 (identity split / twin record), atk_19 (guarded branch RETURNING the stale prepatch outcome), atk_20 (loop-shaped extra deref with full invariants + MustTerminate).

OTHER REJECTED (rc=2, all same-spec): atk_5 partial-domain assoc (target_store>=0 guard; -2 admissible), atk_6 restate-observables (refused for lack of permission -- the half share is load-bearing as refinement.md claims), atk_7 associate with ambient default (G-MUT mutant), atk_8 divergence (unbounded while -- MustTerminate(6) at the METHOD level rejects it), atk_9 unbounded self-recursion, atk_10 forge a convenient Deployment (refused: Requires(False) discharged, not assumed), atk_12 associate only where target!=default, atk_13 ungrounded-oracle echo (validate against world.record_store instead of the record's own association), atk_14 world-frame write (world.default_store = ... refused: read-only share), atk_23 explicit UNROUTED on the coinciding half, atk_26 ORDER RIVAL (key first, associate after; final state identical to gold) -> rejected, confirming refinement.md's load-bearing claim.

NINE CANDIDATES (rc=0: share spec AND verify) -- EVERY ONE had its faithful refined patch MATERIALIZED and RUN through the official harness. This is the part that decides the gate, and it was executed, not speculated. Driver: resolve_one.py calling swebench_unified.harness.run_resolve("django__django-15525", patch, run_id="sbu-geq-v33h-<tag>", timeout=3600, retries=2) under `docker`. All patches confirmed to apply cleanly at base_commit fbacaa58ffc5a62456ee68b90efa13957f761ce4 via `git -C <base worktree> apply --check` BEFORE running.

Results (9 runs, all completed=True applied=True): patch_atk_4.diff  -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_15.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_16.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_17.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_18.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_22.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_24.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_atk_27.diff -> resolved=True  F2P 1/1  P2P 53/53 patch_gold.diff   -> resolved=True  F2P 1/1  P2P 53/53  (oracle-direction control) No candidate's patch failed to resolve, so no verify-but-wrong witness exists.

(atk_15/18/27 refine to the same repo condition as atk_4: under the precondition record_store==target_store, the guards `world.default_store==target_store`, `dereference_succeeds(UNROUTED,default,record_store)`, `query_store(UNROUTED,default)==record_store` and `record_store==default_store` are all the single repo predicate `DEFAULT_DB_ALIAS == db`.)

WHY THE CANDIDATE FAMILY CANNOT BREAK IT -- the structural reason, which is the real finding. The only way an impl gets an EXTRA unpatched-shaped dereference past the producer's precondition (K) is to GUARD it by a condition that implies (K) for an UNROUTED record, i.e. query_store(UNROUTED, default)==record_store, i.e. default_store==record_store==target_store. Refined, that guard is `if DEFAULT_DB_ALIAS == db:` -- and on exactly that branch the extra dereference falls back to the ambient default store, which IS the store holding the related row, so it genuinely SUCCEEDS and raises nothing. The guard that makes the attack verifiable is the same guard that makes it correct. Confirmed by measurement in both directions: the UNGUARDED versions (atk_2, atk_3, atk_25, atk_21) are all rejected, and every guarded version that verifies also resolves with P2P 53/53 intact. The prior break exploited an unguarded extra deref; the repair (moving the existence condition onto the KeyedRecord PRODUCER, judged against a world that can be neither written nor minted) is precisely what forces the guard, and the guard collapses the attack into a correct impl.

A-LEG AUDIT (my assigned focus). No consumed axiom exists: `grep ContractOnly|sorry|Assume|@Predicate model.py` -> NONE; the axioms region is a comment only; meta.axioms == []. Both deep models are declared A-reference. I validated them INDEPENDENTLY (probe written from scratch, axprobe.py; does NOT import the bundle's axiom_check.py) against REAL Django imported from a fresh base_commit worktree (, `git worktree add --detach`), DATABASE_ROUTERS=[], real django.db.utils.ConnectionRouter with routers==[]: over all 120 alias<->id bijections x every association (None + all 5 stores) x every record_store, 4320 cases, query_store == real router.db_for_read(instance=rec) and dereference_succeeds == the real success criterion, MISMATCHES=0.

FALSITY CONTROL: the prepatch belief "always route to the ambient default" gives 80 mismatches on the same harness, so my probe can go red and the green is meaningful. I also read the real callees at base_commit and confirmed the correspondence chain by hand: _route_db (django/db/utils.py:222-238) returns instance._state.db if truthy else DEFAULT_DB_ALIAS == query_store; the forward FK descriptor's get_object -> get_queryset(instance=instance) -> _base_manager.db_manager(hints=hints).all() (related_descriptors.py:121-122, 165-168) routes the related-object query by the record's OWN _state.db, exactly as mapping.md 3.1 claims; and build_instance's try/except Model.DoesNotExist (base.py:340-346) wraps ONLY the get_by_natural_key lookup, so a raising natural_key() is genuinely uncaught -- which is what licenses (K) sitting on the producer and binding every key computation. Verified DEFAULT_DB_ALIAS == "default".

REFINEMENT.MD LEG AUDIT: every leg is R, A-reference, or unchanged-tail; NO kind-3. A1 (obj=Model(**data)) R, A2 (obj._state.db=db) R, A0 (Deployment) R, A3 (KeyedRecord == obj.natural_key()) R + A-reference, A4 (return / unchanged get_by_natural_key tail) R + unchanged-tail. The two A-reference legs' correspondence to the real callees HOLDS (measured above). KeyedRecord and Deployment are correctly characterized as NOT axioms: KeyedRecord carries a real verified body, and Deployment's Requires(False) is a precondition the verifier DISCHARGES -- I confirmed operationally via atk_10 (mint a world -> refused) and atk_14 (write the world -> refused). refinement.md's two "measured, not assumed" parenthetical claims are consistent with my independent results (atk_6 restate-observables refused for permission; atk_10 forge-world refused at the constructor). The one documented "refines to nothing" escape (evaluating query_store/dereference_succeeds in an Assert) is correctly scoped -- atk_13 takes that escape and is REJECTED, so the escape cannot be used to smuggle a dereference.

HONEST LIMITS. (1) 27 attacks is broad but not exhaustive; I concentrated on the A legs and the model<->patch correspondence as instructed, and on the guarded-extra-deref family that the prior break belonged to. (2) atk_22's patch is byte-identical to gold (the arithmetic reshape refines to the same op), so its resolve=True is a consistency check rather than an independent probe. (3) All resolve verdicts are single run_resolve calls with retries=2 built in; every one came back resolved=True with the full P2P set green, so there is no non-resolved verdict whose flakiness would need distinguishing.

VERDICT: SOUND. 31 same-spec builds; controls behave (positive verifies, vacuity fails, prepatch rejected, over-fit probe verifies); 18 wrong impls rejected; 9 verifying candidates ALL had faithful patches executed through the official harness and ALL resolve with F2P 1/1 and P2P 53/53, alongside a resolving gold control. Both A-reference legs independently re-validated against real Django with a red falsity control. No verify-but-not-correct witness found. NOTE FOR THE DRIVER: the recorded G-EQ fail on this cell is STALE -- it judged pre-repair sha 453c3395, not the current febbdea9, and its named counterexample atk_2 is now rejected (re-measured above).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

ATTACK GOAL: show the modeled function build_with_natural_key disagrees with the real callee django.core.serializers.base.build_instance on some Requires-satisfying, bridge-realizable input. Reference = base_commit worktree WITH patch.diff APPLIED (per instructions); base commit used only for the unchanged callees the A-references model. Result: could not break it. All work in /tmp; bundle verified untouched (git status --porcelain on benchmark-verified/django__django-15525/ empty at end; only /tmp copies of model.py / axiom_check.py / conformance_check.py were executed).

SETUP (fresh, independent of prior runs). Two new worktrees from the upstream repository at fbacaa58ffc5a62456ee68b90efa13957f761ce4:  (gold applied) and  (unpatched). The bundle's meta.json patch_diff is the literal string 'gold patch verbatim (applies cleanly at base_commit)' -- NOT the diff text -- so I took the gold patch from data/swe_bench_verified/test.jsonl instead and confirmed it is byte-identical to gold_15525.diff and applies clean. Patched body confirmed to be obj = Model(**data); obj._state.db = db; natural_key = obj.natural_key().

ORACLE DIRECTION CONFIRMED END-TO-END with the REAL F2P test. Applied the dataset test_patch to both worktrees and ran fixtures_regress.tests.NaturalKeyFixtureOnOtherDatabaseTests.test_natural_key_dependencies via tests/runtests.py with a TEST DEPENDENCIES:[] settings shim: PATCHED = 'Ran 1 test ... OK'; BASE = 'FAILED (errors=1)' with DeserializationError installing nk_with_foreign_key.json. So the patched tree is the correct faithfulness reference and the delta is real.

INDEPENDENT PROBE (written from scratch; does NOT import the bundle's conformance_check.py). Real Django, 5 sqlite :memory: stores (default/other/shard_a/shard_b/replica), real schema_editor tables, DATABASE_ROUTERS=[]. F2P model shape reproduced (Person + Book, Book.natural_key() == (name,) + self.author.natural_key()) with two PURE observation hooks (record self._state.db at key-computation time; record which author row the FK deref actually read). Every store holds a Person at every pk under a STORE-STAMPED name, so the resolved name identifies WHICH store the deref read -- this discriminates every misroute, not just default-vs-target. Diffed all three Ensures (routed, queried_store, deref_ok).
  - EXHAUSTIVE over the realizable Requires-domain: all 120 alias->id bijections x 5 target aliases x 3 author pks x {book pre-exists, not} = 3600 cases -> 0 disagreements. Covers all 5 distinct default_store ids and 720 cases with target_store == default_store (the coinciding sub-domain the bundle's own G-CONF-declared domain used to exclude; model.py leaves default_store FREE and claims the Ensures there, and it holds against real Django).
  - Plus 12000 randomized fuzz over the same domain -> 15600 total, 0 disagreements.
  - DISCRIMINATION SELF-TEST of my own harness: repointed at the UNPATCHED worktree (provenance guard bypassed deliberately) -> 15600/15600 disagreements (real routed=UNROUTED vs spec routed=target_store). My harness can go red, so the green is meaningful.
  - Exact F2P shape (db='other', author 'J.R.R. Tolkien'): real routed='other', deref read 'J.R.R. Tolkien', no exception -- all three Ensures agree.
  - EXTRA model shape not in the bundle's G-CONF: a NULLABLE-FK Book variant (author null=True, so no RelatedObjectDoesNotExist short-circuit), 6000 fuzz cases -> 0 disagreements.

CANDIDATE DIVERGENCES I CONSTRUCTED, AND WHY EACH FAILS TO BE ONE:
  1) PRE-CACHED FK -- the sharpest one, and it is genuinely a real divergence in raw behaviour. If `data` carries the related OBJECT (data={'name':..,'author':<Person instance>}) rather than author_id, Django caches it and NO store-routed query is issued at all: at target='other' with the cached author fetched from 'default', the real key is computed from 'auth::default::1' while the spec claims queried_store==target and the target's row was found. REFUTED on two independent grounds, both measured. (a) NOT REACHABLE: I intercepted build_instance and drove every repo caller (python, json, jsonl, yaml/pyyaml and xml Deserializers -- json/jsonl/yaml all delegate to PythonDeserializer, so python+xml is the complete set of call sites, confirmed by grep: only xml_serializer.py:276 and python.py:174 call it). Both build `data` with data[field.attname] = value from deserialize_fk_value, which returns a scalar pk, never an instance -- measured: every intercepted data dict had only int/str/NoneType values, 'Any data value that is a MODEL INSTANCE: False'. (b) OUTSIDE THE REQUIRES: when the cached related record is the target store's own row (the only case where Requires(record_store == target_store) is satisfied FOR THAT RECORD) the observables AGREE; the divergence appears only when the cached row resides in 'default'/'shard_a', i.e. exactly when record_store != target_store, which the precondition excludes. (c) OUTSIDE THE DELTA: patched and base produce the identical key here ('auth::default::1' both), so the patch is a no-op on this input -- it is not the modeled changed behaviour.
  2) UNBRIDGED `data` ARGUMENT variants. pk PRESENT in data -> the real function skips the whole natural-key branch (deref_attempted=False, no key computed, no exception): the model has no outcome to compare, and mapping.md scopes the model to the branch's interior; base and patched behave identically, so it is outside the delta. Null FK (author_id=None) -> RelatedObjectDoesNotExist, and dangling FK (pk=99) -> DoesNotExist; BOTH raise identically on base and patched, so again no delta, and both violate Requires(record_store == target_store) since no related record resides in the target.
  3) FALSY-BUT-NOT-NONE ALIAS ''. The real router is `if instance is not None and instance._state.db:` so '' is treated as no-association, whereas UNROUTED maps to None only. Measured with file-backed sqlite: Person.objects.using('').create() lands with _state.db=='default' -- the '' store is degenerate/unaddressable, so no related record can ever RESIDE in it, making Requires(record_store == target_store) unsatisfiable at target_store == id(''). Not a diverging input of the modeled function.
  4) UNCONFIGURED alias as db: real call raises ConnectionDoesNotExist; nothing can reside there either, so record_store == target_store is unsatisfiable.
  5) MULTI-HOP natural_key chain, testing 'the dereference is performed here, and nowhere else'. Built a 3-level Bk2 -> Author2 -> Country chain with a DIFFERENT Country row in each store. Patched: every hop routed to the target and read the target's rows ('Tolkien-other' then 'Shire-other'), no exception -- because hop 1's fetched row carries the _state.db it was read from, so hop 2 inherits it. Base: raised at hop 1. The one-deref abstraction is not too strong.
  6) CUSTOM DATABASE_ROUTERS is the one configuration where queried_store != target is achievable, but it is explicitly SCOPED OUT up front by mapping.md 3.1 / refinement.md ('no custom routers configured'), which is the framework default (global_settings DATABASE_ROUTERS = []) and the F2P configuration; the gold patch itself does not fix that case. Declared scoping of an unchanged framework mechanism is not spec drift.

CORROBORATING RE-RUNS (from /tmp copies, independently): model.py verifies (scripts/nagini_verify.sh, 'Verification successful', 8.28s). NON-VACUITY CONTROL: injecting Assert(False) at the top of the impl region FAILS ('Assertion False might not hold'), so the verification is not vacuous and the Requires are satisfiable. model_prepatch.py fails exactly at the claimed point ('The precondition of method KeyedRecord might not hold. Assertion dereference_succeeds(record.routed, world.default_store, world.record_store) might not hold'), so the spec senses the delta.

G-AX re-run: 'G-AX OK: routing deep model == real ConnectionRouter routing on all boundary store combinations and 20000 fuzz cases; no consumed axiom.' G-CONF re-run against my own patched worktree: status pass, n=100000, 3602 enumerated exhaustively, 0 disagreements, discrimination self-test pass. I also hand-verified the two A-references against source: db/utils.py:222-238 _route_db matches query_store clause for clause, and related_descriptors.py get_queryset(121-122)/get_object(165-168) confirm the hints={'instance': obj} routing and the qs.get success criterion. meta.json axioms == [], so there is no consumed-axiom trust point.

BOOKKEEPING DEFECT NOTED, NOT A FAITHFULNESS FINDING (flagging for the release gate, outside this gate's verdict): (a) meta.json['patch_diff'] holds the placeholder prose 'gold patch verbatim (applies cleanly at base_commit)' rather than the diff text; (b) meta.json['region_hashes'] does NOT match markers.region_hashes(model.py, nagini) -- post-conditions, pre-conditions, impl and spec_view all differ, i.e. the recorded hashes are stale relative to the current model.py (the pre-conditions hash matches an older old_15525_model.py and the post/impl hash matches a different older copy, consistent with a spec edit that did not refresh meta). This is systemic rather than instance-specific -- 425 of 500 nagini bundles mismatch on the same computation -- so it most likely reflects a hashing/serialization convention change in markers.py rather than tampering with this bundle. Neither affects the spec-vs-repo comparison this gate makes: I compared model.py's spec region as it actually reads against real patched Django.

CONCLUSION: on every input the spec's Requires admit and that real Django can realize, the modeled function's three Ensures agree with the real patched build_instance -- 15600 independent exhaustive+fuzz cases including the target==default sub-domain, 6000 additional nullable-FK cases, plus the bundle's own 100000 re-run, all 0 disagreements, with a harness proven able to go red. The candidate divergences I built are either unreachable through every repo call site, outside the precondition, or no-ops of the patch (hence outside the modeled delta). No diverging input: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (checked by json load -> False/None) and no RELAXED_LEAKAGE.md exists anywhere under benchmark-verified/django__django-15525/ (find -iname '*RELAX*' empty). So this is a straight leakage review, judged against problem_statement only, never hints_text.

WHAT THE SOLVER ACTUALLY SEES. Traced the exposure path rather than assuming it: eval/dataset.py:285 sets task.spec_view = adapter.spec_view(model); as_dict emits only spec_view + modeled_functions + float_encoding in spec modes. refinement.md and mapping.md are NOT in the solver's file set (no reference to them in eval/prompts.py or adapter.py) -- which matters, because refinement.md section A reproduces the gold hunk verbatim (`obj._state.db = db`). That is auditor-only and outside this gate. Reproduced the projection myself: spec_view sha256 61cc57743ea1cb6cf3c4f8f77a1721517a22ffa93a5dab7ddaf70cb3f03de671, idempotent (spec_view(spec_view(x))==spec_view(x)), ELISION_IMPL present, and the fix-carrying line `obj.routed = target_store` is absent from the view (grep -> False).

Also checked meta.modeled_functions, which IS solver-visible: eval/prompts.py:58-62 renders ONLY `model_symbol (<-> repo_symbol)` for nagini, so the `role` field's giveaway text ('The delta is an ORDERING - the association must exist BEFORE the key is computed') and `carrier_type`/`repo_location` never reach the prompt. The rendered repo_symbol `django.core.serializers.base.build_instance` is deliberate mode-1/2 localization and appears verbatim in the public traceback (base.py line 332, inside build_instance) anyway.

MECHANICAL SCREEN, RERUN BY ME. leakage.screen(model.py, nagini.language, patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Independently re-ran _NARRATION_RE over the spec view: zero hits (no bug/fix/patch/wrong/previously/regression). Grepped my own fix-ordering vocabulary; the only two hits are innocuous English -- 'rather than' in a scope sentence at line 48 and a substring false positive where 'the fix' matches 'the fixture' at line 199.

VOCABULARY CROSS-CHECK (my own, beyond the screen). Extracted every >=4-char identifier from the spec view and intersected with the gold patch text: the only overlaps are 'data', 'default', 'instance', 'model', 'name', 'natural', 'state' -- and I confirmed each of those seven also appears in the problem_statement, so none is a term the solver could not already see. Separately probed for patched repo symbols: `_state`, `state.db`, `build_instance`, `serializers`, `base.py`, `db_manager`, `get_by_natural_key`, `DEFAULT_DB_ALIAS`, `alias` -- ALL zero occurrences in the spec view, while most appear in the problem_statement. The spec view's whole vocabulary is deliberately re-abstracted (store/record/dereference/association), never Django's.

DISCRIMINATOR IS PUBLIC. The gold edit is 'set the store association before computing the natural key'. Every ingredient is in the public problem_statement: the title states loaddata fails on a non-default database when natural keys use foreign keys; the traceback walks natural_key() -> self.author.natural_key() -> related_descriptors.get_object -> qs.get -> 'Author matching query does not exist'; the reporter notes it works on the default DB and that the problem disappears if the data is already present in the default DB -- which is precisely 'the dereference was routed to the ambient default store'. The spec view narrates that same routing story at the abstract level and pins three observables (association at key-computation time, store queried, dereference succeeds) without naming _state.db or the ordering edit.

LOAD-BEARING (spec is not decorative narration). Ran the standard strip test via the shipped prepatch twin: same_spec(model.py, model_prepatch.py)=True (byte-identical spec signature; the diff is confined to the impl region), and `bash scripts/nagini_verify.sh` gives model.py 'Verification successful' (9.97s, exit 0) while model_prepatch.py FAILS with exactly the discriminating obligation -- pre.py:238 'The precondition of method KeyedRecord might not hold. Assertion dereference_succeeds(record.routed, world.default_store, world.record_store) might not hold' (exit 1). Also `adversary same-spec nagini django__django-15525` -> exit 0, 'SAME'. So the spec discriminates gold from pre-patch on the routing facet, which is the facet the public statement already describes.

INCIDENTAL FINDING (not leakage, flagged for the record). meta.json's frozen `region_hashes` is STALE relative to the live model.py: pre-conditions, post-conditions, impl and spec_view all mismatch what region_hashes() computes on the current file. I bisected the git history of model.py and the stamp matches revision 71649c6d0, two content revisions back. I diffed spec_view@71649c6d0 vs spec_view@live: the change is a strict STRENGTHENING (the old view required `default_store != record_store`, pinning the spec to the non-default case only; the live view drops that and leaves the ambient default free, adds the Deployment given-world carrier with an unsatisfiable constructor so the loader cannot mint favourable routing facts). Nothing leaky was introduced -- the added prose is all scope/permission reasoning in abstract vocabulary -- so this does not change my verdict, but the stamp should be re-frozen since a G-LEAK/G-HYGIENE stamp checked against region_hashes would be describing an artifact that no longer exists.

No file in this bundle addresses the reviewer or suggests a verdict: ran leakage.reviewer_directed() over all ten bundle .md/.py/.json files -> [] for every one.

VERDICT: NO-LEAKAGE. The spec view elides the fix-carrying assignment, uses no Django symbol touched by the patch, carries no narration vocabulary, reproduces no gold-diff line, and every gold-patch-overlapping word it does use is present in the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
