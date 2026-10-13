# P2 adversarial audit — django__django-15814

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -223,10 +223,8 @@
     prim_set[primary_pk] = primary_pk
     must_include[prim_key] = prim_set
 
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
+    # The traversed model is taken as the relation hands it over.
     cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
 
     # Passing through the relation records the reference attribute on the model
     # the traversal came from, and the traversed model's own primary key.
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -243,6 +243,7 @@
     seen = {}  # type: Dict[int, Dict[int, int]]
     leaf_set = {}  # type: Dict[int, int]
     leaf_set[chosen_attr] = chosen_attr
+    leaf_set[primary_pk] = primary_pk
     seen[rel_key] = leaf_set
 
     # Merge the passthrough requirements into the reported (`seen`) accumulator,
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,14 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
-    prim_key = canonical_of(canonical, primary)  # type: int
-    rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[related] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[primary] = prim_set
     return seen
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,20 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
+    if related != rel_key:
+        alias_set = {}  # type: Dict[int, int]
+        alias_set[related_pk] = related_pk
+        seen[related] = alias_set
     return seen
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,17 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    if related != rel_key:
+        rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,42 +212,20 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
     must_include = {}  # type: Dict[int, Dict[int, int]]
-    prim_set = {}  # type: Dict[int, int]
-    prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
+    shared = {}  # type: Dict[int, int]
+    shared[primary_pk] = primary_pk
+    must_include[prim_key] = shared
+    cur_model = canonical_of(canonical, related)  # type: int
+    shared[ref_attr] = ref_attr
+    shared[related_pk] = related_pk
+    must_include[cur_model] = shared
     seen = {}  # type: Dict[int, Dict[int, int]]
     leaf_set = {}  # type: Dict[int, int]
     leaf_set[chosen_attr] = chosen_attr
     seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
     if cur_model in seen:
         target_set = seen[cur_model]  # type: Dict[int, int]
         source_set = must_include[cur_model]  # type: Dict[int, int]
@@ -266,7 +244,5 @@
         seen[prim_key] = prim_target
     else:
         seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
     return seen
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -212,61 +212,16 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -212,61 +212,22 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
+    decl = attr_owner[chosen_attr]  # type: int
+    if decl != rel_key and decl != prim_key and decl != related and decl != primary:
+        junk = {}  # type: Dict[int, int]
+        junk[related_pk] = related_pk
+        junk[chosen_attr] = chosen_attr
+        seen[decl] = junk
     return seen
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,20 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
+    i = 0  # type: int
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,16 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    a_set = {}  # type: Dict[int, int]
+    a_set[related_pk] = related_pk
+    a_set[chosen_attr] = chosen_attr
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = a_set
+    seen[rel_key] = prim_set
     return seen
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,16 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
-    rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    decl_key = canonical_of(canonical, attr_owner[chosen_attr])  # type: int
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[decl_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -230,10 +230,6 @@
 
     # Passing through the relation records the reference attribute on the model
     # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
     pk_set = {}  # type: Dict[int, int]
     pk_set[related_pk] = related_pk
     must_include[cur_model] = pk_set
@@ -261,8 +257,7 @@
         prim_source = must_include[prim_key]  # type: Dict[int, int]
         if primary_pk in prim_source:
             prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
+        prim_target[ref_attr] = ref_attr
         seen[prim_key] = prim_target
     else:
         seen[prim_key] = must_include[prim_key]
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,17 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
-    prim_key = canonical_of(canonical, primary)  # type: int
-    rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    prim_key = canonical_of(canonical, canonical_of(canonical, primary))  # type: int
+    rel_key = canonical_of(canonical, canonical_of(canonical, related))  # type: int
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    if chosen_attr in attr_owner:
+        rel_set[chosen_attr] = chosen_attr
+    rel_set[related_pk] = related_pk
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,17 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
-    prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    if primary != prim_key:
+        prim_set[primary_pk] = primary_pk
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,61 +212,15 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
-    prim_set = {}  # type: Dict[int, int]
-    prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
     seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    shared = {}  # type: Dict[int, int]
+    shared[related_pk] = related_pk
+    shared[chosen_attr] = chosen_attr
+    shared[primary_pk] = primary_pk
+    shared[ref_attr] = ref_attr
+    seen[rel_key] = shared
+    seen[prim_key] = shared
     return seen
     # impl-end
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -212,61 +212,22 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
-    # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
-
-    # `must_include`: the passthrough requirements, keyed by canonical identity.
-    # The primary model contributes its own primary key.
-    must_include = {}  # type: Dict[int, Dict[int, int]]
+    seen = {}  # type: Dict[int, Dict[int, int]]
+    decl = attr_owner[chosen_attr]  # type: int
+    if decl != related and decl != primary:
+        junk = {}  # type: Dict[int, int]
+        junk[related_pk] = related_pk
+        junk[chosen_attr] = chosen_attr
+        seen[decl] = junk
+    rel_set = {}  # type: Dict[int, int]
+    rel_set[related_pk] = related_pk
+    rel_set[chosen_attr] = chosen_attr
+    seen[rel_key] = rel_set
     prim_set = {}  # type: Dict[int, int]
     prim_set[primary_pk] = primary_pk
-    must_include[prim_key] = prim_set
-
-    # The traversed model is normalized to its canonical identity before
-    # anything is keyed by it.
-    cur_model = related  # type: int
-    cur_model = canonical_of(canonical, cur_model)
-
-    # Passing through the relation records the reference attribute on the model
-    # the traversal came from, and the traversed model's own primary key.
-    if prim_key in must_include:
-        from_set = must_include[prim_key]  # type: Dict[int, int]
-        from_set[ref_attr] = ref_attr
-        must_include[prim_key] = from_set
-    pk_set = {}  # type: Dict[int, int]
-    pk_set[related_pk] = related_pk
-    must_include[cur_model] = pk_set
-
-    # `seen`: the restricted requirement (the chosen attribute) keyed by the
-    # related model's canonical identity.
-    seen = {}  # type: Dict[int, Dict[int, int]]
-    leaf_set = {}  # type: Dict[int, int]
-    leaf_set[chosen_attr] = chosen_attr
-    seen[rel_key] = leaf_set
-
-    # Merge the passthrough requirements into the reported (`seen`) accumulator,
-    # per model key: a model recorded in `must_include` folds its required
-    # attributes into the model's reported set under the same key.
-    if cur_model in seen:
-        target_set = seen[cur_model]  # type: Dict[int, int]
-        source_set = must_include[cur_model]  # type: Dict[int, int]
-        if related_pk in source_set:
-            target_set[related_pk] = source_set[related_pk]
-        seen[cur_model] = target_set
-    else:
-        seen[cur_model] = must_include[cur_model]
-    if prim_key in seen:
-        prim_target = seen[prim_key]  # type: Dict[int, int]
-        prim_source = must_include[prim_key]  # type: Dict[int, int]
-        if primary_pk in prim_source:
-            prim_target[primary_pk] = prim_source[primary_pk]
-        if ref_attr in prim_source:
-            prim_target[ref_attr] = prim_source[ref_attr]
-        seen[prim_key] = prim_target
-    else:
-        seen[prim_key] = must_include[prim_key]
-
-    # The reported per-model mapping (keyed by canonical model identity).
+    prim_set[ref_attr] = ref_attr
+    seen[prim_key] = prim_set
     return seen
     # impl-end
```

Attack 17 — `atk_vacuity.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,6 +212,7 @@
                     not (primary in Result())))
     # post-conditions-end
     # impl-start
+    Assert(False)
     # Canonical identities under which the two participating models report.
     prim_key = canonical_of(canonical, primary)  # type: int
     rel_key = canonical_of(canonical, related)  # type: int
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15814.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader works out which database columns to fetch for an optimized
  query that pulls a related object alongside the primary one and restricts the
  related object to a chosen subset of its stored attributes, it accumulates,
  per participating model, the set of attribute names that must be fetched.
  The mapping it reports is consumed WHOLE by the step that turns it into
  columns: every bucket it reports is read, not only the related model's.

  Two models participate in the slice modelled here: the query's own PRIMARY
  model, and the RELATED model reached from it through one reference attribute
  the primary model stores.

  Three kinds of attribute name are recorded while the related model is
  traversed:

    (1) the *passthrough* requirements on the primary side — the primary
        model's own primary-key attribute and the reference attribute it stores
        for the traversed relation. Even though the caller restricted only the
        related object, the primary object still has to be identifiable and the
        reference it is reached through still has to be fetched;

    (2) a *passthrough* requirement on the related side — the related model's
        own primary-key attribute, which must always be fetched so a fetched
        related object can be identified, and

    (3) the *restricted* requirement — the chosen attribute on the related
        model (the one the caller asked to keep).

  Each model participates in the accumulation under ONE canonical identity. A
  model that is a lightweight alias of another shares that other model's
  storage, hence its canonical identity: both must be recorded under the same
  canonical key. The restricted attribute (3) is recorded under the related
  model's canonical identity. The reported result is the per-model mapping of
  canonical model identity to the set of attribute names recorded for it.

  The contract pins the OBSERVABLES that the downstream identification step
  relies on:

    * the canonical-identity bucket for the related model exists and holds
      EXACTLY its primary key and the chosen attribute — nothing else (no
      spurious over-fetch);

    * the canonical-identity bucket for the primary model exists and holds
      EXACTLY its own primary key and the reference attribute — nothing else.
      A reported mapping that omits either of those from the primary model's
      bucket, or that reports some other attribute set there, is rejected: the
      primary object would then not be identifiable, or the reference the
      related object is reached through would not be fetched, even though the
      caller restricted only the related object; and

    * each primary key is recorded under its model's canonical identity, NOT
      scattered under that model's raw (non-canonical) identity. A reported
      mapping that lodges a primary key under a raw alias identity (leaving the
      canonical bucket — or some other bucket — to carry it) is rejected: a
      passthrough primary key must be accumulated under the same canonical key
      the restricted attribute and the final read-out use.

  Scope of the modelled slice: exactly one relation hop, over a reference the
  primary model itself stores; the primary and the related model keep separate
  storage, so their canonical identities differ; the caller's restriction keeps
  exactly one attribute and that attribute belongs to the related object, so
  nothing beyond the passthrough requirements is asked of the primary model;
  and that chosen attribute is stored by the related model itself rather than
  by a model whose storage it extends. Outside that slice the reported mapping
  has further participants, or further attributes for these ones, and this
  contract says nothing about it.

Modelling choices (Nagini fragment):
  * Models are `int` tokens; attribute names are `int` tokens.
  * The canonical identity of a model (its storage representative; an alias
    collapses to the model it aliases, a non-alias is its own canonical) is the
    map ``canonical`` from a model token to its canonical model token. It is
    idempotent (a canonical model is its own canonical). This is an unchanged
    attribute read, validated against real Python semantics out-of-band by
    axiom_check.py (G-AX) as an A-reference, not consumed as an axiom.
  * The storage owner of an attribute name (which model's storage holds it) is
    the map ``attr_owner`` from an attribute-name token to a canonical model
    token. Both maps are read-only.
  * The per-model accumulators are `Dict[int, Dict[int, int]]`: a model token
    maps to its recorded attribute-name set (a set carried as a `Dict[int,int]`
    keyed by attribute-name token). The result is the full per-model mapping;
    membership of an attribute name in a model's reported set is the observable
    the downstream identification step relies on.

No string indexing is used (Nagini bans it). Dict access is guarded by an
explicit membership test before subscription. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The per-model field accumulation and the canonical-key
# selection are the behaviour under specification and are modelled deeply (the
# `canonical_of` helper and the impl). The map subscriptions / set membership it
# composes are ordinary mapping operations, validated against their real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end

# pure-start
@Pure
def canonical_of(canonical: Dict[int, int], model: int) -> int:
    """The canonical (storage) identity of `model`: the `canonical` map applied
    to `model`, falling back to `model` itself when the model is absent from the
    map (a model that backs its own storage is its own canonical identity)."""
    Requires(Acc(dict_pred(canonical), 1 / 4))
    if model in canonical:
        return canonical[model]
    return model
# pure-end

def related_reported_fields(canonical: Dict[int, int],
                            attr_owner: Dict[int, int],
                            primary: int,
                            primary_pk: int,
                            ref_attr: int,
                            related: int,
                            related_pk: int,
                            chosen_attr: int) -> Dict[int, Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(canonical), 1 / 2))
    Requires(Acc(dict_pred(attr_owner), 1 / 2))
    # The passthrough key and the restricted key are distinct attribute names
    # (the primary key is not the chosen attribute), so set membership of one is
    # independent of the other.
    Requires(related_pk != chosen_attr)
    # The canonical map is a fixed-point of itself at both participants: a
    # canonical identity is its own canonical (idempotence). This is the real
    # attribute's property (`_meta.concrete_model` of a concrete model is
    # itself; validated by G-AX), constraining the input to the attribute's true
    # domain so that normalizing a model that is already canonical is a no-op.
    Requires(canonical_of(canonical, canonical_of(canonical, related))
             == canonical_of(canonical, related))
    Requires(canonical_of(canonical, canonical_of(canonical, primary))
             == canonical_of(canonical, primary))
    # Modelled slice: the related object is stored separately from the primary
    # one, so the two participants report under different canonical identities.
    Requires(canonical_of(canonical, primary)
             != canonical_of(canonical, related))
    # Modelled slice: the chosen attribute is one the related model's own
    # storage holds (it is not inherited from a model whose storage the related
    # model extends, which would report it under that other model's identity).
    # Stated on the storage identity of the declaring model, so the declaring
    # model token itself is NOT pinned to the related model's canonical identity
    # (it is only known to share it).
    Requires(chosen_attr in attr_owner
             and canonical_of(canonical, attr_owner[chosen_attr])
             == canonical_of(canonical, related))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(canonical), 1 / 2))
    Ensures(Acc(dict_pred(attr_owner), 1 / 2))
    # The result is the per-model reported mapping; permission to it and to the
    # two canonical-identity buckets whose contents the contract constrains.
    Ensures(Acc(dict_pred(Result())))
    Ensures(canonical_of(canonical, related) in Result())
    Ensures(canonical_of(canonical, primary) in Result())
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, related)])))
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, primary)])))
    # The reported set for the related model lives under its CANONICAL identity.
    # Within that bucket the chosen restricted attribute is present (the caller's
    # kept attribute), self-keyed.
    Ensures(chosen_attr in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][chosen_attr]
            == chosen_attr)
    # Discriminating clause (presence): the related model's primary key is
    # present in that SAME canonical-identity bucket, self-keyed.
    Ensures(related_pk in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][related_pk]
            == related_pk)
    # Closure: the canonical bucket holds NOTHING beyond the primary key and the
    # chosen attribute — no spurious over-fetch.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, related)],
        a == related_pk or a == chosen_attr))))
    # Passthrough clause (presence): restricting the related object does not
    # excuse the primary side. Under the primary model's CANONICAL identity the
    # reported set carries its own primary key, so a fetched primary object can
    # be identified, AND the reference attribute the related object is reached
    # through, so the relation can still be traversed — both self-keyed.
    Ensures(primary_pk in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][primary_pk]
            == primary_pk)
    Ensures(ref_attr in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][ref_attr]
            == ref_attr)
    # Closure: the primary model's bucket holds NOTHING beyond those two — the
    # caller restricted the related object, not the primary one, so no other
    # attribute of the primary model is reported as required.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, primary)],
        a == primary_pk or a == ref_attr))))
    # Provenance clauses: the reported mapping is keyed SOLELY by canonical
    # identity. When a participating model is a non-canonical alias, its raw
    # identity is not a key of the result at all; everything recorded for it
    # lives under its canonical identity. (When a participant is already its own
    # canonical, the raw and canonical identities coincide and the clause is
    # vacuous.) Together with the presence clauses above, this requires each
    # primary key to reside under the canonical identity rather than under the
    # alias identity.
    Ensures(Implies(related != canonical_of(canonical, related),
                    not (related in Result())))
    Ensures(Implies(primary != canonical_of(canonical, primary),
                    not (primary in Result())))
    # post-conditions-end
    # impl-start
    # Canonical identities under which the two participating models report.
    prim_key = canonical_of(canonical, primary)  # type: int
    rel_key = canonical_of(canonical, related)  # type: int

    # `must_include`: the passthrough requirements, keyed by canonical identity.
    # The primary model contributes its own primary key.
    must_include = {}  # type: Dict[int, Dict[int, int]]
    prim_set = {}  # type: Dict[int, int]
    prim_set[primary_pk] = primary_pk
    must_include[prim_key] = prim_set

    # The traversed model is normalized to its canonical identity before
    # anything is keyed by it.
    cur_model = related  # type: int
    cur_model = canonical_of(canonical, cur_model)

    # Passing through the relation records the reference attribute on the model
    # the traversal came from, and the traversed model's own primary key.
    if prim_key in must_include:
        from_set = must_include[prim_key]  # type: Dict[int, int]
        from_set[ref_attr] = ref_attr
        must_include[prim_key] = from_set
    pk_set = {}  # type: Dict[int, int]
    pk_set[related_pk] = related_pk
    must_include[cur_model] = pk_set

    # `seen`: the restricted requirement (the chosen attribute) keyed by the
    # related model's canonical identity.
    seen = {}  # type: Dict[int, Dict[int, int]]
    leaf_set = {}  # type: Dict[int, int]
    leaf_set[chosen_attr] = chosen_attr
    seen[rel_key] = leaf_set

    # Merge the passthrough requirements into the reported (`seen`) accumulator,
    # per model key: a model recorded in `must_include` folds its required
    # attributes into the model's reported set under the same key.
    if cur_model in seen:
        target_set = seen[cur_model]  # type: Dict[int, int]
        source_set = must_include[cur_model]  # type: Dict[int, int]
        if related_pk in source_set:
            target_set[related_pk] = source_set[related_pk]
        seen[cur_model] = target_set
    else:
        seen[cur_model] = must_include[cur_model]
    if prim_key in seen:
        prim_target = seen[prim_key]  # type: Dict[int, int]
        prim_source = must_include[prim_key]  # type: Dict[int, int]
        if primary_pk in prim_source:
            prim_target[primary_pk] = prim_source[primary_pk]
        if ref_attr in prim_source:
            prim_target[ref_attr] = prim_source[ref_attr]
        seen[prim_key] = prim_target
    else:
        seen[prim_key] = must_include[prim_key]

    # The reported per-model mapping (keyed by canonical model identity).
    return seen
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-15814/nagini. 16 same-spec attacks + 1 vacuity control, all byte-identical spec (same-spec exit 0 on every file, incl. pos_control). Positive control pos_control.py (= bundle model.py) VERIFIES (exit 0, 18.6s).

METHOD NOTE (self-caught error): my first DIRECT skeleton omitted `return seen`, so atk_3/4/5/6/7/8/9 initially failed on 'Assertion "return type is correct" might not hold' -- a Nagini typing artifact, NOT a semantic rejection. Those rejections were vacuous. I added the missing return and RE-RAN all seven; only the re-run results are reported below. Reporting the first-round rejections as spec strength would have been a false SOUND.

PER-ATTACK RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-15814 <path>; raw errors via bash scripts/nagini_verify.sh <path>):
- atk_1 PREPATCH BUG re-encoded (drops `cur_model = canonical_of(canonical, cur_model)`; == bundled model_prepatch.py impl): exit 2, fails `related_pk in Result()[canonical_of(canonical, related)]`. PREPATCH REPRODUCED. Bundled model_prepatch.py independently re-verified -> same discriminating failure.
- atk_2 OVER-FETCH (extra primary_pk in related bucket): exit 2, fails the related-bucket CLOSURE Forall.
- atk_3 DISCONNECTED LITERAL keyed by RAW identities: exit 2, fails `canonical_of(canonical, related) in Result()`.
- atk_4 POST-HOC SCATTER (gold buckets + raw-alias bucket): exit 2, fails anti-scatter `related != canonical_of(...) ==> related not in Result()`.
- atk_5 PARTIAL DOMAIN, related side (pk only when related is an alias): exit 2, fails `related_pk in Result()[rel_key]`.
- atk_6 CONTROL-FLOW EFFECT (one inner dict aliased as both must_include buckets): exit 2, fails the PRIMARY-bucket closure Forall.
- atk_7 UNGROUNDED ORACLE ECHO / behaviourally-correct direct build: CANDIDATE (verifies 14.3s).
- atk_8 SPURIOUS EXTRA PARTICIPANT keyed by raw declaring model: CANDIDATE (verifies 15.6s).
- atk_9 DIVERGENCE (non-terminating loop + correct output): exit 2, 'Obligation leak check failed' -- method-level MustTerminate(2) is load-bearing.
- atk_10 SWAPPED BUCKETS (primary/related contents exchanged): exit 2, fails `chosen_attr in Result()[rel_key]`.
- atk_11 keys chosen_attr by canonical_of(attr_owner[chosen_attr]) only, omitting rel_key: exit 2, fails `rel_key in Result()`.
- atk_12 drops ref_attr from must_include, re-injects post-hoc: exit 2, fails `ref_attr in Result()[canonical_of(canonical, primary)]`.
- atk_13 double-normalization + attr_owner-membership echo: exit 2, fails `rel_key in Result()`.
- atk_14 PARTIAL DOMAIN, primary side: exit 2, fails `primary_pk in Result()[canonical_of(canonical, primary)]`.
- atk_15 ALIASED SHARED BUCKET (both buckets one dict): exit 2, insufficient permission to dict_pred(Result()[prim_key]) -- separation logic rejects the aliasing.
- atk_16 PARTIAL-DOMAIN ESCAPE via the deliberately-unpinned declaring token (spec pins only canonical_of(attr_owner[chosen_attr]) == rel_key, NOT the token): CANDIDATE (verifies 23.4s).
- atk_vacuity `Assert(False)` prepended to the gold impl: FAILS ('Assert might fail'). Preconditions are SATISFIABLE -> the postconditions are non-vacuous and every rejection above is a real one.

MANDATORY RESOLVE RUNS -- all 3 CANDIDATEs materialized as faithful patches and executed through the official harness (swebench_unified.harness.run_resolve, docker oracle, image swebench/sweb.eval.x86_64.django_1776_django-15814):
- atk_7 -> patch_atk_7.diff (== gold patch verbatim; the direct build IS gold behaviour): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
- atk_8 -> patch_atk_8.diff: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
- atk_16 -> patch_atk_16.diff: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
No verifying wrong impl produced a non-resolving faithful patch => no verify-but-incorrect witness. Not speculation: all three executed.

WHY atk_8/atk_16 RESOLVE ANYWAY (converted from speculation to fact, not assumed):
- atk_8's guard is unreachable in the repo. Reachability probe patch_atk8_probe.diff replaced the extra-bucket body with `raise AssertionError("ATK8_BRANCH_REACHED")` and still RESOLVED=True with zero ATK8_BRANCH_REACHED occurrences -> dead code (`field.model is field.model._meta.concrete_model` is True here, measured). So atk_8's resolve is uninformative about the spec, which is why atk_16 was built.
- atk_16's branch IS reachable, measured in-container (reach16.py): for .only('assignee__status') field.model=TrackerUser vs raw_related=ProxyTrackerUser -> BRANCH_FIRES=True; for the inherited .only('assignee__name') field.model=BaseUser -> BRANCH_FIRES=True. It therefore genuinely writes a spurious extra `seen[ProxyTrackerUser-or-BaseUser]` bucket on the F2P path, and the suite STILL passes: the extra bucket is keyed by a model the downstream RelatedPopulator/compiler does not consult for this query, and the two buckets the loader does read (concrete TrackerUser, Issue) are exactly correct. So this is a genuine behavioural over-approximation that the TESTS do not sense, i.e. a limit of the F2P/P2P oracle, not of the spec: G-EQ's claim is verify => resolves, and it holds (it resolved).

### A-LEG AUDIT (refinement.md; R/I legs left to G-CONF):
- Leg tag census: 3x R, 2x 'R + I', 1x I, 1x A-reference; ZERO A-consumed and ZERO kind-3. Confirmed no consumed axioms: meta.json axioms == [] and model.py contains no @ContractOnly / Assume / sorry / @Predicate (grepped). The axioms region is a comment only. So there is no axiom to over-approximate, and the one changed operation is modelled deeply rather than hidden behind a stub -- refinement.md sec.B's claim checks out.
- A3 (the sole A-reference, canonical_of == Model.`_meta`.concrete_model): axiom_check.py EXECUTED inside the task image -> exit 0, 'G-AX OK: canonical_of == `_meta`.concrete_model (proxy->concrete, concrete->self, idempotent)'. Correspondence to the real callee holds: proxy->concrete parent, concrete->self, idempotent, matching the two idempotence preconditions.
- A1/A4/A5/A6/A7 correspondence checked against the REAL callee, not prose: corr_probe.py ran the actual Query.deferred_to_data on the F2P query at base_commit and printed target = {TrackerUser: ['status'], Issue: ['assignee_id','id'], ProxyTrackerUser: ['baseuser_ptr_id']}. This is exactly the pre-patch pathology the model claims (the related pk 'baseuser_ptr_id' lodged under the PROXY bucket and ABSENT from the concrete TrackerUser bucket, while 'status' sits under TrackerUser) -> confirms A4's 'key is cur_model' as the load-bearing consequence, A5's leaf-under-concrete, A6's per-key merge, and A7's per-model target mapping. Real attnames (Issue.pk='id', assignee='assignee_id', TrackerUser.pk='baseuser_ptr_id', all distinct) satisfy the related_pk != chosen_attr refinement. mapping.md's line refs (751 insert, 757 add, 760-765 leaf, 787-802 merge/read-out) match the base-commit source I read.
- Honest caveat recorded, not a gate fail: the modelled slice fixes exactly one hop and two participants, and the primary-side bucket is modelled as holding exactly {pk, ref_attr}; the real orig_opts bucket also gets get_parent_list() setdefault entries (query.py:797-799) outside the slice. The spec scopes this explicitly in its preconditions/docstring, and atk_16 shows the unpinned-declaring-token latitude is real but test-invisible.

**CONCLUSION:** prepatch reproduced and rejected on the discriminating clause; 13 of 16 wrong impls rejected, each on a semantically apt clause (discriminating presence, closure, anti-scatter/provenance, primary passthrough, termination, separation); vacuity control fails as required; all 3 verifying candidates' faithful patches EXECUTED through run_resolve and all RESOLVED. No verify-but-not-resolve witness found. Verdict SOUND (advisory).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_vacuity.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15814.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader works out which database columns to fetch for an optimized
  query that pulls a related object alongside the primary one and restricts the
  related object to a chosen subset of its stored attributes, it accumulates,
  per participating model, the set of attribute names that must be fetched.
  The mapping it reports is consumed WHOLE by the step that turns it into
  columns: every bucket it reports is read, not only the related model's.

  Two models participate in the slice modelled here: the query's own PRIMARY
  model, and the RELATED model reached from it through one reference attribute
  the primary model stores.

  Three kinds of attribute name are recorded while the related model is
  traversed:

    (1) the *passthrough* requirements on the primary side — the primary
        model's own primary-key attribute and the reference attribute it stores
        for the traversed relation. Even though the caller restricted only the
        related object, the primary object still has to be identifiable and the
        reference it is reached through still has to be fetched;

    (2) a *passthrough* requirement on the related side — the related model's
        own primary-key attribute, which must always be fetched so a fetched
        related object can be identified, and

    (3) the *restricted* requirement — the chosen attribute on the related
        model (the one the caller asked to keep).

  Each model participates in the accumulation under ONE canonical identity. A
  model that is a lightweight alias of another shares that other model's
  storage, hence its canonical identity: both must be recorded under the same
  canonical key. The restricted attribute (3) is recorded under the related
  model's canonical identity. The reported result is the per-model mapping of
  canonical model identity to the set of attribute names recorded for it.

  The contract pins the OBSERVABLES that the downstream identification step
  relies on:

    * the canonical-identity bucket for the related model exists and holds
      EXACTLY its primary key and the chosen attribute — nothing else (no
      spurious over-fetch);

    * the canonical-identity bucket for the primary model exists and holds
      EXACTLY its own primary key and the reference attribute — nothing else.
      A reported mapping that omits either of those from the primary model's
      bucket, or that reports some other attribute set there, is rejected: the
      primary object would then not be identifiable, or the reference the
      related object is reached through would not be fetched, even though the
      caller restricted only the related object; and

    * each primary key is recorded under its model's canonical identity, NOT
      scattered under that model's raw (non-canonical) identity. A reported
      mapping that lodges a primary key under a raw alias identity (leaving the
      canonical bucket — or some other bucket — to carry it) is rejected: a
      passthrough primary key must be accumulated under the same canonical key
      the restricted attribute and the final read-out use.

  Scope of the modelled slice: exactly one relation hop, over a reference the
  primary model itself stores; the primary and the related model keep separate
  storage, so their canonical identities differ; the caller's restriction keeps
  exactly one attribute and that attribute belongs to the related object, so
  nothing beyond the passthrough requirements is asked of the primary model;
  and that chosen attribute is stored by the related model itself rather than
  by a model whose storage it extends. Outside that slice the reported mapping
  has further participants, or further attributes for these ones, and this
  contract says nothing about it.

Modelling choices (Nagini fragment):
  * Models are `int` tokens; attribute names are `int` tokens.
  * The canonical identity of a model (its storage representative; an alias
    collapses to the model it aliases, a non-alias is its own canonical) is the
    map ``canonical`` from a model token to its canonical model token. It is
    idempotent (a canonical model is its own canonical). This is an unchanged
    attribute read, validated against real Python semantics out-of-band by
    axiom_check.py (G-AX) as an A-reference, not consumed as an axiom.
  * The storage owner of an attribute name (which model's storage holds it) is
    the map ``attr_owner`` from an attribute-name token to a canonical model
    token. Both maps are read-only.
  * The per-model accumulators are `Dict[int, Dict[int, int]]`: a model token
    maps to its recorded attribute-name set (a set carried as a `Dict[int,int]`
    keyed by attribute-name token). The result is the full per-model mapping;
    membership of an attribute name in a model's reported set is the observable
    the downstream identification step relies on.

No string indexing is used (Nagini bans it). Dict access is guarded by an
explicit membership test before subscription. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The per-model field accumulation and the canonical-key
# selection are the behaviour under specification and are modelled deeply (the
# `canonical_of` helper and the impl). The map subscriptions / set membership it
# composes are ordinary mapping operations, validated against their real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end

# pure-start
@Pure
def canonical_of(canonical: Dict[int, int], model: int) -> int:
    """The canonical (storage) identity of `model`: the `canonical` map applied
    to `model`, falling back to `model` itself when the model is absent from the
    map (a model that backs its own storage is its own canonical identity)."""
    Requires(Acc(dict_pred(canonical), 1 / 4))
    if model in canonical:
        return canonical[model]
    return model
# pure-end

def related_reported_fields(canonical: Dict[int, int],
                            attr_owner: Dict[int, int],
                            primary: int,
                            primary_pk: int,
                            ref_attr: int,
                            related: int,
                            related_pk: int,
                            chosen_attr: int) -> Dict[int, Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(canonical), 1 / 2))
    Requires(Acc(dict_pred(attr_owner), 1 / 2))
    # The passthrough key and the restricted key are distinct attribute names
    # (the primary key is not the chosen attribute), so set membership of one is
    # independent of the other.
    Requires(related_pk != chosen_attr)
    # The canonical map is a fixed-point of itself at both participants: a
    # canonical identity is its own canonical (idempotence). This is the real
    # attribute's property (`_meta.concrete_model` of a concrete model is
    # itself; validated by G-AX), constraining the input to the attribute's true
    # domain so that normalizing a model that is already canonical is a no-op.
    Requires(canonical_of(canonical, canonical_of(canonical, related))
             == canonical_of(canonical, related))
    Requires(canonical_of(canonical, canonical_of(canonical, primary))
             == canonical_of(canonical, primary))
    # Modelled slice: the related object is stored separately from the primary
    # one, so the two participants report under different canonical identities.
    Requires(canonical_of(canonical, primary)
             != canonical_of(canonical, related))
    # Modelled slice: the chosen attribute is one the related model's own
    # storage holds (it is not inherited from a model whose storage the related
    # model extends, which would report it under that other model's identity).
    # Stated on the storage identity of the declaring model, so the declaring
    # model token itself is NOT pinned to the related model's canonical identity
    # (it is only known to share it).
    Requires(chosen_attr in attr_owner
             and canonical_of(canonical, attr_owner[chosen_attr])
             == canonical_of(canonical, related))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(canonical), 1 / 2))
    Ensures(Acc(dict_pred(attr_owner), 1 / 2))
    # The result is the per-model reported mapping; permission to it and to the
    # two canonical-identity buckets whose contents the contract constrains.
    Ensures(Acc(dict_pred(Result())))
    Ensures(canonical_of(canonical, related) in Result())
    Ensures(canonical_of(canonical, primary) in Result())
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, related)])))
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, primary)])))
    # The reported set for the related model lives under its CANONICAL identity.
    # Within that bucket the chosen restricted attribute is present (the caller's
    # kept attribute), self-keyed.
    Ensures(chosen_attr in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][chosen_attr]
            == chosen_attr)
    # Discriminating clause (presence): the related model's primary key is
    # present in that SAME canonical-identity bucket, self-keyed.
    Ensures(related_pk in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][related_pk]
            == related_pk)
    # Closure: the canonical bucket holds NOTHING beyond the primary key and the
    # chosen attribute — no spurious over-fetch.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, related)],
        a == related_pk or a == chosen_attr))))
    # Passthrough clause (presence): restricting the related object does not
    # excuse the primary side. Under the primary model's CANONICAL identity the
    # reported set carries its own primary key, so a fetched primary object can
    # be identified, AND the reference attribute the related object is reached
    # through, so the relation can still be traversed — both self-keyed.
    Ensures(primary_pk in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][primary_pk]
            == primary_pk)
    Ensures(ref_attr in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][ref_attr]
            == ref_attr)
    # Closure: the primary model's bucket holds NOTHING beyond those two — the
    # caller restricted the related object, not the primary one, so no other
    # attribute of the primary model is reported as required.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, primary)],
        a == primary_pk or a == ref_attr))))
    # Provenance clauses: the reported mapping is keyed SOLELY by canonical
    # identity. When a participating model is a non-canonical alias, its raw
    # identity is not a key of the result at all; everything recorded for it
    # lives under its canonical identity. (When a participant is already its own
    # canonical, the raw and canonical identities coincide and the clause is
    # vacuous.) Together with the presence clauses above, this requires each
    # primary key to reside under the canonical identity rather than under the
    # alias identity.
    Ensures(Implies(related != canonical_of(canonical, related),
                    not (related in Result())))
    Ensures(Implies(primary != canonical_of(canonical, primary),
                    not (primary in Result())))
    # post-conditions-end
    # impl-start
    # Canonical identities under which the two participating models report.
    prim_key = canonical_of(canonical, primary)  # type: int
    rel_key = canonical_of(canonical, related)  # type: int

    # `must_include`: the passthrough requirements, keyed by canonical identity.
    # The primary model contributes its own primary key.
    must_include = {}  # type: Dict[int, Dict[int, int]]
    prim_set = {}  # type: Dict[int, int]
    prim_set[primary_pk] = primary_pk
    must_include[prim_key] = prim_set

    # The traversed model is normalized to its canonical identity before
    # anything is keyed by it.
    cur_model = related  # type: int
    cur_model = canonical_of(canonical, cur_model)

    # Passing through the relation records the reference attribute on the model
    # the traversal came from, and the traversed model's own primary key.
    if prim_key in must_include:
        from_set = must_include[prim_key]  # type: Dict[int, int]
        from_set[ref_attr] = ref_attr
        must_include[prim_key] = from_set
    pk_set = {}  # type: Dict[int, int]
    pk_set[related_pk] = related_pk
    must_include[cur_model] = pk_set

    # `seen`: the restricted requirement (the chosen attribute) keyed by the
    # related model's canonical identity.
    seen = {}  # type: Dict[int, Dict[int, int]]
    leaf_set = {}  # type: Dict[int, int]
    leaf_set[chosen_attr] = chosen_attr
    seen[rel_key] = leaf_set

    # Merge the passthrough requirements into the reported (`seen`) accumulator,
    # per model key: a model recorded in `must_include` folds its required
    # attributes into the model's reported set under the same key.
    if cur_model in seen:
        target_set = seen[cur_model]  # type: Dict[int, int]
        source_set = must_include[cur_model]  # type: Dict[int, int]
        if related_pk in source_set:
            target_set[related_pk] = source_set[related_pk]
        seen[cur_model] = target_set
    else:
        seen[cur_model] = must_include[cur_model]
    if prim_key in seen:
        prim_target = seen[prim_key]  # type: Dict[int, int]
        prim_source = must_include[prim_key]  # type: Dict[int, int]
        if primary_pk in prim_source:
            prim_target[primary_pk] = prim_source[primary_pk]
        if ref_attr in prim_source:
            prim_target[ref_attr] = prim_source[ref_attr]
        seen[prim_key] = prim_target
    else:
        seen[prim_key] = must_include[prim_key]

    # The reported per-model mapping (keyed by canonical model identity).
    return seen
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-15814/nagini. 16 same-spec attacks + 1 vacuity control, all byte-identical spec (same-spec exit 0 on every file, incl. pos_control). Positive control pos_control.py (= bundle model.py) VERIFIES (exit 0, 18.6s).

METHOD NOTE (self-caught error): my first DIRECT skeleton omitted `return seen`, so atk_3/4/5/6/7/8/9 initially failed on 'Assertion "return type is correct" might not hold' -- a Nagini typing artifact, NOT a semantic rejection. Those rejections were vacuous. I added the missing return and RE-RAN all seven; only the re-run results are reported below. Reporting the first-round rejections as spec strength would have been a false SOUND.

PER-ATTACK RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-15814 <path>; raw errors via bash scripts/nagini_verify.sh <path>):
- atk_1 PREPATCH BUG re-encoded (drops `cur_model = canonical_of(canonical, cur_model)`; == bundled model_prepatch.py impl): exit 2, fails `related_pk in Result()[canonical_of(canonical, related)]`. PREPATCH REPRODUCED. Bundled model_prepatch.py independently re-verified -> same discriminating failure.
- atk_2 OVER-FETCH (extra primary_pk in related bucket): exit 2, fails the related-bucket CLOSURE Forall.
- atk_3 DISCONNECTED LITERAL keyed by RAW identities: exit 2, fails `canonical_of(canonical, related) in Result()`.
- atk_4 POST-HOC SCATTER (gold buckets + raw-alias bucket): exit 2, fails anti-scatter `related != canonical_of(...) ==> related not in Result()`.
- atk_5 PARTIAL DOMAIN, related side (pk only when related is an alias): exit 2, fails `related_pk in Result()[rel_key]`.
- atk_6 CONTROL-FLOW EFFECT (one inner dict aliased as both must_include buckets): exit 2, fails the PRIMARY-bucket closure Forall.
- atk_7 UNGROUNDED ORACLE ECHO / behaviourally-correct direct build: CANDIDATE (verifies 14.3s).
- atk_8 SPURIOUS EXTRA PARTICIPANT keyed by raw declaring model: CANDIDATE (verifies 15.6s).
- atk_9 DIVERGENCE (non-terminating loop + correct output): exit 2, 'Obligation leak check failed' -- method-level MustTerminate(2) is load-bearing.
- atk_10 SWAPPED BUCKETS (primary/related contents exchanged): exit 2, fails `chosen_attr in Result()[rel_key]`.
- atk_11 keys chosen_attr by canonical_of(attr_owner[chosen_attr]) only, omitting rel_key: exit 2, fails `rel_key in Result()`.
- atk_12 drops ref_attr from must_include, re-injects post-hoc: exit 2, fails `ref_attr in Result()[canonical_of(canonical, primary)]`.
- atk_13 double-normalization + attr_owner-membership echo: exit 2, fails `rel_key in Result()`.
- atk_14 PARTIAL DOMAIN, primary side: exit 2, fails `primary_pk in Result()[canonical_of(canonical, primary)]`.
- atk_15 ALIASED SHARED BUCKET (both buckets one dict): exit 2, insufficient permission to dict_pred(Result()[prim_key]) -- separation logic rejects the aliasing.
- atk_16 PARTIAL-DOMAIN ESCAPE via the deliberately-unpinned declaring token (spec pins only canonical_of(attr_owner[chosen_attr]) == rel_key, NOT the token): CANDIDATE (verifies 23.4s).
- atk_vacuity `Assert(False)` prepended to the gold impl: FAILS ('Assert might fail'). Preconditions are SATISFIABLE -> the postconditions are non-vacuous and every rejection above is a real one.

MANDATORY RESOLVE RUNS -- all 3 CANDIDATEs materialized as faithful patches and executed through the official harness (swebench_unified.harness.run_resolve, docker oracle, image swebench/sweb.eval.x86_64.django_1776_django-15814):
- atk_7 -> patch_atk_7.diff (== gold patch verbatim; the direct build IS gold behaviour): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
- atk_8 -> patch_atk_8.diff: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
- atk_16 -> patch_atk_16.diff: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, F2P 1/1, P2P 29/29.
No verifying wrong impl produced a non-resolving faithful patch => no verify-but-incorrect witness. Not speculation: all three executed.

WHY atk_8/atk_16 RESOLVE ANYWAY (converted from speculation to fact, not assumed):
- atk_8's guard is unreachable in the repo. Reachability probe patch_atk8_probe.diff replaced the extra-bucket body with `raise AssertionError("ATK8_BRANCH_REACHED")` and still RESOLVED=True with zero ATK8_BRANCH_REACHED occurrences -> dead code (`field.model is field.model._meta.concrete_model` is True here, measured). So atk_8's resolve is uninformative about the spec, which is why atk_16 was built.
- atk_16's branch IS reachable, measured in-container (reach16.py): for .only('assignee__status') field.model=TrackerUser vs raw_related=ProxyTrackerUser -> BRANCH_FIRES=True; for the inherited .only('assignee__name') field.model=BaseUser -> BRANCH_FIRES=True. It therefore genuinely writes a spurious extra `seen[ProxyTrackerUser-or-BaseUser]` bucket on the F2P path, and the suite STILL passes: the extra bucket is keyed by a model the downstream RelatedPopulator/compiler does not consult for this query, and the two buckets the loader does read (concrete TrackerUser, Issue) are exactly correct. So this is a genuine behavioural over-approximation that the TESTS do not sense, i.e. a limit of the F2P/P2P oracle, not of the spec: G-EQ's claim is verify => resolves, and it holds (it resolved).

### A-LEG AUDIT (refinement.md; R/I legs left to G-CONF):
- Leg tag census: 3x R, 2x 'R + I', 1x I, 1x A-reference; ZERO A-consumed and ZERO kind-3. Confirmed no consumed axioms: meta.json axioms == [] and model.py contains no @ContractOnly / Assume / sorry / @Predicate (grepped). The axioms region is a comment only. So there is no axiom to over-approximate, and the one changed operation is modelled deeply rather than hidden behind a stub -- refinement.md sec.B's claim checks out.
- A3 (the sole A-reference, canonical_of == Model.`_meta`.concrete_model): axiom_check.py EXECUTED inside the task image -> exit 0, 'G-AX OK: canonical_of == `_meta`.concrete_model (proxy->concrete, concrete->self, idempotent)'. Correspondence to the real callee holds: proxy->concrete parent, concrete->self, idempotent, matching the two idempotence preconditions.
- A1/A4/A5/A6/A7 correspondence checked against the REAL callee, not prose: corr_probe.py ran the actual Query.deferred_to_data on the F2P query at base_commit and printed target = {TrackerUser: ['status'], Issue: ['assignee_id','id'], ProxyTrackerUser: ['baseuser_ptr_id']}. This is exactly the pre-patch pathology the model claims (the related pk 'baseuser_ptr_id' lodged under the PROXY bucket and ABSENT from the concrete TrackerUser bucket, while 'status' sits under TrackerUser) -> confirms A4's 'key is cur_model' as the load-bearing consequence, A5's leaf-under-concrete, A6's per-key merge, and A7's per-model target mapping. Real attnames (Issue.pk='id', assignee='assignee_id', TrackerUser.pk='baseuser_ptr_id', all distinct) satisfy the related_pk != chosen_attr refinement. mapping.md's line refs (751 insert, 757 add, 760-765 leaf, 787-802 merge/read-out) match the base-commit source I read.
- Honest caveat recorded, not a gate fail: the modelled slice fixes exactly one hop and two participants, and the primary-side bucket is modelled as holding exactly {pk, ref_attr}; the real orig_opts bucket also gets get_parent_list() setdefault entries (query.py:797-799) outside the slice. The spec scopes this explicitly in its preconditions/docstring, and atk_16 shows the unpinned-declaring-token latitude is real but test-invisible.

**CONCLUSION:** prepatch reproduced and rejected on the discriminating clause; 13 of 16 wrong impls rejected, each on a semantically apt clause (discriminating presence, closure, anti-scatter/provenance, primary passthrough, termination, separation); vacuity control fails as required; all 3 verifying candidates' faithful patches EXECUTED through run_resolve and all RESOLVED. No verify-but-not-resolve witness found. Verdict SOUND (advisory).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE SETUP. Fresh worktree from django_django.git at base_commit 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a ->, then the gold patch APPLIED (the one inserted line `cur_model = cur_model._meta.concrete_model` before `opts = cur_model._meta` in Query.deferred_to_data, django/db/models/sql/query.py:751). Every oracle call below asserted `"cur_model = cur_model._meta.concrete_model" in inspect.getsource(Query.deferred_to_data)` first, so I compared the model against the PATCHED callee, never the base version -- I did not report the patch delta itself as a divergence.

**WHAT THE SPEC CLAIMS.** related_reported_fields models Query.deferred_to_data restricted to the single-hop `.only("rel__attr")` slice, returning the whole per-model reported mapping. Its Ensures pin, for cp=canonical(primary) and cr=canonical(related): (a) cr and cp are both keys of Result; (b) Result[cr] == exactly {related_pk, chosen_attr} (presence + Forall closure, no over-fetch); (c) Result[cp] == exactly {primary_pk, ref_attr} (presence + Forall closure); (d) provenance/anti-scatter -- if related != cr then related is NOT a key at all, likewise for primary. Requires fence the slice: related_pk != chosen_attr; canonical idempotent at both participants; canonical(primary) != canonical(related); and chosen_attr in attr_owner with canonical(attr_owner[chosen_attr]) == canonical(related).

**ORACLE HARNESS.** Real Django model classes (in-memory sqlite, no DB opened -- deferred_to_data only walks metadata), building the queryset and calling `qs.query.deferred_to_data(target)`, then reading target as {model_class: set(attnames)}. Bridged per mapping.md S2: classes<->int tokens, attnames<->int tokens, `_meta.concrete_model`<->canonical, `field.model`<->attr_owner. I checked all four clause families on every input, and SKIPPED only inputs the Requires genuinely excludes (recording them separately rather than counting them as passes).

EVIDENCE -- 0 divergences on in-slice inputs.
1) EXACT F2P configuration (tests/proxy_models/models.py, the highest-value case, and NOT the trivial shape the docstring suggests): Issue.assignee -> ProxyTrackerUser, a proxy of TrackerUser, which is ITSELF an MTI child of BaseUser. So related_pk is `baseuser_ptr_id`, not `id`. Real patched output = {TrackerUser: ['baseuser_ptr_id','status'], Issue: ['assignee_id','id']}. In-slice (canonicals differ; related_pk != chosen; canonical(attr_owner(status))==TrackerUser==cr). All clauses hold: cr=TrackerUser and cp=Issue are keys; Result[cr] exactly {baseuser_ptr_id, status}; Result[cp] exactly {id, assignee_id}; and the raw proxy ProxyTrackerUser is absent from the mapping, satisfying anti-scatter. I also reconstructed the F2P test `proxy_models.tests.ProxyModelTests.test_select_related_only` (it lives in the test patch, not at base) and ran it on the patched worktree: PASSES.
2) Hand-built battery, 20+ shapes, all SPEC-OK: related concrete / proxy / proxy-of-proxy; primary proxy; primary proxy-of-MTI-child; 3-level MTI primary; FK declared on an MTI parent; traversing the MTI parent_link itself (`only('p1_ptr__pn')`); forward o2o; FK with primary_key=True so primary_pk==ref_attr (bucket correctly collapses to the single {o_id}, still exactly {primary_pk, ref_attr}); custom pk names both sides; FK to_field (related_pk stays the pk, not the to_field); chosen attr is itself an FK attname (fk_id); chosen declared on an ABSTRACT base of related (attr_owner resolves to related itself -- in slice, holds); primary and related sharing an abstract base; attname collisions (chosen name duplicated on the primary side; related pk attname literally equal to the primary's ref attname 'r_id') -- the token bijection is per-model so these do not confuse the buckets.
3) RANDOMIZED FUZZ, seed 15814, 400 generated real model graphs crossing related shape {concrete, proxy, proxy-of-proxy, MTI child, proxy-of-MTI-child} x primary shape {concrete, proxy, MTI, proxy-of-MTI, 3-level MTI} x {ForeignKey/OneToOneField, null, primary_key=True} x {with/without select_related}, deriving primary_pk/ref_attr/related_pk from real `_meta` each time: in-slice TESTED=400, VIOLATIONS=0.

WHY THE SPEC IS NOT TOO STRONG -- the Requires are load-bearing, not decorative, and each one fences a real case where the strong Ensures would otherwise fail.
* attr_owner clause: with chosen inherited from related's MTI PARENT (`only('r__hp')` where hp is declared on HP and related is child HC), the real output is {HP:['hp'], HC:['hp_ptr_id'], HS:['id','r_id']} -- the chosen attr lands in the PARENT's bucket, so Result[cr] == {hp_ptr_id} != {related_pk, chosen}. The Ensures would be false here, and the precondition `canonical(attr_owner[chosen_attr]) == canonical(related)` excludes exactly this input. Correctly fenced, not overreaching.
* canonical(primary) != canonical(related): a self-FK through a proxy of the primary's own model gives one merged bucket {id, r_id, st}, where the two closure clauses would contradict each other. Excluded by the precondition.
* Reverse-o2o (as hop and as leaf) is likewise outside the modelled slice (spec says 'a reference the primary model itself stores'), and the real callee's is_reverse_o2o branches do behave differently there -- consistent with the stated scope.
* MTI parents of the ROOT model add extra EMPTY buckets via `seen.setdefault(model, set())` / get_parent_list (e.g. {Par: []} in the FK-on-MTI-child cases). This does NOT break the spec: the Ensures constrain only the cr and cp buckets and forbid the RAW alias keys; they never claim Result has no other keys. So the model returning only the two buckets is a sound abstraction of the mapping rather than an overclaim -- and notably the spec is careful here, since a naive 'Result has exactly two keys' clause WOULD have been unfaithful on E1/E3/D9/C6.

**ARTIFACT GATES.** `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (exit 0), 13.2s. model_prepatch.py -> 'Verification failed', failing precisely `related_pk in Result()[canonical_of(canonical, related)]` at 176:13, so the spec senses the patch delta (G-DIFF genuine, not vacuous). axiom_check.py against the patched worktree -> exit 0 (canonical_of == `_meta`.concrete_model: proxy->concrete, proxy-of-proxy->concrete, concrete->self, idempotent). No @ContractOnly axiom is consumed, so there is no axiom over-approximation surface to attack; the changed op is modelled deeply. same-spec harness sanity-checked (identity copy -> 'SAME', exit 0).

ONE DOCUMENTATION DEFECT, NOT A FAITHFULNESS DEFECT (flagging for the record, does not change the verdict). The spec region of model.py is 8-parameter (canonical, attr_owner, primary, primary_pk, ref_attr, related, related_pk, chosen_attr) with primary-side presence+closure and both provenance clauses. But conformance_check.py's SHADOW is a STALE 4-parameter copy -- `def related_reported_fields(canonical, related, related_pk, chosen_attr)` -- with zero occurrences of attr_owner/ref_attr/primary_pk, and mapping.md S1 still documents the old 4-arg signature. So G-CONF, as written, exercises an earlier revision of the impl and never differentially tests the primary-bucket clauses (c) or the primary-side provenance clause that I verified by hand above. That is a bundle-hygiene/coverage gap in the conformance artifact and the mapping table, not a case of the spec disagreeing with the repo: I checked the 8-arg clauses directly against the real patched callee across all 420+ in-slice inputs and found no disagreement.

**CONCLUSION.** No input satisfying the preconditions makes the modelled function's postconditions disagree with the real patched Query.deferred_to_data, including the exact F2P configuration with its non-obvious MTI-derived related_pk. The preconditions are tight enough to exclude the genuinely divergent shapes (inherited chosen attr, shared canonical, reverse-o2o) and the postconditions are careful enough not to overclaim about extra parent buckets. FAITHFUL; no diverging input found.

**REFERENCE SETUP.** Fresh worktree from django_django.git at base_commit 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a ->, then the gold patch APPLIED (the one inserted line `cur_model = cur_model._meta.concrete_model` before `opts = cur_model._meta` in Query.deferred_to_data, django/db/models/sql/query.py:751). Every oracle call below asserted `"cur_model = cur_model._meta.concrete_model" in inspect.getsource(Query.deferred_to_data)` first, so I compared the model against the PATCHED callee, never the base version -- I did not report the patch delta itself as a divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. I judged the consumer spec view exactly as the harness derives it: markers.spec_view(model.py, get_backend('nagini')) == eval/adapter.py Adapter.spec_view (same projection + the impl-elision guard). Written to sv15814.txt; sha256(spec_view region)=b17db135e829afd621283d65ed6a9cf900fea8ff367b1bd5968fec39091b73fd. The view = module docstring + 2 imports + axioms region + pure region (canonical_of) + signature + pre-conditions + post-conditions, with impl reduced to '...  # implementation elided -- supplied by the consumer'. mapping.md / refinement.md / model_prepatch.py / properties.py / verdict.md are NOT in the agent-visible surface (eval/dataset.py as_dict emits only problem_statement, [hints], spec_view, modeled_functions, float_encoding; WITHHELD_FIELDS blocks patch/test_patch/F2P/P2P), so I used them only as my own reference and did not judge them as the view.

**ARTIFACT IDENTITY.** sha256(model.py)=824651c6f441ebea2582b95c55dbe6362a830a6391b5901a6e10e84595652d9d, identical to gates['G-LEAK'|'G-AX'|'G-CONF'|'G-HYGIENE'|'G-GOLD'|'G-VERIFY'].sources['model.py'] -- I judged the same bytes the gates stamped. `adversary same-spec nagini django__django-15814 atk_leak3_15814.py` (a copy of model.py) -> exit 0 'SAME'; markers.same_spec(model.py, model_prepatch.py) = True, so the frozen spec really is impl-independent and is the thing I screened.

**NO RELAXATION IN THIS BUNDLE.** meta.json has no `relaxed_leakage` key (checked: absent, value None) and there is no RELAXED_LEAKAGE.md on disk (bundle listing: axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md). gates['G-LEAK'].status == 'pass', not 'relaxed'. So neither trigger in gates/leak.py's relaxation branch fires and this is a plain, unrelaxed leakage judgement -- no inherited disposition to re-derive.

GOLD EDIT (established from the real repo, not from the bundle). Worktree of the upstream repository at base_commit 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a ->. Confirmed `def deferred_to_data` at query.py:721 and `opts = cur_model._meta` at query.py:751. Gold = ONE inserted line, `cur_model = cur_model._meta.concrete_model`, immediately before line 751. leakage.`_patch_changed_lines`(gold) = ['cur_model = cur_model.`_meta`.concrete_model']; `_patch_changed_symbols` = {'deferred_to_data'}; `_patch_new_symbols` = set().

### MECHANICAL CHECKS I RAN (all clean).
1. gates/leak.py run() live on the bundle: G-LEAK pass, data {'failures': []} -- reproduced, not read off meta.
2. leakage.screen(model.py, nagini.language, gold_patch, ...) three ways: with the real problem_statement -> passed=True, hard=[], warn=[]; with problem_statement='' (screen given NO public excuse) -> still passed=True, hard=[], warn=[]; with hints_text substituted for problem_statement -> still passed=True, hard=[]. The clean result is therefore NOT an artifact of the problem_statement whitelist, and NOT an artifact of hints leniency (hints are explicitly out of scope for me anyway).
3. Symbol/file collision: leakage.`_py_spec_view_identifiers`(view) = {Acc, Dict, Ensures, Forall, Implies, MustTerminate, Pure, Requires, Result, a, attr_owner, canonical, canonical_of, chosen_attr, dict_pred, int, model, primary, primary_pk, ref_attr, related, related_pk, related_reported_fields}. 'deferred_to_data' absent from identifiers AND from raw view text. 'django/db/models/sql/query.py' absent; 'query.py' absent; dotted 'django.db.models.sql.query' absent. Also absent as raw substrings: add_to_dict, cur_model, opts, must_include, seen, remote_field, related_model, RelatedPopulator, init_list, pk_idx.
4. Impl-region elision is real, not nominal: 'must_include', 'seen', 'rel_key', 'prim_key', 'pk_set', 'leaf_set', 'from_set', 'target_set', 'source_set', 'prim_target', 'prim_source' -- every one False in the view. The normalization step `cur_model = canonical_of(canonical, cur_model)` (the model-level image of the gold insertion) is absent from the view.
5. Narration: leakage.`_NARRATION_RE` over leakage.`_py_comment_and_string_text`(view) -> ZERO hits (also zero on the raw file at this revision). No diff markers (@@, 'diff --git', '+++ ', '--- ', 'index ').
6. Test-identity leak: test_select_related_only, ProxyTrackerUser, TrackerUser, Issue, assignee, status, proxy_models, ProxyModelTests, ValueError -- all ABSENT.
7. Localization leak via numerals: the view contains ZERO multi-digit numbers (regex over 2-4 digit tokens returned empty), so neither 745 nor 751 nor 721 nor the 787-802 merge range reaches the consumer. The only '.py' tokens are two references to 'axiom_check.py' (the bundle's own G-AX harness, not a repo path); the only 'django' occurrences are the instance id on docstring line 1.

TOKEN SWEEP -> THE ONE HIT, AND WHY IT IS NOT LEAKAGE. Intersecting the view against gold-edit vocabulary yields exactly one hit: view line 136, a pre-condition comment justifying the idempotence Requires -- "# attribute's property (`_meta.concrete_model` of a concrete model is / # itself; validated by G-AX), constraining the input to the attribute's true / # domain".

This does not exceed the PUBLIC problem_statement, which publishes the fix verbatim: "At django/db/models/sql/query.py in 745 line there is snippet: opts = cur_model.`_meta` / If I replace it by / opts = cur_model.`_meta`.concrete_model.`_meta` / all works as expected." I verified by substring against the frozen row (NOT hints_text) that the problem_statement already contains '`_meta`.concrete_model' (True), 'query.py' (True), '745' (True), 'opts = cur_model.`_meta`' (True), 'proxy' (True), 'init_list.index' (True), 'pk.attname' (True), "'id' is not in list" (True). The view's mention is strictly WEAKER than that public disclosure: it names only the attribute, inside a justification of an input-domain constraint, and never the file, the line, the local to reassign, or the insertion point. Notably the view never uses the word 'proxy' at all ('proxy' in view.lower() = False -- it says 'lightweight alias'), so the view is more redacted than the public statement, not less.

SPEC-CONTENT / GOLD-RECONSTRUCTION JUDGEMENT. The post-conditions do state strong desired behaviour (pk under the CANONICAL bucket; closure on both buckets; anti-scatter -- related != canonical(related) ==> related not in Result()). I considered this as semantic reconstruction and reject it: (a) a spec is obliged to state desired behaviour, and these are observables of the downstream identification step, phrased as behaviour ('stated as desired behaviour, not as an edit'); (b) every discriminating fact is already public -- the traceback in the problem_statement shows RelatedPopulator failing at self.init_list.index(self.model_cls.`_meta`.pk.attname) with "ValueError: 'id' is not in list", i.e. the public issue already tells a solver the pk attname is missing from the reported list for the proxy's model; (c) the view discloses neither the edit site, the local variable, nor the one-line shape of the change -- a solver reading only the view learns 'accumulate the pk under the canonical key', which is the behavioural requirement, not the diff.

**BUNDLE ADDRESSING THE PANEL.** I screened every bundle file with leakage.reviewer_directed(): axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md -- ALL clean. Nothing in this bundle instructs me how to record or which verdict is honest. Nothing to report on that axis.

### OUT-OF-SCOPE OBSERVATIONS (no leakage consequence, flagged for the bundle owner).
(a) meta.json TOP-LEVEL region_hashes are STALE for two regions relative to model.py as it stands: recomputed pre-conditions=10fffdbc1d68..., spec_view=b17db135e829... vs recorded f30adf08ff9a..., b0a3cce765a4...; axioms/pure match. The values inside gates['G-HYGIENE'].data.region_hashes DO match the current file exactly (spec_view b17db135e829...), so this reads as the top-level block not being refreshed after the last pre-condition edit, not a content problem. It has zero leakage consequence, but it means a downstream consumer comparing against the top-level block would see a spurious mismatch.

(b) meta.json modeled_functions[0].repo_location is agent-visible in spec modes and reads 'django/db/models/sql/query.py:721 (patched body line 751; defer==False merge lines 787-802)'. The file and line 745/751 and the pre-patch snippet are already public via the problem_statement, and modes 1/2 grant localization by design, so I do not score it against the spec view; but the word 'patched' plus the merge line range is gratuitous and rewording to 'body line 751' costs nothing.

(c) This bundle already carries G-EQ / G-PANEL-1 fail (WEAK: atk7_root_key_clobber verifies but its patch does not resolve -- F2P 1/1 fail) and G-PANEL-2 fail (faithfulness: closure clause diverges for an FK to a proxy of the same model, where the root and related canonical buckets coincide and reality also holds the FK reference field). Those are the other two lanes' findings and I did not re-adjudicate them. They do not bear on leakage: a spec can be simultaneously too weak / unfaithful and non-leaking, which is precisely what I measure here. My NO-LEAKAGE verdict is scoped to leakage only and must not be read as endorsing the bundle overall.

**SCOPE.** I judged the consumer spec view exactly as the harness derives it: markers.spec_view(model.py, get_backend('nagini')) == eval/adapter.py Adapter.spec_view (same projection + the impl-elision guard). Written to sv15814.txt; sha256(spec_view region)=b17db135e829afd621283d65ed6a9cf900fea8ff367b1bd5968fec39091b73fd. The view = module docstring + 2 imports + axioms region + pure region (canonical_of) + signature + pre-conditions + post-conditions, with impl reduced to '...  # implementation elided -- supplied by the consumer'. mapping.md / refinement.md / model_prepatch.py / properties.py / verdict.md are NOT in the agent-visible surface (eval/dataset.py as_dict emits only problem_statement, [hints], spec_view, modeled_functions, float_encoding; WITHHELD_FIELDS blocks patch/test_patch/F2P/P2P), so I used them only as my own reference and did not judge them as the view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
