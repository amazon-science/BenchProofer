# P2 adversarial audit — scikit-learn__scikit-learn-10908

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 28 admissible attacks re-run of 28 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 28 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 24 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_22.py`, `atk_23.py`, `atk_24.py`, `atk_25.py`, `atk_26.py`, `atk_27.py`, `atk_28.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_10.py`, `atk_11.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 28 same-spec attacks were executed; 4 verified (atk_6, atk_10, atk_11, atk_17) and every one of their materialized faithful refined patches RESOLVED under the official harness (run_resolve: resolved=True, completed=True, F2P 1/1, P2P 47/47, patch_successfully_applied=True). No verifying wrong impl was found whose faithful patch fails to resolve, so no verify=>correct counterexample exists in the families probed.
```

**Attacks re-run (28):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -386,20 +386,8 @@
     # post-conditions-end
     # impl-start
     if not self.fitted:
-        if self.has_param:
-            if usable_terms(self.param):
-                materialise_from_param(self)
-            else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
-                raise UnusableTermsError()
-        else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
-            self.supplied = False
-            raise NotFittedError()
+        # PRE-PATCH: straight to the unusable check.
+        raise NotFittedError()
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,15 +390,10 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
-            self.supplied = False
+            # WRONG: the pre-patch `_check_vocabulary`-only path -- fails
+            # WITHOUT recording fixed_vocabulary_ = False.
             raise NotFittedError()
     result = []  # type: List[int]
     j = 0
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -400,6 +400,21 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        # WRONG: renumber the mapping underneath the very names it reports.
+        ren = []  # type: List[int]
+        m = 0
+        while m < len(self.names):
+            # invariants-start
+            Invariant(Acc(self.names) and Acc(list_pred(self.names), 1 / 2))
+            Invariant(Acc(list_pred(ren)))
+            Invariant(0 <= m and m <= len(self.names) and not isinstance(m, bool))
+            Invariant(len(ren) == m)
+            Invariant(MustTerminate(len(self.names) - m + 1))
+            # invariants-end
+            ren.append(2 * m)
+            m = m + 1
+        self.idx = ren
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -400,6 +400,10 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        # WRONG: wipe the mapping it was asked to report on.
+        self.names = []
+        self.idx = []
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -444,5 +444,6 @@
         result.append(self.names[j])
         j = j + 1
     Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
-    return result
+    # WRONG: hand back the object's OWN list, not a copy.
+    return self.names
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -388,16 +388,36 @@
     if not self.fitted:
         if self.has_param:
             if usable_terms(self.param):
-                materialise_from_param(self)
+                # A-REFERENCE BYPASS: build the mapping HERE instead of
+                # invoking the deep-modelled materialise primitive.
+                nn = []  # type: List[int]
+                ni = []  # type: List[int]
+                k = 0
+                while k < len(self.param):
+                    # invariants-start
+                    Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
+                    Invariant(Acc(list_pred(nn)) and Acc(list_pred(ni)))
+                    Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
+                    Invariant(0 <= k and k <= len(self.param) and not isinstance(k, bool))
+                    Invariant(ToSeq(nn) == ToSeq(self.param).take(k))
+                    Invariant(len(ni) == k)
+                    Invariant(ToSeq(ni) == places(k))
+                    Invariant(MustTerminate(len(self.param) - k + 1))
+                    # invariants-end
+                    Assert(ToSeq(self.param).take(k + 1).drop(k)[0] == self.param[k])
+                    nn.append(self.param[k])
+                    ni.append(k)
+                    k = k + 1
+                Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
+                Assert(len(nn) == k and len(ni) == k)
+                Assert(places(len(nn)) == places(k))
+                self.names = nn
+                self.idx = ni
+                self.fitted = True
+                self.supplied = True
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,14 +390,11 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
-                raise UnusableTermsError()
+                # WRONG: report the unfitted-object failure for a list that
+                # merely could not become a mapping.
+                self.supplied = False
+                raise NotFittedError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,14 +390,11 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
+                # WRONG: record fixed_vocabulary_ = False on the way out of a
+                # rejection that must write nothing.
+                self.supplied = False
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -388,16 +388,26 @@
     if not self.fitted:
         if self.has_param:
             if usable_terms(self.param):
-                materialise_from_param(self)
+                # WRONG: the mapping SHARES the ctor list object (gold copies).
+                ni = []  # type: List[int]
+                k = 0
+                while k < len(self.param):
+                    # invariants-start
+                    Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
+                    Invariant(Acc(list_pred(ni)))
+                    Invariant(0 <= k and k <= len(self.param) and not isinstance(k, bool))
+                    Invariant(len(ni) == k and ToSeq(ni) == places(k))
+                    Invariant(MustTerminate(len(self.param) - k + 1))
+                    # invariants-end
+                    ni.append(k)
+                    k = k + 1
+                self.names = self.param
+                self.idx = ni
+                self.fitted = True
+                self.supplied = True
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -400,6 +400,14 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        if len(self.names) == 0:
+            # DEAD in the model: Requires(Implies(self.fitted,
+            # usable_terms(self.names))) makes an already-present mapping
+            # non-empty, so the spec never looks here. Assert(False) is the
+            # control that proves the branch infeasible.
+            Assert(False)
+            self.idx = []
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -400,6 +400,13 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        if not numbered_by_place(self.idx, self.names):
+            # DEAD in the model: Requires(Implies(self.fitted,
+            # numbered_by_place(self.idx, self.names))) excludes it.
+            Assert(False)
+            self.names = []
+            self.idx = []
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -402,47 +402,11 @@
             raise NotFittedError()
     result = []  # type: List[int]
     j = 0
-    while j < len(self.names):
+    while j < len(self.names) or True:
         # invariants-start
         Invariant(Acc(self.names) and Acc(list_pred(self.names)))
-        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
-        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
-        Invariant(Acc(self.fitted) and self.fitted)
-        Invariant(Acc(list_pred(self.param), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        # The construction inputs are only read, so they still hold their entry
-        # values on every pass.
-        Invariant(self.has_param == Old(self.has_param))
-        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
-        # The mapping being reported is numbered by place throughout: the copy
-        # below reads it, it does not re-index it.
-        Invariant(numbered_by_place(self.idx, self.names))
-        # Whenever the object was not already fitted, a usable construction-
-        # supplied list is what materialised it: the object records a supplied-
-        # at-construction vocabulary, and the materialised names equal that list.
-        # These facts are stable across the loop below.
-        Invariant(Implies(not Old(self.fitted),
-                          Old(self.has_param) and Old(usable_terms(self.param))
-                          and self.supplied
-                          and ToSeq(self.names) == ToSeq(self.param)))
-        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
-        # re-indexed the mapping, so both of its halves and the supplied-at-
-        # construction record are still the ones the object came in with.
-        Invariant(Implies(Old(self.fitted),
-                          ToSeq(self.names) == Old(ToSeq(self.names))
-                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
-                          and self.supplied == Old(self.supplied)))
-        Invariant(0 <= j and j <= len(self.names))
-        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
-        # At most len(self.names) - j + 1 passes remain: the materialised mapping
-        # is held by the invariant above so its length cannot change, and j rises
-        # by exactly one per pass, so the bound strictly decreases; the loop guard
-        # j < len(self.names) keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(self.names) - j + 1))
         # invariants-end
-        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
-        result.append(self.names[j])
         j = j + 1
-    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
     return result
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -389,15 +389,23 @@
         if self.has_param:
             if usable_terms(self.param):
                 materialise_from_param(self)
+                # WRONG: renumber the mapping just built.
+                sh = []  # type: List[int]
+                q = 0
+                while q < len(self.names):
+                    # invariants-start
+                    Invariant(Acc(self.names) and Acc(list_pred(self.names), 1 / 2))
+                    Invariant(Acc(list_pred(sh)))
+                    Invariant(0 <= q and q <= len(self.names) and not isinstance(q, bool))
+                    Invariant(len(sh) == q)
+                    Invariant(MustTerminate(len(self.names) - q + 1))
+                    # invariants-end
+                    sh.append(q + 1)
+                    q = q + 1
+                self.idx = sh
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,14 +390,10 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
+                # WRONG: pollute the read-only construction input on the way out.
+                self.has_param = False
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -387,17 +387,17 @@
     # impl-start
     if not self.fitted:
         if self.has_param:
-            if usable_terms(self.param):
+            if usable_terms(self.param) and len(self.param) > 1:
                 materialise_from_param(self)
+            elif usable_terms(self.param):
+                # WRONG (partial domain): a one-term ctor list is a perfectly
+                # usable vocabulary, but this impl reports the unfitted-object
+                # failure for it.
+                self.supplied = False
+                raise NotFittedError()
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -401,8 +401,8 @@
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
-    j = 0
-    while j < len(self.names):
+    j = len(self.names)
+    while j > 0:
         # invariants-start
         Invariant(Acc(self.names) and Acc(list_pred(self.names)))
         Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
@@ -410,39 +410,22 @@
         Invariant(Acc(self.fitted) and self.fitted)
         Invariant(Acc(list_pred(self.param), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        # The construction inputs are only read, so they still hold their entry
-        # values on every pass.
         Invariant(self.has_param == Old(self.has_param))
         Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
-        # The mapping being reported is numbered by place throughout: the copy
-        # below reads it, it does not re-index it.
         Invariant(numbered_by_place(self.idx, self.names))
-        # Whenever the object was not already fitted, a usable construction-
-        # supplied list is what materialised it: the object records a supplied-
-        # at-construction vocabulary, and the materialised names equal that list.
-        # These facts are stable across the loop below.
         Invariant(Implies(not Old(self.fitted),
                           Old(self.has_param) and Old(usable_terms(self.param))
                           and self.supplied
                           and ToSeq(self.names) == ToSeq(self.param)))
-        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
-        # re-indexed the mapping, so both of its halves and the supplied-at-
-        # construction record are still the ones the object came in with.
         Invariant(Implies(Old(self.fitted),
                           ToSeq(self.names) == Old(ToSeq(self.names))
                           and ToSeq(self.idx) == Old(ToSeq(self.idx))
                           and self.supplied == Old(self.supplied)))
         Invariant(0 <= j and j <= len(self.names))
-        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
-        # At most len(self.names) - j + 1 passes remain: the materialised mapping
-        # is held by the invariant above so its length cannot change, and j rises
-        # by exactly one per pass, so the bound strictly decreases; the loop guard
-        # j < len(self.names) keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(self.names) - j + 1))
+        Invariant(MustTerminate(j + 1))
         # invariants-end
-        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
-        result.append(self.names[j])
-        j = j + 1
-    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
+        # WRONG: report the mapping in DESCENDING index order.
+        result.append(self.names[j - 1])
+        j = j - 1
     return result
     # impl-end
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -400,6 +400,12 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        if self.has_param and not usable_terms(self.names):
+            # DEAD in the model (the representation invariant makes an
+            # already-present mapping usable), so this rebuild never runs.
+            Assert(False)
+            materialise_from_param(self)
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,16 +390,15 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        if self.has_param and usable_terms(self.param):
+            # WRONG (oracle echo): overwrite the LEARNED mapping with the ctor
+            # list, as if `param` were always the answer.
+            materialise_from_param(self)
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

```diff
@@ -385,19 +385,12 @@
             and ToSeq(self.param) == Old(ToSeq(self.param)))
     # post-conditions-end
     # impl-start
-    if not self.fitted:
+    if self.has_param and usable_terms(self.param):
+        materialise_from_param(self)
+    elif not self.fitted:
         if self.has_param:
-            if usable_terms(self.param):
-                materialise_from_param(self)
-            else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
-                raise UnusableTermsError()
+            raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

```diff
@@ -400,6 +400,10 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        # WRONG: claim the vocabulary was supplied at construction even for a
+        # mapping that was LEARNED from data.
+        self.supplied = True
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good)

```diff
@@ -254,7 +254,12 @@
     self.names = new_names
     self.idx = new_idx
     self.fitted = True
-    self.supplied = True
+    if len(self.param) == 1:
+        # WRONG (helper partial domain): a one-term ctor list does not get the
+        # supplied-at-construction record.
+        self.supplied = self.supplied
+    else:
+        self.supplied = True
     # impl-end
 
 
```

Attack 22 — `atk_22.py` → rejected (same spec, does not verify — good)

```diff
@@ -402,7 +402,7 @@
             raise NotFittedError()
     result = []  # type: List[int]
     j = 0
-    while j < len(self.names):
+    while j + 1 < len(self.names):
         # invariants-start
         Invariant(Acc(self.names) and Acc(list_pred(self.names)))
         Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
```

Attack 23 — `atk_23.py` → rejected (same spec, does not verify — good)

```diff
@@ -390,16 +390,12 @@
             if usable_terms(self.param):
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
+            # WRONG: the no-list object gets the rejection, not the
+            # unfitted-object failure.
             self.supplied = False
-            raise NotFittedError()
+            raise UnusableTermsError()
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

Attack 24 — `atk_24.py` → rejected (same spec, does not verify — good)

```diff
@@ -388,16 +388,26 @@
     if not self.fitted:
         if self.has_param:
             if usable_terms(self.param):
-                materialise_from_param(self)
+                # WRONG: report the ctor list but never materialise the mapping
+                # (no vocabulary_ installed, no fixed_vocabulary_ recorded).
+                res0 = []  # type: List[int]
+                p = 0
+                while p < len(self.param):
+                    # invariants-start
+                    Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
+                    Invariant(Acc(list_pred(res0)))
+                    Invariant(0 <= p and p <= len(self.param) and not isinstance(p, bool))
+                    Invariant(ToSeq(res0) == ToSeq(self.param).take(p))
+                    Invariant(MustTerminate(len(self.param) - p + 1))
+                    # invariants-end
+                    Assert(ToSeq(self.param).take(p + 1).drop(p)[0] == self.param[p])
+                    res0.append(self.param[p])
+                    p = p + 1
+                Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
+                return res0
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good)

```diff
@@ -387,17 +387,13 @@
     # impl-start
     if not self.fitted:
         if self.has_param:
-            if usable_terms(self.param):
+            if len(self.param) > 0:
+                # WRONG: the materialise primitive is invoked OUTSIDE its
+                # domain -- a list with a repeated term reaches it.
                 materialise_from_param(self)
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good)

```diff
@@ -410,39 +410,24 @@
         Invariant(Acc(self.fitted) and self.fitted)
         Invariant(Acc(list_pred(self.param), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        # The construction inputs are only read, so they still hold their entry
-        # values on every pass.
         Invariant(self.has_param == Old(self.has_param))
         Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
-        # The mapping being reported is numbered by place throughout: the copy
-        # below reads it, it does not re-index it.
         Invariant(numbered_by_place(self.idx, self.names))
-        # Whenever the object was not already fitted, a usable construction-
-        # supplied list is what materialised it: the object records a supplied-
-        # at-construction vocabulary, and the materialised names equal that list.
-        # These facts are stable across the loop below.
         Invariant(Implies(not Old(self.fitted),
                           Old(self.has_param) and Old(usable_terms(self.param))
                           and self.supplied
                           and ToSeq(self.names) == ToSeq(self.param)))
-        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
-        # re-indexed the mapping, so both of its halves and the supplied-at-
-        # construction record are still the ones the object came in with.
         Invariant(Implies(Old(self.fitted),
                           ToSeq(self.names) == Old(ToSeq(self.names))
                           and ToSeq(self.idx) == Old(ToSeq(self.idx))
                           and self.supplied == Old(self.supplied)))
         Invariant(0 <= j and j <= len(self.names))
-        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
-        # At most len(self.names) - j + 1 passes remain: the materialised mapping
-        # is held by the invariant above so its length cannot change, and j rises
-        # by exactly one per pass, so the bound strictly decreases; the loop guard
-        # j < len(self.names) keeps it >= 2 on entry to a pass.
+        Invariant(ToSeq(result) == places(j))
         Invariant(MustTerminate(len(self.names) - j + 1))
         # invariants-end
-        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
-        result.append(self.names[j])
+        # WRONG (oracle echo): report the spec's own place vocabulary, not the
+        # mapping's names.
+        result.append(j)
         j = j + 1
-    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
     return result
     # impl-end
```

Attack 27 — `atk_27.py` → rejected (same spec, does not verify — good)

```diff
@@ -389,15 +389,12 @@
         if self.has_param:
             if usable_terms(self.param):
                 materialise_from_param(self)
+                # WRONG: clear the read-only construction input on the SUCCESS
+                # path (real: self.vocabulary is never assigned).
+                self.has_param = False
             else:
-                # A supplied list that cannot become a mapping: the materialise
-                # step reports its rejection and writes nothing at all.
                 raise UnusableTermsError()
         else:
-            # The on-demand materialise step runs on the unfitted object; with
-            # no construction-supplied list it builds nothing but records that
-            # the vocabulary was not supplied at construction, and the failure
-            # then surfaces.
             self.supplied = False
             raise NotFittedError()
     result = []  # type: List[int]
```

Attack 28 — `atk_28.py` → rejected (same spec, does not verify — good)

```diff
@@ -400,6 +400,16 @@
             # then surfaces.
             self.supplied = False
             raise NotFittedError()
+    else:
+        # WRONG: shrink the already-present mapping to its first term, keeping
+        # BOTH halves consistent (names + positional idx).
+        tn = []  # type: List[int]
+        tix = []  # type: List[int]
+        Assert(len(self.names) > 0)
+        tn.append(self.names[0])
+        tix.append(0)
+        self.names = tn
+        self.idx = tix
     result = []  # type: List[int]
     j = 0
     while j < len(self.names):
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10908.

Behaviour under specification (a self-standing behavioural contract):

  A text-vectoriser object exposes a query that returns the ordered list of
  feature names. The object can reach a usable state in two ways:

    * it has already been fitted from data (its learned name-to-index mapping is
      materialised on the object); or
    * a name list was supplied to the object at construction time. In this case
      the materialised mapping has not yet been built, but a usable supplied
      list is enough to build it on demand.

  A supplied name list is usable as a source for the mapping exactly when it is
  non-empty and lists no name twice; the materialise step rejects any other
  list, since it could not assign every name its own index.

  The desired behaviour of the feature-name query:

    * If the materialised mapping is not yet present but a name list WAS supplied
      at construction, the query first materialises the mapping from that
      supplied list — exactly as a transform query already does — recording that
      the object's vocabulary was supplied at construction, and then returns the
      feature names. If that supplied list is not usable, the materialise step's
      own rejection surfaces and the object is left untouched.
    * If the materialised mapping is already present, the query returns its
      feature names directly, leaving that mapping as it found it.
    * The query reports an unfitted-object failure ONLY when the object is
      genuinely unusable: no materialised mapping AND no construction-supplied
      list. A construction-supplied list must never trigger that failure.

  The query is an observation, not a reconfiguration: the only mapping it ever
  writes is one it materialises on an object that had none. It never alters a
  mapping that is already present, and it never alters the construction-supplied
  list, nor whether a list was supplied at construction.

  The returned feature names are the mapping's terms in ascending index order.
  When the mapping is materialised from a construction-supplied list, term i of
  that list is assigned index i, so the returned names equal the supplied list
  in its original order; and the object then records that its vocabulary was
  supplied at construction.

  A mapping has TWO observable halves, and the query answers for both: WHICH
  names it holds (reported in ascending index order) and WHICH index each of
  those names carries. The second half is what makes the first meaningful — a
  name's index is the column it addresses everywhere else — and a materialised
  mapping numbers its names BY THEIR PLACE in that reported order: the name
  reported at place k is the one the mapping sends to index k. So:

    * a mapping materialised from a construction-supplied list numbers term i of
      that list i (place = index, as above); and
    * a mapping that was already present is still numbered by place when the
      query is done. The query may not RENUMBER the mapping it reports on, not
      even while leaving the reported names themselves exactly where they were:
      re-indexing the very names it is reporting would move every one of them to
      a place other than the one it is reported at.

Feature names (opaque term identifiers) are modelled as `List[int]`; a
materialised mapping is carried as the parallel pair `names` (its terms in
ascending index order) and `idx` (the index each of those terms carries, in that
same order), so a renumbering is a state change the model can express and the
contract can forbid. A materialised mapping is a name-to-index correspondence, so
its index-ordered names are themselves usable in the above sense — non-empty and
repetition-free — and it is numbered by place; only such states denote a real
object. The materialise-from-supplied-list primitive is the unchanged routine a
transform query already uses; its effect (build the mapping, record the supplied-
at-construction vocabulary) and its usable-list domain are modelled deeply as a
contracted helper and validated == the real routine out-of-band (axiom_check.py /
G-AX). Both failures are user-defined exception classes (a builtin exception in
an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class NotFittedError(Exception):
    """The unfitted-object failure surfaced when the object is genuinely
    unusable (no materialised mapping and no construction-supplied list).
    User-defined stand-in (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass

class UnusableTermsError(Exception):
    """The rejection the materialise step reports for a construction-supplied
    name list it cannot turn into a mapping (empty, or a name listed twice).
    User-defined stand-in, as above (mapping.md §2)."""
    pass

class Vectoriser:
    """The vectoriser object, carrying only the fields the feature-name query
    observes. `fitted` records whether the materialised name-to-index mapping is
    present; `has_param` records whether a name list was supplied at
    construction; `param` is that supplied list (its terms in order, meaningful
    only when `has_param`); `supplied` records whether the object reports that
    its vocabulary was supplied at construction; `names` is the materialised
    mapping viewed as its terms in ascending index order, and `idx` is the index
    each of those terms carries, listed in that same order — the two together are
    the mapping, so `idx` is what makes a renumbering of it observable."""

    def __init__(self, fitted: bool, has_param: bool, supplied: bool,
                 param: List[int], names: List[int], idx: List[int]) -> None:
        Requires(Acc(list_pred(param)) and Acc(list_pred(names)))
        Requires(Acc(list_pred(idx)))
        # Constructing a vectoriser is a bounded step (six field writes); its
        # level (1) sits strictly below every obligated method above it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.fitted) and self.fitted == fitted)  # type: ignore
        Ensures(Acc(self.has_param) and self.has_param == has_param)  # type: ignore
        Ensures(Acc(self.supplied) and self.supplied == supplied)  # type: ignore
        Ensures(Acc(self.param) and self.param is param)  # type: ignore
        Ensures(Acc(self.names) and self.names is names)  # type: ignore
        Ensures(Acc(self.idx) and self.idx is idx)  # type: ignore
        Ensures(Acc(list_pred(self.param)) and Acc(list_pred(self.names)))  # type: ignore
        Ensures(Acc(list_pred(self.idx)))  # type: ignore
        self.fitted = fitted
        self.has_param = has_param
        self.supplied = supplied
        self.param = param
        self.names = names
        self.idx = idx

# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged callee the query
#  invokes — the materialise-from-supplied-list routine — is modelled DEEPLY as
#  the contracted helper `materialise_from_param` below, an A-reference validated
#  == the real routine by axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def usable_terms(xs: List[int]) -> bool:
    """A term list can serve as a name-to-index mapping exactly when it is
    non-empty and no term is listed twice — only then does every term get its
    own index. Both the construction-supplied list (which an arbitrary caller
    may hand over in any shape) and the materialised mapping's index-ordered
    names satisfy this of a usable object."""
    Requires(Acc(list_pred(xs), 1 / 4))
    return len(xs) > 0 and Forall(int, lambda i: (Forall(int, lambda j: (
        Implies(0 <= i and i < j and j < len(xs), xs[i] != xs[j]),
        [[xs[i], xs[j]]])), []))

@Pure
def places(n: int) -> PSeq[int]:
    """The first n places, in order: 0, 1, ..., n-1. (Recursion on n, which
    strictly decreases towards the n <= 0 base case, so this is a total
    function; it is spec-only vocabulary for saying WHICH index a name at a
    given place carries.)"""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n <= 0:
        return PSeq(0).take(0)
    return places(n - 1) + PSeq(n - 1)

@Pure
def numbered_by_place(idx: List[int], names: List[int]) -> bool:
    """A materialised mapping is numbered BY PLACE: every one of its names
    carries an index (the two lists run in parallel), and the name at place k
    carries index k — i.e. the indices, read in the order the names are
    reported, are exactly 0, 1, ..., len(names)-1. This is the half of the
    mapping the reported name order alone cannot show — it is what distinguishes
    the mapping that sends the k-th reported name to k from any other mapping
    holding those same names in that same ascending order."""
    Requires(Acc(list_pred(idx), 1 / 4) and Acc(list_pred(names), 1 / 4))
    return len(idx) == len(names) and ToSeq(idx) == places(len(names))
# pure-end

def materialise_from_param(self: Vectoriser) -> None:
    """The unchanged materialise-from-supplied-list primitive (the routine a
    transform query already uses). Precondition: a USABLE name list was supplied
    at construction. Effect: build the materialised mapping from that list —
    term i of the list gets index i, so the index-ordered names equal the
    supplied list and the mapping it builds is numbered by place — and record
    that the object's vocabulary was supplied at construction. Its effect and its
    usable-list domain are modelled deeply here and validated == the real routine
    by axiom_check.py (G-AX)."""
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(self.has_param)
    # The routine builds a mapping, so it is only defined on a list that CAN be
    # one: an empty list or a repeated term is rejected instead (the caller
    # screens for this before invoking the step).
    Requires(usable_terms(self.param))
    # The materialise step must COMPLETE: without this the postconditions below
    # are claimed only of runs that reach the return, and an implementation that
    # spins forever would satisfy them vacuously. Level 2 leaves room for the
    # list allocation it performs (level 1 leaks `list.__init__`'s obligation).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2) and Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(self.has_param)
    # The step READS the supplied list to build the mapping; the object still
    # carries that same supplied list, unchanged, afterwards.
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # The mapping is now materialised, the object records a supplied-at-
    # construction vocabulary, and the index-ordered feature names equal the
    # supplied list in its order.
    Ensures(self.fitted)
    Ensures(self.supplied)
    Ensures(ToSeq(self.names) == ToSeq(self.param))
    # Term i of the supplied list is given index i, so the mapping this step
    # builds is numbered by place: taken with the clause above, the name at
    # place k of the supplied list is the one the new mapping sends to k.
    Ensures(numbered_by_place(self.idx, self.names))
    # post-conditions-end
    # impl-start
    new_names = []  # type: List[int]
    new_idx = []  # type: List[int]
    k = 0
    while k < len(self.param):
        # invariants-start
        Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(new_names)) and Acc(list_pred(new_idx)))
        # The supplied list is only read, so it still holds its entry value.
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # (`not isinstance(k, bool)` is a proof hint, not an obligation: the
        # counter is a plain int, which the verifier needs spelled out because
        # `bool` is a subtype of `int`.)
        Invariant(0 <= k and k <= len(self.param) and not isinstance(k, bool))
        Invariant(ToSeq(new_names) == ToSeq(self.param).take(k))
        # The two halves are built together: place t of the part built so far
        # carries index t, i.e. the indices assigned so far are the places
        # 0 .. k-1 in order.
        Invariant(len(new_idx) == k)
        Invariant(ToSeq(new_idx) == places(k))
        # At most len(self.param) - k + 1 passes remain: the supplied list is
        # held (read-only) by the invariant above so its length cannot change,
        # and k rises by exactly one per pass, so the bound strictly decreases;
        # the loop guard k < len(self.param) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.param) - k + 1))
        # invariants-end
        Assert(ToSeq(self.param).take(k + 1).drop(k)[0] == self.param[k])
        new_names.append(self.param[k])
        new_idx.append(k)
        k = k + 1
    Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
    Assert(len(new_names) == k and len(new_idx) == k)
    Assert(places(len(new_names)) == places(k))
    self.names = new_names
    self.idx = new_idx
    self.fitted = True
    self.supplied = True
    # impl-end

def get_feature_names(self: Vectoriser) -> List[int]:
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(Acc(list_pred(self.names)))
    Requires(Acc(list_pred(self.idx)))
    # A materialised mapping is a name-to-index correspondence, so on an already
    # fitted object its index-ordered names are themselves a usable term list
    # (non-empty, no repetition). This is the representation invariant of the
    # materialised mapping, not a restriction on the caller's supplied list:
    # `param` below is left entirely unconstrained.
    Requires(Implies(self.fitted, usable_terms(self.names)))
    # The other half of that same representation invariant: a materialised
    # mapping is numbered by place. Every way a mapping comes into being numbers
    # it that way — materialising a supplied list of n names uses places 0..n-1,
    # and so does learning one from data — so this is what an already-materialised
    # mapping IS, not a case being ducked. It is stated here because the exit
    # clause below claims the same of the mapping the query leaves behind, and
    # that claim would be unfaithful of a mapping that arrived numbered some other
    # way: this query reports a mapping, it does not repair one.
    Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))
    # The query must COMPLETE (total correctness): without this obligation every
    # Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 3 is strictly above materialise_from_param's 2 (the callee
    # it invokes) and leaves room for the list allocation it performs.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2))
    Ensures(Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(Acc(list_pred(Result())))
    # The object ends usable: a materialised mapping is present.
    Ensures(self.fitted)
    # The returned feature names are the object's materialised mapping in index
    # order.
    Ensures(ToSeq(Result()) == ToSeq(self.names))
    # ... and that mapping is numbered by place, so the two clauses together say
    # WHICH index every returned name carries: the name at place k of the returned
    # list is the one the mapping the object now holds sends to index k. A query
    # that reported these very names while the mapping sent them to any other
    # indices would satisfy the clause above and violate this one.
    Ensures(numbered_by_place(self.idx, self.names))
    # This query reports names; it does not reconfigure the object it is asked
    # about. Whether a name list was supplied at construction, and that supplied
    # list itself, therefore hold their entry values when the query is done. This
    # is true on every exit, the two failures included (restated there below).
    Ensures(self.has_param == Old(self.has_param))
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # When the object was NOT already fitted, a USABLE construction-supplied list
    # is what made it usable: such a list must have been supplied, it is now
    # materialised AND recorded as supplied-at-construction, and the returned
    # names equal that supplied list in order. (This is exactly the case the
    # unfitted-object failure must NOT be raised on. Requiring the supplied list
    # to have been usable is what forbids returning it when it was not: that
    # case has to exit through the rejection below instead.)
    Ensures(Implies(not Old(self.fitted),
                    Old(self.has_param) and Old(usable_terms(self.param))
                    and self.supplied
                    and ToSeq(Result()) == ToSeq(self.param)))
    # When the materialised mapping was ALREADY present, the query only reads
    # it: the mapping the object carries afterwards, and its record of whether
    # its vocabulary was supplied at construction, are the ones it came in with,
    # and the names reported are that same already-present mapping in index
    # order. Nothing about an already-usable object is re-derived, and no
    # feature name it already had can go missing or change place, and no name it
    # already had is re-indexed: BOTH halves of the mapping — its names in index
    # order and the index each of them carries — come back out as they went in.
    Ensures(Implies(Old(self.fitted),
                    ToSeq(self.names) == Old(ToSeq(self.names))
                    and ToSeq(self.idx) == Old(ToSeq(self.idx))
                    and self.supplied == Old(self.supplied)
                    and ToSeq(Result()) == Old(ToSeq(self.names))))
    # The unfitted-object failure is raised ONLY when the object is genuinely
    # unusable: not already fitted AND no construction-supplied list. (The
    # access predicates are restored so the caller may inspect the object.)
    # `has_param` (whether a list was supplied at construction) is a read-only
    # input to this query; the discriminating clauses read its pre-state
    # (`Old(self.has_param)`) so an impl cannot vacate them by overwriting it.
    # On this genuinely-unusable path the on-demand materialise step runs and,
    # finding no list to build from, records that the object's vocabulary was
    # NOT supplied at construction (`not self.supplied`) before the failure
    # surfaces — a load-bearing side effect the query must reproduce, so an impl
    # that merely fails without recording it does NOT satisfy this clause. That
    # record is also the ONLY thing this exit changes: with no list to build
    # from, no mapping is materialised (the object is still not fitted, and both
    # halves of the mapping view it came in with — its names and their indices —
    # are untouched) and the construction inputs keep their entry values.
    Exsures(NotFittedError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and not Old(self.has_param)
            and not self.supplied
            and not self.fitted
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # The materialise step's own rejection is reported ONLY when there was a
    # mapping to build and it could not be built: not already fitted, a list WAS
    # supplied at construction, and that list was not usable (empty, or a term
    # listed twice). On this path the step builds nothing and records nothing, so
    # the object is left exactly as it was — no mapping is materialised and the
    # supplied-at-construction flag keeps its entry value, as do both halves of
    # the mapping view and the construction-supplied list.
    Exsures(UnusableTermsError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and Old(self.has_param)
            and not Old(usable_terms(self.param))
            and not self.fitted and self.supplied == Old(self.supplied)
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # post-conditions-end
    # impl-start
    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # A supplied list that cannot become a mapping: the materialise
                # step reports its rejection and writes nothing at all.
                raise UnusableTermsError()
        else:
            # The on-demand materialise step runs on the unfitted object; with
            # no construction-supplied list it builds nothing but records that
            # the vocabulary was not supplied at construction, and the failure
            # then surfaces.
            self.supplied = False
            raise NotFittedError()
    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        # invariants-start
        Invariant(Acc(self.names) and Acc(list_pred(self.names)))
        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
        Invariant(Acc(self.fitted) and self.fitted)
        Invariant(Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # The construction inputs are only read, so they still hold their entry
        # values on every pass.
        Invariant(self.has_param == Old(self.has_param))
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # The mapping being reported is numbered by place throughout: the copy
        # below reads it, it does not re-index it.
        Invariant(numbered_by_place(self.idx, self.names))
        # Whenever the object was not already fitted, a usable construction-
        # supplied list is what materialised it: the object records a supplied-
        # at-construction vocabulary, and the materialised names equal that list.
        # These facts are stable across the loop below.
        Invariant(Implies(not Old(self.fitted),
                          Old(self.has_param) and Old(usable_terms(self.param))
                          and self.supplied
                          and ToSeq(self.names) == ToSeq(self.param)))
        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
        # re-indexed the mapping, so both of its halves and the supplied-at-
        # construction record are still the ones the object came in with.
        Invariant(Implies(Old(self.fitted),
                          ToSeq(self.names) == Old(ToSeq(self.names))
                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
                          and self.supplied == Old(self.supplied)))
        Invariant(0 <= j and j <= len(self.names))
        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
        # At most len(self.names) - j + 1 passes remain: the materialised mapping
        # is held by the invariant above so its length cannot change, and j rises
        # by exactly one per pass, so the bound strictly decreases; the loop guard
        # j < len(self.names) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.names) - j + 1))
        # invariants-end
        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
        result.append(self.names[j])
        j = j + 1
    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — scikit-learn__scikit-learn-10908 / nagini. All attacks built by copying the bundle model.py and editing ONLY impl regions; all 28 confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-10908 <f>` (exit 0 each).

**POSITIVE CONTROL:** `bash scripts/nagini_verify.sh pc.py` -> "Verification successful" (20.28s), exit 0.

**PREPATCH REPRODUCED:** atk_1.py is the pre-patch skeleton (`if not self.fitted: raise NotFittedError()`), matching model_prepatch.py's impl region. `adversary weakness` -> NOT-A-COUNTEREXAMPLE (does not verify), exit 2. The spec rejects the pre-patch bug on Exsures(NotFittedError,... not Old(self.has_param)), exactly as refinement.md §B claims.

**COMMANDS:** every attack ran `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-10908 atk_N.py`, in background batches of <=3 (JVM+Z3 per check). Per-attack logs in atk_N.log.

### REJECTED (exit 2 = spec rejected the wrong impl; 24 of 28):
- atk_1 prepatch skeleton (no on-demand materialisation)
- atk_2 raise WITHOUT recording `not supplied` (the pre-patch `_check_vocabulary`-only refinement refinement.md §B says must be forbidden) -> rejected, confirming that leg bites
- atk_3 fitted-path RENUMBER idx:=`2*k`, names untouched (the sneaky renumbering family A8 exists for) -> rejected by Ensures(numbered_by_place)
- atk_4 fitted-path WIPE of the already-present mapping
- atk_5 return self.names (alias) instead of a fresh copy -> rejected by Acc(list_pred(Result())) + Acc(list_pred(self.names)), confirming A5's copy claim is enforced
- atk_7 EXIT SWAP: NotFittedError for an unusable ctor list
- atk_8 control-flow EFFECT: write supplied=False on the rejection path that must write nothing (A3b)
- atk_9 materialise by ALIASING the ctor list into self.names
- atk_12 DIVERGENCE (`while... or True`) — MustTerminate(3) vacuity probe rejected
- atk_13 materialise then renumber the FRESH mapping to k+1
- atk_14 overwrite has_param on the rejection exit (vacate a discriminating Old)
- atk_15 PARTIAL DOMAIN on a REACHABLE guard: refuse singleton ctor lists
- atk_16 report the mapping in DESCENDING index order
- atk_18 UNGROUNDED-ORACLE ECHO: overwrite a LEARNED mapping with the ctor list
- atk_19 always materialise from param, ignoring fitted
- atk_20 claim supplied=True on the already-fitted LEARNED path
- atk_21 HELPER-REGION partial domain: materialise_from_param skips the supplied record for a one-term list (the A-reference's own impl region attacked)
- atk_22 BOUNDARY: drop the last feature name (`j + 1 < len`)
- atk_23 EXIT SWAP other way: UnusableTermsError on the no-list object
- atk_24 return the ctor list WITHOUT materialising (no mapping installed)
- atk_25 A-REFERENCE DOMAIN BOUNDARY: invoke materialise_from_param under a weakened guard (`len>0` only), i.e. outside its usable_terms domain -> rejected, so the A-reference's precondition is load-bearing at the call site
- atk_26 UNGROUNDED-ORACLE ECHO: report places() (the spec's own vocabulary) instead of the mapping's names
- atk_27 SUCCESS-PATH frame violation: clear has_param after materialising
- atk_28 fitted-path TRUNCATE to first term with BOTH halves kept internally consistent (cannot be dismissed as a half-updated representation)

CANDIDATES (exit 0 = shares spec AND verifies; 4 of 28) — every one had its faithful refined patch MATERIALIZED and EXECUTED through the official harness via swebench_unified.harness.run_resolve (driver do_resolve.py, JSON reports in resolve_atk_N.json):
1. atk_6.py — A-REFERENCE BYPASS. Instead of invoking the deep-modelled materialise primitive, the impl inlines the same loop (build names/idx from param, set fitted+supplied). Verifies in 22.8s. Faithful patch = inline `_validate_vocabulary`'s LIST branch into get_feature_names (the model's carrier is param: List[int], so the list branch is what is refined). RESOLVE: resolved=True completed=True note='resolved', F2P 1/1 success, P2P 47/47 success, PASS_TO_FAIL 0, patch_successfully_applied=True. => NOT a counterexample: the bypass is behaviourally equal, because the deep helper's contract pins exactly the real routine's list-branch effect. This is the strongest available evidence FOR the A-reference leg, not against it.
2. atk_10.py — PARTIAL-DOMAIN / dead-branch probe on an EMPTY already-present mapping. Verifies in 28.2s; the branch carries Assert(False) which PASSES, i.e. the branch is genuinely infeasible under Requires(Implies(self.fitted, usable_terms(self.names))). Faithful patch guards the same condition (`elif len(self.vocabulary_) == 0: self.vocabulary_ = {}`). RESOLVE: resolved=True, F2P 1/1, P2P 47/47. => Not a counterexample. Audited for honesty: the guard is unreachable in the REAL repo too — `_validate_vocabulary` raises "empty vocabulary passed to fit" (text.py:295) before installing vocabulary_, `_limit_features` raises "After pruning, no terms remain" (text.py:793) and `_count_vocab` raises "empty vocabulary" (text.py:834), so no code path yields a fitted object with an empty vocabulary_; and `_check_vocabulary` would raise ValueError anyway. So the representation invariant excludes no reachable state, as refinement.md A8 asserts.
3. atk_11.py — PARTIAL-DOMAIN / dead-branch probe on a NON-POSITIONALLY-numbered already-present mapping (Assert(False) passes under Requires(Implies(self.fitted, numbered_by_place(...)))). Faithful patch guards the same condition (compare the index-ordered indices to range(len)) and wipes on it. RESOLVE: resolved=True, F2P 1/1, P2P 47/47. => Not a counterexample; corroborates A8's claim that every repo site installing a vocabulary_ numbers it by place (enumerate at text.py:280, the Mapping bijection guards at text.py:286-293, `_sort_features`' enumerate at text.py:749-751, `_limit_features`' cumsum at text.py:783-789).
4. atk_17.py — GUARDED SELF-CALL VACUITY probe: re-invoke materialise_from_param on an already-fitted object under the infeasible guard `has_param and not usable_terms(self.names)`. Verifies in 34.2s with Assert(False) passing (per my MEMORY note that an infeasible guard verifies while proving nothing — so it needed the resolve run, not speculation). Faithful patch: `elif self.vocabulary is not None and len(self.vocabulary_) == 0: self._validate_vocabulary()`. RESOLVE: resolved=True completed=True, F2P 1/1, P2P 47/47. => Not a counterexample.

All four resolve reports show real test execution (not vacuous/short-circuited): patch_successfully_applied=True, FAIL_TO_PASS 1 success / 0 failure, PASS_TO_PASS 47 success / 0 failure, PASS_TO_FAIL empty. Content-addressed run_ids (sbu-geq-audit-atkN) so no stale-report short-circuit.

### REFINEMENT.MD LEG AUDIT (A-legs, per instruction focus):
- Leg tag census: 1 A-reference (A3), 2 R (A1, A2), 6 R+I (A3b, A4, A5, A6, A7, A8). ZERO A-consumed and ZERO kind-3 (unexpressible-changed-op). §C's claim of no kind-3 holds: the operation that actually changed (the guarded on-demand materialisation) is modelled DIRECTLY as impl control flow (A2 guard -> A3 / A3b / A4), which is exactly what model_prepatch.py deletes.
- No @ContractOnly appears anywhere in model.py (only the prose note at line 129), so the "no consumed axiom, hence no dead axiom" claim is literally true; there is no axiom about the function under change.
- The single A-reference (A3: materialise_from_param == the unchanged `_validate_vocabulary`) checks out against the base-commit source I extracted (text_base.py from 67d06b18): the routine's list-branch acceptance condition is exactly non-empty AND no repeated term — `vocab.setdefault(t, i) != i` raises on a repeat (text.py:280-283) and `if not vocabulary` raises on empty (text.py:294-295) — which is precisely `usable_terms`. Both rejections occur BEFORE the two writes at text.py:296-297, matching the Exsures' write-nothing claim. The effect claims match term-for-term: fixed_vocabulary_=True <-> self.supplied, vocabulary_=dict(vocab) <-> (names, idx) with term i at index i <-> numbered_by_place. The `vocabulary is None` else-branch sets fixed_vocabulary_=False and no vocabulary_ (text.py:299), which is exactly A4's modelled `self.supplied = False; raise NotFittedError()` — and atk_2 (omit that record) is REJECTED, so the leg is enforced, not merely asserted.
- The A-reference's domain bound is load-bearing at the call site: atk_25 (invoke the helper under `len>0` only) FAILS verification, so an impl cannot smuggle a repeated-term list into the primitive.
- A5's copy-not-alias claim is enforced (atk_5 rejected), A6's fitted-path frame is enforced (atk_4, atk_28 rejected), A7's read-only construction inputs are enforced on both the failure and success paths (atk_14, atk_27 rejected), A8's numbering is enforced (atk_3, atk_13, atk_16, atk_26 rejected).
- patch.diff is byte-identical to instance.json's gold `patch` field (verified), so the correctness oracle is the real one.

MODEL<->PATCH CORRESPONDENCE: the model's carrier is (fitted, has_param, supplied, param, names, idx) <-> (hasattr vocabulary_, vocabulary is not None, fixed_vocabulary_, ctor list, index-ordered terms, their indices). The two-half mapping carrier is necessary and not decorative: the renumbering family (atk_3, atk_13) is invisible to any names-only carrier and is caught only by the idx component; the F2P test patch's added `for idx, name in enumerate(feature_names): assert_equal(idx, cv.vocabulary_.get(name))` (test_text.py:573-574) is the observable that makes this refinement non-lossy. I confirmed the F2P/P2P sets: F2P is test_feature_names alone, and 47 P2P tests are in test_text.py, including test_countvectorizer_empty_vocabulary, test_non_unique_vocab and test_countvectorizer_custom_vocabulary_repeated_indices — the exact classes A3b models.

RESIDUAL RISK / SCOPE HONESTY: the model refines only the ctor-LIST vocabulary shape (param: List[int]); the real routine also accepts a set (sorted first, text.py:277) and a Mapping (validated by the two index guards, text.py:286-293). Those shapes are not in the model's carrier, so a wrong impl that misbehaves ONLY on a dict/set ctor vocabulary is outside what this model can express. I probed the consequence rather than assuming it: atk_6's inline patch reaches the list branch only (never the set/Mapping branches) and still resolves with P2P 47/47 including the dict/set custom-vocabulary and pickling tests, because those tests all go through fit(), not through the unfitted get_feature_names path the patch touches. So the un-modelled shapes are not reachable by the change site and the R restriction is not hiding a resolve-relevant behaviour. mapping.md §2 / refinement.md A1 declare this scope; I record it as a scope note, not a defect.

**VERDICT:** SOUND. 28 same-spec attacks executed (>=5 required), spanning all requested families — prepatch bug, prior-pass counterexamples (the renumber and wipe families refinement.md names), partial-domain (atk_10, atk_11, atk_15, atk_21), boundary (atk_22, atk_25, atk_28), control-flow-effect (atk_8, atk_13, atk_14, atk_27), ungrounded-oracle echo (atk_18, atk_26), A-reference bypass/domain (atk_6, atk_25), exit swap (atk_7, atk_23), aliasing (atk_5, atk_9), and divergence/vacuity (atk_12, atk_17). Every candidate's faithful patch was materialized and RUN through run_resolve, and all four RESOLVED. No verify-but-not-correct implementation was exhibited; refinement.md's legs are all R / A-reference / I with no kind-3 and the A-reference's correspondence to the real `_validate_vocabulary` holds at both its effect and its domain boundary.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 28 admissible attacks re-run of 28 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 28 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 24 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_22.py`, `atk_23.py`, `atk_24.py`, `atk_25.py`, `atk_26.py`, `atk_27.py`, `atk_28.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_10.py`, `atk_11.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 28 same-spec attacks were executed; 4 verified (atk_6, atk_10, atk_11, atk_17) and every one of their materialized faithful refined patches RESOLVED under the official harness (run_resolve: resolved=True, completed=True, F2P 1/1, P2P 47/47, patch_successfully_applied=True). No verifying wrong impl was found whose faithful patch fails to resolve, so no verify=>correct counterexample exists in the families probed.
```

**Attacks re-run (28):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 28 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22.py` → rejected (same spec, does not verify — good)

Attack 23 — `atk_23.py` → rejected (same spec, does not verify — good)

Attack 24 — `atk_24.py` → rejected (same spec, does not verify — good)

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good)

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good)

Attack 27 — `atk_27.py` → rejected (same spec, does not verify — good)

Attack 28 — `atk_28.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10908.

Behaviour under specification (a self-standing behavioural contract):

  A text-vectoriser object exposes a query that returns the ordered list of
  feature names. The object can reach a usable state in two ways:

    * it has already been fitted from data (its learned name-to-index mapping is
      materialised on the object); or
    * a name list was supplied to the object at construction time. In this case
      the materialised mapping has not yet been built, but a usable supplied
      list is enough to build it on demand.

  A supplied name list is usable as a source for the mapping exactly when it is
  non-empty and lists no name twice; the materialise step rejects any other
  list, since it could not assign every name its own index.

  The desired behaviour of the feature-name query:

    * If the materialised mapping is not yet present but a name list WAS supplied
      at construction, the query first materialises the mapping from that
      supplied list — exactly as a transform query already does — recording that
      the object's vocabulary was supplied at construction, and then returns the
      feature names. If that supplied list is not usable, the materialise step's
      own rejection surfaces and the object is left untouched.
    * If the materialised mapping is already present, the query returns its
      feature names directly, leaving that mapping as it found it.
    * The query reports an unfitted-object failure ONLY when the object is
      genuinely unusable: no materialised mapping AND no construction-supplied
      list. A construction-supplied list must never trigger that failure.

  The query is an observation, not a reconfiguration: the only mapping it ever
  writes is one it materialises on an object that had none. It never alters a
  mapping that is already present, and it never alters the construction-supplied
  list, nor whether a list was supplied at construction.

  The returned feature names are the mapping's terms in ascending index order.
  When the mapping is materialised from a construction-supplied list, term i of
  that list is assigned index i, so the returned names equal the supplied list
  in its original order; and the object then records that its vocabulary was
  supplied at construction.

  A mapping has TWO observable halves, and the query answers for both: WHICH
  names it holds (reported in ascending index order) and WHICH index each of
  those names carries. The second half is what makes the first meaningful — a
  name's index is the column it addresses everywhere else — and a materialised
  mapping numbers its names BY THEIR PLACE in that reported order: the name
  reported at place k is the one the mapping sends to index k. So:

    * a mapping materialised from a construction-supplied list numbers term i of
      that list i (place = index, as above); and
    * a mapping that was already present is still numbered by place when the
      query is done. The query may not RENUMBER the mapping it reports on, not
      even while leaving the reported names themselves exactly where they were:
      re-indexing the very names it is reporting would move every one of them to
      a place other than the one it is reported at.

Feature names (opaque term identifiers) are modelled as `List[int]`; a
materialised mapping is carried as the parallel pair `names` (its terms in
ascending index order) and `idx` (the index each of those terms carries, in that
same order), so a renumbering is a state change the model can express and the
contract can forbid. A materialised mapping is a name-to-index correspondence, so
its index-ordered names are themselves usable in the above sense — non-empty and
repetition-free — and it is numbered by place; only such states denote a real
object. The materialise-from-supplied-list primitive is the unchanged routine a
transform query already uses; its effect (build the mapping, record the supplied-
at-construction vocabulary) and its usable-list domain are modelled deeply as a
contracted helper and validated == the real routine out-of-band (axiom_check.py /
G-AX). Both failures are user-defined exception classes (a builtin exception in
an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class NotFittedError(Exception):
    """The unfitted-object failure surfaced when the object is genuinely
    unusable (no materialised mapping and no construction-supplied list).
    User-defined stand-in (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass

class UnusableTermsError(Exception):
    """The rejection the materialise step reports for a construction-supplied
    name list it cannot turn into a mapping (empty, or a name listed twice).
    User-defined stand-in, as above (mapping.md §2)."""
    pass

class Vectoriser:
    """The vectoriser object, carrying only the fields the feature-name query
    observes. `fitted` records whether the materialised name-to-index mapping is
    present; `has_param` records whether a name list was supplied at
    construction; `param` is that supplied list (its terms in order, meaningful
    only when `has_param`); `supplied` records whether the object reports that
    its vocabulary was supplied at construction; `names` is the materialised
    mapping viewed as its terms in ascending index order, and `idx` is the index
    each of those terms carries, listed in that same order — the two together are
    the mapping, so `idx` is what makes a renumbering of it observable."""

    def __init__(self, fitted: bool, has_param: bool, supplied: bool,
                 param: List[int], names: List[int], idx: List[int]) -> None:
        Requires(Acc(list_pred(param)) and Acc(list_pred(names)))
        Requires(Acc(list_pred(idx)))
        # Constructing a vectoriser is a bounded step (six field writes); its
        # level (1) sits strictly below every obligated method above it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.fitted) and self.fitted == fitted)  # type: ignore
        Ensures(Acc(self.has_param) and self.has_param == has_param)  # type: ignore
        Ensures(Acc(self.supplied) and self.supplied == supplied)  # type: ignore
        Ensures(Acc(self.param) and self.param is param)  # type: ignore
        Ensures(Acc(self.names) and self.names is names)  # type: ignore
        Ensures(Acc(self.idx) and self.idx is idx)  # type: ignore
        Ensures(Acc(list_pred(self.param)) and Acc(list_pred(self.names)))  # type: ignore
        Ensures(Acc(list_pred(self.idx)))  # type: ignore
        self.fitted = fitted
        self.has_param = has_param
        self.supplied = supplied
        self.param = param
        self.names = names
        self.idx = idx

# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged callee the query
#  invokes — the materialise-from-supplied-list routine — is modelled DEEPLY as
#  the contracted helper `materialise_from_param` below, an A-reference validated
#  == the real routine by axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def usable_terms(xs: List[int]) -> bool:
    """A term list can serve as a name-to-index mapping exactly when it is
    non-empty and no term is listed twice — only then does every term get its
    own index. Both the construction-supplied list (which an arbitrary caller
    may hand over in any shape) and the materialised mapping's index-ordered
    names satisfy this of a usable object."""
    Requires(Acc(list_pred(xs), 1 / 4))
    return len(xs) > 0 and Forall(int, lambda i: (Forall(int, lambda j: (
        Implies(0 <= i and i < j and j < len(xs), xs[i] != xs[j]),
        [[xs[i], xs[j]]])), []))

@Pure
def places(n: int) -> PSeq[int]:
    """The first n places, in order: 0, 1, ..., n-1. (Recursion on n, which
    strictly decreases towards the n <= 0 base case, so this is a total
    function; it is spec-only vocabulary for saying WHICH index a name at a
    given place carries.)"""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n <= 0:
        return PSeq(0).take(0)
    return places(n - 1) + PSeq(n - 1)

@Pure
def numbered_by_place(idx: List[int], names: List[int]) -> bool:
    """A materialised mapping is numbered BY PLACE: every one of its names
    carries an index (the two lists run in parallel), and the name at place k
    carries index k — i.e. the indices, read in the order the names are
    reported, are exactly 0, 1, ..., len(names)-1. This is the half of the
    mapping the reported name order alone cannot show — it is what distinguishes
    the mapping that sends the k-th reported name to k from any other mapping
    holding those same names in that same ascending order."""
    Requires(Acc(list_pred(idx), 1 / 4) and Acc(list_pred(names), 1 / 4))
    return len(idx) == len(names) and ToSeq(idx) == places(len(names))
# pure-end

def materialise_from_param(self: Vectoriser) -> None:
    """The unchanged materialise-from-supplied-list primitive (the routine a
    transform query already uses). Precondition: a USABLE name list was supplied
    at construction. Effect: build the materialised mapping from that list —
    term i of the list gets index i, so the index-ordered names equal the
    supplied list and the mapping it builds is numbered by place — and record
    that the object's vocabulary was supplied at construction. Its effect and its
    usable-list domain are modelled deeply here and validated == the real routine
    by axiom_check.py (G-AX)."""
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(self.has_param)
    # The routine builds a mapping, so it is only defined on a list that CAN be
    # one: an empty list or a repeated term is rejected instead (the caller
    # screens for this before invoking the step).
    Requires(usable_terms(self.param))
    # The materialise step must COMPLETE: without this the postconditions below
    # are claimed only of runs that reach the return, and an implementation that
    # spins forever would satisfy them vacuously. Level 2 leaves room for the
    # list allocation it performs (level 1 leaks `list.__init__`'s obligation).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2) and Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(self.has_param)
    # The step READS the supplied list to build the mapping; the object still
    # carries that same supplied list, unchanged, afterwards.
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # The mapping is now materialised, the object records a supplied-at-
    # construction vocabulary, and the index-ordered feature names equal the
    # supplied list in its order.
    Ensures(self.fitted)
    Ensures(self.supplied)
    Ensures(ToSeq(self.names) == ToSeq(self.param))
    # Term i of the supplied list is given index i, so the mapping this step
    # builds is numbered by place: taken with the clause above, the name at
    # place k of the supplied list is the one the new mapping sends to k.
    Ensures(numbered_by_place(self.idx, self.names))
    # post-conditions-end
    # impl-start
    new_names = []  # type: List[int]
    new_idx = []  # type: List[int]
    k = 0
    while k < len(self.param):
        # invariants-start
        Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(new_names)) and Acc(list_pred(new_idx)))
        # The supplied list is only read, so it still holds its entry value.
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # (`not isinstance(k, bool)` is a proof hint, not an obligation: the
        # counter is a plain int, which the verifier needs spelled out because
        # `bool` is a subtype of `int`.)
        Invariant(0 <= k and k <= len(self.param) and not isinstance(k, bool))
        Invariant(ToSeq(new_names) == ToSeq(self.param).take(k))
        # The two halves are built together: place t of the part built so far
        # carries index t, i.e. the indices assigned so far are the places
        # 0 .. k-1 in order.
        Invariant(len(new_idx) == k)
        Invariant(ToSeq(new_idx) == places(k))
        # At most len(self.param) - k + 1 passes remain: the supplied list is
        # held (read-only) by the invariant above so its length cannot change,
        # and k rises by exactly one per pass, so the bound strictly decreases;
        # the loop guard k < len(self.param) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.param) - k + 1))
        # invariants-end
        Assert(ToSeq(self.param).take(k + 1).drop(k)[0] == self.param[k])
        new_names.append(self.param[k])
        new_idx.append(k)
        k = k + 1
    Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
    Assert(len(new_names) == k and len(new_idx) == k)
    Assert(places(len(new_names)) == places(k))
    self.names = new_names
    self.idx = new_idx
    self.fitted = True
    self.supplied = True
    # impl-end

def get_feature_names(self: Vectoriser) -> List[int]:
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(Acc(list_pred(self.names)))
    Requires(Acc(list_pred(self.idx)))
    # A materialised mapping is a name-to-index correspondence, so on an already
    # fitted object its index-ordered names are themselves a usable term list
    # (non-empty, no repetition). This is the representation invariant of the
    # materialised mapping, not a restriction on the caller's supplied list:
    # `param` below is left entirely unconstrained.
    Requires(Implies(self.fitted, usable_terms(self.names)))
    # The other half of that same representation invariant: a materialised
    # mapping is numbered by place. Every way a mapping comes into being numbers
    # it that way — materialising a supplied list of n names uses places 0..n-1,
    # and so does learning one from data — so this is what an already-materialised
    # mapping IS, not a case being ducked. It is stated here because the exit
    # clause below claims the same of the mapping the query leaves behind, and
    # that claim would be unfaithful of a mapping that arrived numbered some other
    # way: this query reports a mapping, it does not repair one.
    Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))
    # The query must COMPLETE (total correctness): without this obligation every
    # Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 3 is strictly above materialise_from_param's 2 (the callee
    # it invokes) and leaves room for the list allocation it performs.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2))
    Ensures(Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(Acc(list_pred(Result())))
    # The object ends usable: a materialised mapping is present.
    Ensures(self.fitted)
    # The returned feature names are the object's materialised mapping in index
    # order.
    Ensures(ToSeq(Result()) == ToSeq(self.names))
    # ... and that mapping is numbered by place, so the two clauses together say
    # WHICH index every returned name carries: the name at place k of the returned
    # list is the one the mapping the object now holds sends to index k. A query
    # that reported these very names while the mapping sent them to any other
    # indices would satisfy the clause above and violate this one.
    Ensures(numbered_by_place(self.idx, self.names))
    # This query reports names; it does not reconfigure the object it is asked
    # about. Whether a name list was supplied at construction, and that supplied
    # list itself, therefore hold their entry values when the query is done. This
    # is true on every exit, the two failures included (restated there below).
    Ensures(self.has_param == Old(self.has_param))
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # When the object was NOT already fitted, a USABLE construction-supplied list
    # is what made it usable: such a list must have been supplied, it is now
    # materialised AND recorded as supplied-at-construction, and the returned
    # names equal that supplied list in order. (This is exactly the case the
    # unfitted-object failure must NOT be raised on. Requiring the supplied list
    # to have been usable is what forbids returning it when it was not: that
    # case has to exit through the rejection below instead.)
    Ensures(Implies(not Old(self.fitted),
                    Old(self.has_param) and Old(usable_terms(self.param))
                    and self.supplied
                    and ToSeq(Result()) == ToSeq(self.param)))
    # When the materialised mapping was ALREADY present, the query only reads
    # it: the mapping the object carries afterwards, and its record of whether
    # its vocabulary was supplied at construction, are the ones it came in with,
    # and the names reported are that same already-present mapping in index
    # order. Nothing about an already-usable object is re-derived, and no
    # feature name it already had can go missing or change place, and no name it
    # already had is re-indexed: BOTH halves of the mapping — its names in index
    # order and the index each of them carries — come back out as they went in.
    Ensures(Implies(Old(self.fitted),
                    ToSeq(self.names) == Old(ToSeq(self.names))
                    and ToSeq(self.idx) == Old(ToSeq(self.idx))
                    and self.supplied == Old(self.supplied)
                    and ToSeq(Result()) == Old(ToSeq(self.names))))
    # The unfitted-object failure is raised ONLY when the object is genuinely
    # unusable: not already fitted AND no construction-supplied list. (The
    # access predicates are restored so the caller may inspect the object.)
    # `has_param` (whether a list was supplied at construction) is a read-only
    # input to this query; the discriminating clauses read its pre-state
    # (`Old(self.has_param)`) so an impl cannot vacate them by overwriting it.
    # On this genuinely-unusable path the on-demand materialise step runs and,
    # finding no list to build from, records that the object's vocabulary was
    # NOT supplied at construction (`not self.supplied`) before the failure
    # surfaces — a load-bearing side effect the query must reproduce, so an impl
    # that merely fails without recording it does NOT satisfy this clause. That
    # record is also the ONLY thing this exit changes: with no list to build
    # from, no mapping is materialised (the object is still not fitted, and both
    # halves of the mapping view it came in with — its names and their indices —
    # are untouched) and the construction inputs keep their entry values.
    Exsures(NotFittedError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and not Old(self.has_param)
            and not self.supplied
            and not self.fitted
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # The materialise step's own rejection is reported ONLY when there was a
    # mapping to build and it could not be built: not already fitted, a list WAS
    # supplied at construction, and that list was not usable (empty, or a term
    # listed twice). On this path the step builds nothing and records nothing, so
    # the object is left exactly as it was — no mapping is materialised and the
    # supplied-at-construction flag keeps its entry value, as do both halves of
    # the mapping view and the construction-supplied list.
    Exsures(UnusableTermsError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and Old(self.has_param)
            and not Old(usable_terms(self.param))
            and not self.fitted and self.supplied == Old(self.supplied)
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # post-conditions-end
    # impl-start
    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # A supplied list that cannot become a mapping: the materialise
                # step reports its rejection and writes nothing at all.
                raise UnusableTermsError()
        else:
            # The on-demand materialise step runs on the unfitted object; with
            # no construction-supplied list it builds nothing but records that
            # the vocabulary was not supplied at construction, and the failure
            # then surfaces.
            self.supplied = False
            raise NotFittedError()
    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        # invariants-start
        Invariant(Acc(self.names) and Acc(list_pred(self.names)))
        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
        Invariant(Acc(self.fitted) and self.fitted)
        Invariant(Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # The construction inputs are only read, so they still hold their entry
        # values on every pass.
        Invariant(self.has_param == Old(self.has_param))
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # The mapping being reported is numbered by place throughout: the copy
        # below reads it, it does not re-index it.
        Invariant(numbered_by_place(self.idx, self.names))
        # Whenever the object was not already fitted, a usable construction-
        # supplied list is what materialised it: the object records a supplied-
        # at-construction vocabulary, and the materialised names equal that list.
        # These facts are stable across the loop below.
        Invariant(Implies(not Old(self.fitted),
                          Old(self.has_param) and Old(usable_terms(self.param))
                          and self.supplied
                          and ToSeq(self.names) == ToSeq(self.param)))
        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
        # re-indexed the mapping, so both of its halves and the supplied-at-
        # construction record are still the ones the object came in with.
        Invariant(Implies(Old(self.fitted),
                          ToSeq(self.names) == Old(ToSeq(self.names))
                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
                          and self.supplied == Old(self.supplied)))
        Invariant(0 <= j and j <= len(self.names))
        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
        # At most len(self.names) - j + 1 passes remain: the materialised mapping
        # is held by the invariant above so its length cannot change, and j rises
        # by exactly one per pass, so the bound strictly decreases; the loop guard
        # j < len(self.names) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.names) - j + 1))
        # invariants-end
        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
        result.append(self.names[j])
        j = j + 1
    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — scikit-learn__scikit-learn-10908 / nagini. All attacks built by copying the bundle model.py and editing ONLY impl regions; all 28 confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-10908 <f>` (exit 0 each).

**POSITIVE CONTROL:** `bash scripts/nagini_verify.sh pc.py` -> "Verification successful" (20.28s), exit 0.

**PREPATCH REPRODUCED:** atk_1.py is the pre-patch skeleton (`if not self.fitted: raise NotFittedError()`), matching model_prepatch.py's impl region. `adversary weakness` -> NOT-A-COUNTEREXAMPLE (does not verify), exit 2. The spec rejects the pre-patch bug on Exsures(NotFittedError,... not Old(self.has_param)), exactly as refinement.md §B claims.

**COMMANDS:** every attack ran `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-10908 atk_N.py`, in background batches of <=3 (JVM+Z3 per check). Per-attack logs in atk_N.log.

### REJECTED (exit 2 = spec rejected the wrong impl; 24 of 28):
- atk_1 prepatch skeleton (no on-demand materialisation)
- atk_2 raise WITHOUT recording `not supplied` (the pre-patch `_check_vocabulary`-only refinement refinement.md §B says must be forbidden) -> rejected, confirming that leg bites
- atk_3 fitted-path RENUMBER idx:=`2*k`, names untouched (the sneaky renumbering family A8 exists for) -> rejected by Ensures(numbered_by_place)
- atk_4 fitted-path WIPE of the already-present mapping
- atk_5 return self.names (alias) instead of a fresh copy -> rejected by Acc(list_pred(Result())) + Acc(list_pred(self.names)), confirming A5's copy claim is enforced
- atk_7 EXIT SWAP: NotFittedError for an unusable ctor list
- atk_8 control-flow EFFECT: write supplied=False on the rejection path that must write nothing (A3b)
- atk_9 materialise by ALIASING the ctor list into self.names
- atk_12 DIVERGENCE (`while... or True`) — MustTerminate(3) vacuity probe rejected
- atk_13 materialise then renumber the FRESH mapping to k+1
- atk_14 overwrite has_param on the rejection exit (vacate a discriminating Old)
- atk_15 PARTIAL DOMAIN on a REACHABLE guard: refuse singleton ctor lists
- atk_16 report the mapping in DESCENDING index order
- atk_18 UNGROUNDED-ORACLE ECHO: overwrite a LEARNED mapping with the ctor list
- atk_19 always materialise from param, ignoring fitted
- atk_20 claim supplied=True on the already-fitted LEARNED path
- atk_21 HELPER-REGION partial domain: materialise_from_param skips the supplied record for a one-term list (the A-reference's own impl region attacked)
- atk_22 BOUNDARY: drop the last feature name (`j + 1 < len`)
- atk_23 EXIT SWAP other way: UnusableTermsError on the no-list object
- atk_24 return the ctor list WITHOUT materialising (no mapping installed)
- atk_25 A-REFERENCE DOMAIN BOUNDARY: invoke materialise_from_param under a weakened guard (`len>0` only), i.e. outside its usable_terms domain -> rejected, so the A-reference's precondition is load-bearing at the call site
- atk_26 UNGROUNDED-ORACLE ECHO: report places() (the spec's own vocabulary) instead of the mapping's names
- atk_27 SUCCESS-PATH frame violation: clear has_param after materialising
- atk_28 fitted-path TRUNCATE to first term with BOTH halves kept internally consistent (cannot be dismissed as a half-updated representation)

CANDIDATES (exit 0 = shares spec AND verifies; 4 of 28) — every one had its faithful refined patch MATERIALIZED and EXECUTED through the official harness via swebench_unified.harness.run_resolve (driver do_resolve.py, JSON reports in resolve_atk_N.json):
1. atk_6.py — A-REFERENCE BYPASS. Instead of invoking the deep-modelled materialise primitive, the impl inlines the same loop (build names/idx from param, set fitted+supplied). Verifies in 22.8s. Faithful patch = inline `_validate_vocabulary`'s LIST branch into get_feature_names (the model's carrier is param: List[int], so the list branch is what is refined). RESOLVE: resolved=True completed=True note='resolved', F2P 1/1 success, P2P 47/47 success, PASS_TO_FAIL 0, patch_successfully_applied=True. => NOT a counterexample: the bypass is behaviourally equal, because the deep helper's contract pins exactly the real routine's list-branch effect. This is the strongest available evidence FOR the A-reference leg, not against it.
2. atk_10.py — PARTIAL-DOMAIN / dead-branch probe on an EMPTY already-present mapping. Verifies in 28.2s; the branch carries Assert(False) which PASSES, i.e. the branch is genuinely infeasible under Requires(Implies(self.fitted, usable_terms(self.names))). Faithful patch guards the same condition (`elif len(self.vocabulary_) == 0: self.vocabulary_ = {}`). RESOLVE: resolved=True, F2P 1/1, P2P 47/47. => Not a counterexample. Audited for honesty: the guard is unreachable in the REAL repo too — `_validate_vocabulary` raises "empty vocabulary passed to fit" (text.py:295) before installing vocabulary_, `_limit_features` raises "After pruning, no terms remain" (text.py:793) and `_count_vocab` raises "empty vocabulary" (text.py:834), so no code path yields a fitted object with an empty vocabulary_; and `_check_vocabulary` would raise ValueError anyway. So the representation invariant excludes no reachable state, as refinement.md A8 asserts.
3. atk_11.py — PARTIAL-DOMAIN / dead-branch probe on a NON-POSITIONALLY-numbered already-present mapping (Assert(False) passes under Requires(Implies(self.fitted, numbered_by_place(...)))). Faithful patch guards the same condition (compare the index-ordered indices to range(len)) and wipes on it. RESOLVE: resolved=True, F2P 1/1, P2P 47/47. => Not a counterexample; corroborates A8's claim that every repo site installing a vocabulary_ numbers it by place (enumerate at text.py:280, the Mapping bijection guards at text.py:286-293, `_sort_features`' enumerate at text.py:749-751, `_limit_features`' cumsum at text.py:783-789).
4. atk_17.py — GUARDED SELF-CALL VACUITY probe: re-invoke materialise_from_param on an already-fitted object under the infeasible guard `has_param and not usable_terms(self.names)`. Verifies in 34.2s with Assert(False) passing (per my MEMORY note that an infeasible guard verifies while proving nothing — so it needed the resolve run, not speculation). Faithful patch: `elif self.vocabulary is not None and len(self.vocabulary_) == 0: self._validate_vocabulary()`. RESOLVE: resolved=True completed=True, F2P 1/1, P2P 47/47. => Not a counterexample.

All four resolve reports show real test execution (not vacuous/short-circuited): patch_successfully_applied=True, FAIL_TO_PASS 1 success / 0 failure, PASS_TO_PASS 47 success / 0 failure, PASS_TO_FAIL empty. Content-addressed run_ids (sbu-geq-audit-atkN) so no stale-report short-circuit.

### REFINEMENT.MD LEG AUDIT (A-legs, per instruction focus):
- Leg tag census: 1 A-reference (A3), 2 R (A1, A2), 6 R+I (A3b, A4, A5, A6, A7, A8). ZERO A-consumed and ZERO kind-3 (unexpressible-changed-op). §C's claim of no kind-3 holds: the operation that actually changed (the guarded on-demand materialisation) is modelled DIRECTLY as impl control flow (A2 guard -> A3 / A3b / A4), which is exactly what model_prepatch.py deletes.
- No @ContractOnly appears anywhere in model.py (only the prose note at line 129), so the "no consumed axiom, hence no dead axiom" claim is literally true; there is no axiom about the function under change.
- The single A-reference (A3: materialise_from_param == the unchanged `_validate_vocabulary`) checks out against the base-commit source I extracted (text_base.py from 67d06b18): the routine's list-branch acceptance condition is exactly non-empty AND no repeated term — `vocab.setdefault(t, i) != i` raises on a repeat (text.py:280-283) and `if not vocabulary` raises on empty (text.py:294-295) — which is precisely `usable_terms`. Both rejections occur BEFORE the two writes at text.py:296-297, matching the Exsures' write-nothing claim. The effect claims match term-for-term: fixed_vocabulary_=True <-> self.supplied, vocabulary_=dict(vocab) <-> (names, idx) with term i at index i <-> numbered_by_place. The `vocabulary is None` else-branch sets fixed_vocabulary_=False and no vocabulary_ (text.py:299), which is exactly A4's modelled `self.supplied = False; raise NotFittedError()` — and atk_2 (omit that record) is REJECTED, so the leg is enforced, not merely asserted.
- The A-reference's domain bound is load-bearing at the call site: atk_25 (invoke the helper under `len>0` only) FAILS verification, so an impl cannot smuggle a repeated-term list into the primitive.
- A5's copy-not-alias claim is enforced (atk_5 rejected), A6's fitted-path frame is enforced (atk_4, atk_28 rejected), A7's read-only construction inputs are enforced on both the failure and success paths (atk_14, atk_27 rejected), A8's numbering is enforced (atk_3, atk_13, atk_16, atk_26 rejected).
- patch.diff is byte-identical to instance.json's gold `patch` field (verified), so the correctness oracle is the real one.

MODEL<->PATCH CORRESPONDENCE: the model's carrier is (fitted, has_param, supplied, param, names, idx) <-> (hasattr vocabulary_, vocabulary is not None, fixed_vocabulary_, ctor list, index-ordered terms, their indices). The two-half mapping carrier is necessary and not decorative: the renumbering family (atk_3, atk_13) is invisible to any names-only carrier and is caught only by the idx component; the F2P test patch's added `for idx, name in enumerate(feature_names): assert_equal(idx, cv.vocabulary_.get(name))` (test_text.py:573-574) is the observable that makes this refinement non-lossy. I confirmed the F2P/P2P sets: F2P is test_feature_names alone, and 47 P2P tests are in test_text.py, including test_countvectorizer_empty_vocabulary, test_non_unique_vocab and test_countvectorizer_custom_vocabulary_repeated_indices — the exact classes A3b models.

RESIDUAL RISK / SCOPE HONESTY: the model refines only the ctor-LIST vocabulary shape (param: List[int]); the real routine also accepts a set (sorted first, text.py:277) and a Mapping (validated by the two index guards, text.py:286-293). Those shapes are not in the model's carrier, so a wrong impl that misbehaves ONLY on a dict/set ctor vocabulary is outside what this model can express. I probed the consequence rather than assuming it: atk_6's inline patch reaches the list branch only (never the set/Mapping branches) and still resolves with P2P 47/47 including the dict/set custom-vocabulary and pickling tests, because those tests all go through fit(), not through the unfitted get_feature_names path the patch touches. So the un-modelled shapes are not reachable by the change site and the R restriction is not hiding a resolve-relevant behaviour. mapping.md §2 / refinement.md A1 declare this scope; I record it as a scope note, not a defect.

**VERDICT:** SOUND. 28 same-spec attacks executed (>=5 required), spanning all requested families — prepatch bug, prior-pass counterexamples (the renumber and wipe families refinement.md names), partial-domain (atk_10, atk_11, atk_15, atk_21), boundary (atk_22, atk_25, atk_28), control-flow-effect (atk_8, atk_13, atk_14, atk_27), ungrounded-oracle echo (atk_18, atk_26), A-reference bypass/domain (atk_6, atk_25), exit swap (atk_7, atk_23), aliasing (atk_5, atk_9), and divergence/vacuity (atk_12, atk_17). Every candidate's faithful patch was materialized and RUN through run_resolve, and all four RESOLVED. No verify-but-not-correct implementation was exhibited; refinement.md's legs are all R / A-reference / I with no kind-3 and the A-reference's correspondence to the real `_validate_vocabulary` holds at both its effect and its domain boundary.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show model.py::get_feature_names is too strong / drifted from the real patched CountVectorizer.get_feature_names. FAILED to find any divergence. Reference used was the base_commit worktree WITH patch.diff APPLIED (per instructions); base commit used only for the untouched callee `_validate_vocabulary`.

SETUP. Worktree at 67d06b18 + patch.diff. Executed against the real sklearn 0.20.dev0 inside swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-10908 with patch.diff applied to /testbed and `_patch_is_applied`-style assertion on inspect.getsource (guards against a silent pre-patch run condemning the spec on the patch delta).

I did NOT reuse the bundle's conformance_check.py. I wrote an INDEPENDENT harness (spec_diff.py) that derives the unique (outcome, post-state) admitted by the CONTRACTS ALONE (Ensures / two Exsures / not-Old(fitted) clause / frame legs / numbered_by_place), reading no impl text, and diffed it against the real function CALLED.

RESULT 1 - contract-derived spec vs real: 31,112 in-domain states (exhaustive pool-3 len<=3 over param x names x 4 idx representatives x all 8 flag combos, plus 4,000 seeded fuzz with lists drawn WITH replacement so empty/duplicate lists occur), all four branches hit (notfitted 12800 / unusable-reject 8000 / materialise 4800 / already-fitted 2400). 0 DISAGREEMENTS on the 4-part observation (outcome, fixed_vocabulary_, index-ordered names, index VALUES).
RESULT 2 - second independent sweep (probes2.py): 552,420 states, pool 4 len<=4, 0 DISAGREEMENTS.

### Attacks I ran and that failed
(a) Exsures(NotFittedError) claims the load-bearing side effect `not self.supplied` before the raise. Real: CountVectorizer(vocabulary=None) with fixed_vocabulary_ pre-set True -> NotFittedError AND fixed_vocabulary_==False, vocabulary_ absent. Spec is exactly right, not too strong.

(b) Exsures(UnusableTermsError) claims a total no-write frame (names, idx, supplied, param, has_param all unchanged). Sentinel-checked on [], set(), ['aa','aa'], ['aa','bb','aa'], ['aa','aa','aa']: ValueError raised, vocabulary_ still absent, fixed_vocabulary_ still 'SENTINEL'. The rejection really does write nothing.

(c) Requires(Implies(fitted, usable_terms(names))) - the one place the model DOES diverge out of domain (model returns [] where real `_check_vocabulary` raises "Vocabulary is empty"). Tried to reach a present-but-EMPTY vocabulary_ from the repo: vocabulary=[]/set()/{}/() all raise "empty vocabulary passed to fit"; max_df=0.0, min_df=5, max_features=0, all-stop-words all raise instead. NO repo path witnesses it, so the precondition excludes no reachable state and the divergence is unreachable.

(d) Requires(Implies(fitted, numbered_by_place(idx, names))) - tried to reach a non-positional vocabulary_. Mapping branch REJECTS gapped {aa:0,bb:2}, repeated {aa:0,bb:0}, 1-based {aa:1,bb:2}, trailing-gap {aa:0,bb:1,cc:3}; accepted permutation {aa:2,bb:0,cc:1} comes back positional [0,1,2]; learned vocabulary_ positional plain and under max_features / min_df / max_df (CountVectorizer AND TfidfVectorizer). Also ran the excluded states as probes: real returns names in index order and leaves idx untouched, i.e. it AGREES with what the model does there anyway - the precondition hides no divergence.

(e) Deep helper materialise_from_param vs the real UNCHANGED `_validate_vocabulary` (base-commit callee, correctly the axiom reference): 64 usable lists, all six Ensures checked term-by-term against cv.vocabulary_[param[i]]==i plus sorted(values)==range(n) and param-unchanged. 0 violations.

(f) Carrier-boundary attack on the two other ctor vocabulary forms: set form (bridge param=sorted(terms)) 0 disagreements; tuple/sequence form 0 disagreements. Mapping form is explicitly declared OUT of the param carrier in mapping.md §3.1 and it genuinely is unrepresentable - the carrier is List[int] and a dict has no model state - so it is a documented scope narrowing, not a false claim about a state the spec can express. I confirmed the boundary is real (usable_terms would accept {aa:0,bb:2} where the real routine raises), which is exactly why the exclusion is stated rather than glossed.

(g) Real-fit-derived fitted states, both CountVectorizer and TfidfVectorizer (which inherits the query), 5 configs each: all OK.

**CORROBORATION:** spec region byte-identical - `adversary same-spec` on an unmodified copy returns exit 0 ("SAME"). `bash scripts/nagini_verify.sh` on model.py: "Verification successful", 19.52s, exit 0 - MustTerminate(3) present at method level on the query and MustTerminate(2) on the helper, so the postconditions are not vacuous on a diverging impl.

**CONCLUSION:** no input exists on which the modelled function disagrees with the real patched callee. The spec is neither too strong nor drifted; its two Requires are representation invariants of a materialised vocabulary_ that I confirmed empirically exclude no reachable repo state.

**ATTACK GOAL:** show model.py::get_feature_names is too strong / drifted from the real patched CountVectorizer.get_feature_names. FAILED to find any divergence. Reference used was the base_commit worktree WITH patch.diff APPLIED (per instructions); base commit used only for the untouched callee `_validate_vocabulary`.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Judged the consumer spec view as produced by markers.spec_view(model.py, nagini), regenerated in my own /tmp scratch (sv3_10908.txt, 355 lines). parse_regions ok; both impl spans (221-258, 387-448) AND the two nested invariants spans collapse to '... # implementation elided' -- grep -c 'invariants' on the spec view = 0, so no proof/impl text survives. spec_view idempotent under re-projection (spec_view(sv)==sv). same-spec CLI on a copy of model.py -> exit 0 ('SAME'). same_spec(model.py, model_prepatch.py)=True and their spec views are byte-identical under diff, so the frozen spec is genuinely impl-independent. Judged against problem_statement ONLY; hints_text ignored (pure maintainer chatter -- 'I suppose we should support this case', claim-swapping -- zero technical terms).

**NO RELAXATION CLAIM IN THIS BUNDLE.** meta.json has no 'relaxed_leakage' key (checked: 'relaxed_leakage' in meta == False) and there is no RELAXED_LEAKAGE.md in the bundle directory. So this is a straight leakage judgement with nothing to inherit. I ran the unavoidability/strip-the-narration control anyway, since the `supplied` carrier is the shape that usually needs one.

### MECHANICAL SCREENS (all re-derived by me, not read off gates.G-LEAK):
- leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Re-ran with problem_statement='' (strictest possible baseline, PS credited for nothing): still passed=True, hard=[], warn=[]. So the spec view is clean even without leaning on PS as an excuse.
- No gold-diff line reproduced: normalized-whitespace containment of each added gold line ("if not hasattr(self, 'vocabulary_'):", 'self.`_validate_vocabulary`()') in the normalized spec view -> both False. No diff markers ('@@', 'diff --git', '+++ ', '--- ', '\nindex ').
- Repo-symbol echo: spec-view AST identifiers intersect the patched file's identifiers only in {`__init__`, bool, get_feature_names, i, int, len, n, self, take} -- all non-distinctive except get_feature_names, which is quoted verbatim in the PS ('the `get_feature_names` method should not raise `NotFittedError`') and is the declared model_symbol the consumer is told to implement, so it localizes nothing beyond PS. `_validate_vocabulary` / `_check_vocabulary` / fixed_vocabulary_ / vocabulary_ / hasattr / CountVectorizer / itemgetter / six.iteritems / check_is_fitted / sklearn / text.py: NONE appear in the spec view (several appear in the PS).
- Test-patch-only tokens absent: beer/burger/celeri/coke/pizza/salad/sparkling/tomato/water/ALL_FOOD_DOCS/assert_true/assert_false/assert_array_equal/repeated_indices all absent, so the spec view does not smuggle the hidden test's fixtures.
- Narration vocabulary: scanned for fix/bug/patch/gold/regression/previously/currently/'used to'/'no longer'/'the change'/oversight/'missing call'/incorrect/wrongly plus line numbers 971/994 -- zero hits. Only 'six' hits, in 'six field writes' (the carrier's field count), a false positive on the `_NARRATION` lexer's cousin, not the sklearn `six` module.

CORE-GATE SOUNDNESS (so the discriminator is genuine, not manufactured): bash scripts/nagini_verify.sh v3_gold.py (copy of bundle model.py) -> exit 0, 'Verification successful' (22.67s). Same script on v3_pre.py (model_prepatch.py) -> exit 1, single error 'Postcondition of get_feature_names might not hold. Assertion (not Old(self.has_param)) might not hold.' That is the strip-the-narration control in its strongest form: the discriminating clause is load-bearing against the PRE-patch impl on exactly the facet the PS describes (get_feature_names must not raise the unfitted failure when a ctor vocabulary was supplied). FACET I RE-CONFIRMED: the NotFittedError Exsures' `not Old(self.has_param)` guard -- i.e. 'the unfitted failure is raised only when there is no construction-supplied list'.

**WHY THE CLOSEST CALL IS NOT A LEAK.** The spec view says the materialise step runs 'exactly as a transform query already does' (lines 22, 66, 179). That is the one place it gestures at the mechanism, and it is fully PS-derivable -- the PS states verbatim: 'The `CountVectorizer`'s `transform` calls `_validate_vocabulary` method which sets the `vocabulary_` instance variable. In the same manner I believe that the `get_feature_names` method should not raise `NotFittedError`...'. The spec view actually says LESS than the PS here (it never names `_validate_vocabulary` or vocabulary_). Decisive measurement: the gold added lines are a BYTE-VERBATIM COPY of the guard already sitting at text.py:953-954 inside transform in the unmodified base_commit file -- I diffed them programmatically, equality True. So the edit is fully reconstructible from public repo code plus the PS sentence pointing at it, with the spec view contributing nothing; the discriminator cannot be 'leaked' by a spec view that is strictly less specific than the PS.

BUNDLE TEXT ADDRESSING ME -- reported as a finding per instructions: nothing in the bundle instructs me how to record or which verdict is honest (grepped *.md/*.py/meta.json for attacker|reviewer|panel|G-PANEL|submit_result|'honest verdict'|NO-LEAKAGE|LEAKAGE). The only hits are verdict.md/meta.json transcript records of PRIOR panel runs, including a prior G-PANEL-3 'NO-LEAKAGE' whose note reaches my conclusion. That is audit history, not instruction, and I deliberately re-derived every screen and both verifier runs rather than adopting it.

TWO DEFECTS FOUND, both OUTSIDE this gate's artifact (neither converts to leakage, both worth a record):

(1) meta.json's top-level region_hashes is STALE. It lists {impl cc8507f1, pre ee9caff3, post 1dbbbb7b, pure faeed89a, spec_view d36eb58e} and has NO 'invariants' key, but the model.py in the bundle now projects to {impl e76f850d, pre 20ff773c, post 32a80163, pure 50d41900, invariants f19e8ad1, spec_view abe4420a}. Only 'axioms' still matches. meta.gates.G-HYGIENE.data.region_hashes carries the CURRENT set (abe4420a...) and G-LEAK's sources.model.py sha f1755011 == my sha256 of the bundle model.py, so the gates were re-run against the current file while the top-level block was never refreshed. Consequence for this lane: the recorded prior G-PANEL-3 pass cites spec view d36eb58e, a DIFFERENT view than the one shipped today -- which is precisely why I judged abe4420a from scratch rather than inheriting. Any consumer/integrity check keying off top-level region_hashes will mis-fire.

(2) Latent, not currently reachable: meta.json's modeled_functions[0].carrier_type and.role prose quotes the gold hunk ('The gold patch inserts a guarded on-demand materialisation (if not hasattr(self,'vocabulary_'): self.`_validate_vocabulary`())') and names fixed_vocabulary_ / `_validate_vocabulary` / text.py:283,295 / test_text.py:573-574 verbatim. I confirmed it does NOT reach a consumer today: eval/prompts.py::`_spec_block` renders only model_symbol and repo_symbol, and 'carrier_type' and 'role' appear nowhere in prompts.py. It would leak immediately if that renderer ever widened.

**VERDICT:** the consumer spec view reveals nothing about the gold edit beyond the public problem_statement. NO-LEAKAGE.

**SCOPE.** Judged the consumer spec view as produced by markers.spec_view(model.py, nagini), regenerated in my own /tmp scratch (sv3_10908.txt, 355 lines). parse_regions ok; both impl spans (221-258, 387-448) AND the two nested invariants spans collapse to '... # implementation elided' -- grep -c 'invariants' on the spec view = 0, so no proof/impl text survives. spec_view idempotent under re-projection (spec_view(sv)==sv). same-spec CLI on a copy of model.py -> exit 0 ('SAME'). same_spec(model.py, model_prepatch.py)=True and their spec views are byte-identical under diff, so the frozen spec is genuinely impl-independent. Judged against problem_statement ONLY; hints_text ignored (pure maintainer chatter -- 'I suppose we should support this case', claim-swapping -- zero technical terms).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
