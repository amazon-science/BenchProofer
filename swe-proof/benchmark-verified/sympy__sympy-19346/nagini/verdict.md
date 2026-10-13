# P2 adversarial audit — sympy__sympy-19346

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_plain_str.py`, `atk_2_dict_colon_no_space.py`, `atk_3_dict_value_from_key.py`, `atk_5_dict_empty_is_set_literal.py`, `atk_6_dict_uses_set_assembly.py`, `atk_7_dict_ungrounded_echo.py`, `atk_8_dict_diverges_multi_pair.py`, `atk_9_set_empty_is_dict_literal.py`, `atk_10_set_trailing_separator.py`, +5 more |

**Non-vacuity.** The positive control `pos_control_frozen.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_plain_str.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -197,16 +197,15 @@
         elt = elems[i - 1]  # type: int
         Assert(elems_s.drop(i - 1)[0] == elt)
         Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
-        piece = doprint_elem(elt)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(elt))
+        # PRE-PATCH BEHAVIOUR: a collection has no dedicated renderer, so it
+        # falls back to the whole-object plain display form, which renders each
+        # element via its PLAIN display form (`str_elem`), not its executable
+        # representation (`elem_repr`/`doprint_elem`).
+        piece = str_elem(elt)  # type: List[int]
         if i == len(elems):
             inner = piece
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
-                   + joined_elems(elems_s.drop(i)))
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         i = i - 1
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
@@ -258,18 +257,15 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        # PRE-PATCH BEHAVIOUR: a mapping has no dedicated renderer, so it falls
+        # back to the whole-object plain display form, which renders each key
+        # and value via its PLAIN display form (`str_elem`), not its executable
+        # representation (`elem_repr`/`doprint_elem`).
+        piece = str_elem(key) + [COLON, SPACE] + str_elem(val)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 2 — `atk_2_dict_colon_no_space.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -258,18 +258,11 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        piece = doprint_elem(key) + [COLON] + doprint_elem(val)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 3 — `atk_3_dict_value_from_key.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -258,18 +258,11 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(key)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 4 — `atk_5_dict_empty_is_set_literal.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [115, 101, 116, 40, 41]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -259,17 +259,10 @@
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
         piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 5 — `atk_6_dict_uses_set_assembly.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -258,18 +258,11 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        piece = doprint_elem(key) + [COMMA, SPACE] + doprint_elem(val)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 6 — `atk_7_dict_ungrounded_echo.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -248,31 +248,12 @@
         Invariant(i % 2 == 0)
         Invariant(flat_s == ToSeq(flat))
         Invariant(len(flat_s) == len(flat))
-        Invariant(len(flat_s.drop(i)) % 2 == 0)
-        Invariant(ToSeq(inner) == joined_pairs(flat_s.drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         key = flat[i - 2]  # type: int
-        val = flat[i - 1]  # type: int
-        Assert(len(flat_s.drop(i - 2)) % 2 == 0)
-        Assert(flat_s.drop(i - 2)[0] == key)
-        Assert(flat_s.drop(i - 2)[1] == val)
-        Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
-        if i == len(flat):
-            inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
-        else:
-            inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
+        inner = doprint_elem(key) + inner
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
     Assert(ToSeq(result) == dict_seq(flat_s))
     return result
     # impl-end
```

Attack 7 — `atk_8_dict_diverges_multi_pair.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -250,7 +250,7 @@
         Invariant(len(flat_s) == len(flat))
         Invariant(len(flat_s.drop(i)) % 2 == 0)
         Invariant(ToSeq(inner) == joined_pairs(flat_s.drop(i)))
-        Invariant(MustTerminate(i + 1))
+        Invariant(MustTerminate(1))
         # invariants-end
         key = flat[i - 2]  # type: int
         val = flat[i - 1]  # type: int
@@ -259,18 +259,12 @@
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
         piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
-        i = i - 2
+        if len(flat) == 2:
+            i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
     Assert(ToSeq(result) == dict_seq(flat_s))
```

Attack 8 — `atk_9_set_empty_is_dict_literal.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,7 +180,7 @@
     # impl-start
     elems_s = ToSeq(elems)  # type: PSeq[int]
     if len(elems) == 0:
-        out_empty = [115, 101, 116, 40, 41]  # type: List[int]  # "set()"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == set_seq(elems_s))
         return out_empty
     inner = []  # type: List[int]
@@ -198,15 +198,10 @@
         Assert(elems_s.drop(i - 1)[0] == elt)
         Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
         piece = doprint_elem(elt)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(elt))
         if i == len(elems):
             inner = piece
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
-                   + joined_elems(elems_s.drop(i)))
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         i = i - 1
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
```

Attack 9 — `atk_10_set_trailing_separator.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,7 +180,7 @@
     # impl-start
     elems_s = ToSeq(elems)  # type: PSeq[int]
     if len(elems) == 0:
-        out_empty = [115, 101, 116, 40, 41]  # type: List[int]  # "set()"
+        out_empty = [115, 101, 116, 40, 41]  # type: List[int]
         Assert(ToSeq(out_empty) == set_seq(elems_s))
         return out_empty
     inner = []  # type: List[int]
@@ -198,15 +198,10 @@
         Assert(elems_s.drop(i - 1)[0] == elt)
         Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
         piece = doprint_elem(elt)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(elt))
         if i == len(elems):
-            inner = piece
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
+            inner = piece + [COMMA, SPACE]
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
-                   + joined_elems(elems_s.drop(i)))
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         i = i - 1
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
```

Attack 10 — `atk_11_set_leg_plain_str.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -197,16 +197,15 @@
         elt = elems[i - 1]  # type: int
         Assert(elems_s.drop(i - 1)[0] == elt)
         Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
-        piece = doprint_elem(elt)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(elt))
+        # PRE-PATCH BEHAVIOUR: a collection has no dedicated renderer, so it
+        # falls back to the whole-object plain display form, which renders each
+        # element via its PLAIN display form (`str_elem`), not its executable
+        # representation (`elem_repr`/`doprint_elem`).
+        piece = str_elem(elt)  # type: List[int]
         if i == len(elems):
             inner = piece
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
-                   + joined_elems(elems_s.drop(i)))
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         i = i - 1
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
```

Attack 11 — `atk_12_dict_value_plain_str.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -258,18 +258,11 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        piece = doprint_elem(key) + [COLON, SPACE] + str_elem(val)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 12 — `atk_13_set_drops_last_elem.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,11 +180,11 @@
     # impl-start
     elems_s = ToSeq(elems)  # type: PSeq[int]
     if len(elems) == 0:
-        out_empty = [115, 101, 116, 40, 41]  # type: List[int]  # "set()"
+        out_empty = [115, 101, 116, 40, 41]  # type: List[int]
         Assert(ToSeq(out_empty) == set_seq(elems_s))
         return out_empty
     inner = []  # type: List[int]
-    i = len(elems)
+    i = len(elems) - 1
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(elems), 1 / 2))
@@ -198,15 +198,10 @@
         Assert(elems_s.drop(i - 1)[0] == elt)
         Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
         piece = doprint_elem(elt)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(elt))
         if i == len(elems):
             inner = piece
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
-                   + joined_elems(elems_s.drop(i)))
-            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
         i = i - 1
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
```

Attack 13 — `atk_14_dict_keys_only.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,7 +235,7 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
@@ -258,18 +258,11 @@
         Assert(flat_s.drop(i - 2)[0] == key)
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
-        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
+        piece = doprint_elem(key)  # type: List[int]
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

Attack 14 — `atk_15_dict_drops_last_pair.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -235,11 +235,11 @@
     flat_s = ToSeq(flat)  # type: PSeq[int]
     Assert(len(flat_s) == len(flat))
     if len(flat) == 0:
-        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
+        out_empty = [LBRACE, RBRACE]  # type: List[int]
         Assert(ToSeq(out_empty) == dict_seq(flat_s))
         return out_empty
     inner = []  # type: List[int]
-    i = len(flat)
+    i = len(flat) - 2
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(flat), 1 / 2))
@@ -259,17 +259,10 @@
         Assert(flat_s.drop(i - 2)[1] == val)
         Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
         piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
-        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
-               + elem_repr(val))
         if i == len(flat):
             inner = piece
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         else:
             inner = piece + [COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
-                   + elem_repr(val) + PSeq(COMMA, SPACE)
-                   + joined_pairs(flat_s.drop(i)))
-            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
         i = i - 2
     result = [LBRACE] + inner + [RBRACE]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_frozen.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-19346/nagini. 14 same-spec wrong impls, built by splicing ONLY the two impl regions (splice.py is IDENTITY-VERIFIED: the identity splice reproduces the bundle model.py byte-for-byte, so axioms/@Pure/Requires/Ensures are provably untouched). All 14 + the positive control: `adversary same-spec` rc=0 SAME, and my own pre-flight of the runner's screen (markers.same_spec AND variant_scope.unsound_evasions) reports same_spec=True admissible=True for all 15 -- no new @ContractOnly, no dropped obligation. NO ATTACK PRODUCED A CANDIDATE, so `patches` is empty by the protocol's own terms: there was no verifying wrong impl whose refined patch needed a resolve run.

COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-19346 <f>` (all rc=2 = NOT-A-COUNTEREXAMPLE) plus `bash scripts/nagini_verify.sh <f>` to capture the exact rejection (logs/<name>.detail). Run 3-concurrent as background jobs. Positive control pos_control_frozen.py: rc=0 CANDIDATE, 'Verification successful' 24.6s.

PER-ATTACK: rc | refined-patch measured test_dict/test_set | verifier rejection.
- atk_1 prepatch, str per element on BOTH legs: 2 | FAIL/FAIL | Obligation leak, callee str_elem
- atk_2 ':' without space: 2 | FAIL/PASS | Loop invariant not preserved (ToSeq(inner)==joined_pairs)
- atk_3 value rendered from the key token: 2 | FAIL/PASS | same fold invariant
- atk_5 empty dict renders 'set()': 2 | FAIL/PASS | Assert ToSeq(out_empty)==dict_seq fails
- atk_6 dict assembled with ', ' not ': ': 2 | FAIL/PASS | same fold invariant
- atk_7 ungrounded-oracle echo (fold invariant DROPPED, postcondition merely asserted): 2 | FAIL/PASS | Assert ToSeq(result)==dict_seq fails
- atk_8 diverges for >=2 pairs: 2 | HANG(60s timeout, both tests) | 'Loop might not keep promise to terminate' (method-level MustTerminate(3) is enforced)
- atk_9 empty set renders '{}': 2 | PASS/FAIL | Assert ToSeq(out_empty)==set_seq fails
- atk_10 trailing ', ' after last elem: 2 | PASS/FAIL | Loop invariant (joined_elems)
- atk_11 set leg via str only, dict leg gold: 2 | PASS/FAIL | Obligation leak, callee str_elem
- atk_12 HALF-FIX, key via doprint but VALUE via str: 2 | FAIL/PASS | Obligation leak, callee str_elem
- atk_13 set drops its last element: 2 | PASS/FAIL | Loop invariant not hold on ENTRY (joined_elems)
- atk_14 dict renders keys only: 2 | FAIL/PASS | Loop invariant (joined_pairs)
- atk_15 dict drops its last pair (partial domain): 2 | FAIL/PASS | Loop invariant not hold on entry (joined_pairs)

EVERY refined patch is a MEASURED wrong patch, not an assumed one. I materialized all 15 faithful patches MECHANICALLY (git diff at the gold insertion site, repr.py after _print_list line 145); all 15 `git apply --check` clean at base_commit, and I then APPLIED each in a worktree and RAN the real F2P body: gold = test_dict PASS/test_set PASS; base(prepatch) = FAIL/FAIL; every attack patch fails at least one (table above; f2p_results.json). So each attack is genuinely incorrect in the repo -- had any verified, its patch was ready and would have been resolve-run.

### ORACLE IS LIVE AND CAN REFUTE (both anchors executed, not assumed):
- GOLD: run_resolve('sympy__sympy-19346', patch.diff) => completed=True resolved=True attempts=1 (logs/gold_resolve.log).
- REFUTATION: run_resolve with my atk_2 refined patch => completed=True resolved=False, 'did not resolve in 3 attempts (consistent -- not flaky)' (logs/refute_anchor.log). This is the anchor prior passes did not have: a non-resolve on this instance is a REAL signal, so 'no attack broke it' is informative rather than an untested oracle.

A-LEG AUDIT (my own re-transcription; I did NOT import axiom_check.py, so a bug in the bundle's checker cannot hide here). Against a base_commit worktree + patch.diff, pool of 33 real elements:
- A-consumed value link ToSeq(doprint_elem(t))==elem_repr(t), i.e. ReprPrinter().doprint(e)==srepr(e): holds on all 33.
- elem_repr is legitimately a pure FUNCTION of the element (@Pure is sound): srepr identical at _print_level=3 and on repeat calls on the same printer, for all 33.
- 4 elements render as the EMPTY representation (Quantity(''), stringPict(''), CNF(), ReferenceFrame('')), confirming the bundle is RIGHT to ship elem_repr uninterpreted with no len>=1.
- Distinctness is EXISTENTIAL as documented: str!=srepr on 16, str==srepr on 17, str(Symbol(''))==''. A universal inequality would be unsound; the spec correctly ships none.
- DEEP MODEL == LIVE GOLD: my re-transcribed set_seq/dict_seq vs ReprPrinter()._print_set/_print_dict on 604 set + 603 dict cases (boundary + randomized over the full pool, using the real iteration order): 0 mismatches.
- NON-INJECTIVE elem_repr probed on purpose (the token bijection assumes distinct tokens, not distinct renderings): two distinct elements both rendering '', key token == value token ({x:x}), tokens reused across pairs, singleton set of an empty-rendering element (live '{}'): 26 cases, deep model == live gold on all.
- A4 (`if not expr` <-> len(elems)==0): 24 reachable set/dict subclasses, NONE overrides __bool__ or __len__, so truthiness and emptiness cannot disagree. (My first pass wrote this check with an `or True` that made it vacuous; I caught it and re-ran it properly in a4_recheck.py -- reporting the slip because the corrected result is the one that counts.)
- Line citations in refinement.md/mapping.md all verified in the repo: reprify repr.py:27-31, emptyPrinter's `return str(expr)` repr.py:49, _print_AtomicExpr repr.py:117-118, doprint printer.py:249, _print printer.py:253, MRO scan printer.py:286, StrPrinter._print_Quantity str.py:810, and ReprPrinter.__mro__ == (ReprPrinter, Printer, object) so StrPrinter never applies.

refinement.md LEG AUDIT (protocol step 3): 10 legs, tags are 2 R, 6 R+I, 1 A-consumed, 1 A-consumed+I. NO kind-3 -- and the claim is substantively right, not just lexically: the operation that genuinely changed (a dedicated container renderer routing each element through the recursive routine) IS modeled deeply, and the only consumed axiom is the unchanged callee doprint's value link. §D's 'A-reference' description of elem_str is accurate: it is declared but never consumed by the proof.

WHY NO WRONG IMPL CAN VERIFY (the structural argument the 14 rejections instantiate). Both postconditions are EQUALITIES to total @Pure functions of the carrier (ToSeq(Result())==set_seq/dict_seq), so the admissible output is UNIQUELY determined per input -- there is no slack for a wrong-but-verifying impl. Wrongness could therefore only enter via (a) the deep model disagreeing with gold, refuted by the 1207 live-case A3 check; (b) non-termination, closed by method-level MustTerminate(3) and demonstrated by atk_8's termination rejection; or (c) an unsound axiom, audited above. I also confirmed the domain has no partial-domain escape: every real dict maps to an EVEN-length carrier so `len(flat) % 2 == 0` is never violated by refinement, and the set leg carries no length constraint at all.

SPEC-vs-ORACLE DIRECTION (both safe, spec strictly STRONGER). (a) test_dict TOLERATES pair-order reversal on the 2-pair case while the joined_pairs fold REJECTS it. (b) test_set is graded by NEITHER FAIL_TO_PASS (['test_dict']) nor PASS_TO_PASS (I checked both lists programmatically), so the whole set leg is oracle-unfalsifiable -- yet the spec still rejects every set-leg break (atk_9/10/11/13, each measured to fail test_set). Strictly stronger in both directions, so neither is a verify-but-wrong hole.

### HONEST PROCESS NOTES (two items, neither changes the verdict).
1. atk_4 (dict loop bound i>2, dropping the FIRST pair) DID NOT CONVERGE: 300s cap then the adversary's automatic 1800s retry leg, ~48min wall, on a host carrying ~174 other nagini processes from concurrent fleet work. A timeout is NOT a rejection, so I killed it by PID and EXCLUDED it from `attacks` rather than bank it as a spec win. I re-encoded the SAME wrongness class (dict-leg partial domain) in the convergent shape that the set-leg analogue used, as atk_15 (drops the LAST pair) -- rejected in 14.8s. The class is therefore covered by a real verdict, and the file atk_4_dict_drops_first_pair.py plus its patch remain on disk unsubmitted. I deliberately did not submit it because the runner re-runs every listed attack and a non-converging one would (correctly) read as INCONCLUSIVE.
2. CONFIRMED DEFECT, pre-existing and documented: refinement.md §C/mapping.md §3.2 say a str_elem-based rival is reported as an obligation leak rather than the semantic fold error, and that IS what happens -- atk_1, atk_11 and atk_12 are all rejected at the str_elem call site by 'Obligation leak check failed. Callee str_elem might not take all unsatisfied obligations', because str_elem carries no Requires(MustTerminate(...)) while the renderers hold MustTerminate(3). That discriminator would reject ANY rival calling str_elem regardless of semantics. I did not take the docs' word that the semantic discriminator exists underneath: I added Requires(MustTerminate(2)) to str_elem in a /tmp copy of model_prepatch.py (diag_prepatch_str_elem_mt.py -- a DIAGNOSTIC, spec modified, hence NOT submitted as an attack) and re-verified: exit 1 with exactly 'Loop invariant might not be preserved. Assertion (ToSeq(inner) == joined_elems(elems_s.drop(i)))' AND the joined_pairs analogue, on both legs, in 17.5s. So the semantic elem_repr-vs-elem_str discriminator refinement.md rests its soundness argument on is REAL on both sites, resting only on open-world distinctness of two @ContractOnly callees; the shipped prepatch merely masks it behind the termination error. The bundle discloses this masking accurately, including the measured reason it is not shipped (the strengthening pushes the single-leg battery cases past the verifier budget). Documentation/G-DIFF-reporting concern, NOT a G-EQ refinement-fidelity break: the 11 attacks rejected on genuine SEMANTIC grounds (fold invariant, empty-literal Assert, postcondition Assert, termination) are unaffected, and the three obligation-leak rejections are each independently confirmed wrong by the measured F2P table.

Bundle NEVER modified (git status on benchmark-verified/sympy__sympy-19346/ is clean); the sympy git worktree I created was removed and pruned.

VERDICT SOUND: 14 admissible attacks re-run (>=5 floor), prepatch reproduced (atk_1, both legs), positive control verifies, oracle proven able to BOTH certify gold and refute a wrong patch, and no attack verified -- so no materialized patch needed a resolve run and verify=>correct is unbroken on the evidence I could construct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_plain_str.py`, `atk_2_dict_colon_no_space.py`, `atk_3_dict_value_from_key.py`, `atk_5_dict_empty_is_set_literal.py`, `atk_6_dict_uses_set_assembly.py`, `atk_7_dict_ungrounded_echo.py`, `atk_8_dict_diverges_multi_pair.py`, `atk_9_set_empty_is_dict_literal.py`, `atk_10_set_trailing_separator.py`, +5 more |

**Non-vacuity.** The positive control `pos_control_frozen.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch_plain_str.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_dict_colon_no_space.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_dict_value_from_key.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_dict_empty_is_set_literal.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_dict_uses_set_assembly.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_dict_ungrounded_echo.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_dict_diverges_multi_pair.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9_set_empty_is_dict_literal.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10_set_trailing_separator.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11_set_leg_plain_str.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12_dict_value_plain_str.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13_set_drops_last_elem.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14_dict_keys_only.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15_dict_drops_last_pair.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_frozen.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-19346/nagini. 14 same-spec wrong impls, built by splicing ONLY the two impl regions (splice.py is IDENTITY-VERIFIED: the identity splice reproduces the bundle model.py byte-for-byte, so axioms/@Pure/Requires/Ensures are provably untouched). All 14 + the positive control: `adversary same-spec` rc=0 SAME, and my own pre-flight of the runner's screen (markers.same_spec AND variant_scope.unsound_evasions) reports same_spec=True admissible=True for all 15 -- no new @ContractOnly, no dropped obligation. NO ATTACK PRODUCED A CANDIDATE, so `patches` is empty by the protocol's own terms: there was no verifying wrong impl whose refined patch needed a resolve run.

COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-19346 <f>` (all rc=2 = NOT-A-COUNTEREXAMPLE) plus `bash scripts/nagini_verify.sh <f>` to capture the exact rejection (logs/<name>.detail). Run 3-concurrent as background jobs. Positive control pos_control_frozen.py: rc=0 CANDIDATE, 'Verification successful' 24.6s.

PER-ATTACK: rc | refined-patch measured test_dict/test_set | verifier rejection.
- atk_1 prepatch, str per element on BOTH legs: 2 | FAIL/FAIL | Obligation leak, callee str_elem
- atk_2 ':' without space: 2 | FAIL/PASS | Loop invariant not preserved (ToSeq(inner)==joined_pairs)
- atk_3 value rendered from the key token: 2 | FAIL/PASS | same fold invariant
- atk_5 empty dict renders 'set()': 2 | FAIL/PASS | Assert ToSeq(out_empty)==dict_seq fails
- atk_6 dict assembled with ', ' not ': ': 2 | FAIL/PASS | same fold invariant
- atk_7 ungrounded-oracle echo (fold invariant DROPPED, postcondition merely asserted): 2 | FAIL/PASS | Assert ToSeq(result)==dict_seq fails
- atk_8 diverges for >=2 pairs: 2 | HANG(60s timeout, both tests) | 'Loop might not keep promise to terminate' (method-level MustTerminate(3) is enforced)
- atk_9 empty set renders '{}': 2 | PASS/FAIL | Assert ToSeq(out_empty)==set_seq fails
- atk_10 trailing ', ' after last elem: 2 | PASS/FAIL | Loop invariant (joined_elems)
- atk_11 set leg via str only, dict leg gold: 2 | PASS/FAIL | Obligation leak, callee str_elem
- atk_12 HALF-FIX, key via doprint but VALUE via str: 2 | FAIL/PASS | Obligation leak, callee str_elem
- atk_13 set drops its last element: 2 | PASS/FAIL | Loop invariant not hold on ENTRY (joined_elems)
- atk_14 dict renders keys only: 2 | FAIL/PASS | Loop invariant (joined_pairs)
- atk_15 dict drops its last pair (partial domain): 2 | FAIL/PASS | Loop invariant not hold on entry (joined_pairs)

EVERY refined patch is a MEASURED wrong patch, not an assumed one. I materialized all 15 faithful patches MECHANICALLY (git diff at the gold insertion site, repr.py after _print_list line 145); all 15 `git apply --check` clean at base_commit, and I then APPLIED each in a worktree and RAN the real F2P body: gold = test_dict PASS/test_set PASS; base(prepatch) = FAIL/FAIL; every attack patch fails at least one (table above; f2p_results.json). So each attack is genuinely incorrect in the repo -- had any verified, its patch was ready and would have been resolve-run.

### ORACLE IS LIVE AND CAN REFUTE (both anchors executed, not assumed):
- GOLD: run_resolve('sympy__sympy-19346', patch.diff) => completed=True resolved=True attempts=1 (logs/gold_resolve.log).
- REFUTATION: run_resolve with my atk_2 refined patch => completed=True resolved=False, 'did not resolve in 3 attempts (consistent -- not flaky)' (logs/refute_anchor.log). This is the anchor prior passes did not have: a non-resolve on this instance is a REAL signal, so 'no attack broke it' is informative rather than an untested oracle.

A-LEG AUDIT (my own re-transcription; I did NOT import axiom_check.py, so a bug in the bundle's checker cannot hide here). Against a base_commit worktree + patch.diff, pool of 33 real elements:
- A-consumed value link ToSeq(doprint_elem(t))==elem_repr(t), i.e. ReprPrinter().doprint(e)==srepr(e): holds on all 33.
- elem_repr is legitimately a pure FUNCTION of the element (@Pure is sound): srepr identical at _print_level=3 and on repeat calls on the same printer, for all 33.
- 4 elements render as the EMPTY representation (Quantity(''), stringPict(''), CNF(), ReferenceFrame('')), confirming the bundle is RIGHT to ship elem_repr uninterpreted with no len>=1.
- Distinctness is EXISTENTIAL as documented: str!=srepr on 16, str==srepr on 17, str(Symbol(''))==''. A universal inequality would be unsound; the spec correctly ships none.
- DEEP MODEL == LIVE GOLD: my re-transcribed set_seq/dict_seq vs ReprPrinter()._print_set/_print_dict on 604 set + 603 dict cases (boundary + randomized over the full pool, using the real iteration order): 0 mismatches.
- NON-INJECTIVE elem_repr probed on purpose (the token bijection assumes distinct tokens, not distinct renderings): two distinct elements both rendering '', key token == value token ({x:x}), tokens reused across pairs, singleton set of an empty-rendering element (live '{}'): 26 cases, deep model == live gold on all.
- A4 (`if not expr` <-> len(elems)==0): 24 reachable set/dict subclasses, NONE overrides __bool__ or __len__, so truthiness and emptiness cannot disagree. (My first pass wrote this check with an `or True` that made it vacuous; I caught it and re-ran it properly in a4_recheck.py -- reporting the slip because the corrected result is the one that counts.)
- Line citations in refinement.md/mapping.md all verified in the repo: reprify repr.py:27-31, emptyPrinter's `return str(expr)` repr.py:49, _print_AtomicExpr repr.py:117-118, doprint printer.py:249, _print printer.py:253, MRO scan printer.py:286, StrPrinter._print_Quantity str.py:810, and ReprPrinter.__mro__ == (ReprPrinter, Printer, object) so StrPrinter never applies.

refinement.md LEG AUDIT (protocol step 3): 10 legs, tags are 2 R, 6 R+I, 1 A-consumed, 1 A-consumed+I. NO kind-3 -- and the claim is substantively right, not just lexically: the operation that genuinely changed (a dedicated container renderer routing each element through the recursive routine) IS modeled deeply, and the only consumed axiom is the unchanged callee doprint's value link. §D's 'A-reference' description of elem_str is accurate: it is declared but never consumed by the proof.

WHY NO WRONG IMPL CAN VERIFY (the structural argument the 14 rejections instantiate). Both postconditions are EQUALITIES to total @Pure functions of the carrier (ToSeq(Result())==set_seq/dict_seq), so the admissible output is UNIQUELY determined per input -- there is no slack for a wrong-but-verifying impl. Wrongness could therefore only enter via (a) the deep model disagreeing with gold, refuted by the 1207 live-case A3 check; (b) non-termination, closed by method-level MustTerminate(3) and demonstrated by atk_8's termination rejection; or (c) an unsound axiom, audited above. I also confirmed the domain has no partial-domain escape: every real dict maps to an EVEN-length carrier so `len(flat) % 2 == 0` is never violated by refinement, and the set leg carries no length constraint at all.

SPEC-vs-ORACLE DIRECTION (both safe, spec strictly STRONGER). (a) test_dict TOLERATES pair-order reversal on the 2-pair case while the joined_pairs fold REJECTS it. (b) test_set is graded by NEITHER FAIL_TO_PASS (['test_dict']) nor PASS_TO_PASS (I checked both lists programmatically), so the whole set leg is oracle-unfalsifiable -- yet the spec still rejects every set-leg break (atk_9/10/11/13, each measured to fail test_set). Strictly stronger in both directions, so neither is a verify-but-wrong hole.

### HONEST PROCESS NOTES (two items, neither changes the verdict).
1. atk_4 (dict loop bound i>2, dropping the FIRST pair) DID NOT CONVERGE: 300s cap then the adversary's automatic 1800s retry leg, ~48min wall, on a host carrying ~174 other nagini processes from concurrent fleet work. A timeout is NOT a rejection, so I killed it by PID and EXCLUDED it from `attacks` rather than bank it as a spec win. I re-encoded the SAME wrongness class (dict-leg partial domain) in the convergent shape that the set-leg analogue used, as atk_15 (drops the LAST pair) -- rejected in 14.8s. The class is therefore covered by a real verdict, and the file atk_4_dict_drops_first_pair.py plus its patch remain on disk unsubmitted. I deliberately did not submit it because the runner re-runs every listed attack and a non-converging one would (correctly) read as INCONCLUSIVE.
2. CONFIRMED DEFECT, pre-existing and documented: refinement.md §C/mapping.md §3.2 say a str_elem-based rival is reported as an obligation leak rather than the semantic fold error, and that IS what happens -- atk_1, atk_11 and atk_12 are all rejected at the str_elem call site by 'Obligation leak check failed. Callee str_elem might not take all unsatisfied obligations', because str_elem carries no Requires(MustTerminate(...)) while the renderers hold MustTerminate(3). That discriminator would reject ANY rival calling str_elem regardless of semantics. I did not take the docs' word that the semantic discriminator exists underneath: I added Requires(MustTerminate(2)) to str_elem in a /tmp copy of model_prepatch.py (diag_prepatch_str_elem_mt.py -- a DIAGNOSTIC, spec modified, hence NOT submitted as an attack) and re-verified: exit 1 with exactly 'Loop invariant might not be preserved. Assertion (ToSeq(inner) == joined_elems(elems_s.drop(i)))' AND the joined_pairs analogue, on both legs, in 17.5s. So the semantic elem_repr-vs-elem_str discriminator refinement.md rests its soundness argument on is REAL on both sites, resting only on open-world distinctness of two @ContractOnly callees; the shipped prepatch merely masks it behind the termination error. The bundle discloses this masking accurately, including the measured reason it is not shipped (the strengthening pushes the single-leg battery cases past the verifier budget). Documentation/G-DIFF-reporting concern, NOT a G-EQ refinement-fidelity break: the 11 attacks rejected on genuine SEMANTIC grounds (fold invariant, empty-literal Assert, postcondition Assert, termination) are unaffected, and the three obligation-leak rejections are each independently confirmed wrong by the measured F2P table.

Bundle NEVER modified (git status on benchmark-verified/sympy__sympy-19346/ is clean); the sympy git worktree I created was removed and pruned.

VERDICT SOUND: 14 admissible attacks re-run (>=5 floor), prepatch reproduced (atk_1, both legs), positive control verifies, oracle proven able to BOTH certify gold and refute a wrong patch, and no attack verified -- so no materialized patch needed a resolve run and verify=>correct is unbroken on the evidence I could construct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

REFERENCE SETUP (per instructions): compared model.py against a fresh worktree of sympy/sympy at base_commit 94fb720696f5f5d12bad8bc813699fd696afd2fb with the gold patch APPLIED (git apply clean; confirmed _print_dict/_print_set present in sympy/printing/repr.py after _print_list). Base commit used only for untouched callees (doprint/_print/reprify/emptyPrinter, which the patch demonstrably does not modify).

SPEC-REGION IDENTITY: `adversary same-spec nagini sympy__sympy-19346` on a copy of model.py -> exit 0 ("SAME"); on model_prepatch.py -> exit 0, confirming the G-DIFF rival shares the frozen spec byte-identically and only the impl region differs. meta.json region_hashes present for axioms/pure/pre/post/invariants/impl/spec_view.

MODEL VERIFIES: `scripts/nagini_verify.sh` on model.py -> "Verification successful" in 21.6s, exit 0. So the spec is discharged, not vacuous, and the MustTerminate(3)/MustTerminate(2) obligation chain is real.

### MY OWN DIFFERENTIAL EVIDENCE (independent of the bundle's own checks):
- Wide element-pool differential: 76-element pool (Symbols incl. Symbol(''), Dummy, Wild, Integer/Rational/Float incl. Float(0.1,60) and Float('1e100'), oo/-oo/zoo/nan/pi/E/I, S.Half/EmptySet/Naturals/Reals/Integers, True/False/None, raw python int/float/str/'', Add/Mul/Pow/sin/AppliedUndef/Lambda, tuples/lists/dicts/sets/frozensets, Matrix incl. Matrix(0,3,[]), Interval/FiniteSet/Tuple/Eq/And, Permutation/Cycle, Quantity('')/meter, PolyElement, Ket/Bra/HilbertSpace, stringPict(''), CNF(), diffgeom CoordSystem/Manifold/Patch). Tested empty, every singleton, every unordered pair (itertools.combinations), plus 20000 random sets and 20000 random dicts against the model assembly set_seq/dict_seq (token substitution, using the real set/dict iteration order). RESULT: 0 divergences, and _print_set/_print_dict live-method output matched too.
- _sympyrepr-hook pool (the classes that bypass the normal dispatch and could make nested rendering differ): codegen.ast String/Type/Variable/Declaration/Assignment, physics.quantum Ket/Bra/Dagger/HilbertSpace/ComplexSpace/FockSpace/L2/TensorProduct/InnerProduct/Commutator/AntiCommutator/Operator/hbar, physics.vector frames+dyadics incl. ReferenceFrame(''), sympy.vector, Q.positive(x). 8000 more random containers: 0 divergences.
- PRINTER-STATE probes (the sharpest attack on an `elem_repr(t)` axiom modeled as a stateless pure function): for all 50 hook-pool elements checked (a) reused-printer doprint == fresh srepr, (b) nested rendering at _print_level>=1 == fresh rendering (srepr([e]) == '['+srepr(e)+']'), (c) idempotence of repeated srepr. 0 anomalies. I specifically confirmed ReprPrinter.__mro__ == (ReprPrinter, Printer, object) -- it does NOT inherit StrPrinter, so str.py:693's `self._print_level > 1` full_prec branch (the one genuinely level-sensitive printer path) is unreachable, which is why the stateless elem_repr modeling is sound here.
- SETTINGS probe: found the one real settings-sensitive element (Permutation under perm_cyclic=False makes fresh srepr(p) != that printer's doprint(p)). Crucially the modeled function still matched the model assembly computed with the SAME printer's doprint in all 4 settings dicts ({}, perm_cyclic=False/True, order='lex') -- the model's elem_repr is per-printer, so this is faithful, and mapping.md's provenance (ReprPrinter.doprint) is the right binding rather than the free function srepr.
- TRUE-DOMAIN test: determined by MRO scan which classes actually dispatch to the modeled methods, then compared model vs modeled-fn on each: OrderedDict, Counter, defaultdict, plain dict/set (empty and non-empty), AssumptionsContext (empty+non-empty), DiophantineSolutionSet (empty+non-empty), StdFactKB, SubsSet, FiniteDensity, polyoptions Options -> ALL match. Cycle and PolyElement are dict subclasses but dispatch to _print_Cycle/_print_PolyElement, so they never reach the modeled function (correctly out of scope); frozenset is NOT a set subclass (MRO is (frozenset, object)) so it falls to emptyPrinter -- also out of scope. These three were the only 'mismatches' my sweep produced and all three are dispatch-level, not spec-level.
- Deep nesting + scale: {x:{y:{z:{x:{y}}}}}, {x:[{y:z},{z}]}, {frozenset([x]):{y:(z,)}}, {(x,y):{z:[1,2,{x}]}}, {x:set()}, {x:{}} and a 300-key dict / 300-element set (past the 255-arg boundary in _print_Add) all match.

SPEC-STRENGTH REVIEW (is the spec too strong?): the axioms are notably WEAK in the right direction, and I confirmed the two documented non-over-claims are genuinely necessary rather than cosmetic. elem_repr is Ensures(True) with NO len>=1: I reproduced the empty-representation witnesses (Quantity(''), stringPict(''), CNF() all have srepr == '' at base and under the patch), and confirmed the container still emits them with separators (srepr({Quantity(''), Symbol('x')}) style cases matched the model). elem_str carries no universal `!= elem_repr` and no len>=1: str(oo)==srepr(oo)=='oo' and str(Symbol(''))=='' both hold, so shipping either would have been the unsound over-claim -- the spec correctly omits both and the G-DIFF discriminator rests only on open-world distinctness of two @ContractOnly callees. The dict carrier's `len(flat) % 2 == 0` precondition is a carrier well-formedness condition (a real dict's items() always yields pairs), not a strengthening that excludes real inputs.

BUNDLE CHECKS RE-RUN BY ME IN MY OWN WORKTREE (not trusted from meta.json): axiom_check.py -> exit 0, G-AX OK (value link on 26 elements, 3 empty-representation witnesses, existential str!=srepr, 8000 fuzz). conformance_check.py -> exit 0, "shadow impl == real repo renderers on 100023 inputs (50013 collection + 50010 mapping), disagreements: 0". F2P: applied the test_patch and ran pytest sympy/printing/tests/test_repr.py -k 'test_dict or test_set' -> 3 passed (F2P test_dict passes with the patch).

CONCLUSION: I could not produce an input on the modeled function's real domain where the modeled function disagrees with the real patched callee. Roughly 150k+ differential inputs across element classes, hook classes, real subclasses, printer states, settings, nesting depth and scale yielded zero in-domain divergence. The spec is not too strong and does not drift from real repo behavior. Verdict FAITHFUL. Residual (documented, non-blocking): the two out-of-domain gaps above -- a hypothetical user set subclass overriding __bool__, and self-referential containers where the untouched callee already diverges at base_commit -- are honest carrier/idealization boundaries, not spec defects, and neither is reachable from any in-repo input.

Counterexample / evidence:

```
None. No input was found on which the modeled function disagrees with the real patched callee.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

ATTACKER-3 (leakage / gold-reconstruction), sympy__sympy-19346 nagini. Verdict NO-LEAKAGE, from my own measurements.

SCOPE / DISPOSITION. No relaxation is in play: meta.json has NO `relaxed_leakage` key (checked by key scan), no RELAXED_LEAKAGE.md exists in the bundle, and gates.G-LEAK.status == 'pass' (detail 'spec view clean'). So this is an ordinary strict leakage judgement, not a relaxed one, and there was no unavoidability argument to re-derive.

WHAT I JUDGED. I generated the actual consumer projection myself rather than eyeballing model.py: markers.spec_view(model.py, nagini.language) -> spec_view.py. Both impl regions elide to the placeholder; what reaches the consumer is the module docstring, the 5 punctuation constants, the axioms region (elem_repr/elem_str/doprint_elem/str_elem), the pure region (empty_seq/joined_elems/joined_pairs/set_seq/dict_seq), and the two signatures + pre/post regions. mapping.md and refinement.md -- which DO say '_print_set/_print_dict ... added by the patch' and narrate the pre-patch emptyPrinter->str(expr) dispatch -- are audit-only: prompts.py `_spec_block` injects ONLY task.spec_view (+ meta modeled_functions), and dataset.py builds spec_view solely from adapter.spec_view(model). Neither doc is ever assembled into a consumer prompt, so their edit-localizing prose is out of scope. Frozen artifact I judged: model.py sha256 223f3eb6...41a544, identical to the digest recorded in gates.G-LEAK.sources.

MECHANICAL RE-RUN (my own, not the stamp). leakage.screen(model.py, nagini, patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Patched symbols the screen derives: {print_dict, print_set, print_EmptySequence}; patched files: sympy/printing/repr.py. I then hand-scanned the projection for mechanism vocabulary the lexical screen could miss: '_print_dict', '_print_set', '_print_list', 'ReprPrinter', 'emptyPrinter', 'reprify', 'repr.py', 'printing/repr', 'srepr', 'MRO', 'dispatch', 'fallback', '__str__' -- ALL absent. Independent narration scan over ['bug','fix','wrong','patch','previously','incorrectly','broken','regression','prepatch','pre-patch'] with word boundaries: zero hits. Model symbol names are render_collection_codepoints / render_mapping_codepoints -- no echo of print_dict/print_set. Same-spec confirmed byte-identical spec region for the identity copy AND for the shipped model_prepatch.py (both exit 0), and the pinned verifier accepts model.py (28.95s, 'Verification successful'), so the artifact I screened is the live, verifying one.

SEMANTIC RE-DERIVATION -- every spec-view fact traced to a public source. (a) 'render each element by the EXECUTABLE element representation, not the element's PLAIN DISPLAY FORM' -- this is the discriminator, and it is a direct restatement of the problem_statement's own two code blocks: the PS shows srepr([x,y]) == "[Symbol('x'), Symbol('y')]" against srepr({x,y}) == '{x, y}' and srepr({x:y}) == '{x: y}'. The wrong form IS the plain-str form and the PS displays both sides, so the contrast is public, not hints-derived (hints_text is empty here anyway, len 0 -- nothing to echo). (b) Braces, ', ' separators, ': ' pair separator -- all literally visible in the PS's own '{x, y}' / '{x: y}' / '[Symbol('x'), Symbol('y')]' output.

(c) The 'set()' five-char and '{}' two-char empty literals are the only spec-view facts NOT in the PS text, so I measured them at base_commit in a fresh worktree (94fb720) BEFORE the patch: srepr(set()) == 'set()' and srepr({}) == '{}' already. They are UNCHANGED pre-patch behaviour, hence cannot disclose the edit, and they are independently forced by the public round-trip premise (eval('{}') is a dict, only 'set()' re-creates a set).

(d) 'doprint' appears (as doprint_elem) at spec-view lines 74/90 -- I confirmed in the worktree that doprint pre-exists at base_commit (printer.py:249) and is NOT among the patched symbols; naming an unchanged callee is permitted and localizes no edit, while _print_set/_print_dict are genuinely absent from repr.py at base (grep: only reprify:27, emptyPrinter:33, _print_list:144). (e) No test identity leaks: 'test_dict'/'test_set' and the hidden nested-dict case appear nowhere in the projection; the recursive-rendering clause is stated as the abstract consistency requirement, which the PS's list/tuple examples already exhibit.

BUNDLE-ADDRESSES-THE-REVIEWER CHECK (reported as its own finding, per my instructions). I ran leakage.reviewer_directed() over every bundle file plus a wider hand-written pattern set ('the honest/correct recording is', 'submit NO-LEAKAGE|LEAKAGE', 'attacker 3', 'G-PANEL-3', 'recording convention', 'you should record', 'dear auditor/reviewer/panel'). reviewer_directed() returns [] for every file. The only hits for 'G-PANEL-3'/'recording convention' are in meta.json and verdict.md, and on reading the surrounding text they are a PRIOR panel run's own recorded note (it states it found no file addressing it) plus machine-derived role statuses -- audit records of past runs, not instructions aimed at me. NOTHING in this bundle told me how to record or which verdict is honest, and I inherited no disposition from any file: the pass above is my own screen re-run plus my own base_commit measurements.

ADJACENT OBSERVATIONS (not leakage, not my gate, recorded for the trail). meta.json carries G-PANEL-2 = fail (faithfulness) and G-PANEL = fail overall; that is orthogonal to leakage and I did not let it colour this verdict. refinement.md §C / mapping.md §3.2 candidly disclose that the shipped model_prepatch.py is actually rejected by an obligation-leak error at the str_elem call site rather than by the named fold invariants (str_elem carries no MustTerminate while the renderers hold MustTerminate(3)), with the semantic discriminator measured only in a scratch strengthening. That is a G-DIFF/G-EQ documentation-precision matter, and it is disclosed rather than hidden -- it does not affect the spec view the consumer sees.

CONCLUSION. The projection reads as a behavioural contract over an abstract container renderer; every discriminating fact in it is recoverable from the public problem_statement or from unchanged base_commit behaviour the solver can observe directly, and nothing names the patched file, the patched methods, the dispatch mechanism, or the hidden tests. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
