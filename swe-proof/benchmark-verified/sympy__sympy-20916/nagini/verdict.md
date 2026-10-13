# P2 adversarial audit — sympy__sympy-20916

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_v2_1.py`, `atk_v2_2.py`, `atk_v2_3.py`, `atk_v2_5.py`, `atk_v2_6.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_v2_4.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_v2_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,6 +186,10 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: the ENTIRE gold proof
+    # scaffold is retained byte-for-byte; only the RETURNED VALUE is
+    # perturbed, after the final Assert. So a rejection can only be the
+    # POSTCONDITION, never missing proof hints.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +330,14 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # PARTIAL-DOMAIN attack on the split domain: correct on every name the
+    # exception does NOT apply to, and off-by-one high on every name it DOES apply
+    # to -- the bare name keeps the FIRST digit of the peeled run.
+    # `matched` implies upper == k and k < m <= n, so the guard fires exactly on the
+    # splitting names; when not matched upper == n and nothing happens.
+    # Refines to a patch whose group-1 boundary is one code point too far right.
+    # Witness "w1": spec demands Result() == "w"; this impl returns "w1".
+    if upper < n:
+        result = result + [name[upper]]
     return result
     # impl-end
```

Attack 2 — `atk_v2_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,6 +186,10 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: the ENTIRE gold proof
+    # scaffold is retained byte-for-byte; only the RETURNED VALUE is
+    # perturbed, after the final Assert. So a rejection can only be the
+    # POSTCONDITION, never missing proof hints.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +330,14 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # PARTIAL-DOMAIN attack on the A2b / core_len ($-anchor) leg alone: correct on
+    # every name that does not end in a line feed, and wrong exactly on the
+    # LF-terminated splitting names -- the set-aside terminating line feed is glued
+    # back onto the BARE NAME instead of belonging to neither group.
+    # Witness "w1\n": the real patched regex gives groups() == ("w", "1") and
+    # split_super_sub("w1\n") == ("w", [], ["1"]), so the spec demands
+    # Result() == "w"; this impl returns "w\n".
+    if matched and n >= 1 and name[n - 1] == 10:
+        result = result + [10]
     return result
     # impl-end
```

Attack 3 — `atk_v2_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,6 +186,10 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: the ENTIRE gold proof
+    # scaffold is retained byte-for-byte; only the RETURNED VALUE is
+    # perturbed, after the final Assert. So a rejection can only be the
+    # POSTCONDITION, never missing proof hints.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +330,13 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # CONTROL-FLOW-EFFECT attack: the recognise/split decision and the whole gold
+    # proof are exact, but the result-building step has a spurious effect -- the
+    # first code point of the name is duplicated onto the end of the bare name on
+    # every non-empty input. Wrong on BOTH branches (split and no-split).
+    # Witness "abc": spec demands the name back unchanged; this impl returns
+    # "abca". Witness "w1": spec demands "w"; this impl returns "ww".
+    if n >= 1:
+        result = result + [name[0]]
     return result
     # impl-end
```

Attack 4 — `atk_v2_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,6 +186,9 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: ENTIRE gold proof scaffold retained
+    # byte-for-byte; only the RETURNED VALUE is perturbed, after the final
+    # Assert. A rejection can only be the POSTCONDITION.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +329,16 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # A-LEG (A2/A3) PARTIAL-DOMAIN attack on the ASCII-vs-any-script DISCRIMINATOR
+    # -- the very content the gold patch changed. Exactly right on every ASCII-led
+    # name, and wrong precisely on the NON-ASCII-led splitting names (code point of
+    # the first letter > 127): the bare name keeps the first digit of the peeled run.
+    # This is the prepatch defect's DOMAIN (ASCII fine, Greek/Cyrillic/astral wrong)
+    # carried by a perturbation that costs the proof nothing, so the rejection is
+    # attributable to the postcondition rather than to missing hints.
+    # Witness "ω1": the real patched regex gives groups() == ("ω", "1") so the spec
+    # demands Result() == "ω"; this impl returns "ω1". ASCII "w1" stays correct.
+    if matched and name[0] > 127:
+        result = result + [name[upper]]
     return result
     # impl-end
```

Attack 5 — `atk_v2_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,6 +186,9 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: ENTIRE gold proof scaffold retained
+    # byte-for-byte; only the RETURNED VALUE is perturbed, after the final
+    # Assert. A rejection can only be the POSTCONDITION.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +329,13 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # A-LEG (is_letter class) PARTIAL-DOMAIN attack on the UNDERSCORE boundary of
+    # [^\W\d_] vs \w (mapping.md 3.1): correct everywhere except on the
+    # underscore-bearing non-splitting names, where an extra underscore is appended.
+    # The real class excludes "_" explicitly, so "a_1" does NOT match the patched
+    # pattern and the spec demands the name back unchanged.
+    # Witness "a_1": spec demands Result() == "a_1"; this impl returns "a_1_".
+    if not matched and n >= 2 and name[1] == 95:
+        result = result + [95]
     return result
     # impl-end
```

Attack 6 — `atk_v2_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -186,6 +186,10 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (zero proof debt: the ENTIRE gold proof
+    # scaffold is retained byte-for-byte; only the RETURNED VALUE is
+    # perturbed, after the final Assert. So a rejection can only be the
+    # POSTCONDITION, never missing proof hints.)
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -326,5 +330,14 @@
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
     Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
+    # INSTRUMENT CONTROL (expected to VERIFY): the same perturbation SITE as
+    # atk_v2_1..3, wired to a guard that is provably UNREACHABLE -- `matched`
+    # implies upper == k >= 1 so len(result) >= 1, and `not matched` implies
+    # upper == n so len(result) == 0 only when n == 0, which the n >= 1 conjunct
+    # excludes. The returned value is therefore the gold value on every input.
+    # Purpose: prove the perturbation site itself is verifiable, so the rejection of
+    # atk_v2_1..3 is attributable to their VALUE CHANGE and nothing else.
+    if len(result) == 0 and n >= 1:
+        result = result + [name[n - 1]]
     return result
     # impl-end
```

Attack 7 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,28 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (prepatch ASCII recogniser)
+    # PREPATCH BUG re-encoded: the leading-letter and trailing-digit runs are
+    # recognised with the ASCII-only ranges the pre-patch regex
+    # r'^([a-zA-Z]+)([0-9]+)$' used (65..90 / 97..122 for letters, 48..57 for
+    # digits) instead of the spec's any-script is_letter / is_digit. Diverges on
+    # every non-ASCII letter or non-ASCII decimal digit (Greek omega + "1", astral
+    # bold digits), so the splits-keyed postcondition must fail.
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
     if n >= 1 and name[n - 1] == 10:
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
-    while k < n and is_letter(name[k]):
+    while k < n and ((65 <= name[k] and name[k] <= 90)
+                     or (97 <= name[k] and name[k] <= 122)):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +215,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
-            if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
+            if not (48 <= name[j] and name[j] <= 57):
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +234,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 8 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,26 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (partial-domain: no LF set aside (\Z instead of $))
+    # PARTIAL-DOMAIN attack on the A2b / core_len leg: the recogniser is
+    # correct on every name that does not end in a line feed, but sets aside NO
+    # terminating line feed (m == n always) -- i.e. it refines to the regex
+    # r'^([^\W\d_]+)(\d+)\Z' (a \Z anchor) rather than the gold's $ anchor.
+    # On "w1\n" the spec says splits (core_len sets the LF aside) and demands
+    # Result() == "w"; this impl leaves the name unchanged.
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
-    if n >= 1 and name[n - 1] == 10:
-        m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
+    # NO line feed is ever set aside: m == n always.
     k = 0
     while k < n and is_letter(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +213,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +232,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 9 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,26 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (boundary: sets aside a terminating CR as well as an LF)
+    # BOUNDARY attack on the A2b leg: sets aside ONE terminating line feed
+    # OR carriage return. The real $ anchor tolerates only '\n'
+    # (re.match(r'^([^\W\d_]+)(\d+)$', "w1\r") is None), and mapping.md 3.2 pins
+    # that. On "w1\r" the spec says NOT splits and demands the name back
+    # unchanged; this impl splits and returns "w".
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
-    if n >= 1 and name[n - 1] == 10:
+    if n >= 1 and (name[n - 1] == 10 or name[n - 1] == 13):
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
     while k < n and is_letter(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +213,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +232,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 10 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,30 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (boundary: sets aside EVERY trailing LF, not exactly one)
+    # BOUNDARY attack on the "exactly one" clause of A2b: peels every
+    # trailing line feed instead of exactly one. The real $ tolerates one only
+    # (re.match(..., "w1\n\n") is None). On "w1\n\n" the spec says NOT splits
+    # and demands the name back unchanged; this impl splits and returns "w".
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
-    if n >= 1 and name[n - 1] == 10:
-        m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
+    while m >= 1 and name[m - 1] == 10:
+        # invariants-start
+        Invariant(Acc(list_pred(name), 1 / 2))
+        Invariant(0 <= m and m <= n and n == len(name))
+        Invariant(MustTerminate(m + 1))
+        # invariants-end
+        m = m - 1
     k = 0
     while k < n and is_letter(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +217,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +236,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 11 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,27 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (A-leg: \w+ instead of [^\W\d_]+ (underscore is a letter))
+    # A-REFERENCE attack on the is_letter class (mapping.md 3.1): counts the
+    # UNDERSCORE (code point 95) as a letter, i.e. refines to r'^(\w+)(\d+)$'
+    # instead of the gold r'^([^\W\d_]+)(\d+)$'. The real class [^\W\d_]
+    # excludes '_' explicitly. On "a_1" the spec's num_leading_letters is 1, the
+    # name-proper remainder "_1" is not all digits, so NOT splits and the name must
+    # come back unchanged; this impl scans "a_" as letters and returns "a_".
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
     if n >= 1 and name[n - 1] == 10:
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
-    while k < n and is_letter(name[k]):
+    while k < n and (is_letter(name[k]) or name[k] == 95):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +214,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +233,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 12 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,26 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (control-flow effect: no-match branch truncates at first non-letter)
+    # CONTROL-FLOW-EFFECT attack: the recognise decision is exactly right,
+    # but the RESULT-BUILDING control flow leaks the letter-scan bound into the
+    # no-match branch (upper = k instead of n), so a name the exception does not
+    # apply to is silently truncated at its first non-letter. On "a_1" (NOT splits)
+    # the spec demands the name back unchanged; this impl returns "a".
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
     if n >= 1 and name[n - 1] == 10:
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
     while k < n and is_letter(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +213,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
-        upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
+        upper = k
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +232,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 13 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,45 +186,26 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (ungrounded-oracle swap: is_digit leads, is_letter tails)
+    # UNGROUNDED-ORACLE attack: the two per-code-point axioms are swapped --
+    # the leading run is scanned with is_digit and the tail with is_letter, i.e.
+    # the impl refines to r'^(\d+)([^\W\d_]+)$'. It is a same-shaped recogniser
+    # grounded in the SAME axioms, just wired to the wrong one. On "w1" the spec
+    # says splits with Result() == "w"; this impl finds no leading digit run.
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
     if n >= 1 and name[n - 1] == 10:
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
-    while k < n and is_letter(name[k]):
+    while k < n and is_digit(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
     if k >= 1 and k < m:
         j = k
         bad = False
@@ -232,64 +213,17 @@
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
-            if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
+            if not is_letter(name[j]):
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +232,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 14 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -186,110 +186,43 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (boundary off-by-one: requires a digit run of length >= 2)
+    # BOUNDARY off-by-one attack: the match guard demands k < m - 1 instead
+    # of k < m, so a name with exactly ONE trailing digit is not split. On "w1"
+    # (the headline F2P case) the spec says splits with Result() == "w"; this impl
+    # returns "w1".
     n = len(name)
-    # The name PROPER ends at `m`: a single terminating line-feed code point
-    # (10) is set aside, so m == core_len(name).
     m = n
     if n >= 1 and name[n - 1] == 10:
         m = n - 1
-    Assert(core_len(ToSeq(name)) == m)
-    Assert(0 <= m and m <= n)
-    # Count the leading run of letters. The suffix invariant carries the
-    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
-    # while every consumed position is a letter, so on exit (k == n or
-    # name[k] not a letter) k IS the full leading-letter count.
     k = 0
     while k < n and is_letter(name[k]):
         # invariants-start
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(0 <= k and k <= n and n == len(name))
-        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
-        Invariant(num_leading_letters(ToSeq(name))
-                  == k + num_leading_letters(ToSeq(name).drop(k)))
+        Invariant(0 <= m and m <= n)
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        Assert(ToSeq(name).drop(k)[0] == name[k])
-        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
         k = k + 1
-    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
-    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
-    # run. The suffix invariant mirrors all_digits over the consumed positions
-    # of the name proper `take(m)`.
     matched = False
-    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
-    # with k == num_leading_letters(name) (established above). When the leading
-    # letter run is empty or reaches the end of the name proper, splits is
-    # already False.
-    Assert(num_leading_letters(ToSeq(name)) == k)
-    if not (k >= 1 and k < m):
-        Assert(not splits(ToSeq(name)))
-    if k >= 1 and k < m:
+    if k >= 1 and k < m - 1:
         j = k
         bad = False
         while j < m and not bad:
             # invariants-start
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(k <= j and j <= m and m <= n and n == len(name))
-            Invariant(core_len(ToSeq(name)) == m)
-            Invariant(num_leading_letters(ToSeq(name)) == k)
-            Invariant(Implies(not bad,
-                              all_digits(ToSeq(name).take(m).drop(k))
-                              == all_digits(ToSeq(name).take(m).drop(j))))
-            Invariant(Implies(bad,
-                              not all_digits(ToSeq(name).take(m).drop(k))))
             Invariant(MustTerminate(m - j + 1))
             # invariants-end
             if not is_digit(name[j]):
-                # The invariant (not-bad branch) gave
-                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
-                # take(m).drop(j) starts with a non-digit, so it is False, hence
-                # all_digits(take(m).drop(k)) is False.
-                Assert(all_digits(ToSeq(name).take(m).drop(k))
-                       == all_digits(ToSeq(name).take(m).drop(j)))
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                 bad = True
             else:
-                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
-                # reduces to all_digits(take(m).drop(j+1)); the prefix
-                # equivalence is preserved.
-                Assert(ToSeq(name).take(m)[j] == name[j])
-                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
-                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
-                Assert(ToSeq(name).take(m).drop(j).drop(1)
-                       == ToSeq(name).take(m).drop(j + 1))
-                Assert(all_digits(ToSeq(name).take(m).drop(j))
-                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                 j = j + 1
-        if not bad:
-            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
-            Assert(all_digits(ToSeq(name).take(m).drop(j)))
-            Assert(all_digits(ToSeq(name).take(m).drop(k)))
         matched = not bad
-        # In this branch k>=1 and k<m, so splits reduces to
-        # all_digits(take(m).drop(k)), which is exactly `matched`.
-        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
-        Assert(matched == splits(ToSeq(name)))
-    Assert(matched == splits(ToSeq(name)))
-    # Build the result list: the leading letter run when matched, else the
-    # whole name unchanged.
     if matched:
         upper = k
     else:
         upper = n
-    # Freeze the facts the postconditions need as loop invariants so they
-    # survive the result-building loop (which only grows `result`).
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, digit_run(ToSeq(name))
-                   == ToSeq(name).take(m).drop(upper)))
-    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not matched, upper == n))
     result = []  # type: List[int]
     i = 0
     while i < upper:
@@ -298,33 +231,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
         Invariant(ToSeq(result) == ToSeq(name).take(i))
-        Invariant(matched == splits(ToSeq(name)))
-        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
-        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
-                          and all_digits(digit_run(ToSeq(name)))))
-        Invariant(Implies(not matched, upper == n))
         Invariant(MustTerminate(upper - i + 1))
         # invariants-end
         Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
         result = result + [name[i]]
         i = i + 1
-    Assert(ToSeq(result) == ToSeq(name).take(upper))
-    # When matched, upper == k == num_leading_letters == split_point(name).
-    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
-    Assert(Implies(matched, upper == split_point(ToSeq(name))))
-    Assert(Implies(matched, ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    # When not matched, upper == n and take(n) is the whole sequence.
-    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
-    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
-    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
-    Assert(matched == splits(ToSeq(name)))
-    Assert(Implies(splits(ToSeq(name)), matched))
-    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
-                   == ToSeq(name).take(split_point(ToSeq(name)))))
-    Assert(Implies(splits(ToSeq(name)),
-                   len(digit_run(ToSeq(name))) >= 1
-                   and all_digits(digit_run(ToSeq(name)))))
-    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
     return result
     # impl-end
```

Attack 15 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -186,6 +186,11 @@
     # post-conditions-end
 
     # impl-start
+    # ATTACK (echo): SEMANTICS-PRESERVING restructure of the gold impl --
+    # `upper` by default-then-override, `matched` by if/else, plus two
+    # redundant provably-true Asserts. Computes exactly the gold function, so
+    # it is expected to VERIFY; its faithful refined patch is the gold regex
+    # change and must RESOLVE (a resolving echo is not a spec weakness).
     n = len(name)
     # The name PROPER ends at `m`: a single terminating line-feed code point
     # (10) is set aside, so m == core_len(name).
@@ -269,7 +274,12 @@
             Assert(len(ToSeq(name).take(m).drop(j)) == 0)
             Assert(all_digits(ToSeq(name).take(m).drop(j)))
             Assert(all_digits(ToSeq(name).take(m).drop(k)))
-        matched = not bad
+        # ECHO: if/else instead of `matched = not bad` -- same value.
+        if bad:
+            matched = False
+        else:
+            matched = True
+        Assert(matched == (not bad))
         # In this branch k>=1 and k<m, so splits reduces to
         # all_digits(take(m).drop(k)), which is exactly `matched`.
         Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
@@ -277,10 +287,12 @@
     Assert(matched == splits(ToSeq(name)))
     # Build the result list: the leading letter run when matched, else the
     # whole name unchanged.
+    # ECHO: default-then-override instead of if/else -- same value.
+    upper = n
     if matched:
         upper = k
-    else:
-        upper = n
+    Assert(upper == k or upper == n)
+    Assert(0 <= upper and upper <= n)
     # Freeze the facts the postconditions need as loop invariants so they
     # survive the result-building loop (which only grows `result`).
     Assert(matched == splits(ToSeq(name)))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-20916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbol name ends in a run of digits, those trailing digits are peeled
  off and treated as a subscript, the remaining leading run of letters becoming
  the bare name. This trailing-digit exception is purely script-agnostic: a
  code point counts as a "letter" if it is a letter in ANY script (Latin,
  Greek, ...), and as a "digit" if it is a decimal digit in ANY script. So a
  leading run of letters in any script followed by a run of decimal digits is
  recognised and split, and a Greek-letter name with trailing digits is treated
  exactly like a Latin-letter one.

  A single line-feed code point sitting at the very END of a candidate name is
  not part of the name proper: it is set aside before the recognise/split
  decision is taken, and when the split applies it joins neither the bare name
  nor the peeled digit run. Exactly one terminating line feed is set aside, so a
  name ending in two of them still has a non-digit tail and is not split, and no
  code point other than a single terminating line feed is ever set aside.

  Concretely, for a candidate name s (the part of a symbol left of any explicit
  sub/superscript markers), write c for the name proper — s with one terminating
  line feed set aside as above. The split applies iff c is a NON-EMPTY run of
  letters immediately followed by a NON-EMPTY run of decimal digits, with
  nothing else: every code point of c before the first digit is a letter and
  every code point of c from the first digit onward is a digit. When it applies,
  the bare name becomes that leading letter run and the trailing digit run of c
  becomes a subscript; otherwise the name is left unchanged — terminating line
  feed included — and no subscript is produced.

  The discriminating cases the contract pins:
    * a Latin-letter name with trailing digits splits, e.g. "w1" -> name "w",
      subscript "1";
    * a Greek-letter (or any other non-Latin script) name with trailing digits
      ALSO splits, e.g. a Greek omega followed by "1" -> name omega, subscript
      "1" — letters are recognised regardless of script;
    * trailing digits are recognised whatever script the digits come from;
    * a name with no trailing digit run, or with a non-letter before the
      digits, or all-digit, or all-letter, is NOT split;
    * one terminating line feed disturbs none of the above: "w1" and "w1"
      followed by a line feed both give name "w", subscript "1".

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The two per-code-point classifications (letter, decimal digit) are the UNCHANGED
primitives the operation rests on; they are `@Pure @ContractOnly` axioms
validated == the language runtime's full (any-script) letter/decimal-digit
classes by axiom_check.py (G-AX), NOT consumed beyond what the proof needs. The
recognise/split decision itself — the behaviour under specification — is
modelled DEEPLY as verified front-recursive folds over the code points.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def is_letter(c: int) -> bool:
    """True iff code point `c` is a LETTER in any script (the language's
    name-letter notion: a word character that is neither a decimal digit nor
    the underscore). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script letter class,
    A-reference)."""
    Ensures(Implies(Result(), not is_digit(c)))   # letters and digits disjoint

@Pure
@ContractOnly
def is_digit(c: int) -> bool:
    """True iff code point `c` is a DECIMAL DIGIT in any script (the language's
    decimal-digit class). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script decimal-digit
    class, A-reference)."""
# axioms-end

# pure-start
@Pure
def core_len(s: PSeq[int]) -> int:
    """Length of the name PROPER of `s`: `s` with a single terminating line-feed
    code point (10) set aside. Exactly one trailing line feed is set aside;
    every other code point — a second line feed included — belongs to the name
    proper, so the name proper is `s.take(core_len(s))`."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) >= 1 and s[len(s) - 1] == 10:
        return len(s) - 1
    return len(s)

@Pure
def num_leading_letters(s: PSeq[int]) -> int:
    """Length of the maximal prefix of `s` whose every code point is a letter.
    Front-recursive so a single unfold is available per proof step."""
    Ensures(0 <= Result() and Result() <= len(s))
    # Everything strictly before the returned index is a letter; the code point
    # AT the index (when there is one) is not a letter.
    Ensures(Implies(Result() < len(s), not is_letter(s[Result()])))
    # The count of the whole sequence is its first letter plus the count of the
    # tail (front-recursive decomposition the loop relies on).
    if len(s) == 0:
        return 0
    if not is_letter(s[0]):
        return 0
    return 1 + num_leading_letters(s.drop(1))

@Pure
def all_digits(s: PSeq[int]) -> bool:
    """True iff every code point of `s` is a decimal digit. Front-recursive."""
    Ensures(Result() == Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                        is_digit(s[k])),
                                                [[s[k]]])))
    if len(s) == 0:
        return True
    if not is_digit(s[0]):
        # s[0] is a non-digit at index 0: witnesses the Forall failing.
        return False
    # is_digit(s[0]) holds. Every tail position s.drop(1)[t] equals s[t+1], so
    # the tail's Forall (the recursive postcondition) transfers to the full
    # Forall over s (index 0 is the digit s[0]).
    Assert(Forall(int, lambda t: (Implies(0 <= t and t < len(s) - 1,
                                          s.drop(1)[t] == s[t + 1]),
                                  [[s.drop(1)[t]]])))
    Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                          s[k] == s.drop(1)[k - 1]),
                                  [[s[k]]])))
    return all_digits(s.drop(1))

@Pure
def splits(s: PSeq[int]) -> bool:
    """The trailing-digit exception applies to `s` iff the name proper
    `s.take(core_len(s))` is a non-empty run of letters immediately followed by
    a non-empty run of decimal digits, with nothing else. Because letters and
    digits are disjoint, the boundary is the end of the leading letter run: the
    split applies iff that run is non-empty, stops strictly inside the name
    proper, and the rest of the name proper is all digits."""
    return (num_leading_letters(s) >= 1
            and num_leading_letters(s) < core_len(s)
            and all_digits(s.take(core_len(s))
                           .drop(num_leading_letters(s))))

@Pure
def split_point(s: PSeq[int]) -> int:
    """The code-point index at which `s` is split when the exception applies:
    the length of the leading letter run (= the start of the trailing digit run
    inside the name proper). Only meaningful when `splits(s)`."""
    return num_leading_letters(s)

@Pure
def digit_run(s: PSeq[int]) -> PSeq[int]:
    """The peeled trailing digit run — the part of the name PROPER from the
    split point onward, so the set-aside terminating line feed is not part of
    it. Only meaningful when `splits(s)`."""
    return s.take(core_len(s)).drop(split_point(s))
# pure-end

def split_trailing_digits(name: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` is the candidate symbol name (code points), read-only: the
    # operation derives a new bare name and never mutates the input.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the trailing-digit exception applies, the bare name is exactly the
    # leading letter run; the peeled trailing digit run (the new subscript) is
    # `digit_run` and is non-empty and all digits.
    Ensures(Implies(splits(ToSeq(name)),
                    ToSeq(Result())
                    == ToSeq(name).take(split_point(ToSeq(name)))))
    Ensures(Implies(splits(ToSeq(name)),
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
    # When it does not apply, the name is returned unchanged.
    Ensures(Implies(not splits(ToSeq(name)), ToSeq(Result()) == ToSeq(name)))
    # post-conditions-end

    # impl-start
    n = len(name)
    # The name PROPER ends at `m`: a single terminating line-feed code point
    # (10) is set aside, so m == core_len(name).
    m = n
    if n >= 1 and name[n - 1] == 10:
        m = n - 1
    Assert(core_len(ToSeq(name)) == m)
    Assert(0 <= m and m <= n)
    # Count the leading run of letters. The suffix invariant carries the
    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
    # while every consumed position is a letter, so on exit (k == n or
    # name[k] not a letter) k IS the full leading-letter count.
    k = 0
    while k < n and is_letter(name[k]):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(0 <= k and k <= n and n == len(name))
        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
        Invariant(num_leading_letters(ToSeq(name))
                  == k + num_leading_letters(ToSeq(name).drop(k)))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        Assert(ToSeq(name).drop(k)[0] == name[k])
        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
        k = k + 1
    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
    Assert(num_leading_letters(ToSeq(name)) == k)
    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
    # run. The suffix invariant mirrors all_digits over the consumed positions
    # of the name proper `take(m)`.
    matched = False
    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
    # with k == num_leading_letters(name) (established above). When the leading
    # letter run is empty or reaches the end of the name proper, splits is
    # already False.
    Assert(num_leading_letters(ToSeq(name)) == k)
    if not (k >= 1 and k < m):
        Assert(not splits(ToSeq(name)))
    if k >= 1 and k < m:
        j = k
        bad = False
        while j < m and not bad:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(k <= j and j <= m and m <= n and n == len(name))
            Invariant(core_len(ToSeq(name)) == m)
            Invariant(num_leading_letters(ToSeq(name)) == k)
            Invariant(Implies(not bad,
                              all_digits(ToSeq(name).take(m).drop(k))
                              == all_digits(ToSeq(name).take(m).drop(j))))
            Invariant(Implies(bad,
                              not all_digits(ToSeq(name).take(m).drop(k))))
            Invariant(MustTerminate(m - j + 1))
            # invariants-end
            if not is_digit(name[j]):
                # The invariant (not-bad branch) gave
                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
                # take(m).drop(j) starts with a non-digit, so it is False, hence
                # all_digits(take(m).drop(k)) is False.
                Assert(all_digits(ToSeq(name).take(m).drop(k))
                       == all_digits(ToSeq(name).take(m).drop(j)))
                Assert(ToSeq(name).take(m)[j] == name[j])
                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                bad = True
            else:
                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
                # reduces to all_digits(take(m).drop(j+1)); the prefix
                # equivalence is preserved.
                Assert(ToSeq(name).take(m)[j] == name[j])
                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
                Assert(ToSeq(name).take(m).drop(j).drop(1)
                       == ToSeq(name).take(m).drop(j + 1))
                Assert(all_digits(ToSeq(name).take(m).drop(j))
                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                j = j + 1
        if not bad:
            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
            Assert(all_digits(ToSeq(name).take(m).drop(j)))
            Assert(all_digits(ToSeq(name).take(m).drop(k)))
        matched = not bad
        # In this branch k>=1 and k<m, so splits reduces to
        # all_digits(take(m).drop(k)), which is exactly `matched`.
        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
        Assert(matched == splits(ToSeq(name)))
    Assert(matched == splits(ToSeq(name)))
    # Build the result list: the leading letter run when matched, else the
    # whole name unchanged.
    if matched:
        upper = k
    else:
        upper = n
    # Freeze the facts the postconditions need as loop invariants so they
    # survive the result-building loop (which only grows `result`).
    Assert(matched == splits(ToSeq(name)))
    Assert(Implies(matched, upper == split_point(ToSeq(name))))
    Assert(Implies(matched, digit_run(ToSeq(name))
                   == ToSeq(name).take(m).drop(upper)))
    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
                   and all_digits(digit_run(ToSeq(name)))))
    Assert(Implies(not matched, upper == n))
    result = []  # type: List[int]
    i = 0
    while i < upper:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        Invariant(matched == splits(ToSeq(name)))
        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
                          and all_digits(digit_run(ToSeq(name)))))
        Invariant(Implies(not matched, upper == n))
        Invariant(MustTerminate(upper - i + 1))
        # invariants-end
        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(result) == ToSeq(name).take(upper))
    # When matched, upper == k == num_leading_letters == split_point(name).
    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
    Assert(Implies(matched, upper == split_point(ToSeq(name))))
    Assert(Implies(matched, ToSeq(result)
                   == ToSeq(name).take(split_point(ToSeq(name)))))
    # When not matched, upper == n and take(n) is the whole sequence.
    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
    Assert(matched == splits(ToSeq(name)))
    Assert(Implies(splits(ToSeq(name)), matched))
    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
                   == ToSeq(name).take(split_point(ToSeq(name)))))
    Assert(Implies(splits(ToSeq(name)),
                   len(digit_run(ToSeq(name))) >= 1
                   and all_digits(digit_run(ToSeq(name)))))
    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 15 same-spec attacks run (floor 5); prepatch bug reproduced; positive control verifies; both CANDIDATEs' faithful patches RESOLVED under the official harness. No verifying impl whose faithful patch fails to resolve was found.

METHODOLOGY NOTE (the finding that shaped this audit): my first attack family (atk_1..atk_8) used a MINIMAL proof scaffold (the model_prepatch.py skeleton) with the spec-referencing Asserts dropped. All 8 came back EXIT=2. But a SKELETON CONTROL — skel_control.py, that same minimal scaffold wired to the CORRECT gold behaviour (any-script is_letter/is_digit, exactly one terminating LF set aside, upper=k/n) — ALSO fails: `bash scripts/nagini_verify.sh skel_control.py` -> EXIT=1, 'Postcondition ... Implies(splits(ToSeq(name)), ToSeq(Result()) == ToSeq(name).take(split_point(ToSeq(name)))) might not hold' (21.45s). So those 8 rejections are NOT attributable: the minimal scaffold carries proof debt, and a correct impl fails it too. Reporting them alone would have been a rubber-stamp dressed as 8 data points. They are still submitted (all same-spec, all genuinely wrong) but carry no weight.

ATTRIBUTABLE FAMILY (atk_v2_*): each retains the ENTIRE gold proof scaffold byte-for-byte and perturbs ONLY the returned value, after the final Assert. Proof debt is therefore zero by construction, so a rejection can only be the postcondition. This is instrumented by atk_v2_4, an INSTRUMENT CONTROL using the same perturbation SITE under a provably-unreachable guard (`len(result)==0 and n>=1`): it VERIFIES (CANDIDATE, 46.3s), proving the site itself is verifiable and the v2 rejections are due to the VALUE CHANGE alone.

### Per-attack results
- atk_v2_1.py partial-domain / boundary: bare name keeps the FIRST digit of the peeled run on exactly the splitting names (`if upper < n: result += [name[upper]]`), correct on all non-splitting names. Witness 'w1' -> gold 'w', attack 'w1'. EXIT=2. Reason captured directly: `bash scripts/nagini_verify.sh atk_v2_1.py` -> EXIT=1, 'atk_v2_1.py:178:13:180:67: error: Postcondition ... Implies(splits, Result()==take(split_point)) might not hold' (25.70s).
- atk_v2_2.py partial-domain on the A2b/core_len ($-anchor) leg ALONE: correct on every non-LF-terminated name; on LF-terminated splitting names it glues the set-aside line feed back onto the BARE name. Witness 'w1\n' -> real regex groups()==('w','1') and real split_super_sub('w1\n')==('w',[],['1']), so gold 'w'; attack 'w\n'. EXIT=2; reason = same P1 postcondition (err_v2_2.txt).
- atk_v2_3.py control-flow-effect: spurious effect in the result-building step duplicates name[0] onto the bare name on every non-empty input, wrong on BOTH branches. Witness 'w' -> gold 'w', attack 'ww'; 'w1' -> gold 'w', attack 'ww'. EXIT=2.
- atk_v2_5.py A-LEG (A2/A3) partial-domain on the ASCII-vs-any-script DISCRIMINATOR — the exact content the gold patch changed: correct on every ASCII-led name, wrong precisely on the NON-ASCII-led splitting names (`if matched and name[0] > 127`). Witness 'ω1' -> gold 'ω', attack 'ω1'; 'w1' stays correct. Simulated: 7 divergences / 15 agreements. EXIT=2; reason = P1 (err_v2_5.txt).
- atk_v2_6.py A-LEG partial-domain on the UNDERSCORE boundary of [^\W\d_] vs \w (mapping.md §3.1): appends an underscore only on underscore-bearing non-splitting names. Witness 'a_1' -> gold 'a_1', attack 'a_1_'. 3 divergences / 19 agreements. EXIT=2.
- atk_v2_4.py INSTRUMENT CONTROL (behaviourally the gold): EXIT=0 CANDIDATE (46.3s) -> resolve run below.
- atk_9.py ECHO: semantics-preserving restructure of the gold impl (`upper` by default-then-override, `matched` by if/else, two redundant provable Asserts). EXIT=0 CANDIDATE (46.5s) -> resolve run below.
- atk_1.py PREPATCH BUG re-encoded (ASCII ranges 65..90/97..122 letters, 48..57 digits = the pre-patch regex r'^([a-zA-Z]+)([0-9]+)$'): EXIT=2. Independently confirmed attributable via the bundle's own prepatch model: `bash scripts/nagini_verify.sh benchmark-verified/.../model_prepatch.py` -> EXIT=1 on the SAME P1 postcondition. PREPATCH BUG REPRODUCED.
- atk_2/3/4 ($-anchor variants: \Z instead of $; CR tolerated; ALL trailing LFs peeled), atk_5 (\w+ i.e. underscore-as-letter), atk_6 (no-match branch truncates), atk_7 (classes swapped: r'^(\d+)([^\W\d_]+)$'), atk_8 (digit run must be >=2): all EXIT=2, all same-spec, all with confirmed divergence witnesses — but NOT attributable per the methodology note.

MANDATORY RESOLVE ON EVERY CANDIDATE. Both candidates (atk_v2_4, atk_9) compute exactly the gold function — verified by simulation against the real compiled patched regex on 37 boundary names, zero divergence — so the faithful refined patch of each IS the gold regex change. Materialized at faithful_patch.diff (md5 ccf26b09b88458ab139d287688218507, byte-identical to the bundle's patch.diff) and RUN through the official harness: `swebench_unified.harness.run_resolve('sympy__sympy-20916', patch, timeout=3600, retries=1)`. OBSERVED (resolve_result.json): resolved=true, completed=true, note='resolved'. Both candidates RESOLVE -> correct echoes, NOT spec weaknesses (per docs/architecture.md §6 and the per-attack derivation in build_one.py).

SPEC-TOTALITY PROBE (why so little room exists): the frozen postconditions are P1 Implies(splits, Result()==take(split_point)), P2 Implies(splits, len(digit_run)>=1 and all_digits(digit_run)), P3 Implies(not splits, Result()==name). P1/P3 are keyed on complementary guards over a TOTAL precondition (Acc(list_pred(name),1/2)+MustTerminate admits any int list), so Result() is pinned on EVERY input. _specstrength.py over 300000 random code-point lists (incl. NUL, U+10FFFF, LS, NEL): 0 unpinned inputs, 0 inputs where the pinned value differs from the real gold function, 0 inputs where P1 fires but P2 is unsatisfiable. The only verifying impls are therefore behavioural echoes of the gold — consistent with both candidates resolving.

A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's). Ran the bundle's own check — `python axiom_check.py` -> EXIT=0, 'is_letter/is_digit classes + disjointness sound over 65792 code points; deep split model == real re recogniser on 51 boundary + 60000 fuzz names' — and then an INDEPENDENT re-derivation I wrote from scratch (_aleg.py), not a re-run of theirs:
  * B1 (A-consumed, the ONLY consumed kind-A fact: is_letter(c) => not is_digit(c)): holds over 68352 real code points (full BMP + U+1D400-1D7FF + U+1E900-1EDFF + U+10000-104FF + U+1FB00-1FFFF), a wider sweep than axiom_check.py's.
  * A2/A2b/A3/A5 (the deep model splits/split_point/digit_run == the real compiled patched regex's match/groups()): HOLDS over 200000 adversarial names on an alphabet deliberately including boundaries axiom_check.py OMITS — VT, FF, NEL(U+0085), LS(U+2028), PS(U+2029), NBSP, FS/GS/RS, and 'digit-looking' code points that are NOT \d (superscript ², roman Ⅰ, fraction ⅓, circled), plus full-width, Ethiopic and Adlam digits. Zero divergences: the $-anchor rule really does tolerate exactly one '\n' and nothing else, as mapping.md §3.2 claims.
  * A7/A5/A6 (the legs refinement.md declares I and does NOT model — subs.insert(0,sub) and the surrounding split_super_sub loop): checked END-TO-END against the REAL patched repo file (_a7.py loads sympy/printing/conventions.py at base_commit 82298df6 with the gold hunk applied, asserts _name_with_digits_p.pattern is the post-patch pattern). On 35077 separator-free names the real patched split_super_sub's (name, supers, subs) == (model bare name, [], [model digit_run] or []) with zero divergences. The unmodeled legs are genuinely identity.

REFINEMENT.MD LEG CLASSIFICATION: every leg is R / A-consumed / A-reference / I — NO kind-3. A1=R (str <-> List[int] of code points); A2=A-reference (greedy [^\W\d_]+ <-> num_leading_letters); A2b=A-reference ($ anchor <-> core_len, and correctly flagged UNCHANGED by the patch, so not the discriminator); A3=A-reference (\d+$ <-> all_digits over take(core_len)); A4=A-reference+I (match success <-> deep splits; the k>=1 / k<m conjunction control flow is identical); A5=R+A-reference (m.group(1)/(2) <-> take(split_point) / digit_run bounded by core_len not len); A6=I (no-match leaves name and subs untouched); A7=I (subs.insert, verified above). The one genuinely CHANGED operation (ASCII -> any-script recogniser) is modeled DEEPLY, not hidden behind a whole-callee axiom; the single A-consumed fact is the disjointness clause B1. §C's no-kind-3 claim checks out.

G-MUT SURVIVOR reviewed (not a G-EQ defect): 'line 226: < -> <=' sits in `if not (k >= 1 and k < m): Assert(not splits(...))`, a PROOF-ONLY hint line inside the impl region, not a behavioural branch — the behavioural guard is the `if k >= 1 and k < m:` on line 228. Weakening the hint's guard cannot change the returned value, which is why it survives; atk_v2_1's boundary perturbation covers the real off-by-one direction and is rejected.

Every attack fully verified and reported; no run left incomplete, no timeouts, so nothing is inconclusive.

VERDICT SOUND: 5 attributable same-spec wrong impls (atk_v2_1/2/3/5/6, zero proof debt, instrument-controlled) all REJECTED on postcondition P1; the prepatch bug reproduced and rejected; 10 further same-spec wrong impls also rejected; the positive control verifies (EXIT=0, 42.83s); both verifying candidates RESOLVE under the official harness. verify => correct upheld for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_v2_1.py`, `atk_v2_2.py`, `atk_v2_3.py`, `atk_v2_5.py`, `atk_v2_6.py`, `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_v2_4.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_v2_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_v2_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_v2_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_v2_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_v2_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_v2_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-20916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbol name ends in a run of digits, those trailing digits are peeled
  off and treated as a subscript, the remaining leading run of letters becoming
  the bare name. This trailing-digit exception is purely script-agnostic: a
  code point counts as a "letter" if it is a letter in ANY script (Latin,
  Greek, ...), and as a "digit" if it is a decimal digit in ANY script. So a
  leading run of letters in any script followed by a run of decimal digits is
  recognised and split, and a Greek-letter name with trailing digits is treated
  exactly like a Latin-letter one.

  A single line-feed code point sitting at the very END of a candidate name is
  not part of the name proper: it is set aside before the recognise/split
  decision is taken, and when the split applies it joins neither the bare name
  nor the peeled digit run. Exactly one terminating line feed is set aside, so a
  name ending in two of them still has a non-digit tail and is not split, and no
  code point other than a single terminating line feed is ever set aside.

  Concretely, for a candidate name s (the part of a symbol left of any explicit
  sub/superscript markers), write c for the name proper — s with one terminating
  line feed set aside as above. The split applies iff c is a NON-EMPTY run of
  letters immediately followed by a NON-EMPTY run of decimal digits, with
  nothing else: every code point of c before the first digit is a letter and
  every code point of c from the first digit onward is a digit. When it applies,
  the bare name becomes that leading letter run and the trailing digit run of c
  becomes a subscript; otherwise the name is left unchanged — terminating line
  feed included — and no subscript is produced.

  The discriminating cases the contract pins:
    * a Latin-letter name with trailing digits splits, e.g. "w1" -> name "w",
      subscript "1";
    * a Greek-letter (or any other non-Latin script) name with trailing digits
      ALSO splits, e.g. a Greek omega followed by "1" -> name omega, subscript
      "1" — letters are recognised regardless of script;
    * trailing digits are recognised whatever script the digits come from;
    * a name with no trailing digit run, or with a non-letter before the
      digits, or all-digit, or all-letter, is NOT split;
    * one terminating line feed disturbs none of the above: "w1" and "w1"
      followed by a line feed both give name "w", subscript "1".

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The two per-code-point classifications (letter, decimal digit) are the UNCHANGED
primitives the operation rests on; they are `@Pure @ContractOnly` axioms
validated == the language runtime's full (any-script) letter/decimal-digit
classes by axiom_check.py (G-AX), NOT consumed beyond what the proof needs. The
recognise/split decision itself — the behaviour under specification — is
modelled DEEPLY as verified front-recursive folds over the code points.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def is_letter(c: int) -> bool:
    """True iff code point `c` is a LETTER in any script (the language's
    name-letter notion: a word character that is neither a decimal digit nor
    the underscore). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script letter class,
    A-reference)."""
    Ensures(Implies(Result(), not is_digit(c)))   # letters and digits disjoint

@Pure
@ContractOnly
def is_digit(c: int) -> bool:
    """True iff code point `c` is a DECIMAL DIGIT in any script (the language's
    decimal-digit class). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script decimal-digit
    class, A-reference)."""
# axioms-end

# pure-start
@Pure
def core_len(s: PSeq[int]) -> int:
    """Length of the name PROPER of `s`: `s` with a single terminating line-feed
    code point (10) set aside. Exactly one trailing line feed is set aside;
    every other code point — a second line feed included — belongs to the name
    proper, so the name proper is `s.take(core_len(s))`."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) >= 1 and s[len(s) - 1] == 10:
        return len(s) - 1
    return len(s)

@Pure
def num_leading_letters(s: PSeq[int]) -> int:
    """Length of the maximal prefix of `s` whose every code point is a letter.
    Front-recursive so a single unfold is available per proof step."""
    Ensures(0 <= Result() and Result() <= len(s))
    # Everything strictly before the returned index is a letter; the code point
    # AT the index (when there is one) is not a letter.
    Ensures(Implies(Result() < len(s), not is_letter(s[Result()])))
    # The count of the whole sequence is its first letter plus the count of the
    # tail (front-recursive decomposition the loop relies on).
    if len(s) == 0:
        return 0
    if not is_letter(s[0]):
        return 0
    return 1 + num_leading_letters(s.drop(1))

@Pure
def all_digits(s: PSeq[int]) -> bool:
    """True iff every code point of `s` is a decimal digit. Front-recursive."""
    Ensures(Result() == Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                        is_digit(s[k])),
                                                [[s[k]]])))
    if len(s) == 0:
        return True
    if not is_digit(s[0]):
        # s[0] is a non-digit at index 0: witnesses the Forall failing.
        return False
    # is_digit(s[0]) holds. Every tail position s.drop(1)[t] equals s[t+1], so
    # the tail's Forall (the recursive postcondition) transfers to the full
    # Forall over s (index 0 is the digit s[0]).
    Assert(Forall(int, lambda t: (Implies(0 <= t and t < len(s) - 1,
                                          s.drop(1)[t] == s[t + 1]),
                                  [[s.drop(1)[t]]])))
    Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                          s[k] == s.drop(1)[k - 1]),
                                  [[s[k]]])))
    return all_digits(s.drop(1))

@Pure
def splits(s: PSeq[int]) -> bool:
    """The trailing-digit exception applies to `s` iff the name proper
    `s.take(core_len(s))` is a non-empty run of letters immediately followed by
    a non-empty run of decimal digits, with nothing else. Because letters and
    digits are disjoint, the boundary is the end of the leading letter run: the
    split applies iff that run is non-empty, stops strictly inside the name
    proper, and the rest of the name proper is all digits."""
    return (num_leading_letters(s) >= 1
            and num_leading_letters(s) < core_len(s)
            and all_digits(s.take(core_len(s))
                           .drop(num_leading_letters(s))))

@Pure
def split_point(s: PSeq[int]) -> int:
    """The code-point index at which `s` is split when the exception applies:
    the length of the leading letter run (= the start of the trailing digit run
    inside the name proper). Only meaningful when `splits(s)`."""
    return num_leading_letters(s)

@Pure
def digit_run(s: PSeq[int]) -> PSeq[int]:
    """The peeled trailing digit run — the part of the name PROPER from the
    split point onward, so the set-aside terminating line feed is not part of
    it. Only meaningful when `splits(s)`."""
    return s.take(core_len(s)).drop(split_point(s))
# pure-end

def split_trailing_digits(name: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` is the candidate symbol name (code points), read-only: the
    # operation derives a new bare name and never mutates the input.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the trailing-digit exception applies, the bare name is exactly the
    # leading letter run; the peeled trailing digit run (the new subscript) is
    # `digit_run` and is non-empty and all digits.
    Ensures(Implies(splits(ToSeq(name)),
                    ToSeq(Result())
                    == ToSeq(name).take(split_point(ToSeq(name)))))
    Ensures(Implies(splits(ToSeq(name)),
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
    # When it does not apply, the name is returned unchanged.
    Ensures(Implies(not splits(ToSeq(name)), ToSeq(Result()) == ToSeq(name)))
    # post-conditions-end

    # impl-start
    n = len(name)
    # The name PROPER ends at `m`: a single terminating line-feed code point
    # (10) is set aside, so m == core_len(name).
    m = n
    if n >= 1 and name[n - 1] == 10:
        m = n - 1
    Assert(core_len(ToSeq(name)) == m)
    Assert(0 <= m and m <= n)
    # Count the leading run of letters. The suffix invariant carries the
    # front-recursive identity num_leading_letters(name) == k + nll(drop k)
    # while every consumed position is a letter, so on exit (k == n or
    # name[k] not a letter) k IS the full leading-letter count.
    k = 0
    while k < n and is_letter(name[k]):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(0 <= k and k <= n and n == len(name))
        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)
        Invariant(num_leading_letters(ToSeq(name))
                  == k + num_leading_letters(ToSeq(name).drop(k)))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        Assert(ToSeq(name).drop(k)[0] == name[k])
        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))
        k = k + 1
    Assert(k == n or not is_letter(ToSeq(name).drop(k)[0]))
    Assert(num_leading_letters(ToSeq(name).drop(k)) == 0)
    Assert(num_leading_letters(ToSeq(name)) == k)
    # Decide whether the name proper's remainder [k, m) is a non-empty all-digit
    # run. The suffix invariant mirrors all_digits over the consumed positions
    # of the name proper `take(m)`.
    matched = False
    # splits(name) decomposes as (k>=1) and (k<m) and all_digits(take(m).drop(k)),
    # with k == num_leading_letters(name) (established above). When the leading
    # letter run is empty or reaches the end of the name proper, splits is
    # already False.
    Assert(num_leading_letters(ToSeq(name)) == k)
    if not (k >= 1 and k < m):
        Assert(not splits(ToSeq(name)))
    if k >= 1 and k < m:
        j = k
        bad = False
        while j < m and not bad:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(k <= j and j <= m and m <= n and n == len(name))
            Invariant(core_len(ToSeq(name)) == m)
            Invariant(num_leading_letters(ToSeq(name)) == k)
            Invariant(Implies(not bad,
                              all_digits(ToSeq(name).take(m).drop(k))
                              == all_digits(ToSeq(name).take(m).drop(j))))
            Invariant(Implies(bad,
                              not all_digits(ToSeq(name).take(m).drop(k))))
            Invariant(MustTerminate(m - j + 1))
            # invariants-end
            if not is_digit(name[j]):
                # The invariant (not-bad branch) gave
                # all_digits(take(m).drop(k)) == all_digits(take(m).drop(j));
                # take(m).drop(j) starts with a non-digit, so it is False, hence
                # all_digits(take(m).drop(k)) is False.
                Assert(all_digits(ToSeq(name).take(m).drop(k))
                       == all_digits(ToSeq(name).take(m).drop(j)))
                Assert(ToSeq(name).take(m)[j] == name[j])
                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
                Assert(not is_digit(ToSeq(name).take(m).drop(j)[0]))
                Assert(not all_digits(ToSeq(name).take(m).drop(j)))
                bad = True
            else:
                # is_digit(name[j]) holds, so all_digits(take(m).drop(j))
                # reduces to all_digits(take(m).drop(j+1)); the prefix
                # equivalence is preserved.
                Assert(ToSeq(name).take(m)[j] == name[j])
                Assert(ToSeq(name).take(m).drop(j)[0] == name[j])
                Assert(is_digit(ToSeq(name).take(m).drop(j)[0]))
                Assert(ToSeq(name).take(m).drop(j).drop(1)
                       == ToSeq(name).take(m).drop(j + 1))
                Assert(all_digits(ToSeq(name).take(m).drop(j))
                       == all_digits(ToSeq(name).take(m).drop(j + 1)))
                j = j + 1
        if not bad:
            Assert(len(ToSeq(name).take(m).drop(j)) == 0)
            Assert(all_digits(ToSeq(name).take(m).drop(j)))
            Assert(all_digits(ToSeq(name).take(m).drop(k)))
        matched = not bad
        # In this branch k>=1 and k<m, so splits reduces to
        # all_digits(take(m).drop(k)), which is exactly `matched`.
        Assert(matched == all_digits(ToSeq(name).take(m).drop(k)))
        Assert(matched == splits(ToSeq(name)))
    Assert(matched == splits(ToSeq(name)))
    # Build the result list: the leading letter run when matched, else the
    # whole name unchanged.
    if matched:
        upper = k
    else:
        upper = n
    # Freeze the facts the postconditions need as loop invariants so they
    # survive the result-building loop (which only grows `result`).
    Assert(matched == splits(ToSeq(name)))
    Assert(Implies(matched, upper == split_point(ToSeq(name))))
    Assert(Implies(matched, digit_run(ToSeq(name))
                   == ToSeq(name).take(m).drop(upper)))
    Assert(Implies(matched, len(digit_run(ToSeq(name))) >= 1
                   and all_digits(digit_run(ToSeq(name)))))
    Assert(Implies(not matched, upper == n))
    result = []  # type: List[int]
    i = 0
    while i < upper:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        Invariant(matched == splits(ToSeq(name)))
        Invariant(Implies(matched, upper == split_point(ToSeq(name))))
        Invariant(Implies(matched, len(digit_run(ToSeq(name))) >= 1
                          and all_digits(digit_run(ToSeq(name)))))
        Invariant(Implies(not matched, upper == n))
        Invariant(MustTerminate(upper - i + 1))
        # invariants-end
        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(result) == ToSeq(name).take(upper))
    # When matched, upper == k == num_leading_letters == split_point(name).
    Assert(Implies(matched, upper == num_leading_letters(ToSeq(name))))
    Assert(Implies(matched, upper == split_point(ToSeq(name))))
    Assert(Implies(matched, ToSeq(result)
                   == ToSeq(name).take(split_point(ToSeq(name)))))
    # When not matched, upper == n and take(n) is the whole sequence.
    Assert(Implies(not matched, ToSeq(name).take(n) == ToSeq(name)))
    Assert(Implies(not matched, ToSeq(result) == ToSeq(name)))
    # Chain matched == splits(name) to discharge the splits-keyed postconditions.
    Assert(matched == splits(ToSeq(name)))
    Assert(Implies(splits(ToSeq(name)), matched))
    Assert(Implies(splits(ToSeq(name)), ToSeq(result)
                   == ToSeq(name).take(split_point(ToSeq(name)))))
    Assert(Implies(splits(ToSeq(name)),
                   len(digit_run(ToSeq(name))) >= 1
                   and all_digits(digit_run(ToSeq(name)))))
    Assert(Implies(not splits(ToSeq(name)), ToSeq(result) == ToSeq(name)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 15 same-spec attacks run (floor 5); prepatch bug reproduced; positive control verifies; both CANDIDATEs' faithful patches RESOLVED under the official harness. No verifying impl whose faithful patch fails to resolve was found.

METHODOLOGY NOTE (the finding that shaped this audit): my first attack family (atk_1..atk_8) used a MINIMAL proof scaffold (the model_prepatch.py skeleton) with the spec-referencing Asserts dropped. All 8 came back EXIT=2. But a SKELETON CONTROL — skel_control.py, that same minimal scaffold wired to the CORRECT gold behaviour (any-script is_letter/is_digit, exactly one terminating LF set aside, upper=k/n) — ALSO fails: `bash scripts/nagini_verify.sh skel_control.py` -> EXIT=1, 'Postcondition ... Implies(splits(ToSeq(name)), ToSeq(Result()) == ToSeq(name).take(split_point(ToSeq(name)))) might not hold' (21.45s). So those 8 rejections are NOT attributable: the minimal scaffold carries proof debt, and a correct impl fails it too. Reporting them alone would have been a rubber-stamp dressed as 8 data points. They are still submitted (all same-spec, all genuinely wrong) but carry no weight.

ATTRIBUTABLE FAMILY (atk_v2_*): each retains the ENTIRE gold proof scaffold byte-for-byte and perturbs ONLY the returned value, after the final Assert. Proof debt is therefore zero by construction, so a rejection can only be the postcondition. This is instrumented by atk_v2_4, an INSTRUMENT CONTROL using the same perturbation SITE under a provably-unreachable guard (`len(result)==0 and n>=1`): it VERIFIES (CANDIDATE, 46.3s), proving the site itself is verifiable and the v2 rejections are due to the VALUE CHANGE alone.

### Per-attack results
- atk_v2_1.py partial-domain / boundary: bare name keeps the FIRST digit of the peeled run on exactly the splitting names (`if upper < n: result += [name[upper]]`), correct on all non-splitting names. Witness 'w1' -> gold 'w', attack 'w1'. EXIT=2. Reason captured directly: `bash scripts/nagini_verify.sh atk_v2_1.py` -> EXIT=1, 'atk_v2_1.py:178:13:180:67: error: Postcondition ... Implies(splits, Result()==take(split_point)) might not hold' (25.70s).
- atk_v2_2.py partial-domain on the A2b/core_len ($-anchor) leg ALONE: correct on every non-LF-terminated name; on LF-terminated splitting names it glues the set-aside line feed back onto the BARE name. Witness 'w1\n' -> real regex groups()==('w','1') and real split_super_sub('w1\n')==('w',[],['1']), so gold 'w'; attack 'w\n'. EXIT=2; reason = same P1 postcondition (err_v2_2.txt).
- atk_v2_3.py control-flow-effect: spurious effect in the result-building step duplicates name[0] onto the bare name on every non-empty input, wrong on BOTH branches. Witness 'w' -> gold 'w', attack 'ww'; 'w1' -> gold 'w', attack 'ww'. EXIT=2.
- atk_v2_5.py A-LEG (A2/A3) partial-domain on the ASCII-vs-any-script DISCRIMINATOR — the exact content the gold patch changed: correct on every ASCII-led name, wrong precisely on the NON-ASCII-led splitting names (`if matched and name[0] > 127`). Witness 'ω1' -> gold 'ω', attack 'ω1'; 'w1' stays correct. Simulated: 7 divergences / 15 agreements. EXIT=2; reason = P1 (err_v2_5.txt).
- atk_v2_6.py A-LEG partial-domain on the UNDERSCORE boundary of [^\W\d_] vs \w (mapping.md §3.1): appends an underscore only on underscore-bearing non-splitting names. Witness 'a_1' -> gold 'a_1', attack 'a_1_'. 3 divergences / 19 agreements. EXIT=2.
- atk_v2_4.py INSTRUMENT CONTROL (behaviourally the gold): EXIT=0 CANDIDATE (46.3s) -> resolve run below.
- atk_9.py ECHO: semantics-preserving restructure of the gold impl (`upper` by default-then-override, `matched` by if/else, two redundant provable Asserts). EXIT=0 CANDIDATE (46.5s) -> resolve run below.
- atk_1.py PREPATCH BUG re-encoded (ASCII ranges 65..90/97..122 letters, 48..57 digits = the pre-patch regex r'^([a-zA-Z]+)([0-9]+)$'): EXIT=2. Independently confirmed attributable via the bundle's own prepatch model: `bash scripts/nagini_verify.sh benchmark-verified/.../model_prepatch.py` -> EXIT=1 on the SAME P1 postcondition. PREPATCH BUG REPRODUCED.
- atk_2/3/4 ($-anchor variants: \Z instead of $; CR tolerated; ALL trailing LFs peeled), atk_5 (\w+ i.e. underscore-as-letter), atk_6 (no-match branch truncates), atk_7 (classes swapped: r'^(\d+)([^\W\d_]+)$'), atk_8 (digit run must be >=2): all EXIT=2, all same-spec, all with confirmed divergence witnesses — but NOT attributable per the methodology note.

MANDATORY RESOLVE ON EVERY CANDIDATE. Both candidates (atk_v2_4, atk_9) compute exactly the gold function — verified by simulation against the real compiled patched regex on 37 boundary names, zero divergence — so the faithful refined patch of each IS the gold regex change. Materialized at faithful_patch.diff (md5 ccf26b09b88458ab139d287688218507, byte-identical to the bundle's patch.diff) and RUN through the official harness: `swebench_unified.harness.run_resolve('sympy__sympy-20916', patch, timeout=3600, retries=1)`. OBSERVED (resolve_result.json): resolved=true, completed=true, note='resolved'. Both candidates RESOLVE -> correct echoes, NOT spec weaknesses (per docs/architecture.md §6 and the per-attack derivation in build_one.py).

SPEC-TOTALITY PROBE (why so little room exists): the frozen postconditions are P1 Implies(splits, Result()==take(split_point)), P2 Implies(splits, len(digit_run)>=1 and all_digits(digit_run)), P3 Implies(not splits, Result()==name). P1/P3 are keyed on complementary guards over a TOTAL precondition (Acc(list_pred(name),1/2)+MustTerminate admits any int list), so Result() is pinned on EVERY input. _specstrength.py over 300000 random code-point lists (incl. NUL, U+10FFFF, LS, NEL): 0 unpinned inputs, 0 inputs where the pinned value differs from the real gold function, 0 inputs where P1 fires but P2 is unsatisfiable. The only verifying impls are therefore behavioural echoes of the gold — consistent with both candidates resolving.

A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's). Ran the bundle's own check — `python axiom_check.py` -> EXIT=0, 'is_letter/is_digit classes + disjointness sound over 65792 code points; deep split model == real re recogniser on 51 boundary + 60000 fuzz names' — and then an INDEPENDENT re-derivation I wrote from scratch (_aleg.py), not a re-run of theirs:
  * B1 (A-consumed, the ONLY consumed kind-A fact: is_letter(c) => not is_digit(c)): holds over 68352 real code points (full BMP + U+1D400-1D7FF + U+1E900-1EDFF + U+10000-104FF + U+1FB00-1FFFF), a wider sweep than axiom_check.py's.
  * A2/A2b/A3/A5 (the deep model splits/split_point/digit_run == the real compiled patched regex's match/groups()): HOLDS over 200000 adversarial names on an alphabet deliberately including boundaries axiom_check.py OMITS — VT, FF, NEL(U+0085), LS(U+2028), PS(U+2029), NBSP, FS/GS/RS, and 'digit-looking' code points that are NOT \d (superscript ², roman Ⅰ, fraction ⅓, circled), plus full-width, Ethiopic and Adlam digits. Zero divergences: the $-anchor rule really does tolerate exactly one '\n' and nothing else, as mapping.md §3.2 claims.
  * A7/A5/A6 (the legs refinement.md declares I and does NOT model — subs.insert(0,sub) and the surrounding split_super_sub loop): checked END-TO-END against the REAL patched repo file (_a7.py loads sympy/printing/conventions.py at base_commit 82298df6 with the gold hunk applied, asserts _name_with_digits_p.pattern is the post-patch pattern). On 35077 separator-free names the real patched split_super_sub's (name, supers, subs) == (model bare name, [], [model digit_run] or []) with zero divergences. The unmodeled legs are genuinely identity.

REFINEMENT.MD LEG CLASSIFICATION: every leg is R / A-consumed / A-reference / I — NO kind-3. A1=R (str <-> List[int] of code points); A2=A-reference (greedy [^\W\d_]+ <-> num_leading_letters); A2b=A-reference ($ anchor <-> core_len, and correctly flagged UNCHANGED by the patch, so not the discriminator); A3=A-reference (\d+$ <-> all_digits over take(core_len)); A4=A-reference+I (match success <-> deep splits; the k>=1 / k<m conjunction control flow is identical); A5=R+A-reference (m.group(1)/(2) <-> take(split_point) / digit_run bounded by core_len not len); A6=I (no-match leaves name and subs untouched); A7=I (subs.insert, verified above). The one genuinely CHANGED operation (ASCII -> any-script recogniser) is modeled DEEPLY, not hidden behind a whole-callee axiom; the single A-consumed fact is the disjointness clause B1. §C's no-kind-3 claim checks out.

G-MUT SURVIVOR reviewed (not a G-EQ defect): 'line 226: < -> <=' sits in `if not (k >= 1 and k < m): Assert(not splits(...))`, a PROOF-ONLY hint line inside the impl region, not a behavioural branch — the behavioural guard is the `if k >= 1 and k < m:` on line 228. Weakening the hint's guard cannot change the returned value, which is why it survives; atk_v2_1's boundary perturbation covers the real off-by-one direction and is rejected.

Every attack fully verified and reported; no run left incomplete, no timeouts, so nothing is inconclusive.

VERDICT SOUND: 5 attributable same-spec wrong impls (atk_v2_1/2/3/5/6, zero proof debt, instrument-controlled) all REJECTED on postcondition P1; the prepatch bug reproduced and rejected; 10 further same-spec wrong impls also rejected; the positive control verifies (EXIT=0, 42.83s); both verifying candidates RESOLVE under the official harness. verify => correct upheld for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFUL — no diverging input found. I attacked the spec independently (fresh worktree at base_commit 82298df6a51 + gold patch applied; my own harness, not the bundle's conformance_check.py) and could not separate the modeled function from the real callee.

SPEC REGION INTEGRITY. `same-spec` on an unmodified copy of model.py returns exit 0 ("SAME"). I recomputed markers.region_hashes(model.py, NaginiBackend) directly: the shipped file hashes to spec_view=c8e120af..., pure=979f44e8..., post-conditions=3922e58f..., which is EXACTLY the 2026-08-14 G-HYGIENE snapshot in meta.json.

THE RECORDED UNFAITHFUL LABEL IS STALE — I did not inherit it. meta.json's *top-level* region_hashes (spec_view=3f844036..., pure=5fdb9498..., impl=246b60a9...) do NOT match the shipped file. That older hash set is the pre-repair revision that the recorded G-PANEL-2 (dated 2026-08-12, agent_verdict UNFAITHFUL) attacked. Every behavioural gate was re-run later, on 2026-08-14 (G-VERIFY, G-CONF, G-AX, G-GOLD, G-DIFF, G-RESOLVE, G-HYGIENE all pass). Re-asserting a retained label against a repaired artifact would be inventing spec weakness, so I re-derived the verdict from scratch. The prior witness is genuinely closed: the `core_len`/`digit_run` pair is present in the shipped pure region (core_len x10, digit_run x11, `take(core_len` x4) and the `m = n - 1` name-proper bound is in the impl.

WHAT I RAN. I transcribed the spec (core_len / num_leading_letters / all_digits / splits / split_point / digit_run + the four total postconditions) into an executable oracle and diffed it against the REAL patched `_name_with_digits_p.match(name).groups()` and, end-to-end, against the real consumer `split_super_sub`. is_letter/is_digit were evaluated by the real `re` engine on classes EXTRACTED at run time from the real patched pattern's own group bodies (`[^\W\d_]`, `\d` under re.U) — not hand-retyped. Pattern identity asserted == r'^([^\W\d_]+)(\d+)$'.

TOTAL ~2.2M inputs, 0 divergences:
  * 69,696 exhaustive single code points (0..0x11000 + astral math-digit block)
  * exhaustive len<=3 over a 27-char multi-script alphabet (20,440) and exhaustive len<=2 over a 91-char alphabet stratified across all 30 Unicode general categories (17,612)
  * 1,000,000+ seeded fuzz names len 3..12 over the stratified alphabets
  * 632,172 structured letters^i + digits^j + tail cases (10 letter scripts x 7 digit scripts x 13 tails incl. '\n', '\n\n', '\r', '\r\n', combining mark, ZWSP, NBSP, astral digit)
  * 8,568 line-boundary probes over every char Python might treat as a line break ('\n','\r','\x0b','\x0c','\x1c','\x1d','\x1e','\x85','
','
') in every position
  * 9,240 surrogate / astral / private-use / plane-14-tag probes
  * 30,043 end-to-end checks through the real `split_super_sub` (name/supers/subs triple, incl. subs[0] placement)

THE $-ANCHOR RULE — the exact prior failure locus — is now correct on the real engine: 'w1\n' -> ('w',[],['1']) (matches, LF in neither group), 'w1\n\n' -> unsplit, 'w1\r' -> unsplit, and the spec agrees on all three. 'omega1\n' also splits, so the repair did not disturb the ASCII->any-script discriminator. I probed the adjacent over-strip and under-strip errors ('w1 \n', 'w1\n ', 'w1\r\n', 'w1\x0b', 'w1\x0c', '
'/'
' tails) — the spec's "exactly one terminating LF, nothing else" matches the engine on every one. G-PBT independently rejects both neighbours (partial-domain-ignore-terminating-lf, partial-domain-strip-all-terminating-lf).

CONSUMED AXIOM (the only fact the proof uses) validated EXHAUSTIVELY, beyond the bundle's own ~65,792-point sweep: is_letter(c) => not is_digit(c) checked over ALL 1,114,112 Unicode code points — 132,372 letters, 650 decimal digits, 0 violations. Also confirmed the greedy-boundary assumption the deep model rests on (group1/group2 meet at the maximal leading letter run) over 200 letters x 120 digits, 0 mismatches. The axioms are A-reference with a deep model, so there is no over-strong whole-regex axiom to exploit: `splits`/`split_point` are spelled out as verified folds.

NOT-TOO-STRONG / DOMAIN NOT NARROWED: Requires is only Acc(list_pred(name),1/2) + MustTerminate(2), i.e. any int list, read-only — no precondition excludes the '\n' witness or any other input, so faithfulness is not being bought by narrowing the domain. The postconditions are total (splits and not-splits both pinned), so there is no unconstrained input where a verifying impl could drift.

Positive control: unmodified model.py verifies under the pinned verifier ("Verification successful", 35.8s).

RESIDUAL RISK (not a defect, disclosed): faithfulness is checked at the `name`-local boundary, so it inherits mapping.md's claim that the unchanged split_super_sub parsing loop is the identity on separator-free names — I confirmed that end-to-end but only for names free of '_','^','{','}'. Names containing separators exercise unpatched code outside the modeled region. Also, is_letter/is_digit extension is tied to the host CPython's Unicode database version; a different UCD build could in principle shift the letter/digit classes, though disjointness is a UCD invariant.

Work done entirely under /tmp; the bundle was read-only (the two modified files in git status are pre-existing from the 2026-08-14 regate, not mine). Worktree removed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacked the spec view of model.py (spec_view sha c8e120af813be3fd7c956851a00da06d38b55301a94f37a4734950ef7d5d1b92; SPEC_REGIONS = axioms, pure, pre-conditions, post-conditions + module docstring; impl region confirmed elided to '... # implementation elided'). Judged against problem_statement ONLY, never hints_text. NOTE the hints_text here is unusually explicit ('there is a regular expression in sympy/printing/conventions.py ... using [a-zA-Z] but it should be using \w') -- I deliberately excluded all of that from the baseline, so the bar was the much thinner public statement: title 'pprint unicode does not format subscripts on Greek letters' plus a Good/Bad block showing -t0*w0 subscripting correctly and -t0*w0 with Greek omega NOT subscripting.

MECHANICAL: leakage.screen() over spec_view -> passed=True, zero hard failures, zero warnings. Gold patch changes one file (sympy/printing/conventions.py, twice), changed lines = the two _name_with_digits_p regex lines plus the make->Make comment-capitalisation pair; distinctive changed symbol set = {split_super_sub}. L1 (no gold line reproduced, no diff markers), L2 (no patched file path 'sympy/printing/conventions.py', no dotted module path), L2/L5 (no spec-view identifier embeds 'split_super_sub'), L2/L3 (no comment names it), L3 (no bug/fix narration) all clean. Independent cross-check: parsed the real conventions.py at base_commit and intersected its identifiers (len>=4) with the spec view -- only generic English collisions 'name', 'part', 'start'; '_name_with_digits_p' and 'split_super_sub' absent.

INDEPENDENT TERM SCAN (not relying on the bundle's own claim): every edit-mechanism token is ABSENT from the spec view -- regex, regular expression, re.compile, re.U, pattern, compile, match(, groups(), capture, group, a-zA-Z, [0-9], \w, \d, ascii, anchor, subs.insert, conventions, sympy/. The view names no regex, no character-class syntax, no flag, no file, no symbol. The ASCII->Unicode discriminator lives only in mapping.md/refinement.md/axiom_check.py, which are NOT in the consumer view.

STRONGEST CANDIDATES, each tested and rejected:

(1) The 'script-agnostic' / 'a Greek-letter name with trailing digits is treated exactly like a Latin-letter one' / omega-plus-1 discriminating cases. This is the closest call, and it is the OBSERVABLE the public statement already ships: the Good/Bad pair IS 'Latin w0 subscripts, Greek omega-0 does not'. Restating the desired end-state behaviour is what a spec is for; it does not name the mechanism, the file, or the class syntax, so a solver still has to find the recogniser and choose how to widen it. No net information beyond problem_statement.

(2) is_letter's docstring gloss 'a word character that is neither a decimal digit nor the underscore' -- suspicious because it reads like a transcription of the post-patch class [^\W\d_]. Tested: the gloss is (a) fidelity-forced -- I evaluated it against the real class over code points 0..0x2FFF and found 0 mismatches, so any weaker wording would make the spec unfaithful; and (b) behaviourally load-bearing, not decorative -- if '_' were allowed to count as a letter, 'a_1'/'ab_12'/'a_b1'/'_1' would all split (('a_','1') etc.) where the real recogniser correctly refuses. A spec must pin that, and it pins it in behavioural terms (word char / not a digit / not underscore) rather than by quoting [^\W\d_]. Describing the class extension is not disclosing the edit: the pre-patch [a-zA-Z] also excluded '_' and digits, so this sentence does not even distinguish pre from post.

(3) The core_len / terminating-line-feed paragraph -- disclosure of a $-anchor subtlety a solver would not guess. Rejected as leakage because it is provably NOT part of the gold edit: I ran both patterns side by side on 'w1\n', 'w1\n\n', 'w1\r', 'w1\r\n', 'w\n1', 'w1' and pre and post agree on ALL six (identical groups or identical None). The $ anchor is byte-identical pre- and post-patch, so this paragraph localizes nothing about the change; it is spec completeness on an unchanged property. Consistent with refinement.md A2b/C.

(4) The consumed disjointness axiom is_letter(c) => not is_digit(c). Verified true of the real classes over 0..0x2FFF, and it holds of the pre-patch ASCII classes too -- an unchanged property, no discriminating content.

GOLD-RECONSTRUCTION TEST: from the spec view alone a solver learns 'split trailing decimal digits off a leading letter run, letters/digits in any script'. That is the requirement, restated from the public bug report. It does not reveal that the mechanism is a module-level compiled regex, which file or symbol holds it, that the fix is a character-class swap, or the specific replacement r'^([^\W\d_]+)(\d+)$' with re.U. A solver could satisfy this spec with an explicit str.isalpha/isdigit scan and never touch a regex. Notably the spec view is strictly LESS informative than the (excluded) hints_text, which hands over file + class + fix.

Also confirmed the spec view is not tailored to the F2P oracle: test_super_sub asserts any-script DIGITS too (w+MATHEMATICAL DOUBLE-STRUCK ONE, 'w12-with-double-struck', omega cases). The spec's 'trailing digits are recognised whatever script the digits come from' is required for conformance, and I verified the pre-patch regex fails exactly those (pre: False; post: ('w','double-struck 1')). Spec breadth matches oracle breadth -- no overfit, and no extra mechanism disclosed.

No LEAKAGE finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
