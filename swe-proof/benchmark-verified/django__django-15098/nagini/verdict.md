# P2 adversarial audit — django__django-15098

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.py`, `atk_2_budget3.py`, `atk_3_ascii_hardcode.py`, `atk_4_unicode_hardcode.py`, `atk_5_partial_domain.py`, `atk_6_no_final_newline.py`, `atk_7_multiline_dollar.py`, `atk_8_cfe_no_terminator.py`, `atk_9_offbyone_endsword.py`, `atk_11_no_adjacent.py`, `atk_12_vacuity_control.py`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 13 same-spec attacks run; the only CANDIDATE (atk_10_echo, the ungrounded-oracle echo `return prefix_len_spec(ToSeq(path), 2)`) is NOT a weakness: it is behaviourally IDENTICAL to the gold matcher (0 divergences over 1,535,892 probed paths incl. non-ASCII), its faithful refined patch is byte-identical to the gold patch.diff, and that patch RESOLVED under the official harness (completed=True resolved=True attempts=1 flaky=False). All 12 genuinely-wrong impls were REJECTED by the verifier.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -292,10 +292,10 @@
     Assert(len(ToSeq(path).drop(1)) == body_len)
     Assert(run_len(ToSeq(path).drop(1)) == rlen)
     Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
-    if tseps > 2:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
+    if tseps > 1:
+        # OLD behaviour: more than one separator is not a locale prefix.
+        return -1
+    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 1)
     # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
     # one level of the (non-recursive) spec body, expressed in the same
     # sub-calls the impl loops established.
@@ -304,8 +304,8 @@
     Assert(ToSeq(path)[0] == 47)
     Assert(run_len(ToSeq(path).drop(1)) == rlen)
     Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
-    spec_val = spec_unfold(ToSeq(path), 2, rlen)
-    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
+    spec_val = spec_unfold(ToSeq(path), 1, rlen)
+    Assert(prefix_len_spec(ToSeq(path), 1) == spec_val)
     # termination: end-of-body, the next character is "/", or a newline (10)
     # that is the final character of the path (Python-re `$` semantics).
     if rlen == body_len:
```

Attack 2 — `atk_2_budget3.py` → rejected (same spec, does not verify — good)

```diff
@@ -197,135 +197,5 @@
     Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
     # post-conditions-end
     # impl-start
-    n = len(path)
-    if n == 0:
-        Assert(len(ToSeq(path)) == 0)
-        return -1
-    Assert(ToSeq(path)[0] == path[0])
-    if path[0] != 47:
-        return -1
-    if n == 1:
-        # body == path.drop(1) is empty: no candidate run.
-        Assert(len(ToSeq(path).drop(1)) == 0)
-        Assert(run_len(ToSeq(path).drop(1)) == 0)
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # body == path.drop(1) has length n-1; scan it from the back,
-    # reconstructing run_len(body.drop(i)) over each suffix.
-    body_len = n - 1
-    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
-    i = body_len      # index into body == path.drop(1)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(body_len == n - 1)
-        Invariant(0 <= i and i <= body_len)
-        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
-        Invariant(0 <= rlen and rlen <= body_len - i)
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # body[i-1] == path[1 + (i-1)] == path[i]
-        c = path[i]
-        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
-        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
-               == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
-            rlen = rlen + 1
-        else:
-            rlen = 0
-        i = i - 1
-    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
-    Assert(rlen == run_len(ToSeq(path).drop(1)))
-    if rlen == 0:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # tag == body.take(rlen); check well-formedness + separator budget by a
-    # second backward pass over the tag.
-    Assert(rlen <= body_len)
-    Assert(ToSeq(path).drop(1).take(rlen)
-           == ToSeq(path).drop(1).take(rlen))
-    tseps = 0         # nsep over tag suffix
-    adj_ok = True     # no_adjacent_sep over tag suffix
-    j = rlen
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(rlen == run_len(ToSeq(path).drop(1)))
-        Invariant(0 <= j and j <= rlen)
-        Invariant(rlen <= n - 1)
-        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        # element body[j-1] == path[1 + (j-1)] == path[j]
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
-               == ToSeq(path).drop(1).take(rlen).drop(j))
-        c2 = path[j]
-        if is_sep(c2):
-            tseps = tseps + 1
-        # adjacency: body[j-1] and body[j] both seps?
-        if j < rlen:
-            if is_sep(c2) and is_sep(path[j + 1]):
-                adj_ok = False
-        j = j - 1
-    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
-           == ToSeq(path).drop(1).take(rlen))
-    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
-    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
-    # well-formedness: starts/ends with a word code point.
-    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
-    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
-    if not (starts_word and ends_word and adj_ok):
-        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-    # Bind the spec's internal facts: same body, same run length, well-formed,
-    # and the separator budget.
-    Assert(len(ToSeq(path).drop(1)) == body_len)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
-    if tseps > 2:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
-    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
-    # one level of the (non-recursive) spec body, expressed in the same
-    # sub-calls the impl loops established.
-    Assert(len(ToSeq(path)) > 0)
-    Assert(ToSeq(path)[0] == path[0])
-    Assert(ToSeq(path)[0] == 47)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
-    spec_val = spec_unfold(ToSeq(path), 2, rlen)
-    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
-    # termination: end-of-body, the next character is "/", or a newline (10)
-    # that is the final character of the path (Python-re `$` semantics).
-    if rlen == body_len:
-        Assert(rlen == len(ToSeq(path).drop(1)))
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(rlen < len(ToSeq(path).drop(1)))
-    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
-    if path[rlen + 1] == 47:
-        Assert(ToSeq(path).drop(1)[rlen] == 47)
-        Assert(spec_val == rlen)
-        return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
-        Assert(ToSeq(path).drop(1)[rlen] == 10)
-        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(ToSeq(path).drop(1)[rlen] != 47)
-    Assert(not (ToSeq(path).drop(1)[rlen] == 10
-                and rlen == len(ToSeq(path).drop(1)) - 1))
-    Assert(spec_val == -1)
-    return -1
+    return prefix_len_spec(ToSeq(path), 3)
     # impl-end
```

Attack 3 — `atk_3_ascii_hardcode.py` → rejected (same spec, does not verify — good)

```diff
@@ -231,7 +231,7 @@
         Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
         Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
                == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
+        if (((48 <= c and c <= 57) or (65 <= c and c <= 90) or (97 <= c and c <= 122) or c == 95) or c == 45 or c == 64):
             rlen = rlen + 1
         else:
             rlen = 0
@@ -280,8 +280,8 @@
     # well-formedness: starts/ends with a word code point.
     Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
     Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
+    starts_word = ((48 <= path[1] and path[1] <= 57) or (65 <= path[1] and path[1] <= 90) or (97 <= path[1] and path[1] <= 122) or path[1] == 95)
+    ends_word = ((48 <= path[rlen] and path[rlen] <= 57) or (65 <= path[rlen] and path[rlen] <= 90) or (97 <= path[rlen] and path[rlen] <= 122) or path[rlen] == 95)
     if not (starts_word and ends_word and adj_ok):
         Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
         Assert(prefix_len_spec(ToSeq(path), 2) == -1)
```

Attack 4 — `atk_4_unicode_hardcode.py` → rejected (same spec, does not verify — good)

```diff
@@ -231,7 +231,7 @@
         Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
         Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
                == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
+        if (is_tagchar(c) or c >= 128):
             rlen = rlen + 1
         else:
             rlen = 0
@@ -280,8 +280,8 @@
     # well-formedness: starts/ends with a word code point.
     Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
     Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
+    starts_word = (is_word(path[1]) or path[1] >= 128)
+    ends_word = (is_word(path[rlen]) or path[rlen] >= 128)
     if not (starts_word and ends_word and adj_ok):
         Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
         Assert(prefix_len_spec(ToSeq(path), 2) == -1)
```

Attack 5 — `atk_5_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -197,135 +197,7 @@
     Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
     # post-conditions-end
     # impl-start
-    n = len(path)
-    if n == 0:
-        Assert(len(ToSeq(path)) == 0)
-        return -1
-    Assert(ToSeq(path)[0] == path[0])
-    if path[0] != 47:
-        return -1
-    if n == 1:
-        # body == path.drop(1) is empty: no candidate run.
-        Assert(len(ToSeq(path).drop(1)) == 0)
-        Assert(run_len(ToSeq(path).drop(1)) == 0)
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # body == path.drop(1) has length n-1; scan it from the back,
-    # reconstructing run_len(body.drop(i)) over each suffix.
-    body_len = n - 1
-    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
-    i = body_len      # index into body == path.drop(1)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(body_len == n - 1)
-        Invariant(0 <= i and i <= body_len)
-        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
-        Invariant(0 <= rlen and rlen <= body_len - i)
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # body[i-1] == path[1 + (i-1)] == path[i]
-        c = path[i]
-        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
-        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
-               == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
-            rlen = rlen + 1
-        else:
-            rlen = 0
-        i = i - 1
-    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
-    Assert(rlen == run_len(ToSeq(path).drop(1)))
-    if rlen == 0:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # tag == body.take(rlen); check well-formedness + separator budget by a
-    # second backward pass over the tag.
-    Assert(rlen <= body_len)
-    Assert(ToSeq(path).drop(1).take(rlen)
-           == ToSeq(path).drop(1).take(rlen))
-    tseps = 0         # nsep over tag suffix
-    adj_ok = True     # no_adjacent_sep over tag suffix
-    j = rlen
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(rlen == run_len(ToSeq(path).drop(1)))
-        Invariant(0 <= j and j <= rlen)
-        Invariant(rlen <= n - 1)
-        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        # element body[j-1] == path[1 + (j-1)] == path[j]
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
-               == ToSeq(path).drop(1).take(rlen).drop(j))
-        c2 = path[j]
-        if is_sep(c2):
-            tseps = tseps + 1
-        # adjacency: body[j-1] and body[j] both seps?
-        if j < rlen:
-            if is_sep(c2) and is_sep(path[j + 1]):
-                adj_ok = False
-        j = j - 1
-    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
-           == ToSeq(path).drop(1).take(rlen))
-    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
-    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
-    # well-formedness: starts/ends with a word code point.
-    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
-    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
-    if not (starts_word and ends_word and adj_ok):
-        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-    # Bind the spec's internal facts: same body, same run length, well-formed,
-    # and the separator budget.
-    Assert(len(ToSeq(path).drop(1)) == body_len)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
-    if tseps > 2:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
-    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
-    # one level of the (non-recursive) spec body, expressed in the same
-    # sub-calls the impl loops established.
-    Assert(len(ToSeq(path)) > 0)
-    Assert(ToSeq(path)[0] == path[0])
-    Assert(ToSeq(path)[0] == 47)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
-    spec_val = spec_unfold(ToSeq(path), 2, rlen)
-    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
-    # termination: end-of-body, the next character is "/", or a newline (10)
-    # that is the final character of the path (Python-re `$` semantics).
-    if rlen == body_len:
-        Assert(rlen == len(ToSeq(path).drop(1)))
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(rlen < len(ToSeq(path).drop(1)))
-    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
-    if path[rlen + 1] == 47:
-        Assert(ToSeq(path).drop(1)[rlen] == 47)
-        Assert(spec_val == rlen)
-        return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
-        Assert(ToSeq(path).drop(1)[rlen] == 10)
-        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(ToSeq(path).drop(1)[rlen] != 47)
-    Assert(not (ToSeq(path).drop(1)[rlen] == 10
-                and rlen == len(ToSeq(path).drop(1)) - 1))
-    Assert(spec_val == -1)
+    if len(path) <= 6:
+        return prefix_len_spec(ToSeq(path), 2)
     return -1
     # impl-end
```

Attack 6 — `atk_6_no_final_newline.py` → rejected (same spec, does not verify — good)

```diff
@@ -318,11 +318,6 @@
         Assert(ToSeq(path).drop(1)[rlen] == 47)
         Assert(spec_val == rlen)
         return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
-        Assert(ToSeq(path).drop(1)[rlen] == 10)
-        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
-        Assert(spec_val == rlen)
-        return rlen
     Assert(ToSeq(path).drop(1)[rlen] != 47)
     Assert(not (ToSeq(path).drop(1)[rlen] == 10
                 and rlen == len(ToSeq(path).drop(1)) - 1))
```

Attack 7 — `atk_7_multiline_dollar.py` → rejected (same spec, does not verify — good)

```diff
@@ -318,7 +318,7 @@
         Assert(ToSeq(path).drop(1)[rlen] == 47)
         Assert(spec_val == rlen)
         return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
+    if path[rlen + 1] == 10:
         Assert(ToSeq(path).drop(1)[rlen] == 10)
         Assert(rlen == len(ToSeq(path).drop(1)) - 1)
         Assert(spec_val == rlen)
```

Attack 8 — `atk_8_cfe_no_terminator.py` → rejected (same spec, does not verify — good)

```diff
@@ -306,26 +306,5 @@
     Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
     spec_val = spec_unfold(ToSeq(path), 2, rlen)
     Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
-    # termination: end-of-body, the next character is "/", or a newline (10)
-    # that is the final character of the path (Python-re `$` semantics).
-    if rlen == body_len:
-        Assert(rlen == len(ToSeq(path).drop(1)))
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(rlen < len(ToSeq(path).drop(1)))
-    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
-    if path[rlen + 1] == 47:
-        Assert(ToSeq(path).drop(1)[rlen] == 47)
-        Assert(spec_val == rlen)
-        return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
-        Assert(ToSeq(path).drop(1)[rlen] == 10)
-        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(ToSeq(path).drop(1)[rlen] != 47)
-    Assert(not (ToSeq(path).drop(1)[rlen] == 10
-                and rlen == len(ToSeq(path).drop(1)) - 1))
-    Assert(spec_val == -1)
-    return -1
+    return rlen
     # impl-end
```

Attack 9 — `atk_9_offbyone_endsword.py` → rejected (same spec, does not verify — good)

```diff
@@ -281,7 +281,7 @@
     Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
     Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
     starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
+    ends_word = is_word(path[rlen - 1])
     if not (starts_word and ends_word and adj_ok):
         Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
         Assert(prefix_len_spec(ToSeq(path), 2) == -1)
```

Attack 10 — `atk_10_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -197,135 +197,5 @@
     Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
     # post-conditions-end
     # impl-start
-    n = len(path)
-    if n == 0:
-        Assert(len(ToSeq(path)) == 0)
-        return -1
-    Assert(ToSeq(path)[0] == path[0])
-    if path[0] != 47:
-        return -1
-    if n == 1:
-        # body == path.drop(1) is empty: no candidate run.
-        Assert(len(ToSeq(path).drop(1)) == 0)
-        Assert(run_len(ToSeq(path).drop(1)) == 0)
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # body == path.drop(1) has length n-1; scan it from the back,
-    # reconstructing run_len(body.drop(i)) over each suffix.
-    body_len = n - 1
-    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
-    i = body_len      # index into body == path.drop(1)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(body_len == n - 1)
-        Invariant(0 <= i and i <= body_len)
-        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
-        Invariant(0 <= rlen and rlen <= body_len - i)
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # body[i-1] == path[1 + (i-1)] == path[i]
-        c = path[i]
-        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
-        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
-               == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
-            rlen = rlen + 1
-        else:
-            rlen = 0
-        i = i - 1
-    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
-    Assert(rlen == run_len(ToSeq(path).drop(1)))
-    if rlen == 0:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    # tag == body.take(rlen); check well-formedness + separator budget by a
-    # second backward pass over the tag.
-    Assert(rlen <= body_len)
-    Assert(ToSeq(path).drop(1).take(rlen)
-           == ToSeq(path).drop(1).take(rlen))
-    tseps = 0         # nsep over tag suffix
-    adj_ok = True     # no_adjacent_sep over tag suffix
-    j = rlen
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(n == len(path))
-        Invariant(n >= 2 and path[0] == 47)
-        Invariant(rlen == run_len(ToSeq(path).drop(1)))
-        Invariant(0 <= j and j <= rlen)
-        Invariant(rlen <= n - 1)
-        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        # element body[j-1] == path[1 + (j-1)] == path[j]
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
-        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
-               == ToSeq(path).drop(1).take(rlen).drop(j))
-        c2 = path[j]
-        if is_sep(c2):
-            tseps = tseps + 1
-        # adjacency: body[j-1] and body[j] both seps?
-        if j < rlen:
-            if is_sep(c2) and is_sep(path[j + 1]):
-                adj_ok = False
-        j = j - 1
-    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
-           == ToSeq(path).drop(1).take(rlen))
-    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
-    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
-    # well-formedness: starts/ends with a word code point.
-    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
-    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
-    if not (starts_word and ends_word and adj_ok):
-        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
-    # Bind the spec's internal facts: same body, same run length, well-formed,
-    # and the separator budget.
-    Assert(len(ToSeq(path).drop(1)) == body_len)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
-    if tseps > 2:
-        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
-        return -1
-    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
-    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
-    # one level of the (non-recursive) spec body, expressed in the same
-    # sub-calls the impl loops established.
-    Assert(len(ToSeq(path)) > 0)
-    Assert(ToSeq(path)[0] == path[0])
-    Assert(ToSeq(path)[0] == 47)
-    Assert(run_len(ToSeq(path).drop(1)) == rlen)
-    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
-    spec_val = spec_unfold(ToSeq(path), 2, rlen)
-    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
-    # termination: end-of-body, the next character is "/", or a newline (10)
-    # that is the final character of the path (Python-re `$` semantics).
-    if rlen == body_len:
-        Assert(rlen == len(ToSeq(path).drop(1)))
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(rlen < len(ToSeq(path).drop(1)))
-    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
-    if path[rlen + 1] == 47:
-        Assert(ToSeq(path).drop(1)[rlen] == 47)
-        Assert(spec_val == rlen)
-        return rlen
-    if path[rlen + 1] == 10 and rlen == body_len - 1:
-        Assert(ToSeq(path).drop(1)[rlen] == 10)
-        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
-        Assert(spec_val == rlen)
-        return rlen
-    Assert(ToSeq(path).drop(1)[rlen] != 47)
-    Assert(not (ToSeq(path).drop(1)[rlen] == 10
-                and rlen == len(ToSeq(path).drop(1)) - 1))
-    Assert(spec_val == -1)
-    return -1
+    return prefix_len_spec(ToSeq(path), 2)
     # impl-end
```

Attack 11 — `atk_11_no_adjacent.py` → rejected (same spec, does not verify — good)

```diff
@@ -282,7 +282,7 @@
     Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
     starts_word = is_word(path[1])
     ends_word = is_word(path[rlen])
-    if not (starts_word and ends_word and adj_ok):
+    if not (starts_word and ends_word):
         Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
         Assert(prefix_len_spec(ToSeq(path), 2) == -1)
         return -1
```

Attack 12 — `atk_12_vacuity_control.py` → rejected (same spec, does not verify — good)

```diff
@@ -197,6 +197,7 @@
     Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
     # post-conditions-end
     # impl-start
+    Assert(False)
     n = len(path)
     if n == 0:
         Assert(len(ToSeq(path)) == 0)
```

Attack 13 — `atk_13_piecewise_open.py` → rejected (same spec, does not verify — good)

```diff
@@ -231,7 +231,7 @@
         Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
         Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
                == ToSeq(path).drop(1).drop(i))
-        if is_tagchar(c):
+        if (is_tagchar(c) or c >= 256):
             rlen = rlen + 1
         else:
             rlen = 0
@@ -280,8 +280,8 @@
     # well-formedness: starts/ends with a word code point.
     Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
     Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
-    starts_word = is_word(path[1])
-    ends_word = is_word(path[rlen])
+    starts_word = (is_word(path[1]) or path[1] >= 256)
+    ends_word = (is_word(path[rlen]) or path[rlen] >= 256)
     if not (starts_word and ends_word and adj_ok):
         Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
         Assert(prefix_len_spec(ToSeq(path), 2) == -1)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15098.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a request path is inspected for a leading locale prefix, the locale
  candidate is the run of characters that immediately follows the leading
  ``"/"`` and that is built only from "word" code points joined by the two
  permitted sub-tag separators ``"-"`` and ``"@"``. Following the language-tag
  grammar of RFC 5646, such a candidate is

      language ["-" script] ["-" region]

  i.e. a primary sub-tag optionally followed by up to TWO further sub-tags,
  each separator immediately followed by a non-empty word run (so a sub-tag is
  never empty and the candidate neither begins nor ends with a separator). The
  candidate is accepted as a locale prefix iff:

    * the path begins with ``"/"``;
    * the candidate run is a well-formed sequence of word sub-tags joined by
      single separators (non-empty; starts and ends with a word code point; no
      two adjacent separators);
    * it contains AT MOST TWO separators (a primary sub-tag plus at most a
      script and a region sub-tag); and
    * the character immediately after the candidate run is the path separator
      ``"/"``, the end of the path, or a newline that is the LAST character of
      the path (Python-``re`` ``$`` semantics: ``$`` matches at end-of-string
      and also immediately before a newline at the very end of the string).

  When accepted, the extracted locale candidate is exactly that run (its length
  is returned); otherwise there is no locale prefix (``-1`` is returned). In
  particular a candidate carrying both a script and a region sub-tag (three
  word sub-tags, two separators) IS a locale prefix, whereas a longer run with
  three or more separators is NOT.

Paths are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
acceptance/extraction rule above is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates over ONE axiomatized primitive: membership of a single code
point in the "word" character class. That membership test is an unchanged
callee, pinned exactly below code point 128 and left OPEN over the rest of
Unicode, so the extraction rule is claimed for EVERY class the axiom permits
and never for an ASCII-only reading of it. The rule's equality to the real
compiled prefix matcher is checked out-of-band by axiom_check.py (G-AX).

The downstream resolution of the extracted candidate against the configured
locales is an UNCHANGED callee and is documented in mapping.md / refinement.md;
it is not part of the modelled, changed operation (the extraction is).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_word(c: int) -> bool:
    """Membership of ONE code point in the "word" character class that a locale
    sub-tag's characters are drawn from. This per-code-point class test is an
    UNCHANGED community callee; its provenance and its executable soundness
    check live in mapping.md / axiom_check.py.

    The class is pinned EXACTLY below code point 128: there it is the decimal
    digits, the two cased Latin letter runs, and the low line — and NOTHING
    else below 128 belongs to it (not the space, not the path separator, not a
    sub-tag separator, not a newline, not any other punctuation mark). At and
    above 128 the class is deliberately left OPEN: the real class is evaluated
    over the whole of Unicode, so exactly which further letters and digits it
    admits is the callee's business and is NOT something this specification
    decides. An implementation must therefore agree with the extraction rule
    below for EVERY class this contract permits, rather than for one chosen
    reading of it."""
    Ensures(Implies(c < 128, Result() == ((48 <= c and c <= 57)      # 0-9
                                          or (65 <= c and c <= 90)   # A-Z
                                          or (97 <= c and c <= 122)  # a-z
                                          or c == 95)))              # _
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A sub-tag separator: ``"-"`` (45) or ``"@"`` (64)."""
    return c == 45 or c == 64


@Pure
def is_tagchar(c: int) -> bool:
    """A character that may appear inside a locale candidate run: a word code
    point or a sub-tag separator."""
    return is_word(c) or is_sep(c)


@Pure
def run_len(s: PSeq[int]) -> int:
    """Length of the maximal leading run of candidate characters (word or
    separator). Front-recursive: one unfold per step. The candidate run starts
    at the front of ``s`` and stops at the first character that may not appear
    in a locale candidate (e.g. ``"/"`` or any other punctuation)."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if not is_tagchar(s[0]):
        return 0
    return 1 + run_len(s.drop(1))


@Pure
def nsep(s: PSeq[int]) -> int:
    """Number of sub-tag separators in ``s``. Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (1 if is_sep(s[0]) else 0) + nsep(s.drop(1))


@Pure
def no_adjacent_sep(s: PSeq[int]) -> bool:
    """No two adjacent separators in ``s`` (every separator is immediately
    followed by another character that is not a separator). Front-recursive."""
    if len(s) <= 1:
        return True
    return not (is_sep(s[0]) and is_sep(s[1])) and no_adjacent_sep(s.drop(1))


@Pure
def well_formed_tag(t: PSeq[int]) -> bool:
    """``t`` is a well-formed sequence of word sub-tags joined by single
    separators: non-empty, begins and ends with a word code point, and has no
    two adjacent separators. (``t`` is assumed to consist only of candidate
    characters; the caller guarantees this via ``run_len``.)"""
    return (len(t) > 0
            and is_word(t[0])
            and is_word(t[len(t) - 1])
            and no_adjacent_sep(t))


@Pure
def spec_unfold(path: PSeq[int], maxsep: int, r: int) -> int:
    """One-level body of the locale-prefix decision, with the candidate run
    length ``r`` supplied explicitly (``r == run_len(path.drop(1))``). Given the
    path begins with ``"/"``, the candidate of length ``r`` is accepted iff it
    is non-empty, a well-formed tag, within the separator budget, and terminated
    by ``"/"``, end-of-path, or a trailing FINAL newline (Python-``re`` ``$``);
    the accepted length is ``r`` else ``-1``."""
    Requires(0 <= r and r <= len(path) - 1 if len(path) >= 1 else True)
    Ensures(Result() == -1 or Result() == r)
    body = path.drop(1)
    if r == 0:
        return -1
    tag = body.take(r)
    if not well_formed_tag(tag):
        return -1
    if nsep(tag) > maxsep:
        return -1
    # termination: end of path, the next character is "/", or the next
    # character is a newline (10) that is the LAST character of the path
    # (Python-re `$` also matches just before a trailing final newline).
    if r == len(body):
        return r
    if body[r] == 47:
        return r
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1


@Pure
def prefix_len_spec(path: PSeq[int], maxsep: int) -> int:
    """Length of the accepted locale candidate at the front of ``path`` under a
    separator budget ``maxsep``, or ``-1`` when there is no acceptable locale
    prefix. The path must begin with ``"/"`` (47); the candidate is the maximal
    run after it (``run_len``); it must be a well-formed tag with at most
    ``maxsep`` separators; and the run must be terminated by ``"/"`` (47),
    end-of-path, or a newline (10) that is the path's final character
    (Python-``re`` ``$``)."""
    Ensures(Result() == -1 or Result() >= 1)
    if len(path) == 0 or path[0] != 47:
        return -1
    return spec_unfold(path, maxsep, run_len(path.drop(1)))
# pure-end


def language_prefix_len(path: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The extracted locale-prefix length is exactly the deep structural parse
    # with a budget of TWO sub-tag separators (primary + script + region).
    Ensures(Result() == prefix_len_spec(ToSeq(path), 2))
    # Grounding: either no prefix (-1), or a positive length within the path.
    Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
    # post-conditions-end
    # impl-start
    n = len(path)
    if n == 0:
        Assert(len(ToSeq(path)) == 0)
        return -1
    Assert(ToSeq(path)[0] == path[0])
    if path[0] != 47:
        return -1
    if n == 1:
        # body == path.drop(1) is empty: no candidate run.
        Assert(len(ToSeq(path).drop(1)) == 0)
        Assert(run_len(ToSeq(path).drop(1)) == 0)
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # body == path.drop(1) has length n-1; scan it from the back,
    # reconstructing run_len(body.drop(i)) over each suffix.
    body_len = n - 1
    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
    i = body_len      # index into body == path.drop(1)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(body_len == n - 1)
        Invariant(0 <= i and i <= body_len)
        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
        Invariant(0 <= rlen and rlen <= body_len - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # body[i-1] == path[1 + (i-1)] == path[i]
        c = path[i]
        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
               == ToSeq(path).drop(1).drop(i))
        if is_tagchar(c):
            rlen = rlen + 1
        else:
            rlen = 0
        i = i - 1
    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
    Assert(rlen == run_len(ToSeq(path).drop(1)))
    if rlen == 0:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # tag == body.take(rlen); check well-formedness + separator budget by a
    # second backward pass over the tag.
    Assert(rlen <= body_len)
    Assert(ToSeq(path).drop(1).take(rlen)
           == ToSeq(path).drop(1).take(rlen))
    tseps = 0         # nsep over tag suffix
    adj_ok = True     # no_adjacent_sep over tag suffix
    j = rlen
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(rlen == run_len(ToSeq(path).drop(1)))
        Invariant(0 <= j and j <= rlen)
        Invariant(rlen <= n - 1)
        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        # element body[j-1] == path[1 + (j-1)] == path[j]
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
               == ToSeq(path).drop(1).take(rlen).drop(j))
        c2 = path[j]
        if is_sep(c2):
            tseps = tseps + 1
        # adjacency: body[j-1] and body[j] both seps?
        if j < rlen:
            if is_sep(c2) and is_sep(path[j + 1]):
                adj_ok = False
        j = j - 1
    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
           == ToSeq(path).drop(1).take(rlen))
    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
    # well-formedness: starts/ends with a word code point.
    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
    starts_word = is_word(path[1])
    ends_word = is_word(path[rlen])
    if not (starts_word and ends_word and adj_ok):
        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
    # Bind the spec's internal facts: same body, same run length, well-formed,
    # and the separator budget.
    Assert(len(ToSeq(path).drop(1)) == body_len)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
    if tseps > 2:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
    # one level of the (non-recursive) spec body, expressed in the same
    # sub-calls the impl loops established.
    Assert(len(ToSeq(path)) > 0)
    Assert(ToSeq(path)[0] == path[0])
    Assert(ToSeq(path)[0] == 47)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
    spec_val = spec_unfold(ToSeq(path), 2, rlen)
    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
    # termination: end-of-body, the next character is "/", or a newline (10)
    # that is the final character of the path (Python-re `$` semantics).
    if rlen == body_len:
        Assert(rlen == len(ToSeq(path).drop(1)))
        Assert(spec_val == rlen)
        return rlen
    Assert(rlen < len(ToSeq(path).drop(1)))
    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
    if path[rlen + 1] == 47:
        Assert(ToSeq(path).drop(1)[rlen] == 47)
        Assert(spec_val == rlen)
        return rlen
    if path[rlen + 1] == 10 and rlen == body_len - 1:
        Assert(ToSeq(path).drop(1)[rlen] == 10)
        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
        Assert(spec_val == rlen)
        return rlen
    Assert(ToSeq(path).drop(1)[rlen] != 47)
    Assert(not (ToSeq(path).drop(1)[rlen] == 10
                and rlen == len(ToSeq(path).drop(1)) - 1))
    Assert(spec_val == -1)
    return -1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP. Every attack built by copying model.py and editing ONLY the impl region; `same-spec` exit 0 ("SAME — attack shares the bundle's exact specification") for all 13 attacks AND the positive control.

POSITIVE CONTROL. pos_control.py (= model.py verbatim) -> `weakness` exit 0, CANDIDATE: shares spec AND verifies (55.7s). The obligation is live.

VACUITY CONTROL. atk_12_vacuity_control.py (impl region prefixed with `Assert(False)`) -> exit 2, "attack does not verify". The proof is NOT vacuous, so the 12 rejections below are meaningful rather than an artifact of an infeasible path.

PER-ATTACK RESULTS. Command for each: `python -m swebench_unified.adversary weakness nagini django__django-15098 <path>` (logs <name>.out). Behavioural wrongness of each was independently confirmed by re-executing the attack's impl semantics against the REAL gold matcher (witness.py) — every attack has a concrete divergence witness, so none is a strawman.
- atk_1_prepatch.py PREPATCH BUG (model_prepatch.py verbatim; budget 1 <=> the old `?`). exit 2 REJECTED => prepatch reproduced and sensed. Witnesses: /en-latn-us/ -1 vs gold 10, /en-Latn-US/, /de-ch-1901/, /nan-hani-tw/ — exactly the F2P additions (8 total).
- atk_2_budget3.py budget 3. exit 2 REJECTED. Witness: /de-simple-page-test/ -> 19 vs gold -1 (the F2P `None` case).
- atk_3_ascii_hardcode.py A-LEG ATTACK: hardcodes the axiom's OPEN region (cp>=128) as NON-word, i.e. transcribes `\w` as the ASCII enumeration instead of routing through `is_word`. exit 2 REJECTED. Witnesses: /en-é/ -1 vs 4, /é/, /en-é-us/ (5). This is the sharpest A-consumed attack and the spec kills it.
- atk_4_unicode_hardcode.py DUAL A-LEG ATTACK: hardcodes cp>=128 as WORD. exit 2 REJECTED. Witness: /en×/ -> 3 vs gold -1 (× is a non-word cp above 128).
- atk_13_piecewise_open.py A-LEG ATTACK, piecewise: decides the open region as 128..255 per-axiom but >=256 as WORD. exit 2 REJECTED. 24 witnesses (e.g. /en‐/ -> 3 vs gold -1). Together atk_3/atk_4/atk_13 confirm the openness above 128 is genuinely load-bearing: NO reading of the open region may be baked in, in EITHER direction or piecewise.
- atk_5_partial_domain.py PARTIAL-DOMAIN: echoes the spec only for len(path)<=6, -1 otherwise. exit 2 REJECTED — the postcondition is total over `Acc(list_pred(path),1/2)`. 16 witnesses.
- atk_6_no_final_newline.py drops the trailing-FINAL-newline acceptance (Python-re `$`). exit 2 REJECTED. Witnesses: '/en\n' -1 vs gold 2, '/en@gb\n'.
- atk_7_multiline_dollar.py BOUNDARY, other direction: `$` misread as re.MULTILINE (ANY newline terminates). exit 2 REJECTED. Witnesses: '/en\nx' 2 vs -1, '/en\n\n'. With atk_6 this pins A5 tight in BOTH directions on the subtlest edge in the spec.
- atk_8_cfe_no_terminator.py CONTROL-FLOW-EFFECT: whole terminator block deleted, `return rlen` unconditionally. exit 2 REJECTED. Witnesses: /en.html -> 2 vs -1, '/en\nx', /de-simple-page-test/.
- atk_9_offbyone_endsword.py BOUNDARY off-by-one: ends_word read at path[rlen-1]. exit 2 REJECTED. Witnesses: '/a-/' 2 vs -1, /en-é/, /中-文/.
- atk_11_no_adjacent.py drops the no-adjacent-separator conjunct. exit 2 REJECTED. Witness: /a--b/ -> 4 vs gold -1.
- atk_10_echo.py UNGROUNDED-ORACLE ECHO: impl region = `return prefix_len_spec(ToSeq(path), 2)`. exit 0 **CANDIDATE** (shares spec AND verifies) — necessarily so, since the postcondition IS that equality.

MANDATORY RESOLVE RUN (the one CANDIDATE). Materialized its faithful refined patch at patch_atk_10_echo.diff. The echo's impl IS `prefix_len_spec(.,2)`, whose A-reference is the compiled matcher r'^/(\w+([@-]\w+){0,2})(/|$)' — validated by G-AX and re-derived independently by me (below) — so the faithful materialization is exactly that regex; `diff` against benchmark-verified/django__django-15098/patch.diff reports IDENTICAL. Executed via swebench_unified.harness.run_resolve("django__django-15098", patch, run_id="sbu-geq-audit-7u8kg8sc-atk10echo", timeout=3600) -> **completed=True resolved=True attempts=1 flaky=False, note="resolved"**. So the only verifying rival RESOLVES: no verify=>incorrect witness. Note this echo cannot in principle break G-EQ here, because the A-reference (deep model == real matcher) is checked with `is_word` instantiated at the REAL Unicode \w over the whole input domain, with no excluded region.

A-LEG AUDIT (refinement.md). 8 legs, tags: 2 R (A1 str<->List[int]; A6 Result()=group-1 length, -1 <=> no-match <=> None), 1 A-consumed (A0 `is_word`), 4 A-reference (A2 `^/`; A3 group-1 structure = run_len+well_formed_tag; A4 the `{0,2}` bound = `nsep(tag)<=2`; A5 trailing `(/|$)`), 1 I (A7 the UNCHANGED downstream get_supported_language_variant, by composition). Untagged/kind-3 rows: 0. Exactly ONE @ContractOnly in model.py (`is_word`) and it is the per-code-point class test the patch does NOT touch — the operation that genuinely changed (the repeat bound) is modelled DEEPLY, never hidden behind an axiom about the function under change.

A-LEG CORRESPONDENCE RE-DERIVED INDEPENDENTLY (not by trusting the bundle or axiom_check.py). I transcribed prefix_len_spec/run_len/nsep/no_adjacent_sep/well_formed_tag/spec_unfold from model.py's pure region into plain Python myself (indep_corr.py) with is_word := re.compile(r'\w').fullmatch (the REAL Unicode class), and diffed it against BOTH real compiled matchers over: exhaustive strings of length<=5 on a 14-char class-complete alphabet "a1_-@/.\n\ré中×\t ", plus exhaustive length 6-7 on "a-@/\né×", plus a code-point sweep of 0..0x3FF / CJK / general-punct / fullwidth / Arabic-Indic / math-alnum in 11 locale-shaped templates (966 word + 442 non-word cps), plus the F2P corpus verbatim. TOTAL 1,535,892 inputs, **0 divergences** for spec(.,2) vs the post-patch matcher AND 0 for spec(.,1) vs the pre-patch r'^/(\w+([@-]\w+)?)(/|$)'. A3/A4/A5 therefore correspond exactly to the real callee, in both the accept and reject directions, on both sides of the 128 boundary. The bundle's own G-AX agrees: `python axiom_check.py` -> pinned half SOUND (exhaustive cp 0..127), open half SOUND and NON-VACUOUS (15 member / 14 non-member probes above 128), checked=175156 failures=0, SOUND, exit 0.

NO OUT-OF-DOMAIN REGION. Unlike a narrower ASCII-only reading, this bundle consumes the class as an axiom pinned below 128 and OPEN at/above 128, so non-ASCII paths are ordinary in-domain probed inputs rather than a documented gap; there is no `Requires` bounding path[k]. atk_3/atk_4/atk_13 are the machine-checked proof that the openness is enforced rather than decorative. There is consequently no ASCII escape hatch through which a verifying-but-wrong impl could slip.

VERDICT: SOUND. 13 same-spec attacks executed (>=5 required; distinct families: prepatch, budget, 3x axiom-open-region/A-leg, partial-domain, 2x boundary/`$`-semantics, control-flow-effect, off-by-one, well-formedness, ungrounded-oracle echo, vacuity control). 12 rejected by the verifier with confirmed divergence witnesses; the sole CANDIDATE's materialized faithful patch RESOLVED under the official harness. Positive control verifies, vacuity control does not, prepatch reproduced and sensed, no timeouts or infra gaps. No verify=>incorrect witness exists at this attack depth.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.py`, `atk_2_budget3.py`, `atk_3_ascii_hardcode.py`, `atk_4_unicode_hardcode.py`, `atk_5_partial_domain.py`, `atk_6_no_final_newline.py`, `atk_7_multiline_dollar.py`, `atk_8_cfe_no_terminator.py`, `atk_9_offbyone_endsword.py`, `atk_11_no_adjacent.py`, `atk_12_vacuity_control.py`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 13 same-spec attacks run; the only CANDIDATE (atk_10_echo, the ungrounded-oracle echo `return prefix_len_spec(ToSeq(path), 2)`) is NOT a weakness: it is behaviourally IDENTICAL to the gold matcher (0 divergences over 1,535,892 probed paths incl. non-ASCII), its faithful refined patch is byte-identical to the gold patch.diff, and that patch RESOLVED under the official harness (completed=True resolved=True attempts=1 flaky=False). All 12 genuinely-wrong impls were REJECTED by the verifier.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_budget3.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ascii_hardcode.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_unicode_hardcode.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_no_final_newline.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_multiline_dollar.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_cfe_no_terminator.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_offbyone_endsword.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_no_adjacent.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_vacuity_control.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_piecewise_open.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15098.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a request path is inspected for a leading locale prefix, the locale
  candidate is the run of characters that immediately follows the leading
  ``"/"`` and that is built only from "word" code points joined by the two
  permitted sub-tag separators ``"-"`` and ``"@"``. Following the language-tag
  grammar of RFC 5646, such a candidate is

      language ["-" script] ["-" region]

  i.e. a primary sub-tag optionally followed by up to TWO further sub-tags,
  each separator immediately followed by a non-empty word run (so a sub-tag is
  never empty and the candidate neither begins nor ends with a separator). The
  candidate is accepted as a locale prefix iff:

    * the path begins with ``"/"``;
    * the candidate run is a well-formed sequence of word sub-tags joined by
      single separators (non-empty; starts and ends with a word code point; no
      two adjacent separators);
    * it contains AT MOST TWO separators (a primary sub-tag plus at most a
      script and a region sub-tag); and
    * the character immediately after the candidate run is the path separator
      ``"/"``, the end of the path, or a newline that is the LAST character of
      the path (Python-``re`` ``$`` semantics: ``$`` matches at end-of-string
      and also immediately before a newline at the very end of the string).

  When accepted, the extracted locale candidate is exactly that run (its length
  is returned); otherwise there is no locale prefix (``-1`` is returned). In
  particular a candidate carrying both a script and a region sub-tag (three
  word sub-tags, two separators) IS a locale prefix, whereas a longer run with
  three or more separators is NOT.

Paths are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
acceptance/extraction rule above is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates over ONE axiomatized primitive: membership of a single code
point in the "word" character class. That membership test is an unchanged
callee, pinned exactly below code point 128 and left OPEN over the rest of
Unicode, so the extraction rule is claimed for EVERY class the axiom permits
and never for an ASCII-only reading of it. The rule's equality to the real
compiled prefix matcher is checked out-of-band by axiom_check.py (G-AX).

The downstream resolution of the extracted candidate against the configured
locales is an UNCHANGED callee and is documented in mapping.md / refinement.md;
it is not part of the modelled, changed operation (the extraction is).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_word(c: int) -> bool:
    """Membership of ONE code point in the "word" character class that a locale
    sub-tag's characters are drawn from. This per-code-point class test is an
    UNCHANGED community callee; its provenance and its executable soundness
    check live in mapping.md / axiom_check.py.

    The class is pinned EXACTLY below code point 128: there it is the decimal
    digits, the two cased Latin letter runs, and the low line — and NOTHING
    else below 128 belongs to it (not the space, not the path separator, not a
    sub-tag separator, not a newline, not any other punctuation mark). At and
    above 128 the class is deliberately left OPEN: the real class is evaluated
    over the whole of Unicode, so exactly which further letters and digits it
    admits is the callee's business and is NOT something this specification
    decides. An implementation must therefore agree with the extraction rule
    below for EVERY class this contract permits, rather than for one chosen
    reading of it."""
    Ensures(Implies(c < 128, Result() == ((48 <= c and c <= 57)      # 0-9
                                          or (65 <= c and c <= 90)   # A-Z
                                          or (97 <= c and c <= 122)  # a-z
                                          or c == 95)))              # _
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A sub-tag separator: ``"-"`` (45) or ``"@"`` (64)."""
    return c == 45 or c == 64


@Pure
def is_tagchar(c: int) -> bool:
    """A character that may appear inside a locale candidate run: a word code
    point or a sub-tag separator."""
    return is_word(c) or is_sep(c)


@Pure
def run_len(s: PSeq[int]) -> int:
    """Length of the maximal leading run of candidate characters (word or
    separator). Front-recursive: one unfold per step. The candidate run starts
    at the front of ``s`` and stops at the first character that may not appear
    in a locale candidate (e.g. ``"/"`` or any other punctuation)."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if not is_tagchar(s[0]):
        return 0
    return 1 + run_len(s.drop(1))


@Pure
def nsep(s: PSeq[int]) -> int:
    """Number of sub-tag separators in ``s``. Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (1 if is_sep(s[0]) else 0) + nsep(s.drop(1))


@Pure
def no_adjacent_sep(s: PSeq[int]) -> bool:
    """No two adjacent separators in ``s`` (every separator is immediately
    followed by another character that is not a separator). Front-recursive."""
    if len(s) <= 1:
        return True
    return not (is_sep(s[0]) and is_sep(s[1])) and no_adjacent_sep(s.drop(1))


@Pure
def well_formed_tag(t: PSeq[int]) -> bool:
    """``t`` is a well-formed sequence of word sub-tags joined by single
    separators: non-empty, begins and ends with a word code point, and has no
    two adjacent separators. (``t`` is assumed to consist only of candidate
    characters; the caller guarantees this via ``run_len``.)"""
    return (len(t) > 0
            and is_word(t[0])
            and is_word(t[len(t) - 1])
            and no_adjacent_sep(t))


@Pure
def spec_unfold(path: PSeq[int], maxsep: int, r: int) -> int:
    """One-level body of the locale-prefix decision, with the candidate run
    length ``r`` supplied explicitly (``r == run_len(path.drop(1))``). Given the
    path begins with ``"/"``, the candidate of length ``r`` is accepted iff it
    is non-empty, a well-formed tag, within the separator budget, and terminated
    by ``"/"``, end-of-path, or a trailing FINAL newline (Python-``re`` ``$``);
    the accepted length is ``r`` else ``-1``."""
    Requires(0 <= r and r <= len(path) - 1 if len(path) >= 1 else True)
    Ensures(Result() == -1 or Result() == r)
    body = path.drop(1)
    if r == 0:
        return -1
    tag = body.take(r)
    if not well_formed_tag(tag):
        return -1
    if nsep(tag) > maxsep:
        return -1
    # termination: end of path, the next character is "/", or the next
    # character is a newline (10) that is the LAST character of the path
    # (Python-re `$` also matches just before a trailing final newline).
    if r == len(body):
        return r
    if body[r] == 47:
        return r
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1


@Pure
def prefix_len_spec(path: PSeq[int], maxsep: int) -> int:
    """Length of the accepted locale candidate at the front of ``path`` under a
    separator budget ``maxsep``, or ``-1`` when there is no acceptable locale
    prefix. The path must begin with ``"/"`` (47); the candidate is the maximal
    run after it (``run_len``); it must be a well-formed tag with at most
    ``maxsep`` separators; and the run must be terminated by ``"/"`` (47),
    end-of-path, or a newline (10) that is the path's final character
    (Python-``re`` ``$``)."""
    Ensures(Result() == -1 or Result() >= 1)
    if len(path) == 0 or path[0] != 47:
        return -1
    return spec_unfold(path, maxsep, run_len(path.drop(1)))
# pure-end


def language_prefix_len(path: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The extracted locale-prefix length is exactly the deep structural parse
    # with a budget of TWO sub-tag separators (primary + script + region).
    Ensures(Result() == prefix_len_spec(ToSeq(path), 2))
    # Grounding: either no prefix (-1), or a positive length within the path.
    Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
    # post-conditions-end
    # impl-start
    n = len(path)
    if n == 0:
        Assert(len(ToSeq(path)) == 0)
        return -1
    Assert(ToSeq(path)[0] == path[0])
    if path[0] != 47:
        return -1
    if n == 1:
        # body == path.drop(1) is empty: no candidate run.
        Assert(len(ToSeq(path).drop(1)) == 0)
        Assert(run_len(ToSeq(path).drop(1)) == 0)
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # body == path.drop(1) has length n-1; scan it from the back,
    # reconstructing run_len(body.drop(i)) over each suffix.
    body_len = n - 1
    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
    i = body_len      # index into body == path.drop(1)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(body_len == n - 1)
        Invariant(0 <= i and i <= body_len)
        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
        Invariant(0 <= rlen and rlen <= body_len - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # body[i-1] == path[1 + (i-1)] == path[i]
        c = path[i]
        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
               == ToSeq(path).drop(1).drop(i))
        if is_tagchar(c):
            rlen = rlen + 1
        else:
            rlen = 0
        i = i - 1
    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
    Assert(rlen == run_len(ToSeq(path).drop(1)))
    if rlen == 0:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # tag == body.take(rlen); check well-formedness + separator budget by a
    # second backward pass over the tag.
    Assert(rlen <= body_len)
    Assert(ToSeq(path).drop(1).take(rlen)
           == ToSeq(path).drop(1).take(rlen))
    tseps = 0         # nsep over tag suffix
    adj_ok = True     # no_adjacent_sep over tag suffix
    j = rlen
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(rlen == run_len(ToSeq(path).drop(1)))
        Invariant(0 <= j and j <= rlen)
        Invariant(rlen <= n - 1)
        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        # element body[j-1] == path[1 + (j-1)] == path[j]
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
               == ToSeq(path).drop(1).take(rlen).drop(j))
        c2 = path[j]
        if is_sep(c2):
            tseps = tseps + 1
        # adjacency: body[j-1] and body[j] both seps?
        if j < rlen:
            if is_sep(c2) and is_sep(path[j + 1]):
                adj_ok = False
        j = j - 1
    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
           == ToSeq(path).drop(1).take(rlen))
    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
    # well-formedness: starts/ends with a word code point.
    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
    starts_word = is_word(path[1])
    ends_word = is_word(path[rlen])
    if not (starts_word and ends_word and adj_ok):
        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
    # Bind the spec's internal facts: same body, same run length, well-formed,
    # and the separator budget.
    Assert(len(ToSeq(path).drop(1)) == body_len)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
    if tseps > 2:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
    # one level of the (non-recursive) spec body, expressed in the same
    # sub-calls the impl loops established.
    Assert(len(ToSeq(path)) > 0)
    Assert(ToSeq(path)[0] == path[0])
    Assert(ToSeq(path)[0] == 47)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
    spec_val = spec_unfold(ToSeq(path), 2, rlen)
    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
    # termination: end-of-body, the next character is "/", or a newline (10)
    # that is the final character of the path (Python-re `$` semantics).
    if rlen == body_len:
        Assert(rlen == len(ToSeq(path).drop(1)))
        Assert(spec_val == rlen)
        return rlen
    Assert(rlen < len(ToSeq(path).drop(1)))
    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
    if path[rlen + 1] == 47:
        Assert(ToSeq(path).drop(1)[rlen] == 47)
        Assert(spec_val == rlen)
        return rlen
    if path[rlen + 1] == 10 and rlen == body_len - 1:
        Assert(ToSeq(path).drop(1)[rlen] == 10)
        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
        Assert(spec_val == rlen)
        return rlen
    Assert(ToSeq(path).drop(1)[rlen] != 47)
    Assert(not (ToSeq(path).drop(1)[rlen] == 10
                and rlen == len(ToSeq(path).drop(1)) - 1))
    Assert(spec_val == -1)
    return -1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP. Every attack built by copying model.py and editing ONLY the impl region; `same-spec` exit 0 ("SAME — attack shares the bundle's exact specification") for all 13 attacks AND the positive control.

POSITIVE CONTROL. pos_control.py (= model.py verbatim) -> `weakness` exit 0, CANDIDATE: shares spec AND verifies (55.7s). The obligation is live.

VACUITY CONTROL. atk_12_vacuity_control.py (impl region prefixed with `Assert(False)`) -> exit 2, "attack does not verify". The proof is NOT vacuous, so the 12 rejections below are meaningful rather than an artifact of an infeasible path.

PER-ATTACK RESULTS. Command for each: `python -m swebench_unified.adversary weakness nagini django__django-15098 <path>` (logs <name>.out). Behavioural wrongness of each was independently confirmed by re-executing the attack's impl semantics against the REAL gold matcher (witness.py) — every attack has a concrete divergence witness, so none is a strawman.
- atk_1_prepatch.py PREPATCH BUG (model_prepatch.py verbatim; budget 1 <=> the old `?`). exit 2 REJECTED => prepatch reproduced and sensed. Witnesses: /en-latn-us/ -1 vs gold 10, /en-Latn-US/, /de-ch-1901/, /nan-hani-tw/ — exactly the F2P additions (8 total).
- atk_2_budget3.py budget 3. exit 2 REJECTED. Witness: /de-simple-page-test/ -> 19 vs gold -1 (the F2P `None` case).
- atk_3_ascii_hardcode.py A-LEG ATTACK: hardcodes the axiom's OPEN region (cp>=128) as NON-word, i.e. transcribes `\w` as the ASCII enumeration instead of routing through `is_word`. exit 2 REJECTED. Witnesses: /en-é/ -1 vs 4, /é/, /en-é-us/ (5). This is the sharpest A-consumed attack and the spec kills it.
- atk_4_unicode_hardcode.py DUAL A-LEG ATTACK: hardcodes cp>=128 as WORD. exit 2 REJECTED. Witness: /en×/ -> 3 vs gold -1 (× is a non-word cp above 128).
- atk_13_piecewise_open.py A-LEG ATTACK, piecewise: decides the open region as 128..255 per-axiom but >=256 as WORD. exit 2 REJECTED. 24 witnesses (e.g. /en‐/ -> 3 vs gold -1). Together atk_3/atk_4/atk_13 confirm the openness above 128 is genuinely load-bearing: NO reading of the open region may be baked in, in EITHER direction or piecewise.
- atk_5_partial_domain.py PARTIAL-DOMAIN: echoes the spec only for len(path)<=6, -1 otherwise. exit 2 REJECTED — the postcondition is total over `Acc(list_pred(path),1/2)`. 16 witnesses.
- atk_6_no_final_newline.py drops the trailing-FINAL-newline acceptance (Python-re `$`). exit 2 REJECTED. Witnesses: '/en\n' -1 vs gold 2, '/en@gb\n'.
- atk_7_multiline_dollar.py BOUNDARY, other direction: `$` misread as re.MULTILINE (ANY newline terminates). exit 2 REJECTED. Witnesses: '/en\nx' 2 vs -1, '/en\n\n'. With atk_6 this pins A5 tight in BOTH directions on the subtlest edge in the spec.
- atk_8_cfe_no_terminator.py CONTROL-FLOW-EFFECT: whole terminator block deleted, `return rlen` unconditionally. exit 2 REJECTED. Witnesses: /en.html -> 2 vs -1, '/en\nx', /de-simple-page-test/.
- atk_9_offbyone_endsword.py BOUNDARY off-by-one: ends_word read at path[rlen-1]. exit 2 REJECTED. Witnesses: '/a-/' 2 vs -1, /en-é/, /中-文/.
- atk_11_no_adjacent.py drops the no-adjacent-separator conjunct. exit 2 REJECTED. Witness: /a--b/ -> 4 vs gold -1.
- atk_10_echo.py UNGROUNDED-ORACLE ECHO: impl region = `return prefix_len_spec(ToSeq(path), 2)`. exit 0 **CANDIDATE** (shares spec AND verifies) — necessarily so, since the postcondition IS that equality.

MANDATORY RESOLVE RUN (the one CANDIDATE). Materialized its faithful refined patch at patch_atk_10_echo.diff. The echo's impl IS `prefix_len_spec(.,2)`, whose A-reference is the compiled matcher r'^/(\w+([@-]\w+){0,2})(/|$)' — validated by G-AX and re-derived independently by me (below) — so the faithful materialization is exactly that regex; `diff` against benchmark-verified/django__django-15098/patch.diff reports IDENTICAL. Executed via swebench_unified.harness.run_resolve("django__django-15098", patch, run_id="sbu-geq-audit-7u8kg8sc-atk10echo", timeout=3600) -> **completed=True resolved=True attempts=1 flaky=False, note="resolved"**. So the only verifying rival RESOLVES: no verify=>incorrect witness. Note this echo cannot in principle break G-EQ here, because the A-reference (deep model == real matcher) is checked with `is_word` instantiated at the REAL Unicode \w over the whole input domain, with no excluded region.

A-LEG AUDIT (refinement.md). 8 legs, tags: 2 R (A1 str<->List[int]; A6 Result()=group-1 length, -1 <=> no-match <=> None), 1 A-consumed (A0 `is_word`), 4 A-reference (A2 `^/`; A3 group-1 structure = run_len+well_formed_tag; A4 the `{0,2}` bound = `nsep(tag)<=2`; A5 trailing `(/|$)`), 1 I (A7 the UNCHANGED downstream get_supported_language_variant, by composition). Untagged/kind-3 rows: 0. Exactly ONE @ContractOnly in model.py (`is_word`) and it is the per-code-point class test the patch does NOT touch — the operation that genuinely changed (the repeat bound) is modelled DEEPLY, never hidden behind an axiom about the function under change.

A-LEG CORRESPONDENCE RE-DERIVED INDEPENDENTLY (not by trusting the bundle or axiom_check.py). I transcribed prefix_len_spec/run_len/nsep/no_adjacent_sep/well_formed_tag/spec_unfold from model.py's pure region into plain Python myself (indep_corr.py) with is_word := re.compile(r'\w').fullmatch (the REAL Unicode class), and diffed it against BOTH real compiled matchers over: exhaustive strings of length<=5 on a 14-char class-complete alphabet "a1_-@/.\n\ré中×\t ", plus exhaustive length 6-7 on "a-@/\né×", plus a code-point sweep of 0..0x3FF / CJK / general-punct / fullwidth / Arabic-Indic / math-alnum in 11 locale-shaped templates (966 word + 442 non-word cps), plus the F2P corpus verbatim. TOTAL 1,535,892 inputs, **0 divergences** for spec(.,2) vs the post-patch matcher AND 0 for spec(.,1) vs the pre-patch r'^/(\w+([@-]\w+)?)(/|$)'. A3/A4/A5 therefore correspond exactly to the real callee, in both the accept and reject directions, on both sides of the 128 boundary. The bundle's own G-AX agrees: `python axiom_check.py` -> pinned half SOUND (exhaustive cp 0..127), open half SOUND and NON-VACUOUS (15 member / 14 non-member probes above 128), checked=175156 failures=0, SOUND, exit 0.

NO OUT-OF-DOMAIN REGION. Unlike a narrower ASCII-only reading, this bundle consumes the class as an axiom pinned below 128 and OPEN at/above 128, so non-ASCII paths are ordinary in-domain probed inputs rather than a documented gap; there is no `Requires` bounding path[k]. atk_3/atk_4/atk_13 are the machine-checked proof that the openness is enforced rather than decorative. There is consequently no ASCII escape hatch through which a verifying-but-wrong impl could slip.

VERDICT: SOUND. 13 same-spec attacks executed (>=5 required; distinct families: prepatch, budget, 3x axiom-open-region/A-leg, partial-domain, 2x boundary/`$`-semantics, control-flow-effect, off-by-one, well-formedness, ungrounded-oracle echo, vacuity control). 12 rejected by the verifier with confirmed divergence witnesses; the sole CANDIDATE's materialized faithful patch RESOLVED under the official harness. Positive control verifies, vacuity control does not, prepatch reproduced and sensed, no timeouts or infra gaps. No verify=>incorrect witness exists at this attack depth.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE SETUP. Fresh worktree from the upstream repository at base_commit 2c7846d992 with patch.diff APPLIED (per instructions: the patched tree is the reference for the modelled function). Confirmed post-patch matcher: `^/(\w+([@-]\w+){0,2})(/|$)`, plus the anti-vacuity guard RE.match('/en-latn-us/').group(1)=='en-latn-us' (which the pre-patch `?` bound cannot produce).

METHOD (deliberately NOT reusing the bundle's shadow). I hand-transcribed model.py's frozen spec region (pure-start..pure-end: run_len, nsep, no_adjacent_sep, well_formed_tag, spec_unfold, prefix_len_spec) into an independent Python module from the source text, with the is_word axiom instantiated at its REAL counterpart re.compile(r'\w').fullmatch -- so the axiom is EXERCISED, not assumed, and an ASCII-enumeration reading would be caught. Oracle is the imported patched compiled regex CALLED exactly as trans_real.py:508/:511 does (mo=RE.match(path); len(mo[1]) else -1); no pattern text hardcoded. Confirmed same-spec exit 0 on the bundle model, so the spec region I transcribed is the frozen one.

RESULT: ~6.3 MILLION inputs, ZERO divergences.
- Hand/boundary corpus (44): all F2P shapes, empty, '/', '//', no-leading-slash, adjacent/leading/trailing separators, the `$` trailing-final-newline family ('/en\n', '/en\n\n', '/en\nx', '/en\r\n', '/\n'), 300-char run. 0 div.
- Exhaustive len<=4 over a 16-char class-complete alphabet straddling cp128 (a 1 _ - @ / . \n é 中 × \r \t · ٠ ǅ): 0 div.
- Per-code-point sweep, ~2.6k code points across 12 Unicode blocks x 13 locale-shaped templates: 0 div.
- Exhaustive len 5-8 over minimal/2-sep alphabets: 0 div.
- 700k adversarial fuzz incl. surrogates (D800/DFFF), astral (10FFFF, 1D400, 1F600), NBSP, ZWSP, U+2028/2029, U+0085, Arabic-Indic digit, superscripts: 0 div.
- Long/positional: separator injected at every position of runs len 1-24, subtag counts 0-11 x both separators x 5 tails: 0 div.

### Load-bearing claims independently confirmed
1. GREEDY MAXIMALITY -- the spec's strongest structural assumption is that group(1) is always the MAXIMAL leading word/sep run (run_len), i.e. that regex backtracking can never make a SHORTER prefix match succeed. Tested directly as a separate assertion over 5,242,880 EXHAUSTIVE strings of length 9-10 across four backtracking-dense alphabets ('a-/\n','a-@/','a@-\n','a1-@'): 0 divergences AND 0 maximality violations. Sound because \w and [@-] are disjoint, so a backtracked shorter group(1) always leaves a separator (never '/' or $) at the terminator position.
2. AXIOM PINNED HALF -- re-derived independently: real \w == the axiom's enumeration (0-9|A-Z|a-z|_) on ALL 128 code points 0..127, 0 mismatches. Open half above 128 is genuinely two-sided (members from 170, non-members from 128), so the contract is non-vacuous and permits the real Unicode class; the spec is correctly OPEN there rather than over-strong.
3. PRE-PATCH DIRECTION (not over-claiming) -- prefix_len_spec(.,1) == the real OLD matcher `^/(\w+([@-]\w+)?)(/|$)` on 222,621 inputs, 0 div. So maxsep is a faithful proxy for the repeat bound in BOTH directions; the maxsep=2 postcondition is exactly the patched behavior, not a stronger invention.
4. UNCHANGED-CALLEE SCOPE -- grepped the patched worktree: language_code_prefix_re has exactly ONE consumer, trans_real.py:508 inside get_language_from_path. mapping.md §2 / refinement.md A7 are accurate; get_supported_language_variant is untouched by patch.diff, so treating it as an I-step composition is correct and does not hide a delta.
5. COMPOSITION / CONTENT BRIDGE -- booted real Django with the F2P LANGUAGES and checked the R-refinement end to end: prefix_len_spec==-1 <=> get_language_from_path returns None, and group(1)==path[1:1+len] on every accepted input. 0 divergences. Length-vs-content bridge holds.
6. REAL TESTS -- applied instance test_patch: i18n.tests.MiscTests 13/13 OK, including both F2P (test_get_language_from_path_real, test_get_supported_language_variant_null). NOTE: without the test patch the base file's stale assertion assertIsNone(g('/de-simple-page/')) fails on the patched tree -- that is the expected pre/post delta the test patch replaces with '/de-simple-page-test/', NOT a spec defect.
7. Bundle axiom_check.py reproduced independently in my lab: exit 0, 175,156 paths, 0 failures.

### Subtleties I tried to break and could not
- The Python-re `$` semantics (matches at end-of-string AND before a single trailing final newline) are modelled exactly by `body[r]==10 and r==len(body)-1`. Probed '/en\n' (both give 2), '/en\n\n' (both -1), '/en\nx' (-1), '/en\r\n' (-1), '/a-\n', '/\n\n'. Dropping or widening this clause is what would diverge; the spec has it right, neither too strong nor too weak.
- No Requires bounds path[k], so there is NO excluded domain to hide a divergence in; non-ASCII and surrogate code points are ordinary in-domain inputs and I probed them heavily.
- spec_unfold's Requires is trivially satisfied at the only call site (r==run_len(body)<=len(body)), so it is not a hidden domain restriction.

CONCLUSION: I found no input on which the modelled function disagrees with the real patched callee. The spec is neither too strong nor drifting: its one @ContractOnly axiom is a partial contract the real Unicode \w class provably satisfies (pinned <128, open >=128), the changed operation (the {0,2} repeat bound) is modelled DEEPLY rather than axiomatized, and the deep model matches the real matcher in both the post-patch (maxsep=2) and pre-patch (maxsep=1) instantiations. FAITHFUL -- no diverging input to cite. This is an attacker's failure to break, not a rubber stamp: the 5.2M-input exhaustive maximality probe and the two-sided pre/post-patch check were designed specifically to expose over-strong structural readings and found none.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC VIEW AUDITED: markers.spec_view(model.py, nagini) = 201 lines (module docstring + axioms + pure + pre/post-conditions; impl elided). model.py sha256 d2ad8ce6172aa70ae7c953b0472d2b0271adb617bb61ef359f8789567dbe2772 == meta.json gates.G-LEAK.sources.model.py, so I audited the artifact the gate scored. Judged against the SOLVER-VISIBLE problem_statement ONLY (test.jsonl row); hints_text excluded per role.

VIEW IDENTITY CONFIRMED AGAINST WHAT EVAL ACTUALLY SHIPS (did not assume): built the real consumer task via eval.dataset.build_task(get_adapter('nagini'), ...) for modes 1 and 2, as_dict + assert_no_leak both clean. Shipped spec_view sha256 = 49288054a724c0c2... == meta.json region_hashes.spec_view AND byte-identical to the view I audited. Consumer keys are exactly {instance_id, repo, base_commit, mode, backend, problem_statement, localization, changed_files, spec_view, modeled_functions} — no patch/test_patch/FAIL_TO_PASS.

GOLD EDIT ISOLATED (what must not leak). The hunk's ENTIRE payload is one token in django/utils/translation/trans_real.py:46:
  pre  (base_commit 2c7846d99, read from the upstream repository): ^/(\w+([@-]\w+)?)(/|$)
  post (gold):                                                     ^/(\w+([@-]\w+){0,2})(/|$)
  delta: '?' -> '{0,2}'  <- the ONLY secret token.

1) MECHANICAL SCREEN RE-RUN MYSELF (not trusting meta.json): leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Independently reproduces the recorded 'spec view clean'.

2) L1 (reproduced gold line): both gold changed lines normalized-absent from the normalized view. Probed 40+ edit/test artifacts, ALL ABSENT: '{0,2}', '0,2', 'language_code_prefix_re', 'trans_real', '_lazy_re_compile', 'lazy_re', 'django/utils', 'get_language_from_path', 'get_supported_language_variant', 're.compile', 'regex', 'IGNORECASE', 'quantifier', '^/', '(/|$)', '[@-]', '\w+'. No diff markers ('@@', 'diff --git', '+++ ', '--- ', 'index '). Patched file path absent.

3) CAVEAT I CHECKED RATHER THAN ASSUMED — the automated L2/L5 symbol check was VACUOUS here: the gold hunk is a module-level ASSIGNMENT defining no def/class, so _patch_changed_symbols(gold)==set() and _patch_new_symbols(gold)==set(). I therefore did it by hand: extracted all 33 spec-view identifiers and intersected with the token set of the real trans_real.py at base_commit. Only {body, int, len, path, r, s, t} collide — generic single letters, builtins, and a local name; none is edit-localizing. 'r' collides with the gold line only as Python's raw-string prefix r'...', a lexer coincidence carrying no localization.

4) NARRATION (L3): regex scan for the full _NARRATION vocabulary over every view line returned ZERO matches. The two raw substring hits are innocuous morphology, not narration: 'fix' only inside 'prefix'/'prefix_len_spec' (12 sites), and 'old ' only inside 'unfold ' at L99. 'unchanged'/'UNCHANGED' at L39/L46/L62 describe callees deliberately OUTSIDE the modelled operation (the \w class test, the downstream locale resolution) — that is scope-fencing, and it points AWAY from the edit rather than at it.

5) THE ONE REAL QUESTION — does 'AT MOST TWO separators' hand over the gold edit? I concluded NO, because that bound is exactly what the PUBLIC problem_statement demands. The issue quotes the RFC 5646 langtag grammar verbatim, including 'langtag = language ["-" script] ["-" region]', names RFC 5646 by number, and states that /en-latn-us/ and /en-Latn-US/ (three sub-tags, two separators) MUST return 200. A solver reading only the issue derives 'primary + optional script + optional region' = at most two separators with no access to the patch. The view states this as DESIRED BEHAVIOUR ('stated as desired behaviour, not as an edit', L3) in the vocabulary of the public RFC grammar (L13, L22-L23, L32-L33, L194), never as a regex bound. Restating the public requirement is the spec's job; it is not leakage.

6) PRE-PATCH STATE IS NOT REVEALED — the discriminating check for 'does the view let a consumer read off the edit'. The view nowhere discloses the OLD budget of one separator: ', 1)', 'maxsep, 1)', 'budget of ONE', 'one separator', 'exactly one', 'only one', 'single sub-tag', 'previously', 'used to', 'formerly', 'no longer', 'now ' — ALL ABSENT. The view describes only the target behaviour, so it cannot be diffed against a stated prior behaviour to recover '? -> {0,2}'.

7) Strongest candidate leak I considered and REJECTED: prefix_len_spec/spec_unfold take a 'maxsep' PARAMETER rather than hardcoding the bound, which one could argue whispers 'the edit changed a bound'. Rejected because (a) the post-condition pins the consumer to the single concrete call prefix_len_spec(ToSeq(path), 2) and the value 1 appears nowhere, (b) parameterization is ordinary modeling reuse (G-DIFF instantiates the prepatch twin at 1, out-of-band and not consumer-visible), and (c) even granting the whisper, 'the acceptable number of sub-tags increased' is precisely the public issue's thesis — no information beyond problem_statement.

8) ELISION SOUND: parse_regions ok=True, regions {axioms:1, pure:1, pre-conditions:1, post-conditions:1, invariants:2, impl:1}. The impl region (src lines 199-331, 132 lines incl. the Assert/loop/Invariant machinery) collapses to the 3-line placeholder at view L199-L201. Impl body absent verbatim; no distinctive impl line survives; 'Invariant(', 'while ', 'range(' all absent from the view. (A naive substring pass flagged seven bare 'return -1' lines — I traced each to the PURE spec helpers run_len/spec_unfold/prefix_len_spec, which are spec-constituting and pass through by design, not impl survival.) spec_view is idempotent.

9) NOT A FINDING, recorded for completeness: the docstring cites axiom_check.py / mapping.md / refinement.md (L43, L46, L63). Those bundle files are not shipped in modes 1/2 and naming them discloses no edit content. Separately, the co-shipped 'localization'/'modeled_functions' fields DO name language_code_prefix_re and trans_real.py:46 — but that is modes 0/1/2/100's deliberate edit-localization input, not the spec view, and even it withholds the '{0,2}' payload.

CONCLUSION: the secret is a single regex quantifier token. It is absent from the view, as is the pre-patch state needed to infer it, as is every patched symbol and file path. Everything the view does state about the two-separator bound is independently derivable from the public RFC 5646 grammar and the en-latn-us examples in problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
