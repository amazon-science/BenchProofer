# P2 adversarial audit — scikit-learn__scikit-learn-26323

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, TERMINATING verifying wrong-impl exists. All 7 terminating same-spec attacks are rejected on the exact discriminating ensures clauses. The only verifying wrong-impls are non-terminating (while-true) ones that verify vacuously under loom.semantics.termination "partial" — these have NO faithful refined patch (the R/I map §A3 transliterates the terminating fold to a terminating for-loop; there is no map leg for `while true`), so they are not refinement-fidelity counterexamples and are excluded from the attack list.
```

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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,22 +65,16 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
     let mut result : List Component := []
     let mut i := listed.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ listed.length
       invariant result = selectReal (listed.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := listed[i - 1]!
       result := (if isReal c then [c] else []) ++ result
       i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
     return result
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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,22 +65,17 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
     let mut result : List Component := []
     let mut i := listed.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ listed.length
       invariant result = selectReal (listed.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := listed[i - 1]!
       result := (if isReal c then [c] else []) ++ result
       i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
+    result := result ++ [extra]
     return result
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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,22 +65,17 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
     let mut result : List Component := []
     let mut i := listed.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ listed.length
       invariant result = selectReal (listed.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := listed[i - 1]!
       result := (if isReal c then [c] else []) ++ result
       i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
+    result := result ++ (if isReal extra then [] else [extra])
     return result
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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,22 +65,17 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
     let mut result : List Component := []
     let mut i := listed.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ listed.length
       invariant result = selectReal (listed.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := listed[i - 1]!
       result := (if isReal c then [c] else []) ++ result
       i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
+    result := (if isReal extra then [extra] else []) ++ result
     return result
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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,20 +65,15 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
     let mut result : List Component := []
     let mut i := listed.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ listed.length
-      invariant result = selectReal (listed.drop i)
+      invariant result = listed.drop i
       done_with i = 0
-      decreasing i
     do
       let c := listed[i - 1]!
-      result := (if isReal c then [c] else []) ++ result
+      result := [c] ++ result
       i := i - 1
     result := result ++ (if isReal extra then [extra] else [])
     return result
```

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,23 +65,7 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
-    let mut result : List Component := []
-    let mut i := listed.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ listed.length
-      invariant result = selectReal (listed.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := listed[i - 1]!
-      result := (if isReal c then [c] else []) ++ result
-      i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
-    return result
+    return listed
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -101,5 +85,4 @@
 
 prove_correct collectBroadcastTargets by
   loom_solve
-  all_goals simp_all [broadcastTargets]
-  all_goals (rw [selectReal_drop_step listed i (by omega) (by omega)]; simp_all)
+  all_goals simp_all [broadcastTargets, selectReal]
```

Attack 7 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-component configuration action that is
@@ -65,23 +65,7 @@
   ensures isReal extra = false → out = selectReal listed
   do
     -- impl-start
-    -- Walk the listed sub-components, keeping the real ones (placeholder markers
-    -- are skipped). Then, after the listed components, also include the
-    -- designated extra component when it is a real component — the placeholder
-    -- markers are the only values excluded there too.
-    let mut result : List Component := []
-    let mut i := listed.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ listed.length
-      invariant result = selectReal (listed.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := listed[i - 1]!
-      result := (if isReal c then [c] else []) ++ result
-      i := i - 1
-    result := result ++ (if isReal extra then [extra] else [])
-    return result
+    return (if isReal extra then [extra] else [])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -101,5 +85,4 @@
 
 prove_correct collectBroadcastTargets by
   loom_solve
-  all_goals simp_all [broadcastTargets]
-  all_goals (rw [selectReal_drop_step listed i (by omega) (by omega)]; simp_all)
+  all_goals simp_all [broadcastTargets, selectReal]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-component configuration action that is
--  dispatched to each selected component is unchanged by this change and is
--  applied identically to every selected component, so it factors out of the
--  model: the operation is reduced to *which* components are selected to
--  receive it, and that selection is modeled DEEPLY in the `pure` region below.
--  There is no `axiom` declaration and no A-reference deep model of an outside
--  callee.)
-- axioms-end

-- pure-start
/- A sub-component of the composite is either a placeholder marker that is meant
   to be left untouched, or a real component carrying a numeric identity. The
   only distinction the selection reacts to is marker-vs-real. -/
inductive Component where
  | marker
  | real (id : Nat)
  deriving Inhabited, DecidableEq

/- A real component takes part in the configuration broadcast; a placeholder
   marker does not. -/
def isReal : Component → Bool
  | .marker  => false
  | .real _  => true

/- The selection over a list of listed sub-components: keep the real ones, in
   order, dropping the placeholder markers. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def selectReal : List Component → List Component
  | []      => []
  | c :: cs => (if isReal c then [c] else []) ++ selectReal cs

@[grind] lemma selectReal_nil : selectReal [] = [] := rfl
@[grind] lemma selectReal_cons (c : Component) (cs : List Component) :
    selectReal (c :: cs) = (if isReal c then [c] else []) ++ selectReal cs := rfl

/- The complete broadcast target list: the real listed sub-components, in order,
   followed by the designated extra component when it too is real (and never
   when it is a placeholder marker). -/
def broadcastTargets (listed : List Component) (extra : Component) : List Component :=
  selectReal listed ++ (if isReal extra then [extra] else [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the ordered list of sub-components that the configuration is
   broadcast to. `listed` and `extra` are read-only inputs (not `mut`); the
   query reads the membership of each and mutates nothing (directive 5). -/
method collectBroadcastTargets (listed : List Component) (extra : Component)
    return (out : List Component)
  ensures out = broadcastTargets listed extra
  ensures isReal extra = true → out = selectReal listed ++ [extra]
  ensures isReal extra = false → out = selectReal listed
  do
    -- impl-start
    return (selectReal listed) ++ (if isReal extra then [extra] else [])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectReal` peels one selection step. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectReal_drop_step (listed : List Component) (i : Nat)
    (hi : 0 < i) (hle : i ≤ listed.length) :
    selectReal (listed.drop (i - 1))
      = (if isReal listed[i - 1]! then [listed[i - 1]!] else []) ++ selectReal (listed.drop i) := by
  have hlt : i - 1 < listed.length := by omega
  have hcons : listed.drop (i - 1) = listed[i - 1]! :: listed.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectReal_cons]

prove_correct collectBroadcastTargets by
  loom_solve
  all_goals simp_all [broadcastTargets]
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS: per-attack `bash scripts/lean_verify.sh <path>` (run concurrently, <=4 background jobs). same_spec via `swebench_unified.markers.same_spec(...)` with get_backend('velvet').language.

SPEC SHAPE: complete FUNCTIONAL postcondition `out = broadcastTargets listed extra` (= selectReal listed ++ (if isReal extra then [extra] else [])) plus two case-split clauses ensures_2/ensures_3. The oracle broadcastTargets/selectReal is a TRANSPARENT pure function of the actual inputs — no axiom, no opaque/ungrounded callee (meta.json axioms=[], deep_model_references=[]; G-AX genuinely vacuous). Therefore any TERMINATING verifying impl is forced to return exactly the gold selection; ungrounded-oracle echo is impossible.

### RESULTS MATRIX (all same_spec=True):
- atk_1 prepatch bug (walk listed, NEVER append extra) -> exit 1, fails ensures_2 (isReal extra=true -> out=selectReal listed++[extra]) and ensures_3. Reproduces the reported bug (remainder estimator never configured). [prepatch_reproduced=true]
- atk_2 always append extra even for markers -> exit 1, fails ensures_1 (isReal extra=false -> out=selectReal listed) + ensures_3.
- atk_3 inverted guard (append extra iff MARKER) -> exit 1, fails ensures_1/2/3.
- atk_4 correct selection but PREPEND extra at front (order violation) -> exit 1, fails ensures_2/3 (order pinned).
- atk_5 no sentinel filter on listed (keep markers) -> exit 1, fails ensures_1/2/3 (membership pinned).
- atk_9 no-op: return listed unchanged -> exit 1.
- atk_10 extra-only: drop the listed selection -> exit 1, fails ensures_1/2.
All 7 fail on the EXACT ensures clauses (not proof-script artifacts) — the discriminator is precisely the F2P scenario (remainder=VarianceThreshold() => real estimator => isReal extra=true).

CONTROL-FLOW-EFFECT / DIVERGENCE probes (verify vacuously, EXCLUDED from attacks, patch-less by design):
- atk_6 `while true` loop then return partial result -> exit 0 (vacuous).
- atk_7 partial-domain: correct on empty listed, diverge (`while true`) otherwise -> exit 0 (vacuous on the diverging branch).
- atk_8 `while true` returning [] unconditionally -> exit 0 (vacuous).
These verify ONLY because loom.semantics.termination is "partial" (401/500 velvet bundles use this, benchmark-sanctioned per prompts/velvet/spec_guide.md). A diverging Lean method has NO faithful refined patch: refinement.md §A3 maps the TERMINATING `while i>0 ... done_with i=0` backward fold to the TERMINATING `for trans in transformers` loop; there is no map construct corresponding to `while true`, so materializing a patch would require an unfaithful infinite loop with no gold counterpart. Hence divergence is not a verify-not-correct refinement-fidelity counterexample; it is a universal partial-correctness artifact, out of scope for the resolve test, and correctly omitted from the attack list.

POSITIVE CONTROL pos_control.lean: structurally-different correct impl `return (selectReal listed) ++ (if isReal extra then [extra] else [])` (closed form, no loop) -> exit 0 verifies. Spec is non-vacuous.

RESOLVE: no resolve run was required or possible. Required: the runner runs resolve only for same-spec VERIFYING attacks with a submitted patch; none of the 7 submitted (terminating) attacks verify, so there is no verifying-candidate patch to materialize.

REFINEMENT.MD LEG AUDIT: all legs R or I (A1,A2,A5,A6=R; A3,A4=I). No kind-3, no axiom, no A-reference (§B/§C confirmed; meta axioms=[], deep_model_references=[]). The one non-trivial R (A5: _safe_set_output factored to identity-on-Component) is SOUND — the gold patch only ADDS a call site, does not modify the callee, and the F2P observable is membership of the broadcast target set (which components get configured, now including the remainder), which is exactly the modeled `out` list. R/I legs are mechanically covered by G-CONF (100009 inputs, 0 disagreements, seed 26323; oracle = verbatim transliteration of the patched set_output selection block). patch.diff is gold verbatim (G-RESOLVE recorded resolved in meta.json).

CONCLUSION: G-EQ SOUND. Spec-strength TIGHT: every terminating deviation from the gold selection is refuted on the discriminating ensures clauses; the only verifying wrong-impls are vacuously-verifying non-terminating ones, which have no faithful refined patch and thus cannot exhibit verify-not-correct. No refinement-fidelity defect found across 7 terminating attacks (>= 5 floor met) + prepatch reproduced + verifying positive control.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, TERMINATING verifying wrong-impl exists. All 7 terminating same-spec attacks are rejected on the exact discriminating ensures clauses. The only verifying wrong-impls are non-terminating (while-true) ones that verify vacuously under loom.semantics.termination "partial" — these have NO faithful refined patch (the R/I map §A3 transliterates the terminating fold to a terminating for-loop; there is no map leg for `while true`), so they are not refinement-fidelity counterexamples and are excluded from the attack list.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-component configuration action that is
--  dispatched to each selected component is unchanged by this change and is
--  applied identically to every selected component, so it factors out of the
--  model: the operation is reduced to *which* components are selected to
--  receive it, and that selection is modeled DEEPLY in the `pure` region below.
--  There is no `axiom` declaration and no A-reference deep model of an outside
--  callee.)
-- axioms-end

-- pure-start
/- A sub-component of the composite is either a placeholder marker that is meant
   to be left untouched, or a real component carrying a numeric identity. The
   only distinction the selection reacts to is marker-vs-real. -/
inductive Component where
  | marker
  | real (id : Nat)
  deriving Inhabited, DecidableEq

/- A real component takes part in the configuration broadcast; a placeholder
   marker does not. -/
def isReal : Component → Bool
  | .marker  => false
  | .real _  => true

/- The selection over a list of listed sub-components: keep the real ones, in
   order, dropping the placeholder markers. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def selectReal : List Component → List Component
  | []      => []
  | c :: cs => (if isReal c then [c] else []) ++ selectReal cs

@[grind] lemma selectReal_nil : selectReal [] = [] := rfl
@[grind] lemma selectReal_cons (c : Component) (cs : List Component) :
    selectReal (c :: cs) = (if isReal c then [c] else []) ++ selectReal cs := rfl

/- The complete broadcast target list: the real listed sub-components, in order,
   followed by the designated extra component when it too is real (and never
   when it is a placeholder marker). -/
def broadcastTargets (listed : List Component) (extra : Component) : List Component :=
  selectReal listed ++ (if isReal extra then [extra] else [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the ordered list of sub-components that the configuration is
   broadcast to. `listed` and `extra` are read-only inputs (not `mut`); the
   query reads the membership of each and mutates nothing (directive 5). -/
method collectBroadcastTargets (listed : List Component) (extra : Component)
    return (out : List Component)
  ensures out = broadcastTargets listed extra
  ensures isReal extra = true → out = selectReal listed ++ [extra]
  ensures isReal extra = false → out = selectReal listed
  do
    -- impl-start
    return (selectReal listed) ++ (if isReal extra then [extra] else [])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectReal` peels one selection step. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectReal_drop_step (listed : List Component) (i : Nat)
    (hi : 0 < i) (hle : i ≤ listed.length) :
    selectReal (listed.drop (i - 1))
      = (if isReal listed[i - 1]! then [listed[i - 1]!] else []) ++ selectReal (listed.drop i) := by
  have hlt : i - 1 < listed.length := by omega
  have hcons : listed.drop (i - 1) = listed[i - 1]! :: listed.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectReal_cons]

prove_correct collectBroadcastTargets by
  loom_solve
  all_goals simp_all [broadcastTargets]
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS: per-attack `bash scripts/lean_verify.sh <path>` (run concurrently, <=4 background jobs). same_spec via `swebench_unified.markers.same_spec(...)` with get_backend('velvet').language.

SPEC SHAPE: complete FUNCTIONAL postcondition `out = broadcastTargets listed extra` (= selectReal listed ++ (if isReal extra then [extra] else [])) plus two case-split clauses ensures_2/ensures_3. The oracle broadcastTargets/selectReal is a TRANSPARENT pure function of the actual inputs — no axiom, no opaque/ungrounded callee (meta.json axioms=[], deep_model_references=[]; G-AX genuinely vacuous). Therefore any TERMINATING verifying impl is forced to return exactly the gold selection; ungrounded-oracle echo is impossible.

### RESULTS MATRIX (all same_spec=True):
- atk_1 prepatch bug (walk listed, NEVER append extra) -> exit 1, fails ensures_2 (isReal extra=true -> out=selectReal listed++[extra]) and ensures_3. Reproduces the reported bug (remainder estimator never configured). [prepatch_reproduced=true]
- atk_2 always append extra even for markers -> exit 1, fails ensures_1 (isReal extra=false -> out=selectReal listed) + ensures_3.
- atk_3 inverted guard (append extra iff MARKER) -> exit 1, fails ensures_1/2/3.
- atk_4 correct selection but PREPEND extra at front (order violation) -> exit 1, fails ensures_2/3 (order pinned).
- atk_5 no sentinel filter on listed (keep markers) -> exit 1, fails ensures_1/2/3 (membership pinned).
- atk_9 no-op: return listed unchanged -> exit 1.
- atk_10 extra-only: drop the listed selection -> exit 1, fails ensures_1/2.
All 7 fail on the EXACT ensures clauses (not proof-script artifacts) — the discriminator is precisely the F2P scenario (remainder=VarianceThreshold() => real estimator => isReal extra=true).

CONTROL-FLOW-EFFECT / DIVERGENCE probes (verify vacuously, EXCLUDED from attacks, patch-less by design):
- atk_6 `while true` loop then return partial result -> exit 0 (vacuous).
- atk_7 partial-domain: correct on empty listed, diverge (`while true`) otherwise -> exit 0 (vacuous on the diverging branch).
- atk_8 `while true` returning [] unconditionally -> exit 0 (vacuous).
These verify ONLY because loom.semantics.termination is "partial" (401/500 velvet bundles use this, benchmark-sanctioned per prompts/velvet/spec_guide.md). A diverging Lean method has NO faithful refined patch: refinement.md §A3 maps the TERMINATING `while i>0 ... done_with i=0` backward fold to the TERMINATING `for trans in transformers` loop; there is no map construct corresponding to `while true`, so materializing a patch would require an unfaithful infinite loop with no gold counterpart. Hence divergence is not a verify-not-correct refinement-fidelity counterexample; it is a universal partial-correctness artifact, out of scope for the resolve test, and correctly omitted from the attack list.

POSITIVE CONTROL pos_control.lean: structurally-different correct impl `return (selectReal listed) ++ (if isReal extra then [extra] else [])` (closed form, no loop) -> exit 0 verifies. Spec is non-vacuous.

RESOLVE: no resolve run was required or possible. Required: the runner runs resolve only for same-spec VERIFYING attacks with a submitted patch; none of the 7 submitted (terminating) attacks verify, so there is no verifying-candidate patch to materialize.

REFINEMENT.MD LEG AUDIT: all legs R or I (A1,A2,A5,A6=R; A3,A4=I). No kind-3, no axiom, no A-reference (§B/§C confirmed; meta axioms=[], deep_model_references=[]). The one non-trivial R (A5: _safe_set_output factored to identity-on-Component) is SOUND — the gold patch only ADDS a call site, does not modify the callee, and the F2P observable is membership of the broadcast target set (which components get configured, now including the remainder), which is exactly the modeled `out` list. R/I legs are mechanically covered by G-CONF (100009 inputs, 0 disagreements, seed 26323; oracle = verbatim transliteration of the patched set_output selection block). patch.diff is gold verbatim (G-RESOLVE recorded resolved in meta.json).

CONCLUSION: G-EQ SOUND. Spec-strength TIGHT: every terminating deviation from the gold selection is refuted on the discriminating ensures clauses; the only verifying wrong-impls are vacuously-verifying non-terminating ones, which have no faithful refined patch and thus cannot exhibit verify-not-correct. No refinement-fidelity defect found across 7 terminating attacks (>= 5 floor met) + prepatch reproduced + verifying positive control.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function and the real repo behavior.

### Setup verified
- same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (spec region axioms/pure/pre/post byte-identical).
- Solution.lean elaborates cleanly (lean_verify RC=0). Prepatch fails (RC=1) exactly on the isReal extra=true postcondition — spec has real discriminating content, not a rubber stamp.
- G-CONF conformance_check.py passes: 100,009 inputs incl. boundary cases, seed=26323, 0 SHADOW/ORACLE disagreements.

MODEL vs REAL (base 586f4318, gold patch adds `if self.remainder not in {"passthrough","drop"}: _safe_set_output(self.remainder, transform=transform)` after the `for trans in transformers: _safe_set_output(trans,...)` loop where the generator filters `trans not in {"passthrough","drop"}`):
- Model: broadcastTargets listed extra = selectReal listed ++ (if isReal extra then [extra] else []); isReal c ⇔ c not in {"passthrough","drop"}. This is a verbatim transliteration of the patched selection block. selectReal keeps the real listed components in order (markers dropped), then appends extra iff real. Exactly mirrors the loop + new conditional.
- Subtle case checked (potential source of over/under-modeling): on a FITTED ColumnTransformer, self.transformers_ (built by _update_fitted_transformers over _iter, which appends a `('remainder', self.remainder, column)` tuple) means chain(self.transformers, transformers_) CAN contain the remainder object itself inside the loop, so real code would _safe_set_output the remainder twice (once in loop, once in the new conditional). The MODEL reproduces this faithfully: if the same real Component appears in `listed`, selectReal keeps it AND the extra-append adds it again → duplicate, matching the real double-dispatch. Conformance boundary case ([1],1) confirms shadow==oracle both = [1,1]. No abstraction hides this behavior.
- _safe_set_output is unchanged by the patch and applied identically to every selected component; correctly factored out as identity-on-Component (R-refinement per mapping.md §2), not a hidden axiom over the function under change. The observable F2P behavior is *which* components are configured, which is precisely the ordered `out` list the spec constrains.
- transform keyword passed through unchanged to all components on both sides; not part of the selection, correctly omitted.

The spec is neither too strong (prepatch-only weakness aside, the postconditions pin the exact selection ordering + membership) nor drifting from repo behavior. No input distinguishes broadcastTargets from the patched set_output selection. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified: same_spec(Solution, Solution_prepatch)=True, so the spec region is byte-identical; impl and prove_correct bodies are elided by _lean_spec_view). Mechanical leakage.screen over the spec view PASSES with zero hard failures (no diff markers, no gold-patch line reproduced, no patched file/module path, no spec-view identifier embedding the patched symbol 'set_output', no narration terms).

Gold edit: add `if self.remainder not in {"passthrough","drop"}: _safe_set_output(self.remainder, transform=transform)` to ColumnTransformer.set_output — i.e. set_output must also configure the `remainder` when it is a real estimator, not just the listed sub-transformers.

The public problem_statement ALREADY discloses this fully: its title is "ColumnTransformer.set_output ignores the remainder if it's an estimator" and the body states set_output configures its sub-transformers but ignores the remainder transformer, with expected results showing the remainder estimator being configured. So 'include the remainder estimator in the broadcast' is already public knowledge.

The spec view models this only ABSTRACTLY: `broadcastTargets listed extra = selectReal listed ++ (if isReal extra then [extra] else [])` over an invented `Component`/`marker`/`real` type. It never names set_output, remainder, _safe_set_output, ColumnTransformer, the file path sklearn/compose/_column_transformer.py, or the sentinel strings "passthrough"/"drop" — those repo specifics appear only in mapping.md/refinement.md, which are audit-side derivation docs, not the consumer spec view. The abstract selection semantics ('append the extra element iff real, after the kept listed elements') carry no localization beyond the problem_statement; if anything they are less revealing (no repo symbols at all). No spec-view line quotes gold-patch specifics or narrates the edit. Comments describe abstract selection behavior, not the bug/fix.

Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
