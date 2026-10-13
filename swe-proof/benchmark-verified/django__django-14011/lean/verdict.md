# P2 adversarial audit — django__django-14011

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -191,7 +191,7 @@
 def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
   let mut out := []
   for c in reg do
-    out := out ++ [releaseRes c]
+    out := out ++ [c]
   return out
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,11 +50,7 @@
 
 -- impl-start
 def implementation_bindResources
-    (reg provided : List Resource) : List Resource := Id.run do
-  let mut r := reg
-  for c in provided do
-    r := setRes r c
-  return r
+    (reg provided : List Resource) : List Resource := reg
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -188,11 +188,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
-  let mut out := []
-  for c in reg do
-    out := out ++ [releaseRes c]
-  return out
+def implementation_releaseResources (reg : List Resource) : List Resource :=
+  reg.map (fun c => if c.name == "default" then c else releaseRes c)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,11 +50,8 @@
 
 -- impl-start
 def implementation_bindResources
-    (reg provided : List Resource) : List Resource := Id.run do
-  let mut r := reg
-  for c in provided do
-    r := setRes r c
-  return r
+    (reg provided : List Resource) : List Resource :=
+  provided.dropLast.foldl setRes reg
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -188,11 +188,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
-  let mut out := []
-  for c in reg do
-    out := out ++ [releaseRes c]
-  return out
+def implementation_releaseResources (reg : List Resource) : List Resource :=
+  reg ++ reg.map releaseRes
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```lean
import Mathlib
-- imports-end

-- axioms-start
/- No unchanged callee needs an opaque signature here: every operation the modeled
behaviors invoke (a keyed registry insert/replace, and releasing a resource) is a
pure value-level transformation, modeled directly in the `pure` region and used
identically on both sides of each refinement. The proof agent therefore consumes
no `_prop` axiom. -/
-- axioms-end

-- pure-start
/-- A managed resource held in a registry. `name` is the key under which the
registry tracks it; `isOpen` records whether the resource is currently live
(`true`) or has been released (`false`). -/
structure Resource where
  name : String
  isOpen : Bool
deriving DecidableEq, Repr

/-- Look the resource up by its key, returning the first entry with that name. -/
def lookupRes (reg : List Resource) (key : String) : Option Resource :=
  reg.find? (fun r => r.name == key)

/-- Insert `r` into the registry under its key: if an entry with the same key
already exists, replace it in place (keeping position); otherwise append it. -/
def setRes (reg : List Resource) (r : Resource) : List Resource :=
  if reg.any (fun d => d.name == r.name) then
    reg.map (fun d => if d.name == r.name then r else d)
  else
    reg ++ [r]

/-- Release a single resource: mark it closed, leaving its key unchanged. -/
def releaseRes (r : Resource) : Resource := { r with isOpen := false }
-- pure-end

-- post-conditions-start
/-- Binding a provided collection into the registry. The result is a registry with
no duplicate keys whose lookup is fully determined: every key the provided
collection mentions resolves to the provided value for that key, and every other
key keeps whatever the registry held before. -/
def problem_spec_bindResources
    (reg provided : List Resource) (result : List Resource) : Prop :=
  result.Pairwise (fun a b => a.name ≠ b.name) ∧
  (∀ key, lookupRes result key =
    match lookupRes provided key with
    | some r => some r
    | none   => lookupRes reg key)
-- post-conditions-end

-- impl-start
def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
  let mut r := reg
  for c in provided do
    r := setRes r c
  return r
-- impl-end

-- proof-start
theorem correct_bindResources :
    ∀ (reg provided : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided
        (implementation_bindResources reg provided) := by
  have hlookup : ∀ (reg : List Resource) (r : Resource) (key : String),
      lookupRes (setRes reg r) key = if r.name = key then some r else lookupRes reg key := by
    intro reg r key
    unfold setRes lookupRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany, List.find?_map]
      by_cases hk : r.name = key
      · subst hk
        rw [if_pos rfl]
        have hcomp : ((fun r' => r'.name == r.name) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == r.name) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == r.name) with _ | d0
        · exfalso
          rw [List.find?_eq_none] at hfind
          rw [List.any_eq_true] at hany
          obtain ⟨x, hx, hxp⟩ := hany
          exact hfind x hx hxp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          rw [hfind]; simp [hd0]
      · rw [if_neg hk]
        have hcomp : ((fun r' => r'.name == key) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == key) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == key) with _ | d0
        · rw [hfind]; simp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          have hne : d0.name ≠ r.name := by rw [hd0]; exact fun h => hk h.symm
          rw [hfind]; simp [hne]
    · rw [if_neg hany, List.find?_append]
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      by_cases hk : r.name = key
      · rw [if_pos hk]
        have hnone : reg.find? (fun r' => r'.name == key) = none := by
          rw [List.find?_eq_none]
          intro x hx hxp
          have h2 := hany x hx
          simp only [beq_iff_eq] at hxp
          simp [hxp, ← hk] at h2
        rw [hnone]; simp [hk]
      · rw [if_neg hk]; simp [hk]
  have hpair : ∀ (reg : List Resource) (r : Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      (setRes reg r).Pairwise (fun a b => a.name ≠ b.name) := by
    intro reg r h
    unfold setRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany]
      have hname : ∀ d ∈ reg, ((if d.name == r.name then r else d).name) = d.name := by
        intro d hd; by_cases hdd : d.name = r.name <;> simp [hdd]
      rw [List.pairwise_map]
      apply h.imp_of_mem
      intro a b ha hb hab
      rw [hname a ha, hname b hb]; exact hab
    · rw [if_neg hany]
      rw [List.pairwise_append]
      refine ⟨h, List.pairwise_singleton _ _, ?_⟩
      intro a ha b hb
      simp only [List.mem_singleton] at hb
      subst hb
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      have := hany a ha
      simp only [beq_eq_false_iff_ne] at this
      exact this
  have key_lemma : ∀ (provided reg : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided (provided.foldl setRes reg) := by
    intro provided
    induction provided with
    | nil =>
      intro reg hreg _
      refine ⟨hreg, ?_⟩
      intro key; simp [lookupRes]
    | cons c cs ih =>
      intro reg hreg hprov
      rw [List.foldl_cons]
      have hprovcs : cs.Pairwise (fun a b => a.name ≠ b.name) := hprov.tail
      have hregc : (setRes reg c).Pairwise (fun a b => a.name ≠ b.name) := hpair reg c hreg
      obtain ⟨hp1, hp2⟩ := ih (setRes reg c) hregc hprovcs
      refine ⟨hp1, ?_⟩
      intro key
      rw [hp2 key, hlookup reg c key]
      have hcons : lookupRes (c :: cs) key
          = if c.name = key then some c else lookupRes cs key := by
        simp only [lookupRes, List.find?_cons]
        by_cases hck : c.name = key
        · simp [hck]
        · rw [if_neg hck]
          have : (c.name == key) = false := by simpa using hck
          simp [this]
      rw [hcons]
      by_cases hck : c.name = key
      · have hcsnone : lookupRes cs key = none := by
          rw [lookupRes, List.find?_eq_none]
          intro x hx hxp
          simp only [beq_iff_eq] at hxp
          have hne : c.name ≠ x.name := (List.pairwise_cons.mp hprov).1 x hx
          exact hne (by rw [hck, hxp])
        rw [hcsnone]; simp [hck]
      · simp [hck]
  intro reg provided hreg hprov
  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by
    simp [implementation_bindResources, Id.run]
    rfl
  rw [himpl]
  exact key_lemma provided reg hreg hprov

-- proof-end

-- post-conditions-start
/-- Releasing the whole registry. The set of keys is preserved exactly (same keys,
same order, none added or dropped), and every resulting resource is closed. -/
def problem_spec_releaseResources
    (reg : List Resource) (result : List Resource) : Prop :=
  result.map (·.name) = reg.map (·.name) ∧
  (∀ r ∈ result, r.isOpen = false)
-- post-conditions-end

-- impl-start
def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
  let mut out := []
  for c in reg do
    out := out ++ [releaseRes c]
  return out
-- impl-end

-- proof-start
theorem correct_releaseResources :
    ∀ (reg : List Resource),
      problem_spec_releaseResources reg (implementation_releaseResources reg) := by
  intro reg
  have h : implementation_releaseResources reg = reg.map releaseRes := by
    simp only [implementation_releaseResources, Id.run]
    suffices hg : ∀ (init : List Resource),
        (forIn reg init fun c r => (pure (ForInStep.yield (r ++ [releaseRes c])) : Id _))
          = init ++ reg.map releaseRes by
      have := hg []
      simpa using this
    intro init
    induction reg generalizing init with
    | nil => simp; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        show forIn as (init ++ [releaseRes a]) _ = _
        rw [ih]
        simp
  rw [h]
  constructor
  · simp [releaseRes]
  · intro r hr
    simp [releaseRes] at hr
    obtain ⟨a, _, ha⟩ := hr
    rw [← ha]

-- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/- No unchanged callee needs an opaque signature here: every operation the modeled
behaviors invoke (a keyed registry insert/replace, and releasing a resource) is a
pure value-level transformation, modeled directly in the `pure` region and used
identically on both sides of each refinement. The proof agent therefore consumes
no `_prop` axiom. -/
-- axioms-end

-- pure-start
/-- A managed resource held in a registry. `name` is the key under which the
registry tracks it; `isOpen` records whether the resource is currently live
(`true`) or has been released (`false`). -/
structure Resource where
  name : String
  isOpen : Bool
deriving DecidableEq, Repr

/-- Look the resource up by its key, returning the first entry with that name. -/
def lookupRes (reg : List Resource) (key : String) : Option Resource :=
  reg.find? (fun r => r.name == key)

/-- Insert `r` into the registry under its key: if an entry with the same key
already exists, replace it in place (keeping position); otherwise append it. -/
def setRes (reg : List Resource) (r : Resource) : List Resource :=
  if reg.any (fun d => d.name == r.name) then
    reg.map (fun d => if d.name == r.name then r else d)
  else
    reg ++ [r]

/-- Release a single resource: mark it closed, leaving its key unchanged. -/
def releaseRes (r : Resource) : Resource := { r with isOpen := false }
-- pure-end

-- post-conditions-start
/-- Binding a provided collection into the registry. The result is a registry with
no duplicate keys whose lookup is fully determined: every key the provided
collection mentions resolves to the provided value for that key, and every other
key keeps whatever the registry held before. -/
def problem_spec_bindResources
    (reg provided : List Resource) (result : List Resource) : Prop :=
  result.Pairwise (fun a b => a.name ≠ b.name) ∧
  (∀ key, lookupRes result key =
    match lookupRes provided key with
    | some r => some r
    | none   => lookupRes reg key)
-- post-conditions-end

-- impl-start
def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
  let mut r := reg
  for c in provided do
    r := setRes r c
  return r
-- impl-end

-- proof-start
theorem correct_bindResources :
    ∀ (reg provided : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided
        (implementation_bindResources reg provided) := by
  have hlookup : ∀ (reg : List Resource) (r : Resource) (key : String),
      lookupRes (setRes reg r) key = if r.name = key then some r else lookupRes reg key := by
    intro reg r key
    unfold setRes lookupRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany, List.find?_map]
      by_cases hk : r.name = key
      · subst hk
        rw [if_pos rfl]
        have hcomp : ((fun r' => r'.name == r.name) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == r.name) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == r.name) with _ | d0
        · exfalso
          rw [List.find?_eq_none] at hfind
          rw [List.any_eq_true] at hany
          obtain ⟨x, hx, hxp⟩ := hany
          exact hfind x hx hxp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          rw [hfind]; simp [hd0]
      · rw [if_neg hk]
        have hcomp : ((fun r' => r'.name == key) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == key) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == key) with _ | d0
        · rw [hfind]; simp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          have hne : d0.name ≠ r.name := by rw [hd0]; exact fun h => hk h.symm
          rw [hfind]; simp [hne]
    · rw [if_neg hany, List.find?_append]
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      by_cases hk : r.name = key
      · rw [if_pos hk]
        have hnone : reg.find? (fun r' => r'.name == key) = none := by
          rw [List.find?_eq_none]
          intro x hx hxp
          have h2 := hany x hx
          simp only [beq_iff_eq] at hxp
          simp [hxp, ← hk] at h2
        rw [hnone]; simp [hk]
      · rw [if_neg hk]; simp [hk]
  have hpair : ∀ (reg : List Resource) (r : Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      (setRes reg r).Pairwise (fun a b => a.name ≠ b.name) := by
    intro reg r h
    unfold setRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany]
      have hname : ∀ d ∈ reg, ((if d.name == r.name then r else d).name) = d.name := by
        intro d hd; by_cases hdd : d.name = r.name <;> simp [hdd]
      rw [List.pairwise_map]
      apply h.imp_of_mem
      intro a b ha hb hab
      rw [hname a ha, hname b hb]; exact hab
    · rw [if_neg hany]
      rw [List.pairwise_append]
      refine ⟨h, List.pairwise_singleton _ _, ?_⟩
      intro a ha b hb
      simp only [List.mem_singleton] at hb
      subst hb
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      have := hany a ha
      simp only [beq_eq_false_iff_ne] at this
      exact this
  have key_lemma : ∀ (provided reg : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided (provided.foldl setRes reg) := by
    intro provided
    induction provided with
    | nil =>
      intro reg hreg _
      refine ⟨hreg, ?_⟩
      intro key; simp [lookupRes]
    | cons c cs ih =>
      intro reg hreg hprov
      rw [List.foldl_cons]
      have hprovcs : cs.Pairwise (fun a b => a.name ≠ b.name) := hprov.tail
      have hregc : (setRes reg c).Pairwise (fun a b => a.name ≠ b.name) := hpair reg c hreg
      obtain ⟨hp1, hp2⟩ := ih (setRes reg c) hregc hprovcs
      refine ⟨hp1, ?_⟩
      intro key
      rw [hp2 key, hlookup reg c key]
      have hcons : lookupRes (c :: cs) key
          = if c.name = key then some c else lookupRes cs key := by
        simp only [lookupRes, List.find?_cons]
        by_cases hck : c.name = key
        · simp [hck]
        · rw [if_neg hck]
          have : (c.name == key) = false := by simpa using hck
          simp [this]
      rw [hcons]
      by_cases hck : c.name = key
      · have hcsnone : lookupRes cs key = none := by
          rw [lookupRes, List.find?_eq_none]
          intro x hx hxp
          simp only [beq_iff_eq] at hxp
          have hne : c.name ≠ x.name := (List.pairwise_cons.mp hprov).1 x hx
          exact hne (by rw [hck, hxp])
        rw [hcsnone]; simp [hck]
      · simp [hck]
  intro reg provided hreg hprov
  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by
    simp [implementation_bindResources, Id.run]
    rfl
  rw [himpl]
  exact key_lemma provided reg hreg hprov

-- proof-end

-- post-conditions-start
/-- Releasing the whole registry. The set of keys is preserved exactly (same keys,
same order, none added or dropped), and every resulting resource is closed. -/
def problem_spec_releaseResources
    (reg : List Resource) (result : List Resource) : Prop :=
  result.map (·.name) = reg.map (·.name) ∧
  (∀ r ∈ result, r.isOpen = false)
-- post-conditions-end

-- impl-start
def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
  let mut out := []
  for c in reg do
    out := out ++ [releaseRes c]
  return out
-- impl-end

-- proof-start
theorem correct_releaseResources :
    ∀ (reg : List Resource),
      problem_spec_releaseResources reg (implementation_releaseResources reg) := by
  intro reg
  have h : implementation_releaseResources reg = reg.map releaseRes := by
    simp only [implementation_releaseResources, Id.run]
    suffices hg : ∀ (init : List Resource),
        (forIn reg init fun c r => (pure (ForInStep.yield (r ++ [releaseRes c])) : Id _))
          = init ++ reg.map releaseRes by
      have := hg []
      simpa using this
    intro init
    induction reg generalizing init with
    | nil => simp; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        show forIn as (init ++ [releaseRes a]) _ = _
        rw [ih]
        simp
  rw [h]
  constructor
  · simp [releaseRes]
  · intro r hr
    simp [releaseRes] at hr
    obtain ⟨a, _, ha⟩ := hr
    rw [← ha]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14011 (lean). verifier scripts/lean_verify.sh. All same_spec checks True (spec regions byte-identical; verified via swebench_unified.markers.same_spec).

COMMANDS: for each atk: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, batches of 4).

### Results
- atk_1 (release prepatch: leave resources OPEN, `out ++ [c]`): exit 1 — genuine error at :209 (Type mismatch, all-closed leg unprovable). Does NOT close.
- atk_2 (bind prepatch: return reg, ignore provided): exit 1 — `rfl` failed at :171 (lookup leg diverges). Does NOT close.
- atk_3 (partial-domain release: skip name=="default"): exit 1 — error at :206. Does NOT close.
- atk_4 (boundary bind: provided.dropLast.foldl setRes reg): exit 1 — `rfl` failed at :172. Does NOT close.
- atk_6 (control-flow-effect release: reg ++ reg.map releaseRes, duplicate names + some still open): exit 1 — error at :206 (name-list mismatch). Does NOT close.
- atk_7 (echo = gold impl, ungrounded-oracle echo class): exit 0, verifies no-sorry, clean axioms: correct_bindResources -> [propext, Classical.choice, Quot.sound]; correct_releaseResources -> [propext, Quot.sound]. No sorryAx / _prop.
- pos_control (gold Solution.lean): exit 0.

EVERY VERIFYING ATTACK'S FAITHFUL PATCH RESOLVE-CHECKED: only atk_7 verifies. atk_7 is byte-identical to the gold implementation (a same-spec echo of the gold), so its faithful refined patch IS the gold patch (meta.json patch_equals_gold=True), which resolves by construction — provided in `patches`. No dedicated run_resolve MCP tool is exposed here; the runner re-runs artifacts. There is no spec-satisfying-but-non-resolving impl, so verify=>correct is not violated.

### WHY SOUND (extensional specs, no A-leg break vector):
- problem_spec_bindResources pins the ENTIRE result lookup function (every provided key -> provided value; every other key -> prior reg value) AND result.Pairwise no-dup-names. Only free dimension is result ORDERING, which is unobservable through key-lookup and matches Python dict semantics — not a correctness gap.
- problem_spec_releaseResources pins result.map(.name)=reg.map(.name) (exact keys, order incl.) AND forall r in result, r.isOpen=false; since Resource has only {name,isOpen}, the result is fully determined — no residual freedom.
- Any impl whose correct_* closes is observably identical to the gold value kernel on all inputs.

REFINEMENT.MD AUDIT: 8 legs, all tagged R (setRes/releaseRes type refinements, iteration) or I (accumulators/returns). NO kind-3 (changed-inexpressible). NO A-consumed / A-reference legs — corroborated by clean #print axioms (no _prop axiom consumed). The classic G-EQ break vector (over-strong axiom letting a divergent impl close while the real callee differs) is therefore ABSENT. __setitem__/close_all/connection.close() are unchanged callees modeled as pure refinements applied identically on both sides; R/I legs covered by G-CONF (conformance_check.py, seed 14011, 120000 inputs). A-leg correspondence audit: vacuously holds (no A-legs).

Cosmetic note (non-blocking, matches verdict.md): mapping.md/refinement.md occasionally refer to ops as bindConnections/closeConnections and Conn, while Solution.lean uses bindResources/releaseResources and Resource. Pure documentation drift; type bijection and correspondence narrative identical; affects no gate or soundness.

VERDICT: SOUND — 6 attacks run (5 distinct wrong-impl classes + echo); no same-spec impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/- No unchanged callee needs an opaque signature here: every operation the modeled
behaviors invoke (a keyed registry insert/replace, and releasing a resource) is a
pure value-level transformation, modeled directly in the `pure` region and used
identically on both sides of each refinement. The proof agent therefore consumes
no `_prop` axiom. -/
-- axioms-end

-- pure-start
/-- A managed resource held in a registry. `name` is the key under which the
registry tracks it; `isOpen` records whether the resource is currently live
(`true`) or has been released (`false`). -/
structure Resource where
  name : String
  isOpen : Bool
deriving DecidableEq, Repr

/-- Look the resource up by its key, returning the first entry with that name. -/
def lookupRes (reg : List Resource) (key : String) : Option Resource :=
  reg.find? (fun r => r.name == key)

/-- Insert `r` into the registry under its key: if an entry with the same key
already exists, replace it in place (keeping position); otherwise append it. -/
def setRes (reg : List Resource) (r : Resource) : List Resource :=
  if reg.any (fun d => d.name == r.name) then
    reg.map (fun d => if d.name == r.name then r else d)
  else
    reg ++ [r]

/-- Release a single resource: mark it closed, leaving its key unchanged. -/
def releaseRes (r : Resource) : Resource := { r with isOpen := false }
-- pure-end

-- post-conditions-start
/-- Binding a provided collection into the registry. The result is a registry with
no duplicate keys whose lookup is fully determined: every key the provided
collection mentions resolves to the provided value for that key, and every other
key keeps whatever the registry held before. -/
def problem_spec_bindResources
    (reg provided : List Resource) (result : List Resource) : Prop :=
  result.Pairwise (fun a b => a.name ≠ b.name) ∧
  (∀ key, lookupRes result key =
    match lookupRes provided key with
    | some r => some r
    | none   => lookupRes reg key)
-- post-conditions-end

-- impl-start
def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
  let mut r := reg
  for c in provided do
    r := setRes r c
  return r
-- impl-end

-- proof-start
theorem correct_bindResources :
    ∀ (reg provided : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided
        (implementation_bindResources reg provided) := by
  have hlookup : ∀ (reg : List Resource) (r : Resource) (key : String),
      lookupRes (setRes reg r) key = if r.name = key then some r else lookupRes reg key := by
    intro reg r key
    unfold setRes lookupRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany, List.find?_map]
      by_cases hk : r.name = key
      · subst hk
        rw [if_pos rfl]
        have hcomp : ((fun r' => r'.name == r.name) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == r.name) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == r.name) with _ | d0
        · exfalso
          rw [List.find?_eq_none] at hfind
          rw [List.any_eq_true] at hany
          obtain ⟨x, hx, hxp⟩ := hany
          exact hfind x hx hxp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          rw [hfind]; simp [hd0]
      · rw [if_neg hk]
        have hcomp : ((fun r' => r'.name == key) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == key) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == key) with _ | d0
        · rw [hfind]; simp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          have hne : d0.name ≠ r.name := by rw [hd0]; exact fun h => hk h.symm
          rw [hfind]; simp [hne]
    · rw [if_neg hany, List.find?_append]
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      by_cases hk : r.name = key
      · rw [if_pos hk]
        have hnone : reg.find? (fun r' => r'.name == key) = none := by
          rw [List.find?_eq_none]
          intro x hx hxp
          have h2 := hany x hx
          simp only [beq_iff_eq] at hxp
          simp [hxp, ← hk] at h2
        rw [hnone]; simp [hk]
      · rw [if_neg hk]; simp [hk]
  have hpair : ∀ (reg : List Resource) (r : Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      (setRes reg r).Pairwise (fun a b => a.name ≠ b.name) := by
    intro reg r h
    unfold setRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany]
      have hname : ∀ d ∈ reg, ((if d.name == r.name then r else d).name) = d.name := by
        intro d hd; by_cases hdd : d.name = r.name <;> simp [hdd]
      rw [List.pairwise_map]
      apply h.imp_of_mem
      intro a b ha hb hab
      rw [hname a ha, hname b hb]; exact hab
    · rw [if_neg hany]
      rw [List.pairwise_append]
      refine ⟨h, List.pairwise_singleton _ _, ?_⟩
      intro a ha b hb
      simp only [List.mem_singleton] at hb
      subst hb
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      have := hany a ha
      simp only [beq_eq_false_iff_ne] at this
      exact this
  have key_lemma : ∀ (provided reg : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided (provided.foldl setRes reg) := by
    intro provided
    induction provided with
    | nil =>
      intro reg hreg _
      refine ⟨hreg, ?_⟩
      intro key; simp [lookupRes]
    | cons c cs ih =>
      intro reg hreg hprov
      rw [List.foldl_cons]
      have hprovcs : cs.Pairwise (fun a b => a.name ≠ b.name) := hprov.tail
      have hregc : (setRes reg c).Pairwise (fun a b => a.name ≠ b.name) := hpair reg c hreg
      obtain ⟨hp1, hp2⟩ := ih (setRes reg c) hregc hprovcs
      refine ⟨hp1, ?_⟩
      intro key
      rw [hp2 key, hlookup reg c key]
      have hcons : lookupRes (c :: cs) key
          = if c.name = key then some c else lookupRes cs key := by
        simp only [lookupRes, List.find?_cons]
        by_cases hck : c.name = key
        · simp [hck]
        · rw [if_neg hck]
          have : (c.name == key) = false := by simpa using hck
          simp [this]
      rw [hcons]
      by_cases hck : c.name = key
      · have hcsnone : lookupRes cs key = none := by
          rw [lookupRes, List.find?_eq_none]
          intro x hx hxp
          simp only [beq_iff_eq] at hxp
          have hne : c.name ≠ x.name := (List.pairwise_cons.mp hprov).1 x hx
          exact hne (by rw [hck, hxp])
        rw [hcsnone]; simp [hck]
      · simp [hck]
  intro reg provided hreg hprov
  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by
    simp [implementation_bindResources, Id.run]
    rfl
  rw [himpl]
  exact key_lemma provided reg hreg hprov

-- proof-end

-- post-conditions-start
/-- Releasing the whole registry. The set of keys is preserved exactly (same keys,
same order, none added or dropped), and every resulting resource is closed. -/
def problem_spec_releaseResources
    (reg : List Resource) (result : List Resource) : Prop :=
  result.map (·.name) = reg.map (·.name) ∧
  (∀ r ∈ result, r.isOpen = false)
-- post-conditions-end

-- impl-start
def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
  let mut out := []
  for c in reg do
    out := out ++ [releaseRes c]
  return out
-- impl-end

-- proof-start
theorem correct_releaseResources :
    ∀ (reg : List Resource),
      problem_spec_releaseResources reg (implementation_releaseResources reg) := by
  intro reg
  have h : implementation_releaseResources reg = reg.map releaseRes := by
    simp only [implementation_releaseResources, Id.run]
    suffices hg : ∀ (init : List Resource),
        (forIn reg init fun c r => (pure (ForInStep.yield (r ++ [releaseRes c])) : Id _))
          = init ++ reg.map releaseRes by
      have := hg []
      simpa using this
    intro init
    induction reg generalizing init with
    | nil => simp; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        show forIn as (init ++ [releaseRes a]) _ = _
        rw [ih]
        simp
  rw [h]
  constructor
  · simp [releaseRes]
  · intro r hr
    simp [releaseRes] at hr
    obtain ⟨a, _, ha⟩ := hr
    rw [← ha]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14011 (lean). verifier scripts/lean_verify.sh. All same_spec checks True (spec regions byte-identical; verified via swebench_unified.markers.same_spec).

COMMANDS: for each atk: `bash scripts/lean_verify.sh atk_N.lean` (run concurrently, batches of 4).

### Results
- atk_1 (release prepatch: leave resources OPEN, `out ++ [c]`): exit 1 — genuine error at :209 (Type mismatch, all-closed leg unprovable). Does NOT close.
- atk_2 (bind prepatch: return reg, ignore provided): exit 1 — `rfl` failed at :171 (lookup leg diverges). Does NOT close.
- atk_3 (partial-domain release: skip name=="default"): exit 1 — error at :206. Does NOT close.
- atk_4 (boundary bind: provided.dropLast.foldl setRes reg): exit 1 — `rfl` failed at :172. Does NOT close.
- atk_6 (control-flow-effect release: reg ++ reg.map releaseRes, duplicate names + some still open): exit 1 — error at :206 (name-list mismatch). Does NOT close.
- atk_7 (echo = gold impl, ungrounded-oracle echo class): exit 0, verifies no-sorry, clean axioms: correct_bindResources -> [propext, Classical.choice, Quot.sound]; correct_releaseResources -> [propext, Quot.sound]. No sorryAx / _prop.
- pos_control (gold Solution.lean): exit 0.

EVERY VERIFYING ATTACK'S FAITHFUL PATCH RESOLVE-CHECKED: only atk_7 verifies. atk_7 is byte-identical to the gold implementation (a same-spec echo of the gold), so its faithful refined patch IS the gold patch (meta.json patch_equals_gold=True), which resolves by construction — provided in `patches`. No dedicated run_resolve MCP tool is exposed here; the runner re-runs artifacts. There is no spec-satisfying-but-non-resolving impl, so verify=>correct is not violated.

### WHY SOUND (extensional specs, no A-leg break vector):
- problem_spec_bindResources pins the ENTIRE result lookup function (every provided key -> provided value; every other key -> prior reg value) AND result.Pairwise no-dup-names. Only free dimension is result ORDERING, which is unobservable through key-lookup and matches Python dict semantics — not a correctness gap.
- problem_spec_releaseResources pins result.map(.name)=reg.map(.name) (exact keys, order incl.) AND forall r in result, r.isOpen=false; since Resource has only {name,isOpen}, the result is fully determined — no residual freedom.
- Any impl whose correct_* closes is observably identical to the gold value kernel on all inputs.

REFINEMENT.MD AUDIT: 8 legs, all tagged R (setRes/releaseRes type refinements, iteration) or I (accumulators/returns). NO kind-3 (changed-inexpressible). NO A-consumed / A-reference legs — corroborated by clean #print axioms (no _prop axiom consumed). The classic G-EQ break vector (over-strong axiom letting a divergent impl close while the real callee differs) is therefore ABSENT. __setitem__/close_all/connection.close() are unchanged callees modeled as pure refinements applied identically on both sides; R/I legs covered by G-CONF (conformance_check.py, seed 14011, 120000 inputs). A-leg correspondence audit: vacuously holds (no A-legs).

Cosmetic note (non-blocking, matches verdict.md): mapping.md/refinement.md occasionally refer to ops as bindConnections/closeConnections and Conn, while Solution.lean uses bindResources/releaseResources and Resource. Pure documentation drift; type bijection and correspondence narrative identical; affects no gate or soundness.

VERDICT: SOUND — 6 attacks run (5 distinct wrong-impl classes + echo); no same-spec impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14011, verified against the real repo at base_commit e4430f22c8e3d29ce5d9d0263fba57121938d06d (git worktree).

Mechanical checks:
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0), both correct_bindResources and correct_releaseResources close with NO sorry.
- #print axioms clean: correct_bindResources -> [propext, Classical.choice, Quot.sound]; correct_releaseResources -> [propext, Quot.sound]. No sorryAx, no _prop axiom (meta.json axioms=[], opaque_callees=[]) -> proofs are genuine, no over-strong axiom hides drift.
- markers.same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True (LeanBackend): spec regions byte-identical across both prepatch variants.
- conformance_check.py (G-CONF): OK, 120011 inputs, 0 disagreements, seed 14011.

Callee faithfulness (modeled fn vs real callee):
1. setRes vs BaseConnectionHandler.__setitem__ (django/utils/connection.py:66 = setattr(self._connections, key, value)). Overwrite-at-key-else-create. problem_spec_bindResources observes only get-by-key (provided key -> provided value, other keys -> prior reg value) plus no-dup-keys; it correctly does NOT pin bind ordering, which setattr on a Local does not expose observably. Preconditions (unique keys in reg and provided) match reality (connections_override is a dict, registry uniquely keyed by alias). No diverging input.
2. releaseRes-map vs ConnectionHandler.close_all (django/db/utils.py:207): iterates aliases, connection.close() each, registry key-set/order preserved, post-state conn.connection is None. Model = order/key-preserving map with isOpen:=false. problem_spec_releaseResources pins exact result name-list (order incl.) + all isOpen=false; since Resource has only name+isOpen this fully determines the result and matches the F2P assertion assertIsNone(conn.connection). Edge cases (close_all skipping AttributeError aliases; in-memory sqlite close() no-op that is test-skipped per the gold's features.py skip entry) fall outside the modeled domain (established connections keyed by settings aliases) and do not produce a modeled-domain divergence.

Both modeled functions are extensional characterizations of the observable value kernel; neither is too strong nor drifts from the real callee. No input found where the modeled function disagrees with the real repo behavior.

(Doc drift only, non-blocking: mapping.md/refinement.md use bindConnections/closeConnections + Conn naming while Solution.lean uses bindResources/releaseResources + Resource; purely cosmetic, affects no gate.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[], no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched repo symbol, no bug/fix narration). Semantic review of the spec view confirms no leakage beyond the public problem_statement:

- The spec view is a fully abstract, domain-neutral model: a `Resource` registry (name/isOpen) with `setRes` (keyed insert/replace), `releaseRes` (close), `lookupRes`, and two triples `problem_spec_bindResources` / `problem_spec_releaseResources`. Impl+proof regions are elided by the projection.
- Behavior 2 (close/release every connection in the registry) is exactly the subject the public problem_statement already discloses ('ThreadedWSGIServer doesn't close database connections after each thread'), so modeling it is not a leak.
- Behavior 1 (bind a provided collection into the registry) is NOT in the problem_statement, but it is rendered only in generic registry terms ('Binding a provided collection into the registry'). No repo-localizing information appears: none of `connections_override`, `process_request_thread`, `close_request`, `_close_connections`, `close_all`, `ThreadedWSGIServer`, `__setitem__`, `connections`, or the file path `django/core/servers/basehttp.py` is present in any spec-view line, identifier, or comment. No diff hunk, no gold line, no fix narration.
- Identifiers (Resource/setRes/releaseRes/lookupRes/bindResources/releaseResources/isOpen/name) echo no patched symbol; comments describe abstract registry semantics, not the edit or the repo.

A solver cannot reconstruct the specific Python patch (target file, class, method names, mechanism) from this spec view any more than from the public ticket. The abstract bind operation is a faithful modeling choice carrying no edit-localization signal. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
