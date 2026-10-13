# P2 adversarial audit — matplotlib__matplotlib-23314

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_swapbranch.py`, `atk2_double.py`, `atk3_partial.py`, `atk4_noguard.py`, `atk7_offbyone.py`, `atk8_subtract.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_loop.py`, `atk6_elseform.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_swapbranch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -78,7 +76,7 @@
     Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
     # post-conditions-end
     # impl-start
-    if not self.visible:
+    if self.visible:
         return
     sink.work = sink.work + self.content
     return
```

Attack 2 — `atk2_double.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -80,6 +78,6 @@
     # impl-start
     if not self.visible:
         return
-    sink.work = sink.work + self.content
+    sink.work = sink.work + self.content + self.content
     return
     # impl-end
```

Attack 3 — `atk3_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -80,6 +78,7 @@
     # impl-start
     if not self.visible:
         return
-    sink.work = sink.work + self.content
+    if self.content == 0:
+        sink.work = sink.work + self.content
     return
     # impl-end
```

Attack 4 — `atk4_noguard.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -78,8 +76,6 @@
     Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
     # post-conditions-end
     # impl-start
-    if not self.visible:
-        return
     sink.work = sink.work + self.content
     return
     # impl-end
```

Attack 5 — `atk5_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -80,6 +78,13 @@
     # impl-start
     if not self.visible:
         return
-    sink.work = sink.work + self.content
+    i = 0
+    while i < self.content:
+        Invariant(Acc(sink.work))
+        Invariant(Acc(self.content, 1 / 4))
+        Invariant(0 <= i and i <= self.content)
+        Invariant(sink.work == Old(sink.work) + i)
+        sink.work = sink.work + 1
+        i = i + 1
     return
     # impl-end
```

Attack 6 — `atk6_elseform.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -78,8 +76,9 @@
     Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
     # post-conditions-end
     # impl-start
-    if not self.visible:
-        return
-    sink.work = sink.work + self.content
+    if self.visible == False:
+        pass
+    else:
+        sink.work = sink.work + self.content
     return
     # impl-end
```

Attack 7 — `atk7_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -80,6 +78,6 @@
     # impl-start
     if not self.visible:
         return
-    sink.work = sink.work + self.content
+    sink.work = sink.work + self.content + 1
     return
     # impl-end
```

Attack 8 — `atk8_subtract.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Sink:
@@ -64,7 +63,6 @@
     Requires(Acc(self.content, 1 / 2))
     Requires(self.content >= 0)
     Requires(Acc(sink.work))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # read-only container fields are returned at the same fractional permission
@@ -80,6 +78,6 @@
     # impl-start
     if not self.visible:
         return
-    sink.work = sink.work + self.content
+    sink.work = sink.work - self.content
     return
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23314.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A renderable container exposes a boolean visibility flag and a body of
  drawable content. Its render entry point, given an output sink that
  accumulates the work it is asked to perform, must honour the visibility
  flag the same way every other renderable container does:

    (1) when the container is flagged not-visible, the render entry point
        performs NO drawing work whatsoever — the sink is left exactly as it
        was on entry (no content is emitted to it); and

    (2) when the container is flagged visible, the render entry point performs
        its full body of work — the sink receives the container's entire
        drawable content.

So the amount of work delivered to the sink is the container's content when it
is visible and zero when it is not; visibility gates the whole render pass.

The output sink is modelled as a minimal mutable object carrying only the
touched field — a running tally of work it has received (``work``). The
container is modelled as a minimal object carrying only the two fields the
behaviour reads — its visibility flag (``visible``) and the size of its
drawable body (``content``, a non-negative quantity), both read-only here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Sink:
    def __init__(self) -> None:
        Ensures(Acc(self.work) and self.work == 0)  # type: ignore
        self.work = 0  # type: int


class Container:
    def __init__(self, visible: bool, content: int) -> None:
        Requires(content >= 0)
        Ensures(Acc(self.visible, 1 / 2) and self.visible == visible)  # type: ignore
        Ensures(Acc(self.content, 1 / 2) and self.content == content)  # type: ignore
        Ensures(self.content >= 0)  # type: ignore
        self.visible = visible    # type: bool
        self.content = content    # type: int


# axioms-start
# (no unchanged callee needs axiomatizing: the rendering body is abstracted as
#  the single quantity `self.content` and the whole pass is modeled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def render(self: Container, sink: Sink) -> None:
    # pre-conditions-start
    Requires(Acc(self.visible, 1 / 2))
    Requires(Acc(self.content, 1 / 2))
    Requires(self.content >= 0)
    Requires(Acc(sink.work))
    # pre-conditions-end
    # post-conditions-start
    # read-only container fields are returned at the same fractional permission
    # and are unchanged by the render pass.
    Ensures(Acc(self.visible, 1 / 2) and self.visible == Old(self.visible))
    Ensures(Acc(self.content, 1 / 2) and self.content == Old(self.content))
    Ensures(Acc(sink.work))
    # (1) not-visible => no work is delivered to the sink (left as on entry).
    Ensures(Implies(not self.visible, sink.work == Old(sink.work)))
    # (2) visible => the sink receives the container's entire drawable content.
    Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
    # post-conditions-end
    # impl-start
    if not self.visible:
        return
    sink.work = sink.work + self.content
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The postcondition fully and deterministically pins sink.work in BOTH branches: (1) not visible => sink.work==Old(sink.work); (2) visible => sink.work==Old(sink.work)+self.content, with content>=0 a free non-negative variable. Any impl that verifies therefore computes sink.work identically as a function of (visible, content) == the gold behavior; no behavioral wiggle room exists.

PROTOCOL RUN (project root; python python; verifier scripts/nagini_verify.sh; SBU_BENCHMARK_DIR=benchmark-verified). All edits touched ONLY the impl region; same-spec confirmed (atk1 same-spec -> SAME, exit 0).
- atk1 swap-branch (visible returns early / invisible adds): exit 2 (does not verify) REJECTED.
- atk2 double (sink.work += content+content): exit 2 REJECTED.
- atk3 partial-domain (only add when content==0): exit 2 REJECTED.
- atk4 no-guard echo (== prepatch bug, always add): exit 2 REJECTED (does not verify).
- atk5 loop-accumulation (while i<content: work+=1, with invariants): exit 0 CANDIDATE (verifies 12.9s).
- atk6 else-form (if visible==False: pass else work+=content): exit 0 CANDIDATE (verifies 10.7s).
- atk7 off-by-one (work += content+1): exit 2 REJECTED.
- atk8 subtract (work -= content): exit 2 REJECTED.
Positive control (unedited model.py) verifies: nagini_verify exit 0. Prepatch reproduced: atk_prepatch.py (guard dropped, body only) FAILS to verify (nagini_verify exit 1) => spec senses the change (G-DIFF).

CANDIDATE RESOLVE (protocol step 2, actually executed, not speculated): atk5 and atk6 are pure control-flow rewrites of the gold behavior (loop that adds `content` ones; else-branch delivering `content`). Both deliver exactly Old+content when visible and leave work unchanged when not, i.e. behaviorally IDENTICAL to gold. Their faithful refined patch is the gold visibility guard `if not self.get_visible(): return`. Materialized faithful patch run through harness.run_resolve('matplotlib__matplotlib-23314', patch, timeout=3600) => RESOLVED: True (NOTE: resolved). So neither verifying candidate's faithful patch fails to resolve => verify does NOT imply incorrect here. No BROKEN condition met.

REFINEMENT LEG AUDIT (refinement.md): step1/2 R (Axes3D<->Container, renderer<->Sink); step3 I+A-reference (not self.visible <-> not self.get_visible(); accessor faithfulness); step4 I (guard/early-return, the whole gold hunk); step5 R/A-reference (unchanged render body abstracted as opaque content>=0). NO kind-3 (unexpressible-changed-op) leg; NO consumed @ContractOnly axiom. The two A-references are genuinely EXECUTED against real matplotlib in axiom_check.py: it drives the real Axes3D.draw with a recording RendererBase and asserts invisible=>0 draw primitives (clause 1), visible=>>0 (clause 2), and set_visible(b)=>get_visible()==b (accessor faithfulness). Correspondence to the real callees holds.

**CONCLUSION:** >=5 attacks run (8 wrong impls + prepatch + positive control); the only verifying candidates are gold-equivalent and their materialized faithful patches RESOLVE. Spec admits no incorrect verifying impl. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_swapbranch.py`, `atk2_double.py`, `atk3_partial.py`, `atk4_noguard.py`, `atk7_offbyone.py`, `atk8_subtract.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_loop.py`, `atk6_elseform.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_swapbranch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_double.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_partial.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_noguard.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6_elseform.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7_offbyone.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_subtract.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23314.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A renderable container exposes a boolean visibility flag and a body of
  drawable content. Its render entry point, given an output sink that
  accumulates the work it is asked to perform, must honour the visibility
  flag the same way every other renderable container does:

    (1) when the container is flagged not-visible, the render entry point
        performs NO drawing work whatsoever — the sink is left exactly as it
        was on entry (no content is emitted to it); and

    (2) when the container is flagged visible, the render entry point performs
        its full body of work — the sink receives the container's entire
        drawable content.

So the amount of work delivered to the sink is the container's content when it
is visible and zero when it is not; visibility gates the whole render pass.

The output sink is modelled as a minimal mutable object carrying only the
touched field — a running tally of work it has received (``work``). The
container is modelled as a minimal object carrying only the two fields the
behaviour reads — its visibility flag (``visible``) and the size of its
drawable body (``content``, a non-negative quantity), both read-only here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Sink:
    def __init__(self) -> None:
        Ensures(Acc(self.work) and self.work == 0)  # type: ignore
        self.work = 0  # type: int


class Container:
    def __init__(self, visible: bool, content: int) -> None:
        Requires(content >= 0)
        Ensures(Acc(self.visible, 1 / 2) and self.visible == visible)  # type: ignore
        Ensures(Acc(self.content, 1 / 2) and self.content == content)  # type: ignore
        Ensures(self.content >= 0)  # type: ignore
        self.visible = visible    # type: bool
        self.content = content    # type: int


# axioms-start
# (no unchanged callee needs axiomatizing: the rendering body is abstracted as
#  the single quantity `self.content` and the whole pass is modeled deeply.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def render(self: Container, sink: Sink) -> None:
    # pre-conditions-start
    Requires(Acc(self.visible, 1 / 2))
    Requires(Acc(self.content, 1 / 2))
    Requires(self.content >= 0)
    Requires(Acc(sink.work))
    # pre-conditions-end
    # post-conditions-start
    # read-only container fields are returned at the same fractional permission
    # and are unchanged by the render pass.
    Ensures(Acc(self.visible, 1 / 2) and self.visible == Old(self.visible))
    Ensures(Acc(self.content, 1 / 2) and self.content == Old(self.content))
    Ensures(Acc(sink.work))
    # (1) not-visible => no work is delivered to the sink (left as on entry).
    Ensures(Implies(not self.visible, sink.work == Old(sink.work)))
    # (2) visible => the sink receives the container's entire drawable content.
    Ensures(Implies(self.visible, sink.work == Old(sink.work) + self.content))
    # post-conditions-end
    # impl-start
    if not self.visible:
        return
    sink.work = sink.work + self.content
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The postcondition fully and deterministically pins sink.work in BOTH branches: (1) not visible => sink.work==Old(sink.work); (2) visible => sink.work==Old(sink.work)+self.content, with content>=0 a free non-negative variable. Any impl that verifies therefore computes sink.work identically as a function of (visible, content) == the gold behavior; no behavioral wiggle room exists.

PROTOCOL RUN (project root; python python; verifier scripts/nagini_verify.sh; SBU_BENCHMARK_DIR=benchmark-verified). All edits touched ONLY the impl region; same-spec confirmed (atk1 same-spec -> SAME, exit 0).
- atk1 swap-branch (visible returns early / invisible adds): exit 2 (does not verify) REJECTED.
- atk2 double (sink.work += content+content): exit 2 REJECTED.
- atk3 partial-domain (only add when content==0): exit 2 REJECTED.
- atk4 no-guard echo (== prepatch bug, always add): exit 2 REJECTED (does not verify).
- atk5 loop-accumulation (while i<content: work+=1, with invariants): exit 0 CANDIDATE (verifies 12.9s).
- atk6 else-form (if visible==False: pass else work+=content): exit 0 CANDIDATE (verifies 10.7s).
- atk7 off-by-one (work += content+1): exit 2 REJECTED.
- atk8 subtract (work -= content): exit 2 REJECTED.
Positive control (unedited model.py) verifies: nagini_verify exit 0. Prepatch reproduced: atk_prepatch.py (guard dropped, body only) FAILS to verify (nagini_verify exit 1) => spec senses the change (G-DIFF).

CANDIDATE RESOLVE (protocol step 2, actually executed, not speculated): atk5 and atk6 are pure control-flow rewrites of the gold behavior (loop that adds `content` ones; else-branch delivering `content`). Both deliver exactly Old+content when visible and leave work unchanged when not, i.e. behaviorally IDENTICAL to gold. Their faithful refined patch is the gold visibility guard `if not self.get_visible(): return`. Materialized faithful patch run through harness.run_resolve('matplotlib__matplotlib-23314', patch, timeout=3600) => RESOLVED: True (NOTE: resolved). So neither verifying candidate's faithful patch fails to resolve => verify does NOT imply incorrect here. No BROKEN condition met.

REFINEMENT LEG AUDIT (refinement.md): step1/2 R (Axes3D<->Container, renderer<->Sink); step3 I+A-reference (not self.visible <-> not self.get_visible(); accessor faithfulness); step4 I (guard/early-return, the whole gold hunk); step5 R/A-reference (unchanged render body abstracted as opaque content>=0). NO kind-3 (unexpressible-changed-op) leg; NO consumed @ContractOnly axiom. The two A-references are genuinely EXECUTED against real matplotlib in axiom_check.py: it drives the real Axes3D.draw with a recording RendererBase and asserts invisible=>0 draw primitives (clause 1), visible=>>0 (clause 2), and set_visible(b)=>get_visible()==b (accessor faithfulness). Correspondence to the real callees holds.

**CONCLUSION:** >=5 attacks run (8 wrong impls + prepatch + positive control); the only verifying candidates are gold-equivalent and their materialized faithful patches RESOLVE. Spec admits no incorrect verifying impl. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for matplotlib__matplotlib-23314 nagini bundle. The real gold patch for this instance (verified against data/swe_bench_verified/test.jsonl) is exactly the visibility guard 'if not self.get_visible(): return' at the top of Axes3D.draw — NOT the axis-limit-swap patch found in the stale gold.diff worktree artifact (that file is mismatched to another instance; I analyzed against the true dataset patch).

The model abstracts Axes3D↔Container (visible bool + opaque non-negative content), renderer↔Sink (cumulative primitive tally 'work'). Spec clauses: (1) not-visible ⇒ work unchanged; (2) visible ⇒ work == Old(work)+content (exact additivity, stable across arbitrary starting tally).

Evidence the modeled function agrees with the real callee on every input:
- same-spec: SAME (exit 0) — spec markers confirmed byte-identical.
- nagini_verify.sh: Verification successful (14.11s).
- axiom_check.py (G-AX): exit 0 on real matplotlib 3.6.3 — invisible Axes3D emits 0 draw primitives, visible emits 41; get_visible() faithfully returns the stored flag.
- conformance_check.py (G-CONF): exit 0, 100126 inputs (126 boundary + 100000 fuzz, seed 23314) over 9 real axes configurations (content values 1,25,27,28,29,30), zero disagreements. Additivity verified across negative/large-magnitude (±1e12/1e15) starting tallies and randomized interleavings; per-pass primitive count asserted reproducible so 'content' is well-defined.

**The abstraction is sound:** the render body is deterministic (reproducible primitive count), the model never over-claims a specific numeric content, and visibility gating matches the real early-return exactly. No diverging input exists. Spec is a faithful (not too-strong) model of the gold-patched Axes3D.draw.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen) passes: no diff markers, no reproduced gold-patch line, no patched file path ('lib/mpl_toolkits/mplot3d/axes3d.py'), and the sole distinctive changed symbol 'apply_aspect' (from the hunk header) does not appear in the spec view. Semantic review confirms NO leakage beyond the public problem_statement. The problem_statement already states the desired behavior fully: 'set_visible() not working for 3d projection' with 'Expected outcome: the subplot is not visible if the value is set to False.' The spec view describes only an abstract Container/Sink/render carrier with a 'visible' flag gating a 'content'/'work' render pass — clause (1) not-visible => sink unchanged, clause (2) visible => sink receives full content. This is exactly the publicly-stated expected outcome, expressed in generic abstract identifiers. The gold-edit specifics — that the guard belongs in Axes3D.draw in axes3d.py, reading get_visible() — appear ONLY in mapping.md/refinement.md (auditor-facing derivation artifacts), NOT in the solver-visible spec view (model.py docstring + Requires/Ensures with impl elided). The impl region is elided in the spec view, so the concrete guard code is not shown. No comment narrates the bug/fix. Verdict: the spec view does not reconstruct the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
