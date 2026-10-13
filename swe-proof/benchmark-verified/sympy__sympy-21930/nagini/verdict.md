# P2 adversarial audit — sympy__sympy-21930

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,18 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = []  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
 
@@ -148,22 +144,18 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = []  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
 
@@ -190,21 +182,17 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = []  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,14 +114,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
 
@@ -156,14 +152,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
 
@@ -198,13 +190,9 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
-    result.append(RBRACE())
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,17 +106,14 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = [RBRACE()]  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == PSeq(RBRACE()) + ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
@@ -148,17 +145,14 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = [RBRACE()]  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == PSeq(RBRACE()) + ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
@@ -190,17 +184,14 @@
                    appended_super_is_outer(ToSeq(Result()), e)))
     # post-conditions-end
     # impl-start
-    result = [LBRACE()]  # type: List[int]
+    result = [RBRACE()]  # type: List[int]
     i = 0
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == PSeq(RBRACE()) + ToSeq(body).take(i))
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,13 +114,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
+    result.append(RBRACE())
     result.append(RBRACE())
     return result
     # impl-end
@@ -156,13 +154,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
+    result.append(RBRACE())
     result.append(RBRACE())
     return result
     # impl-end
@@ -198,13 +194,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
     result.append(RBRACE())
+    result.append(RBRACE())
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,13 +114,8 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
-        i = i + 1
     result.append(RBRACE())
     return result
     # impl-end
@@ -156,13 +151,8 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
-        i = i + 1
     result.append(RBRACE())
     return result
     # impl-end
@@ -198,13 +188,8 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
-        i = i + 1
     result.append(RBRACE())
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,13 +114,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
+    result.append(CARET())
     result.append(RBRACE())
     return result
     # impl-end
@@ -156,13 +154,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
+    result.append(CARET())
     result.append(RBRACE())
     return result
     # impl-end
@@ -198,13 +194,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(body))
         Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
         i = i + 1
+    result.append(CARET())
     result.append(RBRACE())
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,16 +107,12 @@
     # post-conditions-end
     # impl-start
     result = [LBRACE()]  # type: List[int]
-    i = 0
+    i = 1
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(1 <= i and i <= len(body) + 1)
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
@@ -149,16 +145,12 @@
     # post-conditions-end
     # impl-start
     result = [LBRACE()]  # type: List[int]
-    i = 0
+    i = 1
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(1 <= i and i <= len(body) + 1)
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
@@ -191,16 +183,12 @@
     # post-conditions-end
     # impl-start
     result = [LBRACE()]  # type: List[int]
-    i = 0
+    i = 1
     while i < len(body):
         # invariants-start
         Invariant(Acc(list_pred(body), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(body))
-        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
-        # the copy loop consumes the caller's termination obligation with a
-        # strictly decreasing measure (len(body) - i), discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(1 <= i and i <= len(body) + 1)
         Invariant(MustTerminate(len(body) - i + 1))
         # invariants-end
         result.append(body[i])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21930.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer whose body already carries an interior ``^`` superscript must emit
  that body as a SINGLE self-delimited group: the rendered token begins with
  ``{`` and ends with the matching ``}``, with the original body verbatim in
  between (result element 0 is ``{``, the last element is ``}``, and the
  interior is the body unchanged). The contract is compositional — when a
  further superscript ``^{...}`` is appended directly after the token, that
  appended ``^`` must bind to the WHOLE token rather than colliding with the
  body's own interior ``^``. A token that is a single delimited group has this
  property: the appended ``^`` sits just outside the closing ``}``. A bare body
  that exposes a trailing interior ``^`` does not.

Three renderers with this contract are modelled. Each receives a body that
already contains an interior ``^`` and must wrap it as one group.

Rendering is a bounded, straight-line computation: the operation MUST
terminate and return its token (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered token to the printer.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
special tokens are the ASCII code points ``{`` = 123, ``}`` = 125, ``^`` = 94.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the rendered-token construction is
# modelled DEEPLY below. A body that carries an interior ``^`` and its
# interaction with an appended outer superscript — which must bind to the
# wrapped group rather than to the interior ``^`` — are spelled out as the pure
# models `grouped_token` / `appended_super_is_outer`, validated against the real
# renderer out-of-band by axiom_check.py (G-AX).)
# axioms-end


# pure-start
@Pure
def LBRACE() -> int:
    return 123        # '{'


@Pure
def RBRACE() -> int:
    return 125        # '}'


@Pure
def CARET() -> int:
    return 94         # '^'


@Pure
def grouped_token(body: PSeq[int]) -> PSeq[int]:
    """The rendered token: the body wrapped as one group `{ body }`."""
    return PSeq(LBRACE()) + body + PSeq(RBRACE())


@Pure
def appended_super_is_outer(token: PSeq[int], exp: PSeq[int]) -> bool:
    """A superscript `^{...}` appended after `token` is the OUTERMOST
    superscript of the composite: the `^` introducing it sits immediately after
    a closing `}` (so it binds to the preceding delimited group), not
    immediately after another superscript's content. This holds exactly when
    `token` ends in `}` — i.e. `token` is a self-delimited group."""
    Requires(0 <= len(token))
    if len(token) == 0:
        return False
    return token[len(token) - 1] == RBRACE()
# pure-end


def render_token_a(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the token is exactly the body wrapped as one group
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    # self-delimited group: opens with `{`, closes with `}`, body verbatim
    # between (length is body + the two delimiters)
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    # an appended superscript binds to the whole token (it follows the closing
    # `}`), so it does not collide with the body's interior `^`
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_b(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_c(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL — G-EQ refinement fidelity (A-leg focus), instance sympy__sympy-21930 (nagini).

RESULT: SOUND. 7 distinct same-spec wrong impls encoded (impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical across all 3 sites via gen.py). Each run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-21930 <atk>`; ALL exited 2 (NOT-A-COUNTEREXAMPLE: verification failed). Positive control (verbatim model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0, 'Verification successful' (11.42s). NO CANDIDATE ever produced, so no faithful patch needed materializing/resolving.

WHY SOUND (root cause): the value postcondition `ToSeq(Result()) == grouped_token(ToSeq(body))` is a TOTAL PSeq equality that pins the return to EXACTLY PSeq(123)+body+PSeq(125) = gold `{body}`. No behavioral freedom remains; the extra Ensures (len==body+2, Result[0]=={, Result[-1]==}, Forall e: appended_super_is_outer) are redundant reinforcements, not the load-bearing constraint. Any verifying impl is byte-for-byte the gold wrap up to the str<->List[int] refinement.

### ATTACKS (all exit 2, atk_N.py):
- atk_1 PREPATCH BUG: bare body, no braces (== model_prepatch.py) -> rejected. Confirms G-DIFF: spec senses the change. prepatch_reproduced=true.
- atk_2 boundary: opens { but omits closing } -> rejected (fails grouped_token/len/Result[-1]).
- atk_3 wrong delimiter: leads with } instead of { -> rejected (fails Result[0]/grouped_token).
- atk_4 boundary: appends } twice -> '{body}}' -> rejected (fails len/grouped_token).
- atk_5 control-flow/ungrounded-oracle: infinite loop (no i increment, MustTerminate invariant removed) — vacuous value postconds -> rejected. Confirms the MustTerminate(2) total-correctness obligation is genuinely enforced (a diverging impl is NOT admitted).
- atk_6 caret injection: appends CARET before } -> '{body^}' -> rejected (fails grouped_token/len).
- atk_7 off-by-one/partial-domain: skips body[0] (i starts at 1) -> rejected (fails grouped_token).

REFINEMENT.md AUDIT (A-legs): A1=R (str<->List[int]), A2=I (prefix {), A3=R+I (identity body copy), A4=I (suffix }), A5=A-reference, A6=A-reference. NO consumed @ContractOnly axioms; NO kind-3 (changed op modeled deeply as grouped_token / appended_super_is_outer, NOT axiomatized). A-reference correspondence HOLDS: axiom_check.py (G-AX) imports the real `sympy` (library under change), asserts sympy.latex(op)==grouped_token(intrinsic_body) for the 3 patched operators (Bd/Fd/AntiSymmetricTensor), checks the interior '^' is present (wrap load-bearing), power-safety composite latex(op**2) contains token+'^{2}' and NOT the malformed bare double-superscript, and the exact issue-19661 witness. axiom_check exits 0 on patched printer / non-zero on unpatched — genuine discriminator. mapping.md binds render_token_{a,b,c} to AntiSymmetricTensor/CreateBoson/CreateFermion._latex at base_commit de446c6; gold patch.diff (3 hunks) adds ONLY outer braces around each intrinsic %-format body, exactly the modeled grouped_token wrap; body is a faithful uninterpreted carrier. Every leg is R / A-reference / I; correspondence to real callees holds.

No verify->correct gap found. verify => correct on the tested inputs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21930.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer whose body already carries an interior ``^`` superscript must emit
  that body as a SINGLE self-delimited group: the rendered token begins with
  ``{`` and ends with the matching ``}``, with the original body verbatim in
  between (result element 0 is ``{``, the last element is ``}``, and the
  interior is the body unchanged). The contract is compositional — when a
  further superscript ``^{...}`` is appended directly after the token, that
  appended ``^`` must bind to the WHOLE token rather than colliding with the
  body's own interior ``^``. A token that is a single delimited group has this
  property: the appended ``^`` sits just outside the closing ``}``. A bare body
  that exposes a trailing interior ``^`` does not.

Three renderers with this contract are modelled. Each receives a body that
already contains an interior ``^`` and must wrap it as one group.

Rendering is a bounded, straight-line computation: the operation MUST
terminate and return its token (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered token to the printer.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
special tokens are the ASCII code points ``{`` = 123, ``}`` = 125, ``^`` = 94.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the rendered-token construction is
# modelled DEEPLY below. A body that carries an interior ``^`` and its
# interaction with an appended outer superscript — which must bind to the
# wrapped group rather than to the interior ``^`` — are spelled out as the pure
# models `grouped_token` / `appended_super_is_outer`, validated against the real
# renderer out-of-band by axiom_check.py (G-AX).)
# axioms-end


# pure-start
@Pure
def LBRACE() -> int:
    return 123        # '{'


@Pure
def RBRACE() -> int:
    return 125        # '}'


@Pure
def CARET() -> int:
    return 94         # '^'


@Pure
def grouped_token(body: PSeq[int]) -> PSeq[int]:
    """The rendered token: the body wrapped as one group `{ body }`."""
    return PSeq(LBRACE()) + body + PSeq(RBRACE())


@Pure
def appended_super_is_outer(token: PSeq[int], exp: PSeq[int]) -> bool:
    """A superscript `^{...}` appended after `token` is the OUTERMOST
    superscript of the composite: the `^` introducing it sits immediately after
    a closing `}` (so it binds to the preceding delimited group), not
    immediately after another superscript's content. This holds exactly when
    `token` ends in `}` — i.e. `token` is a self-delimited group."""
    Requires(0 <= len(token))
    if len(token) == 0:
        return False
    return token[len(token) - 1] == RBRACE()
# pure-end


def render_token_a(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the token is exactly the body wrapped as one group
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    # self-delimited group: opens with `{`, closes with `}`, body verbatim
    # between (length is body + the two delimiters)
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    # an appended superscript binds to the whole token (it follows the closing
    # `}`), so it does not collide with the body's interior `^`
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_b(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_c(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL — G-EQ refinement fidelity (A-leg focus), instance sympy__sympy-21930 (nagini).

RESULT: SOUND. 7 distinct same-spec wrong impls encoded (impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical across all 3 sites via gen.py). Each run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-21930 <atk>`; ALL exited 2 (NOT-A-COUNTEREXAMPLE: verification failed). Positive control (verbatim model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0, 'Verification successful' (11.42s). NO CANDIDATE ever produced, so no faithful patch needed materializing/resolving.

WHY SOUND (root cause): the value postcondition `ToSeq(Result()) == grouped_token(ToSeq(body))` is a TOTAL PSeq equality that pins the return to EXACTLY PSeq(123)+body+PSeq(125) = gold `{body}`. No behavioral freedom remains; the extra Ensures (len==body+2, Result[0]=={, Result[-1]==}, Forall e: appended_super_is_outer) are redundant reinforcements, not the load-bearing constraint. Any verifying impl is byte-for-byte the gold wrap up to the str<->List[int] refinement.

### ATTACKS (all exit 2, atk_N.py):
- atk_1 PREPATCH BUG: bare body, no braces (== model_prepatch.py) -> rejected. Confirms G-DIFF: spec senses the change. prepatch_reproduced=true.
- atk_2 boundary: opens { but omits closing } -> rejected (fails grouped_token/len/Result[-1]).
- atk_3 wrong delimiter: leads with } instead of { -> rejected (fails Result[0]/grouped_token).
- atk_4 boundary: appends } twice -> '{body}}' -> rejected (fails len/grouped_token).
- atk_5 control-flow/ungrounded-oracle: infinite loop (no i increment, MustTerminate invariant removed) — vacuous value postconds -> rejected. Confirms the MustTerminate(2) total-correctness obligation is genuinely enforced (a diverging impl is NOT admitted).
- atk_6 caret injection: appends CARET before } -> '{body^}' -> rejected (fails grouped_token/len).
- atk_7 off-by-one/partial-domain: skips body[0] (i starts at 1) -> rejected (fails grouped_token).

REFINEMENT.md AUDIT (A-legs): A1=R (str<->List[int]), A2=I (prefix {), A3=R+I (identity body copy), A4=I (suffix }), A5=A-reference, A6=A-reference. NO consumed @ContractOnly axioms; NO kind-3 (changed op modeled deeply as grouped_token / appended_super_is_outer, NOT axiomatized). A-reference correspondence HOLDS: axiom_check.py (G-AX) imports the real `sympy` (library under change), asserts sympy.latex(op)==grouped_token(intrinsic_body) for the 3 patched operators (Bd/Fd/AntiSymmetricTensor), checks the interior '^' is present (wrap load-bearing), power-safety composite latex(op**2) contains token+'^{2}' and NOT the malformed bare double-superscript, and the exact issue-19661 witness. axiom_check exits 0 on patched printer / non-zero on unpatched — genuine discriminator. mapping.md binds render_token_{a,b,c} to AntiSymmetricTensor/CreateBoson/CreateFermion._latex at base_commit de446c6; gold patch.diff (3 hunks) adds ONLY outer braces around each intrinsic %-format body, exactly the modeled grouped_token wrap; body is a faithful uninterpreted carrier. Every leg is R / A-reference / I; correspondence to real callees holds.

No verify->correct gap found. verify => correct on the tested inputs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no drift. The three modeled renderers (render_token_a/b/c) model AntiSymmetricTensor._latex / CreateBoson._latex / CreateFermion._latex, whose gold change is exactly wrapping the intrinsic %-format body in an outer LaTeX group `{...}`. The model's deep function grouped_token(body) = PSeq(123)+body+PSeq(125) = '{'+body+'}' is byte-for-byte the wrap the gold installs; body is carried uninterpreted, matching the patch which touches only the outer braces. Postconditions (Result==grouped_token(body), len==len(body)+2, first=='{', last=='}', appended_super_is_outer i.e. ends in '}') are all true observable consequences of the real callee, not over-strengthenings. Verified: (1) spec region repeated identically across all 3 sites (grouped_token/appended_super_is_outer Ensures each appear 3x); (2) axiom_check.py (G-AX) exits 0 on the real patched printer — latex(op)==grouped_token(intrinsic_body) for all 3 operators + power composite + issue-19661 witness `{b^\dagger_{0}}^{2}`; (3) conformance_check.py (G-CONF) exits 0 on 105000 inputs (158 boundary + 104842 fuzz, seed 219300), zero disagreements between contract-stripped shadow impl and the real _latex methods; (4) independent adversarial probe of edge-case state/symbol labels (braces '}' '{', '^', '\dagger', empty, unicode 'α', astral) found the real _latex output equals '{'+body+'}' for every case, matching the model. MustTerminate(2) is trivially satisfied by the total '%s'%... callee, so it excludes no faithful implementation. No input exists where the modeled function disagrees with the real repo callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction audit for sympy__sympy-21930 (nagini).

METHOD: Rendered the exact solver-visible spec view via markers.spec_view(model.py, get_backend('nagini').language). Elided impl regions ('... implementation elided'); visible surface = module docstring + axioms comment + pure region (LBRACE/RBRACE/CARET, grouped_token, appended_super_is_outer) + the three render_token_{a,b,c} pre/post-condition regions. Compared ONLY against the public problem_statement (hints_text empty / out of scope). Confirmed against the gold patch in data/swe_bench_verified/test.jsonl.

BASELINE (problem_statement, PUBLIC): titled 'Issues with Latex printing output in second quantization module', shows the malformed double superscript `b^\dagger_{0}^{2}`, and states the fix VERBATIM: 'It should be correct by adding curly brackets `{b^\dagger_{0}}^{2}`'. The gold edit (wrap each operator's _latex rendering in `{...}` so an appended superscript binds to the whole group instead of colliding with the interior `^`) is therefore already fully disclosed publicly.

SPEC-VIEW CONTENT: an abstract behavioural contract — a renderer must emit its body as one self-delimited group `{ body }` (result[0]=='{', result[-1]=='}', body verbatim between; grouped_token = PSeq(123)+body+PSeq(125)), and an appended `^{...}` binds to the whole token (appended_super_is_outer true iff token ends in '}'). This is exactly the publicly-stated brace-wrap fix, re-expressed over List[int]/PSeq[int] code points.

LEXICAL SCAN (case-insensitive over the rendered spec view): repo identifiers ABSENT — secondquant, dagger, createboson, createfermion, antisymmetric, latex, _latex, sympy, physics, commutator, symbol, 'b^', 'a^' none present. Model function names deliberately non-echoing (render_token_a/b/c); do not token-overlap patched class names. 'printer' appears only as generic renderer prose ('deliver the rendered token to the printer') and problem_statement is itself about a LaTeX printer. Only '.py' hit is the bundle artifact axiom_check.py — not the repo path sympy/physics/secondquant.py (never named). Token constants {=123,}=125,^=94 are the same LaTeX delimiters problem_statement names.

The 'three renderers' multiplicity is a structural modeling detail (three sites got the same fix); it does not reveal the repo class identities, which live only in mapping.md / meta.json (bundle-internal, NOT in the solver-visible spec view).

CONCLUSION: nothing in the spec view reconstructs the gold edit beyond what problem_statement already discloses verbatim. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
