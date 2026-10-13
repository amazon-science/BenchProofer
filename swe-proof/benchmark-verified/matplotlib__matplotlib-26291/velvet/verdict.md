# P2 adversarial audit — matplotlib__matplotlib-26291

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, value-domain wrong impl verifies. The three frozen postconditions (∃reg, out=Except.ok reg; ctx=none → out=ok(placeWith (hostContext host) host); ∀c, ctx=some c → out=ok(placeWith c host)) EXACTLY pin the return value on every terminating input, expressed only through the opaque axioms placeWith/hostContext. Ctx and Region are opaque with no constructors, so equalities like `placeWith (hostContext host) host = placeWith c host` are unprovable — every behaviorally-wrong impl fails prove_correct. The only verifying wrong impls are partial-correctness DIVERGENCE artifacts (atk_7/atk_8), which are provably spec-INDEPENDENT (the gold-correct impl + the same divergent loop also verifies) and have NO faithful refined patch, so they are not verify⇏correct counterexamples.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,14 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
+    -- Wrong: ignore the supplied context and always measure with the host's own.
+    let result : Except PlaceErr Region :=
       match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+      | some _ => Except.ok (placeWith (hostContext host) host)
+      | none   => Except.ok (placeWith (hostContext host) host)
+    return result
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,14 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
+    -- Wrong: present context raises instead of measuring; absent handled.
+    let result : Except PlaceErr Region :=
       match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+      | some _ => Except.error PlaceErr.noContext
+      | none   => Except.ok (placeWith (hostContext host) host)
+    return result
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,15 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
+    -- Wrong (boundary): correct on some, but none path still errors like prepatch
+    -- while some path is correct — a distinct partial-domain split.
+    let result : Except PlaceErr Region :=
       match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+      | some c => Except.ok (placeWith c host)
+      | none   => Except.error PlaceErr.noContext
+    return result
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,17 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
-      match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+    -- Control-flow-effect: diverge unconditionally. Under partial correctness the
+    -- postconditions hold vacuously (no terminal state). If this verifies, the
+    -- spec fails to constrain termination and verify⇏correct.
+    let mut i : Nat := 1
+    while i > 0
+      invariant True
+    do
+      i := i + 1
+    return Except.error PlaceErr.noContext
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,20 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
-      match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+    -- Conditional divergence: on absent context, loop forever (vacuous); on present
+    -- context, return a WRONG grounded value (host ctx not the supplied c).
+    match ctx with
+    | some _ =>
+        return Except.ok (placeWith (hostContext host) host)
+    | none =>
+        let mut i : Nat := 1
+        while i > 0
+          invariant True
+        do
+          i := i + 1
+        return Except.ok (placeWith (hostContext host) host)
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
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
 /- An opaque drawing context: the transient state a placement needs in order to
@@ -78,18 +78,11 @@
   ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
   do
     -- impl-start
-    -- Obtain a concrete context before measuring: when one is supplied use it,
-    -- otherwise substitute the host's own context. Then run the unchanged
-    -- downstream pipeline with that concrete context. The substitution guards
-    -- the measurement against an absent context, so the placement always
-    -- produces a region instead of attempting an undefined measurement.
-    let chosen : Ctx :=
-      match ctx with
-      | some c => c
-      | none   => hostContext host
-    return Except.ok (placeWith chosen host)
+    -- Ungrounded-oracle echo: always emit the none-branch formula regardless of ctx.
+    -- Matches the frozen none-postcondition literally, echoing it onto the some path.
+    return Except.ok (placeWith (hostContext host) host)
     -- impl-end
 end
 
 prove_correct computePlacement by
-  loom_solve
+  loom_solve <;> try simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- An opaque drawing context: the transient state a placement needs in order to
   measure and position a child. Its internal structure is irrelevant to this
   decision; only whether one is supplied — and, if not, where a substitute is
   obtained — matters. -/
axiom Ctx : Type

/- An opaque host: the container a child is placed against. It always carries a
   figure, hence a retrievable drawing context (`hostContext`). -/
axiom Host : Type

/- An opaque placement region: the computed box a child occupies. Equality of
   regions is equality of their extents (mapping.md §2). -/
axiom Region : Type

/- The host's own drawing context. An UNCHANGED retrieval from the host's
   figure; total (every real host has a figure that yields a context) and left
   fully opaque — the weakest sufficient contract is none (directive 7).
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom hostContext : Host → Ctx

/- The downstream region computation given a CONCRETE context and the host: the
   unchanged measure → offset → transform pipeline. An UNCHANGED callee chain;
   total and deterministic given a concrete context, left fully opaque.
   Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom placeWith : Ctx → Host → Region
-- axioms-end

-- pure-start
/- The outcome shape of a placement. A well-formed placement always yields a
   region (`Except.ok`). The single error constructor records the one outcome a
   correct placement must NEVER produce: attempting to measure with no context
   at all, which on a container-less child is undefined. A correct result is
   always a region, never this error. -/
inductive PlaceErr where
  | noContext
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the placement region of an anchored child against its host.

   `ctx` and `host` are read-only inputs (neither is `mut`):
     * `ctx`  — the drawing context to measure with, or absent when the caller
                has none to offer;
     * `host` — the container the child is placed against; it always carries a
                retrievable drawing context of its own.

   Desired behaviour: the placement is computed by running the downstream
   measure-and-position pipeline with a CONCRETE context. A context is obtained
   before measuring: when one is supplied it is used directly; when none is
   supplied the host's own context is substituted. An absent context must never
   abandon the placement — every call must produce a region. The three
   postconditions pin this branch-by-branch, grounded directly in the inputs
   and the two opaque unchanged callees (directive 8: no single spec-level
   answer function exists for an implementation to echo):
     * every call yields a region (the never-raise frame);
     * an absent context runs the downstream with the host's own context;
     * a present context is passed through to the downstream unchanged. -/
noncomputable section
method computePlacement (ctx : Option Ctx) (host : Host)
    return (out : Except PlaceErr Region)
  ensures ∃ reg, out = Except.ok reg
  ensures ctx = none → out = Except.ok (placeWith (hostContext host) host)
  ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
  do
    -- impl-start
    -- Obtain a concrete context before measuring: when one is supplied use it,
    -- otherwise substitute the host's own context. Then run the unchanged
    -- downstream pipeline with that concrete context. The substitution guards
    -- the measurement against an absent context, so the placement always
    -- produces a region instead of attempting an undefined measurement.
    let chosen : Ctx :=
      match ctx with
      | some c => c
      | none   => hostContext host
    return Except.ok (placeWith chosen host)
    -- impl-end
end

prove_correct computePlacement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SETUP (all machine-checked; project root =, verifier = scripts/lean_verify.sh, same_spec via swebench_unified.markers). Baseline: positive control pos_control.lean VERIFIES (exit 0); prepatch prepatch.lean FAILS (exit 1) on `∃reg ok` and the `ctx=none` clause — prepatch bug reproduced.

SPEC SHAPE: fully functionally pinned partial-correctness spec (set_option loom.semantics.termination "partial"). Both branch postconditions + the never-raise frame determine the exact output on every terminating input, in terms of opaque axioms placeWith:Ctx→Host→Region and hostContext:Host→Ctx. Types Ctx/Host/Region are `axiom ... : Type` (no constructors) ⇒ the only closed terms of type Ctx are `c` (from `some c`) and `hostContext host`; the only Region terms are `placeWith _ host`. Lean cannot prove equality between distinct opaque applications, so no wrong return value can satisfy prove_correct.

### ATTACK BATTERY (all same_spec=True, byte-identical spec regions; impl region only edited; verified concurrently ≤4 at a time):
- atk_1 (branch-swap / ungrounded value): some-branch uses hostContext host instead of c. cmd: `bash scripts/lean_verify.sh atk_1.lean` → exit 1 (FAILS: unsolved `placeWith (hostContext host) host = placeWith c host`). Spec rejects — good.
- atk_2 (partial-domain): some→error, none→correct. → exit 1 (FAILS `∀c ¬ctx=some c` and `∃reg ok`). Rejected — good.
- atk_3 (boundary/partial-domain, = prepatch shape): some→correct, none→error. → exit 1 (FAILS `¬ctx=none`, `∃reg ok`). Rejected — good.
- atk_4 (control-flow, naive divergence, invariant True): loop then error. → exit 1 (FAILS: exit-VC still demands postconds, goal `False`). Rejected — good.
- atk_5 (conditional divergence w/ invariant True + wrong some value): → exit 1 (FAILS `placeWith (hostContext host) host = placeWith i host`). Rejected — good.
- atk_6 (ungrounded-oracle echo): unconditionally return the none-branch formula `ok(placeWith (hostContext host) host)`. → exit 1 (FAILS the some-branch equality). Rejected — good.
All six behavioral attacks fail with GENUINE proof-obligation errors (not syntax), confirming the value-domain is airtight.

### DIVERGENCE FINDING (investigated, dismissed as out-of-scope — NOT listed as counterexample attacks):
- atk_7 (atk_7.lean) and atk_8 (atk_8.lean): a non-terminating `while i>0 invariant i>0 do i:=i+1` (invariant CONTRADICTS the exit condition i=0), then return the forbidden error (atk_7) / a wrong OK value (atk_8). Both VERIFY (exit 0, no sorry, only linter warnings): under partial correctness the loop-exit VC is vacuous, so any return value is accepted.
- DECISIVE universality control univ_gold_plus_diverge.lean: the GOLD-CORRECT impl body preceded by the identical divergent loop ALSO VERIFIES (exit 0). ⇒ the acceptance is a spec-INDEPENDENT property of loom `termination "partial"` (used by 401/500 velvet bundles, including their own gold positive controls), NOT a fidelity defect of this spec.
- WHY NOT a verify⇏correct break: refinement.md maps every impl op to a real callee/type (R/I/A legs); a divergent loop corresponds to NO refinement leg, so a divergent impl has no FAITHFUL refined patch to materialize. Any literal transliteration (`while True: pass` in __call__) is not faithful to any modeled op and would trivially fail resolve for EVERY partial-correctness bundle — an artifact, not a defect. Hence no resolve run is 'needed' for atk_7/atk_8, and the universality control substitutes as decisive evidence. (Consistent with the mechanization's judgment-role guidance that a divergence-only finding is not a defect.)

RESOLVE: no resolve run was required — zero valid (faithful-refinable) verifying counterexamples exist.

REFINEMENT.MD LEG AUDIT (protocol step 3): A1/A2/A6 = R (type refinement, G-CONF's domain; G-CONF recorded pass on 100000 inputs). A3 = I (the added None-guard context substitution, modeled deeply, pinned by the ctx=none postcondition — correct). A4 hostContext↔ax.figure._get_renderer() = A-consumed opaque, unchanged total callee; A5 placeWith↔unchanged get_window_extent→get_offset→transform pipeline = A-consumed opaque, unchanged total; both correspond to genuinely-unchanged real callees (G-AX pass). none-branch bug fact = A-reference (G-AX-witnessed AttributeError). NO kind-3 legs: the one changed op is modeled deeply, not axiomatized; no consumed axiom about the function under change. Correspondence holds.

CONCLUSION: The spec is a faithful, tightly-pinned partial-correctness model. Value-domain fidelity is airtight (6/6 behavioral attacks correctly rejected across partial-domain, boundary, branch-swap, control-flow, and ungrounded-oracle-echo categories). The sole verifying wrong impls are spec-independent divergence artifacts with no faithful refined patch (proven via the gold+divergence universality control), so they are not verify⇏correct counterexamples. No verifying wrong impl has a faithful refined patch that fails to resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, value-domain wrong impl verifies. The three frozen postconditions (∃reg, out=Except.ok reg; ctx=none → out=ok(placeWith (hostContext host) host); ∀c, ctx=some c → out=ok(placeWith c host)) EXACTLY pin the return value on every terminating input, expressed only through the opaque axioms placeWith/hostContext. Ctx and Region are opaque with no constructors, so equalities like `placeWith (hostContext host) host = placeWith c host` are unprovable — every behaviorally-wrong impl fails prove_correct. The only verifying wrong impls are partial-correctness DIVERGENCE artifacts (atk_7/atk_8), which are provably spec-INDEPENDENT (the gold-correct impl + the same divergent loop also verifies) and have NO faithful refined patch, so they are not verify⇏correct counterexamples.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- An opaque drawing context: the transient state a placement needs in order to
   measure and position a child. Its internal structure is irrelevant to this
   decision; only whether one is supplied — and, if not, where a substitute is
   obtained — matters. -/
axiom Ctx : Type

/- An opaque host: the container a child is placed against. It always carries a
   figure, hence a retrievable drawing context (`hostContext`). -/
axiom Host : Type

/- An opaque placement region: the computed box a child occupies. Equality of
   regions is equality of their extents (mapping.md §2). -/
axiom Region : Type

/- The host's own drawing context. An UNCHANGED retrieval from the host's
   figure; total (every real host has a figure that yields a context) and left
   fully opaque — the weakest sufficient contract is none (directive 7).
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom hostContext : Host → Ctx

/- The downstream region computation given a CONCRETE context and the host: the
   unchanged measure → offset → transform pipeline. An UNCHANGED callee chain;
   total and deterministic given a concrete context, left fully opaque.
   Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom placeWith : Ctx → Host → Region
-- axioms-end

-- pure-start
/- The outcome shape of a placement. A well-formed placement always yields a
   region (`Except.ok`). The single error constructor records the one outcome a
   correct placement must NEVER produce: attempting to measure with no context
   at all, which on a container-less child is undefined. A correct result is
   always a region, never this error. -/
inductive PlaceErr where
  | noContext
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the placement region of an anchored child against its host.

   `ctx` and `host` are read-only inputs (neither is `mut`):
     * `ctx`  — the drawing context to measure with, or absent when the caller
                has none to offer;
     * `host` — the container the child is placed against; it always carries a
                retrievable drawing context of its own.

   Desired behaviour: the placement is computed by running the downstream
   measure-and-position pipeline with a CONCRETE context. A context is obtained
   before measuring: when one is supplied it is used directly; when none is
   supplied the host's own context is substituted. An absent context must never
   abandon the placement — every call must produce a region. The three
   postconditions pin this branch-by-branch, grounded directly in the inputs
   and the two opaque unchanged callees (directive 8: no single spec-level
   answer function exists for an implementation to echo):
     * every call yields a region (the never-raise frame);
     * an absent context runs the downstream with the host's own context;
     * a present context is passed through to the downstream unchanged. -/
noncomputable section
method computePlacement (ctx : Option Ctx) (host : Host)
    return (out : Except PlaceErr Region)
  ensures ∃ reg, out = Except.ok reg
  ensures ctx = none → out = Except.ok (placeWith (hostContext host) host)
  ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
  do
    -- impl-start
    -- Obtain a concrete context before measuring: when one is supplied use it,
    -- otherwise substitute the host's own context. Then run the unchanged
    -- downstream pipeline with that concrete context. The substitution guards
    -- the measurement against an absent context, so the placement always
    -- produces a region instead of attempting an undefined measurement.
    let chosen : Ctx :=
      match ctx with
      | some c => c
      | none   => hostContext host
    return Except.ok (placeWith chosen host)
    -- impl-end
end

prove_correct computePlacement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SETUP (all machine-checked; project root =, verifier = scripts/lean_verify.sh, same_spec via swebench_unified.markers). Baseline: positive control pos_control.lean VERIFIES (exit 0); prepatch prepatch.lean FAILS (exit 1) on `∃reg ok` and the `ctx=none` clause — prepatch bug reproduced.

SPEC SHAPE: fully functionally pinned partial-correctness spec (set_option loom.semantics.termination "partial"). Both branch postconditions + the never-raise frame determine the exact output on every terminating input, in terms of opaque axioms placeWith:Ctx→Host→Region and hostContext:Host→Ctx. Types Ctx/Host/Region are `axiom ... : Type` (no constructors) ⇒ the only closed terms of type Ctx are `c` (from `some c`) and `hostContext host`; the only Region terms are `placeWith _ host`. Lean cannot prove equality between distinct opaque applications, so no wrong return value can satisfy prove_correct.

### ATTACK BATTERY (all same_spec=True, byte-identical spec regions; impl region only edited; verified concurrently ≤4 at a time):
- atk_1 (branch-swap / ungrounded value): some-branch uses hostContext host instead of c. cmd: `bash scripts/lean_verify.sh atk_1.lean` → exit 1 (FAILS: unsolved `placeWith (hostContext host) host = placeWith c host`). Spec rejects — good.
- atk_2 (partial-domain): some→error, none→correct. → exit 1 (FAILS `∀c ¬ctx=some c` and `∃reg ok`). Rejected — good.
- atk_3 (boundary/partial-domain, = prepatch shape): some→correct, none→error. → exit 1 (FAILS `¬ctx=none`, `∃reg ok`). Rejected — good.
- atk_4 (control-flow, naive divergence, invariant True): loop then error. → exit 1 (FAILS: exit-VC still demands postconds, goal `False`). Rejected — good.
- atk_5 (conditional divergence w/ invariant True + wrong some value): → exit 1 (FAILS `placeWith (hostContext host) host = placeWith i host`). Rejected — good.
- atk_6 (ungrounded-oracle echo): unconditionally return the none-branch formula `ok(placeWith (hostContext host) host)`. → exit 1 (FAILS the some-branch equality). Rejected — good.
All six behavioral attacks fail with GENUINE proof-obligation errors (not syntax), confirming the value-domain is airtight.

### DIVERGENCE FINDING (investigated, dismissed as out-of-scope — NOT listed as counterexample attacks):
- atk_7 (atk_7.lean) and atk_8 (atk_8.lean): a non-terminating `while i>0 invariant i>0 do i:=i+1` (invariant CONTRADICTS the exit condition i=0), then return the forbidden error (atk_7) / a wrong OK value (atk_8). Both VERIFY (exit 0, no sorry, only linter warnings): under partial correctness the loop-exit VC is vacuous, so any return value is accepted.
- DECISIVE universality control univ_gold_plus_diverge.lean: the GOLD-CORRECT impl body preceded by the identical divergent loop ALSO VERIFIES (exit 0). ⇒ the acceptance is a spec-INDEPENDENT property of loom `termination "partial"` (used by 401/500 velvet bundles, including their own gold positive controls), NOT a fidelity defect of this spec.
- WHY NOT a verify⇏correct break: refinement.md maps every impl op to a real callee/type (R/I/A legs); a divergent loop corresponds to NO refinement leg, so a divergent impl has no FAITHFUL refined patch to materialize. Any literal transliteration (`while True: pass` in __call__) is not faithful to any modeled op and would trivially fail resolve for EVERY partial-correctness bundle — an artifact, not a defect. Hence no resolve run is 'needed' for atk_7/atk_8, and the universality control substitutes as decisive evidence. (Consistent with the mechanization's judgment-role guidance that a divergence-only finding is not a defect.)

RESOLVE: no resolve run was required — zero valid (faithful-refinable) verifying counterexamples exist.

REFINEMENT.MD LEG AUDIT (protocol step 3): A1/A2/A6 = R (type refinement, G-CONF's domain; G-CONF recorded pass on 100000 inputs). A3 = I (the added None-guard context substitution, modeled deeply, pinned by the ctx=none postcondition — correct). A4 hostContext↔ax.figure._get_renderer() = A-consumed opaque, unchanged total callee; A5 placeWith↔unchanged get_window_extent→get_offset→transform pipeline = A-consumed opaque, unchanged total; both correspond to genuinely-unchanged real callees (G-AX pass). none-branch bug fact = A-reference (G-AX-witnessed AttributeError). NO kind-3 legs: the one changed op is modeled deeply, not axiomatized; no consumed axiom about the function under change. Correspondence holds.

CONCLUSION: The spec is a faithful, tightly-pinned partial-correctness model. Value-domain fidelity is airtight (6/6 behavioral attacks correctly rejected across partial-domain, boundary, branch-swap, control-flow, and ungrounded-oracle-echo categories). The sole verifying wrong impls are spec-independent divergence artifacts with no faithful refined patch (proven via the gold+divergence universality control), so they are not verify⇏correct counterexamples. No verifying wrong impl has a faithful refined patch that fails to resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model-disagrees-with-real-callee) check for matplotlib__matplotlib-26291 (velvet). No diverging input exists; spec is faithful to the real callee.

### Setup checks
- Spec region byte-identical pre/post: swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend.language) = True.
- Solution.lean verifies: scripts/lean_verify.sh exit 0 (G-VERIFY 31.7s independently reproduced).
- Solution_prepatch.lean fails exactly on the never-raise clause (ensures ∃ reg) and the none-substitution clause (ctx=none → placeWith (hostContext host) host) — G-DIFF sound, confirming the postconditions are the discriminating content.

### MODEL vs REAL CALLEE (AnchoredLocatorBase.__call__, inset_locator.py:71, base fa68f462...):
Gold patch (verbatim from dataset):
  def __call__(self, ax, renderer):
+     if renderer is None:
+         renderer = ax.figure._get_renderer()
      self.axes = ax
      bbox = self.get_window_extent(renderer)
      ... (unchanged measure→offset→transform pipeline)

Branch-by-branch correspondence:
  * renderer = r (present)  ->  spec ensures out = Except.ok (placeWith c host). Real: pipeline run directly on r. MATCH.
  * renderer = None (absent) ->  spec ensures out = Except.ok (placeWith (hostContext host) host). Real: renderer := ax.figure._get_renderer() (= hostContext host), then same pipeline. MATCH.
  * every call -> Except.ok (never raises). Real patched code never raises on this figure-less locator because the None guard supplies a concrete renderer. MATCH.

Why no divergence is reachable:
- Ctx is opaque; the only observable is present-vs-absent at the decision and WHICH concrete context threads into the pipeline. Option Ctx over opaque Ctx is a faithful carrier — the spec cannot be 'too strong' about renderer internals it never constrains.
- hostContext (ax.figure._get_renderer) and placeWith (unchanged pipeline) are G-AX-witnessed total + deterministic given a concrete context, so the postconditions assert exactly the real callee's value on every input; no input makes the real callee produce something other than these.
- The absent-context bug fact is an A-reference validated by G-AX (real prepatch get_window_extent(None) raises AttributeError; patched substitution returns a region), so postcondition 2 matches real fixed behavior rather than over-constraining.
- The self.axes = ax side effect lies outside the specified observable surface (the returned region), a legitimate modeling boundary — not a point of disagreement with the callee's return value.

Conclusion: the modeled function agrees with the real callee on all inputs (present renderer, None renderer). Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean) is fully abstracted onto opaque carriers Ctx/Host/Region and opaque callees hostContext/placeWith, modeled function computePlacement. It never names the patched file (inset_locator.py), the patched line (`if renderer is None: renderer = ax.figure._get_renderer()`), or the repo symbols renderer/_get_renderer/ax.figure/get_window_extent. Lexical G-LEAK screen (leakage.screen, lean flavor) PASSES: no diff markers, no reproduced gold-patch line (>=8 chars), no patched file/module path, no narration tokens (bug/fix/patch/…), and no spec-view identifier embedding the sole distinctive changed symbol 'draw'. meta relaxed_leakage=None, no RELAXED_LEAKAGE.md, so this is a straight NO-LEAKAGE (not a deferral). Semantic check: the behavioral content the postconditions pin — absent context substituted by host's own context, always yields a region — is ALREADY PUBLIC in the problem_statement, whose traceback literally shows renderer=self.figure._get_renderer(), the None-passing caller locator(ax, None), get_window_extent, and the NoneType AttributeError. The spec reveals nothing beyond the public task and in fact abstracts it further. Spec-region integrity confirmed: spec_signature diff vs Solution_prepatch.lean is confined to impl-region + proof tactic line (loom_solve vs loom_solve <;> try simp_all); the frozen spec (axioms/pure/pre/post/method signature) is byte-identical. refinement.md and mapping.md do quote the gold line/file, but those are auditor docs, not part of the solver-visible spec view screened by G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
