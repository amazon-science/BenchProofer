# P2 adversarial audit — pytest-dev__pytest-10356

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -65,22 +63,5 @@
     Ensures(Implies(not consider_chain, Result() == chain[0]))
     # post-conditions-end
     # impl-start
-    if not consider_chain:
-        return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
-    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
-        Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
-        i = i - 1
-    return result
+    return chain[0]
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -67,19 +65,11 @@
     # impl-start
     if not consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
     result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
+    i = len(chain) - 1
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
         Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
         result = chain[i - 1] + result
         i = i - 1
     return result
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -67,20 +65,12 @@
     # impl-start
     if not consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
     result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
     i = len(chain)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
         Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
+        result = result + chain[i - 1]
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -65,19 +63,13 @@
     Ensures(Implies(not consider_chain, Result() == chain[0]))
     # post-conditions-end
     # impl-start
-    if not consider_chain:
+    if consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
     result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
     i = len(chain)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
         Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(chain.drop(i - 1)[0] == chain[i - 1])
         Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
         result = chain[i - 1] + result
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -66,21 +64,6 @@
     # post-conditions-end
     # impl-start
     if not consider_chain:
-        return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
-    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
-        Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
-        i = i - 1
-    return result
+        return chain[len(chain) - 1]
+    return concat_chain(chain)
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -67,20 +65,5 @@
     # impl-start
     if not consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
-    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
-        Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
-        i = i - 1
-    return result
+    return chain[0] + concat_chain(chain)
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -67,20 +65,7 @@
     # impl-start
     if not consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
-    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
-        Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
-        i = i - 1
-    return result
+    if len(chain) == 1:
+        return concat_chain(chain)
+    return chain[0]
     # impl-end
```

Attack 8 — `atk8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,7 +54,6 @@
     # pre-conditions-start
     # The chain always has at least its first member (the class itself).
     Requires(len(chain) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # With the full chain considered, the result is EXACTLY the concatenation
@@ -67,20 +65,5 @@
     # impl-start
     if not consider_chain:
         return chain[0]
-    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
-    # is empty, and concat_chain of the empty chain is the empty sequence).
-    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
-    i = len(chain)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(chain))
-        # `result` is the concatenation of the suffix chain[i:].
-        Invariant(result == concat_chain(chain.drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(chain.drop(i - 1)[0] == chain[i - 1])
-        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
-        result = chain[i - 1] + result
-        i = i - 1
-    return result
+    return concat_chain(chain)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-10356.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class participates in a linearised ancestor chain: itself first, then each
  of its ancestors in a determinate resolution order. Each class in that chain
  carries its OWN directly-attached list of decorating tokens (the tokens
  applied to that class alone, not inherited).

  When the full ancestor chain is to be considered, the tokens attached to the
  whole class are EXACTLY the concatenation of every chain member's own token
  list, in chain order: the class's own tokens first, then those of each
  ancestor in order. No member's tokens are dropped, even when several ancestors
  each contribute tokens (e.g. a class with two independent ancestors, each
  decorated, yields BOTH ancestors' tokens, not just one).

  When only the directly-attached tokens are wanted, the result is exactly the
  class's own token list -- the contributions of the ancestors are excluded.

The ancestor chain is modelled as `PSeq[PSeq[int]]`: an ordered sequence of
per-class own-token lists, each a `PSeq[int]` of token identifiers (Nagini bans
`str` indexing / rich objects). The concatenation is modelled DEEPLY as a
front-recursive fold (`concat_chain`); the per-class own-token lookup along the
real linearisation is the unchanged callee, validated out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the chain-concatenation is modelled deeply
#  below as `concat_chain` and validated == the real per-class own-list lookup
#  over the linearisation out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def concat_chain(chain: PSeq[PSeq[int]]) -> PSeq[int]:
    """The concatenation of a chain of per-member token lists, in chain order:
    chain[0] then, appended, the concatenation of the remaining members.
    Front-recursive (one unfold per member) so a backward impl loop can
    discharge the value equality. The empty chain concatenates to the empty
    sequence."""
    if len(chain) == 0:
        return PSeq(0).take(0)
    return chain[0] + concat_chain(chain.drop(1))
# pure-end


def unpacked_tokens(chain: PSeq[PSeq[int]], consider_chain: bool) -> PSeq[int]:
    # pre-conditions-start
    # The chain always has at least its first member (the class itself).
    Requires(len(chain) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # With the full chain considered, the result is EXACTLY the concatenation
    # of every member's own token list, in chain order -- nothing dropped.
    Ensures(Implies(consider_chain, Result() == concat_chain(chain)))
    # Without the chain, the result is exactly the first member's own tokens.
    Ensures(Implies(not consider_chain, Result() == chain[0]))
    # post-conditions-end
    # impl-start
    if not consider_chain:
        return chain[0]
    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
    # is empty, and concat_chain of the empty chain is the empty sequence).
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        # `result` is the concatenation of the suffix chain[i:].
        Invariant(result == concat_chain(chain.drop(i)))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec fully pins the output on the ENTIRE precondition domain (len(chain)>=1): Ensures(Implies(consider_chain, Result()==concat_chain(chain))) and Ensures(Implies(not consider_chain, Result()==chain[0])). Both branches are deterministic; concat_chain is a DEEP front-recursive fold (no consumed @ContractOnly axiom). There is no under-specified region for a verifying-but-wrong impl to hide in.

ATTACK PROTOCOL. Command per attack: `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-10356 <atk>`. Same-spec confirmed via `adversary same-spec` on atk1 (SAME) and atk8 (SAME); every attack edits ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical).

6+ DISTINCT wrong impls, all NOT-A-COUNTEREXAMPLE (exit 2, verification failed = spec rejected):
- atk_prepatch.py (prepatch, return chain[0]) -> FAILS verify. prepatch_reproduced=true.
- atk1.py (partial-domain: return chain[0] for both flags) -> FAILS verify (exit 2).
- atk2.py (boundary/off-by-one: backward loop starts i=len-1, drops chain[0]) -> FAILS verify (exit 2).
- atk3.py (wrong concat order: result = result + chain[i-1]) -> FAILS verify (exit 2).
- atk4.py (control-flow-effect: branch swap, concat when NOT consider_chain) -> FAILS verify (exit 2).
- atk5.py (ungrounded-oracle echo: class-only returns chain[len-1] instead of chain[0]) -> FAILS verify (exit 2).
- atk6.py (extra-token: chain[0] + concat_chain(chain), duplicates own marks) -> FAILS verify (exit 2).
- atk7.py (partial-domain: correct only when len==1, else chain[0]) -> FAILS verify (exit 2).

### One candidate
- atk8.py (correct alternative: `if not consider_chain: return chain[0]` else `return concat_chain(chain)`) -> CANDIDATE (shares spec AND verifies, 9.0s). Per protocol I MATERIALIZED its faithful refined patch (behaviorally identical to gold get_unpacked_marks: full MRO concatenation + consider_mro=False class-only, plus store_mark consider_mro=False) and RAN the official harness: run_resolve('pytest-dev__pytest-10356', patch) => RESOLVED=True, completed=True, attempts=1, flaky=False. A resolving echo of the gold is NOT a weakness (post-2026-08-06 policy). Patch file 

POSITIVE CONTROL: positive_control.py (= bundle model.py, the backward-loop impl) verifies (nagini_verify.sh exit 0).

REFINEMENT.md AUDIT: leg kinds = 3xR, 1xR/I, 1xA-reference. NO kind-3 (unexpressible-changed-op), NO consumed @ContractOnly axiom (model.py axioms region empty). The single changed operation (collect along full MRO) is modeled DEEPLY as concat_chain (A-reference A4), validated == the real _pytest.mark.structures.get_unpacked_marks by axiom_check.py/G-AX over F2P shape C(A,B)->[c,a,b], boundary shapes, and ~4000 fuzz DAGs at the ordered per-mark-name level. store_mark(consider_mro=False) call-site (site B) establishes chain[k]=own-marks abstraction, audited by G-AX (classes built through real decorator/store_mark path). A-reference correspondence holds. meta.json records G-AX pass, G-CONF pass, G-EQ pass. Every A-leg's correspondence to real callees checked and holds.

CONCLUSION: 8 attacks run; the sole verifying candidate's materialized faithful patch RESOLVES under the official harness. verify=>correct holds for this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-10356.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class participates in a linearised ancestor chain: itself first, then each
  of its ancestors in a determinate resolution order. Each class in that chain
  carries its OWN directly-attached list of decorating tokens (the tokens
  applied to that class alone, not inherited).

  When the full ancestor chain is to be considered, the tokens attached to the
  whole class are EXACTLY the concatenation of every chain member's own token
  list, in chain order: the class's own tokens first, then those of each
  ancestor in order. No member's tokens are dropped, even when several ancestors
  each contribute tokens (e.g. a class with two independent ancestors, each
  decorated, yields BOTH ancestors' tokens, not just one).

  When only the directly-attached tokens are wanted, the result is exactly the
  class's own token list -- the contributions of the ancestors are excluded.

The ancestor chain is modelled as `PSeq[PSeq[int]]`: an ordered sequence of
per-class own-token lists, each a `PSeq[int]` of token identifiers (Nagini bans
`str` indexing / rich objects). The concatenation is modelled DEEPLY as a
front-recursive fold (`concat_chain`); the per-class own-token lookup along the
real linearisation is the unchanged callee, validated out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the chain-concatenation is modelled deeply
#  below as `concat_chain` and validated == the real per-class own-list lookup
#  over the linearisation out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def concat_chain(chain: PSeq[PSeq[int]]) -> PSeq[int]:
    """The concatenation of a chain of per-member token lists, in chain order:
    chain[0] then, appended, the concatenation of the remaining members.
    Front-recursive (one unfold per member) so a backward impl loop can
    discharge the value equality. The empty chain concatenates to the empty
    sequence."""
    if len(chain) == 0:
        return PSeq(0).take(0)
    return chain[0] + concat_chain(chain.drop(1))
# pure-end


def unpacked_tokens(chain: PSeq[PSeq[int]], consider_chain: bool) -> PSeq[int]:
    # pre-conditions-start
    # The chain always has at least its first member (the class itself).
    Requires(len(chain) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # With the full chain considered, the result is EXACTLY the concatenation
    # of every member's own token list, in chain order -- nothing dropped.
    Ensures(Implies(consider_chain, Result() == concat_chain(chain)))
    # Without the chain, the result is exactly the first member's own tokens.
    Ensures(Implies(not consider_chain, Result() == chain[0]))
    # post-conditions-end
    # impl-start
    if not consider_chain:
        return chain[0]
    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
    # is empty, and concat_chain of the empty chain is the empty sequence).
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        # `result` is the concatenation of the suffix chain[i:].
        Invariant(result == concat_chain(chain.drop(i)))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec fully pins the output on the ENTIRE precondition domain (len(chain)>=1): Ensures(Implies(consider_chain, Result()==concat_chain(chain))) and Ensures(Implies(not consider_chain, Result()==chain[0])). Both branches are deterministic; concat_chain is a DEEP front-recursive fold (no consumed @ContractOnly axiom). There is no under-specified region for a verifying-but-wrong impl to hide in.

ATTACK PROTOCOL. Command per attack: `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-10356 <atk>`. Same-spec confirmed via `adversary same-spec` on atk1 (SAME) and atk8 (SAME); every attack edits ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical).

6+ DISTINCT wrong impls, all NOT-A-COUNTEREXAMPLE (exit 2, verification failed = spec rejected):
- atk_prepatch.py (prepatch, return chain[0]) -> FAILS verify. prepatch_reproduced=true.
- atk1.py (partial-domain: return chain[0] for both flags) -> FAILS verify (exit 2).
- atk2.py (boundary/off-by-one: backward loop starts i=len-1, drops chain[0]) -> FAILS verify (exit 2).
- atk3.py (wrong concat order: result = result + chain[i-1]) -> FAILS verify (exit 2).
- atk4.py (control-flow-effect: branch swap, concat when NOT consider_chain) -> FAILS verify (exit 2).
- atk5.py (ungrounded-oracle echo: class-only returns chain[len-1] instead of chain[0]) -> FAILS verify (exit 2).
- atk6.py (extra-token: chain[0] + concat_chain(chain), duplicates own marks) -> FAILS verify (exit 2).
- atk7.py (partial-domain: correct only when len==1, else chain[0]) -> FAILS verify (exit 2).

### One candidate
- atk8.py (correct alternative: `if not consider_chain: return chain[0]` else `return concat_chain(chain)`) -> CANDIDATE (shares spec AND verifies, 9.0s). Per protocol I MATERIALIZED its faithful refined patch (behaviorally identical to gold get_unpacked_marks: full MRO concatenation + consider_mro=False class-only, plus store_mark consider_mro=False) and RAN the official harness: run_resolve('pytest-dev__pytest-10356', patch) => RESOLVED=True, completed=True, attempts=1, flaky=False. A resolving echo of the gold is NOT a weakness (post-2026-08-06 policy). Patch file 

POSITIVE CONTROL: positive_control.py (= bundle model.py, the backward-loop impl) verifies (nagini_verify.sh exit 0).

REFINEMENT.md AUDIT: leg kinds = 3xR, 1xR/I, 1xA-reference. NO kind-3 (unexpressible-changed-op), NO consumed @ContractOnly axiom (model.py axioms region empty). The single changed operation (collect along full MRO) is modeled DEEPLY as concat_chain (A-reference A4), validated == the real _pytest.mark.structures.get_unpacked_marks by axiom_check.py/G-AX over F2P shape C(A,B)->[c,a,b], boundary shapes, and ~4000 fuzz DAGs at the ordered per-mark-name level. store_mark(consider_mro=False) call-site (site B) establishes chain[k]=own-marks abstraction, audited by G-AX (classes built through real decorator/store_mark path). A-reference correspondence holds. meta.json records G-AX pass, G-CONF pass, G-EQ pass. Every A-leg's correspondence to real callees checked and holds.

CONCLUSION: 8 attacks run; the sole verifying candidate's materialized faithful patch RESOLVES under the official harness. verify=>correct holds for this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-10356 nagini bundle. No diverging input found; the modeled function agrees with the real repo callee on all tested inputs.

Evidence:
- model.py verifies with pinned Nagini (exit 0, 7.82s).
- axiom_check.py (G-AX) passes against the REAL repo worktree at base_commit's patched function get_unpacked_marks: concat_chain deep model == real callee over F2P + boundary shapes + ~4000 fuzz hierarchies (both consider_mro=True and False), 0 violations.
- Independent adversarial probe (6000 random class DAGs, plus edge cases: pytestmark set directly as a single non-list Mark in __dict__, subclass of such, duplicate-name marks with differing args along MRO) found ZERO divergences between model's concat_chain(chain)/chain[0] and real get_unpacked_marks(obj, consider_mro=True/False).

Spec analysis:
- Postcondition consider_chain=True -> Result == concat_chain(chain) exactly matches the real MRO-ordered concatenation of each class's own __dict__['pytestmark'] (each holding only directly-applied marks since post-patch store_mark uses consider_mro=False).
- Postcondition consider_chain=False -> Result == chain[0] matches the class-only branch (obj.__dict__.get('pytestmark', [])).
- Requires(len(chain) >= 1) is not overconstraining: __mro__ always contains the class itself, so >=1 always holds in reality.
- The int/name-level abstraction is a faithful ORDERED projection of the F2P observable (ordered mark-name list); confirmed the real callee preserves full mark order/args along the MRO ([('dup',('argB',)),('dup',('argA',))]), so name-projection doesn't drop discriminating order.
- The model scopes to the class branch (the branch the F2P test exercises); the non-class branch being unmodeled is a documented scoping decision, not a modeled-vs-real disagreement.

Spec region markers present and intact (axioms/pure/pre/post/invariants/impl). No evidence the spec is too strong or drifts from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the solver-visible spec view = spec_view(model.py) (elided-impl projection that G-LEAK/panel_3 screens), NOT the auditor artifacts refinement.md/mapping.md/patch.diff (which contain the gold verbatim but are grader references, not solver-facing). Mechanical screen (leakage.screen) PASSES with zero hard failures.

Detailed review of the spec view:
- No diff markers, no gold-patch line reproduced (>=8 normalized chars), no patched file path 'src/_pytest/mark/structures.py' or dotted module, no narration words.
- Zero patched repo symbols appear: get_unpacked_marks, store_mark, pytestmark, consider_mro, normalize_mark_list, __mro__, __dict__ are all ABSENT. The model renames to non-leaking generic identifiers (unpacked_tokens / consider_chain / concat_chain / chain).
- The only '_pytest' hit is the substring inside the public instance-id header 'pytest-dev__pytest-10356' on docstring line 1 — not the module path _pytest.mark.structures. Not a leak.

Semantic check vs the PUBLIC problem_statement (title 'Consider MRO when obtaining marks for classes'): the problem statement already publicly states the desired fix — merge marker values by MRO so a class inheriting from two decorated baseclasses keeps BOTH markers, and even ships a metaclass snippet concatenating over self.__mro__. The spec docstring's abstract behaviour ('linearised ancestor chain', 'concatenation of every chain member's own token list ... yields BOTH ancestors' tokens, not just one', 'consider only directly-attached tokens') is a faithful abstract restatement of that public request. It reveals nothing about the gold EDIT (the isinstance(obj,type) branch, __dict__.get, the consider_mro=False store_mark call-site) beyond what the problem statement already discloses. The consider_chain/chain[0] branch is a generic modeling artifact, not a repo-mechanism leak.

Conclusion: spec view does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
