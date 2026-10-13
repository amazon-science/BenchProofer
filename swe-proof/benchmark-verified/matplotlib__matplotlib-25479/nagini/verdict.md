# P2 adversarial audit — matplotlib__matplotlib-25479

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 13 same-spec attacks; 3 came back CANDIDATE (share spec AND verify); ALL 3 had their faithful refined patch materialized and RUN through the official harness, and ALL 3 RESOLVED (2/2 F2P, 263/263 P2P each). No verify=>correct witness found.

CRITICAL FINDING — I REFUTE THE RECORDED G-EQ/G-PANEL-1 'fail'. meta.json records G-EQ=fail on the CURRENT model.py hash (5cd95084...) with note 'BROKEN (verify=>correct): atk_5.py verifies but its patch does not resolve — FAIL_TO_PASS fails 2/2 ...; PASS_TO_PASS fails 1/263: test_register_cmap'. That prior atk_5 was the aliased-receiver label clobber (`if self is other: self.name = 0`), which I re-encoded as MY atk_7. Its faithful patch RESOLVES (2/2 F2P, 263/263 P2P, resolve_7.json). The recorded 'fail' is a PATCH-MATERIALIZATION ARTIFACT, not a spec defect, and I proved the mechanism: the recorded failure signature is reproduced EXACTLY by applying only the cm.py hunk while leaving colors.py at PREPATCH. Run in-container at base_commit (cm relabel applied, colors.py untouched, test_patch applied):
  python -m pytest test_colormap_equals test_set_cmap_mismatched_name test_register_cmap
  -> 3 failed: test_colormap_equals, test_set_cmap_mismatched_name (F2P 2/2) AND test_register_cmap (the 1/263 P2P)
That is precisely the recorded signature. A well-formed patch carrying BOTH gold hunks cannot produce it, so the prior run's colors.py hunk never applied (its context line `if (not isinstance(other, Colormap) or self.name != other.name or` had the extra step spliced ahead of it, which breaks the hunk context). Note also the prior pass's OWN notes say all 5 candidates resolved and its agent verdict was SOUND — the recorded machine 'fail' contradicts its own evidence. I built every patch via `git diff` in a worktree at base_commit so the text is well-formed by construction, and asserted read-back that BOTH gold hunks are present in the patched tree before diffing.

WHY THE ONE GENUINE FREEDOM IS HARMLESS (measured, not assumed): `colormaps_equal` requires Acc(self.X,1/2) and Acc(other.X,1/2) SEPARATELY, so on an ALIASED call (self is other) the halves SUM TO WRITE permission, and no Ensures value-constrains self.name/colorbar_extend/lut. A verifying impl may therefore mutate the receiver on the self-comparison path (atk_7, atk_8). But the postcondition `Result() == (colorbar_extend-equal AND seq_eq(lut,lut))` TOTALLY pins the returned value as a function of observable state, so aliased-receiver mutation is the ONLY residual observational freedom. I measured its reachability: I instrumented the REAL Colormap.__eq__ with an aliasing spy and ran the ENTIRE 265-test graded suite (F2P+P2P) under the gold patch -> 265 passed, 10 total __eq__ calls, ZERO aliased (self is other) calls. The graded suite always compares two DISTINCT objects (cm_copy vs cmap, cmap_returned vs cmap), and ColormapRegistry.__getitem__ returns a .copy(), so no registry read can alias. The freedom is unreachable-in-practice latent freedom, refuted 3/3 by the harness — reporting it as a break would invent spec weakness (retained-attack-label failure mode).
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,6 +161,8 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
+    if self.name != other.name:
+        return False
     if self.colorbar_extend != other.colorbar_extend:
         return False
     if len(self.lut) != len(other.lut):
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -260,9 +260,5 @@
     if name in reg:
         raise LabelAlreadyBound()
     snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
-    # The published snapshot is relabelled to the chosen registration label, so
-    # that a later lookup by that label yields a mapping whose own label matches
-    # the label it was looked up under.
-    snapshot.name = name
     reg[name] = snapshot
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,6 +161,8 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
+    if self is other:
+        return True
     if self.colorbar_extend != other.colorbar_extend:
         return False
     if len(self.lut) != len(other.lut):
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,7 +168,7 @@
         Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))
         return False
     i = 0
-    while i < len(self.lut):
+    while i < len(self.lut) - 1:
         # invariants-start
         Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))
         Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,7 +185,7 @@
         Assert(ToSeq(other.lut).drop(i)[0] == other.lut[i])
         Assert(ToSeq(self.lut).drop(i).drop(1) == ToSeq(self.lut).drop(i + 1))
         Assert(ToSeq(other.lut).drop(i).drop(1) == ToSeq(other.lut).drop(i + 1))
-        if not entry_eq(self.lut[i], other.lut[i]):
+        if self.lut[i] != other.lut[i]:
             return False
         i = i + 1
     Assert(len(ToSeq(self.lut).drop(i)) == 0)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,7 +161,7 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
-    if self.colorbar_extend != other.colorbar_extend:
+    if (self.colorbar_extend > 0) != (other.colorbar_extend > 0):
         return False
     if len(self.lut) != len(other.lut):
         Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,6 +161,8 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
+    if self is other:
+        self.name = 0
     if self.colorbar_extend != other.colorbar_extend:
         return False
     if len(self.lut) != len(other.lut):
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,6 +161,9 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
+    if self is other:
+        self.lut = []
+        return True
     if self.colorbar_extend != other.colorbar_extend:
         return False
     if len(self.lut) != len(other.lut):
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -265,4 +265,5 @@
     # the label it was looked up under.
     snapshot.name = name
     reg[name] = snapshot
+    reg[name + 1] = snapshot
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -256,13 +256,13 @@
                                               reg[k] is Old(reg[k])))
             and name in reg and reg[name] is Old(reg[name]))
     # impl-start
-    # The already-bound label is refused before anything is built or stored.
-    if name in reg:
-        raise LabelAlreadyBound()
+    present = name in reg
     snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
     # The published snapshot is relabelled to the chosen registration label, so
     # that a later lookup by that label yields a mapping whose own label matches
     # the label it was looked up under.
     snapshot.name = name
     reg[name] = snapshot
+    if present:
+        raise LabelAlreadyBound()
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -256,9 +256,6 @@
                                               reg[k] is Old(reg[k])))
             and name in reg and reg[name] is Old(reg[name]))
     # impl-start
-    # The already-bound label is refused before anything is built or stored.
-    if name in reg:
-        raise LabelAlreadyBound()
     snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
     # The published snapshot is relabelled to the chosen registration label, so
     # that a later lookup by that label yields a mapping whose own label matches
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,10 +259,6 @@
     # The already-bound label is refused before anything is built or stored.
     if name in reg:
         raise LabelAlreadyBound()
-    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)
-    # The published snapshot is relabelled to the chosen registration label, so
-    # that a later lookup by that label yields a mapping whose own label matches
-    # the label it was looked up under.
-    snapshot.name = name
+    snapshot = Cmap(name, cmap.colorbar_extend, cmap.lut)
     reg[name] = snapshot
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,6 +161,8 @@
                          and seq_eq(ToSeq(self.lut), ToSeq(other.lut))))
     # post-conditions-end
     # impl-start
+    if len(self.lut) == 0 and len(other.lut) == 0:
+        return True
     if self.colorbar_extend != other.colorbar_extend:
         return False
     if len(self.lut) != len(other.lut):
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC IDENTITY FIRST: sha256(model.py) = 5cd95084734c7e469dd6961ddf81434dfa0cdc6f2923c53f4f727a6f93dcdeaf, matching meta.json G-VERIFY/G-AX/G-CONF/G-GOLD/G-DIFF/G-MUT/G-PBT sources. All 13 attacks confirmed byte-identical spec via `adversary same-spec` -> 'SAME', exit 0. Bundle read-only throughout; hash re-checked unchanged at the end. My git worktree was created under my own scratch dir only and removed afterwards.

POSITIVE CONTROL: pos_control.py (byte-identical model.py) -> `bash scripts/nagini_verify.sh` -> 'Verification successful', 15.41s, exit 0 (non-vacuity).

### PREPATCH REPRODUCED (both sites, both REJECTED):
  atk_1 — eq site, prepatch `if self.name != other.name: return False` -> exit 2.
  atk_2 — register site, drops `snapshot.name = name` -> exit 2.

Command for every attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25479 atk_N.py` (run 3-at-a-time as background jobs; each spawns JVM+Z3). Outputs at wk_N.out.

REJECTED (10/13, exit 2 — spec is strong here), with the clause that kills each:
  atk_1 prepatch eq (label re-added) | atk_2 prepatch register (no relabel)
  atk_3 PARTIAL-DOMAIN `if self is other: return True` -> 'Postcondition of colormaps_equal might not hold' — killed by A5 non-reflexivity (a NaN-carrying table must be unequal to ITSELF).
  atk_4 BOUNDARY: scan `while i < len(self.lut) - 1` (last entry never compared).
  atk_5 UNGROUNDED-ORACLE ECHO: raw token `!=` instead of the frozen `entry_eq` (idealised REFLEXIVE equality) -> 'Loop invariant might not be preserved'.
  atk_6 FLAG-DOMAIN COLLAPSE: six-valued flag through a 2-valued carrier `(x>0) != (y>0)` — confirms A2 injectivity is load-bearing IN THE CONTRACT, not just prose.
  atk_9 FRAME: side-write `reg[name+1] = snapshot` — killed by B6's Forall clauses.
  atk_10 CONTROL-FLOW EFFECT: store-then-raise -> 'Postcondition of register_named might not hold. Assertion (reg[name] is Old(reg[name])) might not hold' — the Exsures frame clause.
  atk_11 SILENT OVERWRITE (collision refusal dropped) — killed by `Ensures(not Old(name in reg))`.
  atk_13 PARTIAL-DOMAIN: flag ignored when both tables empty.

CANDIDATES (3/13, exit 0) — ALL RESOLVED, so none breaks the spec. Patches built via `git diff` at base_commit 7fdf7722, `git apply --check` CLEAN, read-back asserted BOTH gold hunks present; run via swebench_unified.harness.run_resolve (run_id geq7cf-<tag>), records at resolve_<tag>.json:
  atk_7  aliased receiver: clobber the label      -> resolved=True completed=True F2P 2/2 P2P 263/263
  atk_8  aliased receiver: destroy lut, return True -> resolved=True completed=True F2P 2/2 P2P 263/263
  atk_12 CORRECT RESHAPE control (copy built already-relabelled) -> resolved=True completed=True F2P 2/2 P2P 263/263
  GOLD CONTROL patch_gold.diff (my materializer's output for the unmodified impl) -> resolved=True F2P 2/2 P2P 263/263, validating the materializer itself.

A-LEG AUDIT (my focus; R/I legs left to G-CONF). There is NO consumed axiom in this bundle — `axioms-start/end` is a comment block only (confirmed: axioms region is prose), so there is no axiom-soundness surface; the only kind-A entries are three A-REFERENCES. I re-measured each against the REAL post-patch callee in-container (aleg.py, after asserting the loaded colors.py has the name disjunct ABSENT): A2 flag injectivity over (False,True,'neither','min','max','both'): all 15 distinct pairs SEPARATED by the real __eq__ (not-separated list EMPTY) -> the carrier may merge nothing. Load-bearing, confirmed by atk_6's rejection.

A4/A5 (seq_eq/entry_eq <-> np.array_equal's elementwise ==, equal_nan default False): NaN-carrying lut -> `c == c` is False AND `c == c.copy()` is False, exactly the deliberate NON-REFLEXIVITY entry_eq encodes; determinate table -> `d == d` True. Confirmed load-bearing by atk_3's rejection. A3 (label irrelevant — the patch delta): relabelled-but-content-equal -> real __eq__ True, matching a postcondition naming no label term. B2/B3 (copy() <-> Cmap constructor; relabel): register(name='wrong-cmap') -> stored.name=='wrong-cmap', `is not` supplied, `==` supplied, supplied.name still 'test-cmap'. Matches every Ensures.

All A-leg correspondences HOLD. refinement.md §C's 'no kind-3' claim checks out: every step is R / A-reference / I, and the two genuinely-changed ops are modelled DEEPLY (postcondition predicate + seq_eq fold over entry_eq; spelled-out relabel+store) rather than axiomatized. No A-consumed legs exist, so nothing is assumed rather than established.

DOCUMENTATION GAP (advisory, NOT a G-EQ break — the spec is sound and all 3 candidate patches resolve): `grep -nE 'LabelAlreadyBound|Exsures|refus|collision' refinement.md mapping.md` returns NOTHING (exit 1). The impl's collision-refusal step (`if name in reg: raise LabelAlreadyBound()`) and its Exsures leg have NO row in the refinement table, yet that leg is real and load-bearing — it is what kills atk_10 and atk_11. Its correspondence DOES hold: I measured a second `register(name='wrong-cmap')` -> `ValueError: A colormap named "wrong-cmap" is already registered.` with the store left untouched (same bound object, same key set), matching the Exsures frame clauses; cm.py:129-136 `if name in self: if not force: raise ValueError`, pre-existing at base_commit. Recommend adding a B0 row (LabelAlreadyBound <-> the force=False ValueError, tag I). Also: refinement.md B6 cites test_double_register_builtin_cmap, which is NOT in this instance's graded set (all 265 graded tests are test_colors.py; the collision behaviour is untested by this oracle) — the citation overstates oracle coverage though the clause itself is sound.

ENVIRONMENT: all work (13 attacks, 4 patches, 4 resolve JSONs, builders mk.py/mkpatch.py, runners runwk.sh/runresolve.py, instrumentation spy.py/conftest_spy.py/aleg.py). Every attack verification and every resolve ran to COMPLETION — no timeouts, no host-saturation artifacts, nothing INCONCLUSIVE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7.py`, `atk_8.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 13 same-spec attacks; 3 came back CANDIDATE (share spec AND verify); ALL 3 had their faithful refined patch materialized and RUN through the official harness, and ALL 3 RESOLVED (2/2 F2P, 263/263 P2P each). No verify=>correct witness found.

CRITICAL FINDING — I REFUTE THE RECORDED G-EQ/G-PANEL-1 'fail'. meta.json records G-EQ=fail on the CURRENT model.py hash (5cd95084...) with note 'BROKEN (verify=>correct): atk_5.py verifies but its patch does not resolve — FAIL_TO_PASS fails 2/2 ...; PASS_TO_PASS fails 1/263: test_register_cmap'. That prior atk_5 was the aliased-receiver label clobber (`if self is other: self.name = 0`), which I re-encoded as MY atk_7. Its faithful patch RESOLVES (2/2 F2P, 263/263 P2P, resolve_7.json). The recorded 'fail' is a PATCH-MATERIALIZATION ARTIFACT, not a spec defect, and I proved the mechanism: the recorded failure signature is reproduced EXACTLY by applying only the cm.py hunk while leaving colors.py at PREPATCH. Run in-container at base_commit (cm relabel applied, colors.py untouched, test_patch applied):
  python -m pytest test_colormap_equals test_set_cmap_mismatched_name test_register_cmap
  -> 3 failed: test_colormap_equals, test_set_cmap_mismatched_name (F2P 2/2) AND test_register_cmap (the 1/263 P2P)
That is precisely the recorded signature. A well-formed patch carrying BOTH gold hunks cannot produce it, so the prior run's colors.py hunk never applied (its context line `if (not isinstance(other, Colormap) or self.name != other.name or` had the extra step spliced ahead of it, which breaks the hunk context). Note also the prior pass's OWN notes say all 5 candidates resolved and its agent verdict was SOUND — the recorded machine 'fail' contradicts its own evidence. I built every patch via `git diff` in a worktree at base_commit so the text is well-formed by construction, and asserted read-back that BOTH gold hunks are present in the patched tree before diffing.

WHY THE ONE GENUINE FREEDOM IS HARMLESS (measured, not assumed): `colormaps_equal` requires Acc(self.X,1/2) and Acc(other.X,1/2) SEPARATELY, so on an ALIASED call (self is other) the halves SUM TO WRITE permission, and no Ensures value-constrains self.name/colorbar_extend/lut. A verifying impl may therefore mutate the receiver on the self-comparison path (atk_7, atk_8). But the postcondition `Result() == (colorbar_extend-equal AND seq_eq(lut,lut))` TOTALLY pins the returned value as a function of observable state, so aliased-receiver mutation is the ONLY residual observational freedom. I measured its reachability: I instrumented the REAL Colormap.__eq__ with an aliasing spy and ran the ENTIRE 265-test graded suite (F2P+P2P) under the gold patch -> 265 passed, 10 total __eq__ calls, ZERO aliased (self is other) calls. The graded suite always compares two DISTINCT objects (cm_copy vs cmap, cmap_returned vs cmap), and ColormapRegistry.__getitem__ returns a .copy(), so no registry read can alias. The freedom is unreachable-in-practice latent freedom, refuted 3/3 by the harness — reporting it as a break would invent spec weakness (retained-attack-label failure mode).
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC IDENTITY FIRST: sha256(model.py) = 5cd95084734c7e469dd6961ddf81434dfa0cdc6f2923c53f4f727a6f93dcdeaf, matching meta.json G-VERIFY/G-AX/G-CONF/G-GOLD/G-DIFF/G-MUT/G-PBT sources. All 13 attacks confirmed byte-identical spec via `adversary same-spec` -> 'SAME', exit 0. Bundle read-only throughout; hash re-checked unchanged at the end. My git worktree was created under my own scratch dir only and removed afterwards.

POSITIVE CONTROL: pos_control.py (byte-identical model.py) -> `bash scripts/nagini_verify.sh` -> 'Verification successful', 15.41s, exit 0 (non-vacuity).

### PREPATCH REPRODUCED (both sites, both REJECTED):
  atk_1 — eq site, prepatch `if self.name != other.name: return False` -> exit 2.
  atk_2 — register site, drops `snapshot.name = name` -> exit 2.

Command for every attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25479 atk_N.py` (run 3-at-a-time as background jobs; each spawns JVM+Z3). Outputs at wk_N.out.

REJECTED (10/13, exit 2 — spec is strong here), with the clause that kills each:
  atk_1 prepatch eq (label re-added) | atk_2 prepatch register (no relabel)
  atk_3 PARTIAL-DOMAIN `if self is other: return True` -> 'Postcondition of colormaps_equal might not hold' — killed by A5 non-reflexivity (a NaN-carrying table must be unequal to ITSELF).
  atk_4 BOUNDARY: scan `while i < len(self.lut) - 1` (last entry never compared).
  atk_5 UNGROUNDED-ORACLE ECHO: raw token `!=` instead of the frozen `entry_eq` (idealised REFLEXIVE equality) -> 'Loop invariant might not be preserved'.
  atk_6 FLAG-DOMAIN COLLAPSE: six-valued flag through a 2-valued carrier `(x>0) != (y>0)` — confirms A2 injectivity is load-bearing IN THE CONTRACT, not just prose.
  atk_9 FRAME: side-write `reg[name+1] = snapshot` — killed by B6's Forall clauses.
  atk_10 CONTROL-FLOW EFFECT: store-then-raise -> 'Postcondition of register_named might not hold. Assertion (reg[name] is Old(reg[name])) might not hold' — the Exsures frame clause.
  atk_11 SILENT OVERWRITE (collision refusal dropped) — killed by `Ensures(not Old(name in reg))`.
  atk_13 PARTIAL-DOMAIN: flag ignored when both tables empty.

CANDIDATES (3/13, exit 0) — ALL RESOLVED, so none breaks the spec. Patches built via `git diff` at base_commit 7fdf7722, `git apply --check` CLEAN, read-back asserted BOTH gold hunks present; run via swebench_unified.harness.run_resolve (run_id geq7cf-<tag>), records at resolve_<tag>.json:
  atk_7  aliased receiver: clobber the label      -> resolved=True completed=True F2P 2/2 P2P 263/263
  atk_8  aliased receiver: destroy lut, return True -> resolved=True completed=True F2P 2/2 P2P 263/263
  atk_12 CORRECT RESHAPE control (copy built already-relabelled) -> resolved=True completed=True F2P 2/2 P2P 263/263
  GOLD CONTROL patch_gold.diff (my materializer's output for the unmodified impl) -> resolved=True F2P 2/2 P2P 263/263, validating the materializer itself.

A-LEG AUDIT (my focus; R/I legs left to G-CONF). There is NO consumed axiom in this bundle — `axioms-start/end` is a comment block only (confirmed: axioms region is prose), so there is no axiom-soundness surface; the only kind-A entries are three A-REFERENCES. I re-measured each against the REAL post-patch callee in-container (aleg.py, after asserting the loaded colors.py has the name disjunct ABSENT): A2 flag injectivity over (False,True,'neither','min','max','both'): all 15 distinct pairs SEPARATED by the real __eq__ (not-separated list EMPTY) -> the carrier may merge nothing. Load-bearing, confirmed by atk_6's rejection.

A4/A5 (seq_eq/entry_eq <-> np.array_equal's elementwise ==, equal_nan default False): NaN-carrying lut -> `c == c` is False AND `c == c.copy()` is False, exactly the deliberate NON-REFLEXIVITY entry_eq encodes; determinate table -> `d == d` True. Confirmed load-bearing by atk_3's rejection. A3 (label irrelevant — the patch delta): relabelled-but-content-equal -> real __eq__ True, matching a postcondition naming no label term. B2/B3 (copy() <-> Cmap constructor; relabel): register(name='wrong-cmap') -> stored.name=='wrong-cmap', `is not` supplied, `==` supplied, supplied.name still 'test-cmap'. Matches every Ensures.

All A-leg correspondences HOLD. refinement.md §C's 'no kind-3' claim checks out: every step is R / A-reference / I, and the two genuinely-changed ops are modelled DEEPLY (postcondition predicate + seq_eq fold over entry_eq; spelled-out relabel+store) rather than axiomatized. No A-consumed legs exist, so nothing is assumed rather than established.

DOCUMENTATION GAP (advisory, NOT a G-EQ break — the spec is sound and all 3 candidate patches resolve): `grep -nE 'LabelAlreadyBound|Exsures|refus|collision' refinement.md mapping.md` returns NOTHING (exit 1). The impl's collision-refusal step (`if name in reg: raise LabelAlreadyBound()`) and its Exsures leg have NO row in the refinement table, yet that leg is real and load-bearing — it is what kills atk_10 and atk_11. Its correspondence DOES hold: I measured a second `register(name='wrong-cmap')` -> `ValueError: A colormap named "wrong-cmap" is already registered.` with the store left untouched (same bound object, same key set), matching the Exsures frame clauses; cm.py:129-136 `if name in self: if not force: raise ValueError`, pre-existing at base_commit. Recommend adding a B0 row (LabelAlreadyBound <-> the force=False ValueError, tag I). Also: refinement.md B6 cites test_double_register_builtin_cmap, which is NOT in this instance's graded set (all 265 graded tests are test_colors.py; the collision behaviour is untested by this oracle) — the citation overstates oracle coverage though the clause itself is sound.

ENVIRONMENT: all work (13 attacks, 4 patches, 4 resolve JSONs, builders mk.py/mkpatch.py, runners runwk.sh/runresolve.py, instrumentation spy.py/conftest_spy.py/aleg.py). Every attack verification and every resolve ran to COMPLETION — no timeouts, no host-saturation artifacts, nothing INCONCLUSIVE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**SPEC REGION IDENTITY FIRST:** sha256(model.py) = 5cd95084734c7e469dd6961ddf81434dfa0cdc6f2923c53f4f727a6f93dcdeaf, matching meta.json gates.G-AX/G-CONF/G-GOLD/G-DIFF sources exactly. A byte-identical copy through `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-25479 atk_same.py` -> "SAME — attack shares the bundle's exact specification", exit 0. I judged the shipped spec, not a variant.

**NOT AN INHERITED LABEL:** verdict.md on this bundle records G-PANEL-2 fail / UNFAITHFUL, but it was written at 13:23 against model.py hash eddba376..., and model.py was rewritten at 14:55 to hash 5cd95084.... Per the retained-attack-label failure mode, re-judging a repaired spec by its stale label would invent spec weakness, so I re-derived every leg from scratch and explicitly re-ran the prior attack to test whether it still bites. It does not (see counterexample).

REFERENCE DISCIPLINE (checked BEFORE comparing): the modelled function's reference is base_commit WITH patch.diff APPLIED. Asserted in-script on the executed matplotlib that both gold hunks are present:
  - colors.py `__eq__`: the `self.name != other.name` disjunct ABSENT
  - cm.py register: `if self._cmaps[name].name != name: self._cmaps[name].name = name` PRESENT
So I never scored the patch delta itself as a divergence.

### REAL-CALLEE LEGS MEASURED (all AGREE with the spec):
 (1) label-free equality, the patch delta: relabelled-but-content-equal pair -> real == True (model predicts True); flag differs -> False; lut differs -> False.

 (2) entry_eq's deliberate NON-reflexivity: a NaN-carrying lut compares unequal to ITSELF (False) and to its own copy (False) in the real callee -- exactly what a negative token predicts, correctly modelling np.array_equal's default equal_nan=False.

 (3) colorbar_extend int token is genuinely INJECTIVE over the full six-valued domain (False/True/'neither'/'min'/'max'/'both'): all 15 distinct pairs separated by the real `__eq__`, empty not-separated list. The carrier merges nothing the callee distinguishes.

 (4) register on a FRESH label: stored name == registration label, independent object, flag and table carried, supplied cmap untouched, other keys keep membership AND identity.

 (5) register on an ALREADY-BOUND label: raises ValueError, `reg[name] is Old(reg[name])` True, supplied cmap untouched, membership of every key frozen -- matching the new Exsures clause-for-clause.

 (6) snapshot fidelity on an INDETERMINATE table: bitwise-equal under equal_nan=True (model's ToSeq clause) while ==-unequal under the default (model's seq_eq) -- the model gets BOTH legs right, which is refinement.md B2's distinction.

 (7) name == cmap.name: the patch's `if != name` guard no-ops; the model's unconditional assign yields the same post-state (400 trials, 0 disagreements).

INDEPENDENT FUZZ (my own generator, deliberately NOT reusing the bundle's): 6000 equality trials over relabels/truncations/NaN rows/full flag domain + 1200 FRESH-label registrations + 1200 COLLIDING-label registrations (all 1200 raised, state checked against the Exsures clauses) = 8400 trials, 0 disagreements. The collision leg is the one the bundle's own G-CONF generator draws disjoint from the seeded keys (fuzz_reg_input draws name_token from range(1000,2000) vs seed_keys from range(1000)), so I covered the previously-generated-away boundary directly and it now holds.

MACHINE-CHECKED DERIVATION + VACUITY CONTROLS (per the guarded-self-call failure mode, an infeasible guard verifies while proving nothing; Assert(False) is the control):
  fresh_client.py  (spec still DERIVES B3 `reg[60].name == 60`, independence, flag/table carry, and the frame clause on key 50) -> Verification successful (21.16s)
  ctl_fresh.py     (same + trailing Assert(False))                                  -> FAILS: "Assertion False might not hold" (23.77s) => non-vacuous
  coll_handled.py  (collision caught; asserts the Exsures state -- binding INTACT, `reg[50] is old`, cmap untouched; and Assert(False) on the normal-return branch, proving that branch is unreachable when the label is bound) -> Verification successful (20.68s)
  ctl_coll.py      (same + Assert(False) INSIDE the except handler)                  -> FAILS: "Assertion False might not hold" (24.70s) => the Exsures path is genuinely REACHABLE, not a dead branch that verifies trivially
The pair (coll_handled passes / ctl_coll fails) is the key evidence: the exception path is live and its post-state is exactly the real callee's refusal semantics.

**CONCLUSION:** the spec is not too strong on any input I could reach. The one previously-known over-claim (the unguarded collision domain) is closed by the Exsures + `not Old(name in reg)` clauses, and closed in the contract rather than in prose -- which is precisely what the earlier finding asked for. Every remaining clause I tested is TRUE of the real post-patch callee. Verdict FAITHFUL.

**ENVIRONMENT:** the /tmp worktree (, HEAD 7fdf7722 + both gold hunks applied) cannot be imported directly (no compiled extensions), so execution used the installed matplotlib 3.10.9 after asserting in-script that its `__eq__`/register/`__copy__` sources carry both gold hunks and match the patched worktree on every modelled line. the bundle was read-only throughout and is unmodified. Verifier ran to completion in all five runs (no timeouts, no host-saturation artifacts), so this is a measured verdict, not an INCONCLUSIVE dressed up as a pass.

Counterexample / evidence:

```
None. The exact prior counterexample client, replayed verbatim against the current spec region:

  bash scripts/nagini_verify.sh client.py
  -> Verification failed
     client.py:271:1:293:50: error: Exhale might fail. Assertion "method raises no exceptions" might not hold.
     (23.60s)

The repair is real and is visible in the spec region itself: register_named now carries
  Ensures(not Old(name in reg))                  # normal return implies the label was FREE
  Exsures(LabelAlreadyBound, Old(name in reg) and ... reg[name] is Old(reg[name]) ...)
so a colliding label is an out-of-band report with the live binding provably INTACT, and a caller can no longer derive the silent-overwrite conclusion. model.py hash moved eddba376... -> 5cd95084..., and meta.json's G-VERIFY/G-AX/G-CONF/G-GOLD/G-DIFF sources all now cite 5cd95084..., i.e. the gates were re-run on the repaired spec.
```

SPEC REGION IDENTITY FIRST: sha256(model.py) = 5cd95084734c7e469dd6961ddf81434dfa0cdc6f2923c53f4f727a6f93dcdeaf, matching meta.json gates.G-AX/G-CONF/G-GOLD/G-DIFF sources exactly. A byte-identical copy through `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-25479 atk_same.py` -> "SAME — attack shares the bundle's exact specification", exit 0. I judged the shipped spec, not a variant.

NOT AN INHERITED LABEL: verdict.md on this bundle records G-PANEL-2 fail / UNFAITHFUL, but it was written at 13:23 against model.py hash eddba376..., and model.py was rewritten at 14:55 to hash 5cd95084.... Per the retained-attack-label failure mode, re-judging a repaired spec by its stale label would invent spec weakness, so I re-derived every leg from scratch and explicitly re-ran the prior attack to test whether it still bites. It does not (see counterexample).

REFERENCE DISCIPLINE (checked BEFORE comparing): the modelled function's reference is base_commit WITH patch.diff APPLIED. Asserted in-script on the executed matplotlib that both gold hunks are present:
  - colors.py __eq__: the `self.name != other.name` disjunct ABSENT
  - cm.py register: `if self._cmaps[name].name != name: self._cmaps[name].name = name` PRESENT
So I never scored the patch delta itself as a divergence.

### REAL-CALLEE LEGS MEASURED (all AGREE with the spec):
 (1) label-free equality, the patch delta: relabelled-but-content-equal pair -> real == True (model predicts True); flag differs -> False; lut differs -> False.

 (2) entry_eq's deliberate NON-reflexivity: a NaN-carrying lut compares unequal to ITSELF (False) and to its own copy (False) in the real callee -- exactly what a negative token predicts, correctly modelling np.array_equal's default equal_nan=False.

 (3) colorbar_extend int token is genuinely INJECTIVE over the full six-valued domain (False/True/'neither'/'min'/'max'/'both'): all 15 distinct pairs separated by the real __eq__, empty not-separated list. The carrier merges nothing the callee distinguishes.

 (4) register on a FRESH label: stored name == registration label, independent object, flag and table carried, supplied cmap untouched, other keys keep membership AND identity.

 (5) register on an ALREADY-BOUND label: raises ValueError, `reg[name] is Old(reg[name])` True, supplied cmap untouched, membership of every key frozen -- matching the new Exsures clause-for-clause.

 (6) snapshot fidelity on an INDETERMINATE table: bitwise-equal under equal_nan=True (model's ToSeq clause) while ==-unequal under the default (model's seq_eq) -- the model gets BOTH legs right, which is refinement.md B2's distinction.

 (7) name == cmap.name: the patch's `if != name` guard no-ops; the model's unconditional assign yields the same post-state (400 trials, 0 disagreements).

INDEPENDENT FUZZ (my own generator, deliberately NOT reusing the bundle's): 6000 equality trials over relabels/truncations/NaN rows/full flag domain + 1200 FRESH-label registrations + 1200 COLLIDING-label registrations (all 1200 raised, state checked against the Exsures clauses) = 8400 trials, 0 disagreements. The collision leg is the one the bundle's own G-CONF generator draws disjoint from the seeded keys (fuzz_reg_input draws name_token from range(1000,2000) vs seed_keys from range(1000)), so I covered the previously-generated-away boundary directly and it now holds.

MACHINE-CHECKED DERIVATION + VACUITY CONTROLS (per the guarded-self-call failure mode, an infeasible guard verifies while proving nothing; Assert(False) is the control):
  fresh_client.py  (spec still DERIVES B3 `reg[60].name == 60`, independence, flag/table carry, and the frame clause on key 50) -> Verification successful (21.16s)
  ctl_fresh.py     (same + trailing Assert(False))                                  -> FAILS: "Assertion False might not hold" (23.77s) => non-vacuous
  coll_handled.py  (collision caught; asserts the Exsures state -- binding INTACT, `reg[50] is old`, cmap untouched; and Assert(False) on the normal-return branch, proving that branch is unreachable when the label is bound) -> Verification successful (20.68s)
  ctl_coll.py      (same + Assert(False) INSIDE the except handler)                  -> FAILS: "Assertion False might not hold" (24.70s) => the Exsures path is genuinely REACHABLE, not a dead branch that verifies trivially
The pair (coll_handled passes / ctl_coll fails) is the key evidence: the exception path is live and its post-state is exactly the real callee's refusal semantics.

CONCLUSION: the spec is not too strong on any input I could reach. The one previously-known over-claim (the unguarded collision domain) is closed by the Exsures + `not Old(name in reg)` clauses, and closed in the contract rather than in prose -- which is precisely what the earlier finding asked for. Every remaining clause I tested is TRUE of the real post-patch callee. Verdict FAITHFUL.

ENVIRONMENT: the /tmp worktree (, HEAD 7fdf7722 + both gold hunks applied) cannot be imported directly (no compiled extensions), so execution used the installed matplotlib 3.10.9 after asserting in-script that its __eq__/register/__copy__ sources carry both gold hunks and match the patched worktree on every modelled line. the bundle was read-only throughout and is unmodified. Verifier ran to completion in all five runs (no timeouts, no host-saturation artifacts), so this is a measured verdict, not an INCONCLUSIVE dressed up as a pass.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

ATTACKER 3 (leakage / gold-reconstruction), matplotlib__matplotlib-25479 nagini. Verdict NO-LEAKAGE.

SCOPE / NO RELAXATION IN PLAY -- established by my own measurement, not inherited. `find` over the whole instance dir returns no RELAXED_LEAKAGE.md; meta.json has NO top-level `relaxed_leakage` key (top-level keys are [auxiliary_classes, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version] -- zero matching /relax/i); gates.G-LEAK.status == 'pass' with mode 'strict' and detail 'spec view clean', NOT 'relaxed'. So there was no unavoidability argument for me to credit or reject, and I applied the full strict spec_guide.md 0.6 bar: problem_statement is the sole baseline, hints_text and test_patch excluded.

**SPEC IDENTITY FIRST.** sha256(model.py) = 5cd95084734c7e469dd6961ddf81434dfa0cdc6f2923c53f4f727a6f93dcdeaf, matching meta.json gates G-VERIFY/G-AX/G-CONF/G-LEAK/G-GOLD/G-DIFF/G-MUT/G-PBT sources exactly (note G-EQ/G-PANEL-* still stamp the older eddba376... hash, i.e. those are stale relative to the live artifact; the gates my verdict leans on are all on the current hash). I computed the spec view myself via swebench_unified.markers.spec_view over the live file rather than trusting a stamp, and confirmed spec-region identity with `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-25479 <impl-only variant>` -> "SAME -- attack shares the bundle's exact specification", exit 0. Live file verifies: `bash scripts/nagini_verify.sh` -> "Verification successful", 16.08s, exit 0. patch.diff is byte-equal to the frozen instance patch. I judged the shipped spec view, not a variant.

MECHANICAL SCREEN, re-run by me on the current hash: swebench_unified.leakage.screen(spec_view, nagini, patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. No diff marker (L1), no gold-patch line reproduced (L1), no patched file/module path -- 'lib/matplotlib/cm.py' and 'lib/matplotlib/colors.py' both absent from the view (L2), no spec-view identifier embedding a patched repo symbol (L2/L5), no bug/fix narration (L3).

**I DID NOT STOP AT THE LEXICAL SCREEN.** Four semantic probes, each of which cleared:

(1) SUB-THRESHOLD GOLD-LINE RECONSTRUCTION. The screen only rejects a whole normalized changed line at >=8 chars, so I computed the LONGEST normalized substring of each gold changed line that occurs in the view. Worst cases: '[name].name=' (12) from `self._cmaps[name].name = name`, matching `Ensures(reg[name].name == name)`; 'other.name' (10) from the REMOVED disjunct `self.name != other.name`, matching only the permission clause `Acc(other.name, 1/2)`; 'different'/'theregist'/'abuiltin' (8-9) from the gold's added comment block. All are dict-subscript-plus-attribute or English-word coincidences, not reproduced gold code. Decisively: the removed disjunct is NOT reconstructible, because the view's equality characterisation `Result() == (self.colorbar_extend == other.colorbar_extend and seq_eq(...))` contains no label term at all -- `other.name` survives only in permission bookkeeping, never in a comparison.

(2) HINTS-ONLY VOCABULARY (the documented #1 leak mode). I diffed hints_text vocabulary against the view with problem_statement subtracted. Every survivor is a common English word (above, because, different, only, still, under, ...). No hints-only diagnosis is echoed: the hints' actual content (set_cmap, pyplot.py L2072-2078, cmap_d, rcParams['image.cmap'], the #18503 refactor, timhoffm/greglucas) appears NOWHERE in the view. The two hints-only technical tokens I checked individually -- 'colormaps' and 'colorbar_extend' -- resolve benignly: 'colormaps' matches only case-insensitively inside the model's own `colormaps_equal`, and 'colormap' IS public in the problem_statement.

(3) PATCHED-SYMBOL LOCALIZATION, checked by hand not just by the screen. Gold changed symbols are {register, copy}. `register_named` DOES embed 'register' -- the screen excuses it, and I confirmed the excuse is legitimate rather than a screen gap: the problem_statement names registration explicitly and repeatedly (`cm.register_cmap(name='my_cmap_name', cmap=my_cmap)`, 'registered colormap name'). 'copy' is absent from the view entirely (zero matches for /\`w*copy`\w*/i) -- the snapshot primitive is called 'snapshot' throughout (15 uses), so the `__copy__`/`copy()` A-reference is NOT named. `colorbar_extend` appears 15 times but occurs in the gold diff only as a CONTEXT line, never a changed one: it is pre-existing base_commit structure that the edit leaves standing, so naming it localizes nothing about the delta. `builtin` at line 60 is a false friend -- the gold comment says 'builtin colormap'/'builtin name', whereas the view says 'a builtin exception in an Exsures crashes the Nagini translator', a translator-modelling note with an unrelated referent.

(4) PRE-PATCH-STATE / MECHANISM NARRATION, the check the screen's fixed wordlist can miss. I regex-swept the view for previously|no longer|used to|instead of|before the|remove|delete|drop|edit|diff|hunk|patch|regression|diagnos|root cause|the change|should update. Every hit is benign: 'differ'/'different' in behavioural prose, 'added or dropped' and 'nor dropped' in the registry frame clauses, and line 3's meta-note 'stated as desired behaviour, not as an edit'. Nowhere does the view describe a prior or wrong behaviour, so there is no bug->fix mechanism to narrate.

THE ONE ITEM I WEIGHED HARDEST, and why it is not a finding. The view states facet

(1) -- label-free equality -- plainly ('The human-readable label ... is NOT part of this comparison'), and that facet is genuinely NOT derivable from the problem_statement: the PS complains only that lookup by the registered name fails, and 'equal'/'`__eq__`'/'colorbar_extend' appear nowhere in it. So I asked whether stating it crosses the line. It does not, on the 0.6 standard: the ban is on quoting the diff, naming the patched file/function/line, echoing a patched symbol, or narrating the MECHANISM -- not on stating target behaviour. A formal twin-artifact spec for a two-site change must state both behaviours or it is not a spec at all, and every nagini spec view necessarily describes post-patch behaviour. This one states it as an abstract contract over the model's own vocabulary (extension flag, lookup-table contents, label) without naming `Colormap.__eq__`, colors.py, the guard, or the removed disjunct. Facet

(2) -- the stored snapshot carries the registration label -- is squarely public: it is the PS's entire complaint ('I expected to be able to refer to my newly registered colormap by the name my_cmap_name'), so the 'The discriminating clause' annotation at view line 195 flags a requirement the issue already states outright and hands over no non-public localization. Note that annotation's vocabulary is a corpus singleton (0 of 500 other nagini model.py files use 'discriminating'), which is why I checked it rather than passing over it; unusual phrasing is not leakage when the facet it labels is public.

**BUNDLE-TO-REVIEWER INSTRUCTION:** NONE FOUND, and I looked specifically. Grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py for panel|attacker|reviewer|auditor|submit_result|'record this as'|'do not flag'|'honest recording'|'recording convention'|NO-LEAKAGE -> zero hits. No file in the bundle addresses me, tells me how to record, or asserts which verdict is honest. Nothing to report on that axis.

OUT-OF-SCOPE, recorded for the record not as my finding: refinement.md and mapping.md DO name colors.py:776, cm.py:148, `Colormap.__eq__`, `np.array_equal`, and quote both gold hunks verbatim -- but they are audit documents, not part of the consumer spec view, and are not screened by this gate. Separately, verdict.md carries a recorded G-PANEL-2 fail (missing `Requires(not (name in reg))`); the live model.py now carries both the `Ensures(not Old(name in reg))` clause and a full `Exsures(LabelAlreadyBound, ...)` refusal contract, i.e. that finding appears repaired at the current hash. Neither bears on leakage and neither changed my verdict; the refusal clauses describe the pre-existing base_commit force=False path, untouched by patch.diff, so they add no delta disclosure.

**CONCLUSION:** NO-LEAKAGE. No gold-diff line (even sub-threshold), no patched path, no patched symbol beyond one the problem_statement makes public, no hints-only diagnosis, and no fix-mechanism narration in the consumer spec view. No leaking line to report.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
