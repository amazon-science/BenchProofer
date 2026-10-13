# P2 adversarial audit — sympy__sympy-23262

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,36 +155,25 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
-        right = PSeq(comma(), rparen())  # type: PSeq[int]
+        right = PSeq(rparen())  # type: PSeq[int]  # BUG: no trailing comma
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
         Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
         Assert(elems.drop(i - 1)[0] == elems[i - 1])
         Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
         if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
             Assert(len(elems.drop(i - 1)) == 1)
             body = elems[i - 1]
         else:
-            # at least two elements remain, so `joined` unfolds once.
             Assert(len(elems.drop(i - 1)) >= 2)
             body = elems[i - 1] + sep() + body
         i = i - 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,38 +155,22 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
-        Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
-        Assert(elems.drop(i - 1)[0] == elems[i - 1])
-        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
         if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
-            Assert(len(elems.drop(i - 1)) == 1)
             body = elems[i - 1]
         else:
-            # at least two elements remain, so `joined` unfolds once.
-            Assert(len(elems.drop(i - 1)) >= 2)
-            body = elems[i - 1] + sep() + body
+            body = elems[i - 1] + PSeq(comma()) + body  # BUG: comma, no space
         i = i - 1
     result = left + body + right  # type: PSeq[int]
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,36 +155,25 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
-        right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
+        right = PSeq(comma(), rparen())  # BUG: list should close with ']'
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
         Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
         Assert(elems.drop(i - 1)[0] == elems[i - 1])
         Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
         if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
             Assert(len(elems.drop(i - 1)) == 1)
             body = elems[i - 1]
         else:
-            # at least two elements remain, so `joined` unfolds once.
             Assert(len(elems.drop(i - 1)) >= 2)
             body = elems[i - 1] + sep() + body
         i = i - 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,38 +155,19 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
-        Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
-        Assert(elems.drop(i - 1)[0] == elems[i - 1])
-        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
-        if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
-            Assert(len(elems.drop(i - 1)) == 1)
-            body = elems[i - 1]
-        else:
-            # at least two elements remain, so `joined` unfolds once.
-            Assert(len(elems.drop(i - 1)) >= 2)
-            body = elems[i - 1] + sep() + body
+        body = elems[i - 1] + sep() + body  # BUG: sep() even for last elem
         i = i - 1
     result = left + body + right  # type: PSeq[int]
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,39 +155,17 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(elems)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(elems))
-        Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
-        Assert(elems.drop(i - 1)[0] == elems[i - 1])
-        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
-        if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
-            Assert(len(elems.drop(i - 1)) == 1)
-            body = elems[i - 1]
-        else:
-            # at least two elements remain, so `joined` unfolds once.
-            Assert(len(elems.drop(i - 1)) >= 2)
-            body = elems[i - 1] + sep() + body
-        i = i - 1
+    while True:  # BUG: never terminates -> MustTerminate(2) must reject
+        Invariant(body == PSeq(0).take(0))
+        body = body
     result = left + body + right  # type: PSeq[int]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,39 +155,31 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
         Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
         Assert(elems.drop(i - 1)[0] == elems[i - 1])
         Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
         if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
             Assert(len(elems.drop(i - 1)) == 1)
             body = elems[i - 1]
         else:
-            # at least two elements remain, so `joined` unfolds once.
             Assert(len(elems.drop(i - 1)) >= 2)
             body = elems[i - 1] + sep() + body
         i = i - 1
-    result = left + body + right  # type: PSeq[int]
-    return result
+    if len(elems) == 0:
+        result = left  # BUG: drops the closing delimiter for empty container
+    else:
+        result = left + body + right
+    return result  # type: PSeq[int]
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -155,39 +155,7 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
-    if is_paren:
-        left = PSeq(lparen())  # type: PSeq[int]
-        right = PSeq(comma(), rparen())  # type: PSeq[int]
-    else:
-        left = PSeq(lbracket())
-        right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(elems)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(elems))
-        Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
-        Assert(elems.drop(i - 1)[0] == elems[i - 1])
-        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
-        if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
-            Assert(len(elems.drop(i - 1)) == 1)
-            body = elems[i - 1]
-        else:
-            # at least two elements remain, so `joined` unfolds once.
-            Assert(len(elems.drop(i - 1)) >= 2)
-            body = elems[i - 1] + sep() + body
-        i = i - 1
-    result = left + body + right  # type: PSeq[int]
+
+    result = rendered(elems, is_paren)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -155,37 +155,21 @@
                     Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
     # post-conditions-end
     # impl-start
-    # left, right := the delimiter pair for the requested kind. The parenthesis
-    # kind's closing delimiter carries the trailing comma.
+
     if is_paren:
         left = PSeq(lparen())  # type: PSeq[int]
         right = PSeq(comma(), rparen())  # type: PSeq[int]
     else:
         left = PSeq(lbracket())
         right = PSeq(rbracket())
-    # body := the ", "-joined element list (front-recursive fold, built back to
-    # front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
+    body = PSeq(comma())  # type: PSeq[int]  # BUG: spurious leading comma
     i = len(elems)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(elems))
-        Invariant(body == joined(elems.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
-        # its head is elems[i-1] and its tail is elems.drop(i).
-        Assert(elems.drop(i - 1)[0] == elems[i - 1])
-        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
         if i == len(elems):
-            # last element: a single-element tail, no trailing separator.
-            Assert(len(elems.drop(i - 1)) == 1)
             body = elems[i - 1]
         else:
-            # at least two elements remain, so `joined` unfolds once.
-            Assert(len(elems.drop(i - 1)) >= 2)
             body = elems[i - 1] + sep() + body
         i = i - 1
     result = left + body + right  # type: PSeq[int]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.py`

```python
"""Twin-artifact model for sympy__sympy-23262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite ordered container of already-rendered element source-fragments is
  serialised into the surface source text of a container literal that, when
  re-parsed, reconstructs a container of the SAME KIND (a parenthesis-delimited
  container vs. a square-bracket-delimited container) and the SAME ARITY as the
  input.

  The body is the element fragments concatenated left-to-right with exactly one
  ", " (comma, single space) between each adjacent pair, with no separator
  before the first or after the last element. The body is wrapped in the
  delimiters of the requested kind:

    * the square-bracket kind opens with "[" and closes with "]";
    * the parenthesis kind opens with "(" and closes with ",)" -- a comma
      immediately before the closing parenthesis.

  The trailing comma of the parenthesis kind is REQUIRED: it is what makes the
  emitted text re-parse as a one-element grouping rather than as the bare
  parenthesised value of its single element. A parenthesis container holding
  exactly one element therefore serialises as "(" element ",)", which re-parses
  to that same one-element container; without the trailing comma it would
  re-parse to the element itself, collapsing the arity from one to zero.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); the element list is `PSeq[PSeq[int]]`, the sequence of the elements'
already-rendered surface fragments. Pure sequences carry no heap permission, so
the specification quantifies over them directly. No library callee is
axiomatized: the element-fragment production is unchanged upstream machinery,
taken as given; the assembly modelled here -- delimiter selection plus the
", "-join -- is modelled deeply and pinned exactly by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The per-element surface fragments are taken as given
# `PSeq[int]` values -- producing them is unchanged recursive machinery, not
# part of the modelled assembly. The assembly itself -- delimiter selection and
# the ", "-join -- is modelled deeply.)
# axioms-end


# pure-start
@Pure
def lparen() -> int:
    # '(' : opening delimiter of the parenthesis-kind container.
    return 40


@Pure
def rparen() -> int:
    # ')' : closing delimiter of the parenthesis-kind container.
    return 41


@Pure
def lbracket() -> int:
    # '[' : opening delimiter of the square-bracket-kind container.
    return 91


@Pure
def rbracket() -> int:
    # ']' : closing delimiter of the square-bracket-kind container.
    return 93


@Pure
def comma() -> int:
    # ',' : the separator/terminator code point.
    return 44


@Pure
def sep() -> PSeq[int]:
    # ', ' : a comma followed by a single space, the element separator.
    return PSeq(44, 32)


@Pure
def left_delim(is_paren: bool) -> PSeq[int]:
    """Opening delimiter for the requested container kind."""
    if is_paren:
        return PSeq(lparen())
    return PSeq(lbracket())


@Pure
def right_delim(is_paren: bool) -> PSeq[int]:
    """Closing delimiter for the requested container kind. The parenthesis kind
    closes with a comma immediately before the closing parenthesis so that a
    one-element container re-parses to a one-element container; the square-
    bracket kind closes with the bare closing bracket."""
    if is_paren:
        return PSeq(comma(), rparen())
    return PSeq(rbracket())


@Pure
def joined(elems: PSeq[PSeq[int]]) -> PSeq[int]:
    """The element fragments rendered as the separator-joined body that sits
    between the delimiters: the fragments concatenated left-to-right with
    exactly one `sep()` between each adjacent pair and no trailing separator.
    Front-recursive so a single unfold is available per loop step."""
    if len(elems) == 0:
        return PSeq(0).take(0)
    if len(elems) == 1:
        return elems[0]
    return elems[0] + sep() + joined(elems.drop(1))


@Pure
def rendered(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    """The full container literal: opening delimiter, the ", "-joined element
    body, closing delimiter."""
    return left_delim(is_paren) + joined(elems) + right_delim(is_paren)
# pure-end


def render_container(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    # pre-conditions-start
    # (no heap input; pure sequences carry no permission)
    # TERMINATION: the serialiser must actually ANSWER — assembling a finite
    # container literal from finitely many fragments is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion or
    # an endless loop) satisfies every Ensures vacuously; the real assembly
    # always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The rendered text is exactly left-delim + (", "-joined elements) + right-delim.
    Ensures(Result() == rendered(elems, is_paren))
    # Kind fidelity: the first code point is the opening delimiter of the
    # requested kind -- '(' (40) for the parenthesis kind, '[' (91) otherwise.
    Ensures(len(Result()) >= 2)
    Ensures(Implies(is_paren, Result()[0] == lparen()))
    Ensures(Implies(not is_paren, Result()[0] == lbracket()))
    # Closing fidelity: the parenthesis kind ends with ',' immediately followed
    # by ')' (the REQUIRED trailing comma -- the last two code points are 44
    # then 41); the square-bracket kind ends with ']' (93).
    Ensures(Implies(is_paren, Result()[len(Result()) - 1] == rparen()))
    Ensures(Implies(is_paren, Result()[len(Result()) - 2] == comma()))
    Ensures(Implies(not is_paren, Result()[len(Result()) - 1] == rbracket()))
    # Arity-preserving single-element case: a parenthesis container of exactly
    # one element serialises as '(' + element + ',)' -- the trailing comma keeps
    # it a one-element grouping rather than collapsing to the bare element.
    Ensures(Implies(is_paren and len(elems) == 1,
                    Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
    # post-conditions-end
    # impl-start
    # left, right := the delimiter pair for the requested kind. The parenthesis
    # kind's closing delimiter carries the trailing comma.
    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma(), rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
    # body := the ", "-joined element list (front-recursive fold, built back to
    # front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(elems))
        Invariant(body == joined(elems.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
        # its head is elems[i-1] and its tail is elems.drop(i).
        Assert(elems.drop(i - 1)[0] == elems[i - 1])
        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            Assert(len(elems.drop(i - 1)) == 1)
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            Assert(len(elems.drop(i - 1)) >= 2)
            body = elems[i - 1] + sep() + body
        i = i - 1
    result = left + body + right  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: Ensures(Result() == rendered(elems, is_paren)) over the FROZEN @Pure deep models joined/rendered/left_delim/right_delim, plus Requires(MustTerminate(2)) and explicit delimiter/arity clauses (opening/closing delim identity, required trailing comma [44,41] for paren kind, one-element paren arity Result()=='('+e+',)'). Any verifying same-spec impl must return exactly the gold serialiser text AND terminate.

atk_1 PREPATCH BUG (tuple right=')' no trailing comma): exit 2 rejected (prepatch reproduced).
- atk_2 control-flow-effect (join with bare ',' no space): exit 2 rejected.
- atk_3 boundary (list closes with ',)'): exit 2 rejected.
- atk_4 off-by-one (trailing separator after last element): exit 2 rejected.
- atk_5 non-termination (endless while True): exit 2 rejected — MustTerminate(2) blocks the vacuous partial-correctness escape.
- atk_6 partial-domain (drops closing delim for empty container): exit 2 rejected.
- atk_7 ungrounded-oracle ECHO (return rendered(elems,is_paren)): exit 0 CANDIDATE (shares spec + verifies, 11.1s). same-spec confirmed byte-identical.
- atk_8 boundary (spurious leading comma in body): exit 2 rejected.

MANDATORY resolve step for the sole CANDIDATE (atk_7): it computes EXACTLY the pinned gold text rendered(elems,is_paren), so its faithful refined patch IS the gold patch verbatim (patches map above). Ran through the official harness: `run_resolve('sympy__sympy-23262', gold)` → RESOLVED: True, COMPLETED: True, NOTE 'resolved'. Direct run_evaluation cross-check: resolved=true, FAIL_TO_PASS test_issue_14941 PASS, all 61 PASS_TO_PASS pass. (A first run_resolve attempt returned a report-path miss = transient infra glitch, not a non-resolution; disproven by the manual harness run + wrapper retry.) So the verifying candidate's faithful patch RESOLVES — no verify⇏correct break.

Positive control (gold model.py): weakness → CANDIDATE (verifies, 14.8s).

G-AX (axiom_check.py): exit 0 — deep-model A-references sound (joined==', '.join; rendered==real left+body+right serialiser with required trailing comma; one-element paren container re-parses to a 1-tuple) on 8 boundary lists + 6 round-trip lists + 40000 fuzz. Uses only stdlib ast/str.join/+, the same ops the gold patch relies on.

refinement.md leg audit: 5 legs, all R / I / A-reference — NO kind-3. Leg1 R+A-reference (elems ↔ recursively-rendered fragments, str↔PSeq[int], production taken as given input). Leg2 R (is_paren ↔ isinstance(tuple/list)). Leg3 I (delimiter pair char-for-char; right_delim(True)=[44,41]). Leg4 I+A-reference (joined==', '.join, G-AX). Leg5 I+A-reference (rendered==real serialiser, G-AX). No @ContractOnly axiom exists, so there is no consumed-axiom trust point; the A-references' correspondence to the real Python callees is machine-validated by G-AX. Model↔patch correspondence holds. Verdict SOUND: ≥5 diverse attacks run, none breaks the spec; the one verifying candidate's materialized faithful patch resolves under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.py`

```python
"""Twin-artifact model for sympy__sympy-23262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite ordered container of already-rendered element source-fragments is
  serialised into the surface source text of a container literal that, when
  re-parsed, reconstructs a container of the SAME KIND (a parenthesis-delimited
  container vs. a square-bracket-delimited container) and the SAME ARITY as the
  input.

  The body is the element fragments concatenated left-to-right with exactly one
  ", " (comma, single space) between each adjacent pair, with no separator
  before the first or after the last element. The body is wrapped in the
  delimiters of the requested kind:

    * the square-bracket kind opens with "[" and closes with "]";
    * the parenthesis kind opens with "(" and closes with ",)" -- a comma
      immediately before the closing parenthesis.

  The trailing comma of the parenthesis kind is REQUIRED: it is what makes the
  emitted text re-parse as a one-element grouping rather than as the bare
  parenthesised value of its single element. A parenthesis container holding
  exactly one element therefore serialises as "(" element ",)", which re-parses
  to that same one-element container; without the trailing comma it would
  re-parse to the element itself, collapsing the arity from one to zero.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); the element list is `PSeq[PSeq[int]]`, the sequence of the elements'
already-rendered surface fragments. Pure sequences carry no heap permission, so
the specification quantifies over them directly. No library callee is
axiomatized: the element-fragment production is unchanged upstream machinery,
taken as given; the assembly modelled here -- delimiter selection plus the
", "-join -- is modelled deeply and pinned exactly by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The per-element surface fragments are taken as given
# `PSeq[int]` values -- producing them is unchanged recursive machinery, not
# part of the modelled assembly. The assembly itself -- delimiter selection and
# the ", "-join -- is modelled deeply.)
# axioms-end


# pure-start
@Pure
def lparen() -> int:
    # '(' : opening delimiter of the parenthesis-kind container.
    return 40


@Pure
def rparen() -> int:
    # ')' : closing delimiter of the parenthesis-kind container.
    return 41


@Pure
def lbracket() -> int:
    # '[' : opening delimiter of the square-bracket-kind container.
    return 91


@Pure
def rbracket() -> int:
    # ']' : closing delimiter of the square-bracket-kind container.
    return 93


@Pure
def comma() -> int:
    # ',' : the separator/terminator code point.
    return 44


@Pure
def sep() -> PSeq[int]:
    # ', ' : a comma followed by a single space, the element separator.
    return PSeq(44, 32)


@Pure
def left_delim(is_paren: bool) -> PSeq[int]:
    """Opening delimiter for the requested container kind."""
    if is_paren:
        return PSeq(lparen())
    return PSeq(lbracket())


@Pure
def right_delim(is_paren: bool) -> PSeq[int]:
    """Closing delimiter for the requested container kind. The parenthesis kind
    closes with a comma immediately before the closing parenthesis so that a
    one-element container re-parses to a one-element container; the square-
    bracket kind closes with the bare closing bracket."""
    if is_paren:
        return PSeq(comma(), rparen())
    return PSeq(rbracket())


@Pure
def joined(elems: PSeq[PSeq[int]]) -> PSeq[int]:
    """The element fragments rendered as the separator-joined body that sits
    between the delimiters: the fragments concatenated left-to-right with
    exactly one `sep()` between each adjacent pair and no trailing separator.
    Front-recursive so a single unfold is available per loop step."""
    if len(elems) == 0:
        return PSeq(0).take(0)
    if len(elems) == 1:
        return elems[0]
    return elems[0] + sep() + joined(elems.drop(1))


@Pure
def rendered(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    """The full container literal: opening delimiter, the ", "-joined element
    body, closing delimiter."""
    return left_delim(is_paren) + joined(elems) + right_delim(is_paren)
# pure-end


def render_container(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    # pre-conditions-start
    # (no heap input; pure sequences carry no permission)
    # TERMINATION: the serialiser must actually ANSWER — assembling a finite
    # container literal from finitely many fragments is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion or
    # an endless loop) satisfies every Ensures vacuously; the real assembly
    # always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The rendered text is exactly left-delim + (", "-joined elements) + right-delim.
    Ensures(Result() == rendered(elems, is_paren))
    # Kind fidelity: the first code point is the opening delimiter of the
    # requested kind -- '(' (40) for the parenthesis kind, '[' (91) otherwise.
    Ensures(len(Result()) >= 2)
    Ensures(Implies(is_paren, Result()[0] == lparen()))
    Ensures(Implies(not is_paren, Result()[0] == lbracket()))
    # Closing fidelity: the parenthesis kind ends with ',' immediately followed
    # by ')' (the REQUIRED trailing comma -- the last two code points are 44
    # then 41); the square-bracket kind ends with ']' (93).
    Ensures(Implies(is_paren, Result()[len(Result()) - 1] == rparen()))
    Ensures(Implies(is_paren, Result()[len(Result()) - 2] == comma()))
    Ensures(Implies(not is_paren, Result()[len(Result()) - 1] == rbracket()))
    # Arity-preserving single-element case: a parenthesis container of exactly
    # one element serialises as '(' + element + ',)' -- the trailing comma keeps
    # it a one-element grouping rather than collapsing to the bare element.
    Ensures(Implies(is_paren and len(elems) == 1,
                    Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
    # post-conditions-end
    # impl-start
    # left, right := the delimiter pair for the requested kind. The parenthesis
    # kind's closing delimiter carries the trailing comma.
    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(comma(), rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
    # body := the ", "-joined element list (front-recursive fold, built back to
    # front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(elems))
        Invariant(body == joined(elems.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
        # its head is elems[i-1] and its tail is elems.drop(i).
        Assert(elems.drop(i - 1)[0] == elems[i - 1])
        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            Assert(len(elems.drop(i - 1)) == 1)
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            Assert(len(elems.drop(i - 1)) >= 2)
            body = elems[i - 1] + sep() + body
        i = i - 1
    result = left + body + right  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output: Ensures(Result() == rendered(elems, is_paren)) over the FROZEN @Pure deep models joined/rendered/left_delim/right_delim, plus Requires(MustTerminate(2)) and explicit delimiter/arity clauses (opening/closing delim identity, required trailing comma [44,41] for paren kind, one-element paren arity Result()=='('+e+',)'). Any verifying same-spec impl must return exactly the gold serialiser text AND terminate.

atk_1 PREPATCH BUG (tuple right=')' no trailing comma): exit 2 rejected (prepatch reproduced).
- atk_2 control-flow-effect (join with bare ',' no space): exit 2 rejected.
- atk_3 boundary (list closes with ',)'): exit 2 rejected.
- atk_4 off-by-one (trailing separator after last element): exit 2 rejected.
- atk_5 non-termination (endless while True): exit 2 rejected — MustTerminate(2) blocks the vacuous partial-correctness escape.
- atk_6 partial-domain (drops closing delim for empty container): exit 2 rejected.
- atk_7 ungrounded-oracle ECHO (return rendered(elems,is_paren)): exit 0 CANDIDATE (shares spec + verifies, 11.1s). same-spec confirmed byte-identical.
- atk_8 boundary (spurious leading comma in body): exit 2 rejected.

MANDATORY resolve step for the sole CANDIDATE (atk_7): it computes EXACTLY the pinned gold text rendered(elems,is_paren), so its faithful refined patch IS the gold patch verbatim (patches map above). Ran through the official harness: `run_resolve('sympy__sympy-23262', gold)` → RESOLVED: True, COMPLETED: True, NOTE 'resolved'. Direct run_evaluation cross-check: resolved=true, FAIL_TO_PASS test_issue_14941 PASS, all 61 PASS_TO_PASS pass. (A first run_resolve attempt returned a report-path miss = transient infra glitch, not a non-resolution; disproven by the manual harness run + wrapper retry.) So the verifying candidate's faithful patch RESOLVES — no verify⇏correct break.

Positive control (gold model.py): weakness → CANDIDATE (verifies, 14.8s).

G-AX (axiom_check.py): exit 0 — deep-model A-references sound (joined==', '.join; rendered==real left+body+right serialiser with required trailing comma; one-element paren container re-parses to a 1-tuple) on 8 boundary lists + 6 round-trip lists + 40000 fuzz. Uses only stdlib ast/str.join/+, the same ops the gold patch relies on.

refinement.md leg audit: 5 legs, all R / I / A-reference — NO kind-3. Leg1 R+A-reference (elems ↔ recursively-rendered fragments, str↔PSeq[int], production taken as given input). Leg2 R (is_paren ↔ isinstance(tuple/list)). Leg3 I (delimiter pair char-for-char; right_delim(True)=[44,41]). Leg4 I+A-reference (joined==', '.join, G-AX). Leg5 I+A-reference (rendered==real serialiser, G-AX). No @ContractOnly axiom exists, so there is no consumed-axiom trust point; the A-references' correspondence to the real Python callees is machine-validated by G-AX. Model↔patch correspondence holds. Verdict SOUND: ≥5 diverse attacks run, none breaks the spec; the one verifying candidate's materialized faithful patch resolves under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for sympy__sympy-23262 nagini bundle. The modeled function render_container(elems, is_paren) models the iterable branch of _recursive_to_string in sympy/utilities/lambdify.py: left + ', '.join(fragments) + right, with the post-fix delimiter pair ('[',']') for lists and ('(',',)') for tuples.

Checks performed:
1. Model verifies under the pinned Nagini verifier (Verification successful, 9.46s) — spec is satisfiable, not too-strong/vacuous.
2. 200,000-input differential fuzz (seed 12345) comparing the model's rendered/joined semantics against the REAL _recursive_to_string(lambda x:x, cont) at base behavior, over both container kinds, with adversarial fragments (empty strings, embedded commas '1, 2', brackets ']' '[1, 2]', '', multibyte 'é', spaces): ZERO mismatches.
3. F2P crux confirmed: real _recursive_to_string(p, ('1',)) == '(1,)' matches model rendered(["1"], True) == '(1,)' — the exact one-element-tuple regression fix.
4. Boundary cases match real function: 2-tuple -> '(1, 2,)', empty tuple -> '(,)', 1-list -> '[1]', empty list -> '[]'.
5. Domain boundary honest: model covers only list/tuple via is_paren; the real else-branch raises NotImplementedError for other iterables, explicitly declared outside the modeled domain in mapping.md (F2P concerns only list/tuple). No overreach.

The spec agrees with the real callee on every input in the modeled domain. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: for the tuple/parenthesis kind, close the container literal with ',)' instead of ')' (repo: `left, right = "()"` -> `left, right = "(", ",)"` in _recursive_to_string, sympy/utilities/lambdify.py), restoring the trailing comma so a one-element tuple re-parses as a tuple.

This discriminator is ALREADY FULLY PUBLIC in the problem_statement: it shows the correct output `'return (1,)\n'` vs the broken `'return (1)\n'` and states 'Note the missing comma after `1` that causes an integer to be returned instead of a tuple', and confirms multi-element tuples like `(1, 2)` are fine. So 'one-element tuple must render with a trailing comma before the closing paren' is solver-visible from the public task.

Spec view (projected via markers.spec_view): stays at abstract modeling altitude. It pins the desired serialiser behavior ('parenthesis kind ... closes with ",)"; the trailing comma ... makes a one-element container re-parse to a one-element container') — which is exactly what the public problem statement already demands, not new information. The spec view names NO repo file (lambdify.py), NO repo symbol (_recursive_to_string / left / right), NO diff markers, NO pre-patch construct, and carries no bug/fix/regression narration. The localization detail (lambdify.py:948, the pre-patch `left, right = "()"` bug) appears ONLY in mapping.md / refinement.md, which are auditor-facing docs, not the consumer spec view.

Mechanical G-LEAK screen (leakage.screen over the spec view against gold patch + problem_statement) PASSES with zero hard failures: no gold-diff line reproduced, no diff markers, no patched file path/module, no spec-view identifier embedding a patched symbol, no narration terms. A specification necessarily fixing the correct behavior is not leakage; the only behavioral discriminator (the trailing comma for the 1-element paren kind) is already public. Not a relaxed bundle (no RELAXED_LEAKAGE.md dependence needed). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
