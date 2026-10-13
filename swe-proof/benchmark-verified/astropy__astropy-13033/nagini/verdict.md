# P2 adversarial audit — astropy__astropy-13033

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,8 +307,15 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
-    expected_field = render_name_run(demanded)  # type: List[int]
-    found_field = render_name_run(found)  # type: List[int]
+    # PREPATCH: echo only the FIRST name of each run, apostrophe-wrapped.
+    if len(demanded) >= 1:
+        expected_field = [NAME_QUOTE, encode_name(demanded[0]), NAME_QUOTE]  # type: List[int]
+    else:
+        expected_field = []
+    if len(found) >= 1:
+        found_field = [NAME_QUOTE, encode_name(found[0]), NAME_QUOTE]  # type: List[int]
+    else:
+        found_field = []
     # " object is invalid - expected "
     seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
             118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
@@ -324,10 +331,5 @@
     seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
     result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
               + found_field)  # type: List[int]
-    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
-    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
-    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
-                                        ToSeq(demanded), ToSeq(found)))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -220,6 +220,11 @@
     # post-conditions-end
     # impl-start
     run_s = ToSeq(run)  # type: PSeq[int]
+    if len(run) == 0:
+        # BOUNDARY: hand back nothing at all for the empty run, instead of the
+        # bracketed empty textual list form render_run pins ("[]").
+        empty_out = []  # type: List[int]
+        return empty_out
     if len(run) == 1:
         out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
         Assert(ToSeq(out_single) == quoted(run_s[0]))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -246,14 +246,10 @@
             Assert(ToSeq(inner) == quoted(elt))
             Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
         else:
-            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
-                   + joined(run_s.drop(i)))
-            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
+            # BOUNDARY: separator punctuation emitted in the wrong ORDER.
+            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, SPACE, COMMA] + inner
         i = i - 1
     result = [LBRACK] + inner + [RBRACK]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
-    Assert(ToSeq(result) == render_run(run_s))
     return result
     # impl-end
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,27 +307,10 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
-    expected_field = render_name_run(demanded)  # type: List[int]
-    found_field = render_name_run(found)  # type: List[int]
-    # " object is invalid - expected "
-    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
-            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
-            116, 101, 100, 32]  # type: List[int]
-    # " as the first column"
-    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
-            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
-    if len(demanded) > 1:
-        plural = [115]  # type: List[int]
-    else:
-        plural = []
-    # " but found "
-    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
-    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
-              + found_field)  # type: List[int]
-    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
-    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
-    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
-                                        ToSeq(demanded), ToSeq(found)))
-    return result
+    # NON-DELIVERY: declare an exceptional contract in the (elided) impl region
+    # and leave by that exit. No report is ever handed back, on any input.
+    Exsures(Exception, Acc(list_pred(cls_name), 1 / 2)
+            and Acc(list_pred(demanded), 1 / 2)
+            and Acc(list_pred(found), 1 / 2))
+    raise Exception()
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -225,36 +225,9 @@
         Assert(ToSeq(out_single) == quoted(run_s[0]))
         Assert(ToSeq(out_single) == render_run(run_s))
         return out_single
-    # any other length -> bracketed textual list form
-    inner = []  # type: List[int]
-    i = len(run)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(run), 1 / 2))
-        Invariant(Acc(list_pred(inner)))
-        Invariant(0 <= i and i <= len(run))
-        Invariant(run_s == ToSeq(run))
-        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        elt = run[i - 1]  # type: int
-        Assert(run_s.drop(i - 1)[0] == elt)
-        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
-        if i == len(run):
-            # last name: no trailing separator
-            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
-            Assert(ToSeq(inner) == quoted(elt))
-            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
-        else:
-            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
-            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
-                   + joined(run_s.drop(i)))
-            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
-        i = i - 1
-    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
-    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
-    Assert(ToSeq(result) == render_run(run_s))
-    return result
+    # NON-COMPLETION on every other length: re-ask the same question instead of
+    # ever answering it.
+    return render_name_run(run)
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,6 +307,11 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
+    # ALIASED-INPUT REWRITE: two 1/2 shares on one object sum to FULL, so the
+    # caller's own declared list of names is writable here.
+    if demanded is found:
+        if len(demanded) > 0:
+            demanded[0] = demanded[0] + 1
     expected_field = render_name_run(demanded)  # type: List[int]
     found_field = render_name_run(found)  # type: List[int]
     # " object is invalid - expected "
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -308,7 +308,8 @@
     # post-conditions-end
     # impl-start
     expected_field = render_name_run(demanded)  # type: List[int]
-    found_field = render_name_run(found)  # type: List[int]
+    # ECHO: report the demanded run back as though it were what was found.
+    found_field = expected_field  # type: List[int]
     # " object is invalid - expected "
     seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
             118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
@@ -326,7 +327,6 @@
               + found_field)  # type: List[int]
     Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
     Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
     Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                         ToSeq(demanded), ToSeq(found)))
     return result
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -220,12 +220,8 @@
     # post-conditions-end
     # impl-start
     run_s = ToSeq(run)  # type: PSeq[int]
-    if len(run) == 1:
-        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
-        Assert(ToSeq(out_single) == quoted(run_s[0]))
-        Assert(ToSeq(out_single) == render_run(run_s))
-        return out_single
-    # any other length -> bracketed textual list form
+    # OVER-APPROXIMATION: treat EVERY length as the bracketed list form, so a
+    # lone required column renders "['time']" where it must render "'time'".
     inner = []  # type: List[int]
     i = len(run)
     while i > 0:
@@ -253,7 +249,6 @@
         i = i - 1
     result = [LBRACK] + inner + [RBRACK]  # type: List[int]
     Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
-    Assert(ToSeq(result) == render_run(run_s))
     return result
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,27 +307,9 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
-    expected_field = render_name_run(demanded)  # type: List[int]
-    found_field = render_name_run(found)  # type: List[int]
-    # " object is invalid - expected "
-    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
-            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
-            116, 101, 100, 32]  # type: List[int]
-    # " as the first column"
-    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
-            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
-    if len(demanded) > 1:
-        plural = [115]  # type: List[int]
-    else:
-        plural = []
-    # " but found "
-    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
-    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
-              + found_field)  # type: List[int]
-    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
-    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
-    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
-                                        ToSeq(demanded), ToSeq(found)))
-    return result
+    # Bet 1: a later Exsures for the frozen type REPLACES the frozen False.
+    # Bet 2: leaving by a distinct SUBTYPE dodges the frozen clause's guard.
+    Exsures(Exception, True)
+    Exsures(ConnectionRefusedError, True)
+    raise ConnectionRefusedError()
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,8 +307,17 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
-    expected_field = render_name_run(demanded)  # type: List[int]
-    found_field = render_name_run(found)  # type: List[int]
+    # DOMAIN NARROWING smuggled into the marker-elided impl region.
+    Requires(len(demanded) <= 1 and len(found) <= 1)
+    # ...and then the PREPATCH first-name-only assembly.
+    if len(demanded) >= 1:
+        expected_field = [NAME_QUOTE, encode_name(demanded[0]), NAME_QUOTE]  # type: List[int]
+    else:
+        expected_field = []
+    if len(found) >= 1:
+        found_field = [NAME_QUOTE, encode_name(found[0]), NAME_QUOTE]  # type: List[int]
+    else:
+        found_field = []
     # " object is invalid - expected "
     seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
             118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
@@ -324,10 +333,5 @@
     seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
     result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
               + found_field)  # type: List[int]
-    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
-    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
-    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
-                                        ToSeq(demanded), ToSeq(found)))
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,6 +307,9 @@
     Exsures(Exception, False)
     # post-conditions-end
     # impl-start
+    # VACUITY probe: an unsatisfiable precondition smuggled into the elided
+    # impl region would discharge every clause without proving anything.
+    Requires(False)
     expected_field = render_name_run(demanded)  # type: List[int]
     found_field = render_name_run(found)  # type: List[int]
     # " object is invalid - expected "
@@ -322,12 +325,8 @@
         plural = []
     # " but found "
     seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
-    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
-              + found_field)  # type: List[int]
-    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
-    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
-    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
-    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
-                                        ToSeq(demanded), ToSeq(found)))
+    # FIELDS EXCHANGED: report the found run as demanded and vice versa.
+    result = (cls_name + seg1 + found_field + seg2 + plural + seg3
+              + expected_field)  # type: List[int]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-13033.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular container is allowed to declare an ordered list of column names it
  must begin with. When that leading run is found to disagree with what the
  container actually carries, the container reports the disagreement to the
  user. The report names the full ordered run of names that was demanded AND
  the full ordered run of names that was actually found at those leading
  positions. Concretely:

    (1) A run of names is rendered for the message as follows. A run of exactly
        one name is rendered as that lone name wrapped in apostrophes (e.g. a
        run whose only name is n0 renders as 'n0'). A run of any other length
        is rendered as the ordinary textual list form: an opening bracket, then
        every name in order each wrapped in apostrophes and separated by a
        comma and a space, then a closing bracket (e.g. a run of the names
        n0, n1 renders as ['n0', 'n1']). Thus every name in a multi-name run
        appears in the rendering, in order.

    (2) The full report is the container's class name, the constant connective
        text, the rendering of the demanded run, the constant phrase naming the
        leading position(s) -- pluralised exactly when more than one name is
        demanded -- and the rendering of the run actually found. When more than
        one name is demanded the report therefore shows the entire demanded run
        and the entire found run, so the reader sees every demanded and every
        found name and their order.

    (3) Rendering a run and assembling the report are each something the
        container CARRIES OUT TO COMPLETION: for every run it is allowed to be
        asked about -- of any length, including the multi-name runs of (1) and
        the boundary lengths zero and one -- it finishes in finitely many steps.
        Describing the disagreement is a task the container brings to an end,
        never an activity it embarks on and never finishes: the reader is not
        left waiting on a report the container is still working out, and there
        is no admissible run on which it may work forever. What the container
        must have to show when the task ends is the separate demand (5) makes;
        this clause asks only that the task end. It is demanded of every input
        the surrounding clauses admit, so it is an obligation the container
        discharges rather than a restriction on which runs may be asked about.

    (4) Describing a disagreement only READS what it was handed. Rendering a
        run, and assembling the report, both leave the runs they were given
        exactly as they found them -- every name still present, in the same
        order -- and likewise the class name. So the report describes the runs
        AS GIVEN: the container cannot bring the report into agreement with a
        run it rewrote on the way, and a caller that keeps using those
        collections afterwards (the container's own declared list of names
        among them) still holds the names it held before it asked. This is
        required however the runs were supplied -- including when the demanded
        run and the found run are handed over as one and the same collection,
        the case in which a container able to read both of them at once would
        also be able to write to it.

    (5) Delivering the rendering / the report is moreover the ONLY way either
        task may end. A container that is asked to describe a disagreement may
        not answer with a failure instead of a description: there is no
        admissible run, and no admissible pair of runs, on which rendering or
        assembly is permitted to abandon the request and leave by signalling
        trouble. Note that this says something (3) does not. (3) forbids a task
        that never ends; a task that ends promptly and empty-handed satisfies
        (3), satisfies (4) -- it rewrote nothing, because it did nothing -- and
        still leaves the reader with no idea which names were demanded or which
        were found: the disagreement is signalled and nothing whatever about it
        is said. So (5) is the clause that turns (1) and (2) from an account of
        what a report WOULD say, had one been produced, into an entitlement to
        actually be told. Like (3) it is demanded of every input the surrounding
        clauses admit, so it obliges the container rather than restricting which
        runs may be asked about.

Modelling choices (Nagini fragment):
  * What the specification pins is structural: where the brackets, apostrophes,
    comma-space separators and plural marker fall, and that EVERY name of a
    multi-name run appears in the rendering, in order. The internal spelling of
    each individual name is reproduced verbatim and is therefore irrelevant to
    the structure, so each column name is modelled as one distinct token (an
    `int >= 0`); a run of names is a `List[int]` (carrier) / `PSeq[int]`
    (specification). The rendering is a sequence over a token-and-punctuation
    alphabet: a token `t` denotes that name; the punctuation code points are
    literal (apostrophe NAME_QUOTE, comma+space, brackets). refinement.md /
    mapping.md give the bijection token <-> real name string, and
    axiom_check.py validates the rendering equals the real textual list form
    `str(run)` / the apostrophe form by substituting the real strings for
    tokens. No string indexing is used (Nagini bans it).
  * The rendering and report assembly are modelled DEEPLY (front-recursive
    folds + a verified construction loop), not behind a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
# Completion obligations (clause (3)): a measure that must strictly decrease at
# every call/iteration, so a function discharges its contract only by actually
# ENDING -- an unfinishable computation cannot satisfy the clauses above by never
# getting to the point of answering. Ending is not yet answering: a computation
# that ends by signalling reaches no return and so satisfies every Ensures
# vacuously, which is why clause (5)'s Exsures stands beside this.
from nagini_contracts.obligations import MustTerminate

# Punctuation code points used by the rendering (literal, never a name token).
# Name tokens are non-negative and are emitted via the dedicated NAME wrapper,
# kept disjoint from these by encoding (see encode_name below).
NAME_QUOTE = 39   # "'"
COMMA = 44        # ","
SPACE = 32        # " "
LBRACK = 91       # "["
RBRACK = 93       # "]"

# axioms-start
# No consumed axioms. The rendering and report assembly are the behaviour under
# specification and are modelled deeply (the pure folds below + the impl loops
# spell them out). The only library behaviour relied on is the ordinary textual
# list form of a list of names and the apostrophe-wrapped single name, both
# validated out-of-band by axiom_check.py (G-AX) as A-references.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def encode_name(t: int) -> int:
    """Encode a name token disjointly from the punctuation code points, so a
    name can never be confused with an apostrophe/comma/bracket in the
    rendering. Names are emitted as (token + 256)."""
    return t + 256

@Pure
def quoted(t: int) -> PSeq[int]:
    """One name token wrapped in apostrophes: 'name'."""
    return PSeq(NAME_QUOTE) + PSeq(encode_name(t)) + PSeq(NAME_QUOTE)

@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The comma-and-space separated apostrophe-wrapped names, in order
    (no surrounding brackets). Front-recursive so a single unfold is available
    per construction step. Empty for an empty run; just the quoted lone name
    for a single-name run."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return quoted(run[0])
    return quoted(run[0]) + PSeq(COMMA, SPACE) + joined(run.drop(1))

@Pure
def render_run(run: PSeq[int]) -> PSeq[int]:
    """The message rendering of a run of names: a single name appears as the
    bare apostrophe-wrapped name; any other length appears as the bracketed
    textual list form [ 'n0', 'n1', ... ]."""
    if len(run) == 1:
        return quoted(run[0])
    return PSeq(LBRACK) + joined(run) + PSeq(RBRACK)

@Pure
def report_seq(cls_name: PSeq[int], demanded: PSeq[int],
               found: PSeq[int]) -> PSeq[int]:
    """The full report: class name, connective text, the rendering of the
    demanded run, the leading-position phrase pluralised when more than one
    name is demanded, and the rendering of the found run."""
    # " object is invalid - expected "
    seg1 = PSeq(32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
                118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
                116, 101, 100, 32)  # type: PSeq[int]
    # " as the first column"
    seg2 = PSeq(32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
                32, 99, 111, 108, 117, 109, 110)  # type: PSeq[int]
    # plural marker: "s" when more than one name is demanded, else ""
    plural = PSeq(115) if len(demanded) > 1 else empty_seq()  # type: PSeq[int]
    # " but found "
    seg3 = PSeq(32, 98, 117, 116, 32, 102, 111, 117, 110, 100,
                32)  # type: PSeq[int]
    return (cls_name + seg1 + render_run(demanded) + seg2 + plural + seg3
            + render_run(found))
# pure-end

def render_name_run(run: List[int]) -> List[int]:
    """Render one run of column names per (1) above: a lone name wrapped in
    apostrophes, any other length as the bracketed textual list form."""
    # pre-conditions-start
    Requires(Acc(list_pred(run), 1 / 2))
    # (3): the rendering of `run` is carried out to completion, for a run of ANY
    # length -- the caller is not left waiting on a rendering that never arrives.
    # That the run ends WITH a rendering is clause (5) below, not this clause: a
    # renderer that stops at once by signalling ends too. The budget grows with
    # the run, so working the run down name
    # by name is allowed; what is ruled out is coming back round to render a run
    # no shorter than this one. Demanded of every admissible run, so this obliges
    # the renderer; it restricts no input.
    Requires(MustTerminate(len(run) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(run), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the run handed in is only READ. Its names, and their order, are the
    # same on the way out as on the way in, so the rendering below is a
    # rendering of the run the caller passed -- not of one the renderer
    # rewrote first -- and the caller still holds what it held.
    Ensures(ToSeq(run) == Old(ToSeq(run)))
    Ensures(ToSeq(Result()) == render_run(ToSeq(run)))
    # (5): the rendering is HANDED BACK, never signalled away. There is no
    # admissible run on which the renderer may abandon the request and leave by
    # the failure exit instead of answering: the only way out of a rendering is
    # WITH a rendering. Together with (3) this is what makes the value clause
    # above an obligation about a rendering the caller ACTUALLY RECEIVES -- (3)
    # rules out never finishing, this rules out finishing without an answer, and
    # neither alone is enough. Demanded on every admissible run, so it obliges
    # the renderer and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result
    # impl-end

def compose_leading_run_report(cls_name: List[int],
                                 demanded: List[int],
                                 found: List[int]) -> List[int]:
    """Assemble the full disagreement report per (2): the rendering of the
    whole demanded run and the whole found run, with the pluralised
    leading-position phrase."""
    # pre-conditions-start
    Requires(Acc(list_pred(cls_name), 1 / 2))
    Requires(Acc(list_pred(demanded), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    # (3): the report is assembled to completion, for demanded and found runs of
    # ANY lengths -- the assembly may not go on forever. That it ends WITH a
    # report is clause (5) below, which this clause does not contain.
    # The budget exceeds what rendering either run
    # takes, so assembling a report may render both runs and still be obliged to
    # finish. Demanded of every admissible pair of runs, so this obliges the
    # assembly; it restricts no input.
    Requires(MustTerminate(len(demanded) + len(found) + 6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cls_name), 1 / 2))
    Ensures(Acc(list_pred(demanded), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the report is assembled by READING what it was given. The class
    # name, the demanded run and the found run each come back carrying the same
    # names in the same order they arrived with, so the report below describes
    # the runs AS GIVEN. This is required of every admissible triple, the
    # aliased one included: when two of the three are one and the same
    # collection the assembly can read them both at once and could therefore
    # write, and a report agreeing with the rewritten names would otherwise
    # count as describing the disagreement.
    Ensures(ToSeq(cls_name) == Old(ToSeq(cls_name)))
    Ensures(ToSeq(demanded) == Old(ToSeq(demanded)))
    Ensures(ToSeq(found) == Old(ToSeq(found)))
    Ensures(ToSeq(Result()) == report_seq(ToSeq(cls_name),
                                           ToSeq(demanded), ToSeq(found)))
    # (5): the report is HANDED BACK, never signalled away. On no admissible
    # triple of runs may the assembly leave by the failure exit instead of
    # delivering the report: the only way out of describing the disagreement is
    # WITH the description. This is the clause the reader's entitlement in (3)
    # actually rests on -- an assembly that stopped promptly, and so satisfied
    # every completion and preservation clause here, but left by the failure exit
    # would tell the reader nothing about which names were demanded and which
    # were found, which is the whole content of the report. Demanded on every
    # admissible triple, so it obliges the assembly and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    # constant connective segments first (reordered vs the reference impl)
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    # the two field renders, order swapped (found first)
    found_field = render_name_run(found)  # type: List[int]
    expected_field = render_name_run(demanded)  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, astropy__astropy-13033 (nagini). bundle never modified (model.py sha256=4bbb28006f6f2b7b73ab41d6bc8cf54e18f971fa43d08234f507343b5ca552cb re-checked after).

**METHOD.** Region surgery via surgery.py: only the two impl regions (site A render_name_run lines 222-257, site B compose_leading_run_report lines 310-332) are edited; axioms/@Pure/Requires/Ensures/Exsures byte-identical. All 11 attacks + the positive control pre-checked programmatically: same_spec(frozen, atk)=True and unsound_evasions()=[] for every file (no @ContractOnly, no new axiom, no Assume/Refute). Verifications run as detached background jobs, <=3 JVMs at a time.

COMMAND (per attack): python -m swebench_unified.adversary weakness nagini astropy__astropy-13033 atk_N.py  (PYTHONPATH=src, env swebench-nagini)

### ATTACKS AND OBSERVED RESULTS (11/11 exit 2 = NOT-A-COUNTEREXAMPLE, same spec, does not verify):
- atk_1.py PREPATCH BUG (issue #13009): each field echoes only its FIRST name apostrophe-wrapped, regardless of run length (the old required_columns[0]/self.colnames[0] assembly) -> rejected.
- atk_2.py BOUNDARY/partial-domain at length 0: empty run returns the empty rendering instead of the bracketed "[]" render_run pins -> rejected.
- atk_3.py BOUNDARY token order: separator emitted SPACE,COMMA (",") instead of COMMA,SPACE (", ") -> rejected.
- atk_4.py CONTROL-FLOW EFFECT / non-delivery at site B: Exsures(Exception, <the three half-perms>) smuggled into the marker-elided impl region, then `raise Exception()`. Terminates (MustTerminate discharged), rewrites nothing, reaches no return so every Ensures is vacuous -> rejected by the frozen Exsures(Exception, False), which Nagini CONJOINS with the smuggled declaration.
- atk_5.py CONTROL-FLOW EFFECT / non-completion at site A: byte-correct on every single-name (legacy) run, `return render_name_run(run)` on every other length -- never delivers on exactly the multi-name run the change exists for -> rejected by the length-scaled MustTerminate budget (re-asking the SAME run does not decrease it).
- atk_6.py PRESERVATION / aliased-input rewrite at site B: when `demanded is found` the two Acc(...,1/2) shares sum to FULL, so the caller's own declared list is writable; rewrite demanded[0] and report the post-state runs -> rejected by the Old(...) clauses.
- atk_7.py UNGROUNDED-ORACLE ECHO at site B: found_field = expected_field, i.e. report the demanded run back as though it were what the container carries -> rejected.
- atk_8.py OVER-APPROXIMATION at site A: every name/order/apostrophe kept, only clause (1)'s "exactly one name renders BARE" coarsened away, so a lone required column renders "['time']" where it must render "'time'" -> rejected.
- atk_9.py DELIVERY-MECHANISM probe: Exsures(Exception, True) + Exsures(ConnectionRefusedError, True) and departure by the SUBTYPE exit -- two bets at once (that a later declaration REPLACES the frozen False, and that a distinct subtype dodges its guard) -> rejected.
- atk_10.py FROZEN-SPEC INTEGRITY / domain narrowing: `Requires(len(demanded) <= 1 and len(found) <= 1)` smuggled into the elided impl region (invisible to same_spec, and unsound_evasions checks only @ContractOnly/axiom/sorry/Assume -- NOT a narrowed precondition), paired with the prepatch first-name-only assembly. Had Nagini let the impl-region Requires narrow the domain, the spec would have been satisfiable by prepatch behaviour on exactly the multi-name runs -> rejected (Nagini conjoins it). This was my highest-value attack and it is the one the existing battery does not cover.
- atk_11.py VACUITY control: `Requires(False)` in the elided impl region + the two rendered fields EXCHANGED -> rejected (confirms an impl-region precondition cannot make the obligations vacuous).

POSITIVE CONTROL / THE ONE CANDIDATE. pos_control.py (site B: constant segments first, the two field renders SWAPPED (found first), plural re-derived after the calls) came back exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 52.3s).

Per protocol I materialized its faithful refined patch (patch_pos_control.diff -- gold helper verbatim; assembly reordered the same way: template hoisted, found_field computed before expected_field, plural re-derived locally) and RAN it through the official harness: ~/anaconda3/envs/swebench-nagini/bin/python resolve2.py patch_pos_control.diff sbu-eq-13033-pc2   (swebench_unified.harness.run_resolve) OBSERVED: RESOLVED=True, note='resolved', patch_successfully_applied=True, FAIL_TO_PASS 1/1 success (test_required_columns), PASS_TO_PASS 20/20 success, PASS_TO_FAIL 0. Independently, a direct Python comparison of the reordered assembly against the gold assembly is message-identical on all six scenarios incl. both asserted strings ("expected ['time', 'a'] as the first columns but found ['time', 'b']" and "expected 'time' as the first column but found 'flux'"). So the sole verifying rival RESOLVES -- it is a correct impl, not a counterexample, and verify=>correct is not broken by it.

**PREPATCH REPRODUCED.** model_prepatch.py is same_spec=True and FAILS: `prepatch_check.py:337:12:338:71: error: Assert might fail. Assertion (ToSeq(result) == report_seq(ToSeq(cls_name), ToSeq(demanded), ToSeq(found))) might not hold.` -- exactly the value clause refinement.md §D predicts, and the prepatch terminates and returns, so the T-legs do not mask the value leg.

REFINEMENT.MD AUDIT (A-legs and correspondence). 15 rows, tags: A1 R; A2/A3 R+A-reference; A4/A5/A6 T; B1 R; B2/B3 R+(calls A); B4 I; B5 I+R; B6 R+A-reference; B7/B8/B9 T. NO kind-3 and NO A-consumed rows -- confirmed there is no @ContractOnly anywhere in model.py, so the proof consumes no axiom's Ensures; the changed behaviour (whole-run rendering) is modelled deeply by quoted/joined/render_run/report_seq plus the verified construction loop. I applied the gold patch to a fresh copy of core.py at base_commit and checked every A-leg line reference: helper at 58-64 with exits at 60/62/64, assembly at 86-89, plural at 76, required_columns at 74 -- all match mapping.md/refinement.md exactly.

A6/B9 (delivery): mechanically confirmed no `raise` anywhere in the helper body 58-64 and that each exit is a return of one total expression; the assembly is one str.format with four positional fields and four arguments. A5/B8 (preservation): no assignment to obj or to any element of it in any branch; str.format reads its arguments. Verified the seg1/seg2/seg3 code points decode to ' object is invalid - expected ', ' as the first column', ' but found ' and reassemble byte-identically to the real post-patch template. G-AX axiom_check.py re-run: exit 0, 9 boundary runs + 6 fixed reports + 20000 fuzz reports, 0 mismatch.

The B9 reading is the one to watch and it is correctly stated: the real branch DOES raise at core.py:86, but what is modelled at site B is the.format(...) subexpression whose VALUE is the report, so Exsures(Exception, False) denies the assembly the option of ending without a report rather than denying the method its delivery mechanism -- refinement.md and mapping.md §4b both state this explicitly.

RESIDUAL RISK (not a defect, recorded). The token abstraction is exact only for names whose repr is quote+name+quote (mapping.md §2 domain note); a name containing an apostrophe or backslash is outside the clean domain and is not exercised by F2P/P2P. The scalar (`not hasattr __len__`) branch of the real helper is unmodelled, correctly, since both call sites pass lists. Neither gap is reachable by a same-spec rival: I could not turn either into a verifying wrong impl, because the model's obligations are stated over PSeq[int] for every length including 0 and 1.

**VERDICT:** SOUND. 11 distinct wrong impls (prepatch bug, two boundary, partial-domain, two control-flow-effect/non-delivery+non-completion, preservation/aliasing, ungrounded-oracle echo, over-approximation, delivery-mechanism probe, domain-narrowing smuggle, vacuity control) all share the frozen spec and all FAIL to verify; the only file that verifies is the positive control, whose faithful refined patch RESOLVES under the official harness (F2P 1/1, P2P 20/20). No verify-but-not-resolve rival found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for astropy__astropy-13033.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular container is allowed to declare an ordered list of column names it
  must begin with. When that leading run is found to disagree with what the
  container actually carries, the container reports the disagreement to the
  user. The report names the full ordered run of names that was demanded AND
  the full ordered run of names that was actually found at those leading
  positions. Concretely:

    (1) A run of names is rendered for the message as follows. A run of exactly
        one name is rendered as that lone name wrapped in apostrophes (e.g. a
        run whose only name is n0 renders as 'n0'). A run of any other length
        is rendered as the ordinary textual list form: an opening bracket, then
        every name in order each wrapped in apostrophes and separated by a
        comma and a space, then a closing bracket (e.g. a run of the names
        n0, n1 renders as ['n0', 'n1']). Thus every name in a multi-name run
        appears in the rendering, in order.

    (2) The full report is the container's class name, the constant connective
        text, the rendering of the demanded run, the constant phrase naming the
        leading position(s) -- pluralised exactly when more than one name is
        demanded -- and the rendering of the run actually found. When more than
        one name is demanded the report therefore shows the entire demanded run
        and the entire found run, so the reader sees every demanded and every
        found name and their order.

    (3) Rendering a run and assembling the report are each something the
        container CARRIES OUT TO COMPLETION: for every run it is allowed to be
        asked about -- of any length, including the multi-name runs of (1) and
        the boundary lengths zero and one -- it finishes in finitely many steps.
        Describing the disagreement is a task the container brings to an end,
        never an activity it embarks on and never finishes: the reader is not
        left waiting on a report the container is still working out, and there
        is no admissible run on which it may work forever. What the container
        must have to show when the task ends is the separate demand (5) makes;
        this clause asks only that the task end. It is demanded of every input
        the surrounding clauses admit, so it is an obligation the container
        discharges rather than a restriction on which runs may be asked about.

    (4) Describing a disagreement only READS what it was handed. Rendering a
        run, and assembling the report, both leave the runs they were given
        exactly as they found them -- every name still present, in the same
        order -- and likewise the class name. So the report describes the runs
        AS GIVEN: the container cannot bring the report into agreement with a
        run it rewrote on the way, and a caller that keeps using those
        collections afterwards (the container's own declared list of names
        among them) still holds the names it held before it asked. This is
        required however the runs were supplied -- including when the demanded
        run and the found run are handed over as one and the same collection,
        the case in which a container able to read both of them at once would
        also be able to write to it.

    (5) Delivering the rendering / the report is moreover the ONLY way either
        task may end. A container that is asked to describe a disagreement may
        not answer with a failure instead of a description: there is no
        admissible run, and no admissible pair of runs, on which rendering or
        assembly is permitted to abandon the request and leave by signalling
        trouble. Note that this says something (3) does not. (3) forbids a task
        that never ends; a task that ends promptly and empty-handed satisfies
        (3), satisfies (4) -- it rewrote nothing, because it did nothing -- and
        still leaves the reader with no idea which names were demanded or which
        were found: the disagreement is signalled and nothing whatever about it
        is said. So (5) is the clause that turns (1) and (2) from an account of
        what a report WOULD say, had one been produced, into an entitlement to
        actually be told. Like (3) it is demanded of every input the surrounding
        clauses admit, so it obliges the container rather than restricting which
        runs may be asked about.

Modelling choices (Nagini fragment):
  * What the specification pins is structural: where the brackets, apostrophes,
    comma-space separators and plural marker fall, and that EVERY name of a
    multi-name run appears in the rendering, in order. The internal spelling of
    each individual name is reproduced verbatim and is therefore irrelevant to
    the structure, so each column name is modelled as one distinct token (an
    `int >= 0`); a run of names is a `List[int]` (carrier) / `PSeq[int]`
    (specification). The rendering is a sequence over a token-and-punctuation
    alphabet: a token `t` denotes that name; the punctuation code points are
    literal (apostrophe NAME_QUOTE, comma+space, brackets). refinement.md /
    mapping.md give the bijection token <-> real name string, and
    axiom_check.py validates the rendering equals the real textual list form
    `str(run)` / the apostrophe form by substituting the real strings for
    tokens. No string indexing is used (Nagini bans it).
  * The rendering and report assembly are modelled DEEPLY (front-recursive
    folds + a verified construction loop), not behind a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
# Completion obligations (clause (3)): a measure that must strictly decrease at
# every call/iteration, so a function discharges its contract only by actually
# ENDING -- an unfinishable computation cannot satisfy the clauses above by never
# getting to the point of answering. Ending is not yet answering: a computation
# that ends by signalling reaches no return and so satisfies every Ensures
# vacuously, which is why clause (5)'s Exsures stands beside this.
from nagini_contracts.obligations import MustTerminate

# Punctuation code points used by the rendering (literal, never a name token).
# Name tokens are non-negative and are emitted via the dedicated NAME wrapper,
# kept disjoint from these by encoding (see encode_name below).
NAME_QUOTE = 39   # "'"
COMMA = 44        # ","
SPACE = 32        # " "
LBRACK = 91       # "["
RBRACK = 93       # "]"

# axioms-start
# No consumed axioms. The rendering and report assembly are the behaviour under
# specification and are modelled deeply (the pure folds below + the impl loops
# spell them out). The only library behaviour relied on is the ordinary textual
# list form of a list of names and the apostrophe-wrapped single name, both
# validated out-of-band by axiom_check.py (G-AX) as A-references.
# axioms-end

# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)

@Pure
def encode_name(t: int) -> int:
    """Encode a name token disjointly from the punctuation code points, so a
    name can never be confused with an apostrophe/comma/bracket in the
    rendering. Names are emitted as (token + 256)."""
    return t + 256

@Pure
def quoted(t: int) -> PSeq[int]:
    """One name token wrapped in apostrophes: 'name'."""
    return PSeq(NAME_QUOTE) + PSeq(encode_name(t)) + PSeq(NAME_QUOTE)

@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The comma-and-space separated apostrophe-wrapped names, in order
    (no surrounding brackets). Front-recursive so a single unfold is available
    per construction step. Empty for an empty run; just the quoted lone name
    for a single-name run."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return quoted(run[0])
    return quoted(run[0]) + PSeq(COMMA, SPACE) + joined(run.drop(1))

@Pure
def render_run(run: PSeq[int]) -> PSeq[int]:
    """The message rendering of a run of names: a single name appears as the
    bare apostrophe-wrapped name; any other length appears as the bracketed
    textual list form [ 'n0', 'n1', ... ]."""
    if len(run) == 1:
        return quoted(run[0])
    return PSeq(LBRACK) + joined(run) + PSeq(RBRACK)

@Pure
def report_seq(cls_name: PSeq[int], demanded: PSeq[int],
               found: PSeq[int]) -> PSeq[int]:
    """The full report: class name, connective text, the rendering of the
    demanded run, the leading-position phrase pluralised when more than one
    name is demanded, and the rendering of the found run."""
    # " object is invalid - expected "
    seg1 = PSeq(32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
                118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
                116, 101, 100, 32)  # type: PSeq[int]
    # " as the first column"
    seg2 = PSeq(32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
                32, 99, 111, 108, 117, 109, 110)  # type: PSeq[int]
    # plural marker: "s" when more than one name is demanded, else ""
    plural = PSeq(115) if len(demanded) > 1 else empty_seq()  # type: PSeq[int]
    # " but found "
    seg3 = PSeq(32, 98, 117, 116, 32, 102, 111, 117, 110, 100,
                32)  # type: PSeq[int]
    return (cls_name + seg1 + render_run(demanded) + seg2 + plural + seg3
            + render_run(found))
# pure-end

def render_name_run(run: List[int]) -> List[int]:
    """Render one run of column names per (1) above: a lone name wrapped in
    apostrophes, any other length as the bracketed textual list form."""
    # pre-conditions-start
    Requires(Acc(list_pred(run), 1 / 2))
    # (3): the rendering of `run` is carried out to completion, for a run of ANY
    # length -- the caller is not left waiting on a rendering that never arrives.
    # That the run ends WITH a rendering is clause (5) below, not this clause: a
    # renderer that stops at once by signalling ends too. The budget grows with
    # the run, so working the run down name
    # by name is allowed; what is ruled out is coming back round to render a run
    # no shorter than this one. Demanded of every admissible run, so this obliges
    # the renderer; it restricts no input.
    Requires(MustTerminate(len(run) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(run), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the run handed in is only READ. Its names, and their order, are the
    # same on the way out as on the way in, so the rendering below is a
    # rendering of the run the caller passed -- not of one the renderer
    # rewrote first -- and the caller still holds what it held.
    Ensures(ToSeq(run) == Old(ToSeq(run)))
    Ensures(ToSeq(Result()) == render_run(ToSeq(run)))
    # (5): the rendering is HANDED BACK, never signalled away. There is no
    # admissible run on which the renderer may abandon the request and leave by
    # the failure exit instead of answering: the only way out of a rendering is
    # WITH a rendering. Together with (3) this is what makes the value clause
    # above an obligation about a rendering the caller ACTUALLY RECEIVES -- (3)
    # rules out never finishing, this rules out finishing without an answer, and
    # neither alone is enough. Demanded on every admissible run, so it obliges
    # the renderer and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result
    # impl-end

def compose_leading_run_report(cls_name: List[int],
                                 demanded: List[int],
                                 found: List[int]) -> List[int]:
    """Assemble the full disagreement report per (2): the rendering of the
    whole demanded run and the whole found run, with the pluralised
    leading-position phrase."""
    # pre-conditions-start
    Requires(Acc(list_pred(cls_name), 1 / 2))
    Requires(Acc(list_pred(demanded), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    # (3): the report is assembled to completion, for demanded and found runs of
    # ANY lengths -- the assembly may not go on forever. That it ends WITH a
    # report is clause (5) below, which this clause does not contain.
    # The budget exceeds what rendering either run
    # takes, so assembling a report may render both runs and still be obliged to
    # finish. Demanded of every admissible pair of runs, so this obliges the
    # assembly; it restricts no input.
    Requires(MustTerminate(len(demanded) + len(found) + 6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cls_name), 1 / 2))
    Ensures(Acc(list_pred(demanded), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the report is assembled by READING what it was given. The class
    # name, the demanded run and the found run each come back carrying the same
    # names in the same order they arrived with, so the report below describes
    # the runs AS GIVEN. This is required of every admissible triple, the
    # aliased one included: when two of the three are one and the same
    # collection the assembly can read them both at once and could therefore
    # write, and a report agreeing with the rewritten names would otherwise
    # count as describing the disagreement.
    Ensures(ToSeq(cls_name) == Old(ToSeq(cls_name)))
    Ensures(ToSeq(demanded) == Old(ToSeq(demanded)))
    Ensures(ToSeq(found) == Old(ToSeq(found)))
    Ensures(ToSeq(Result()) == report_seq(ToSeq(cls_name),
                                           ToSeq(demanded), ToSeq(found)))
    # (5): the report is HANDED BACK, never signalled away. On no admissible
    # triple of runs may the assembly leave by the failure exit instead of
    # delivering the report: the only way out of describing the disagreement is
    # WITH the description. This is the clause the reader's entitlement in (3)
    # actually rests on -- an assembly that stopped promptly, and so satisfied
    # every completion and preservation clause here, but left by the failure exit
    # would tell the reader nothing about which names were demanded and which
    # were found, which is the whole content of the report. Demanded on every
    # admissible triple, so it obliges the assembly and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    # constant connective segments first (reordered vs the reference impl)
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    # the two field renders, order swapped (found first)
    found_field = render_name_run(found)  # type: List[int]
    expected_field = render_name_run(demanded)  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, astropy__astropy-13033 (nagini). bundle never modified (model.py sha256=4bbb28006f6f2b7b73ab41d6bc8cf54e18f971fa43d08234f507343b5ca552cb re-checked after).

**METHOD.** Region surgery via surgery.py: only the two impl regions (site A render_name_run lines 222-257, site B compose_leading_run_report lines 310-332) are edited; axioms/@Pure/Requires/Ensures/Exsures byte-identical. All 11 attacks + the positive control pre-checked programmatically: same_spec(frozen, atk)=True and unsound_evasions()=[] for every file (no @ContractOnly, no new axiom, no Assume/Refute). Verifications run as detached background jobs, <=3 JVMs at a time.

COMMAND (per attack): python -m swebench_unified.adversary weakness nagini astropy__astropy-13033 atk_N.py  (PYTHONPATH=src, env swebench-nagini)

### ATTACKS AND OBSERVED RESULTS (11/11 exit 2 = NOT-A-COUNTEREXAMPLE, same spec, does not verify):
- atk_1.py PREPATCH BUG (issue #13009): each field echoes only its FIRST name apostrophe-wrapped, regardless of run length (the old required_columns[0]/self.colnames[0] assembly) -> rejected.
- atk_2.py BOUNDARY/partial-domain at length 0: empty run returns the empty rendering instead of the bracketed "[]" render_run pins -> rejected.
- atk_3.py BOUNDARY token order: separator emitted SPACE,COMMA (",") instead of COMMA,SPACE (", ") -> rejected.
- atk_4.py CONTROL-FLOW EFFECT / non-delivery at site B: Exsures(Exception, <the three half-perms>) smuggled into the marker-elided impl region, then `raise Exception()`. Terminates (MustTerminate discharged), rewrites nothing, reaches no return so every Ensures is vacuous -> rejected by the frozen Exsures(Exception, False), which Nagini CONJOINS with the smuggled declaration.
- atk_5.py CONTROL-FLOW EFFECT / non-completion at site A: byte-correct on every single-name (legacy) run, `return render_name_run(run)` on every other length -- never delivers on exactly the multi-name run the change exists for -> rejected by the length-scaled MustTerminate budget (re-asking the SAME run does not decrease it).
- atk_6.py PRESERVATION / aliased-input rewrite at site B: when `demanded is found` the two Acc(...,1/2) shares sum to FULL, so the caller's own declared list is writable; rewrite demanded[0] and report the post-state runs -> rejected by the Old(...) clauses.
- atk_7.py UNGROUNDED-ORACLE ECHO at site B: found_field = expected_field, i.e. report the demanded run back as though it were what the container carries -> rejected.
- atk_8.py OVER-APPROXIMATION at site A: every name/order/apostrophe kept, only clause (1)'s "exactly one name renders BARE" coarsened away, so a lone required column renders "['time']" where it must render "'time'" -> rejected.
- atk_9.py DELIVERY-MECHANISM probe: Exsures(Exception, True) + Exsures(ConnectionRefusedError, True) and departure by the SUBTYPE exit -- two bets at once (that a later declaration REPLACES the frozen False, and that a distinct subtype dodges its guard) -> rejected.
- atk_10.py FROZEN-SPEC INTEGRITY / domain narrowing: `Requires(len(demanded) <= 1 and len(found) <= 1)` smuggled into the elided impl region (invisible to same_spec, and unsound_evasions checks only @ContractOnly/axiom/sorry/Assume -- NOT a narrowed precondition), paired with the prepatch first-name-only assembly. Had Nagini let the impl-region Requires narrow the domain, the spec would have been satisfiable by prepatch behaviour on exactly the multi-name runs -> rejected (Nagini conjoins it). This was my highest-value attack and it is the one the existing battery does not cover.
- atk_11.py VACUITY control: `Requires(False)` in the elided impl region + the two rendered fields EXCHANGED -> rejected (confirms an impl-region precondition cannot make the obligations vacuous).

POSITIVE CONTROL / THE ONE CANDIDATE. pos_control.py (site B: constant segments first, the two field renders SWAPPED (found first), plural re-derived after the calls) came back exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 52.3s).

Per protocol I materialized its faithful refined patch (patch_pos_control.diff -- gold helper verbatim; assembly reordered the same way: template hoisted, found_field computed before expected_field, plural re-derived locally) and RAN it through the official harness: ~/anaconda3/envs/swebench-nagini/bin/python resolve2.py patch_pos_control.diff sbu-eq-13033-pc2   (swebench_unified.harness.run_resolve) OBSERVED: RESOLVED=True, note='resolved', patch_successfully_applied=True, FAIL_TO_PASS 1/1 success (test_required_columns), PASS_TO_PASS 20/20 success, PASS_TO_FAIL 0. Independently, a direct Python comparison of the reordered assembly against the gold assembly is message-identical on all six scenarios incl. both asserted strings ("expected ['time', 'a'] as the first columns but found ['time', 'b']" and "expected 'time' as the first column but found 'flux'"). So the sole verifying rival RESOLVES -- it is a correct impl, not a counterexample, and verify=>correct is not broken by it.

**PREPATCH REPRODUCED.** model_prepatch.py is same_spec=True and FAILS: `prepatch_check.py:337:12:338:71: error: Assert might fail. Assertion (ToSeq(result) == report_seq(ToSeq(cls_name), ToSeq(demanded), ToSeq(found))) might not hold.` -- exactly the value clause refinement.md §D predicts, and the prepatch terminates and returns, so the T-legs do not mask the value leg.

REFINEMENT.MD AUDIT (A-legs and correspondence). 15 rows, tags: A1 R; A2/A3 R+A-reference; A4/A5/A6 T; B1 R; B2/B3 R+(calls A); B4 I; B5 I+R; B6 R+A-reference; B7/B8/B9 T. NO kind-3 and NO A-consumed rows -- confirmed there is no @ContractOnly anywhere in model.py, so the proof consumes no axiom's Ensures; the changed behaviour (whole-run rendering) is modelled deeply by quoted/joined/render_run/report_seq plus the verified construction loop. I applied the gold patch to a fresh copy of core.py at base_commit and checked every A-leg line reference: helper at 58-64 with exits at 60/62/64, assembly at 86-89, plural at 76, required_columns at 74 -- all match mapping.md/refinement.md exactly.

A6/B9 (delivery): mechanically confirmed no `raise` anywhere in the helper body 58-64 and that each exit is a return of one total expression; the assembly is one str.format with four positional fields and four arguments. A5/B8 (preservation): no assignment to obj or to any element of it in any branch; str.format reads its arguments. Verified the seg1/seg2/seg3 code points decode to ' object is invalid - expected ', ' as the first column', ' but found ' and reassemble byte-identically to the real post-patch template. G-AX axiom_check.py re-run: exit 0, 9 boundary runs + 6 fixed reports + 20000 fuzz reports, 0 mismatch.

The B9 reading is the one to watch and it is correctly stated: the real branch DOES raise at core.py:86, but what is modelled at site B is the.format(...) subexpression whose VALUE is the report, so Exsures(Exception, False) denies the assembly the option of ending without a report rather than denying the method its delivery mechanism -- refinement.md and mapping.md §4b both state this explicitly.

RESIDUAL RISK (not a defect, recorded). The token abstraction is exact only for names whose repr is quote+name+quote (mapping.md §2 domain note); a name containing an apostrophe or backslash is outside the clean domain and is not exercised by F2P/P2P. The scalar (`not hasattr __len__`) branch of the real helper is unmodelled, correctly, since both call sites pass lists. Neither gap is reachable by a same-spec rival: I could not turn either into a verifying wrong impl, because the model's obligations are stated over PSeq[int] for every length including 0 and 1.

**VERDICT:** SOUND. 11 distinct wrong impls (prepatch bug, two boundary, partial-domain, two control-flow-effect/non-delivery+non-completion, preservation/aliasing, ungrounded-oracle echo, over-approximation, delivery-mechanism probe, domain-narrowing smuggle, vacuity control) all share the frozen spec and all FAIL to verify; the only file that verifies is the positive control, whose faithful refined patch RESOLVES under the official harness (F2P 1/1, P2P 20/20). No verify-but-not-resolve rival found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE. Built a fresh worktree at base_commit 298ccb478e6bf092953bca67a3d29dc6c35f6752 () and applied patch.diff, per instructions: the patched tree is the reference for the two modeled functions. I did NOT compare against the base version -- the pre-patch first-name-only assembly is the delta the patch introduces, and reporting that as drift would condemn a correct spec.

BOTH REAL CALLEES EXTRACTED, NOT RETYPED. My differential harness parses the patched core.py and exec()s the real nested helper as_scalar_or_list_str verbatim, and eval()s the real.format(...) expression lifted out of the real raise statement (substituting only the self.colnames[:len(required_columns)] subexpression so arbitrary found-runs can be driven). So the oracle is the shipped code, independent of axiom_check.py's re-typed copy.

VALUE LEG -- EXHAUSTIVE, NOT SAMPLED. Over an 18-name declared-domain alphabet: render_run exhaustive on all runs of length 0..3 = 6175 cases, 0 divergences; report_seq exhaustive over 2 class names x demanded 0..2 x found 0..2 = 235,298 cases, 0 divergences; long runs of length 4, 5, 8, 17, 64 exact. Plus 30,000 randomized reports mixing in the hard alphabet -- 6308 mismatches, ALL 6308 involving a non-identifier name, 0 mismatches on identifier-only names. The exact F2P string reproduces character-for-character: "TimeSeries object is invalid - expected ['time', 'a'] as the first columns but found ['time', 'b']".

I also checked the model's impl region against its own pure region independently (transliterated the backward construction loop and diffed it against render_run on every case above) -- 0 disagreements, so the verified Asserts are not papering over an impl/pure gap.

**LITERAL SEGMENTS.** Decoded seg1/seg2/seg3 from code points and reassembled the template: '{} object is invalid - expected {} as the first column{} but found {}' -- byte-identical to the real post-patch format string. The old template's literal apostrophes around the fields are correctly absent (the helper now supplies them). No off-by-one in the spacing around the fields.

**PLURAL BOUNDARY.** By AST: the real plural is keyed on len(required_columns), and required_columns is exactly the run passed to the demanded-field render in BOTH the relax branch (self.`_required_columns`[:len(self.colnames)]) and the non-relax branch. The model keys plural on len(demanded) and renders render_run(demanded) -- same run, so no drift is possible via the relax path. Length-0 boundary checked: real field '[]' with plural '' -- the model's render_run falls through to the bracketed form at length 0 (only length 1 is special-cased), matching.

NON-VALUE CLAUSES ARE TRUE OF THE REAL CALLEE, so they add no strength the repo does not have. By AST on the patched helper: 3 Return nodes and 0 Raise nodes (clause (5) / Exsures holds); 0 While/For nodes and no self-call -- only hasattr, len, str (clause (3) / MustTerminate holds); 0 Assign/AugAssign nodes anywhere in the body, so obj and its elements are never written (clause (4) / the Old(...) preservation clauses hold). The assembly side: the template has 4 positional {} fields and 0 conversion specifiers against exactly 4 supplied arguments, so str.format cannot fail there either. Each obligation is a Requires/Ensures demanded of every input the other preconditions admit, so none narrows the modeled domain.

**GOLD BASELINE.** An unmodified copy of model.py passes same-spec (exit 0) and Nagini 'Verification successful' (49.86s), so the bundle's own artifact is live and the negative results above are real verifier outcomes rather than a broken harness. axiom_check.py exits 0 on its own terms. conformance_check.py could not run here (no astropy/erfa importable in any available env) -- an environment gap, not a spec finding, so I built the differential harness above instead of treating it as evidence either way.

**CONCLUSION.** I found no input inside the declared domain on which the modeled functions disagree with the patched repo, and the one out-of-domain class is disclosed up front in mapping.md and unreachable by the tests. The abstraction (one name = one token) is the honest place to draw the line given Nagini bans str indexing, and it is exactly where the changed behavior is structural. Verdict FAITHFUL.

Counterexample / evidence:

```
None. No spec-too-strong / drift counterexample found. Two faithful-alternative implementations sharing the frozen spec byte-for-byte were constructed and both VERIFY, so the spec does not over-fit the gold construction: (1) atkB_reorder.py -- compose_leading_run_report rebuilt with the found run rendered FIRST, plural computed before the demanded render, literal segments declared in reverse order and the tail pre-concatenated: same-spec exit=0, Nagini 'Verification successful' (40.85s). (2) The bundle's own two latitude controls extracted from properties.py, ctl_recursive (recursive-descent rendering instead of the backward loop) and ctl_internal (raises and handles a signal internally before returning the right report): both same-spec exit=0 and both 'Verification successful' (47.52s / 38.25s), confirming the length-scaled MustTerminate budgets admit structural recursion and that Exsures(Exception, False) constrains only the EXIT, not exception machinery in the body.
```

**REFERENCE DISCIPLINE.** Built a fresh worktree at base_commit 298ccb478e6bf092953bca67a3d29dc6c35f6752 () and applied patch.diff, per instructions: the patched tree is the reference for the two modeled functions. I did NOT compare against the base version -- the pre-patch first-name-only assembly is the delta the patch introduces, and reporting that as drift would condemn a correct spec.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LANE: G-PANEL attacker (3) leakage / gold-reconstruction, astropy__astropy-13033 / nagini, model.py sha256=4bbb28006f6f2b7b73ab41d6bc8cf54e18f971fa43d08234f507343b5ca552cb (re-checked unchanged after all work; all scratch, worktree at 298ccb478e). Env: PYTHONPATH=src, python3.

NO RELAXATION IN PLAY -- established by my own measurement, not from a stamp. meta.json top-level keys are [additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, migrated_from, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version]: ZERO keys matching /relax/i, so no `relaxed_leakage`. `find. -iname '*RELAX*'` over the whole instance dir returns nothing, so there is no RELAXED_LEAKAGE.md to check. gates.G-LEAK.status == 'pass' with mode 'strict', not 'relaxed'. This is therefore an ordinary STRICT judgement: problem_statement is the sole baseline; hints_text and the test_patch are excluded from it.

### WHAT I DERIVED AND RAN (measurements, not the bundle's assertions)
1. Spec view derived myself: markers.spec_view(model.py, backend('nagini')) -> 276 lines, read end to end (module docstring clauses (1)-(5) + Modelling-choices paragraph; punctuation constants; axioms region; pure region empty_seq/encode_name/quoted/joined/render_run/report_seq; both Requires/Ensures/Exsures blocks; 2 elided impl regions).
2. Elision audit per region, independently: ELISION_IMPL appears exactly 2x. Parsed regions = axioms (110,116), pure (119,184), pre-conditions (190,201)+(267,279), post-conditions (202,220)+(280,308), invariants (232,239), impl (221,258)+(309,333). I took every impl/invariants body line >12 chars and tested membership in the view: 6 apparent survivors, EACH traced to a different legitimate origin by a per-region identical-text search -- 'if len(run) == 1:' -> pure:149/159; the three decoded-segment comments -> pure:170/174/179; the seg1 code-point continuation -> pure:172; 'ToSeq(demanded), ToSeq(found)))' -> post-conditions:297. No impl content reaches the view.
3. Mechanical screen run by me: leakage.screen(model.py, nagini, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[].
4. STRICTER than the screen: normalized every gold changed line and searched the normalized view at threshold >=6 chars (screen uses >=8): ZERO gold changed lines reproduced. I then swept every sliding 12-char normalized window of every gold changed line: the only windows present are substrings of the message literals 'objectisinvalid-expected' and 'asthefirstcolumn' -- both of which are (a) verbatim in the PUBLIC problem_statement and (b) pre-existing base_commit text (see 7). No window from the changed MECHANISM (as_scalar_or_list_str, hasattr/`__len__`, obj[0], str(obj), the [:len(required_columns)] slice) appears.
5. Patched symbols: `_patch_changed_symbols` = {as_scalar_or_list_str, BaseTimeSeries, check_required_columns}. For each I tested membership in the lowercased view: all three ABSENT (and all three absent from the problem_statement, so they would have been hard failures). Spec-view identifiers are render_name_run, compose_leading_run_report, render_run, report_seq, joined, quoted, encode_name, empty_seq, cls_name, demanded, found, run, plural, seg1-3, NAME_QUOTE/COMMA/SPACE/LBRACK/RBRACK -- none embeds or paraphrases a patched repo symbol; the gold's invented helper name is nowhere.
6. Vocabulary sweep over the view -- ABSENT: required_columns, colnames, `_check_required`, timeseries/TimeSeries, QTable, remove_column, flux, core.py, hasattr, `__len__`, '.format(', ValueError, '`__class__`', '`__name__`', 'slice', '[:len('. F2P discriminator literals "['time', 'a']" / "['time', 'b']" / 'first columns but found': all absent -- names are opaque int tokens with placeholder examples n0/n1. Hints-only diagnosis vocabulary absent too ('misleading', 'confusing', 'no longer makes sense', 'works under the assumption', 'proposal'); the hints' concrete proposal string is not reproduced, and the view never uses 'required' as a render verb (its 2 hits, lines 50 and 253, are obligation prose 'required however the runs were supplied' / 'required of every admissible triple'). Narration regex `_NARRATION_RE` -> zero matches; the docstring's own frame is 'stated as desired behaviour, not as an edit', and the only 'instead of' hits are clause (5)'s 'a failure instead of a description'. The single 'astropy' hit in the whole view is the instance-id header line 1 -- the solver's own task identifier, naming no file/symbol/edit.
7. WHY THE MESSAGE-TEXT SPECIFICITY IS PUBLIC, NOT A LEAK. I decoded report_seq's code points myself: seg1=' object is invalid - expected ', seg2=' as the first column', seg3=' but found ', plural=chr(115)='s'. All three test `in problem_statement` == True, and so does ' as the first columns but found ' -- the PS Actual-behavior line is "TimeSeries object is invalid - expected 'time' as the first columns but found 'time'", which makes even the plural marker public. I also read the base_commit worktree: astropy/timeseries/core.py:72-81 already carries those literals pre-patch, and test_sampled.py:38/370-396 + test_binned.py:31 already assert the apostrophe-wrapped single-name form. So the length-1 branch and all connective text localize nothing a solver cannot read in the issue or the base tree.
8. The one item NOT in the problem_statement is the BRACKETED multi-name list form (clause (1)'s ['n0', 'n1']); a regex for that shape matches only hints_text. I judged it and it is not a leak: it is the ABSTRACT desired output shape the issue explicitly demands ('Expected behavior: An exception that informs the users required columns are missing'), stated over opaque tokens, with no file, no function, no invented helper name, no slicing expression, no raise site, and no bug->fix mechanism. A solver holding this view still has to locate `_check_required_columns` in astropy/timeseries/core.py, discover the found side must become a leading-run slice rather than self.colnames[0], and choose an implementation. That is a behavioral contract, which spec_guide.md 0.6 directs a spec to state.
9. CORE-GATE SOUNDNESS I MEASURED (so the verdict rests on my runs, not stamps). scripts/nagini_verify.sh on the gold model -> 'Verification successful', 49.40s, exit 0. On model_prepatch.py (markers.same_spec(model, prepatch) == True, i.e. byte-identical spec, impl-only revert) -> 'Verification failed', exit 1, at exactly the load-bearing value clause: 'm_pre.py:337: Assert might fail. Assertion (ToSeq(result) == report_seq(ToSeq(cls_name), ToSeq(demanded), ToSeq(found))) might not hold.' spec_view(model_prepatch.py) == spec_view(model.py) BYTE-IDENTICAL, so the prepatch's own '# PRE-PATCH (buggy)' / 'misleading report' comments at lines 310/313 sit inside impl (221-258)+(309-333) and are elided from any consumer view.
10. DE-NARRATION CONTROL (the strip-the-prose test, run even though no relaxation is claimed): I replaced the entire 5816-char module docstring of model_prepatch.py with '"""Model."""' and re-verified -> still 'Verification failed', exit 1, same clause ('m_pre_nodoc.py:250:... ToSeq(result) == report_seq(...) might not hold'), 86.19s. The discriminating power therefore lives entirely in the formal code-point-level report_seq equality in the pure/post-conditions regions, NOT in the prose. So the narration is not load-bearing and could in principle be trimmed further -- which is precisely why no relaxation is needed here, and why what prose remains is descriptive rather than a smuggled discriminator.
11. REVIEWER-DIRECTED CONTENT (a finding in its own right if present): leakage.reviewer_directed() returns [] on the spec view and on every bundle file individually (axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md). I also grepped the non-log artifacts (mapping.md, refinement.md, model.py, properties.py, axiom_check.py, conformance_check.py) for 'you must/should/need', 'your verdict', 'record NO-LEAKAGE', 'attacker (3)', 'panel 3', 'treat this as': zero hits. The only bundle hits for such phrasing are inside meta.json's recorded PRIOR G-PANEL-3 note and verdict.md's copy of it, where they appear as quoted grep PATTERNS a previous panel ran, not as directives to me. NOTHING in this bundle addresses me or tells me what to record; I treated the prior NO-LEAKAGE note purely as a record and re-derived every claim above from the current bytes.

HOUSEKEEPING DISCREPANCY (not a leakage finding, recorded): meta.json's TOP-LEVEL region_hashes are STALE. Recomputing all 7 from the current model.py, only 'axioms' (bc58ef570ad6) matches; impl, invariants, pre-conditions, post-conditions, pure and spec_view all differ from the top-level block. The copies inside gates.G-HYGIENE.data.region_hashes match my recomputation on all 7, so the current file is internally consistent with the gate that measured it and the top-level block is a stale duplicate. Also noted: verdict.md line 4315 records that the G-EQ/G-PANEL stamps once carried sources.model.py=e11ef2e9.., but gates.G-LEAK.sources.model.py == 4bbb2800.. == the current hash, so the leak gate I am re-judging is stamped on the current bytes. Bears on integrity bookkeeping, not leakage; I derived the view from the current bytes regardless.

**VERDICT:** NO-LEAKAGE. The spec view discloses nothing about the gold edit beyond the public problem_statement: no gold changed line at >=6 normalized chars (and no mechanism-bearing 12-char window), no patched file path or module path, none of the three patched symbols in identifiers or comments, no bug->fix narration, no hints-only vocabulary, no F2P literals, and its message-text specificity is verbatim public problem_statement text that also pre-exists at base_commit. The one non-PS element (the bracketed multi-name rendering) is the abstract behaviour the issue demands, stated over opaque tokens; and the de-narration control shows the spec's rejection of the pre-patch survives total removal of the narration, so no prose clause is doing discriminator-smuggling work.

**LANE:** G-PANEL attacker (3) leakage / gold-reconstruction, astropy__astropy-13033 / nagini, model.py sha256=4bbb28006f6f2b7b73ab41d6bc8cf54e18f971fa43d08234f507343b5ca552cb (re-checked unchanged after all work; all scratch, worktree at 298ccb478e). Env: PYTHONPATH=src, python3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
