# P2 adversarial audit — sympy__sympy-14976

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
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,8 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
-    out = out + [40]
-    # numerator digits
     out = out + p_digits
-    # ')' '/'
-    out = out + [41]
     out = out + [47]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
-    out = out + [40]
-    # denominator digits
     out = out + q_digits
-    # ')'
-    out = out + [41]
     return out
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,14 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # numerator digits
-    out = out + p_digits
-    # ')' '/'
+    out = out + q_digits
     out = out + [41]
     out = out + [47]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # denominator digits
-    out = out + q_digits
-    # ')'
+    out = out + p_digits
     out = out + [41]
     return out
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,11 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # numerator digits
     out = out + p_digits
-    # ')' '/'
     out = out + [41]
     out = out + [47]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
-    out = out + [40]
-    # denominator digits
     out = out + q_digits
-    # ')'
-    out = out + [41]
     return out
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,19 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
-    out = out + [40]
-    # numerator digits
-    out = out + p_digits
-    # ')' '/'
-    out = out + [41]
-    out = out + [47]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
-    out = out + [40]
-    # denominator digits
-    out = out + q_digits
-    # ')'
-    out = out + [41]
+    if len(p_digits) > 0 and len(q_digits) > 0:
+        out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
+        out = out + [40]
+        out = out + p_digits
+        out = out + [41]
+        out = out + [47]
+        out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
+        out = out + [40]
+        out = out + q_digits
+        out = out + [41]
+    else:
+        out = out + p_digits
+        out = out + [47]
+        out = out + q_digits
     return out
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,14 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
+    out = out + [109, 112, 102]
     out = out + [40]
-    # numerator digits
     out = out + p_digits
-    # ')' '/'
     out = out + [41]
     out = out + [47]
-    # ctor '('
-    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
+    out = out + [109, 112, 102]
     out = out + [40]
-    # denominator digits
     out = out + q_digits
-    # ')'
     out = out + [41]
     return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,13 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # numerator digits
     out = out + p_digits
-    # ')' '/'
     out = out + [41]
     out = out + [47]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # denominator digits
     out = out + q_digits
-    # ')'
-    out = out + [41]
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(p_digits), 1 / 2))
     Requires(Acc(list_pred(q_digits), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(p_digits), 1 / 2))
@@ -86,20 +84,14 @@
     # post-conditions-end
     # impl-start
     out = []  # type: List[int]
-    # ctor '('
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # numerator digits
     out = out + p_digits
-    # ')' '/'
     out = out + [41]
-    out = out + [47]
-    # ctor '('
+    out = out + [42]
     out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
     out = out + [40]
-    # denominator digits
     out = out + q_digits
-    # ')'
     out = out + [41]
     return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-14976.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A high-precision arbitrary-precision renderer turns a ratio of two integers
  (a numerator carrier and a denominator carrier, each already rendered as its
  decimal digit string) into source text that performs the division WITHIN the
  arbitrary-precision arithmetic domain. Concretely, the rendered text is the
  numerator wrapped in a high-precision constructor call, divided by the
  denominator wrapped in the SAME high-precision constructor call:

      CTOR ( <numerator digits> ) / CTOR ( <denominator digits> )

  where ``CTOR`` is the constant fully-qualified constructor token the renderer
  uses for high-precision numbers. The discriminating property is that BOTH
  operands of the division are wrapped in that constructor call — so the
  quotient is computed at arbitrary precision — rather than the two digit
  strings being divided as a bare ``num / den`` (which would be an ordinary
  truncating/limited-precision division and lose precision).

The two digit-string carriers and the constructor token are modelled as
``List[int]`` of code points (Nagini bans ``str`` indexing); the specification
is carried over ``PSeq[int]`` via ``ToSeq``. The literal tokens are the ASCII
code points ``(`` = 40, ``)`` = 41, ``/`` = 47, and the constructor token
``mpmath.mpf`` = ``[109,112,109,97,116,104,46,109,112,102]``.

The constructor token is produced by an unchanged helper (the fully-qualified
module-formatter) that, under the renderer's default configuration, returns
that constant token; it is modelled as the pure constant ``ctor`` and validated
against the real helper out-of-band by axiom_check.py (G-AX), not consumed as
an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The renderer's changed string construction
# is modelled DEEPLY below as the pure fold-free concatenation `rendered`. The
# only callee the construction invokes — the fully-qualified module-formatter
# that yields the constructor token — is an UNCHANGED helper that, under the
# renderer's default configuration, returns the constant token modelled by the
# pure constant `ctor`; its equality to the real helper is validated
# out-of-band by axiom_check.py (G-AX), an A-reference, NOT a consumed axiom.)
# axioms-end


# pure-start
@Pure
def ctor() -> PSeq[int]:
    """The constant fully-qualified high-precision constructor token, as code
    points: ``mpmath.mpf``. This is what the unchanged module-formatter returns
    under the renderer's default (fully-qualified) configuration."""
    return PSeq(109, 112, 109, 97, 116, 104, 46, 109, 112, 102)


@Pure
def rendered(p: PSeq[int], q: PSeq[int]) -> PSeq[int]:
    """The rendered text for the ratio of the numerator digit string ``p`` and
    the denominator digit string ``q``: each wrapped in a constructor call and
    divided.

        ctor '(' p ')' '/' ctor '(' q ')'
    """
    return (ctor() + PSeq(40) + p + PSeq(41) + PSeq(47)
            + ctor() + PSeq(40) + q + PSeq(41))
# pure-end


def render_mpf_ratio(p_digits: List[int], q_digits: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(p_digits), 1 / 2))
    Requires(Acc(list_pred(q_digits), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(p_digits), 1 / 2))
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text wraps BOTH the numerator digits and the denominator
    # digits in the high-precision constructor call, dividing the two calls.
    Ensures(ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # numerator digits
    out = out + p_digits
    # ')' '/'
    out = out + [41]
    out = out + [47]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # denominator digits
    out = out + q_digits
    # ')'
    out = out + [41]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sympy__sympy-14976 (nagini). Spec: render_mpf_ratio has the TOTAL, UNCONDITIONAL postcondition Ensures(ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits))) where rendered(p,q)=ctor '(' p ')' '/' ctor '(' q ')' and ctor()=PSeq(109,112,109,97,116,104,46,109,112,102)='mpmath.mpf'. No precondition restricts digit values, so the postcondition pins the ENTIRE output for every input => verify implies byte-exact gold output; no verifying wrong impl can exist.

Protocol executed All attacks edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; same-spec confirmed on atk_1 via `adversary same-spec` exit 0).

Results — all 7 returned NOT-A-COUNTEREXAMPLE (spec rejected the wrong impl / verification failed). Since none verifies, none is a CANDIDATE and there are NO faithful patches to materialize/resolve (patches={}):
- atk_1.py PREPATCH bug (bare num/den, no ctor wrap): rejected -> prepatch reproduced, matches model_prepatch.py (G-DIFF).
- atk_2.py control-flow: swap operands ctor(q)/ctor(p): rejected.
- atk_3.py partial fix: only numerator wrapped, bare denominator: rejected.
- atk_4.py partial-domain/control-flow-effect: constructor-wrap only when both digit lists nonempty, else bare: rejected.
- atk_5.py ungrounded-oracle echo: wrong ctor token 'mpf' [109,112,102] instead of 'mpmath.mpf': rejected.
- atk_6.py boundary: missing closing ')' on denominator: rejected.
- atk_7.py control-flow-effect: wrong operator '*' (42) instead of '/' (47): rejected.
Positive control (bundle model.py impl) VERIFIES: 'Verification successful', 20.13s.

Refinement.md leg audit: all legs A1-A5 are R / A-reference / I; no A-consumed, no kind-3 (refinement.md §B confirmed). The single A-reference (ctor()=='mpmath.mpf' code points; rendered <-> patched MpmathPrinter._print_Rational template) is validated OUT-OF-BAND by axiom_check.py, which executes the real SymPy callees (_module_format unchanged helper under default fully_qualified_modules=True; _print_Rational called directly to avoid Rational auto-canonicalisation to Integer) and imports only sympy (the repo under test). Verified the code-point token [109,112,109,97,116,104,46,109,112,102] decodes exactly to 'mpmath.mpf'. A-leg correspondence to the real callees holds. Because the postcondition is total and fully determines the output, verify => correct.

VERDICT: SOUND. >=5 (7) distinct wrong impls run through the official weakness harness; none is a verifying counterexample; positive control verifies; prepatch reproduced; no resolve runs needed (no CANDIDATE).

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
"""Twin-artifact model for sympy__sympy-14976.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A high-precision arbitrary-precision renderer turns a ratio of two integers
  (a numerator carrier and a denominator carrier, each already rendered as its
  decimal digit string) into source text that performs the division WITHIN the
  arbitrary-precision arithmetic domain. Concretely, the rendered text is the
  numerator wrapped in a high-precision constructor call, divided by the
  denominator wrapped in the SAME high-precision constructor call:

      CTOR ( <numerator digits> ) / CTOR ( <denominator digits> )

  where ``CTOR`` is the constant fully-qualified constructor token the renderer
  uses for high-precision numbers. The discriminating property is that BOTH
  operands of the division are wrapped in that constructor call — so the
  quotient is computed at arbitrary precision — rather than the two digit
  strings being divided as a bare ``num / den`` (which would be an ordinary
  truncating/limited-precision division and lose precision).

The two digit-string carriers and the constructor token are modelled as
``List[int]`` of code points (Nagini bans ``str`` indexing); the specification
is carried over ``PSeq[int]`` via ``ToSeq``. The literal tokens are the ASCII
code points ``(`` = 40, ``)`` = 41, ``/`` = 47, and the constructor token
``mpmath.mpf`` = ``[109,112,109,97,116,104,46,109,112,102]``.

The constructor token is produced by an unchanged helper (the fully-qualified
module-formatter) that, under the renderer's default configuration, returns
that constant token; it is modelled as the pure constant ``ctor`` and validated
against the real helper out-of-band by axiom_check.py (G-AX), not consumed as
an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The renderer's changed string construction
# is modelled DEEPLY below as the pure fold-free concatenation `rendered`. The
# only callee the construction invokes — the fully-qualified module-formatter
# that yields the constructor token — is an UNCHANGED helper that, under the
# renderer's default configuration, returns the constant token modelled by the
# pure constant `ctor`; its equality to the real helper is validated
# out-of-band by axiom_check.py (G-AX), an A-reference, NOT a consumed axiom.)
# axioms-end


# pure-start
@Pure
def ctor() -> PSeq[int]:
    """The constant fully-qualified high-precision constructor token, as code
    points: ``mpmath.mpf``. This is what the unchanged module-formatter returns
    under the renderer's default (fully-qualified) configuration."""
    return PSeq(109, 112, 109, 97, 116, 104, 46, 109, 112, 102)


@Pure
def rendered(p: PSeq[int], q: PSeq[int]) -> PSeq[int]:
    """The rendered text for the ratio of the numerator digit string ``p`` and
    the denominator digit string ``q``: each wrapped in a constructor call and
    divided.

        ctor '(' p ')' '/' ctor '(' q ')'
    """
    return (ctor() + PSeq(40) + p + PSeq(41) + PSeq(47)
            + ctor() + PSeq(40) + q + PSeq(41))
# pure-end


def render_mpf_ratio(p_digits: List[int], q_digits: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(p_digits), 1 / 2))
    Requires(Acc(list_pred(q_digits), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(p_digits), 1 / 2))
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text wraps BOTH the numerator digits and the denominator
    # digits in the high-precision constructor call, dividing the two calls.
    Ensures(ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # numerator digits
    out = out + p_digits
    # ')' '/'
    out = out + [41]
    out = out + [47]
    # ctor '('
    out = out + [109, 112, 109, 97, 116, 104, 46, 109, 112, 102]
    out = out + [40]
    # denominator digits
    out = out + q_digits
    # ')'
    out = out + [41]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sympy__sympy-14976 (nagini). Spec: render_mpf_ratio has the TOTAL, UNCONDITIONAL postcondition Ensures(ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits))) where rendered(p,q)=ctor '(' p ')' '/' ctor '(' q ')' and ctor()=PSeq(109,112,109,97,116,104,46,109,112,102)='mpmath.mpf'. No precondition restricts digit values, so the postcondition pins the ENTIRE output for every input => verify implies byte-exact gold output; no verifying wrong impl can exist.

Protocol executed All attacks edit ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; same-spec confirmed on atk_1 via `adversary same-spec` exit 0).

Results — all 7 returned NOT-A-COUNTEREXAMPLE (spec rejected the wrong impl / verification failed). Since none verifies, none is a CANDIDATE and there are NO faithful patches to materialize/resolve (patches={}):
- atk_1.py PREPATCH bug (bare num/den, no ctor wrap): rejected -> prepatch reproduced, matches model_prepatch.py (G-DIFF).
- atk_2.py control-flow: swap operands ctor(q)/ctor(p): rejected.
- atk_3.py partial fix: only numerator wrapped, bare denominator: rejected.
- atk_4.py partial-domain/control-flow-effect: constructor-wrap only when both digit lists nonempty, else bare: rejected.
- atk_5.py ungrounded-oracle echo: wrong ctor token 'mpf' [109,112,102] instead of 'mpmath.mpf': rejected.
- atk_6.py boundary: missing closing ')' on denominator: rejected.
- atk_7.py control-flow-effect: wrong operator '*' (42) instead of '/' (47): rejected.
Positive control (bundle model.py impl) VERIFIES: 'Verification successful', 20.13s.

Refinement.md leg audit: all legs A1-A5 are R / A-reference / I; no A-consumed, no kind-3 (refinement.md §B confirmed). The single A-reference (ctor()=='mpmath.mpf' code points; rendered <-> patched MpmathPrinter._print_Rational template) is validated OUT-OF-BAND by axiom_check.py, which executes the real SymPy callees (_module_format unchanged helper under default fully_qualified_modules=True; _print_Rational called directly to avoid Rational auto-canonicalisation to Integer) and imports only sympy (the repo under test). Verified the code-point token [109,112,109,97,116,104,46,109,112,102] decodes exactly to 'mpmath.mpf'. A-leg correspondence to the real callees holds. Because the postcondition is total and fully determines the output, verify => correct.

VERDICT: SOUND. >=5 (7) distinct wrong impls run through the official weakness harness; none is a verifying counterexample; positive control verifies; prepatch reproduced; no resolve runs needed (no CANDIDATE).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the nagini bundle sympy__sympy-14976. The modeled function render_mpf_ratio's spec postcondition is ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits)) where rendered = ctor '(' p ')' '/' ctor '(' q ')' and ctor = 'mpmath.mpf' (code points). Real callee: MpmathPrinter._print_Rational (added by gold patch at pycode.py:335), body '{0}({1})/{0}({2})'.format(self._module_format('mpmath.mpf'), e.p, e.q). Verified: (1) model.py verifies under pinned Nagini (18.4s, 'Verification successful'). (2) axiom_check.py exit 0 on 11 boundary + 5000 fuzz Rationals, directly comparing the real _print_Rational output to the rendered deep model. (3) Independent direct comparison in a base_commit+gold-patch worktree: real _print_Rational produces exactly 'mpmath.mpf({e.p})/mpmath.mpf({e.q})' on all boundary inputs (q==1, 0, negatives, unnormalized 2/4, -3/-6) AND on 20,000 random Rationals with |num|,|den| up to 1e30 — zero mismatches. Under default fully_qualified_modules=True, _module_format('mpmath.mpf') returns 'mpmath.mpf' verbatim (confirmed in source), so ctor() is exact. The int->decimal-digit-string List[int] type refinement is sound and opaque (format field {1}/{2} == str(e.p)/str(e.q)). No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (not hints_text). The problem_statement already discloses the full defect and desired fix: title 'lambdify(modules=\'mpmath\') doesn't wrap rationals', shows the bad bare output '232/3', and states this 'results in reduced precision results ... because the 232/3 isn't evaluated at full precision.' So 'wrap rationals in mpmath so the quotient is computed at full precision' is already public.

The spec view (model.py: module docstring + pure defs ctor/rendered + render_mpf_ratio pre/post) describes exactly that behavior: render a ratio as CTOR('(' num ')') '/' CTOR('(' den ')') with both operands wrapped in the high-precision constructor mpmath.mpf, rather than a bare num/den (precision-losing). This is the behavioral restatement of the public issue, not edit-localization beyond it.

Checked all leak vectors: (1) diff markers/file path/module path — none present (patched file sympy/printing/pycode.py never appears); (2) verbatim gold-patch lines — none reproduced; (3) spec-view identifiers (render_mpf_ratio, ctor, rendered, p_digits, q_digits) are deliberately non-echoing and none embeds the patched symbols _print_Rational/_print_Float (mechanical screen confirms changed symbols {print_Rational, print_Float}, screen PASSES with no failures/warnings); (4) no bug/fix narration words in comments; (5) the token 'mpmath.mpf' — 'mpmath' is explicitly public via modules='mpmath', and 'mpf' is the obvious mpmath float constructor implied by 'wrap rationals in mpmath', not a leak beyond the task. The true repo binding (MpmathPrinter._print_Rational, pycode.py:335) lives only in mapping.md/meta, outside the consumer spec view.

Ran swebench_unified.leakage.screen on model.py against the frozen row: passed=True, hard_failures=[], warnings=[]. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
