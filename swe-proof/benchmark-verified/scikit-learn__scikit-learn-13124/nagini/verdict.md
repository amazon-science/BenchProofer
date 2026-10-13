# P2 adversarial audit — scikit-learn__scikit-learn-13124

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,28 +85,14 @@
     # post-conditions-end
     # impl-start
     start = seed_state(seed)
-    cur = start
     result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
-        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
-                  state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
+        cur = seed_state(seed)  # fresh source from the raw seed, every class
         result = result + [cur]
-        cur = advance(cur)
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,26 +85,15 @@
     # post-conditions-end
     # impl-start
     start = seed_state(seed)
-    cur = start
+    cur = advance(start)
     result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
         Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
-                  state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
+                  state_stream(advance(start), n_classes))
         result = result + [cur]
         cur = advance(cur)
         i = i + 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,11 @@
     result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
-        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
-                  state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
         result = result + [cur]
-        cur = advance(cur)
+        cur = advance(advance(cur))
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,11 @@
     result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
-        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
-                  state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
+        cur = advance(cur)
         result = result + [cur]
-        cur = advance(cur)
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,26 +85,18 @@
     # post-conditions-end
     # impl-start
     start = seed_state(seed)
+    result = []  # type: List[int]
+    if n_classes == 1:
+        result = result + [seed_state(seed)]
+        return result
     cur = start
-    result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
         Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                   state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
         result = result + [cur]
         cur = advance(cur)
         i = i + 1
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,12 @@
     result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
-        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
-                  state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
-        Assert(state_stream(cur, n_classes - i) ==
-               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
         result = result + [cur]
         cur = advance(cur)
         i = i + 1
+    result = result + [cur]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -85,24 +85,15 @@
     # post-conditions-end
     # impl-start
     start = seed_state(seed)
+    result = []  # type: List[int]
     cur = start
-    result = []  # type: List[int]
     i = 0
     while i < n_classes:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n_classes)
         Invariant(len(result) == i)
-        # "what is built ++ the stream of the rest == the whole stream":
-        # `result` is the first i draw states and `cur` is the state the i-th
-        # class would draw, so the stream of the remaining n-i classes from
-        # `cur` completes exactly the full stream.
         Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                   state_stream(start, n_classes))
-        # invariants-end
-        # The remaining stream is non-empty (i < n_classes), so it unfolds to
-        # its head `cur` followed by the stream from the advanced state --
-        # exactly the move performed below.
         Assert(state_stream(cur, n_classes - i) ==
                PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
         result = result + [cur]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13124.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stratified splitter assigns, independently within each class, a randomized
  test-fold ordering drawn from a configured pseudo-random source. The source
  is described by a single seed value. When several classes are processed in
  turn, the randomized draw used for each class must come from one shared
  pseudo-random stream that ADVANCES between classes: the draw for the k-th
  class is the stream's state after k advances from the seed's initial state.

  The consequence the specification pins is that successive classes are NOT all
  drawn from one and the same unchanging state. A correct splitter therefore
  makes the per-class draws depend on the position in the stream (class 0 from
  the initial state, class 1 from the once-advanced state, and so on), so that
  the whole assignment is a function of the entire stream rather than of a
  single repeated draw.

The pseudo-random source's internal state is modelled as an integer. Turning
the configured seed into a source, and advancing the source by one draw, are
unchanged primitives, modelled as abstract pure functions (`seed_state`,
`advance`) whose real counterparts are validated out-of-band by axiom_check.py
(G-AX). The per-class stream of draw states is modelled deeply as a
front-recursive fold (`state_stream`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def seed_state(seed: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer seed (the unchanged seed-to-source conversion). Abstract: the proof
    relies only on this being a deterministic function of the seed, not on any
    particular value. Real counterpart + executable soundness: mapping.md /
    axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive per-class draws differ)
    is the discriminating fact validated by axiom_check.py (G-AX), not a
    consumed contract here. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def state_stream(s: int, n: int) -> PSeq[int]:
    """The sequence of draw states for `n` successive classes sharing one
    advancing source that starts at state `s`: class 0 draws from `s`, class 1
    from `advance(s)`, class k from the k-fold advance of `s`. Front-recursive
    on `n` so a single unfold is available per loop step."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(s) + state_stream(advance(s), n - 1)
# pure-end


def per_class_draw_states(seed: int, n_classes: int) -> List[int]:
    """Per-class draw states when `n_classes` classes are processed in turn
    from the source configured by integer `seed`. Element k is the state the
    k-th class's randomized draw is taken from."""
    # pre-conditions-start
    Requires(n_classes >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_classes)
    # The per-class draw states are the advancing stream from the seed's
    # initial state: class k draws from the k-fold-advanced state, so no two
    # classes are pinned to one and the same unchanging state.
    Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes))
    # post-conditions-end
    # impl-start
    start = seed_state(seed)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_classes:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_classes)
        Invariant(len(result) == i)
        # "what is built ++ the stream of the rest == the whole stream":
        # `result` is the first i draw states and `cur` is the state the i-th
        # class would draw, so the stream of the remaining n-i classes from
        # `cur` completes exactly the full stream.
        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                  state_stream(start, n_classes))
        # invariants-end
        # The remaining stream is non-empty (i < n_classes), so it unfolds to
        # its head `cur` followed by the stream from the advanced state --
        # exactly the move performed below.
        Assert(state_stream(cur, n_classes - i) ==
               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
        result = result + [cur]
        cur = advance(cur)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition is an EXACT functional equality: Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes)), which fully pins the output to the advancing stream [s, advance(s), advance^2(s), ...] for every input. Any verifying impl is therefore behaviorally identical to gold; no verifying-but-wrong impl exists.

same-spec: all 7 attacks + positive_control return SAME (byte-identical spec signature; only impl region edited).

7 DISTINCT wrong/alternative impls:
- atk_1.py (control-flow-effect / PREPATCH BUG REPRODUCTION): every class re-seeded via cur=seed_state(seed) inside loop -> constant list [start,start,...]. weakness EXIT=2 (does not verify) -> REJECTED. Reproduces the prepatch defect (matches model_prepatch.py; prepatch_reproduced=true).
- atk_2.py (boundary/off-by-one): stream started from advance(start), whole sequence shifted by one. EXIT=2 REJECTED.
- atk_3.py (boundary/stride): advance(advance(cur)) per class (stride 2). EXIT=2 REJECTED.
- atk_4.py (control-flow-effect): advance before emit, so class 0 gets advance(start). EXIT=2 REJECTED.
- atk_5.py (partial-domain): correct advancing stream except a special-case shortcut for n_classes==1 emitting seed_state(seed) (== correct for k=0, so this branch is actually still correct on value; kept as a partial-domain probe) -- overall EXIT=2 REJECTED (invariant/postcondition on the shortcut branch not provable).
- atk_6.py (wrong-length): appends an extra cur after the loop -> len == n_classes+1. EXIT=2 REJECTED (len postcondition).
- atk_7.py (ungrounded-oracle echo / correct ALTERNATIVE impl with an extra Assert): weakness EXIT=0 CANDIDATE (shares spec AND verifies, 10.5s). Behaviorally identical to gold.

MANDATORY resolve on the CANDIDATE (atk_7): materialized its faithful refined patch = the gold patch verbatim (patch.diff, the single edit rng = check_random_state(self.random_state)) and RAN it through the official harness: run_resolve('scikit-learn__scikit-learn-13124', patch) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So this verifying candidate's faithful patch DOES resolve -> a valid echo per the G-PANEL-1/G-EQ resolved-echo policy, NOT a weakness. No verifying wrong impl's patch failed to resolve.

Positive control: unchanged model.py verifies (weakness EXIT=0, CANDIDATE by construction; its faithful patch is the gold, resolves).

A-leg audit (the focus): refinement.md legs A1..A5 are all R (type refinement on int seed / class-count / element<->draw correspondence) or A-reference (A3 seed_state = RandomState(seed) initial state, hoisted 'once'; A4 advance = per-class .shuffle state move; state_stream = the advancing stream). Verified there is NO A-consumed axiom and NO kind-3 (unexpressible-changed-op) step: seed_state/advance carry no Ensures, and the discriminating fact (source advances vs. repeats) is modeled DEEPLY via the front-recursive state_stream threaded by the impl loop, not hidden behind a value axiom. The proof goes through by definitional unfolding of state_stream only.

A-reference soundness (G-AX) independently executed: ran axiom_check.py against real numpy+sklearn -> AX_EXIT=0 ('shared source advances over 25 seeds; re-seed constant over 25 seeds; real patched StratifiedKFold seed-dependent end-to-end'). Confirms advance is a genuine state MOVE and the abstract callees correspond to the real RandomState/check_random_state/KFold.shuffle machinery -- the model<->patch correspondence holds.

Conclusion: 6 distinct wrong impls (incl. prepatch) all rejected by the tight equality spec; the only verifying candidate is a correct echo whose materialized faithful patch RESOLVES (executed). verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13124.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stratified splitter assigns, independently within each class, a randomized
  test-fold ordering drawn from a configured pseudo-random source. The source
  is described by a single seed value. When several classes are processed in
  turn, the randomized draw used for each class must come from one shared
  pseudo-random stream that ADVANCES between classes: the draw for the k-th
  class is the stream's state after k advances from the seed's initial state.

  The consequence the specification pins is that successive classes are NOT all
  drawn from one and the same unchanging state. A correct splitter therefore
  makes the per-class draws depend on the position in the stream (class 0 from
  the initial state, class 1 from the once-advanced state, and so on), so that
  the whole assignment is a function of the entire stream rather than of a
  single repeated draw.

The pseudo-random source's internal state is modelled as an integer. Turning
the configured seed into a source, and advancing the source by one draw, are
unchanged primitives, modelled as abstract pure functions (`seed_state`,
`advance`) whose real counterparts are validated out-of-band by axiom_check.py
(G-AX). The per-class stream of draw states is modelled deeply as a
front-recursive fold (`state_stream`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def seed_state(seed: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer seed (the unchanged seed-to-source conversion). Abstract: the proof
    relies only on this being a deterministic function of the seed, not on any
    particular value. Real counterpart + executable soundness: mapping.md /
    axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive per-class draws differ)
    is the discriminating fact validated by axiom_check.py (G-AX), not a
    consumed contract here. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def state_stream(s: int, n: int) -> PSeq[int]:
    """The sequence of draw states for `n` successive classes sharing one
    advancing source that starts at state `s`: class 0 draws from `s`, class 1
    from `advance(s)`, class k from the k-fold advance of `s`. Front-recursive
    on `n` so a single unfold is available per loop step."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(s) + state_stream(advance(s), n - 1)
# pure-end


def per_class_draw_states(seed: int, n_classes: int) -> List[int]:
    """Per-class draw states when `n_classes` classes are processed in turn
    from the source configured by integer `seed`. Element k is the state the
    k-th class's randomized draw is taken from."""
    # pre-conditions-start
    Requires(n_classes >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_classes)
    # The per-class draw states are the advancing stream from the seed's
    # initial state: class k draws from the k-fold-advanced state, so no two
    # classes are pinned to one and the same unchanging state.
    Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes))
    # post-conditions-end
    # impl-start
    start = seed_state(seed)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_classes:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_classes)
        Invariant(len(result) == i)
        # "what is built ++ the stream of the rest == the whole stream":
        # `result` is the first i draw states and `cur` is the state the i-th
        # class would draw, so the stream of the remaining n-i classes from
        # `cur` completes exactly the full stream.
        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                  state_stream(start, n_classes))
        # invariants-end
        # The remaining stream is non-empty (i < n_classes), so it unfolds to
        # its head `cur` followed by the stream from the advanced state --
        # exactly the move performed below.
        Assert(state_stream(cur, n_classes - i) ==
               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
        result = result + [cur]
        cur = advance(cur)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition is an EXACT functional equality: Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes)), which fully pins the output to the advancing stream [s, advance(s), advance^2(s), ...] for every input. Any verifying impl is therefore behaviorally identical to gold; no verifying-but-wrong impl exists.

same-spec: all 7 attacks + positive_control return SAME (byte-identical spec signature; only impl region edited).

7 DISTINCT wrong/alternative impls:
- atk_1.py (control-flow-effect / PREPATCH BUG REPRODUCTION): every class re-seeded via cur=seed_state(seed) inside loop -> constant list [start,start,...]. weakness EXIT=2 (does not verify) -> REJECTED. Reproduces the prepatch defect (matches model_prepatch.py; prepatch_reproduced=true).
- atk_2.py (boundary/off-by-one): stream started from advance(start), whole sequence shifted by one. EXIT=2 REJECTED.
- atk_3.py (boundary/stride): advance(advance(cur)) per class (stride 2). EXIT=2 REJECTED.
- atk_4.py (control-flow-effect): advance before emit, so class 0 gets advance(start). EXIT=2 REJECTED.
- atk_5.py (partial-domain): correct advancing stream except a special-case shortcut for n_classes==1 emitting seed_state(seed) (== correct for k=0, so this branch is actually still correct on value; kept as a partial-domain probe) -- overall EXIT=2 REJECTED (invariant/postcondition on the shortcut branch not provable).
- atk_6.py (wrong-length): appends an extra cur after the loop -> len == n_classes+1. EXIT=2 REJECTED (len postcondition).
- atk_7.py (ungrounded-oracle echo / correct ALTERNATIVE impl with an extra Assert): weakness EXIT=0 CANDIDATE (shares spec AND verifies, 10.5s). Behaviorally identical to gold.

MANDATORY resolve on the CANDIDATE (atk_7): materialized its faithful refined patch = the gold patch verbatim (patch.diff, the single edit rng = check_random_state(self.random_state)) and RAN it through the official harness: run_resolve('scikit-learn__scikit-learn-13124', patch) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So this verifying candidate's faithful patch DOES resolve -> a valid echo per the G-PANEL-1/G-EQ resolved-echo policy, NOT a weakness. No verifying wrong impl's patch failed to resolve.

Positive control: unchanged model.py verifies (weakness EXIT=0, CANDIDATE by construction; its faithful patch is the gold, resolves).

A-leg audit (the focus): refinement.md legs A1..A5 are all R (type refinement on int seed / class-count / element<->draw correspondence) or A-reference (A3 seed_state = RandomState(seed) initial state, hoisted 'once'; A4 advance = per-class .shuffle state move; state_stream = the advancing stream). Verified there is NO A-consumed axiom and NO kind-3 (unexpressible-changed-op) step: seed_state/advance carry no Ensures, and the discriminating fact (source advances vs. repeats) is modeled DEEPLY via the front-recursive state_stream threaded by the impl loop, not hidden behind a value axiom. The proof goes through by definitional unfolding of state_stream only.

A-reference soundness (G-AX) independently executed: ran axiom_check.py against real numpy+sklearn -> AX_EXIT=0 ('shared source advances over 25 seeds; re-seed constant over 25 seeds; real patched StratifiedKFold seed-dependent end-to-end'). Confirms advance is a genuine state MOVE and the abstract callees correspond to the real RandomState/check_random_state/KFold.shuffle machinery -- the model<->patch correspondence holds.

Conclusion: 6 distinct wrong impls (incl. prepatch) all rejected by the tight equality spec; the only verifying candidate is a correct echo whose materialized faithful patch RESOLVES (executed). verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Role: panel_2 (faithfulness). Verdict FAITHFUL. Rationale: (1) model.py verifies under pinned Nagini (Verification successful, 10.19s). (2) seed_state/advance are @ContractOnly abstract pure symbols claiming only determinism (no value contract); the real numpy RandomState transition IS deterministic in (state, m), and within the balanced modeled domain m is constant, so advance is a faithful deterministic function of state alone. (3) The modeled function's signature (seed, n_classes) has no per-class-count parameter, so the unbalanced regime where the single-advance abstraction would diverge is not expressible by the model — it is genuinely out of scope, not a hidden overclaim. (4) The abstraction domain matches the correctness oracle: the F2P test test_shuffle_stratifiedkfold uses balanced y=[0]*20+[1]*20, and G-CONF's differential check (real seed_state/advance callees + unchanged downstream bookkeeping vs real patched StratifiedKFold._make_test_folds) passed 100k balanced fuzz + boundary cases with zero disagreements. (5) Empirically confirmed: real shared-advancing RandomState per-class states == model state_stream for balanced configs. The spec is neither too strong nor drifting from real repo behavior within its declared domain; a verifying same-spec impl reproduces the gold's balanced per-class draw states and thus resolves the F2P. NB: this cell is flagged G-PANEL-1=fail in the queue (a separate role); the panel_2 faithfulness dimension is clean.

Counterexample / evidence:

```
N/A — no counterexample within the modeled domain. Empirical check: balanced cases (2,20,5),(2,5,5),(3,4,2),(5,6,5),(8,10,4) over seeds 0-2 all match real shared-source per-class states exactly; G-CONF passed 100042 balanced configurations with 0 disagreements.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `rng = self.random_state` -> `rng = check_random_state(self.random_state)` in StratifiedKFold._make_test_folds (+ docstring reword), i.e. convert the seed to a RandomState source ONCE and share the advancing source across per-class draws instead of re-seeding an identical fresh source per class.

Mechanical G-LEAK screen PASSES (leakage.screen -> passed=True, no hard failures).

Semantic gold-reconstruction check of the spec view (docstring + axioms/pure/pre/post regions):
- No patched file path (`sklearn/model_selection/_split.py`) or dotted module path present.
- No patched repo symbol echoed: `StratifiedKFold`, `_make_test_folds`, `check_random_state`, `random_state`, `RandomState`, `shuffle` all absent. Spec-view identifiers are abstract (`seed_state`, `advance`, `state_stream`, `per_class_draw_states`).
- No verbatim gold-diff line, no diff markers.
- No bug/fix narration; comments explicitly frame everything as 'desired behaviour, not an edit' and call the primitives 'unchanged'.

The spec formalizes desired behavior (per-class draws come from one shared, ADVANCING pseudo-random stream so different seeds yield different, position-dependent draws) at an abstract mathematical level. This is exactly the behavior the PUBLIC problem_statement already describes as expected: the reporter shows that with shuffle=True the batches are identical for any random_state and states 'I expect batches to be different ... for different random_state seeds.' The spec neither localizes the one-line edit nor names the fix function/callee, so it does not reconstruct the gold edit beyond what the problem_statement already makes public. Describing correct behavior is the spec's legitimate purpose.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
