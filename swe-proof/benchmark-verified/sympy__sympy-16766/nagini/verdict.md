# P2 adversarial audit — sympy__sympy-16766

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -102,7 +100,6 @@
         Invariant(n >= 1)
         Invariant(0 <= i and i <= n)
         Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = idx[i - 1]
         Assert(idx.drop(i - 1)[0] == e)
@@ -112,5 +109,9 @@
         else:
             joined = e + sep() + joined
         i = i - 1
-    return nm + PSeq(91) + joined + PSeq(93)
+    not_supported_prefix = PSeq(
+        32, 32, 35, 32, 78, 111, 116, 32, 115, 117, 112, 112, 111, 114, 116,
+        101, 100, 32, 105, 110, 32, 80, 121, 116, 104, 111, 110, 58, 10,
+        32, 32, 35, 32, 73, 110, 100, 101, 120, 101, 100, 10)  # type: PSeq[int]
+    return not_supported_prefix + nm + PSeq(91) + joined + PSeq(93)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -92,21 +90,15 @@
     n = len(index_renderings)
     joined = empty_seq()              # type: PSeq[int]
     i = n
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(Acc(list_pred(index_renderings), 1 / 2))
         Invariant(nm == ToSeq(name))
         Invariant(idx == ToSeq(index_renderings))
         Invariant(n == len(index_renderings))
         Invariant(n >= 1)
-        Invariant(0 <= i and i <= n)
-        Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= n)
         e = idx[i - 1]
-        Assert(idx.drop(i - 1)[0] == e)
-        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
         if i == n:
             joined = e
         else:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -102,7 +100,6 @@
         Invariant(n >= 1)
         Invariant(0 <= i and i <= n)
         Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = idx[i - 1]
         Assert(idx.drop(i - 1)[0] == e)
@@ -110,7 +107,7 @@
         if i == n:
             joined = e
         else:
-            joined = e + sep() + joined
+            joined = e + PSeq(44) + joined
         i = i - 1
     return nm + PSeq(91) + joined + PSeq(93)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -102,7 +100,6 @@
         Invariant(n >= 1)
         Invariant(0 <= i and i <= n)
         Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = idx[i - 1]
         Assert(idx.drop(i - 1)[0] == e)
@@ -112,5 +109,5 @@
         else:
             joined = e + sep() + joined
         i = i - 1
-    return nm + PSeq(91) + joined + PSeq(93)
+    return nm + PSeq(93) + joined + PSeq(91)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -90,6 +88,8 @@
     nm = ToSeq(name)                  # type: PSeq[int]
     idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
     n = len(index_renderings)
+    if n == 1:
+        return nm + PSeq(91) + idx[0] + PSeq(93)
     joined = empty_seq()              # type: PSeq[int]
     i = n
     while i > 0:
@@ -102,7 +102,6 @@
         Invariant(n >= 1)
         Invariant(0 <= i and i <= n)
         Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = idx[i - 1]
         Assert(idx.drop(i - 1)[0] == e)
@@ -112,5 +111,5 @@
         else:
             joined = e + sep() + joined
         i = i - 1
-    return nm + PSeq(91) + joined + PSeq(93)
+    return joined
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -91,9 +89,8 @@
     idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
     n = len(index_renderings)
     joined = empty_seq()              # type: PSeq[int]
-    i = n
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < n:
         Invariant(Acc(list_pred(name), 1 / 2))
         Invariant(Acc(list_pred(index_renderings), 1 / 2))
         Invariant(nm == ToSeq(name))
@@ -101,16 +98,11 @@
         Invariant(n == len(index_renderings))
         Invariant(n >= 1)
         Invariant(0 <= i and i <= n)
-        Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = idx[i - 1]
-        Assert(idx.drop(i - 1)[0] == e)
-        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
-        if i == n:
+        e = idx[i]
+        if i == 0:
             joined = e
         else:
-            joined = e + sep() + joined
-        i = i - 1
+            joined = joined + sep() + e
+        i = i + 1
     return nm + PSeq(91) + joined + PSeq(93)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -87,30 +85,5 @@
     Ensures(Result() == render_indexed(ToSeq(name), ToSeq(index_renderings)))
     # post-conditions-end
     # impl-start
-    nm = ToSeq(name)                  # type: PSeq[int]
-    idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
-    n = len(index_renderings)
-    joined = empty_seq()              # type: PSeq[int]
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(name), 1 / 2))
-        Invariant(Acc(list_pred(index_renderings), 1 / 2))
-        Invariant(nm == ToSeq(name))
-        Invariant(idx == ToSeq(index_renderings))
-        Invariant(n == len(index_renderings))
-        Invariant(n >= 1)
-        Invariant(0 <= i and i <= n)
-        Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = idx[i - 1]
-        Assert(idx.drop(i - 1)[0] == e)
-        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
-        if i == n:
-            joined = e
-        else:
-            joined = e + sep() + joined
-        i = i - 1
-    return nm + PSeq(91) + joined + PSeq(93)
+    return render_indexed(ToSeq(name), ToSeq(index_renderings))
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -77,7 +76,6 @@
     Requires(Acc(list_pred(index_renderings), 1 / 2))
     # An element-access expression always carries at least one index.
     Requires(len(index_renderings) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -89,28 +87,5 @@
     # impl-start
     nm = ToSeq(name)                  # type: PSeq[int]
     idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
-    n = len(index_renderings)
-    joined = empty_seq()              # type: PSeq[int]
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(name), 1 / 2))
-        Invariant(Acc(list_pred(index_renderings), 1 / 2))
-        Invariant(nm == ToSeq(name))
-        Invariant(idx == ToSeq(index_renderings))
-        Invariant(n == len(index_renderings))
-        Invariant(n >= 1)
-        Invariant(0 <= i and i <= n)
-        Invariant(joined == join_sep(idx.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = idx[i - 1]
-        Assert(idx.drop(i - 1)[0] == e)
-        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
-        if i == n:
-            joined = e
-        else:
-            joined = e + sep() + joined
-        i = i - 1
-    return nm + PSeq(91) + joined + PSeq(93)
+    return nm + PSeq(91) + join_sep(idx) + PSeq(93)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-16766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An element-access expression — a named carrier subscripted by one or more
  index expressions — is rendered to its source-like Python textual form from
  the rendering of its carrier name and the renderings of its individual index
  expressions. The rendering is the carrier name, immediately followed by an
  opening U+005B `[`, then the index renderings separated from one another by
  the two-code-point sequence U+002C U+0020 (`, `), then a closing U+005D `]`.
  There is no separator before the first index or after the last, and the
  rendering carries no other surrounding text.

  An element-access expression always has at least one index, so the bracketed
  index list is never empty.

The carrier name and the rendering of each index expression are produced by
unchanged helpers; this model takes the carrier name and the index renderings
as given code-point sequences (they are the input carriers) and specifies only
the surrounding assembly, which is the behaviour under change.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of index renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the carrier name and the index renderings are inputs; the
# assembly under specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The index separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of index renderings: between every two
    adjacent indices a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_indexed(name: PSeq[int], idx: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full rendering of an element-access expression with carrier name
    `name` and index renderings `idx`: the name, then `[`, then the
    separator-joined index renderings, then `]`. No surrounding text."""
    return name + PSeq(91) + join_sep(idx) + PSeq(93)   # name + '[' + join + ']'
# pure-end


def print_indexed(name: List[int], index_renderings: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(index_renderings), 1 / 2))
    # An element-access expression always carries at least one index.
    Requires(len(index_renderings) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(index_renderings), 1 / 2))
    # The result is exactly the bracketed, separator-joined rendering of the
    # index renderings prefixed by the carrier name — with no other text.
    Ensures(Result() == render_indexed(ToSeq(name), ToSeq(index_renderings)))
    # post-conditions-end
    # impl-start
    nm = ToSeq(name)                  # type: PSeq[int]
    idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
    n = len(index_renderings)
    joined = empty_seq()              # type: PSeq[int]
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(index_renderings), 1 / 2))
        Invariant(nm == ToSeq(name))
        Invariant(idx == ToSeq(index_renderings))
        Invariant(n == len(index_renderings))
        Invariant(n >= 1)
        Invariant(0 <= i and i <= n)
        Invariant(joined == join_sep(idx.drop(i)))
        # invariants-end
        e = idx[i - 1]
        Assert(idx.drop(i - 1)[0] == e)
        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
        if i == n:
            joined = e
        else:
            joined = e + sep() + joined
        i = i - 1
    return nm + PSeq(91) + joined + PSeq(93)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-16766 (nagini). Positive control (pristine model.py) VERIFIES (10.85s) via scripts/nagini_verify.sh. All 8 attacks confirmed same-spec (adversary same-spec exit 0): only the impl region differs; axioms(empty)/pure region(join_sep,render_indexed,sep,empty_seq)/@Pure/Requires/Ensures byte-identical.

Protocol commands (swebench-lean venv):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-16766 <atk>  (all exit 0)
  python -m swebench_unified.adversary weakness nagini sympy__sympy-16766 <atk>

Weakness results:
- atk_1 (PREPATCH bug: prepend '  # Not supported in Python:\n  # Indexed\n' annotation prefix) -> EXIT 2, does NOT verify. Prepatch reproduced: the spec senses the change (G-DIFF) — postcondition Result()==render_indexed(...) rejects the leading prefix.
- atk_2 (boundary/off-by-one: loop i>1 drops the first index) -> EXIT 2, rejected.
- atk_3 (wrong separator: bare comma PSeq(44) instead of sep()=PSeq(44,32)) -> EXIT 2, rejected. Pins the multi-index ', ' separator (F2P observes p[0, 1]).
- atk_4 (control-flow: swapped brackets, PSeq(93)...PSeq(91)) -> EXIT 2, rejected.
- atk_5 (partial-domain: correct only n==1, else returns bare joined w/o name/brackets) -> EXIT 2, rejected.
- atk_6 (control-flow-effect: forward loop reversing index order via append) -> EXIT 2, rejected.
- atk_7 (correct echo: return render_indexed(ToSeq(name), ToSeq(index_renderings))) -> EXIT 0 CANDIDATE (verifies 10.4s).
- atk_8 (correct echo: nm + PSeq(91) + join_sep(idx) + PSeq(93)) -> EXIT 0 CANDIDATE (verifies 10.4s).

Materialized faithful refined patches for BOTH candidates (each impl computes exactly render_indexed == name+'['+', '-join+']', so the faithful Python refinement is the gold _print_Indexed) and RAN run_resolve (Docker oracle, timeout 1800):
  patch_7.diff -> RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False ATTEMPTS=1
  patch_8.diff -> RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False ATTEMPTS=1
Both executed (not speculated). No verifying wrong-impl's faithful patch fails to resolve.

Refinement.md audit: legs A1/A2/A5=R (str<->List[int]/PSeq[int]; literals '['/']'<->PSeq(91)/PSeq(93); '{}[{}]'.format<->concat), A3=I/R (index count, Indexed always >=1 index), A4=R (', '.join<->join_sep, loop invariant joined==join_sep(idx.drop(i))). NO kind-3 leg. meta.json confirms axioms=[] and deep_model_references=[]: the two callees str(base) and self._print(ind) are UNCHANGED by the gold patch and correctly abstracted as INPUT carriers (name, index_renderings) — there is NO A-consumed axiom, NO A-reference deep model of a real callee, and axiom_check.py is legitimately absent (G-AX has no obligation). The deep pure region (join_sep/render_indexed) is a closed-form spec of the assembly-under-change, part of the FROZEN spec, and faithfully corresponds to ', '.join / '{}[{}]'.format. The postcondition is a TOTAL functional spec (output uniquely determined by inputs), so any verifying impl returns the exact pinned sequence — verify DOES imply correct here.

VERDICT: SOUND. >=6 distinct wrong impls encoded and run (all rejected by verification), prepatch reproduced, and both same-spec verifying candidates' materialized faithful patches were executed through the official harness and RESOLVED. No verify=>correct violation found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-16766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An element-access expression — a named carrier subscripted by one or more
  index expressions — is rendered to its source-like Python textual form from
  the rendering of its carrier name and the renderings of its individual index
  expressions. The rendering is the carrier name, immediately followed by an
  opening U+005B `[`, then the index renderings separated from one another by
  the two-code-point sequence U+002C U+0020 (`, `), then a closing U+005D `]`.
  There is no separator before the first index or after the last, and the
  rendering carries no other surrounding text.

  An element-access expression always has at least one index, so the bracketed
  index list is never empty.

The carrier name and the rendering of each index expression are produced by
unchanged helpers; this model takes the carrier name and the index renderings
as given code-point sequences (they are the input carriers) and specifies only
the surrounding assembly, which is the behaviour under change.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of index renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the carrier name and the index renderings are inputs; the
# assembly under specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The index separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of index renderings: between every two
    adjacent indices a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_indexed(name: PSeq[int], idx: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full rendering of an element-access expression with carrier name
    `name` and index renderings `idx`: the name, then `[`, then the
    separator-joined index renderings, then `]`. No surrounding text."""
    return name + PSeq(91) + join_sep(idx) + PSeq(93)   # name + '[' + join + ']'
# pure-end


def print_indexed(name: List[int], index_renderings: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(index_renderings), 1 / 2))
    # An element-access expression always carries at least one index.
    Requires(len(index_renderings) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(index_renderings), 1 / 2))
    # The result is exactly the bracketed, separator-joined rendering of the
    # index renderings prefixed by the carrier name — with no other text.
    Ensures(Result() == render_indexed(ToSeq(name), ToSeq(index_renderings)))
    # post-conditions-end
    # impl-start
    nm = ToSeq(name)                  # type: PSeq[int]
    idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]
    n = len(index_renderings)
    joined = empty_seq()              # type: PSeq[int]
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(index_renderings), 1 / 2))
        Invariant(nm == ToSeq(name))
        Invariant(idx == ToSeq(index_renderings))
        Invariant(n == len(index_renderings))
        Invariant(n >= 1)
        Invariant(0 <= i and i <= n)
        Invariant(joined == join_sep(idx.drop(i)))
        # invariants-end
        e = idx[i - 1]
        Assert(idx.drop(i - 1)[0] == e)
        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))
        if i == n:
            joined = e
        else:
            joined = e + sep() + joined
        i = i - 1
    return nm + PSeq(91) + joined + PSeq(93)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-16766 (nagini). Positive control (pristine model.py) VERIFIES (10.85s) via scripts/nagini_verify.sh. All 8 attacks confirmed same-spec (adversary same-spec exit 0): only the impl region differs; axioms(empty)/pure region(join_sep,render_indexed,sep,empty_seq)/@Pure/Requires/Ensures byte-identical.

Protocol commands (swebench-lean venv):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-16766 <atk>  (all exit 0)
  python -m swebench_unified.adversary weakness nagini sympy__sympy-16766 <atk>

Weakness results:
- atk_1 (PREPATCH bug: prepend '  # Not supported in Python:\n  # Indexed\n' annotation prefix) -> EXIT 2, does NOT verify. Prepatch reproduced: the spec senses the change (G-DIFF) — postcondition Result()==render_indexed(...) rejects the leading prefix.
- atk_2 (boundary/off-by-one: loop i>1 drops the first index) -> EXIT 2, rejected.
- atk_3 (wrong separator: bare comma PSeq(44) instead of sep()=PSeq(44,32)) -> EXIT 2, rejected. Pins the multi-index ', ' separator (F2P observes p[0, 1]).
- atk_4 (control-flow: swapped brackets, PSeq(93)...PSeq(91)) -> EXIT 2, rejected.
- atk_5 (partial-domain: correct only n==1, else returns bare joined w/o name/brackets) -> EXIT 2, rejected.
- atk_6 (control-flow-effect: forward loop reversing index order via append) -> EXIT 2, rejected.
- atk_7 (correct echo: return render_indexed(ToSeq(name), ToSeq(index_renderings))) -> EXIT 0 CANDIDATE (verifies 10.4s).
- atk_8 (correct echo: nm + PSeq(91) + join_sep(idx) + PSeq(93)) -> EXIT 0 CANDIDATE (verifies 10.4s).

Materialized faithful refined patches for BOTH candidates (each impl computes exactly render_indexed == name+'['+', '-join+']', so the faithful Python refinement is the gold _print_Indexed) and RAN run_resolve (Docker oracle, timeout 1800):
  patch_7.diff -> RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False ATTEMPTS=1
  patch_8.diff -> RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False ATTEMPTS=1
Both executed (not speculated). No verifying wrong-impl's faithful patch fails to resolve.

Refinement.md audit: legs A1/A2/A5=R (str<->List[int]/PSeq[int]; literals '['/']'<->PSeq(91)/PSeq(93); '{}[{}]'.format<->concat), A3=I/R (index count, Indexed always >=1 index), A4=R (', '.join<->join_sep, loop invariant joined==join_sep(idx.drop(i))). NO kind-3 leg. meta.json confirms axioms=[] and deep_model_references=[]: the two callees str(base) and self._print(ind) are UNCHANGED by the gold patch and correctly abstracted as INPUT carriers (name, index_renderings) — there is NO A-consumed axiom, NO A-reference deep model of a real callee, and axiom_check.py is legitimately absent (G-AX has no obligation). The deep pure region (join_sep/render_indexed) is a closed-form spec of the assembly-under-change, part of the FROZEN spec, and faithfully corresponds to ', '.join / '{}[{}]'.format. The postcondition is a TOTAL functional spec (output uniquely determined by inputs), so any verifying impl returns the exact pinned sequence — verify DOES imply correct here.

VERDICT: SOUND. >=6 distinct wrong impls encoded and run (all rejected by verification), prepatch reproduced, and both same-spec verifying candidates' materialized faithful patches were executed through the official harness and RESOLVED. No verify=>correct violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) audit for sympy__sympy-16766 nagini bundle.

Modeled function `print_indexed(name, index_renderings)` models the gold-patch method `PythonCodePrinter._print_Indexed(self, expr)` added at sympy/printing/pycode.py:360:
  def _print_Indexed(self, expr):
      base = expr.args[0]; index = expr.args[1:]
      return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))

Spec: Result() == render_indexed(ToSeq(name), ToSeq(index_renderings)) = name + '[' + join_sep(idx) + ']', where join_sep is the ', '-separated concatenation (none at ends). The two callees str(base) and self._print(ind) are UNCHANGED by the patch and correctly taken as input carriers (name: List[int], index_renderings: List[PSeq[int]] of code points). Precondition len(index_renderings) >= 1 matches Indexed always carrying >=1 index (Indexed.__new__ raises otherwise). This is a proper, not-too-strong scope.

Independent differential check: built a fresh worktree at base_commit b8fe457a02cc24b3470ff678d0099c350b7fef43, applied patch.diff verbatim, and compared the real patched _print_Indexed against the model's assembly `str(base) + '[' + ", ".join(renders) + ']'` (renders derived from the real unchanged callees) over 200,025 adversarial inputs: carrier names and index renderings containing brackets [ ], the separator ', ' itself, braces { }, percent %, format-ish {0}, unicode, plus single/multi/6-index cases and symbolic/rational/compound indices. Result: 0 disagreements. The bundle's own conformance_check.py (G-CONF pass, 100000 inputs, seed 167660, 0 disagreements) corroborates.

spec region byte-identity confirmed via `adversary same-spec` (exit 0). The @Pure closed-form join_sep/render_indexed exactly mirror Python's str '+', '.format', and ', '.join semantics under the code-point bijection (ord('[')==91, ord(']')==93, ord(',')==44, ord(' ')==32). No divergence found; the modeled function equals the real repo callee on every tested input. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (swebench_unified.leakage.screen over spec_view) passes: no diff markers, no reproduced gold-patch line, no patched file/module path (pycode.py), and no spec-view identifier or comment naming a patched repo symbol (PythonCodePrinter / _print_Indexed), no bug/fix narration. Semantic review confirms NO leakage beyond the public problem_statement. Critically, the public problem_statement OVER-discloses the gold edit: it literally instructs 'We should add following method to PythonCodePrinter' and prints the exact gold code `def _print_Indexed(self, expr): ... return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))`. Thus every discriminating detail the spec view abstractly states — carrier name + '[' + ', '-joined index renderings + ']', no surrounding text, >=1 index — is already fully public (indeed as literal code). The spec view uses only abstract, non-repo identifiers (print_indexed, render_indexed, join_sep, sep) and describes desired behaviour, not an edit. The pre-patch 'Not supported in Python / Indexed' unsupported-node fallback story (the actual gold discriminator narrative) appears ONLY in refinement.md and mapping.md, which are NOT part of the consumer spec view; it is absent from model.py's spec regions. Nothing in the spec view reveals the gold edit beyond the (over-disclosing) problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
