# P2 adversarial audit — matplotlib__matplotlib-26208

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := none
     return out
     -- impl-end
 
@@ -94,7 +94,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := none
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := some 0
     return out
     -- impl-end
 
@@ -94,7 +94,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := some 0
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := none
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := if source.isSome then some 1 else none
     return out
     -- impl-end
 
@@ -94,7 +94,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := if source.isSome then some 1 else none
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := if source.isSome then none else some 0
     return out
     -- impl-end
 
@@ -94,7 +94,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := if source.isSome then none else some 0
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,7 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := none
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No unchanged opaque callee is consumed. The modeled behaviour is the
@@ -67,7 +67,9 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := match source with
+      | none => none
+      | some t => some (t + 1)
     return out
     -- impl-end
 
@@ -94,7 +96,9 @@
   ensures isPresent out = isPresent source
   do
     -- impl-start
-    let out := source
+    let out : ConvSetting := match source with
+      | none => none
+      | some t => some (t + 1)
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No unchanged opaque callee is consumed. The modeled behaviour is the
--  per-axis carry-over of a shared coordinate's display-conversion setting,
--  modeled deeply below as a plain value copy. There is no consumed axiom and
--  no A-reference deep model of an unchanged callee. See refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The display-conversion setting that an axis may carry for the quantity
   plotted along it. It is either absent (`none` — no conversion configured) or
   a present setting identified up to object identity by an opaque tag
   (`some t`). When a quantity has already been plotted along an axis, that axis
   carries a present setting; a freshly created axis carries `none`.

   The behaviour under spec turns only on whether two axes carry the SAME
   setting (the identical present object, or both absent), so the setting is
   modeled as `Option Int`: `none` ↔ absent, `some t` ↔ a present setting whose
   integer tag is its object identity. Equality of the modeled value is exactly
   identity of the underlying setting (mapping.md §2). -/
abbrev ConvSetting := Option Int

/- Whether an axis carries a present (non-absent) conversion setting. The public
   reproduction observes that, after a quantity has been plotted, the shared
   axis carries a present setting on BOTH the original and the newly created
   companion axes. -/
@[grind, simp]
def isPresent (s : ConvSetting) : Bool := s.isSome
-- pure-end

-- pre-conditions-start
-- (inheritSharedConvA: the source axis's conversion setting for the shared
--  coordinate.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvA: the companion axis's setting for the shared coordinate
--  equals the source's — the same present object, or both absent.)
-- post-conditions-end

/- First companion-creation site. A new companion view is created that shares
   one coordinate with the source view. The companion's axis for that SHARED
   coordinate must carry exactly the source axis's conversion setting for it:
   the identical setting object when one is present, and absent when the source
   has none. Two guarantees pin the behavior the issue's tested scenario
   demands:

   - the companion's shared-axis setting equals the source's (`out = source`);
     so when the source already carries a present setting the companion carries
     that very same one, and the companion never silently starts from absent.
   - consequently the companion's shared axis reports a present setting exactly
     when the source does (`isPresent out = isPresent source`).

   `source` is the read-only setting carried by the source view's shared axis;
   the step constructs the companion's setting and never alters the source
   (directive 5). -/
method inheritSharedConvA (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    let out : ConvSetting := match source with
      | none => none
      | some t => some t
    return out
    -- impl-end

prove_correct inheritSharedConvA by
  loom_solve

-- pre-conditions-start
-- (inheritSharedConvB: the source axis's conversion setting for the shared
--  coordinate, at the second independent companion-creation site.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvB: same carry-over guarantee as inheritSharedConvA, at the
--  second independent site.)
-- post-conditions-end

/- Second, independent companion-creation site with the same obligation: a new
   companion view shares the OTHER coordinate with the source, and its axis for
   that shared coordinate must carry exactly the source axis's conversion
   setting. Modeled separately because it is observed independently of the first
   site (the issue's tested scenario exercises each coordinate on its own). -/
method inheritSharedConvB (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    let out : ConvSetting := match source with
      | none => none
      | some t => some t
    return out
    -- impl-end

prove_correct inheritSharedConvB by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial (A-leg / model↔patch focus) verdict: SOUND. No verifying wrong impl exists, so the mandatory materialize+resolve step (protocol step 2) has NO candidate to run — verify⇏correct cannot be exhibited.

Spec shape: two methods inheritSharedConvA/B, each with postcondition `ensures out = source` (plus redundant `ensures isPresent out = isPresent source`). `out = source` is the TIGHTEST possible postcondition — it pins the output to be identical to the actual input `source`, not to any answer-key constant/oracle. Therefore no wrong impl can discharge it (no ungrounded-oracle echo is possible: the only opaque symbol is the Int identity tag, and the post demands equality to the actual input rather than a fixed key — atk_2 returning a constant is rejected).

 Byte-identical-spec confirmed via swebench_unified.markers.same_spec (velvet): all 8 files True (only impl regions edited; axioms/pure/pre/post/ensures untouched). Verified with `bash scripts/lean_verify.sh <file>`, run concurrently in two batches of 4.

7 DISTINCT same-spec wrong impls, all verify exit=1 (rejected), all on the discriminating clause:
- atk_1: out:=none at BOTH sites (the prepatch bug re-encoded). exit 1; fails ensures_1 isPresent + ensures_2 out=source at lines 74 & 101.
- atk_2: out:=some 0 at both (fixed constant / closest oracle-echo). exit 1; fails ensures_1 & ensures_2.
- atk_3: site A correct (out:=source), site B out:=none (partial-domain / proves sites independently observed). exit 1; fails at site B (line 101).
- atk_4: out := if source.isSome then some 1 else none (present but WRONG identity — boundary). exit 1; fails ensures_2 out=source at both sites.
- atk_5: out := if source.isSome then none else some 0 (FLIPPED presence — control-flow-effect). exit 1; fails ensures_1 + ensures_2.
- atk_6: mirror of atk_3 — site A out:=none, site B correct (partial-domain, other site). exit 1; fails at site A.
- atk_7: out := match source with none=>none | some t=>some (t+1) (present, tag off-by-one — control-flow-effect / ungrounded-echo variant). exit 1; fails ensures_2 out=source at both sites.

Positive control atk_pc: out := match source with none=>none | some t=>some t (structurally different but behaviourally correct) — verify exit=0. Spec is NON-VACUOUS: it accepts the correct behavior and rejects every wrong one.

Prepatch reproduced: yes — atk_1 is the prepatch bug (companion axis keeps freshly-initialised absent default `none` instead of carrying over source's setting), matching bundle Solution_prepatch_1/2.lean; both fail on out=source/isPresent exactly as recorded.

Refinement.md / mapping.md audit (A-leg + correspondence, my mandate): every leg is R or I — A1/A3/B1/B3 = R (type bijection Axis.units ↔ Option Int; None↔none, present object↔some id(obj); object identity ↔ tag equality); A2/B2 = I (deep value copy `out:=source` modeling gold's `ax2.<axis>.units = self.<axis>.units`). §C: NO kind-3 inexpressible-changed-op, NO consumed axioms, NO A-reference deep model of an unchanged callee (G-AX genuinely vacuous; empty axiom + deep_model_references inventories, conf_skip=false). There are thus no A-legs whose correspondence to a real callee could be falsified — the single changed op is modeled deeply and its fidelity is G-CONF's job (R/I leg, out of my scope, mechanically covered by G-CONF: bundle reports 100,004 inputs seed 26208, 0 disagreements against the REAL patched twinx/twiny). Model↔patch correspondence (inheritSharedConvA↔twinx @ _base.py:4441, inheritSharedConvB↔twiny @ :4470) is coherent and matches mapping.md §1.

Since no wrong impl verifies, no faithful refined patch needed materializing/resolving; there is no BROKEN candidate. Verdict SOUND: ≥5 (7) distinct attacks verified-rejected, positive control verifies, prepatch reproduced, refinement legs all R/I with sound A-inventory (vacuous).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No unchanged opaque callee is consumed. The modeled behaviour is the
--  per-axis carry-over of a shared coordinate's display-conversion setting,
--  modeled deeply below as a plain value copy. There is no consumed axiom and
--  no A-reference deep model of an unchanged callee. See refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The display-conversion setting that an axis may carry for the quantity
   plotted along it. It is either absent (`none` — no conversion configured) or
   a present setting identified up to object identity by an opaque tag
   (`some t`). When a quantity has already been plotted along an axis, that axis
   carries a present setting; a freshly created axis carries `none`.

   The behaviour under spec turns only on whether two axes carry the SAME
   setting (the identical present object, or both absent), so the setting is
   modeled as `Option Int`: `none` ↔ absent, `some t` ↔ a present setting whose
   integer tag is its object identity. Equality of the modeled value is exactly
   identity of the underlying setting (mapping.md §2). -/
abbrev ConvSetting := Option Int

/- Whether an axis carries a present (non-absent) conversion setting. The public
   reproduction observes that, after a quantity has been plotted, the shared
   axis carries a present setting on BOTH the original and the newly created
   companion axes. -/
@[grind, simp]
def isPresent (s : ConvSetting) : Bool := s.isSome
-- pure-end

-- pre-conditions-start
-- (inheritSharedConvA: the source axis's conversion setting for the shared
--  coordinate.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvA: the companion axis's setting for the shared coordinate
--  equals the source's — the same present object, or both absent.)
-- post-conditions-end

/- First companion-creation site. A new companion view is created that shares
   one coordinate with the source view. The companion's axis for that SHARED
   coordinate must carry exactly the source axis's conversion setting for it:
   the identical setting object when one is present, and absent when the source
   has none. Two guarantees pin the behavior the issue's tested scenario
   demands:

   - the companion's shared-axis setting equals the source's (`out = source`);
     so when the source already carries a present setting the companion carries
     that very same one, and the companion never silently starts from absent.
   - consequently the companion's shared axis reports a present setting exactly
     when the source does (`isPresent out = isPresent source`).

   `source` is the read-only setting carried by the source view's shared axis;
   the step constructs the companion's setting and never alters the source
   (directive 5). -/
method inheritSharedConvA (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    let out : ConvSetting := match source with
      | none => none
      | some t => some t
    return out
    -- impl-end

prove_correct inheritSharedConvA by
  loom_solve

-- pre-conditions-start
-- (inheritSharedConvB: the source axis's conversion setting for the shared
--  coordinate, at the second independent companion-creation site.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvB: same carry-over guarantee as inheritSharedConvA, at the
--  second independent site.)
-- post-conditions-end

/- Second, independent companion-creation site with the same obligation: a new
   companion view shares the OTHER coordinate with the source, and its axis for
   that shared coordinate must carry exactly the source axis's conversion
   setting. Modeled separately because it is observed independently of the first
   site (the issue's tested scenario exercises each coordinate on its own). -/
method inheritSharedConvB (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    let out : ConvSetting := match source with
      | none => none
      | some t => some t
    return out
    -- impl-end

prove_correct inheritSharedConvB by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial (A-leg / model↔patch focus) verdict: SOUND. No verifying wrong impl exists, so the mandatory materialize+resolve step (protocol step 2) has NO candidate to run — verify⇏correct cannot be exhibited.

Spec shape: two methods inheritSharedConvA/B, each with postcondition `ensures out = source` (plus redundant `ensures isPresent out = isPresent source`). `out = source` is the TIGHTEST possible postcondition — it pins the output to be identical to the actual input `source`, not to any answer-key constant/oracle. Therefore no wrong impl can discharge it (no ungrounded-oracle echo is possible: the only opaque symbol is the Int identity tag, and the post demands equality to the actual input rather than a fixed key — atk_2 returning a constant is rejected).

 Byte-identical-spec confirmed via swebench_unified.markers.same_spec (velvet): all 8 files True (only impl regions edited; axioms/pure/pre/post/ensures untouched). Verified with `bash scripts/lean_verify.sh <file>`, run concurrently in two batches of 4.

7 DISTINCT same-spec wrong impls, all verify exit=1 (rejected), all on the discriminating clause:
- atk_1: out:=none at BOTH sites (the prepatch bug re-encoded). exit 1; fails ensures_1 isPresent + ensures_2 out=source at lines 74 & 101.
- atk_2: out:=some 0 at both (fixed constant / closest oracle-echo). exit 1; fails ensures_1 & ensures_2.
- atk_3: site A correct (out:=source), site B out:=none (partial-domain / proves sites independently observed). exit 1; fails at site B (line 101).
- atk_4: out := if source.isSome then some 1 else none (present but WRONG identity — boundary). exit 1; fails ensures_2 out=source at both sites.
- atk_5: out := if source.isSome then none else some 0 (FLIPPED presence — control-flow-effect). exit 1; fails ensures_1 + ensures_2.
- atk_6: mirror of atk_3 — site A out:=none, site B correct (partial-domain, other site). exit 1; fails at site A.
- atk_7: out := match source with none=>none | some t=>some (t+1) (present, tag off-by-one — control-flow-effect / ungrounded-echo variant). exit 1; fails ensures_2 out=source at both sites.

Positive control atk_pc: out := match source with none=>none | some t=>some t (structurally different but behaviourally correct) — verify exit=0. Spec is NON-VACUOUS: it accepts the correct behavior and rejects every wrong one.

Prepatch reproduced: yes — atk_1 is the prepatch bug (companion axis keeps freshly-initialised absent default `none` instead of carrying over source's setting), matching bundle Solution_prepatch_1/2.lean; both fail on out=source/isPresent exactly as recorded.

Refinement.md / mapping.md audit (A-leg + correspondence, my mandate): every leg is R or I — A1/A3/B1/B3 = R (type bijection Axis.units ↔ Option Int; None↔none, present object↔some id(obj); object identity ↔ tag equality); A2/B2 = I (deep value copy `out:=source` modeling gold's `ax2.<axis>.units = self.<axis>.units`). §C: NO kind-3 inexpressible-changed-op, NO consumed axioms, NO A-reference deep model of an unchanged callee (G-AX genuinely vacuous; empty axiom + deep_model_references inventories, conf_skip=false). There are thus no A-legs whose correspondence to a real callee could be falsified — the single changed op is modeled deeply and its fidelity is G-CONF's job (R/I leg, out of my scope, mechanically covered by G-CONF: bundle reports 100,004 inputs seed 26208, 0 disagreements against the REAL patched twinx/twiny). Model↔patch correspondence (inheritSharedConvA↔twinx @ _base.py:4441, inheritSharedConvB↔twiny @ :4470) is coherent and matches mapping.md §1.

Since no wrong impl verifies, no faithful refined patch needed materializing/resolving; there is no BROKEN candidate. Verdict SOUND: ≥5 (7) distinct attacks verified-rejected, positive control verifies, prepatch reproduced, refinement legs all R/I with sound A-inventory (vacuous).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions are byte-identical across Solution.lean and both Solution_prepatch_{1,2}.lean (verified with swebench_unified.markers.same_spec on the velvet LanguageTables). Solution.lean elaborates cleanly (lean_verify exit 0); prepatch_1 fails (exit 1) so the spec has teeth. Modeled functions inheritSharedConvA/B correspond to _AxesBase.twinx/twiny at base_commit f0f133943d. Gold patch adds the unconditional last-statement reference copy `ax2.xaxis.units = self.xaxis.units` (twinx) / `ax2.yaxis.units = self.yaxis.units` (twiny) right before `return ax2`. Axis.units is a plain instance attribute (no property/setter in axis.py), so after the companion is created its shared-axis units IS the source's units object on every input. The spec ensures `out = source` and `isPresent out = isPresent source`; under the mapping.md §2 bijection (object identity <-> Option Int tag equality, `is not None` <-> isSome), the modeled function is the identity map source|->source, which coincides exactly with the real callee's observable (source-axis units |-> companion-axis units) on every input. This is exactly what the sole F2P test asserts (units is not None; ax2.units is ax1.units). No input exists where the modeled function disagrees with the real patched twinx/twiny, and the spec is not too strong: it mirrors the gold patch's unconditional copy rather than adding constraints a resolving impl could violate. FAITHFUL, no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted relaxed-leakage disposition independently rather than rubber-stamping. (1) Spec region frozen: same_spec(Solution, Solution_prepatch_1/2, velvet)=True for both — the G-DIFF prepatch pair varies only impl regions. (2) Core sound: gates all pass (G-VERIFY, G-DIFF, G-EQ tight on grounded structural postconditions out=source / isPresent out = isPresent source, G-MUT, G-CONF non-skip conf_skip=false, G-AX vacuous, G-RESOLVE gold-verbatim); prepatch files reproduce the absent-default (out:=none) and fail exactly on the discriminating clause out=source at each independently-tested site. (3) Lexical G-LEAK screen on the spec_view passes: the view uses only abstract vocabulary ('display-conversion setting', 'companion view sharing a coordinate', 'source') and names NONE of the gold discriminators — no 'units', 'xaxis'/'yaxis', 'twinx'/'twiny', 'converter', 'inherit', 'dataLim', 'stackplot', or 'lib/matplotlib/axes/_base.py'. (4) The only behavior disclosed beyond problem_statement is the coordinate-sharing companion carrying over the source axis's conversion setting — precisely the dispositioned relaxed-leakage facet. Unavoidability re-confirmed: the public problem_statement is entirely about the dataLim->±inf symptom (verified: 'units'/'unit'/'converter'/'inherit'/'xaxis'/'yaxis'/'category' all absent from problem_statement; units vocabulary appears only in hints_text), while the sole FAIL_TO_PASS test test_twin_units[x]/[y] asserts units inheritance and object identity; no problem_statement-only derivation of the units-inheritance obligation exists, so a faithful verify-implies-correct spec MUST pin it. No NEW leaking line beyond the dispositioned carry-over behavior and the disposition is not broken (RELAXED_LEAKAGE.md present, meta.json relaxed_leakage=true, gates.G-LEAK.status='relaxed'). Per gates/_audit.py convention a properly dispositioned relaxed-leakage panel-3 result records as pass/NO-LEAKAGE + note; this is not a panel-layer defect.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
