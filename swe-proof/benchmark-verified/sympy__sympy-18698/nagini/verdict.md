# P2 adversarial audit — sympy__sympy-18698

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -212,94 +212,39 @@
                                       dedup(ToSeq(mults))[j], len(mults))))))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH skeleton: the report is returned WITHOUT consolidating by
+    # multiplicity -- every contribution is kept as its own entry, so a
+    # multiplicity shared by several factors yields several entries (each carrying
+    # that factor alone) instead of one merged product entry. This mirrors the
+    # pre-fix code, which appends every contribution and returns them unchanged.
+    # It FAILS the postcondition `len(Result()) == len(dedup(mults))` (too many
+    # entries) and the per-group product clause (each kept factor is the lone
+    # contribution, not the product) whenever a multiplicity repeats (G-DIFF).
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
-    dmults = []  # type: List[int]
+    out = []  # type: List[int]
     i = 0
-    while i < len(mults):
+    while i < len(factors):
         # invariants-start
         Invariant(Acc(list_pred(factors), 1 / 2))
         Invariant(Acc(list_pred(mults), 1 / 2))
         Invariant(len(factors) == len(mults))
-        Invariant(0 <= i and i <= len(mults))
-        Invariant(Acc(list_pred(dmults)))
+        Invariant(0 <= i and i <= len(factors))
+        Invariant(Acc(list_pred(out)))
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
-        Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
-        Invariant(MustTerminate(len(mults) - i + 1))
+        Invariant(ToSeq(out) == fs.take(i))
+        # This loop consumes the caller's obligation on the strictly decreasing,
+        # bounded-below measure len(factors) - i: `i` rises by exactly one per
+        # pass and the guard keeps i < len(factors), so the remaining-iteration
+        # bound falls by one and stays >= 1 (`factors` is only read, so
+        # len(factors) is fixed across the loop).
+        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
-        m = mults[i]  # type: int
-        Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
-        Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
-        if not present:
-            dmults = dmults + [m]
+        f = factors[i]  # type: int
+        Assert(fs.take(i + 1) == fs.take(i) + PSeq(f))
+        out = out + [f]
         i = i + 1
-    Assert(ms.take(len(mults)) == ms)
-    Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
-    out = []  # type: List[int]
-    p = 0
-    while p < len(dmults):
-        # invariants-start
-        Invariant(Acc(list_pred(factors), 1 / 2))
-        Invariant(Acc(list_pred(mults), 1 / 2))
-        Invariant(len(factors) == len(mults))
-        Invariant(Acc(list_pred(dmults), 1 / 2))
-        Invariant(fs == ToSeq(factors))
-        Invariant(ms == ToSeq(mults))
-        Invariant(ToSeq(dmults) == dedup(ms))
-        Invariant(0 <= p and p <= len(dmults))
-        Invariant(Acc(list_pred(out)))
-        Invariant(len(out) == p)
-        Invariant(Forall(int, lambda j: (
-            Implies(0 <= j and j < p,
-                    ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
-        Invariant(MustTerminate(len(dmults) - p + 1))
-        # invariants-end
-        kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
-        acc = 1
-        n = 0
-        while n < len(mults):
-            # invariants-start
-            Invariant(Acc(list_pred(factors), 1 / 2))
-            Invariant(Acc(list_pred(mults), 1 / 2))
-            Invariant(len(factors) == len(mults))
-            Invariant(fs == ToSeq(factors))
-            Invariant(ms == ToSeq(mults))
-            Invariant(0 <= n and n <= len(mults))
-            Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
-            Invariant(MustTerminate(len(mults) - n + 1))
-            # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
-                acc = acc * factors[n]
-            n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
-        out = out + [acc]
-        p = p + 1
-    Assert(len(out) == len(dmults))
-    Assert(len(dmults) == len(dedup(ms)))
+    Assert(fs.take(len(factors)) == fs)
     return out
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,17 +254,11 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
+        seen = False
         n = 0
         while n < len(mults):
             # invariants-start
@@ -283,20 +268,12 @@
             Invariant(fs == ToSeq(factors))
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
-            Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
-                acc = acc * factors[n]
+            if mults[n] == kk and not seen:
+                acc = factors[n]
+                seen = True
             n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
         out = out + [acc]
         p = p + 1
     Assert(len(out) == len(dmults))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +254,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
         while n < len(mults):
@@ -284,18 +268,8 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
-            Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
-                acc = acc * factors[n]
-            n = n + 1
+            acc = acc
         Assert(acc == prod_k(fs, ms, kk, len(mults)))
         out = out + [acc]
         p = p + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +254,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
         while n < len(mults):
@@ -284,12 +268,6 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
             Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
@@ -301,5 +279,7 @@
         p = p + 1
     Assert(len(out) == len(dmults))
     Assert(len(dmults) == len(dedup(ms)))
+    if len(mults) > 2:
+        raise ValueError("too many contributions")
     return out
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,40 +254,44 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
-        while n < len(mults):
-            # invariants-start
-            Invariant(Acc(list_pred(factors), 1 / 2))
-            Invariant(Acc(list_pred(mults), 1 / 2))
-            Invariant(len(factors) == len(mults))
-            Invariant(fs == ToSeq(factors))
-            Invariant(ms == ToSeq(mults))
-            Invariant(0 <= n and n <= len(mults))
-            Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
-            Invariant(MustTerminate(len(mults) - n + 1))
-            # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
-                acc = acc * factors[n]
-            n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
+        if len(dmults) == len(mults):
+            while n < len(mults):
+                # invariants-start
+                Invariant(Acc(list_pred(factors), 1 / 2))
+                Invariant(Acc(list_pred(mults), 1 / 2))
+                Invariant(len(factors) == len(mults))
+                Invariant(fs == ToSeq(factors))
+                Invariant(ms == ToSeq(mults))
+                Invariant(0 <= n and n <= len(mults))
+                Invariant(acc == prod_k(fs, ms, kk, n))
+                Invariant(MustTerminate(len(mults) - n + 1))
+                # invariants-end
+                Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
+                if mults[n] == kk:
+                    acc = acc * factors[n]
+                n = n + 1
+            Assert(acc == prod_k(fs, ms, kk, len(mults)))
+        else:
+            seen2 = False
+            while n < len(mults):
+                # invariants-start
+                Invariant(Acc(list_pred(factors), 1 / 2))
+                Invariant(Acc(list_pred(mults), 1 / 2))
+                Invariant(len(factors) == len(mults))
+                Invariant(fs == ToSeq(factors))
+                Invariant(ms == ToSeq(mults))
+                Invariant(0 <= n and n <= len(mults))
+                Invariant(MustTerminate(len(mults) - n + 1))
+                # invariants-end
+                if mults[n] == kk and not seen2:
+                    acc = factors[n]
+                    seen2 = True
+                n = n + 1
         out = out + [acc]
         p = p + 1
     Assert(len(out) == len(dmults))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,10 +214,9 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
-    while i < len(mults):
+    while i < len(mults) - 1:
         # invariants-start
         Invariant(Acc(list_pred(factors), 1 / 2))
         Invariant(Acc(list_pred(mults), 1 / 2))
@@ -227,25 +226,15 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
-    Assert(ms.take(len(mults)) == ms)
-    Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +252,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
         while n < len(mults):
@@ -284,12 +266,6 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
             Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,40 +254,11 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
-        acc = 1
-        n = 0
-        while n < len(mults):
-            # invariants-start
-            Invariant(Acc(list_pred(factors), 1 / 2))
-            Invariant(Acc(list_pred(mults), 1 / 2))
-            Invariant(len(factors) == len(mults))
-            Invariant(fs == ToSeq(factors))
-            Invariant(ms == ToSeq(mults))
-            Invariant(0 <= n and n <= len(mults))
-            Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
-            Invariant(MustTerminate(len(mults) - n + 1))
-            # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
-                acc = acc * factors[n]
-            n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
+        Assert(len(mults) >= 0)
+        acc = prod_k(fs, ms, kk + 1, len(mults))
         out = out + [acc]
         p = p + 1
     Assert(len(out) == len(dmults))
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +254,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
         while n < len(mults):
@@ -284,16 +268,10 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
             Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
+            if mults[n] == kk and factors[n] != 1:
                 acc = acc * factors[n]
             n = n + 1
         Assert(acc == prod_k(fs, ms, kk, len(mults)))
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +254,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
         while n < len(mults):
@@ -283,20 +267,11 @@
             Invariant(fs == ToSeq(factors))
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
-            Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
-            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
-            if mults[n] == kk:
+            if factors[n] == kk:
                 acc = acc * factors[n]
             n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
         out = out + [acc]
         p = p + 1
     Assert(len(out) == len(dmults))
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,16 +254,9 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
-        kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
+        kk = dmults[len(dmults) - 1 - p]  # type: int
         acc = 1
         n = 0
         while n < len(mults):
@@ -284,12 +268,6 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
             Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -214,7 +214,6 @@
     # impl-start
     ms = ToSeq(mults)  # type: PSeq[int]
     fs = ToSeq(factors)  # type: PSeq[int]
-    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
     dmults = []  # type: List[int]
     i = 0
     while i < len(mults):
@@ -227,25 +226,17 @@
         Invariant(fs == ToSeq(factors))
         Invariant(ms == ToSeq(mults))
         Invariant(ToSeq(dmults) == dedup(ms.take(i)))
-        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
-        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
-        # + 1 covers the last pass, which has 0 iterations left). `mults` is
-        # only read here, so len(mults) is fixed across the loop.
         Invariant(MustTerminate(len(mults) - i + 1))
         # invariants-end
         m = mults[i]  # type: int
         Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
         Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
-        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
+        present = occurs_in(dmults, m)
         if not present:
             dmults = dmults + [m]
         i = i + 1
     Assert(ms.take(len(mults)) == ms)
     Assert(ToSeq(dmults) == dedup(ms))
-
-    # Phase 2: the merged factor of each reported multiplicity is the product of
-    # exactly the contributions of that multiplicity (mirrors the gold's
-    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
     out = []  # type: List[int]
     p = 0
     while p < len(dmults):
@@ -263,19 +254,12 @@
         Invariant(Forall(int, lambda j: (
             Implies(0 <= j and j < p,
                     ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
-        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
-        # exactly one per pass and the guard keeps p < len(dmults), so
-        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
-        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
-        # counter `n`, which is reset to 0 on every outer pass and so does not
-        # descend across passes.
         Invariant(MustTerminate(len(dmults) - p + 1))
         # invariants-end
         kk = dmults[p]  # type: int
-        # inner product over exactly the group of multiplicity kk
         acc = 1
         n = 0
-        while n < len(mults):
+        while n < p + 1 and n < len(mults):
             # invariants-start
             Invariant(Acc(list_pred(factors), 1 / 2))
             Invariant(Acc(list_pred(mults), 1 / 2))
@@ -284,19 +268,12 @@
             Invariant(ms == ToSeq(mults))
             Invariant(0 <= n and n <= len(mults))
             Invariant(acc == prod_k(fs, ms, kk, n))
-            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
-            # to 0 just before this loop and rises by exactly one per pass, and
-            # the guard keeps n < len(mults), so len(mults) - n strictly falls
-            # and stays >= 1. The bound is the contribution count, which does not
-            # depend on the outer counter `p` (every group is scanned over the
-            # whole contribution sequence), so nothing about `p` is needed here.
             Invariant(MustTerminate(len(mults) - n + 1))
             # invariants-end
             Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
             if mults[n] == kk:
                 acc = acc * factors[n]
             n = n + 1
-        Assert(acc == prod_k(fs, ms, kk, len(mults)))
         out = out + [acc]
         p = p + 1
     Assert(len(out) == len(dmults))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-18698.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A square-free factorisation is reported as a collection of (factor,
  multiplicity) contributions. The report must be CONSOLIDATED by multiplicity:
  a multiplicity may appear at most once in the whole report, and the single
  factor recorded for a multiplicity is the product of every contributing factor
  that carries that multiplicity. So whenever several factors share one
  multiplicity they are merged into one product entry; a multiplicity that
  occurs once is left as it is.

  Concretely, given the raw collection of (factor, multiplicity) contributions
  (carried as two parallel sequences ``factors`` / ``mults`` of equal length),
  the reported multiplicities are exactly the DISTINCT multiplicities occurring
  among the contributions, each kept once (at its first occurrence). The factor
  recorded against the j-th reported multiplicity is the PRODUCT, over every
  contribution whose multiplicity equals that reported multiplicity, of the
  contributing factors -- so several factors sharing a multiplicity collapse to
  one product entry, while a multiplicity that occurs once keeps its single
  factor unchanged.

Modelling choices (Nagini fragment):
  * Each contribution is modelled as a multiplicity (an `int`) paired with a
    factor token (an `int`), carried as two parallel `List[int]` (``factors`` /
    ``mults``) of equal length and specified over `PSeq[int]` via ``ToSeq``.
    mapping.md gives the bijection token <-> factor expression.
  * The merged factor of a group is the PRODUCT of the group. Factor expressions
    form a commutative/associative monoid under multiplication; integer
    multiplication of the distinct factor tokens is a faithful model of that
    monoid (the consolidation depends only on WHICH factors are multiplied for a
    given multiplicity, never on the internal spelling of an expression --
    mapping.md). The product is therefore modelled DEEPLY: ``prod_k`` is the
    spelled-out product fold over exactly the contributions of a given
    multiplicity, and the verified construction proves the recorded factor equals
    that fold. The product over a group is thereby pinned exactly by the inputs.
  * The reported multiplicities are likewise modelled DEEPLY: ``dedup`` is the
    distinct-keeping fold over the multiplicity sequence (keeping each
    multiplicity at its first occurrence). The order in which the distinct
    multiplicities are listed is canonicalised here (first occurrence); it is
    unobservable because the report is sorted downstream (refinement.md), so this
    faithfully refines an unordered distinct collection.

Consolidating a finite collection of contributions is bounded work that must
actually deliver the report, so both operations carry a total-correctness
obligation (MustTerminate in the pre-conditions region, discharged by a per-loop
measure at the end of each loop's invariants region): without it an
implementation that never reaches its return would satisfy every postcondition
vacuously while never producing a merged factor.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. Both dimensions of the consolidation are modelled deeply:
# the reported multiplicities (keeping each distinct multiplicity once) by the
# `dedup` fold, and the merged factor of a group by the `prod_k` product fold --
# each discharged by the verified construction loops, not by a @ContractOnly
# Ensures. The only library fact relied on is that the factor expressions form a
# commutative/associative monoid under multiplication (so integer multiplication
# of the distinct factor tokens faithfully models the per-group product); that
# monoid correspondence is validated out-of-band by axiom_check.py (G-AX) and is
# NOT consumed as an axiom.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty multiplicity sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def occurs(s: PSeq[int], k: int) -> bool:
    """Whether the value ``k`` occurs in ``s``. Front-recursive so a single
    unfold is available per step (value-based membership)."""
    if len(s) == 0:
        return False
    if s[0] == k:
        return True
    return occurs(s.drop(1), k)

@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The distinct values of ``s`` in order of FIRST occurrence: each value is
    kept once. Defined by recursion on the final element so it pairs with a
    forward-building loop -- the prefix is deduplicated, and the last value is
    appended only if it has not already appeared."""
    if len(s) == 0:
        return empty_seq()
    if occurs(dedup(s.take(len(s) - 1)), s[len(s) - 1]):
        return dedup(s.take(len(s) - 1))
    return dedup(s.take(len(s) - 1)) + PSeq(s[len(s) - 1])

@Pure
def prod_k(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> int:
    """The product of exactly the factors whose multiplicity is ``k``, taken over
    the first ``n`` contributions (axes ``0 <= i < n``): the merged factor of the
    multiplicity-``k`` group. A contribution enters the product iff its
    multiplicity equals ``k``; the empty product is 1. Prefix-recursive (extends
    by one contribution per step) so an accumulation loop's invariant tracks
    ``acc == prod_k(facs, mlts, k, i)``. Defensive on bounds: a contribution
    enters the product only when both parallel sequences carry an axis ``n-1``,
    so the fold is total over any ``n >= 0`` (out-of-range axes contribute the
    empty product 1)."""
    Requires(n >= 0)
    if n == 0:
        return 1
    if n - 1 < len(mlts) and n - 1 < len(facs) and mlts[n - 1] == k:
        return prod_k(facs, mlts, k, n - 1) * facs[n - 1]
    return prod_k(facs, mlts, k, n - 1)

@Pure
def lemma_prod_unfold(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> bool:
    """The prefix-recursion equation of ``prod_k``, exposed for callers (its body
    unfolded once): the product over the first ``n`` contributions multiplies the
    product over the first ``n-1`` by ``facs[n-1]`` exactly when the ``n-1``-th
    contribution has multiplicity ``k`` and is within both sequences."""
    Requires(0 < n and n <= len(mlts) and n <= len(facs))
    Ensures(Result())
    Ensures(prod_k(facs, mlts, k, n) ==
            (prod_k(facs, mlts, k, n - 1) * facs[n - 1] if mlts[n - 1] == k
             else prod_k(facs, mlts, k, n - 1)))
    return True
# pure-end

def occurs_in(xs: List[int], k: int) -> bool:
    """Whether the value ``k`` occurs in the list ``xs`` (== ``occurs`` over its
    sequence). A read-only membership scan."""
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # TERMINATION: the membership answer must actually be DELIVERED -- a scan
    # that never reaches its return satisfies the Ensures vacuously. LEVEL 2 is
    # the base level for a method that owns a loop and calls nothing obligated
    # of its own (it reads `xs` and builds no list), leaving room below it.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Result() == occurs(ToSeq(xs), k))
    # post-conditions-end
    # impl-start
    n = len(xs)
    found = False
    j = n
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(0 <= j and j <= n and n == len(xs))
        Invariant(found == occurs(ToSeq(xs).drop(j), k))
        # This down-counting scan consumes the caller's obligation on the
        # strictly decreasing, bounded-below measure `j`: `j` falls by exactly
        # one per pass and the guard keeps j > 0, so the remaining-iteration
        # bound j + 1 falls by one and stays >= 1 (the + 1 matters -- the last
        # pass has 0 iterations left and MustTerminate(0) is unsatisfiable).
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(xs).drop(j - 1) == PSeq(ToSeq(xs)[j - 1]) + ToSeq(xs).drop(j))
        if xs[j - 1] == k:
            found = True
        j = j - 1
    Assert(ToSeq(xs).drop(0) == ToSeq(xs))
    return found
    # impl-end

def consolidate_by_multiplicity(factors: List[int],
                                mults: List[int]) -> List[int]:
    """Consolidate the contributions (parallel ``factors`` / ``mults``) into the
    list of merged factors of the report. The report carries one entry per
    distinct multiplicity that occurs among the contributions (kept once, at its
    first occurrence); the merged factor recorded for the j-th reported
    multiplicity is the product of exactly the contributions whose multiplicity
    equals that reported multiplicity. Returns those merged factors, in the order
    the distinct multiplicities first occur."""
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Acc(list_pred(mults), 1 / 2))
    Requires(len(factors) == len(mults))
    # TERMINATION: the consolidated report must actually be DELIVERED -- an
    # implementation that never reaches its return satisfies every Ensures
    # vacuously. The LEVEL 3 strictly exceeds the level 2 of the obligated
    # membership scan `occurs_in`, which the consolidation may invoke, and still
    # leaves room below for the list-building calls; at level 2 Nagini reports
    # `Obligation leak check failed. Callee occurs_in might not take all
    # unsatisfied obligations from the caller.`
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(mults), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One merged factor per distinct contribution multiplicity.
    Ensures(len(Result()) == len(dedup(ToSeq(mults))))
    # The j-th merged factor is the product of EXACTLY the contributions whose
    # multiplicity is the j-th distinct multiplicity -- the deep per-group product
    # fold over the whole contribution sequence. Pins the merged factor value
    # (not just which multiplicities are reported) to the input group product.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(Result()),
                Result()[j] == prod_k(ToSeq(factors), ToSeq(mults),
                                      dedup(ToSeq(mults))[j], len(mults))))))
    # post-conditions-end
    # impl-start
    ms = ToSeq(mults)  # type: PSeq[int]
    fs = ToSeq(factors)  # type: PSeq[int]
    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
    dmults = []  # type: List[int]
    i = 0
    while i < len(mults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(0 <= i and i <= len(mults))
        Invariant(Acc(list_pred(dmults)))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms.take(i)))
        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
        # + 1 covers the last pass, which has 0 iterations left). `mults` is
        # only read here, so len(mults) is fixed across the loop.
        Invariant(MustTerminate(len(mults) - i + 1))
        # invariants-end
        m = mults[i]  # type: int
        Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
        Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
        if not present:
            dmults = dmults + [m]
        i = i + 1
    Assert(ms.take(len(mults)) == ms)
    Assert(ToSeq(dmults) == dedup(ms))

    # Phase 2: the merged factor of each reported multiplicity is the product of
    # exactly the contributions of that multiplicity (mirrors the gold's
    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
    out = []  # type: List[int]
    p = 0
    while p < len(dmults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(Acc(list_pred(dmults), 1 / 2))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms))
        Invariant(0 <= p and p <= len(dmults))
        Invariant(Acc(list_pred(out)))
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < p,
                    ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
        # exactly one per pass and the guard keeps p < len(dmults), so
        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
        # counter `n`, which is reset to 0 on every outer pass and so does not
        # descend across passes.
        Invariant(MustTerminate(len(dmults) - p + 1))
        # invariants-end
        kk = dmults[p]  # type: int
        # inner product over exactly the group of multiplicity kk
        acc = 1
        n = 0
        while n < len(mults):
            # invariants-start
            Invariant(Acc(list_pred(factors), 1 / 2))
            Invariant(Acc(list_pred(mults), 1 / 2))
            Invariant(len(factors) == len(mults))
            Invariant(fs == ToSeq(factors))
            Invariant(ms == ToSeq(mults))
            Invariant(0 <= n and n <= len(mults))
            Invariant(acc == prod_k(fs, ms, kk, n))
            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
            # to 0 just before this loop and rises by exactly one per pass, and
            # the guard keeps n < len(mults), so len(mults) - n strictly falls
            # and stays >= 1. The bound is the contribution count, which does not
            # depend on the outer counter `p` (every group is scanned over the
            # whole contribution sequence), so nothing about `p` is needed here.
            Invariant(MustTerminate(len(mults) - n + 1))
            # invariants-end
            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
            if mults[n] == kk:
                acc = acc * factors[n]
            n = n + 1
        Assert(acc == prod_k(fs, ms, kk, len(mults)))
        out = out + [acc]
        p = p + 1
    Assert(len(out) == len(dmults))
    Assert(len(dmults) == len(dedup(ms)))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-18698/nagini. VERDICT: SOUND. 11 same-spec attacks + positive control, 12 Nagini runs, 1 official run_resolve executed. A-legs audited against the real repo source at base_commit 3dff1b98a.

**TOOLING:** root swe-proof, SBU_BENCHMARK_DIR=benchmark-verified, python=python. Attacks were built by a splicer (build.py) that copies model.py and replaces ONLY the 2nd impl region (lines 214-305, consolidate_by_multiplicity); axioms/@Pure/Requires/Ensures byte-identical. All 11 + control confirmed `same-spec` exit 0 (SAME).

**POSITIVE CONTROL:** positive_control.py (unmodified model.py) -> `adversary verify` VERIFIED in 26.9s (exit 0). So the spec is satisfiable and the battery's rejections are real.

SPEC SHAPE (why value-attacks are cheap to reject): the postcondition is FULLY FUNCTIONAL -- it pins both output dimensions to a unique function of the inputs: (i) len(Result()) == len(dedup(ToSeq(mults))), (ii) Forall j: Result()[j] == prod_k(ToSeq(factors), ToSeq(mults), dedup(ToSeq(mults))[j], len(mults)). dedup and prod_k are DEEP folds in the pure region (no @ContractOnly anywhere), discharged by the phase-1/phase-2 loops via lemma_prod_unfold + the acc==prod_k invariant. So the prior pass's value-attacks were structurally bound to fail; I deliberately concentrated the NEW attacks on VACUITY (bypassing Ensures rather than violating it), CROSS-DIMENSION association, and the A-reference monoid gap.

ATTACKS (each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-18698 <path>`; all same-spec=SAME; run concurrently in background batches of 3, each spawning JVM+Z3):
- atk_1.py PREPATCH BUG (= model_prepatch.py impl verbatim: un-consolidated, copies every contribution so len(out)==len(mults)) -> exit 2 REJECTED. PREPATCH REPRODUCED: fails both the len clause and the prod_k clause exactly when a multiplicity repeats -- precisely the reported bug (sqf_list(x*(x+y)) yielding (x,1),(x+y,1) instead of (`x**2`+`x*y`,1)).
- atk_2.py KEEP-FIRST (seen-flag: record the FIRST factor of the group, not the product) -> exit 2 REJECTED. This is the counterexample refinement.md §A/§D explicitly claims fails; claim CONFIRMED independently.
- atk_3.py VACUITY/DIVERGENCE (inner loop body `acc = acc`, n never advances; inner MustTerminate measure removed) -> exit 2 REJECTED. Confirms the method-level MustTerminate(3) + per-loop measures genuinely close the non-termination hole the docstring claims; a diverging impl cannot satisfy the postconditions vacuously.
- atk_4.py VACUITY/EXCEPTION EXIT (compute the fully CORRECT out, then `raise ValueError` when len(mults) > 2) -> exit 2 REJECTED. Nagini rejects the uncaught-exception escape, so a partial-delivery impl cannot pass.
- atk_5.py PARTIAL-DOMAIN (correct product when no multiplicity repeats i.e. len(dmults)==len(mults); keep-first on the repeating branch -- wrong on exactly the F2P inputs) -> exit 2 REJECTED. The strongest weakness shape for this bug (right on the easy domain, wrong where the bug lives) is closed.
- atk_6.py BOUNDARY (phase-1 `while i < len(mults) - 1`, dropping the last contribution from the dedup) -> exit 2 REJECTED.
- atk_7.py UNGROUNDED-ORACLE ECHO (echo the deep model but off-by-one on the key: `acc = prod_k(fs, ms, kk + 1, len(mults))`) -> exit 2 REJECTED. An echo of the spec function keyed wrongly does not slip through.
- atk_8.py A-REFERENCE MONOID GAP: inner guard `if mults[n] == kk and factors[n] != 1` -- skip factor tokens equal to 1 -> exit 0 **CANDIDATE-COUNTEREXAMPLE** (shares spec AND verifies, 34.2s). SEE THE RESOLVE LEG BELOW.
- atk_9.py CONTROL-FLOW-EFFECT / cross-dimension guard (`if factors[n] == kk`, testing the factor token against the multiplicity) -> exit 2 REJECTED.
- atk_10.py REVERSE PAIRING (correct multiset of group products, but slot p records the product of group dmults[len-1-p], i.e. the key<->product ASSOCIATION is scrambled while the multiset is right) -> exit 2 REJECTED. This pins refinement.md A4: the association of each reported multiplicity to ITS product is in the verified spec, not just the collection of products.
- atk_11.py OUTER-DEPENDENT BOUNDARY (inner product over only the first p+1 contributions: a per-group PREFIX product) -> exit 2 REJECTED. Confirms prod_k's n==len(mults) argument is pinned; a group product cannot be truncated as a function of the outer counter.

MANDATORY RESOLVE LEG (the only CANDIDATE, atk_8): materialized its faithful refined patch at patch_atk_8.diff -- the gold patch with the consolidation comprehension changed to the impl's own semantics, `reduce(mul, (f for f, _ in factors if _ == k and f != 1), 1)` (the `if f != 1` filter is the exact refinement of `factors[n] != 1`; the initializer 1 is required because reduce over a possibly-empty filtered group needs the identity, and the hunk line counts are preserved). Executed via swebench_unified.harness.run_resolve('sympy__sympy-18698', patch, timeout=3600) [driver do_resolve.py, log resolve_atk_8.log]. OBSERVED RESULT: resolved=True, completed=True, note='resolved', attempts=1, flaky=False, patch_successfully_applied=True; FAIL_TO_PASS 1/1 success 0 failures, PASS_TO_PASS 147/147 success 0 failures, PASS_TO_FAIL 0, FAIL_TO_FAIL 0. So the CANDIDATE **RESOLVES** and is therefore NOT a counterexample -- the BROKEN trigger (a verifying impl whose faithful patch does NOT resolve) did not fire.

WHY atk_8 verifying is CORRECT behaviour, not a spec hole: 1 is the IDENTITY of the monoid the merged factor lives in, in both the model and the repo. In the model, skipping a token equal to 1 is provably product-preserving (prod_k(...,n+1) == prod_k(...,n) * 1 == prod_k(...,n)), so Z3 discharges acc == prod_k(...) legitimately -- the spec admitted a BEHAVIOURALLY EQUIVALENT variant, not a wrong one. The refinement carries that identity-skip faithfully into `Mul` (where dropping a factor of S.One likewise changes nothing, Mul flattening the identity away), and the harness confirms it empirically: 148/148 tests. This is exactly the situation the A-reference is supposed to license: the token monoid and the Mul monoid agree on the identity, so verify => correct HELD on the one impl that the spec let through. An equivalence-admitting spec is sound; only a WRONG-behaviour-admitting spec is broken.

A-LEG / CORRESPONDENCE AUDIT (refinement.md, checked against `git show 3dff1b98a:sympy/polys/polytools.py`):
- A1 (R): the local `factors` list of (expr, k) pairs <-> two parallel List[int] (token, multiplicity), equal length enforced by Requires. Sound type refinement; the consolidation depends only on which factors group and on their product, both preserved.
- A2 (R): dedup(ToSeq(mults)) <-> `for k in set(i for _, i in factors)`. The first-occurrence canonicalisation is justified as unobservable via the downstream `_sorted_factors(fp, method)`; I CONFIRMED that call exists at polytools.py:5998 in `_generic_factor_list` (and that the sqf key is (exp, len(rep), len(gens), rep)), so the ordering claim is real. Note the spec is in fact STRICTER than the doc needs -- the postcondition pins first-occurrence order (atk_10's reverse pairing is rejected). Stricter-than-documented is not a leak.
- A3 (R + A-reference): prod_k is a deep fold and is CONSUMED by the verified postcondition (Result()[j] == prod_k(...)), so the F2P-graded merged-factor VALUE is inside the proof, not delegated. The ONLY delegated fact is the monoid faithfulness of integer `*` for `reduce(operator.mul, group)`. I RE-RAN axiom_check.py: exit 0, 'G-AX OK: consolidation (dedup-by-multiplicity) + A-reference (merged factor == reduce(mul, group)) sound on 10 boundary mult lists + 7 boundary factor lists + 20000 fuzz cases'. It re-executes the patch's EXACT comprehension against the real operator.mul/functools.reduce. A-reference correspondence to the real callee HOLDS. atk_8's resolve=True is independent empirical corroboration of exactly this monoid leg (identity agreement) through the real harness.
- A4 (R): `return out` <-> the rebound `factors` list of (product_k, k) pairs returned via `return coeff, factors`; coeff untouched by the block (verified: the inserted hunk sits immediately before `return coeff, factors` and rebinds only `factors`). Association pinned (atk_10).
- §B refactor hunk (removal of the dead `if arg.is_Mul: args.extend(arg.args); continue` and the `if arg.is_Pow:` -> `elif arg.is_Pow:` join): I read the base-commit source and the pre-patch `if arg.is_Number:... continue` chain -- since the Number branch `continue`s, converting the following `if` to `elif` is semantics-preserving, and `Mul.make_args` already flattens nested Muls so the removed branch was unreachable for elements of `args`. Behaviourally inert, carried verbatim in patch.diff, correctly NOT modeled -- justified omission, NOT a kind-3 step.
- §C: NO kind-3 (unexpressible-changed-op) legs. Every leg is R / A-reference / I. There is no A-consumed leg and no @ContractOnly declaration anywhere in the bundle (axioms region is a comment only; meta.json axioms == []). The genuinely-changed operation -- collapsing same-multiplicity factors into one product entry -- is modeled deeply in BOTH dimensions and consumed by the proof.

**CONCLUSION:** 12 Nagini runs completed (1 control VERIFIED, 11 same-spec attacks: 10 REJECTED, 1 CANDIDATE) plus 1 official run_resolve on the sole CANDIDATE's materialized faithful patch, which RESOLVED (148/148). The prepatch bug was reproduced and rejected. Vacuity (divergence + exception exit), partial-domain, boundary (both input-indexed and outer-counter-indexed), cross-dimension, association-scrambling, and ungrounded-oracle-echo shapes are all closed. The one impl the spec admits is behaviourally equivalent to the gold and resolves under the official harness. No evidence of verify=>correct failing. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-18698.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A square-free factorisation is reported as a collection of (factor,
  multiplicity) contributions. The report must be CONSOLIDATED by multiplicity:
  a multiplicity may appear at most once in the whole report, and the single
  factor recorded for a multiplicity is the product of every contributing factor
  that carries that multiplicity. So whenever several factors share one
  multiplicity they are merged into one product entry; a multiplicity that
  occurs once is left as it is.

  Concretely, given the raw collection of (factor, multiplicity) contributions
  (carried as two parallel sequences ``factors`` / ``mults`` of equal length),
  the reported multiplicities are exactly the DISTINCT multiplicities occurring
  among the contributions, each kept once (at its first occurrence). The factor
  recorded against the j-th reported multiplicity is the PRODUCT, over every
  contribution whose multiplicity equals that reported multiplicity, of the
  contributing factors -- so several factors sharing a multiplicity collapse to
  one product entry, while a multiplicity that occurs once keeps its single
  factor unchanged.

Modelling choices (Nagini fragment):
  * Each contribution is modelled as a multiplicity (an `int`) paired with a
    factor token (an `int`), carried as two parallel `List[int]` (``factors`` /
    ``mults``) of equal length and specified over `PSeq[int]` via ``ToSeq``.
    mapping.md gives the bijection token <-> factor expression.
  * The merged factor of a group is the PRODUCT of the group. Factor expressions
    form a commutative/associative monoid under multiplication; integer
    multiplication of the distinct factor tokens is a faithful model of that
    monoid (the consolidation depends only on WHICH factors are multiplied for a
    given multiplicity, never on the internal spelling of an expression --
    mapping.md). The product is therefore modelled DEEPLY: ``prod_k`` is the
    spelled-out product fold over exactly the contributions of a given
    multiplicity, and the verified construction proves the recorded factor equals
    that fold. The product over a group is thereby pinned exactly by the inputs.
  * The reported multiplicities are likewise modelled DEEPLY: ``dedup`` is the
    distinct-keeping fold over the multiplicity sequence (keeping each
    multiplicity at its first occurrence). The order in which the distinct
    multiplicities are listed is canonicalised here (first occurrence); it is
    unobservable because the report is sorted downstream (refinement.md), so this
    faithfully refines an unordered distinct collection.

Consolidating a finite collection of contributions is bounded work that must
actually deliver the report, so both operations carry a total-correctness
obligation (MustTerminate in the pre-conditions region, discharged by a per-loop
measure at the end of each loop's invariants region): without it an
implementation that never reaches its return would satisfy every postcondition
vacuously while never producing a merged factor.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. Both dimensions of the consolidation are modelled deeply:
# the reported multiplicities (keeping each distinct multiplicity once) by the
# `dedup` fold, and the merged factor of a group by the `prod_k` product fold --
# each discharged by the verified construction loops, not by a @ContractOnly
# Ensures. The only library fact relied on is that the factor expressions form a
# commutative/associative monoid under multiplication (so integer multiplication
# of the distinct factor tokens faithfully models the per-group product); that
# monoid correspondence is validated out-of-band by axiom_check.py (G-AX) and is
# NOT consumed as an axiom.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty multiplicity sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def occurs(s: PSeq[int], k: int) -> bool:
    """Whether the value ``k`` occurs in ``s``. Front-recursive so a single
    unfold is available per step (value-based membership)."""
    if len(s) == 0:
        return False
    if s[0] == k:
        return True
    return occurs(s.drop(1), k)

@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The distinct values of ``s`` in order of FIRST occurrence: each value is
    kept once. Defined by recursion on the final element so it pairs with a
    forward-building loop -- the prefix is deduplicated, and the last value is
    appended only if it has not already appeared."""
    if len(s) == 0:
        return empty_seq()
    if occurs(dedup(s.take(len(s) - 1)), s[len(s) - 1]):
        return dedup(s.take(len(s) - 1))
    return dedup(s.take(len(s) - 1)) + PSeq(s[len(s) - 1])

@Pure
def prod_k(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> int:
    """The product of exactly the factors whose multiplicity is ``k``, taken over
    the first ``n`` contributions (axes ``0 <= i < n``): the merged factor of the
    multiplicity-``k`` group. A contribution enters the product iff its
    multiplicity equals ``k``; the empty product is 1. Prefix-recursive (extends
    by one contribution per step) so an accumulation loop's invariant tracks
    ``acc == prod_k(facs, mlts, k, i)``. Defensive on bounds: a contribution
    enters the product only when both parallel sequences carry an axis ``n-1``,
    so the fold is total over any ``n >= 0`` (out-of-range axes contribute the
    empty product 1)."""
    Requires(n >= 0)
    if n == 0:
        return 1
    if n - 1 < len(mlts) and n - 1 < len(facs) and mlts[n - 1] == k:
        return prod_k(facs, mlts, k, n - 1) * facs[n - 1]
    return prod_k(facs, mlts, k, n - 1)

@Pure
def lemma_prod_unfold(facs: PSeq[int], mlts: PSeq[int], k: int, n: int) -> bool:
    """The prefix-recursion equation of ``prod_k``, exposed for callers (its body
    unfolded once): the product over the first ``n`` contributions multiplies the
    product over the first ``n-1`` by ``facs[n-1]`` exactly when the ``n-1``-th
    contribution has multiplicity ``k`` and is within both sequences."""
    Requires(0 < n and n <= len(mlts) and n <= len(facs))
    Ensures(Result())
    Ensures(prod_k(facs, mlts, k, n) ==
            (prod_k(facs, mlts, k, n - 1) * facs[n - 1] if mlts[n - 1] == k
             else prod_k(facs, mlts, k, n - 1)))
    return True
# pure-end

def occurs_in(xs: List[int], k: int) -> bool:
    """Whether the value ``k`` occurs in the list ``xs`` (== ``occurs`` over its
    sequence). A read-only membership scan."""
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # TERMINATION: the membership answer must actually be DELIVERED -- a scan
    # that never reaches its return satisfies the Ensures vacuously. LEVEL 2 is
    # the base level for a method that owns a loop and calls nothing obligated
    # of its own (it reads `xs` and builds no list), leaving room below it.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Result() == occurs(ToSeq(xs), k))
    # post-conditions-end
    # impl-start
    n = len(xs)
    found = False
    j = n
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(0 <= j and j <= n and n == len(xs))
        Invariant(found == occurs(ToSeq(xs).drop(j), k))
        # This down-counting scan consumes the caller's obligation on the
        # strictly decreasing, bounded-below measure `j`: `j` falls by exactly
        # one per pass and the guard keeps j > 0, so the remaining-iteration
        # bound j + 1 falls by one and stays >= 1 (the + 1 matters -- the last
        # pass has 0 iterations left and MustTerminate(0) is unsatisfiable).
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(xs).drop(j - 1) == PSeq(ToSeq(xs)[j - 1]) + ToSeq(xs).drop(j))
        if xs[j - 1] == k:
            found = True
        j = j - 1
    Assert(ToSeq(xs).drop(0) == ToSeq(xs))
    return found
    # impl-end

def consolidate_by_multiplicity(factors: List[int],
                                mults: List[int]) -> List[int]:
    """Consolidate the contributions (parallel ``factors`` / ``mults``) into the
    list of merged factors of the report. The report carries one entry per
    distinct multiplicity that occurs among the contributions (kept once, at its
    first occurrence); the merged factor recorded for the j-th reported
    multiplicity is the product of exactly the contributions whose multiplicity
    equals that reported multiplicity. Returns those merged factors, in the order
    the distinct multiplicities first occur."""
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Acc(list_pred(mults), 1 / 2))
    Requires(len(factors) == len(mults))
    # TERMINATION: the consolidated report must actually be DELIVERED -- an
    # implementation that never reaches its return satisfies every Ensures
    # vacuously. The LEVEL 3 strictly exceeds the level 2 of the obligated
    # membership scan `occurs_in`, which the consolidation may invoke, and still
    # leaves room below for the list-building calls; at level 2 Nagini reports
    # `Obligation leak check failed. Callee occurs_in might not take all
    # unsatisfied obligations from the caller.`
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(mults), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One merged factor per distinct contribution multiplicity.
    Ensures(len(Result()) == len(dedup(ToSeq(mults))))
    # The j-th merged factor is the product of EXACTLY the contributions whose
    # multiplicity is the j-th distinct multiplicity -- the deep per-group product
    # fold over the whole contribution sequence. Pins the merged factor value
    # (not just which multiplicities are reported) to the input group product.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(Result()),
                Result()[j] == prod_k(ToSeq(factors), ToSeq(mults),
                                      dedup(ToSeq(mults))[j], len(mults))))))
    # post-conditions-end
    # impl-start
    ms = ToSeq(mults)  # type: PSeq[int]
    fs = ToSeq(factors)  # type: PSeq[int]
    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
    dmults = []  # type: List[int]
    i = 0
    while i < len(mults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(0 <= i and i <= len(mults))
        Invariant(Acc(list_pred(dmults)))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms.take(i)))
        # PHASE-1 measure: `i` rises by exactly one per pass and the guard keeps
        # i < len(mults), so len(mults) - i strictly falls and stays >= 1 (the
        # + 1 covers the last pass, which has 0 iterations left). `mults` is
        # only read here, so len(mults) is fixed across the loop.
        Invariant(MustTerminate(len(mults) - i + 1))
        # invariants-end
        m = mults[i]  # type: int
        Assert(ms.take(i + 1).take(len(ms.take(i + 1)) - 1) == ms.take(i))
        Assert(ms.take(i + 1)[len(ms.take(i + 1)) - 1] == m)
        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
        if not present:
            dmults = dmults + [m]
        i = i + 1
    Assert(ms.take(len(mults)) == ms)
    Assert(ToSeq(dmults) == dedup(ms))

    # Phase 2: the merged factor of each reported multiplicity is the product of
    # exactly the contributions of that multiplicity (mirrors the gold's
    # `reduce(mul, (f for f, _ in factors if _ == k))` inner product per group).
    out = []  # type: List[int]
    p = 0
    while p < len(dmults):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(mults), 1 / 2))
        Invariant(len(factors) == len(mults))
        Invariant(Acc(list_pred(dmults), 1 / 2))
        Invariant(fs == ToSeq(factors))
        Invariant(ms == ToSeq(mults))
        Invariant(ToSeq(dmults) == dedup(ms))
        Invariant(0 <= p and p <= len(dmults))
        Invariant(Acc(list_pred(out)))
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < p,
                    ToSeq(out)[j] == prod_k(fs, ms, ToSeq(dmults)[j], len(mults))))))
        # PHASE-2 OUTER measure, one pass per reported multiplicity: `p` rises by
        # exactly one per pass and the guard keeps p < len(dmults), so
        # len(dmults) - p strictly falls and stays >= 1 (`dmults` is read-only in
        # phase 2, so len(dmults) is fixed). It must NOT mention the inner
        # counter `n`, which is reset to 0 on every outer pass and so does not
        # descend across passes.
        Invariant(MustTerminate(len(dmults) - p + 1))
        # invariants-end
        kk = dmults[p]  # type: int
        # inner product over exactly the group of multiplicity kk
        acc = 1
        n = 0
        while n < len(mults):
            # invariants-start
            Invariant(Acc(list_pred(factors), 1 / 2))
            Invariant(Acc(list_pred(mults), 1 / 2))
            Invariant(len(factors) == len(mults))
            Invariant(fs == ToSeq(factors))
            Invariant(ms == ToSeq(mults))
            Invariant(0 <= n and n <= len(mults))
            Invariant(acc == prod_k(fs, ms, kk, n))
            # PHASE-2 INNER measure, decreasing within ONE outer pass: `n` is set
            # to 0 just before this loop and rises by exactly one per pass, and
            # the guard keeps n < len(mults), so len(mults) - n strictly falls
            # and stays >= 1. The bound is the contribution count, which does not
            # depend on the outer counter `p` (every group is scanned over the
            # whole contribution sequence), so nothing about `p` is needed here.
            Invariant(MustTerminate(len(mults) - n + 1))
            # invariants-end
            Assert(lemma_prod_unfold(fs, ms, kk, n + 1))
            if mults[n] == kk:
                acc = acc * factors[n]
            n = n + 1
        Assert(acc == prod_k(fs, ms, kk, len(mults)))
        out = out + [acc]
        p = p + 1
    Assert(len(out) == len(dmults))
    Assert(len(dmults) == len(dedup(ms)))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-18698/nagini. VERDICT: SOUND. 11 same-spec attacks + positive control, 12 Nagini runs, 1 official run_resolve executed. A-legs audited against the real repo source at base_commit 3dff1b98a.

**TOOLING:** root swe-proof, SBU_BENCHMARK_DIR=benchmark-verified, python=python. Attacks were built by a splicer (build.py) that copies model.py and replaces ONLY the 2nd impl region (lines 214-305, consolidate_by_multiplicity); axioms/@Pure/Requires/Ensures byte-identical. All 11 + control confirmed `same-spec` exit 0 (SAME).

**POSITIVE CONTROL:** positive_control.py (unmodified model.py) -> `adversary verify` VERIFIED in 26.9s (exit 0). So the spec is satisfiable and the battery's rejections are real.

SPEC SHAPE (why value-attacks are cheap to reject): the postcondition is FULLY FUNCTIONAL -- it pins both output dimensions to a unique function of the inputs: (i) len(Result()) == len(dedup(ToSeq(mults))), (ii) Forall j: Result()[j] == prod_k(ToSeq(factors), ToSeq(mults), dedup(ToSeq(mults))[j], len(mults)). dedup and prod_k are DEEP folds in the pure region (no @ContractOnly anywhere), discharged by the phase-1/phase-2 loops via lemma_prod_unfold + the acc==prod_k invariant. So the prior pass's value-attacks were structurally bound to fail; I deliberately concentrated the NEW attacks on VACUITY (bypassing Ensures rather than violating it), CROSS-DIMENSION association, and the A-reference monoid gap.

ATTACKS (each: `python -m swebench_unified.adversary weakness nagini sympy__sympy-18698 <path>`; all same-spec=SAME; run concurrently in background batches of 3, each spawning JVM+Z3):
- atk_1.py PREPATCH BUG (= model_prepatch.py impl verbatim: un-consolidated, copies every contribution so len(out)==len(mults)) -> exit 2 REJECTED. PREPATCH REPRODUCED: fails both the len clause and the prod_k clause exactly when a multiplicity repeats -- precisely the reported bug (sqf_list(x*(x+y)) yielding (x,1),(x+y,1) instead of (`x**2`+`x*y`,1)).
- atk_2.py KEEP-FIRST (seen-flag: record the FIRST factor of the group, not the product) -> exit 2 REJECTED. This is the counterexample refinement.md §A/§D explicitly claims fails; claim CONFIRMED independently.
- atk_3.py VACUITY/DIVERGENCE (inner loop body `acc = acc`, n never advances; inner MustTerminate measure removed) -> exit 2 REJECTED. Confirms the method-level MustTerminate(3) + per-loop measures genuinely close the non-termination hole the docstring claims; a diverging impl cannot satisfy the postconditions vacuously.
- atk_4.py VACUITY/EXCEPTION EXIT (compute the fully CORRECT out, then `raise ValueError` when len(mults) > 2) -> exit 2 REJECTED. Nagini rejects the uncaught-exception escape, so a partial-delivery impl cannot pass.
- atk_5.py PARTIAL-DOMAIN (correct product when no multiplicity repeats i.e. len(dmults)==len(mults); keep-first on the repeating branch -- wrong on exactly the F2P inputs) -> exit 2 REJECTED. The strongest weakness shape for this bug (right on the easy domain, wrong where the bug lives) is closed.
- atk_6.py BOUNDARY (phase-1 `while i < len(mults) - 1`, dropping the last contribution from the dedup) -> exit 2 REJECTED.
- atk_7.py UNGROUNDED-ORACLE ECHO (echo the deep model but off-by-one on the key: `acc = prod_k(fs, ms, kk + 1, len(mults))`) -> exit 2 REJECTED. An echo of the spec function keyed wrongly does not slip through.
- atk_8.py A-REFERENCE MONOID GAP: inner guard `if mults[n] == kk and factors[n] != 1` -- skip factor tokens equal to 1 -> exit 0 **CANDIDATE-COUNTEREXAMPLE** (shares spec AND verifies, 34.2s). SEE THE RESOLVE LEG BELOW.
- atk_9.py CONTROL-FLOW-EFFECT / cross-dimension guard (`if factors[n] == kk`, testing the factor token against the multiplicity) -> exit 2 REJECTED.
- atk_10.py REVERSE PAIRING (correct multiset of group products, but slot p records the product of group dmults[len-1-p], i.e. the key<->product ASSOCIATION is scrambled while the multiset is right) -> exit 2 REJECTED. This pins refinement.md A4: the association of each reported multiplicity to ITS product is in the verified spec, not just the collection of products.
- atk_11.py OUTER-DEPENDENT BOUNDARY (inner product over only the first p+1 contributions: a per-group PREFIX product) -> exit 2 REJECTED. Confirms prod_k's n==len(mults) argument is pinned; a group product cannot be truncated as a function of the outer counter.

MANDATORY RESOLVE LEG (the only CANDIDATE, atk_8): materialized its faithful refined patch at patch_atk_8.diff -- the gold patch with the consolidation comprehension changed to the impl's own semantics, `reduce(mul, (f for f, _ in factors if _ == k and f != 1), 1)` (the `if f != 1` filter is the exact refinement of `factors[n] != 1`; the initializer 1 is required because reduce over a possibly-empty filtered group needs the identity, and the hunk line counts are preserved). Executed via swebench_unified.harness.run_resolve('sympy__sympy-18698', patch, timeout=3600) [driver do_resolve.py, log resolve_atk_8.log]. OBSERVED RESULT: resolved=True, completed=True, note='resolved', attempts=1, flaky=False, patch_successfully_applied=True; FAIL_TO_PASS 1/1 success 0 failures, PASS_TO_PASS 147/147 success 0 failures, PASS_TO_FAIL 0, FAIL_TO_FAIL 0. So the CANDIDATE **RESOLVES** and is therefore NOT a counterexample -- the BROKEN trigger (a verifying impl whose faithful patch does NOT resolve) did not fire.

WHY atk_8 verifying is CORRECT behaviour, not a spec hole: 1 is the IDENTITY of the monoid the merged factor lives in, in both the model and the repo. In the model, skipping a token equal to 1 is provably product-preserving (prod_k(...,n+1) == prod_k(...,n) * 1 == prod_k(...,n)), so Z3 discharges acc == prod_k(...) legitimately -- the spec admitted a BEHAVIOURALLY EQUIVALENT variant, not a wrong one. The refinement carries that identity-skip faithfully into `Mul` (where dropping a factor of S.One likewise changes nothing, Mul flattening the identity away), and the harness confirms it empirically: 148/148 tests. This is exactly the situation the A-reference is supposed to license: the token monoid and the Mul monoid agree on the identity, so verify => correct HELD on the one impl that the spec let through. An equivalence-admitting spec is sound; only a WRONG-behaviour-admitting spec is broken.

A-LEG / CORRESPONDENCE AUDIT (refinement.md, checked against `git show 3dff1b98a:sympy/polys/polytools.py`):
- A1 (R): the local `factors` list of (expr, k) pairs <-> two parallel List[int] (token, multiplicity), equal length enforced by Requires. Sound type refinement; the consolidation depends only on which factors group and on their product, both preserved.
- A2 (R): dedup(ToSeq(mults)) <-> `for k in set(i for _, i in factors)`. The first-occurrence canonicalisation is justified as unobservable via the downstream `_sorted_factors(fp, method)`; I CONFIRMED that call exists at polytools.py:5998 in `_generic_factor_list` (and that the sqf key is (exp, len(rep), len(gens), rep)), so the ordering claim is real. Note the spec is in fact STRICTER than the doc needs -- the postcondition pins first-occurrence order (atk_10's reverse pairing is rejected). Stricter-than-documented is not a leak.
- A3 (R + A-reference): prod_k is a deep fold and is CONSUMED by the verified postcondition (Result()[j] == prod_k(...)), so the F2P-graded merged-factor VALUE is inside the proof, not delegated. The ONLY delegated fact is the monoid faithfulness of integer `*` for `reduce(operator.mul, group)`. I RE-RAN axiom_check.py: exit 0, 'G-AX OK: consolidation (dedup-by-multiplicity) + A-reference (merged factor == reduce(mul, group)) sound on 10 boundary mult lists + 7 boundary factor lists + 20000 fuzz cases'. It re-executes the patch's EXACT comprehension against the real operator.mul/functools.reduce. A-reference correspondence to the real callee HOLDS. atk_8's resolve=True is independent empirical corroboration of exactly this monoid leg (identity agreement) through the real harness.
- A4 (R): `return out` <-> the rebound `factors` list of (product_k, k) pairs returned via `return coeff, factors`; coeff untouched by the block (verified: the inserted hunk sits immediately before `return coeff, factors` and rebinds only `factors`). Association pinned (atk_10).
- §B refactor hunk (removal of the dead `if arg.is_Mul: args.extend(arg.args); continue` and the `if arg.is_Pow:` -> `elif arg.is_Pow:` join): I read the base-commit source and the pre-patch `if arg.is_Number:... continue` chain -- since the Number branch `continue`s, converting the following `if` to `elif` is semantics-preserving, and `Mul.make_args` already flattens nested Muls so the removed branch was unreachable for elements of `args`. Behaviourally inert, carried verbatim in patch.diff, correctly NOT modeled -- justified omission, NOT a kind-3 step.
- §C: NO kind-3 (unexpressible-changed-op) legs. Every leg is R / A-reference / I. There is no A-consumed leg and no @ContractOnly declaration anywhere in the bundle (axioms region is a comment only; meta.json axioms == []). The genuinely-changed operation -- collapsing same-multiplicity factors into one product entry -- is modeled deeply in BOTH dimensions and consumed by the proof.

**CONCLUSION:** 12 Nagini runs completed (1 control VERIFIED, 11 same-spec attacks: 10 REJECTED, 1 CANDIDATE) plus 1 official run_resolve on the sole CANDIDATE's materialized faithful patch, which RESOLVED (148/148). The prepatch bug was reproduced and rejected. Vacuity (divergence + exception exit), partial-domain, boundary (both input-indexed and outer-counter-indexed), cross-dimension, association-scrambling, and ungrounded-oracle-echo shapes are all closed. The one impl the spec admits is behaviourally equivalent to the gold and resolves under the official harness. No evidence of verify=>correct failing. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Spec region confirmed byte-identical: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-18698` on an identity copy of model.py -> exit 0, 'SAME'. Two fresh worktrees at base_commit 3dff1b98a7 from the upstream repository under /tmp: wt = gold patch.diff applied (the reference for the modeled function, per the brief); wt_spec = gold + test_patch + spec-faithful consolidation. patch.diff was taken from the instance dir (the nagini/ subdir has no patch.diff; instance.json['patch'] matches it byte-for-byte).

**METHOD.** I extracted the real post-patch `_symbolic_factor_list` and built a 'raw' variant with only the new `if method == 'sqf'` block removed, so I could feed the SAME raw (expr, k) contribution list to (a) the gold block `[(reduce(mul,(f for f,_ in factors if _==k)), k) for k in set(i for _,i in factors)]` and (b) a direct transcription of the model's spec (`dedup` first-occurrence keep + `prod_k` per-group left product), then compared the results as multisets of srepr'd (factor, multiplicity). This tests the modeled function against the real callee on real repo-reachable inputs, not against a paraphrase.

### What checked out
1. prod_k == reduce(mul, group), exactly. 4000-case randomized fuzz over products of 1-4 distinct bases with integer exponents 1-4 (real polynomial factorizations through the real `_symbolic_factor_list`): 0 divergences. Also 837,931-case exhaustive sweep of the abstract int carrier (n=0..4, mults in {0,1,2,3,-1}, factors in {1,2,3,5,-2,0}): 0 divergences. Group membership (filter _==k) and the fold both match; no factor of k dropped, none of another multiplicity mixed in.
2. len(Result()) == len(dedup(mults)) matches |set(mults)| on every in-domain case. Both F2P inputs reproduce exactly: sqf_list(x*(x+y)) -> merged (`x**2`+`x*y`,1); (`x**2`+1)(x-1)^2(x-2)^3(x-3)^3 -> the two multiplicity-3 factors collapse to `x**2`-5x+6.
3. Order-unobservability (refinement.md §A2 / mapping.md §2), the load-bearing R-refinement claim: I permuted the raw contribution list and pushed each first-occurrence consolidation through the real downstream tail (`_poly_from_expr` + `_sorted_factors`(fp,'sqf') + as_expr) — 1500 real factorizations x all permutations: 0 order leaks. The claim that first-occurrence order is washed out by `_sorted_factors` is confirmed on real data, not just asserted.
4. Per-group product order-independence (the §3.1 Mul monoid A-reference) held on mixed Poly/Expr groups (`x*sin`(x), `x**2*sin`(x)**2, (x+1)*Abs(x), sqrt(2)*x*(x+y), `x*exp`(x), `x*log`(x)): fwd and rev folds agree as expressions in every case, so integer `*` is a sound monoid model here.
5. Empty input: expr=1 and expr=5 give raw=[] -> real block [] and model [] agree. prod_k's 'empty product = 1' branch is defensive and unreachable at the postcondition's call sites (it is only instantiated at k = dedup(ms)[j], which by construction occurs in ms, so every graded group is non-empty) — not a source of divergence or vacuity.
6. Not-too-strong in the other direction either: the postcondition pins BOTH dimensions (count via dedup, value via prod_k), matching what the F2P test grades; that is not over-strength, it is exactly the gold block.

THE ONE ASYMMETRY FOUND, AND WHY IT IS NOT A DEFECT. The model's `occurs`/`dedup` group multiplicities by `==`; the gold groups by `set()`, i.e. hash-then-eq. SymPy violates the eq/hash contract across numeric types: Integer(1) == Float(1.0) is True but their hashes differ, so `set` keeps both while `==` merges them. This is genuinely reachable from the public API (sqf_list(x*(x+1)**1.0) -> gold gives two entries, spec-faithful gives one; I confirmed both by running the two worktrees side by side).

I considered reporting UNFAITHFUL on this and decided against it, on two independent grounds: (a) DOMAIN — mapping.md §2 declares the multiplicity carrier as Python `int` with identity bijection, and for Python ints == and set-identity provably coincide (verified exhaustively), so the divergence is not expressible in the modeled domain; the abstraction is declared up front rather than discovered as a gap. (b) RESOLUTION — the spec-faithful implementation passes the graded suite identically to gold (149 passed / 1 xfailed), so no verifying-but-non-resolving implementation is admitted through this hole. It is a boundary caveat on the int abstraction worth recording, not a spec that is too strong or that drifts from real behavior on any input it claims to cover.

**HYGIENE.** I verified the divergence against the PATCHED worktree (the correct reference), so this is not the patch delta being mislabeled as drift; separately, the pre-patch behavior (every contribution kept separately) is what model_prepatch.py targets and is not the reference for the modeled function. The behaviorally-inert is_Mul/elif refactor hunk is correctly excluded from the model (refinement.md §B) — Mul.make_args already flattens nested Muls, so the removed branch was dead; nothing in the modeled postcondition depends on it.

Counterexample / evidence:

```
None. The spec-faithful implementation (real repo, gold patch applied, consolidation block rewritten to the model's first-occurrence `==` dedup over the identical reduce(mul, filter) product) passes sympy/polys/tests/test_polytools.py with 149 passed, 1 xfailed — byte-identical to the gold's own G-RESOLVE result. Both F2P tests (test_factor_terms sqf_list(x*(x+y)) == (1,[(x**2+x*y,1)]) and test_issue_8695) pass, and no P2P test regresses. So the Float grouping difference is not graded and verify ⇒ resolved is intact.
```

**SETUP.** Spec region confirmed byte-identical: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-18698` on an identity copy of model.py -> exit 0, 'SAME'. Two fresh worktrees at base_commit 3dff1b98a7 from the upstream repository under /tmp: wt = gold patch.diff applied (the reference for the modeled function, per the brief); wt_spec = gold + test_patch + spec-faithful consolidation. patch.diff was taken from the instance dir (the nagini/ subdir has no patch.diff; instance.json['patch'] matches it byte-for-byte).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** NO RELAXATION IN THIS BUNDLE: no RELAXED_LEAKAGE.md present and meta.json has no `relaxed_leakage` key (checked: 'relaxed_leakage' in meta == False; G-LEAK status is 'pass', not 'relaxed'). So this is judged as an ordinary strict-leakage review, not an inherited disposition.

### WHAT I MEASURED (my own runs, not the bundle's assertions):

1. Spec view derived myself via swebench_unified.markers.spec_view(model.py, nagini backend) -- confirmed both impl regions elide to '...  # implementation elided'. Verified only spec_view ships to solvers (eval/dataset.py:285, eval/prompts.py:77-82); mapping.md / refinement.md / model_prepatch.py / verdict.md are NOT consumer-visible.

2. Mechanical G-LEAK screen re-run directly: swebench_unified.leakage.screen(model.py, nagini, row['patch'], row['problem_statement']) over the frozen data/swe_bench_verified/test.jsonl row -> passed=True, hard_failures=[], warnings=[].

3. Exhaustive identifier cross-check of the gold patch against the spec view. Every identifier on a +/- gold line {arg, args, elif, extend, factors, functools, is_Mul, is_Pow, method, mul, operator, reduce, set, sqf, wraps}: the repo-specific discriminators are ALL ABSENT from the view -- 'reduce'=False, 'operator'=False, 'functools'=False, 'is_Mul'=False, 'is_Pow'=False, 'sqf'=False, 'set('=False, '`_symbolic_factor_list`'=False, 'polytools'=False, "method =="=False. Confirmed 'reduce(mul' NOT in view: the one line that does name the gold ('mirrors the gold's reduce(mul,...)' at model.py:248) sits INSIDE impl-start/impl-end and is elided by the projection -- it never reaches a consumer. The apparent hits on 'method'/'extend'/'arg'/'mul'/'factors' are incidental substrings of ordinary prose ('a method that owns a loop', 'extends by one contribution', 'discharged', 'multiplicity', 'factors'), inspected in context one by one.

4. Derivability from the PUBLIC problem_statement (hints_text deliberately not consulted): the statement itself displays the merged expectation -- 'we should have (`x**2` - `5*x` + 6, 3) and not 2 factors of multiplicity 3' plus the contrasting correct case 'one factor of multiplicity 2'. Consolidate-by-multiplicity with merged factor = product of the group is exactly (x-3)*(x-2) = `x**2`-`5*x`+6 at multiplicity 3. So the whole specified behaviour (distinct multiplicities once, factor = product over the group) is a direct read of the public statement; the spec view adds no information beyond it.

5. Core-gate soundness re-derived rather than inherited. same_spec(model.py, model_prepatch.py) = True. Ran the pinned verifier myself on a /tmp copy: model.py -> 'Verification successful' (36.58s, exit 0); model_prepatch.py -> 'Verification failed', exit 1, with the discriminating error 'model_prepatch.py:204: Postcondition of consolidate_by_multiplicity might not hold. Assertion (len(Result()) == len(dedup(ToSeq(mults)))) might not hold.' The consolidation postcondition is therefore genuinely load-bearing against the PRE-patch impl -- G-DIFF/G-GOLD are sound by my measurement, not by their recorded status.

6. No bundle file addresses this reviewer. Ran leakage.reviewer_directed() over all 10 bundle files (model.py, model_prepatch.py, mapping.md, refinement.md, meta.json, axiom_check.py, conformance_check.py, properties.py, pbt_result.json, verdict.md): [] for every one. A grep for panel/auditor/reviewer/verdict/submit across the docs found only refinement.md:82 discussing 'verify => resolved' semantics -- a technical remark, not an instruction about how to record. Nothing in the bundle attempts to steer my verdict.

MINOR OBSERVATION (not leakage, not a fail): meta.json's TOP-LEVEL region_hashes are stale relative to the file -- impl/invariants/pre-conditions/spec_view disagree with the recomputed values, while the fresher G-HYGIENE data.region_hashes match my recomputation exactly on all 7 regions. Crucially the spec-CONSTITUTING regions 'post-conditions' (38de298cd73f) and 'pure' (a356f46b587c) and 'axioms' (60e88b8d07a9) agree across the stale record, the G-HYGIENE record, and my recomputation, so there is no drift in actual spec semantics -- the spec_view hash moved only because MustTerminate narration in pre-conditions was reworded. Flagging for bookkeeping hygiene; it does not affect this gate.

**SCOPE NOTE:** the gold patch also contains an is_Mul/is_Pow -> elif control-flow change that the model does not cover. That is a faithfulness/scope question for panel 2, not leakage -- and since the spec view is silent about it, it leaks nothing either way.

**VERDICT:** the consumer-visible spec view names no repo symbol, no gold-patch line, no changed file path, and nothing about the discriminator that the public problem_statement does not already show. NO-LEAKAGE.

**NO RELAXATION IN THIS BUNDLE:** no RELAXED_LEAKAGE.md present and meta.json has no `relaxed_leakage` key (checked: 'relaxed_leakage' in meta == False; G-LEAK status is 'pass', not 'relaxed'). So this is judged as an ordinary strict-leakage review, not an inherited disposition.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
