# P2 adversarial audit — scikit-learn__scikit-learn-13779

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_probe_on_absent.py`, `atk_2_never_rejects.py`, `atk_3_skips_last_entry.py`, `atk_4_absent_treated_as_reject.py`, `atk_6_quantifier_swap_all_reject.py`, `atk_7_off_by_one_index.py`, `atk_9_diverge_on_absent.py`, `atk_10_rejects_empty_roster.py`, `atk_11_probes_wrong_entry.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_oracle_echo_no_probe.py`, `atk_8_fabricated_probe_arg.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_probe_on_absent.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 1 (pre-patch bug): no absent-entry skip; the probe is
+    # consulted on every entry, including status 0 (absent).
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,17 +116,13 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
         Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
         Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
-        elif not accepts_weighting(status):
+        if not accepts_weighting(status):
             supported = False
         i = i - 1
     if not supported:
```

Attack 2 — `atk_2_never_rejects.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,9 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 2 (rejection dropped): skip absent (0) AND present-rejecting
+    # (2) entries; only present-accepting entries reach the probe, so
+    # `supported` can never become False.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,15 +117,10 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
+        if status == 0 or status == 2:
             supported = supported
         elif not accepts_weighting(status):
             supported = False
```

Attack 3 — `atk_3_skips_last_entry.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 3 (partial domain / boundary): the LAST roster entry is
+    # never examined -- the scan skips index len(roster) - 1.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,15 +116,12 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
+        if i == len(roster):
+            supported = supported
+        elif status == 0:
             supported = supported
         elif not accepts_weighting(status):
             supported = False
```

Attack 4 — `atk_4_absent_treated_as_reject.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,9 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 4 (control-flow effect): an ABSENT entry is treated as a
+    # rejection rather than skipped. The probe is never consulted on it,
+    # so the axiom precondition still holds.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,16 +117,11 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
+            supported = False
         elif not accepts_weighting(status):
             supported = False
         i = i - 1
```

Attack 5 — `atk_5_oracle_echo_no_probe.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 5 (ungrounded-oracle echo): the capability probe is NEVER
+    # invoked; the status tag is read directly instead.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,17 +116,13 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
         Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
         Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
-        elif not accepts_weighting(status):
+        if status == 2:
             supported = False
         i = i - 1
     if not supported:
```

Attack 6 — `atk_6_quantifier_swap_all_reject.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,10 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 6 (quantifier swap): reject only when EVERY present entry
+    # rejects weighting, instead of when SOME present entry does.
+    any_accepts = False  # type: bool
+    any_present = False  # type: bool
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,19 +118,18 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
-        elif not accepts_weighting(status):
-            supported = False
+            any_present = any_present
+        else:
+            any_present = True
+            if accepts_weighting(status):
+                any_accepts = True
         i = i - 1
+    if any_present and not any_accepts:
+        supported = False
     if not supported:
         raise WeightingUnsupported()
     return
```

Attack 7 — `atk_7_off_by_one_index.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 7 (off-by-one): consults roster[i] instead of
+    # roster[i - 1], so index 0 is never examined.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,18 +116,14 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
-        status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
-        elif not accepts_weighting(status):
-            supported = False
+        if i < len(roster):
+            status = roster[i]
+            if status == 0:
+                supported = supported
+            elif not accepts_weighting(status):
+                supported = False
         i = i - 1
     if not supported:
         raise WeightingUnsupported()
```

Attack 8 — `atk_8_fabricated_probe_arg.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -104,14 +104,9 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 8 (fabricated probe argument): the absent-entry branch still
+    # consults the probe, but with a fabricated PRESENT status so the
+    # axiom precondition is satisfied by construction.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,7 +117,6 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
         Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -130,8 +124,10 @@
         Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
+            if accepts_weighting(1):
+                supported = supported
+            else:
+                supported = supported
         elif not accepts_weighting(status):
             supported = False
         i = i - 1
```

Attack 9 — `atk_9_diverge_on_absent.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 9 (divergence): loop forever on an absent entry instead of
+    # skipping it. Returns the right answer whenever it returns at all.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,7 +116,6 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
         Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -130,8 +123,9 @@
         Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
-            supported = supported
+            while True:
+                Invariant(Acc(list_pred(roster), 1 / 2))
+                supported = supported
         elif not accepts_weighting(status):
             supported = False
         i = i - 1
```

Attack 10 — `atk_10_rejects_empty_roster.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,15 +104,9 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
-    supported = True  # type: bool
+    # ATTACK 10 (empty boundary): an empty roster is rejected even though
+    # it supports weighting vacuously.
+    supported = len(roster) > 0  # type: bool
     i = len(roster)
     while i > 0:
         # invariants-start
@@ -122,15 +116,10 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
             supported = supported
         elif not accepts_weighting(status):
             supported = False
```

Attack 11 — `atk_11_probes_wrong_entry.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,15 +104,10 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 11 (wrong probe argument / aliasing): a present entry is
+    # judged by probing the LAST present entry's status, not its own.
     supported = True  # type: bool
+    witness = 1  # type: int
     i = len(roster)
     while i > 0:
         # invariants-start
@@ -122,18 +117,17 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
+        Invariant(witness == 1 or witness == 2)
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
             supported = supported
-        elif not accepts_weighting(status):
-            supported = False
+        else:
+            if witness == 1:
+                witness = status
+            if not accepts_weighting(witness):
+                supported = False
         i = i - 1
     if not supported:
         raise WeightingUnsupported()
```

Attack 12 — `atk_12_only_first_entry.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,7 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 12 (partial domain): only roster index 0 is examined.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,15 +115,12 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
-        if status == 0:
-            # absent entry: skip, never consult the probe on it
+        if i != 1:
+            supported = supported
+        elif status == 0:
             supported = supported
         elif not accepts_weighting(status):
             supported = False
```

Attack 13 — `atk_13_position_dependent_skip.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,14 +104,8 @@
             and (not config_supports(ToSeq(roster))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
-    # step). An absent entry (0) is skipped — the probe is never consulted on it,
-    # honouring its precondition. A present entry (1 or 2) is consulted via the
-    # probe; `supported` folds whether every present entry seen so far accepts.
-    # The single rejection is raised once, at the end, when `supported` is false
-    # (observationally identical to raising on the first present-rejecting entry;
-    # refinement.md justifies the short-circuit equivalence).
+    # ATTACK 13 (position-dependent): a present-rejecting entry at index 0
+    # is skipped; the rejection depends on roster POSITION.
     supported = True  # type: bool
     i = len(roster)
     while i > 0:
@@ -122,15 +116,12 @@
                         (Implies(0 <= k and k < len(roster),
                                  0 <= roster[k] and roster[k] <= 2),
                          [[roster[k]]])))
-        # `supported` tracks support over the suffix already scanned.
-        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
-        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
         status = roster[i - 1]
         if status == 0:
-            # absent entry: skip, never consult the probe on it
+            supported = supported
+        elif i == 1:
             supported = supported
         elif not accepts_weighting(status):
             supported = False
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13779.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ensemble meta-estimator holds a roster of named sub-estimators. Each entry
  of the roster is either ABSENT (a placeholder that has been cleared away and
  carries no sub-estimator at all) or PRESENT (it carries a real sub-estimator,
  which itself either does or does not accept per-sample weighting).

  When the caller supplies per-sample weights, the meta-estimator must first
  check that the configuration can honour them, by consulting each roster entry:

    * An ABSENT entry carries no sub-estimator, so there is nothing to consult.
      The capability probe — which inspects a sub-estimator's fitting interface —
      is meaningful ONLY for a present sub-estimator and must NOT be applied to an
      absent entry. An absent entry is simply skipped and can never, by itself,
      cause the check to fail or error.

    * A PRESENT entry is consulted via the capability probe. If the present
      sub-estimator does not accept per-sample weighting, the configuration
      cannot honour the supplied weights and the check rejects it.

  The behaviour pinned here: the weighted-fit pre-check returns normally exactly
  when every PRESENT sub-estimator accepts per-sample weighting (absent entries
  notwithstanding), and rejects (raises) exactly when some PRESENT sub-estimator
  does not. The probe is never consulted for an absent entry.

The roster is modelled as a `List[int]` of per-entry status tags: 0 = absent,
1 = present-and-accepts-weighting, 2 = present-and-rejects-weighting. The
capability probe is an unchanged callee the check invokes; it inspects a present
sub-estimator's interface, so it is meaningful only for a present entry — this is
encoded as its precondition (consulting it on an absent entry is out of contract,
exactly as the real probe dereferences an attribute that an absent entry lacks).
The rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2). Nagini bans `str` indexing, so the
specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class WeightingUnsupported(Exception):
    """Signals a rejected weighted-fit configuration: some present sub-estimator
    does not accept per-sample weighting. Stands in for the `ValueError` the
    desired behaviour raises; a builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""

# axioms-start
@Pure
@ContractOnly
def accepts_weighting(status: int) -> bool:
    """The capability probe applied to one roster entry: whether the carried
    sub-estimator accepts per-sample weighting. It inspects a PRESENT
    sub-estimator's fitting interface, so it is meaningful only for a present
    entry; consulting it on an absent entry is out of contract (the real probe
    dereferences an attribute an absent entry does not have). Hence its
    precondition admits only the present statuses {1, 2}, and it reports
    acceptance exactly on status 1. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(status == 1 or status == 2)
    Ensures(Result() == (status == 1))
# axioms-end

# pure-start
@Pure
def config_supports(roster: PSeq[int]) -> bool:
    """Whether the configuration can honour per-sample weights: every PRESENT
    entry accepts weighting. An absent entry (0) and a present-accepting entry
    (1) are both fine; only a present-rejecting entry (2) breaks support. Front-
    recursive over the sequence so a single unfold is available per loop step."""
    if len(roster) == 0:
        return True
    return roster[0] != 2 and config_supports(roster.drop(1))
# pure-end

def check_weighting_support(roster: List[int]) -> None:
    # pre-conditions-start
    # Every entry is a valid status tag: 0 absent, 1 present-accepts,
    # 2 present-rejects.
    Requires(Acc(list_pred(roster), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(roster),
                             0 <= roster[k] and roster[k] <= 2),
                     [[roster[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input: fractional permission, required and ensured (and returned
    # on the exceptional path too), so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Ensures(Acc(list_pred(roster), 1 / 2))
    # Returns normally exactly when every PRESENT entry accepts weighting. Absent
    # entries are skipped: they do not appear in this condition.
    Ensures(config_supports(ToSeq(roster)))
    # Rejects (raises) exactly when some PRESENT entry does not accept weighting.
    Exsures(WeightingUnsupported,
            Acc(list_pred(roster), 1 / 2)
            and (not config_supports(ToSeq(roster))))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
    # step). An absent entry (0) is skipped — the probe is never consulted on it,
    # honouring its precondition. A present entry (1 or 2) is consulted via the
    # probe; `supported` folds whether every present entry seen so far accepts.
    # The single rejection is raised once, at the end, when `supported` is false
    # (observationally identical to raising on the first present-rejecting entry;
    # refinement.md justifies the short-circuit equivalence).
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        # `supported` tracks support over the suffix already scanned.
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            # absent entry: skip, never consult the probe on it
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

13 DISTINCT same-spec wrong impls encoded (all built by gen.py, which splices ONLY the impl-region body of the frozen model.py, leaving axioms/@Pure/Requires/Ensures byte-identical). All 14 files (13 attacks + positive control) pass `adversary same-spec` with exit 0.

Per-attack logs at <file>.weakness.log; tally at results.txt.

POSITIVE CONTROL: pos_control.py (byte-identical to frozen model.py, asserted in gen.py) => exit 0, CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (13.4s). The spec is not vacuously unsatisfiable.

PREPATCH REPRODUCED: atk_1_prepatch_probe_on_absent.py re-encodes the pre-patch bug (probe consulted on EVERY entry incl. status 0, no absent-entry skip) => exit 2, verification failed. The failure lands exactly where refinement.md B/D and mapping.md 3.1 predict: the call-site precondition `status == 1 or status == 2` of accepts_weighting is unprovable on a status-0 entry -- the formal face of `'NoneType' object has no attribute 'fit'`. G-DIFF sensing confirmed independently of the bundle's own model_prepatch.py.

### ATTACK RESULTS (exit 2 = spec REJECTED the wrong impl):
- atk_1 prepatch, probe on absent entry: exit 2 REJECTED
- atk_2 never rejects (skip status 0 AND 2, so `supported` can never go False): exit 2 REJECTED
- atk_3 partial domain / boundary, LAST entry never examined (test_sample_weight's rejecting 'knn' is last): exit 2 REJECTED
- atk_4 control-flow effect, absent entry treated as a REJECTION rather than skipped (probe still never consulted on it, so the axiom precondition IS honoured -- this attack isolates the postcondition rather than the axiom): exit 2 REJECTED
- atk_5 ungrounded-oracle echo, probe NEVER invoked, status tag read directly (`if status == 2`): exit 0 CANDIDATE (verifies, 13.5s)
- atk_6 quantifier swap, reject only when EVERY present entry rejects: exit 2 REJECTED
- atk_7 off-by-one, consults roster[i] not roster[i-1] so index 0 never examined: exit 2 REJECTED
- atk_8 fabricated probe argument, absent-entry branch DOES consult the probe but on a fabricated PRESENT status `accepts_weighting(1)`: exit 0 CANDIDATE (verifies, 13.7s)
- atk_9 divergence, `while True` on an absent entry (right answer whenever it returns at all): exit 2 REJECTED -- MustTerminate(i+1)/MustTerminate(2) at the METHOD level really does pin termination here
- atk_10 empty-roster boundary, rejects an empty roster which supports weighting vacuously: exit 2 REJECTED
- atk_11 wrong probe argument / aliasing, present entries judged by probing a DIFFERENT present entry's status (argument still a present status, so the precondition holds): exit 2 REJECTED
- atk_12 partial domain complement, only roster index 0 examined: exit 2 REJECTED
- atk_13 position-dependent skip, a present-rejecting entry at index 0 is skipped (rejection made a function of roster POSITION): exit 2 REJECTED

MANDATORY RESOLVE RUNS -- both CANDIDATEs materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, SWE-bench_Verified, real Docker oracle):

1) atk_5 -> patch_atk_5.diff. The faithful refinement of "the probe is never invoked; the status tag is read directly" is the short-circuit `step is not None and not has_fit_parameter(...)`: under the R-map (mapping.md 2) `status == 2` IS `step is not None and not has_fit_parameter(step,'sample_weight')`, and Python's `and` makes the probe unreachable for an absent entry exactly as the model's status-0 path does. run_resolve => RESOLVED=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=True, FAIL_TO_PASS 2/2 success 0 failure, PASS_TO_PASS 18/18 success 0 failure. Log: resolve_atk_5.log. NOT a counterexample.

2) atk_8 -> patch_atk_8.diff. Faithful refinement: keep the `if step is None: continue` skip but still call the probe on a fabricated PRESENT argument (`self`, whose own `fit` declares `sample_weight`) and discard the result. First attempt errored on a hand-written hunk header (`no report ... Instances with errors: 1`, resolve_atk_8.log); the diff was REGENERATED mechanically via `git diff` in a throwaway worktree and re-checked with `git apply --check` before re-running -- so this is a fixed harness input, not an unexplained infra failure. run_resolve (run_id geqaudit-atk8-v2) => RESOLVED=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=True, FAIL_TO_PASS 2/2, PASS_TO_PASS 18/18. Log: resolve_atk_8_v2.log. NOT a counterexample.

Why both candidates were expected to resolve, and why that is the spec being RIGHT rather than the attacks being weak: atk_5 and atk_8 are the only two shapes the spec admits beyond the frozen impl, and both are behavioural no-ops on the observable surface. atk_5 differs only in WHETHER the probe symbol is syntactically invoked -- but under the R-map the status tag is DEFINED by the probe's result (mapping.md 2), so "reading the tag" and "calling the probe" denote the same value; the model cannot and should not distinguish them, since the discriminating observable (crash-on-absent vs. reject-exactly-when-some-present-rejects) is identical. atk_8 adds a discarded call on a present argument, which is dead code. Neither changes the outcome on any input, so their resolving is the correct outcome, not a gap.

### A-LEG AUDIT (the R/I legs are G-CONF's job):
- refinement.md has exactly 6 legs, tags extracted mechanically: A1=R, A2=R+I, A3=R+I, A4=A-consumed, A5=R+I, A6=I(observationally). NO kind-3 (unexpressible-changed-op) leg. Section C's claim is accurate: the operation that genuinely changed (the absent-entry guard) is modeled DIRECTLY by the status-0 skip in A3, not hidden behind an axiom. meta.json deep_model_references == [] and additional_change_sites == [], consistent with there being no A-reference leg -- correct here, since the change is a control-flow guard rather than a value computation.
- A4 (the single A-consumed leg) correspondence VERIFIED against the real callee at base_commit b34751b7: `sklearn/utils/validation.py:784`, body `return parameter in signature(estimator.fit).parameters`, called at `sklearn/ensemble/voting.py:81` -- both line references in mapping.md 3.1 are exact. The callee is UNCHANGED by the gold patch (patch.diff touches only voting.py's loop), so axiomatizing it is legitimate rather than a way to assume the fix. The precondition `status in {1,2}` is faithful, not fabricated: the body dereferences `estimator.fit`, so `has_fit_parameter(None, ...)` genuinely raises AttributeError -- and that restriction is LOAD-BEARING in the right direction, since it is precisely what rejects atk_1 (the prepatch bug). The `Ensures(Result() == (status == 1))` direction is the weakest fact the fold needs and is not stronger than the real bool-returning callee. axiom_check.py exercises the REAL probe (imports sklearn.utils.validation.has_fit_parameter) over 9 weight-accepting + 2 weight-rejecting estimators + 2000 fuzz AND asserts the raise-on-None; recorded G-AX exit 0. I could not re-execute axiom_check.py on the host (no sklearn in the host env -- it is an in-container check by design), so that leg rests on the recorded G-AX stamp rather than my own re-run.
- Model<->patch correspondence holds on the discriminating observable. The gold hunk is a 2-line insertion of `if step is None: continue` before the probe; the model's status-0 branch skips the probe identically. Section B's full-scan <-> short-circuit equivalence argument is sound: the loop body holds only Acc(...,1/2) (read-only, so no side effect on the roster can make visit order observable), and both forms return-normally iff every present entry accepts. atk_13 (position-dependent skip) and atk_3/atk_12 (partial domain) confirm mechanically that the spec does not actually permit order- or position-sensitive behaviour to sneak through that equivalence.

ONE DOCUMENTATION DEFECT FOUND (advisory, NOT a verify=>correct break; no attack exploits it and I did not treat it as grounds for BROKEN): refinement.md legs A1 and A5, and mapping.md 2, each assert the rejection's MESSAGE TEXT is "unobserved by the tests" / "the message string is unobserved". That is FALSE.

PASS_TO_PASS includes sklearn/ensemble/tests/test_voting.py::test_sample_weight, which at base_commit (test_voting.py:347-348) does `msg = ('Underlying estimator \'knn\' does not support sample weights.')` then `assert_raise_message`; assert_raise_message (sklearn/utils/testing.py:387-417) substring-matches `str(e)`, so BOTH the exception class ValueError AND the message text -- including the interpolated `name` that A1 says is "dropped" because it is unobserved -- are load-bearing for a P2P test.

This does not weaken the spec as submitted (the model's WeightingUnsupported stand-in is forced by the Nagini translator limitation, and dropping `name` is a genuine R-refinement that the gold patch does not touch: the gold patch leaves the raise statement byte-identical, so no admissible attack can alter the message without editing a line outside the modeled hunk). But the JUSTIFICATION as written is wrong about the test suite, and a future refinement that leaned on "the message is unobserved" to license changing the raise would break test_sample_weight. Recommend correcting A1/A5/mapping-2 to say the message is unchanged-by-the-patch (hence outside the pinned behaviour) rather than unobserved-by-the-tests.

CONCLUSION: 13 same-spec attacks encoded and fully verified, 11 rejected by the spec, 2 CANDIDATEs both materialized and EXECUTED through run_resolve with RESOLVED=True (F2P 2/2, P2P 18/18, non-flaky, patch applied). Positive control verifies; prepatch bug reproduced and rejected on the predicted obligation. No verifying wrong impl whose faithful patch fails to resolve => verify=>correct holds for this bundle. Verdict SOUND, with the message-observability wording defect noted above as an advisory docs fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch_probe_on_absent.py`, `atk_2_never_rejects.py`, `atk_3_skips_last_entry.py`, `atk_4_absent_treated_as_reject.py`, `atk_6_quantifier_swap_all_reject.py`, `atk_7_off_by_one_index.py`, `atk_9_diverge_on_absent.py`, `atk_10_rejects_empty_roster.py`, `atk_11_probes_wrong_entry.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_oracle_echo_no_probe.py`, `atk_8_fabricated_probe_arg.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_probe_on_absent.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_never_rejects.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_skips_last_entry.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_absent_treated_as_reject.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_oracle_echo_no_probe.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_quantifier_swap_all_reject.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_off_by_one_index.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_fabricated_probe_arg.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_diverge_on_absent.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_rejects_empty_roster.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_probes_wrong_entry.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_only_first_entry.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_position_dependent_skip.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13779.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ensemble meta-estimator holds a roster of named sub-estimators. Each entry
  of the roster is either ABSENT (a placeholder that has been cleared away and
  carries no sub-estimator at all) or PRESENT (it carries a real sub-estimator,
  which itself either does or does not accept per-sample weighting).

  When the caller supplies per-sample weights, the meta-estimator must first
  check that the configuration can honour them, by consulting each roster entry:

    * An ABSENT entry carries no sub-estimator, so there is nothing to consult.
      The capability probe — which inspects a sub-estimator's fitting interface —
      is meaningful ONLY for a present sub-estimator and must NOT be applied to an
      absent entry. An absent entry is simply skipped and can never, by itself,
      cause the check to fail or error.

    * A PRESENT entry is consulted via the capability probe. If the present
      sub-estimator does not accept per-sample weighting, the configuration
      cannot honour the supplied weights and the check rejects it.

  The behaviour pinned here: the weighted-fit pre-check returns normally exactly
  when every PRESENT sub-estimator accepts per-sample weighting (absent entries
  notwithstanding), and rejects (raises) exactly when some PRESENT sub-estimator
  does not. The probe is never consulted for an absent entry.

The roster is modelled as a `List[int]` of per-entry status tags: 0 = absent,
1 = present-and-accepts-weighting, 2 = present-and-rejects-weighting. The
capability probe is an unchanged callee the check invokes; it inspects a present
sub-estimator's interface, so it is meaningful only for a present entry — this is
encoded as its precondition (consulting it on an absent entry is out of contract,
exactly as the real probe dereferences an attribute that an absent entry lacks).
The rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2). Nagini bans `str` indexing, so the
specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class WeightingUnsupported(Exception):
    """Signals a rejected weighted-fit configuration: some present sub-estimator
    does not accept per-sample weighting. Stands in for the `ValueError` the
    desired behaviour raises; a builtin exception in an `Exsures` crashes the
    Nagini translator (mapping.md §2)."""

# axioms-start
@Pure
@ContractOnly
def accepts_weighting(status: int) -> bool:
    """The capability probe applied to one roster entry: whether the carried
    sub-estimator accepts per-sample weighting. It inspects a PRESENT
    sub-estimator's fitting interface, so it is meaningful only for a present
    entry; consulting it on an absent entry is out of contract (the real probe
    dereferences an attribute an absent entry does not have). Hence its
    precondition admits only the present statuses {1, 2}, and it reports
    acceptance exactly on status 1. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(status == 1 or status == 2)
    Ensures(Result() == (status == 1))
# axioms-end

# pure-start
@Pure
def config_supports(roster: PSeq[int]) -> bool:
    """Whether the configuration can honour per-sample weights: every PRESENT
    entry accepts weighting. An absent entry (0) and a present-accepting entry
    (1) are both fine; only a present-rejecting entry (2) breaks support. Front-
    recursive over the sequence so a single unfold is available per loop step."""
    if len(roster) == 0:
        return True
    return roster[0] != 2 and config_supports(roster.drop(1))
# pure-end

def check_weighting_support(roster: List[int]) -> None:
    # pre-conditions-start
    # Every entry is a valid status tag: 0 absent, 1 present-accepts,
    # 2 present-rejects.
    Requires(Acc(list_pred(roster), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(roster),
                             0 <= roster[k] and roster[k] <= 2),
                     [[roster[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input: fractional permission, required and ensured (and returned
    # on the exceptional path too), so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Ensures(Acc(list_pred(roster), 1 / 2))
    # Returns normally exactly when every PRESENT entry accepts weighting. Absent
    # entries are skipped: they do not appear in this condition.
    Ensures(config_supports(ToSeq(roster)))
    # Rejects (raises) exactly when some PRESENT entry does not accept weighting.
    Exsures(WeightingUnsupported,
            Acc(list_pred(roster), 1 / 2)
            and (not config_supports(ToSeq(roster))))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
    # step). An absent entry (0) is skipped — the probe is never consulted on it,
    # honouring its precondition. A present entry (1 or 2) is consulted via the
    # probe; `supported` folds whether every present entry seen so far accepts.
    # The single rejection is raised once, at the end, when `supported` is false
    # (observationally identical to raising on the first present-rejecting entry;
    # refinement.md justifies the short-circuit equivalence).
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        # `supported` tracks support over the suffix already scanned.
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            # absent entry: skip, never consult the probe on it
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

13 DISTINCT same-spec wrong impls encoded (all built by gen.py, which splices ONLY the impl-region body of the frozen model.py, leaving axioms/@Pure/Requires/Ensures byte-identical). All 14 files (13 attacks + positive control) pass `adversary same-spec` with exit 0.

Per-attack logs at <file>.weakness.log; tally at results.txt.

POSITIVE CONTROL: pos_control.py (byte-identical to frozen model.py, asserted in gen.py) => exit 0, CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (13.4s). The spec is not vacuously unsatisfiable.

PREPATCH REPRODUCED: atk_1_prepatch_probe_on_absent.py re-encodes the pre-patch bug (probe consulted on EVERY entry incl. status 0, no absent-entry skip) => exit 2, verification failed. The failure lands exactly where refinement.md B/D and mapping.md 3.1 predict: the call-site precondition `status == 1 or status == 2` of accepts_weighting is unprovable on a status-0 entry -- the formal face of `'NoneType' object has no attribute 'fit'`. G-DIFF sensing confirmed independently of the bundle's own model_prepatch.py.

### ATTACK RESULTS (exit 2 = spec REJECTED the wrong impl):
- atk_1 prepatch, probe on absent entry: exit 2 REJECTED
- atk_2 never rejects (skip status 0 AND 2, so `supported` can never go False): exit 2 REJECTED
- atk_3 partial domain / boundary, LAST entry never examined (test_sample_weight's rejecting 'knn' is last): exit 2 REJECTED
- atk_4 control-flow effect, absent entry treated as a REJECTION rather than skipped (probe still never consulted on it, so the axiom precondition IS honoured -- this attack isolates the postcondition rather than the axiom): exit 2 REJECTED
- atk_5 ungrounded-oracle echo, probe NEVER invoked, status tag read directly (`if status == 2`): exit 0 CANDIDATE (verifies, 13.5s)
- atk_6 quantifier swap, reject only when EVERY present entry rejects: exit 2 REJECTED
- atk_7 off-by-one, consults roster[i] not roster[i-1] so index 0 never examined: exit 2 REJECTED
- atk_8 fabricated probe argument, absent-entry branch DOES consult the probe but on a fabricated PRESENT status `accepts_weighting(1)`: exit 0 CANDIDATE (verifies, 13.7s)
- atk_9 divergence, `while True` on an absent entry (right answer whenever it returns at all): exit 2 REJECTED -- MustTerminate(i+1)/MustTerminate(2) at the METHOD level really does pin termination here
- atk_10 empty-roster boundary, rejects an empty roster which supports weighting vacuously: exit 2 REJECTED
- atk_11 wrong probe argument / aliasing, present entries judged by probing a DIFFERENT present entry's status (argument still a present status, so the precondition holds): exit 2 REJECTED
- atk_12 partial domain complement, only roster index 0 examined: exit 2 REJECTED
- atk_13 position-dependent skip, a present-rejecting entry at index 0 is skipped (rejection made a function of roster POSITION): exit 2 REJECTED

MANDATORY RESOLVE RUNS -- both CANDIDATEs materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, SWE-bench_Verified, real Docker oracle):

1) atk_5 -> patch_atk_5.diff. The faithful refinement of "the probe is never invoked; the status tag is read directly" is the short-circuit `step is not None and not has_fit_parameter(...)`: under the R-map (mapping.md 2) `status == 2` IS `step is not None and not has_fit_parameter(step,'sample_weight')`, and Python's `and` makes the probe unreachable for an absent entry exactly as the model's status-0 path does. run_resolve => RESOLVED=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=True, FAIL_TO_PASS 2/2 success 0 failure, PASS_TO_PASS 18/18 success 0 failure. Log: resolve_atk_5.log. NOT a counterexample.

2) atk_8 -> patch_atk_8.diff. Faithful refinement: keep the `if step is None: continue` skip but still call the probe on a fabricated PRESENT argument (`self`, whose own `fit` declares `sample_weight`) and discard the result. First attempt errored on a hand-written hunk header (`no report ... Instances with errors: 1`, resolve_atk_8.log); the diff was REGENERATED mechanically via `git diff` in a throwaway worktree and re-checked with `git apply --check` before re-running -- so this is a fixed harness input, not an unexplained infra failure. run_resolve (run_id geqaudit-atk8-v2) => RESOLVED=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=True, FAIL_TO_PASS 2/2, PASS_TO_PASS 18/18. Log: resolve_atk_8_v2.log. NOT a counterexample.

Why both candidates were expected to resolve, and why that is the spec being RIGHT rather than the attacks being weak: atk_5 and atk_8 are the only two shapes the spec admits beyond the frozen impl, and both are behavioural no-ops on the observable surface. atk_5 differs only in WHETHER the probe symbol is syntactically invoked -- but under the R-map the status tag is DEFINED by the probe's result (mapping.md 2), so "reading the tag" and "calling the probe" denote the same value; the model cannot and should not distinguish them, since the discriminating observable (crash-on-absent vs. reject-exactly-when-some-present-rejects) is identical. atk_8 adds a discarded call on a present argument, which is dead code. Neither changes the outcome on any input, so their resolving is the correct outcome, not a gap.

### A-LEG AUDIT (the R/I legs are G-CONF's job):
- refinement.md has exactly 6 legs, tags extracted mechanically: A1=R, A2=R+I, A3=R+I, A4=A-consumed, A5=R+I, A6=I(observationally). NO kind-3 (unexpressible-changed-op) leg. Section C's claim is accurate: the operation that genuinely changed (the absent-entry guard) is modeled DIRECTLY by the status-0 skip in A3, not hidden behind an axiom. meta.json deep_model_references == [] and additional_change_sites == [], consistent with there being no A-reference leg -- correct here, since the change is a control-flow guard rather than a value computation.
- A4 (the single A-consumed leg) correspondence VERIFIED against the real callee at base_commit b34751b7: `sklearn/utils/validation.py:784`, body `return parameter in signature(estimator.fit).parameters`, called at `sklearn/ensemble/voting.py:81` -- both line references in mapping.md 3.1 are exact. The callee is UNCHANGED by the gold patch (patch.diff touches only voting.py's loop), so axiomatizing it is legitimate rather than a way to assume the fix. The precondition `status in {1,2}` is faithful, not fabricated: the body dereferences `estimator.fit`, so `has_fit_parameter(None, ...)` genuinely raises AttributeError -- and that restriction is LOAD-BEARING in the right direction, since it is precisely what rejects atk_1 (the prepatch bug). The `Ensures(Result() == (status == 1))` direction is the weakest fact the fold needs and is not stronger than the real bool-returning callee. axiom_check.py exercises the REAL probe (imports sklearn.utils.validation.has_fit_parameter) over 9 weight-accepting + 2 weight-rejecting estimators + 2000 fuzz AND asserts the raise-on-None; recorded G-AX exit 0. I could not re-execute axiom_check.py on the host (no sklearn in the host env -- it is an in-container check by design), so that leg rests on the recorded G-AX stamp rather than my own re-run.
- Model<->patch correspondence holds on the discriminating observable. The gold hunk is a 2-line insertion of `if step is None: continue` before the probe; the model's status-0 branch skips the probe identically. Section B's full-scan <-> short-circuit equivalence argument is sound: the loop body holds only Acc(...,1/2) (read-only, so no side effect on the roster can make visit order observable), and both forms return-normally iff every present entry accepts. atk_13 (position-dependent skip) and atk_3/atk_12 (partial domain) confirm mechanically that the spec does not actually permit order- or position-sensitive behaviour to sneak through that equivalence.

ONE DOCUMENTATION DEFECT FOUND (advisory, NOT a verify=>correct break; no attack exploits it and I did not treat it as grounds for BROKEN): refinement.md legs A1 and A5, and mapping.md 2, each assert the rejection's MESSAGE TEXT is "unobserved by the tests" / "the message string is unobserved". That is FALSE.

PASS_TO_PASS includes sklearn/ensemble/tests/test_voting.py::test_sample_weight, which at base_commit (test_voting.py:347-348) does `msg = ('Underlying estimator \'knn\' does not support sample weights.')` then `assert_raise_message`; assert_raise_message (sklearn/utils/testing.py:387-417) substring-matches `str(e)`, so BOTH the exception class ValueError AND the message text -- including the interpolated `name` that A1 says is "dropped" because it is unobserved -- are load-bearing for a P2P test.

This does not weaken the spec as submitted (the model's WeightingUnsupported stand-in is forced by the Nagini translator limitation, and dropping `name` is a genuine R-refinement that the gold patch does not touch: the gold patch leaves the raise statement byte-identical, so no admissible attack can alter the message without editing a line outside the modeled hunk). But the JUSTIFICATION as written is wrong about the test suite, and a future refinement that leaned on "the message is unobserved" to license changing the raise would break test_sample_weight. Recommend correcting A1/A5/mapping-2 to say the message is unchanged-by-the-patch (hence outside the pinned behaviour) rather than unobserved-by-the-tests.

CONCLUSION: 13 same-spec attacks encoded and fully verified, 11 rejected by the spec, 2 CANDIDATEs both materialized and EXECUTED through run_resolve with RESOLVED=True (F2P 2/2, P2P 18/18, non-flaky, patch applied). Positive control verifies; prepatch bug reproduced and rejected on the predicted obligation. No verifying wrong impl whose faithful patch fails to resolve => verify=>correct holds for this bundle. Verdict SOUND, with the message-observability wording defect noted above as an advisory docs fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled function (check_weighting_support) disagrees with the real repo callee, or show the spec is too strong / drifted. RESULT: no such input found. Verdict FAITHFUL.

SETUP. Fresh worktree of scikit-learn at base_commit b34751b7ed02b2cfcc36037fb729d4360480a299 (/tmp only; bundle never modified — `git status --porcelain -- benchmark-verified/scikit-learn__scikit-learn-13779/` is empty; worktree removed after use). Read the real region sklearn/ensemble/voting.py:79-83 inside _BaseVoting.fit and the unchanged callee sklearn/utils/validation.py:808 `has_fit_parameter` = `return parameter in signature(estimator.fit).parameters`. That body depends only on stdlib inspect.signature, so I transcribed it BYTE-FAITHFULLY rather than relying on a compiled sklearn (no docker image exists for this instance; sklearn is not importable in the host env).

(1) SPEC IDENTITY. `same-spec` exits 0 for every variant I built; markers.spec_view hash 96029e8c2141b46f identical to the bundle for all of them. Only impl regions ever differed.

 IN-DOMAIN DIFFERENTIAL — 65,465 inputs, ZERO divergence (atk2f_13779_diff2.py). Compared the model's PINNED semantics (its Ensures/Exsures: return normally iff config_supports, raise iff not) against the exact transcription of the PATCHED real region. Exhaustive rosters length 0..6 over {0,1,2} crossed with 5 distinct status->estimator factories (synthesized; LogisticRegression/RandomForest/SVC/KNeighbors signature shapes as they actually appear at this commit; plus test_sample_weight_kwargs' MockClassifier whose `**sample_weight` VAR_KEYWORD makes the real probe return True), then 60,000 fuzz rosters up to length 24 biased to discriminating shapes. Model outcome == real outcome on every single one.

(3) AXIOM IS NOT STRONGER THAN REALITY. Probe bijection confirmed against the real callee: weight-accepting shapes -> True (tag 1), KNeighbors-shaped fit(X,y) -> False (tag 2). Precondition Requires(status in {1,2}) is FAITHFUL, not an invented restriction: the real `has_fit_parameter(None,'sample_weight')` genuinely raises AttributeError "'NoneType' object has no attribute 'fit'" — exactly the bug. Also confirmed the real probe is deterministic (5000 repeats, single-valued), returns a true bool, and does not mutate the estimator — so the @Pure/@ContractOnly modeling is sound.

(4) SPEC IS NOT TOO STRONG — the decisive test. The bundle's impl scans back-to-front and raises once at the end, while the GOLD patch scans forward and short-circuits on the FIRST rejecting entry. I wrote the literal gold-shaped impl (forward + short-circuit raise) against the FROZEN spec. First attempt FAILED ("Assertion (not config_supports(ToSeq(roster))) might not hold") — but only on the prefix->whole bridge lemma, exactly the missing-lemma situation refinement.md §B predicts. Supplying that one bridge invariant (config_supports(whole) == config_supports(drop)) makes the gold-shaped short-circuit impl VERIFY (atk2f_13779_gold2.py, same-spec 0, "Verification successful"). So the spec does admit the real algorithm's shape; the full-scan form is proof engineering, not a behavioural constraint. No over-strength.

(5) SPEC STILL SENSES THE BUG. model_prepatch.py shares the spec and FAILS precisely on the probe precondition ("The precondition of function accepts_weighting might not hold") — the formal face of the AttributeError. Non-vacuity controls all behave: Assert(False) fails (precondition satisfiable, spec not vacuous); always-raise fails the Ensures; never-raise fails the Exsures. Pristine bundle verifies in 13.3s.

(6) DOMAIN-GAP HUNT — the only real residue, and it is NOT a defect. I found present (non-None) steps the {0,1,2} tagging cannot classify because the real probe RAISES on them: an object with no .fit (AttributeError), fit=print, fit=3 (TypeError: not callable), fit via a property that raises. These are outside the model's Requires. But each is IDENTICAL pre- and post-patch (the gold hunk only adds `if step is None: continue`, which cannot affect a non-None step), so the patch does not change that behaviour and excluding it neither hides the bug nor admits a wrong impl. Note some become AttributeError-on-None pre-patch when preceded by a None entry, but the post-patch outcome is still a crash of the same kind — no F2P/P2P test constructs such a member. This is legitimate skeleton-faithful scoping (mapping.md §1), not drift.

(7) MINOR, NON-DEFECT MODELING SLACK, disclosed for completeness: (a) the model drops `name`, so it cannot pin WHICH estimator the message identifies; with >1 rejecting entry the real code names the first while the model raises anonymously at the end. Unobservable on the tested inputs — test_sample_weight has exactly ONE rejecting entry ('knn', so first==last) and the F2P test_none_estimator_with_weights ([None, rf]) has none. (b) The empty roster has no real-execution counterpart (the surrounding estimators-empty guard at voting.py:66-70 fires first) but the model and real region agree there anyway. (c) ValueError -> WeightingUnsupported is a forced translator workaround (documented, mapping.md §2) and preserves the discriminating observable: a weighting rejection vs. the un-fixed AttributeError crash.

CONCLUSION: I could not produce a diverging input. The modeled function agrees with the real patched region on all 65,465 in-domain inputs tested, the axiom is the weakest sufficient contract and is never stronger than the real callee, the spec admits the gold algorithm's own shape, and it still rejects the pre-patch impl. FAITHFUL — no faithfulness break to report.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: leakage / gold-reconstruction of the consumer spec view for scikit-learn__scikit-learn-13779 (nagini). Judged against problem_statement ONLY; hints_text is empty here in any case.

SPEC VIEW RENDERED INDEPENDENTLY. Projected model.py via swebench_unified.markers.spec_view (nagini LanguageTables) rather than trusting the bundle. Confirmed elision is complete and idempotent: 'Invariant', 'while i > 0', 'raise WeightingUnsupported', 'ToSeq(roster).drop', and the back-to-front scan comment are all absent from the view; spec_view(spec_view(x))==spec_view(x). The only surviving 'supported'/'supports' tokens are the spec's own names (WeightingUnsupported, config_supports), not the impl's local `supported` flag.

GOLD EDIT. patch.diff adds exactly two lines to sklearn/ensemble/voting.py: `if step is None:` / `continue`. Reconstruction targets are therefore (a) the file/module path, (b) the repo symbols in the hunk, (c) the two added lines, (d) the fix mechanism.

MECHANICAL SCREEN. leakage.screen() -> passed, zero hard failures, zero warnings. I treated that as near-vacuous rather than dispositive: _patch_changed_symbols(gold) is the EMPTY SET for this patch (the added lines declare no def/class), so the L2/L5 identifier check and the L2/L3 comment-symbol check have nothing to screen against, and both added lines normalize below/at the len>=8 bar in a way that cannot collide. A pass here is close to free, so I re-ran the checks by hand at stricter thresholds.

### MANUAL CHECKS (all negative for leakage):
- Gold fragments at threshold 4 instead of the harness's 8, whitespace-normalized: 'if step is None:', 'continue', 'step is None', and even bare 'is None' are all ABSENT from the view.
- Paths: 'sklearn', 'voting', 'ensemble.voting', 'sklearn.ensemble.voting' absent (the lone 'ensemble' hit is the English phrase 'An ensemble meta-estimator', not a module path). No diff markers.
- Repo symbols from the hunk NOT in the PS -- has_fit_parameter, step, name, ValueError -- appear in ZERO spec-view identifiers. The full identifier set is abstract domain/Nagini vocabulary only: accepts_weighting, check_weighting_support, config_supports, roster, status, WeightingUnsupported. 'step' occurs once, in the English phrase 'one unfold is available per loop step'; 'ValueError' occurs once, as the declared stand-in the translator forced (mapping.md §2) -- naming a builtin exception type localizes no edit and the raise line is CONTEXT in the hunk, not an added line.
- Narration: no bug/fix/patched/regression/incorrectly vocabulary. The docstring is written as desired behaviour, not as an edit or a diagnosis.

THE ONE REAL QUESTION -- 'an absent entry is simply skipped'. This is the closest thing to the gold mechanism (`continue`), so I examined whether it exceeds the PS. It does not: the issue itself states the diagnosis verbatim -- "Because we don't check for an estimator to be `None` in `sample_weight` support, `fit` is failing" -- plus `voter.set_params(lr=None)` and `AttributeError: 'NoneType' object has no attribute 'fit'`. Every substantive spec-view claim maps onto public PS text: roster of named sub-estimators <- the estimators=[('lr',...),('rf',...)] literal; entries can be cleared to absent <- set_params(lr=None); weights trigger a pre-check <- 'if weights are passed' + sample_weight=np.ones(...); absent entries must be skipped and the probe not applied to them <- the author's own 'we don't check for an estimator to be None'; the probe dereferences an attribute an absent entry lacks <- the quoted AttributeError. The spec adds abstraction (status tags 0/1/2, PSeq encoding), not edit-localization. A solver handed this view learns the behavioural obligation the issue already states; it is not told which file, function, or line to touch, nor the two-line form of the fix.

Retained meta.json labels: G-PANEL/G-PANEL-1/-2/-3 all read 'fail', but each detail is 'INCONCLUSIVE -- the audit role did not run' with 0 of 0 attacks admissible and no positive control. That is a harness/host failure, not a recorded leakage finding, and G-LEAK itself is status 'pass', mode 'strict', detail 'spec view clean', with no RELAXED_LEAKAGE.md in the bundle. I judged fresh from the rendered view rather than inheriting those labels.

Tooling sanity: confirmed `adversary same-spec` is live and discriminating on this instance (a one-comment impl-region edit returns 'SAME -- attack shares the bundle's exact specification', exit 0), so the spec-region identity used for the projection is trustworthy.

CONCLUSION: no spec-view line reveals the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
