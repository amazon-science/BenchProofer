# P2 adversarial audit — matplotlib__matplotlib-23476

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,8 +105,6 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
-    else:
-        state[key_dpi()] = state[key_dpi()]
+    # PREPATCH: the round trip's mapping is produced WITHOUT the selection.
+    pass
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,8 +105,7 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
-    else:
-        state[key_dpi()] = state[key_dpi()]
+    # Selection applied unconditionally: the dpi entry always takes the
+    # reference value, even when no reference entry was recorded.
+    state[key_dpi()] = reference_value
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,9 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
+    # Real-world wrong idiom: `state['_dpi'] = state.get('_original_dpi') or
+    # state['_dpi']` -- a reference value of 0 is silently treated as absent.
+    if key_reference() in state and state[key_reference()] != 0:
         state[key_dpi()] = state[key_reference()]
     else:
         state[key_dpi()] = state[key_dpi()]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,4 +109,6 @@
         state[key_dpi()] = state[key_reference()]
     else:
         state[key_dpi()] = state[key_dpi()]
+    while True:
+        pass
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,4 +109,5 @@
         state[key_dpi()] = state[key_reference()]
     else:
         state[key_dpi()] = state[key_dpi()]
+    raise ValueError("serialisation aborted")
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,8 +105,10 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
+    live = state[key_dpi()]
     if key_reference() in state:
         state[key_dpi()] = state[key_reference()]
+        state[key_reference()] = live
     else:
         state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,8 +105,8 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
-    else:
-        state[key_dpi()] = state[key_dpi()]
+    # The selection is driven ENTIRELY by the spec's pre-state grounding
+    # parameters; the mapping itself is never queried for the reference entry.
+    if reference_present:
+        state[key_dpi()] = reference_value
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,8 +105,10 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
+    # Identity on int tokens (x | 0 == x), but the value carrier of the real
+    # entry is a float, where `|` has no counterpart at all.
     if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
+        state[key_dpi()] = state[key_reference()] | 0
     else:
-        state[key_dpi()] = state[key_dpi()]
+        state[key_dpi()] = state[key_dpi()] | 0
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,8 +105,9 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
+    if reference_present:
+        state[key_dpi()] = reference_value
+    else:
+        # unguarded: the reference entry is NOT present on this path
         state[key_dpi()] = state[key_reference()]
-    else:
-        state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -109,4 +109,10 @@
         state[key_dpi()] = state[key_reference()]
     else:
         state[key_dpi()] = state[key_dpi()]
+    # On the int carrier this guard is provably dead (integer equality is
+    # reflexive), so the corrupting write below is unreachable IN THE MODEL.
+    # Under the value-token refinement the carrier is a float, where a NaN dpi
+    # makes exactly this guard TRUE.
+    if state[key_dpi()] != state[key_dpi()]:
+        state[key_dpi()] = 0
     # impl-end
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -106,7 +106,8 @@
     # post-conditions-end
     # impl-start
     if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
+        if state[key_dpi()] != state[key_reference()]:
+            state[key_dpi()] = state[key_reference()]
     else:
         state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,14 @@
     # post-conditions-end
     # impl-start
     if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
+        v = state[key_reference()]
+        # Entry IDENTITY / ORDER: the reference entry is removed and re-added
+        # with the same value. Membership and value are restored, so the token
+        # carrier cannot see it -- but the real mapping's insertion order (and
+        # the identity of the entry) is not what it was.
+        del state[key_reference()]
+        state[key_reference()] = v
+        state[key_dpi()] = v
     else:
         state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -107,6 +107,4 @@
     # impl-start
     if key_reference() in state:
         state[key_dpi()] = state[key_reference()]
-    else:
-        state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -105,8 +105,8 @@
                                           state[k] == Old(state[k]))))
     # post-conditions-end
     # impl-start
-    if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
+    if key_dpi() + 1 in state:
+        state[key_dpi()] = state[key_dpi() + 1]
     else:
         state[key_dpi()] = state[key_dpi()]
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -106,7 +106,7 @@
     # post-conditions-end
     # impl-start
     if key_reference() in state:
-        state[key_dpi()] = state[key_reference()]
+        state[key_dpi()] = state[key_reference()] // 1
     else:
-        state[key_dpi()] = state[key_dpi()]
+        state[key_dpi()] = state[key_dpi()] // 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23476.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A figure's dpi must be STABLE under a save/restore round trip: taking a
  figure through such a round trip, repeatedly, must leave the recorded dpi at
  the value it already had, rather than letting it drift upwards on every cycle
  (doubling until it grows past what can be represented).

  What a round trip carries is a mapping of the figure's recorded values. That
  mapping always holds a dpi entry, and it may also hold a second entry recording
  a reference dpi. The behaviour required of the step specified here: whenever
  the reference entry is present, the dpi entry is recorded as that reference
  value; otherwise the dpi entry keeps the value it already held.

  Every entry of the mapping other than the dpi entry -- including the reference
  entry itself -- is left exactly as it was; only the dpi entry may change.

Modelling choices (Nagini fragment):
  * The mapping of recorded values is a ``Dict[int, int]`` from an entry-name
    token to that entry's value token. Only membership of, and the value at, the
    two relevant entry names is observed, so an integer-keyed mapping is the
    faithful carrier (mapping.md §2). ``key_dpi`` names the dpi entry;
    ``key_reference`` names the reference-dpi entry; they are distinct.
  * dpi values are modelled as ``int`` tokens. The specified behaviour SELECTS
    one of two stored dpi values by entry membership; it never computes on the
    value, so the tested behaviour is precision-independent and the value
    carrier need not be a real ``float`` (mapping.md §2).

The mapping is genuinely mutated in place (the dpi entry is reassigned), so it
is held at FULL permission with the post-state stated exactly via ``Old``. No
callee is axiomatised: the behaviour is pure mapping logic, modelled deeply.
Markers (machine-parsed) delimit the spec / proof / impl regions.

The operation is a bounded, loop-free selection carried out as one step of the
round trip: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges would
satisfy the value postconditions only vacuously while hanging the round trip
forever -- the cycle the behaviour is about would never complete.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def key_dpi() -> int:
    # The entry name of the dpi entry of the mapping.
    return 0


@Pure
def key_reference() -> int:
    # The entry name of the reference-dpi entry, when present. Distinct from the
    # dpi entry name.
    return 1
# pure-end


def normalize_state_dpi(state: Dict[int, int],
                        reference_present: bool,
                        reference_value: int) -> None:
    # pre-conditions-start
    # The mapping is mutated in place (the dpi entry is reassigned), so it is
    # held at FULL permission. A mapping of recorded values always holds a dpi
    # entry.
    Requires(Acc(dict_pred(state)))
    Requires(state is not None)
    Requires(key_dpi() in state)
    # ``reference_present`` / ``reference_value`` capture, AT ENTRY, whether the
    # reference-dpi entry exists and (if so) its value. They are pre-state facts
    # about the input -- bound before any mutation -- so the selection guarantee
    # below gates on the genuine entry record rather than on a query against the
    # (mutated-in-place) mapping, which an implementation could perturb.
    Requires(reference_present == (key_reference() in state))
    Requires(Implies(reference_present, reference_value == state[key_reference()]))
    # The selection is a bounded, loop-free step of the round trip: it MUST
    # terminate -- total correctness. A diverging implementation would satisfy
    # the value postconditions only vacuously while hanging the round trip
    # forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(state)))
    # The dpi entry remains present ...
    Ensures(key_dpi() in state)
    # ... and now holds the reference value when a reference entry was present at
    # entry, the value it already held otherwise. The antecedents are the
    # captured ENTRY facts, so each implication has teeth: the recorded value
    # must be PRODUCED by the selection, not merely left at whatever it happened
    # to be.
    Ensures(Implies(reference_present, state[key_dpi()] == reference_value))
    Ensures(Implies(not reference_present, state[key_dpi()] == Old(state[key_dpi()])))
    # No entry other than the dpi entry changes: every other name's membership is
    # preserved, and no new name is introduced. In particular the reference entry
    # itself is untouched.
    Ensures(Forall(int, lambda k: Implies(k != key_dpi(),
                                          (k in state) == Old(k in state))))
    Ensures(Forall(int, lambda k: Implies(k != key_dpi() and Old(k in state),
                                          state[k] == Old(state[k]))))
    # post-conditions-end
    # impl-start
    if key_reference() in state:
        state[key_dpi()] = state[key_reference()]
    else:
        state[key_dpi()] = state[key_dpi()]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for matplotlib__matplotlib-23476/nagini. 15 same-spec attacks encoded (each a copy of the bundle model.py with ONLY the impl region edited; the concatenated non-impl byte range is IDENTICAL across all 15 attacks + the positive control: sha256[:16]=8e62668eed1c476c, exactly one distinct hash). same-spec: all 16 files -> SAME (exit 0), cmd `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-23476 <path>`. All weakness runs with SBU_BENCHMARK_DIR=benchmark-verified, SBU_ATTACK_VERIFY_TIMEOUT=1200, scheduled 3-at-a-time as concurrent background jobs (logs/w<N>.log); no timeouts, every run completed with a decided verdict (exit 0 or 2, never 124).

### PER-ATTACK RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-23476 atk_N.py`):
- atk_1.py (PREPATCH BUG re-encoded: `pass`, no selection) -> exit 2 NOT-A-COUNTEREXAMPLE, verification failed. PREPATCH REPRODUCED: the spec senses the real bug (independent re-check of G-DIFF).
- atk_2.py (PARTIAL DOMAIN: unconditional `state[key_dpi()] = reference_value`) -> exit 2, rejected (fails the reference-absent arm; `reference_value` is unconstrained there).
- atk_3.py (BOUNDARY / falsy-default: `.get(...) or state['_dpi']` idiom -- treats a reference value of 0 as absent) -> exit 2, rejected. The real-world wrong idiom is caught.
- atk_4.py (CONTROL-FLOW EFFECT: correct selection, then `while True: pass`) -> exit 2, rejected. MustTerminate(2) has teeth even AFTER the value postconditions are already established.
- atk_5.py (CONTROL-FLOW EFFECT: correct selection, then `raise ValueError`) -> exit 2, rejected.
- atk_6.py (FRAME: correct dpi selection but also clobbers the reference entry with the live value -- the regression that re-breaks stability on the NEXT round trip) -> exit 2, rejected by the Forall other-key frame clause.
- atk_7.py (UNGROUNDED-ORACLE ECHO: selection driven ENTIRELY by the spec's pre-state grounding parameters `reference_present`/`reference_value`; the mapping is never queried; no write at all in the absent arm) -> exit 0 CANDIDATE (13.3s). Faithful patch materialized (patch_7.diff: captures `'_original_dpi' in state` / its value into locals, writes only when present) and RUN through the official harness: `python resolve.py 7` -> run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=true, F2P 1/1 success (test_unpickle_with_device_pixel_ratio), 0 F2P failures, PASS_TO_PASS block with an empty failure list. => CORRECT ECHO (the absent arm's `state['_dpi'] = state['_dpi']` is a value no-op, so omitting the write is behaviourally identical), not a spec weakness.
- atk_8.py (VALUE-TOKEN ARITHMETIC with no float counterpart: `state[...] | 0`, identity on int tokens) -> exit 2, rejected. Good: the value carrier cannot be laundered through a bitwise op.
- atk_9.py (PARTIAL DOMAIN via UNGUARDED read: reads `state[key_reference()]` on the path where the reference entry is provably ABSENT -- a KeyError on any figure with no pixel-ratio record) -> exit 2, rejected.
- atk_10.py (INT-CARRIER DEAD BRANCH, the sharpest float->int refinement probe: correct selection, then `if state[k]!=state[k]: state[k]=0` -- provably dead on the int carrier by reflexivity, but LIVE on the real float carrier for a NaN dpi) -> exit 0 CANDIDATE (15.2s). Faithful patch materialized (patch_10.diff, the guard transliterated verbatim onto the real float state) and RUN: run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => CORRECT ECHO on the graded suite. See the ADVISORY below: this is the one place where the int-token value carrier is genuinely weaker than reality, and it is not a resolve-level break because no graded test constructs a NaN dpi.
- atk_11.py (CONDITIONAL WRITE: writes the dpi entry only when the selected value differs from the recorded one) -> exit 0 CANDIDATE (20.9s). Faithful patch materialized (patch_11.diff) and RUN: run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => correct echo (skipping a write of an equal value is observationally identical on a dict).
- atk_12.py (ENTRY IDENTITY/ORDER: del + reinsert the reference entry with the same value, then the correct selection) -> exit 2, rejected. The frame clause forces the reference entry to be left literally untouched.
- atk_13.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_2: one-armed `.get`, no else self-assign) -> exit 0 CANDIDATE (18.9s). Faithful patch materialized (patch_13.diff) and RUN: resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => correct echo, independently re-confirmed.
- atk_14.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_8: ungrounded key-token ARITHMETIC `key_dpi()+1`, never names key_reference()) -> exit 0 CANDIDATE (19.1s). Faithful patch materialized (patch_14.diff, probe key = '`_original_dpi`' per the mapping.md §2 token bijection 0<->'`_dpi`', 1<->'`_original_dpi`') and RUN: resolved=True, completed=True, patch_applied=true, F2P 1/1, no P2P failures. => correct echo; confirms the key-token leg is tight (the only int satisfying the spec at that position IS the reference entry name).
- atk_15.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_11: value-token `// 1`) -> exit 0 CANDIDATE (18.9s). Faithful patch materialized (patch_15.diff) and RUN: resolved=True, completed=True, patch_applied=true, F2P 1/1, no P2P failures. => correct echo (`float // 1` is identity on the integral DPI values 42.0/294.0 the graded suite exercises).

**POSITIVE CONTROL:** `SBN_VERIFY_TIMEOUT=900 bash scripts/nagini_verify.sh pos_control.py` (byte copy of the bundle model.py) -> 'Verification successful', 14.40s, exit 0.

**SCORE:** 15 attacks, 6 CANDIDATES (atk_7, atk_10, atk_11, atk_13, atk_14, atk_15). ALL SIX faithful refined patches were MATERIALIZED against a git worktree at base_commit 33a0599711d26dc2b79f851c6daed4947df7c167 and EXECUTED through the official harness via swebench_unified.harness.run_resolve (image pre-built with ensure_image -> None, i.e. present; runs scheduled 3-at-a-time). All six RESOLVED (resolved=True, completed=True, flaky=False, patch_successfully_applied=true, F2P test_unpickle_with_device_pixel_ratio 1/1, no P2P failures). Zero speculation: no candidate's resolve verdict is asserted without an executed run. => NO verify-but-not-correct witness exists among these 15; the 9 wrong-impl classes (prepatch, partial-domain x2, falsy-default boundary, divergence, exception, frame-clobber, value-token bitwise, entry-identity) are all REJECTED.

### REFINEMENT.MD AUDIT (A legs / deep-model references; R/I legs left to G-CONF as instructed):
- The `axioms` region of model.py is EMPTY (lines 46-47) and meta.json `axioms` == []. There is NO A-consumed leg: no @ContractOnly contract is consumed and the proof leans on no callee. The sole deep-model reference (meta.json deep_model_references[0], kind='A-reference') is `state['_dpi'] = state.get('_original_dpi', state['_dpi'])`, modeled DEEPLY in the impl region (membership branch + BOTH arms), so nothing is hidden behind an axiom. refinement.md §B's 'no kind-3' claim therefore holds: legs A1-A5 are each R, I, or R+I, and the R+I tags are genuine control/assignment identities under the token bijection -- I confirmed each by reading the gold hunk against the impl.
- A-REFERENCE CORRESPONDENCE CHECKED against the real callees at base_commit (via `git show 33a0599...:<file>`): (a) INSERTION POINT -- figure.py `__getstate__` at line 3015, body `state.pop('canvas')` then `state['_cachedRenderer'] = None` then `state['__mpl_version__'] = mpl.__version__`; patch.diff's hunk anchors exactly between the renderer-clearing and the version stamp, as refinement.md §A claims. (b) CARRIER -- `Artist.__getstate__` at artist.py:186-191 is `d = self.__dict__.copy(); d['stale_callback'] = None; return d`, i.e. `state` really is a plain `dict`, so `dict.get`/membership/in-place assignment are the true primitives and mapping.md §2's Dict[int,int] carrier is faithful. (c) OPTIONALITY of the reference entry -- `_original_dpi` is set at backend_bases.py:1656 (`figure._original_dpi = figure.dpi`, in FigureCanvasBase.`__init__`), consumed at 2104 (`dpi = ratio * self.figure._original_dpi`) and read defensively at 2284 (`getattr(self.figure, '_original_dpi', self.figure.dpi)`). The `getattr` default at 2284 is the repo's own admission that the attribute can be ABSENT -- which is exactly why the two-armed `.get` semantics (not a one-armed conditional) is the right deep model, and why atk_9's unguarded read must be, and is, rejected. (d) mapping.md §4's claim that `__getstate__` never writes `_original_dpi` is true of the gold hunk (verified against the printed method body), so binding reference_present/reference_value as PRE-STATE parameters faithfully describes both the pre- and post-state of that key; the antecedents have real teeth -- atk_1/atk_2/atk_3 all die on them, and the grounding is what makes atk_7's parameter-only echo behaviourally correct rather than vacuous.
- axiom_check.py (the A-reference validator) RE-RUN: exit 0, 'G-AX OK: deep model (== real dict.get('`_original_dpi`', state['`_dpi`'])) sound on 8 boundary + 50000 fuzz states'. Inspected the source: it compares the deep model against the LITERAL gold line (written independently), asserts the selected value equals `before.get('_original_dpi', before['_dpi'])`, AND asserts the no-other-key-changed frame, on real float DPI including the F2P 42.0/294.0 pair. Not a tautology.
- patch.diff verified BYTE-IDENTICAL to instance.json['patch'] (Python string compare -> True), so the resolve oracle really is the gold patch.
- IDENTIFIER DRIFT (cosmetic, not a defect): refinement.md legs A2/A3 and §C still spell the reference-entry symbol `key_original_dpi` / `original_present` / `original_value`, whereas the frozen model.py now uses `key_reference` / `reference_present` / `reference_value` (a de-leaking rename). The correspondence claims are unaffected -- the renamed symbols occupy the same positions and mapping.md §1 binds `key_reference()` to `'_original_dpi'` -- but the two documents should be re-synced. Likewise meta.json's top-level `region_hashes` is stale relative to the live file, while the G-HYGIENE-recorded block (impl 6129b417..., pre-conditions f5d67b97..., post-conditions a0c3ef6a..., pure c8b12333..., spec_view 18c836a7...) reproduces `markers.region_hashes(model.py)` EXACTLY -- I recomputed it. Bookkeeping, not a spec defect.

ADVISORY (not a break, flagged for the record): atk_10 is the sharpest surviving consequence of the float->int value-token refinement (mapping.md §2). On the int carrier `state[k] != state[k]` is provably FALSE, so Nagini discharges the branch as dead; on the real float carrier that guard is TRUE for a NaN dpi, and the branch zeroes the serialized dpi. matplotlib does accept `set_dpi(float('nan'))`, so this is a real behavioural divergence the int abstraction cannot see -- it is nevertheless not a verify-not-correct witness at the level G-EQ decides, because the materialized patch RESOLVED (executed: F2P 1/1, no P2P failures): no graded test constructs a NaN dpi. The same caveat covers atk_15 (`// 1` truncates a fractional dpi, identity on the integral values the suite uses). The refinement's stated justification -- the modeled op is pure value SELECTION, never arithmetic -- is what makes the abstraction sound, and the frame + selection clauses do enforce it against any impl that does not manufacture a value; atk_8's rejection (`| 0`) shows the enforcement is partial rather than uniform, so the leg's soundness rests on the argument, not on the verifier alone.

**VERDICT:** SOUND (advisory). 15 same-spec attacks all run to a decided verdict; 9 distinct wrong-impl classes REJECTED by the frozen spec (including the prepatch bug, so the spec demonstrably senses the fix); all 6 verifying candidates had their faithful refined patch materialized at base_commit and EXECUTED through run_resolve, and all 6 RESOLVED. No verify-does-not-imply-correct witness exhibited. Nothing INCONCLUSIVE: every needed verification and every needed resolve run completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23476.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A figure's dpi must be STABLE under a save/restore round trip: taking a
  figure through such a round trip, repeatedly, must leave the recorded dpi at
  the value it already had, rather than letting it drift upwards on every cycle
  (doubling until it grows past what can be represented).

  What a round trip carries is a mapping of the figure's recorded values. That
  mapping always holds a dpi entry, and it may also hold a second entry recording
  a reference dpi. The behaviour required of the step specified here: whenever
  the reference entry is present, the dpi entry is recorded as that reference
  value; otherwise the dpi entry keeps the value it already held.

  Every entry of the mapping other than the dpi entry -- including the reference
  entry itself -- is left exactly as it was; only the dpi entry may change.

Modelling choices (Nagini fragment):
  * The mapping of recorded values is a ``Dict[int, int]`` from an entry-name
    token to that entry's value token. Only membership of, and the value at, the
    two relevant entry names is observed, so an integer-keyed mapping is the
    faithful carrier (mapping.md §2). ``key_dpi`` names the dpi entry;
    ``key_reference`` names the reference-dpi entry; they are distinct.
  * dpi values are modelled as ``int`` tokens. The specified behaviour SELECTS
    one of two stored dpi values by entry membership; it never computes on the
    value, so the tested behaviour is precision-independent and the value
    carrier need not be a real ``float`` (mapping.md §2).

The mapping is genuinely mutated in place (the dpi entry is reassigned), so it
is held at FULL permission with the post-state stated exactly via ``Old``. No
callee is axiomatised: the behaviour is pure mapping logic, modelled deeply.
Markers (machine-parsed) delimit the spec / proof / impl regions.

The operation is a bounded, loop-free selection carried out as one step of the
round trip: it MUST terminate (a total-correctness obligation, carried as
``MustTerminate`` in the precondition). An implementation that diverges would
satisfy the value postconditions only vacuously while hanging the round trip
forever -- the cycle the behaviour is about would never complete.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def key_dpi() -> int:
    # The entry name of the dpi entry of the mapping.
    return 0


@Pure
def key_reference() -> int:
    # The entry name of the reference-dpi entry, when present. Distinct from the
    # dpi entry name.
    return 1
# pure-end


def normalize_state_dpi(state: Dict[int, int],
                        reference_present: bool,
                        reference_value: int) -> None:
    # pre-conditions-start
    # The mapping is mutated in place (the dpi entry is reassigned), so it is
    # held at FULL permission. A mapping of recorded values always holds a dpi
    # entry.
    Requires(Acc(dict_pred(state)))
    Requires(state is not None)
    Requires(key_dpi() in state)
    # ``reference_present`` / ``reference_value`` capture, AT ENTRY, whether the
    # reference-dpi entry exists and (if so) its value. They are pre-state facts
    # about the input -- bound before any mutation -- so the selection guarantee
    # below gates on the genuine entry record rather than on a query against the
    # (mutated-in-place) mapping, which an implementation could perturb.
    Requires(reference_present == (key_reference() in state))
    Requires(Implies(reference_present, reference_value == state[key_reference()]))
    # The selection is a bounded, loop-free step of the round trip: it MUST
    # terminate -- total correctness. A diverging implementation would satisfy
    # the value postconditions only vacuously while hanging the round trip
    # forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(state)))
    # The dpi entry remains present ...
    Ensures(key_dpi() in state)
    # ... and now holds the reference value when a reference entry was present at
    # entry, the value it already held otherwise. The antecedents are the
    # captured ENTRY facts, so each implication has teeth: the recorded value
    # must be PRODUCED by the selection, not merely left at whatever it happened
    # to be.
    Ensures(Implies(reference_present, state[key_dpi()] == reference_value))
    Ensures(Implies(not reference_present, state[key_dpi()] == Old(state[key_dpi()])))
    # No entry other than the dpi entry changes: every other name's membership is
    # preserved, and no new name is introduced. In particular the reference entry
    # itself is untouched.
    Ensures(Forall(int, lambda k: Implies(k != key_dpi(),
                                          (k in state) == Old(k in state))))
    Ensures(Forall(int, lambda k: Implies(k != key_dpi() and Old(k in state),
                                          state[k] == Old(state[k]))))
    # post-conditions-end
    # impl-start
    if key_reference() in state:
        state[key_dpi()] = state[key_reference()]
    else:
        state[key_dpi()] = state[key_dpi()]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for matplotlib__matplotlib-23476/nagini. 15 same-spec attacks encoded (each a copy of the bundle model.py with ONLY the impl region edited; the concatenated non-impl byte range is IDENTICAL across all 15 attacks + the positive control: sha256[:16]=8e62668eed1c476c, exactly one distinct hash). same-spec: all 16 files -> SAME (exit 0), cmd `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-23476 <path>`. All weakness runs with SBU_BENCHMARK_DIR=benchmark-verified, SBU_ATTACK_VERIFY_TIMEOUT=1200, scheduled 3-at-a-time as concurrent background jobs (logs/w<N>.log); no timeouts, every run completed with a decided verdict (exit 0 or 2, never 124).

### PER-ATTACK RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-23476 atk_N.py`):
- atk_1.py (PREPATCH BUG re-encoded: `pass`, no selection) -> exit 2 NOT-A-COUNTEREXAMPLE, verification failed. PREPATCH REPRODUCED: the spec senses the real bug (independent re-check of G-DIFF).
- atk_2.py (PARTIAL DOMAIN: unconditional `state[key_dpi()] = reference_value`) -> exit 2, rejected (fails the reference-absent arm; `reference_value` is unconstrained there).
- atk_3.py (BOUNDARY / falsy-default: `.get(...) or state['_dpi']` idiom -- treats a reference value of 0 as absent) -> exit 2, rejected. The real-world wrong idiom is caught.
- atk_4.py (CONTROL-FLOW EFFECT: correct selection, then `while True: pass`) -> exit 2, rejected. MustTerminate(2) has teeth even AFTER the value postconditions are already established.
- atk_5.py (CONTROL-FLOW EFFECT: correct selection, then `raise ValueError`) -> exit 2, rejected.
- atk_6.py (FRAME: correct dpi selection but also clobbers the reference entry with the live value -- the regression that re-breaks stability on the NEXT round trip) -> exit 2, rejected by the Forall other-key frame clause.
- atk_7.py (UNGROUNDED-ORACLE ECHO: selection driven ENTIRELY by the spec's pre-state grounding parameters `reference_present`/`reference_value`; the mapping is never queried; no write at all in the absent arm) -> exit 0 CANDIDATE (13.3s). Faithful patch materialized (patch_7.diff: captures `'_original_dpi' in state` / its value into locals, writes only when present) and RUN through the official harness: `python resolve.py 7` -> run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_successfully_applied=true, F2P 1/1 success (test_unpickle_with_device_pixel_ratio), 0 F2P failures, PASS_TO_PASS block with an empty failure list. => CORRECT ECHO (the absent arm's `state['_dpi'] = state['_dpi']` is a value no-op, so omitting the write is behaviourally identical), not a spec weakness.
- atk_8.py (VALUE-TOKEN ARITHMETIC with no float counterpart: `state[...] | 0`, identity on int tokens) -> exit 2, rejected. Good: the value carrier cannot be laundered through a bitwise op.
- atk_9.py (PARTIAL DOMAIN via UNGUARDED read: reads `state[key_reference()]` on the path where the reference entry is provably ABSENT -- a KeyError on any figure with no pixel-ratio record) -> exit 2, rejected.
- atk_10.py (INT-CARRIER DEAD BRANCH, the sharpest float->int refinement probe: correct selection, then `if state[k]!=state[k]: state[k]=0` -- provably dead on the int carrier by reflexivity, but LIVE on the real float carrier for a NaN dpi) -> exit 0 CANDIDATE (15.2s). Faithful patch materialized (patch_10.diff, the guard transliterated verbatim onto the real float state) and RUN: run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => CORRECT ECHO on the graded suite. See the ADVISORY below: this is the one place where the int-token value carrier is genuinely weaker than reality, and it is not a resolve-level break because no graded test constructs a NaN dpi.
- atk_11.py (CONDITIONAL WRITE: writes the dpi entry only when the selected value differs from the recorded one) -> exit 0 CANDIDATE (20.9s). Faithful patch materialized (patch_11.diff) and RUN: run_resolve resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => correct echo (skipping a write of an equal value is observationally identical on a dict).
- atk_12.py (ENTRY IDENTITY/ORDER: del + reinsert the reference entry with the same value, then the correct selection) -> exit 2, rejected. The frame clause forces the reference entry to be left literally untouched.
- atk_13.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_2: one-armed `.get`, no else self-assign) -> exit 0 CANDIDATE (18.9s). Faithful patch materialized (patch_13.diff) and RUN: resolved=True, completed=True, attempts=1, flaky=False, patch_applied=true, F2P 1/1, no P2P failures. => correct echo, independently re-confirmed.
- atk_14.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_8: ungrounded key-token ARITHMETIC `key_dpi()+1`, never names key_reference()) -> exit 0 CANDIDATE (19.1s). Faithful patch materialized (patch_14.diff, probe key = '`_original_dpi`' per the mapping.md §2 token bijection 0<->'`_dpi`', 1<->'`_original_dpi`') and RUN: resolved=True, completed=True, patch_applied=true, F2P 1/1, no P2P failures. => correct echo; confirms the key-token leg is tight (the only int satisfying the spec at that position IS the reference entry name).
- atk_15.py = PRIOR-PASS COUNTEREXAMPLE re-encoded (prior atk_11: value-token `// 1`) -> exit 0 CANDIDATE (18.9s). Faithful patch materialized (patch_15.diff) and RUN: resolved=True, completed=True, patch_applied=true, F2P 1/1, no P2P failures. => correct echo (`float // 1` is identity on the integral DPI values 42.0/294.0 the graded suite exercises).

**POSITIVE CONTROL:** `SBN_VERIFY_TIMEOUT=900 bash scripts/nagini_verify.sh pos_control.py` (byte copy of the bundle model.py) -> 'Verification successful', 14.40s, exit 0.

**SCORE:** 15 attacks, 6 CANDIDATES (atk_7, atk_10, atk_11, atk_13, atk_14, atk_15). ALL SIX faithful refined patches were MATERIALIZED against a git worktree at base_commit 33a0599711d26dc2b79f851c6daed4947df7c167 and EXECUTED through the official harness via swebench_unified.harness.run_resolve (image pre-built with ensure_image -> None, i.e. present; runs scheduled 3-at-a-time). All six RESOLVED (resolved=True, completed=True, flaky=False, patch_successfully_applied=true, F2P test_unpickle_with_device_pixel_ratio 1/1, no P2P failures). Zero speculation: no candidate's resolve verdict is asserted without an executed run. => NO verify-but-not-correct witness exists among these 15; the 9 wrong-impl classes (prepatch, partial-domain x2, falsy-default boundary, divergence, exception, frame-clobber, value-token bitwise, entry-identity) are all REJECTED.

### REFINEMENT.MD AUDIT (A legs / deep-model references; R/I legs left to G-CONF as instructed):
- The `axioms` region of model.py is EMPTY (lines 46-47) and meta.json `axioms` == []. There is NO A-consumed leg: no @ContractOnly contract is consumed and the proof leans on no callee. The sole deep-model reference (meta.json deep_model_references[0], kind='A-reference') is `state['_dpi'] = state.get('_original_dpi', state['_dpi'])`, modeled DEEPLY in the impl region (membership branch + BOTH arms), so nothing is hidden behind an axiom. refinement.md §B's 'no kind-3' claim therefore holds: legs A1-A5 are each R, I, or R+I, and the R+I tags are genuine control/assignment identities under the token bijection -- I confirmed each by reading the gold hunk against the impl.
- A-REFERENCE CORRESPONDENCE CHECKED against the real callees at base_commit (via `git show 33a0599...:<file>`): (a) INSERTION POINT -- figure.py `__getstate__` at line 3015, body `state.pop('canvas')` then `state['_cachedRenderer'] = None` then `state['__mpl_version__'] = mpl.__version__`; patch.diff's hunk anchors exactly between the renderer-clearing and the version stamp, as refinement.md §A claims. (b) CARRIER -- `Artist.__getstate__` at artist.py:186-191 is `d = self.__dict__.copy(); d['stale_callback'] = None; return d`, i.e. `state` really is a plain `dict`, so `dict.get`/membership/in-place assignment are the true primitives and mapping.md §2's Dict[int,int] carrier is faithful. (c) OPTIONALITY of the reference entry -- `_original_dpi` is set at backend_bases.py:1656 (`figure._original_dpi = figure.dpi`, in FigureCanvasBase.`__init__`), consumed at 2104 (`dpi = ratio * self.figure._original_dpi`) and read defensively at 2284 (`getattr(self.figure, '_original_dpi', self.figure.dpi)`). The `getattr` default at 2284 is the repo's own admission that the attribute can be ABSENT -- which is exactly why the two-armed `.get` semantics (not a one-armed conditional) is the right deep model, and why atk_9's unguarded read must be, and is, rejected. (d) mapping.md §4's claim that `__getstate__` never writes `_original_dpi` is true of the gold hunk (verified against the printed method body), so binding reference_present/reference_value as PRE-STATE parameters faithfully describes both the pre- and post-state of that key; the antecedents have real teeth -- atk_1/atk_2/atk_3 all die on them, and the grounding is what makes atk_7's parameter-only echo behaviourally correct rather than vacuous.
- axiom_check.py (the A-reference validator) RE-RUN: exit 0, 'G-AX OK: deep model (== real dict.get('`_original_dpi`', state['`_dpi`'])) sound on 8 boundary + 50000 fuzz states'. Inspected the source: it compares the deep model against the LITERAL gold line (written independently), asserts the selected value equals `before.get('_original_dpi', before['_dpi'])`, AND asserts the no-other-key-changed frame, on real float DPI including the F2P 42.0/294.0 pair. Not a tautology.
- patch.diff verified BYTE-IDENTICAL to instance.json['patch'] (Python string compare -> True), so the resolve oracle really is the gold patch.
- IDENTIFIER DRIFT (cosmetic, not a defect): refinement.md legs A2/A3 and §C still spell the reference-entry symbol `key_original_dpi` / `original_present` / `original_value`, whereas the frozen model.py now uses `key_reference` / `reference_present` / `reference_value` (a de-leaking rename). The correspondence claims are unaffected -- the renamed symbols occupy the same positions and mapping.md §1 binds `key_reference()` to `'_original_dpi'` -- but the two documents should be re-synced. Likewise meta.json's top-level `region_hashes` is stale relative to the live file, while the G-HYGIENE-recorded block (impl 6129b417..., pre-conditions f5d67b97..., post-conditions a0c3ef6a..., pure c8b12333..., spec_view 18c836a7...) reproduces `markers.region_hashes(model.py)` EXACTLY -- I recomputed it. Bookkeeping, not a spec defect.

ADVISORY (not a break, flagged for the record): atk_10 is the sharpest surviving consequence of the float->int value-token refinement (mapping.md §2). On the int carrier `state[k] != state[k]` is provably FALSE, so Nagini discharges the branch as dead; on the real float carrier that guard is TRUE for a NaN dpi, and the branch zeroes the serialized dpi. matplotlib does accept `set_dpi(float('nan'))`, so this is a real behavioural divergence the int abstraction cannot see -- it is nevertheless not a verify-not-correct witness at the level G-EQ decides, because the materialized patch RESOLVED (executed: F2P 1/1, no P2P failures): no graded test constructs a NaN dpi. The same caveat covers atk_15 (`// 1` truncates a fractional dpi, identity on the integral values the suite uses). The refinement's stated justification -- the modeled op is pure value SELECTION, never arithmetic -- is what makes the abstraction sound, and the frame + selection clauses do enforce it against any impl that does not manufacture a value; atk_8's rejection (`| 0`) shows the enforcement is partial rather than uniform, so the leg's soundness rests on the argument, not on the verifier alone.

**VERDICT:** SOUND (advisory). 15 same-spec attacks all run to a decided verdict; 9 distinct wrong-impl classes REJECTED by the frozen spec (including the prepatch bug, so the spec demonstrably senses the fix); all 6 verifying candidates had their faithful refined patch materialized at base_commit and EXECUTED through run_resolve, and all 6 RESOLVED. No verify-does-not-imply-correct witness exhibited. Nothing INCONCLUSIVE: every needed verification and every needed resolve run completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK LANE: faithfulness / spec-too-strong. Searched for an input where the modeled function `normalize_state_dpi` disagrees with the real callee, and for a correct implementation the spec wrongly rejects. Found neither. Verdict FAITHFUL.

WORKED IN /tmp ONLY. Created a worktree of matplotlib_matplotlib.git at base_commit 33a0599711d2 under /tmp, removed it at the end. Bundle unmodified (all bundle mtimes 21:53-22:32 predate this session, which began ~22:38; only *.py were written).

(1) SPEC REGION BYTE-IDENTITY. All 7 attack variants pass `adversary same-spec` ("SAME — attack shares the bundle's exact specification") AND an independent byte-comparison of everything outside the impl-start/impl-end markers vs gold model.py (True for every variant). Only the impl region differs.

(2) THE MODELED FUNCTION MATCHES THE REAL CALLEE. The gold patch is exactly one line: `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` (lib/matplotlib/figure.py, added between the renderer-clearing and version-stamping lines of Figure.`__getstate__` — confirmed against the dataset `patch` field and the base-commit source). The impl region is a deep, faithful expansion of dict.get-with-default: membership branch + both arms. I wrote my OWN differential (not the bundle's) running the impl region on the int-token domain against the gold line on the real float domain: 300,000 randomized inputs spanning negative values, 0, `2**53`, non-integer floats (uniform, 1/3, 0.1), and subnormals/extremes (5e-324, 1e308) plus 0-4 untouched extra entries. ZERO disagreements on the dpi entry, and the spec's three value/frame postconditions HELD on the real result on every input. This independently reproduces the bundle's own G-AX (50k states, exit 0) and G-CONF (100,020 inputs vs real patched Figure.`__getstate__`, 0 disagreements, both of which I re-ran green).

(3) NO SPEC-TOO-STRONG. Six behaviourally-correct, structurally-different same-spec implementations ALL VERIFY, so the spec admits the real behaviour rather than only the gold syntax:
  - A_else_pass: else branch is a literal `pass` (the real .get default arm is a no-op on the value) — VERIFIES. This is the sharpest probe: the gold `state[key_dpi()] = state[key_dpi()]` self-assign is not load-bearing.
  - C_temp_eager: truest transliteration of `.get(k, default)` — eager default into a temp, then select, then ONE assignment — VERIFIES.
  - F_gate_param / G_param_temp: gate on the grounded `reference_present`/`reference_value` parameters instead of the membership test — VERIFY.
  - E_double_write: writes the dpi entry twice (transient intermediate) before landing on the gold value — VERIFIES, so the frame clauses constrain only the EXIT state, not the write trace.
  - D2_loop: the selection wrapped in a bounded `while i < 1` loop with `Invariant(MustTerminate(2 - i))` — VERIFIES. So `Requires(MustTerminate(2))` at level 2 is NOT over-strong: it admits looping implementations, it only excludes divergence. (My first attempt D_bounded_loop failed, but on `state[key_dpi()]` well-definedness from MY incomplete invariants, not on any spec clause — strengthening the invariants made it verify. Not a spec defect.)

(4) PRECONDITION IS NOT TOO STRONG (domain faithfulness). `Requires(key_dpi() in state)` mirrors reality: `self._dpi` is unconditionally assigned in Figure.`__init__` (figure.py:2408), so the real state mapping always carries `_dpi`. I confirmed empirically that a fresh `Figure` reaches `__getstate__` with `_dpi` present. The reference-entry parameters are honestly grounded to the ENTRY record (`reference_present == (key_reference() in state)` and the value equality), not an opaque oracle — so the discriminating clause has teeth rather than being echoable. mapping.md §4's claim that `__getstate__` never writes `_original_dpi` is TRUE at base_commit: the only `state[...]` writes in the function are `_cachedRenderer`, `__mpl_version__`, and `_restore_to_pylab` (verified by reading the function body), so the pre-state parameters correctly describe the post-state of that key too.

(5) SPEC HAS TEETH (control). model_prepatch.py (impl = `pass`, the literal pre-patch behaviour) is same-spec and FAILS on exactly the discriminating clause: "Postcondition ... Implies(reference_present, (state[key_dpi()] == reference_value)) might not hold." So the spec is not vacuous, and the clause it rejects on is precisely the one the F2P test `test_unpickle_with_device_pixel_ratio` observes (fig2.dpi == 42, not `42*7` == 294).

ONE EDGE EXAMINED AND DISMISSED — NaN. The int-token value carrier cannot express NaN, and with a NaN dpi the real gold line makes the spec's own equality clauses false (`out["_dpi"] == ref_value` is False for NaN by IEEE reflexivity failure). I checked reachability: `Figure(dpi=nan)` IS constructible in the real repo and carries `_dpi = nan` through `__getstate__`. However this is NOT a faithfulness break in the audited direction: (a) it is a case where the SPEC IS STRICTER than reality (the spec's equality demands more than NaN can satisfy), so it cannot admit a non-resolving implementation — it could only reject a correct one, and no NaN input is reachable in the F2P/P2P test set (dpi is always a finite float; the scaling path `ratio * _original_dpi` produced 294 as expected); (b) the modeled behaviour is pure value SELECTION with no arithmetic, so int-token vs float is sound per mapping.md §2 and is exactly what my 300k-input differential (incl. non-integer floats) confirmed. This does not yield a diverging input where the model disagrees with the real callee on a reachable state.

**CONCLUSION:** the spec is a faithful, appropriately-tight model of the gold change. It rejects the pre-patch behaviour and every wrong-selection/frame-violating rival, while admitting six distinct correct implementations including the literal `.get`-with-default transliteration and a bounded-loop form. No diverging input found; no spec-too-strong defect. FAITHFUL.

**ATTACK LANE:** faithfulness / spec-too-strong. Searched for an input where the modeled function `normalize_state_dpi` disagrees with the real callee, and for a correct implementation the spec wrongly rejects. Found neither. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: leakage / gold-reconstruction, judged against solver-visible problem_statement ONLY (hints_text excluded).

**SPEC IDENTITY CONFIRMED FIRST:** `adversary same-spec nagini matplotlib__matplotlib-23476 atk.py` => exit 0 ('SAME — attack shares the bundle's exact specification'), so the spec region I judged is the shipped one. spec_signature(model.py) == spec_signature(model_prepatch.py) = 06f9457e9817489b (twin artifacts share the spec, as designed). Shipped model.py verifies under the pinned verifier: 'Verification successful' (17.86s).

IMPORTANT — THE RECORDED meta.json G-PANEL-3 IS STALE, NOT A CURRENT DEFECT. meta.json gates.G-PANEL-3.status = 'fail' with agent_verdict LEAKAGE. That finding was against an EARLIER bundle and its two cited leak channels are both GONE from the current file:
  (1) it quoted spec-view identifier `key_original_dpi` (a verbatim echo of repo attribute `_original_dpi`) — the current file uses abstract `key_reference` / `reference_present` / `reference_value`; 'original' does not occur anywhere in the current spec view (checked case-insensitively).
  (2) it quoted a docstring phrase 'Producing a figure's serialisable state' localizing Figure.`__getstate__` — absent from the current docstring ('getstate'/'serialisable' both absent from the view).
The prior attacker also itself recorded that the de-leak it demanded (abstract reference/primary vocabulary) still verifies — that de-leak has since been applied. Per the retained-attack-label rule I re-judged the current bundle independently rather than re-stamping the old verdict.

MECHANICAL SCREEN (G-LEAK, leakage.screen): passed=True, hard_failures=[], warnings=[]. Confirmed the view is impl-free and spec_view is idempotent.
  - L1 gold lines: neither changed line reproduced. Gold hunk is the comment '# discard any changes to the dpi due to pixel ratio changes' and `state["_dpi"] = state.get('_original_dpi', state['_dpi'])`. Neither appears normalized in the view; '.get(' , 'pixel', 'ratio' (as a word), 'device', 'scal' all absent. Both impl arms and the guard confirmed NOT exposed (impl region collapses to the elision placeholder).
  - L1 diff markers: none.
  - L2 paths: 'lib/matplotlib/figure.py' and the dotted module path absent.
  - L2/L5 patched symbols: the only screened def/class symbol is `getstate` (from the hunk section header `def __getstate__`); it is NOT in the view and NOT in the problem_statement. So the spec view does NOT localize the gold method. Note the PS traceback names only `__setstate__` — the WRONG method — and the view does not correct that.
  - L3 narration: no hit from the narration vocabulary.

SUBSTRING FALSE POSITIVES I RAN DOWN (so this is not a rubber-stamp): a naive substring scan flagged 'ratio' and 'mac' in the view. Both are innocent: 'ratio' is inside 'ope-ratio-n' ('The operation is a bounded, loop-free selection'), 'mac' is inside 'machine-parsed'. Neither is the pixel-ratio diagnosis. 'doubling' (L8, 'doubling until it grows past what can be represented') is a morphological variant of PS's own title 'DPI of a figure is doubled after unpickling' plus PS's documented OverflowError — the public SYMPTOM, not the hints-only mechanism. 'dpi' is public via the PS title.

GOLD-RECONSTRUCTION ATTEMPT — the discriminating repo facts are NOT handed over. Verified in the base_commit worktree (@ 33a0599711, clean): `grep -n _original_dpi lib/matplotlib/figure.py` => 0 hits; the string lives only in lib/matplotlib/backend_bases.py:1656,2104,2284. Under the CURRENT view a solver is told, abstractly, that the round-trip mapping may carry 'a second entry recording a reference dpi' and that the reference wins when present — but is NOT given the key string `_original_dpi`, the file, the method `__getstate__`, the insertion point, or the pixel-ratio causal story. The solver must still discover from the repo that such an attribute exists, that it is set by the canvas in a different file, and that `__getstate__` (not the `__setstate__` the traceback points at) is the site. That residual gap is exactly the work modes 1/2 intend the solver to do.

**WHY THE REMAINING ABSTRACT CLAUSE IS NOT A LEAK:** the clause 'whenever the reference entry is present, the dpi entry is recorded as that reference value; otherwise the dpi entry keeps the value it already held' IS the behavior under specification. SPEC_GUIDE 6 requires stating the abstract desired behavior and forbids naming the patched file/function/line, echoing a patched repo symbol, quoting diff lines, or narrating the bug->fix MECHANISM. This view does the former and none of the latter — the causal diagnosis (dpi scaled by the device pixel ratio, then re-scaled on reload) is the hints_text-only content and it is absent. A spec cannot withhold the behavior it specifies without ceasing to be a spec, and no relaxed-leakage exception is needed or claimed (no RELAXED_LEAKAGE.md present, G-LEAK status 'pass' not 'relaxed' — correct).

SCOPE NOTE (not charged as a finding): in spec modes the consumer additionally receives meta.json modeled_functions, whose repo_symbol ('matplotlib.figure.Figure.`__getstate__`') and repo_location ('lib/matplotlib/figure.py:3015') DO localize the edit. That is the deliberate cross-mode edit-localization aid (dataset.py MODES_WITH_LOCALIZATION / `_spec_block`), identical information mode 0 gets, and it is not part of the spec view this gate screens. Flagging for transparency only. The bundle's audit docs (mapping.md/refinement.md), which do name the keys and site, are never shipped to consumers — confirmed absent from prompts.py/dataset.py/adapter.py assembly.

**CONCLUSION:** NO-LEAKAGE on the current spec view. The recorded meta.json G-PANEL-3 'fail' is stale and should be refreshed to pass for this bundle revision.

**ROLE:** leakage / gold-reconstruction, judged against solver-visible problem_statement ONLY (hints_text excluded).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
