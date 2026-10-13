# P2 adversarial audit — sympy__sympy-15976

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.py`, `atk_2_recursion.py`, `atk_3_diverge_loop.py`, `atk_5_partial_domain_msub_root.py`, `atk_6_slot_swap.py`, `atk_7_group_collapse_supers.py`, `atk_8_bold_drop_bare.py`, `atk_10_fake_measure.py`, `atk_11_bare_wrapper.py`, `atk_13_cross_role_group.py`, `atk_14_ctags_mutate.py`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo_oracle.py` |

**Non-vacuity.** The positive control `atk_0_positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified. The two CANDIDATEs (exit 0) were both CORRECT impls whose faithful refined patches RESOLVED on the official harness, so neither is a counterexample:

(1) atk_0_positive_control.py = the gold impl verbatim (the required positive control): verifies in 13.7s; patch_atk_0_positive_control.diff => run_resolve(run_id=geq-zx-atk0, timeout=1800) RESOLVED=True COMPLETED=True, F2P 1/1 (test_presentation_symbol), P2P 37/37.

(2) atk_9_echo_oracle.py = the ungrounded-oracle ECHO probe: it builds the root as MNode(root_tag_for(has_subs, has_supers), kids) with conditionally-appended kids rather than re-deriving the four-way branch. Discharged the candidate obligation as the protocol requires: (a) exhaustive enumeration of all 16 flag combinations shows (root, kids) == (root_tag_for, child_tags_for) on every combo, i.e. it IS a correct impl; (b) confirmed on the real oracle: patch_atk_9_echo_oracle.diff => run_resolve(run_id=geq-zx-atk9, timeout=1800) RESOLVED=True COMPLETED=True, F2P 1/1, P2P 37/37. Echoing root_tag_for/child_tags_for/sub_group_tag/sup_group_tag is not an answer-key leak here because those @Pure oracles are TOTAL grounded functions of the flag ARGUMENTS the caller supplies -- computing them IS computing the right answer, and G-LEAK passes independently.

IMPORTANT PROVENANCE NOTE: the recorded meta.json G-EQ verdict (fail/BROKEN, stamped 21:06) is STALE with respect to the current model.py. That break was the partial-correctness hole (no MustTerminate => a diverging/self-recursing rival satisfies every Ensures vacuously). model.py was subsequently REPAIRED at 21:27 -- it now carries `from nagini_contracts.obligations import MustTerminate`, `Requires(MustTerminate(2))` on print_symbol and `Requires(MustTerminate(1))` on MNode.__init__. I re-encoded that exact prior counterexample (atk_2_recursion.py) plus three further termination-evasion variants and all four are now REJECTED:
  - atk_2_recursion.py  => 'Obligation leak check failed. Callee print_symbol might not take all unsatisfied obligations from the caller.'
  - atk_3_diverge_loop.py => 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
  - atk_10_fake_measure.py (constant Invariant(MustTerminate(1)) on a diverging loop) => 'Obligation leak check failed. Loop might not keep promise to terminate.'
  - atk_15_diverge_combined_only.py (partial-domain divergence: correct on 3 branches, diverges only on the both-scripts domain) => same loop-obligation rejection.
So the hole the stale stamp records is closed, and the docstring/pre-conditions text now states the totality obligation explicitly ('Rendering is TOTAL ... a renderer that consumes a name and yields no tree -- for any reason -- has not met them').
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,26 +214,24 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the produced root is ALWAYS an identifier element, and
+    # the structural element (when there are sub/superscripts) is appended as the
+    # identifier's single child rather than being the root itself.
     x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
+    kids = []  # type: List[int]
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
+            pass                                   # name is the identifier's text
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
+            kids = [TAG_MSUB]                      # msub appended inside the mi
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
+            kids = [TAG_MSUP]                      # msup appended inside the mi
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
+            kids = [TAG_MSUBSUP]                   # msubsup appended inside the mi
+    x = MNode(TAG_MI, kids)                        # root is always <mi>
+    # Set the bold marker on the produced root (the identifier element; touches
+    # only the marker, leaving the element kind and child kinds unchanged).
     ct = node_ctags(x)
     tg = node_tag(x)
     Unfold(node_pred(x))
```

Attack 2 — `atk_2_recursion.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,32 +214,6 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
-    x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
-    if not has_supers:
-        if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
-        else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
-    else:
-        if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
-        else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
-    Unfold(node_pred(x))
-    x.bold = bold
-    Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
-    return x
+    r = print_symbol(name, has_subs, has_supers, subs_multi, supers_multi, bold)
+    return r
     # impl-end
```

Attack 3 — `atk_3_diverge_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,32 +214,24 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
-    x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
+    kids = []  # type: List[int]
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
+            pass
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
+            kids = [TAG_MSUB]
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
+            kids = [TAG_MSUP]
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
+            kids = [TAG_MSUBSUP]
+    x = MNode(TAG_MI, kids)          # prepatch wrong root
+    spin = 0
+    while spin >= 0:
+        Invariant(spin >= 0)
+        spin = spin + 1
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 4 — `atk_5_partial_domain_msub_root.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,21 +219,18 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
+            kids = [TAG_MNAME, sub_g, sup_g]
+            x = MNode(TAG_MSUB, kids)   # WRONG: msub, not msubsup
     ct = node_ctags(x)
     tg = node_tag(x)
     Unfold(node_pred(x))
```

Attack 5 — `atk_6_slot_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,20 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sup_g, sub_g]   # WRONG: supers before subs
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 6 — `atk_7_group_collapse_supers.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,30 +216,23 @@
     # impl-start
     x = None  # type: Optional[MNode]
     sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
+    sup_g = TAG_SUP_ONE            # WRONG: ignores supers_multi (no mrow)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 7 — `atk_8_bold_drop_bare.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,20 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
-    x.bold = bold
+    x.bold = bold and (has_subs or has_supers)   # WRONG on the bare kind
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 8 — `atk_10_fake_measure.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,32 +214,25 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
-    x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
+    kids = []  # type: List[int]
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
+            pass
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
+            kids = [TAG_MSUB]
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
+            kids = [TAG_MSUP]
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
+            kids = [TAG_MSUBSUP]
+    x = MNode(TAG_MI, kids)          # prepatch wrong root
+    spin = 0
+    while spin >= 0:
+        Invariant(spin >= 0)
+        Invariant(MustTerminate(1))
+        spin = spin + 1
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 9 — `atk_11_bare_wrapper.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,20 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
+            kids = [TAG_MNAME]        # WRONG: mi wrapping the name identifier
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 10 — `atk_13_cross_role_group.py` → rejected (same spec, does not verify — good)

```diff
@@ -215,31 +215,24 @@
     # post-conditions-end
     # impl-start
     x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
+    sub_g = sup_group_tag(subs_multi)   # WRONG role code for the subs slot
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 11 — `atk_14_ctags_mutate.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,21 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
+    x.ctags.append(TAG_MNAME)     # WRONG: spurious extra child, after the fact
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 12 — `atk_15_diverge_combined_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,24 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
+            kids = [TAG_MNAME, sub_g]
+            x = MNode(TAG_MSUB, kids)     # WRONG tree on the combined domain
+            spin = 0
+            while spin >= 0:              # ...never observed: diverges here
+                Invariant(spin >= 0)
+                spin = spin + 1
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 13 — `atk_16_group_collapse_subs.py` → rejected (same spec, does not verify — good)

```diff
@@ -215,31 +215,24 @@
     # post-conditions-end
     # impl-start
     x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
+    sub_g = TAG_SUB_ONE            # WRONG: ignores subs_multi (no mrow)
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 14 — `atk_17_bold_drop_combined.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,27 +219,20 @@
     sup_g = sup_group_tag(supers_multi)
     if not has_supers:
         if not has_subs:
-            # bare identifier: the name is its own text content, no element child
             kids = []  # type: List[int]
             x = MNode(TAG_MI, kids)
         else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
+            kids = [TAG_MNAME, sub_g]
             x = MNode(TAG_MSUB, kids)
     else:
         if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
+            kids = [TAG_MNAME, sup_g]
             x = MNode(TAG_MSUP, kids)
         else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
+            kids = [TAG_MNAME, sub_g, sup_g]
             x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
     Unfold(node_pred(x))
-    x.bold = bold
+    x.bold = bold and not (has_subs and has_supers)   # WRONG on msubsup
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 15 — `atk_18_alias_name_list.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,32 +214,9 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
-    x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
-    if not has_supers:
-        if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
-        else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
-    else:
-        if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
-        else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
+    x = MNode(root_tag_for(has_subs, has_supers), name)   # ALIAS the caller's list
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

Attack 16 — `atk_9_echo_oracle.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -214,32 +214,16 @@
     Ensures(node_bold(Result()) == bold)
     # post-conditions-end
     # impl-start
-    x = None  # type: Optional[MNode]
-    sub_g = sub_group_tag(subs_multi)
-    sup_g = sup_group_tag(supers_multi)
-    if not has_supers:
-        if not has_subs:
-            # bare identifier: the name is its own text content, no element child
-            kids = []  # type: List[int]
-            x = MNode(TAG_MI, kids)
-        else:
-            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
-            x = MNode(TAG_MSUB, kids)
-    else:
-        if not has_subs:
-            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
-            x = MNode(TAG_MSUP, kids)
-        else:
-            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
-            x = MNode(TAG_MSUBSUP, kids)
-    # Set the bold marker on the produced root (touches only the marker; the
-    # element kind and child kinds are unchanged).
-    ct = node_ctags(x)
-    tg = node_tag(x)
+    kids = []  # type: List[int]
+    if has_subs or has_supers:
+        kids.append(TAG_MNAME)
+        if has_subs:
+            kids.append(sub_group_tag(subs_multi))
+        if has_supers:
+            kids.append(sup_group_tag(supers_multi))
+    x = MNode(root_tag_for(has_subs, has_supers), kids)
     Unfold(node_pred(x))
     x.bold = bold
     Fold(node_pred(x))
-    Assert(node_ctags(x) == ct)
-    Assert(node_tag(x) == tg)
     return x
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-15976.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A named quantity is rendered to a small presentation-markup tree. The name may
  carry an ordered list of subscript parts and an ordered list of superscript
  parts; the renderer chooses one of four ROOT element kinds purely from whether
  those two lists are empty:

      no subscripts and no superscripts  -> an identifier element (`mi`)
      subscripts only                    -> a subscript element (`msub`)
      superscripts only                  -> a superscript element (`msup`)
      both                               -> a sub-and-superscript element (`msubsup`)

  The chosen kind is the ROOT of the produced tree. Its direct children are, in
  order: the identifier element holding the base name FIRST, then the rendered
  subscript group and/or superscript group as the kind requires (subscript group
  before superscript group for the combined kind). A group of a SINGLE part is
  rendered as a bare identifier element; a group of more than one part is
  rendered as a grouping element. The base-name identifier and the rendered
  sub/super groups are the immediate (depth-one) children of this structural
  root.

  When a bold style is requested, the bold-font marker is set on the ROOT of the
  produced tree (whichever of the four kinds it is).

  Rendering is TOTAL: every name the renderer accepts is rendered to such a tree
  in a bounded number of steps. The structural claims above are obligations on
  every invocation, not merely on those invocations that happen to produce a
  result, so a renderer that consumes a name and yields no tree — for any reason
  — has not met them.

A markup element is modelled by the only facets the rendered tree exposes to a
consumer: its element kind (`tag`, an int code), the ordered kinds of its DIRECT
children (`ctags`, a `List[int]`), and the bold-font marker (`bold`). `tag`
mirrors the DOM `nodeName` of the element. `ctags[i]` mirrors the `nodeName` of
`childNodes[i]`, refined by ROLE identity: a consumer reads each child's own
content and the slot it occupies, so two children filling different roles are
never interchangeable even when they are the same element kind. Each child
therefore carries a code naming its role together with its kind — the identifier
holding the base name; the subscript group as one part or as several; the
superscript group as one part or as several. A group's role is determined by
which of the two ordered part lists it renders, never by the element kind it
happens to take, so the subscript slot and the superscript slot of the combined
kind stay distinguishable even when both groups render to the same kind. `print_symbol` is
the verified builder.

No callee is axiomatized for the tree construction: the structural choice is pure
logic, modelled deeply. The name/sub/super decomposition of the textual name is
performed by an unchanged community helper, whose result is abstracted to the two
emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as an
A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly. Markers
(machine-parsed) delimit spec/proof/impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# ROOT element-kind codes (abstract DOM tag identities).
TAG_MI = 1       # identifier element
TAG_MSUB = 2     # subscript element
TAG_MSUP = 3     # superscript element
TAG_MSUBSUP = 4  # sub-and-superscript element
# Direct-CHILD codes. A child is identified by the ROLE it fills as well as by
# its element kind, so children in different roles are never interchangeable
# even when they share an element kind — see the module docstring.
TAG_MNAME = 6      # the identifier child carrying the base name
TAG_SUB_ONE = 7    # the SUBSCRIPT group, one part      -> an identifier element
TAG_SUB_ROW = 8    # the SUBSCRIPT group, several parts -> a grouping element
TAG_SUP_ONE = 9    # the SUPERSCRIPT group, one part      -> an identifier element
TAG_SUP_ROW = 10   # the SUPERSCRIPT group, several parts -> a grouping element

# axioms-start
# (No consumed axioms. The structural choice of root element kind, and the
# placement of the base-name identifier and of each script group in its own
# DIRECT-child slot of that structural root, are pure logic — modelled deeply by
# the pure functions below and the
# verified `print_symbol` builder. The only callee the real code invokes here is
# the unchanged name-decomposition helper, whose result is abstracted to the two
# emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as
# an A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly.
# G-EQ audits the refinement against the real builder.)
# axioms-end

# pure-start
class MNode:
    """One element of the produced markup tree, abstracted to the facets a
    consumer observes: its element kind `tag`, the ordered kinds of its direct
    children `ctags` (mirroring the DOM node's `childNodes[i].nodeName`), and the
    bold-font marker `bold`."""

    def __init__(self, tag: int, ctags: List[int]) -> None:
        Requires(Acc(list_pred(ctags)))
        # Making an element is likewise total: it always yields the element.
        Requires(MustTerminate(1))
        Ensures(Acc(node_pred(self)))
        Ensures(node_tag(self) == tag)
        Ensures(node_ctags(self) == Old(ToSeq(ctags)))
        Ensures(node_bold(self) == False)
        self.tag = tag
        self.ctags = ctags
        self.bold = False
        Fold(node_pred(self))

@Predicate
def node_pred(n: MNode) -> bool:
    return Acc(n.tag) and Acc(n.ctags) and Acc(list_pred(n.ctags)) and Acc(n.bold)

@Pure
def node_tag(n: MNode) -> int:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.tag)

@Pure
def node_bold(n: MNode) -> bool:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.bold)

@Pure
def node_ctags(n: MNode) -> PSeq[int]:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), ToSeq(n.ctags))

@Pure
def root_tag_for(has_subs: bool, has_supers: bool) -> int:
    """The structural ROOT kind chosen purely from the two emptiness flags."""
    if not has_supers and not has_subs:
        return TAG_MI
    if not has_supers:
        return TAG_MSUB
    if not has_subs:
        return TAG_MSUP
    return TAG_MSUBSUP

@Pure
def sub_group_tag(multi: bool) -> int:
    """The code of the rendered SUBSCRIPT group: a grouping element when it holds
    more than one part, a bare identifier element for a single part. The code
    names the subscript role, so this group is never interchangeable with the
    superscript group."""
    if multi:
        return TAG_SUB_ROW
    return TAG_SUB_ONE

@Pure
def sup_group_tag(multi: bool) -> int:
    """The code of the rendered SUPERSCRIPT group: a grouping element when it
    holds more than one part, a bare identifier element for a single part. The
    code names the superscript role, so this group is never interchangeable with
    the subscript group."""
    if multi:
        return TAG_SUP_ROW
    return TAG_SUP_ONE

@Pure
def child_tags_for(has_subs: bool, has_supers: bool,
                   subs_multi: bool, supers_multi: bool) -> PSeq[int]:
    """The required direct children (role-and-kind codes, in order) of the
    structural root: the base-name identifier FIRST, then the subscript group
    and/or the superscript group as the chosen kind demands, the subscript group
    preceding the superscript group. A single-part group is an identifier; a
    multi-part group is a grouping element. Each group's code names the part
    list it renders, so the sequence pins WHICH group occupies each slot and not
    merely how many slots there are and what element kinds fill them. Empty for
    the bare identifier kind (the name text is its own text content, carrying no
    element child)."""
    if not has_supers and not has_subs:
        return PSeq(TAG_MNAME).take(0)                             # no element kids
    if not has_supers:
        return PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi))   # mname, subs
    if not has_subs:
        return PSeq(TAG_MNAME) + PSeq(sup_group_tag(supers_multi))  # mname, supers
    return (PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi)) +
            PSeq(sup_group_tag(supers_multi)))                     # mname, subs, sup
# pure-end

def print_symbol(name: List[int], has_subs: bool, has_supers: bool,
                 subs_multi: bool, supers_multi: bool, bold: bool) -> MNode:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # The rendering is a TOTAL obligation: the postconditions below are claimed
    # of EVERY invocation, not merely of the ones that happen to reach a return.
    # A renderer that consumes a name and never yields a tree has not rendered
    # it. Level 2, not 1, because building the child-kind list invokes a
    # constructor that carries its own obligation and needs room strictly below
    # the renderer's level.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(node_pred(Result())))
    # The ROOT is the structural kind chosen purely from the emptiness flags.
    Ensures(node_tag(Result()) == root_tag_for(has_subs, has_supers))
    # The base-name identifier (and any sub/super groups) are the depth-one
    # direct children of the structural root, in order. Each group is an
    # identifier for a single part, a grouping element for several, and each
    # occupies the slot of the part list it renders: the subscript group's slot
    # precedes the superscript group's, and the two are not interchangeable even
    # when both render to the same element kind.
    Ensures(node_ctags(Result()) ==
            child_tags_for(has_subs, has_supers, subs_multi, supers_multi))
    # The bold-font marker lands on the produced root.
    Ensures(node_bold(Result()) == bold)
    # post-conditions-end
    # impl-start
    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            # bare identifier: the name is its own text content, no element child
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
            x = MNode(TAG_MSUBSUP, kids)
    # Set the bold marker on the produced root (touches only the marker; the
    # element kind and child kinds are unchanged).
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 19 same-spec files encoded in  (each = model.py with ONLY the impl region edited; axioms/@Pure/Requires/Ensures byte-identical). ALL 19 pass `adversary same-spec` (exit 0, 'SAME -- attack shares the bundle's exact specification'). Weakness runs were batched 3-at-a-time as concurrent background jobs (each spawns a JVM+Z3), as instructed.

### COMMANDS (from repo root, SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-15976 <path>
  python -m swebench_unified.adversary weakness  nagini sympy__sympy-15976 <path>     # raw output at <path minus .py>.out
  bash scripts/nagini_verify.sh <path>                                                # rejection reason at <path minus .py>.direct
  python resolve.py <name> <run_id>      # wraps swebench_unified.harness.run_resolve

RESULTS -- 2 CANDIDATE (both correct, both RESOLVED), 17 rejected:
0. atk_0_positive_control.py -- gold impl verbatim -- exit 0 CANDIDATE, verifies 13.7s. POSITIVE CONTROL: the spec is not vacuously rejecting. run_resolve => RESOLVED=True COMPLETED=True.
1. atk_1_prepatch.py -- PREPATCH BUG (root always TAG_MI wrapping the structural element) -- exit 2. Rejected by P2: 'Postcondition ... (node_tag(Result()) == root_tag_for(has_subs, has_supers)) might not hold.' PREPATCH REPRODUCED.
2. atk_2_recursion.py -- CONTROL-FLOW-EFFECT, unbounded self-recursion (the PRIOR recorded counterexample) -- exit 2. 'Obligation leak check failed. Callee print_symbol might not take all unsatisfied obligations from the caller.'
3. atk_3_diverge_loop.py -- CONTROL-FLOW-EFFECT, builds the prepatch wrong tree then diverges (the prior second witness) -- exit 2. 'Loop might not take all unsatisfied obligations from the context.'
4. atk_4_raise_combined.py -- partial-domain by abrupt termination -- exit 2 but via TRANSLATION failure ('Unsupported builtin function' at the `raise`), NOT a semantic rejection. NOT COUNTED as evidence in either direction; excluded from the submitted attack list, and superseded by atk_15 which achieves partial-domain non-return in a translatable form.
5. atk_5_partial_domain_msub_root.py -- PARTIAL-DOMAIN/BOUNDARY: msub root on the combined domain -- exit 2, rejected by P2 (node_tag).
6. atk_6_slot_swap.py -- ROLE/SLOT SWAP [MNAME, sup_g, sub_g] on the combined kind -- exit 2, rejected by P3 (node_ctags). Both groups share a DOM nodeName when multiplicities match, so this is the load-bearing test of the role-identity refinement -- and it holds.
7. atk_7_group_collapse_supers.py -- BOUNDARY: pins sup_g = TAG_SUP_ONE, dropping the mrow for multi-part superscripts -- exit 2, P3.
8. atk_8_bold_drop_bare.py -- PARTIAL-DOMAIN bold: `bold and (has_subs or has_supers)`, dropping the marker on the bare kind -- exit 2, rejected by P4 (node_bold).
9. atk_9_echo_oracle.py -- UNGROUNDED-ORACLE ECHO -- exit 0 CANDIDATE, verifies 18.1s. Discharged: correct on all 16 flag combos AND run_resolve => RESOLVED=True COMPLETED=True. Second positive control, not a weakness.
10. atk_10_fake_measure.py -- TERMINATION-EVASION: diverging loop with a constant Invariant(MustTerminate(1)) -- exit 2. 'Loop might not keep promise to terminate.' The obligation cannot be faked with a non-decreasing measure.
11. atk_11_bare_wrapper.py -- BOUNDARY uncovered by the prepatch twin: an extra <mi> wrapper on the BARE domain only (prepatch appends a #text there, so its ctags is empty too -- genuinely distinct) -- exit 2, P3.
12. atk_12_nested_bottom.py -- termination evasion via a nested `def bottom(): Ensures(False)` -- exit 2 but via TRANSLATION failure ('Invalid program: nested.function.declaration'). NOT COUNTED, excluded from the attack list; superseded by atk_10/atk_15.
13. atk_13_cross_role_group.py -- CROSS-ROLE code: the SUPERSCRIPT group's code in the SUBSCRIPT slot (identical DOM nodeName when single) -- exit 2, P3. Confirms the role codes are not decorative.
14. atk_14_ctags_mutate.py -- POST-HOC MUTATION: correct tree, then `x.ctags.append(TAG_MNAME)` after the fact -- exit 2, P3. The postcondition pins the FINAL observable state, not an intermediate snapshot.
15. atk_15_diverge_combined_only.py -- PARTIAL-DOMAIN DIVERGENCE: correct on three branches, wrong tree + divergence only on the combined domain -- exit 2, loop-obligation rejection. The totality obligation is per-invocation, not just on the easy branches.
16. atk_16_group_collapse_subs.py -- BOUNDARY mirror of atk_7 on the SUBS side (pins sub_g = TAG_SUB_ONE) -- exit 2, P3.
17. atk_17_bold_drop_combined.py -- PARTIAL-DOMAIN bold on the COMBINED kind (`bold and not (has_subs and has_supers)`; the P2P bold-matrix path lands on the bare kind, so this boundary is not covered by atk_8) -- exit 2, P4.
18. atk_18_alias_name_list.py -- ALIASING/FRAMING: pass the caller's read-only `name` list as ctags -- exit 2, 'The precondition of method MNode might not hold. There might be insufficient permission to access list_pred(ctags).' The 1/2 fractional permission on `name` is load-bearing.

PATCH-MACHINERY CONTROL (so a non-resolve could not be blamed on my diff generation): I regenerated the gold-equivalent patch through my own generator (mkpatch.py) and diffed the resulting mathml.py against the officially-applied patch.diff result -- BYTE-IDENTICAL. Both my patches apply cleanly at base_commit 701441853569d370506514083b995d11f9a130bd (`patch -p1 --dry-run`), and both RESOLVE, so the generator is sound and a hypothetical non-resolve would have been attributable to attack semantics.

### REFINEMENT.MD AUDIT (the assigned A-leg focus):
- **LEG KINDS:** A1 R + A-reference; A2 R + I; A3 R + I; A4 R + I; A5 A-reference + I; A6 R + I. Every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op) leg. Section C's claim that there is no CONSUMED axiom is TRUE and mechanically confirmed: meta.json axioms == [], the axioms-start/axioms-end region is comment-only, and there is no @ContractOnly anywhere in model.py -- so no A-consumed leg exists to audit.
- A-REFERENCE 1 (A1: split_super_sub). Correspondence HOLDS. I read the real helper at base_commit (sympy/printing/conventions.py:14) and confirmed patch.diff touches ONLY sympy/printing/mathml.py -- conventions.py is not in the diff at all, so 'UNCHANGED' is exact, not asserted. The trailing-digit subscript rule the mapping cites (`_name_with_digits_p`, conventions.py:11 + the `m = _name_with_digits_p.match(name)` block) is present as documented and is genuinely why `x2` acquires a subscript and hits the bug. axiom_check.decomposition_flags CALLS the real helper and derives exactly has_subs=len(subs)>0 / has_supers=len(supers)>0 / subs_multi=len(subs)>1 / supers_multi=len(supers)>1 -- the abstraction refinement.md A1 claims.
- A-REFERENCE 2 (A5 + mapping 3.2: the fixed `_print_Symbol` builder and the nested join). Correspondence HOLDS, checked mechanically rather than by eye: I applied the gold patch.diff to the base mathml.py, extracted the post-patch `_print_Symbol` body, normalized whitespace/comments/imports, and diffed it against axiom_check.fixed_print_Symbol -- 48 vs 48 operations, IDENTICAL. So the builder G-AX installs on the real MathMLPresentationPrinter really is the gold body, not a re-reading of it, and `join` is carried verbatim (patch.diff does not touch the join body -- confirmed by grep over the diff). This is the trust point that matters most for an A-reference, and it is tight.
- WHAT G-AX ACTUALLY ASSERTS (read, not taken on faith): per name it checks root nodeName == model_root_nodename, the ELEMENT-child nodeName sequence == model_child_nodenames (with '#text' filtered, matching mapping 2's 'text content is not an element child'), the POSITIONAL role/content check (TAG_MNAME's child must be an mi whose #text is the translated base name; a group code's child must render exactly that code's part list, with the assertion message naming the other list -- this is what discriminates the two script slots that share a nodeName at equal multiplicity), the no-extra-mi invariant, and bold-on-root. Over 13 named (all F2P shapes + the trailing-digit issue names + greek) x {plain,bold} + 4000 seeded fuzz names. Nothing claimed in mapping 3.2 is missing from the script.
- MODEL <-> PATCH CORRESPONDENCE: the four-way branch, the child ORDER (mname first, subs group before supers group), the bare-identifier case binding x = mname (hence empty ctags), and the bold move to the END onto the chosen root all line up one-to-one with the gold hunk. My attacks 6/11/13/14/16 empirically confirm each of those is pinned by a postcondition rather than merely narrated.
- REFINEMENT.MD SECTION D IS NOW SOUND, where it previously was not. Its inference 'the verified renderer produces, on every tested symbol name, the same (nodeName, child nodeNames, bold) triple as the gold `_print_Symbol`' presupposes that a verifying impl TERMINATES AND RETURNS. The MustTerminate repair supplies that premise (attacks 2/3/10/15 are the machine-checked evidence). ONE DOCUMENTATION GAP, non-blocking and NOT a soundness defect: neither the refinement.md leg table nor section D mentions termination/totality at all (grep for 'terminat'/'total' over refinement.md: zero hits), even though the model's pre-conditions region now carries Requires(MustTerminate(2)) and the docstring states the totality obligation. The obligation is doing real work that the refinement map does not credit -- recommend adding a leg (e.g. A7: model `Requires(MustTerminate(2))` <-> the gold `_print_Symbol` being straight-line and total, tag R) and a sentence in section D saying the totality premise is discharged by the obligation rather than assumed. That is a completeness fix to the map's prose, not a hole in the spec.

**VERDICT BASIS:** 16 submitted same-spec wrong impls spanning partial-domain, boundary, control-flow-effect/termination-evasion, role/slot, post-hoc-mutation, aliasing and ungrounded-oracle-echo classes; all 16 rejected by a named clause (P2 node_tag / P3 node_ctags / P4 node_bold / MNode's permission precondition / the MustTerminate obligation). Both exit-0 candidates were shown CORRECT and both RESOLVED on the official harness (COMPLETED=True). Prepatch reproduced and sensed by P2. No verifying wrong impl exists among these, so no verify-not-implies-correct witness -- SOUND. Caveat carried honestly: the recorded meta.json G-EQ stamp is a stale fail against a pre-repair model.py and should be re-stamped from this run; atk_4 and atk_12 hit Nagini TRANSLATION limits rather than semantic rejection and are excluded from the attack list so they cannot be miscounted as rejections the spec performed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.py`, `atk_2_recursion.py`, `atk_3_diverge_loop.py`, `atk_5_partial_domain_msub_root.py`, `atk_6_slot_swap.py`, `atk_7_group_collapse_supers.py`, `atk_8_bold_drop_bare.py`, `atk_10_fake_measure.py`, `atk_11_bare_wrapper.py`, `atk_13_cross_role_group.py`, `atk_14_ctags_mutate.py`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo_oracle.py` |

**Non-vacuity.** The positive control `atk_0_positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified. The two CANDIDATEs (exit 0) were both CORRECT impls whose faithful refined patches RESOLVED on the official harness, so neither is a counterexample:

(1) atk_0_positive_control.py = the gold impl verbatim (the required positive control): verifies in 13.7s; patch_atk_0_positive_control.diff => run_resolve(run_id=geq-zx-atk0, timeout=1800) RESOLVED=True COMPLETED=True, F2P 1/1 (test_presentation_symbol), P2P 37/37.

(2) atk_9_echo_oracle.py = the ungrounded-oracle ECHO probe: it builds the root as MNode(root_tag_for(has_subs, has_supers), kids) with conditionally-appended kids rather than re-deriving the four-way branch. Discharged the candidate obligation as the protocol requires: (a) exhaustive enumeration of all 16 flag combinations shows (root, kids) == (root_tag_for, child_tags_for) on every combo, i.e. it IS a correct impl; (b) confirmed on the real oracle: patch_atk_9_echo_oracle.diff => run_resolve(run_id=geq-zx-atk9, timeout=1800) RESOLVED=True COMPLETED=True, F2P 1/1, P2P 37/37. Echoing root_tag_for/child_tags_for/sub_group_tag/sup_group_tag is not an answer-key leak here because those @Pure oracles are TOTAL grounded functions of the flag ARGUMENTS the caller supplies -- computing them IS computing the right answer, and G-LEAK passes independently.

IMPORTANT PROVENANCE NOTE: the recorded meta.json G-EQ verdict (fail/BROKEN, stamped 21:06) is STALE with respect to the current model.py. That break was the partial-correctness hole (no MustTerminate => a diverging/self-recursing rival satisfies every Ensures vacuously). model.py was subsequently REPAIRED at 21:27 -- it now carries `from nagini_contracts.obligations import MustTerminate`, `Requires(MustTerminate(2))` on print_symbol and `Requires(MustTerminate(1))` on MNode.__init__. I re-encoded that exact prior counterexample (atk_2_recursion.py) plus three further termination-evasion variants and all four are now REJECTED:
  - atk_2_recursion.py  => 'Obligation leak check failed. Callee print_symbol might not take all unsatisfied obligations from the caller.'
  - atk_3_diverge_loop.py => 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.'
  - atk_10_fake_measure.py (constant Invariant(MustTerminate(1)) on a diverging loop) => 'Obligation leak check failed. Loop might not keep promise to terminate.'
  - atk_15_diverge_combined_only.py (partial-domain divergence: correct on 3 branches, diverges only on the both-scripts domain) => same loop-obligation rejection.
So the hole the stale stamp records is closed, and the docstring/pre-conditions text now states the totality obligation explicitly ('Rendering is TOTAL ... a renderer that consumes a name and yields no tree -- for any reason -- has not met them').
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_recursion.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_diverge_loop.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_partial_domain_msub_root.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_slot_swap.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_group_collapse_supers.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_bold_drop_bare.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10_fake_measure.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11_bare_wrapper.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_13_cross_role_group.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_14_ctags_mutate.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_15_diverge_combined_only.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_16_group_collapse_subs.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_17_bold_drop_combined.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_18_alias_name_list.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_9_echo_oracle.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-15976.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A named quantity is rendered to a small presentation-markup tree. The name may
  carry an ordered list of subscript parts and an ordered list of superscript
  parts; the renderer chooses one of four ROOT element kinds purely from whether
  those two lists are empty:

      no subscripts and no superscripts  -> an identifier element (`mi`)
      subscripts only                    -> a subscript element (`msub`)
      superscripts only                  -> a superscript element (`msup`)
      both                               -> a sub-and-superscript element (`msubsup`)

  The chosen kind is the ROOT of the produced tree. Its direct children are, in
  order: the identifier element holding the base name FIRST, then the rendered
  subscript group and/or superscript group as the kind requires (subscript group
  before superscript group for the combined kind). A group of a SINGLE part is
  rendered as a bare identifier element; a group of more than one part is
  rendered as a grouping element. The base-name identifier and the rendered
  sub/super groups are the immediate (depth-one) children of this structural
  root.

  When a bold style is requested, the bold-font marker is set on the ROOT of the
  produced tree (whichever of the four kinds it is).

  Rendering is TOTAL: every name the renderer accepts is rendered to such a tree
  in a bounded number of steps. The structural claims above are obligations on
  every invocation, not merely on those invocations that happen to produce a
  result, so a renderer that consumes a name and yields no tree — for any reason
  — has not met them.

A markup element is modelled by the only facets the rendered tree exposes to a
consumer: its element kind (`tag`, an int code), the ordered kinds of its DIRECT
children (`ctags`, a `List[int]`), and the bold-font marker (`bold`). `tag`
mirrors the DOM `nodeName` of the element. `ctags[i]` mirrors the `nodeName` of
`childNodes[i]`, refined by ROLE identity: a consumer reads each child's own
content and the slot it occupies, so two children filling different roles are
never interchangeable even when they are the same element kind. Each child
therefore carries a code naming its role together with its kind — the identifier
holding the base name; the subscript group as one part or as several; the
superscript group as one part or as several. A group's role is determined by
which of the two ordered part lists it renders, never by the element kind it
happens to take, so the subscript slot and the superscript slot of the combined
kind stay distinguishable even when both groups render to the same kind. `print_symbol` is
the verified builder.

No callee is axiomatized for the tree construction: the structural choice is pure
logic, modelled deeply. The name/sub/super decomposition of the textual name is
performed by an unchanged community helper, whose result is abstracted to the two
emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as an
A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly. Markers
(machine-parsed) delimit spec/proof/impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# ROOT element-kind codes (abstract DOM tag identities).
TAG_MI = 1       # identifier element
TAG_MSUB = 2     # subscript element
TAG_MSUP = 3     # superscript element
TAG_MSUBSUP = 4  # sub-and-superscript element
# Direct-CHILD codes. A child is identified by the ROLE it fills as well as by
# its element kind, so children in different roles are never interchangeable
# even when they share an element kind — see the module docstring.
TAG_MNAME = 6      # the identifier child carrying the base name
TAG_SUB_ONE = 7    # the SUBSCRIPT group, one part      -> an identifier element
TAG_SUB_ROW = 8    # the SUBSCRIPT group, several parts -> a grouping element
TAG_SUP_ONE = 9    # the SUPERSCRIPT group, one part      -> an identifier element
TAG_SUP_ROW = 10   # the SUPERSCRIPT group, several parts -> a grouping element

# axioms-start
# (No consumed axioms. The structural choice of root element kind, and the
# placement of the base-name identifier and of each script group in its own
# DIRECT-child slot of that structural root, are pure logic — modelled deeply by
# the pure functions below and the
# verified `print_symbol` builder. The only callee the real code invokes here is
# the unchanged name-decomposition helper, whose result is abstracted to the two
# emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as
# an A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly.
# G-EQ audits the refinement against the real builder.)
# axioms-end

# pure-start
class MNode:
    """One element of the produced markup tree, abstracted to the facets a
    consumer observes: its element kind `tag`, the ordered kinds of its direct
    children `ctags` (mirroring the DOM node's `childNodes[i].nodeName`), and the
    bold-font marker `bold`."""

    def __init__(self, tag: int, ctags: List[int]) -> None:
        Requires(Acc(list_pred(ctags)))
        # Making an element is likewise total: it always yields the element.
        Requires(MustTerminate(1))
        Ensures(Acc(node_pred(self)))
        Ensures(node_tag(self) == tag)
        Ensures(node_ctags(self) == Old(ToSeq(ctags)))
        Ensures(node_bold(self) == False)
        self.tag = tag
        self.ctags = ctags
        self.bold = False
        Fold(node_pred(self))

@Predicate
def node_pred(n: MNode) -> bool:
    return Acc(n.tag) and Acc(n.ctags) and Acc(list_pred(n.ctags)) and Acc(n.bold)

@Pure
def node_tag(n: MNode) -> int:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.tag)

@Pure
def node_bold(n: MNode) -> bool:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.bold)

@Pure
def node_ctags(n: MNode) -> PSeq[int]:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), ToSeq(n.ctags))

@Pure
def root_tag_for(has_subs: bool, has_supers: bool) -> int:
    """The structural ROOT kind chosen purely from the two emptiness flags."""
    if not has_supers and not has_subs:
        return TAG_MI
    if not has_supers:
        return TAG_MSUB
    if not has_subs:
        return TAG_MSUP
    return TAG_MSUBSUP

@Pure
def sub_group_tag(multi: bool) -> int:
    """The code of the rendered SUBSCRIPT group: a grouping element when it holds
    more than one part, a bare identifier element for a single part. The code
    names the subscript role, so this group is never interchangeable with the
    superscript group."""
    if multi:
        return TAG_SUB_ROW
    return TAG_SUB_ONE

@Pure
def sup_group_tag(multi: bool) -> int:
    """The code of the rendered SUPERSCRIPT group: a grouping element when it
    holds more than one part, a bare identifier element for a single part. The
    code names the superscript role, so this group is never interchangeable with
    the subscript group."""
    if multi:
        return TAG_SUP_ROW
    return TAG_SUP_ONE

@Pure
def child_tags_for(has_subs: bool, has_supers: bool,
                   subs_multi: bool, supers_multi: bool) -> PSeq[int]:
    """The required direct children (role-and-kind codes, in order) of the
    structural root: the base-name identifier FIRST, then the subscript group
    and/or the superscript group as the chosen kind demands, the subscript group
    preceding the superscript group. A single-part group is an identifier; a
    multi-part group is a grouping element. Each group's code names the part
    list it renders, so the sequence pins WHICH group occupies each slot and not
    merely how many slots there are and what element kinds fill them. Empty for
    the bare identifier kind (the name text is its own text content, carrying no
    element child)."""
    if not has_supers and not has_subs:
        return PSeq(TAG_MNAME).take(0)                             # no element kids
    if not has_supers:
        return PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi))   # mname, subs
    if not has_subs:
        return PSeq(TAG_MNAME) + PSeq(sup_group_tag(supers_multi))  # mname, supers
    return (PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi)) +
            PSeq(sup_group_tag(supers_multi)))                     # mname, subs, sup
# pure-end

def print_symbol(name: List[int], has_subs: bool, has_supers: bool,
                 subs_multi: bool, supers_multi: bool, bold: bool) -> MNode:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # The rendering is a TOTAL obligation: the postconditions below are claimed
    # of EVERY invocation, not merely of the ones that happen to reach a return.
    # A renderer that consumes a name and never yields a tree has not rendered
    # it. Level 2, not 1, because building the child-kind list invokes a
    # constructor that carries its own obligation and needs room strictly below
    # the renderer's level.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(node_pred(Result())))
    # The ROOT is the structural kind chosen purely from the emptiness flags.
    Ensures(node_tag(Result()) == root_tag_for(has_subs, has_supers))
    # The base-name identifier (and any sub/super groups) are the depth-one
    # direct children of the structural root, in order. Each group is an
    # identifier for a single part, a grouping element for several, and each
    # occupies the slot of the part list it renders: the subscript group's slot
    # precedes the superscript group's, and the two are not interchangeable even
    # when both render to the same element kind.
    Ensures(node_ctags(Result()) ==
            child_tags_for(has_subs, has_supers, subs_multi, supers_multi))
    # The bold-font marker lands on the produced root.
    Ensures(node_bold(Result()) == bold)
    # post-conditions-end
    # impl-start
    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            # bare identifier: the name is its own text content, no element child
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
            x = MNode(TAG_MSUBSUP, kids)
    # Set the bold marker on the produced root (touches only the marker; the
    # element kind and child kinds are unchanged).
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 19 same-spec files encoded in  (each = model.py with ONLY the impl region edited; axioms/@Pure/Requires/Ensures byte-identical). ALL 19 pass `adversary same-spec` (exit 0, 'SAME -- attack shares the bundle's exact specification'). Weakness runs were batched 3-at-a-time as concurrent background jobs (each spawns a JVM+Z3), as instructed.

### COMMANDS (from repo root, SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-15976 <path>
  python -m swebench_unified.adversary weakness  nagini sympy__sympy-15976 <path>     # raw output at <path minus .py>.out
  bash scripts/nagini_verify.sh <path>                                                # rejection reason at <path minus .py>.direct
  python resolve.py <name> <run_id>      # wraps swebench_unified.harness.run_resolve

RESULTS -- 2 CANDIDATE (both correct, both RESOLVED), 17 rejected:
0. atk_0_positive_control.py -- gold impl verbatim -- exit 0 CANDIDATE, verifies 13.7s. POSITIVE CONTROL: the spec is not vacuously rejecting. run_resolve => RESOLVED=True COMPLETED=True.
1. atk_1_prepatch.py -- PREPATCH BUG (root always TAG_MI wrapping the structural element) -- exit 2. Rejected by P2: 'Postcondition ... (node_tag(Result()) == root_tag_for(has_subs, has_supers)) might not hold.' PREPATCH REPRODUCED.
2. atk_2_recursion.py -- CONTROL-FLOW-EFFECT, unbounded self-recursion (the PRIOR recorded counterexample) -- exit 2. 'Obligation leak check failed. Callee print_symbol might not take all unsatisfied obligations from the caller.'
3. atk_3_diverge_loop.py -- CONTROL-FLOW-EFFECT, builds the prepatch wrong tree then diverges (the prior second witness) -- exit 2. 'Loop might not take all unsatisfied obligations from the context.'
4. atk_4_raise_combined.py -- partial-domain by abrupt termination -- exit 2 but via TRANSLATION failure ('Unsupported builtin function' at the `raise`), NOT a semantic rejection. NOT COUNTED as evidence in either direction; excluded from the submitted attack list, and superseded by atk_15 which achieves partial-domain non-return in a translatable form.
5. atk_5_partial_domain_msub_root.py -- PARTIAL-DOMAIN/BOUNDARY: msub root on the combined domain -- exit 2, rejected by P2 (node_tag).
6. atk_6_slot_swap.py -- ROLE/SLOT SWAP [MNAME, sup_g, sub_g] on the combined kind -- exit 2, rejected by P3 (node_ctags). Both groups share a DOM nodeName when multiplicities match, so this is the load-bearing test of the role-identity refinement -- and it holds.
7. atk_7_group_collapse_supers.py -- BOUNDARY: pins sup_g = TAG_SUP_ONE, dropping the mrow for multi-part superscripts -- exit 2, P3.
8. atk_8_bold_drop_bare.py -- PARTIAL-DOMAIN bold: `bold and (has_subs or has_supers)`, dropping the marker on the bare kind -- exit 2, rejected by P4 (node_bold).
9. atk_9_echo_oracle.py -- UNGROUNDED-ORACLE ECHO -- exit 0 CANDIDATE, verifies 18.1s. Discharged: correct on all 16 flag combos AND run_resolve => RESOLVED=True COMPLETED=True. Second positive control, not a weakness.
10. atk_10_fake_measure.py -- TERMINATION-EVASION: diverging loop with a constant Invariant(MustTerminate(1)) -- exit 2. 'Loop might not keep promise to terminate.' The obligation cannot be faked with a non-decreasing measure.
11. atk_11_bare_wrapper.py -- BOUNDARY uncovered by the prepatch twin: an extra <mi> wrapper on the BARE domain only (prepatch appends a #text there, so its ctags is empty too -- genuinely distinct) -- exit 2, P3.
12. atk_12_nested_bottom.py -- termination evasion via a nested `def bottom(): Ensures(False)` -- exit 2 but via TRANSLATION failure ('Invalid program: nested.function.declaration'). NOT COUNTED, excluded from the attack list; superseded by atk_10/atk_15.
13. atk_13_cross_role_group.py -- CROSS-ROLE code: the SUPERSCRIPT group's code in the SUBSCRIPT slot (identical DOM nodeName when single) -- exit 2, P3. Confirms the role codes are not decorative.
14. atk_14_ctags_mutate.py -- POST-HOC MUTATION: correct tree, then `x.ctags.append(TAG_MNAME)` after the fact -- exit 2, P3. The postcondition pins the FINAL observable state, not an intermediate snapshot.
15. atk_15_diverge_combined_only.py -- PARTIAL-DOMAIN DIVERGENCE: correct on three branches, wrong tree + divergence only on the combined domain -- exit 2, loop-obligation rejection. The totality obligation is per-invocation, not just on the easy branches.
16. atk_16_group_collapse_subs.py -- BOUNDARY mirror of atk_7 on the SUBS side (pins sub_g = TAG_SUB_ONE) -- exit 2, P3.
17. atk_17_bold_drop_combined.py -- PARTIAL-DOMAIN bold on the COMBINED kind (`bold and not (has_subs and has_supers)`; the P2P bold-matrix path lands on the bare kind, so this boundary is not covered by atk_8) -- exit 2, P4.
18. atk_18_alias_name_list.py -- ALIASING/FRAMING: pass the caller's read-only `name` list as ctags -- exit 2, 'The precondition of method MNode might not hold. There might be insufficient permission to access list_pred(ctags).' The 1/2 fractional permission on `name` is load-bearing.

PATCH-MACHINERY CONTROL (so a non-resolve could not be blamed on my diff generation): I regenerated the gold-equivalent patch through my own generator (mkpatch.py) and diffed the resulting mathml.py against the officially-applied patch.diff result -- BYTE-IDENTICAL. Both my patches apply cleanly at base_commit 701441853569d370506514083b995d11f9a130bd (`patch -p1 --dry-run`), and both RESOLVE, so the generator is sound and a hypothetical non-resolve would have been attributable to attack semantics.

### REFINEMENT.MD AUDIT (the assigned A-leg focus):
- **LEG KINDS:** A1 R + A-reference; A2 R + I; A3 R + I; A4 R + I; A5 A-reference + I; A6 R + I. Every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op) leg. Section C's claim that there is no CONSUMED axiom is TRUE and mechanically confirmed: meta.json axioms == [], the axioms-start/axioms-end region is comment-only, and there is no @ContractOnly anywhere in model.py -- so no A-consumed leg exists to audit.
- A-REFERENCE 1 (A1: split_super_sub). Correspondence HOLDS. I read the real helper at base_commit (sympy/printing/conventions.py:14) and confirmed patch.diff touches ONLY sympy/printing/mathml.py -- conventions.py is not in the diff at all, so 'UNCHANGED' is exact, not asserted. The trailing-digit subscript rule the mapping cites (`_name_with_digits_p`, conventions.py:11 + the `m = _name_with_digits_p.match(name)` block) is present as documented and is genuinely why `x2` acquires a subscript and hits the bug. axiom_check.decomposition_flags CALLS the real helper and derives exactly has_subs=len(subs)>0 / has_supers=len(supers)>0 / subs_multi=len(subs)>1 / supers_multi=len(supers)>1 -- the abstraction refinement.md A1 claims.
- A-REFERENCE 2 (A5 + mapping 3.2: the fixed `_print_Symbol` builder and the nested join). Correspondence HOLDS, checked mechanically rather than by eye: I applied the gold patch.diff to the base mathml.py, extracted the post-patch `_print_Symbol` body, normalized whitespace/comments/imports, and diffed it against axiom_check.fixed_print_Symbol -- 48 vs 48 operations, IDENTICAL. So the builder G-AX installs on the real MathMLPresentationPrinter really is the gold body, not a re-reading of it, and `join` is carried verbatim (patch.diff does not touch the join body -- confirmed by grep over the diff). This is the trust point that matters most for an A-reference, and it is tight.
- WHAT G-AX ACTUALLY ASSERTS (read, not taken on faith): per name it checks root nodeName == model_root_nodename, the ELEMENT-child nodeName sequence == model_child_nodenames (with '#text' filtered, matching mapping 2's 'text content is not an element child'), the POSITIONAL role/content check (TAG_MNAME's child must be an mi whose #text is the translated base name; a group code's child must render exactly that code's part list, with the assertion message naming the other list -- this is what discriminates the two script slots that share a nodeName at equal multiplicity), the no-extra-mi invariant, and bold-on-root. Over 13 named (all F2P shapes + the trailing-digit issue names + greek) x {plain,bold} + 4000 seeded fuzz names. Nothing claimed in mapping 3.2 is missing from the script.
- MODEL <-> PATCH CORRESPONDENCE: the four-way branch, the child ORDER (mname first, subs group before supers group), the bare-identifier case binding x = mname (hence empty ctags), and the bold move to the END onto the chosen root all line up one-to-one with the gold hunk. My attacks 6/11/13/14/16 empirically confirm each of those is pinned by a postcondition rather than merely narrated.
- REFINEMENT.MD SECTION D IS NOW SOUND, where it previously was not. Its inference 'the verified renderer produces, on every tested symbol name, the same (nodeName, child nodeNames, bold) triple as the gold `_print_Symbol`' presupposes that a verifying impl TERMINATES AND RETURNS. The MustTerminate repair supplies that premise (attacks 2/3/10/15 are the machine-checked evidence). ONE DOCUMENTATION GAP, non-blocking and NOT a soundness defect: neither the refinement.md leg table nor section D mentions termination/totality at all (grep for 'terminat'/'total' over refinement.md: zero hits), even though the model's pre-conditions region now carries Requires(MustTerminate(2)) and the docstring states the totality obligation. The obligation is doing real work that the refinement map does not credit -- recommend adding a leg (e.g. A7: model `Requires(MustTerminate(2))` <-> the gold `_print_Symbol` being straight-line and total, tag R) and a sentence in section D saying the totality premise is discharged by the obligation rather than assumed. That is a completeness fix to the map's prose, not a hole in the spec.

**VERDICT BASIS:** 16 submitted same-spec wrong impls spanning partial-domain, boundary, control-flow-effect/termination-evasion, role/slot, post-hoc-mutation, aliasing and ungrounded-oracle-echo classes; all 16 rejected by a named clause (P2 node_tag / P3 node_ctags / P4 node_bold / MNode's permission precondition / the MustTerminate obligation). Both exit-0 candidates were shown CORRECT and both RESOLVED on the official harness (COMPLETED=True). Prepatch reproduced and sensed by P2. No verifying wrong impl exists among these, so no verify-not-implies-correct witness -- SOUND. Caveat carried honestly: the recorded meta.json G-EQ stamp is a stale fail against a pre-repair model.py and should be re-stamped from this run; atk_4 and atk_12 hit Nagini TRANSLATION limits rather than semantic rejection and are excluded from the attack list so they cannot be miscounted as rejections the spec performed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Fresh worktree from the upstream repository at base_commit 701441853569d370506514083b995d11f9a130bd, gold patch (extracted from data/swe_bench_verified/test.jsonl, byte-identical to the bundle's described hunk) applied cleanly => this is the reference. A second unpatched worktree * served as the mutation control. Nothing in the bundle was modified. Bundle model.py verifies under the pinned verifier (scripts/nagini_verify.sh, exit 0, 12.3s) and `adversary same-spec` on an unmodified copy returns SAME (exit 0), so the spec region I audited is the frozen one.

**METHOD.** I did NOT reuse the bundle's axiom_check.py/conformance_check.py. I wrote an independent harness (atk2_diff.py) that transliterates model.py's SPEC only (root_tag_for / child_tags_for / sub_group_tag / sup_group_tag and the four Ensures clauses), bridges via mapping.md §2 inverted (List[int] name -> str -> Symbol; bold -> style='bold'; MNode.tag <-> root nodeName; ctags[i] <-> nodeName of i-th direct non-#text child; MNode.bold <-> getAttribute('mathvariant')=='bold'), and calls the REAL patched `_print_Symbol` on real Symbol objects. Every one of the four postconditions was checked per input, including the role-identity refinement checked POSITIONALLY by content (TAG_MNAME child's text == translated base name; each group slot's rendered parts == the list its code names).

### EVIDENCE (all zero divergences against the patched reference).
1. 303 boundary names x {plain,bold,italic}: F2P shapes (x, x^2, x__2, x_2, x^3_2, x__3_2, x_2_a, x^2^a, x__2__a), issue trailing-digit names (x1, x2, x23, alpha1, Alpha12), P2P bold matrix name A, all 51 greek_unicode keys plus each decorated (`_1`, ^1^2, x_<greek>), and degenerate/adversarial names ('', `'_'`, '`__`', '`___`', '^', '^^', '^_', '_^', 'x_', 'x__', 'x^', 'x^^', '`_x`', '`__x`', '^x', 'x___', 'x_1_2_3_4', 'x_1^2_3^4', '0', '12', ' ', tab, newline, 'x y', 'x-y', '{x}', '\\alpha', 'x_{1}', literal unicode 'α'/'é', a 200-char name, 'x_a^a', 'x_a_a', 'x^a^a', 'x_1_1^1_1').
2. Abstract-domain completeness, self-checked: the observable domain is finite — (subs,supers) each in {absent,one,several} x bold — and I confirmed all 9/9 script classes were actually reached via the REAL split_super_sub (my first run reported only 8/9 and ERRORED; I added x_1^2^3 / x^2^3_1 / x_1^a^b^c to close the (1,2) class rather than letting the gap pass). The final fuzz histogram shows every class populated with >=1,552 hits: {(0,0):212865, (0,1):43285, (0,2):32861, (1,0):26580, (1,1):39854, (1,2):25093, (2,0):1552, (2,1):6489, (2,2):11421}.
3. Fuzzing: 60,000 + 250,000 + 400,000 names (three distinct seeds, alphabets including bare `'_'`/'^'/'`__`'/'^^' separators, digits, braces, backslash, whitespace, literal greek code points, greek words), each x a random style drawn from {plain,bold,italic,''}. Zero postcondition violations.
4. TOTALITY (the spec's strongest claim — 'Rendering is TOTAL ... a renderer that consumes a name and yields no tree, for any reason, has not met them'). This is the clause most likely to be too strong, so I probed it directly: 200,000 arbitrary unicode names => split_super_sub raised 0 times and `_print_Symbol` raised 0 times. Notably split_super_sub does NOT raise on '' (returns ('',[],[])) and 'x_' yields subs=[''] which join() renders fine, so no name in the accepted domain (the sole Requires is Acc(list_pred(name),1/2), i.e. any name) makes the real function fail to return. MustTerminate is likewise sound: both real callees are bounded loops over a finite string.
5. Delegation paths covered: `_print_MatrixSymbol` with mat_symbol_style in {plain,bold} on A, A_1, B^2, C_1^2, X12, and `_print_RandomSymbol` (sympy.stats Normal('X_1')) => msub ['mi','mi'], matching the model.
6. Statefulness: 360 invocations on a single shared MathMLPresentationPrinter (interleaved styles) — 0 divergences, so the model's stateless framing is faithful.
7. Bridge fidelity: Symbol(name).name == name on 80,000/80,000 fuzz names, so the str<->Symbol leg of the R-refinement introduces no drift.
8. Real test suite on the patched worktree: full sympy/printing/tests/test_mathml.py = 39 passed (F2P test_presentation_symbol passes post-patch; it FAILS on the unpatched worktree, confirming the reference direction).

### HARNESS TEETH (controls, so the null result is not a rubber stamp).
- Pre-patch control: the identical harness against the unpatched worktree reports 82,664 divergences, correctly localized to root nodeName and child sequence (e.g. x^2: real root 'mi', children ['msup'] vs model 'msup'/['mi','mi']), plus 8 MatrixSymbol root hits. So the harness detects exactly the wrapper bug.
- Swapped-slot mutant: monkeypatching the patched printer to emit msubsup children as (name, supers, subs) — a mutation INVISIBLE to a plain nodeName-sequence check whenever both lists have equal multiplicity — produced 6 divergences flagged by my positional content check (x_a^b: 'child 1 claimed subs, real renders [b] want [a]'). This confirms the role-identity refinement (TAG_SUB_ONE=7 vs TAG_SUP_ONE=9 both mapping to nodeName 'mi') is a genuine, checkable property of the real code and not an unfalsifiable strengthening.

**ASSESSMENT OF THE STRONGEST CLAUSES.** The spec is deliberately strong in three places and each survives: (a) role-identity child codes — justified because a consumer reads each child's content and slot, and verified positionally against the real DOM; (b) TAG_MNAME != TAG_MI pinning the base-name child FIRST — true of the real builder on every branch; (c) bold on the ROOT — true post-patch on all four kinds, and the model proves tag/ctags are unchanged by the bold mutation, matching setAttribute's semantics. The abstraction of split_super_sub to four emptiness/multiplicity flags loses information (which code points) but that information provably never reaches the structural choice or join's kind decision, so no observable is under-determined. I found no input on which the modeled function is stronger than the real callee.

**CONCLUSION:** FAITHFUL. No diverging input; the spec does not drift from or over-constrain the real post-patch behavior.

**SETUP.** Fresh worktree from the upstream repository at base_commit 701441853569d370506514083b995d11f9a130bd, gold patch (extracted from data/swe_bench_verified/test.jsonl, byte-identical to the bundle's described hunk) applied cleanly => this is the reference. A second unpatched worktree * served as the mutation control. Nothing in the bundle was modified. Bundle model.py verifies under the pinned verifier (scripts/nagini_verify.sh, exit 0, 12.3s) and `adversary same-spec` on an unmodified copy returns SAME (exit 0), so the spec region I audited is the frozen one.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** RE-DERIVED THE RELAXATION; DID NOT INHERIT IT. bundle untouched.

FACET RE-CONFIRMED as the only thing the spec view names beyond problem_statement: the presentation-MathML structural taxonomy — root element kind chosen four-way from sub/super emptiness (mi/msub/msup/msubsup); base-name identifier FIRST among the depth-one direct children, subscript group before superscript group; group = identifier for one part / grouping element for several; bold marker on the root. Nothing in the spec view goes beyond that facet.

SPEC-REGION INTEGRITY (my own recompute). markers.spec_view/same_spec/region_hashes with get_backend('nagini').language on the shipped model.py (sha256 ddf2483b1357...). same_spec(model.py, model_prepatch.py) = True. My region hashes: spec_view 9953324e731a..., pre-conditions 9e662ea58857..., post-conditions 09dd15556503..., pure 90bb9b228d29..., impl 64fde4ce6fd2.... These are the CURRENT artifact's hashes; meta.json's top-level region_hashes block (spec_view 45b5d4a88dde...) is the prepatch variant's set, as expected. meta.json G-LEAK sources.model.py = ddf2483b1357... matches what I audited, so I judged the stamped spec.

UNAVOIDABILITY — MY OWN LOAD-BEARING MEASUREMENT (the decisive test, `bash scripts/nagini_verify.sh`):
- baseline: model.py verifies, RC=0, 11.28s.
- model_prepatch.py (unstripped) → RC=1, fails at 204 on `node_tag(Result()) == root_tag_for(has_subs, has_supers)`. G-DIFF real.
- strip_B (BOTH structural Ensures deleted) + prepatch buggy impl → RC=0 VERIFICATION SUCCESSFUL. The removed clauses are jointly load-bearing: without the taxonomy the buggy always-<mi>-root renderer passes and G-DIFF collapses. A faithful spec cannot omit them.
- strip_A (root-tag clause only deleted) + prepatch impl → still RC=1 on the ctags clause; and strip_A + my wrong impl 1 (root hardcoded TAG_MI, children otherwise correct) → RC=0 VERIFIES, while full spec + wrong impl 1 → RC=1 on the root-tag clause. Root-tag clause individually load-bearing.
- strip_C (ctags clause only deleted) + my wrong impl 2 (root echoed from root_tag_for, base-name child dropped and sub/sup slots swapped) → RC=0 VERIFIES, while full spec + wrong impl 2 → RC=1 on the ctags clause. ctags clause individually load-bearing.
⇒ Both clauses are necessary, so the named facet is MINIMAL, not padded narration. Faithful + non-leaking is genuinely impossible here.

**PROBLEM_STATEMENT-ONLY DERIVATION:** DOES NOT EXIST. Word-boundary + substring scan of the real dataset problem_statement (1053 chars, data/swe_bench_verified/test.jsonl), all counts 0: mi, msub, msup, msubsup, mrow, subscript, superscript, wrap, nest, child, root, identifier, element, outermost, remove, extra, tag, nodeName, depth, bold, mathvariant, structur, group, order, first, createElement. It carries only the SYMPTOM (x2 invisible in Safari 12.0.2, screenshots). The structural diagnosis ('an extra set of <mi></mi> tags ... when they are removed') lives only in hints_text — correctly excluded from the bar — and in the hidden test_patch, whose post-gold assertions pin nodeName=='msub'/'msup'/'msubsup' and ordered childNodes directly.

LEAK-VOCABULARY GREP over the COMPUTED spec view: ZERO hits for wrapper/wrap/outer/outermost/extra/nested/nest/remove/removed/fix/fixed/bug/Safari/invisible/instead/previously/used to/rather than/single child/enclosing/one level/deeper/no longer/incorrect/wrong/broken/regression/`_print_Symbol`/mathml.py/patch/copy/createElement/setAttribute. 'mrow' is also 0 — de-narrated to 'grouping element'. Only nodeName (3) / childNodes (2) appear, and only as the declared R-refinement of the abstract facets. The residual is the positive behavioral contract, not bug/fix narration. Note the bold-on-root clause is NOT a discriminator (pre-patch also set mathvariant on its root, which was the wrapper mi) — it is a preserved invariant, so naming it leaks nothing about the edit.

CORE GATES THE ARGUMENT LEANS ON, RE-RUN BY ME: G-VERIFY model.py RC=0 (11.28s). G-DIFF prepatch RC=1 at 204, same_spec True. G-AX axiom_check.py exit 0 against a fresh worktree of the upstream repository at base_commit 701441853569d370506514083b995d11f9a130bd (13 named + 4000 fuzz; root nodeName + child nodeName sequence + no-extra-mi + bold placement, flags from the real split_super_sub). G-CONF conformance_check.py exit 0, 100060 inputs, 0 disagreements vs the real PATCHED `_print_Symbol` (it fails 1/4 against the un-patched tree — correct discrimination, and the expected sense). Faithfulness: bundle patch.diff sha256 cb296790ccb2... is byte-identical to the dataset gold patch; with test_patch applied, F2P test_presentation_symbol FAILS pre-patch and PASSES post-gold, and P2P test_print_matrix_symbol passes.

### FINDINGS I REPORT RATHER THAN INHERIT (none defeats the leakage disposition, none was taken at face value):
(a) The brief's documented-relaxation precondition is NOT actually met by this bundle's bookkeeping. meta.json has NO `relaxed_leakage` key, and gates.G-LEAK is recorded status='pass', mode='strict', detail='spec view clean' — not 'relaxed'. RELAXED_LEAKAGE.md section 3's assertion that "meta.json carries gates.G-LEAK.status = 'relaxed' pointing here" is FALSE. This cuts in the safe direction (the mechanical strict screen passes on its own merits), but the .md's provenance record is wrong and should be corrected.

(b) RELAXED_LEAKAGE.md section 1 asserts "G-EQ SOUND/TIGHT — 6 adversarial wrong impls ... all rejected". meta.json actually records G-EQ = fail / G-PANEL-1 = fail: 'BROKEN (verify⇏correct): atk_3_diverge_loop.py verifies but its patch does not resolve'. So the .md affirmatively overclaims the one gate its 'Core is sound' section rests on. I did NOT inherit either the claim or the failure — I measured the current artifact: the recorded break is STALE (G-EQ sources model.py = c24fabd79fa4..., 21:06; the shipped model.py is ddf2483b1357..., 21:27, and the newer revision adds `from nagini_contracts.obligations import MustTerminate`, `Requires(MustTerminate(1))` on MNode.`__init__` and `Requires(MustTerminate(2))` on print_symbol).

I rebuilt both break classes as same-spec attacks against the CURRENT spec (adversary same-spec RC=0 for each): unbounded self-recursion → REJECTED, 'Obligation leak check failed. Callee print_symbol might not take all unsatisfied obligations from the caller'; diverging while-loop → REJECTED, 'Loop might not take all unsatisfied obligations from the context'. The verify⇏correct hole the record names is closed on the shipped artifact, so the disposition is not broken — but that is my measurement, not the .md's assertion.

(c) RELAXED_LEAKAGE.md frames its own conclusion as settled policy ('it is KEPT with the leakage bar relaxed', 'All three requirements of the policy hold', 'faithful + non-leaking is provably impossible here') and cites ITSELF as the authority ('Per RELAXED_LEAKAGE.md'). Self-citation of a disposition is argument dressed as precedent. I grepped every bundle file (RELAXED_LEAKAGE.md, mapping.md, refinement.md, model.py, axiom_check.py, conformance_check.py, properties.py, meta.json) for auditor/reviewer/panel/'you should'/'must submit'/'the honest'/'do not report'/NO-LEAKAGE/LEAKAGE and found NO line instructing a reviewer what to record — so this is overclaiming argument, not an attempt to direct the panel. I treated it as a claim to check throughout, and every load-bearing part of it I re-derived independently above.

(d) Advisory only, not leakage: the totality paragraph added to the docstring (spec view lines 27-31) hardens the spec against the (b) evasions; it describes a general termination obligation, is true of both the pre- and post-patch real code, and therefore discloses nothing about the gold edit.

**VERDICT BASIS:** the unavoidability argument holds on my own strip re-derivation (strip_B verifying against the prepatch impl is the proof, and both single-clause strips prove minimality), the discriminator is not derivable from the problem_statement (all 26 structural tokens count 0), the spec view leaks nothing beyond that one facet (leak-vocabulary grep clean), and every core gate the argument leans on passes when I re-run it on the shipped hash — including the one the record shows as broken, which I confirmed repaired rather than assumed. Hence NO-LEAKAGE, with (a)/(b)/(c) recorded as bundle-bookkeeping and overclaim defects for the provenance record.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
