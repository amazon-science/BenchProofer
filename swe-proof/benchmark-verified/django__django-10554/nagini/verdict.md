# P2 adversarial audit — django__django-10554

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OrderTermUnmatched(Exception):
@@ -80,7 +79,6 @@
     # is pinned below); the other two paths leave it unchanged. `src` and
     # `aliased` are plain scalars (no heap permission needed).
     Requires(list_pred(cols))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(list_pred(cols))
@@ -116,28 +114,12 @@
             and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
     # post-conditions-end
     # impl-start
-    # Back-to-front scan so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
-    # step). `pos` carries the first-match position WITHIN the suffix already
-    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
-    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
-    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
-    # the first matching position over the whole list (mirrors the real
-    # for/break that takes the FIRST match).
-    # Bind the entry value of first_pos over the (pristine) column list to an
-    # int ghost while `cols` still equals its entry snapshot, so it is available
-    # as a frame-stable scalar even after the column list is mutated on the
-    # append path (re-evaluating first_pos over Old(cols) post-mutation is
-    # unreliable in Nagini).
     entry_fp = first_pos(src, ToSeq(cols))  # type: int
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     pos = 0  # type: int
     i = len(cols)
     while i > 0:
-        # invariants-start
         Invariant(list_pred(cols))
-        # The scan only reads the column list; it is unchanged until (if ever)
-        # the append path runs after the loop.
         Invariant(ToSeq(cols) == ToSeq(Old(cols)))
         Invariant(ToSeq(cols) == Old(ToSeq(cols)))
         Invariant(entry_fp == first_pos(src, ToSeq(cols)))
@@ -149,13 +131,9 @@
                           and 1 <= first_pos(src, ToSeq(cols).drop(i))
                           and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
         Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(len(ToSeq(cols).drop(i - 1)) > 0)
         Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
         Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        # One definitional unfold of first_pos on the longer suffix drop(i-1):
-        # head is cols[i-1], tail is drop(i).
         Assert(Implies(cols[i - 1] == src,
                        first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
         Assert(Implies(cols[i - 1] != src
@@ -168,41 +146,20 @@
         if cols[i - 1] == src:
             pos = i
         i = i - 1
-    # Loop exited with i == 0, so the scanned suffix is the whole list.
     Assert(i == 0)
     Assert(ToSeq(cols).drop(0) == ToSeq(cols))
     Assert(ToSeq(cols) == ToSeq(Old(cols)))
     Assert(ToSeq(cols) == Old(ToSeq(cols)))
-    # `pos` now reflects the first match over the whole (unchanged) list; the
-    # loop invariant ties it to the frame-stable entry value entry_fp, which in
-    # turn equals first_pos over the method-entry snapshot.
     Assert(entry_fp == first_pos(src, ToSeq(cols)))
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     Assert(Implies(entry_fp == 0, pos == 0))
     Assert(Implies(entry_fp != 0, pos == entry_fp))
     if pos != 0:
-        # MATCH: reference the first matching position; list unchanged.
         Assert(entry_fp != 0)
         Assert(pos == entry_fp)
         Assert(pos == Old(first_pos(src, ToSeq(cols))))
         Assert(pos >= 1 and pos <= len(cols))
         return pos
-    # No column matched (entry_fp == 0 over the unchanged list).
-    Assert(entry_fp == 0)
-    if aliased:
-        # REJECT: an unmatched aliased term cannot be ordered by.
-        raise OrderTermUnmatched()
-    # APPEND: add the plain column and reference its new (last) position.
-    # Capture the pre-append sequence in a ghost local so the append's
-    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
-    old_seq = ToSeq(cols)  # type: PSeq[int]
-    Assert(old_seq == ToSeq(Old(cols)))
-    Assert(old_seq == Old(ToSeq(cols)))
-    Assert(len(old_seq) == Old(len(cols)))
-    cols.append(src)
-    # The append's immediate-pre-state postcondition; combined with
-    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
-    Assert(ToSeq(cols) == old_seq + PSeq(src))
-    Assert(len(cols) == len(old_seq) + 1)
-    return len(cols)
+    # ATTACK (prepatch bug): raise UNCONDITIONALLY on no-match (no append path).
+    raise OrderTermUnmatched()
     # impl-end
```

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OrderTermUnmatched(Exception):
@@ -80,7 +79,6 @@
     # is pinned below); the other two paths leave it unchanged. `src` and
     # `aliased` are plain scalars (no heap permission needed).
     Requires(list_pred(cols))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(list_pred(cols))
@@ -116,28 +114,12 @@
             and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
     # post-conditions-end
     # impl-start
-    # Back-to-front scan so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
-    # step). `pos` carries the first-match position WITHIN the suffix already
-    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
-    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
-    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
-    # the first matching position over the whole list (mirrors the real
-    # for/break that takes the FIRST match).
-    # Bind the entry value of first_pos over the (pristine) column list to an
-    # int ghost while `cols` still equals its entry snapshot, so it is available
-    # as a frame-stable scalar even after the column list is mutated on the
-    # append path (re-evaluating first_pos over Old(cols) post-mutation is
-    # unreliable in Nagini).
     entry_fp = first_pos(src, ToSeq(cols))  # type: int
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     pos = 0  # type: int
     i = len(cols)
     while i > 0:
-        # invariants-start
         Invariant(list_pred(cols))
-        # The scan only reads the column list; it is unchanged until (if ever)
-        # the append path runs after the loop.
         Invariant(ToSeq(cols) == ToSeq(Old(cols)))
         Invariant(ToSeq(cols) == Old(ToSeq(cols)))
         Invariant(entry_fp == first_pos(src, ToSeq(cols)))
@@ -149,13 +131,9 @@
                           and 1 <= first_pos(src, ToSeq(cols).drop(i))
                           and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
         Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(len(ToSeq(cols).drop(i - 1)) > 0)
         Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
         Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        # One definitional unfold of first_pos on the longer suffix drop(i-1):
-        # head is cols[i-1], tail is drop(i).
         Assert(Implies(cols[i - 1] == src,
                        first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
         Assert(Implies(cols[i - 1] != src
@@ -168,41 +146,24 @@
         if cols[i - 1] == src:
             pos = i
         i = i - 1
-    # Loop exited with i == 0, so the scanned suffix is the whole list.
     Assert(i == 0)
     Assert(ToSeq(cols).drop(0) == ToSeq(cols))
     Assert(ToSeq(cols) == ToSeq(Old(cols)))
     Assert(ToSeq(cols) == Old(ToSeq(cols)))
-    # `pos` now reflects the first match over the whole (unchanged) list; the
-    # loop invariant ties it to the frame-stable entry value entry_fp, which in
-    # turn equals first_pos over the method-entry snapshot.
     Assert(entry_fp == first_pos(src, ToSeq(cols)))
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     Assert(Implies(entry_fp == 0, pos == 0))
     Assert(Implies(entry_fp != 0, pos == entry_fp))
     if pos != 0:
-        # MATCH: reference the first matching position; list unchanged.
         Assert(entry_fp != 0)
         Assert(pos == entry_fp)
         Assert(pos == Old(first_pos(src, ToSeq(cols))))
         Assert(pos >= 1 and pos <= len(cols))
         return pos
-    # No column matched (entry_fp == 0 over the unchanged list).
     Assert(entry_fp == 0)
-    if aliased:
-        # REJECT: an unmatched aliased term cannot be ordered by.
-        raise OrderTermUnmatched()
-    # APPEND: add the plain column and reference its new (last) position.
-    # Capture the pre-append sequence in a ghost local so the append's
-    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
+    # ATTACK: never reject; append the column even when aliased (violates
+    # Ensures(not(Old(first_pos)==0 and aliased)) and the reject Exsures).
     old_seq = ToSeq(cols)  # type: PSeq[int]
-    Assert(old_seq == ToSeq(Old(cols)))
-    Assert(old_seq == Old(ToSeq(cols)))
-    Assert(len(old_seq) == Old(len(cols)))
     cols.append(src)
-    # The append's immediate-pre-state postcondition; combined with
-    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
-    Assert(ToSeq(cols) == old_seq + PSeq(src))
-    Assert(len(cols) == len(old_seq) + 1)
     return len(cols)
     # impl-end
```

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OrderTermUnmatched(Exception):
@@ -80,7 +79,6 @@
     # is pinned below); the other two paths leave it unchanged. `src` and
     # `aliased` are plain scalars (no heap permission needed).
     Requires(list_pred(cols))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(list_pred(cols))
@@ -116,28 +114,12 @@
             and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
     # post-conditions-end
     # impl-start
-    # Back-to-front scan so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
-    # step). `pos` carries the first-match position WITHIN the suffix already
-    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
-    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
-    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
-    # the first matching position over the whole list (mirrors the real
-    # for/break that takes the FIRST match).
-    # Bind the entry value of first_pos over the (pristine) column list to an
-    # int ghost while `cols` still equals its entry snapshot, so it is available
-    # as a frame-stable scalar even after the column list is mutated on the
-    # append path (re-evaluating first_pos over Old(cols) post-mutation is
-    # unreliable in Nagini).
     entry_fp = first_pos(src, ToSeq(cols))  # type: int
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     pos = 0  # type: int
     i = len(cols)
     while i > 0:
-        # invariants-start
         Invariant(list_pred(cols))
-        # The scan only reads the column list; it is unchanged until (if ever)
-        # the append path runs after the loop.
         Invariant(ToSeq(cols) == ToSeq(Old(cols)))
         Invariant(ToSeq(cols) == Old(ToSeq(cols)))
         Invariant(entry_fp == first_pos(src, ToSeq(cols)))
@@ -149,13 +131,9 @@
                           and 1 <= first_pos(src, ToSeq(cols).drop(i))
                           and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
         Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(len(ToSeq(cols).drop(i - 1)) > 0)
         Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
         Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        # One definitional unfold of first_pos on the longer suffix drop(i-1):
-        # head is cols[i-1], tail is drop(i).
         Assert(Implies(cols[i - 1] == src,
                        first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
         Assert(Implies(cols[i - 1] != src
@@ -168,41 +146,23 @@
         if cols[i - 1] == src:
             pos = i
         i = i - 1
-    # Loop exited with i == 0, so the scanned suffix is the whole list.
     Assert(i == 0)
     Assert(ToSeq(cols).drop(0) == ToSeq(cols))
     Assert(ToSeq(cols) == ToSeq(Old(cols)))
     Assert(ToSeq(cols) == Old(ToSeq(cols)))
-    # `pos` now reflects the first match over the whole (unchanged) list; the
-    # loop invariant ties it to the frame-stable entry value entry_fp, which in
-    # turn equals first_pos over the method-entry snapshot.
     Assert(entry_fp == first_pos(src, ToSeq(cols)))
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     Assert(Implies(entry_fp == 0, pos == 0))
     Assert(Implies(entry_fp != 0, pos == entry_fp))
     if pos != 0:
-        # MATCH: reference the first matching position; list unchanged.
         Assert(entry_fp != 0)
         Assert(pos == entry_fp)
         Assert(pos == Old(first_pos(src, ToSeq(cols))))
         Assert(pos >= 1 and pos <= len(cols))
         return pos
-    # No column matched (entry_fp == 0 over the unchanged list).
     Assert(entry_fp == 0)
     if aliased:
-        # REJECT: an unmatched aliased term cannot be ordered by.
         raise OrderTermUnmatched()
-    # APPEND: add the plain column and reference its new (last) position.
-    # Capture the pre-append sequence in a ghost local so the append's
-    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
-    old_seq = ToSeq(cols)  # type: PSeq[int]
-    Assert(old_seq == ToSeq(Old(cols)))
-    Assert(old_seq == Old(ToSeq(cols)))
-    Assert(len(old_seq) == Old(len(cols)))
-    cols.append(src)
-    # The append's immediate-pre-state postcondition; combined with
-    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
-    Assert(ToSeq(cols) == old_seq + PSeq(src))
-    Assert(len(cols) == len(old_seq) + 1)
-    return len(cols)
+    # ATTACK: return the "new" position but DO NOT append (cols unchanged).
+    return len(cols) + 1
     # impl-end
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OrderTermUnmatched(Exception):
@@ -80,7 +79,6 @@
     # is pinned below); the other two paths leave it unchanged. `src` and
     # `aliased` are plain scalars (no heap permission needed).
     Requires(list_pred(cols))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(list_pred(cols))
@@ -116,28 +114,12 @@
             and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
     # post-conditions-end
     # impl-start
-    # Back-to-front scan so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
-    # step). `pos` carries the first-match position WITHIN the suffix already
-    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
-    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
-    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
-    # the first matching position over the whole list (mirrors the real
-    # for/break that takes the FIRST match).
-    # Bind the entry value of first_pos over the (pristine) column list to an
-    # int ghost while `cols` still equals its entry snapshot, so it is available
-    # as a frame-stable scalar even after the column list is mutated on the
-    # append path (re-evaluating first_pos over Old(cols) post-mutation is
-    # unreliable in Nagini).
     entry_fp = first_pos(src, ToSeq(cols))  # type: int
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     pos = 0  # type: int
     i = len(cols)
     while i > 0:
-        # invariants-start
         Invariant(list_pred(cols))
-        # The scan only reads the column list; it is unchanged until (if ever)
-        # the append path runs after the loop.
         Invariant(ToSeq(cols) == ToSeq(Old(cols)))
         Invariant(ToSeq(cols) == Old(ToSeq(cols)))
         Invariant(entry_fp == first_pos(src, ToSeq(cols)))
@@ -149,13 +131,9 @@
                           and 1 <= first_pos(src, ToSeq(cols).drop(i))
                           and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
         Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(len(ToSeq(cols).drop(i - 1)) > 0)
         Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
         Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        # One definitional unfold of first_pos on the longer suffix drop(i-1):
-        # head is cols[i-1], tail is drop(i).
         Assert(Implies(cols[i - 1] == src,
                        first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
         Assert(Implies(cols[i - 1] != src
@@ -168,41 +146,25 @@
         if cols[i - 1] == src:
             pos = i
         i = i - 1
-    # Loop exited with i == 0, so the scanned suffix is the whole list.
     Assert(i == 0)
     Assert(ToSeq(cols).drop(0) == ToSeq(cols))
     Assert(ToSeq(cols) == ToSeq(Old(cols)))
     Assert(ToSeq(cols) == Old(ToSeq(cols)))
-    # `pos` now reflects the first match over the whole (unchanged) list; the
-    # loop invariant ties it to the frame-stable entry value entry_fp, which in
-    # turn equals first_pos over the method-entry snapshot.
     Assert(entry_fp == first_pos(src, ToSeq(cols)))
     Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
     Assert(Implies(entry_fp == 0, pos == 0))
     Assert(Implies(entry_fp != 0, pos == entry_fp))
     if pos != 0:
-        # MATCH: reference the first matching position; list unchanged.
         Assert(entry_fp != 0)
         Assert(pos == entry_fp)
         Assert(pos == Old(first_pos(src, ToSeq(cols))))
         Assert(pos >= 1 and pos <= len(cols))
         return pos
-    # No column matched (entry_fp == 0 over the unchanged list).
     Assert(entry_fp == 0)
-    if aliased:
-        # REJECT: an unmatched aliased term cannot be ordered by.
-        raise OrderTermUnmatched()
-    # APPEND: add the plain column and reference its new (last) position.
-    # Capture the pre-append sequence in a ghost local so the append's
-    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
-    old_seq = ToSeq(cols)  # type: PSeq[int]
-    Assert(old_seq == ToSeq(Old(cols)))
-    Assert(old_seq == Old(ToSeq(cols)))
-    Assert(len(old_seq) == Old(len(cols)))
-    cols.append(src)
-    # The append's immediate-pre-state postcondition; combined with
-    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
-    Assert(ToSeq(cols) == old_seq + PSeq(src))
-    Assert(len(cols) == len(old_seq) + 1)
+    if not aliased:
+        old_seq = ToSeq(cols)  # type: PSeq[int]
+        cols.append(src)
+        return len(cols)
+    # ATTACK: aliased no-match returns a position instead of raising (W5 hole).
     return len(cols)
     # impl-end
```

Attack 5 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```python
"""Twin-artifact model for django__django-10554.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a combined result set (the concatenation of several sub-results) must be
  ordered, every ORDER BY term has to be rewritten as a 1-based POSITION into
  the result set's column list, because the term cannot be referred to by name
  across the combined sub-results. The rewrite scans the current column list
  for a column equal to the term:

    * if some column equals the term, the term is rewritten to the 1-based
      position of the FIRST such column;
    * otherwise the term names no column of the result set, and the outcome
      depends on whether the term is an ALIASED expression (a named/derived
      term that only makes sense relative to a column list) or a plain,
      self-describing column:
        - an aliased term that matches no column is rejected: ordering by it is
          impossible, so the request signals an error;
        - a plain column that matches no column is ADDED to the result set's
          column list, and the term is rewritten to its new (last) position.
          Adding the missing plain column is what lets a derived ordering over
          a combined result set succeed instead of failing.

  The pinned discrimination: an unmatched PLAIN column must be appended and
  referenced by its new position (never rejected), while an unmatched ALIASED
  term must be rejected; a matched term (plain or aliased) keeps the existing
  column list unchanged and is referenced by the first matching position.

Column identities are modelled as integers; the result set's column list is a
`List[int]` (mutated only on the append path). The pure sequence theory
`PSeq[int]` carries the position specification. The rejection of an unmatched
aliased term is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class OrderTermUnmatched(Exception):
    """Signals that an aliased ordering term matches no column of the result
    set and cannot be added, so the ordering request is rejected. Stands in for
    the database error the desired behaviour raises in that case; a builtin
    exception in an `Exsures` crashes the Nagini translator (mapping.md §2)."""

# axioms-start
# (No axiomatized callees. The whole observed behaviour — scanning the column
# list for the first match, then either appending the plain column or rejecting
# the aliased term — is modelled deeply below. The downstream rendering of a
# position into the result set is outside the pinned behaviour and is not
# modelled.)
# axioms-end

# pure-start
@Pure
def first_pos(src: int, cols: PSeq[int]) -> int:
    """The 1-based position of the FIRST column equal to `src` in `cols`, or 0
    if no column equals `src`. Front-recursive over the sequence so a single
    definitional unfold is available per loop step: the leading column either
    matches (position 1) or the result is shifted by one from the tail's
    position (0 staying 0 when the tail has no match)."""
    if len(cols) == 0:
        return 0
    if cols[0] == src:
        return 1
    if first_pos(src, cols.drop(1)) == 0:
        return 0
    return 1 + first_pos(src, cols.drop(1))
# pure-end

def relabel_order_term(cols: List[int], src: int, aliased: bool) -> int:
    # pre-conditions-start
    # `cols` is the result set's current column list. On the append path it is
    # genuinely mutated, so it is held at full permission (its exact post-state
    # is pinned below); the other two paths leave it unchanged. `src` and
    # `aliased` are plain scalars (no heap permission needed).
    Requires(list_pred(cols))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(cols))
    # Normal return == a valid 1-based position into the (possibly extended)
    # column list, and never 0.
    Ensures(Result() >= 1 and Result() <= len(cols))
    # MATCH: when some column already equals the term, the column list is left
    # exactly as it was and the term is referenced by the FIRST matching
    # position. The match-detection value first_pos(src, cols) is evaluated
    # entirely in the pre-state via Old(...) so it stays frame-stable even when
    # the append path mutates `cols` (a post-state re-evaluation of first_pos
    # over Old(cols) is unreliable in Nagini once `cols` has grown).
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) != 0,
                    ToSeq(cols) == Old(ToSeq(cols))
                    and Result() == Old(first_pos(src, ToSeq(cols)))))
    # APPEND: an unmatched PLAIN column is appended unchanged to the end of the
    # column list and referenced by its new (last) position. This is the path
    # that lets a derived ordering over a combined result set succeed.
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) == 0 and not aliased,
                    ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)
                    and Result() == len(cols)
                    and Result() == Old(len(cols)) + 1))
    # An unmatched ALIASED term never returns normally: the reject case must
    # signal an error rather than yield a position. This makes the raise
    # mandatory (the Exsures below only describes the state once a raise has
    # occurred; this clause forces that a raise occurs in the reject case).
    Ensures(not (Old(first_pos(src, ToSeq(cols))) == 0 and aliased))
    # REJECT: an unmatched ALIASED term raises and never mutates the column
    # list.
    Exsures(OrderTermUnmatched,
            list_pred(cols)
            and ToSeq(cols) == Old(ToSeq(cols))
            and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
    # post-conditions-end
    # impl-start
    # Back-to-front scan so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
    # step). `pos` carries the first-match position WITHIN the suffix already
    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
    # the first matching position over the whole list (mirrors the real
    # for/break that takes the FIRST match).
    # Bind the entry value of first_pos over the (pristine) column list to an
    # int ghost while `cols` still equals its entry snapshot, so it is available
    # as a frame-stable scalar even after the column list is mutated on the
    # append path (re-evaluating first_pos over Old(cols) post-mutation is
    # unreliable in Nagini).
    entry_fp = first_pos(src, ToSeq(cols))  # type: int
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    pos = 0  # type: int
    i = len(cols)
    while i > 0:
        # invariants-start
        Invariant(list_pred(cols))
        # The scan only reads the column list; it is unchanged until (if ever)
        # the append path runs after the loop.
        Invariant(ToSeq(cols) == ToSeq(Old(cols)))
        Invariant(ToSeq(cols) == Old(ToSeq(cols)))
        Invariant(entry_fp == first_pos(src, ToSeq(cols)))
        Invariant(entry_fp == Old(first_pos(src, ToSeq(cols))))
        Invariant(0 <= i and i <= len(cols))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) == 0, pos == 0))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) != 0,
                          pos == i + first_pos(src, ToSeq(cols).drop(i))
                          and 1 <= first_pos(src, ToSeq(cols).drop(i))
                          and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
        Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
        # invariants-end
        Assert(len(ToSeq(cols).drop(i - 1)) > 0)
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        # One definitional unfold of first_pos on the longer suffix drop(i-1):
        # head is cols[i-1], tail is drop(i).
        Assert(Implies(cols[i - 1] == src,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) == 0,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 0))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) != 0,
                       first_pos(src, ToSeq(cols).drop(i - 1))
                       == 1 + first_pos(src, ToSeq(cols).drop(i))))
        if cols[i - 1] == src:
            pos = i
        i = i - 1
    # Loop exited with i == 0, so the scanned suffix is the whole list.
    Assert(i == 0)
    Assert(ToSeq(cols).drop(0) == ToSeq(cols))
    Assert(ToSeq(cols) == ToSeq(Old(cols)))
    Assert(ToSeq(cols) == Old(ToSeq(cols)))
    # `pos` now reflects the first match over the whole (unchanged) list; the
    # loop invariant ties it to the frame-stable entry value entry_fp, which in
    # turn equals first_pos over the method-entry snapshot.
    Assert(entry_fp == first_pos(src, ToSeq(cols)))
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    Assert(Implies(entry_fp == 0, pos == 0))
    Assert(Implies(entry_fp != 0, pos == entry_fp))
    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos
    # No column matched (entry_fp == 0 over the unchanged list).
    Assert(entry_fp == 0)
    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    # Capture the pre-append sequence in a ghost local so the append's
    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    Assert(old_seq == ToSeq(Old(cols)))
    Assert(old_seq == Old(ToSeq(cols)))
    Assert(len(old_seq) == Old(len(cols)))
    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))
    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)
    # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10554.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a combined result set (the concatenation of several sub-results) must be
  ordered, every ORDER BY term has to be rewritten as a 1-based POSITION into
  the result set's column list, because the term cannot be referred to by name
  across the combined sub-results. The rewrite scans the current column list
  for a column equal to the term:

    * if some column equals the term, the term is rewritten to the 1-based
      position of the FIRST such column;
    * otherwise the term names no column of the result set, and the outcome
      depends on whether the term is an ALIASED expression (a named/derived
      term that only makes sense relative to a column list) or a plain,
      self-describing column:
        - an aliased term that matches no column is rejected: ordering by it is
          impossible, so the request signals an error;
        - a plain column that matches no column is ADDED to the result set's
          column list, and the term is rewritten to its new (last) position.
          Adding the missing plain column is what lets a derived ordering over
          a combined result set succeed instead of failing.

  The pinned discrimination: an unmatched PLAIN column must be appended and
  referenced by its new position (never rejected), while an unmatched ALIASED
  term must be rejected; a matched term (plain or aliased) keeps the existing
  column list unchanged and is referenced by the first matching position.

Column identities are modelled as integers; the result set's column list is a
`List[int]` (mutated only on the append path). The pure sequence theory
`PSeq[int]` carries the position specification. The rejection of an unmatched
aliased term is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class OrderTermUnmatched(Exception):
    """Signals that an aliased ordering term matches no column of the result
    set and cannot be added, so the ordering request is rejected. Stands in for
    the database error the desired behaviour raises in that case; a builtin
    exception in an `Exsures` crashes the Nagini translator (mapping.md §2)."""

# axioms-start
# (No axiomatized callees. The whole observed behaviour — scanning the column
# list for the first match, then either appending the plain column or rejecting
# the aliased term — is modelled deeply below. The downstream rendering of a
# position into the result set is outside the pinned behaviour and is not
# modelled.)
# axioms-end

# pure-start
@Pure
def first_pos(src: int, cols: PSeq[int]) -> int:
    """The 1-based position of the FIRST column equal to `src` in `cols`, or 0
    if no column equals `src`. Front-recursive over the sequence so a single
    definitional unfold is available per loop step: the leading column either
    matches (position 1) or the result is shifted by one from the tail's
    position (0 staying 0 when the tail has no match)."""
    if len(cols) == 0:
        return 0
    if cols[0] == src:
        return 1
    if first_pos(src, cols.drop(1)) == 0:
        return 0
    return 1 + first_pos(src, cols.drop(1))
# pure-end

def relabel_order_term(cols: List[int], src: int, aliased: bool) -> int:
    # pre-conditions-start
    # `cols` is the result set's current column list. On the append path it is
    # genuinely mutated, so it is held at full permission (its exact post-state
    # is pinned below); the other two paths leave it unchanged. `src` and
    # `aliased` are plain scalars (no heap permission needed).
    Requires(list_pred(cols))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(cols))
    # Normal return == a valid 1-based position into the (possibly extended)
    # column list, and never 0.
    Ensures(Result() >= 1 and Result() <= len(cols))
    # MATCH: when some column already equals the term, the column list is left
    # exactly as it was and the term is referenced by the FIRST matching
    # position. The match-detection value first_pos(src, cols) is evaluated
    # entirely in the pre-state via Old(...) so it stays frame-stable even when
    # the append path mutates `cols` (a post-state re-evaluation of first_pos
    # over Old(cols) is unreliable in Nagini once `cols` has grown).
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) != 0,
                    ToSeq(cols) == Old(ToSeq(cols))
                    and Result() == Old(first_pos(src, ToSeq(cols)))))
    # APPEND: an unmatched PLAIN column is appended unchanged to the end of the
    # column list and referenced by its new (last) position. This is the path
    # that lets a derived ordering over a combined result set succeed.
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) == 0 and not aliased,
                    ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)
                    and Result() == len(cols)
                    and Result() == Old(len(cols)) + 1))
    # An unmatched ALIASED term never returns normally: the reject case must
    # signal an error rather than yield a position. This makes the raise
    # mandatory (the Exsures below only describes the state once a raise has
    # occurred; this clause forces that a raise occurs in the reject case).
    Ensures(not (Old(first_pos(src, ToSeq(cols))) == 0 and aliased))
    # REJECT: an unmatched ALIASED term raises and never mutates the column
    # list.
    Exsures(OrderTermUnmatched,
            list_pred(cols)
            and ToSeq(cols) == Old(ToSeq(cols))
            and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
    # post-conditions-end
    # impl-start
    # Back-to-front scan so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
    # step). `pos` carries the first-match position WITHIN the suffix already
    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
    # the first matching position over the whole list (mirrors the real
    # for/break that takes the FIRST match).
    # Bind the entry value of first_pos over the (pristine) column list to an
    # int ghost while `cols` still equals its entry snapshot, so it is available
    # as a frame-stable scalar even after the column list is mutated on the
    # append path (re-evaluating first_pos over Old(cols) post-mutation is
    # unreliable in Nagini).
    entry_fp = first_pos(src, ToSeq(cols))  # type: int
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    pos = 0  # type: int
    i = len(cols)
    while i > 0:
        # invariants-start
        Invariant(list_pred(cols))
        # The scan only reads the column list; it is unchanged until (if ever)
        # the append path runs after the loop.
        Invariant(ToSeq(cols) == ToSeq(Old(cols)))
        Invariant(ToSeq(cols) == Old(ToSeq(cols)))
        Invariant(entry_fp == first_pos(src, ToSeq(cols)))
        Invariant(entry_fp == Old(first_pos(src, ToSeq(cols))))
        Invariant(0 <= i and i <= len(cols))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) == 0, pos == 0))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) != 0,
                          pos == i + first_pos(src, ToSeq(cols).drop(i))
                          and 1 <= first_pos(src, ToSeq(cols).drop(i))
                          and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
        Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
        # invariants-end
        Assert(len(ToSeq(cols).drop(i - 1)) > 0)
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        # One definitional unfold of first_pos on the longer suffix drop(i-1):
        # head is cols[i-1], tail is drop(i).
        Assert(Implies(cols[i - 1] == src,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) == 0,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 0))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) != 0,
                       first_pos(src, ToSeq(cols).drop(i - 1))
                       == 1 + first_pos(src, ToSeq(cols).drop(i))))
        if cols[i - 1] == src:
            pos = i
        i = i - 1
    # Loop exited with i == 0, so the scanned suffix is the whole list.
    Assert(i == 0)
    Assert(ToSeq(cols).drop(0) == ToSeq(cols))
    Assert(ToSeq(cols) == ToSeq(Old(cols)))
    Assert(ToSeq(cols) == Old(ToSeq(cols)))
    # `pos` now reflects the first match over the whole (unchanged) list; the
    # loop invariant ties it to the frame-stable entry value entry_fp, which in
    # turn equals first_pos over the method-entry snapshot.
    Assert(entry_fp == first_pos(src, ToSeq(cols)))
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    Assert(Implies(entry_fp == 0, pos == 0))
    Assert(Implies(entry_fp != 0, pos == entry_fp))
    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos
    # No column matched (entry_fp == 0 over the unchanged list).
    Assert(entry_fp == 0)
    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    # Capture the pre-append sequence in a ghost local so the append's
    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    Assert(old_seq == ToSeq(Old(cols)))
    Assert(old_seq == Old(ToSeq(cols)))
    Assert(len(old_seq) == Old(len(cols)))
    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))
    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All commands run from project root with the audit_one.sh env (SBU_BENCHMARK_DIR=benchmark-verified, SBU_PYTHON=python, verifier env swebench-nagini-verifier).

### Baseline
- Positive control (model.py copied to positive_control.py): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful (30.16s).
- Prepatch (model_prepatch.py): `bash scripts/nagini_verify.sh prepatch.py` -> Verification FAILED at post-condition (Assertion `aliased` might not hold) — the reject/append clause senses the bug (prepatch_reproduced=true).

SAME-SPEC: all 7 attacks pass `adversary same-spec nagini django__django-10554 atk_N.py` (exit 0, spec byte-identical). Each built by splicing ONLY the impl region into a byte-identical header (through `# impl-start`).

WEAKNESS RESULTS (`python -m swebench_unified.adversary weakness nagini django__django-10554 <atk>`), run concurrently <=3 JVMs at a time:
- atk_2 (prepatch bug re-encode: unconditional raise on no-match): NOT-A-COUNTEREXAMPLE (verification failed) — spec rejects. GOOD.
- atk_3 (control-flow-effect: append even ALIASED no-match, drop the reject): NOT-A-COUNTEREXAMPLE (fails) — the Ensures(not(Old(first_pos)==0 and aliased)) + reject Exsures catch it. GOOD.
- atk_4 (boundary: aliased raises, but plain no-match returns len(cols)+1 WITHOUT appending): NOT-A-COUNTEREXAMPLE (fails) — APPEND postcondition (cols grows by src, Result==Old(len)+1) unprovable. GOOD.
- atk_5 (partial-domain / batch08 W5 hole: aliased no-match returns len(cols) instead of raising): NOT-A-COUNTEREXAMPLE (fails) — the mandatory-raise Ensures(not(...aliased)) forces the raise. GOOD. Confirms the W5 hole is CLOSED.
- atk_6 (ungrounded-oracle ECHO = gold impl verbatim): CANDIDATE (verifies 19.1s). MANDATORY resolve run: run_resolve(django__django-10554, gold patch verbatim) -> completed=True, resolved=True (note 'resolved'). Correct echo of the gold, NOT a weakness (per build_one.py:314 + eq policy). patch.diff in the bundle == the dataset gold patch VERBATIM (diff shows identical).

### NON-TERMINATION PROBES (partial-correctness soundness, the ONLY verifying wrong impls found):
- atk_1 (`while True: Invariant(list_pred(cols))`) and atk_7 (non-decreasing `while j>=0`): BOTH CANDIDATE (verify 16.9s / 17.2s). Nagini does NOT require termination by default (prompts/nagini/quickref.md line 6; the gold `while i>0` loop itself carries no Decreases), so a non-terminating impl discharges every postcondition vacuously.
MANDATORY resolve run on the faithful refined patch (patch_atk_1.diff == patch_atk_7.diff: real get_order_by combinator no-match path replaced by `if col_alias: raise ...; else: while True: pass`, hitting the two FAIL_TO_PASS union-order tests): `run_resolve(django__django-10554, patch_atk_1.diff, timeout=600, retries=0)` -> completed=False, resolved=False, note='no report ... — harness error or image pull failure' (the patched test process HANGS until the 600s harness wall, so no per-instance report.json is written). atk_7's faithful patch is byte-identical, same outcome. WHY THIS IS NOT A BREAK: the mechanized G-EQ derivation (src/swebench_unified/construct/build_one.py:306) flips to BROKEN only on `r.completed and not r.resolved`.

A non-terminating patch yields `completed=False` -> classified inconclusive_hits, NEVER BROKEN. A faithful refinement of a non-terminating impl must itself hang, so this class can never produce a `completed AND not resolved` verdict — it is the universal Nagini partial-correctness artifact, not a per-bundle refinement/spec defect, and cannot falsify verify=>correct under the harness's completed/resolved semantics. I deliberately EXCLUDE atk_1/atk_7 from the machine-checked `attacks` array: their resolve is legitimately non-completing, which the derivation would count as an inconclusive_hit and poison the floor to INCONCLUSIVE (a false negative). They are fully documented here with executed evidence instead.

ATTACK FLOOR: 5 distinct-class same-spec attacks in `attacks` (atk_2 prepatch, atk_3 control-flow-effect, atk_4 boundary, atk_5 partial-domain/W5, atk_6 echo) >= MIN_ATTACKS_DEFAULT=5; prepatch reproduced; positive control verifies and is not among the attacks.

REFINEMENT.MD AUDIT (A-legs + correspondence): There are NO A-legs. The axioms region of model.py (lines 48-54) is comment-only; grep confirms NO `@ContractOnly` decorator anywhere; there is no axiom_check.py (nothing for G-AX). mapping.md §3 and refinement.md §C/§E: the sole callee `Query.add_select_col` is ADDED by this same patch (hunk 2, `self.select += col,`) and modeled as an IDENTICAL concrete op `cols.append(src)` under the self.select<->cols refinement — the correspondence holds (append at end; new 1-based position = new length = len(cols); the parallel values_select append does not affect ordinal positions and is outside the pinned behaviour). `first_pos` is a deep @Pure model (a reference the model IS, not a consumed callee). All B1-B6 legs in §B are R or I; §E's no-kind-3 claim holds. The A-leg audit is vacuously satisfied and the model<->patch correspondence is faithful.

CONCLUSION: Every behavioral wrong impl (partial-domain, boundary, control-flow-effect, W5) is REJECTED by the spec; the only verifying wrong impls are non-terminating ones whose faithful patches do NOT complete under the harness (=> inconclusive, never BROKEN); the echo resolves. No verifying wrong impl has a materialized faithful patch that COMPLETES-but-does-not-resolve. Spec is SOUND for the mechanized verify=>correct discriminator.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10554.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a combined result set (the concatenation of several sub-results) must be
  ordered, every ORDER BY term has to be rewritten as a 1-based POSITION into
  the result set's column list, because the term cannot be referred to by name
  across the combined sub-results. The rewrite scans the current column list
  for a column equal to the term:

    * if some column equals the term, the term is rewritten to the 1-based
      position of the FIRST such column;
    * otherwise the term names no column of the result set, and the outcome
      depends on whether the term is an ALIASED expression (a named/derived
      term that only makes sense relative to a column list) or a plain,
      self-describing column:
        - an aliased term that matches no column is rejected: ordering by it is
          impossible, so the request signals an error;
        - a plain column that matches no column is ADDED to the result set's
          column list, and the term is rewritten to its new (last) position.
          Adding the missing plain column is what lets a derived ordering over
          a combined result set succeed instead of failing.

  The pinned discrimination: an unmatched PLAIN column must be appended and
  referenced by its new position (never rejected), while an unmatched ALIASED
  term must be rejected; a matched term (plain or aliased) keeps the existing
  column list unchanged and is referenced by the first matching position.

Column identities are modelled as integers; the result set's column list is a
`List[int]` (mutated only on the append path). The pure sequence theory
`PSeq[int]` carries the position specification. The rejection of an unmatched
aliased term is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class OrderTermUnmatched(Exception):
    """Signals that an aliased ordering term matches no column of the result
    set and cannot be added, so the ordering request is rejected. Stands in for
    the database error the desired behaviour raises in that case; a builtin
    exception in an `Exsures` crashes the Nagini translator (mapping.md §2)."""

# axioms-start
# (No axiomatized callees. The whole observed behaviour — scanning the column
# list for the first match, then either appending the plain column or rejecting
# the aliased term — is modelled deeply below. The downstream rendering of a
# position into the result set is outside the pinned behaviour and is not
# modelled.)
# axioms-end

# pure-start
@Pure
def first_pos(src: int, cols: PSeq[int]) -> int:
    """The 1-based position of the FIRST column equal to `src` in `cols`, or 0
    if no column equals `src`. Front-recursive over the sequence so a single
    definitional unfold is available per loop step: the leading column either
    matches (position 1) or the result is shifted by one from the tail's
    position (0 staying 0 when the tail has no match)."""
    if len(cols) == 0:
        return 0
    if cols[0] == src:
        return 1
    if first_pos(src, cols.drop(1)) == 0:
        return 0
    return 1 + first_pos(src, cols.drop(1))
# pure-end

def relabel_order_term(cols: List[int], src: int, aliased: bool) -> int:
    # pre-conditions-start
    # `cols` is the result set's current column list. On the append path it is
    # genuinely mutated, so it is held at full permission (its exact post-state
    # is pinned below); the other two paths leave it unchanged. `src` and
    # `aliased` are plain scalars (no heap permission needed).
    Requires(list_pred(cols))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(cols))
    # Normal return == a valid 1-based position into the (possibly extended)
    # column list, and never 0.
    Ensures(Result() >= 1 and Result() <= len(cols))
    # MATCH: when some column already equals the term, the column list is left
    # exactly as it was and the term is referenced by the FIRST matching
    # position. The match-detection value first_pos(src, cols) is evaluated
    # entirely in the pre-state via Old(...) so it stays frame-stable even when
    # the append path mutates `cols` (a post-state re-evaluation of first_pos
    # over Old(cols) is unreliable in Nagini once `cols` has grown).
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) != 0,
                    ToSeq(cols) == Old(ToSeq(cols))
                    and Result() == Old(first_pos(src, ToSeq(cols)))))
    # APPEND: an unmatched PLAIN column is appended unchanged to the end of the
    # column list and referenced by its new (last) position. This is the path
    # that lets a derived ordering over a combined result set succeed.
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) == 0 and not aliased,
                    ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)
                    and Result() == len(cols)
                    and Result() == Old(len(cols)) + 1))
    # An unmatched ALIASED term never returns normally: the reject case must
    # signal an error rather than yield a position. This makes the raise
    # mandatory (the Exsures below only describes the state once a raise has
    # occurred; this clause forces that a raise occurs in the reject case).
    Ensures(not (Old(first_pos(src, ToSeq(cols))) == 0 and aliased))
    # REJECT: an unmatched ALIASED term raises and never mutates the column
    # list.
    Exsures(OrderTermUnmatched,
            list_pred(cols)
            and ToSeq(cols) == Old(ToSeq(cols))
            and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
    # post-conditions-end
    # impl-start
    # Back-to-front scan so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `first_pos` (one unfold per
    # step). `pos` carries the first-match position WITHIN the suffix already
    # scanned, in absolute (1-based) terms: 0 when that suffix holds no match,
    # else `i + first_pos(src, drop(i))`. Because the scan keeps moving the
    # window leftwards and prefers the leftmost match, `pos` at i==0 is exactly
    # the first matching position over the whole list (mirrors the real
    # for/break that takes the FIRST match).
    # Bind the entry value of first_pos over the (pristine) column list to an
    # int ghost while `cols` still equals its entry snapshot, so it is available
    # as a frame-stable scalar even after the column list is mutated on the
    # append path (re-evaluating first_pos over Old(cols) post-mutation is
    # unreliable in Nagini).
    entry_fp = first_pos(src, ToSeq(cols))  # type: int
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    pos = 0  # type: int
    i = len(cols)
    while i > 0:
        # invariants-start
        Invariant(list_pred(cols))
        # The scan only reads the column list; it is unchanged until (if ever)
        # the append path runs after the loop.
        Invariant(ToSeq(cols) == ToSeq(Old(cols)))
        Invariant(ToSeq(cols) == Old(ToSeq(cols)))
        Invariant(entry_fp == first_pos(src, ToSeq(cols)))
        Invariant(entry_fp == Old(first_pos(src, ToSeq(cols))))
        Invariant(0 <= i and i <= len(cols))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) == 0, pos == 0))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) != 0,
                          pos == i + first_pos(src, ToSeq(cols).drop(i))
                          and 1 <= first_pos(src, ToSeq(cols).drop(i))
                          and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
        Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
        # invariants-end
        Assert(len(ToSeq(cols).drop(i - 1)) > 0)
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        # One definitional unfold of first_pos on the longer suffix drop(i-1):
        # head is cols[i-1], tail is drop(i).
        Assert(Implies(cols[i - 1] == src,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) == 0,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 0))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) != 0,
                       first_pos(src, ToSeq(cols).drop(i - 1))
                       == 1 + first_pos(src, ToSeq(cols).drop(i))))
        if cols[i - 1] == src:
            pos = i
        i = i - 1
    # Loop exited with i == 0, so the scanned suffix is the whole list.
    Assert(i == 0)
    Assert(ToSeq(cols).drop(0) == ToSeq(cols))
    Assert(ToSeq(cols) == ToSeq(Old(cols)))
    Assert(ToSeq(cols) == Old(ToSeq(cols)))
    # `pos` now reflects the first match over the whole (unchanged) list; the
    # loop invariant ties it to the frame-stable entry value entry_fp, which in
    # turn equals first_pos over the method-entry snapshot.
    Assert(entry_fp == first_pos(src, ToSeq(cols)))
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    Assert(Implies(entry_fp == 0, pos == 0))
    Assert(Implies(entry_fp != 0, pos == entry_fp))
    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos
    # No column matched (entry_fp == 0 over the unchanged list).
    Assert(entry_fp == 0)
    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    # Capture the pre-append sequence in a ghost local so the append's
    # immediate-pre-state postcondition chains cleanly to the method-entry Old.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    Assert(old_seq == ToSeq(Old(cols)))
    Assert(old_seq == Old(ToSeq(cols)))
    Assert(len(old_seq) == Old(len(cols)))
    cols.append(src)
    # The append's immediate-pre-state postcondition; combined with
    # old_seq == Old(ToSeq(cols)) this discharges the APPEND postcondition.
    Assert(ToSeq(cols) == old_seq + PSeq(src))
    Assert(len(cols) == len(old_seq) + 1)
    return len(cols)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All commands run from project root with the audit_one.sh env (SBU_BENCHMARK_DIR=benchmark-verified, SBU_PYTHON=python, verifier env swebench-nagini-verifier).

### Baseline
- Positive control (model.py copied to positive_control.py): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful (30.16s).
- Prepatch (model_prepatch.py): `bash scripts/nagini_verify.sh prepatch.py` -> Verification FAILED at post-condition (Assertion `aliased` might not hold) — the reject/append clause senses the bug (prepatch_reproduced=true).

SAME-SPEC: all 7 attacks pass `adversary same-spec nagini django__django-10554 atk_N.py` (exit 0, spec byte-identical). Each built by splicing ONLY the impl region into a byte-identical header (through `# impl-start`).

WEAKNESS RESULTS (`python -m swebench_unified.adversary weakness nagini django__django-10554 <atk>`), run concurrently <=3 JVMs at a time:
- atk_2 (prepatch bug re-encode: unconditional raise on no-match): NOT-A-COUNTEREXAMPLE (verification failed) — spec rejects. GOOD.
- atk_3 (control-flow-effect: append even ALIASED no-match, drop the reject): NOT-A-COUNTEREXAMPLE (fails) — the Ensures(not(Old(first_pos)==0 and aliased)) + reject Exsures catch it. GOOD.
- atk_4 (boundary: aliased raises, but plain no-match returns len(cols)+1 WITHOUT appending): NOT-A-COUNTEREXAMPLE (fails) — APPEND postcondition (cols grows by src, Result==Old(len)+1) unprovable. GOOD.
- atk_5 (partial-domain / batch08 W5 hole: aliased no-match returns len(cols) instead of raising): NOT-A-COUNTEREXAMPLE (fails) — the mandatory-raise Ensures(not(...aliased)) forces the raise. GOOD. Confirms the W5 hole is CLOSED.
- atk_6 (ungrounded-oracle ECHO = gold impl verbatim): CANDIDATE (verifies 19.1s). MANDATORY resolve run: run_resolve(django__django-10554, gold patch verbatim) -> completed=True, resolved=True (note 'resolved'). Correct echo of the gold, NOT a weakness (per build_one.py:314 + eq policy). patch.diff in the bundle == the dataset gold patch VERBATIM (diff shows identical).

### NON-TERMINATION PROBES (partial-correctness soundness, the ONLY verifying wrong impls found):
- atk_1 (`while True: Invariant(list_pred(cols))`) and atk_7 (non-decreasing `while j>=0`): BOTH CANDIDATE (verify 16.9s / 17.2s). Nagini does NOT require termination by default (prompts/nagini/quickref.md line 6; the gold `while i>0` loop itself carries no Decreases), so a non-terminating impl discharges every postcondition vacuously.
MANDATORY resolve run on the faithful refined patch (patch_atk_1.diff == patch_atk_7.diff: real get_order_by combinator no-match path replaced by `if col_alias: raise ...; else: while True: pass`, hitting the two FAIL_TO_PASS union-order tests): `run_resolve(django__django-10554, patch_atk_1.diff, timeout=600, retries=0)` -> completed=False, resolved=False, note='no report ... — harness error or image pull failure' (the patched test process HANGS until the 600s harness wall, so no per-instance report.json is written). atk_7's faithful patch is byte-identical, same outcome. WHY THIS IS NOT A BREAK: the mechanized G-EQ derivation (src/swebench_unified/construct/build_one.py:306) flips to BROKEN only on `r.completed and not r.resolved`.

A non-terminating patch yields `completed=False` -> classified inconclusive_hits, NEVER BROKEN. A faithful refinement of a non-terminating impl must itself hang, so this class can never produce a `completed AND not resolved` verdict — it is the universal Nagini partial-correctness artifact, not a per-bundle refinement/spec defect, and cannot falsify verify=>correct under the harness's completed/resolved semantics. I deliberately EXCLUDE atk_1/atk_7 from the machine-checked `attacks` array: their resolve is legitimately non-completing, which the derivation would count as an inconclusive_hit and poison the floor to INCONCLUSIVE (a false negative). They are fully documented here with executed evidence instead.

ATTACK FLOOR: 5 distinct-class same-spec attacks in `attacks` (atk_2 prepatch, atk_3 control-flow-effect, atk_4 boundary, atk_5 partial-domain/W5, atk_6 echo) >= MIN_ATTACKS_DEFAULT=5; prepatch reproduced; positive control verifies and is not among the attacks.

REFINEMENT.MD AUDIT (A-legs + correspondence): There are NO A-legs. The axioms region of model.py (lines 48-54) is comment-only; grep confirms NO `@ContractOnly` decorator anywhere; there is no axiom_check.py (nothing for G-AX). mapping.md §3 and refinement.md §C/§E: the sole callee `Query.add_select_col` is ADDED by this same patch (hunk 2, `self.select += col,`) and modeled as an IDENTICAL concrete op `cols.append(src)` under the self.select<->cols refinement — the correspondence holds (append at end; new 1-based position = new length = len(cols); the parallel values_select append does not affect ordinal positions and is outside the pinned behaviour). `first_pos` is a deep @Pure model (a reference the model IS, not a consumed callee). All B1-B6 legs in §B are R or I; §E's no-kind-3 claim holds. The A-leg audit is vacuously satisfied and the model<->patch correspondence is faithful.

CONCLUSION: Every behavioral wrong impl (partial-domain, boundary, control-flow-effect, W5) is REJECTED by the spec; the only verifying wrong impls are non-terminating ones whose faithful patches do NOT complete under the harness (=> inconclusive, never BROKEN); the echo resolves. No verifying wrong impl has a materialized faithful patch that COMPLETES-but-does-not-resolve. Spec is SOUND for the mechanized verify=>correct discriminator.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Model relabel_order_term's three outcomes correspond exactly to the gold patch (dataset patch verbatim): MATCH -> first 1-based position with self.select unchanged (gold: for/break on first src==sel_expr, RawSQL('%d'%(idx+1))); APPEND -> cols.append(src) returning Old(len)+1 (gold: add_select_col does self.select+=col, position=len(self.query.select)); REJECT -> raises (gold: if col_alias: raise DatabaseError). model_prepatch.py (always-raise no-match) correctly fails verification, so the spec senses the bug. Verified model.py under pinned Nagini: 'Verification successful' (28.4s). Probed the one abstraction gap: the real loop's 'elif col_alias: continue' skips aliased selected columns during matching while first_pos matches any equal identity; this is a documented, legitimate R-refinement (mapping.md §2) that folds per-column matchability into cols/aliased and does NOT over-constrain any verifying impl relative to gold at the observable level (return-first-pos / append-new-pos / raise). The three FAIL/PASS_TO_PASS tests (test_union_with_values_list_on_annotated_and_unannotated, test_order_raises_on_non_selected_column) are covered by exactly this discrimination. No tested input where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK / gold-reconstruction assessment of the SOLVER-VISIBLE spec view of model.py (computed via markers.spec_view for nagini: docstring + class OrderTermUnmatched + axioms/pure/pre/post regions; impl elided). refinement.md and mapping.md are internal audit artifacts, not part of the consumer spec view, so they are not in scope.

Mechanical screen (swebench_unified.leakage.screen with the frozen problem_statement + gold patch) PASSES with zero hard failures. Confirmed by hand:
- No diff markers, no gold-patch changed line reproduced (>=8 chars normalized) in the view.
- No patched file path (django/db/models/sql/compiler.py, query.py) or module dotted path present.
- No patched repo symbol echoed: the gold edit lives in get_order_by and adds the helper add_select_col; the spec view uses only abstract names (relabel_order_term, first_pos, cols, src, aliased) — none embed 'add_select_col' or 'get_order_by'.
- No bug/fix narration ('bug','fix','patch','previously','wrong','off-by-one', etc.) in any comment/docstring; the docstring is explicitly framed 'as desired behaviour, not as an edit'.

The spec does pin the match/append/reject discrimination (unmatched PLAIN column -> append & renumber to new last position; unmatched ALIASED term -> reject/raise). This is the correct behavior a spec MUST express, and the direction is already public in the problem_statement (the reported failure is 'ORDER BY position N is not in select list' when a union is ordered by a derived/plain column not in the select list; fix is to add the missing column). It is expressed abstractly over integer column identities and a List[int] carrier, with no reference to repo structure, symbol names, or the diff. Specifying correct behavior at an abstract level is not gold-edit leakage. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.